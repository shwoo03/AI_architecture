#!/usr/bin/env python3
"""Append and inspect incubating AgentRun ledger records."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib_runtime_lock import runtime_lock  # noqa: E402


try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass


REQUIRED_FIELDS = (
    "schema_version",
    "ts",
    "agent_run_id",
    "brief_id",
    "tier",
    "agent",
    "workflow",
    "status",
    "goal_lineage",
    "artifacts",
    "result_summary",
    "changed_paths",
    "validation",
    "created_by",
    "ext",
)
STATUSES = {"completed", "failed", "blocked"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def resolve_under_root(root: Path, value: str, *, label: str) -> Path:
    path = Path(value)
    resolved = path.resolve(strict=False) if path.is_absolute() else (root / path).resolve(strict=False)
    try:
        resolved.relative_to(root.resolve(strict=False))
    except ValueError as exc:
        raise ValueError(f"{label} outside root: {value}") from exc
    return resolved


def rel_path(root: Path, path: Path) -> str:
    return path.resolve(strict=False).relative_to(root.resolve(strict=False)).as_posix()


def ledger_path(root: Path) -> Path:
    return root / "runtime" / "agent-runs.jsonl"


def load_brief(root: Path, value: str) -> tuple[Path, dict[str, Any]]:
    path = resolve_under_root(root, value, label="brief path")
    if not path.is_file():
        raise ValueError(f"brief not found: {value}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"brief invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("brief must be a JSON object")
    brief_id = data.get("brief_id")
    lineage = data.get("goal_lineage")
    if not isinstance(brief_id, str) or not brief_id:
        raise ValueError("brief missing string brief_id")
    if not isinstance(lineage, list) or not all(isinstance(item, dict) for item in lineage):
        raise ValueError("brief missing object-array goal_lineage")
    return path, data


def read_ledger_strict(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            value = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path.as_posix()}:{line_no} malformed JSON: {exc}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"{path.as_posix()}:{line_no} record must be an object")
        records.append(value)
    return records


def next_run_id(records: list[dict[str, Any]], brief_id: str) -> str:
    prefix = f"run-{brief_id}-"
    highest = 0
    for record in records:
        value = record.get("agent_run_id")
        if not isinstance(value, str) or not value.startswith(prefix):
            continue
        suffix = value.removeprefix(prefix)
        if suffix.isdigit():
            highest = max(highest, int(suffix))
    return f"{prefix}{highest + 1:02d}"


def parse_validation(values: list[str]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for value in values:
        if "=" not in value:
            raise ValueError("--validation must use command=status")
        command, status = value.split("=", 1)
        command = command.strip()
        status = status.strip()
        if not command or not status:
            raise ValueError("--validation must use non-empty command=status")
        result.append({"command": command, "status": status})
    return result


def validate_record(record: dict[str, Any]) -> None:
    findings = record_findings(record, "<record>")
    if findings:
        raise ValueError(str(findings[0]["detail"]))


def record_findings(record: dict[str, Any], location: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    missing = [field for field in REQUIRED_FIELDS if field not in record]
    if missing:
        findings.append({"severity": "ERROR", "check": "required_fields", "path": location, "detail": "missing required fields: " + ", ".join(missing)})
        return findings
    string_fields = ("schema_version", "ts", "agent_run_id", "brief_id", "tier", "agent", "workflow", "status", "result_summary", "created_by")
    for field in string_fields:
        if not isinstance(record[field], str) or not record[field]:
            findings.append({"severity": "ERROR", "check": "field_type", "path": location, "detail": f"{field} must be non-empty string"})
    if record["schema_version"] != "ai-architecture.agent-run.v1":
        findings.append({"severity": "ERROR", "check": "schema_version", "path": location, "detail": "unsupported schema_version"})
    if not re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", record["ts"]):
        findings.append({"severity": "ERROR", "check": "timestamp", "path": location, "detail": "ts must be UTC ISO 8601 with Z suffix"})
    if not isinstance(record["goal_lineage"], list) or not all(isinstance(item, dict) for item in record["goal_lineage"]):
        findings.append({"severity": "ERROR", "check": "goal_lineage", "path": location, "detail": "goal_lineage must be an object array"})
    elif not record["goal_lineage"]:
        findings.append({"severity": "ERROR", "check": "goal_lineage", "path": location, "detail": "goal_lineage must not be empty"})
    else:
        tail = record["goal_lineage"][-1]
        expected_ref = f"runtime/agent-runs.jsonl#{record.get('agent_run_id')}"
        if tail.get("type") != "agent_run":
            findings.append({"severity": "ERROR", "check": "goal_lineage_tail", "path": location, "detail": "goal_lineage must end with type=agent_run"})
        if tail.get("ref") != expected_ref:
            findings.append({"severity": "ERROR", "check": "goal_lineage_tail", "path": location, "detail": f"agent_run tail ref must be {expected_ref}"})
    for field in ("artifacts", "changed_paths", "validation"):
        if not isinstance(record[field], list):
            findings.append({"severity": "ERROR", "check": "field_type", "path": location, "detail": f"{field} must be a list"})
    if not isinstance(record["ext"], dict):
        findings.append({"severity": "ERROR", "check": "ext", "path": location, "detail": "ext must be an object"})
    if record["tier"] != "incubating":
        findings.append({"severity": "ERROR", "check": "tier", "path": location, "detail": "tier must be incubating for Phase 1c"})
    return findings


def build_record(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    brief_path, brief = load_brief(root, args.brief)
    ts = utc_now()
    path = ledger_path(root)
    records = read_ledger_strict(path)
    brief_id = str(brief["brief_id"])
    agent_run_id = next_run_id(records, brief_id)
    summary = args.result_summary.strip()
    if not summary:
        raise ValueError("--result-summary is required")
    validation = parse_validation(args.validation)
    lineage = [dict(item) for item in brief["goal_lineage"]]
    lineage.append(
        {
            "type": "agent_run",
            "ref": f"runtime/agent-runs.jsonl#{agent_run_id}",
            "summary": summary,
        }
    )
    record = {
        "schema_version": "ai-architecture.agent-run.v1",
        "ts": ts,
        "agent_run_id": agent_run_id,
        "brief_id": brief_id,
        "tier": args.tier,
        "agent": args.agent,
        "workflow": args.workflow,
        "status": args.status,
        "goal_lineage": lineage,
        "artifacts": args.artifact,
        "result_summary": summary,
        "changed_paths": args.changed_path,
        "validation": validation,
        "created_by": args.created_by,
        "ext": {},
    }
    brief_rel = rel_path(root, brief_path)
    if not any(item.get("type") == "brief" and item.get("ref") == brief_rel for item in lineage if isinstance(item, dict)):
        record["artifacts"] = [*record["artifacts"], brief_rel]
    validate_record(record)
    return record


def add_record(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    path = ledger_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with runtime_lock(root, "agent-runs"):
        record = build_record(root, args)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    return record


def dump_records(root: Path, args: argparse.Namespace) -> list[dict[str, Any]]:
    if args.tail < 0:
        raise ValueError("--tail must be non-negative")
    records = read_ledger_strict(ledger_path(root))
    return records[-args.tail :] if args.tail else []


def list_records(root: Path, args: argparse.Namespace) -> list[dict[str, Any]]:
    records = read_ledger_strict(ledger_path(root))
    if args.status:
        records = [record for record in records if record.get("status") == args.status]
    if args.agent:
        records = [record for record in records if record.get("agent") == args.agent]
    return records


def check_records(root: Path, _args: argparse.Namespace) -> dict[str, Any]:
    path = ledger_path(root)
    records = read_ledger_strict(path)
    findings: list[dict[str, str]] = []
    for index, record in enumerate(records, start=1):
        findings.extend(record_findings(record, f"runtime/agent-runs.jsonl:{index}"))
    return {
        "ok": not findings,
        "record_count": len(records),
        "findings": findings,
    }


def summary_records(root: Path, _args: argparse.Namespace) -> dict[str, Any]:
    records = read_ledger_strict(ledger_path(root))
    check_payload = check_records(root, _args)
    by_status: dict[str, int] = {}
    by_agent: dict[str, int] = {}
    by_workflow: dict[str, int] = {}
    latest_ts = ""
    for record in records:
        for key, target in (("status", by_status), ("agent", by_agent), ("workflow", by_workflow)):
            value = str(record.get(key) or "")
            if value:
                target[value] = target.get(value, 0) + 1
        ts = str(record.get("ts") or "")
        if ts > latest_ts:
            latest_ts = ts
    return {
        "total": len(records),
        "by_status": dict(sorted(by_status.items())),
        "by_agent": dict(sorted(by_agent.items())),
        "by_workflow": dict(sorted(by_workflow.items())),
        "latest_ts": latest_ts,
        "findings_count": len(check_payload["findings"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=None)
    parser.add_argument("--format", choices=("json",), default="json")
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="Append one manual AgentRun record.")
    add.add_argument("--brief", required=True)
    add.add_argument("--status", choices=sorted(STATUSES), default="completed")
    add.add_argument("--result-summary", required=True)
    add.add_argument("--changed-path", action="append", default=[])
    add.add_argument("--validation", action="append", default=[])
    add.add_argument("--artifact", action="append", default=[])
    add.add_argument("--tier", default="incubating")
    add.add_argument("--agent", default="human_operator")
    add.add_argument("--workflow", default="manual_smoke")
    add.add_argument("--created-by", default="manual")
    add.add_argument("--format", choices=("json",), default="json")

    dump = sub.add_parser("dump", help="Print recent AgentRun records.")
    dump.add_argument("--tail", type=int, default=5)
    dump.add_argument("--format", choices=("json",), default="json")

    list_parser = sub.add_parser("list", help="Print AgentRun records.")
    list_parser.add_argument("--status", default="")
    list_parser.add_argument("--agent", default="")
    list_parser.add_argument("--format", choices=("json",), default="json")

    check = sub.add_parser("check", help="Validate AgentRun ledger records.")
    check.add_argument("--format", choices=("json",), default="json")

    summary = sub.add_parser("summary", help="Summarize AgentRun ledger records.")
    summary.add_argument("--format", choices=("json",), default="json")

    args = parser.parse_args()
    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[2]
    try:
        if args.command == "add":
            payload: Any = add_record(root, args)
        elif args.command == "dump":
            payload = dump_records(root, args)
        elif args.command == "list":
            payload = list_records(root, args)
        elif args.command == "check":
            payload = check_records(root, args)
        else:
            payload = summary_records(root, args)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2 if args.command == "dump" else 1
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if args.command == "check" and not payload.get("ok", False):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

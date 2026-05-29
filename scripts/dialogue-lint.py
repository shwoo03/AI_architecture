#!/usr/bin/env python3
"""Validate subagent debate planning ledgers."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass


SCHEMA_VERSION = "ai-architecture.subagent-debate.v1"
KINDS = {"start", "claim", "critique", "concession", "unresolved", "converged"}
PARTICIPANTS = {"codex", "subagent-critic", "subagent-researcher", "subagent-verifier", "human"}
PROVIDERS = {"codex", "subagent", "manual"}
SEVERITIES = {"info", "risk", "block"}
RESOLUTIONS = {"resolved", "accepted_as_risk"}
NESTED_SUBAGENT_FIELDS = ("subagents", "spawned_agents", "delegated_to", "delegation_plan")


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def is_subagent_participant(value: str) -> bool:
    return value.startswith("subagent-")


def finding(severity: str, check: str, detail: str, *, line: int = 0, turn_id: str = "") -> dict[str, Any]:
    payload: dict[str, Any] = {"severity": severity, "check": check, "detail": detail}
    if line:
        payload["line"] = line
    if turn_id:
        payload["turn_id"] = turn_id
    return payload


def load_records(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    findings: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    if not path.exists():
        return [], [finding("ERROR", "dialogue_missing", f"{path.as_posix()} does not exist")]
    for index, raw in enumerate(path.read_text(encoding="utf-8-sig", errors="replace").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            record = json.loads(raw)
        except json.JSONDecodeError as exc:
            findings.append(finding("ERROR", "json_parse", str(exc), line=index))
            continue
        if not isinstance(record, dict):
            findings.append(finding("ERROR", "record_type", "record must be a JSON object", line=index))
            continue
        record["_line"] = index
        records.append(record)
    return records, findings


def validate_records(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str], dict[str, Any] | None]:
    findings: list[dict[str, Any]] = []
    seen: dict[str, dict[str, Any]] = {}
    resolved_blocks: set[str] = set()
    converged: dict[str, Any] | None = None
    start_count = 0

    for record in records:
        line = int(record.get("_line") or 0)
        turn_id = str(record.get("turn_id") or "")
        kind = str(record.get("kind") or "")
        participant = str(record.get("from") or "")
        provider = str(record.get("provider") or "")

        if record.get("schema_version") != SCHEMA_VERSION:
            findings.append(finding("ERROR", "schema_version", f"expected {SCHEMA_VERSION}", line=line, turn_id=turn_id))
        if not turn_id:
            findings.append(finding("ERROR", "turn_id_missing", "turn_id is required", line=line))
        elif turn_id in seen:
            findings.append(finding("ERROR", "turn_id_duplicate", f"duplicate turn_id {turn_id}", line=line, turn_id=turn_id))
        if kind not in KINDS:
            findings.append(finding("ERROR", "kind_invalid", f"invalid kind {kind!r}", line=line, turn_id=turn_id))
        if participant not in PARTICIPANTS:
            findings.append(finding("ERROR", "participant_invalid", f"invalid from {participant!r}", line=line, turn_id=turn_id))
        if provider not in PROVIDERS:
            findings.append(finding("ERROR", "provider_invalid", f"invalid provider {provider!r}", line=line, turn_id=turn_id))
        if is_subagent_participant(participant) and provider != "subagent":
            findings.append(finding("ERROR", "subagent_provider", "subagent participants must use provider=subagent", line=line, turn_id=turn_id))
        if participant == "codex" and provider != "codex":
            findings.append(finding("ERROR", "codex_provider", "codex turns must use provider=codex", line=line, turn_id=turn_id))
        if is_subagent_participant(participant):
            if record.get("subagents_allowed") is True or record.get("uses_subagents") is True:
                findings.append(finding("ERROR", "nested_subagents_forbidden", "subagent debate turns must not spawn nested subagents", line=line, turn_id=turn_id))
            for field in NESTED_SUBAGENT_FIELDS:
                value = record.get(field)
                if value not in (None, "", [], {}):
                    findings.append(finding("ERROR", "nested_subagents_forbidden", f"subagent debate turns must not record {field}", line=line, turn_id=turn_id))

        if kind == "start":
            start_count += 1
            if not str(record.get("task") or "").strip():
                findings.append(finding("ERROR", "task_missing", "start record requires task", line=line, turn_id=turn_id))
            policy = record.get("policy")
            if isinstance(policy, dict):
                if policy.get("claude_auto_debate_disabled") is not True:
                    findings.append(finding("ERROR", "claude_auto_debate_disabled", "dialogue policy must disable automatic Claude debate", line=line, turn_id=turn_id))
                if policy.get("nested_subagents_allowed") is True:
                    findings.append(finding("ERROR", "nested_subagents_forbidden", "dialogue policy must not allow nested subagents", line=line, turn_id=turn_id))
        elif kind in {"claim", "critique", "concession", "unresolved"}:
            if not str(record.get("content") or "").strip():
                findings.append(finding("ERROR", "content_missing", f"{kind} requires content", line=line, turn_id=turn_id))

        target = str(record.get("targets_claim_id") or "")
        if kind == "critique":
            if not target:
                findings.append(finding("ERROR", "critique_target_missing", "critique requires targets_claim_id", line=line, turn_id=turn_id))
            elif target not in seen:
                findings.append(finding("ERROR", "critique_target_unknown", f"unknown target {target}", line=line, turn_id=turn_id))
            severity = str(record.get("severity") or "")
            if severity not in SEVERITIES:
                findings.append(finding("ERROR", "severity_invalid", f"invalid severity {severity!r}", line=line, turn_id=turn_id))
            evidence = record.get("evidence")
            if severity == "block" and not (isinstance(evidence, list) and any(str(item).strip() for item in evidence)):
                findings.append(finding("ERROR", "block_evidence_missing", "block critique requires evidence", line=line, turn_id=turn_id))
        elif kind == "concession":
            if not target:
                findings.append(finding("ERROR", "concession_target_missing", "concession requires targets_claim_id", line=line, turn_id=turn_id))
            elif target not in seen:
                findings.append(finding("ERROR", "concession_target_unknown", f"unknown target {target}", line=line, turn_id=turn_id))
            resolution = str(record.get("resolution") or "")
            if resolution not in RESOLUTIONS:
                findings.append(finding("ERROR", "resolution_invalid", f"invalid resolution {resolution!r}", line=line, turn_id=turn_id))
            else:
                resolved_blocks.add(target)
        elif kind == "converged":
            converged = record
            ready_by = record.get("ready_by")
            implementation_scope = record.get("implementation_scope")
            if not isinstance(ready_by, list):
                findings.append(finding("ERROR", "ready_by_missing", "converged requires ready_by list", line=line, turn_id=turn_id))
            else:
                ready_set = {str(item) for item in ready_by}
                if "codex" not in ready_set:
                    findings.append(finding("ERROR", "ready_by_codex_missing", "converged requires codex readiness", line=line, turn_id=turn_id))
                unknown_ready = sorted(item for item in ready_set if item not in PARTICIPANTS)
                if unknown_ready:
                    findings.append(finding("ERROR", "ready_by_unknown", "converged ready_by contains unknown participant(s): " + ", ".join(unknown_ready), line=line, turn_id=turn_id))
                if not any(is_subagent_participant(item) for item in ready_set):
                    findings.append(finding("ERROR", "ready_by_subagent_missing", "converged requires at least one subagent readiness", line=line, turn_id=turn_id))
            if not isinstance(implementation_scope, dict):
                findings.append(finding("ERROR", "implementation_scope_missing", "converged requires implementation_scope object", line=line, turn_id=turn_id))
            else:
                for key in ("allowed_paths", "allowed_actions", "forbidden_actions", "validation"):
                    if not isinstance(implementation_scope.get(key), list):
                        findings.append(finding("ERROR", "implementation_scope_field", f"implementation_scope.{key} must be a list", line=line, turn_id=turn_id))

        if turn_id:
            seen[turn_id] = record

    if start_count != 1:
        findings.append(finding("ERROR", "start_count", f"expected exactly one start record, found {start_count}"))

    open_blocks = [
        str(record.get("turn_id"))
        for record in records
        if record.get("kind") == "critique"
        and record.get("severity") == "block"
        and str(record.get("turn_id") or "") not in resolved_blocks
    ]
    if converged and open_blocks:
        findings.append(
            finding(
                "ERROR",
                "converged_with_open_blocks",
                "cannot converge with unresolved block critiques: " + ", ".join(open_blocks),
                line=int(converged.get("_line") or 0),
                turn_id=str(converged.get("turn_id") or ""),
            )
        )
    return findings, open_blocks, converged


def clean_record(record: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in record.items() if key != "_line"}


def lint(path: Path) -> dict[str, Any]:
    records, parse_findings = load_records(path)
    findings, open_blocks, converged = validate_records(records)
    all_findings = [*parse_findings, *findings]
    return {
        "ok": not any(item["severity"] == "ERROR" for item in all_findings),
        "path": path.as_posix(),
        "records": len(records),
        "open_blocks": open_blocks,
        "converged": bool(converged),
        "implementation_scope": clean_record(converged).get("implementation_scope") if converged else {},
        "findings": all_findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=None)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("path")
    args = parser.parse_args()
    root = Path(args.root).resolve() if args.root else repo_root().resolve()
    path = Path(args.path)
    resolved = path if path.is_absolute() else root / path
    payload = lint(resolved.resolve(strict=False))
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif payload["ok"]:
        print(f"dialogue OK: {payload['records']} record(s), open_blocks={len(payload['open_blocks'])}")
    else:
        print("dialogue findings:")
        for item in payload["findings"]:
            print(f"  {item['severity']} [{item['check']}] {item['detail']}")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

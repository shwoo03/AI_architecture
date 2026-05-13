#!/usr/bin/env python3
"""Check whether the next agent can resume from handoff and runtime ledgers."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass


REQUIRED_HANDOFF_SECTIONS = (
    "Last Updated",
    "Current Task",
    "Last Completed",
    "Validation",
    "Recommended Next Step",
    "Open Questions / Blockers",
    "Resume Prompt",
)
TIMESTAMP_SKEW_SECONDS = 300


@dataclass
class Finding:
    severity: str
    check: str
    detail: str


@dataclass
class ReadinessResult:
    root: str
    summary: dict[str, int]
    latest: dict[str, object]
    findings: list[dict[str, object]]


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def parse_utc_ts(value: object) -> Optional[datetime]:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    try:
        if text.endswith("Z"):
            parsed = datetime.fromisoformat(text[:-1] + "+00:00")
        else:
            parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def format_ts(value: Optional[datetime]) -> str:
    if value is None:
        return ""
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_jsonl(path: Path, root: Path, logical_name: str) -> tuple[list[dict[str, Any]], list[Finding]]:
    if not path.exists():
        return [], []
    records: list[dict[str, Any]] = []
    findings: list[Finding] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            value = json.loads(stripped)
        except json.JSONDecodeError as exc:
            findings.append(
                Finding(
                    "ERROR",
                    f"{logical_name}_parse",
                    f"{path.relative_to(root).as_posix()}:{line_no} invalid JSON: {exc}",
                )
            )
            continue
        if not isinstance(value, dict):
            findings.append(
                Finding(
                    "ERROR",
                    f"{logical_name}_parse",
                    f"{path.relative_to(root).as_posix()}:{line_no} JSONL record must be an object",
                )
            )
            continue
        records.append(value)
    return records, findings


def parse_handoff(root: Path, findings: list[Finding]) -> tuple[Optional[datetime], dict[str, object]]:
    path = root / "runtime" / "state" / "session-handoff.md"
    latest: dict[str, object] = {"path": path.relative_to(root).as_posix(), "ts": ""}
    if not path.exists():
        findings.append(Finding("ERROR", "handoff_missing", "runtime/state/session-handoff.md missing"))
        return None, latest
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    sections = {
        match.group(1).strip(): match.start()
        for match in re.finditer(r"^##\s+(.+?)\s*$", text, flags=re.MULTILINE)
    }
    latest["sections"] = sorted(sections)
    for section in REQUIRED_HANDOFF_SECTIONS:
        if section not in sections:
            findings.append(Finding("ERROR", "handoff_section_missing", f"handoff missing section `{section}`"))
    match = re.search(r"^##\s+Last Updated\s*\n+([^\n]+)", text, flags=re.MULTILINE)
    if not match:
        findings.append(Finding("ERROR", "handoff_timestamp_missing", "handoff Last Updated value missing"))
        return None, latest
    raw_ts = match.group(1).strip()
    latest["ts"] = raw_ts
    parsed = parse_utc_ts(raw_ts)
    if parsed is None or not raw_ts.endswith("Z"):
        findings.append(Finding("ERROR", "handoff_timestamp_invalid", f"handoff Last Updated is not UTC ISO timestamp: {raw_ts}"))
        return None, latest
    return parsed, latest


def latest_timestamp(records: list[dict[str, Any]]) -> Optional[datetime]:
    for record in reversed(records):
        parsed = parse_utc_ts(record.get("ts"))
        if parsed is not None:
            return parsed
    return None


def latest_record(records: list[dict[str, Any]]) -> dict[str, Any] | None:
    return records[-1] if records else None


def check_latest_completion_outcome(records: list[dict[str, Any]], findings: list[Finding]) -> None:
    latest = latest_record(records)
    if latest is None:
        return
    outcome = str(latest.get("outcome") or "").strip()
    disposition = str(latest.get("disposition") or "").strip()
    if disposition and disposition != "complete":
        findings.append(
            Finding(
                "WARN",
                "completion_evidence_not_complete",
                f"latest completion evidence disposition is {disposition}; resume with next_action/residual_risk review",
            )
        )
    if outcome and outcome != "genuine_success":
        findings.append(
            Finding(
                "WARN",
                "completion_evidence_not_genuine_success",
                f"latest completion evidence outcome is {outcome}; resume with residual risk review",
            )
        )
    if disposition == "complete" and outcome != "genuine_success":
        findings.append(Finding("ERROR", "completion_disposition_conflict", "complete disposition requires genuine_success outcome"))


def check_latest_checkpoint(records: list[dict[str, Any]], findings: list[Finding]) -> None:
    latest = latest_record(records)
    if latest is None:
        return
    approval_state = str(latest.get("approval_state") or "not_required").strip()
    if approval_state == "pending":
        findings.append(Finding("WARN", "checkpoint_approval_pending", "latest checkpoint is waiting for user approval"))
    side_effects = latest.get("side_effects")
    if isinstance(side_effects, list) and side_effects and not str(latest.get("resume_from") or "").strip():
        findings.append(Finding("WARN", "checkpoint_resume_from_missing", "latest checkpoint has side_effects but no resume_from"))


def compare_not_newer(
    handoff_ts: Optional[datetime],
    other_ts: Optional[datetime],
    name: str,
    findings: list[Finding],
) -> None:
    if handoff_ts is None or other_ts is None:
        return
    if other_ts > handoff_ts:
        findings.append(
            Finding(
                "WARN",
                f"{name}_newer_than_handoff",
                f"{name} has newer timestamp {format_ts(other_ts)} than handoff {format_ts(handoff_ts)}",
            )
        )


def check_handoff_event_alignment(
    handoff_ts: Optional[datetime],
    activity_records: list[dict[str, Any]],
    findings: list[Finding],
) -> Optional[datetime]:
    handoff_events = [record for record in activity_records if record.get("action") == "handoff_saved"]
    if not handoff_events:
        findings.append(Finding("WARN", "handoff_event_missing", "activity log has no handoff_saved event"))
        return None
    event_ts = latest_timestamp(handoff_events)
    if handoff_ts is None or event_ts is None:
        return event_ts
    delta = abs((handoff_ts - event_ts).total_seconds())
    if delta > TIMESTAMP_SKEW_SECONDS:
        findings.append(
            Finding(
                "WARN",
                "handoff_event_timestamp_skew",
                f"latest handoff_saved event {format_ts(event_ts)} is more than {TIMESTAMP_SKEW_SECONDS}s from handoff {format_ts(handoff_ts)}",
            )
        )
    return event_ts


def check_progress_state(root: Path, handoff_ts: Optional[datetime], evidence_ts: Optional[datetime], findings: list[Finding]) -> dict[str, object]:
    path = root / "state" / "progress.md"
    latest: dict[str, object] = {"path": "state/progress.md", "exists": path.exists(), "mtime": "", "placeholder": False}
    if not path.exists():
        return latest
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    placeholder = "(부트스트랩 완료 후 첫 plan에서 채워짐)" in text or "(project-scaffolder가 채움)" in text
    latest["placeholder"] = placeholder
    try:
        mtime = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
    except OSError:
        return latest
    latest["mtime"] = format_ts(mtime)
    if placeholder and (handoff_ts is not None or evidence_ts is not None):
        findings.append(Finding("WARN", "progress_placeholder", "state/progress.md still contains bootstrap placeholders despite runtime handoff/evidence"))
    if handoff_ts is not None and mtime < handoff_ts:
        findings.append(Finding("WARN", "progress_older_than_handoff", f"state/progress.md mtime {format_ts(mtime)} is older than handoff {format_ts(handoff_ts)}"))
    return latest


def run_check(root: Path) -> ReadinessResult:
    findings: list[Finding] = []
    handoff_ts, handoff_latest = parse_handoff(root, findings)
    activity_records, activity_findings = read_jsonl(root / "runtime" / "activity-log.jsonl", root, "activity_log")
    evidence_records, evidence_findings = read_jsonl(root / "runtime" / "completion-evidence.jsonl", root, "completion_evidence")
    checkpoint_records, checkpoint_findings = read_jsonl(root / "runtime" / "checkpoints.jsonl", root, "checkpoint")
    findings.extend(activity_findings)
    findings.extend(evidence_findings)
    findings.extend(checkpoint_findings)

    activity_ts = latest_timestamp(activity_records)
    evidence_ts = latest_timestamp(evidence_records)
    checkpoint_ts = latest_timestamp(checkpoint_records)
    check_latest_completion_outcome(evidence_records, findings)
    check_latest_checkpoint(checkpoint_records, findings)
    handoff_event_ts = check_handoff_event_alignment(handoff_ts, activity_records, findings)
    compare_not_newer(handoff_ts, activity_ts, "activity_log", findings)
    compare_not_newer(handoff_ts, evidence_ts, "completion_evidence", findings)
    compare_not_newer(handoff_ts, checkpoint_ts, "checkpoint", findings)
    progress_latest = check_progress_state(root, handoff_ts, evidence_ts, findings)

    latest = {
        "handoff": handoff_latest,
        "activity_log": {"records": len(activity_records), "latest_ts": format_ts(activity_ts)},
        "handoff_saved_event": {"latest_ts": format_ts(handoff_event_ts)},
        "completion_evidence": {
            "records": len(evidence_records),
            "latest_ts": format_ts(evidence_ts),
            "latest_outcome": latest_record(evidence_records).get("outcome") if latest_record(evidence_records) else None,
            "latest_disposition": latest_record(evidence_records).get("disposition") if latest_record(evidence_records) else None,
        },
        "checkpoint": {
            "records": len(checkpoint_records),
            "latest_ts": format_ts(checkpoint_ts),
            "latest_id": latest_record(checkpoint_records).get("id") if latest_record(checkpoint_records) else None,
            "latest_approval_state": latest_record(checkpoint_records).get("approval_state") if latest_record(checkpoint_records) else None,
        },
        "progress": progress_latest,
    }
    summary = dict(Counter(finding.severity for finding in findings))
    for severity in ("ERROR", "WARN", "INFO"):
        summary.setdefault(severity, 0)
    return ReadinessResult(
        root=str(root),
        summary=summary,
        latest=latest,
        findings=[asdict(finding) for finding in findings],
    )


def render_text(result: ReadinessResult) -> str:
    lines = [
        "Resume Readiness",
        f"root: {result.root}",
        "summary: "
        f"error={result.summary.get('ERROR', 0)}, "
        f"warn={result.summary.get('WARN', 0)}, "
        f"info={result.summary.get('INFO', 0)}",
    ]
    for finding in result.findings:
        lines.append(f"  {finding['severity']:<5} [{finding['check']}] {finding['detail']}")
    if not result.findings:
        lines.append("  OK next agent can resume from current handoff and ledgers")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=None, help="Project root (default: this skeleton root).")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--strict", action="store_true", help="Fail on warnings as well as errors.")
    args = parser.parse_args()

    root = Path(args.root).resolve() if args.root else repo_root().resolve()
    if not root.is_dir():
        print(f"root not a directory: {root}", file=sys.stderr)
        return 2
    result = run_check(root)
    if args.format == "json":
        print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    else:
        print(render_text(result))
    has_error = result.summary.get("ERROR", 0) > 0
    has_warn = result.summary.get("WARN", 0) > 0
    return 1 if has_error or (args.strict and has_warn) else 0


if __name__ == "__main__":
    raise SystemExit(main())

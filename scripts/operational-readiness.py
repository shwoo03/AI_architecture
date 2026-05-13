#!/usr/bin/env python3
"""Report whether the skeleton has observable, governed operating surfaces."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass


@dataclass
class Finding:
    severity: str
    check: str
    detail: str


@dataclass
class ReadinessResult:
    root: str
    harnesses: list[dict[str, object]]
    references: list[dict[str, object]]
    observability: dict[str, object]
    summary: dict[str, int]
    findings: list[dict[str, object]]


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def read_jsonl(path: Path, root: Path, logical_name: str, findings: list[Finding]) -> list[dict[str, Any]]:
    if not path.exists():
        findings.append(Finding("WARN", f"{logical_name}_missing", f"{path.relative_to(root).as_posix()} missing"))
        return []
    records: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8-sig", errors="replace").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            findings.append(Finding("ERROR", f"{logical_name}_parse", f"{path.relative_to(root).as_posix()}:{line_no} invalid JSON: {exc}"))
            continue
        if not isinstance(payload, dict):
            findings.append(Finding("ERROR", f"{logical_name}_parse", f"{path.relative_to(root).as_posix()}:{line_no} JSONL record must be an object"))
            continue
        records.append(payload)
    return records


def run_verify_parity(root: Path) -> tuple[bool, str]:
    script = root / "scripts" / "verify-parity.py"
    if not script.exists():
        return False, "scripts/verify-parity.py missing"
    try:
        result = subprocess.run(
            [sys.executable, str(script), "--root", str(root)],
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60,
        )
    except subprocess.SubprocessError as exc:
        return False, f"verify-parity failed to run: {exc}"
    detail = (result.stdout or result.stderr or "").strip().splitlines()
    return result.returncode == 0, detail[0] if detail else f"exit {result.returncode}"


def harness_status(root: Path, findings: list[Finding]) -> list[dict[str, object]]:
    parity_ok, parity_detail = run_verify_parity(root)
    harnesses = [
        {
            "name": "codex",
            "status": "native" if parity_ok and all((root / rel).exists() for rel in (".codex/skills", ".codex/agents", ".codex/rules", ".codex/mcp.json")) else "generated",
            "evidence": [".codex/skills", ".codex/agents", ".codex/rules", ".codex/mcp.json", "scripts/verify-parity.py"],
            "parity_ok": parity_ok,
        },
        {
            "name": "claude",
            "status": "generated" if parity_ok and all((root / rel).exists() for rel in (".claude/skills", ".claude/agents", ".claude/rules", ".mcp.json", "CLAUDE.md")) else "adapter-backed",
            "evidence": [".claude/skills", ".claude/agents", ".claude/rules", ".mcp.json", "CLAUDE.md", "scripts/verify-parity.py"],
            "parity_ok": parity_ok,
        },
    ]
    if not parity_ok:
        findings.append(Finding("ERROR", "harness_parity", parity_detail))
    if (root / "references.yaml").exists() and "opencode" in (root / "references.yaml").read_text(encoding="utf-8", errors="replace"):
        harnesses.append(
            {
                "name": "opencode",
                "status": "reference-only",
                "evidence": ["references.yaml"],
                "parity_ok": None,
            }
        )
    return harnesses


def parse_references(root: Path) -> list[dict[str, str]]:
    path = root / "references.yaml"
    if not path.exists():
        return []
    repos: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = raw.strip()
        if stripped.startswith("- name:"):
            if current:
                repos.append(current)
            current = {"name": stripped.split(":", 1)[1].strip().strip('"')}
            continue
        if current is not None and ":" in stripped:
            key, value = stripped.split(":", 1)
            current[key.strip()] = value.strip().strip('"')
    if current:
        repos.append(current)
    return repos


def markdown_files_text(root: Path, directory: Path) -> list[tuple[Path, str]]:
    if not directory.is_dir():
        return []
    return [
        (path, path.read_text(encoding="utf-8", errors="replace"))
        for path in sorted(directory.glob("*.md"))
        if path.name not in {"README.md", "_template.md"} and not path.name.startswith(".")
    ]


def reference_status(root: Path, findings: list[Finding]) -> list[dict[str, object]]:
    candidates = markdown_files_text(root, root / "research" / "reference-candidates")
    proposals = markdown_files_text(root, root / "runtime" / "proposals" / "reference-adoption")
    refs: list[dict[str, object]] = []
    for repo in parse_references(root):
        name = repo.get("name", "")
        local_path = repo.get("local_path", "")
        resolved = (root / local_path).resolve(strict=False) if local_path else None
        has_local = bool(resolved and (resolved / ".git").exists())
        matching_candidates = [path.relative_to(root).as_posix() for path, text in candidates if name and name in text]
        matching_proposals = [path.relative_to(root).as_posix() for path, text in proposals if name and name in text]
        if matching_proposals:
            status = "proposal-ready"
        elif matching_candidates:
            status = "reviewable"
        elif has_local:
            status = "tracked"
        else:
            status = "blocked"
            findings.append(Finding("WARN", "reference_not_reviewable", f"{name} has no local clone or candidate card"))
        refs.append(
            {
                "name": name,
                "status": status,
                "local_path": local_path,
                "local_clone_present": has_local,
                "candidate_cards": matching_candidates,
                "proposals": matching_proposals,
            }
        )
    if not refs:
        findings.append(Finding("WARN", "references_missing", "references.yaml has no repo entries"))
    return refs


def observability_status(root: Path, findings: list[Finding]) -> dict[str, object]:
    activity = read_jsonl(root / "runtime" / "activity-log.jsonl", root, "activity_log", findings)
    evidence = read_jsonl(root / "runtime" / "completion-evidence.jsonl", root, "completion_evidence", findings)
    tasks = read_jsonl(root / "runtime" / "reference-tasks.jsonl", root, "reference_tasks", findings)
    handoff = root / "runtime" / "state" / "session-handoff.md"
    if not handoff.exists():
        findings.append(Finding("ERROR", "handoff_missing", "runtime/state/session-handoff.md missing"))
    handoff_events = [record for record in activity if record.get("action") == "handoff_saved"]
    if not handoff_events:
        findings.append(Finding("WARN", "handoff_event_missing", "activity log has no handoff_saved event"))
    return {
        "activity_records": len(activity),
        "completion_evidence_records": len(evidence),
        "reference_task_records": len(tasks),
        "handoff_exists": handoff.exists(),
        "handoff_saved_events": len(handoff_events),
    }


def run_check(root: Path) -> ReadinessResult:
    findings: list[Finding] = []
    harnesses = harness_status(root, findings)
    references = reference_status(root, findings)
    observability = observability_status(root, findings)
    summary = dict(Counter(finding.severity for finding in findings))
    for severity in ("ERROR", "WARN", "INFO"):
        summary.setdefault(severity, 0)
    return ReadinessResult(
        root=str(root),
        harnesses=harnesses,
        references=references,
        observability=observability,
        summary=summary,
        findings=[asdict(finding) for finding in findings],
    )


def render_text(result: ReadinessResult) -> str:
    lines = [
        "Operational Readiness",
        f"root: {result.root}",
        f"summary: error={result.summary.get('ERROR', 0)}, warn={result.summary.get('WARN', 0)}, info={result.summary.get('INFO', 0)}",
        "Harnesses:",
    ]
    for harness in result.harnesses:
        lines.append(f"  - {harness['name']}: {harness['status']}")
    lines.append("References:")
    for reference in result.references:
        lines.append(f"  - {reference['name']}: {reference['status']}")
    lines.append("Observability:")
    for key, value in result.observability.items():
        lines.append(f"  - {key}: {value}")
    for finding in result.findings:
        lines.append(f"  {finding['severity']:<5} [{finding['check']}] {finding['detail']}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=None)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--strict", action="store_true")
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

#!/usr/bin/env python3
"""Validate structured implementation plan documents."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass


REQUIRED_HEADINGS = [
    "## Summary",
    "## Assumptions",
    "## Out of Scope",
    "## Implementation Steps",
    "## Definition of Done",
    "## Rollback Plan",
    "## Stop Conditions",
    "## Validation",
]

CLOSEOUT_COMMANDS = (
    "python3 scripts/agent-flow.py closeout",
    "python scripts/agent-flow.py closeout",
)
VALIDATION_COMMAND_RE = r"(?m)^\s*(?:[-*]\s*)?`?(?:PYTHONDONTWRITEBYTECODE=1\s+)?(?:python3|python)\s+scripts/[A-Za-z0-9_./-]+\.py\b"


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def plan_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for rel in ("plans/active", "plans/done", "plans/failed"):
        directory = root / rel
        if directory.is_dir():
            files.extend(path for path in directory.glob("*.md") if not path.name.startswith("_"))
    return sorted(files)


def is_legacy_done_plan(root: Path, path: Path, text: str) -> bool:
    try:
        rel = path.relative_to(root).as_posix()
    except ValueError:
        return False
    if not rel.startswith("plans/done/"):
        return False
    if text.lstrip().startswith("# Plan ") or "| seq |" in text:
        return True
    if not all(heading in text for heading in REQUIRED_HEADINGS):
        return False
    if any(command in text for command in CLOSEOUT_COMMANDS):
        return False
    validation_index = text.find("## Validation")
    if validation_index < 0:
        return False
    validation_block = text[validation_index:]
    return bool(re.search(VALIDATION_COMMAND_RE, validation_block))


def validate_file(root: Path, path: Path, *, allow_legacy_done: bool = False) -> tuple[list[str], bool]:
    text = path.read_text(encoding="utf-8", errors="replace")
    rel = path.relative_to(root).as_posix()
    if allow_legacy_done and is_legacy_done_plan(root, path, text):
        return [], True
    findings: list[str] = []
    for heading in REQUIRED_HEADINGS:
        if heading not in text:
            findings.append(f"{rel} missing heading `{heading}`")
    if "python3 scripts/agent-flow.py closeout" not in text and "python scripts/agent-flow.py closeout" not in text:
        findings.append(f"{rel} missing closeout validation command")
    return findings, False


def run_check(root: Path, *, allow_legacy_done: bool = False) -> dict[str, object]:
    findings: list[str] = []
    legacy_done_skipped = 0
    files = plan_files(root)
    for path in files:
        file_findings, skipped = validate_file(root, path, allow_legacy_done=allow_legacy_done)
        findings.extend(file_findings)
        if skipped:
            legacy_done_skipped += 1
    return {"ok": not findings, "plans": len(files), "legacy_done_skipped": legacy_done_skipped, "findings": findings}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=None)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument(
        "--allow-legacy-done",
        action="store_true",
        help="Do not fail historical plans/done records that predate the structured plan contract.",
    )
    args = parser.parse_args()
    root = Path(args.root).resolve() if args.root else repo_root().resolve()
    if not root.is_dir():
        print(f"root not a directory: {root}", file=sys.stderr)
        return 2
    payload = run_check(root, allow_legacy_done=args.allow_legacy_done)
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif payload["findings"]:
        print("plan validation findings:")
        for finding in payload["findings"]:
            print(f"  ERROR {finding}")
    else:
        suffix = f", {payload['legacy_done_skipped']} legacy done plan(s) skipped" if payload.get("legacy_done_skipped") else ""
        print(f"plans OK: {payload['plans']} plan(s) checked{suffix}")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

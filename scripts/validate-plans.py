#!/usr/bin/env python3
"""Validate structured implementation plan documents."""

from __future__ import annotations

import argparse
import json
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


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def plan_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for rel in ("plans/active", "plans/done", "plans/failed"):
        directory = root / rel
        if directory.is_dir():
            files.extend(path for path in directory.glob("*.md") if not path.name.startswith("_"))
    return sorted(files)


def validate_file(root: Path, path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    rel = path.relative_to(root).as_posix()
    findings: list[str] = []
    for heading in REQUIRED_HEADINGS:
        if heading not in text:
            findings.append(f"{rel} missing heading `{heading}`")
    if "python3 scripts/agent-flow.py closeout" not in text and "python scripts/agent-flow.py closeout" not in text:
        findings.append(f"{rel} missing closeout validation command")
    return findings


def run_check(root: Path) -> dict[str, object]:
    findings: list[str] = []
    files = plan_files(root)
    for path in files:
        findings.extend(validate_file(root, path))
    return {"ok": not findings, "plans": len(files), "findings": findings}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=None)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()
    root = Path(args.root).resolve() if args.root else repo_root().resolve()
    if not root.is_dir():
        print(f"root not a directory: {root}", file=sys.stderr)
        return 2
    payload = run_check(root)
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif payload["findings"]:
        print("plan validation findings:")
        for finding in payload["findings"]:
            print(f"  ERROR {finding}")
    else:
        print(f"plans OK: {payload['plans']} plan(s) checked")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

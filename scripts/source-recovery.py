#!/usr/bin/env python3
"""Generate source-scoped recovery plans without mutating files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


DO_NOT_RUN = ["git reset --hard", "git checkout -- <path>", "rm -rf <path>", "automatic rollback without source review"]


def normalize_changed_path(root: Path, raw: str) -> str:
    value = raw.strip()
    if not value:
        raise ValueError("changed path cannot be empty")
    path = Path(value)
    candidate = path if path.is_absolute() else root / path
    try:
        return candidate.resolve(strict=False).relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError(f"changed path escapes repository root: {raw}") from exc


def classify(path: str) -> str:
    first = path.split("/", 1)[0]
    if first in {"scripts", "tests"}:
        return "scripts"
    if first in {"runtime", "state"}:
        return "runtime"
    if first in {"docs", "plans", "rules", "skills", "agents"}:
        return "docs"
    if first in {"research", "references.yaml", "mcp"}:
        return "reference"
    if path == ".":
        return "all"
    return "project"


def commands_for_scope(scope: str, failure: str) -> tuple[list[str], list[str]]:
    if scope == "scripts":
        return (
            [
                "python3 -m unittest discover -s tests -v",
                "python3 scripts/lsp-diagnostics.py --root . --format json",
                "python3 scripts/quality-gate.py --skip-tests --format json",
            ],
            ["Review touched scripts/tests before broad rewrites.", "Inspect the failing quality-gate payload first."],
        )
    if scope == "runtime":
        return (
            [
                "python3 scripts/completion-evidence.py check --root . --format json",
                "python3 scripts/resume-readiness.py --root . --strict --format json",
                "python3 scripts/session-snapshot.py write --root . --format json",
            ],
            ["Regenerate runtime handoff/snapshot only after the source change is correct.", "Check handoff, progress, and activity-log consistency."],
        )
    if scope == "docs":
        return (
            ["python3 scripts/verify-skeleton.py", "python3 scripts/validate-plans.py --root . --format json", "python3 scripts/quality-gate.py --skip-tests --format json"],
            ["Check for documentation contract drift before editing code."],
        )
    if scope == "reference":
        return (
            [
                "python3 scripts/reference-wiki.py check --root . --format json",
                "python3 scripts/reference-copy-ledger.py check --root . --format json",
                "python3 scripts/security-scan.py --strict --format json",
            ],
            ["Confirm copied-source boundaries and licensing metadata before changing reference files."],
        )
    return (
        ["python3 scripts/verify-skeleton.py", "python3 scripts/quality-gate.py --skip-tests --format json", "python3 scripts/resume-readiness.py --strict --format json"],
        [f"Start from the failing command family ({failure}) and narrow the touched path list.", "Prefer a small forward fix over broad rollback."],
    )


def build_plan(root: Path, changed_paths: list[str], failure: str) -> dict[str, Any]:
    normalized = [normalize_changed_path(root, path) for path in changed_paths]
    grouped: dict[str, list[str]] = {}
    for path in normalized:
        grouped.setdefault(classify(path), []).append(path)
    scopes: list[dict[str, Any]] = []
    for scope, paths in sorted(grouped.items()):
        commands, actions = commands_for_scope(scope, failure)
        scopes.append(
            {
                "scope": scope,
                "paths": paths,
                "summary": f"Recover {failure} by rechecking the {scope} source boundary only.",
                "recommended_commands": commands,
                "manual_actions": actions,
                "do_not_run": DO_NOT_RUN,
            }
        )
    return {"ok": True, "mutates_files": False, "root": str(root), "failure": failure, "changed_paths": normalized, "scopes": scopes}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--changed-path", action="append", required=True)
    parser.add_argument("--failure", required=True)
    parser.add_argument("--format", choices=["text", "json"], default="text")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"error: root is not a directory: {root}", file=sys.stderr)
        return 2
    try:
        payload = build_plan(root, args.changed_path, args.failure)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"failure: {payload['failure']}")
        print("mutates_files: false")
        for scope in payload["scopes"]:
            print(f"[{scope['scope']}] {', '.join(scope['paths'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

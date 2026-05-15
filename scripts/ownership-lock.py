#!/usr/bin/env python3
"""Generate and check the ownership classification lock."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import lib_ownership


def default_root() -> Path:
    return Path(__file__).resolve().parent.parent


def payload_for_changes(changes: list[lib_ownership.LockChange]) -> dict[str, object]:
    return {
        "ok": not any(change.kind == "classification_drift" for change in changes),
        "summary": {
            "lock_addition": sum(1 for change in changes if change.kind == "lock_addition"),
            "lock_removal": sum(1 for change in changes if change.kind == "lock_removal"),
            "classification_drift": sum(1 for change in changes if change.kind == "classification_drift"),
        },
        "changes": [change.__dict__ for change in changes],
    }


def load_config(root: Path) -> dict[str, object]:
    return lib_ownership.load_ownership_config(root / "config" / "ownership.yaml")


def cmd_write(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    config = load_config(root)
    report = lib_ownership.classify_self(root, config)
    payload = {
        "ok": not report.unknown,
        "total": report.total,
        "unknown": report.unknown,
        "lock_path": "runtime/ownership-classification.lock.json",
    }
    if report.unknown:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1
    lib_ownership.write_lock(root / "runtime" / "ownership-classification.lock.json", report)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    config = load_config(root)
    lock_path = root / "runtime" / "ownership-classification.lock.json"
    if not lock_path.is_file():
        print(json.dumps({"ok": False, "error": "ownership lock missing", "lock_path": str(lock_path)}, indent=2, sort_keys=True))
        return 1
    report = lib_ownership.classify_self(root, config)
    if report.unknown:
        print(json.dumps({"ok": False, "unknown": report.unknown}, indent=2, sort_keys=True))
        return 1
    payload = payload_for_changes(lib_ownership.compare_lock(report.classifications, lib_ownership.load_lock(lock_path)))
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["ok"] else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(default_root()), help="Project root.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("write", help="Regenerate runtime/ownership-classification.lock.json.")
    sub.add_parser("check", help="Check current classification against the lock.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "write":
        return cmd_write(args)
    if args.command == "check":
        return cmd_check(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

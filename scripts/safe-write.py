#!/usr/bin/env python3
"""Check or apply a safe local text write inside the project boundary."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from lib_safe_write import SafeWriteError, atomic_write_text, resolve_write_target


try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=None)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check")
    check.add_argument("--path", required=True)
    write = sub.add_parser("write")
    write.add_argument("--path", required=True)
    write.add_argument("--text", required=True)
    write.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve() if args.root else repo_root().resolve()
    if not root.is_dir():
        print(f"root not a directory: {root}", file=sys.stderr)
        return 2
    try:
        target = resolve_write_target(root, args.path)
        applied = False
        if args.command == "write" and args.apply:
            atomic_write_text(root, args.path, args.text)
            applied = True
    except SafeWriteError as exc:
        payload = {"ok": False, "path": args.path, "error": str(exc), "applied": False}
        if args.format == "json":
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"deny ({exc})")
        return 1
    payload = {"ok": True, "path": target.relative_to(root).as_posix(), "applied": applied}
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"OK {payload['path']}" + (" written" if applied else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

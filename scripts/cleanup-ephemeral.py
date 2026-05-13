#!/usr/bin/env python3
"""Preview or remove safe ephemeral Python cache directories."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path


try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass


DEFAULT_TARGETS = ("scripts", "tests", "agents", "rules", "docs")
SKIP_PARTS = {".git", "node_modules", ".venv", "venv", "dist", "build"}


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def resolve_under_root(root: Path, value: str) -> Path:
    path = Path(value)
    resolved = path.resolve(strict=False) if path.is_absolute() else (root / path).resolve(strict=False)
    resolved.relative_to(root.resolve(strict=False))
    return resolved


def safe_pycache_dir(root: Path, path: Path) -> bool:
    if path.name != "__pycache__" or not path.is_dir() or path.is_symlink():
        return False
    try:
        rel = path.resolve(strict=False).relative_to(root.resolve(strict=False))
    except ValueError:
        return False
    return not any(part in SKIP_PARTS for part in rel.parts)


def collect(root: Path, targets: list[str]) -> list[Path]:
    matches: list[Path] = []
    for target in targets or list(DEFAULT_TARGETS):
        base = resolve_under_root(root, target)
        if not base.exists():
            continue
        for path in base.rglob("__pycache__"):
            if safe_pycache_dir(root, path):
                matches.append(path)
    return sorted(set(matches))


def rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=None)
    parser.add_argument("--target", action="append", default=[], help="Directory to scan; repeatable. Defaults to common source dirs.")
    parser.add_argument("--apply", action="store_true", help="Delete matched __pycache__ directories. Default is preview/check only.")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()
    root = Path(args.root).resolve() if args.root else repo_root().resolve()
    if not root.is_dir():
        print(f"root not a directory: {root}", file=sys.stderr)
        return 2
    try:
        matches = collect(root, args.target)
    except ValueError as exc:
        print(f"target must stay inside project root: {exc}", file=sys.stderr)
        return 2
    removed: list[str] = []
    errors: list[str] = []
    if args.apply:
        for path in matches:
            try:
                shutil.rmtree(path)
                removed.append(rel(root, path))
            except OSError as exc:
                errors.append(f"{rel(root, path)}: {exc}")
    payload = {
        "ok": not errors,
        "apply": args.apply,
        "matches": [rel(root, path) for path in matches],
        "removed": removed,
        "errors": errors,
    }
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        items = removed if args.apply else payload["matches"]
        print(f"cleanup-ephemeral {'removed' if args.apply else 'matched'}: {len(items)}")
        for item in items:
            print(f"  {item}")
        for item in errors:
            print(f"  ERROR {item}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

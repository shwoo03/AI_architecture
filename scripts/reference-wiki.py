#!/usr/bin/env python3
"""Check the local reference-wiki source/synthesis contract."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from lib_safe_write import atomic_write_text


try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def raw_sources(root: Path) -> list[Path]:
    raw = root / "docs" / "reference-wiki" / "raw"
    if not raw.is_dir():
        return []
    return sorted(path for path in raw.iterdir() if path.is_file() and path.name != ".gitkeep")


def ensure_table(text: str) -> str:
    if "| source pointer | status | pointer |" in text:
        return text.rstrip() + "\n"
    if text.strip():
        return text.rstrip() + "\n\n| source pointer | status | pointer |\n| --- | --- | --- |\n"
    return "# Reference Wiki Index\n\n| source pointer | status | pointer |\n| --- | --- | --- |\n"


def run_sync(root: Path) -> dict[str, object]:
    base = root / "docs" / "reference-wiki"
    index = base / "wiki" / "index.md"
    log = base / "wiki" / "log.md"
    index_text = index.read_text(encoding="utf-8", errors="replace") if index.exists() else ""
    updated = ensure_table(index_text)
    added: list[str] = []
    for source in raw_sources(root):
        rel = source.relative_to(root).as_posix()
        if rel in updated:
            continue
        pointer = f"docs/reference-wiki/wiki/{source.stem}.md"
        updated += f"| {rel} | raw | {pointer} |\n"
        added.append(rel)
    if added:
        atomic_write_text(root, index.relative_to(root).as_posix(), updated)
        log_text = log.read_text(encoding="utf-8", errors="replace") if log.exists() else "# Reference Wiki Log\n"
        log_text = log_text.rstrip() + "\n\n## 2026-05-13\n"
        for rel in added:
            log_text += f"- Indexed raw source `{rel}`.\n"
        atomic_write_text(root, log.relative_to(root).as_posix(), log_text)
    return {"ok": True, "path": "docs/reference-wiki", "added": added}


def run_check(root: Path) -> dict[str, object]:
    base = root / "docs" / "reference-wiki"
    required = [
        base / "README.md",
        base / "raw",
        base / "wiki",
        base / "wiki" / "index.md",
        base / "wiki" / "log.md",
    ]
    findings: list[str] = []
    for path in required:
        if not path.exists():
            findings.append(f"missing {path.relative_to(root).as_posix()}")
    index = base / "wiki" / "index.md"
    if index.exists():
        text = index.read_text(encoding="utf-8", errors="replace")
        for phrase in ("source", "status", "pointer"):
            if phrase not in text.lower():
                findings.append(f"{index.relative_to(root).as_posix()} missing `{phrase}` column/term")
    log = base / "wiki" / "log.md"
    if log.exists() and "2026-" not in log.read_text(encoding="utf-8", errors="replace"):
        findings.append(f"{log.relative_to(root).as_posix()} has no dated entries")
    return {"ok": not findings, "path": "docs/reference-wiki", "findings": findings}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=None)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--sync", action="store_true", help="Index raw reference files into wiki/index.md and wiki/log.md.")
    args = parser.parse_args()
    root = Path(args.root).resolve() if args.root else repo_root().resolve()
    if not root.is_dir():
        print(f"root not a directory: {root}", file=sys.stderr)
        return 2
    payload = run_sync(root) if args.sync else run_check(root)
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif payload["findings"]:
        print("reference-wiki findings:")
        for finding in payload["findings"]:
            print(f"  ERROR {finding}")
    else:
        print("reference-wiki OK")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

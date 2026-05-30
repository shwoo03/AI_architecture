#!/usr/bin/env python3
"""Generate harness adapter instruction files from canonical AGENTS.md."""

from __future__ import annotations

import argparse
from pathlib import Path


HEADER = """# CLAUDE.md

> Generated adapter. Do not edit directly.
>
> Canonical source: `AGENTS.md`
>
> Regenerate with:
>
> ```bash
> python3 tools/scaffold/gen-harness-instructions.py --project . --harness claude
> ```

"""


def generate_claude(project: Path) -> Path:
    source = project / "AGENTS.md"
    if not source.is_file():
        raise SystemExit(f"missing canonical source: {source}")
    target = project / "CLAUDE.md"
    text = source.read_text(encoding="utf-8")
    target.write_text(HEADER + text, encoding="utf-8")
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", default=".", help="Project root containing AGENTS.md")
    parser.add_argument("--harness", choices=("claude",), default="claude")
    args = parser.parse_args()

    project = Path(args.project).resolve()
    if args.harness == "claude":
        target = generate_claude(project)
        print(f"generated {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


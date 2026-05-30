#!/usr/bin/env python3
"""Copy thin-core templates into a target project."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


PROFILE_FILES = {
    "solo-small-project": [
        ("templates/canonical/AGENTS.md", "AGENTS.md"),
        ("templates/canonical/PROJECT_PROFILE.md", "docs/PROJECT_PROFILE.md"),
        ("templates/canonical/HANDOFF.md", "docs/HANDOFF.md"),
        ("templates/canonical/SECURITY.md", "docs/SECURITY.md"),
    ],
    "team-audit-project": [
        ("templates/canonical/AGENTS.md", "AGENTS.md"),
        ("templates/canonical/PROJECT_PROFILE.md", "docs/PROJECT_PROFILE.md"),
        ("templates/canonical/HANDOFF.md", "docs/HANDOFF.md"),
        ("templates/canonical/SECURITY.md", "docs/SECURITY.md"),
        ("templates/canonical/REFERENCES.md", "docs/REFERENCES.md"),
    ],
}


def copy_file(source: Path, target: Path, *, force: bool) -> None:
    if target.exists() and not force:
        print(f"skip existing {target}")
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    print(f"wrote {target}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True)
    parser.add_argument("--profile", choices=sorted(PROFILE_FILES), default="solo-small-project")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    target_root = Path(args.target).expanduser().resolve()
    target_root.mkdir(parents=True, exist_ok=True)

    for src_rel, dst_rel in PROFILE_FILES[args.profile]:
        copy_file(ROOT / src_rel, target_root / dst_rel, force=args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


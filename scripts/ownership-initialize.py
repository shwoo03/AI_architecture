#!/usr/bin/env python3
"""Report-only ownership initialization for an existing target repository."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib_ownership


try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass


@dataclass(frozen=True)
class CandidateGroup:
    pattern: str
    owner: str
    count: int
    examples: list[str]


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def source_config_for_initialize(source: Path) -> dict[str, object]:
    config = copy.deepcopy(lib_ownership.load_ownership_config(source / "config" / "ownership.yaml"))
    config["project_overrides"] = {"rules": []}
    return config


def group_pattern(rel: str) -> str:
    path = Path(rel)
    parent = path.parent
    if str(parent) == ".":
        return rel
    parts = parent.parts[:2]
    return "/".join(parts) + "/**"


def yaml_for_groups(groups: list[CandidateGroup]) -> str:
    if not groups:
        return "project_overrides:\n  rules: []\n"
    lines = ["project_overrides:", "  rules:"]
    for group in groups:
        lines.append(f"    - pattern: {group.pattern}")
        lines.append(f"      owner: {group.owner}")
    return "\n".join(lines) + "\n"


def classify_target(source: Path, target: Path) -> tuple[list[str], list[CandidateGroup], str]:
    config = source_config_for_initialize(source)
    rel_paths = lib_ownership.collect_repo_paths(target)
    buckets: dict[str, list[str]] = {}
    for rel in rel_paths:
        target_file = target / rel
        source_file = source / rel
        if not target_file.is_file():
            continue
        source_exists = source_file.is_file()
        content_equal = source_exists and target_file.read_bytes() == source_file.read_bytes()
        result = lib_ownership.classify_path(
            rel,
            config,
            source_exists=source_exists,
            target_exists=True,
            content_equal=content_equal,
        )
        if result.owner == "skip_generated" or result.system_locked or result.action == "unchanged":
            continue
        if result.owner not in {"unknown", "manual_merge"}:
            continue
        buckets.setdefault(group_pattern(rel), []).append(rel)
    groups = [
        CandidateGroup(pattern=pattern, owner="project_owned", count=len(paths), examples=paths[:5])
        for pattern, paths in sorted(buckets.items())
    ]
    return rel_paths, groups, yaml_for_groups(groups)


def payload_for(source: Path, target: Path) -> tuple[int, dict[str, object]]:
    if not source.is_dir():
        return 2, {"ok": False, "status": "bad_source", "error": f"--source is not a directory: {source}"}
    if not target.is_dir():
        return 2, {"ok": False, "status": "bad_target", "error": f"--target is not a directory: {target}"}

    config_path = target / "config" / "ownership.yaml"
    lock_path = target / "runtime" / "ownership-classification.lock.json"
    if config_path.exists() and lock_path.exists():
        return 1, {
            "ok": False,
            "status": "already_initialized",
            "target": str(target),
            "ownership_config": "config/ownership.yaml",
            "lock": "runtime/ownership-classification.lock.json",
            "draft_yaml": "",
            "next_command": f"python3 scripts/ownership-lock.py --root {target} check",
        }
    if config_path.exists() and not lock_path.exists():
        return 0, {
            "ok": True,
            "status": "lock_missing",
            "target": str(target),
            "ownership_config": "config/ownership.yaml",
            "lock": "",
            "draft_yaml": "",
            "next_command": f"python3 scripts/ownership-lock.py --root {target} write",
        }

    rel_paths, groups, draft = classify_target(source, target)
    return 0, {
        "ok": True,
        "status": "draft",
        "source": str(source),
        "target": str(target),
        "analyzed_paths": len(rel_paths),
        "candidate_paths": sum(group.count for group in groups),
        "grouping": "directory depth up to 2",
        "groups": [asdict(group) for group in groups],
        "draft_yaml": draft,
        "next_command": "Review the draft, create config/ownership.yaml manually, then run ownership-lock.py write.",
    }


def render_text(payload: dict[str, object]) -> str:
    status = str(payload.get("status", "unknown"))
    lines = [f"ownership initialize: {status}"]
    if payload.get("target"):
        lines.append(f"target: {payload['target']}")
    if status == "draft":
        lines.append(f"analyzed_paths: {payload.get('analyzed_paths', 0)}")
        lines.append(f"candidate_paths: {payload.get('candidate_paths', 0)}")
        lines.append("")
        lines.append("project_overrides draft:")
        lines.append("```yaml")
        lines.append(str(payload.get("draft_yaml", "")).rstrip())
        lines.append("```")
        groups = payload.get("groups")
        if isinstance(groups, list) and groups:
            lines.append("")
            lines.append("groups:")
            for item in groups:
                if not isinstance(item, dict):
                    continue
                examples = ", ".join(str(value) for value in item.get("examples", []))
                lines.append(f"- {item.get('pattern')} ({item.get('count')} path(s)): {examples}")
    elif status == "lock_missing":
        lines.append("ownership config exists; no draft emitted.")
        lines.append(f"next: {payload.get('next_command')}")
    elif status == "already_initialized":
        lines.append("ownership config and lock already exist; initialization refused.")
        lines.append(f"next: {payload.get('next_command')}")
    else:
        lines.append(str(payload.get("error", "")))
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default=None, help="Skeleton source root. Defaults to this repository.")
    parser.add_argument("--target", required=True, help="Existing project root to inspect.")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()

    source = Path(args.source).resolve() if args.source else repo_root().resolve()
    target = Path(args.target).resolve()
    exit_code, payload = payload_for(source, target)
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(render_text(payload))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

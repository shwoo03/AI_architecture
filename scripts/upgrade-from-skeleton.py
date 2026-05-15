#!/usr/bin/env python3
"""Plan or apply safe upgrades from this skeleton into existing projects.

Default behavior is a dry-run. Applying with --safe-only only copies files that
are missing in the target. Existing target files with different content are
reported for review and left untouched unless --include-risky is explicitly
used.
"""

from __future__ import annotations

import argparse
import filecmp
import json
import shutil
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib_feature_status import feature_by_doc_path, load_feature_manifest, tiers_for_profile
import lib_ownership


try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass


SKIP_DIR_NAMES = {
    ".git",
    ".claude",
    ".codex",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "venv",
    ".venv",
    "env",
    ".env",
    "dist",
    "build",
    "_meta",
    "tests",
}

SKIP_FILE_NAMES = {".DS_Store", "Thumbs.db"}
SKIP_NAME_PREFIXES = ("tmp-", "scratch-")
SKIP_NAME_CONTAINS = ("-smoke-",)

PROJECT_STATE_EXACT = {
    ".claude/settings.local.json",
    ".claude/settings.json",
    "docs/PROJECT_PROFILE.md",
    "docs/PROJECT_SPEC.md",
    "docs/PROJECT_OPERATING_PLAN.md",
    "knowledge/index.md",
    "knowledge/log.md",
    "knowledge/project-registry.md",
    "knowledge/lint-report.md",
    "runtime/activity-log.jsonl",
    "runtime/agent-runs.jsonl",
    "runtime/checkpoints.jsonl",
    "runtime/completion-evidence.jsonl",
    "runtime/install-state.jsonl",
    "runtime/review-queue.jsonl",
    "runtime/session-snapshot.json",
    "runtime/skill-lifecycle.jsonl",
    "runtime/skill-usage.jsonl",
    "runtime/state/session-handoff.md",
}

SAFE_STATE_SEED_EXACT = {
    "runtime/review-queue.jsonl",
}

PROJECT_STATE_PREFIXES = (
    "docs/CODEMAPS/",
    "plans/active/",
    "plans/done/",
    "plans/failed/",
    "research/reference-candidates/",
    "runtime/archive/",
    "runtime/agent-briefs/",
    "runtime/external-repos/",
    "runtime/schedules/",
    "runtime/validation/",
)

PROJECT_STATE_RUNTIME_PREFIXES = (
    "runtime/proposals/",
)

RUNTIME_TEMPLATE_ALLOWLIST = {
    "runtime/external-repos/README.md",
    "runtime/external-repos/.gitkeep",
    "runtime/proposals/reference-adoption/README.md",
    "runtime/proposals/reference-adoption/_template.md",
}

SAFE_MISSING_EXACT = {
    "config/agent-team.yaml",
    "config/install-profiles.yaml",
    "config/ownership.yaml",
    "config/policy.yaml",
    "config/roles.yaml",
    "docs/AGENT_REGISTRY.md",
    "docs/DOCUMENTATION_STYLE_GUIDE.md",
    "docs/FEATURE_DECISION_GUIDE.md",
    "docs/OPERATING_LOOP.md",
    "docs/RUNTIME_EVENT_SCHEMA.md",
    "docs/SESSION_CONTINUITY.md",
    "docs/SKELETON_UPGRADE.md",
    "docs/WORKFLOW_CATALOG.md",
    "runtime/AGENTS.md",
    "scripts/agent-brief.py",
    "scripts/agent-flow.py",
    "scripts/cleanup-ephemeral.py",
    "scripts/generate-codemaps.py",
    "scripts/knowledge-search.py",
    "scripts/quality-gate.py",
    "scripts/review-queue.py",
    "scripts/resume-readiness.py",
    "scripts/skeleton-doctor.py",
    "scripts/source-recovery.py",
    "scripts/task-closeout.py",
    "scripts/upgrade-from-skeleton.py",
    "scripts/verify-skeleton.py",
    "runtime/review-queue.jsonl",
    "runtime/ownership-classification.lock.json",
}

SAFE_MISSING_PREFIXES = (
    "agents/",
    "codex/agents/",
    "codex/rules/",
    "rules/common/",
    "rules/languages/",
    "schemas/",
    "scripts/hooks/",
    "skills/",
)

CANONICAL_PREFIXES = (
    "agents/",
    "config/",
    "docs/",
    "rules/",
    "schemas/",
    "scripts/",
    "codex/",
    "examples/",
    "skills/",
)

CANONICAL_EXACT = {
    "AGENTS.md",
    "CLAUDE.md",
    "README.md",
    ".editorconfig",
}

SAFE_MISSING_SUFFIXES = (
    ".template.md",
    "_template.md",
    "README.md",
    ".gitkeep",
)

PROFILE_EXCLUDED_PREFIXES = {
    "stable": (
        "scripts/incubating/",
        "docs/design/",
    ),
    "incubating": (),
    "all": (),
}

PROFILE_EXCLUDED_NAME_PARTS = {
    "stable": (
        "incubating",
        "phase-1d",
        "phase-1e",
        "agent-run",
        "agent-brief",
        "delegate",
    ),
    "incubating": (),
    "all": (),
}

PERSONAL_LAYER_PREFIXES = (
    ".agents/",
)

STABLE_FEATURE_PATH_OVERRIDES = {
    "docs/AGENT_REGISTRY.md",
    "docs/RUNTIME_EVENT_SCHEMA.md",
    "docs/WORKFLOW_CATALOG.md",
}


@dataclass
class Action:
    target: str
    path: str
    action: str
    safety: str
    reason: str
    applied: bool = False
    owner: str = ""
    ownership_action: str = ""
    matched_pattern: str = ""
    system_locked: bool = False


def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def rel_posix(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def should_skip_source(
    path: Path,
    source: Path,
    target_roots: list[Path],
    *,
    include_personal_skills: bool,
) -> bool:
    rel = rel_posix(path, source)
    if any(path == target or is_relative_to(path, target) for target in target_roots):
        return True
    if not include_personal_skills and rel.startswith(PERSONAL_LAYER_PREFIXES):
        return True
    if any(part in SKIP_DIR_NAMES for part in path.relative_to(source).parts):
        return True
    if path.name in SKIP_FILE_NAMES:
        return True
    if path.name.startswith(SKIP_NAME_PREFIXES):
        return True
    if any(fragment in path.name for fragment in SKIP_NAME_CONTAINS):
        return True
    if rel.startswith("runtime/.") and rel.endswith(".lock"):
        return True
    if path.is_symlink():
        return True
    if rel in SAFE_STATE_SEED_EXACT:
        return False
    if rel in PROJECT_STATE_EXACT:
        return True
    if rel in RUNTIME_TEMPLATE_ALLOWLIST:
        return False
    if rel.startswith("runtime/state/"):
        return True
    if rel.startswith(PROJECT_STATE_PREFIXES):
        return True
    if rel.startswith(PROJECT_STATE_RUNTIME_PREFIXES):
        return True
    return False


def iter_source_files(
    source: Path,
    target_roots: list[Path],
    *,
    include_personal_skills: bool,
) -> list[Path]:
    files: list[Path] = []
    for path in sorted(source.rglob("*")):
        if should_skip_source(
            path,
            source,
            target_roots,
            include_personal_skills=include_personal_skills,
        ):
            continue
        if path.is_file():
            files.append(path)
    return files


def is_canonical(rel: str) -> bool:
    return rel in CANONICAL_EXACT or rel.startswith(CANONICAL_PREFIXES) or rel in RUNTIME_TEMPLATE_ALLOWLIST


def is_safe_missing(rel: str) -> bool:
    path = Path(rel)
    return (
        rel in RUNTIME_TEMPLATE_ALLOWLIST
        or rel in SAFE_MISSING_EXACT
        or rel.startswith(SAFE_MISSING_PREFIXES)
        or (rel.startswith("scripts/") and "/" not in rel.removeprefix("scripts/"))
        or path.name.endswith(SAFE_MISSING_SUFFIXES)
    )


def path_profile_excluded(rel: str, profile: str) -> bool:
    normalized = rel.replace("\\", "/")
    if normalized.startswith(PROFILE_EXCLUDED_PREFIXES.get(profile, ())):
        return True
    name = Path(normalized).name
    return any(part in name for part in PROFILE_EXCLUDED_NAME_PARTS.get(profile, ()))


def feature_for_path(features: list[dict[str, object]], rel: str) -> dict[str, object] | None:
    if rel in STABLE_FEATURE_PATH_OVERRIDES:
        return {"id": "stable-overlay-bundle", "tier": "stable", "overlay_default": True}
    if rel.startswith("scripts/incubating/") or rel.startswith("docs/design/"):
        return {"id": "v2-incubating-runtime", "tier": "incubating", "overlay_default": False}
    return feature_by_doc_path(features, rel)


def action_from_classification(
    target: Path,
    rel: str,
    classification: lib_ownership.Classification,
    *,
    target_file: Path,
) -> Action:
    owner = classification.owner
    ownership_action = classification.action
    metadata = {
        "owner": owner,
        "ownership_action": ownership_action,
        "matched_pattern": classification.matched_pattern,
        "system_locked": classification.system_locked,
    }
    if ownership_action == "skip_generated":
        return Action(str(target), rel, "skip", "protected", "generated/cache path", **metadata)
    if ownership_action == "unchanged":
        return Action(str(target), rel, "unchanged", "safe", "same content", **metadata)
    if ownership_action == "protected_preserve":
        return Action(str(target), rel, "skip", "protected", "ownership protected path", **metadata)
    if ownership_action == "preserve_project":
        if not target_file.exists() and is_safe_missing(rel):
            return Action(str(target), rel, "add", "safe", "missing safe template/readme", **metadata)
        return Action(str(target), rel, "skip", "protected", "project-owned path", **metadata)
    if target_file.exists() and target_file.is_dir():
        return Action(str(target), rel, "review", "manual", "target path is a directory", **metadata)
    if ownership_action == "add_system":
        return Action(str(target), rel, "add", "safe", "missing system-owned file", **metadata)
    if ownership_action == "update_system":
        return Action(str(target), rel, "update_available", "risky", "target has different system-owned content", **metadata)
    if ownership_action in {"manual_merge", "manual_approval"}:
        if not target_file.exists() and is_safe_missing(rel):
            return Action(str(target), rel, "add", "safe", "missing safe template/readme", **metadata)
        return Action(str(target), rel, "review", "manual", ownership_action, **metadata)
    return Action(str(target), rel, "review", "manual", "unknown ownership action", **metadata)


def classify_file(source_file: Path, source: Path, target: Path, ownership_config: dict[str, object]) -> Action:
    rel = rel_posix(source_file, source)
    target_file = target / rel
    content_equal = target_file.is_file() and filecmp.cmp(source_file, target_file, shallow=False)
    classification = lib_ownership.classify_path(
        rel,
        ownership_config,
        source_exists=True,
        target_exists=target_file.exists(),
        content_equal=content_equal,
    )
    return action_from_classification(target, rel, classification, target_file=target_file)


def effective_ownership_config(source: Path, target: Path) -> dict[str, object]:
    source_config = lib_ownership.load_ownership_config(source / "config" / "ownership.yaml")
    target_config_path = target / "config" / "ownership.yaml"
    if target_config_path.is_file():
        target_config = lib_ownership.load_ownership_config(target_config_path)
        source_config["project_overrides"] = target_config.get("project_overrides", {"rules": []})
    return source_config


def plan_target(source: Path, target: Path, source_files: list[Path]) -> list[Action]:
    if not target.is_dir():
        return [
            Action(
                str(target),
                ".",
                "skip",
                "protected",
                "target is not a directory",
            )
        ]
    if target == source or is_relative_to(target, source):
        return [
            Action(
                str(target),
                ".",
                "skip",
                "protected",
                "target is the skeleton or inside the skeleton",
            )
        ]
    try:
        ownership_config = effective_ownership_config(source, target)
    except (OSError, ValueError, lib_ownership.OwnershipConfigError) as exc:
        return [
            Action(
                str(target),
                "config/ownership.yaml",
                "review",
                "manual",
                f"ownership config invalid: {exc}",
            )
        ]
    return [classify_file(path, source, target, ownership_config) for path in source_files]


def apply_actions(
    actions: list[Action],
    source: Path,
    *,
    safe_only: bool,
    include_risky: bool,
) -> None:
    for action in actions:
        if action.action not in {"add", "update_available"}:
            continue
        if action.safety == "safe":
            pass
        elif action.safety == "risky" and include_risky and not safe_only:
            pass
        else:
            continue
        src = source / action.path
        dst = Path(action.target) / action.path
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        action.applied = True


def discover_projects(root: Path) -> list[Path]:
    if not root.is_dir():
        raise SystemExit(f"--projects-root is not a directory: {root}")
    projects: list[Path] = []
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        if (child / "AGENTS.md").exists() or (child / "CLAUDE.md").exists():
            projects.append(child.resolve())
    return projects


def summarize(actions: list[Action]) -> dict[str, int]:
    summary: dict[str, int] = {}
    for action in actions:
        key = f"{action.action}:{action.safety}"
        summary[key] = summary.get(key, 0) + 1
    return dict(sorted(summary.items()))


def action_payload(action: Action) -> dict[str, object]:
    return asdict(action)


def feature_payload_for_action(action: Action, features: list[dict[str, object]], profile: str) -> dict[str, object]:
    feature = feature_for_path(features, action.path)
    if feature is None:
        feature = {"id": "unmapped", "tier": "stable", "overlay_default": True}
    tier = str(feature.get("tier", "stable"))
    overlay_default = bool(feature.get("overlay_default", True))
    approval_required = action.safety != "safe" or tier != "stable" or (profile == "all" and tier == "experimental")
    tier_warning = ""
    if tier == "incubating":
        tier_warning = "incubating feature: schema and workflow may change"
    elif tier == "experimental":
        tier_warning = "experimental adapter/future feature: explicit approval required"
    return {
        "feature_id": str(feature.get("id", "unmapped")),
        "tier": tier,
        "overlay_default": overlay_default,
        "approval_required": approval_required,
        "tier_warning": tier_warning,
    }


def action_payload_with_feature(action: Action, features: list[dict[str, object]], profile: str) -> dict[str, object]:
    payload = action_payload(action)
    payload.update(feature_payload_for_action(action, features, profile))
    return payload


def include_action_for_profile(action: Action, features: list[dict[str, object]], profile: str) -> bool:
    if action.safety == "profile":
        return False
    if path_profile_excluded(action.path, profile):
        return False
    feature_meta = feature_payload_for_action(action, features, profile)
    tier = str(feature_meta["tier"])
    if tier not in tiers_for_profile(profile):
        return False
    if profile == "stable":
        return bool(feature_meta["overlay_default"])
    return True


def apply_profile_to_actions(actions: list[Action], features: list[dict[str, object]], profile: str) -> list[Action]:
    filtered: list[Action] = []
    allowed_tiers = tiers_for_profile(profile)
    for action in actions:
        if action.path == ".":
            filtered.append(action)
            continue
        feature_meta = feature_payload_for_action(action, features, profile)
        tier = str(feature_meta["tier"])
        overlay_default = bool(feature_meta["overlay_default"])
        excluded = (
            tier not in allowed_tiers
            or (profile == "stable" and not overlay_default)
            or path_profile_excluded(action.path, profile)
        )
        if excluded and action.action in {"add", "update_available", "review", "unchanged"}:
            filtered.append(
                Action(
                    target=action.target,
                    path=action.path,
                    action="skip",
                    safety="profile",
                    reason=f"excluded by {profile} overlay profile",
                    applied=action.applied,
                    owner=action.owner,
                    ownership_action=action.ownership_action,
                    matched_pattern=action.matched_pattern,
                    system_locked=action.system_locked,
                )
            )
        else:
            filtered.append(action)
    return filtered


def build_brief(actions: list[Action], features: list[dict[str, object]], profile: str) -> dict[str, object]:
    included = [action for action in actions if include_action_for_profile(action, features, profile)]
    safe_additions = [action for action in included if action.action == "add" and action.safety == "safe"]
    manual_reviews = [action for action in included if action.action == "review" or action.safety in {"manual", "review"}]
    risky_reviews = [action for action in included if action.safety == "risky" or action.action == "update_available"]
    protected_skips = [action for action in included if action.action == "skip" or action.safety == "protected"]
    review_items = manual_reviews + risky_reviews
    priority = {
        "AGENTS.md": 0,
        "CLAUDE.md": 1,
        "docs/PROJECT_PROFILE.md": 2,
        "docs/PROJECT_SPEC.md": 3,
        "docs/PROJECT_OPERATING_PLAN.md": 4,
    }
    ordered_review_paths = sorted(
        {action.path for action in review_items if action.path != "."},
        key=lambda path: (priority.get(path, 50), path),
    )
    return {
        "profile": profile,
        "included_tiers": sorted(tiers_for_profile(profile)),
        "tier_warning": "stable overlay only" if profile == "stable" else "incubating/experimental items are advisory and may require manual approval",
        "safe_additions": [action_payload_with_feature(action, features, profile) for action in safe_additions],
        "manual_reviews": [action_payload_with_feature(action, features, profile) for action in manual_reviews],
        "risky_reviews": [action_payload_with_feature(action, features, profile) for action in risky_reviews],
        "protected_skips": [action_payload_with_feature(action, features, profile) for action in protected_skips],
        "recommended_next_prompt": "Review manual_merge/risky entries one by one with the user before applying changes.",
        "manual_merge_order": ordered_review_paths,
        "validation_commands": [
            "python3 scripts/verify.py",
            "python3 scripts/quality-gate.py --format json",
            "python3 scripts/resume-readiness.py --strict --format json",
        ],
        "approval_required": bool(review_items),
        "approval_note": "This brief is not approval to overwrite risky or manual-merge files.",
    }


def render_text(actions: list[Action], *, dry_run: bool) -> str:
    lines: list[str] = []
    by_target: dict[str, list[Action]] = {}
    for action in actions:
        by_target.setdefault(action.target, []).append(action)
    for target, target_actions in by_target.items():
        lines.append(f"target: {target}")
        summary = summarize(target_actions)
        for key, count in summary.items():
            lines.append(f"  {key}: {count}")
        visible = [
            a
            for a in target_actions
            if a.action in {"add", "update_available", "review", "skip"} and a.path != "."
        ]
        for action in visible[:40]:
            applied = " applied" if action.applied else ""
            lines.append(
                f"  - {action.action} [{action.safety}]{applied}: {action.path} ({action.reason})"
            )
        if len(visible) > 40:
            lines.append(f"  - ... {len(visible) - 40} more item(s)")
    lines.append("dry-run: no files changed" if dry_run else "apply: completed")
    return "\n".join(lines)


def append_upgrade_log(target: Path, actions: list[Action]) -> None:
    applied = [a for a in actions if a.applied]
    if not applied:
        return
    log = target / "runtime" / "activity-log.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "ts": utc_now(),
        "phase": "maintenance",
        "action": "skeleton_upgraded",
        "project": target.name,
        "goal_lineage": [
            "maintenance",
            target.name,
            "follow skeleton improvements",
        ],
        "tool_call": {
            "tool": "scripts/upgrade-from-skeleton.py",
            "status": "completed",
            "summary": "applied safe skeleton upgrade files",
        },
        "data": {
            "applied_paths": [a.path for a in applied],
            "mode": "safe-only",
        },
    }
    with log.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        default=None,
        help="Skeleton root (defaults to this script's repository root).",
    )
    parser.add_argument(
        "--target",
        action="append",
        default=[],
        help="Existing project root to inspect or upgrade. Can be repeated.",
    )
    parser.add_argument(
        "--projects-root",
        default=None,
        help="Directory whose immediate children should be treated as projects if they contain AGENTS.md or CLAUDE.md.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply eligible actions. Without this flag the command is dry-run only.",
    )
    parser.add_argument(
        "--safe-only",
        action="store_true",
        help="Only apply safe missing-file additions. This is the recommended apply mode.",
    )
    parser.add_argument(
        "--include-risky",
        action="store_true",
        help="Also overwrite changed canonical files. Requires --apply and is not compatible with --safe-only.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of text.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default=None,
        help="Output format. --json is kept as a compatibility alias for --format json.",
    )
    parser.add_argument(
        "--brief",
        action="store_true",
        help="Emit an AI-assisted dry-run upgrade brief. Incompatible with --apply.",
    )
    parser.add_argument(
        "--profile",
        choices=("stable", "incubating", "all"),
        default="stable",
        help="Feature maturity profile for overlay planning and --brief output.",
    )
    parser.add_argument(
        "--include-personal-skills",
        action="store_true",
        help="Include generated/user-personal .agents skill/plugin layer. Default is to skip it.",
    )
    args = parser.parse_args()

    if args.brief and args.apply:
        raise SystemExit("--brief is dry-run only and cannot be combined with --apply")
    if args.include_risky and args.safe_only:
        raise SystemExit("--include-risky cannot be combined with --safe-only")
    if args.include_risky and not args.apply:
        raise SystemExit("--include-risky requires --apply")
    if args.safe_only and not args.apply:
        raise SystemExit("--safe-only requires --apply")

    source = Path(args.source).resolve() if args.source else repo_root()
    if not source.is_dir():
        raise SystemExit(f"--source is not a directory: {source}")
    try:
        feature_manifest = load_feature_manifest(source)
        features = feature_manifest.get("features") or []
    except FileNotFoundError:
        features = []

    targets = [Path(item).resolve() for item in args.target]
    if args.projects_root:
        targets.extend(discover_projects(Path(args.projects_root).resolve()))
    # De-duplicate while preserving order.
    deduped: list[Path] = []
    seen: set[str] = set()
    for target in targets:
        key = str(target).lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(target)
    if not deduped:
        raise SystemExit("provide --target at least once or --projects-root")

    source_files = iter_source_files(
        source,
        deduped,
        include_personal_skills=args.include_personal_skills,
    )
    all_actions: list[Action] = []
    by_target: dict[Path, list[Action]] = {}
    for target in deduped:
        actions = plan_target(source, target, source_files)
        actions = apply_profile_to_actions(actions, features, args.profile)
        by_target[target] = actions
        all_actions.extend(actions)

    if args.apply:
        for target, actions in by_target.items():
            apply_actions(
                actions,
                source,
                safe_only=args.safe_only,
                include_risky=args.include_risky,
            )
            append_upgrade_log(target, actions)

    output_format = "json" if args.json else (args.format or "text")
    if output_format == "json":
        payload = {
            "source": str(source),
            "dry_run": not args.apply,
            "summary": summarize(all_actions),
            "actions": [action_payload(action) for action in all_actions],
        }
        if args.brief:
            payload["brief"] = build_brief(all_actions, features, args.profile)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_text(all_actions, dry_run=not args.apply))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

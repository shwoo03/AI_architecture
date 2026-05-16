#!/usr/bin/env python3
"""Create a bounded brief for specialist subagents."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from importlib import util

sys.dont_write_bytecode = True


try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass


SPECIALISTS = {
    "build-error-resolver": "Minimal build, typecheck, and test failure fixes after implementation.",
    "security-reviewer": "Review security-scan, permission, secret, and copied-source findings.",
    "reference-reviewer": "Compare reference candidates and produce source-backed absorption notes.",
    "docs-sync-auditor": "Check docs, catalog, codemap, and workflow drift.",
    "closeout-validator": "Independently inspect verify, quality-gate, and completion evidence.",
}
WRITE_POLICIES = {"read_only", "manual_work_required", "write_with_confirmation"}
WRITE_POLICY_RANK = {
    "read_only": 0,
    "manual_work_required": 1,
    "write_with_confirmation": 2,
}
REGISTRY_FIELDS = {"mission", "write_policy", "default_scope", "recommended_checks"}


@dataclass
class Brief:
    schema_version: str
    brief_id: str
    created_at: str
    tier: str
    parent_plan: str
    parent_goal: str
    goal_lineage: list[dict[str, str | None]]
    objective: str
    read_scope: list[str]
    write_scope: list[str]
    forbidden_paths: list[str]
    expected_output: str
    validation_hints: list[str]
    handoff_requirements: str
    execution_mode: str
    ext: dict[str, object]
    role: str
    role_source: str
    write_policy: str
    policy_inheritance: dict[str, object]
    forbidden_actions: list[str]
    relevant_rules: list[str]
    subdirectory_hints: list[dict[str, str]]


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def normalize_scope(root: Path, values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values or ["."]:
        path = Path(value)
        resolved = path.resolve(strict=False) if path.is_absolute() else (root / path).resolve(strict=False)
        try:
            rel = resolved.relative_to(root.resolve(strict=False)).as_posix()
        except ValueError as exc:
            raise ValueError(f"scope outside root: {value}") from exc
        if rel not in result:
            result.append(rel)
    return result


def normalize_optional_repo_path(root: Path, value: str) -> str:
    if not value:
        return ""
    path = Path(value)
    resolved = path.resolve(strict=False) if path.is_absolute() else (root / path).resolve(strict=False)
    try:
        return resolved.relative_to(root.resolve(strict=False)).as_posix()
    except ValueError as exc:
        raise ValueError(f"path outside root: {value}") from exc


def slugify(value: str, fallback: str = "adhoc") -> str:
    lowered = value.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return slug or fallback


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def next_brief_sequence(root: Path, date_part: str, plan_slug: str, role_slug: str) -> int:
    brief_dir = root / "runtime" / "agent-briefs"
    prefix = f"{date_part}-{plan_slug}-{role_slug}-"
    highest = 0
    if brief_dir.exists():
        for path in brief_dir.glob(f"{prefix}*.json"):
            suffix = path.stem.removeprefix(prefix)
            if suffix.isdigit():
                highest = max(highest, int(suffix))
    return highest + 1


def build_brief_id(root: Path, parent_plan: str, role: str, brief_seq: str) -> tuple[str, str]:
    created_at = utc_now()
    date_part = created_at[:10]
    plan_slug = slugify(Path(parent_plan).stem if parent_plan else "adhoc")
    role_slug = slugify(role)
    if brief_seq:
        try:
            seq = int(brief_seq)
        except ValueError as exc:
            raise ValueError("--brief-seq must be numeric") from exc
    else:
        seq = next_brief_sequence(root, date_part, plan_slug, role_slug)
    return f"{date_part}-{plan_slug}-{role_slug}-{seq:02d}", created_at


def build_goal_lineage(user_goal: str, parent_plan: str, parent_goal: str, brief_id: str, objective: str) -> list[dict[str, str | None]]:
    brief_ref = f"runtime/agent-briefs/{brief_id}.json"
    lineage: list[dict[str, str | None]] = [
        {"type": "user_goal", "ref": None, "summary": user_goal or parent_goal or objective},
    ]
    if parent_plan:
        lineage.append({"type": "plan", "ref": parent_plan, "summary": parent_goal or objective})
    lineage.append({"type": "brief", "ref": brief_ref, "summary": objective})
    return lineage


def is_same_or_under(child: str, parent: str) -> bool:
    child_path = Path(child)
    parent_path = Path(parent)
    return child == parent or parent == "." or child_path == parent_path or parent_path in child_path.parents


def intersect_scope(scope: list[str], parent_scope: list[str]) -> list[str]:
    if not parent_scope:
        return scope
    result: list[str] = []
    for item in scope:
        if any(is_same_or_under(item, parent) for parent in parent_scope):
            result.append(item)
    return result


def narrower_policy(*policies: str) -> str:
    valid = [policy for policy in policies if policy]
    return min(valid, key=lambda item: WRITE_POLICY_RANK[item]) if valid else "read_only"


def parse_inline_list(value: str) -> list[str]:
    value = value.strip()
    if not (value.startswith("[") and value.endswith("]")):
        return []
    return [item.strip().strip('"').strip("'") for item in value[1:-1].split(",") if item.strip()]


def load_specialist_registry_file(path: Path, *, strict_top_level: bool) -> dict[str, dict[str, object]]:
    if not path.exists():
        return {}
    entries: dict[str, dict[str, object]] = {}
    in_specialists = False
    current = ""
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        stripped = raw.strip()
        if indent == 0:
            if strict_top_level and stripped != "specialists:":
                raise ValueError(f"{path.name} has unsupported top-level key: {stripped.rstrip(':')}")
            in_specialists = stripped == "specialists:"
            current = ""
            continue
        if not in_specialists:
            continue
        if indent == 2 and stripped.endswith(":"):
            current = stripped[:-1]
            entries[current] = {}
            continue
        if current and indent == 4 and ":" in stripped:
            key, value = stripped.split(":", 1)
            key = key.strip()
            if key not in REGISTRY_FIELDS:
                raise ValueError(f"{path.name} specialist {current} has unsupported field: {key}")
            value = value.strip()
            entries[current][key] = parse_inline_list(value) if value.startswith("[") else value.strip('"').strip("'")
            continue
        if strict_top_level:
            raise ValueError(f"{path.name} has unsupported specialist shape near: {stripped}")
    return entries


def normalized_registry_scope(root: Path, role: str, value: object) -> list[str]:
    if value is None:
        return ["."]
    if not isinstance(value, list):
        raise ValueError(f"specialist {role} default_scope must be an inline list")
    return normalize_scope(root, [str(item) for item in value] or ["."])


def overlay_scope_narrows(root: Path, role: str, base_scope: object, overlay_scope: object) -> bool:
    base = normalized_registry_scope(root, role, base_scope)
    overlay = normalized_registry_scope(root, role, overlay_scope)
    return all(any(is_same_or_under(item, parent) for parent in base) for item in overlay)


def merge_specialist_overlay(root: Path, base: dict[str, dict[str, object]], overlay: dict[str, dict[str, object]]) -> dict[str, dict[str, object]]:
    merged: dict[str, dict[str, object]] = {role: {**entry, "role_source": "base"} for role, entry in base.items()}
    for role in SPECIALISTS:
        merged.setdefault(role, {"role_source": "base"})
    for role, overlay_entry in overlay.items():
        if role not in merged:
            merged[role] = {**overlay_entry, "role_source": "project"}
            continue
        base_entry = merged[role]
        if "write_policy" in overlay_entry:
            base_policy = str(base_entry.get("write_policy") or "read_only")
            overlay_policy = str(overlay_entry.get("write_policy") or "read_only")
            if base_policy not in WRITE_POLICIES:
                raise ValueError(f"invalid base specialist write_policy for {role}: {base_policy}")
            if overlay_policy not in WRITE_POLICIES:
                raise ValueError(f"invalid overlay specialist write_policy for {role}: {overlay_policy}")
            if WRITE_POLICY_RANK[overlay_policy] > WRITE_POLICY_RANK[base_policy]:
                raise ValueError(f"overlay for {role} broadens base specialist write_policy {base_policy} -> {overlay_policy}")
        if "default_scope" in overlay_entry and not overlay_scope_narrows(root, role, base_entry.get("default_scope"), overlay_entry.get("default_scope")):
            raise ValueError(f"overlay for {role} broadens base specialist default_scope")
        merged[role] = {**base_entry, **overlay_entry, "role_source": "base"}
    return merged


def load_team_registry(root: Path) -> dict[str, dict[str, object]]:
    base = load_specialist_registry_file(root / "config" / "agent-team.yaml", strict_top_level=False)
    overlay = load_specialist_registry_file(root / "config" / "agent-team-overrides.yaml", strict_top_level=True)
    return merge_specialist_overlay(root, base, overlay)


def recommended_checks(role: str) -> list[str]:
    if role == "security-reviewer":
        return ["python3 scripts/security-scan.py --root . --include-runtime --strict"]
    if role == "reference-reviewer":
        return ["python3 scripts/validate-reference-candidates.py --root .", "python3 scripts/validate-reference-proposals.py --root ."]
    if role == "docs-sync-auditor":
        return ["python3 scripts/generate-codemaps.py --root . --format json", "python3 scripts/wiki-lint.py --root . --format json"]
    if role == "closeout-validator":
        return ["python3 scripts/verify.py --root .", "python3 scripts/quality-gate.py --root . --format json"]
    return ["python3 -m unittest discover -s tests -v"]


def normalize_check_command(command: str) -> str:
    if command.startswith("python "):
        return "python3 " + command[len("python ") :]
    return command


def load_subdir_hints(root: Path, scope: list[str]) -> list[dict[str, str]]:
    path = root / "scripts" / "subdir-hints.py"
    if not path.exists():
        return []
    spec = util.spec_from_file_location("subdir_hints_module", path)
    if spec is None or spec.loader is None:
        return []
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    hints: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in scope:
        for hint in module.collect_hints(root, item):
            key = str(hint.get("path", ""))
            if key and key not in seen:
                seen.add(key)
                hints.append(hint)
    return hints


def build_brief(root: Path, args: argparse.Namespace) -> Brief:
    registry = load_team_registry(root)
    known_roles = set(SPECIALISTS) | set(registry)
    if args.role not in known_roles:
        raise ValueError(f"unknown specialist role: {args.role}")
    configured = registry.get(args.role, {})
    role_source = str(configured.get("role_source") or "base")
    if role_source not in {"base", "project"}:
        raise ValueError(f"invalid role source: {role_source}")
    configured_policy = str(configured.get("write_policy") or "read_only")
    if configured_policy not in WRITE_POLICIES:
        raise ValueError(f"invalid configured write policy: {configured_policy}")
    requested_policy = args.write_policy or configured_policy
    if requested_policy not in WRITE_POLICIES:
        raise ValueError(f"invalid write policy: {args.write_policy}")
    if WRITE_POLICY_RANK[requested_policy] > WRITE_POLICY_RANK[configured_policy]:
        raise ValueError(f"requested write policy {requested_policy} broadens specialist policy {configured_policy}")
    inherited_policy = args.parent_write_policy or requested_policy
    if inherited_policy not in WRITE_POLICIES:
        raise ValueError(f"invalid parent write policy: {inherited_policy}")
    if WRITE_POLICY_RANK[requested_policy] > WRITE_POLICY_RANK[inherited_policy]:
        raise ValueError(f"requested write policy {requested_policy} broadens parent policy {inherited_policy}")
    write_policy = narrower_policy(configured_policy, requested_policy, inherited_policy)
    default_scope = configured.get("default_scope") if isinstance(configured.get("default_scope"), list) else []
    scope_values = args.scope or [str(item) for item in default_scope] or ["."]
    scope = normalize_scope(root, scope_values)
    parent_scope = normalize_scope(root, args.parent_scope) if args.parent_scope else []
    effective_scope = intersect_scope(scope, parent_scope)
    if parent_scope and not effective_scope:
        raise ValueError("effective scope is empty after applying parent scope")
    forbidden = [
        "Do not edit files outside allowed_files.",
        "Do not run dependency install, git push, or destructive filesystem commands.",
        "Do not change public command boundaries; route through scripts/agent-flow.py.",
        "Do not expand permissions beyond the parent/session brief.",
    ]
    if write_policy == "read_only":
        forbidden.append("Do not modify files; report findings only.")
    elif write_policy == "manual_work_required":
        forbidden.append("Do not write until the planner/user has approved the implementation scope.")
    parent_plan = normalize_optional_repo_path(root, args.parent_plan)
    parent_goal = args.parent_goal.strip() or args.goal.strip()
    brief_id, created_at = build_brief_id(root, parent_plan, args.role, args.brief_seq)
    checks = [normalize_check_command(str(item)) for item in configured.get("recommended_checks", [])] if isinstance(configured.get("recommended_checks"), list) else recommended_checks(args.role)
    handoff = "Return findings, changed files if any, checks run, residual risk, and next recommended action."
    return Brief(
        schema_version="ai-architecture.agent-brief.v1",
        brief_id=brief_id,
        created_at=created_at,
        tier="incubating",
        parent_plan=parent_plan,
        parent_goal=parent_goal,
        goal_lineage=build_goal_lineage(args.user_goal.strip(), parent_plan, parent_goal, brief_id, args.goal.strip()),
        objective=args.goal.strip(),
        read_scope=effective_scope,
        write_scope=[] if write_policy == "read_only" else effective_scope,
        forbidden_paths=[],
        expected_output=handoff,
        validation_hints=checks,
        handoff_requirements=handoff,
        execution_mode="manual_human",
        ext={},
        role=args.role,
        role_source=role_source,
        write_policy=write_policy,
        policy_inheritance={
            "parent_role": args.parent_role.strip(),
            "inherited_write_policy": inherited_policy,
            "effective_write_policy": write_policy,
            "effective_scope": effective_scope,
        },
        forbidden_actions=forbidden,
        relevant_rules=["AGENTS.md", "scripts/catalog.yaml", "config/policy.yaml", "rules/common/confirmation-required.md"],
        subdirectory_hints=load_subdir_hints(root, scope),
    )


def write_brief(root: Path, brief: Brief) -> Path:
    brief_dir = root / "runtime" / "agent-briefs"
    brief_dir.mkdir(parents=True, exist_ok=True)
    path = brief_dir / f"{brief.brief_id}.json"
    if path.exists():
        raise ValueError(f"brief already exists: {path.relative_to(root).as_posix()}")
    path.write_text(json.dumps(asdict(brief), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def render_text(brief: Brief) -> str:
    policy = brief.policy_inheritance
    lines = [
        f"Role: {brief.role}",
        f"Role source: {brief.role_source}",
        f"Objective: {brief.objective}",
        f"Write policy: {brief.write_policy}",
        f"Parent role: {policy.get('parent_role') or '(none)'}",
        f"Inherited write policy: {policy.get('inherited_write_policy')}",
        f"Effective write policy: {policy.get('effective_write_policy')}",
        "Read scope:",
        *[f"- {item}" for item in brief.read_scope],
        "Write scope:",
        *[f"- {item}" for item in brief.write_scope],
        "Forbidden actions:",
        *[f"- {item}" for item in brief.forbidden_actions],
        "Validation hints:",
        *[f"- {item}" for item in brief.validation_hints],
        "Subdirectory hints:",
        *[f"- {item['path']}: {item.get('summary', '')}" for item in brief.subdirectory_hints],
        f"Handoff: {brief.handoff_requirements}",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=None)
    parser.add_argument("--role", required=True)
    parser.add_argument("--goal", required=True)
    parser.add_argument("--scope", action="append", default=[])
    parser.add_argument("--write-policy", choices=sorted(WRITE_POLICIES), default="")
    parser.add_argument("--parent-role", default="")
    parser.add_argument("--parent-write-policy", choices=sorted(WRITE_POLICIES), default="")
    parser.add_argument("--parent-scope", action="append", default=[])
    parser.add_argument("--parent-plan", default="")
    parser.add_argument("--parent-goal", default="")
    parser.add_argument("--user-goal", default="")
    parser.add_argument("--brief-seq", default="")
    parser.add_argument("--write", action="store_true", help="Write the brief artifact under runtime/agent-briefs/.")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()
    root = Path(args.root).resolve() if args.root else repo_root().resolve()
    if not root.is_dir():
        print(f"root not a directory: {root}", file=sys.stderr)
        return 2
    try:
        brief = build_brief(root, args)
        brief_path = write_brief(root, brief) if args.write else None
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if args.format == "json":
        if args.write and brief_path is not None:
            payload = {
                "written": True,
                "brief_path": brief_path.relative_to(root).as_posix(),
                "brief": asdict(brief),
            }
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(json.dumps(asdict(brief), ensure_ascii=False, indent=2))
    else:
        if args.write and brief_path is not None:
            print(f"written: {brief_path.relative_to(root).as_posix()}")
        print(render_text(brief))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

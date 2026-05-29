#!/usr/bin/env python3
"""Build and validate versioned skeleton release manifests."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import convert as convert_lib
from lib_feature_status import feature_by_doc_path, load_feature_manifest, tiers_for_profile
import lib_ownership


SCHEMA_VERSION = "ai-architecture.release.v1"
CHANNEL_PROFILES = {"stable": "stable", "preview": "incubating", "edge": "all"}
COMPONENT_ORDER = {
    "core": 0,
    "validation": 1,
    "runtime": 2,
    "reference": 3,
    "wiki": 4,
    "skills": 5,
    "agents": 6,
    "docs": 7,
    "bootstrap": 8,
}
REMOVED_PATHS = [
    "runtime/memory",
    "codex/agents/memory-curator.md",
    "knowledge/workflows/wiki-ingest.md",
]
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
    "manifest.yaml",
    "mcp/servers.yaml",
}
PROJECT_STATE_PREFIXES = (
    "docs/CODEMAPS/",
    "plans/",
    "research/reference-candidates/",
    "runtime/archive/",
    "runtime/agent-briefs/",
    "runtime/external-repos/",
    "runtime/proposals/",
    "runtime/schedules/",
    "runtime/state/",
    "runtime/validation/",
)
PROJECT_STATE_EXACT = {
    "docs/PROJECT_PROFILE.md",
    "docs/PROJECT_SPEC.md",
    "docs/PROJECT_OPERATING_PLAN.md",
    "runtime/activity-log.jsonl",
    "runtime/agent-runs.jsonl",
    "runtime/checkpoints.jsonl",
    "runtime/completion-evidence.jsonl",
    "runtime/install-state.jsonl",
    "runtime/reference-tasks.jsonl",
    "runtime/review-queue.jsonl",
    "runtime/session-snapshot.json",
    "runtime/skill-lifecycle.jsonl",
    "runtime/skill-usage.jsonl",
}
RUNTIME_TEMPLATE_ALLOWLIST = {
    "runtime/AGENTS.md",
    "runtime/external-repos/README.md",
    "runtime/external-repos/.gitkeep",
    "runtime/proposals/reference-adoption/README.md",
    "runtime/proposals/reference-adoption/_template.md",
}
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
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def git_commit(root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=5,
        )
    except subprocess.SubprocessError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def git_dirty(root: Path) -> bool | None:
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=5,
        )
    except subprocess.SubprocessError:
        return None
    if result.returncode != 0:
        return None
    return bool(result.stdout.strip())


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel_posix(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def should_skip(path: Path, root: Path) -> bool:
    rel = rel_posix(path, root)
    if any(part in SKIP_DIR_NAMES for part in path.relative_to(root).parts):
        return True
    if path.is_symlink() or not path.is_file():
        return True
    if rel in PROJECT_STATE_EXACT:
        return True
    if rel.startswith(PROJECT_STATE_PREFIXES):
        return True
    if rel.startswith("runtime/") and rel not in RUNTIME_TEMPLATE_ALLOWLIST:
        return True
    if rel in RUNTIME_TEMPLATE_ALLOWLIST:
        return False
    return not (rel in CANONICAL_EXACT or rel.startswith(CANONICAL_PREFIXES))


def iter_release_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*") if not should_skip(path, root))


def fallback_feature(rel: str) -> dict[str, Any]:
    if rel.startswith("scripts/incubating/") or rel.startswith("docs/design/"):
        return {"id": "v2-incubating-runtime", "tier": "incubating", "overlay_default": False}
    return {"id": "stable-overlay-bundle", "tier": "stable", "overlay_default": True}


def component_id_for_path(rel: str) -> str:
    """Return the coarse install/upgrade component for a release path."""
    if rel.startswith("skills/") or rel.startswith("scripts/skill") or rel.startswith("docs/SKILL"):
        return "skills"
    if rel.startswith("agents/") or rel == "config/agent-team.yaml" or rel == "docs/AGENT_REGISTRY.md":
        return "agents"
    if rel.startswith("scripts/bootstrap/") or rel.startswith("examples/") or rel in {
        "docs/NEW_PROJECT_CHECKLIST.md",
        "docs/PROJECT_PROFILE.template.md",
        "docs/PROJECT_SPEC.template.md",
        "docs/RUNTIME_STARTUP.template.md",
    }:
        return "bootstrap"
    if (
        rel == "references.yaml"
        or rel.startswith("scripts/reference")
        or rel.startswith("runtime/proposals/reference-adoption/")
        or rel == "docs/REFERENCE_DISCOVERY_WORKFLOW.md"
        or rel.startswith("docs/REFERENCE")
    ):
        return "reference"
    if rel.startswith("scripts/wiki") or rel.startswith("scripts/knowledge") or "WIKI" in rel:
        return "wiki"
    if (
        rel.startswith("schemas/")
        or rel.startswith("scripts/verify")
        or rel.startswith("scripts/quality")
        or rel.startswith("scripts/schema")
        or rel.startswith("scripts/lsp")
        or rel.startswith("scripts/security")
        or rel.startswith("scripts/surface-bloat")
        or rel.startswith("scripts/path-safety")
        or rel.startswith("scripts/markdown-sanitize")
    ):
        return "validation"
    if (
        rel.startswith("runtime/")
        or rel.startswith("scripts/task-closeout")
        or rel.startswith("scripts/completion-evidence")
        or rel.startswith("scripts/install-state")
        or rel.startswith("scripts/agent-brief")
        or rel.startswith("scripts/incubating/")
        or rel == "docs/RUNTIME_EVENT_SCHEMA.md"
        or rel == "docs/SESSION_CONTINUITY.md"
    ):
        return "runtime"
    if rel.startswith("docs/"):
        return "docs"
    return "core"


def include_for_channel(feature: dict[str, Any], channel: str) -> bool:
    profile = CHANNEL_PROFILES[channel]
    tier = str(feature.get("tier") or "stable")
    if tier not in tiers_for_profile(profile):
        return False
    if channel == "stable":
        return bool(feature.get("overlay_default", True))
    return True


def _source_matches(path: str, source: str) -> bool:
    source = source.rstrip("/")
    if not source:
        return False
    return path == source or path.startswith(source + "/")


def generated_artifact_policies(root: Path) -> list[dict[str, Any]]:
    manifest = convert_lib.load_manifest(root)
    policies: list[dict[str, Any]] = []
    seen: set[tuple[str, tuple[str, ...]]] = set()
    mappings = manifest.get("mappings", {})
    if not isinstance(mappings, dict):
        return policies
    for key, mapping in sorted(mappings.items()):
        if not isinstance(mapping, dict):
            continue
        source = str(mapping.get("source") or "").rstrip("/")
        targets = mapping.get("targets") or {}
        if not source or not isinstance(targets, dict):
            continue
        generated_targets = sorted(
            str(target).rstrip("/")
            for target in targets.values()
            if str(target or "").strip() and str(target).rstrip("/") != source
        )
        if not generated_targets:
            continue
        signature = (source, tuple(generated_targets))
        if signature in seen:
            continue
        seen.add(signature)
        policies.append(
            {
                "mapping": str(key),
                "canonical_source": source,
                "generated_targets": generated_targets,
                "regeneration_command": "python3 scripts/convert.py --root <target>",
                "parity_check": "python3 scripts/verify-parity.py --root <target> --format json",
                "direct_edit_allowed": False,
            }
        )
    return policies


def generated_policies_for_paths(paths: list[str], policies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for policy in policies:
        source = str(policy.get("canonical_source") or "")
        if any(_source_matches(path, source) for path in paths):
            selected.append(policy)
    return selected


def build_components(
    files: list[dict[str, Any]],
    features: list[dict[str, Any]],
    policies: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    features_by_id = {str(feature.get("id") or ""): feature for feature in features}
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in files:
        grouped.setdefault(str(item.get("component_id") or "core"), []).append(item)

    components: list[dict[str, Any]] = []
    for component_id, items in sorted(grouped.items(), key=lambda pair: (COMPONENT_ORDER.get(pair[0], 999), pair[0])):
        paths = sorted(str(item["path"]) for item in items)
        feature_ids = sorted({str(item.get("feature_id") or "unmapped") for item in items})
        tiers = sorted({str(item.get("tier") or "stable") for item in items})
        owner_counts: dict[str, int] = {}
        action_counts: dict[str, int] = {}
        required_checks: set[str] = set()
        for feature_id in feature_ids:
            feature = features_by_id.get(feature_id, {})
            checks = feature.get("checks", [])
            if isinstance(checks, list):
                required_checks.update(str(check) for check in checks)
        for item in items:
            owner = str(item.get("owner") or "unknown")
            action = str(item.get("ownership_action") or "unknown")
            owner_counts[owner] = owner_counts.get(owner, 0) + 1
            action_counts[action] = action_counts.get(action, 0) + 1
        generated_artifacts = generated_policies_for_paths(paths, policies)
        components.append(
            {
                "id": component_id,
                "feature_ids": feature_ids,
                "tiers": tiers,
                "overlay_default": all(bool(item.get("overlay_default", True)) for item in items),
                "file_count": len(items),
                "byte_count": sum(int(item.get("size") or 0) for item in items),
                "paths": paths,
                "required_checks": sorted(required_checks),
                "owner_counts": dict(sorted(owner_counts.items())),
                "ownership_action_counts": dict(sorted(action_counts.items())),
                "generated_artifacts": generated_artifacts,
                "generated_artifact_policy": {
                    "status": "managed" if generated_artifacts else "none",
                    "managed_mappings": generated_artifacts,
                    "target_direct_edit_allowed": False if generated_artifacts else True,
                },
            }
        )
    return components


def release_id_for(root: Path, channel: str) -> str:
    commit = git_commit(root)
    suffix = (commit or "unknown")[:12]
    return f"skeleton-{channel}-{suffix}"


def file_entry(root: Path, path: Path, features: list[dict[str, Any]], ownership_config: dict[str, Any]) -> dict[str, Any]:
    rel = rel_posix(path, root)
    feature = feature_by_doc_path(features, rel) or fallback_feature(rel)
    classification = lib_ownership.classify_path(
        rel,
        ownership_config,
        source_exists=True,
        target_exists=False,
        content_equal=False,
    )
    return {
        "path": rel,
        "sha256": sha256_file(path),
        "size": path.stat().st_size,
        "feature_id": str(feature.get("id") or "unmapped"),
        "component_id": component_id_for_path(rel),
        "tier": str(feature.get("tier") or "stable"),
        "stable_role": str(feature.get("stable_role") or ""),
        "delivery": str(feature.get("delivery") or "overlay"),
        "overlay_default": bool(feature.get("overlay_default", True)),
        "owner": classification.owner,
        "ownership_action": classification.action,
    }


def build_release_manifest(
    root: Path,
    *,
    channel: str = "stable",
    release_id: str = "",
    created_at: str = "",
) -> dict[str, Any]:
    if channel not in CHANNEL_PROFILES:
        raise ValueError(f"unsupported release channel: {channel}")
    try:
        feature_manifest = load_feature_manifest(root)
        features = list(feature_manifest.get("features") or [])
    except FileNotFoundError:
        features = []
    ownership_config = lib_ownership.load_ownership_config(root / "config" / "ownership.yaml")
    files = [
        file_entry(root, path, features, ownership_config)
        for path in iter_release_files(root)
    ]
    files = [entry for entry in files if include_for_channel(entry, channel)]
    files.sort(key=lambda item: str(item["path"]))
    policies = generated_artifact_policies(root)
    components = build_components(files, features, policies)
    return {
        "schema_version": SCHEMA_VERSION,
        "release_id": release_id or release_id_for(root, channel),
        "source_commit": git_commit(root),
        "source_dirty": git_dirty(root),
        "created_at": created_at or utc_now(),
        "channel": channel,
        "feature_profile": CHANNEL_PROFILES[channel],
        "components": components,
        "generated_artifact_policy": policies,
        "files": files,
        "removed_paths": REMOVED_PATHS,
        "migrations": [],
        "verification": [
            "python3 scripts/verify-skeleton.py",
            "python3 scripts/verify-parity.py --format json",
            "python3 scripts/resume-readiness.py --strict --format json",
        ],
    }


def release_summary(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": manifest.get("schema_version"),
        "release_id": manifest.get("release_id"),
        "source_commit": manifest.get("source_commit"),
        "source_dirty": manifest.get("source_dirty"),
        "channel": manifest.get("channel"),
        "feature_profile": manifest.get("feature_profile"),
        "component_count": len(manifest.get("components") or []),
        "managed_generated_component_count": sum(
            1
            for component in manifest.get("components") or []
            if isinstance(component, dict)
            and isinstance(component.get("generated_artifact_policy"), dict)
            and component["generated_artifact_policy"].get("status") == "managed"
        ),
        "files_by_delivery": dict(
            sorted(
                {
                    str(entry.get("delivery") or "overlay"): sum(
                        1
                        for file_entry in manifest.get("files") or []
                        if isinstance(file_entry, dict)
                        and str(file_entry.get("delivery") or "overlay") == str(entry.get("delivery") or "overlay")
                    )
                    for entry in manifest.get("files") or []
                    if isinstance(entry, dict)
                }.items()
            )
        ),
        "generated_artifact_policy_count": len(manifest.get("generated_artifact_policy") or []),
        "file_count": len(manifest.get("files") or []),
        "migration_count": len(manifest.get("migrations") or []),
    }


def validate_manifest(root: Path, manifest: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    if manifest.get("schema_version") != SCHEMA_VERSION:
        findings.append(f"schema_version must be {SCHEMA_VERSION}")
    channel = str(manifest.get("channel") or "")
    if channel not in CHANNEL_PROFILES:
        findings.append(f"channel must be one of: {', '.join(sorted(CHANNEL_PROFILES))}")
    current_commit = git_commit(root)
    if manifest.get("source_commit") and current_commit and manifest.get("source_commit") != current_commit:
        findings.append("source_commit differs from current root commit")
    files = manifest.get("files")
    if not isinstance(files, list):
        return findings + ["files must be a list"]
    seen: set[str] = set()
    file_component_counts: dict[str, int] = {}
    for index, item in enumerate(files, start=1):
        if not isinstance(item, dict):
            findings.append(f"files[{index}] must be an object")
            continue
        rel = str(item.get("path") or "")
        if not rel or Path(rel).is_absolute() or ".." in Path(rel).parts:
            findings.append(f"files[{index}].path must be a safe relative path")
            continue
        if rel in seen:
            findings.append(f"duplicate file entry: {rel}")
        seen.add(rel)
        component_id = str(item.get("component_id") or "")
        if not component_id:
            findings.append(f"files[{index}].component_id must be set")
        else:
            file_component_counts[component_id] = file_component_counts.get(component_id, 0) + 1
        path = root / rel
        if not path.is_file():
            findings.append(f"missing file: {rel}")
            continue
        actual = sha256_file(path)
        if item.get("sha256") != actual:
            findings.append(f"hash_mismatch: {rel}")
        if item.get("size") != path.stat().st_size:
            findings.append(f"size_mismatch: {rel}")
    components = manifest.get("components")
    if components is not None:
        if not isinstance(components, list):
            findings.append("components must be a list")
        else:
            file_paths = {str(item.get("path") or "") for item in files if isinstance(item, dict)}
            component_ids: set[str] = set()
            for index, item in enumerate(components, start=1):
                if not isinstance(item, dict):
                    findings.append(f"components[{index}] must be an object")
                    continue
                component_id = str(item.get("id") or "")
                if not component_id:
                    findings.append(f"components[{index}].id is required")
                elif component_id in component_ids:
                    findings.append(f"duplicate component entry: {component_id}")
                component_ids.add(component_id)
                if component_id and item.get("file_count") != file_component_counts.get(component_id, 0):
                    findings.append(f"component_file_count_mismatch: {component_id}")
                paths = item.get("paths")
                if not isinstance(paths, list) or not paths:
                    findings.append(f"components[{index}].paths must be a non-empty list")
                else:
                    for rel in paths:
                        if str(rel) not in file_paths:
                            findings.append(f"components[{index}].paths references unknown file: {rel}")
                generated = item.get("generated_artifacts", [])
                if generated is not None and not isinstance(generated, list):
                    findings.append(f"components[{index}].generated_artifacts must be a list")
                policy = item.get("generated_artifact_policy")
                if not isinstance(policy, dict):
                    findings.append(f"components[{index}].generated_artifact_policy must be an object")
                elif policy.get("status") == "managed" and policy.get("target_direct_edit_allowed") is not False:
                    findings.append(f"components[{index}].generated_artifact_policy.target_direct_edit_allowed must be false for managed generated artifacts")
    policies = manifest.get("generated_artifact_policy")
    if policies is not None:
        if not isinstance(policies, list):
            findings.append("generated_artifact_policy must be a list")
        else:
            for index, item in enumerate(policies, start=1):
                if not isinstance(item, dict):
                    findings.append(f"generated_artifact_policy[{index}] must be an object")
                    continue
                if item.get("direct_edit_allowed") is not False:
                    findings.append(f"generated_artifact_policy[{index}].direct_edit_allowed must be false")
                if not item.get("canonical_source"):
                    findings.append(f"generated_artifact_policy[{index}].canonical_source is required")
                targets = item.get("generated_targets")
                if not isinstance(targets, list) or not targets:
                    findings.append(f"generated_artifact_policy[{index}].generated_targets must be a non-empty list")
    return findings


def read_manifest(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("release manifest must be a JSON object")
    return payload

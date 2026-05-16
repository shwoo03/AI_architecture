#!/usr/bin/env python3
"""Ownership-aware upgrade classification helpers.

This module intentionally stays independent from upgrade application code.
Slice 2 owns classifier correctness; later slices wire these helpers into
upgrade and verify commands.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Any, Mapping, Sequence


SCHEMA_VERSION = "ai-architecture.ownership.v1"
NORMAL_OWNERS = {"system_owned", "project_owned", "manual_merge"}


class OwnershipConfigError(ValueError):
    """Raised when an ownership config is malformed or unsupported."""


@dataclass(frozen=True)
class Classification:
    path: str
    owner: str
    action: str
    reason: str
    matched_pattern: str = ""
    system_locked: bool = False


@dataclass(frozen=True)
class LockChange:
    path: str
    kind: str
    previous_owner: str = ""
    current_owner: str = ""
    previous_action: str = ""
    current_action: str = ""


@dataclass(frozen=True)
class SelfClassificationReport:
    root: str
    total: int
    unknown: list[str]
    classifications: dict[str, Classification]


def normalize_path(path: str | Path) -> str:
    rel = Path(path).as_posix()
    while rel.startswith("./"):
        rel = rel[2:]
    while rel.startswith("../"):
        rel = rel[3:]
    return rel


def path_matches(pattern: str, path: str | Path) -> bool:
    rel = normalize_path(path)
    pat = normalize_path(pattern)
    if pat.startswith("**/"):
        return fnmatchcase(rel, pat) or fnmatchcase(rel, pat[3:])
    if pat.endswith("/**"):
        prefix = pat[:-3]
        return rel == prefix or rel.startswith(prefix + "/")
    return fnmatchcase(rel, pat)


def load_ownership_config(path: str | Path) -> dict[str, Any]:
    """Load the v1 ownership YAML subset without requiring PyYAML.

    Supported constructs are intentionally narrow: nested mappings, scalar
    values, lists of scalars, and lists of `{pattern, owner}` mappings.
    """

    return parse_ownership_yaml(Path(path).read_text(encoding="utf-8"))


def parse_ownership_yaml(text: str) -> dict[str, Any]:
    config: dict[str, Any] = {}
    current_top = ""
    current_key = ""
    current_rule: dict[str, str] | None = None

    for raw in text.splitlines():
        line = raw.split(" #", 1)[0].rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        if indent == 0:
            key, value = _split_mapping(stripped)
            current_top = key
            current_key = ""
            current_rule = None
            config[key] = value if value else {}
            continue
        if indent == 2:
            if current_top == "unknown_policy":
                key, value = _split_mapping(stripped)
                _ensure_dict(config, current_top)[key] = value
                continue
            key, value = _split_mapping(stripped)
            current_key = key
            current_rule = None
            parent = _ensure_dict(config, current_top)
            parent[key] = [] if value == "[]" else (value if value else ([] if key in {"skip_patterns", "protected", "system_locked", "rules"} else {}))
            continue
        if indent == 4 and stripped.startswith("- "):
            parent = _ensure_dict(config, current_top)
            values = parent.setdefault(current_key, [])
            if not isinstance(values, list):
                raise OwnershipConfigError(f"{current_top}.{current_key} must be a list")
            item = stripped[2:].strip()
            if item.startswith("pattern:"):
                current_rule = {"pattern": item.split(":", 1)[1].strip()}
                values.append(current_rule)
            else:
                values.append(item)
                current_rule = None
            continue
        if indent == 6 and current_rule is not None:
            key, value = _split_mapping(stripped)
            current_rule[key] = value
            continue
        raise OwnershipConfigError(f"unsupported ownership YAML line: {raw}")
    validate_ownership_config(config)
    return config


def validate_ownership_config(config: Mapping[str, Any]) -> None:
    version = config.get("schema_version")
    if version != SCHEMA_VERSION:
        raise OwnershipConfigError(f"unsupported ownership schema_version: {version!r}")
    defaults = _mapping(config.get("system_defaults"), "system_defaults")
    for key in ("skip_patterns", "protected", "system_locked", "rules"):
        if key not in defaults:
            raise OwnershipConfigError(f"system_defaults.{key} missing")
    overrides = _mapping(config.get("project_overrides"), "project_overrides")
    if "rules" not in overrides:
        raise OwnershipConfigError("project_overrides.rules missing")
    policy = _mapping(config.get("unknown_policy"), "unknown_policy")
    for key in ("source_new_file", "target_only_file", "both_exist_differ", "generated_or_cache"):
        if not policy.get(key):
            raise OwnershipConfigError(f"unknown_policy.{key} missing")
    for block_name, rules in (("system_defaults.rules", defaults.get("rules")), ("project_overrides.rules", overrides.get("rules"))):
        for rule in _sequence(rules, block_name):
            if not isinstance(rule, Mapping):
                raise OwnershipConfigError(f"{block_name} entries must be mappings")
            if not rule.get("pattern") or rule.get("owner") not in NORMAL_OWNERS:
                raise OwnershipConfigError(f"{block_name} has invalid rule: {rule!r}")


def classify_path(
    path: str | Path,
    config: Mapping[str, Any],
    *,
    source_exists: bool,
    target_exists: bool,
    content_equal: bool = False,
) -> Classification:
    validate_ownership_config(config)
    rel = normalize_path(path)
    defaults = _mapping(config["system_defaults"], "system_defaults")
    unknown = _mapping(config["unknown_policy"], "unknown_policy")

    skip_pattern = _first_match(defaults["skip_patterns"], rel)
    if skip_pattern:
        return Classification(rel, "skip_generated", str(unknown["generated_or_cache"]), "skip_patterns", skip_pattern)

    locked_pattern = _first_match(defaults["system_locked"], rel)

    if source_exists and target_exists and content_equal:
        return Classification(rel, "unchanged", "unchanged", "content_identical", system_locked=bool(locked_pattern))

    protected_pattern = _first_match(defaults["protected"], rel)
    if protected_pattern:
        return Classification(rel, "protected", "protected_preserve", "protected", protected_pattern, system_locked=bool(locked_pattern))

    owner, pattern, reason = _last_rule_match(defaults["rules"], rel, "system_defaults.rules")
    if not locked_pattern:
        override_owner, override_pattern, override_reason = _last_rule_match(
            _mapping(config["project_overrides"], "project_overrides")["rules"],
            rel,
            "project_overrides.rules",
        )
        if override_owner:
            owner, pattern, reason = override_owner, override_pattern, override_reason
    elif not owner:
        owner, pattern, reason = "system_owned", locked_pattern, "system_locked"

    if owner:
        return Classification(
            rel,
            owner,
            _action_for_owner(owner, source_exists=source_exists, target_exists=target_exists),
            reason,
            pattern,
            system_locked=bool(locked_pattern),
        )

    return Classification(
        rel,
        "unknown",
        _action_for_unknown(unknown, source_exists=source_exists, target_exists=target_exists),
        "unknown_policy",
    )


def compare_lock(
    current: Mapping[str, Classification],
    locked: Mapping[str, Mapping[str, str]],
) -> list[LockChange]:
    changes: list[LockChange] = []
    current_paths = set(current)
    locked_paths = set(locked)
    for path in sorted(current_paths - locked_paths):
        item = current[path]
        changes.append(LockChange(path, "lock_addition", current_owner=item.owner, current_action=item.action))
    for path in sorted(locked_paths - current_paths):
        old = locked[path]
        changes.append(LockChange(path, "lock_removal", previous_owner=str(old.get("owner", "")), previous_action=str(old.get("action", ""))))
    for path in sorted(current_paths & locked_paths):
        item = current[path]
        old = locked[path]
        old_owner = str(old.get("owner", ""))
        old_action = str(old.get("action", ""))
        if item.owner != old_owner or item.action != old_action:
            changes.append(
                LockChange(
                    path,
                    "classification_drift",
                    previous_owner=old_owner,
                    current_owner=item.owner,
                    previous_action=old_action,
                    current_action=item.action,
                )
            )
    return changes


def collect_repo_paths(root: str | Path) -> list[str]:
    base = Path(root)
    try:
        result = subprocess.run(
            ["git", "-C", str(base), "-c", "core.quotePath=false", "ls-files", "--cached", "--others", "--exclude-standard"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30,
            check=False,
        )
        if result.returncode == 0:
            return sorted({normalize_path(line) for line in result.stdout.splitlines() if line.strip()})
    except (OSError, subprocess.SubprocessError):
        pass
    paths: list[str] = []
    for path in base.rglob("*"):
        rel = normalize_path(path.relative_to(base))
        if ".git/" in f"{rel}/" or not path.is_file():
            continue
        paths.append(rel)
    return sorted(paths)


def classify_self(root: str | Path, config: Mapping[str, Any], paths: Sequence[str] | None = None) -> SelfClassificationReport:
    base = Path(root)
    rel_paths = list(paths) if paths is not None else collect_repo_paths(base)
    classifications: dict[str, Classification] = {}
    unknown: list[str] = []
    for rel in rel_paths:
        result = classify_path(rel, config, source_exists=True, target_exists=True, content_equal=False)
        if result.owner == "skip_generated":
            continue
        classifications[rel] = result
        if result.owner == "unknown":
            unknown.append(rel)
    return SelfClassificationReport(str(base), len(classifications), sorted(unknown), dict(sorted(classifications.items())))


def lock_payload(report: SelfClassificationReport) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "root": report.root,
        "total": report.total,
        "classifications": {
            path: {
                "owner": item.owner,
                "action": item.action,
                "reason": item.reason,
                "matched_pattern": item.matched_pattern,
                "system_locked": item.system_locked,
            }
            for path, item in sorted(report.classifications.items())
        },
    }


def write_lock(path: str | Path, report: SelfClassificationReport) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(lock_payload(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_lock(path: str | Path) -> dict[str, Mapping[str, str]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise OwnershipConfigError(f"unsupported lock schema_version: {payload.get('schema_version')!r}")
    classifications = payload.get("classifications")
    if not isinstance(classifications, Mapping):
        raise OwnershipConfigError("lock classifications must be a mapping")
    return {str(key): _mapping(value, f"classifications.{key}") for key, value in classifications.items()}


def lock_changes_for_root(root: str | Path, config: Mapping[str, Any], lock_path: str | Path) -> list[LockChange]:
    report = classify_self(root, config)
    locked = load_lock(lock_path)
    return compare_lock(report.classifications, locked)


def _split_mapping(text: str) -> tuple[str, str]:
    if ":" not in text:
        raise OwnershipConfigError(f"expected mapping line: {text}")
    key, value = text.split(":", 1)
    return key.strip(), value.strip().strip('"').strip("'")


def _ensure_dict(config: dict[str, Any], key: str) -> dict[str, Any]:
    value = config.setdefault(key, {})
    if not isinstance(value, dict):
        raise OwnershipConfigError(f"{key} must be a mapping")
    return value


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise OwnershipConfigError(f"{name} must be a mapping")
    return value


def _sequence(value: Any, name: str) -> Sequence[Any]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise OwnershipConfigError(f"{name} must be a list")
    return value


def _first_match(patterns: Any, path: str) -> str:
    for pattern in _sequence(patterns, "patterns"):
        if isinstance(pattern, str) and path_matches(pattern, path):
            return pattern
    return ""


def _last_rule_match(rules: Any, path: str, name: str) -> tuple[str, str, str]:
    owner = ""
    pattern = ""
    for rule in _sequence(rules, name):
        if isinstance(rule, Mapping) and path_matches(str(rule.get("pattern", "")), path):
            owner = str(rule.get("owner", ""))
            pattern = str(rule.get("pattern", ""))
    return (owner, pattern, name) if owner else ("", "", "")


def _action_for_owner(owner: str, *, source_exists: bool, target_exists: bool) -> str:
    if owner == "system_owned":
        if source_exists and target_exists:
            return "update_system"
        if source_exists:
            return "add_system"
        return "preserve_project"
    if owner == "project_owned":
        return "preserve_project"
    if owner == "manual_merge":
        if source_exists and target_exists:
            return "manual_merge"
        if source_exists:
            return "manual_approval"
        return "preserve_project"
    raise OwnershipConfigError(f"unknown owner: {owner}")


def _action_for_unknown(unknown: Mapping[str, Any], *, source_exists: bool, target_exists: bool) -> str:
    if source_exists and target_exists:
        return str(unknown["both_exist_differ"])
    if source_exists:
        return str(unknown["source_new_file"])
    if target_exists:
        return str(unknown["target_only_file"])
    return "absent"

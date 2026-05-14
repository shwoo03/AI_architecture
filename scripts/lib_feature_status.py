#!/usr/bin/env python3
"""Shared helpers for feature maturity manifest handling."""

from __future__ import annotations

from pathlib import Path
from typing import Any

TIERS = {"stable", "incubating", "experimental", "deprecated"}
PROFILE_TIERS = {
    "stable": {"stable"},
    "incubating": {"stable", "incubating"},
    "all": set(TIERS),
}
REQUIRED_FEATURE_FIELDS = {"id", "tier", "docs", "overlay_default"}


def manifest_path(root: Path) -> Path:
    return root / "docs" / "feature-status.yaml"


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value in {"true", "false"}:
        return value == "true"
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(part.strip()) for part in inner.split(",")]
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    try:
        return int(value)
    except ValueError:
        return value


def _split_key_value(line: str) -> tuple[str, Any]:
    key, _, value = line.partition(":")
    if key.strip() == "features" and not value.strip():
        return key.strip(), []
    return key.strip(), _parse_scalar(value.strip())


def load_feature_manifest(root: Path) -> dict[str, Any]:
    path = manifest_path(root)
    if not path.exists():
        raise FileNotFoundError(path)
    manifest: dict[str, Any] = {"features": []}
    current: dict[str, Any] | None = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if line.startswith("  - "):
            current = {}
            manifest.setdefault("features", []).append(current)
            key, value = _split_key_value(line[4:])
            current[key] = value
            continue
        if line.startswith("    ") and current is not None:
            key, value = _split_key_value(line[4:])
            current[key] = value
            continue
        key, value = _split_key_value(line)
        manifest[key] = value
    return manifest


def tiers_for_profile(profile: str) -> set[str]:
    if profile not in PROFILE_TIERS:
        raise ValueError(f"unsupported profile/tier: {profile}")
    return set(PROFILE_TIERS[profile])


def feature_counts(features: list[dict[str, Any]]) -> dict[str, int]:
    counts = {tier: 0 for tier in sorted(TIERS)}
    for feature in features:
        tier = str(feature.get("tier", ""))
        counts[tier] = counts.get(tier, 0) + 1
    return counts


def included_features(features: list[dict[str, Any]], profile: str) -> list[dict[str, Any]]:
    allowed = tiers_for_profile(profile)
    return [feature for feature in features if feature.get("tier") in allowed]


def skipped_features(features: list[dict[str, Any]], profile: str) -> list[dict[str, Any]]:
    allowed = tiers_for_profile(profile)
    return [feature for feature in features if feature.get("tier") not in allowed]


def feature_by_doc_path(features: list[dict[str, Any]], relative_path: str) -> dict[str, Any] | None:
    normalized = relative_path.replace("\\", "/")
    best: tuple[int, dict[str, Any]] | None = None
    for feature in features:
        docs = feature.get("docs") or []
        if not isinstance(docs, list):
            continue
        for doc in docs:
            doc_path = str(doc).replace("\\", "/").rstrip("/")
            if normalized == doc_path or normalized.startswith(doc_path + "/"):
                score = len(doc_path)
                if best is None or score > best[0]:
                    best = (score, feature)
    return best[1] if best else None


def validate_feature_manifest(root: Path, profile: str = "all") -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    path = manifest_path(root)
    try:
        manifest = load_feature_manifest(root)
    except FileNotFoundError:
        return {
            "ok": False,
            "path": str(path),
            "tier": profile,
            "features_by_tier": {},
            "included_features": [],
            "skipped_by_tier": [],
            "findings": [{"severity": "ERROR", "check": "manifest_exists", "detail": f"missing {path}"}],
        }
    features = manifest.get("features") or []
    if not isinstance(features, list):
        findings.append({"severity": "ERROR", "check": "features_list", "detail": "features must be a list"})
        features = []
    selected = included_features(features, profile)
    skipped = skipped_features(features, profile)
    selected_ids = {str(feature.get("id", "")) for feature in selected}
    for feature in features:
        feature_id = str(feature.get("id", "<missing-id>"))
        tier = feature.get("tier")
        if tier not in TIERS:
            findings.append({"severity": "ERROR", "check": "tier", "feature_id": feature_id, "detail": f"invalid tier: {tier}"})
        if feature_id not in selected_ids:
            continue
        missing = sorted(REQUIRED_FEATURE_FIELDS - set(feature.keys()))
        if missing:
            findings.append({"severity": "ERROR", "check": "required_fields", "feature_id": feature_id, "detail": f"missing fields: {', '.join(missing)}"})
        docs = feature.get("docs")
        if not isinstance(docs, list) or not docs:
            findings.append({"severity": "ERROR", "check": "docs", "feature_id": feature_id, "detail": "docs must be a non-empty list"})
            continue
        for doc in docs:
            doc_path = root / str(doc)
            if not doc_path.exists():
                findings.append({"severity": "ERROR", "check": "doc_exists", "feature_id": feature_id, "detail": f"missing doc path: {doc}"})
        if not isinstance(feature.get("overlay_default"), bool):
            findings.append({"severity": "ERROR", "check": "overlay_default", "feature_id": feature_id, "detail": "overlay_default must be boolean"})
    return {
        "ok": not any(finding.get("severity") == "ERROR" for finding in findings),
        "path": str(path),
        "tier": profile,
        "feature_count": len(features),
        "features_by_tier": feature_counts(features),
        "included_features": [str(feature.get("id")) for feature in selected],
        "skipped_by_tier": [str(feature.get("id")) for feature in skipped],
        "findings": findings,
    }

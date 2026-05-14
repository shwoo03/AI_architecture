#!/usr/bin/env python3
"""Validate and summarize docs/feature-status.yaml."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
from lib_feature_status import validate_feature_manifest


def render_text(payload: dict) -> str:
    lines = [f"feature-status {payload['tier']}: {'OK' if payload['ok'] else 'FAIL'}"]
    lines.append(f"manifest: {payload['path']}")
    lines.append(f"included: {len(payload.get('included_features', []))}")
    lines.append(f"skipped_by_tier: {len(payload.get('skipped_by_tier', []))}")
    for finding in payload.get("findings", []):
        feature = finding.get("feature_id", "manifest")
        lines.append(f"[{finding.get('severity')}] {feature}: {finding.get('detail')}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs="?", default="check", choices=["check"])
    parser.add_argument("--root", default=".")
    parser.add_argument("--tier", default="all", choices=["stable", "incubating", "all"])
    parser.add_argument("--format", default="text", choices=["text", "json"])
    args = parser.parse_args()

    payload = validate_feature_manifest(Path(args.root).resolve(), profile=args.tier)
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_text(payload))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())

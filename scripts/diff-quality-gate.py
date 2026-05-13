#!/usr/bin/env python3
"""Compare quality-gate JSON outputs and report newly introduced findings."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass


def load_payload(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def checks_by_name(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    checks = payload.get("checks", [])
    if not isinstance(checks, list):
        return result
    for item in checks:
        if isinstance(item, dict) and item.get("name"):
            result[str(item["name"])] = item
    return result


def non_ok(status: object) -> bool:
    return str(status or "").upper() in {"FAIL", "WARN", "ERROR"}


def compare(baseline: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    old = checks_by_name(baseline)
    new = checks_by_name(current)
    introduced: list[dict[str, Any]] = []
    fixed: list[dict[str, Any]] = []
    for name, check in sorted(new.items()):
        old_status = str(old.get(name, {}).get("status", "MISSING")).upper()
        new_status = str(check.get("status", "")).upper()
        if non_ok(new_status) and not non_ok(old_status):
            introduced.append({"name": name, "status": new_status, "previous_status": old_status, "detail": check.get("detail", "")})
    for name, check in sorted(old.items()):
        old_status = str(check.get("status", "")).upper()
        new_status = str(new.get(name, {}).get("status", "MISSING")).upper()
        if non_ok(old_status) and not non_ok(new_status):
            fixed.append({"name": name, "status": new_status, "previous_status": old_status})
    return {"ok": not introduced, "introduced": introduced, "fixed": fixed}


def render_text(payload: dict[str, Any]) -> str:
    lines = ["Diff-aware Quality Gate"]
    if not payload["introduced"]:
        lines.append("  OK no new WARN/FAIL checks")
    for item in payload["introduced"]:
        lines.append(f"  NEW {item['status']} {item['name']}: {item['detail']}")
    for item in payload["fixed"]:
        lines.append(f"  FIXED {item['name']}: {item['previous_status']} -> {item['status']}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--current", required=True)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()
    try:
        payload = compare(load_payload(Path(args.baseline)), load_payload(Path(args.current)))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"diff-quality-gate input error: {exc}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_text(payload))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

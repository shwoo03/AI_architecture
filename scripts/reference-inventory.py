#!/usr/bin/env python3
"""Check tracked references against candidate cards and proposal status."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import convert as convert_lib


try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass


FIELD_RE = re.compile(r"^-\s+`([^`]+)`:\s*(.*)$", re.MULTILINE)
SKIP_FILES = {"README.md", "_template.md"}


@dataclass
class Finding:
    severity: str
    check: str
    detail: str
    reference: str = ""


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def clean_value(value: str) -> str:
    stripped = value.strip()
    if len(stripped) >= 2 and stripped.startswith("`") and stripped.endswith("`"):
        return stripped[1:-1].strip()
    return stripped.strip('"').strip("'")


def parse_fields(text: str) -> dict[str, str]:
    return {match.group(1): clean_value(match.group(2)) for match in FIELD_RE.finditer(text)}


def parse_references(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    repos: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    in_repos = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = convert_lib._strip_comment(raw)
        if not line.strip():
            continue
        stripped = line.strip()
        if stripped == "repos:":
            in_repos = True
            continue
        if not in_repos:
            continue
        if stripped.startswith("- "):
            if current:
                repos.append(current)
            current = {}
            stripped = stripped[2:].strip()
            if not stripped:
                continue
        if current is None or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        current[key.strip()] = convert_lib._parse_scalar(value)
    if current:
        repos.append(current)
    return repos


def markdown_files(root: Path, directory: str) -> list[Path]:
    base = root / directory
    if not base.is_dir():
        return []
    return sorted(path for path in base.glob("*.md") if path.name not in SKIP_FILES and not path.name.startswith("."))


def slug(value: object) -> str:
    text = str(value or "").lower().replace(".git", "")
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def candidate_records(root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in markdown_files(root, "research/reference-candidates"):
        fields = parse_fields(path.read_text(encoding="utf-8", errors="replace"))
        records.append(
            {
                "path": path.relative_to(root).as_posix(),
                "name": fields.get("name", ""),
                "url": fields.get("url", ""),
                "status": fields.get("status", ""),
                "adoption_decision": fields.get("adoption_decision", ""),
                "proposal_needed": fields.get("proposal_needed", ""),
            }
        )
    return records


def proposal_records(root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in markdown_files(root, "runtime/proposals/reference-adoption"):
        fields = parse_fields(path.read_text(encoding="utf-8", errors="replace"))
        records.append(
            {
                "path": path.relative_to(root).as_posix(),
                "candidate_card": fields.get("candidate_card", ""),
                "proposal_type": fields.get("proposal_type", ""),
                "status": fields.get("status", ""),
                "decision": fields.get("decision", ""),
            }
        )
    return records


def candidate_matches(repo: dict[str, Any], candidate: dict[str, Any]) -> bool:
    repo_values = {slug(repo.get("name")), slug(Path(str(repo.get("local_path") or "")).name), slug(repo.get("url"))}
    candidate_values = {slug(candidate.get("name")), slug(candidate.get("url")), slug(candidate.get("path"))}
    return any(value and any(value == item or value in item for item in candidate_values) for value in repo_values)


def proposal_matches(candidate: dict[str, Any], proposal: dict[str, Any]) -> bool:
    candidate_path = str(candidate.get("path") or "")
    return bool(candidate_path and clean_value(str(proposal.get("candidate_card") or "")) == candidate_path)


def build_inventory(root: Path) -> dict[str, Any]:
    tracked = parse_references(root / "references.yaml")
    candidates = candidate_records(root)
    proposals = proposal_records(root)
    findings: list[Finding] = []
    tracked_payload: list[dict[str, Any]] = []
    for repo in tracked:
        name = str(repo.get("name") or repo.get("url") or "unnamed")
        matched_candidates = [candidate for candidate in candidates if candidate_matches(repo, candidate)]
        matched_proposals = [proposal for candidate in matched_candidates for proposal in proposals if proposal_matches(candidate, proposal)]
        if not matched_candidates:
            findings.append(Finding("WARN", "candidate_missing", "tracked reference has no candidate card", name))
        tracked_payload.append(
            {
                "name": name,
                "url": repo.get("url", ""),
                "local_path": repo.get("local_path", ""),
                "last_known_commit": repo.get("last_known_commit", ""),
                "candidate_cards": [item["path"] for item in matched_candidates],
                "proposals": [item["path"] for item in matched_proposals],
                "proposal_status": "present" if matched_proposals else "not_required_or_not_created",
            }
        )
    return {
        "ok": not any(item.severity == "WARN" for item in findings),
        "tracked_repos": tracked_payload,
        "candidate_cards": candidates,
        "proposals": proposals,
        "findings": [asdict(item) for item in findings],
    }


def render_text(payload: dict[str, Any]) -> str:
    lines = [
        "Reference Inventory",
        f"ok: {payload['ok']}",
        f"tracked_repos: {len(payload['tracked_repos'])}",
        f"candidate_cards: {len(payload['candidate_cards'])}",
        f"proposals: {len(payload['proposals'])}",
    ]
    for finding in payload["findings"]:
        lines.append(f"  {finding['severity']} {finding['check']} {finding['reference']}: {finding['detail']}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=None)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on WARN findings.")
    args = parser.parse_args()
    root = Path(args.root).resolve() if args.root else repo_root().resolve()
    if not root.is_dir():
        print(f"root not a directory: {root}", file=sys.stderr)
        return 2
    payload = build_inventory(root)
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_text(payload))
    return 1 if args.strict and not payload["ok"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

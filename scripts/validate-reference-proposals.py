#!/usr/bin/env python3
"""Validate reference-adoption dry-run proposal documents.

The checker validates concrete proposal files under
runtime/proposals/reference-adoption/. README.md and _template.md are skipped.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass


REQUIRED_FIELDS = [
    "status",
    "created_at",
    "candidate_card",
    "proposal_type",
    "approval_required",
    "absorption_mode",
    "recommended_mode",
    "reuse_boundary",
    "direct_implementation_reason",
    "decision_source",
    "decision",
    "decided_at",
    "decided_by",
    "applied_in",
    "validation_result",
]
ALLOWED_VALUES = {
    "status": {"proposed", "accepted", "rejected", "applied", "deferred"},
    "proposal_type": {"reference_adoption_dry_run"},
    "approval_required": {"yes", "no"},
    "absorption_mode": {
        "dependency",
        "wrapper",
        "partial_copy",
        "concept_only",
        "direct_implementation",
        "mixed",
    },
    "decision": {"pending", "accepted", "rejected", "applied", "deferred"},
}
REQUIRED_HEADINGS = [
    "## 상태",
    "## 한 문장 정의",
    "## 근거",
    "## 적용하지 않을 것",
    "## 모듈형 흡수 판단",
    "## 제안 변경",
    "## 기대 효과",
    "## 위험",
    "## 검증 계획",
    "## 롤백 또는 중단 조건",
    "## 승인 후 실제 변경 범위",
    "## 최종 결정 기록",
]
REQUIRED_PHRASES = [
    "python scripts/verify-skeleton.py",
    "python scripts/validate-reference-candidates.py",
    "python scripts/validate-reference-proposals.py",
]
SKIP_FILES = {"README.md", "_template.md"}
FIELD_RE = re.compile(r"^-[ \t]+`([^`]+)`:[ \t]*([^\r\n]*?)\r?$", re.MULTILINE)


@dataclass
class Finding:
    path: Path
    message: str


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def proposal_dir(root: Path) -> Path:
    return root / "runtime" / "proposals" / "reference-adoption"


def parse_fields(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    matches = list(FIELD_RE.finditer(text))
    for match in matches:
        fields[match.group(1)] = match.group(2).strip()
    return fields


def is_blank(value: str) -> bool:
    return value.strip() in {"", "-", "TBD", "todo", "TODO"}


def clean_value(value: str) -> str:
    stripped = value.strip()
    if len(stripped) >= 2 and stripped.startswith("`") and stripped.endswith("`"):
        return stripped[1:-1].strip()
    return stripped


def proposal_files(root: Path) -> list[Path]:
    directory = proposal_dir(root)
    if not directory.is_dir():
        return []
    return sorted(
        path
        for path in directory.glob("*.md")
        if path.name not in SKIP_FILES and not path.name.startswith(".")
    )


def validate_headings(path: Path, text: str, findings: list[Finding]) -> None:
    for heading in REQUIRED_HEADINGS:
        if heading not in text:
            findings.append(Finding(path, f"missing heading `{heading}`"))


def validate_fields(root: Path, path: Path, fields: dict[str, str], findings: list[Finding]) -> None:
    decision = clean_value(fields.get("decision", ""))
    absorption_mode = clean_value(fields.get("absorption_mode", ""))
    for field in REQUIRED_FIELDS:
        if field not in fields:
            findings.append(Finding(path, f"missing field `{field}`"))
            continue
        if field in {"decision_source", "decided_at", "decided_by", "applied_in", "validation_result"}:
            # Pending proposals legitimately leave final-decision fields blank.
            if decision == "pending":
                continue
        if is_blank(fields[field]):
            findings.append(Finding(path, f"field `{field}` is blank"))
    for field, allowed in ALLOWED_VALUES.items():
        value = clean_value(fields.get(field, ""))
        if value and value not in allowed:
            findings.append(
                Finding(
                    path,
                    f"field `{field}` has invalid value `{value}`; expected one of {sorted(allowed)}",
                )
            )
    candidate = clean_value(fields.get("candidate_card", ""))
    if candidate and not is_blank(candidate) and not (root / candidate).is_file():
        findings.append(Finding(path, f"candidate_card target does not exist: `{candidate}`"))
    if absorption_mode == "partial_copy":
        copy_boundary = clean_value(fields.get("copy_boundary", ""))
        if is_blank(copy_boundary):
            findings.append(
                Finding(
                    path,
                    "partial_copy proposal requires non-blank field `copy_boundary`",
                )
            )


def validate_list_section(path: Path, text: str, heading: str, findings: list[Finding]) -> None:
    index = text.find(heading)
    if index == -1:
        return
    tail = text[index + len(heading) :]
    next_heading = tail.find("\n## ")
    block = tail if next_heading == -1 else tail[:next_heading]
    if not re.search(r"^\s*-\s+\S", block, re.MULTILINE):
        findings.append(Finding(path, f"section `{heading}` has no bullet items"))


def validate_content(path: Path, text: str, findings: list[Finding]) -> None:
    for heading in (
        "## 적용하지 않을 것",
        "## 모듈형 흡수 판단",
        "## 기대 효과",
        "## 위험",
        "## 롤백 또는 중단 조건",
        "## 승인 후 실제 변경 범위",
    ):
        validate_list_section(path, text, heading, findings)
    for phrase in REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(Finding(path, f"missing validation command `{phrase}`"))


def validate(root: Path) -> tuple[list[Finding], int]:
    findings: list[Finding] = []
    files = proposal_files(root)
    for path in files:
        text = path.read_text(encoding="utf-8")
        fields = parse_fields(text)
        validate_headings(path, text, findings)
        validate_fields(root, path, fields, findings)
        validate_content(path, text, findings)
    return findings, len(files)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        default=None,
        help="Project root (defaults to this script's repository root).",
    )
    args = parser.parse_args()
    root = Path(args.root).resolve() if args.root else repo_root()
    findings, count = validate(root)
    if findings:
        print("reference proposal findings:")
        for finding in findings:
            rel = finding.path.relative_to(root).as_posix()
            print(f"  ERROR {rel}: {finding.message}")
        print(f"checked {count} reference proposal(s), {len(findings)} error(s)")
        return 1
    print(f"reference proposals OK: {count} proposal(s) checked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

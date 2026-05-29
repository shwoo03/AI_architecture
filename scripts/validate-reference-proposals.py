#!/usr/bin/env python3
"""Validate reference-adoption dry-run proposal documents.

The checker validates concrete proposal files under
runtime/proposals/reference-adoption/. README.md and _template.md are skipped.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass


ADOPTION_REQUIRED_FIELDS = [
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
REFRESH_REQUIRED_FIELDS = [
    "status",
    "created_at",
    "candidate_card",
    "proposal_type",
    "approval_required",
    "decision_source",
    "decision",
    "decided_at",
    "decided_by",
    "applied_in",
    "validation_result",
]
COMMON_ALLOWED_VALUES = {
    "status": {"proposed", "accepted", "rejected", "applied", "deferred", "superseded"},
    "proposal_type": {"reference_adoption_dry_run", "reference_refresh"},
    "approval_required": {"yes", "no"},
    "decision": {"pending", "accepted", "rejected", "applied", "deferred", "superseded"},
}
ADOPTION_ALLOWED_VALUES = {
    "absorption_mode": {
        "dependency",
        "wrapper",
        "partial_copy",
        "concept_only",
        "direct_implementation",
        "mixed",
    },
}
ADOPTION_REQUIRED_HEADINGS = [
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
REFRESH_REQUIRED_HEADINGS = [
    "## 상태",
    "## 한 문장 정의",
    "## 근거",
    "## 제안 변경",
    "## 검증 계획",
    "## 최종 결정 기록",
]
ADOPTION_REQUIRED_PHRASES = [
    "python scripts/verify-skeleton.py",
    "python scripts/validate-reference-candidates.py",
    "python scripts/validate-reference-proposals.py",
]
REFRESH_REQUIRED_PHRASES = [
    "python scripts/verify-skeleton.py",
    "python scripts/validate-reference-proposals.py",
]
SKIP_FILES = {"README.md", "_template.md"}
FIELD_RE = re.compile(r"^-[ \t]+`([^`]+)`:[ \t]*([^\r\n]*?)\r?$", re.MULTILINE)
WEAK_SOURCE_ANCHORS = {
    "",
    "-",
    "TBD",
    "todo",
    "TODO",
    "not checked",
    "not applicable",
    "n/a",
    "local-reference",
    "external-reference",
    "directory",
    "candidate-card",
}


@dataclass
class Finding:
    path: Path
    message: str
    severity: str = "ERROR"


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


def weak_source_anchor(value: str) -> bool:
    stripped = clean_value(value)
    if stripped in WEAK_SOURCE_ANCHORS:
        return True
    return not any(char.isdigit() for char in stripped)


def proposal_files(root: Path) -> list[Path]:
    directory = proposal_dir(root)
    if not directory.is_dir():
        return []
    return sorted(
        path
        for path in directory.glob("*.md")
        if path.name not in SKIP_FILES and not path.name.startswith(".")
    )


def validate_headings(path: Path, text: str, headings: list[str], findings: list[Finding]) -> None:
    for heading in headings:
        if heading not in text:
            findings.append(Finding(path, f"missing heading `{heading}`"))


def validate_fields(root: Path, path: Path, fields: dict[str, str], proposal_type: str, findings: list[Finding]) -> None:
    decision = clean_value(fields.get("decision", ""))
    status = clean_value(fields.get("status", ""))
    absorption_mode = clean_value(fields.get("absorption_mode", ""))
    required_fields = REFRESH_REQUIRED_FIELDS if proposal_type == "reference_refresh" else ADOPTION_REQUIRED_FIELDS
    for field in required_fields:
        if field not in fields:
            findings.append(Finding(path, f"missing field `{field}`"))
            continue
        if field in {"decision_source", "decided_at", "decided_by", "applied_in", "validation_result"}:
            # Pending proposals legitimately leave final-decision fields blank.
            if decision == "pending":
                continue
        if is_blank(fields[field]):
            findings.append(Finding(path, f"field `{field}` is blank"))
    allowed_values = dict(COMMON_ALLOWED_VALUES)
    if proposal_type == "reference_adoption_dry_run":
        allowed_values.update(ADOPTION_ALLOWED_VALUES)
    for field, allowed in allowed_values.items():
        value = clean_value(fields.get(field, ""))
        if value and value not in allowed:
            findings.append(
                Finding(
                    path,
                    f"field `{field}` has invalid value `{value}`; expected one of {sorted(allowed)}",
                )
            )
    candidate = clean_value(fields.get("candidate_card", ""))
    if candidate and not is_blank(candidate) and not (root / candidate).exists():
        findings.append(Finding(path, f"candidate_card target does not exist: `{candidate}`"))
    superseded_by = clean_value(fields.get("superseded_by", ""))
    supersedes = clean_value(fields.get("supersedes", ""))
    if status == "superseded" or decision == "superseded":
        if is_blank(superseded_by):
            findings.append(Finding(path, "superseded proposal requires non-blank field `superseded_by`"))
    for field, value in (("superseded_by", superseded_by), ("supersedes", supersedes)):
        if value and not is_blank(value) and not (root / value).exists():
            findings.append(Finding(path, f"{field} target does not exist: `{value}`"))
    if proposal_type == "reference_adoption_dry_run" and absorption_mode == "partial_copy":
        copy_boundary = clean_value(fields.get("copy_boundary", ""))
        if is_blank(copy_boundary):
            findings.append(
                Finding(
                    path,
                    "partial_copy proposal requires non-blank field `copy_boundary`",
                )
            )
    if proposal_type == "reference_adoption_dry_run" and absorption_mode == "direct_implementation":
        reason = clean_value(fields.get("direct_implementation_reason", ""))
        if is_blank(reason) or reason.lower() in {"not applicable", "n/a"}:
            findings.append(
                Finding(
                    path,
                    "direct_implementation proposal requires a concrete `direct_implementation_reason`",
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


def validate_content(path: Path, text: str, proposal_type: str, findings: list[Finding]) -> None:
    if proposal_type == "reference_refresh":
        for phrase in REFRESH_REQUIRED_PHRASES:
            if phrase not in text:
                findings.append(Finding(path, f"missing validation command `{phrase}`"))
        return
    for heading in (
        "## 적용하지 않을 것",
        "## 모듈형 흡수 판단",
        "## 기대 효과",
        "## 위험",
        "## 롤백 또는 중단 조건",
        "## 승인 후 실제 변경 범위",
    ):
        validate_list_section(path, text, heading, findings)
    for phrase in ADOPTION_REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(Finding(path, f"missing validation command `{phrase}`"))
    marker = "Source-backed evidence:"
    if marker not in text:
        findings.append(Finding(path, "missing source-backed evidence section"))
    else:
        tail = text[text.find(marker) + len(marker) :]
        next_heading = tail.find("\n## ")
        block = tail if next_heading == -1 else tail[:next_heading]
        if not re.search(r"^\s*-\s+\S", block, re.MULTILINE):
            findings.append(Finding(path, "source-backed evidence section has no bullet items"))


def validate_candidate_source_anchor(root: Path, path: Path, candidate: str, findings: list[Finding]) -> None:
    if not candidate or is_blank(candidate):
        return
    candidate_path = root / candidate
    try:
        rel = candidate_path.relative_to(root)
    except ValueError:
        return
    if rel.parts[:2] != ("research", "reference-candidates") or not candidate_path.is_file():
        return
    text = candidate_path.read_text(encoding="utf-8")
    fields = parse_fields(text)
    revision = fields.get("checked_revision", "")
    freshness = fields.get("freshness_signal", "")
    if weak_source_anchor(revision):
        findings.append(Finding(path, f"strict source anchor requires concrete checked_revision in `{candidate}`"))
    if is_blank(freshness) or "requires" in freshness.lower():
        findings.append(Finding(path, f"strict source anchor requires concrete freshness_signal in `{candidate}`"))
    marker = "- `sources`:"
    index = text.find(marker)
    if index == -1:
        return
    tail = text[index + len(marker) :]
    next_field = tail.find("\n- `")
    block = tail if next_field == -1 else tail[:next_field]
    source_lines = [line.strip()[2:].strip() for line in block.splitlines() if line.strip().startswith("- ")]
    for offset, line in enumerate(source_lines, start=1):
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            findings.append(Finding(path, f"strict source anchor requires `{candidate}` sources item {offset} to use JSON object syntax"))
            continue
        if not isinstance(item, dict):
            findings.append(Finding(path, f"strict source anchor requires `{candidate}` sources item {offset} to be an object"))
            continue
        if weak_source_anchor(str(item.get("hash_or_line_ref", ""))):
            findings.append(Finding(path, f"strict source anchor requires concrete hash_or_line_ref in `{candidate}` sources item {offset}"))


def validate_proposal_source_anchor(path: Path, text: str, proposal_type: str, findings: list[Finding]) -> None:
    if proposal_type == "reference_refresh":
        return
    marker = "Source-backed evidence:"
    index = text.find(marker)
    if index == -1:
        return
    tail = text[index + len(marker) :]
    next_heading = tail.find("\n## ")
    block = tail if next_heading == -1 else tail[:next_heading]
    bullets = [line.strip()[2:].strip() for line in block.splitlines() if line.strip().startswith("- ")]
    for offset, bullet in enumerate(bullets, start=1):
        if not any(token in bullet for token in ("hash_or_line_ref", "checked_revision", "line", "lines", "commit", "@")):
            findings.append(Finding(path, f"strict source anchor requires source-backed evidence bullet {offset} to cite a concrete anchor"))


def validate(root: Path, *, strict_source_anchor: bool = False) -> tuple[list[Finding], int]:
    findings: list[Finding] = []
    files = proposal_files(root)
    for path in files:
        text = path.read_text(encoding="utf-8")
        fields = parse_fields(text)
        proposal_type = clean_value(fields.get("proposal_type", ""))
        if proposal_type not in COMMON_ALLOWED_VALUES["proposal_type"]:
            findings.append(Finding(path, f"field `proposal_type` has invalid value `{proposal_type}`; expected one of {sorted(COMMON_ALLOWED_VALUES['proposal_type'])}"))
            proposal_type = "reference_adoption_dry_run"
        headings = REFRESH_REQUIRED_HEADINGS if proposal_type == "reference_refresh" else ADOPTION_REQUIRED_HEADINGS
        validate_headings(path, text, headings, findings)
        validate_fields(root, path, fields, proposal_type, findings)
        validate_content(path, text, proposal_type, findings)
        if strict_source_anchor:
            validate_candidate_source_anchor(root, path, clean_value(fields.get("candidate_card", "")), findings)
            validate_proposal_source_anchor(path, text, proposal_type, findings)
    return findings, len(files)


def lifecycle_warnings(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in proposal_files(root):
        text = path.read_text(encoding="utf-8")
        fields = parse_fields(text)
        decision = clean_value(fields.get("decision", ""))
        status = clean_value(fields.get("status", ""))
        if decision not in {"accepted", "applied"} and status not in {"accepted", "applied"}:
            continue
        applied_in = clean_value(fields.get("applied_in", ""))
        validation_result = clean_value(fields.get("validation_result", ""))
        decided_at = clean_value(fields.get("decided_at", ""))
        decided_by = clean_value(fields.get("decided_by", ""))
        weak_values = {"", "-", "TBD", "todo", "TODO", "pending", "not run", "not run in this turn", "not recorded", "n/a"}
        if applied_in.strip().lower() in weak_values:
            findings.append(Finding(path, "accepted/applied proposal has no concrete `applied_in` evidence", "WARN"))
        if validation_result.strip().lower() in weak_values:
            findings.append(Finding(path, "accepted/applied proposal has no concrete `validation_result` evidence", "WARN"))
        if decided_at.strip().lower() in weak_values or decided_by.strip().lower() in weak_values:
            findings.append(Finding(path, "accepted/applied proposal has incomplete decision evidence", "WARN"))
    return findings


def finding_payload(root: Path, finding: Finding) -> dict[str, str]:
    payload = asdict(finding)
    payload["path"] = finding.path.relative_to(root).as_posix()
    return payload


def render_json(root: Path, findings: list[Finding], count: int) -> str:
    errors = sum(1 for finding in findings if finding.severity == "ERROR")
    warnings = sum(1 for finding in findings if finding.severity == "WARN")
    payload = {
        "ok": errors == 0 and warnings == 0,
        "summary": {"ERROR": errors, "WARN": warnings, "checked": count},
        "findings": [finding_payload(root, finding) for finding in findings],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        default=None,
        help="Project root (defaults to this script's repository root).",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--lifecycle", action="store_true", help="Warn about accepted/applied proposals missing application or validation evidence.")
    parser.add_argument("--strict-lifecycle", action="store_true", help="Fail when lifecycle warnings are present.")
    parser.add_argument("--strict-source-anchor", action="store_true", help="Require concrete source anchors in linked candidate cards and source evidence.")
    args = parser.parse_args()
    root = Path(args.root).resolve() if args.root else repo_root()
    findings, count = validate(root, strict_source_anchor=args.strict_source_anchor)
    if args.lifecycle:
        findings.extend(lifecycle_warnings(root))
    if args.format == "json":
        print(render_json(root, findings, count))
    elif findings:
        print("reference proposal findings:")
        for finding in findings:
            rel = finding.path.relative_to(root).as_posix()
            print(f"  {finding.severity} {rel}: {finding.message}")
        errors = sum(1 for finding in findings if finding.severity == "ERROR")
        warnings = sum(1 for finding in findings if finding.severity == "WARN")
        print(f"checked {count} reference proposal(s), {errors} error(s), {warnings} warning(s)")
    else:
        print(f"reference proposals OK: {count} proposal(s) checked")
    errors = any(finding.severity == "ERROR" for finding in findings)
    warnings = any(finding.severity == "WARN" for finding in findings)
    return 1 if errors or (args.strict_lifecycle and warnings) else 0


if __name__ == "__main__":
    raise SystemExit(main())

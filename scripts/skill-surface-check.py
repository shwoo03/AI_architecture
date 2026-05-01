#!/usr/bin/env python3
"""Check that project skills avoid duplicated Codex/Claude maintenance surface."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path


try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass


FRONTMATTER_RE = re.compile(r"^---\r?\n(.*?)\r?\n---", re.DOTALL)
CODEX_SKILLS = Path(".codex") / "skills"
CLAUDE_SKILLS = Path(".claude") / "skills"


@dataclass
class Finding:
    severity: str
    check: str
    path: str
    detail: str


@dataclass
class SkillSurfaceResult:
    root: str
    summary: dict[str, int]
    codex_skills: int
    claude_skills: int
    duplicate_files: int
    shimmed_claude_skills: int
    findings: list[dict[str, object]]


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def skill_dirs(base: Path) -> list[Path]:
    if not base.is_dir():
        return []
    return sorted(path for path in base.iterdir() if path.is_dir())


def is_shim(path: Path, skill_name: str) -> bool:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    expected = f"../../../.codex/skills/{skill_name}/SKILL.md"
    return "Compatibility Shim" in text and expected in text


def has_frontmatter(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return bool(FRONTMATTER_RE.search(text))


def find_duplicate_files(root: Path) -> list[list[Path]]:
    files: list[Path] = []
    for base in (root / CODEX_SKILLS, root / CLAUDE_SKILLS):
        if base.is_dir():
            files.extend(path for path in base.rglob("*") if path.is_file())
    by_digest: dict[str, list[Path]] = {}
    for path in files:
        by_digest.setdefault(sha256(path), []).append(path)
    duplicate_groups: list[list[Path]] = []
    codex_root = root / CODEX_SKILLS
    claude_root = root / CLAUDE_SKILLS
    for group in by_digest.values():
        if len(group) <= 1:
            continue
        has_codex = any(codex_root in path.parents for path in group)
        has_claude = any(claude_root in path.parents for path in group)
        if has_codex and has_claude:
            duplicate_groups.append(group)
    return duplicate_groups


def run_check(root: Path) -> SkillSurfaceResult:
    findings: list[Finding] = []
    codex_base = root / CODEX_SKILLS
    claude_base = root / CLAUDE_SKILLS
    codex_dirs = skill_dirs(codex_base)
    claude_dirs = skill_dirs(claude_base)
    codex_names = {path.name for path in codex_dirs}
    shimmed = 0

    for path in codex_dirs:
        skill_file = path / "SKILL.md"
        if not skill_file.exists():
            findings.append(Finding("ERROR", "canonical_skill_missing", rel(skill_file, root), "canonical skill has no SKILL.md"))
        elif not has_frontmatter(skill_file):
            findings.append(Finding("ERROR", "canonical_frontmatter_missing", rel(skill_file, root), "canonical SKILL.md has no frontmatter"))

    for path in claude_dirs:
        skill_file = path / "SKILL.md"
        if not skill_file.exists():
            findings.append(Finding("ERROR", "claude_skill_missing", rel(skill_file, root), "Claude skill has no SKILL.md"))
            continue
        if path.name in codex_names:
            extra_files = [item for item in path.rglob("*") if item.is_file() and item.name != "SKILL.md"]
            if extra_files:
                findings.append(
                    Finding(
                        "ERROR",
                        "claude_duplicate_payload",
                        rel(path, root),
                        f"Claude shim for canonical skill must not keep payload files: {len(extra_files)} found",
                    )
                )
            if is_shim(skill_file, path.name):
                shimmed += 1
            else:
                findings.append(
                    Finding(
                        "ERROR",
                        "claude_shim_missing",
                        rel(skill_file, root),
                        "Claude skill shadows a Codex canonical skill without a compatibility shim",
                    )
                )
        elif not has_frontmatter(skill_file):
            findings.append(Finding("ERROR", "claude_frontmatter_missing", rel(skill_file, root), "Claude-only SKILL.md has no frontmatter"))

    duplicate_groups = find_duplicate_files(root)
    duplicate_files = sum(len(group) for group in duplicate_groups)
    if duplicate_files:
        examples = ", ".join(rel(path, root) for path in duplicate_groups[0][:3])
        findings.append(Finding("WARN", "duplicate_skill_files", ".", f"{duplicate_files} duplicate skill files remain; first group: {examples}"))

    summary = dict(Counter(finding.severity for finding in findings))
    for severity in ("ERROR", "WARN", "INFO"):
        summary.setdefault(severity, 0)
    return SkillSurfaceResult(
        root=str(root),
        summary=summary,
        codex_skills=len(codex_dirs),
        claude_skills=len(claude_dirs),
        duplicate_files=duplicate_files,
        shimmed_claude_skills=shimmed,
        findings=[asdict(finding) for finding in findings],
    )


def render_text(result: SkillSurfaceResult) -> str:
    lines = [
        "Skill Surface Check",
        f"root: {result.root}",
        "summary: "
        f"error={result.summary.get('ERROR', 0)}, "
        f"warn={result.summary.get('WARN', 0)}, "
        f"info={result.summary.get('INFO', 0)}",
        f"codex_skills: {result.codex_skills}",
        f"claude_skills: {result.claude_skills}",
        f"shimmed_claude_skills: {result.shimmed_claude_skills}",
        f"duplicate_files: {result.duplicate_files}",
    ]
    for finding in result.findings:
        lines.append(f"  {finding['severity']:<5} [{finding['check']}] {finding['path']}: {finding['detail']}")
    if not result.findings:
        lines.append("  OK skill surface is canonicalized")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=None, help="Project root (default: this skeleton root).")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--strict", action="store_true", help="Fail on warnings as well as errors.")
    args = parser.parse_args()

    root = Path(args.root).resolve() if args.root else repo_root().resolve()
    if not root.is_dir():
        print(f"root not a directory: {root}", file=sys.stderr)
        return 2
    result = run_check(root)
    if args.format == "json":
        print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    else:
        print(render_text(result))
    has_error = result.summary.get("ERROR", 0) > 0
    has_warn = result.summary.get("WARN", 0) > 0
    return 1 if has_error or (args.strict and has_warn) else 0


if __name__ == "__main__":
    raise SystemExit(main())

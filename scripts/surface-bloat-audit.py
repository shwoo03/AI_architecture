#!/usr/bin/env python3
"""Read-only audit for skill and agent surface bloat.

The audit reports mechanical surface-control signals only. It never deletes,
moves, promotes, or demotes skills/agents.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass


FRONTMATTER_RE = re.compile(r"^---\r?\n(.*?)\r?\n---", re.DOTALL)
SKILL_ROOTS = {
    "active": "skills/active",
    "candidate": "skills/_candidates",
    "meta": "skills/_meta",
    "deprecated": "skills/_deprecated",
}


@dataclass
class SurfaceEntry:
    kind: str
    name: str
    status: str
    path: str
    references: int


@dataclass
class Finding:
    severity: str
    check: str
    path: str
    detail: str
    recommendation: str


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def parse_frontmatter(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    fields: dict[str, Any] = {}
    current_key = ""
    for raw in match.group(1).splitlines():
        stripped = raw.strip()
        if not stripped:
            continue
        if stripped.startswith("- ") and current_key:
            fields.setdefault(current_key, []).append(stripped[2:].strip().strip("'\""))
            continue
        if ":" not in stripped:
            current_key = ""
            continue
        key, value = stripped.split(":", 1)
        current_key = key.strip()
        value = value.strip()
        if not value:
            fields[current_key] = []
        else:
            fields[current_key] = value.strip("'\"")
            current_key = ""
    return fields


def generated_names(root: Path, path: str) -> set[str]:
    directory = root / path
    if not directory.is_dir():
        return set()
    return {item.name for item in directory.iterdir() if item.name != ".gitkeep" and not item.name.startswith(".")}


def iter_text_files(root: Path) -> list[Path]:
    skipped = {".git", ".codex", ".claude", "node_modules", "__pycache__", ".pytest_cache", "runtime"}
    files: list[Path] = []
    for path in root.rglob("*"):
        if any(part in skipped for part in path.relative_to(root).parts):
            continue
        if path.is_file() and path.suffix.lower() in {".md", ".py", ".yaml", ".yml", ".json", ".toml"}:
            files.append(path)
    return files


def reference_count(root: Path, name: str, own_path: str, corpus: list[Path]) -> int:
    if not name:
        return 0
    pattern = re.compile(rf"(?<![A-Za-z0-9_-]){re.escape(name)}(?![A-Za-z0-9_-])")
    count = 0
    own = root / own_path
    for path in corpus:
        try:
            path.relative_to(own)
            continue
        except ValueError:
            pass
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if pattern.search(text):
            count += 1
    return count


def collect_skills(root: Path, corpus: list[Path], findings: list[Finding]) -> list[SurfaceEntry]:
    entries: list[SurfaceEntry] = []
    for status, root_rel in SKILL_ROOTS.items():
        directory = root / root_rel
        if not directory.is_dir():
            continue
        for path in sorted(directory.iterdir()):
            skill_file = path / "SKILL.md"
            if not path.is_dir():
                continue
            if not skill_file.exists():
                findings.append(
                    Finding(
                        "ERROR",
                        "skill_source_missing",
                        rel(skill_file, root),
                        "skill directory has no SKILL.md",
                        "Restore SKILL.md or remove the directory from the canonical skill surface.",
                    )
                )
                continue
            fields = parse_frontmatter(skill_file)
            name = str(fields.get("name") or path.name).strip()
            own = rel(path, root)
            entries.append(SurfaceEntry("skill", name, status, own, reference_count(root, name, own, corpus)))
    return entries


def collect_agents(root: Path, corpus: list[Path]) -> list[SurfaceEntry]:
    entries: list[SurfaceEntry] = []
    directory = root / "agents"
    if not directory.is_dir():
        return entries
    for path in sorted(directory.glob("*.md")):
        name = path.stem
        own = rel(path, root)
        entries.append(SurfaceEntry("agent", name, "active", own, reference_count(root, name, own, corpus)))
    return entries


def duplicate_findings(entries: list[SurfaceEntry]) -> list[Finding]:
    findings: list[Finding] = []
    by_key: dict[tuple[str, str], list[SurfaceEntry]] = defaultdict(list)
    for entry in entries:
        by_key[(entry.kind, entry.name)].append(entry)
    for (kind, name), matches in sorted(by_key.items()):
        if len(matches) <= 1:
            continue
        paths = ", ".join(match.path for match in matches)
        findings.append(
            Finding(
                "ERROR",
                f"{kind}_duplicate",
                paths,
                f"duplicate {kind} name `{name}`",
                "Keep one canonical entry or mark aliases/deprecated entries explicitly before generated export.",
            )
        )
    return findings


def parity_findings(root: Path, skills: list[SurfaceEntry], agents: list[SurfaceEntry]) -> list[Finding]:
    findings: list[Finding] = []
    active_skill_dirs = {Path(entry.path).name for entry in skills if entry.status == "active"}
    deprecated_skill_dirs = {Path(entry.path).name for entry in skills if entry.status == "deprecated"}
    active_agent_files = {Path(entry.path).name for entry in agents if entry.status == "active"}
    expected_agents = set(active_agent_files)
    for generated_path in (".codex/skills", ".claude/skills"):
        generated = generated_names(root, generated_path)
        leaked = sorted(deprecated_skill_dirs & generated)
        if leaked:
            findings.append(
                Finding(
                    "ERROR",
                    "deprecated_skill_generated",
                    generated_path,
                    f"deprecated skills generated into runtime surface: {leaked}",
                    "Remove deprecated skills from generated surfaces by regenerating from active canonical skills only.",
                )
            )
    for label, expected, actual_path in (
        ("codex_skill", active_skill_dirs, ".codex/skills"),
        ("claude_skill", active_skill_dirs, ".claude/skills"),
        ("codex_agent", expected_agents, ".codex/agents"),
        ("claude_agent", expected_agents, ".claude/agents"),
    ):
        actual = generated_names(root, actual_path)
        if expected == actual:
            continue
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        findings.append(
            Finding(
                "ERROR",
                f"{label}_manifest_disk_mismatch",
                actual_path,
                f"expected={sorted(expected)} actual={sorted(actual)} missing={missing} extra={extra}",
                "Regenerate generated surfaces with `python3 scripts/convert.py --root <target>`; do not edit generated files directly.",
            )
        )
    return findings


def bloat_findings(entries: list[SurfaceEntry]) -> list[Finding]:
    findings: list[Finding] = []
    for entry in entries:
        if entry.status == "deprecated" and entry.references > 0:
            findings.append(
                Finding(
                    "WARN",
                    f"{entry.kind}_deprecated_referenced",
                    entry.path,
                    f"`{entry.name}` is deprecated but referenced from {entry.references} file(s)",
                    "Review callers before removing or replacing this surface.",
                )
            )
        if entry.status in {"active", "candidate"} and entry.references == 0:
            findings.append(
                Finding(
                    "INFO",
                    f"{entry.kind}_orphan_candidate",
                    entry.path,
                    f"`{entry.name}` has no textual references outside its own path",
                    "Treat as a review signal only; external trigger-based use may still be valid.",
                )
            )
    return findings


def run_audit(root: Path) -> dict[str, Any]:
    corpus = iter_text_files(root)
    pre_findings: list[Finding] = []
    skills = collect_skills(root, corpus, pre_findings)
    agents = collect_agents(root, corpus)
    findings = [
        *pre_findings,
        *duplicate_findings([*skills, *agents]),
        *parity_findings(root, skills, agents),
        *bloat_findings([*skills, *agents]),
    ]
    summary = dict(Counter(finding.severity for finding in findings))
    for severity in ("ERROR", "WARN", "INFO"):
        summary.setdefault(severity, 0)
    return {
        "root": str(root),
        "ok": summary["ERROR"] == 0,
        "summary": summary,
        "entries": {
            "skills": [asdict(entry) for entry in skills],
            "agents": [asdict(entry) for entry in agents],
        },
        "findings": [asdict(finding) for finding in findings],
        "read_only": True,
        "mutates_files": False,
    }


def render_text(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "Surface Bloat Audit",
        f"root: {payload['root']}",
        f"summary: error={summary['ERROR']}, warn={summary['WARN']}, info={summary['INFO']}",
        f"skills: {len(payload['entries']['skills'])}",
        f"agents: {len(payload['entries']['agents'])}",
    ]
    for finding in payload["findings"]:
        lines.append(f"  {finding['severity']:<5} [{finding['check']}] {finding['path']}: {finding['detail']}")
    if not payload["findings"]:
        lines.append("  OK no mechanical bloat signals found")
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
    payload = run_audit(root)
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_text(payload))
    summary = payload["summary"]
    return 1 if summary["ERROR"] or (args.strict and summary["WARN"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())

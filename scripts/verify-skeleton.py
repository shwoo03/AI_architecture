#!/usr/bin/env python3
"""Verify that a copy of this skeleton (or the skeleton itself) is internally
consistent. Intended for quick health checks after edits or immediately after
`scripts/bootstrap/new-project.py` runs.

Exit code 0 if all checks pass; non-zero if any check fails.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tokenize
from dataclasses import dataclass
from pathlib import Path


# Ensure non-ASCII output (em-dash, Korean, etc.) prints cleanly on Windows
# consoles that default to cp949 / cp1252.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass


CLAUDE_MD_LINE_LIMIT = 60
REQUIRED_TOP_LEVEL = ["AGENTS.md", "CLAUDE.md", "README.md"]
# Required paths are grouped by why they are mandatory. This keeps the
# verifier from turning into an undifferentiated list and makes future slimming
# decisions safer: move paths between groups intentionally instead of deleting
# them from one large bucket.
REQUIRED_CORE_DOCS = [
    "docs/README.md",
    "docs/PROJECT_PROFILE.md",
    "docs/PROJECT_PROFILE.template.md",
    "docs/PROJECT_SPEC.template.md",
    "docs/PROJECT_OPERATING_PLAN.template.md",
    "docs/OPERATING_LOOP.md",
    "docs/SESSION_CONTINUITY.md",
    "docs/SKELETON_UPGRADE.md",
    "docs/ARCHITECTURE.md",
    "docs/GOVERNANCE.md",
    "docs/AGENT_REGISTRY.md",
    "docs/WORKFLOW_CATALOG.md",
    "docs/decisions/README.md",
    "docs/PIVOT_TRIGGERS.md",
    "docs/THREE_LAYER_MODEL.md",
    "docs/SKILL_DISTRIBUTION_MODEL.md",
    "docs/RUNTIME_EVENT_SCHEMA.md",
    "docs/FEATURE_DECISION_GUIDE.md",
    "docs/DOCUMENTATION_STYLE_GUIDE.md",
    "docs/NOTION_DOCUMENTATION_RULES.md",
]
REQUIRED_REFERENCE_DOCS = [
    "docs/REFERENCE_REVIEW.template.md",
    "docs/REFERENCE_DISCOVERY_WORKFLOW.md",
    "docs/decisions/ADR-0001-reference-discovery-and-adoption.md",
    "research/reference-candidates/README.md",
    "research/reference-candidates/_template.md",
    "runtime/external-repos/README.md",
    "runtime/proposals/reference-adoption/README.md",
    "runtime/proposals/reference-adoption/_template.md",
]
REQUIRED_RUNTIME_DOCS = [
    "docs/RUNTIME_STARTUP.template.md",
    "runtime/state/session-handoff.md",
    "runtime/activity-log.jsonl",
    "runtime/review-queue.jsonl",
]
REQUIRED_WIKI_DOCS = [
    "docs/wiki-ops/wiki-query.md",
    "docs/wiki-ops/wiki-lint.md",
    "knowledge/index.md",
]
REQUIRED_RULE_DOCS = [
    "rules/common/README.md",
    "rules/common/search-first.md",
    "rules/common/tdd-workflow.md",
    "rules/common/verification-loop.md",
    "rules/common/security-review.md",
    "rules/common/mcp-discipline.md",
    "rules/common/code-style.md",
    "rules/common/directory-layout.md",
    "rules/common/ephemeral-files.md",
    "rules/languages/README.md",
    "rules/languages/python/README.md",
    "rules/languages/typescript/README.md",
    "examples/README.md",
]
REQUIRED_DOCS = (
    REQUIRED_CORE_DOCS
    + REQUIRED_REFERENCE_DOCS
    + REQUIRED_RUNTIME_DOCS
    + REQUIRED_WIKI_DOCS
    + REQUIRED_RULE_DOCS
)
REQUIRED_RUNTIME_DIRS = [
    "runtime/state",
    "runtime/external-repos",
    "runtime/proposals",
    "runtime/validation",
    "runtime/schedules",
]
REMOVED_PATHS = [
    "runtime/memory",
    "codex/agents/memory-curator.md",
    "knowledge/workflows/wiki-ingest.md",
]
# Recovery hints for well-known required paths. Keeps error messages
# actionable: "missing X" alone tells an operator *what* but not *how to fix*.
# Unlisted paths fall back to a generic "restore from skeleton" hint so we do
# not silently degrade when new required paths are added.
RECOVERY_HINTS = {
    "runtime/state/session-handoff.md": (
        "run scripts/bootstrap/new-project.py into this tree, or copy the "
        "template body from docs/SESSION_CONTINUITY.md"
    ),
    "runtime/activity-log.jsonl": (
        "create an empty file: `touch runtime/activity-log.jsonl`. "
        "The post-tool-use hook will populate it on the next tool call."
    ),
    "runtime/review-queue.jsonl": (
        "create an empty file: `touch runtime/review-queue.jsonl`. "
        "scripts/review-queue.py will append decision events when needed."
    ),
    "knowledge/index.md": (
        "bootstrap re-seeds this; otherwise copy the starter table from "
        "docs/wiki-ops/wiki-lint.md"
    ),
    "docs/PROJECT_PROFILE.template.md": (
        "restore from the skeleton; this file is the single source of truth "
        "for the profile schema"
    ),
    "docs/REFERENCE_REVIEW.template.md": (
        "restore from the skeleton; new projects use this to record which "
        "external references were adopted, adapted, deferred, or rejected"
    ),
    "docs/RUNTIME_STARTUP.template.md": (
        "restore from the skeleton; new projects use this to record startup "
        "commands, env, ports, healthchecks, and failure signals"
    ),
    "CLAUDE.md": "restore from the skeleton root; see docs/SKELETON_UPGRADE.md",
    "AGENTS.md": "restore from the skeleton root; see docs/SKELETON_UPGRADE.md",
}
FRONTMATTER_PATTERN = re.compile(r"^---\r?\n(.*?)\r?\n---", re.DOTALL)
AGENT_REQUIRED_FIELDS = ["name", "description"]
CLARIFICATION_OK = re.compile(r"\[NEEDS CLARIFICATION:\s*\S[^\]]*\]")
CLARIFICATION_BARE = re.compile(r"\[NEEDS CLARIFICATION(?:\s*:\s*)?\]")
CLARIFICATION_SEARCH_DIRS = ["docs"]
CLARIFICATION_SKIP_NAMES = {
    "PROJECT_PROFILE.template.md",
    "PROJECT_SPEC.template.md",
    "README.md",
    "OPERATING_LOOP.md",
}


@dataclass
class Finding:
    level: str  # "error", "warn", or "info"
    check: str
    detail: str


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def check_claude_md_size(root: Path, findings: list[Finding]) -> None:
    path = root / "CLAUDE.md"
    if not path.exists():
        findings.append(Finding("error", "claude_md_size", "CLAUDE.md missing"))
        return
    lines = path.read_text(encoding="utf-8").splitlines()
    if len(lines) > CLAUDE_MD_LINE_LIMIT:
        findings.append(
            Finding(
                "error",
                "claude_md_size",
                f"CLAUDE.md is {len(lines)} lines; target is <= {CLAUDE_MD_LINE_LIMIT}",
            )
        )


def _with_hint(rel: str, base_msg: str) -> str:
    hint = RECOVERY_HINTS.get(rel)
    if hint:
        return f"{base_msg} -- fix: {hint}"
    # Generic fallback: point at the upgrade doc so the operator knows where
    # to look even for paths we have not hand-hinted.
    return f"{base_msg} -- fix: restore from the skeleton (see docs/SKELETON_UPGRADE.md)"


def check_required_paths(root: Path, findings: list[Finding]) -> None:
    for rel in REQUIRED_TOP_LEVEL + REQUIRED_DOCS:
        if not (root / rel).exists():
            findings.append(
                Finding(
                    "error",
                    "required_path_missing",
                    _with_hint(rel, f"missing {rel}"),
                )
            )
    for rel in REQUIRED_RUNTIME_DIRS:
        if not (root / rel).is_dir():
            findings.append(
                Finding(
                    "error",
                    "required_dir_missing",
                    _with_hint(rel, f"missing directory {rel}"),
                )
            )


def check_project_profile_nonempty(root: Path, findings: list[Finding]) -> None:
    """Warn when docs/PROJECT_PROFILE.md exists but is zero bytes.

    The cold-start protocol (CLAUDE.md / docs/SESSION_CONTINUITY.md) distinguishes
    "missing" from "empty fields". An existing-but-0-byte profile is a third state:
    the file exists so cold-start does not re-seed it, but there is nothing to read.
    Surface it as a warning so the agent or operator re-seeds from the template.
    """
    path = root / "docs" / "PROJECT_PROFILE.md"
    if not path.exists():
        return
    try:
        size = path.stat().st_size
    except OSError:
        return
    if size == 0:
        findings.append(
            Finding(
                "warn",
                "project_profile_empty",
                "docs/PROJECT_PROFILE.md exists but is 0 bytes; "
                "re-seed from docs/PROJECT_PROFILE.template.md or run bootstrap",
            )
        )


def check_ephemeral_artifacts(root: Path, findings: list[Finding]) -> None:
    warning_patterns = (
        ("pycache_present", "**/__pycache__"),
        ("smoke_artifact_present", "runtime/*-smoke-*"),
        ("bom_lock_present", "runtime/.skeleton-bom-*.rotation.lock"),
    )
    for check_name, pattern in warning_patterns:
        matches = sorted(path for path in root.glob(pattern) if path.exists())
        for path in matches[:10]:
            findings.append(
                Finding(
                    "warn",
                    check_name,
                    f"{path.relative_to(root).as_posix()} is a temporary/test artifact; remove before publishing",
                )
            )
        if len(matches) > 10:
            findings.append(
                Finding(
                    "warn",
                    check_name,
                    f"{len(matches) - 10} more {pattern} artifact(s) not shown",
                )
            )


def check_removed_paths(root: Path, findings: list[Finding]) -> None:
    for rel in REMOVED_PATHS:
        if (root / rel).exists():
            findings.append(
                Finding(
                    "error",
                    "removed_path_present",
                    f"{rel} should not exist; it was removed from the skeleton",
                )
            )


def check_agent_frontmatter(root: Path, findings: list[Finding]) -> None:
    agents_dir = root / "codex" / "agents"
    if not agents_dir.is_dir():
        findings.append(
            Finding("error", "agents_dir_missing", "codex/agents/ missing")
        )
        return
    for agent_file in sorted(agents_dir.glob("*.md")):
        if agent_file.name == "README.md":
            continue
        text = agent_file.read_text(encoding="utf-8")
        match = FRONTMATTER_PATTERN.match(text)
        if not match:
            findings.append(
                Finding(
                    "error",
                    "agent_frontmatter_missing",
                    f"{agent_file.relative_to(root).as_posix()} has no YAML frontmatter",
                )
            )
            continue
        body = match.group(1)
        for field in AGENT_REQUIRED_FIELDS:
            if not re.search(rf"^{re.escape(field)}\s*:", body, re.MULTILINE):
                findings.append(
                    Finding(
                        "error",
                        "agent_field_missing",
                        f"{agent_file.relative_to(root).as_posix()} missing '{field}' in frontmatter",
                    )
                )


def check_activity_log_parses(root: Path, findings: list[Finding]) -> None:
    path = root / "runtime" / "activity-log.jsonl"
    if not path.exists():
        return
    # utf-8-sig transparently strips a leading UTF-8 BOM (which Windows editors
    # like Notepad can introduce). Plain utf-8 leaves the BOM in the stream and
    # json.loads rejects it on line 1 with "Unexpected UTF-8 BOM".
    for line_no, line in enumerate(
        path.read_text(encoding="utf-8-sig").splitlines(), start=1
    ):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            json.loads(stripped)
        except json.JSONDecodeError as exc:
            findings.append(
                Finding(
                    "error",
                    "activity_log_parse",
                    f"runtime/activity-log.jsonl:{line_no} invalid JSON: {exc}",
                )
            )


def check_agent_runs_parses(root: Path, findings: list[Finding]) -> None:
    path = root / "runtime" / "agent-runs.jsonl"
    if not path.exists():
        return
    # Same BOM-tolerance rationale as check_activity_log_parses.
    for line_no, line in enumerate(
        path.read_text(encoding="utf-8-sig").splitlines(), start=1
    ):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            json.loads(stripped)
        except json.JSONDecodeError as exc:
            findings.append(
                Finding(
                    "error",
                    "agent_runs_parse",
                    f"runtime/agent-runs.jsonl:{line_no} invalid JSON: {exc}",
                )
            )


def check_review_queue_parses(root: Path, findings: list[Finding]) -> None:
    path = root / "runtime" / "review-queue.jsonl"
    if not path.exists():
        return
    for line_no, line in enumerate(
        path.read_text(encoding="utf-8-sig").splitlines(), start=1
    ):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            value = json.loads(stripped)
        except json.JSONDecodeError as exc:
            findings.append(
                Finding(
                    "error",
                    "review_queue_parse",
                    f"runtime/review-queue.jsonl:{line_no} invalid JSON: {exc}",
                )
            )
            continue
        if not isinstance(value, dict):
            findings.append(
                Finding(
                    "error",
                    "review_queue_parse",
                    f"runtime/review-queue.jsonl:{line_no} JSONL event must be an object",
                )
            )


def _marker_inside_backticks(line: str, marker_start: int) -> bool:
    """True when the marker at marker_start is inside a backtick-fenced span.

    Backticked markers are documentation examples, not outstanding questions,
    so they must not be counted. We approximate fencing by counting backticks
    preceding the marker: an odd count means we are inside a span.
    """
    return line[:marker_start].count("`") % 2 == 1


def check_clarifications(root: Path, findings: list[Finding]) -> None:
    """Surface outstanding [NEEDS CLARIFICATION: ...] markers as info and flag
    malformed bare [NEEDS CLARIFICATION] markers as warnings.

    Template files are skipped so their example text is not reported. Markers
    inside backtick fences (both inline single-backtick spans and triple-
    backtick fenced code blocks) are also skipped because they are
    documentation examples, not real pending questions. An instantiated
    PROJECT_PROFILE.md (no .template suffix) is still scanned.
    """
    open_count = 0
    malformed_examples: list[str] = []
    open_examples: list[str] = []
    for search_rel in CLARIFICATION_SEARCH_DIRS:
        search_dir = root / search_rel
        if not search_dir.is_dir():
            continue
        for path in search_dir.rglob("*.md"):
            if path.name in CLARIFICATION_SKIP_NAMES:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            # Track triple-backtick fenced blocks across lines. A line whose
            # leading non-whitespace token is ``` toggles the fence; markers
            # inside the fence are documentation and must not be flagged.
            in_fence = False
            for line_no, line in enumerate(text.splitlines(), start=1):
                if line.lstrip().startswith("```"):
                    in_fence = not in_fence
                    continue
                if "NEEDS CLARIFICATION" not in line:
                    continue
                marker_pos = line.find("[NEEDS CLARIFICATION")
                if marker_pos == -1:
                    continue
                if in_fence:
                    continue
                if _marker_inside_backticks(line, marker_pos):
                    continue
                rel = path.relative_to(root).as_posix()
                location = f"{rel}:{line_no}"
                ok = CLARIFICATION_OK.search(line)
                bare = CLARIFICATION_BARE.search(line)
                if ok:
                    open_count += 1
                    if len(open_examples) < 5:
                        open_examples.append(f"{location} {line.strip()}")
                elif bare:
                    malformed_examples.append(
                        f"{location} bare marker without question"
                    )
    for item in malformed_examples:
        findings.append(Finding("warn", "clarification_malformed", item))
    if open_count:
        findings.append(
            Finding(
                "info",
                "clarification_open",
                f"{open_count} outstanding `[NEEDS CLARIFICATION: ...]` marker(s)",
            )
        )
        for example in open_examples:
            findings.append(Finding("info", "clarification_open", example))


def check_scripts_compile(root: Path, findings: list[Finding]) -> None:
    """Parse every *.py under scripts/ so syntax errors surface here rather
    than at first runtime invocation. Cheap (no imports executed) and catches
    the common "edit a hook, ship the typo" class of regression without
    creating __pycache__ artifacts.
    """
    scripts_dir = root / "scripts"
    if not scripts_dir.is_dir():
        return
    for path in sorted(scripts_dir.rglob("*.py")):
        try:
            with tokenize.open(path) as handle:
                source = handle.read()
            compile(source, str(path), "exec")
        except (OSError, SyntaxError, UnicodeDecodeError) as exc:
            rel = path.relative_to(root).as_posix()
            detail = str(exc).strip()
            findings.append(
                Finding("error", "script_compile", f"{rel}: {detail}")
            )


def check_wiki_lint(root: Path, findings: list[Finding]) -> None:
    script = root / "scripts" / "wiki-lint.py"
    if not script.exists():
        findings.append(
            Finding("warn", "wiki_lint_missing", "scripts/wiki-lint.py missing")
        )
        return
    try:
        result = subprocess.run(
            [sys.executable, str(script), "--stale-days", "180"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.SubprocessError as exc:
        findings.append(
            Finding("error", "wiki_lint_run", f"wiki-lint failed to run: {exc}")
        )
        return
    stdout = result.stdout
    if result.returncode != 0:
        # Report the crash and do not trust the stdout as a valid report.
        # Parsing a malformed report would either hide the real error or
        # produce misleading "missing" findings.
        findings.append(
            Finding(
                "error",
                "wiki_lint_exit",
                f"wiki-lint exited {result.returncode}: {result.stderr.strip()}",
            )
        )
        return
    for section in (
        "stale",
        "duplicate_topic",
        "source_pointer_missing",
        "supersession_missing",
        "supersession_invalid",
        "orphan",
        "invalid",
    ):
        block = _extract_section(stdout, section)
        if block is None:
            continue
        for item in block:
            findings.append(
                Finding("error", f"wiki_{section}", item)
            )


def check_reference_candidates(root: Path, findings: list[Finding]) -> None:
    script = root / "scripts" / "validate-reference-candidates.py"
    if not script.exists():
        findings.append(
            Finding(
                "warn",
                "reference_candidate_validator_missing",
                "scripts/validate-reference-candidates.py missing",
            )
        )
        return
    try:
        result = subprocess.run(
            [sys.executable, str(script), "--root", str(root)],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.SubprocessError as exc:
        findings.append(
            Finding(
                "error",
                "reference_candidate_validator_run",
                f"validate-reference-candidates failed to run: {exc}",
            )
        )
        return
    if result.returncode != 0:
        detail = (result.stdout or result.stderr).strip()
        findings.append(
            Finding(
                "error",
                "reference_candidate_validator_exit",
                detail or f"validate-reference-candidates exited {result.returncode}",
            )
        )


def check_reference_proposals(root: Path, findings: list[Finding]) -> None:
    script = root / "scripts" / "validate-reference-proposals.py"
    if not script.exists():
        findings.append(
            Finding(
                "warn",
                "reference_proposal_validator_missing",
                "scripts/validate-reference-proposals.py missing",
            )
        )
        return
    try:
        result = subprocess.run(
            [sys.executable, str(script), "--root", str(root)],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.SubprocessError as exc:
        findings.append(
            Finding(
                "error",
                "reference_proposal_validator_run",
                f"validate-reference-proposals failed to run: {exc}",
            )
        )
        return
    if result.returncode != 0:
        detail = (result.stdout or result.stderr).strip()
        findings.append(
            Finding(
                "error",
                "reference_proposal_validator_exit",
                detail or f"validate-reference-proposals exited {result.returncode}",
            )
        )


def _extract_section(report: str, section: str) -> list[str] | None:
    lines = report.splitlines()
    header = f"## {section}"
    try:
        start = lines.index(header)
    except ValueError:
        return None
    items: list[str] = []
    for line in lines[start + 1 :]:
        if line.startswith("## "):
            break
        stripped = line.strip()
        if stripped == "- none" or not stripped.startswith("- "):
            continue
        items.append(stripped[2:])
    return items


def render(findings: list[Finding]) -> str:
    errors = [f for f in findings if f.level == "error"]
    warns = [f for f in findings if f.level == "warn"]
    infos = [f for f in findings if f.level == "info"]
    if not errors and not warns and not infos:
        return "skeleton OK: all checks passed"
    if not errors and not warns:
        lines = ["skeleton OK: all checks passed"]
    else:
        lines = ["skeleton findings:"]
        for finding in errors:
            lines.append(f"  ERROR [{finding.check}] {finding.detail}")
        for finding in warns:
            lines.append(f"  WARN  [{finding.check}] {finding.detail}")
    for finding in infos:
        lines.append(f"  INFO  [{finding.check}] {finding.detail}")
    lines.append(
        f"total: {len(errors)} error(s), {len(warns)} warning(s), "
        f"{len(infos)} info"
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        default=None,
        help="Skeleton or project root (defaults to this script's repo root).",
    )
    parser.add_argument(
        "--skip-wiki-lint",
        action="store_true",
        help="Skip running scripts/wiki-lint.py (useful for fast checks).",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve() if args.root else repo_root()
    if not root.is_dir():
        print(f"root not a directory: {root}", file=sys.stderr)
        return 2

    findings: list[Finding] = []
    check_claude_md_size(root, findings)
    check_required_paths(root, findings)
    check_project_profile_nonempty(root, findings)
    check_ephemeral_artifacts(root, findings)
    check_removed_paths(root, findings)
    check_agent_frontmatter(root, findings)
    check_activity_log_parses(root, findings)
    check_agent_runs_parses(root, findings)
    check_review_queue_parses(root, findings)
    check_scripts_compile(root, findings)
    check_clarifications(root, findings)
    check_reference_candidates(root, findings)
    check_reference_proposals(root, findings)
    if not args.skip_wiki_lint:
        check_wiki_lint(root, findings)

    print(render(findings))
    errors = [f for f in findings if f.level == "error"]
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

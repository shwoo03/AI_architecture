#!/usr/bin/env python3
"""Lint the knowledge wiki for stale, duplicate, superseded, orphan, and source-pointer issues."""

from __future__ import annotations

import argparse
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


DATE_RE = re.compile(r"\b(20\d{2}-\d{2}-\d{2})\b")
TIMESTAMP_RE = re.compile(r"\b20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\b")
URL_RE = re.compile(r"https?://\S+")
FILE_LINE_RE = re.compile(
    r"(?:^|[\s,])"
    r"((?:[A-Za-z]:[\\/])?"         # optional Windows drive letter prefix (C:\, D:/)
    r"[-A-Za-z0-9_./\\]+"           # hyphen first (literal), backslash last (escaped)
    r"\.[A-Za-z0-9_+-]+"
    r":\d+(?::\d+)?)"
    r"(?:$|[\s,])"
)
ENTRY_ID_RE = re.compile(r"^K[0-9A-Za-z_-]+$")
SUPERSEDED_NOTE_RE = re.compile(r"\bsuperseded\b|\bsupersedes\b", re.IGNORECASE)
SUPERSEDED_FIELD_RE = re.compile(r"\bsuperseded_by(?:_id)?\b", re.IGNORECASE)
# Inline wikilink references like [[K003]] for cross-entry references inside
# knowledge/ markdown bodies. Not used in index.md itself (the index is a
# table); only knowledge pages.
WIKILINK_RE = re.compile(r"\[\[(K[0-9A-Za-z_-]+)\]\]")


@dataclass
class IndexRow:
    line_no: int
    entry_id: str
    topic: str
    status: str
    pointer: str
    superseded_by: str
    superseded_at: str


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def parse_date(value: str) -> datetime | None:
    try:
        return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def collect_markdown(root: Path) -> list[Path]:
    # Skip symlinks: rglob can follow directory symlinks into a cycle (hang) or
    # into content outside knowledge/ (e.g. a symlink to /etc or C:\Windows),
    # which would leak file names and line counts into the lint report. The
    # knowledge tree has no legitimate need for symlinks; fail closed.
    resolved_root = root.resolve()
    results: list[Path] = []
    for path in root.rglob("*.md"):
        if path.is_symlink():
            continue
        if not path.is_file():
            continue
        # Belt-and-suspenders: even if rglob walked into a non-symlink path
        # that somehow points outside root (e.g. a junction on Windows that
        # is_symlink does not recognize), reject anything whose resolved path
        # escapes the knowledge root.
        try:
            path.resolve().relative_to(resolved_root)
        except ValueError:
            continue
        results.append(path)
    return sorted(results)


def normalize_cell(value: str) -> str:
    normalized = value.strip().strip("`").strip()
    if normalized in {"-", "none", "None", "N/A", "n/a"}:
        return ""
    return normalized


def parse_index_rows(index_text: str) -> tuple[list[IndexRow], list[str]]:
    """Parse index rows plus a list of per-line rejection reasons.

    A "looks like a table row" line (starts with `|`, is not a separator) that
    fails validation yields a rejection reason keyed to its line number. The
    caller surfaces these so an operator sees WHY their index did not parse
    instead of the opaque "no parseable knowledge rows found".
    """
    rows: list[IndexRow] = []
    rejections: list[str] = []
    for line_no, line in enumerate(index_text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if set(stripped.replace("|", "").replace("-", "").replace(" ", "")) == set():
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 4:
            rejections.append(
                f"index.md:{line_no} has {len(cells)} cell(s); need >= 4 "
                f"(id | topic | status | pointer [| superseded_by | superseded_at])"
            )
            continue
        entry_id = normalize_cell(cells[0])
        if not ENTRY_ID_RE.match(entry_id):
            # Skip header rows ("ID", "---") silently; flag other first-cell
            # values so a typo in the ID prefix (e.g. "k001" lowercase) is
            # discoverable.
            if entry_id and entry_id.lower() not in {"id", "entry_id", "entry id"}:
                rejections.append(
                    f"index.md:{line_no} first cell {entry_id!r} is not a valid "
                    f"entry id (must match /^K[0-9A-Za-z_-]+$/, e.g. K001)"
                )
            continue
        rows.append(
            IndexRow(
                line_no=line_no,
                entry_id=entry_id,
                topic=normalize_cell(cells[1]),
                status=normalize_cell(cells[2]),
                pointer=normalize_cell(cells[3]),
                superseded_by=normalize_cell(cells[4]) if len(cells) >= 5 else "",
                superseded_at=normalize_cell(cells[5]) if len(cells) >= 6 else "",
            )
        )
    return rows, rejections


def has_valid_source_pointer(pointer: str) -> bool:
    if not pointer:
        return False
    return bool(
        TIMESTAMP_RE.search(pointer)
        or URL_RE.search(pointer)
        or FILE_LINE_RE.search(pointer)
    )


def pointer_candidates(pointer: str) -> list[str]:
    cleaned = pointer.replace("`", "")
    return [piece.strip() for piece in cleaned.split(",") if piece.strip()]


def canonical_index_path(candidate: str) -> str:
    normalized = candidate.replace("\\", "/")
    normalized = re.sub(r":\d+(?::\d+)?$", "", normalized)
    if normalized.startswith("knowledge/"):
        normalized = normalized[len("knowledge/") :]
    return normalized


def lint_index(knowledge: Path, index_rows: list[IndexRow]) -> tuple[dict[str, list[str]], set[str]]:
    findings: dict[str, list[str]] = {
        "duplicate_topic": [],
        "source_pointer_missing": [],
        "supersession_missing": [],
        "supersession_invalid": [],
    }
    indexed_files: set[str] = set()
    topics: dict[str, list[str]] = defaultdict(list)
    ids = {row.entry_id for row in index_rows}

    for row in index_rows:
        topic_key = row.topic.lower()
        if topic_key:
            topics[topic_key].append(f"index.md:{row.line_no}")

        if not has_valid_source_pointer(row.pointer):
            findings["source_pointer_missing"].append(
                f"index.md:{row.line_no} {row.entry_id}: pointer must include activity-log ts, file:line, or URL"
            )

        for candidate in pointer_candidates(row.pointer):
            canonical = canonical_index_path(candidate)
            if canonical.endswith(".md") and (knowledge / canonical).exists():
                indexed_files.add(canonical)

        has_superseded_by = bool(row.superseded_by)
        has_superseded_at = bool(row.superseded_at)

        if has_superseded_by != has_superseded_at:
            findings["supersession_missing"].append(
                f"index.md:{row.line_no} {row.entry_id}: superseded_by and superseded_at must be set together"
            )

        if has_superseded_by:
            target_id = row.superseded_by
            if not ENTRY_ID_RE.match(target_id):
                findings["supersession_invalid"].append(
                    f"index.md:{row.line_no} {row.entry_id}: invalid superseded_by '{target_id}'"
                )
            elif target_id == row.entry_id:
                findings["supersession_invalid"].append(
                    f"index.md:{row.line_no} {row.entry_id}: superseded_by cannot reference itself"
                )
            elif target_id not in ids:
                findings["supersession_invalid"].append(
                    f"index.md:{row.line_no} {row.entry_id}: superseded_by '{target_id}' not found in index"
                )

            if row.superseded_at and not parse_date(row.superseded_at):
                findings["supersession_invalid"].append(
                    f"index.md:{row.line_no} {row.entry_id}: superseded_at must be YYYY-MM-DD"
                )

            if row.status.lower() not in {"superseded", "deprecated", "archived"}:
                findings["supersession_invalid"].append(
                    f"index.md:{row.line_no} {row.entry_id}: status should be superseded/deprecated/archived when superseded_by is set"
                )
        elif row.status.lower() == "superseded":
            findings["supersession_missing"].append(
                f"index.md:{row.line_no} {row.entry_id}: status is superseded but superseded_by/superseded_at are empty"
            )

    for topic, refs in topics.items():
        if len(refs) > 1:
            findings["duplicate_topic"].append(f"{topic}: {', '.join(refs)}")

    return findings, indexed_files


def lint(knowledge: Path, stale_days: int) -> dict[str, list[str]]:
    findings: dict[str, list[str]] = {
        "stale": [],
        "duplicate_topic": [],
        "source_pointer_missing": [],
        "supersession_missing": [],
        "supersession_invalid": [],
        "orphan": [],
        "wikilink_broken": [],
        "invalid": [],
    }
    files = collect_markdown(knowledge)
    today = datetime.now(timezone.utc)

    index = knowledge / "index.md"
    indexed_files: set[str] = set()
    known_entry_ids: set[str] = set()
    if index.exists():
        index_text = index.read_text(encoding="utf-8")
        index_rows, rejections = parse_index_rows(index_text)
        # Surface per-line rejection reasons even when a subset of rows did
        # parse, so a single malformed row in an otherwise-valid index is
        # discoverable instead of hidden.
        for reason in rejections:
            findings["invalid"].append(reason)
        if not index_rows:
            if rejections:
                findings["invalid"].append(
                    "index.md: no parseable knowledge rows (see reasons above)"
                )
            else:
                findings["invalid"].append(
                    "index.md: no parseable knowledge rows found -- fix: "
                    "add at least one row matching "
                    "`| K001 | <topic> | active | <pointer> | - | - |` "
                    "(see docs/wiki-ops/wiki-lint.md for the schema)"
                )
        else:
            index_findings, indexed_files = lint_index(knowledge, index_rows)
            for key, values in index_findings.items():
                findings[key].extend(values)
            known_entry_ids = {row.entry_id for row in index_rows}
    else:
        findings["invalid"].append(
            "index.md: missing -- fix: create knowledge/index.md with the "
            "starter table documented in docs/wiki-ops/wiki-lint.md"
        )

    for path in files:
        rel = path.relative_to(knowledge).as_posix()
        text = path.read_text(encoding="utf-8")
        dates = [date for date in (parse_date(value) for value in DATE_RE.findall(text)) if date]
        if dates:
            newest = max(dates)
            if (today - newest).days > stale_days:
                findings["stale"].append(f"{rel}: newest date is {newest.date().isoformat()}")
        else:
            # No ISO date markers in content: fall back to file modification time
            # so files without date headers still participate in stale detection.
            # st_mtime is a POSIX timestamp (seconds since epoch, UTC), so
            # fromtimestamp(ts) returns local-naive time. Convert via the local
            # clock and then move to UTC so the comparison with `today` (aware
            # UTC) is not skewed by timezone offset on Windows/other systems.
            mtime = datetime.fromtimestamp(path.stat().st_mtime).astimezone(
                timezone.utc
            )
            if (today - mtime).days > stale_days:
                findings["stale"].append(
                    f"{rel}: no date markers; mtime is {mtime.date().isoformat()}"
                )
        if SUPERSEDED_FIELD_RE.search(text) and not SUPERSEDED_NOTE_RE.search(text):
            findings["supersession_missing"].append(
                f"{rel}: has superseded_by field without supersession note"
            )
        # Wikilink cross-reference check: [[Kxxx]] inside knowledge/ bodies
        # (not in index.md itself — the index uses the table's entry_id column).
        if rel != "index.md" and known_entry_ids:
            for line_no, line in enumerate(text.splitlines(), start=1):
                for match in WIKILINK_RE.finditer(line):
                    target = match.group(1)
                    if target not in known_entry_ids:
                        findings["wikilink_broken"].append(
                            f"{rel}:{line_no}: [[{target}]] not found in index.md"
                        )
        if rel not in {"index.md", "log.md", "lint-report.md"} and rel not in indexed_files:
            findings["orphan"].append(f"{rel}: not referenced from index.md")

    return findings


def render_report(findings: dict[str, list[str]], stale_days: int) -> str:
    lines = [
        "# Knowledge Lint Report",
        "",
        f"- generated_at: {datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')}",
        f"- stale_days: {stale_days}",
        "",
    ]
    for section, items in findings.items():
        lines.append(f"## {section}")
        lines.append("")
        if items:
            lines.extend(f"- {item}" for item in items)
        else:
            lines.append("- none")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--knowledge", default=None)
    parser.add_argument("--stale-days", type=int, default=180)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()

    knowledge = Path(args.knowledge).resolve() if args.knowledge else repo_root() / "knowledge"
    findings = lint(knowledge, args.stale_days)
    report = render_report(findings, args.stale_days)
    if args.write_report:
        (knowledge / "lint-report.md").write_text(report, encoding="utf-8", newline="\n")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

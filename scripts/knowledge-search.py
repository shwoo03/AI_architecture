#!/usr/bin/env python3
"""Search local knowledge/wiki docs with a small stdlib ranker."""

from __future__ import annotations

import argparse
import importlib.util
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


SEARCH_ROOTS = ("knowledge", "docs/wiki-ops", "docs/CODEMAPS")
TOKEN_RE = re.compile(r"[A-Za-z0-9_가-힣-]+")


@dataclass
class SearchHit:
    path: str
    score: float
    line: int
    snippet: str
    rrf_score: float = 0.0
    rank_sources: list[str] | None = None


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def tokens(value: str) -> list[str]:
    return [item.lower() for item in TOKEN_RE.findall(value) if item.strip()]


def iter_markdown(root: Path) -> list[Path]:
    paths: list[Path] = []
    for rel in SEARCH_ROOTS:
        base = root / rel
        if base.is_file() and base.suffix == ".md":
            paths.append(base)
        elif base.is_dir():
            paths.extend(path for path in base.rglob("*.md") if path.is_file())
    return sorted(set(paths))


def best_line(query: str, query_terms: list[str], path: Path) -> tuple[float, int, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    best = (0.0, 1, "")
    query_lower = query.lower()
    for line_no, line in enumerate(text.splitlines(), start=1):
        haystack = line.lower()
        line_tokens = tokens(line)
        if not line_tokens and query_lower not in haystack:
            continue
        term_score = sum(haystack.count(term) for term in query_terms)
        phrase_score = 3 if query_lower and query_lower in haystack else 0
        heading_boost = 1 if line.lstrip().startswith("#") else 0
        score = float(term_score + phrase_score + heading_boost)
        if score > best[0]:
            best = (score, line_no, line.strip())
    return best


def title_score(query: str, query_terms: list[str], path: Path, root: Path) -> float:
    rel = path.relative_to(root).as_posix().lower()
    stem = path.stem.lower()
    query_lower = query.lower()
    score = 0.0
    if query_lower and query_lower in rel:
        score += 5.0
    if query_lower and query_lower in stem:
        score += 4.0
    score += sum(1.0 for term in query_terms if term in rel)
    return score


def phrase_score(query: str, path: Path) -> tuple[float, int, str]:
    query_lower = query.lower()
    if not query_lower:
        return 0.0, 1, ""
    text = path.read_text(encoding="utf-8", errors="replace")
    for line_no, line in enumerate(text.splitlines(), start=1):
        if query_lower in line.lower():
            return 1.0, line_no, line.strip()
    return 0.0, 1, ""


def link_score(query_terms: list[str], path: Path) -> float:
    text = path.read_text(encoding="utf-8", errors="replace").lower()
    linkish = re.findall(r"\[[^\]]+\]\([^)]+\)|`[^`]+`", text)
    if not linkish:
        return 0.0
    haystack = " ".join(linkish)
    return float(sum(1 for term in query_terms if term in haystack))


def ranked_list(items: list[tuple[str, float]]) -> list[str]:
    return [path for path, score in sorted(items, key=lambda item: (-item[1], item[0])) if score > 0]


def reciprocal_rank_fusion(rankings: dict[str, list[str]], k: int = 60) -> dict[str, tuple[float, list[str]]]:
    scores: dict[str, float] = {}
    sources: dict[str, list[str]] = {}
    for source, paths in rankings.items():
        for rank, path in enumerate(paths, start=1):
            scores[path] = scores.get(path, 0.0) + 1.0 / (k + rank)
            sources.setdefault(path, []).append(source)
    return {path: (score, sources.get(path, [])) for path, score in scores.items()}


def search(root: Path, query: str, limit: int) -> list[SearchHit]:
    query_terms = tokens(query)
    if not query_terms:
        return []
    paths = iter_markdown(root)
    metadata: dict[str, tuple[float, int, str]] = {}
    title_items: list[tuple[str, float]] = []
    phrase_items: list[tuple[str, float]] = []
    body_items: list[tuple[str, float]] = []
    link_items: list[tuple[str, float]] = []
    for path in paths:
        rel = path.relative_to(root).as_posix()
        score, line_no, snippet = best_line(query, query_terms, path)
        phrase, phrase_line, phrase_snippet = phrase_score(query, path)
        metadata[rel] = (
            max(score, phrase),
            phrase_line if phrase > score else line_no,
            (phrase_snippet if phrase > score else snippet)[:240],
        )
        title_items.append((rel, title_score(query, query_terms, path, root)))
        phrase_items.append((rel, phrase))
        body_items.append((rel, score))
        link_items.append((rel, link_score(query_terms, path)))
    fused = reciprocal_rank_fusion(
        {
            "filename_title": ranked_list(title_items),
            "phrase": ranked_list(phrase_items),
            "body_tokens": ranked_list(body_items),
            "link_signal": ranked_list(link_items),
        }
    )
    hits: list[SearchHit] = []
    for rel, (rrf_score, sources) in fused.items():
        score, line_no, snippet = metadata.get(rel, (0.0, 1, ""))
        if rrf_score <= 0:
            continue
        hits.append(SearchHit(rel, round(rrf_score, 6), line_no, snippet[:240], round(rrf_score, 6), sources))
    return sorted(hits, key=lambda hit: (-hit.rrf_score, hit.path, hit.line))[:limit]


def load_helper(root: Path, script_name: str, module_name: str):
    path = root / "scripts" / script_name
    if not path.exists():
        path = repo_root() / "scripts" / script_name
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {script_name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def open_question_findings(root: Path) -> list[dict[str, object]]:
    try:
        module = load_helper(root, "list-open-questions.py", "list_open_questions_for_gap_check")
        return list(module.scan(root))
    except Exception as exc:
        return [{"category": "open_question_scan_error", "detail": str(exc)}]


def wiki_lint_findings(root: Path) -> list[dict[str, object]]:
    knowledge = root / "knowledge"
    if not knowledge.exists():
        return []
    try:
        module = load_helper(root, "wiki-lint.py", "wiki_lint_for_gap_check")
        raw = module.lint(knowledge, 180)
    except Exception as exc:
        return [{"category": "knowledge_lint_error", "detail": str(exc)}]
    findings: list[dict[str, object]] = []
    for category, values in raw.items():
        if category in {"graph_gap", "bridge_candidate", "weak_link", "isolated_entry"}:
            continue
        for value in values:
            findings.append({"category": "knowledge_lint", "check": category, "detail": value})
    return findings


def gap_check(root: Path, query: str, limit: int) -> dict[str, object]:
    hits = search(root, query, limit)
    findings: list[dict[str, object]] = []
    questions = open_question_findings(root)
    if questions:
        findings.extend({"category": "open_question", **item} for item in questions)
    findings.extend(wiki_lint_findings(root))

    if questions:
        status = "blocked_by_question"
        confidence = "high"
        next_action = "ask_user"
    elif not hits:
        findings.append({"category": "no_hits", "detail": "no local knowledge hit matched the query"})
        status = "missing"
        confidence = "low"
        next_action = "reference_review" if any(term in tokens(query) for term in {"reference", "upgrade", "external", "opensource", "오픈소스"}) else "propose_doc_update"
    else:
        best = hits[0]
        rank_sources = best.rank_sources or []
        if len(rank_sources) < 2:
            findings.append({"category": "weak_hits", "detail": "best hit has only one ranking signal"})
            status = "weak"
            confidence = "medium"
            next_action = "propose_doc_update"
        else:
            status = "covered"
            confidence = "high"
            next_action = "use_existing"
        if any(item.get("category") == "knowledge_lint" for item in findings) and status == "covered":
            status = "weak"
            confidence = "medium"
            next_action = "propose_doc_update"
    return {
        "query": query,
        "status": status,
        "confidence": confidence,
        "hits": [asdict(hit) for hit in hits],
        "findings": findings,
        "recommended_next_action": next_action,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=None)
    sub = parser.add_subparsers(dest="command", required=True)
    search_parser = sub.add_parser("search")
    search_parser.add_argument("query")
    search_parser.add_argument("--limit", type=int, default=10)
    search_parser.add_argument("--format", choices=("text", "json"), default="text")
    gap_parser = sub.add_parser("gap-check")
    gap_parser.add_argument("query")
    gap_parser.add_argument("--limit", type=int, default=5)
    gap_parser.add_argument("--format", choices=("text", "json"), default="text")
    gap_parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    root = Path(args.root).resolve() if args.root else repo_root().resolve()
    if not root.is_dir():
        print(f"root not a directory: {root}", file=sys.stderr)
        return 2
    if args.command == "search":
        hits = search(root, args.query, args.limit)
        if args.format == "json":
            print(json.dumps({"query": args.query, "hits": [asdict(hit) for hit in hits]}, ensure_ascii=False, indent=2))
        else:
            if not hits:
                print("no knowledge matches.")
            for hit in hits:
                print(f"{hit.path}:{hit.line} score={hit.score:g} {hit.snippet}")
        return 0
    payload = gap_check(root, args.query, args.limit)
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"status: {payload['status']} confidence: {payload['confidence']}")
        for hit in payload["hits"]:
            print(f"{hit['path']}:{hit['line']} {hit['snippet']}")
        for finding in payload["findings"]:
            print(f"{finding.get('category')}: {finding.get('detail') or finding}")
    return 1 if args.strict and payload["status"] in {"missing", "blocked_by_question"} else 0


if __name__ == "__main__":
    raise SystemExit(main())

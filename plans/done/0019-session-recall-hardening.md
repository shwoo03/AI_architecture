# 0019 Session Recall Hardening

## Summary
Existing `scripts/session-recall.py` was hardened as the local session recall surface. Source-of-truth data remains Markdown/JSONL; `runtime/session-recall.sqlite` is only a derived, rebuildable SQLite FTS cache.

## Assumptions
- No new search script, DB path, external dependency, tokenizer dependency, graph recommendation, or BM25 tuning is introduced.
- Redaction is applied before inserting text into the FTS cache.
- `session-recall` remains an operational tool checked by quality-gate, not a new `docs/feature-status.yaml` feature entry.

## Out of Scope
- Replacing Markdown/JSONL ledgers with SQLite.
- Using search results as automatic decision inputs.
- Korean morphological analysis.
- Incremental append-only indexing.

## Implementation Steps
- Added `runtime/state/session-handoff.md` to the indexed sources as `handoff`.
- Added insert-time redaction through the existing `scripts/redact.py` helper.
- Added `recall_meta.index_version` so older or unversioned caches are reported stale and rebuilt by search/summary.
- Added `agent-flow recall <query>` as a public wrapper around `session-recall.py search`.
- Documented the cache/source-of-truth boundary and Korean tokenizer limitation.
- Added regression coverage for handoff indexing, redaction, stale version checks, summary rebuild, and agent-flow recall pass-through.

## Definition of Done
- Focused recall tests pass.
- Full `tests.test_runtime` and `tests.test_agent_flow` pass.
- `session-recall.py check`, `verify-skeleton.py`, and stable/all quality gates pass.
- Closeout evidence and handoff are recorded.

## Rollback Plan
- Revert this plan's changes to `scripts/session-recall.py`, `scripts/agent-flow.py`, tests, docs, `.gitignore`, plan index, and generated operational artifacts.
- Delete `runtime/session-recall.sqlite` if present; it is a rebuildable cache.

## Stop Conditions
- Stop if implementation creates a new DB path or new search script.
- Stop if implementation adds external dependencies or morphology/tokenizer packages.
- Stop if search output becomes an automatic decision input.
- Stop if redaction cannot invalidate older caches.

## Validation
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_runtime.SessionRecallTests tests.test_agent_flow.AgentFlowTests.test_recall_wrapper_passes_through_session_recall_json tests.test_agent_flow.AgentFlowTests.test_recall_wrapper_rejects_empty_query -v`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_runtime tests.test_agent_flow -v`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/session-recall.py check --format json`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify-skeleton.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/quality-gate.py --root . --tier stable --skip-tests --format json`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/quality-gate.py --root . --tier all --skip-tests --format json`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/agent-flow.py closeout --goal "0019 session recall hardening" --format json`

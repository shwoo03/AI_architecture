# Session Handoff

## Last Updated
2026-05-16T14:15:52Z

## Current Task
0020 specialist usage evidence ledger is complete. The specialist flow now records redacted advisory-only usage evidence while preserving the existing preview/approval/execute behavior.

## Last Completed
- Added append-only `runtime/specialist-usage.jsonl` records from `scripts/agent-flow.py specialist ...` flows.
- Recorded `preview_created`, `proposal_approved`, `proposal_rejected`, `delegation_plan_approved`, `delegation_execute_blocked`, and `delegation_execute_prepared` events.
- Kept the ledger separate from `runtime/agent-runs.jsonl`: 0020 records recommendation/decision/execute-prep evidence only, not actual runtime execution state.
- Redacted string-like event payloads with `scripts/redact.py` before appending records.
- Preserved advisory-only behavior: no recommendation scoring change, no automatic specialist creation or selection, no validator verdict, no spawn-ready packet generation, and no recursive delegation.
- Added tests in `tests/test_agent_flow.py` for preview, approve/reject, plan approval, execute blocked/prepared events, handoff paths, and redaction.
- Documented the ledger contract in `docs/RUNTIME_EVENT_SCHEMA.md`.
- Added `plans/done/0020-specialist-usage-evidence-ledger.md`, marked 0020 done in `plans/INDEX.md`, regenerated ownership lock and CODEMAPS, and recorded closeout for `0020 specialist usage evidence ledger`.

## Validation
- Focused specialist usage tests: passed.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_agent_flow -v`: passed, 37 tests.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate-plans.py --root . --format json`: passed with 20 plans and no findings.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/ownership-lock.py write`: passed with 690 classified paths and no unknown paths.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/generate-codemaps.py --write`: passed and rewrote docs/CODEMAPS.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify-skeleton.py`: passed.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/quality-gate.py --root . --tier stable --skip-tests --format json`: passed with OK=36, SKIP=2.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/quality-gate.py --root . --tier all --skip-tests --format json`: passed with OK=37, SKIP=2.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/agent-flow.py closeout --goal "0020 specialist usage evidence ledger" ...`: passed and recorded=true; it also ran full verify and stable quality-gate internally.

## Recommended Next Step
Use the specialist flow on demand only, then let `runtime/specialist-usage.jsonl` accumulate real/external evidence. Open 0021 closeout-validator loop only after at least 20 evidence records, with 30+ preferred, or after an explicit user implementation exception.

## Open Questions / Blockers
- `runtime/session-recall.sqlite` is intentionally ignored and may be deleted/rebuilt at any time.
- `runtime/specialist-usage.jsonl` is append-only evidence; do not use it to auto-select or auto-spawn specialists.
- 0021 is intentionally blocked until enough external/real-use specialist evidence accumulates.
- Slice 4 ENKI remains blocked on human review because `candidate_paths=261` exceeds the stop threshold of 20.
- Do not touch `/Users/shwoo/mydir/Project/ENKI_WIKI`; it is not the active target for this migration.
- `.claude/settings.local.json` is tracked local permission state with unrelated local edits; keep it out of specialist overlay commits unless the user explicitly approves untracking or committing it.
- Existing unrelated dirty/generated files remain: `.claude/settings.local.json`, generated `.claude/.codex` README changes, and ENKI 0013 residual files.

## Resume Prompt
Resume in `/Users/shwoo/mydir/AI/AI_architecture` after 0020 specialist usage evidence ledger. Plan 0020 is done. Specialist preview/approval/execute-prep now writes redacted advisory-only records to `runtime/specialist-usage.jsonl`; scoring, auto-selection, validator verdicts, spawn packets, and recursive delegation remain unchanged. Continue preserving existing unrelated dirty/generated files unless the user explicitly asks to clean them.

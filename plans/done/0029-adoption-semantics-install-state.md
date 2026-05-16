# 0029 Adoption Semantics And Install-State UX

## Summary

`agent-flow adopt` currently reports `needs_review` without distinguishing a
blocking failure from an intentional preserve or metadata review. This slice
adds a two-level review classification and reads existing target install-state
history so adoption output can explain previous/current skeleton commits and
intentional preserve candidates.

## Assumptions

- `runtime/install-state.jsonl` already exists in targets that have received the
  skeleton. 0029 reads it; it does not create a new adoption ledger.
- Older install-state entries do not contain the new fields and must be handled
  with fallback values.
- License `unknown` is not a legal judgment and should be a non-blocking
  metadata review unless another stop condition exists.
- ENKI validation must use read-only dry-run/status only.

## Out of Scope

- Applying files to target projects.
- Rollback.
- New adoption ledger files.
- Automatic legal compatibility decisions.
- Automatic manual/risky merge resolution.
- Editing ENKI target files.

## Implementation Steps

1. Add `review_classification` to adopt JSON output with two arrays:
   `blocking` and `non_blocking_review`.
2. Treat license `warning` as blocking review and license `unknown` as
   non-blocking metadata review.
3. Preserve existing `stop_reasons` and `review_reasons` fields for backward
   compatibility.
4. Read target `runtime/install-state.jsonl` with missing-key fallback and expose
   previous/current skeleton source commit fields.
5. Extract intentional preserve candidates from manual/risky brief items without
   auto-resolving them.
6. Add focused tests for unknown license semantics, old install-state fallback,
   previous/current commit reporting, and preserve candidates.
7. Validate ENKI using read-only `agent-flow adopt` only.

## Definition of Done

- Adopt output includes `review_classification.blocking` and
  `review_classification.non_blocking_review`.
- Unknown license no longer becomes a stop condition by itself.
- Existing consumers can still read `stop_reasons`, `review_reasons`,
  `skeleton_revision_in_target`, and `skeleton_revision_current`.
- Old install-state records without new keys do not crash adopt.
- Intentional preserve candidates are visible but not applied.
- ENKI validation is read-only.

## Rollback Plan

- Revert the adopt helper/output changes, focused tests, and this plan/index
  entry. No target rollback is needed because 0029 is read-only.

## Stop Conditions

- Stop if implementation writes to ENKI or any target project.
- Stop if unknown license is presented as legal clearance.
- Stop if manual/risky items are auto-resolved.
- Stop if existing install-state entries are rewritten or migrated.
- Stop if generated/local files are staged with this slice.

## Validation

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_agent_flow -v`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/agent-flow.py adopt --target <ENKI_WIKI_PATH> --format json`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate-plans.py --root . --format json`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/ownership-lock.py write`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/generate-codemaps.py --write`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify-skeleton.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/quality-gate.py --root . --tier stable --skip-tests --format json`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/quality-gate.py --root . --tier all --skip-tests --format json`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/agent-flow.py doctor --format json`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/resume-readiness.py --strict --format json`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/agent-flow.py closeout --goal "0029 adoption semantics and install-state UX" --changed-path scripts/agent-flow.py --changed-path tests/test_agent_flow.py --changed-path plans/done/0029-adoption-semantics-install-state.md --changed-path plans/INDEX.md --format json`

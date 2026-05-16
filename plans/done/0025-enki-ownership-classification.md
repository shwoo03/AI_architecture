# 0025 ENKI Ownership Classification

## Summary

Classify ENKI_WIKI project-owned paths so the AI_architecture operating OS can continue migrating without overwriting ENKI runtime data or domain code. This slice reduces the 0024 adoption stop condition (`candidate_paths > 20`) by turning the read-only initialize draft into a reviewed ownership proposal.

This slice still treats ENKI writes as approval-gated. The first deliverable is a verified classification report and a target-write proposal, not an automatic apply.

## Assumptions

- Target is `<ENKI_WIKI_PATH>`.
- `<WRONG_ENKI_WIKI_PATH>` remains out of scope.
- ENKI git working tree starts clean.
- ENKI runtime ledgers, state, deployment files, app code, and local evidence must be preserved.
- `config/ownership.yaml` and `runtime/ownership-classification.lock.json` writes in ENKI require explicit approval after this report.

## Out of Scope

- Running `upgrade-from-skeleton.py --apply`.
- Running `--include-risky`.
- Auto-resolving manual/risky upgrade items.
- Editing ENKI application code.
- Editing ENKI runtime evidence or state ledgers.
- Filling `docs/PROJECT_PROFILE.md` automatically.
- Committing or pushing ENKI changes.

## Implementation Steps

1. Re-run `agent-flow adopt --target <ENKI_WIKI_PATH> --format json` to confirm the current stop condition.
2. Re-run `ownership-initialize.py --target <ENKI_WIKI_PATH> --format json`.
3. Fix ownership path collection if ENKI exposes valid paths as quoted/escaped git paths.
4. Classify the 27 candidate groups into a proposed `project_overrides.rules` block.
5. Simulate the proposed ownership config in a temporary ENKI copy only.
6. Verify the temporary copy can write an ownership lock with unknown=0.
7. Record remaining safe/manual/risky migration items after the proposed classification.
8. Stop before writing `config/ownership.yaml` into ENKI unless explicitly approved.

## Definition of Done

- Current ENKI adoption stop condition is documented.
- Candidate groups and proposed owners are documented.
- Non-ASCII ENKI paths are handled without quoted git path artifacts.
- A temporary-copy simulation proves the proposed ownership config can produce a lock with unknown=0.
- Remaining migration work is separated into safe additions, manual reviews, and risky system updates.
- ENKI target remains clean unless the user explicitly approves target writes.

## Rollback Plan

- Revert AI_architecture changes for this slice.
- Delete only temporary simulation directories if any remain.
- No ENKI rollback is needed unless a later approved target-write step occurs.

## Stop Conditions

- Stop if ENKI git becomes dirty unexpectedly.
- Stop if a proposed override would classify protected runtime/state data as system-owned.
- Stop if a broad override would steal system-locked AI_architecture paths.
- Stop if the temporary simulation still reports ownership unknown paths.
- Stop before `upgrade-from-skeleton.py --apply`, `--include-risky`, ENKI commit, or ENKI push.

## Validation

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_ownership tests.test_ownership_initialize -v`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/ownership-initialize.py --target <ENKI_WIKI_PATH> --format json`
- Temporary-copy simulation of proposed `config/ownership.yaml` and `ownership-lock.py write`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate-plans.py --root . --format json`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify-skeleton.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/quality-gate.py --root . --tier stable --skip-tests --format json`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/agent-flow.py closeout --goal "0025 ENKI ownership classification" --changed-path scripts/lib_ownership.py --changed-path tests/test_ownership.py --changed-path plans/active/0025-enki-ownership-classification.md --changed-path plans/INDEX.md --changed-path runtime/validation/0025-enki-ownership-classification.md --format json`

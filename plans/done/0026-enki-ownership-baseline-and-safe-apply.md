# 0026 ENKI Ownership Baseline And Safe Apply

## Summary

Install the approved ENKI ownership baseline and apply only missing safe AI_architecture operating OS files. This slice advances the migration after 0025 proved the ownership config in a temporary copy.

## Assumptions

- Target is `~/mydir/ENKI_WIKI`.
- Ownership baseline write is limited to `config/ownership.yaml` and `runtime/ownership-classification.lock.json`.
- Safe apply is limited to `upgrade-from-skeleton.py --apply --safe-only --profile stable`.
- Manual and risky update items are not applied in this slice.

## Out of Scope

- `--include-risky`.
- Manual merge resolution.
- PROJECT_PROFILE auto-fill.
- License decision.
- ENKI push.

## Implementation Steps

1. Write ENKI ownership config from source `system_defaults` plus approved project overrides.
2. Run `ownership-lock.py --root <ENKI_WIKI_PATH> write`.
3. Commit the ownership baseline locally in ENKI.
4. Re-run `agent-flow adopt --target <ENKI_WIKI_PATH> --format json`.
5. Apply only safe missing files with `upgrade-from-skeleton.py --target <ENKI_WIKI_PATH> --apply --safe-only --profile stable --format json`.
6. Refresh ENKI ownership lock after safe additions.
7. Run ENKI validation checks available in the target.
8. Commit safe additions locally in ENKI.

## Definition of Done

- ENKI ownership lock has no drift and no unknown paths.
- ENKI git has a local ownership baseline commit.
- Safe missing files are added without overwriting existing target files.
- ENKI git has a local safe-apply commit.
- Remaining work is limited to manual/risky review and project metadata review.

## Rollback Plan

- Revert the ENKI ownership baseline and safe-apply commits if needed.
- Do not run automatic rollback tooling in this slice.

## Stop Conditions

- Stop if ENKI git has unexpected dirty files before apply.
- Stop if `upgrade-from-skeleton.py --apply --safe-only` tries to overwrite existing target files.
- Stop if ownership lock reports classification drift.
- Stop before risky/manual changes.

## Validation

- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/ownership-lock.py --root <ENKI_WIKI_PATH> check`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/agent-flow.py adopt --target <ENKI_WIKI_PATH> --format json`
- `PYTHONDONTWRITEBYTECODE=1 python3 <ENKI_WIKI_PATH>/scripts/verify-skeleton.py --root <ENKI_WIKI_PATH>`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/agent-flow.py closeout --goal "0026 ENKI ownership baseline and safe apply" --changed-path plans/active/0026-enki-ownership-baseline-and-safe-apply.md --changed-path plans/INDEX.md --format json`

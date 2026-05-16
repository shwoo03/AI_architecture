# 0013-enki-ownership-initialize-dry-run

## Summary

Slice 4 begins the ENKI_WIKI retrofit migration with a read-only ownership initialization report against `~/mydir/ENKI_WIKI`. The intended outcome is a reviewable `project_overrides` draft and risk summary for the already-overlaid ENKI repository, without writing to the target or applying an upgrade.

## Assumptions

- `~/mydir/ENKI_WIKI` is the only ENKI target for this slice.
- `~/mydir/Project/ENKI_WIKI` is out of bounds for this slice.
- ENKI_WIKI has prior stable safe-only overlay content, so the first useful signal is how ownership classification sees retrofit paths.
- The current milestone stops after `ownership-initialize.py --format json`; ownership config creation, lock creation, and upgrade brief are follow-up decisions.
- Pushing the AI_architecture ownership commit is optional and requires explicit user confirmation.

## Out of Scope

- Writing `config/ownership.yaml` or any other file inside `~/mydir/ENKI_WIKI`.
- Running `ownership-lock.py write` against ENKI_WIKI.
- Running `upgrade-from-skeleton.py --apply`, `--safe-only`, or `--include-risky`.
- Committing or pushing ENKI_WIKI changes.
- Touching `~/mydir/Project/ENKI_WIKI`.

## Implementation Steps

- Confirm the real ENKI target path and git status read-only.
- Run `scripts/ownership-initialize.py` against `~/mydir/ENKI_WIKI` with JSON output.
- Summarize analyzed path count, candidate count, grouped draft patterns, and next command.
- Compare the result against the Slice 4 stop conditions before recommending any target write.
- Record the milestone in AI_architecture progress and handoff artifacts.

## Definition of Done

- Plan 0013 exists in `plans/active/` and is indexed.
- `~/mydir/ENKI_WIKI` has not been modified by this milestone.
- `ownership-initialize.py --target ~/mydir/ENKI_WIKI --format json` has been run.
- The JSON report is summarized for review, including whether it emitted a draft, lock-missing state, or already-initialized state.
- AI_architecture validation passes after plan and closeout updates.

## Rollback Plan

- Remove this plan and its index row if the milestone is abandoned before use.
- Re-run `scripts/ownership-lock.py write` in AI_architecture if the ownership lock was refreshed after plan creation.
- Leave `~/mydir/ENKI_WIKI` untouched because this milestone is read-only.

## Stop Conditions

- Stop if `ownership-initialize.py` attempts or requires writes to `~/mydir/ENKI_WIKI`.
- Stop if the report indicates target ownership is already initialized; use `ownership-lock.py check` as the next reviewed step instead.
- Stop if `unknown` or initialization candidate paths exceed 20 before drafting ENKI overrides automatically.
- Stop if later upgrade brief work reports `lock_drift > 0`.
- Stop if later upgrade brief work reports many `update_system` actions for `system_locked` files.
- Stop if protected candidates fall into review/manual queues, indicating ENKI protected globs do not match target paths.

## Validation

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/ownership-initialize.py --target ~/mydir/ENKI_WIKI --format json
python3 scripts/ownership-lock.py write
python3 scripts/ownership-lock.py check
python3 scripts/validate-plans.py --root . --format json
python3 scripts/verify-skeleton.py
python3 scripts/agent-flow.py closeout \
  --goal "Slice 4: ENKI ownership-aware dry-run only, no writes to target" \
  --changed-path plans/active/0013-enki-ownership-initialize-dry-run.md \
  --changed-path plans/INDEX.md \
  --changed-path runtime/ownership-classification.lock.json \
  --format json
```

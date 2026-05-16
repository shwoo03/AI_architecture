# 0027 ENKI Manual Risky System Review

## Summary

Review the remaining ENKI_WIKI adoption intake items after 0026 cleared safe additions and ownership candidate stops. The intended outcome is to move ENKI closer to 100% AI_architecture operating OS parity while preserving ENKI-owned operational data. This slice starts with evidence: diff and classify the 2 manual items and 13 risky system updates before applying any target write.

## Assumptions

- Target is `~/mydir/ENKI_WIKI`.
- 0026 left ENKI clean and ahead of origin by 2 local commits.
- `agent-flow adopt --target ~/mydir/ENKI_WIKI --format json` currently reports `safe_missing=0`, `manual_merge=2`, `risky_changed=13`, `candidate_paths=0`, and no stop reasons.
- Risky system updates are operating OS files, but they may still contain ENKI-local drift that must be inspected before overwrite.

## Out of Scope

- `--include-risky` bulk apply without file-by-file evidence.
- ENKI app feature changes.
- ENKI push.
- PROJECT_PROFILE auto-fill without deriving facts from ENKI files.
- License decision beyond detection/reporting.
- Rollback automation.

## Implementation Steps

1. Capture the current adoption brief and exact remaining manual/risky file list.
2. Diff each remaining file between AI_architecture source and ENKI target.
3. Classify each item as:
   - apply source as operating OS update,
   - preserve ENKI target,
   - manual merge required,
   - metadata-only follow-up.
4. Apply only items whose diff shows target has no ENKI-specific semantic data to preserve.
5. Refresh ENKI ownership lock, handoff, snapshot/recall, and validation.
6. Commit ENKI target changes locally; do not push.
7. Record a validation report and close out this AI_architecture plan.

## Definition of Done

- A 0027 validation report lists all 15 remaining manual/risky items and their disposition.
- Any applied system updates are committed locally in ENKI.
- ENKI working tree is clean after commit.
- ENKI ownership lock has no drift.
- ENKI `verify-skeleton.py` passes.
- AI_architecture adoption intake shows fewer remaining risky/manual items, or the remaining items are explicitly documented as intentional preserves/manual follow-ups.

## Rollback Plan

- Revert only the ENKI local commit created by this slice if a system update proves unsafe.
- Do not use automated rollback tooling.

## Stop Conditions

- Stop before overwriting `config/ownership.yaml` in a way that removes ENKI `project_overrides`.
- Stop before overwriting `AGENTS.md` if the target contains ENKI-specific operating instructions not represented in AI_architecture.
- Stop before any bulk `--include-risky` apply.
- Stop if ENKI git has unexpected dirty files before applying updates.
- Stop if ownership lock reports classification drift.
- Stop before push.

## Validation

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/agent-flow.py adopt --target ~/mydir/ENKI_WIKI --format json
PYTHONDONTWRITEBYTECODE=1 python3 scripts/ownership-lock.py --root ~/mydir/ENKI_WIKI check
PYTHONDONTWRITEBYTECODE=1 python3 ~/mydir/ENKI_WIKI/scripts/verify-skeleton.py --root ~/mydir/ENKI_WIKI
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate-plans.py --root . --format json
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify-skeleton.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/agent-flow.py closeout --goal "0027 ENKI manual risky system review" --changed-path plans/done/0027-enki-manual-risky-system-review.md --changed-path plans/INDEX.md --changed-path runtime/validation/0027-enki-manual-risky-system-review.md --format json
```

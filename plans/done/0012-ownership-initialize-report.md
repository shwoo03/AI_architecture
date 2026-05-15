# 0012-ownership-initialize-report

## Summary

Ownership-aware upgrade v1 Slice 3.5 adds a read-only ownership initialization report for existing target repositories before the first ownership-aware dry-run.

## Assumptions

- Slice 3 has wired ownership checks into verification and upgrade planning.
- Existing repositories may not yet have `config/ownership.yaml` or an ownership lock.
- Initialization must not write target files in v1.
- ENKI_WIKI dry-run remains out of scope until this report path exists.

## Out of Scope

- Applying the generated `project_overrides` draft to a target repository.
- Creating a target lock file automatically.
- ENKI_WIKI migration or dry-run.
- Replacing `upgrade-from-skeleton.py --brief`.

## Implementation Steps

- Add `scripts/ownership-initialize.py` as a standalone internal tool.
- Support `--target`, optional `--source`, and `--format text|json`.
- If the target has no ownership config, scan target paths and output a copy-pasteable `project_overrides.rules` draft grouped by directory depth up to two levels.
- If the target has ownership config but no lock, report that the next action is lock creation/check, without emitting a draft.
- If the target has both ownership config and lock, refuse initialization and direct the user to `scripts/ownership-lock.py check`.
- Add focused unit tests for empty targets, grouped target-specific paths, and already-initialized targets.

## Definition of Done

- Fresh targets produce a read-only draft with JSON and text output.
- Existing initialized targets are rejected without file mutation.
- The tool is registered in `scripts/catalog.yaml` and the ownership map.
- Existing ownership and skeleton validation still pass.

## Rollback Plan

- Remove `scripts/ownership-initialize.py`, `tests/test_ownership_initialize.py`, and the catalog/ownership map entries.
- Remove this plan/index row.
- Regenerate `runtime/ownership-classification.lock.json`.

## Stop Conditions

- If initialization needs to write target files, stop and keep v1 report-only.
- If grouping cannot be explained as deterministic depth-based output, stop and simplify the report.
- If existing ownership config handling overlaps with upgrade application, stop and split the behavior.

## Validation

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_ownership_initialize tests.test_ownership tests.test_skeleton_self_classification -v
python3 scripts/ownership-lock.py write
python3 scripts/ownership-lock.py check
python3 scripts/verify-skeleton.py
python3 scripts/quality-gate.py --root . --tier stable --skip-tests --format json
python3 scripts/agent-flow.py closeout \
  --goal "Ownership-aware upgrade v1 Slice 3.5 initialize report" \
  --changed-path plans/active/0012-ownership-initialize-report.md \
  --changed-path scripts/ownership-initialize.py \
  --changed-path tests/test_ownership_initialize.py \
  --changed-path docs/OWNERSHIP_MODEL.md \
  --changed-path config/ownership.yaml \
  --changed-path runtime/ownership-classification.lock.json \
  --changed-path scripts/catalog.yaml \
  --changed-path plans/INDEX.md \
  --format json
```

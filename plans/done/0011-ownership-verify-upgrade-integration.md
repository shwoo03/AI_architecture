# 0011-ownership-verify-upgrade-integration

## Summary

Ownership-aware upgrade v1 Slice 3 wires the existing ownership classifier into `scripts/verify-skeleton.py` and `scripts/upgrade-from-skeleton.py`.

## Assumptions

- Slice 2.5 has already produced `scripts/lib_ownership.py`, `scripts/ownership-lock.py`, `config/ownership.yaml`, and `runtime/ownership-classification.lock.json`.
- The user explicitly approved starting Slice 3 by requesting implementation.
- Existing target project `project_overrides` must win only where the source ownership model allows overrides.

## Implementation Steps

- Add a `verify-skeleton.py` ownership gate for `config/ownership.yaml`, `runtime/ownership-classification.lock.json`, unknown paths, and classification drift.
- Make `upgrade-from-skeleton.py` classify source files with `scripts/lib_ownership.py` before planning add/update/review/skip actions.
- Preserve target `project_overrides` when target `config/ownership.yaml` exists while using source `system_defaults`.
- Keep stable safe missing seeds for bootstrap/overlay support files, including initial ownership config and lock files.
- Add focused regression coverage for verify drift reporting and ownership-aware upgrade planning.

## Out of Scope

- `--initialize` report mode for target ownership bootstrap.
- Automatic merge of existing target `config/ownership.yaml`.
- Applying manual merge entries without explicit user approval.

## Definition of Done

- `verify-skeleton.py` fails loudly on missing ownership config, missing lock, unknown durable paths, and classification drift.
- `upgrade-from-skeleton.py` emits ownership metadata in JSON actions and treats existing `manual_merge` paths as manual review rather than risky overwrite candidates.
- Stable safe-only overlay can seed the ownership config and lock into older targets without overwriting project state.
- The ownership lock is refreshed after adding this plan path.

## Rollback Plan

- Revert `scripts/verify-skeleton.py`, `scripts/upgrade-from-skeleton.py`, `scripts/lib_ownership.py`, and the focused tests changed for Slice 3.
- Remove this plan from `plans/active/` and remove its index row.
- Regenerate `runtime/ownership-classification.lock.json` with `python3 scripts/ownership-lock.py write`.

## Stop Conditions

- If ownership integration requires overwriting target project-owned state automatically, stop and redesign the action mapping.
- If `verify-skeleton.py` cannot distinguish lock additions/removals from classification drift, stop and keep the check outside the default verifier.
- If stable upgrade safe-only no longer seeds a self-verifiable target, stop before changing apply behavior.

## Validation

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_validation.ScriptCatalogValidationTests.test_current_root_ownership_check_has_no_errors tests.test_validation.ScriptCatalogValidationTests.test_ownership_check_reports_classification_drift -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_bootstrap_upgrade.UpgradeFromSkeletonTests.test_dry_run_reports_missing_safe_files_and_risky_updates tests.test_bootstrap_upgrade.UpgradeFromSkeletonTests.test_brief_json_is_dry_run_ai_summary tests.test_bootstrap_upgrade.UpgradeFromSkeletonTests.test_ownership_aware_upgrade_classifies_system_owned_and_config_seed -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_ownership tests.test_skeleton_self_classification tests.test_bootstrap_upgrade tests.test_validation -v
python3 scripts/ownership-lock.py check
python3 scripts/verify-skeleton.py
python3 scripts/agent-flow.py closeout --goal 'Ownership-aware upgrade v1 Slice 3 verify/upgrade integration' --changed-path plans/active/0011-ownership-verify-upgrade-integration.md --changed-path scripts/lib_ownership.py --changed-path scripts/verify-skeleton.py --changed-path scripts/upgrade-from-skeleton.py --changed-path tests/test_ownership.py --changed-path tests/test_validation.py --changed-path tests/test_bootstrap_upgrade.py --changed-path runtime/ownership-classification.lock.json --format json
```

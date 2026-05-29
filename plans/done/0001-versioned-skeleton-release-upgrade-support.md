# versioned skeleton release upgrade support

## Summary
- Goal: versioned skeleton release upgrade support
- Status: done

## Assumptions
- The user has approved implementation of this goal.
- Changes stay inside the project repository.

## Out of Scope
- External network changes, dependency installation, and publishing.

## Implementation Steps
- Inspected the existing adoption, upgrade, install-state, and feature-status contracts.
- Added release manifest generation/checking for stable/preview/edge skeleton channels.
- Extended install-state with optional release fields while preserving existing required fields.
- Connected upgrade brief/apply and agent-flow adopt output to release provenance.
- Updated focused tests and documentation.
- Ran the validation commands below.

## Definition of Done
- Required release manifest and release-aware upgrade support is implemented.
- Focused tests and full unittest suite pass.
- Closeout evidence and handoff are updated.

## Rollback Plan
- Revert only the files changed for this plan.

## Stop Conditions
- Stop if validation reveals unrelated unexpected changes.
- Stop if a write would escape the repository boundary.

## Validation
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_bootstrap_upgrade.UpgradeFromSkeletonTests.test_release_manifest_generate_and_check_current_skeleton tests.test_bootstrap_upgrade.UpgradeFromSkeletonTests.test_brief_json_is_dry_run_ai_summary tests.test_bootstrap_upgrade.UpgradeFromSkeletonTests.test_safe_only_apply_copies_missing_templates_without_overwrite -v`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_ledgers.InstallStateTests.test_skeleton_release_applied_accepts_additive_release_fields tests.test_agent_flow.AgentFlowTests.test_adopt_reads_old_install_state_with_fallback tests.test_validation.ScriptHelpTests.test_each_main_script_prints_help -v`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/schema-check.py --format json`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/feature-status.py --format json check --tier all`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/release-manifest.py --format json summary`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/agent-flow.py closeout --goal "versioned skeleton release upgrade support" --plan-id 0001-versioned-skeleton-release-upgrade-support --changed-path . --format json`

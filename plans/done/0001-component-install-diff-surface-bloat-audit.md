# component-level install/diff manifest와 skills/agents bloat audit 구현

## Summary
- Goal: component-level install/diff manifest와 skills/agents bloat audit 구현
- Status: done

## Assumptions
- The user has approved implementation of this goal.
- Changes stay inside the project repository.

## Out of Scope
- External network changes, dependency installation, and publishing.

## Implementation Steps
- Inspect the existing project contracts.
- Implement the smallest safe changes.
- Update focused tests and documentation where needed.
- Run the validation commands below.

## Definition of Done
- Required files are implemented.
- Focused tests pass.
- Closeout evidence and handoff are updated.

## Rollback Plan
- Revert only the files changed for this plan.

## Stop Conditions
- Stop if validation reveals unrelated unexpected changes.
- Stop if a write would escape the repository boundary.

## Validation
- `python3 scripts/agent-flow.py closeout --goal "component-level install/diff manifest와 skills/agents bloat audit 구현" --plan-id 0001-component-install-diff-surface-bloat-audit --changed-path . --format json`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_bootstrap_upgrade.UpgradeFromSkeletonTests -v`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_validation.SurfaceBloatAuditTests -v`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/surface-bloat-audit.py --format json`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/schema-check.py --format json`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify-skeleton.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/ownership-lock.py check`

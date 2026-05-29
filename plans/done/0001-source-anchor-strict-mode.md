# source anchor strict mode

## Summary
- Goal: source anchor strict mode
- Status: done

## Assumptions
- The user has approved implementation of this goal.
- Changes stay inside the project repository.

## Out of Scope
- External network changes, dependency installation, and publishing.
- Refreshing every existing candidate card so all of them pass strict source-anchor mode.
- Making strict source-anchor checks part of global closeout or stable quality-gate defaults.

## Implementation Steps
- Inspect the existing project contracts.
- Add optional strict source-anchor checks to reference candidate/proposal/copy validation surfaces.
- Add source-anchor evidence to skill lifecycle promotion/demotion proposals.
- Update focused tests and documentation where needed.
- Run the validation commands below.

## Definition of Done
- Default reference/copy validators still pass on the current repository.
- `--strict-source-anchor` rejects placeholder anchors such as `local-reference`, `external-reference`, `not checked`, and missing candidate/proposal links.
- Skill lifecycle proposals include source anchors for skill path, usage ledger, lifecycle ledger, and policy source.
- Focused and full tests pass.
- Closeout evidence and handoff are updated.

## Rollback Plan
- Revert only the files changed for this plan.

## Stop Conditions
- Stop if validation reveals unrelated unexpected changes.
- Stop if a write would escape the repository boundary.

## Validation
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_reference_security tests.test_ledgers tests.test_validation.ScriptHelpTests tests.test_validation.ScriptsCompileTests -v`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate-reference-candidates.py --root .`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate-reference-proposals.py --root .`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/reference-copy-ledger.py --root . check`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/agent-flow.py closeout --goal "source anchor strict mode" --plan-id "0001-source-anchor-strict-mode" --changed-path scripts/validate-reference-candidates.py --changed-path scripts/validate-reference-proposals.py --changed-path scripts/reference-copy-ledger.py --changed-path scripts/skill-lifecycle.py --changed-path tests/test_reference_security.py --changed-path tests/test_ledgers.py --changed-path scripts/README.md --changed-path docs/REFERENCE_DISCOVERY_WORKFLOW.md --changed-path docs/RUNTIME_EVENT_SCHEMA.md --profile auto --format json`

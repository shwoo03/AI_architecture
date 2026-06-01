# Eval release gate example

Use for an agent runtime app when behavior changes are risky enough to need a
release decision. This is documentation only, not an eval runner.

## Scope

- Runtime behavior changed:
- Affected agents/tools:
- Safety-sensitive paths:

## Required checks

- [ ] Normal software tests pass.
- [ ] Existing eval cases pass.
- [ ] New regression case added for the changed behavior.
- [ ] Trace review completed for one success and one failure path.
- [ ] Tool permission changes are recorded.
- [ ] Handoff updated with result and next action.

## Decision

- Release:
- Hold:
- Owner:
- Evidence:

## Notes

- LLM evals do not replace unit/integration tests.
- Failed evals must lead to a fix, a regression case, or a documented rejection.

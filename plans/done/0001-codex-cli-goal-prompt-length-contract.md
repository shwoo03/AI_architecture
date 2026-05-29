# Codex CLI goal prompt length contract

## Summary
- Goal: Codex CLI goal prompt length contract
- Status: done
- Treat user requests for `goal 프롬프트` as Codex CLI `/goal` prompt requests and enforce a 4000-character ceiling.

## Assumptions
- The user has approved implementation of this goal.
- Changes stay inside the project repository.
- Long details can be documented separately and referenced from a shorter `/goal` prompt.

## Out of Scope
- External network changes, dependency installation, and publishing.
- Changing Codex CLI itself.
- Automatically generating long design documents for every goal prompt request.

## Implementation Steps
- Add a small prompt length checker for Codex CLI `/goal` prompts.
- Document the 4000-character rule in the agent entrypoint, operating loop, script docs, and goal prompt README.
- Add focused tests for at-limit and over-limit prompts.
- Run focused tests and closeout validation.

## Definition of Done
- `goal 프롬프트` is documented as Codex CLI `/goal`.
- `/goal` prompts are documented and validated as 4000 characters or fewer.
- Over-limit content must be split into a separate document and referenced by the `/goal` prompt.
- Focused tests pass.
- Closeout evidence and handoff are updated.

## Rollback Plan
- Revert only the files changed for this plan.

## Stop Conditions
- Stop if validation reveals unrelated unexpected changes.
- Stop if a write would escape the repository boundary.

## Validation
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_validation.GoalPromptCheckTests tests.test_validation.ScriptHelpTests.test_each_main_script_prints_help -v`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/goal-prompt-check.py --text "/goal verify this prompt" --format json`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/agent-flow.py closeout --goal "Codex CLI goal prompt length contract" --changed-path AGENTS.md --changed-path docs/OPERATING_LOOP.md --changed-path docs/goal-prompts/README.md --changed-path scripts/README.md --changed-path scripts/catalog.yaml --changed-path scripts/goal-prompt-check.py --changed-path tests/test_validation.py --changed-path plans/done/0001-codex-cli-goal-prompt-length-contract.md --plan-id 0001-codex-cli-goal-prompt-length-contract --format json`

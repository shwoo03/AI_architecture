# 0034-claude-strategy-critic-boundary

## Summary
- Goal: Make real Claude a strategy/critique participant only and forbid Claude subagent usage in the dialogue ledger.
- Status: done

## Assumptions
- The user has approved implementation of this goal.
- Changes stay inside the project repository.
- The rule applies to real Claude dialogue records (`from: claude`), not to the explicitly labeled fallback critic used when Claude is unavailable.

## Out of Scope
- External network changes, dependency installation, and publishing.
- Automatic Claude CLI invocation.
- New subagent orchestration, DAGs, or background workers.

## Implementation Steps
- Add machine-checkable dialogue policy fields for Claude's role boundary.
- Make `agent-flow dialogue` record real Claude turns as `strategy_critic_only` with `subagents_allowed=false`.
- Make `dialogue-lint.py` reject real Claude records that use or record subagents.
- Update focused tests and runtime documentation.

## Definition of Done
- Real Claude turns require `provider=claude_cli`.
- Real Claude turns cannot set `subagents_allowed=true`, `uses_subagents=true`, or non-empty subagent/delegation fields.
- Fallback critic remains allowed only as `from: claude-fallback-critic`, `provider=fallback_subagent`.
- Focused tests pass.
- Closeout evidence records this plan id.

## Rollback Plan
- Revert only the files changed for this plan.

## Stop Conditions
- Stop if validation reveals unrelated unexpected changes.
- Stop if a write would escape the repository boundary.

## Validation
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_validation.DialogueLintTests -v`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_agent_flow.AgentFlowTests.test_dialogue_real_claude_turn_records_strategy_critic_boundary tests.test_agent_flow.AgentFlowTests.test_dialogue_rejects_real_claude_manual_provider tests.test_agent_flow.AgentFlowTests.test_dialogue_rejects_unlabeled_fallback_as_claude -v`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/dialogue-lint.py --help`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/agent-flow.py closeout --goal "Claude strategy critic boundary" --changed-path scripts/dialogue-lint.py --changed-path scripts/agent-flow.py --changed-path tests/test_validation.py --changed-path tests/test_agent_flow.py --changed-path docs/RUNTIME_EVENT_SCHEMA.md --changed-path scripts/README.md --changed-path plans/done/0034-claude-strategy-critic-boundary.md --plan-id 0034-claude-strategy-critic-boundary --format json`

# subagent debate workflow replaces Claude auto dialogue

## Summary
- Goal: subagent debate workflow replaces Claude auto dialogue
- Status: done
- Replace Claude-centered critical planning with a subagent debate ledger where Codex remains orchestrator and at least one scoped subagent critique/research/verification role participates before convergence.

## Assumptions
- The user has approved implementation of this goal.
- Changes stay inside the project repository.
- The repo should not invoke Claude automatically or treat Claude session expiry as the trigger for fallback debate.
- Repository scripts record debate artifacts only; actual subagent creation remains a surrounding harness responsibility.

## Out of Scope
- External network changes, dependency installation, and publishing.
- Automatic subagent spawning from repository scripts.
- Renumbering historical plans or changing generated `.codex/`/`.claude/` artifacts.
- Integrating a dashboard, DB, or multi-agent runtime.

## Implementation Steps
- Search current multi-agent/subagent debate best practices and translate only the skeleton-relevant guardrails.
- Update `agent-flow dialogue` and `dialogue-lint.py` from Claude/fallback readiness to Codex plus scoped subagent readiness.
- Update focused tests and documentation/catalog references.
- Run focused dialogue tests, script help/compile checks, and skeleton validation.

## Definition of Done
- `dialogue start` records `claude_auto_debate_disabled=true` and `nested_subagents_allowed=false`.
- `dialogue converge` requires Codex plus at least one `subagent-*` readiness and rejects unresolved block critiques.
- Claude/fallback participants are no longer accepted by the dialogue CLI or validator.
- Focused tests pass.
- Closeout evidence and handoff are updated with this plan id.

## Rollback Plan
- Revert only the files changed for this plan.

## Stop Conditions
- Stop if validation reveals unrelated unexpected changes.
- Stop if a write would escape the repository boundary.

## Validation
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_agent_flow.AgentFlowTests.test_dialogue_lifecycle_converges_after_resolved_subagent_block tests.test_agent_flow.AgentFlowTests.test_dialogue_rejects_claude_as_participant tests.test_agent_flow.AgentFlowTests.test_dialogue_subagent_turn_records_debate_policy tests.test_agent_flow.AgentFlowTests.test_dialogue_rejects_subagent_manual_provider tests.test_validation.DialogueLintTests -v`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/dialogue-lint.py --help`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/agent-flow.py closeout --goal "subagent debate workflow replaces Claude auto dialogue" --changed-path scripts/agent-flow.py --changed-path scripts/dialogue-lint.py --changed-path tests/test_agent_flow.py --changed-path tests/test_validation.py --changed-path docs/RUNTIME_EVENT_SCHEMA.md --changed-path scripts/README.md --changed-path scripts/catalog.yaml --changed-path plans/active/0001-subagent-debate-workflow-replaces-claude-auto-di.md --plan-id 0001-subagent-debate-workflow-replaces-claude-auto-di --format json`

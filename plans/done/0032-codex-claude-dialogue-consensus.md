# 0032-codex-claude-dialogue-consensus

## Summary
Implement the first slice of a task-scoped Codex-Claude critical planning loop. The smallest useful outcome is a structured dialogue ledger, a validator, and `agent-flow dialogue` commands that can start a planning dialogue, record targeted claims/critiques/concessions, report unresolved blockers, and freeze an implementation scope only after convergence.

## Assumptions
- The user approved this implementation slice in chat.
- This slice does not make Claude run automatically for every task.
- A fallback critic is allowed only when real Claude is unavailable, and must be recorded as fallback rather than represented as Claude.
- The main Codex session remains the orchestrator and implementation owner.

## Out of Scope
- Automatic Claude CLI invocation.
- Automatic subagent spawn or always-on background agents.
- Implementing work outside a converged `implementation_scope`.
- Changing generated `.codex/` or `.claude/` surfaces directly.

## Implementation Steps
- Add a `runtime/dialogues/*.jsonl` ledger contract with turn IDs, targeted critiques, severity, evidence, convergence, and implementation scope.
- Add `scripts/dialogue-lint.py` to validate dialogue ledgers.
- Add `agent-flow dialogue start|add-turn|status|converge` as a thin public wrapper.
- Add focused tests for validator failures, successful convergence, and agent-flow dialogue lifecycle.
- Document the runtime event/ledger boundary and script catalog entry.
- Register the new validator script in ownership metadata as a system-owned operating script.

## Definition of Done
- `dialogue-lint.py` rejects critiques without target IDs, block critiques without evidence, and convergence with unresolved block critiques.
- `agent-flow dialogue start` creates a dialogue ledger for a task.
- `agent-flow dialogue add-turn` records structured Codex/Claude/fallback critic turns.
- `agent-flow dialogue converge` writes an explicit `implementation_scope` and refuses open blockers.
- Focused tests and skeleton verification pass.

## Rollback Plan
- Revert `scripts/dialogue-lint.py`, `scripts/agent-flow.py` dialogue command changes, focused tests, and documentation/catalog updates.
- Remove runtime dialogue artifacts generated only for manual smoke if they are not needed as evidence.

## Stop Conditions
- Stop if the implementation would auto-run Claude without explicit task context.
- Stop if fallback output could be mistaken for real Claude output.
- Stop if implementation scope can be marked converged with unresolved block critiques.
- Stop if the command mutates files outside `runtime/dialogues/` before convergence.

## Validation
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_agent_flow.AgentFlowTests -v`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_validation.DialogueLintTests -v`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate-plans.py --allow-legacy-done`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify-skeleton.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/agent-flow.py closeout --goal "Codex-Claude dialogue consensus first slice" --changed-path scripts/dialogue-lint.py --changed-path scripts/agent-flow.py --changed-path tests/test_agent_flow.py --changed-path tests/test_validation.py --changed-path docs/RUNTIME_EVENT_SCHEMA.md --changed-path scripts/catalog.yaml --changed-path scripts/README.md --changed-path config/ownership.yaml --changed-path plans/active/0032-codex-claude-dialogue-consensus.md --format json`

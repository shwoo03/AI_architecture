# 0022 Spawn-Ready Packet

## Summary

Implement harness-agnostic spawn-ready packets for approved specialist delegation plans. This slice creates a packet artifact that an external runtime harness can read, but it does not spawn agents, auto-chain work, or promote the execution loop to stable.

## Assumptions

- 0017 `DelegationPlan`, 0018 approved execute boundary, 0020 usage evidence, and 0021 validator verdict loop are already implemented.
- Actual subagent spawning is performed by the surrounding Codex/Claude/opencode/manual harness, not by repository scripts.
- Each specialist unit remains individually confirmation-gated.
- Existing delegate handoffs and AgentBrief artifacts remain the source of packet unit details.

## Out of Scope

- No automatic subagent spawn.
- No recursive delegation.
- No stable promotion.
- No provider-specific packet schema.
- No recommendation scoring changes.
- No mutation of AgentRun records.

## Implementation Steps

1. Add `agent-flow specialist packet --plan <plan> --confirm` under the existing public `agent-flow.py` entrypoint.
2. Require approved `DelegationPlan` status, non-empty selected roles, and explicit confirmation.
3. Reuse the existing incubating delegate path to create AgentBrief handoffs.
4. Write `runtime/spawn-packets/*.json` using `ai-architecture.spawn-ready-packet.v1`.
5. Include role, brief, write scope, validation command, completion command, expected result schema, and harness hints for each unit.
6. Mark packet metadata as harness-agnostic, no auto-spawn, no auto-chain, and no recursive delegation.
7. Add tests and docs.

## Definition of Done

- `specialist packet` writes a packet for an approved and confirmed plan.
- Packet units reference real AgentBrief artifacts and AgentRun completion commands.
- Draft plans and missing confirmation are rejected.
- Focused tests pass.
- `verify-skeleton`, stable/all quality gates, ownership lock, codemap freshness, and closeout pass.

## Rollback Plan

- Revert `scripts/agent-flow.py`, tests, docs, this plan, and the 0022 INDEX row.
- Remove only uncommitted `runtime/spawn-packets/*.json` artifacts produced by the reverted slice.

## Stop Conditions

- Stop if implementation spawns agents.
- Stop if packet format becomes Codex-only, Claude-only, or provider-specific.
- Stop if recursive delegation is allowed.
- Stop if execution can proceed from a draft plan or without confirmation.
- Stop if AgentRun records are modified instead of appended later by the runtime/operator.

## Validation

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_agent_flow -v`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate-plans.py --root . --format json`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/ownership-lock.py write`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/generate-codemaps.py --write`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify-skeleton.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/quality-gate.py --root . --tier stable --skip-tests --format json`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/quality-gate.py --root . --tier all --skip-tests --format json`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/agent-flow.py closeout --goal "0022 spawn-ready packet" --changed-path scripts/agent-flow.py --changed-path tests/test_agent_flow.py --changed-path docs/AGENT_REGISTRY.md --changed-path docs/RUNTIME_EVENT_SCHEMA.md --changed-path scripts/README.md --changed-path plans/INDEX.md --changed-path plans/done/0022-spawn-ready-packet.md --format json`

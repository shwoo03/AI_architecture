# 0020 Specialist Usage Evidence Ledger

## Summary
Specialist preview, proposal decision, delegation approval, and execution-preparation decisions now append advisory evidence to `runtime/specialist-usage.jsonl`. This ledger records what happened without changing recommendation scoring, creating specialists automatically, producing validator verdicts, or generating spawn packets.

## Assumptions
- 0016 `SpecialistProposal`, 0017 `DelegationPlan`, and 0018 approved execute boundaries are already implemented.
- `runtime/agent-runs.jsonl` remains the execution ledger.
- `runtime/specialist-usage.jsonl` is only recommendation/decision evidence.
- 0021 must wait for at least 20 external or real-use specialist evidence records; 30 or more is preferred.

## Out of Scope
- Recommendation scoring changes.
- Automatic specialist creation, selection, chaining, or spawn.
- Validator verdicts.
- Spawn-ready packet generation.
- Existing AgentRun schema migration.
- `docs/feature-status.yaml` tier changes.

## Implementation Steps
- Add append-only specialist usage helpers to `scripts/agent-flow.py`.
- Record `preview_created`, `proposal_approved`, `proposal_rejected`, `delegation_plan_approved`, `delegation_execute_blocked`, and `delegation_execute_prepared`.
- Keep all fixed v1 fields present with empty strings, false values, or empty lists for not-applicable fields.
- Redact string-like user input through `scripts/redact.py` before ledger append.
- Document the ledger contract in `docs/RUNTIME_EVENT_SCHEMA.md`.
- Add focused tests in `tests/test_agent_flow.py`.

## Definition of Done
- Focused specialist usage tests pass.
- `tests.test_agent_flow` passes.
- `verify-skeleton`, stable quality gate, all-tier quality gate, ownership lock, codemap freshness, and closeout pass.
- `plans/INDEX.md` lists 0020 as done.

## Rollback Plan
- Revert `scripts/agent-flow.py`, `tests/test_agent_flow.py`, `docs/RUNTIME_EVENT_SCHEMA.md`, this plan file, and the 0020 INDEX row.
- Delete `runtime/specialist-usage.jsonl` if it exists and only contains records produced by the reverted implementation.

## Stop Conditions
- Stop if implementation changes specialist scoring or candidate selection.
- Stop if records trigger automatic execution or recursive delegation.
- Stop if validator verdicts or spawn packet fields are added.
- Stop if existing AgentRun records need mutation.

## Validation
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_agent_flow -v`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify-skeleton.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/quality-gate.py --root . --tier stable --skip-tests --format json`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/quality-gate.py --root . --tier all --skip-tests --format json`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/agent-flow.py closeout --goal "0020 specialist usage evidence ledger" --changed-path scripts/agent-flow.py --changed-path tests/test_agent_flow.py --changed-path docs/RUNTIME_EVENT_SCHEMA.md --changed-path plans/INDEX.md --changed-path plans/done/0020-specialist-usage-evidence-ledger.md --format json`

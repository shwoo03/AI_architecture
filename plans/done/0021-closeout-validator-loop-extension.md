# 0021 Closeout Validator Loop Extension

## Summary

Implement the first validator loop slice by extending the existing `closeout-validator` role and AgentRun ledger. This slice adds append-only validator verdict records for specialist runs without creating a new validator agent, a new execution loop, or automatic spawn behavior.

## Assumptions

- 0016-0018 specialist proposal, preview, and execute-preparation flows are already done.
- 0020 specialist usage evidence is already done.
- The user explicitly opened this implementation exception before the preferred 20+ evidence accumulation threshold.
- `runtime/agent-runs.jsonl` remains the AgentRun execution ledger.
- Validator records must be additive only; existing AgentRun records are never rewritten.

## Out of Scope

- No automatic subagent spawn.
- No new validator specialist.
- No stable promotion of validator-loop.
- No recommendation scoring changes.
- No migration of existing `runtime/agent-runs.jsonl` records.
- No mutation of existing AgentRun records.

## Implementation Steps

1. Add additive AgentRun statuses for validator-loop outcomes: `paused`, `aborted`, and `partial`.
2. Add a `validate` subcommand to `scripts/incubating/agent-run.py` that requires a `closeout-validator` brief and a target AgentRun id.
3. Map validator verdicts to next status: `pass -> completed`, `warn -> partial`, `fail -> failed`, `needs_human -> paused`.
4. Append a new AgentRun record with `workflow=validator_loop`, `agent=closeout-validator`, and `ext.validator` metadata.
5. Keep verdicts append-only and preserve target run lineage.
6. Document the validator-loop schema and closeout-validator role contract.
7. Add focused regression tests.

## Definition of Done

- `agent-run.py validate` appends validator records without rewriting target records.
- `agent-run.py check` accepts the new additive statuses and validates `ext.validator` for validator-loop records.
- `agent-run.py summary` counts unresolved non-success statuses.
- Tests cover pass, needs_human, and invalid non-validator brief cases.
- `plans/INDEX.md` lists 0021 as done after closeout.

## Rollback Plan

- Revert `scripts/incubating/agent-run.py`, tests, docs, this plan, and the INDEX row.
- Do not edit existing ledger records. If local test-only `runtime/agent-runs.jsonl` records were produced by this slice, remove only those uncommitted test artifacts.

## Stop Conditions

- Stop if implementation needs to edit existing AgentRun records.
- Stop if a new validator agent or new execution loop is introduced.
- Stop if validator verdicts auto-spawn or auto-select specialists.
- Stop if stable promotion is required.
- Stop if the validator can broaden write permissions.

## Validation

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_validation -v`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/incubating/agent-run.py --root . check --format json`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate-plans.py --root . --format json`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify-skeleton.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/quality-gate.py --root . --tier stable --skip-tests --format json`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/quality-gate.py --root . --tier all --skip-tests --format json`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/agent-flow.py closeout --goal "0021 closeout-validator loop extension" --changed-path scripts/incubating/agent-run.py --changed-path tests/test_validation.py --changed-path config/agent-team.yaml --changed-path docs/AGENT_REGISTRY.md --changed-path docs/RUNTIME_EVENT_SCHEMA.md --changed-path scripts/README.md --changed-path plans/INDEX.md --changed-path plans/done/0021-closeout-validator-loop-extension.md --format json`

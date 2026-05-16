# 0018 Execution Loop

## Summary

Define and implement the execution boundary for specialist delegation. This slice prepares approved delegation through the existing incubating delegate path without auto-spawn, stable promotion, or a second execution loop.

0018 consumes an approved `DelegationPlan` from 0017 and limits execution triggers to explicit user or session approval.

Status: done. Implemented through `scripts/agent-flow.py specialist execute`, which prepares existing incubating delegate handoffs only after approval and confirmation.

## Assumptions

- 0017 defines the `DelegationPlan` draft interface.
- Existing incubating execution surfaces remain `scripts/incubating/agent-flow-delegate.py` and `scripts/incubating/agent-run.py`.
- Agent briefs and agent-run ledger entries remain the evidence surfaces for delegated work.
- Specialist execution remains incubating until separately promoted.
- `docs/_meta/SPECIALIST_AGENT_USAGE_BEST_PRACTICES.md` defines approval, least-privilege, context-minimization, and audit expectations for specialist execution.

## Interface Contract

Input: an approved `DelegationPlan` from 0017 with `plan_id`, `goal`, `candidate_roles`, `selected_roles`, `role_source`, `score_reasons`, `read_scope`, `write_policy`, `requires_confirmation`, and `status`.

Trigger: execution may proceed only when the `DelegationPlan` status is `approved` and the current user/session has explicitly approved execution. A draft or rejected plan cannot trigger execution.

Boundary: future implementation must reuse the existing incubating delegate path. It may pass selected roles into `scripts/incubating/agent-flow-delegate.py` and record run evidence through `scripts/incubating/agent-run.py`, but it must not create a second execution loop.

Output evidence: future execution should preserve AgentBrief artifacts, AgentRun ledger entries, `goal_lineage`, `role_source`, changed paths, validation results, and closeout commands. This plan only defines that boundary; it does not write or execute those artifacts.

## Out of Scope

- No automatic specialist spawn is implemented.
- No new execution loop is designed or implemented.
- No stable public promotion is made.
- Existing delegate and agent-run behavior remain the execution evidence path.
- No execution occurs from draft `DelegationPlan` output.

## Implementation Steps

This slice defines execution boundaries and implements approved handoff preparation.

1. Treat the 0017 `DelegationPlan` as the only execution-boundary input.
2. Require `status: approved` plus explicit user/session approval before any future execution.
3. Identify the future extension boundary as the existing incubating delegate and agent-run surfaces.
4. Minimize context passed to specialists and require concise returned summaries unless raw detail is needed for verification.
5. Define required evidence continuity: AgentBrief, AgentRun ledger, `goal_lineage`, `role_source`, changed paths, validation, and closeout.
6. Keep execution behavior unchanged until a separate implementation exception is opened.

## Definition of Done

- This plan exists in `plans/done/`.
- `plans/INDEX.md` lists 0018 as done.
- The `Interface Contract` references the 0017 `DelegationPlan` fields.
- Trigger conditions are limited to approved plan plus explicit user/session approval.
- Hook points are constrained to existing incubating delegate surfaces.
- `agent-flow specialist execute` refuses draft plans and refuses approved plans without `--confirm`.
- Validation commands complete or any blocker is recorded.

## Rollback Plan

- Revert the 0018 implementation changes and remove `plans/done/0018-execution-loop.md` plus its INDEX row if the implementation is withdrawn.
- Add a corrective decision entry rather than editing previous decisions.
- Regenerate ownership lock and codemaps after rollback if file membership changes.

## Stop Conditions

- Stop if the plan introduces a new execution loop.
- Stop if the plan implies automatic spawn from a preview artifact.
- Stop if the plan promotes incubating delegate behavior to stable.
- Stop if the plan bypasses AgentBrief or AgentRun ledger evidence.
- Stop if execution can happen without explicit user/session approval for the approved `DelegationPlan`.
- Stop if the plan prescribes concrete code edits to scripts, schemas, CLI behavior, or delegate behavior.

## Validation

- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate-plans.py --root . --format json`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/ownership-lock.py write`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/generate-codemaps.py --write`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify-skeleton.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/quality-gate.py --root . --tier stable --skip-tests --format json`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/quality-gate.py --root . --tier all --skip-tests --format json`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/agent-flow.py closeout --goal "0016-0018 specialist flow implementation" --changed-path scripts/agent-flow.py --changed-path tests/test_agent_flow.py --changed-path docs/AGENT_REGISTRY.md --changed-path docs/RUNTIME_EVENT_SCHEMA.md --changed-path plans/done/0016-specialist-proposal-add.md --changed-path plans/done/0017-orchestration-preview.md --changed-path plans/done/0018-execution-loop.md --changed-path plans/INDEX.md --format json`

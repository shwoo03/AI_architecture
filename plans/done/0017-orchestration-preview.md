# 0017 Orchestration Preview

## Summary

Define and implement the interface for previewing which specialists could be delegated for a goal. This slice did not add a new router; it added an `agent-flow specialist preview` surface under the existing public entrypoint.

0017 consumes the `SpecialistProposal` schema from 0016 and produces a draft `DelegationPlan` contract for 0018.

Status: done. Implemented through `scripts/agent-flow.py specialist preview`.

## Assumptions

- 0016 defines the `SpecialistProposal` schema.
- Existing goal-to-candidate scoring should remain rooted in `scripts/agent-flow.py` and `scripts/catalog.yaml`.
- Project specialist overlays remain governed by the 0015 additive-only rules.
- Preview output is review material and does not trigger execution.
- `docs/_meta/SPECIALIST_AGENT_USAGE_BEST_PRACTICES.md` defines when preview should select zero specialists, base roles, skills, or project specialists.

## Interface Contract

Input: one or more `SpecialistProposal` records from 0016, including `proposal_id`, `role`, `mission`, `write_policy`, `default_scope`, `recommended_checks`, `status`, `source_registry`, `created_by`, `created_at`, `reason`, and `review_notes`.

Transform: convert eligible specialist proposals and existing base roles into candidate roles for existing goal-to-candidate scoring. Score explanations must preserve why a role was selected or rejected without inventing a separate routing system. `score_reasons` should include trigger matches and anti-trigger matches from the best-practices report.

Output: a draft `DelegationPlan` with these fields:

- `plan_id`: stable identifier for the preview artifact.
- `goal`: user goal or normalized goal line.
- `candidate_roles`: roles considered by the preview.
- `selected_roles`: roles proposed for delegation.
- `role_source`: `base` or `project` for each selected role.
- `score_reasons`: concise evidence for role selection or non-selection.
- `read_scope`: paths or domains expected to be read.
- `write_policy`: proposed write boundary for the delegation.
- `requires_confirmation`: whether user/session approval is required before execution.
- `status`: one of `draft`, `approved`, or `rejected`.

The `DelegationPlan` is a preview artifact only. 0018 may consume an approved `DelegationPlan` as an execution-boundary input.

## Out of Scope

- No new router is designed or implemented.
- No separate public script is added.
- No execution loop, auto-spawn, or delegate behavior is changed.
- No concrete code-edit steps for scripts, schemas, or CLI behavior are prescribed.
- No overlay permission broadening is allowed.

## Implementation Steps

This slice defines contracts and implements preview generation through the existing public entrypoint.

1. Treat the 0016 `SpecialistProposal` schema as the only proposal input format.
2. Identify the future hook point as the existing `scripts/agent-flow.py` and `scripts/catalog.yaml` goal-to-candidate scoring path.
3. Define how base roles and project proposal roles appear together in `candidate_roles` while preserving `role_source`.
4. Allow preview to select zero specialists when base roles, skills, or the main conversation are enough.
5. Define the `DelegationPlan` draft output that 0018 can consume after approval.
6. Keep routing behavior unchanged until a separate implementation exception is opened.

## Definition of Done

- This plan exists in `plans/done/`.
- `plans/INDEX.md` lists 0017 as done.
- The `Interface Contract` names the 0016 input and `DelegationPlan` output fields.
- Hook points are constrained to existing goal-to-candidate scoring surfaces.
- `agent-flow specialist preview` writes a `DelegationPlan` preview and can select zero specialists.
- Validation commands complete or any blocker is recorded.

## Rollback Plan

- Revert the 0017 implementation changes and remove `plans/done/0017-orchestration-preview.md` plus its INDEX row if the implementation is withdrawn.
- Add a corrective decision entry rather than editing previous decisions.
- Regenerate ownership lock and codemaps after rollback if file membership changes.

## Stop Conditions

- Stop if the plan introduces a new router or parallel routing model.
- Stop if the plan adds a public command or changes CLI behavior.
- Stop if the plan prescribes concrete code edits to scripts, schemas, or delegate behavior.
- Stop if `DelegationPlan` output can trigger execution without explicit approval.
- Stop if role selection broadens project or base permissions beyond 0015 rules.
- Stop if preview always selects a specialist instead of allowing a no-specialist result.

## Validation

- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate-plans.py --root . --format json`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/ownership-lock.py write`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/generate-codemaps.py --write`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify-skeleton.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/quality-gate.py --root . --tier stable --skip-tests --format json`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/quality-gate.py --root . --tier all --skip-tests --format json`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/agent-flow.py closeout --goal "0016-0018 specialist flow implementation" --changed-path scripts/agent-flow.py --changed-path tests/test_agent_flow.py --changed-path docs/AGENT_REGISTRY.md --changed-path docs/RUNTIME_EVENT_SCHEMA.md --changed-path plans/done/0016-specialist-proposal-add.md --changed-path plans/done/0017-orchestration-preview.md --changed-path plans/done/0018-execution-loop.md --changed-path plans/INDEX.md --format json`

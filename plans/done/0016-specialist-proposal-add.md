# 0016 Specialist Proposal Add

## Summary

Define and implement the project-specific specialist proposal and add flow. This slice fixed the proposal schema and lifecycle, then implemented the CLI surface that creates, reviews, approves, rejects, and optionally applies proposals to the project overlay.

0016 is intentionally more detailed than 0017 and 0018 because it defines the input contract that the later orchestration preview consumes.

Status: done. Implemented through `scripts/agent-flow.py specialist propose/review/approve/reject`.

## Assumptions

- 0015 specialist overlay loader exists and enforces additive-first, privilege-safe overlays.
- Project overlays may add new project specialists and may narrow base specialist `write_policy` or `default_scope`; broadening either remains rejected.
- A specialist proposal is a review artifact first. It is not the same thing as writing `config/agent-team-overrides.yaml`.
- 0017 orchestration-preview consumes the proposal schema defined here.
- Specialist creation is on-demand only; no project specialist is created merely because a project starts.
- `docs/_meta/SPECIALIST_AGENT_USAGE_BEST_PRACTICES.md` defines trigger and anti-trigger criteria for proposal eligibility.
- Existing dirty/generated/local files remain unrelated to this slice.

## Out of Scope

- No implementation files under `scripts/`, `schemas/`, generated `.codex/`, or generated `.claude/` are changed.
- No generated agent export is implemented.
- Overlay writes occur only through explicit `specialist approve --apply-overlay`.
- No router, orchestration preview, delegate behavior, execution loop, or auto-spawn behavior is implemented.
- No base specialist permission broadening is allowed or planned.

## Implementation Steps

This slice defines contracts and implements the review boundary.

1. Define the `SpecialistProposal` contract:
   - `proposal_id`: stable identifier for the proposal artifact.
   - `role`: proposed specialist role name.
   - `mission`: one-sentence responsibility statement.
   - `write_policy`: proposed write boundary, subject to 0015 privilege checks.
   - `default_scope`: proposed path or domain scope.
   - `recommended_checks`: validation checks the specialist should normally request.
   - `status`: one of `draft`, `approved`, or `rejected`.
   - `source_registry`: `project` for new project specialists, or `base` when proposing a narrowing override for an existing base specialist.
   - `created_by`: creator identity or tool surface that produced the proposal.
   - `created_at`: local timestamp in ISO-like form.
   - `reason`: concise evidence or blocker that motivated the specialist.
   - `review_notes`: human review notes, including rejection or approval rationale.
2. Define the review lifecycle as `propose -> review -> approve|reject -> approved proposal may become overlay input`.
3. Preserve the 0015 additive-only rule: new project specialists are allowed, base specialist narrowing is allowed, and base broadening of `write_policy` or `default_scope` is rejected.
4. Require proposal `reason` to cite at least one concrete trigger from the best-practices report, such as context isolation, independent parallel work, second opinion, permission boundary, repeated pattern, sequential precondition, or long-running/high-volume work.
5. Reject or keep draft any proposal justified only by anti-triggers, such as quick targeted work, tight back-and-forth, duplicated base roles, or specialist sprawl.
6. Define the handoff to 0017: draft or approved `SpecialistProposal` records become candidate-role inputs for orchestration preview scoring.
7. Keep overlay mutation as a future implementation decision that requires a separate implementation exception.

## Definition of Done

- This plan exists in `plans/done/`.
- `plans/INDEX.md` lists 0016 as done.
- The `SpecialistProposal` schema fields are explicitly named.
- 0017 references this schema as its input contract.
- `agent-flow specialist propose/review/approve/reject` implements the on-demand review flow.
- Validation commands complete or any blocker is recorded.

## Rollback Plan

- Revert the 0016 implementation changes and remove `plans/done/0016-specialist-proposal-add.md` plus its INDEX row if the implementation is withdrawn.
- Add a corrective decision entry rather than editing previous decisions.
- Regenerate ownership lock and codemaps after rollback if file membership changes.

## Stop Conditions

- Stop if the plan starts describing concrete code-edit steps for scripts, schemas, CLI behavior, routing behavior, or delegate behavior.
- Stop if the proposal flow would broaden base specialist `write_policy` or `default_scope`.
- Stop if the flow implies automatic overlay writes without explicit review.
- Stop if the flow implies a new router, new execution loop, or auto-spawn behavior.
- Stop if the flow creates specialists by default at project start rather than on-demand from concrete triggers.
- Stop if 0017 cannot consume the schema fields without inventing additional required fields.

## Validation

- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate-plans.py --root . --format json`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/ownership-lock.py write`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/generate-codemaps.py --write`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify-skeleton.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/quality-gate.py --root . --tier stable --skip-tests --format json`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/quality-gate.py --root . --tier all --skip-tests --format json`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/agent-flow.py closeout --goal "0016-0018 specialist flow implementation" --changed-path scripts/agent-flow.py --changed-path tests/test_agent_flow.py --changed-path docs/AGENT_REGISTRY.md --changed-path docs/RUNTIME_EVENT_SCHEMA.md --changed-path plans/done/0016-specialist-proposal-add.md --changed-path plans/done/0017-orchestration-preview.md --changed-path plans/done/0018-execution-loop.md --changed-path plans/INDEX.md --format json`

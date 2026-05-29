# 0033-plan-id-evidence-trace

## Summary
Add an optional explicit `plan_id` trace from `agent-flow closeout` through `task-closeout.py` into `runtime/completion-evidence.jsonl`.

## Assumptions
- The user approved this focused implementation after Codex-Claude design discussion.
- `plan_id` is an ID such as `0033-plan-id-evidence-trace`, not a file path.
- A provided `plan_id` must resolve to `plans/active/<id>.md` or `plans/done/<id>.md`.

## Out of Scope
- Automatic goal-to-plan matching.
- Storing `plan_path` in completion evidence.
- Query/search commands for plan evidence.
- JSONL migration of historical records.
- Accepting `plans/failed/<id>.md` as a valid completion evidence target.

## Implementation Steps
- Add optional `plan_id` support and validation to `scripts/completion-evidence.py`.
- Pass optional `--plan-id` through `scripts/task-closeout.py`.
- Pass optional `--plan-id` through `scripts/agent-flow.py closeout`.
- Add focused unittest coverage for omitted, active, done, missing, failed-only, and passthrough cases.
- Document the optional completion evidence field and closeout usage.

## Definition of Done
- `--plan-id` omitted preserves existing behavior.
- `--plan-id` pointing to active or done plan records `plan_id`.
- `--plan-id` pointing to no active/done plan fails before append.
- `plans/failed/<id>.md` alone is not accepted.
- Focused tests and skeleton verification pass.

## Rollback Plan
- Revert `completion-evidence.py`, `task-closeout.py`, `agent-flow.py`, focused tests, and docs for this slice.

## Stop Conditions
- Stop if implementation would infer plan IDs from goal text.
- Stop if implementation would add a query engine or database.
- Stop if implementation would make `plan_id` required for all completion evidence.

## Validation
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_validation.CompletionEvidencePlanIdTests -v`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_agent_flow.AgentFlowTests.test_closeout_passes_plan_id_to_task_closeout -v`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate-plans.py --allow-legacy-done --format json`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify-skeleton.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/agent-flow.py closeout --goal "plan_id evidence trace" --changed-path scripts/completion-evidence.py --changed-path scripts/task-closeout.py --changed-path scripts/agent-flow.py --changed-path tests/test_validation.py --changed-path tests/test_agent_flow.py --changed-path docs/RUNTIME_EVENT_SCHEMA.md --changed-path scripts/README.md --changed-path plans/active/0033-plan-id-evidence-trace.md --plan-id 0033-plan-id-evidence-trace --format json`

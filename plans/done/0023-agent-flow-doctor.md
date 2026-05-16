# 0023 Agent Flow Doctor

## Summary
Add `agent-flow doctor` as a single read-only diagnostic UX wrapper for the checks operators currently run separately: `skeleton-doctor`, `verify-skeleton`, `ownership-lock check`, `resume-readiness --strict`, and tier-aware `quality-gate`.

## Assumptions
- This is an operator UX improvement, not a new validation engine.
- Existing diagnostic scripts remain the source of truth.
- The command must be read-only and must not write runtime evidence, codemaps, lock files, or closeout records.
- Fast daily use should avoid recursive or long-running tests by default.

## Out of Scope
- Replacing `quality-gate.py`, `verify-skeleton.py`, `resume-readiness.py`, `ownership-lock.py`, or `skeleton-doctor.py`.
- Adding automatic repair, cleanup, lock writing, codemap generation, closeout, commit, or push.
- Changing `agent-flow start` routing.
- Stable promotion of v2 specialist execution.

## Implementation Steps
- Add a `doctor` subcommand to `scripts/agent-flow.py`.
- Run all component checks and aggregate their status without short-circuiting.
- Support `--tier stable|all`, `--with-tests`, `--format text|json`, and `--timeout`.
- Add focused regression tests in `tests/test_agent_flow.py`.
- Document the command in `scripts/README.md`.

## Definition of Done
- `python3 scripts/agent-flow.py doctor --format json` returns a structured summary and per-command results.
- A failing component check makes doctor exit non-zero while preserving the full report.
- Default quality-gate invocation uses `--skip-tests`; `--with-tests` omits `--skip-tests`.
- Existing diagnostic scripts can still be run directly.

## Rollback Plan
- Revert `scripts/agent-flow.py`, `tests/test_agent_flow.py`, `scripts/README.md`, `plans/INDEX.md`, and this plan file.

## Stop Conditions
- Stop if implementation starts mutating files or adding auto-repair behavior.
- Stop if the wrapper hides component stdout/stderr needed for source recovery.
- Stop if tests require changing existing diagnostic script semantics.

## Validation
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_agent_flow -v`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/agent-flow.py doctor --format json`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify-skeleton.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/quality-gate.py --root . --tier stable --skip-tests --format json`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/agent-flow.py closeout --goal "0023 agent-flow doctor" --changed-path scripts/agent-flow.py --changed-path tests/test_agent_flow.py --changed-path scripts/README.md --changed-path plans/INDEX.md --changed-path plans/done/0023-agent-flow-doctor.md --format json`

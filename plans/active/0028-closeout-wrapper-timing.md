# 0028 Closeout Wrapper Timing

## Summary

`agent-flow closeout` is slower than expected because the wrapper performs
front-loaded verification before `task-closeout.py` receives its profile. This
slice measures that cost first, then applies exactly one repair based on the
measurement.

The work is split into two commit boundaries:

- Commit A: timing instrumentation only, with no behavior change.
- Commit B: one measured repair only.

## Assumptions

- `task-closeout.py` already has profiles; the likely gap is wrapper wiring, not
  missing profile names.
- `task-closeout.py --prevalidated-check` prevents duplicate internal checks, so
  the problem is front-loaded check selection rather than repeated execution.
- Timing data is operational evidence and belongs in an append-only runtime
  ledger.
- ENKI validation for this slice must remain read-only.

## Out of Scope

- New closeout profiles unless measurement proves they are necessary in a later
  slice.
- Lowering final validation expectations for release-grade closeout.
- Changing `task-closeout.py` profile semantics unless the timing data points
  there directly.
- Running write operations against ENKI.
- Introducing a generic performance framework.

## Implementation Steps

1. Add append-only closeout timing instrumentation to
   `scripts/agent-flow.py`.
2. Record one row per closeout phase in `runtime/closeout-timings.jsonl` with at
   least `schema_version`, `ts`, `goal`, `profile`, `phase`, `duration_ms`, and
   `exit_status`.
3. Add focused tests proving timing records are written on both failed and
   successful closeout paths without changing command order.
4. Commit A with instrumentation only.
5. Measure `agent-flow closeout` at least 5 times each for `profile=auto` and
   `profile=docs`; record P50 values and phase comparison evidence.
6. Apply one repair using the decision rule below.
7. Commit B with the single repair and its focused tests.

## Repair Decision Rule

- If the slowest measured phase is at least 1.5x the second slowest phase, repair
  that single phase only.
- Otherwise, repair wrapper wiring so `agent-flow closeout --profile` controls
  the front-loaded verify and quality-gate stage instead of always running the
  strict full path.
- If two unrelated phases both need repairs, stop and open a follow-up plan
  instead of combining them here.

## Definition of Done

- Commit A contains instrumentation only.
- `runtime/closeout-timings.jsonl` receives append-only records with the required
  fields.
- At least 5 `auto` and 5 `docs` timing samples are captured.
- The before/after evidence names the P50 for each measured phase.
- Commit B contains exactly one repair selected by the decision rule.
- Focused tests, `verify-skeleton`, quality gates, doctor, and resume-readiness
  pass or any residual warning is explained.

## Rollback Plan

- Revert Commit B to remove the repair while keeping timing evidence available.
- Revert Commit A to remove timing instrumentation and the runtime timing ledger
  if instrumentation itself causes problems.

## Stop Conditions

- Stop if implementation skips timing and jumps directly to a faster profile.
- Stop if a change weakens final closeout validation without an explicit
  release-grade alternative.
- Stop if more than one unrelated optimization is needed.
- Stop if measurement would write to ENKI or any external target.
- Stop if generated/local files are staged with this slice.

## Validation

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_agent_flow -v`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify-skeleton.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/quality-gate.py --root . --tier stable --skip-tests --format json`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/quality-gate.py --root . --tier all --skip-tests --format json`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/agent-flow.py doctor --format json`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/resume-readiness.py --strict --format json`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/agent-flow.py closeout --goal "0028 closeout wrapper timing" --changed-path scripts/agent-flow.py --changed-path tests/test_agent_flow.py --changed-path plans/done/0028-closeout-wrapper-timing.md --changed-path plans/INDEX.md --format json`

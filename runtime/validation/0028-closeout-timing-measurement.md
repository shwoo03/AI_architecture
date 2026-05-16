# 0028 Closeout Timing Measurement

## Context

Commit A added append-only timing records to `runtime/closeout-timings.jsonl`.
Commit B repairs only one behavior: the `agent-flow closeout` wrapper now lets
non-`all` profiles delegate checks to `task-closeout.py` instead of always
running the strict front-loaded verify plus quality-gate path.

## Baseline Attempts

The first clean baseline run showed the full front path cost:

- `verify`: 59105 ms
- `quality-gate`: 60864 ms
- `task-closeout`: 219 ms

Subsequent baseline attempts exposed the same operational issue from another
angle: after a closeout appends runtime ledgers, the next front-loaded verify can
stop before task-closeout unless supporting runtime caches are refreshed.

Baseline attempts still produced the required five `auto` and five `docs`
measurements:

| profile | phase | samples | P50 ms | notes |
| --- | --- | ---: | ---: | --- |
| auto | verify | 5 | 33433 | mixed successful/failed attempts |
| auto | quality-gate | 1 | 60864 | only reached on the clean full run |
| auto | task-closeout | 1 | 219 | only reached on the clean full run |
| docs | verify | 5 | 33489 | all stopped in the wrapper front phase |

## Repair Decision

The clean full run had `verify` and `quality-gate` within 1.5x of each other
(59105 ms vs 60864 ms). Therefore the plan's decision rule selected wrapper
profile wiring instead of optimizing one individual phase.

## Repaired Measurements

After the repair:

| profile | phase | samples | P50 ms | recorded |
| --- | --- | ---: | ---: | --- |
| auto | task-closeout | 5 | 36498 | false; scripts profile checks ran inside task-closeout |
| docs | task-closeout | 5 | 1591 | true |

The `docs` profile now avoids the front-loaded strict verify plus quality-gate
path and records closeout evidence in roughly 1.6 seconds for documentation-only
changes. `auto` with script/test changed paths still runs the heavier scripts
profile checks, but they now run inside the profile-aware closeout layer instead
of the unconditional wrapper front gate.

## Evidence Files

- Timing ledger: `runtime/closeout-timings.jsonl`
- Focused output captures: `/tmp/0028-closeout-*.json` and
  `/tmp/0028-repaired-*.json` during implementation

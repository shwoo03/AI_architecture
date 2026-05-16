# 0024 Project Adoption Intake

## Summary

`agent-flow adopt` provides a read-only intake command for applying the AI_architecture operating OS to older or external projects. It is not a one-command adoption finisher. It is the entry diagnostic for a multi-slice adoption workflow, reporting the target's current state, risk signals, and the next human decision before any apply slice starts.

0024 does not write to the target, does not write adoption ledgers in the skeleton or target, and does not classify ownership candidates automatically. Closeout evidence records this slice's implementation.

## Assumptions

- Existing upgrade and ownership tools already provide the underlying read-only analysis.
- 0024 is a v1 operational UX improvement and does not require a v2 specialist freeze exception.
- `agent-flow adopt` may read target files, run `git status`, and invoke dry-run internal tools, but it must not mutate target files.
- 0025 will handle safe apply separately and must rerun dry-run immediately before applying. 0024 output is advisory, not a source of truth.

## Out of Scope

- `--apply-safe`, `--verify`, `--rollback`, or `--include-risky` support.
- Target file writes.
- Skeleton-side or target-side adoption ledger writes.
- Candidate ownership classification decisions.
- `manual_merge` conflict resolution.
- `PROJECT_PROFILE.md` auto-fill.
- License compatibility decisions beyond a warning signal.
- Rollback design, which remains deferred until real apply evidence exists.

## Implementation Steps

1. Add `plans/active/0024-project-adoption-intake.md` and index the plan.
2. Add `agent-flow adopt --target <path> --format text|json` as the default dry-run assessment.
3. Add `agent-flow adopt --target <path> --status --format text|json` as the lightweight status assessment.
4. Reuse existing tools instead of reimplementing adoption logic:
   - `git -C <target> status --short`
   - target `LICENSE*` scan
   - target `docs/PROJECT_PROFILE.md` state scan
   - current skeleton `git rev-parse --short HEAD`
   - target skeleton revision hints from `runtime/activity-log.jsonl` or `runtime/install-state.jsonl`
   - `upgrade-from-skeleton.py --target <target> --brief --profile stable --format json`
   - `ownership-initialize.py --target <target> --format json`
5. Keep `--status` lightweight and skip the full upgrade/ownership dry-run tools.
6. Update documentation for the read-only adoption intake surface.
7. Add focused tests for status, dry-run synthesis, stop recommendations, license warnings, dirty targets, and prohibited flags.

## Output Contract

`agent-flow adopt --target ... --format json` emits at least:

```json
{
  "ok": true,
  "target": "/path/to/legacy-project",
  "mode": "dry_run",
  "target_exists": true,
  "target_git_clean": true,
  "skeleton_revision_in_target": null,
  "skeleton_revision_current": "69c01d1",
  "project_profile_state": "missing",
  "license_signal": "compatible",
  "upgrade_brief": {
    "safe_missing": 0,
    "manual_merge": 0,
    "risky_changed": 0
  },
  "ownership": {
    "status": "draft",
    "analyzed_paths": 0,
    "candidate_paths": 0,
    "stop_threshold": 20,
    "exceeds_threshold": false
  },
  "recommendation": "apply_safe_ready",
  "stop_reasons": [],
  "next_action": "..."
}
```

Recommendation rules:

- `stop`: target missing, dirty target git tree, candidate count above threshold, license warning, or ownership analysis unavailable.
- `needs_review`: no stop reason, but profile/license/ownership/manual/risky signals need a person to review.
- `apply_safe_ready`: clean target, candidate count under threshold, safe missing files exist, and no stop reason.

## Definition of Done

- `agent-flow adopt` exposes only `--status` and default dry-run modes.
- JSON output follows the output contract.
- The command does not write target files or adoption ledgers.
- Prohibited options fail at argparse level.
- ENKI dry-run produces a successful read-only assessment with `recommendation=stop` when candidate count exceeds the threshold.
- A clean fixture target can produce `apply_safe_ready` or `needs_review` with explicit next action.
- Focused tests and standard gates pass.

## Rollback Plan

- Revert the `agent-flow adopt` code, focused tests, docs, and this plan/index entry.
- No target-project rollback is needed because 0024 is read-only and writes no adoption ledger.

## Stop Conditions

- Stop if implementation introduces `--apply-safe`, `--verify`, `--rollback`, or `--include-risky`.
- Stop if the command writes to the target or to skeleton/target adoption ledgers.
- Stop if candidate classification, manual merge resolution, project profile filling, or license compatibility judgment is automated.
- Stop if `upgrade-from-skeleton.py` is invoked with `--apply` or `--include-risky`.
- Stop if rollback behavior is added before real apply evidence exists.

## Validation

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_agent_flow -v`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/agent-flow.py adopt --target <ENKI_WIKI_PATH> --format json`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate-plans.py --root . --format json`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/ownership-lock.py write`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/generate-codemaps.py --write`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify-skeleton.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/quality-gate.py --root . --tier stable --skip-tests --format json`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/quality-gate.py --root . --tier all --skip-tests --format json`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/agent-flow.py closeout --goal "0024 project adoption intake" --changed-path scripts/agent-flow.py --changed-path tests/test_agent_flow.py --changed-path scripts/README.md --changed-path docs/SKELETON_UPGRADE.md --changed-path plans/done/0024-project-adoption-intake.md --changed-path plans/INDEX.md --format json`

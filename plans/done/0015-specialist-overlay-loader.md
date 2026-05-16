# 0015-specialist-overlay-loader

## Summary

Implement an optional project-specific specialist overlay loader so projects can add or narrow specialist roles without editing the skeleton base registry or widening permissions.

## Status

Done. The optional project-specific specialist overlay loader is implemented with additive-only merge rules, `role_source` provenance, tests, documentation, and closeout evidence. 0016-0018 remain frozen until external usage evidence appears.

## Implementation Prep

Preparation artifact: `runtime/validation/0015-specialist-overlay-loader-prep.md`.

The first implementation should keep loader behavior inside `scripts/agent-brief.py` because `scripts/incubating/agent-flow-delegate.py` already reuses AgentBrief through subprocess. A separate helper module can be extracted later if another caller needs direct Python imports. This keeps the 0015 write set narrow and avoids changing generated agent surfaces.

Expected write set for implementation:

- `scripts/agent-brief.py`
- `scripts/incubating/agent-flow-delegate.py`
- `tests/test_validation.py`
- `docs/AGENT_REGISTRY.md`
- `docs/RUNTIME_EVENT_SCHEMA.md`
- generated operational files: ownership lock, codemaps, closeout/runtime state

Core tests to add before closing 0015:

- overlay absent emits `role_source: base`
- overlay-only specialist emits `role_source: project`
- base specialist narrowing of `write_policy` and `default_scope` succeeds
- base specialist `write_policy` broadening fails
- base specialist `default_scope` broadening fails
- delegate handoff includes `role_source`

## Assumptions

- Plan 0014 completed the audit in `docs/_meta/SPECIALIST_OVERLAY_AUDIT.md`.
- Base specialists remain defined in `config/agent-team.yaml`.
- The project overlay file is optional and defaults to `config/agent-team-overrides.yaml`.
- The loader supports only the specialist registry path; generated `.codex/agents/` and `.claude/agents/` remain unchanged.

## Out of Scope

- `agent-flow specialist add` or any proposal/add CLI.
- Orchestration preview, automatic role recommendation, subagent spawn, or execution-loop changes.
- Promoting `agent-flow-delegate.py` to stable public surface.
- Updating generated agent exports from overlay specialists.
- Touching ENKI target files.

## Implementation Steps

- Extract specialist registry loading from `scripts/agent-brief.py` into a reusable helper or module that loads the base registry and optional overlay.
- Support `config/agent-team-overrides.yaml` with the same specialist fields currently used by `config/agent-team.yaml`: `mission`, `write_policy`, `default_scope`, and `recommended_checks`.
- Merge rules:
  - New overlay-only specialists are accepted and marked `role_source: project`.
  - Existing base specialists may narrow `write_policy` and `default_scope`.
  - Existing base specialists may not broaden `write_policy` or `default_scope`.
  - Base specialists without overlay changes are marked `role_source: base`.
- Preserve current `agent-brief.py` behavior for unknown roles, invalid write policies, requested write-policy broadening, parent-policy broadening, scope normalization, and recommended check normalization.
- Add `role_source` to emitted AgentBrief JSON and delegate handoff payload.
- Register the overlay file in ownership/config checks as project-owned or explicitly allowed only if validation requires it; do not make the overlay file mandatory.
- Document the overlay behavior in `docs/AGENT_REGISTRY.md` and `docs/RUNTIME_EVENT_SCHEMA.md` without changing stable public command boundaries.

## Definition of Done

- Existing briefs work unchanged when `config/agent-team-overrides.yaml` is absent.
- An overlay-only specialist can produce a brief with `role_source: project`.
- A base specialist narrowed by overlay can produce a brief with the narrowed policy/scope.
- Attempts to broaden base specialist `write_policy` or `default_scope` fail loudly.
- Delegate handoff reports the role source from the brief.
- Stable and all-tier quality gates pass.

## Rollback Plan

- Remove the overlay loader/helper, tests, and documentation updates.
- Remove `role_source` additions if no longer emitted.
- Leave existing runtime ledgers append-only and regenerate ownership lock/codemaps.

## Stop Conditions

- Stop if implementation requires changing generated `.codex/agents/` or `.claude/agents/`.
- Stop if broadening semantics are ambiguous for any field beyond `write_policy` and `default_scope`.
- Stop if the overlay loader needs a dependency install or external YAML package.
- Stop if `agent-flow specialist add`, routing preview, or execution-loop behavior becomes necessary.

## Validation

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_validation tests.test_agent_flow -v
PYTHONDONTWRITEBYTECODE=1 python3 scripts/agent-brief.py --role docs-sync-auditor --goal "overlay absent smoke" --format json
PYTHONDONTWRITEBYTECODE=1 python3 scripts/incubating/agent-flow-delegate.py --role docs-sync-auditor --goal "overlay absent delegate smoke" --format json
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate-plans.py --root . --format json
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify-skeleton.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/quality-gate.py --root . --tier stable --skip-tests --format json
PYTHONDONTWRITEBYTECODE=1 python3 scripts/quality-gate.py --root . --tier all --skip-tests --format json
PYTHONDONTWRITEBYTECODE=1 python3 scripts/agent-flow.py closeout \
  --goal "0015 specialist overlay loader" \
  --changed-path scripts/agent-brief.py \
  --changed-path scripts/incubating/agent-flow-delegate.py \
  --changed-path tests/test_validation.py \
  --changed-path docs/AGENT_REGISTRY.md \
  --changed-path docs/RUNTIME_EVENT_SCHEMA.md \
  --format json
```

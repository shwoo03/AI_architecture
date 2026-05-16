# 0014-specialist-overlay-audit

## Summary

Audit the current specialist registry and delegation surfaces so a future 0015 loader can support project-specific specialist overlays without privilege escalation or a parallel orchestration stack.

## Status

Done. The read-only audit artifact is `docs/_meta/SPECIALIST_OVERLAY_AUDIT.md`, and follow-up implementation scope is captured in `plans/active/0015-specialist-overlay-loader.md`.

## Assumptions

- The 2026-05-16 freeze exception allows only this read-only audit and a future additive-only overlay loader.
- Existing active plans 0007 and 0013 remain active and are not moved by this slice.
- `config/agent-team.yaml` remains the base specialist registry for this audit.
- Project-specific specialist definitions, if implemented later, must be optional and must not be required at project bootstrap.

## Out of Scope

- Editing `config/agent-team.yaml`, `config/roles.yaml`, `agents/*.md`, or generated agent files.
- Implementing `config/agent-team-overrides.yaml` loading.
- Adding `agent-flow specialist add`, proposal/add commands, routing preview, automatic spawn, or execution-loop behavior.
- Promoting incubating delegate behavior to the stable public surface.
- Touching ENKI target files.

## Implementation Steps

- Inspect base registry and role surfaces: `config/agent-team.yaml`, `config/roles.yaml`, `docs/AGENT_REGISTRY.md`, and `agents/*.md`.
- Inspect brief generation: `scripts/agent-brief.py` registry loading, write-policy broadening checks, scope intersection, recommended checks, and brief JSON fields.
- Inspect delegate handoff: `scripts/incubating/agent-flow-delegate.py` subprocess reuse of `scripts/agent-brief.py`, workflow-aware completion command generation, and ledger handoff assumptions.
- Inspect generated surfaces: `scripts/convert.py`, `.codex/agents/`, and `.claude/agents/` to identify whether future project overlays need generated exports or should remain runtime-only.
- Write `docs/_meta/SPECIALIST_OVERLAY_AUDIT.md` with current facts, identified extension points, loader safety constraints, and explicit future-hook notes for 0017/0018.
- Record that 0017 should extend existing goal-to-candidate scoring patterns instead of building a parallel router.
- Record that 0018 should extend the existing incubating delegate path instead of creating a second execution loop.

## Definition of Done

- `docs/_meta/SPECIALIST_OVERLAY_AUDIT.md` exists and is fact-based.
- Registry, code, schema, generated agent surfaces, and ENKI target files are unchanged except for normal closeout artifacts.
- The audit identifies exact 0015 loader touchpoints and rejects write-policy/default-scope broadening.
- The audit states that future briefs must include `role_source: base|project` once overlays exist.
- 0016-0018 remain frozen until external usage signals justify reopening.

## Rollback Plan

- Remove `docs/_meta/SPECIALIST_OVERLAY_AUDIT.md`, this plan, and the 0014 index row.
- Preserve prior decisions and ledgers unless the rollback is part of a reviewed follow-up.
- Regenerate codemaps and ownership lock if the audit artifact had already been included.

## Stop Conditions

- Stop if the audit requires changing registry, code, schema, or generated agent surfaces.
- Stop if a proposed loader would allow project overlays to broaden base specialist `write_policy` or `default_scope`.
- Stop if the audit starts designing 0016-0018 behavior beyond identifying reuse hooks.
- Stop if ENKI target writes become necessary.

## Validation

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate-plans.py --root . --format json
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify-skeleton.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/quality-gate.py --root . --tier stable --skip-tests --format json
PYTHONDONTWRITEBYTECODE=1 python3 scripts/quality-gate.py --root . --tier all --skip-tests --format json
PYTHONDONTWRITEBYTECODE=1 python3 scripts/agent-flow.py closeout \
  --goal "0014 specialist overlay audit" \
  --changed-path plans/active/0014-specialist-overlay-audit.md \
  --changed-path docs/_meta/SPECIALIST_OVERLAY_AUDIT.md \
  --changed-path plans/INDEX.md \
  --format json
```

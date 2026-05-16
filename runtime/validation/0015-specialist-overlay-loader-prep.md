# 0015 Specialist Overlay Loader Implementation Prep

## Purpose

Prepare the implementation of plan 0015 without changing runtime behavior yet. This prep fixes the intended code path, test matrix, and security boundary for the optional project-specific specialist overlay loader.

## Current Facts

- `scripts/agent-brief.py` currently owns specialist registry loading, policy reduction, scope normalization, and AgentBrief JSON emission.
- `scripts/incubating/agent-flow-delegate.py` shells out to `scripts/agent-brief.py --write --format json` and should continue to treat the brief payload as source of truth.
- `config/agent-team.yaml` is the base specialist registry. Generated agent files under `.codex/agents/` and `.claude/agents/` come from `agents/` through `scripts/convert.py`; they are not part of 0015.
- Existing tests for AgentBrief and delegate behavior live in `tests/test_validation.py` and `tests/test_operational_tools.py`.

## Implementation Shape

Keep the first 0015 implementation narrow:

- Extend `scripts/agent-brief.py` registry loading in place.
- Read optional `config/agent-team-overrides.yaml` when present.
- Preserve current behavior when the overlay file is absent.
- Add a `role_source` field to emitted AgentBrief JSON.
- Add `role_source` to `scripts/incubating/agent-flow-delegate.py` handoff JSON by copying the value from the brief.
- Do not create `agent-flow specialist add`, routing preview, generated exports, subagent spawning, or a second execution loop.

If the loader grows enough to need sharing outside AgentBrief and delegate, extract it later. For this slice, the delegate already reuses AgentBrief through subprocess, so a new module is optional rather than required.

## Merge Semantics

Overlay file:

```yaml
specialists:
  example-specialist:
    mission: "..."
    write_policy: read_only
    default_scope: ["docs/"]
    recommended_checks: ["python scripts/verify-skeleton.py"]
```

Rules:

- Overlay-only specialist is allowed and emits `role_source: project`.
- Existing base specialist remains `role_source: base`.
- Existing base specialist may narrow `write_policy`.
- Existing base specialist may narrow `default_scope`.
- Existing base specialist must not broaden `write_policy`.
- Existing base specialist must not broaden `default_scope`.
- Narrowed effective policy/scope continue to appear in existing `write_policy`, `read_scope`, `write_scope`, and `policy_inheritance` fields.

Scope narrowing uses the existing `is_same_or_under(child, parent)` semantics:

- Base `.` allows any narrower repo path.
- Overlay `tests/` is allowed under base `scripts/`, `tests/` only when it is under one of the base items.
- Overlay `.` is rejected when the base scope is narrower than `.`.

## Test Matrix

Add or update tests in `tests/test_validation.py`:

- Overlay absent: existing base role still works and emits `role_source: base`.
- Overlay-only specialist: temp root with only project overlay accepts the role and emits `role_source: project`.
- Base narrowing: overlay narrows `write_policy` and `default_scope`; brief succeeds with narrowed policy/scope.
- Write-policy broadening: overlay attempts to widen a base `read_only` specialist to `manual_work_required`; brief fails loudly.
- Scope broadening: overlay attempts to widen a base narrow scope to `.` or parent directory; brief fails loudly.
- Delegate handoff: returned JSON includes `role_source` copied from the written brief.

Smoke commands after implementation:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_validation tests.test_operational_tools -v
PYTHONDONTWRITEBYTECODE=1 python3 scripts/agent-brief.py --role docs-sync-auditor --goal "overlay absent smoke" --format json
PYTHONDONTWRITEBYTECODE=1 python3 scripts/incubating/agent-flow-delegate.py --role docs-sync-auditor --goal "overlay absent delegate smoke" --format json
```

## Documentation Targets

- `docs/AGENT_REGISTRY.md`: document optional `config/agent-team-overrides.yaml`, additive-only behavior, and no public command expansion.
- `docs/RUNTIME_EVENT_SCHEMA.md`: document `role_source` in AgentBrief/delegate handoff context.

## Security Boundary

Sensitive assets are specialist permissions, write scopes, generated agent surfaces, and runtime ledgers. Safe default for 0015:

- read config only,
- reject broadening,
- fail loud on invalid configured policy values,
- do not execute recommended checks while loading,
- do not write target project files,
- do not mutate generated `.codex/agents/` or `.claude/agents/`.

# 0008-ownership-aware-upgrade-v1

## Summary

Ownership-aware upgrade v1 defines how AI_architecture updates are applied to existing projects without overwriting project-owned work. Slice 1 is spec-only: add the ownership model document and the default ownership map for the skeleton. Classifier code, lock generation, verify integration, and ENKI dry-run are later slices.

## Assumptions

- `0007-role-registry-audit` remains active/deferred and untouched.
- This slice establishes the source-of-truth model for later implementation.
- No classifier code or migration behavior is implemented in Slice 1.
- ENKI migration resumes only after ownership classifier, self-classification, and upgrade integration slices are complete.

## Out of Scope

- `scripts/lib_ownership.py` or classifier implementation.
- `scripts/upgrade-from-skeleton.py` changes.
- `scripts/verify-skeleton.py` ownership checks.
- `runtime/ownership-classification.lock.json` creation.
- ENKI_WIKI migration or dry-run.

## Implementation Steps

- Add `docs/OWNERSHIP_MODEL.md` with the v1 ownership model, classifier semantics, lock semantics, initialization policy, and workflow cost.
- Add `config/ownership.yaml` with `schema_version: ai-architecture.ownership.v1`, default skip/protected/system_locked/rules blocks, minimal `project_overrides`, and unknown policy.
- Add this plan to `plans/INDEX.md` as active.
- Validate Markdown/YAML sanity and existing skeleton gates.

## Definition of Done

- Ownership model document exists and states `layout is advice, ownership is law`.
- Ownership YAML exists and includes schema version, skip patterns, protected paths, system locked paths, normal rules, project overrides, and unknown policy.
- Slice boundaries are explicit: Slice 1 does not implement code or create lock files.
- Existing skeleton validation still passes.

## Rollback Plan

- Remove `docs/OWNERSHIP_MODEL.md`, `config/ownership.yaml`, and the 0008 plan/index entry.
- No runtime ledgers, classifier code, or target projects are affected by this slice.

## Stop Conditions

- If writing the default ownership map requires changing upgrade or verification code, stop and move that work to Slice 2 or Slice 3.
- If ownership categories conflict with existing feature-tier semantics, stop and document the conflict before implementation.
- If validation fails for reasons unrelated to the new spec files, stop and report the pre-existing blocker separately.

## Validation

```bash
python3 scripts/verify-skeleton.py
python3 scripts/quality-gate.py --root . --tier stable --skip-tests --format json
python3 scripts/agent-flow.py closeout \
  --goal "Ownership-aware upgrade v1 Slice 1" \
  --changed-path plans/active/0008-ownership-aware-upgrade-v1.md \
  --changed-path docs/OWNERSHIP_MODEL.md \
  --changed-path config/ownership.yaml \
  --format json
python3 - <<'PY'
from pathlib import Path
import yaml
for path in [Path('config/ownership.yaml')]:
    payload = yaml.safe_load(path.read_text())
    assert payload['schema_version'] == 'ai-architecture.ownership.v1'
assert Path('docs/OWNERSHIP_MODEL.md').read_text().startswith('# Ownership Model')
PY
```

# 0009-ownership-classifier-synthetic-tests

## Summary

Ownership-aware upgrade v1 Slice 2 implements the standalone classifier library and synthetic fixture tests. This slice turns the Slice 1 model into executable classification semantics without wiring it into `upgrade-from-skeleton.py` or `verify-skeleton.py`.

## Assumptions

- Slice 1 artifacts exist: `docs/OWNERSHIP_MODEL.md` and `config/ownership.yaml`.
- `0007-role-registry-audit` remains active/deferred and untouched.
- `0008-ownership-aware-upgrade-v1` remains the Slice 1 spec anchor.
- This slice is classifier correctness only; skeleton self-classification and lock generation belong to later slices.

## Out of Scope

- `scripts/upgrade-from-skeleton.py` integration.
- `scripts/verify-skeleton.py` ownership checks.
- `runtime/ownership-classification.lock.json` creation.
- ENKI_WIKI dry-run or migration.
- Project-specific ownership overrides beyond synthetic fixtures.

## Implementation Steps

- Add `scripts/lib_ownership.py` with a standard-library classifier for ownership config dictionaries and the v1 YAML subset.
- Preserve the v1 model: skip patterns, protected short-circuit, system_locked project-override guard, order-based last-match normal rules, unknown policy, and content-identical unchanged short-circuit.
- Add synthetic fixture tests covering guard precedence, last-match behavior, project override behavior, unknown policy, generated/cache skips, content-identical short-circuit, lock drift comparison, and current config parsing.
- Add `scripts/lib_ownership.py` to the default ownership map as a system-owned locked core library.

## Definition of Done

- Synthetic tests prove classifier correctness independently from AI_architecture's own path set.
- The classifier can parse the current `config/ownership.yaml` v1 subset without PyYAML.
- The current config classifies `scripts/lib_ownership.py` as system-owned and system-locked.
- Existing validation still passes.

## Rollback Plan

- Remove `scripts/lib_ownership.py`, `tests/test_ownership.py`, this plan, and the ownership map entries for `scripts/lib_ownership.py`.
- No runtime ledgers, lock files, target projects, or upgrade integrations are affected.

## Stop Conditions

- If classifier implementation requires changing `upgrade-from-skeleton.py` or `verify-skeleton.py`, stop and move that work to Slice 3.
- If the Slice 1 document and YAML disagree on guard semantics, update the Slice 1 spec text in the same change and keep classifier behavior explicit.
- If the current ownership config cannot be parsed by a small v1 subset parser, stop and either simplify the YAML or defer parsing to Slice 3.

## Validation

```bash
python3 -m unittest tests.test_ownership -v
python3 -m unittest discover -s tests -v
python3 scripts/verify-skeleton.py
python3 scripts/quality-gate.py --root . --tier stable --skip-tests --format json
python3 scripts/agent-flow.py closeout \
  --goal "Ownership-aware upgrade v1 Slice 2 classifier synthetic tests" \
  --changed-path plans/active/0009-ownership-classifier-synthetic-tests.md \
  --changed-path scripts/lib_ownership.py \
  --changed-path tests/test_ownership.py \
  --changed-path docs/OWNERSHIP_MODEL.md \
  --changed-path config/ownership.yaml \
  --changed-path plans/INDEX.md \
  --changed-path runtime/state/session-handoff.md \
  --changed-path state/progress.md \
  --changed-path runtime/session-snapshot.json \
  --format json
```

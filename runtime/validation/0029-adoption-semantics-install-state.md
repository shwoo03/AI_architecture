# 0029 Adoption Semantics Validation

## Focused Tests

`tests.test_agent_flow` adopt regressions passed for:

- status mode without full tool execution
- dry-run synthesis
- candidate threshold stop
- dirty target stop
- GPL warning as blocking review
- unknown license as non-blocking metadata review
- old install-state fallback
- intentional preserve candidate reporting

## ENKI Read-Only Dry-Run

Command:

```text
PYTHONDONTWRITEBYTECODE=1 python3 scripts/agent-flow.py adopt --target <ENKI_WIKI_PATH> --format json
```

Result summary:

- recommendation: `needs_review`
- blocking review items: `0`
- non-blocking review items:
  - target license is unknown; metadata review only, not legal clearance
  - ownership status is already initialized
  - manual/risky upgrade items require review
- previous skeleton source commit: `a083da8f203a`
- current skeleton source commit: `36fa515`
- upgrade brief: `safe_missing=0`, `manual_merge=3`, `risky_changed=3`
- ownership: `already_initialized`, `candidate_paths=0`

Intentional preserve/review candidates reported by the current dry-run:

- `config/ownership.yaml`
- `skills/active/brainstorming/SKILL.md`
- `skills/active/verification-loop/SKILL.md`
- `.github/workflows/ci.yml`
- `docs/SKELETON_UPGRADE.md`
- `scripts/agent-flow.py`

The command was read-only. No ENKI target files were written.

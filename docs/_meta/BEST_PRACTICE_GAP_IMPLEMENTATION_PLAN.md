# Best Practice Gap Implementation Plan

This plan tracks the Claude-suggested G1-G7 improvements against the current
skeleton.

## Apply All, With Staging

All seven gaps are relevant. P0 and most P1 items are documentation/template
work and should be applied immediately. P2 items need executable design and
verification before activation.

## Gaps and Actions

| Gap | Status | Action |
| --- | --- | --- |
| G1 Progressive Disclosure budgets | applied | Added size guards to `CLAUDE.md` and universal skills; enriched trigger examples. |
| G2 LLM Wiki 3-op | partial | Kept `wiki-query.md` and `wiki-lint.md`; removed `wiki-ingest.md` as part of memory/promotion cleanup. Knowledge wiki is human-edited. |
| G3 Spec-Driven Development | applied | Added `docs/PROJECT_SPEC.template.md`; linked spec checks into operating loop and AGENTS read order. |
| G4 Hook/bootstrap automation | prepared | Added `scripts/` contracts for hook and bootstrap pilots. |
| G5 Agent budget/heartbeat | applied | Expanded `docs/AGENT_REGISTRY.md` with budgets, heartbeat, and parent goal. |
| G6 Reference skill | applied | Expanded `verification-loop` into a golden reference skill with data checklist and example report. |
| G7 Bootstrap experience | prepared | Added bootstrap script contract; executable implementation remains P2. |

## P0 Done

- Size guard comments and limits.
- Universal skill trigger examples.
- Reference verification skill.

## P1 Done/Prepared

- Project Spec template.
- Operating loop spec checkpoints.
- Wiki query/lint workflow contracts (ingest removed with memory pipeline).
- Lint report fixed format.
- Agent budget, heartbeat, and parent-goal fields.

## P2 Prepared

- Hook script contract.
- Bootstrap script contract.
- Wiki lint script contract.

## Next Implementation Step

Implement one pilot script first:

1. `scripts/hooks/post-tool-use-log.py`
2. Validate it appends parseable JSONL.
3. Add dry-run mode.
4. Only then connect it to Claude/Codex runtime hooks.

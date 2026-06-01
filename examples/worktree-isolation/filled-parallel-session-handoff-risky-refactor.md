# Filled parallel session handoff: risky refactor

## Worktree

- Main checkout: `/repo`
- Worktree: `/repo-worktrees/parser-boundary`
- Branch: `codex/parser-boundary`
- Base commit: `6a42de1`
- Owner: Codex session A

## Purpose

Isolate a parser refactor while another session updates API docs in the main
checkout.

## Scope

- Owned files: `src/parser/*`, `tests/parser/*`
- Do not edit: `docs/api.md`, `src/http/*`

## Current state

- Extracted token normalization behind `ParserInput`.
- Updated parser unit tests.
- No merge attempted yet.

## Validation

- Run: `pytest tests/parser -q`
- Result: pass
- Not run: full test suite

## Merge plan

1. Fetch latest main.
2. Rebase `codex/parser-boundary`.
3. Run full test suite.
4. Merge only if docs session has finished or conflict owner approves.

## Conflict risk

- Low for parser files.
- Medium if another branch changed shared test fixtures.

## Cleanup plan

- After merge or rejection, remove the worktree.
- Delete the branch only after confirming the merge or preservation decision.

## Notes for next session

- Do not continue this work in the main checkout until the worktree is reconciled.

# Worktree cleanup checklist

Use after an isolated branch is merged, rejected, or abandoned.

## Before cleanup

- [ ] Confirm the worktree branch name.
- [ ] Confirm whether the branch was merged, superseded, or rejected.
- [ ] Copy any needed handoff notes into the main project docs.
- [ ] Run or record the final validation status.
- [ ] Check that no uncommitted user work remains in the worktree.

## Cleanup

```bash
git worktree list
git worktree remove <path>
git branch --delete <branch>
```

Use `git branch --delete` only after merge or explicit rejection. Use
`git branch --delete --force` only when the owner explicitly approves losing the
branch.

## After cleanup

- [ ] Confirm `git worktree list` no longer shows the old path.
- [ ] Confirm `git status --short` in the main checkout.
- [ ] Update `docs/HANDOFF.md` with the final state.

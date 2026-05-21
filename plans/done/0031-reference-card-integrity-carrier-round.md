# reference card integrity carrier round

## Summary

Prepare the reference-card carrier before implementing any new security gate. This round fixed the trace boundary for ECC, paperclip, and opencode cards; recorded which cards were not checked; and prepared the proposal lifecycle so later dry-run proposals can be split or superseded without ambiguous status handling.

## Assumptions

- The user explicitly wanted the carrier/card-integrity round before any invisible-character or closeout/upgrade gate implementation.
- Scope was limited to ECC, paperclip, and opencode cards plus the minimal proposal lifecycle support needed for later dry-run splitting.
- Existing unrelated dirty worktree changes were not part of this plan and were not reverted.
- `agent-flow start` classified this reference/card-editing goal as `read_only`; the user's explicit instruction and this plan provided the write boundary for the card round.

## Out of Scope

- Implementing the invisible-character security scan.
- Implementing the reference-copy-ledger gate.
- Implementing closeout/readiness summaries.
- Implementing upgrade post-apply verification.
- Refreshing Hermes, llm_wiki, LangGraph, oh-my-codex, oh-my-claudecode, or andrej-karpathy-skills cards beyond listing them as unchecked in this round.
- Pulling or cloning additional external repositories.

## Implementation Steps

- Resolved the stale untracked `plans/active/0001-common-skeleton-improvements-for-cache-hygiene-l.md` carrier by preserving it as done plan 0030.
- Added `superseded` lifecycle support for reference adoption proposals, including `supersedes` and `superseded_by` fields in the template and validator/tests.
- Refreshed the ECC candidate card only for the `scripts/ci/` security/validation surface, including checked revision, source anchors, clone existence at review time, and explicit scope/out-of-scope notes.
- Marked paperclip's current candidate status as deferred for the heavy product-runtime governance surface, with rationale.
- Updated the opencode candidate card to distinguish already absorbed role/write-policy/LSP diagnostic ideas from remaining follow-up ideas.
- Recorded the checked and unchecked card list in `research/reference-candidates/README.md`.
- Appended the card-integrity round decision to `state/decisions.md`.

## Definition of Done

- ECC, paperclip, and opencode cards carry enough revision/source-anchor information for a future session to reproduce the review from another clone path.
- The ECC refresh is explicitly scoped to `scripts/ci/` security/validation surfaces and does not imply a full ECC surface review.
- Later security/provenance dry-run proposals can use `superseded` without failing `validate-reference-proposals.py`.
- Unchecked cards are listed so this round does not look like a full candidate inventory refresh.
- The next implementation work is still blocked on user approval of dry-run proposals.

## Rollback Plan

- Revert only this plan's touched files.
- If `superseded` lifecycle support proves too broad, revert the lifecycle change and require separate yes/no dry-run proposals instead.

## Stop Conditions

- Stop if `python3 scripts/agent-flow.py start --goal "<card integrity write goal>" --format json` continues to report `write_policy=read_only` and the user's explicit write approval is not available in the current conversation.
- Stop if candidate-card validation requires broader schema changes than this plan allows.
- Stop if an existing file has unrelated user edits in the same section that cannot be preserved safely.
- Stop if any action would require deleting or rolling back user changes.
- Stop before writing security/provenance or operational dry-run proposals; those are separate rounds.

## Validation

- `python3 scripts/validate-reference-candidates.py`: passed, 9 candidate cards checked.
- `python3 scripts/validate-reference-proposals.py`: passed, 2 proposals checked.
- `python3 -m unittest tests.test_reference_security.ReferenceProposalTests -v`: passed, 8 tests.
- `python3 scripts/validate-plans.py --allow-legacy-done`: passed, 31 plans checked before moving this plan to done.
- `python3 scripts/verify-skeleton.py`: passed with 0 errors and 1 ownership lock drift warning deferred outside this round.
- `python3 scripts/resume-readiness.py --strict`: passed with 0 warnings after handoff/progress alignment.
- `python3 scripts/task-closeout.py --goal "reference card integrity carrier round" --record --format json --profile reference --disposition complete ...`: passed and recorded completion evidence.

## Completion Notes

- A first `agent-flow closeout` attempt inferred a scripts-fast profile and failed because the partial disposition needed a next action; a second scripts-fast closeout recorded partial evidence but exposed that `tests.test_validation` is not runnable under the system Python 3.9 due existing `str | None` type syntax in that test module.
- The final recorded closeout used the reference profile, which matches this carrier round and passed.
- No security/provenance gate implementation was started.

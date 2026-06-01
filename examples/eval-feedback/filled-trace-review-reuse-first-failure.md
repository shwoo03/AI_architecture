# Filled trace review: reuse-first failure

## Trace summary

- Date: 2026-06-01
- Project type: agent runtime app
- Change under review: custom tool dispatcher added for multi-step agent calls
- Result: failed review

## What happened

The agent implemented a local dispatcher for tool calls, retries, and handoffs
without checking official SDK features first. The resulting code duplicated SDK
orchestration and had no tracing owner.

## Expected behavior

Before implementing runtime infrastructure, the agent should run
`recipes/open-source-reuse.md` and compare official SDK support.

## Evidence

- Trace showed no read of `recipes/open-source-reuse.md`.
- `docs/REFERENCES.md` had no adoption record.
- The implementation introduced custom retry state and tool routing.

## Failure class

- wrong SDK/runtime boundary
- missing adoption record
- missing eval case

## Fix

- Remove the custom dispatcher.
- Use the official SDK runtime for tool execution, handoffs, sessions, and tracing.
- Add an adoption record explaining why the SDK is selected.

## Regression case

Given a request to add agent runtime orchestration, the agent must:

1. Read `recipes/open-source-reuse.md`.
2. Check official SDK/runtime capabilities.
3. Write or update `docs/REFERENCES.md`.
4. Avoid custom orchestration unless existing options are rejected with reasons.

## Promote to kit docs?

- AGENTS.md: no change
- recipe: no change
- example: this filled trace review is enough
- dogfood backlog: only if the same failure repeats

# AGENTS.md

This file is the canonical instruction source for AI coding agents working in
this project.

## Project Goal

State the project goal in one sentence.

```text
Goal: <what this project is trying to accomplish>
```

## Success Criteria

Define how completion is judged.

- The primary workflow works for the target user.
- The required tests or checks pass.
- Security and data-handling constraints are respected.
- The handoff file explains the current state and next action.

## Non-Goals

List things the agent should not build unless explicitly asked.

- Do not introduce new frameworks without a clear reason.
- Do not add long-running automation before the project needs it.
- Do not store secrets, tokens, credentials, or private user data in the repo.

## Working Rules

- Read the project profile before making changes.
- Search existing files before creating new structures.
- Prefer small, testable changes.
- Follow the existing stack and style before introducing alternatives.
- Use official SDK or harness features instead of reimplementing agent loops.
- Ask before destructive changes, dependency changes, pushes, deployments, or
  external API calls that may cost money.

## Validation

Record the cheapest useful validation for each task.

```text
Check:
Lint:
Unit:
Smoke:
Manual:
```

If validation cannot run, record why in the handoff.

## Handoff

Update `docs/HANDOFF.md` when:

- A milestone is completed.
- Work stops with unresolved questions.
- The next agent needs context to continue.
- A risky decision was made.

## References

When using external docs, repositories, examples, or copied patterns:

- Add a short entry to `docs/REFERENCES.md`.
- Include the source link, checked date, why it matters, and how it was used.
- Do not copy code unless the license and copy boundary are clear.

## Harness Adapters

This file is canonical. Harness-specific files such as `CLAUDE.md` should be
generated from this file or kept clearly marked as adapters.


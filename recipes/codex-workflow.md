# Codex Workflow Recipe

Use this recipe when Codex is the primary coding agent.

## When To Use

- Small or medium codebase work.
- Refactors, tests, reviews, bug fixes, and local implementation.
- Projects that need a durable instruction file but not a custom agent runtime.

## Structure

```text
AGENTS.md
docs/PROJECT_PROFILE.md
docs/HANDOFF.md
docs/SECURITY.md
docs/REFERENCES.md  # optional
```

## Practice

- Keep `AGENTS.md` short and project-specific.
- Put success criteria in `PROJECT_PROFILE.md`.
- Update `HANDOFF.md` at stopping points.
- Link official docs or external examples in `REFERENCES.md`.
- Do not add custom routing scripts until repeated work proves they help.

## Avoid

- Recreating an agent loop in local scripts.
- Making every project carry audit ledgers or proposal queues.
- Hiding project-specific rules in global user settings.

Official reference:

- https://developers.openai.com/codex/guides/agents-md


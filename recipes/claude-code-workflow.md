# Claude Code workflow recipe

Official links: see `templates/links.md`.

## When to use

- Claude Code is the primary local coding harness.
- The project benefits from Claude-specific adapters, hooks, subagents, skills, or MCP.

## When not to use

- The project only needs generic instructions consumed by multiple harnesses.
- Hooks/subagents would add hidden automation without clear value.

## Minimal setup

```text
AGENTS.md          # canonical
CLAUDE.md          # generated adapter
docs/PROJECT_PROFILE.md
docs/HANDOFF.md
docs/SECURITY.md
```

## Checklist

- Generate `CLAUDE.md` from `AGENTS.md`.
- Enable hooks only if audit/control is needed.
- Define subagents only when scope, permissions, or context separation is needed.
- Keep skills as reusable workflows, not one-off prompts.
- Keep MCP config reviewed and secret-safe.

## Common mistakes

- Using hooks as hidden automation.
- Enabling too many tools.
- Letting `CLAUDE.md` drift from `AGENTS.md`.
- Making subagents the default for simple tasks.


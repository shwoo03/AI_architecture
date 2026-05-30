# CLAUDE.md

> Generated adapter. Do not edit directly.
>
> Canonical source: `AGENTS.md`
>
> Regenerate with:
>
> ```bash
> python3 tools/scaffold/gen-harness-instructions.py --project . --harness claude
> ```

Claude Code should follow the project instructions in `AGENTS.md`.

Use Claude-specific features only when the project opts in:

- `CLAUDE.md`: adapter instructions for Claude Code.
- Subagents: use for isolated context, parallel review, or clearly scoped
  specialist work.
- Hooks: use for blocking unsafe tools, recording audit events, or enforcing
  validation.
- MCP: use for external systems that need a typed, auditable tool boundary.
- Skills/plugins: use for reusable project workflows, not for one-off prompts.


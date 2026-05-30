# Claude Code Workflow Recipe

Use this recipe when Claude Code is the primary local coding harness.

## When To Use

- Local codebase automation with Claude Code.
- Projects that benefit from Claude-specific subagents, hooks, skills, or MCP.
- Teams already standardized on Claude Code.

## Structure

```text
AGENTS.md          # canonical source
CLAUDE.md          # generated adapter
docs/PROJECT_PROFILE.md
docs/HANDOFF.md
docs/SECURITY.md
```

Optional:

```text
.claude/agents/    # project subagents
.claude/skills/    # project skills
.claude/hooks/     # hook scripts or config
.mcp.json          # only when reviewed and secret-safe
```

## Practice

- Generate `CLAUDE.md` from `AGENTS.md`.
- Use subagents for context isolation, parallel review, or specialist work.
- Use hooks to block unsafe tools or enforce validation.
- Use MCP only for external systems that need a tool boundary.

## Avoid

- Keeping divergent instructions in `AGENTS.md` and `CLAUDE.md`.
- Adding subagents for every role before there is repeated need.
- Letting hooks mutate source files invisibly.

Official references:

- https://code.claude.com/docs/en/features-overview
- https://code.claude.com/docs/en/sub-agents
- https://code.claude.com/docs/en/agent-sdk/hooks


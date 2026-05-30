# Claude Agent SDK Recipe

Use this recipe when you want to build programmatic workflows around Claude
Code-style tools, hooks, context management, and local automation.

## When To Use

- You need Claude Code behavior from an application or scripted workflow.
- You need hooks for tool interception or audit.
- You need project-specific plugins, skills, or MCP servers loaded
  programmatically.

## Project Structure

```text
AGENTS.md
CLAUDE.md
docs/PROJECT_PROFILE.md
docs/HANDOFF.md
docs/SECURITY.md
src/claude_agent/
  options/
  hooks/
  tools/
  tests/
```

## Practice

- Use SDK hooks for policy enforcement, logging, and permission handling.
- Keep hook behavior explicit and testable.
- Treat subagents as isolated specialists with clear scope.
- Keep secrets outside repository config.

## Avoid

- Using hooks as hidden business logic.
- Spawning subagents without a bounded task and allowed tools.
- Duplicating canonical project rules in SDK options.

Official references:

- https://code.claude.com/docs/en/agent-sdk/hooks
- https://code.claude.com/docs/en/sub-agents
- https://docs.claude.com/en/api/agent-sdk/plugins


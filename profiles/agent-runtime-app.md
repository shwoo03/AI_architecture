# Agent Runtime App Profile

Use this profile when the application itself includes an agent workflow.

## Copy

- All solo-small templates.
- `templates/canonical/REFERENCES.md`.

## Add

```text
src/agents/
  instructions/
  tools/
  handoffs/
  evals/
```

## Recommended Recipes

- `recipes/openai-agents-sdk.md`
- `recipes/claude-agent-sdk.md`
- `recipes/mcp-connection.md`
- `recipes/security-permissions.md`

## Decision Rule

- Use OpenAI Agents SDK when building a product runtime with tools, handoffs,
  tracing, and streaming.
- Use Claude Agent SDK when you need Claude Code-style local automation or
  hooks in a programmatic workflow.


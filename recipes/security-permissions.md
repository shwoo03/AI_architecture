# Security and Permissions Recipe

Security is part of the starter kit, not an optional afterthought.

## Baseline

Every project should have:

- `docs/SECURITY.md`
- secret handling rules
- destructive-action confirmation rules
- dependency-change confirmation rules
- MCP allowlist expectations when MCP is used

## Secrets

- Use `.env` locally and keep it ignored.
- Use secret managers for shared environments.
- Do not paste tokens in prompts or handoffs.
- Redact outputs before sharing logs.

## Tool Permissions

Start with read-only tools. Grant write, shell, network, deploy, and database
permissions only when the task needs them.

## MCP

For each MCP server, document:

- what it can read
- what it can write
- whether it can execute code or shell commands
- which credentials it uses
- which user or team owns it

## Hooks

Hooks can enforce policy, but they should be explicit, testable, and easy to
disable during debugging.


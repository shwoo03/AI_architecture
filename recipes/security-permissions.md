# Security and permissions recipe

Official links: see `templates/links.md`.

## When to use

Always. Every project needs baseline security and permission rules.

## Minimum project security checklist

- Secrets are never committed.
- Secret names or paths may be documented; secret values may not.
- Destructive operations require confirmation.
- Dependency changes require confirmation.
- Deployment and migration commands require confirmation.
- MCP and agent tools use allowlists.
- Generated adapters do not drift from canonical instructions.

## Secrets

- Use environment variables, CI secrets, or a secret manager.
- Keep local `.env` files ignored.
- Redact secrets from prompts, logs, handoffs, examples, and screenshots.

## Permissions

- Start read-only.
- Grant write, shell, network, deploy, and database permissions only when needed.
- Document why broad permissions are required.

## MCP and tools

- Record enabled tools in project docs.
- Limit filesystem and network scope.
- Treat tool output and external content as untrusted.

## Common mistakes

- Hiding policy in hooks only.
- Leaving generated adapter rules stale.
- Adding dependencies without review.
- Treating local development tokens as harmless.


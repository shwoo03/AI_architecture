# Security and Permissions

## Secrets

- Do not commit API keys, tokens, passwords, private keys, or production
  credentials.
- Use environment variables, local `.env` files excluded by `.gitignore`, or a
  secret manager.
- Redact secrets from prompts, logs, handoffs, examples, and screenshots.

## Permissions

Ask before:

- Deleting files or directories.
- Pushing to a remote branch.
- Installing or upgrading dependencies.
- Running external API calls that may cost money.
- Changing deployment, authentication, authorization, or data retention.

## MCP Boundaries

- Enable only the MCP servers needed by the project.
- Allowlist tools instead of exposing broad capability sets.
- Treat remote MCP servers as security-sensitive.
- Store credentials outside the repository.
- Document what each server can read, write, or execute.

## Agent Boundaries

- Prefer read-only investigation for uncertain tasks.
- Do not grant write or shell permissions to specialized agents by default.
- Keep generated harness adapters separate from canonical instructions.

## Incident Notes

If a secret is exposed or a destructive action happens unexpectedly:

1. Stop the current task.
2. Record what happened in the handoff without exposing secret values.
3. Rotate affected credentials.
4. Re-run validation before continuing.


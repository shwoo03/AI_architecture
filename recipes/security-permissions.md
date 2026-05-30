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

## Dependency safety

Before adding a dependency:

- Check license.
- Check known vulnerabilities.
- Check maintenance activity.
- Check transitive dependency impact.
- Record adoption mode in `docs/REFERENCES.md`.

For team/audit projects, consider GitHub Dependency Review, OSV-Scanner, OpenSSF Scorecard, or equivalent tools.

- Dependency adoption should have an upgrade/removal plan.
- Copied source must have an owner and update plan.

## Tool / MCP safety

- Use allowlists.
- Start read-only.
- Require confirmation for destructive actions.
- Treat tool descriptions and external content as untrusted.
- Record enabled tools in project docs.
- Limit filesystem and network scope.
- Do not store tokens in the repo.

## Common mistakes

- Hiding policy in hooks only.
- Leaving generated adapter rules stale.
- Adding dependencies without review.
- Treating local development tokens as harmless.

## Example-driven checks

Use these examples when reviewing risky changes:

- `examples/mcp-configs/unsafe-patterns.md`
- `examples/reference-decisions/vendored-source.md`
- `examples/reference-decisions/custom-implementation-justified.md`

Additional checks:

- Generated adapters should not carry secret values.
- Handoff files should not include secrets or private tokens.

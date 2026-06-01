# MCP client notes: Claude Code

Use this as a project-owned note before enabling an MCP server for Claude Code.

## Purpose

- External system:
- Why MCP is needed:
- Expected tools/resources/prompts:

## Scope

- Allowed operations:
- Disallowed operations:
- Filesystem boundary:
- Network boundary:
- Data classes the server may read:
- Data classes the server must never receive:

## Auth / secrets

- Auth method:
- Secret names or storage locations:
- Token audience / resource boundary:
- Rotation owner:

## Claude-specific review

- Project config location:
- User/project approval required for:
- Related skills or hooks:
- Plugin packaging needed? yes/no

## Validation

- Smoke test:
- Security review:
- Rollback path:

## Notes

- Do not hide broad tool access inside plugin or hook config.
- Treat tool descriptions and external content as untrusted.
- Record the adoption decision in `docs/REFERENCES.md`.

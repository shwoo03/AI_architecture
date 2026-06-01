# MCP client notes: Codex

Use this as a project-owned note before enabling an MCP server for Codex.

## Purpose

- External system:
- Why MCP is needed instead of a local command or direct API call:
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

## Approval

- Owner:
- Review date:
- User approval required for:
- Rollback path:

## Validation

- Smoke test:
- Security review:
- Logging/tracing owner:

## Notes

- Do not commit credentials.
- Treat tool descriptions and external content as untrusted.
- Record the adoption decision in `docs/REFERENCES.md`.

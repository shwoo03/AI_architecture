# MCP connection recipe

Official links: see `templates/links.md`.

MCP is a standard connection layer for external systems. In this kit, MCP is an
optional boundary for tools and data, not a default project requirement.

## When to use

- The project needs data, tools, or workflows beyond the local repository.
- Multiple harnesses should share one tool boundary.
- The external tool needs permissions, auth, or audit.

## When not to use

- One local function or one HTTP request is enough.
- The permission boundary cannot be described.
- The project has no repeated tool need.

## Concepts

- Host: the AI app or coding harness.
- Client: the component connecting the host to a server.
- Server: the process exposing tools, resources, or prompts.

## Directory convention

```text
mcp/
  servers/<name>/server-config.md
  clients/<host>/client-config.md
```

## Checklist

- Define allowed tools.
- Define secrets/auth boundary.
- Limit filesystem and network scope.
- Record consent or approval requirements.
- Treat tool descriptions and external content as untrusted.

## Example server-config.md

```text
# <server-name>

purpose:
tool allowlist:
auth method:
secret names or paths:
filesystem boundary:
network boundary:
owner:
review date:
```

## Common mistakes

- Exposing broad shell or filesystem tools.
- Committing credentials in MCP config.
- Enabling remote servers without review.


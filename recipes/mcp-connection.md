# MCP Connection Recipe

MCP is a standard way to connect AI hosts and clients to external tools and
data through servers. This kit treats MCP as a connection boundary, not as a
default project requirement.

## When To Use

- The project needs repeated access to external systems.
- Tool calls need a typed and inspectable boundary.
- Multiple harnesses or clients should share the same tool server.
- The tool has meaningful permissions or security risk.

## When Not To Use

- A simple local function or one-off HTTP request is enough.
- The tool has no durable use beyond a single task.
- You cannot define the permission boundary.

## Suggested Structure

```text
mcp/
  servers/
    <server-name>/
      README.md
      config.example.json
      env.example
      tools.md
      security.md
  clients/
    claude-code.md
    codex.md
    openai-agents-sdk.md
```

## Security Checklist

- Document every exposed tool.
- Prefer read-only tools first.
- Use allowlists.
- Store secrets in environment variables or a secret manager.
- Review remote MCP servers before enabling them.
- Do not expose shell, filesystem, or network tools broadly.

Official references:

- https://modelcontextprotocol.io/docs/learn/architecture
- https://modelcontextprotocol.io/specification/2025-03-26/basic/authorization


# Start here

Use this file when you are applying AI Project Kit to a new or existing project.

## 1. Pick your project shape

- Small personal project -> `profiles/solo-small-project.md`
- Team/audit project -> `profiles/team-audit-project.md`
- Agent runtime app -> `profiles/agent-runtime-app.md`
- Research-heavy project -> `profiles/research-heavy-project.md`
- Legacy upgrade -> `profiles/legacy-project-upgrade.md`

## 2. Scaffold or copy manually

```bash
python3 tools/scaffold/init-project.py --target /tmp/my-project --profile solo-small-project --force
```

The scaffold helpers are optional. You can also copy the canonical templates
manually.

## 3. Fill the canonical docs

- `AGENTS.md`
- `docs/PROJECT_PROFILE.md`
- `docs/SECURITY.md`
- `docs/HANDOFF.md`
- `docs/REFERENCES.md`

## 4. Add only what the project needs

- Claude Code -> generate `CLAUDE.md`
- OpenAI Agents SDK app -> read `recipes/openai-agents-sdk.md`
- Claude Agent SDK app -> read `recipes/claude-agent-sdk.md`
- MCP -> read `recipes/mcp-connection.md`
- Skills -> read `recipes/skill-writing.md`
- Community systems -> read `references/community-ai-systems.md`

## 5. Record adoption decisions

Use `docs/REFERENCES.md` whenever the project evaluates SDKs, libraries,
community systems, copied source, adapters, forks, or custom implementation.

## 6. Dogfood the result

If the kit feels too heavy or incomplete, write a sanitized report in
`dogfood/reports/` and add only actionable repeated issues to
`dogfood/backlog.md`.


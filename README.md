# AI Project Kit

This repository is a starter kit for setting up AI-assisted software projects.
It is not an agent runtime and it does not try to replace Codex, Claude Code,
OpenAI Agents SDK, Claude Agent SDK, or MCP clients.

The kit provides:

- Canonical project templates for agent instructions, project profile, handoff,
  references, and security boundaries.
- Recipes for choosing and configuring Codex, Claude Code, OpenAI Agents SDK,
  Claude Agent SDK, skills, MCP, and lightweight reference tracking.
- Profiles that explain which recipes to use for common project shapes.
- Small scaffold helpers that copy templates or generate harness-specific
  instruction files from the canonical source.

## Design Principles

1. Keep the default project surface small.
2. Treat `AGENTS.md` as the canonical instruction source.
3. Generate harness-specific files such as `CLAUDE.md` from canonical source
   instead of hand-maintaining duplicates.
4. Do not reimplement official SDK or harness behavior in this kit.
5. Keep security, permissions, secrets, and provenance visible in templates.
6. Add skills, MCP, agents, logs, or reference workflows only when the project
   actually needs them.

## Recommended Project Minimum

For a small project, copy only:

```text
AGENTS.md
docs/PROJECT_PROFILE.md
docs/HANDOFF.md
docs/SECURITY.md
```

Add `docs/REFERENCES.md` when external examples, SDK docs, or copied ideas
matter to the work.

## Repository Layout

```text
templates/
  canonical/          Source templates shared by all harnesses.
  harness-adapters/   Generated or optional harness-facing surfaces.
recipes/              Practical guides for features and tools.
profiles/             Project-shape checklists.
examples/             Minimal example projects.
tools/scaffold/       Optional helper scripts. Not an operating workflow.
```

## Quick Start

1. Pick a profile from `profiles/`.
2. Copy the matching templates from `templates/canonical/`.
3. Use only the recipes needed by the project.
4. If using Claude Code, generate `CLAUDE.md` from `AGENTS.md`.

Example:

```bash
python3 tools/scaffold/init-project.py --target /path/to/project --profile solo-small-project
python3 tools/scaffold/gen-harness-instructions.py --project /path/to/project --harness claude
```

## Official References

- OpenAI Codex AGENTS.md guide: https://developers.openai.com/codex/guides/agents-md
- OpenAI Agents SDK: https://platform.openai.com/docs/guides/agents-sdk/
- OpenAI Responses API: https://platform.openai.com/docs/api-reference/responses
- Claude Code feature overview: https://code.claude.com/docs/en/features-overview
- Claude Code subagents: https://code.claude.com/docs/en/sub-agents
- Claude Agent SDK hooks: https://code.claude.com/docs/en/agent-sdk/hooks
- Model Context Protocol: https://modelcontextprotocol.io/docs/learn/architecture


# Official link registry

Last verified: 2026-05-30

This file is the single place for official documentation links used by the kit.
Canonical templates and recipes should reference this file instead of duplicating URLs.

## Codex

- Codex AGENTS.md guide
  - https://developers.openai.com/codex/guides/agents-md
  - Use for: canonical project instructions, instruction discovery, nested overrides.

- Codex configuration, permissions, hooks, MCP, skills, and subagents
  - Start from the Codex docs navigation:
  - https://developers.openai.com/api/docs/guides/agents
  - Use for: Codex-specific adapters and optional workflow notes.

## OpenAI

- OpenAI Agents SDK guide
  - https://developers.openai.com/api/docs/guides/agents
  - Use for: official agent runtime, orchestration, guardrails, state, observability, evaluation.

- OpenAI Agents SDK Python docs
  - https://openai.github.io/openai-agents-python/
  - Use for: Python SDK implementation examples.

- OpenAI Responses API reference
  - https://platform.openai.com/docs/api-reference/responses
  - Use for: low-level API integration and stateful response workflows.

## Claude

- Claude Agent SDK overview
  - https://code.claude.com/docs/en/agent-sdk/overview
  - Use for: Claude Code as a programmable agent runtime.

- Claude Code subagents
  - https://code.claude.com/docs/en/sub-agents
  - Use for: optional role/context separation.

- Claude Code hooks
  - https://code.claude.com/docs/en/hooks
  - Use for: optional lifecycle interception and audit hooks.

- Claude Code skills
  - https://code.claude.com/docs/en/skills
  - Use for: optional reusable workflows.

- Claude Code MCP
  - https://code.claude.com/docs/en/mcp
  - Use for: Claude-specific MCP setup.

## MCP

- MCP introduction
  - https://modelcontextprotocol.io/docs/getting-started/intro
  - Use for: high-level MCP explanation and architecture.

- MCP specification
  - https://modelcontextprotocol.io/specification/2025-06-18
  - Use for: security/trust model, hosts/clients/servers, resources/prompts/tools.

## Security

- MCP specification security section
  - https://modelcontextprotocol.io/specification/2025-06-18
  - Use for: consent, data privacy, tool safety, sampling controls.

- OpenAI production and safety docs
  - Start from:
  - https://developers.openai.com/api/docs/guides/agents
  - Use for: guardrails, evals, production checks.

## Reference management

- Keep project-specific references in `docs/REFERENCES.md`.
- Use lightweight entries by default:
  - name
  - URL
  - why it was used
  - adoption level: reference-only | concept-only | dependency | copied-source


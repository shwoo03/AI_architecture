# Official link registry

Last verified: 2026-06-01

This file is the single place for official documentation links used by the kit.
Canonical templates and recipes should reference this file instead of duplicating URLs.

## Freshness policy

- Review this file monthly or before major kit releases.
- Prefer official docs over blog posts.
- Update `Last verified` only after checking links.
- When official docs change behavior, update the matching recipe or example.

## Codex

- Codex AGENTS.md guide
  - https://developers.openai.com/codex/guides/agents-md
  - Use for: canonical project instructions, instruction discovery, nested overrides.

- Codex overview and use cases
  - https://developers.openai.com/codex/
  - Use for: Codex-specific workflow orientation before opening feature-specific docs.

- Codex hooks
  - https://developers.openai.com/codex/hooks
  - Use for: optional lifecycle hook configuration, trust/review flow, and hook event behavior.

- Codex plugins
  - https://developers.openai.com/codex/plugins
  - Use for: installing and managing Codex plugin packages.

- Codex build plugins
  - https://developers.openai.com/codex/plugins/build
  - Use for: plugin packaging rules, `.codex-plugin/plugin.json`, bundled skills/hooks/MCP/app config.

## OpenAI

- OpenAI Agents SDK guide
  - https://developers.openai.com/api/docs/guides/agents
  - Use for: official agent runtime, orchestration, guardrails, state, observability, evaluation.

- OpenAI Agents SDK Python docs
  - https://openai.github.io/openai-agents-python/
  - Use for: Python SDK implementation examples.

- OpenAI Agents SDK tracing
  - https://openai.github.io/openai-agents-python/tracing/
  - Use for: built-in traces/spans, sensitive data controls, and observability decisions.

- OpenAI Responses API reference
  - https://platform.openai.com/docs/api-reference/responses
  - Use for: low-level API integration and stateful response workflows.

- OpenAI conversation state
  - https://developers.openai.com/api/docs/guides/conversation-state
  - Use for: Responses API conversation state, Conversations API, previous_response_id, context window considerations.

- OpenAI Agents SDK sessions
  - https://openai.github.io/openai-agents-python/sessions/
  - Use for: built-in session memory, SQLiteSession, RedisSession, session sharing, compaction session.

- OpenAI evals
  - https://developers.openai.com/api/docs/guides/evals
  - Use for: model/application evaluation loop, datasets, eval runs, regression checks.

- OpenAI compaction
  - https://developers.openai.com/api/docs/guides/compaction
  - Use for: context management and compaction concepts.

## Claude

- Claude Agent SDK overview
  - https://code.claude.com/docs/en/agent-sdk/overview
  - Use for: Claude Code as a programmable agent runtime.

- Claude Code memory
  - https://code.claude.com/docs/en/memory
  - Use for: CLAUDE.md, auto memory, /memory, compaction survival, rules organization.

- Claude Code extension overview
  - https://code.claude.com/docs/en/features-overview
  - Use for: choosing between CLAUDE.md, skills, subagents, hooks, MCP, and plugins.

- Claude Code checkpointing
  - https://code.claude.com/docs/en/checkpointing
  - Use for: rewind, session safety, edit checkpoints.

- Claude Code worktrees
  - https://code.claude.com/docs/en/worktrees
  - Use for: parallel sessions, worktree isolation, subagent isolation.

- Claude Code subagents
  - https://code.claude.com/docs/en/sub-agents
  - Use for: optional role/context separation.

- Claude Code hooks
  - https://code.claude.com/docs/en/hooks
  - Use for: lifecycle hooks, event schemas, command/HTTP/prompt hooks, security guidance.

- Claude Code plugins
  - https://code.claude.com/docs/en/plugins
  - Use for: plugin packaging, `.claude-plugin/plugin.json`, skills/agents/hooks/MCP bundling.

- Claude Code MCP
  - https://code.claude.com/docs/en/mcp
  - Use for: Claude-specific MCP setup.

## Agent memory / context references

- LangGraph memory overview
  - https://docs.langchain.com/oss/python/concepts/memory
  - Use for: short-term vs long-term memory, semantic/episodic/procedural memory concepts.

- LangGraph persistence and memory
  - https://docs.langchain.com/oss/python/langgraph/persistence
  - Use for: checkpoints, thread state, stores, and runtime persistence concepts.

- LlamaIndex agent memory
  - https://developers.llamaindex.ai/python/framework/module_guides/deploying/agents/memory/
  - Use for: short-term/long-term memory blocks, fact extraction memory, vector memory, token-based flushing.

- Google ADK sessions, state, and memory
  - https://adk.dev/sessions/
  - Use for: session/state/memory separation in runtime agent applications.

- CrewAI memory
  - https://docs.crewai.com/en/concepts/memory
  - Use for: community runtime memory concepts and adoption comparisons.

## Claude skills

- Claude Code skills
  - https://code.claude.com/docs/en/skills
  - Use for: optional reusable procedure packaging.

## MCP

- MCP introduction
  - https://modelcontextprotocol.io/docs/getting-started/intro
  - Use for: high-level MCP explanation and architecture.

- MCP specification
  - https://modelcontextprotocol.io/specification/2025-11-25
  - Use for: security/trust model, hosts/clients/servers, resources/prompts/tools.

- MCP authorization
  - https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization
  - Use for: HTTP transport authorization, OAuth/resource handling, token handling, and remote server review.

- MCP elicitation
  - https://modelcontextprotocol.io/specification/2025-11-25/client/elicitation
  - Use for: client-mediated user input requests and human approval boundaries.

## Agent interoperability

- Google ADK multi-agent workflows
  - https://adk.dev/workflows/
  - Use for: runtime multi-agent workflow concepts and reference-only comparisons.

- Google ADK with A2A
  - https://adk.dev/a2a/
  - Use for: agent-to-agent interoperability concepts and reference-only adoption decisions.

## Security

- MCP security best practices
  - https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices
  - Use for: confused deputy, token passthrough, SSRF, session hijacking, and scope minimization.

- OpenAI production and safety docs
  - Start from:
  - https://developers.openai.com/api/docs/guides/agents
  - Use for: guardrails, evals, production checks.

## Project templating

- Copier
  - https://copier.readthedocs.io/en/stable/
  - Use for: replacing custom scaffold scripts if template generation/update logic grows.

- Cookiecutter
  - https://cookiecutter.readthedocs.io/en/stable/
  - Use for: simple project template generation.

## Open-source / dependency safety

- GitHub Dependency Review
  - https://docs.github.com/en/code-security/concepts/supply-chain-security/about-dependency-review
  - Use for: PR dependency change review, vulnerability/license/age signals.

- OpenSSF Scorecard
  - https://securityscorecards.dev/
  - Use for: open-source security posture signal.

- OSV-Scanner
  - https://google.github.io/osv-scanner/
  - Use for: dependency vulnerability scanning.

## Reference management

- Keep project-specific references in `docs/REFERENCES.md`.
- Use lightweight entries by default:
  - name
  - URL
  - why it was used
  - adoption level: reference-only | concept-only | direct-dependency | adapter | fork | vendored-source | rejected

## Community references

- Non-official community/open-source AI systems are tracked in `references/community-ai-systems.md`.
- Keep official links and community references separate.

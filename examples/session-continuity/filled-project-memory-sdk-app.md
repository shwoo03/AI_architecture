# Filled project memory: SDK app

Use this only when stable facts repeat across sessions. Do not copy activity
logs here.

## Stable facts

- The product embeds an agent runtime. Repository instructions stay in
  `AGENTS.md`; runtime agent prompts live under `app/agents/instructions/`.
- The project chose the official OpenAI Agents SDK for orchestration, handoffs,
  sessions, and tracing.

## Non-obvious setup

- Local runs require `OPENAI_API_KEY` in the shell environment.
- Traces are enabled only in development and staging; production export is owned
  by the observability team.

## Recurring pitfalls

- Do not put runtime prompts in repository `AGENTS.md`.
- Do not store user conversation transcripts in `docs/HANDOFF.md`.
- Do not add a custom memory store before checking SDK sessions.

## Successful commands / recipes

- `pytest tests/agents -q`
- `recipes/openai-agents-sdk.md`
- `recipes/eval-feedback-loop.md`

## Important decisions

- Use SDK sessions for runtime conversation state.
- Use `docs/HANDOFF.md` only for repository work state.
- Record new tool approvals in `docs/REFERENCES.md`.

## Open questions

- Whether production tracing needs a custom processor.

## Hygiene

- No secrets.
- No private transcripts.
- Review stale entries monthly.

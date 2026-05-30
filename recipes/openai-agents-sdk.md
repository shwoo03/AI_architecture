# OpenAI Agents SDK Recipe

Use this recipe when the product or service needs an agent runtime.

## When To Use

- The application needs tool-using agents.
- The app needs handoffs between specialized agents.
- You need tracing, streaming, and runtime observability.
- You are building a user-facing or service-facing agent workflow.

## Project Structure

```text
AGENTS.md
docs/PROJECT_PROFILE.md
docs/HANDOFF.md
docs/SECURITY.md
src/agents/
  instructions/
  tools/
  handoffs/
  evals/
```

## Practice

- Keep operational project instructions in `AGENTS.md`.
- Keep agent runtime instructions close to runtime code.
- Treat handoffs and tools as application behavior, not skeleton behavior.
- Add tests or evals for tool contracts and handoff outcomes.
- Record external sources in `docs/REFERENCES.md`.

## Avoid

- Reimplementing SDK handoffs or tracing in custom scripts.
- Mixing product agent prompts with repository operating instructions.
- Granting tools broader access than the user flow needs.

Official references:

- https://platform.openai.com/docs/guides/agents-sdk/
- https://platform.openai.com/docs/api-reference/responses
- https://platform.openai.com/docs/guides/tools


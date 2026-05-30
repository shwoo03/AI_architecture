# OpenAI Agents SDK recipe

Official links: see `templates/links.md`.

## When to use

- The app needs an embedded agent runtime.
- The product needs tools, handoffs, guardrails, state, tracing, or evals.
- Agent behavior is part of application logic.

## When not to use

- You only need coding assistant instructions.
- There is no runtime app or product workflow.
- A simple API call or local script is enough.

## Minimal setup

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

## Checklist

- Define the agent input/output contract.
- Define the tool allowlist.
- Add guardrails/evals for production paths.
- Keep secrets outside the repository.
- Do not rebuild orchestration in kit scripts.

## Common mistakes

- Mixing repository operating instructions with runtime agent prompts.
- Granting tools broader access than the user flow needs.
- Reimplementing SDK handoffs, tracing, or orchestration.

## Policy sentence

This repo uses the official SDK for agent runtime behavior. The starter kit only
supplies canonical project docs, adapters, recipes, and profiles.


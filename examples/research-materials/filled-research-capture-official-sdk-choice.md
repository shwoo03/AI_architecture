# Filled research capture: official SDK choice

## Question

Should this project build a custom agent runtime or use an official SDK?

## Sources checked

- OpenAI Agents SDK docs
- OpenAI conversation state docs
- Claude Agent SDK docs
- One community framework as reference-only comparison

## Findings

- Official SDKs already cover tool execution, handoffs, sessions, tracing, and
  human approval patterns.
- The project needs runtime behavior inside application code, not a repository
  workflow wrapper.
- A custom dispatcher would duplicate SDK behavior and increase maintenance risk.

## Decision

Use the official SDK for runtime orchestration. Keep this starter kit limited to
templates, recipes, examples, and adoption records.

## Applied change

- Updated `docs/REFERENCES.md` with the SDK adoption decision.
- Kept runtime prompts under `app/agents/instructions/`.
- Did not add runtime code to the starter kit.

## Promotion

- Template change: no
- Recipe change: no
- Example change: this file
- Dogfood backlog: only if future projects repeat the same confusion

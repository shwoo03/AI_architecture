# AI Project Kit

This repository is a starter kit for setting up AI-assisted software projects.
It supplies templates, harness adapters, recipes, profiles, examples, and small
scaffold helpers. It is not an agent runtime.

Official links are centralized in `templates/links.md`.

## Design Rules

1. Runtime belongs to official SDKs and harnesses.
2. The kit supplies canonical templates, generated adapters, recipes, and profiles.
3. `AGENTS.md` is the canonical instruction source.
4. Harness-specific files such as `CLAUDE.md` are generated adapter surfaces.
5. MCP, skills, hooks, subagents, SDKs, and reference workflows are optional.
6. Small projects should stay small.

## Reuse-First Philosophy

AI Project Kit is designed to prevent agents from defaulting to "I will build
everything from scratch."

For non-trivial infrastructure, agents should:

1. Check official SDKs first.
2. Search maintained open-source projects.
3. Evaluate real adoption options.
4. Prefer direct dependency or thin adapter.
5. Record license, security, and maintenance decisions.
6. Implement custom code only after rejecting existing options.

This kit is not a runtime. It provides rails:

- templates
- recipes
- profiles
- examples
- optional scaffold helpers

Runtime belongs to official SDKs/harnesses and project-specific code.

## Tooling Policy

This kit is usable without Python.

The files under `tools/scaffold/` are optional convenience helpers for:

- copying canonical templates into a target project
- generating short harness adapter files from canonical instructions

They are not an agent runtime and must not become one.

Do not add new scaffold scripts unless the same result cannot be achieved with:

- a Markdown template
- a profile checklist
- an existing project-template tool
- an official SDK/harness feature

If scaffold logic grows beyond simple copy/generate behavior, prefer adopting a
standard template tool such as Copier or Cookiecutter.

## Layout

```text
templates/
  links.md           Official documentation link registry.
  canonical/         Source templates shared by all harnesses.
  harness-adapters/  Short generated adapter templates.
recipes/             Practical setup guides and checklists.
  open-source-reuse.md
profiles/            Project-shape checklists.
examples/            Minimal example shapes.
  agents-md/
  reference-decisions/
  mcp-configs/
  claude-subagents/
  skills/open-source-adoption/
  openai-agents-sdk-app/
  claude-agent-sdk-app/
tools/scaffold/      Optional copy/generate helpers.
```

## Examples

Use examples when you want a concrete pattern before applying a recipe.

Recommended order:

1. Start with the matching profile.
2. Read the recipe.
3. Copy the closest example.
4. Adapt it to the project.
5. Record decisions in `docs/REFERENCES.md`.

## Minimum Project Surface

For a small project, scaffold:

```text
AGENTS.md
docs/PROJECT_PROFILE.md
docs/HANDOFF.md
docs/SECURITY.md
docs/REFERENCES.md
docs/LINKS.md
docs/PROFILE_CHECKLIST.md
```

Do not add runtime ledgers, proposal queues, specialist ledgers, MCP servers, or
skills unless the project profile calls for them.

## What This Kit Intentionally Does Not Do

- No runtime.
- No `agent-flow.py`.
- No default logs or ledgers.
- No default MCP servers.
- No default skills or subagents.
- No dependency automation.

## Quick Start

```bash
python3 tools/scaffold/init-project.py --target /tmp/my-ai-project --profile solo-small-project --force
python3 tools/scaffold/gen-harness-instructions.py --project /tmp/my-ai-project --harness claude
```

Supported generated adapters:

```bash
python3 tools/scaffold/gen-harness-instructions.py --list-harnesses
```

## How To Choose

- Use Codex or Claude Code directly for small coding projects.
- Use OpenAI Agents SDK when the app embeds an agent runtime.
- Use Claude Agent SDK when you need programmatic Claude Code-like behavior.
- Use MCP only when external tools/data need a reviewed tool boundary.
- Use skills only for repeated workflows with clear contracts.

For details, start with the matching file in `profiles/`, then open only the
recipes that profile names.

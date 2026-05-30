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

## Layout

```text
templates/
  links.md           Official documentation link registry.
  canonical/         Source templates shared by all harnesses.
  harness-adapters/  Short generated adapter templates.
recipes/             Practical setup guides and checklists.
profiles/            Project-shape checklists.
examples/            Minimal example shapes.
tools/scaffold/      Optional copy/generate helpers.
```

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


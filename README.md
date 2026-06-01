# AI Project Kit

This repository is a starter kit for setting up AI-assisted software projects.
It supplies templates, harness adapters, recipes, profiles, examples, and small
scaffold helpers. It is not an agent runtime.

Official links are centralized in `templates/links.md`.

Start with `START_HERE.md` if you are applying the kit to a project for the
first time.

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
  optional/          Optional templates not copied by default.
START_HERE.md        First-use guide for applying the kit.
CHANGELOG.md         Release notes.
recipes/             Practical setup guides and checklists.
  open-source-reuse.md
  hook-policy.md
  plugin-packaging.md
  subagent-policy.md
  session-continuity.md
  research-material-management.md
  eval-feedback-loop.md
  worktree-isolation.md
references/
  community-ai-systems.md  Non-official community/open-source AI systems catalog.
profiles/            Project-shape checklists.
examples/            Minimal example shapes.
  agents-md/
  reference-decisions/
  mcp-configs/
  claude-subagents/
  hooks/
  plugins/
  session-continuity/
  research-materials/
  eval-feedback/
  worktree-isolation/
  skills/open-source-adoption/
  mcp-enabled-tool/
  openai-agents-sdk-app/
  claude-agent-sdk-app/
dogfood/             Sanitized adoption reports, backlog, and repeated lessons.
tools/scaffold/      Optional copy/generate helpers.
```

## Examples

Use examples when you want a concrete pattern before applying a recipe.
See `examples/README.md` for the index.

Recommended order:

1. Start with the matching profile.
2. Read the recipe.
3. Copy the closest example.
4. Adapt it to the project.
5. Record decisions in `docs/REFERENCES.md`.

## Dogfooding

Apply the kit to real projects, then write a short sanitized report in
`dogfood/reports/`.

Use `dogfood/backlog.md` to triage actionable kit improvements. Promote repeated
lessons to recipes, templates, examples, or README only after they repeat across
projects.

## Community References

Official docs live in `templates/links.md`.

Community/open-source AI systems live in `references/community-ai-systems.md`.
Use them for ecosystem learning and concept extraction. Do not install them by
default. Before adopting one, use `recipes/community-reference-evaluation.md`
and record the decision in `docs/REFERENCES.md`.

Examples include ECC, Hermes Agent, Oh My Codex, and Paperclip. See the
reference catalog for details.

## Session Continuity

Use `docs/HANDOFF.md` for current session state. Use optional
`docs/PROJECT_MEMORY.md` only for stable facts that should survive many
sessions. Use `research/` only for research-heavy projects.

Do not build a custom memory system in this kit.

## Research Materials

Use `recipes/research-material-management.md` when papers, blogs, official docs,
issues, or repos materially affect a decision.

Research should flow:

```text
source -> brief -> synthesis -> applied change -> docs/REFERENCES.md or kit update
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

## What This Kit Intentionally Does Not Do

- No runtime.
- No `agent-flow.py`.
- No default logs or ledgers.
- No default MCP servers.
- No default skills or subagents.
- No default hooks.
- No default plugins.
- No default project memory file.
- No default research archive.
- No eval runtime.
- No worktree automation.
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

## Release Validation

Before releasing kit changes, validate the helper surface and the intentionally
small scaffold output:

```bash
python3 -m py_compile tools/scaffold/*.py
```

```bash
for profile in solo-small-project team-audit-project agent-runtime-app research-heavy-project legacy-project-upgrade; do
  python3 tools/scaffold/init-project.py --target "/private/tmp/ai-project-kit-smoke-$profile" --profile "$profile" --force
done
```

```bash
for harness in claude codex openai mcp; do
  python3 tools/scaffold/gen-harness-instructions.py --project /private/tmp/ai-project-kit-smoke-solo-small-project --harness "$harness" --force
done
```

Check that the small-project scaffold still does not generate optional operating
surfaces by default:

```bash
test ! -e /private/tmp/ai-project-kit-smoke-solo-small-project/.claude
test ! -e /private/tmp/ai-project-kit-smoke-solo-small-project/.codex
test ! -e /private/tmp/ai-project-kit-smoke-solo-small-project/docs/PROJECT_MEMORY.md
test ! -e /private/tmp/ai-project-kit-smoke-solo-small-project/research
test ! -e /private/tmp/ai-project-kit-smoke-solo-small-project/evals
test ! -e /private/tmp/ai-project-kit-smoke-solo-small-project/runtime
test ! -e /private/tmp/ai-project-kit-smoke-solo-small-project/mcp
test ! -e /private/tmp/ai-project-kit-smoke-solo-small-project/hooks
test ! -e /private/tmp/ai-project-kit-smoke-solo-small-project/skills
test ! -e /private/tmp/ai-project-kit-smoke-solo-small-project/subagents
test ! -e /private/tmp/ai-project-kit-smoke-solo-small-project/plugins
test ! -e /private/tmp/ai-project-kit-smoke-solo-small-project/worktrees
```

Finish with:

```bash
git diff --check
```

## How To Choose

- Use Codex or Claude Code directly for small coding projects.
- Use OpenAI Agents SDK when the app embeds an agent runtime.
- Use Claude Agent SDK when you need programmatic Claude Code-like behavior.
- Use MCP only when external tools/data need a reviewed tool boundary.
- Use skills only for repeated workflows with clear contracts.
- Use subagents only for isolated context, permissions, or repeated specialist roles.
- Use hooks only for reviewed lifecycle checks or guardrails.
- Use plugins only when skills/hooks/agents/MCP need a reviewed reusable package.
- Use session-continuity recipe for long-running projects.
- Use eval-feedback-loop for agent runtime apps or repeated agent failure.
- Use worktree-isolation for parallel sessions.
- Do not enable hooks or plugins by default.

For details, start with the matching file in `profiles/`, then open only the
recipes that profile names.

# AGENTS.md

This repository is an AI project starter kit. It is not an agent runtime.

## Working Rules

- Keep the default project surface small.
- Treat reuse-first as a core design principle: check official SDKs and maintained open-source options before custom infrastructure.
- Do not reintroduce heavy operating-system defaults.
- Do not restore custom runtime, orchestration, `agent-flow.py`, runtime ledgers, proposal queues, specialist ledgers, or feature-tier machinery.
- Keep `AGENTS.md` as the canonical instruction source.
- Keep harness-specific files as generated adapter surfaces.
- Put official documentation links in `templates/links.md`.
- Keep official links and community references separate.
- Put community AI systems in `references/community-ai-systems.md`.
- Do not promote a community system to default dependency without a project-specific adoption record.
- If adding a community reference, include license/activity/security/adoption-mode notes.
- Prefer official SDK or harness features over local reimplementation.
- Prefer recipes, templates, profiles, and examples over new scripts.
- Treat examples as first-class documentation.
- When improving a recipe, add a small example if it prevents ambiguity.
- Treat hooks and plugins as optional high-risk extension surfaces.
- Prefer recipes/examples over default hook/plugin generation.
- Do not add hooks/plugins to scaffold output.
- If adding hook/plugin guidance, document security review, owner, and rollback path.
- Do not create hidden automation through hooks.
- Preserve session continuity through files, not chat memory.
- Do not rely on conversation-only instructions for stable decisions.
- Promote stable facts to canonical docs or optional `PROJECT_MEMORY`.
- Put detailed paper/blog/repo analysis in research examples or project research docs.
- Do not add default memory/research/eval/worktree automation.
- Treat dogfood reports as evidence for improving templates, recipes, and examples.
- Prefer fixing repeated dogfood issues over reacting to one-off project quirks.
- Do not put secrets, private tokens, customer data, or proprietary source in dogfood reports.
- Keep Python scaffold helpers optional and small.
- New automation must justify why existing tools, official harness features, or Markdown templates are insufficient.
- Do not create default-generated `.claude/skills`, `.claude/agents`, MCP servers, runtime logs, or proposal queues.

## Validation

```bash
python3 -m py_compile tools/scaffold/*.py
python3 tools/scaffold/init-project.py --target /private/tmp/ai-project-kit-smoke --profile solo-small-project --force
python3 tools/scaffold/gen-harness-instructions.py --project /private/tmp/ai-project-kit-smoke --harness claude
python3 tools/scaffold/gen-harness-instructions.py --list-harnesses
git diff --check
```

Before release, also smoke-test every profile and harness adapter. Confirm the
generated small-project surface does not include `.claude/`, `.codex/`,
`docs/PROJECT_MEMORY.md`, `research/`, `evals/`, `runtime/`, MCP servers, hooks,
skills, subagents, plugins, or worktree automation unless a project explicitly
adds them after review.

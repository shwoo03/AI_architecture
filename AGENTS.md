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
- Prefer official SDK or harness features over local reimplementation.
- Prefer recipes, templates, profiles, and examples over new scripts.
- Treat examples as first-class documentation.
- When improving a recipe, add a small example if it prevents ambiguity.
- Keep Python scaffold helpers optional and small.
- New automation must justify why existing tools, official harness features, or Markdown templates are insufficient.
- Do not create default-generated `.claude/skills`, `.claude/agents`, MCP servers, runtime logs, or proposal queues.

## Validation

```bash
python3 -m py_compile tools/scaffold/*.py
python3 tools/scaffold/init-project.py --target /private/tmp/ai-project-kit-smoke --profile solo-small-project --force
python3 tools/scaffold/gen-harness-instructions.py --project /private/tmp/ai-project-kit-smoke --harness claude
```

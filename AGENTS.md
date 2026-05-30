# AGENTS.md

This repository is an AI project starter kit. It is not an agent runtime.

## Working Rules

- Keep the default project surface small.
- Do not reintroduce heavy operating-system defaults.
- Do not restore `agent-flow.py`, runtime ledgers, proposal queues, specialist ledgers, or feature-tier machinery as default behavior.
- Keep `AGENTS.md` as the canonical instruction source.
- Keep harness-specific files as generated adapter surfaces.
- Put official documentation links in `templates/links.md`.
- Prefer official SDK or harness features over local reimplementation.

## Validation

```bash
python3 -m py_compile tools/scaffold/*.py
python3 tools/scaffold/init-project.py --target /private/tmp/ai-project-kit-smoke --profile solo-small-project --force
python3 tools/scaffold/gen-harness-instructions.py --project /private/tmp/ai-project-kit-smoke --harness claude
```


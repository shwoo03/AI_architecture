# AGENTS.md

This repository is an AI project starter kit. It provides templates, recipes,
profiles, examples, and small scaffold helpers. It is not an agent runtime.

## Canonical Sources

- Template source files live in `templates/canonical/`.
- Harness-specific guidance lives in `templates/harness-adapters/`.
- Recipes explain when and how to add optional systems.
- Profiles explain which templates and recipes fit a project shape.

## Working Rules

- Keep the default project surface small.
- Do not reintroduce a custom operating workflow CLI as a default requirement.
- Prefer official SDK or harness features over local reimplementation.
- Keep generated or adapter instructions derived from canonical templates.
- Keep security, secrets, permissions, and MCP boundaries explicit.

## Validation

For changes to this kit:

```bash
python3 -m py_compile tools/scaffold/*.py
python3 tools/scaffold/init-project.py --target /tmp/ai-project-kit-smoke --profile solo-small-project --force
python3 tools/scaffold/gen-harness-instructions.py --project /tmp/ai-project-kit-smoke --harness claude
```


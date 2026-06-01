# Skill examples

Skills are optional reusable workflow contracts. They are not copied into
scaffolded projects by default.

Use a skill when:

- the workflow repeats across projects or sessions
- activation is clear
- inputs, outputs, permissions, and verification can be described
- the skill reduces duplication or operational risk

Do not use a skill when:

- the task is a one-off prompt
- the workflow has broad side effects
- official SDK/runtime behavior already covers the need
- the project cannot review the skill source

## Files

- `open-source-adoption/`: example reuse-first skill.
- `unsafe-skill-patterns.md`: patterns to reject.

## Placement

- Example-only skills stay under `examples/skills/`.
- Project-local Claude skills may live in `.claude/skills/` after review.
- Codex reusable skills should be packaged through a reviewed plugin when needed.
- Generated starter projects should not include skill directories by default.

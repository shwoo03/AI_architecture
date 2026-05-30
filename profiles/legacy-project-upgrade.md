# Legacy Project Upgrade Profile

Use this profile when adding AI project instructions to an existing repository.

## First Step

Do not overwrite existing project docs. Add the minimal files and preserve local
conventions.

## Copy

- `AGENTS.md`
- `docs/PROJECT_PROFILE.md`
- `docs/HANDOFF.md`
- `docs/SECURITY.md`

## Merge Carefully

- Existing README.
- Existing security policy.
- Existing development docs.
- Existing CI and test commands.
- Existing Claude/Codex/Cursor/IDE instructions.

## Avoid

- Bulk moving files.
- Adding a custom workflow CLI.
- Replacing project-specific rules with generic starter kit rules.


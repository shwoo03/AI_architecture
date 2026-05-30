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
- Existing hooks/plugins and generated extension configs.

## Replacement Policy

- Look for official SDKs/open-source packages that can delete custom internal code.
- Prefer deleting custom code over wrapping more custom code.
- Replace in small slices.
- Keep rollback plan.
- Record rejected candidates.
- Watch for hidden hooks/plugins in legacy config.
- Remove duplicates before adding packaged plugins.

## Avoid

- Bulk moving files.
- Adding a custom workflow CLI.
- Replacing project-specific rules with generic starter kit rules.
- Adding new hooks/plugins before understanding existing automation.

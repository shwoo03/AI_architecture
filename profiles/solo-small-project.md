# Solo Small Project Profile

Use this profile for small personal projects, prototypes, scripts, and small
apps.

## Copy

- `templates/canonical/AGENTS.md` -> `AGENTS.md`
- `templates/canonical/PROJECT_PROFILE.md` -> `docs/PROJECT_PROFILE.md`
- `templates/canonical/HANDOFF.md` -> `docs/HANDOFF.md`
- `templates/canonical/SECURITY.md` -> `docs/SECURITY.md`
- `templates/canonical/REFERENCES.md` -> `docs/REFERENCES.md`
- `templates/links.md` -> `docs/LINKS.md`
- `profiles/solo-small-project.md` -> `docs/PROFILE_CHECKLIST.md`

## Optional

- `templates/optional/PROJECT_MEMORY.md` -> `docs/PROJECT_MEMORY.md`
- project-owned research, eval, MCP, hook, skill, plugin, subagent, or worktree docs when friction appears

## Do Not Add By Default

- custom agent orchestration CLI
- activity log JSONL
- proposal queues
- feature tier systems
- specialist ledgers
- MCP servers
- skills directory
- subagents
- hooks
- plugins
- evals
- worktrees
- `docs/PROJECT_MEMORY.md`
- `research/`

## Recommended Harness

Use Codex or Claude Code directly. Keep the project instructions short.

## Reuse Policy

- Implement tiny helpers directly.
- For infrastructure-like features, run `recipes/open-source-reuse.md`.
- Record only the selected/rejected decision in `docs/REFERENCES.md`.
- Do not add heavy dependency gates by default.
- Avoid hooks/plugins by default.
- Use normal validation commands before lifecycle automation.
- Use `docs/HANDOFF.md` only for continuity.
- Do not add `docs/PROJECT_MEMORY.md`, `research/`, evals, or worktrees unless friction appears.

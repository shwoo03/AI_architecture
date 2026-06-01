# Team Audit Project Profile

Use this profile when multiple people or agents collaborate and decisions need
traceability.

## Copy

- Same default scaffold surface as `solo-small-project`.
- This includes `docs/REFERENCES.md`, `docs/LINKS.md`, and
  `docs/PROFILE_CHECKLIST.md`.

## Optional project-owned additions

```text
docs/DECISIONS.md
docs/VALIDATION.md
```

Add these manually only when team review or audit evidence needs more structure
than `docs/REFERENCES.md` and `docs/HANDOFF.md`.

## Practices

- Keep handoff current.
- Record important architecture and security decisions.
- Use lightweight reference entries for external ideas.
- Add CI checks from the project stack, not from this kit.
- Hooks/plugins require owner, review date, and rollback path.
- Plugin/hook adoption should be recorded in `docs/REFERENCES.md`.
- Consider research material management for important dependency/security decisions.
- Use `recipes/eval-feedback-loop.md` for repeated quality failures.
- Use `recipes/worktree-isolation.md` when parallel sessions or risky work need isolated checkouts.
- Keep sanitized evidence.

## Dependency Adoption Gate

Before adding a dependency:

- Record it in `docs/REFERENCES.md`.
- Check license.
- Check known vulnerabilities.
- Check maintenance activity.
- Record upgrade/removal plan.
- Consider GitHub Dependency Review, OSV-Scanner, OpenSSF Scorecard, or equivalent tools.

## Optional Recipes

- `recipes/security-permissions.md`
- `recipes/reference-lite.md`
- `recipes/mcp-connection.md`
- `recipes/subagent-policy.md`
- `recipes/hook-policy.md`
- `recipes/plugin-packaging.md`
- `recipes/research-material-management.md`
- `recipes/eval-feedback-loop.md`
- `recipes/open-source-reuse.md`

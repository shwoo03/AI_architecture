# Team Audit Project Profile

Use this profile when multiple people or agents collaborate and decisions need
traceability.

## Copy

- All solo-small templates.
- `templates/canonical/REFERENCES.md` -> `docs/REFERENCES.md`.

## Add

```text
docs/DECISIONS.md
docs/VALIDATION.md
```

## Practices

- Keep handoff current.
- Record important architecture and security decisions.
- Use lightweight reference entries for external ideas.
- Add CI checks from the project stack, not from this kit.

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
- `recipes/open-source-reuse.md`

# Research Heavy Project Profile

Use this profile when external references strongly shape the project.

## Copy

- Same default scaffold surface as `solo-small-project`.
- This includes `docs/REFERENCES.md`, `docs/LINKS.md`, and
  `docs/PROFILE_CHECKLIST.md`.

## Optional project-owned research area

```text
research/
  sources/
  briefs/
  syntheses/
  applied/
```

Add this manually only when papers, blogs, repos, issues, or official docs
materially affect decisions. Small projects should not create a research archive
by default.

## Practices

- Keep each reference note short and evidence-based.
- Record adoption mode.
- Create a decision note before copying code or adopting architecture.
- Re-check fast-moving SDK docs before implementation.
- Use `recipes/research-material-management.md`.
- Keep source cards, briefs, syntheses, and applied change records.
- Promote only repeated findings to templates/recipes/examples.

## Research Policy

- Compare multiple candidates for major subsystems.
- Include small but high-quality repositories.
- Do not rank by stars alone.
- Inspect code/API fit, release activity, issue quality, license, and integration cost.
- End each reference with an adoption mode.
- Evaluate community hook/plugin packs with `recipes/community-reference-evaluation.md`.

## Avoid

- Link dumps with no reason.
- Copying repository structures wholesale.
- Turning research into a blocking workflow for simple implementation tasks.
- Installing hook/plugin packs before review.

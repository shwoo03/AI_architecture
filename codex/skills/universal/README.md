# Universal Skills

Canonical universal skill seeds live in project `.claude/skills/` so Claude
Code can discover them after the skeleton is copied. Codex uses the same skill
files by explicit instruction from `AGENTS.md`.

Included skills:

- `.claude/skills/search-first/SKILL.md`
- `.claude/skills/tdd-workflow/SKILL.md`
- `.claude/skills/verification-loop/SKILL.md`
- `.claude/skills/security-review/SKILL.md`

Do not duplicate skill bodies here. Keep this directory as a Codex-facing index
to the shared project skill surface.

# Unsafe skill patterns

Reject these patterns unless a project-specific review explicitly accepts the
risk and records owner, permissions, and rollback path.

## Broad hidden side effects

- Skill silently edits many files.
- Skill runs deployment, deletion, or migration commands without approval.
- Skill changes auth, billing, or production data.

## Unclear activation

- Description is so broad the skill activates for unrelated tasks.
- Skill overlaps with `AGENTS.md` rules or another skill.
- Skill is a one-off prompt saved as reusable workflow.

## Permission overreach

- Skill requires broad shell, filesystem, browser, or network access without a
  narrow reason.
- Skill reads secrets or private data as part of normal operation.
- Skill depends on unreviewed remote scripts.

## Runtime duplication

- Skill reimplements SDK handoffs, tracing, sessions, or tool orchestration.
- Skill becomes hidden business logic for an application runtime.

## Poor maintainability

- No owner.
- No validation step.
- No examples.
- No rollback/removal path.

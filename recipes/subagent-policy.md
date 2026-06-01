# Subagent policy recipe

Official links: see `templates/links.md`.

Subagents are optional workers with separate context, tools, or review scope.
They are useful when isolation improves quality or safety. They are not a
default project requirement.

## When to use

- A side task would flood the main session context.
- A reviewer needs different instructions or tool permissions.
- Parallel research, security review, or dependency review can run independently.
- The same specialist role repeats across tasks.

## When not to use

- The task is a simple edit or one-file lookup.
- The only reason is to "think harder".
- The role has no clear output contract.
- Coordination cost is higher than doing the task in the main session.

## Subagent record

Before creating a project-local subagent, record:

- Name:
- Purpose:
- Owner:
- Trigger / when to use:
- Inputs:
- Expected output summary:
- Allowed tools:
- Files or data it may read:
- Files or data it may write:
- Security constraints:
- Validation / review:
- Rollback path:

## Placement

- Example-only subagents live in `examples/claude-subagents/`.
- Project-local Claude subagents may live in `.claude/agents/` only after review.
- Do not add `.claude/agents/` to scaffolded projects by default.
- If several projects need the same subagent, evaluate plugin packaging.

## Common mistakes

- Making subagents the default for simple work.
- Giving broad shell/filesystem access without a reason.
- Hiding business logic or policy inside a subagent.
- Returning long logs instead of a concise summary.
- Creating overlapping subagents with unclear ownership.

# ECC and Paperclip Pattern Adoption

This document records which ECC and Paperclip patterns are adopted by this
skeleton and how to use them in new projects.

## Adopted ECC Patterns

| Pattern | Local Contract |
| --- | --- |
| Harness-agnostic reuse | Shared Markdown, YAML frontmatter, JSONL logs, and Python scripts. |
| Skills as primary workflow surface | Project `.claude/skills/*/SKILL.md` is the shared project skill format; `codex/skills/` explains Codex usage. |
| Rules vs skills split | `rules/` defines WHAT; skills define HOW. |
| Language rule modules | `rules/languages/python/README.md` and `rules/languages/typescript/README.md` seed stack-specific rules. |
| Executable hooks | `scripts/hooks/post-tool-use-log.py` appends activity events. |
| Runtime profiles | `AI_HOOK_PROFILE` and `AI_DISABLED_HOOKS` control hook behavior contracts. |
| Copy/bootstrap project install | `scripts/bootstrap/new-project.py` copies the skeleton and initializes profile/spec/logs. |
| Native skill locations | Project skills stay in `.claude/skills/`; personal global skills are user-managed outside this skeleton. |
| MCP discipline | `rules/common/mcp-discipline.md` caps per-project MCP servers at 10 and tools at 80 to protect the context window. |

## Adopted Paperclip Patterns

| Pattern | Local Contract |
| --- | --- |
| Agent as operating asset | `codex/agents/*.md` frontmatter plus `docs/AGENT_REGISTRY.md`. |
| Heartbeat | `runtime/schedules/README.md` defines recurring wake-up contracts. |
| Persistent task context | Runtime logs and proposals preserve resume pointers. |
| Goal ancestry | `goal_lineage` is required for recurring or delegated runs. |
| Atomic checkout | `task_checkout_start` and `task_checkout_end` events mark work boundaries. |
| Governance controls | `docs/GOVERNANCE.md` records approvals and escalations. |

## Default Usage

1. Start a project with `scripts/bootstrap/new-project.py`.
2. Fill `docs/PROJECT_PROFILE.md`.
3. Select project skills from `.claude/skills/`.
4. Ask the agent to create `docs/PROJECT_SPEC.md` only if implementation needs
   explicit acceptance tests or interface contracts.
5. Select or define agents in `codex/agents/`.
6. Record work using `runtime/activity-log.jsonl` and `runtime/agent-runs.jsonl`.
7. Run `scripts/wiki-lint.py` before editing durable knowledge.

## Explicitly Not Adopted

- `skill-packs/` directories.
- `pack.lock` files.
- `pack.manifest.json` files.
- Custom skill precedence rules.
- Global skill installer or promotion workflow.

Claude Code already provides project, user-global, and plugin skill tiers. This
skeleton keeps custom package management and global skill lifecycle management
out of the base architecture.

## Optional Template Provided

- **PreToolUse write-time guard** (secret patterns, dangerous commands,
  protected path writes). Shipped as `scripts/hooks/pre-tool-use-guard.py.example`
  with the `.example` suffix so it stays inert by default. Rename to
  `pre-tool-use-guard.py` and wire into the harness to enable. See
  `scripts/hooks/README.md` "PreToolUse 선택 활성화" section.

## Not Adopted Yet

- Full daemon scheduler.
- Multi-tenant database isolation.
- Real budget checkout against an external billing ledger.
- **Budget envelope** (per-run and monthly token budgets with soft/hard
  thresholds). Frontmatter fields `max_tokens_per_run`, `monthly_token_budget`,
  `soft_warn_threshold`, `hard_stop_threshold`, `max_wall_time` were removed
  because Codex/Claude Code do not consume them at runtime; declaring numbers
  with no enforcer created a "governance gap". Projects that need budgeting
  can describe it in `docs/PROJECT_OPERATING_PLAN.md`.
- **Circuit-breaker and budget-event logging** (`budget_warning`,
  `budget_exceeded`, `circuit_breaker_opened`). Removed alongside the budget
  envelope for the same reason.

These are intentionally deferred until a concrete project needs them.

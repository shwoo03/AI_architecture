# Knowledge Index

This is the bounded index for durable project knowledge. Keep one line per
entry. Put details in `knowledge/log.md`, `knowledge/project-registry.md`, or
project-specific files.

| ID | Topic | Status | Pointer | Superseded By | Superseded At |
| --- | --- | --- | --- | --- | --- |
| K000 | Common AI architecture skeleton initialized. | active | `README.md:1` | - | - |
| K001 | Agent operations layer added: workflows, registry, governance, schedules, and run logs. | active | `AGENTS.md:1` | - | - |
| K002 | Codex and Claude compatibility added through `CLAUDE.md`, shared rules, `.claude/skills`, and thin project overlay. | active | `docs/THREE_LAYER_MODEL.md:1` | - | - |
| K003 | Notion documentation rules added: DB pages only, no nested pages, directory/feature-based detail. | active | `docs/NOTION_DOCUMENTATION_RULES.md:1` | - | - |
| K004 | Best-practice gap implementation plan added for progressive disclosure, SDD, wiki ops, budgets, hooks, and bootstrap. | active | `docs/_meta/BEST_PRACTICE_GAP_IMPLEMENTATION_PLAN.md:1` | - | - |
| K005 | Project registry preserves reusable project outcomes and salvage notes. | active | `knowledge/project-registry.md:1` | - | - |
| K007 | Wiki query workflow defines index-first lazy loading for agents and skills. | active | `docs/wiki-ops/wiki-query.md:1` | - | - |
| K008 | Wiki lint workflow detects stale, duplicate, superseded, and orphan entries. | active | `docs/wiki-ops/wiki-lint.md:1` | - | - |
| K009 | ECC and Paperclip patterns adopted as rules, skills, agents, budgets, heartbeat, lineage, hooks, bootstrap, and examples. | active | `docs/_meta/ECC_PAPERCLIP_PATTERNS.md:1` | - | - |
| K010 | Memory/promotion pipeline removed: no `runtime/memory/`, no auto-promotion; knowledge is human-edited; agents drive profile via dialogue. | active | `AGENTS.md:1, CLAUDE.md:1` | - | - |
| K011 | Session continuity protocol added: `runtime/state/session-handoff.md` and `docs/SESSION_CONTINUITY.md` preserve state across session boundaries. | active | `docs/SESSION_CONTINUITY.md:1` | - | - |
| K012 | Skeleton self-audit cleanup: bootstrap isolation fixed, meta docs moved to `docs/_meta/`, wiki ops to `docs/wiki-ops/`, AGENTS read order tiered. | active | `runtime/activity-log.jsonl:13` | - | - |

## Index Rules

- One row per knowledge item.
- Keep summaries short.
- Prefer stable IDs.
- Every entry MUST include a source pointer (activity-log ts, file:line, or URL).
- When an entry is replaced, keep the original row and set `superseded_by` and
  `superseded_at` (`YYYY-MM-DD`) instead of deleting history.
- Do not paste large references here.
- Link to the detailed source instead.
- Knowledge wiki files moved into `docs/` subfolders (`_meta/`, `wiki-ops/`) are
  referenced with their new paths; do not restore old `knowledge/workflows/`
  paths.
- Knowledge 본문에서 다른 항목을 참조할 때는 `[[K003]]` 형식의 wikilink를 사용할 수
  있습니다. `scripts/wiki-lint.py`는 인덱스에 없는 대상을 `wikilink_broken` 카테고리로
  보고합니다. wikilinks는 본문 cross-reference 전용이며, 이 인덱스 표 자체에는 쓰지
  않습니다(표의 ID 컬럼이 canonical).

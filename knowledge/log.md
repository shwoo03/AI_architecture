# Knowledge Log

Append-only chronological knowledge log.

## 2026-04-23

- Added Codex and Claude compatibility: `CLAUDE.md`, shared `rules/`,
  Claude-discoverable `.claude/skills/`, a three-layer model document, and a
  thinner `PROJECT_PROFILE` overlay.
- Added `docs/_meta/NOTION_SOURCE_ASSESSMENT.md` to record that the Notion source is
  useful as a pattern library but still CTF Forge oriented rather than a
  plug-and-play general project manual.
- Added agent operations, workflow catalog, agent registry, governance,
  permission boundaries, scheduled workflow contracts, and agent run logs.
- Initialized the common AI architecture skeleton from the Notion-derived
  patterns: agent roles, skill architecture, hook-style automation, knowledge
  wiki, validation pipeline, and pivot triggers.
- Removed the skill/memory auto-promotion pipeline: deleted `runtime/memory/`,
  `codex/agents/memory-curator.md`, and the former `knowledge/workflows/wiki-ingest.md`.
  The bootstrap flow is now dialogue-driven from `docs/PROJECT_PROFILE.md`.

## Log Rules

- Append new entries at the top or bottom consistently.
- Do not delete old entries; add correction notes instead.
- Include evidence links or runtime log references when available.

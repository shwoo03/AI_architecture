# Notion Source Assessment

## Current Assessment

The existing Notion database is valuable as a pattern source, but legacy pages
are not all plug-and-play manuals for the current goal: copy this skeleton into
any new project and adapt it quickly.

Some older pages are domain-specific case studies. They should be preserved as
references, not treated as required architecture or onboarding material.

## What Transfers Well

- Skill 3-depth structure.
- Progressive disclosure.
- Hook-style automation.
- External validation.
- Activity logs.
- Conservative learning loop.
- Knowledge wiki pattern.
- Pivot and salvage triggers.
- Subagent context isolation.

## What Must Stay Out of the Universal Base

- Domain-specific terminology.
- Domain-specific scoring formulas.
- Domain-specific examples as the primary explanation.
- Project-only operating rules.
- Long prompts or recipes that belong in Layer 2 skills.

## Required Refactor for Immediate Reuse

To become immediately usable for arbitrary projects, Notion should document the
architecture as:

1. Layer 1 Universal Base.
2. Layer 2 Domain Skills.
3. Layer 3 Project Overlay.
4. Model A project copy/bootstrap procedure.
5. Claude native project skill location.
6. Thin `PROJECT_PROFILE` guidance as the only user-authored starting file.
7. Agent-created `PROJECT_SPEC` guidance when implementation needs it.
8. Codex and Claude compatibility notes.
9. Directory and feature-level manuals.

Existing domain-specific pages should remain as source examples or case studies,
not the main user-facing onboarding path.

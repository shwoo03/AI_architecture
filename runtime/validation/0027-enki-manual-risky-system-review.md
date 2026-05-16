# 0027 ENKI Manual Risky System Review Validation

## Summary

ENKI_WIKI manual/risky AI_architecture operating OS review completed against target `/Users/shwoo/mydir/ENKI_WIKI`. The migration remained preserve-first: ENKI runtime ledgers, app code, historical plan archive, Node CI, and project ownership overrides were not overwritten.

## Target Commits

- Existing baseline: `768e3a3e Add AI architecture ownership baseline`
- Existing safe apply: `a083da8f Apply safe AI architecture additions`
- New 0027 commit: `a46bc3ea Update AI operating OS system files`
- Follow-up ownership alignment: `54e8c33e Align transferred system ownership rules`
- Follow-up adoption intake profile fix: `7c64a566 Sync adoption intake profile check`

No ENKI push was performed.

## Initial Remaining Items

Initial adoption intake after 0026 reported `safe_missing=0`, `manual_merge=2`, `risky_changed=13`, `candidate_paths=0`, and no stop reasons.

### Manual Items

| Path | Disposition | Reason |
| --- | --- | --- |
| `AGENTS.md` | Applied source update | Diff was the stable-spec guard line; no ENKI-specific instruction was lost. |
| `config/ownership.yaml` | Preserved target with merge | ENKI `project_overrides` are project-owned and must remain. Only new system_locked patterns required by the transferred operating OS were merged. |

### Risky Items

| Path | Disposition | Reason |
| --- | --- | --- |
| `.github/workflows/ci.yml` | Preserved target | Source workflow would remove ENKI Node CI steps. ENKI CI remains project-owned. |
| `config/agent-team.yaml` | Applied source update | Operating OS registry update; no ENKI-specific content was present. |
| `docs/AGENT_REGISTRY.md` | Applied source update | Operating OS documentation update. |
| `docs/RUNTIME_EVENT_SCHEMA.md` | Applied source update | Runtime schema documentation update. |
| `docs/SKELETON_UPGRADE.md` | Applied source update | Upgrade/adoption workflow documentation update. |
| `docs/WORKFLOW_CATALOG.md` | Applied source update | Operating OS workflow catalog update. |
| `schemas/session-snapshot.schema.json` | Applied source update | Runtime schema update. |
| `scripts/agent-flow.py` | Applied source update | Public operating OS command surface update. |
| `scripts/quality-gate.py` | Applied source update | Stable gate update, including legacy done-plan compatibility. |
| `scripts/resume-readiness.py` | Applied source update | Session continuity check update. |
| `scripts/task-closeout.py` | Applied source update | Closeout helper update. |
| `scripts/upgrade-from-skeleton.py` | Applied source update | Adoption/upgrade helper update. |
| `scripts/verify-skeleton.py` | Applied source update | Skeleton health check update. |

## Additional System Dependencies Applied

Simulation showed that the latest transferred validators require additional system-owned files beyond the original 13 risky items. These were added or refreshed:

- `docs/VERSION_ROADMAP.md`
- `docs/design/V2_SPECIALIST_TEAM_OS.md`
- `docs/decisions/ADR-0002-sdk-adapter-not-core.md`
- `docs/reference-wiki/wiki/index.md`
- `docs/reference-wiki/wiki/log.md`
- `scripts/validate-plans.py`
- `scripts/validate-reference-proposals.py`
- `scripts/incubating/agent-flow-delegate.py`
- `scripts/incubating/agent-run.py`
- generated `.codex/.claude` communication-style rule surfaces

`docs/reference-wiki/wiki/**`, v2 design/ADR docs, and validator scripts were added to ENKI ownership system_locked patterns and explicit system_owned ownership rules to prevent future project overrides from hiding required system assets.

## Legacy Plan Compatibility

ENKI has a large historical `plans/done/` archive that predates the strict plan validator schema. Rewriting that archive would violate preserve-first migration. Instead:

- `scripts/validate-plans.py` gained `--allow-legacy-done`.
- `scripts/quality-gate.py` calls validate-plans with legacy done compatibility.
- `plans/active/001-enki-wiki-mvp.md` received a compatibility footer for the new active-plan schema.
- Historical done-plan files were not rewritten.

## ENKI Validation

All commands below were run against `/Users/shwoo/mydir/ENKI_WIKI` after applying and committing 0027:

- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify-parity.py --root /Users/shwoo/mydir/ENKI_WIKI --format json`: passed, no findings.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/operational-readiness.py --root /Users/shwoo/mydir/ENKI_WIKI --format json`: passed with ERROR 0, WARN 2 (`opencode` and `paperclip` candidate cards missing).
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/resume-readiness.py --root /Users/shwoo/mydir/ENKI_WIKI --strict --format json`: passed with ERROR 0, WARN 0.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/quality-gate.py --root /Users/shwoo/mydir/ENKI_WIKI --tier stable --skip-tests --skip-node --format json`: passed with OK 34, SKIP 1, WARN 2.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify-skeleton.py --root /Users/shwoo/mydir/ENKI_WIKI`: passed.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/ownership-lock.py --root /Users/shwoo/mydir/ENKI_WIKI check`: passed with classification_drift=0, lock_addition=0, lock_removal=0.
- After `7c64a566`, final focused checks passed again:
  - `PYTHONDONTWRITEBYTECODE=1 python3 scripts/agent-flow.py adopt --target /Users/shwoo/mydir/ENKI_WIKI --format json`: target clean, `project_profile_state=ready`, `safe_missing=0`, `manual_merge=1`, `risky_changed=1`, `candidate_paths=0`, no stop reasons.
  - `PYTHONDONTWRITEBYTECODE=1 python3 /Users/shwoo/mydir/ENKI_WIKI/scripts/verify-skeleton.py --root /Users/shwoo/mydir/ENKI_WIKI`: passed.
  - `PYTHONDONTWRITEBYTECODE=1 python3 /Users/shwoo/mydir/ENKI_WIKI/scripts/ownership-lock.py --root /Users/shwoo/mydir/ENKI_WIKI check`: passed with classification_drift=0, lock_addition=0, lock_removal=0.
  - `PYTHONDONTWRITEBYTECODE=1 python3 /Users/shwoo/mydir/ENKI_WIKI/scripts/resume-readiness.py --root /Users/shwoo/mydir/ENKI_WIKI --strict --format json`: passed with ERROR 0, WARN 0.
  - `PYTHONDONTWRITEBYTECODE=1 python3 /Users/shwoo/mydir/ENKI_WIKI/scripts/quality-gate.py --root /Users/shwoo/mydir/ENKI_WIKI --tier stable --skip-tests --skip-node --format json`: passed with OK 34, SKIP 1, WARN 2.

## Final Adoption Intake

Final AI_architecture intake:

```text
target_git_clean=true
project_profile_state=ready
safe_missing=0
manual_merge=1
risky_changed=1
candidate_paths=0
recommendation=needs_review
```

Remaining review items are intentional:

- `.github/workflows/ci.yml`: preserve ENKI Node CI.
- `config/ownership.yaml`: preserve ENKI project overrides; never replace wholesale.

## Residual Risk / Non-Blocking Follow-Ups

- ENKI target license signal remains unknown because there is no target `LICENSE*`/`COPYING*` file. This is a legal/project metadata decision and was not invented during migration.
- Reference hygiene WARNs remain for `opencode` and `paperclip` candidate cards.
- Full ENKI Node/Docker app validation without `--skip-node` is outside this operating OS migration slice.

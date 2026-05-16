# 0025 ENKI Ownership Classification Report

## Summary

ENKI_WIKI is still in read-only migration mode. No ENKI target files were written in this pass.

The 0024 adoption intake stop condition is ownership-related:

- target git clean: yes
- adoption recommendation: `stop`
- ownership status: `draft`
- analyzed paths: 957
- candidate paths before classifier fix: 263
- candidate paths after non-ASCII path fix: 264
- stop threshold: 20

The extra candidate is the root file `주제`, which was previously surfaced as a quoted git path. `scripts/lib_ownership.py` now runs `git -c core.quotePath=false ls-files ...` so non-ASCII paths are collected as real paths.

## Proposed Project-Owned Groups

These groups are proposed as ENKI-owned because they are application code, deployment/runtime operations, project documentation, project tests, or target-local customization state.

```yaml
project_overrides:
  rules:
    - pattern: .dockerignore
      owner: project_owned
    - pattern: .gitignore
      owner: project_owned
    - pattern: Makefile
      owner: project_owned
    - pattern: README.md
      owner: project_owned
    - pattern: apps/web/**
      owner: project_owned
    - pattern: apps/wiki/**
      owner: project_owned
    - pattern: deploy/**
      owner: project_owned
    - pattern: docker-compose.yaml
      owner: project_owned
    - pattern: docs/**
      owner: project_owned
    - pattern: docs/CODEMAPS/**
      owner: project_owned
    - pattern: docs/decisions/**
      owner: project_owned
    - pattern: docs/handoff/**
      owner: project_owned
    - pattern: docs/releases/**
      owner: project_owned
    - pattern: docs/runbooks/**
      owner: project_owned
    - pattern: infra/**
      owner: project_owned
    - pattern: infra/nginx/**
      owner: project_owned
    - pattern: package-lock.json
      owner: project_owned
    - pattern: package.json
      owner: project_owned
    - pattern: pnpm-workspace.yaml
      owner: project_owned
    - pattern: references.yaml
      owner: project_owned
    - pattern: rules/**
      owner: project_owned
    - pattern: rules/common/**
      owner: project_owned
    - pattern: scripts/**
      owner: project_owned
    - pattern: scripts/seed/**
      owner: project_owned
    - pattern: tests/**
      owner: project_owned
    - pattern: tests/smoke/**
      owner: project_owned
    - pattern: 주제
      owner: project_owned
```

Guard note: this broad project-owned proposal does not override protected runtime/state files or system-locked AI_architecture paths. The v1 classifier applies protected and system_locked guards before project overrides.

## Temporary Simulation Result

Simulation method:

1. Copy `/Users/shwoo/mydir/ENKI_WIKI` to a temporary directory.
2. Write source `config/ownership.yaml` plus the proposed `project_overrides` into the temporary copy.
3. Run `ownership-lock.py --root <temp> write`.
4. Run `upgrade-from-skeleton.py --target <temp> --brief --profile stable --format json`.
5. Delete the temporary copy.

Result:

- ownership lock write: ok
- total classified paths in temp: 958
- unknown paths: 0

Remaining dry-run upgrade brief after proposed ownership:

- safe additions: 6
- manual reviews: 2
- risky system updates: 13
- protected skips: 37
- unchanged safe: 244

Safe additions:

- `docs/OWNERSHIP_MODEL.md`
- `docs/feature-status.yaml`
- `rules/common/communication-style.md`
- `scripts/lib_ownership.py`
- `scripts/ownership-initialize.py`
- `scripts/ownership-lock.py`

Manual reviews:

- `AGENTS.md`
- `config/ownership.yaml`

Risky system updates:

- `.github/workflows/ci.yml`
- `config/agent-team.yaml`
- `docs/AGENT_REGISTRY.md`
- `docs/RUNTIME_EVENT_SCHEMA.md`
- `docs/SKELETON_UPGRADE.md`
- `docs/WORKFLOW_CATALOG.md`
- `schemas/session-snapshot.schema.json`
- `scripts/agent-flow.py`
- `scripts/quality-gate.py`
- `scripts/resume-readiness.py`
- `scripts/task-closeout.py`
- `scripts/upgrade-from-skeleton.py`
- `scripts/verify-skeleton.py`

## Recommendation

The proposed ownership config is safe enough to present for approval, but it has not been written to ENKI.

Next approved target-write step:

1. Write ENKI `config/ownership.yaml` with source `system_defaults` plus the proposed `project_overrides`.
2. Run `python3 scripts/ownership-lock.py --root /Users/shwoo/mydir/ENKI_WIKI write`.
3. Re-run `python3 scripts/agent-flow.py adopt --target /Users/shwoo/mydir/ENKI_WIKI --format json`.
4. Continue only if ownership candidate stop is cleared.

Do not run `upgrade-from-skeleton.py --apply` or `--include-risky` in this slice.

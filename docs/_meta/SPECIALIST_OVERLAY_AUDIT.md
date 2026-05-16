# Specialist Overlay Audit

## Summary

Plan 0014 audited the current specialist registry and delegation surfaces before adding project-specific specialist overlays. The next implementation slice should extend the existing AgentBrief registry path, not create a parallel router or a second execution loop.

## Current Surfaces

`config/agent-team.yaml` is the canonical base team registry for public team roles and internal specialists. The current specialist entries are `build-error-resolver`, `security-reviewer`, `reference-reviewer`, `docs-sync-auditor`, and `closeout-validator`, each with `mission`, `write_policy`, `default_scope`, and optional `recommended_checks`.

`config/roles.yaml` is a separate model/primary-owner map for planner, implementer, researcher, verifier, and evaluator. It should not become the specialist overlay source; it controls model/runtime ownership, not task-specific delegation permissions.

`docs/AGENT_REGISTRY.md` explains the user-facing role model and names `config/agent-team.yaml` plus `scripts/agent-brief.py` as the specialist handoff path. It also states that specialists do not directly extend the public command surface.

`agents/*.md` are canonical generated-agent definitions for the broad team roles. `scripts/convert.py` copies these files into `.codex/agents/` and `.claude/agents/` with `.GENERATED_DO_NOT_EDIT` markers. Project-specific specialist overlays should stay runtime/config driven in 0015; generated agent exports can be considered later only if external usage shows they are needed.

## Brief Generation Path

`scripts/agent-brief.py` currently owns the specialist registry load and permission reduction logic.

- `load_team_registry` reads only the `specialists:` section of `config/agent-team.yaml`.
- Built-in `SPECIALISTS` provide fallback role names and default descriptions.
- `build_brief` rejects unknown roles, invalid configured write policies, requested write-policy broadening, parent-policy broadening, and empty effective scope after parent-scope intersection.
- Effective `write_policy` is the narrowest of configured, requested, and inherited policies.
- `default_scope` from the registry is used when the caller does not pass `--scope`.
- `recommended_checks` from the registry override role defaults, and `python ` prefixes are normalized to `python3 `.
- The emitted `Brief` does not currently include `role_source`; 0015 must add this once overlay lookup exists.

The current implementation already prevents direct write-policy broadening for one loaded role. 0015 must preserve that behavior when overlay data is present.

## Delegate Path

`scripts/incubating/agent-flow-delegate.py` is a preparation-only wrapper. It invokes `scripts/agent-brief.py --write --format json`, parses the written brief payload, and returns a handoff with `brief_path`, `role`, scopes, validation hints, and a workflow-aware completion command.

The delegate does not append AgentRun records and does not spawn subagents. Completion remains manual through `scripts/incubating/agent-run.py add`. 0018 should extend this delegate path if execution-loop work is reopened; it should not introduce a second delegate/execution stack.

## Generated Surfaces

`scripts/convert.py` regenerates `.codex/agents/` and `.claude/agents/` from canonical `agents/`, not from `config/agent-team.yaml`. The generated agent surfaces currently contain the broad roles only: `strategy-planner`, `codebase-explorer`, `implementation-worker`, and `independent-validator`.

0015 should not regenerate or mutate `.codex/agents/` or `.claude/agents/`. A future generated-export mechanism for project-specific specialists would need a separate decision because it changes personal/runtime surfaces and increases merge risk.

## 0015 Loader Constraints

The overlay loader should be additive-first and privilege-safe.

- Base registry remains `config/agent-team.yaml`.
- Project overlay file is optional and should be named `config/agent-team-overrides.yaml` unless implementation discovers a blocking conflict.
- A project overlay may add a new specialist.
- A project overlay may narrow an existing base specialist's `write_policy`.
- A project overlay may narrow an existing base specialist's `default_scope`.
- A project overlay must not broaden an existing base specialist's `write_policy`.
- A project overlay must not broaden an existing base specialist's `default_scope`.
- Briefs produced after 0015 must include `role_source: base|project`.
- Loader errors should be fail-loud for invalid policy values, unknown schema shapes, broadening attempts, and empty effective scope.

Scope narrowing should use the same "same or under parent" semantics already used by `intersect_scope`: a narrowed scope item must stay under at least one base scope item. The base scope `.` is broad, so narrowing from `.` to a project path is allowed; widening from `scripts/` to `.` is not.

## Future Hook Notes

0017 orchestration preview should extend existing goal-to-candidate scoring patterns in `scripts/agent-flow.py` and `scripts/catalog.yaml`. Do not build a parallel specialist router while `agent-flow start/research` already owns natural-language routing and candidate ranking concepts.

0018 execution loop should extend `scripts/incubating/agent-flow-delegate.py` and `scripts/incubating/agent-run.py`. Do not introduce a second execution loop that bypasses the existing brief and ledger contracts.

0016 specialist proposal/add, 0017 orchestration preview, and 0018 execution loop remain frozen until external usage signals justify reopening.

## Security Review

Sensitive assets are specialist permissions, write scopes, generated agent surfaces, and runtime ledgers. The safe default for 0015 is read/config lookup plus strict rejection of privilege broadening. No credentials, provider-specific SDK fields, generated code execution, or target-project writes are required for the overlay loader.

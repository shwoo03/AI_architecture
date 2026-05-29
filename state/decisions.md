# Decisions (append-only)

> 형식: `## YYYY-MM-DD HH:MM — <결정 요약>` 다음 줄에 근거.
> 절대 이전 결정을 수정/삭제하지 말 것. 번복은 새 항목으로 추가.

## {{INIT_TIMESTAMP}} — 골격 부트스트랩
- 사용 골격: v1.2.0
- 모드: codex-primary (v1)
- 향후 v2 전환 가능 (docs/role-migration.md)

## 2026-05-14 16:39 — 0006 stated goal achieved via housekeeping; delegate execution aborted on role-registry gap
- Plan 0006의 stated goal (smoke artifact policy 문서화 + 5개 brief 분류)은 operator housekeeping으로 달성.
- Delegate execution path는 `docs-sync-auditor` (read_only specialist) + `--write-policy write_with_confirmation` 조합에서 시스템이 정상적으로 broaden 거부 -> cycle abort.
- 우회하지 않음. 이건 1e 회귀가 아니라 role registry coverage gap의 첫 증거.

## 2026-05-14 16:39 — Write-heavy delegate cycle friction goal remains OPEN; deferred to post-0008
- 원래 0006의 메타 목표였던 "write-side friction 데이터 수집"은 미달성.
- 0007 (role registry audit, read-only) -> 0008 (최소 docs-write role 추가) 완료 후, 새 slice로 재시도 예정.
- 그 전에는 routing / validator-loop 등 상위 슬라이스 진행 금지(같은 gap에 다시 막힐 위험).

## 2026-05-14 16:39 — Aborted status enum deferred until governance-driven cycle abort 누적 2건 이상
- INDEX schema에 `aborted` status enum 도입은 데이터가 충분히 모일 때까지 보류.
- Trigger 정의: **governance/policy/schema constraint가 정상 작동해서 cycle을 중단시킨 사례**가 누적 2건 이상. 0006이 1건째.
- 카운트 안 되는 것: 단순 구현 실패, 환경 문제, race condition 발견, 사용자가 마음 바꿔서 중단한 경우.

## 2026-05-15 01:09 — AI_architecture repo 작업 freeze (외부 실사용 trigger 도래 시 resume)
- v1은 운영 OS 수준까지 완성, v2는 incubating 골격까지 완성. 최근 7-8 commit이 대부분 self-referential infra 작업이었고 실사용 데이터는 read-only audit 1건뿐.
- 0007 role registry audit은 정당한 plan이지만 "뭐라도 더 하자"의 편의 옵션이 될 위험이 큼. 외부 실데이터 없이 진행하면 또 한 라운드의 self-improvement loop.
- 외부 프로젝트 후보(ENKI_WIKI, 0-day, ctf-forge 등)는 있으나 현재 자연 발생한 active task는 없음. "외부 적용 실험"도 active task 없이 시작하면 인위적 dogfooding.
- 따라서 결정: 이 repo에 추가 commit 하지 않음. 다음에 진짜 외부 프로젝트 X에서 작업이 발생하면 그때 v1 stable overlay 시도하고, 그 사용 중 발견한 friction만 가져와서 resume.
- 0007 plan은 `plans/active/`에 보존되며 본문에 `Status: Deferred`로 표시. INDEX schema는 변경하지 않음.
- 이 freeze는 "포기"가 아니라 "외부 trigger 대기". resume 조건은 외부 프로젝트 X에서의 실 작업 발생.

## 2026-05-15 03:58 — Freeze exception accepted for ENKI_WIKI stable overlay migration
- External trigger condition is now satisfied: user requested applying the AI_architecture stable system to .
- Scope is limited to overlay release hardening required for deterministic stable migration, followed by stable safe-only application to ENKI_WIKI.
- Deferred v2 work remains frozen: 0007 role registry audit, routing, validator-loop, non-terminal status, and delegate improvements stay out of scope.

## 2026-05-15 04:02 — Correction: ENKI_WIKI freeze exception target path
- The previous ENKI_WIKI freeze-exception entry was affected by shell command substitution while writing handoff text and lost the literal target path in one bullet.
- Correct target path: ~/mydir/ENKI_WIKI.
- Scope remains unchanged: stable overlay release hardening plus safe-only application; deferred v2 slices remain frozen.

## 2026-05-16 21:05 — Freeze exception: v2 specialist overlay mechanism (0014+0015 only)
- The 2026-05-15 freeze remains valid: avoid self-improvement loops without external usage signals.
- The user explicitly requested a project-specific specialist environment that can be added when a project needs it; this is a new requirement and justifies a narrow exception.
- Exception scope is limited to 0014 specialist-overlay-audit and 0015 specialist-overlay-loader.
- 0016 specialist proposal/add, 0017 orchestration preview, and 0018 execution loop remain frozen until external usage signals show they are needed.
- 0015 schema lock: project overlays are additive-first. New project specialists are allowed; base specialist `write_policy` and `default_scope` may only narrow; broadening either is rejected; future briefs must record `role_source`.

## 2026-05-16 21:52 — Planning-only freeze exception: v2 specialist orchestration interfaces (0016-0018)
- The 2026-05-15 freeze remains valid. This exception does not reopen implementation work.
- Exception scope is limited to writing plan bodies for 0016 specialist-proposal-add, 0017 orchestration-preview, and 0018 execution-loop.
- Authoring order is fixed: 0016 defines the specialist proposal schema, 0017 references that schema as input and defines a `DelegationPlan` draft, and 0018 references the `DelegationPlan` as its execution-boundary input.
- Implementation remains out of scope: no changes to scripts, schemas, CLI behavior, routing behavior, delegate behavior, or generated agent behavior.
- Stop conditions: no new router, no new execution loop, no overlay permission broadening, no auto-spawn, and no plan body may prescribe concrete code-edit steps or mutate scripts/schemas/CLI behavior.
- 0017 and 0018 plan bodies must include an explicit `Interface Contract` section so future implementation cannot invent incompatible inputs or outputs.
- Resume conditions for implementation: an external project must record concrete specialist proposal/routing/execution blocker evidence in activity log or handoff, or the user must explicitly open a new implementation exception.

## 2026-05-16 22:17 — Implementation exception: on-demand specialist flow (0016-0018)
- The user explicitly opened `/goal 18` and requested implementation through 0018.
- Exception scope is limited to on-demand specialist proposal/add, orchestration preview, and approval-gated execution preparation through the existing `scripts/agent-flow.py` public entrypoint.
- The implementation must preserve 0015 additive-only overlay safety: project specialists may be added, base specialists may be narrowed, and permission broadening remains rejected by `agent-brief.py`.
- Execution remains approval-gated. `agent-flow specialist execute` may prepare existing incubating delegate handoffs only for an approved `DelegationPlan` with explicit `--confirm`; it must not auto-spawn agents or create a second execution loop.
- Generated `.codex/` and `.claude/` agent surfaces remain out of scope.

## 2026-05-16 23:20 — Implementation exception: closeout-validator loop extension (0021)
- The user explicitly requested implementing 0021 immediately after 0020 instead of waiting for the preferred 20+ real-use evidence threshold.
- Exception scope is limited to extending the existing `closeout-validator` and `runtime/agent-runs.jsonl` append-only ledger with validator verdict records.
- The implementation must not create a new validator agent, new execution loop, automatic specialist spawn, automatic specialist selection, or stable promotion.
- Existing AgentRun records remain immutable. New status values and validator metadata are additive-only and apply only to newly appended records.

## 2026-05-16 23:55 — Implementation exception: spawn-ready packet (0022)
- The user explicitly requested implementing 0022 after 0021.
- Exception scope is limited to creating harness-agnostic spawn-ready packet artifacts from approved and confirmed `DelegationPlan` records.
- The implementation may reuse existing delegate handoff generation to populate packet units, but must not spawn agents or create a second execution loop.
- Packets must remain adapter-neutral and must mark auto-spawn, auto-chain, and recursive delegation as disallowed.

## 2026-05-21 15:35 — Reference card carrier round before security gate implementation
- The user explicitly directed that this round must not jump straight to invisible-character/security gate implementation.
- Scope is limited to carrier integrity for `everything-claude-code`, `paperclip`, and `opencode` candidate cards plus minimal proposal lifecycle support needed for future split/supersede dry-runs.
- Candidate cards should rely on checked revision and source anchors, not clone path alone. Workspace-local clone paths remain useful but are not portable trace.
- ECC refresh is scoped to `scripts/ci/` security/validation surface only; hooks, skills, commands, MCP, memory, install, and harness-adapter surfaces remain unchecked in this round.
- Paperclip governance/runtime adoption is deferred until concrete agent-team budget, approval, or recovery blocker evidence appears.
- OpenCode follow-up for read-only CLI smoke and LSP/diagnostic integration stays separate from the ECC Unicode/security provenance proposal.

## 2026-05-24 23:19 — Reference registry follows actual sibling clone set
- User requested all references be brought up to date, so the refresh target is the actual Git clone set under `../AI_architecture_references`, not only the 7 entries that happened to be in `references.yaml`.
- `llm_wiki` already had a candidate card and a sibling clone, so it is recorded in `references.yaml` with the same concept-only boundary instead of remaining an unregistered local reference.
- This refresh only fast-forwarded external clones and updated registry metadata. It does not adopt or copy external source into the skeleton.

## 2026-05-27 17:38 — Explicit plan_id trace for completion evidence
- Completion evidence may optionally record `plan_id` when a closeout is tied to an explicit plan.
- `plan_id` is an id such as `0033-plan-id-evidence-trace`, not a path, and is never inferred from goal text.
- Supplied ids must resolve to `plans/active/<id>.md` or `plans/done/<id>.md`; `plans/failed/<id>.md` is not accepted for completion evidence.
- The field remains optional to preserve existing ad hoc closeout behavior and avoid turning the skeleton into a query engine or product runtime.

## 2026-05-27 18:44 — Real Claude is strategy/critique only
- Real Claude may participate in Codex-Claude dialogue ledgers only as a strategy and critique voice.
- Real Claude must not use subagents, spawn agents, or record delegation/subagent fields; this preserves Claude session budget and avoids hidden secondary execution.
- `from: claude` requires `provider=claude_cli`. If Claude is unavailable, the substitute must be recorded as `from: claude-fallback-critic` with `provider=fallback_subagent`.
- Fallback subagents are allowed only as labeled substitute critics; they do not grant real Claude permission to delegate.

## 2026-05-27 19:14 — Delegation preflight strengthens the skeleton boundary
- Static DelegationPlan preflight and parent permission inheritance are accepted as skeleton-strengthening safeguards.
- `specialist execute` and `specialist packet` must fail before writing handoff artifacts if the approved plan has unknown or duplicate roles, missing per-role scope/policy, repo-escaping scope, scope/policy broadening, or unsupported DAG/auto-spawn/recursive-delegation fields.
- Source-anchor strict mode remains deferred to reference adoption/proposal/copy/promotion workflows only. Generated/plugin SSOT remains separate validators plus possible reporting, not a merged validator feature.

## 2026-05-27 19:28 — Source-anchor strict mode is opt-in, not global closeout
- Source-anchor strict checks are accepted only for reference adoption, reference proposals, copied-source ledger checks, and skill lifecycle promotion/demotion proposals.
- `--strict-source-anchor` must remain opt-in. It should not be wired into default `verify-skeleton`, stable `quality-gate`, or normal closeout until existing candidate cards have concrete source anchors.
- Strict failures on legacy `local-reference`, `external-reference`, `not checked`, or missing candidate/proposal links are backlog signals, not evidence that the skeleton is unhealthy.

## 2026-05-29 12:05 — Subagent debate replaces Claude automatic dialogue
- The 2026-05-27 Claude strategy/critic dialogue policy is superseded for future planning debates.
- Critical planning debate now defaults to Codex as orchestrator plus scoped `subagent-*` critics/researchers/verifiers.
- Claude is not an automatic participant, Claude session expiry is not a fallback trigger, and `runtime/dialogues/*.jsonl` no longer accepts `from: claude` or `provider: claude_cli`.
- Repository scripts only record debate ledgers; actual subagent spawning remains a surrounding harness responsibility.
- Convergence requires Codex plus at least one subagent readiness and no unresolved block critiques.

## 2026-05-29 12:18 — Goal prompt means Codex CLI /goal prompt
- When the user asks for a `goal 프롬프트`, the agent must interpret it as a Codex CLI `/goal` prompt request.
- The returned `/goal` prompt must be 4000 characters or fewer.
- If the useful content would exceed 4000 characters, the agent should document details separately and return a short `/goal` prompt that points to that document.
- `scripts/goal-prompt-check.py` is the local helper for validating the character limit.

## 2026-05-29 13:05 — Skeleton upgrades are release-manifest based
- Existing projects should not be byte-for-byte overwritten to match the current skeleton.
- Repeatable upgrades use release id, source commit, and channel from a generated release manifest.
- `stable` is the default target-project channel; preview/edge can surface incubating or experimental items but remain opt-in review surfaces.
- Safe-only apply records `skeleton_release_applied` with applied paths and manual review paths in install-state; manual/risky paths remain intentional preserve candidates until approved path by path.

## 2026-05-29 15:34 — Component manifests remain coarse and audits stay read-only
- Component-level install/diff data is accepted as an upgrade review aid, not as a package manager or auto-selector.
- Generated artifact policy belongs in the release/component manifest so target upgrades can see canonical source and regeneration commands before editing generated surfaces.
- Skills/agents bloat detection is a read-only audit. It may report duplicate, stale generated, deprecated, missing-source, and orphan candidate signals, but cleanup still requires a separate explicit plan.

## 2026-05-29 17:13 — Boundary cleanup keeps visibility without automatic expansion
- Stable features are split into `stable_role=core` and `stable_role=advisory`; advisory tools remain safe to ship but should be treated as nonblocking diagnostics.
- `delivery=overlay` is the normal transplant path, `delivery=frozen_optional` keeps v2/incubating runtime visible without stable overlay adoption, and `delivery=decision_only` keeps adapter decisions visible without making them apply targets.
- Install profile `components` must stay aligned with release/upgrade components. Project types such as `cli`, `webapp`, `research`, and `private-mirror` are `flavors`, not components.
- Canonical sources are `agents/`, `skills/*`, `rules/`, `mcp/servers.yaml`, and `AGENTS.md`; `.codex/`, `.claude/`, `.mcp.json`, and `CLAUDE.md` are generated surfaces.

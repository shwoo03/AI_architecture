# Progress

## 현재 마일스톤
External trigger active: ENKI_WIKI stable overlay migration (2026-05-15)

## 완료된 작업
- 골격 부트스트랩
- LSP 진단과 source-scoped recovery
- AI-assisted upgrade brief, resume-safe checkpoint, knowledge gap check
- P0 안정화: no-record 무변경, read-only 라우팅, parity brief, WARN detail, recovery packet
- 운영 진단 개선: quality-gate explain, proposal lifecycle checker, progress-handoff lint
- reference inventory 정리: tracked repo, candidate card, proposal 상태 대조
- closeout hygiene: codemap 자동 갱신, repo-bounded pycache cleanup
- feature maturity manifest: stable/incubating/experimental tier source of truth
- tier-aware quality gate: stable default와 all-tier v2 검증 분리
- profile-aware upgrade brief: stable/incubating/all overlay 판단 지원
- v2 문서 경계: roadmap, design doc, SDK adapter ADR, JSONL source-of-truth ADR
- Phase 1a AgentBrief: Plan child artifact boundary, `--write` creator, canonical fields, manual-smoke brief artifact
- Phase 1a AgentRun draft: ledger required fields documented with `tier` and `ext`
- Phase 1b AgentBrief cleanup: true alias 제거, `policy_inheritance` 격리, `python3` validation hint 통일
- Phase 1b AgentRun writer: `scripts/incubating/agent-run.py add`로 manual smoke record append
- Phase 1b AgentRun reader: `dump --tail 5 --format json`으로 최근 ledger record 확인
- Phase 1b manual smoke: canonical brief 1건 생성 후 `runtime/agent-runs.jsonl`에 incubating run 1건 기록
- Phase 1c controlled migration: pre-v2 AgentRun 2건을 frozen `runtime/agent-runs.legacy.jsonl`로 분리
- Phase 1c read-side aggregation: `agent-run.py list/check/summary` 추가
- Phase 1c all-tier gate: `quality-gate --tier all`에서 incubating AgentRun schema check 연결
- Phase 1d-1 changed_paths validation: AgentRun add strict path validation, historical WARN check, all-tier WARN handling
- Phase 1d-2 retry/idempotency: explicit `retry_of`, same-brief live-ledger lookup, duplicate run id check, retry severity validation
- Phase 1d-3 aggregation summary: retry-aware `summary` fields for retried count, chain heads, unresolved failures
- Phase 1e incubating delegate entrypoint: `agent-brief.py`를 재사용해 brief artifact와 실행 가능한 handoff JSON을 생성
- Phase 1e-followup workflow-aware completion command: read-only workflow에서는 `--changed-path` placeholder를 생략하고 write workflow에서는 유지
- 0006 delegate cycle aborted on role-registry gap; AgentBrief artifact policy documented via operator housekeeping. Write-heavy friction goal remains OPEN, deferred to post-0008.
- 2026-05-15 freeze decision: 추가 슬라이스(0007 포함) 진행 보류. 외부 프로젝트 X 실 작업 발생 시 v1 stable overlay 시도 후 resume.
- 2026-05-15 ENKI_WIKI external trigger: stable overlay release path hardened, with migration limited to deterministic safe-only application.
- Ownership-aware upgrade v1 Slice 2: standalone classifier library and synthetic fixture tests implemented; closeout freshness cleanup in progress.
- Ownership-aware upgrade v1 Slice 2.5: skeleton self-classification lock generated; ownership-lock write/check and self-classification tests pass.
- Ownership-aware upgrade v1 Slice 3: verify-skeleton ownership gate and upgrade-from-skeleton ownership-aware planning implemented, validated, and closeout recorded.
- Ownership-aware upgrade v1 Slice 3.5: self-hygiene completed, OWNERSHIP_MODEL locked, ownership-initialize report tool implemented, tests pass, stable quality gate is WARN 0, closeout recorded, and plan moved to done.
- Slice 4 ENKI_WIKI initialize dry-run started with plan 0013. Read-only `ownership-initialize.py --target ~/mydir/ENKI_WIKI --format json` completed with status=draft, analyzed_paths=957, candidate_paths=261, and stop condition hit because candidates exceed 20. No ENKI target files were written.
- Slice 4 handoff/activity-log timestamp sync recorded after the initialize stop condition.
- Slice 4 first-milestone closeout recorded at 2026-05-15T12:36:45Z; next action remains manual review of the 261-path initialize draft before any ENKI target write.
- 2026-05-17 0013 ENKI ownership initialize dry-run marked done. The milestone completed read-only with normal stop on `candidate_paths=261`; follow-up classification remains a separate human-reviewed slice.
- 2026-05-16 v2 specialist overlay exception recorded for 0014+0015 only; plan 0014 specialist-overlay-audit is active, while 0016-0018 remain frozen until external usage signals appear.
- 2026-05-16 handoff/activity-log/session-snapshot refreshed after 0014 setup closeout.
- 2026-05-16 plan 0014 specialist overlay audit executed. `docs/_meta/SPECIALIST_OVERLAY_AUDIT.md` records current registry, brief, delegate, generated-agent, future 0017/0018 hook, and privilege-safety findings.
- 2026-05-16 plan 0014 moved to done and plan 0015 specialist-overlay-loader prepared as the active additive-only loader implementation slice.
- 2026-05-16 closeout for 0014 execution and 0015 preparation recorded successfully; validate-plans, verify-skeleton, ownership-lock check, stable quality gate, all-tier quality gate, and agent-flow closeout passed.
- 2026-05-16 0015 implementation prep recorded in `runtime/validation/0015-specialist-overlay-loader-prep.md`: exact code path, merge semantics, tests, docs, and security boundary are fixed before behavior changes.
- 2026-05-16 0015 implementation prep closeout recorded and handoff/session snapshot refreshed.
- 2026-05-16 0015 specialist overlay loader implemented: `agent-brief.py` reads optional `config/agent-team-overrides.yaml`, supports overlay-only project specialists, emits `role_source`, allows base narrowing, rejects base broadening, and delegate handoff carries role provenance.
- 2026-05-16 0015 specialist overlay loader closeout recorded successfully and plan moved to done.
- 2026-05-16 0016-0018 planning-only exception recorded. Active plan bodies now define the specialist proposal schema, orchestration preview `DelegationPlan` interface, and execution-loop boundary without changing scripts, schemas, CLI behavior, routing behavior, delegate behavior, or generated agent surfaces.
- 2026-05-16 0016-0018 planning-only handoff and session snapshot refreshed after closeout.
- 2026-05-16 specialist-agent usage best-practices prep completed. `docs/_meta/SPECIALIST_AGENT_USAGE_BEST_PRACTICES.md` now records source-grounded on-demand trigger/anti-trigger, orchestration, contract, safety, and implementation-readiness rules; 0016-0018 plans reference those rules.
- 2026-05-16 0016-0018 specialist flow implemented end to end: `agent-flow specialist propose/review/approve/reject`, preview `DelegationPlan`, and approval-gated execute now work through the existing delegate path without auto-spawning agents.
- 2026-05-16 0016-0018 moved to done; focused specialist tests, `tests.test_agent_flow`, combined operational tests, validate-plans, ownership-lock, verify-skeleton, stable/all quality gates, and closeout passed.
- 2026-05-16 0016-0018 implementation handoff/readiness timestamp sync refreshed after closeout and final strict-readiness pass.
- 2026-05-16 0019 session recall hardening implemented: session handoff is indexed, FTS cache text is redacted at insert time, cache index_version invalidates stale unredacted DBs, `agent-flow recall` wraps session recall search, and the SQLite cache is ignored as derived runtime data.
- 2026-05-16 0019 moved to done; focused recall tests, `tests.test_runtime`, `tests.test_agent_flow`, validate-plans, ownership-lock, verify-skeleton, stable/all quality gates, and closeout passed.
- 2026-05-16 0019 handoff/session snapshot refreshed after closeout.
- 2026-05-16 0020 specialist usage evidence ledger implemented: specialist preview/approve/reject/plan-approve/execute now append redacted advisory-only evidence records to `runtime/specialist-usage.jsonl` without changing scoring, auto-selection, validator verdicts, or spawn packet behavior.
- 2026-05-16 0020 moved to done; `tests.test_agent_flow`, validate-plans, ownership-lock, verify-skeleton, stable/all quality gates, and closeout passed.
- 2026-05-16 0021 closeout-validator loop extension implemented by explicit user exception: `agent-run.py validate` appends `closeout-validator` verdict records with `ext.validator`, additive statuses (`paused`, `aborted`, `partial`), and no mutation of target AgentRun records.
- 2026-05-16 0021 moved to done; focused validator tests, `tests.test_validation`, agent-run check, validate-plans, ownership-lock, verify-skeleton, stable/all quality gates, and closeout passed.
- 2026-05-16 0022 spawn-ready packet implemented by explicit user exception: `agent-flow specialist packet --plan <path> --confirm` writes harness-agnostic `runtime/spawn-packets/*.json` artifacts from approved `DelegationPlan` records and existing delegate handoffs.
- 2026-05-16 0022 moved to done; packet tests, `tests.test_agent_flow`, validate-plans, ownership-lock, generate-codemaps, verify-skeleton, stable/all quality gates, and closeout passed. Packet generation remains approval-gated and does not spawn agents, auto-chain roles, or allow recursive delegation.
- 2026-05-17 0023 diagnostic UX implemented: `agent-flow doctor` now aggregates `skeleton-doctor`, `verify-skeleton`, `ownership-lock check`, `resume-readiness --strict`, and tier-aware `quality-gate` into one read-only OK/WARN/FAIL report.
- 2026-05-17 0023 moved to done; focused doctor tests, `tests.test_agent_flow`, `agent-flow doctor` stable/all real runs, validate-plans, ownership-lock, generate-codemaps, verify-skeleton, all-tier quality gate, and closeout passed.

## 다음 작업
- Use `python3 scripts/agent-flow.py doctor --format json` as the first single-command diagnostic before deeper manual checks. Use `--tier all` for incubating coverage and `--with-tests` for slower full validation.
- Use the new specialist flow only on demand: propose a project specialist when a concrete blocker/trigger exists, approve it before overlay application, preview delegation first, and execute only approved plans with explicit confirmation.
- Use `python3 scripts/agent-flow.py recall "<query>" --format json` for local session recall; source-of-truth remains Markdown/JSONL, and `runtime/session-recall.sqlite` is rebuildable cache only.
- Use `python3 scripts/incubating/agent-run.py validate --brief <closeout-validator-brief> --target-run-id <run-id> --verdict pass|warn|fail|needs_human --reason "<reason>" --format json` to append independent validator verdict evidence after specialist work.
- Use `python3 scripts/agent-flow.py specialist packet --plan <approved-delegation-plan.json> --confirm --format json` only when the user explicitly wants a spawn-ready handoff. The packet is an artifact for Codex/Claude/opencode/manual harnesses; the repo itself still does not spawn subagents.
- Slice 4 ENKI remains blocked on manual review of the 261-path initialize draft before any target write.

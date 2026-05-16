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
- 2026-05-16 v2 specialist overlay exception recorded for 0014+0015 only; plan 0014 specialist-overlay-audit is active, while 0016-0018 remain frozen until external usage signals appear.
- 2026-05-16 handoff/activity-log/session-snapshot refreshed after 0014 setup closeout.
- 2026-05-16 plan 0014 specialist overlay audit executed. `docs/_meta/SPECIALIST_OVERLAY_AUDIT.md` records current registry, brief, delegate, generated-agent, future 0017/0018 hook, and privilege-safety findings.
- 2026-05-16 plan 0014 moved to done and plan 0015 specialist-overlay-loader prepared as the active additive-only loader implementation slice.
- 2026-05-16 closeout for 0014 execution and 0015 preparation recorded successfully; validate-plans, verify-skeleton, ownership-lock check, stable quality gate, all-tier quality gate, and agent-flow closeout passed.
- 2026-05-16 0015 implementation prep recorded in `runtime/validation/0015-specialist-overlay-loader-prep.md`: exact code path, merge semantics, tests, docs, and security boundary are fixed before behavior changes.
- 2026-05-16 0015 implementation prep closeout recorded and handoff/session snapshot refreshed.
- 2026-05-16 0015 specialist overlay loader implemented: `agent-brief.py` reads optional `config/agent-team-overrides.yaml`, supports overlay-only project specialists, emits `role_source`, allows base narrowing, rejects base broadening, and delegate handoff carries role provenance.
- 2026-05-16 0015 specialist overlay loader closeout recorded successfully and plan moved to done.

## 다음 작업
- Keep 0016 specialist proposal/add, 0017 orchestration preview, and 0018 execution loop frozen until external usage evidence appears.
- Slice 4 ENKI remains blocked on manual review of the 261-path initialize draft before any target write.

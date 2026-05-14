# Progress

## 현재 마일스톤
V2 incubating runtime Phase 1e complete

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

## 다음 작업
- Delegate 실데이터 흐름 관찰 후 routing 또는 validator-loop 슬라이스 선택

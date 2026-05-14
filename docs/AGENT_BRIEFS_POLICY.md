# AgentBrief Artifact Policy

## 한 문장 정의

`runtime/agent-briefs/` 디렉터리 안의 brief 파일을 어떤 조건에서 보존, 분류, 삭제할지 정하는 운영 정책이다.

## 무엇을 하는가

이 문서는 AgentBrief artifact가 실제 delegate cycle evidence인지, milestone smoke인지, 검증 중 생긴 pollution인지 구분한다. 분류 결과는 삭제 가능 여부와 커밋 대상 여부를 판단하는 기준이 된다.

## 왜 필요한가

Phase 1e-followup commit `7ba7a7d` 이후 검증 명령이 brief 파일을 남기는 friction이 관찰되었다. 같은 `runtime/agent-briefs/` 디렉터리에 실 cycle 산출물과 검증 pollution이 섞이면 다음 에이전트가 어떤 파일을 evidence로 봐야 하는지 헷갈린다. 이 정책은 brief를 삭제하기 전에 ledger와 handoff 근거를 확인하게 만들어 governance를 우회하지 않게 한다.

## 3-tier 분류 기준

Tier 1은 ledger-anchored evidence다. `runtime/agent-runs.jsonl` 또는 frozen archive인 `runtime/agent-runs.legacy.jsonl`에서 `brief_id`나 `runtime/agent-briefs/<filename>` 참조가 발견되면 Tier 1로 본다. Tier 1 파일은 절대 삭제, 이동, 이름 변경하지 않는다.

Tier 2는 milestone smoke다. matching AgentRun은 없지만 `state/progress.md`, `plans/done/*.md`, commit message, closeout evidence 중 하나에서 해당 phase나 brief 식별자가 확인되면 의도된 feature evidence로 보존한다.

Tier 3은 validation pollution이다. ledger 매칭도 없고 milestone 참조도 없으며, 검증 명령의 부산물로 생성된 것으로 판단되는 파일이다. Tier 3도 추정만으로 확정하지 않는다. 판단 우선순위는 ledger 매칭, 문서/커밋 참조, 추정 금지 순서다. 의심스러우면 Tier 2로 보존한다.

## 삭제 절차

삭제 전에는 ledger 또는 handoff에서 삭제 사유를 확인한다. 삭제를 진행할 때는 삭제 대상 brief id와 사유를 `runtime/activity-log.jsonl`, `state/decisions.md`, 또는 해당 cycle의 AgentRun `result_summary` 중 하나에 남긴다. evidence-backed record인 Tier 1은 삭제 절차 대상이 아니다.

Tier 2를 정리해야 하는 경우에도 먼저 별도 plan으로 승격한다. milestone smoke는 과거 phase의 검증 근거이므로 일반 cleanup처럼 다루지 않는다.

## 현재 분류 결과 (작성 시점 evidence)

- `2026-05-13-phase-1a-agent-brief-docs-sync-auditor-01`: Tier 2. `state/progress.md`의 Phase 1a AgentBrief 완료 항목과 Phase 1a closeout evidence가 `runtime/agent-briefs` 변경을 기록한다.
- `2026-05-13-phase-1a-agent-brief-docs-sync-auditor-02`: Tier 2. 같은 Phase 1a milestone smoke 계열이며 `state/progress.md`와 Phase 1a closeout evidence가 근거다.
- `2026-05-13-phase-1b-agent-run-docs-sync-auditor-01`: Tier 1. `runtime/agent-runs.jsonl`의 `run-2026-05-13-2026-05-13-phase-1b-agent-run-docs-sync-auditor-01-01`가 brief ref를 포함한다.
- `2026-05-14-adhoc-docs-sync-auditor-01`: Tier 2. commit `72c97f9`가 Phase 1e delegate entrypoint smoke artifact로 해당 파일을 포함한다.
- `2026-05-14-adhoc-docs-sync-auditor-02`: Tier 1. `runtime/agent-runs.jsonl`의 `run-2026-05-14-adhoc-docs-sync-auditor-02-01`가 brief ref를 포함한다.

작성 시점에 Tier 3 후보는 없다.

## 향후 검토

- delegate에 `--dry-run` 또는 `--no-write` 옵션 도입은 별도 슬라이스 후보로 둔다.
- `runtime/agent-briefs/smoke/` 같은 서브디렉터리 분리도 데이터가 더 쌓인 뒤 별도 슬라이스에서 결정한다.
- write-heavy delegate cycle friction 데이터 수집은 role registry audit과 최소 docs/governance write role 추가 이후 재시도한다.

## 구현 연결 정보

- 디렉터리: `runtime/agent-briefs/`
- 생성 경로: `scripts/incubating/agent-flow-delegate.py` -> `scripts/agent-brief.py --write`
- 닫는 경로: `scripts/incubating/agent-run.py add --brief ...`
- 관련 결정: `state/decisions.md`

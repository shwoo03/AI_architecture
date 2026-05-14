# 0002-phase-1d-2-retry-idempotency

## Summary

Phase 1d-1에서 `changed_paths` 무결성을 굳혔다. 1d-2는 AgentRun ledger의 retry/idempotency 의미를 canonical field로 박는다. 같은 `brief_id`로 두 번째 run이 생기는 것 자체는 retry일 수도, 새 작업일 수도 있다. 그 의미를 자동 추론으로 두면 reader가 무너지므로, 명시적인 `retry_of` top-level optional field와 `--retry-of` 플래그를 도입한다. retry resolution은 live ledger만 본다(legacy archive 제외). target status, brief 동일성, ordering 같은 invariant를 add는 strict, check는 1d-1과 같은 패턴(malformed=ERROR, drift=WARN)으로 검증한다.

## Assumptions

- `runtime/agent-runs.jsonl`은 v2-only live ledger (1c 확정), `runtime/agent-runs.legacy.jsonl`은 frozen (retry resolution 대상 아님).
- 1d-1에서 도입한 `READ_ONLY_WORKFLOWS`, `record_findings`의 WARN/ERROR 분기, `ok` 판정 분기를 재사용한다.
- `next_run_id`의 자동 증분(`run-<brief_id>-<seq>`)은 그대로 유지한다. retry는 이 증분과 직교하는 별도 선언.
- `retry_of`는 optional. 기존 1c/1d-1 entry는 이 필드가 없는 채로 호환된다.
- status는 append-only로 한 번 기록되면 안 바뀐다 → target status 위반은 drift가 아니라 malformed.

## Out of Scope

- Aggregation summary(failed/retried/stale counts) — 1d-3.
- Ledger rotation/archive 자동화 — 별도 슬라이스.
- delegation entrypoint, agent-flow surface 변경.
- legacy ledger 데이터 보정.
- `agent_run_id` 형식 변경(자동 증분 유지).
- multi-level retry chain을 storage에 명시적으로 저장하는 것(reader가 traversal로 복원).

## 핵심 정책 (구현 기준)

```text
retry relationship  = top-level optional retry_of (string, agent_run_id 형식)
retry declaration   = explicit --retry-of only (자동 추론 금지)
retry scope         = same brief_id only
retry target        = earlier run in live ledger only
retry target status = failed | blocked only
retry chain         = reader reconstructs by following retry_of (단일 단계만 저장)

lookup boundary:
  - runtime/agent-runs.jsonl (live) ONLY
  - runtime/agent-runs.legacy.jsonl is frozen, excluded
```

### add invariants (모두 ERROR)

- `--retry-of`가 비어 있으면 retry로 간주하지 않고 정상 append.
- `--retry-of`가 자기 자신을 가리키면 거부(`agent_run_id`가 아직 할당 안 됐어도 lookup 단계에서 차단).
- target이 live ledger에 없으면 거부.
- target의 `brief_id`가 현재 run의 `brief_id`와 다르면 거부.
- target의 `status`가 `failed` 또는 `blocked`가 아니면 거부.
- 자동 증분으로 만든 새 `agent_run_id`가 기존과 충돌하면 거부(race condition 대비; `runtime_lock` 아래에서 records 재독해 확인).

### check invariants

| 위반 | severity | check 이름 |
|---|---|---|
| `retry_of`가 자기 자신 | ERROR | `retry_self_reference` |
| target과 `brief_id` 불일치 | ERROR | `retry_brief_mismatch` |
| 중복 `agent_run_id` | ERROR | `agent_run_id_duplicate` |
| target 비존재 (drift) | WARN | `retry_target_missing` |
| `retry_of`가 later/equal line 가리킴 | ERROR | `retry_ordering` |
| target status ∉ {failed, blocked} | ERROR | `retry_target_status` |

`ok` 판정은 ERROR만 본다(1d-1 분기 재사용).

## Implementation Steps

1. `scripts/incubating/agent-run.py`
   - `REQUIRED_FIELDS`는 그대로 두고, `OPTIONAL_FIELDS = ("retry_of",)` 상수 추가. `retry_of`가 record에 있을 때만 형식/의미 검증.
   - `RETRYABLE_STATUSES = frozenset({"failed", "blocked"})` 상수 추가.
   - `argparse`에 `--retry-of <agent_run_id>` 옵션 추가. 기본값 `None`.
   - `build_record`:
     - records 읽은 뒤 `args.retry_of`가 truthy이면 target lookup. live ledger에서 `agent_run_id == args.retry_of`인 record를 찾는다.
     - 없으면 `ValueError("retry_of target not found in live ledger: ...")`.
     - target `brief_id`가 현재 brief의 `brief_id`와 다르면 `ValueError("retry_of target brief mismatch: ...")`.
     - target `status` ∉ RETRYABLE_STATUSES이면 `ValueError("retry_of target status must be failed or blocked, got ...")`.
     - 새 `agent_run_id`와 target이 동일하면 `ValueError("retry_of cannot reference self")`.
     - 통과하면 record에 `retry_of: <target_agent_run_id>` 추가.
   - `add_record`는 `runtime_lock` 안에서 records 재독해 → next_run_id 재계산 → 중복 발생 시 거부(race condition 방어).
   - `record_findings` 확장:
     - record에 `retry_of`가 있을 때만 검증.
     - 위 check severity 표 6개 분기. WARN과 ERROR를 정확히 매핑.
     - 중복 `agent_run_id` 검사는 records 전체를 한 번 스캔해 `seen` set으로 처리(개별 record 단위 함수에서 처리하기 위해 `check_records`에서 set을 만들어 helper로 전달).
   - `next_run_id`는 그대로 유지. 변경 없음.
2. `docs/RUNTIME_EVENT_SCHEMA.md` AgentRun v2 섹션 보강
   - `retry_of` field 의미와 형식, optional 여부 명시.
   - 위 "핵심 정책" 7줄을 그대로 박는다.
   - check severity 표 박는다.
   - "retry resolution은 live ledger만 본다, legacy archive는 제외" 한 문장 명시.
   - 1d-3 자리 한 줄 표기(스펙 비워둠).
3. `tests/test_validation.py`에 회귀 테스트 추가 (대략 13건)
   - **add 경로 (ERROR)**:
     - self-reference (현재 `next_run_id`와 같은 id를 `--retry-of`로 줌) 거부.
     - target이 ledger에 없을 때 거부.
     - target과 brief_id 불일치 거부 (다른 brief로 만든 retry target 사용).
     - target status가 `completed`일 때 거부.
     - target status가 `failed`일 때 성공.
     - target status가 `blocked`일 때 성공.
   - **add 경로 (정상)**:
     - `--retry-of` 없이 정상 append(기존 동작 회귀 확인).
     - 유효한 retry 1건 append 후 `retry_of` 필드가 정확히 기록됨.
     - read-only workflow(`manual_smoke`)에서도 `--retry-of`가 정상 동작(read-only와 retry는 직교).
   - **check 경로**:
     - 정상 retry chain (run-A-01 failed → run-A-02 retry_of A-01)에서 `ok=true`.
     - 사후 target이 사라진 (legacy로 옮겨짐 가정) entry → `ok=true`이면서 WARN 1건.
     - record에 self-reference가 박힌 비정상 entry → ERROR.
     - record에 brief mismatch retry_of가 박힌 entry → ERROR.
     - 같은 `agent_run_id` 중복 entry 2건 → ERROR 1건 이상.
   - **legacy lookup 격리**:
     - target이 `runtime/agent-runs.legacy.jsonl`에만 있을 때 `--retry-of`는 거부(live only).
4. `python3 scripts/quality-gate.py --tier all --skip-tests --format json` 통과 확인. stable tier 통과 확인.
5. 1c와 1d-1의 기존 entry는 byte-identical 유지.

## Definition of Done

- `--retry-of` 플래그가 위 add invariants를 모두 enforce.
- `record_findings`가 위 check severity 표를 정확히 반영.
- `runtime/agent-runs.legacy.jsonl`은 retry resolution에 절대 참여하지 않음 (코드와 테스트로 보장).
- `docs/RUNTIME_EVENT_SCHEMA.md`가 새 정책을 반영.
- 신규 unittest ~13건이 통과하고 기존 211건(1d-1 완료 후) 회귀 없음. 총계 224건 이상.
- `quality-gate --tier stable`과 `--tier all` 모두 통과.
- 1c의 1건과 1d-1에서 추가된 entry는 byte-identical 유지.
- `retry_of` 필드가 없는 기존 entry는 그대로 valid로 판정됨(optional 보장).

## Rollback Plan

- 단일 commit 또는 좁은 commit 집합으로 묶어 revert 가능하게 한다.
- ledger 자체에는 mutation을 가하지 않으므로 코드 revert만으로 원상 복귀.
- `retry_of`가 optional이라 revert 후에도 새로 만들어진 retry entry는 deserializable.

## Stop Conditions

- target lookup 비용이 ledger 크기에 비례해 커지는데, 향후 archive rotation 도입 시 lookup scope가 바뀌어야 한다. 이 슬라이스 안에서 rotation까지 끌고 가지 않음 — 만약 rotation 의존성이 발견되면 stop, 별도 슬라이스로 분리.
- check severity 분류가 1d-3의 aggregation summary(failed/retried/stale)와 충돌하면 stop, 1d-3 설계를 끌어와 정합화 후 재개.
- `next_run_id`의 자동 증분이 retry semantics와 충돌하는 케이스가 나오면(예: 사용자가 직접 ledger 편집) stop, race condition 방어 로직을 별도 슬라이스로 분리.
- 강화된 check가 1c/1d-1의 기존 entry에 새 ERROR를 만들면 stop (설계 의도 어긋남; 기존 entry는 retry_of 없으니 영향 없어야 함).

## Validation

```bash
python3 -m unittest tests.test_validation -v
python3 scripts/incubating/agent-run.py --root . check --format json
python3 scripts/quality-gate.py --root . --tier stable --skip-tests --format json
python3 scripts/quality-gate.py --root . --tier all --skip-tests --format json
python3 scripts/verify-skeleton.py
python3 scripts/agent-flow.py closeout --goal "Phase 1d-2 retry/idempotency" --changed-path scripts/incubating/agent-run.py --changed-path docs/RUNTIME_EVENT_SCHEMA.md --changed-path tests/test_validation.py --format json
```

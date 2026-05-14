# Phase 1d-3: AgentRun Aggregation Summary

## Summary

AgentRun v2 ledger의 `summary --format json`을 retry-aware aggregation으로 확장한다. 1d-2에서 고정한 `retry_of` 의미를 read-side에서 해석해 retry 현황과 unresolved failure를 한 번의 ledger scan으로 계산한다.

## Assumptions

- `runtime/agent-runs.jsonl`는 live append-only v2 ledger이며 reader의 기본 입력이다.
- `runtime/agent-runs.legacy.jsonl`는 frozen archive이며 aggregation 대상이 아니다.
- `retry_of`는 top-level optional field이고, retry chain은 `retry_of` edge를 따라 reader가 재구성한다.
- 현재 status set은 terminal 중심이므로 stale 계산은 이번 slice에서 제외한다.

## Out of Scope

- `stale` 또는 in-progress run 정책 정의.
- retry record rewrite, ledger migration, archive rotation.
- `agent-flow delegate` 또는 자동 delegation.
- table output, dashboard output, SDK/LangGraph adapter.

## Key Changes

- `scripts/incubating/agent-run.py summary --format json`에 retry-aware 필드를 추가한다.
- 추가 필드:
  - `retried_count`: `retry_of`가 있는 record 수.
  - `retry_chain_heads`: 다른 run에게 retry target으로 가리켜지지 않는 run 수.
  - `unresolved_failures`: chain head 중 `status`가 `failed` 또는 `blocked`인 run 수.
- 기존 summary 필드(`total`, `by_status`, `by_agent`, `by_workflow`, `latest_ts`, `findings_count`)는 유지한다.
- malformed JSONL 처리와 check severity 정책은 1d-2 동작을 그대로 유지한다.

## Implementation Steps

1. `summary_records(records, findings)` 또는 동등 helper에서 retry reverse index를 만든다.
2. `retry_targets = {record["retry_of"] for record in records if retry_of is present}`를 계산한다.
3. `retry_chain_heads`는 `agent_run_id`가 `retry_targets`에 없는 records 수로 계산한다.
4. `unresolved_failures`는 chain head 중 `status in {"failed", "blocked"}`인 records 수로 계산한다.
5. `retried_count`는 `retry_of`가 present한 records 수로 계산한다.
6. 관련 regression tests를 `tests/test_validation.py`에 추가한다.
7. `docs/RUNTIME_EVENT_SCHEMA.md` AgentRun v2 summary 설명에 새 aggregation 필드를 문서화한다.

## Definition of Done

- `summary --format json`이 세 retry-aware 필드를 출력한다.
- valid retry chain에서 `retried_count`, `retry_chain_heads`, `unresolved_failures`가 기대값을 반환한다.
- failed/blocked chain head는 unresolved failure로 집계된다.
- retry로 대체된 failed/blocked target은 unresolved failure로 집계되지 않는다.
- legacy ledger는 summary 계산에 포함되지 않는다.
- 기존 live ledger에서 `agent-run.py check`는 계속 `ok=true`를 반환한다.

## Validation

```bash
python3 -m unittest tests.test_validation -v
python3 scripts/incubating/agent-run.py --root . check --format json
python3 scripts/incubating/agent-run.py --root . summary --format json
python3 scripts/quality-gate.py --root . --tier stable --skip-tests --format json
python3 scripts/quality-gate.py --root . --tier all --skip-tests --format json
python3 scripts/verify-skeleton.py
python3 scripts/agent-flow.py closeout --goal "Phase 1d-3 aggregation summary" --changed-path scripts/incubating/agent-run.py --changed-path docs/RUNTIME_EVENT_SCHEMA.md --changed-path tests/test_validation.py --changed-path plans/active/0003-phase-1d-3-aggregation-summary.md --format json
```

## Rollback Plan

Revert the 1d-3 commit. Do not edit or rewrite `runtime/agent-runs.jsonl`.

## Stop Conditions

- Summary requires non-terminal status or stale policy decisions.
- Summary needs legacy ledger lookup.
- Existing live ledger produces new ERROR findings.
- Any implementation path suggests rewriting AgentRun ledger history.

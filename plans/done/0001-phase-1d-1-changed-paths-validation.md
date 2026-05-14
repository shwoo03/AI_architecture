# 0001-phase-1d-1-changed-paths-validation

## Summary

Phase 1c에서 ledger를 v2-only로 굳혔지만 `changed_paths`는 아직 `isinstance(list)` 수준의 형식 검증만 한다. 1d-1은 가장 작은 단위로 다음을 잡는다: `add`는 repo 외부, 비존재, symlink escape path를 엄격히 거부하고, `check`는 같은 위반에 대해 historical entry는 advisory(WARN) 로 보고한다. empty `changed_paths`는 read-only workflow(`manual_smoke`, `dry_run`)에서만 허용한다. 1d-2/1d-3가 재사용할 canonical repo-root resolver 한 군데로 모은다.

## Assumptions

- `runtime/agent-runs.jsonl`은 v2-only live ledger이고, legacy archive(`runtime/agent-runs.legacy.jsonl`)는 이번 검증에서 제외한다(1c에서 확정).
- `scripts/incubating/agent-run.py`의 `resolve_under_root`가 현존 canonical resolver이며 그 시맨틱을 확장한다(별도 헬퍼 신설 안 함).
- `changed_paths`는 top-level canonical field로 유지하며, 이번 슬라이스에서 위치 이동 없음.
- `add` 시점 strict 검증으로 충분하며, 과거 entry에 대한 retroactive rewrite는 하지 않는다(append-only 원칙).
- `quality-gate --tier stable`은 영향 없음. 검증 강화는 `--tier all`의 `agent-run-ledger` 경로에서만 시행.

## Out of Scope

- retry/idempotency 정책(1d-2).
- failed/retried/stale summary count(1d-3).
- delegation entrypoint, agent-flow surface 변경.
- legacy ledger의 데이터 보정.
- `changed_paths` schema 위치 이동 또는 entry 재명명.

## Implementation Steps

1. `scripts/incubating/agent-run.py`
   - `resolve_under_root` 옆에 `validate_changed_path(root, value)` 신설: 빈 문자열 거부, repo 외부 거부, 비존재 거부, symlink resolve 후 prefix 비교로 escape 거부. 거부 사유는 `(reason, detail)` tuple로 반환해 호출부가 분류 가능하게.
   - `READ_ONLY_WORKFLOWS = frozenset({"manual_smoke", "dry_run"})` 상수 추가. `build_record`에서 workflow ∉ set 인데 `changed_paths`가 비면 `ValueError`.
   - `build_record` 내부에서 모든 `args.changed_path` 항목을 `validate_changed_path`로 통과시키고, 통과한 값은 repo-relative POSIX path로 정규화하여 저장.
   - `record_findings`에 changed_paths 항목별 검증 추가:
     - missing path: `severity=WARN`, `check=changed_paths_missing` (advisory).
     - outside-root 또는 symlink escape: `severity=ERROR`, `check=changed_paths_escape`.
     - empty list 이면서 workflow ∉ READ_ONLY_WORKFLOWS: `severity=ERROR`, `check=changed_paths_required`.
   - `check_records`/`summary_records`는 기존 흐름 유지하되, WARN은 `ok`를 깨지 않고 `findings`에 포함(현 구조가 이미 findings 리스트만 본다). `ok` 판정은 `ERROR`만으로 결정하도록 분기.
2. `docs/RUNTIME_EVENT_SCHEMA.md` AgentRun v2 섹션 보강
   - `changed_paths` 의미: repo-relative POSIX path 목록. `add` 시점 strict 검증, `check`에서 historical missing은 WARN.
   - `READ_ONLY_WORKFLOWS` 정책 명시(empty 허용 조건).
   - 1d-2/1d-3 후속 슬라이스 자리 한 줄 표기(스펙은 비워둠).
3. `tests/test_validation.py`에 회귀 테스트 추가(`scripts/incubating/agent-run.py` 대상)
   - `add`가 repo 밖 path를 거부(exit code != 0, stderr에 사유).
   - `add`가 존재하지 않는 path를 거부.
   - `add`가 symlink로 repo 외부를 가리킬 때 거부.
   - `add`가 `--workflow manual_smoke`일 때 empty `--changed-path`로 성공.
   - `add`가 `--workflow completed_run` 같은 비 read-only workflow에서 empty `--changed-path`이면 거부.
   - `check`가 정상 entry에서 `ok=true`.
   - `check`가 사후에 삭제된 path를 가진 historical entry에 대해 `ok=true` + `findings`에 WARN 1건(advisory) 표시.
4. `python3 scripts/quality-gate.py --tier all --skip-tests --format json` 통과 확인. stable tier 통과 확인.
5. closeout 전 `runtime/agent-runs.jsonl` 1c 기록은 손대지 않음을 재확인.

## Definition of Done

- `add`가 repo 외부 / 비존재 / symlink escape / 비 read-only workflow의 empty 입력을 모두 거부하며, stderr 사유는 분류 가능.
- `add`가 read-only workflow + empty 입력에는 그대로 성공.
- `check`가 missing path를 가진 historical entry에 대해 `ok=true`이면서 WARN finding을 보고.
- `check`가 outside-root/symlink escape historical entry에 대해 `ok=false`(ERROR) 를 반환.
- `docs/RUNTIME_EVENT_SCHEMA.md`가 위 규칙을 반영.
- 신규 unittest 7건이 통과하고 기존 204건 회귀 없음.
- `quality-gate --tier stable`과 `--tier all` 모두 통과(stable은 영향 없음 재확인, all은 강화된 ledger 검증 포함).
- 1c의 기존 ledger entry는 byte-identical 유지.

## Rollback Plan

- 단일 commit 또는 좁은 commit 집합으로 묶어 revert 가능하게 한다.
- ledger 자체에는 mutation을 가하지 않으므로 코드 revert만으로 원상 복귀.
- 만약 historical WARN이 `--tier all` 운영에서 잡음이 되면, `record_findings`의 WARN 분기를 feature flag 없이 옵션 인자로 끄지 않고 정책 자체를 한 번 더 다듬는다(임시 우회 안 함).

## Stop Conditions

- `resolve_under_root` 동작이 기존 호출부(brief path)에서 회귀할 조짐이 보이면 stop, 회귀 테스트 추가 후 재개.
- WARN/ERROR 분류 기준이 1d-2의 retry/idempotency 설계와 충돌하면 stop, 1d-2 설계 결정을 먼저 끌어와서 정합화 후 재개.
- `quality-gate --tier all`이 강화로 인해 기존 1c entry에서 ERROR를 새로 만들면 stop(설계 의도와 다름; historical은 advisory만). 발견 시 분기 재검토.

## Validation

```bash
python3 -m unittest tests.test_validation -v
python3 scripts/incubating/agent-run.py --root . check --format json
python3 scripts/quality-gate.py --root . --tier stable --skip-tests --format json
python3 scripts/quality-gate.py --root . --tier all --skip-tests --format json
python3 scripts/verify-skeleton.py
python3 scripts/agent-flow.py closeout --goal "Phase 1d-1 changed_paths validation" --changed-path scripts/incubating/agent-run.py --changed-path docs/RUNTIME_EVENT_SCHEMA.md --changed-path tests/test_validation.py --format json
```

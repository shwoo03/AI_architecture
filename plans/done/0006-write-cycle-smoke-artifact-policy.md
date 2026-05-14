# 0006-write-cycle-smoke-artifact-policy

## Summary

이 plan은 코드 feature가 아니라 **첫 write-heavy delegate cycle**의 실행 계약이다. 1e-followup commit(`7ba7a7d`)에서 발견된 새 friction(검증 명령이 brief 파일을 `runtime/agent-briefs/`에 남김 → 실 cycle 산출물과 검증 pollution이 섞임)에 대응한다. delegate로 brief를 만들고, Codex가 그 brief를 읽어 (1) `runtime/agent-briefs/`에 대한 smoke artifact 보존/삭제 정책을 짧은 문서로 작성하고, (2) 현재 디렉터리 안의 5개 brief를 정책 기준으로 분류한다. evidence-backed record는 절대 삭제하지 않는다.

## Assumptions

- 1e-followup commit(`7ba7a7d`)이 main에 있고, ledger sha256은 그대로(live `a422a72c...`, legacy `811c9d3f...`).
- `runtime/agent-briefs/`에 5개 brief가 있다(직전에 orphan 2건은 제거됨).
- `scripts/agent-brief.py`의 `WRITE_POLICIES = {read_only, manual_work_required, write_with_confirmation}`.
- delegate는 `--workflow completed_run` 같은 write workflow에서 `--changed-path` placeholder를 채워둔다(1e-followup 결과).
- 이 cycle은 코드 변경이 아니라 **정책 문서 1개 신설 + 분류 기록**이 산출물. write task로 실데이터를 얻는 게 목적.

## Out of Scope

- delegate에 `--dry-run` 또는 `--no-write` 추가(별도 슬라이스).
- `runtime/agent-briefs/` 디렉터리 구조 변경(`smoke/` 서브디렉터리 신설 등). 이번에는 분류만 한다.
- evidence-backed brief의 이동/이름 변경.
- 새 brief schema 필드, ledger 필드.
- routing, validator-loop, non-terminal status.

## 분류 기준 (cycle 실행 시 적용)

3-tier classification:

```text
Tier 1 — Ledger-anchored evidence
  조건: runtime/agent-runs.jsonl 또는 runtime/agent-runs.legacy.jsonl에서
         이 brief_id를 참조하는 AgentRun이 있다.
  처분: 보존. 어떤 형태로도 이동·삭제·이름 변경 금지.

Tier 2 — Milestone smoke (no AgentRun, but feature-evidence)
  조건: matching AgentRun은 없지만, 특정 phase의 의도된 smoke이며
         state/progress.md / plans / commit message에서 그 phase가
         참조된다(파일명에 phase 식별자가 포함된 경우 강한 신호).
  처분: 보존. 정책 문서에 "milestone smoke로 의도되어 보존"이라고 기록.

Tier 3 — Validation pollution
  조건: matching AgentRun 없음, 어느 phase의 milestone에도 명시적으로
         참조되지 않음, 이름에 `adhoc` 또는 generic role/role-default 외
         의 phase 식별자 부재. 검증 명령을 돌릴 때 부수적으로 생긴 것.
  처분: 삭제 가능. 단 삭제 사유와 brief_id를 cycle의 AgentRun
         `result_summary` 또는 `validation` entry에 기록.
```

판단 우선순위: ledger 매칭 > 파일명/문서 참조 > 추정. 추정으로 Tier 3 분류하지 말 것. 의심스러우면 Tier 2(보존)로.

## 산출물

1. `docs/AGENT_BRIEFS_POLICY.md` 신설 (짧은 문서, ~40-60줄)
   - 한 문장 정의
   - 무엇을 하는가
   - 왜 필요한가
   - 3-tier 분류 기준(위와 동일)
   - 삭제 절차(ledger 또는 handoff에 사유 기록 → 삭제 → 활동 로그 1줄)
   - 향후 검토(--dry-run/--no-write 슬라이스 후보로 명시)
   - 구현 연결 정보(`runtime/agent-briefs/`, `scripts/incubating/agent-flow-delegate.py`, `scripts/incubating/agent-run.py`)
2. classification 기록 (cycle의 AgentRun `result_summary` 또는 sidecar)
   - 5개 brief 각각의 brief_id, tier, 근거(ledger 매칭 / 참조 위치)
   - 삭제한 게 있으면 brief_id와 사유

## Implementation Steps (Codex 실행 순서)

1. delegate로 brief 생성:
   ```bash
   python3 scripts/incubating/agent-flow-delegate.py \
     --role docs-sync-auditor \
     --goal "Document smoke artifact policy for runtime/agent-briefs/ and classify existing brief artifacts without deleting evidence-backed records" \
     --scope runtime/agent-briefs \
     --scope docs \
     --scope state \
     --write-policy write_with_confirmation \
     --workflow completed_run \
     --format json
   ```
2. 생성된 brief 파일 경로와 `completion_command`를 handoff JSON에서 확인.
3. `runtime/agent-briefs/` 안의 5개 brief 각각에 대해 분류:
   - `runtime/agent-runs.jsonl`과 `runtime/agent-runs.legacy.jsonl`에서 `brief_id` 또는 `runtime/agent-briefs/<filename>` 참조를 grep.
   - 매칭 있으면 Tier 1.
   - 매칭 없으면 `state/progress.md`, `plans/done/*.md`, 최근 commit message에서 brief 식별자 검색.
   - 참조 있으면 Tier 2.
   - 참조 없으면 Tier 3 후보. 단 이번 5개에서는 Tier 3이 나오면 안 됨(이미 orphan은 제거됨). 만약 Tier 3 후보가 나온다면 stop, 사람 확인.
4. `docs/AGENT_BRIEFS_POLICY.md` 작성 (위 산출물 1).
5. classification 결과를 정리해서 다음 단계의 AgentRun `result_summary`에 한 단락으로 포함할 수 있게 준비.
6. `agent-run.py add`로 AgentRun 닫음. `--changed-path docs/AGENT_BRIEFS_POLICY.md`를 정확히 넘기고, `--workflow completed_run`, status `completed`. `--retry-of`는 사용하지 않음.
7. 검증 sweep: `agent-run.py check`, `quality-gate --tier stable/all`, `verify-skeleton`, `unittest`.
8. 새로 생긴 brief 파일(이 cycle에서 delegate가 만든 것)은 evidence이므로 그대로 commit 대상.
9. closeout 후 단일 commit.

## Definition of Done

- `docs/AGENT_BRIEFS_POLICY.md`가 신설되고 위 3-tier 분류 + 삭제 절차 + 향후 검토를 명시.
- 5개 기존 brief에 대한 분류 결과가 AgentRun `result_summary`에 기록.
- 이번 cycle에서 evidence-backed brief를 **삭제·이동·이름 변경하지 않음**.
- 새 AgentRun 1건이 `runtime/agent-runs.jsonl`에 정상 append되고 `agent-run.py check`가 `ok=true`.
- live ledger sha256은 정상 갱신(append 발생), legacy ledger sha256은 보존(`811c9d3f...`).
- `scripts/agent-brief.py`, `scripts/agent-flow.py`, `scripts/incubating/agent-run.py`, `scripts/incubating/agent-flow-delegate.py`는 byte-identical.
- `quality-gate --tier stable`과 `--tier all` 통과.
- 기존 240건 unittest 회귀 없음(이번 cycle에 새 unittest는 일반적으로 필요하지 않음. 정책 문서 추가는 코드 변경이 아니라).

## Rollback Plan

- 단일 commit으로 묶음. revert 시 `docs/AGENT_BRIEFS_POLICY.md`만 사라지고 ledger의 AgentRun은 append-only 원칙으로 그대로 남음(이건 의도된 동작).
- 이번 cycle은 ledger에 entry를 추가하지만 기존 entry는 건드리지 않음.

## Stop Conditions

- 5개 brief 중 Tier 3 후보가 나오면 stop. orphan은 이미 제거됐다는 가정이 깨진 것이므로 사람 확인 필요.
- ledger에 새 entry를 append할 때 1d 시리즈 검증(`changed_paths` strict, `retry_of` 부재 OK)이 실패하면 stop.
- `docs/AGENT_BRIEFS_POLICY.md` 작성 중 1d-1/1d-2/1d-3 정책과 모순되는 규칙을 박으려고 하면 stop.
- delegate가 brief를 만들지 못하면(즉 `--write` 실패) stop. 이 경우 1e 회귀 가능성 점검.

## Validation

```bash
python3 scripts/incubating/agent-flow-delegate.py --role docs-sync-auditor --goal "Document smoke artifact policy for runtime/agent-briefs/ and classify existing brief artifacts without deleting evidence-backed records" --scope runtime/agent-briefs --scope docs --scope state --write-policy write_with_confirmation --workflow completed_run --format json
# (수동 또는 자동) brief 읽고 docs/AGENT_BRIEFS_POLICY.md 작성, 5개 brief 분류
python3 scripts/incubating/agent-run.py add --brief "<generated brief path>" --status completed --result-summary "<classification summary>" --changed-path docs/AGENT_BRIEFS_POLICY.md --validation manual_read=passed --workflow completed_run --agent human_operator --created-by manual --format json
python3 scripts/incubating/agent-run.py check --format json
python3 scripts/incubating/agent-run.py summary --format json
python3 -m unittest discover -s tests
python3 scripts/quality-gate.py --root . --tier stable --skip-tests --format json
python3 scripts/quality-gate.py --root . --tier all --skip-tests --format json
python3 scripts/verify-skeleton.py
python3 scripts/agent-flow.py closeout --goal "Write-heavy delegate cycle: smoke artifact policy" --changed-path docs/AGENT_BRIEFS_POLICY.md --format json
```

## Result

Stated artifact-policy goal completed via operator housekeeping. Delegate execution path aborted by role-registry gap: governance correctly rejected expanding `docs-sync-auditor`'s read-only policy to `write_with_confirmation`, and we did not bypass it.

### What was achieved
- `docs/AGENT_BRIEFS_POLICY.md` 신설로 smoke artifact governance 정책 문서화.
- `runtime/agent-briefs/`의 5개 기존 brief를 3-tier 기준으로 분류(결과는 정책 문서 evidence 섹션에).

### What was NOT achieved
- 원래 메타 목표였던 "write-heavy delegate cycle 실행으로 write-side friction 데이터 수집"은 미달성.
- 0007 (role registry audit) -> 0008 (최소 write-capable docs role 추가) 완료 후 새 slice로 재시도.

### Friction signal recorded
- role registry에 docs/governance write task에 적합한 role 부재.
- 이는 routing/validator/non-terminal status보다 선행되어야 하는 gap. `state/decisions.md` 참조.

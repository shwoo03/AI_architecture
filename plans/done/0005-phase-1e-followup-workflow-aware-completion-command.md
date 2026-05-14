# 0005-phase-1e-followup-workflow-aware-completion-command

## Summary

1e 직후 첫 실데이터 cycle(`run-2026-05-14-adhoc-docs-sync-auditor-02-01`, CODEMAPS audit)에서 observed된 friction은 단 한 개였다: delegate가 만드는 `completion_command` 템플릿이 workflow에 무관하게 `--changed-path "<repo-relative-path>"`와 `--workflow manual_smoke`를 박아 넣어서, read-only audit에서는 사람이 `--changed-path`를 매번 손으로 지웠다. 1e-followup은 이 한 가지 friction만 정확히 잡는다. delegate에 `--workflow` 옵션을 추가하고, workflow가 read-only(`manual_smoke`, `dry_run`)이면 completion_command에서 `--changed-path` 라인을 생략한다. write workflow이면 기존 placeholder를 유지한다. ledger writer(`agent-run.py`)는 건드리지 않는다.

## Assumptions

- 1e commit(`72c97f9`)과 첫 audit commit(`c559133`)이 main에 있고, ledger sha256 보존.
- 1d-1에서 도입한 `READ_ONLY_WORKFLOWS = {"manual_smoke", "dry_run"}` 정책이 그대로 유효. delegate 쪽 로컬 상수는 이 집합의 **부분집합 또는 동일집합**으로 시작한다(동일집합으로 시작).
- `scripts/agent-brief.py`, `scripts/agent-flow.py`, `scripts/incubating/agent-run.py`는 변경 대상 아님.
- delegate는 여전히 pure preparation. ledger에 어떤 형태로도 쓰지 않는다.

## Out of Scope

- `agent-run.py`의 workflow enum 추가/축소. delegate 쪽 템플릿 정책만 고친다.
- 새 brief schema 필드.
- routing, validator-loop, non-terminal status — write-heavy cycle 1회 더 본 뒤 결정.
- `--retry-of`를 completion_command 기본 템플릿에 포함시키는 것. 1d-2의 "retry는 명시" 원칙 그대로 유지(retry는 사람이 별도 cli flag로 추가).
- `scripts/agent-flow.py` 본체에 delegate subcommand 노출.
- Notion sync / 외부 알림 / spawn.

## 핵심 정책 (구현 기준)

```text
delegate --workflow option
  - 새 옵션, default "manual_smoke"
  - 자유 문자열 (enum 강제 안 함; agent-run.py가 그렇듯)

completion_command 생성 규칙
  - workflow ∈ READ_ONLY_WORKFLOWS  -> --changed-path 줄 생략
  - workflow ∉ READ_ONLY_WORKFLOWS  -> --changed-path "<repo-relative-path>" 포함
  - --workflow 인자는 항상 실제 값으로 박음 (하드코딩된 manual_smoke 제거)
  - --retry-of는 기본 템플릿에 포함하지 않음

handoff JSON 출력
  - workflow 필드 신규 추가(투명성)
  - 나머지 필수 필드(plan 0004와 동일) 변경 없음
```

## Implementation Steps

1. `scripts/incubating/agent-flow-delegate.py`
   - 파일 상단에 로컬 상수 추가: `READ_ONLY_WORKFLOWS = frozenset({"manual_smoke", "dry_run"})`. 의도는 "agent-run.py가 empty changed_paths를 허용하는 workflow와 같은 집합". 주석 한 줄로 sync 의무 명시.
   - argparse: `parser.add_argument("--workflow", default="manual_smoke")` 추가. choices 강제 없음(agent-run.py와 동일).
   - `completion_command(brief_path)` → `completion_command(brief_path, workflow)`로 시그니처 변경.
     - read-only이면 `--changed-path "<repo-relative-path>"` 줄 자체를 제외하고 join.
     - `--workflow {workflow}` 자리에 실제 인자 값.
     - 그 외 부분은 그대로(`--brief`, `--status completed`, `--result-summary "<result-summary>"`, `--validation manual_read=passed`, `--agent human_operator`, `--created-by manual`, `--format json`).
   - `handoff_payload(brief_path, brief)` → `handoff_payload(brief_path, brief, workflow)`로 시그니처 변경. payload에 `"workflow": workflow` 한 줄 추가. `completion_command` 호출도 새 시그니처 사용.
   - main에서 `handoff_payload(..., args.workflow)`로 전달.
   - `next_prompt` 문구는 그대로 두되, read-only일 때 마지막 줄에 한 토막 추가: "Read-only workflow detected; --changed-path is omitted from the completion_command." 이 한 줄은 정보 전달용. 필수는 아니지만 인지 개선 효과 있음.
2. `tests/test_validation.py` 회귀/신규 테스트 (~6건)
   - default(`manual_smoke`): handoff JSON에 `workflow == "manual_smoke"`, completion_command에 `--changed-path` 없음, `--workflow manual_smoke` 있음.
   - `--workflow dry_run`: completion_command에 `--changed-path` 없음, `--workflow dry_run` 있음.
   - `--workflow completed_run` (또는 임의의 비-read-only 문자열): completion_command에 `--changed-path "<repo-relative-path>"` 있음, `--workflow completed_run` 있음.
   - completion_command가 agent-run.py argparse로 실제 파싱 가능(read-only 경로와 write 경로 모두). subprocess로 `--help` 또는 `--brief ... --workflow ... ...`을 받아 비-zero가 아니게 실행되는지(dry-parse) 검증.
   - 기존 1e 테스트(handoff 필수 필드, smoke 등) 회귀 없음.
   - byte-identical 보장: 테스트 안에서 직접 확인하지 않아도 되지만, CI 단계에서 `scripts/agent-brief.py`/`scripts/agent-flow.py`/`scripts/incubating/agent-run.py` 변경 안 됨을 closeout 단계에서 sha256으로 보고.
3. `docs/RUNTIME_EVENT_SCHEMA.md`
   - 1e 섹션 옆에 한 단락 추가: "delegate의 `completion_command`는 workflow-aware. read-only workflow(`manual_smoke`, `dry_run`)에서는 `--changed-path` placeholder를 생략한다. 이 집합은 1d-1의 `READ_ONLY_WORKFLOWS`와 동기화되어야 한다." 한 단락이면 충분.
4. quality-gate 양 tier 통과 확인.
5. closeout 전 ledger sha256 보존 재확인.

## Definition of Done

- delegate가 `--workflow` 옵션을 수용하고, 위 핵심 정책대로 completion_command를 생성.
- handoff JSON에 `workflow` 필드가 추가됨. 기존 필수 필드는 그대로.
- `scripts/agent-brief.py`, `scripts/agent-flow.py`, `scripts/incubating/agent-run.py`는 byte-identical 유지.
- `runtime/agent-runs.jsonl`은 sha256 동일(이번 슬라이스는 ledger를 건드리지 않음).
  - 직전 audit cycle commit 이후 기준 sha256: `a422a72c61fd00ae3cd027603adde21040d8e4eac6ea474cbd6513809e77c163`
- `runtime/agent-runs.legacy.jsonl`은 sha256 동일: `811c9d3fba2074a785a4a13e38a3a2ddd5fcf4c5b3f683fbf3c55d8a761b7584`.
- 신규 unittest ~6건 통과, 기존 234건 회귀 없음, 총계 240건 이상.
- `quality-gate --tier stable`과 `--tier all` 모두 통과.
- `docs/RUNTIME_EVENT_SCHEMA.md`에 workflow-aware completion_command 한 단락 명시.

## Rollback Plan

- 단일 commit으로 묶어 revert 가능. delegate 한 파일 + 테스트 + 문서 한 단락이라 단순.
- ledger 무영향이라 revert가 어느 슬라이스에도 파급 없음.

## Stop Conditions

- delegate가 `--workflow` 처리 중 brief 생성(agent-brief.py 호출)에 새 인자를 요구하기 시작하면 stop. agent-brief.py는 byte-identical 유지가 원칙. 필요하면 별도 슬라이스로 분리.
- completion_command가 agent-run.py argparse로 실제 파싱 안 되는 케이스가 생기면 stop. agent-run.py의 flag 이름을 confirmed 기준으로 다시 맞춤.
- `READ_ONLY_WORKFLOWS` 집합을 delegate 안에서 확장해야 하는 케이스가 나오면 stop. 1d-1 정책과의 sync 문제는 별도 슬라이스로.
- 강화된 quality-gate가 기존 ledger entry에 새 ERROR/WARN 만들면 stop.

## Validation

```bash
python3 -m unittest tests.test_validation -v
python3 scripts/incubating/agent-flow-delegate.py --role docs-sync-auditor --goal "1e-followup smoke (read-only)" --write-policy read_only --format json
python3 scripts/incubating/agent-flow-delegate.py --role build-error-resolver --goal "1e-followup smoke (write)" --workflow completed_run --format json
python3 scripts/incubating/agent-run.py --root . check --format json
python3 scripts/quality-gate.py --root . --tier stable --skip-tests --format json
python3 scripts/quality-gate.py --root . --tier all --skip-tests --format json
python3 scripts/verify-skeleton.py
python3 scripts/agent-flow.py closeout --goal "Phase 1e-followup workflow-aware completion_command" --changed-path scripts/incubating/agent-flow-delegate.py --changed-path docs/RUNTIME_EVENT_SCHEMA.md --changed-path tests/test_validation.py --format json
```

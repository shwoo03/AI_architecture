# 0004-phase-1e-incubating-delegate-entrypoint

## Summary

1d-1/1d-2/1d-3로 AgentRun ledger의 changed_paths, retry/idempotency, retry-aware aggregation까지 굳혔다. 1e는 그 위에 처음으로 **실제 일을 사람/외부 agent에게 나누는 진입점**을 incubating tier로 도입한다. 핵심은 minimal: brief 파일 생성과 "실행 가능한 handoff" JSON 출력만 하고, 실제 execution이나 ledger append는 하지 않는다. brief schema source-of-truth는 기존 `scripts/agent-brief.py`이고, delegate는 그것을 재사용한다(별도 schema 재구현 금지). 공개 surface(`scripts/agent-flow.py`)는 건드리지 않는다.

## Assumptions

- 1d-3 commit(`999fd74`)이 main에 올라있고, ledger sha256 두 개(live/legacy)가 보존된 상태에서 시작한다.
- `scripts/agent-brief.py`의 `--write --format json` 경로가 brief artifact를 `runtime/agent-briefs/<brief_id>.json`에 쓰고 JSON으로 brief 메타데이터를 돌려준다.
- `scripts/incubating/agent-run.py add`는 1d 슬라이스에서 굳힌 강화된 검증(`changed_paths`, `retry_of`)을 그대로 가진다.
- 1d 시리즈에서 도입한 `READ_ONLY_WORKFLOWS = {manual_smoke, dry_run}`이 delegate completion 예시 명령에서도 동일하게 적용된다.
- delegate는 "stable surface 비차단" 원칙(1c 이래 일관)을 그대로 따른다. `quality-gate --tier stable`은 영향 없음.

## Out of Scope

- 외부 agent / subagent spawning (codex, claude code 호출 금지).
- Plan child artifact 자동 생성.
- AgentRun ledger의 새 `planned` status, run skeleton pre-append.
- non-terminal status enum 확장(`started`, `running` 등).
- `scripts/agent-flow.py`에 `delegate` subcommand 노출.
- `agent-brief.py` schema 변경(필드 추가/이름 변경 등).
- delegation chain 자체의 ledger 기록(brief 생성 사실은 brief 파일과 활동 로그 정도로만 남고, 별도 ledger entry 안 만든다).
- Notion sync, 외부 알림.

## 핵심 정책 (구현 기준)

```text
location          = scripts/incubating/agent-flow-delegate.py (incubating ONLY)
scope             = minimal — brief 파일 생성 + handoff JSON 출력만
execution         = pure preparation (사람/외부 agent가 별도로 실행)
brief schema      = scripts/agent-brief.py 재사용 (재구현 금지)
ledger interaction= NONE (live/legacy ledger 모두 읽기만, 쓰기 없음)
public surface    = NONE (scripts/agent-flow.py는 건드리지 않음)
tier              = incubating
```

## 재사용 전략 (agent-brief.py)

- **선호**: `scripts/agent-flow-delegate.py`가 `subprocess.run([sys.executable, "scripts/agent-brief.py", "--write", "--format", "json", ...])`로 호출하고, stdout JSON을 파싱한다. agent-brief.py가 single source of truth임을 강제한다.
- **대체 허용**: 함수 레벨 재사용도 가능하지만, 그 경우에도 `Brief` dataclass와 `build_brief`/`write_brief`/`render_text`를 **그대로** 호출하고 새 helper를 만들지 않는다. agent-brief.py 자체에는 변경을 가하지 않는다.
- **금지**: brief 필드를 delegate 코드에서 직접 구성하는 것. brief schema의 어떤 필드도 delegate 안에서 새로 정의하지 않는다.

## 출력 (executable handoff)

`delegate --format json`이 stdout으로 돌려주는 payload의 필수 필드:

```text
brief_path           : "runtime/agent-briefs/<brief_id>.json" (repo-relative POSIX)
brief_id             : 동일한 id
role                 : brief.role
objective            : brief.objective
read_scope           : brief.read_scope
write_scope          : brief.write_scope
write_policy         : brief.write_policy
validation_hints     : brief.validation_hints
goal_lineage         : brief.goal_lineage
next_prompt          : human/operator에게 줄 한 줄 지시 텍스트
                       (e.g., "Read runtime/agent-briefs/<id>.json and execute under the
                        listed read_scope/write_scope. On completion run the example
                        agent-run.py add command below.")
completion_command   : python3 scripts/incubating/agent-run.py add invocation 예시
                       (정확한 flag 이름과 brief 경로 포함, --result-summary와
                        --changed-path와 --validation은 placeholder 값)
tier                 : "incubating"
```

`completion_command`는 **agent-run.py argparse가 받는 정확한 flag 이름**만 사용한다(`--brief`, `--status`, `--result-summary`, `--changed-path`, `--validation`, `--workflow`, `--agent`, `--created-by`, `--retry-of`). 새 flag 만들지 않는다.

## Implementation Steps

1. `scripts/incubating/agent-flow-delegate.py` 신설
   - argparse: `--root`, `--role`(required), `--goal`(required), `--scope`(repeatable, default `["."]`), `--write-policy`, `--parent-plan`, `--parent-goal`, `--user-goal`, `--parent-role`, `--parent-write-policy`, `--parent-scope`(repeatable), `--brief-seq`, `--format json`.
   - `--role`, `--goal`만으로도 동작해야 한다(나머지는 agent-brief.py 기본값).
   - `scripts/agent-brief.py`를 subprocess로 호출, `--write --format json`. 모든 pass-through 인자는 동일 이름으로 forward.
   - subprocess 실패 시 비-zero exit + stderr 그대로 전달, ledger 영향 없음.
   - 성공 시 brief JSON 파싱 → handoff payload 구성 → stdout으로 JSON 출력.
   - `completion_command`는 문자열 한 줄로 구성, brief 경로를 정확히 박는다. status는 `completed`, workflow는 `manual_smoke`, changed-path/validation은 placeholder(`<repo-relative-path>`, `<command>=<status>`).
   - ledger 파일은 절대 열지 않는다(읽기 포함). 검증으로 sha256 동일성 확인.
2. `docs/RUNTIME_EVENT_SCHEMA.md` (혹은 별도 incubating 섹션) 한 단락 추가
   - delegate가 schema source-of-truth가 아니라 agent-brief.py를 재사용한다는 점.
   - delegate는 ledger에 쓰지 않으며, 완료는 사람/외부 agent가 `agent-run.py add`로 수행한다는 점.
3. `tests/test_validation.py`에 회귀 테스트 추가 (~6-7건)
   - 정상 호출: `--role X --goal Y`로 brief 파일이 생성되고 handoff JSON에 필수 필드가 모두 있다.
   - `completion_command`가 정확한 flag 이름을 사용한다(`--brief`, `--status`, `--result-summary` 모두 포함).
   - `--role` 또는 `--goal`이 빠지면 비-zero exit(agent-brief.py가 거부하는 동일한 케이스).
   - scope 전파: `--scope src/` 줬을 때 출력 `read_scope`/`write_scope`가 그대로 반영.
   - ledger 비침해: 호출 전후 `runtime/agent-runs.jsonl`과 `runtime/agent-runs.legacy.jsonl`의 sha256이 동일.
   - public surface 비침해: `scripts/agent-flow.py`의 subcommand 목록에 `delegate`가 없다(argparse가 거부).
   - 임시 디렉터리 root에서도 동작(테스트 격리 검증).
4. `python3 scripts/quality-gate.py --tier stable --skip-tests`와 `--tier all --skip-tests` 모두 통과 확인.
5. closeout 전 ledger sha256 보존 재확인.

## Definition of Done

- `scripts/incubating/agent-flow-delegate.py`가 위 핵심 정책을 모두 따른다.
- handoff JSON이 위 필수 필드를 전부 포함하고, `completion_command`가 agent-run.py argparse로 실제 파싱 가능한 형태.
- `scripts/agent-brief.py`는 byte-identical 유지(재사용만 함, 수정 금지).
- `scripts/agent-flow.py`는 byte-identical 유지(stable surface 비침해).
- `runtime/agent-runs.jsonl`과 `runtime/agent-runs.legacy.jsonl`은 sha256 동일.
- 신규 unittest ~6-7건 통과, 기존 227건 회귀 없음, 총계 233건 이상.
- `quality-gate --tier stable`과 `--tier all` 모두 통과.
- `docs/RUNTIME_EVENT_SCHEMA.md`에 delegate가 brief의 wrapper이고 ledger writer가 아니라는 한 단락 명시.

## Rollback Plan

- 단일 commit으로 묶어 revert 가능하게 한다.
- delegate는 새 파일 추가가 주이고 기존 코드 시그니처를 건드리지 않으므로, revert가 어느 슬라이스에도 영향을 주지 않는다.
- agent-brief.py/agent-flow.py를 안 건드리는 것이 rollback 안정성의 핵심.

## Stop Conditions

- delegate 구현이 brief schema의 새 필드를 요구하기 시작하면 stop. 사용자에게 보고 후 별도 슬라이스에서 schema 확장.
- subprocess 재사용이 환경별로 깨지는 케이스(예: `python3` 경로) 가 나오면 stop, 함수 레벨 재사용으로 전환을 사용자에게 제안.
- `completion_command`가 agent-run.py argparse로 파싱 안 되는 케이스가 나오면 stop, agent-run.py flag 이름을 confirmed 기준으로 다시 맞춤.
- public surface(`scripts/agent-flow.py`)에 어떤 형태로든 delegate 노출 요구가 발생하면 stop, 1f 별도 슬라이스로 분리.
- 강화된 quality-gate가 1c/1d의 기존 ledger entry에 새 ERROR/WARN을 만들면 stop(설계 의도 어긋남).

## Validation

```bash
python3 -m unittest tests.test_validation -v
python3 scripts/incubating/agent-flow-delegate.py --role docs-sync-auditor --goal "delegate smoke test" --format json
python3 scripts/incubating/agent-run.py --root . check --format json
python3 scripts/incubating/agent-run.py --root . summary --format json
python3 scripts/quality-gate.py --root . --tier stable --skip-tests --format json
python3 scripts/quality-gate.py --root . --tier all --skip-tests --format json
python3 scripts/verify-skeleton.py
python3 scripts/agent-flow.py closeout --goal "Phase 1e incubating delegate entrypoint" --changed-path scripts/incubating/agent-flow-delegate.py --changed-path docs/RUNTIME_EVENT_SCHEMA.md --changed-path tests/test_validation.py --format json
```

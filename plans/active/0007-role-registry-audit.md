# 0007-role-registry-audit

## Summary

0006 abort 과정에서 role registry coverage gap이 첫 증거로 드러났다. routing/validator-loop/non-terminal status 같은 상위 슬라이스보다 이 gap이 선행되어야 한다. 0007은 **read-only audit만** 수행한다: 현재 정의된 role 목록, 각 role의 default write_policy, scope, 그리고 docs/governance/audit 등 task 종류별 coverage gap을 사실로 정리한다. 새 role 추가는 0008의 일이다.

## Assumptions

- 0006 abort commit이 main에 있고, role registry 현 상태에서 audit한다.
- audit 산출물은 `docs/_meta/ROLE_REGISTRY_AUDIT.md` (또는 동등한 docs 위치)에 둔다.

## Out of Scope

- 새 role 추가/수정/삭제 (0008).
- routing, validator-loop, non-terminal status.
- `agent-flow-delegate.py`, `agent-brief.py`, `agent-run.py` 코드 변경.
- ledger 변경.

## Implementation Steps

1. role registry 파일/경로 파악(예: `config/roles.yaml`, `docs/AGENT_REGISTRY.md`, `scripts/agent-brief.py`의 `load_team_registry` 등). 사실관계로 정리.
2. 각 role의 (role 이름, default write_policy, default scope, 의도된 task 종류) 표 작성.
3. task 종류별 coverage 분석: code-write, docs-write, governance-write, audit (read-only), etc.
4. gap 식별: 어떤 task가 적합한 role 없이 남는지 명시. 0006 abort는 그 중 docs/governance-write의 부재가 trigger였음을 evidence로 인용.
5. 0008에서 추가를 권고할 **최소** role 후보(이름, 제안하는 write_policy, scope 윤곽)를 audit 결론으로 제시. 단 0007에서 실제 추가는 하지 않는다.

## Definition of Done

- `docs/_meta/ROLE_REGISTRY_AUDIT.md` 신설(또는 동등 위치), 위 5단계 결과 포함.
- role registry 자체에 변경 0건.
- ledger 변경 0건.
- 기존 unittest 회귀 0건.
- `quality-gate --tier stable`과 `--tier all` 모두 통과.

## Rollback Plan

- 단일 commit. revert 시 audit 문서만 사라짐. ledger/registry 무영향.

## Stop Conditions

- audit 중 role registry 파일을 수정해야 하는 케이스가 생기면 stop(그건 0008).
- audit이 1d 시리즈 정책과 모순되는 권고를 만들려고 하면 stop.

## Validation

```bash
python3 scripts/verify-skeleton.py
python3 scripts/quality-gate.py --root . --tier stable --skip-tests --format json
python3 scripts/quality-gate.py --root . --tier all --skip-tests --format json
python3 -m unittest discover -s tests
python3 scripts/agent-flow.py closeout --goal "Plan 0007 role registry audit (plan creation only)" --changed-path plans/active/0007-role-registry-audit.md --format json
```

## Status: Deferred

이 plan은 작성된 시점 직후 freeze 결정으로 **미실행 deferred** 상태로 보존된다. 자세한 결정 근거는 `state/decisions.md`의 2026-05-15 freeze entry 참조.

- Deferred 이유: 외부 실사용 데이터 없이 0007을 진행하면 self-referential infra 함정에 빠질 위험이 큼. 0006 abort 직후 자동 다음 단계로 실행하면 그 패턴 그대로 반복.
- Resume 조건: 외부 프로젝트 X에서 v1 stable overlay가 실제로 적용된 뒤, role registry coverage gap이 다시 friction으로 관찰될 때.
- 그때까지 이 plan body는 보존된다. INDEX의 status는 `active`로 두되 본문이 진실(deferred)을 설명한다. INDEX schema 변경(`deferred` enum 추가)은 0006 abort 때와 동일한 이유로 보류.
- 미실행 deferred는 0006 abort와 다름: 0006은 governance check가 cycle을 막은 사례, 0007 deferred는 trigger 부재로 시작 자체를 안 한 사례.

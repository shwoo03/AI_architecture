# paperclip

## 기본 정보

- `name`: paperclip
- `url`: https://github.com/paperclipai/paperclip.git
- `source_type`: repository
- `status`: reviewing
- `searched_for`: AI agent company model, org chart, budgets, approvals, activity, routines, plugin system
- `created_at`: 2026-05-13
- `reviewed_at`: 2026-05-13
- `reviewer`: codex

## 왜 보는가

- `problem_statement`: v2 이후에는 단일 에이전트 도구가 아니라 여러 specialist를 운영 자산으로 관리해야 한다.
- `why_it_matters`: Paperclip은 agents, companies, goals, budgets, approvals, routines, activity, plugins를 조직 운영 모델로 묶는다.
- `expected_value`: 우리 스켈레톤의 agent registry, runtime ledger, approval, budget, team closeout 개념을 성숙한 운영 모델과 비교할 수 있다.

## 유용한 패턴

- `useful_patterns`:
  - agents를 org chart, roles, permissions, budgets로 관리한다.
  - mutating actions, approvals, comments, work products를 durable activity로 남긴다.
  - routines/schedules와 plugin system을 별도 시스템으로 분리한다.
- `what_to_copy_conceptually`:
  - specialist agent를 단순 helper가 아니라 운영 자산으로 기록하는 관점.
  - budget hard-stop, approval workflow, activity/audit trail 분리.
  - orphaned runs and recovery를 정상 운영 표면으로 다루는 방식.
- `what_not_to_copy`:
  - Node/Pnpm/Postgres product runtime을 기본 스켈레톤에 도입하지 않는다.
  - company/org model 전체를 현재 lightweight skeleton에 복제하지 않는다.
  - telemetry, server, UI, database migrations를 복사하지 않는다.

## 증거

- `evidence_summary`: README는 Paperclip을 agents as company model로 설명하고, identity/access, org chart, work/task, heartbeat execution, governance, budgets, routines, plugins, secrets, activity, portability를 핵심 시스템으로 제시한다.
- `local_clone_path`: ../AI_architecture_references/paperclip
- `checked_revision`: 42a299fb9d66fa0c136eae73bf166cad2c2c3e3e
- `freshness_signal`: tracked in references.yaml with local clone revision.
- `maintenance_signal`: README includes quickstart, development commands, roadmap, community, telemetry, and license.
- `documentation_signal`: README explains product boundaries and system components in detail.
- `validation_signal`: Local README and license were inspected; no code copied.
- `sources`:
  - {"path":"../AI_architecture_references/paperclip/README.md","kind":"readme","evidence":"Agent organization, governance, budgets, routines, and activity patterns were reviewed.","hash_or_line_ref":"local-reference"}
  - {"path":"../AI_architecture_references/paperclip/LICENSE","kind":"license","evidence":"License boundary reviewed.","hash_or_line_ref":"local-reference"}

## 리스크

- `license`: MIT
- `security_or_privacy_risk`: Paperclip's secrets, storage, user/company identity, and telemetry concepts require careful privacy boundaries.
- `maintenance_risk`: Product runtime can change faster than our skeleton rules.
- `complexity_risk`: Full org/company model is much heavier than current v1/v2 skeleton needs.
- `dependency_risk`: Node, pnpm, embedded Postgres, server/UI runtime conflict with stdlib-first skeleton.
- `fit_risk`: Use as governance and orchestration reference, not as direct implementation base.

## 적용 후보

- `applies_to`: docs | rules | skills | scripts | tests | runtime
- `target_files_or_areas`:
  - docs/AGENT_REGISTRY.md
  - runtime/agent-runs.jsonl
  - scripts/agent-brief.py
  - scripts/task-closeout.py
- `adoption_decision`: adapt
- `decision_reason`: Operational governance patterns fit, but product runtime and database model are out of scope.
- `next_action`: Use as reference for agent team ledger, budget/approval boundaries, and recovery semantics.

## 점수

| 기준 | 배점 | 점수 | 근거 |
| --- | ---: | ---: | --- |
| 문제 적합성 | 20 | 18 | Agent organization and governance match v2/v3 direction. |
| 구조 명확성 | 15 | 15 | README gives a strong system map and boundaries. |
| 검증 가능성 | 15 | 11 | Concepts are reviewable; runtime validation would require Node/Postgres. |
| 유지보수 신호 | 15 | 14 | Roadmap, dev commands, community, and product docs are present. |
| 흡수 비용 | 15 | 9 | Concept reuse is useful; direct adoption is too expensive. |
| 보안/라이선스 리스크 | 10 | 8 | MIT, but identity/secrets/telemetry are high-sensitivity areas. |
| 설명 가치 | 10 | 10 | Excellent reference for why agent teams need governance. |
| 합계 | 100 | 85 |  |

## Dry-Run 제안

- `proposal_needed`: yes
- `files_to_change`:
  - docs/AGENT_REGISTRY.md
  - scripts/agent-brief.py
  - runtime/agent-runs.jsonl
- `behavior_change`: Treat repeated specialist agents as governed runtime actors with audit, approval, and recovery metadata.
- `validation_plan`: python scripts/validate-reference-candidates.py && python scripts/validate-reference-proposals.py && python scripts/quality-gate.py --skip-tests --format json
- `rollback_or_stop_condition`: Stop if design requires DB/server/product runtime adoption instead of lightweight ledger contracts.
- `approval_required`: yes

## 최종 기록

- `final_status`: reviewing
- `implemented_in`:
  - not implemented
- `validation_result`: candidate card only
- `activity_log_entry`: not recorded
- `notes`: No code copied; use as governance reference for specialist team runtime.

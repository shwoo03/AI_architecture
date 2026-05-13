# oh-my-codex

## 기본 정보

- `name`: oh-my-codex
- `url`: https://github.com/Yeachan-Heo/oh-my-codex.git
- `source_type`: repository
- `status`: reviewing
- `searched_for`: Codex CLI workflow layer, skills, agents, prompts, runtime state, team orchestration
- `created_at`: 2026-05-13
- `reviewed_at`: 2026-05-13
- `reviewer`: codex

## 왜 보는가

- `problem_statement`: v2에서 specialist agent와 team workflow를 안전하게 운영하려면 Codex용 workflow layer 사례가 필요하다.
- `why_it_matters`: oh-my-codex는 Codex CLI를 실행 엔진으로 유지하면서 prompts, skills, plans, logs, state, team flow를 별도 runtime layer로 묶는다.
- `expected_value`: 우리 스켈레톤의 `agent-flow delegate`, closeout hygiene, runtime state, team orchestration 설계에 참고할 수 있다.

## 유용한 패턴

- `useful_patterns`:
  - Codex를 대체하지 않고 workflow layer를 얹는 구조.
  - 의도별 command surface를 분리하는 방식.
  - plans, logs, memory, runtime state를 별도 디렉터리에 모으는 운영 모델.
- `what_to_copy_conceptually`:
  - main agent가 계획과 팀 실행을 구분해서 routing하는 패턴.
  - team 실행을 기본값이 아니라 큰 작업용 선택지로 두는 기준.
  - setup, doctor, smoke 같은 readiness surface 분리.
- `what_not_to_copy`:
  - Node CLI runtime, tmux/HUD, native hook 설치를 기본 의존성으로 가져오지 않는다.
  - Codex global config나 user runtime을 스켈레톤이 직접 수정하지 않는다.
  - 전체 상태 모델을 그대로 복제하지 않는다.

## 증거

- `evidence_summary`: README는 OMX를 Codex CLI workflow layer로 설명하고, canonical skills, team mode, plans/logs/state, doctor/smoke/readiness flow를 제시한다.
- `local_clone_path`: ../AI_architecture_references/oh-my-codex
- `checked_revision`: 148effde4e7c6a35f5bdde3ecd5db3488b3156b5
- `freshness_signal`: local clone HEAD recorded; remote freshness requires refresh proposal review.
- `maintenance_signal`: README documents npm package, website, docs, plugin layout, setup/update flow, and maintainer table.
- `documentation_signal`: README links Getting Started, Agents, Skills, Integrations, Demo, OpenClaw guide, troubleshooting, and multilingual docs.
- `validation_signal`: Local README and license were inspected; no code copied.
- `sources`:
  - {"path":"../AI_architecture_references/oh-my-codex/README.md","kind":"readme","evidence":"Codex workflow layer and team orchestration patterns were reviewed.","hash_or_line_ref":"local-reference"}
  - {"path":"../AI_architecture_references/oh-my-codex/LICENSE","kind":"license","evidence":"License boundary reviewed.","hash_or_line_ref":"local-reference"}

## 리스크

- `license`: MIT
- `security_or_privacy_risk`: setup, hooks, global config, and runtime state can affect user environments if copied directly.
- `maintenance_risk`: Codex CLI/runtime behavior and plugin layout can change quickly.
- `complexity_risk`: tmux/HUD/team runtime is broader than this lightweight skeleton.
- `dependency_risk`: Node 20, npm package, tmux/psmux, and native hook assumptions conflict with stdlib-first skeleton defaults.
- `fit_risk`: Best fit is concept-only or small wrapper guidance, not direct runtime adoption.

## 적용 후보

- `applies_to`: docs | rules | skills | scripts | tests | runtime
- `target_files_or_areas`:
  - scripts/agent-flow.py
  - scripts/agent-brief.py
  - config/agent-team.yaml
  - runtime/agent-runs.jsonl
- `adoption_decision`: adapt
- `decision_reason`: Codex-oriented team workflow patterns are relevant, but direct runtime adoption would be too heavy.
- `next_action`: Use as a v2 delegation/team runtime reference when implementing agent-flow delegate and team aggregation.

## 점수

| 기준 | 배점 | 점수 | 근거 |
| --- | ---: | ---: | --- |
| 문제 적합성 | 20 | 19 | Codex workflow and team orchestration match v2 goals. |
| 구조 명확성 | 15 | 14 | README separates workflow, team, setup, doctor, and runtime state. |
| 검증 가능성 | 15 | 12 | Local source is inspectable; runtime behavior needs separate execution. |
| 유지보수 신호 | 15 | 14 | Maintainers, docs, npm, plugin notes, and troubleshooting are present. |
| 흡수 비용 | 15 | 10 | Concept reuse is cheap, runtime reuse is heavy. |
| 보안/라이선스 리스크 | 10 | 8 | MIT, but hooks/global config need care. |
| 설명 가치 | 10 | 10 | Explains what our v2 Codex team layer can become. |
| 합계 | 100 | 87 |  |

## Dry-Run 제안

- `proposal_needed`: yes
- `files_to_change`:
  - scripts/agent-flow.py
  - scripts/agent-brief.py
  - config/agent-team.yaml
- `behavior_change`: Add controlled delegation/team workflow while keeping Codex as the execution engine.
- `validation_plan`: python scripts/validate-reference-candidates.py && python scripts/validate-reference-proposals.py && python scripts/quality-gate.py --skip-tests --format json
- `rollback_or_stop_condition`: Stop if implementation starts modifying global Codex config, hook setup, or Node runtime assumptions.
- `approval_required`: yes

## 최종 기록

- `final_status`: reviewing
- `implemented_in`:
  - not implemented
- `validation_result`: candidate card only
- `activity_log_entry`: not recorded
- `notes`: No code copied; use as reference target for v2 specialist/team layer.

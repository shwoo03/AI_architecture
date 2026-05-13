# oh-my-claudecode

## 기본 정보

- `name`: oh-my-claudecode
- `url`: https://github.com/Yeachan-Heo/oh-my-claudecode.git
- `source_type`: repository
- `status`: reviewing
- `searched_for`: Claude Code multi-agent orchestration, plugin marketplace, workflows, specialist agent patterns
- `created_at`: 2026-05-13
- `reviewed_at`: 2026-05-13
- `reviewer`: codex

## 왜 보는가

- `problem_statement`: 우리 v2는 specialist subagent를 본격 활용해야 하므로 Claude Code 쪽 multi-agent orchestration 사례도 비교해야 한다.
- `why_it_matters`: oh-my-claudecode는 Claude Code 사용자에게 zero-learning-curve multi-agent orchestration과 plugin/marketplace 설치 경로를 제공한다.
- `expected_value`: Codex/Claude 호환 운영 표면, plugin install flow, team workflow naming, specialist routing 기준을 비교할 수 있다.

## 유용한 패턴

- `useful_patterns`:
  - marketplace/plugin install과 npm runtime path를 분리한다.
  - multi-agent orchestration을 사용자-facing workflow로 단순화한다.
  - migration guide와 multilingual docs로 adoption friction을 줄인다.
- `what_to_copy_conceptually`:
  - runtime 설치 경로와 plugin discovery 경로를 분리하는 문서화.
  - team workflow를 사용자가 이해하기 쉬운 command surface로 묶는 방식.
  - Claude와 Codex 양쪽에 같은 orchestration 경험을 맞추는 compatibility 관점.
- `what_not_to_copy`:
  - Claude Code plugin commands나 npm package를 기본 의존성으로 가져오지 않는다.
  - slash command UX를 우리 public command surface로 그대로 복제하지 않는다.
  - global Claude settings를 스켈레톤이 직접 수정하지 않는다.

## 증거

- `evidence_summary`: README는 multi-agent orchestration for Claude Code, plugin marketplace install, npm CLI fallback, docs/workflows/migration guide, Codex counterpart link를 제시한다.
- `local_clone_path`: ../AI_architecture_references/oh-my-claudecode
- `checked_revision`: 679b418f32409e6d0edecf5038fd2de460cfce04
- `freshness_signal`: local clone HEAD recorded; remote freshness requires refresh proposal review.
- `maintenance_signal`: README includes package badges, docs links, maintainer/collaborator tables, and known npm warning notes.
- `documentation_signal`: README links documentation, CLI reference, workflows, migration guide, Discord, and multiple translations.
- `validation_signal`: Local README was inspected; no code copied.
- `sources`:
  - {"path":"../AI_architecture_references/oh-my-claudecode/README.md","kind":"readme","evidence":"Claude Code multi-agent and plugin installation patterns were reviewed.","hash_or_line_ref":"local-reference"}
  - {"path":"../AI_architecture_references/oh-my-claudecode/LICENSE","kind":"license","evidence":"License boundary reviewed when present in local clone.","hash_or_line_ref":"local-reference"}

## 리스크

- `license`: MIT
- `security_or_privacy_risk`: plugin install and runtime setup can modify user-level Claude Code surfaces if copied directly.
- `maintenance_risk`: Marketplace/plugin APIs and package identity may change.
- `complexity_risk`: Full runtime adoption would add substantial command/plugin surface.
- `dependency_risk`: npm/native dependency warnings and runtime install assumptions do not fit stdlib-first defaults.
- `fit_risk`: Best used to compare Claude-facing orchestration, not as direct code source.

## 적용 후보

- `applies_to`: docs | rules | skills | scripts | tests | runtime
- `target_files_or_areas`:
  - docs/AGENT_REGISTRY.md
  - config/agent-team.yaml
  - scripts/agent-brief.py
  - scripts/agent-flow.py
- `adoption_decision`: adapt
- `decision_reason`: Multi-agent UX and plugin separation are useful, but direct install/runtime mechanics are out of scope.
- `next_action`: Use as comparison reference when designing cross-harness delegation and specialist role surfacing.

## 점수

| 기준 | 배점 | 점수 | 근거 |
| --- | ---: | ---: | --- |
| 문제 적합성 | 20 | 18 | Multi-agent orchestration directly matches v2. |
| 구조 명확성 | 15 | 13 | README clearly separates install, docs, workflows, migration. |
| 검증 가능성 | 15 | 11 | Local docs are inspectable; plugin behavior needs separate environment. |
| 유지보수 신호 | 15 | 14 | Badges, docs, collaborators, known issue notes are present. |
| 흡수 비용 | 15 | 10 | Concept reuse is manageable; runtime reuse is high cost. |
| 보안/라이선스 리스크 | 10 | 8 | MIT, but plugin/user settings need approval. |
| 설명 가치 | 10 | 9 | Helps define cross-harness v2 specialist team direction. |
| 합계 | 100 | 83 |  |

## Dry-Run 제안

- `proposal_needed`: yes
- `files_to_change`:
  - docs/AGENT_REGISTRY.md
  - config/agent-team.yaml
  - scripts/agent-flow.py
- `behavior_change`: Improve specialist orchestration UX without adopting Claude-specific plugin runtime.
- `validation_plan`: python scripts/validate-reference-candidates.py && python scripts/validate-reference-proposals.py && python scripts/quality-gate.py --skip-tests --format json
- `rollback_or_stop_condition`: Stop if changes imply automatic plugin install, global Claude settings writes, or uncontrolled subagent execution.
- `approval_required`: yes

## 최종 기록

- `final_status`: reviewing
- `implemented_in`:
  - not implemented
- `validation_result`: candidate card only
- `activity_log_entry`: not recorded
- `notes`: No code copied; use for cross-harness v2 delegation design.

# 외부 후보 기반 resume-safe checkpoint 제안 예시

## 상태

- `status`: proposed
- `created_at`: 2026-04-27
- `candidate_card`: `research/reference-candidates/2026-04-27-langgraph.md`
- `proposal_type`: reference_adoption_dry_run
- `approval_required`: yes
- `decision_source`:

## 한 문장 정의

이 제안서는 특정 프레임워크를 도입하려는 계획이 아니라, 외부 후보에서 발견한 durable execution 계열 개념을 우리 스켈레톤에 맞는 작은 운영 규칙으로 번역하는 절차 예시입니다.

## 근거

현재 스켈레톤은 `runtime/state/session-handoff.md`와 `runtime/activity-log.jsonl`로 재개 가능성을 확보합니다. 다만 긴 작업이 중간에 끊겼을 때 다음 세션이 다음을 명확히 판단할 수 있는 규칙은 아직 가볍습니다.

- 마지막으로 안전하게 완료된 지점이 어디인지
- 다시 실행하면 안 되는 부작용이 무엇인지
- 이미 기록된 결과를 재사용해야 하는지
- 사람 승인 대기 상태인지, 단순 중단 상태인지

이 제안은 LangGraph 후보 카드에서 확인한 durable execution 개념을 사용해 **외부 후보 카드 -> dry-run 제안** 변환 절차를 보여주는 예시입니다. LangGraph 패키지, 그래프 런타임, LangChain/LangSmith 의존성을 추가하지 않습니다.

Source-backed evidence:

- {"path":"research/reference-candidates/2026-04-27-langgraph.md","kind":"candidate_card","evidence":"Example candidate card anchors this dry-run proposal.","hash_or_line_ref":"candidate-card"}

## 적용하지 않을 것

- LangGraph 설치 또는 런타임 의존성 추가
- 기존 운영 루프를 그래프 노드/엣지 구조로 재작성
- LangSmith, LangChain, 외부 checkpoint store 기본 채택
- 자동으로 세션 상태를 복원하거나 파일 쓰기를 재실행하는 기능
- 이 예시를 곧바로 실제 운영 문서 변경으로 간주하는 것

## 모듈형 흡수 판단

- `absorption_mode`: concept_only
- `recommended_mode`: LangGraph 패키지나 graph runtime은 쓰지 않고 durable execution, checkpoint, idempotent side effect 개념만 운영 문서로 번역한다.
- `reuse_boundary`: 의존성, wrapper, partial copy 모두 제외한다. 반영 범위는 세션 연속성, 운영 루프, 런타임 이벤트 문서의 규칙 문구로 제한한다.
- `direct_implementation_reason`: 실제 checkpoint runtime을 구현하지 않는다. 현재 목표는 장기 실행 프레임워크 구축이 아니라 세션 인수인계 규칙 강화다.

흡수 방식 판단:

- 의존성 사용: 제외. 공용 스켈레톤 기본 의존성을 늘리지 않는다.
- wrapper 사용: 제외. LangGraph API를 호출할 런타임 요구가 없다.
- 일부 코드 복사: 제외. 필요한 것은 코드가 아니라 운영 개념이다.
- 개념 번역: 채택. resume-safe checkpoint와 side effect 재실행 방지 규칙만 번역한다.
- 직접 구현: 제외. 런타임 checkpoint 엔진은 이번 범위 밖이다.

## 제안 변경

### 1. 세션 인수인계에 resume-safe checkpoint 개념 추가

대상: `docs/SESSION_CONTINUITY.md`

추가할 내용:

- 긴 작업 인수인계에는 "마지막 안전 지점"을 적는다.
- 파일 쓰기, API 호출, 로그 append, Notion 업데이트처럼 재실행하면 중복될 수 있는 부작용을 별도 항목으로 적는다.
- 다음 세션은 부작용을 재실행하기 전에 이미 완료됐는지 확인한다.
- 사람 승인 대기 상태는 단순 작업 중단과 구분한다.

예상 문구 방향:

```text
긴 작업을 넘길 때는 마지막 안전 checkpoint와 재실행하면 안 되는 side effect를 함께 적습니다. 다음 세션은 그 지점 이후부터 이어가되, 파일 쓰기·API 호출·로그 append·Notion 업데이트는 먼저 완료 여부를 확인합니다.
```

### 2. 운영 루프에 idempotent side effect 확인 추가

대상: `docs/OPERATING_LOOP.md`

추가할 내용:

- 실행 단계 전에 재시도 가능한 작업과 재시도하면 안 되는 작업을 구분한다.
- 검증 단계에서 "재실행 안전성"을 확인한다.
- 결정 단계에서 중단/재설계 판단 시 부작용 중복 위험을 고려한다.

예상 문구 방향:

```text
쓰기 작업, 외부 API 호출, 로그 append처럼 부작용이 있는 행동은 재시도 전에 idempotent한지 확인합니다. idempotent하지 않다면 완료 여부를 먼저 조회하거나 사용자에게 확인합니다.
```

### 3. 런타임 이벤트에 선택 필드 추가

대상: `docs/RUNTIME_EVENT_SCHEMA.md`

추가할 선택 필드:

| 필드 | 언제 쓰나 | 예시 값 |
| --- | --- | --- |
| `checkpoint` | 긴 작업의 재개 기준점 기록 | `{"safe_point":"candidate card written","resume_from":"dry-run proposal"}` |
| `side_effects` | 재실행하면 중복될 수 있는 작업 기록 | `["notion_update_pending","activity_log_appended"]` |
| `approval_state` | 사람 승인 대기 여부 기록 | `"pending_user_approval"` |

이 필드는 필수가 아니라 선택 필드입니다. 기존 로그와 호환되어야 합니다.

## 기대 효과

- 다음 세션이 어디서 재개해야 하는지 더 명확해집니다.
- 같은 파일 쓰기, 로그 append, Notion 업데이트를 중복 실행할 위험이 줄어듭니다.
- 외부 사례를 "프레임워크 도입"이 아니라 "작은 운영 원칙"으로 흡수하는 흐름이 검증됩니다.
- 후보 카드에서 dry-run 제안으로 넘어가는 end-to-end 절차가 실제 예시로 남습니다.

## 위험

- 문서가 지나치게 복잡해질 수 있습니다.
- checkpoint라는 용어가 실제 런타임 저장소 기능처럼 오해될 수 있습니다.
- 모든 작업에 side effect 목록을 강제하면 운영 부담이 커질 수 있습니다.
- 예시 후보가 특정 프레임워크 도입 계획처럼 보일 수 있습니다.

완화:

- 필수 필드가 아니라 "긴 작업/외부 부작용이 있는 작업"에만 적용한다고 명시합니다.
- 외부 후보는 개념 참고용 예시이며, 특정 프레임워크 도입이 아니라고 문서 앞부분에 명시합니다.
- 자동화 구현은 이번 제안 범위 밖으로 둡니다.

## 검증 계획

승인 후 실제 반영 작업에서는 다음을 실행합니다.

```powershell
python scripts/verify-skeleton.py
python scripts/validate-reference-candidates.py
python scripts/validate-reference-proposals.py
python scripts/list-open-questions.py --count
```

문서 변경만 포함하므로 `unittest` 전체 실행은 필수는 아니지만, `verify-skeleton`이 깨지면 중단합니다.

## 롤백 또는 중단 조건

다음 중 하나라도 해당하면 적용하지 않습니다.

- 문서가 특정 프레임워크 채택으로 읽힙니다.
- checkpoint 규칙이 모든 작은 작업에 강제되는 것처럼 보입니다.
- 기존 세션 인수인계 규칙보다 읽기 어려워집니다.
- 사용자 승인 없이 실제 운영 문서를 수정하려는 흐름이 됩니다.

## 승인 후 실제 변경 범위

승인되면 다음 파일만 수정합니다.

- `docs/SESSION_CONTINUITY.md`
- `docs/OPERATING_LOOP.md`
- `docs/RUNTIME_EVENT_SCHEMA.md`
- 필요 시 후보 카드의 최종 기록

`scripts/`, `.claude/skills/`, `codex/agents/`는 이번 제안 범위에 포함하지 않습니다.

## 최종 결정 기록

- `decision`: pending
- `decided_at`:
- `decided_by`:
- `decision_source`:
- `applied_in`:
- `validation_result`:

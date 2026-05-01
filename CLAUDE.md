<!-- 목표: 얇은 Claude Code 진입점으로 유지합니다. 자세한 방법론은 docs/와 rules/에 둡니다. -->

# Claude 프로젝트 가이드

## 한 문장 정의

이 문서는 Claude Code가 이 프로젝트를 시작할 때 읽는 얇은 진입점이며, 프로젝트 목표를 확인하고 공통 운영 규칙으로 연결하는 역할을 합니다.

## 무엇을 하는가

프로젝트별 사실과 공통 방법론을 분리합니다. 목표·제약·성공 기준은 프로젝트 프로필에서, 반복 규칙과 절차는 공통 문서와 스킬에서 읽습니다.

## 먼저 읽을 것

`AGENTS.md`의 "먼저 읽을 것"과 같은 순서입니다.

1. `docs/PROJECT_PROFILE.md` — 비어 있으면 바로 "대화 시작"으로.
2. `rules/common/README.md` — 공통 규칙.
3. `docs/OPERATING_LOOP.md` — 계획·실행·검증·결정 루프.
4. `docs/SESSION_CONTINUITY.md` — 인수인계 프로토콜. 이어받으면 `runtime/state/session-handoff.md` 먼저.

## 대화 시작

사용자가 "시작하자" 같은 짧은 말만 해도 **대기하지 않고 먼저 질문**합니다. PROJECT_PROFILE의 `primary_goal`/`success_criteria`/`failure_definition` 중 하나라도 비어 있으면 바로 시작.

- 첫 질문 예: "이 프로젝트가 끝났을 때 최종 사용자가 무엇을 할 수 있게 돼야 하나요?"
- 한 번에 한두 개만 묻고 답을 반영 후 다음으로.
- 모르면 `[NEEDS CLARIFICATION: <질문>]`로 두고 진행 (형식 정의: `rules/common/README.md`의 "모르는 사실 표시 규칙").
- 전체 순서: `docs/PROJECT_PROFILE.template.md` Agent Fill-In Contract.

## 스킬 활성화

작업이 `.claude/skills/<skill>/SKILL.md`의 활성 조건과 맞으면 SKILL.md를 먼저 읽고 실행합니다. 없으면 공통 규칙·운영 루프로 진행. 프로젝트 스킬은 `<project>/.claude/skills/`, 사용자 전역은 `~/.claude/skills/` (skeleton 관리 밖). 이름 충돌 시 프로젝트 로컬 우선.

## 운영 규칙

- 이 파일은 얇게 유지합니다 (60줄 이내). 전체 운영 규칙은 `AGENTS.md`가 canonical.
- 프로젝트별 사실은 프로필에, 공통 방법론은 공통 규칙·스킬에.
- 장기 지식은 직접 수정하지 말고 제안으로 남깁니다.
- 주요 실행 증거는 활동 로그에 (`scripts/hooks/post-tool-use-log.py` 또는 `runtime/activity-log.jsonl` append), 세션 종료·큰 작업 완료 시 인수인계 갱신 (`handoff_saved` 이벤트 포함).

## 구현 연결 정보

- 공유 진입점: `AGENTS.md`
- 프로젝트 프로필: `docs/PROJECT_PROFILE.template.md`
- 운영 루프: `docs/OPERATING_LOOP.md`
- 세션 연속성: `docs/SESSION_CONTINUITY.md`
- 기능 결정: `docs/FEATURE_DECISION_GUIDE.md`
- 문서화 스타일: `docs/DOCUMENTATION_STYLE_GUIDE.md`
- 스켈레톤 업그레이드: `docs/SKELETON_UPGRADE.md`
- 건강 체크: `scripts/verify-skeleton.py`

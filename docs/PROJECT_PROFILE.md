# 프로젝트 프로필

## 기본 정보

- `project_name`: common-ai-architecture
- `domain`: AI agent operating skeleton
- `owner`: TBD
- `status`: active
- `created_at`: 2026-04-27

## 목표

- `primary_goal`: 좋은 외부 사례를 찾아 검증하고, 승인된 패턴만 문서·규칙·스킬·스크립트로 흡수할 수 있는 공용 AI 운영 스켈레톤을 만든다.
- `target_users`: AI 프로젝트를 시작하거나 이어받는 사용자, Codex/Claude 같은 코딩 에이전트, 반복 운영 절차를 정리하는 프로젝트 관리자.
- `success_criteria`: `python scripts/verify-skeleton.py`가 통과하고, 새 프로젝트가 프로필 기반으로 시작되며, 주요 운영 변경이 활동 로그와 세션 인수인계에 남고, 외부 사례는 후보 카드와 dry-run 제안 없이 바로 장기 규칙으로 승격되지 않는다.
- `failure_definition`: 목표·성공 기준 없이 에이전트가 임의로 구현하거나, 출처와 검증 없이 외부 구조를 복사하거나, 검증/로그/인수인계 없이 스켈레톤 운영 규칙이 바뀌면 실패로 본다.
- `non_goals`: 특정 앱 하나의 기능 구현, 외부 프레임워크 전체 복제, 사용자 승인 없는 자동 문서 수정, 장기 지식의 무근거 자동 생성은 범위 밖이다.

## 프로젝트별 맥락

- `stack`: Markdown 운영 문서, Python 표준 라이브러리 스크립트, JSONL 런타임 로그, Codex/Claude 에이전트 규칙.
- `runtime_environment`: Windows/PowerShell 로컬 작업 공간을 기본으로 하며, 새 프로젝트 복사본에서도 Python 3.9 이상으로 검증 가능해야 한다.
- `data_sources`: 로컬 문서와 런타임 로그, Notion을 사용하는 프로젝트의 데이터베이스 페이지, 사용자가 승인한 외부 저장소·공식 문서·기술 글 후보 카드.
- `external_dependencies`: 기본 검증과 운영 스크립트는 외부 패키지 없이 동작해야 한다. 인터넷 검색, GitHub API, Notion 연동은 필요할 때 별도 승인과 dry-run을 거친다.
- `security_or_privacy_constraints`: API 키, 토큰, CTF flag, 개인정보는 문서와 로그에 원문으로 남기지 않는다. 외부 코드나 문구를 가져올 때는 라이선스와 출처를 확인한다.
- `compatibility_constraints`: 기존 프로젝트에 스켈레톤을 얹을 때 사용자 코드와 런타임 소유 설정을 덮어쓰지 않는다. 자동화는 기본적으로 dry-run 또는 검증 중심이어야 한다.
- `project_specific_notes`: 루트 작업 폴더는 현재 Git 저장소가 아닐 수 있다. 테스트 일부는 스켈레톤 바깥 쓰기 가능한 임시 경로가 없으면 skip될 수 있다.

## 활성 운영 선택

- `active_workflows`: 프로젝트 부트스트랩, 마이크로 검증, 스킬 생성, 외부 사례 탐색.
- `active_skills`: brainstorming, code-review-expert, web-design-guidelines, writing-skills 등 프로젝트 로컬 스킬과 필요 시 전역 스킬.
- `active_rules`: 공통 코드 스타일, 디렉터리 레이아웃, 임시 파일 수명, MCP discipline, Notion 중복 방지.
- `validation_summary`: 기본 구조 검증은 `python scripts/verify-skeleton.py`로 수행한다. 미해결 질문은 `python scripts/list-open-questions.py --count`로 확인한다.
- `pivot_summary`: 외부 후보가 후보 카드 없이 장기 규칙으로 승격되거나, 검증 없이 자동화가 쓰기 작업을 하려 하면 중단하고 dry-run 제안으로 되돌린다.

## 첫 반복 체크리스트

- [x] 목표가 한 문장으로 쓰였습니다.
- [x] 성공 기준과 실패 기준이 측정 가능합니다.
- [x] 기술 스택과 제약 조건이 명확합니다.
- [x] 모르는 항목은 명시적 보류용 `TBD`로 표시했습니다.
- [x] 이미 아는 경우에만 활성 스킬과 워크플로를 적었습니다.
- [x] 이미 아는 경우에만 마이크로 검증을 요약했습니다.
- [x] 프로젝트별 예외가 있다면 문서화했습니다.

## Automation Ownership

- `execution_owner`: agent
- `user_role`: goals, constraints, approvals, rejections, and direction changes through chat
- `agent_role`: discover references, update files, run local validation commands, record activity logs, update handoff state, and preserve provenance
- `manual_user_commands`: exceptional only; use when the agent cannot access the required environment or permission boundary
- `completion_rule`: a task is not complete because the user was told which command to run; it is complete when the agent has run feasible validation itself and recorded the result

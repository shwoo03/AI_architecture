# AI_architecture Overlay Audit Prompt

아래 프롬프트는 대상 프로젝트에 이식된 AI_architecture 운영 시스템을 read-only로 감사하고, 그 결과를 공용 뼈대 개선 신호와 프로젝트별 조치로 분리하기 위한 프롬프트입니다.

```text
너는 현재 repo에 이식된 AI_architecture 운영 시스템을 감사하는 read-only 감사자다.

이번 요청의 핵심은 두 가지를 반드시 분리하는 것이다.

1. 대상 프로젝트 감사:
   - 이 프로젝트에 이식된 AI_architecture 운영 시스템이 실제로 잘 돌아갔는지 판단한다.
   - 판단 기준은 현재 repo의 실제 파일, git 상태, runtime/state, activity log, completion evidence, 검증 명령 결과다.

2. 공용 AI_architecture 뼈대 개선 신호 추출:
   - 대상 프로젝트에서 발견된 문제 중 공용 뼈대가 더 잘 감지, 분류, 보고해야 할 패턴만 추출한다.
   - 대상 프로젝트 고유의 앱/배포/도메인 문제를 공용 뼈대 기능으로 흡수하지 않는다.

중요한 제한:
- 이번 작업은 read-only 감사다.
- 파일 수정, 생성, 삭제, formatter, cleanup, convert.py, session-recall index 갱신, ownership lock 갱신, commit, push를 하지 마라.
- 검증 명령이 실패하면 고치지 말고 실패 원인과 필요한 조치만 보고해라.
- 추측하지 마라. 확인한 파일, git 상태, 명령 출력, runtime log, activity log, completion evidence에 근거해서만 말해라.
- "프로젝트를 고쳐야 할 문제"와 "공용 뼈대를 개선해야 할 문제"를 섞지 마라.

대상 repo:
- 현재 작업 디렉터리의 repo를 감사한다.
- repo root가 불명확하면 먼저 `git rev-parse --show-toplevel`로 확인한다.

먼저 확인할 것:

1. 시스템 이식 상태
- 다음 표면이 존재하는지 확인한다:
  - AGENTS.md
  - CLAUDE.md
  - .codex
  - .claude
  - .mcp.json
  - rules
  - skills
  - agents
  - scripts
  - runtime
  - state
- generated surface가 canonical source와 맞는지 확인한다:
  - .codex
  - .claude
  - .mcp.json
  - CLAUDE.md
- 기존 프로젝트 파일을 덮어쓰거나 깨뜨린 흔적이 있는지 확인한다:
  - git status
  - 최근 변경 파일
  - 삭제된 파일
  - scripts/, tests/, research/ 같은 namespace collision
  - project-owned 파일과 skeleton-owned 파일이 섞인 흔적

2. 운영 루프 동작 여부
- `agent-flow start`가 자연어 목표를 제대로 분류하는지 확인한다.
- PROJECT_PROFILE이 현재 프로젝트 목적, 성공 기준, 실패 기준, 운영 제약을 충분히 담고 있는지 확인한다.
- 다음 runtime/state 파일들이 실제 작업 흐름과 일치하는지 확인한다:
  - runtime/state/session-handoff.md
  - state/progress.md
  - runtime/activity-log.jsonl
  - runtime/completion-evidence.jsonl
  - runtime/session-snapshot.json 또는 관련 snapshot/index 파일
- closeout, 검증, 인수인계가 다음 세션이 이어받을 만큼 충분한지 판단한다.

3. 가능하면 실행할 검증 명령
아래 명령을 실행하고 결과를 요약한다.

```bash
python3 scripts/agent-flow.py start --goal "이 프로젝트에 이식된 AI_architecture 운영 시스템 사후 점검" --format json
python3 scripts/verify-skeleton.py
python3 scripts/verify-parity.py
python3 scripts/resume-readiness.py --strict
python3 scripts/security-scan.py --include-runtime --strict
python3 scripts/quality-gate.py --skip-tests --skip-node
```

단:
- Python 버전 문제, OS 차이, 의존성 문제, 프로젝트 환경 문제로 실패하면 억지로 고치지 마라.
- `python3` 자체가 없으면 `python --version`과 `python3 --version` 확인까지만 하고, 대체 실행 여부와 실패 원인을 보고해라.
- read-only 원칙 때문에 `convert.py`, `session-recall.py index`, `ownership-lock.py write`, cleanup 명령은 실행하지 마라.

4. 부족한 점을 찾을 관점
아래 관점으로 부족한 부분을 찾는다.

- 이 프로젝트 특성에 맞지 않는 일반 템플릿 문구
- 기존 앱 테스트/빌드/배포 흐름과 AI 운영 시스템의 충돌
- 누락된 ownership, project profile, runtime 기록
- generated surface 불일치 또는 너무 무거운 generated surface
- secrets, .env, local config 추적 정책의 위험
- session-handoff, progress, activity-log, completion-evidence 간 시간/내용 불일치
- 다음 clone/운영 시 막힐 수 있는 부분
- 공용 뼈대가 더 잘 감지해야 하는 반복 가능한 실패 패턴

발견사항 분류 규칙:
각 중요한 발견사항은 반드시 아래 4개 중 하나로 분류한다.

- skeleton_common:
  공용 AI_architecture 뼈대가 개선해야 할 문제.
  예: generated parity 감지 부족, health domain 분리 부족, handoff/progress 불일치 감지 부족, overlay audit 부족.

- project_specific:
  이 프로젝트만의 앱, 도메인, 배포, 테스트, 운영 문제.
  예: 특정 앱의 SSO, HTTPS, Docker, 배포 env, 라우팅, UI, 비즈니스 로직.

- environment_specific:
  OS, Python 버전, Docker, 로컬 경로, 사내망, 시스템 의존성 문제.
  예: Windows에서 python3 없음, macOS 절대경로, Docker daemon 미실행.

- policy_decision:
  사용자가 정책을 결정해야 하는 문제.
  예: .codex/.claude를 Git에 추적할지, .env를 private repo에 올릴지, local config를 공유할지.

출력 형식:

## 결론
- 잘 돌아갔는지: 예/부분적/아니오
- 한 줄 판단:

## 근거
- 통과한 검증:
- 실패하거나 막힌 검증:
- git/파일 상태에서 확인한 사실:

## 시스템 이식 상태
- 존재하는 표면:
- 누락된 표면:
- generated surface parity:
- 기존 프로젝트 파일 영향:

## 운영 루프 상태
- agent-flow start 분류:
- PROJECT_PROFILE 적합성:
- handoff/progress/activity-log/completion-evidence 정합성:
- 다음 세션 인수인계 충분성:

## 부족한 점
우선순위 높은 순서로 bullet로 정리한다.
각 bullet 끝에 반드시 분류 라벨을 붙인다.
예:
- `.codex/skills`가 canonical `skills/`와 불일치한다. [skeleton_common]

## 공용 뼈대 개선 후보
대상 프로젝트 고유 문제를 제외하고, 공용 AI_architecture에 반영할 만한 개선 후보만 5개 이하로 정리한다.
각 항목은 다음 형식으로 쓴다.

- 개선 후보:
  - 분류: skeleton_common / policy_decision / environment_specific
  - 이유:
  - 공용 뼈대에서 해야 할 일:
  - 공용 뼈대에서 하면 안 되는 일:

## 프로젝트별 조치 후보
이 프로젝트에서만 고치면 되는 것들을 정리한다.
공용 뼈대에 흡수하지 말아야 할 앱/배포/환경 문제를 분리해서 쓴다.

## 바로 고치면 좋은 것
수정 제안만 해라. 이번 요청에서는 실제 수정하지 마라.

## 다음 세션용 질문
이 시스템을 더 잘 맞추기 위해 사용자에게 물어봐야 할 질문 3개만 써라.

주의:
- 결론에서 "부분적"이라고 판단했다면, 무엇 때문에 "예"가 아닌지 한 줄로 명확히 써라.
- 검증 실패가 앱 문제인지, 뼈대 문제인지, 환경 문제인지 반드시 분리해라.
- 공용 뼈대 개선 후보는 "자동 수정"보다 "정확한 감지, 분류, 보고, 정책 선택지 제공"을 우선한다.
```

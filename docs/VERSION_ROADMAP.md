# Version Roadmap

## 한 문장 정의

이 문서는 v1/v2를 폴더나 운영 문서의 분리 기준으로 쓰지 않고, 각 기능의 maturity tier를 기준으로 개발과 overlay 범위를 관리하는 짧은 로드맵입니다.

## Source of truth

기능별 현재 상태의 단일 진실 소스는 `docs/feature-status.yaml`입니다. 이 문서는 tier의 의미와 승격 기준만 설명하고, 기능별 상세 상태를 중복 기재하지 않습니다.

## Maturity tier

- `stable`: 기본 closeout과 기존 프로젝트 overlay에 포함될 수 있는 기능입니다.
- `incubating`: v2 후보 기능입니다. 기본 stable closeout을 막지 않으며 명시적 opt-in에서만 overlay 대상으로 봅니다.
- `experimental`: SDK/LangGraph 같은 future adapter입니다. core dependency가 아니며 명시 승인 없이는 적용하지 않습니다.
- `deprecated`: 제거 또는 대체 경로가 정해진 기능입니다.

## 현재 방향

v1은 stable agent-governed project scaffold입니다. v2는 lightweight specialist team OS를 incubating tier로 실험합니다. SDK/LangGraph 통합은 v2 core가 아니라 experimental adapter로 둡니다.

## Stable 승격 기준

incubating 기능은 다음 조건을 모두 만족해야 stable 승격 후보가 됩니다.

- 운영 증거가 충분해야 합니다. 예: 30회 이상 실행 기록과 낮은 closeout failure 비율.
- schema가 일정 기간 breaking change 없이 유지되어야 합니다.
- 루트 운영 문서에서 사용법이 설명되어야 합니다.
- rollback 또는 비활성화 경로가 있어야 합니다.
- ADR 또는 결정 기록에 승격 이유와 잔여 위험이 남아야 합니다.

## Overlay 정책

기존 프로젝트 적용은 기본적으로 `stable` profile을 사용합니다. `incubating`이나 `all` profile은 사용자가 해당 tier의 변경 가능성과 승인 필요성을 이해하고 opt-in할 때만 사용합니다.

# Secrets

- 절대 코드·로그·plan에 평문 시크릿 쓰지 말 것
- 기본은 `.env.template`을 공유하고 `.env`는 로컬에 둔다
- 사용자가 private repo mirror와 `.env` 포함을 명시 승인한 경우에는 `.env`도 커밋 가능
  - 이 경우에도 에이전트 응답, 활동 로그, 리뷰에는 평문 시크릿 값을 출력하지 않는다
  - public 전환 또는 외부 공유 전에는 `.env` 포함 여부를 다시 검토한다
- API 키는 환경변수 또는 시크릿 매니저 참조
- 시크릿 노출 시 즉시 회전 + state/decisions.md에 기록

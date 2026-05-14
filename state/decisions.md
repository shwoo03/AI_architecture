# Decisions (append-only)

> 형식: `## YYYY-MM-DD HH:MM — <결정 요약>` 다음 줄에 근거.
> 절대 이전 결정을 수정/삭제하지 말 것. 번복은 새 항목으로 추가.

## {{INIT_TIMESTAMP}} — 골격 부트스트랩
- 사용 골격: v1.2.0
- 모드: codex-primary (v1)
- 향후 v2 전환 가능 (docs/role-migration.md)

## 2026-05-14 16:39 — 0006 stated goal achieved via housekeeping; delegate execution aborted on role-registry gap
- Plan 0006의 stated goal (smoke artifact policy 문서화 + 5개 brief 분류)은 operator housekeeping으로 달성.
- Delegate execution path는 `docs-sync-auditor` (read_only specialist) + `--write-policy write_with_confirmation` 조합에서 시스템이 정상적으로 broaden 거부 -> cycle abort.
- 우회하지 않음. 이건 1e 회귀가 아니라 role registry coverage gap의 첫 증거.

## 2026-05-14 16:39 — Write-heavy delegate cycle friction goal remains OPEN; deferred to post-0008
- 원래 0006의 메타 목표였던 "write-side friction 데이터 수집"은 미달성.
- 0007 (role registry audit, read-only) -> 0008 (최소 docs-write role 추가) 완료 후, 새 slice로 재시도 예정.
- 그 전에는 routing / validator-loop 등 상위 슬라이스 진행 금지(같은 gap에 다시 막힐 위험).

## 2026-05-14 16:39 — Aborted status enum deferred until governance-driven cycle abort 누적 2건 이상
- INDEX schema에 `aborted` status enum 도입은 데이터가 충분히 모일 때까지 보류.
- Trigger 정의: **governance/policy/schema constraint가 정상 작동해서 cycle을 중단시킨 사례**가 누적 2건 이상. 0006이 1건째.
- 카운트 안 되는 것: 단순 구현 실패, 환경 문제, race condition 발견, 사용자가 마음 바꿔서 중단한 경우.

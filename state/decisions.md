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

## 2026-05-15 01:09 — AI_architecture repo 작업 freeze (외부 실사용 trigger 도래 시 resume)
- v1은 운영 OS 수준까지 완성, v2는 incubating 골격까지 완성. 최근 7-8 commit이 대부분 self-referential infra 작업이었고 실사용 데이터는 read-only audit 1건뿐.
- 0007 role registry audit은 정당한 plan이지만 "뭐라도 더 하자"의 편의 옵션이 될 위험이 큼. 외부 실데이터 없이 진행하면 또 한 라운드의 self-improvement loop.
- 외부 프로젝트 후보(ENKI_WIKI, 0-day, ctf-forge 등)는 있으나 현재 자연 발생한 active task는 없음. "외부 적용 실험"도 active task 없이 시작하면 인위적 dogfooding.
- 따라서 결정: 이 repo에 추가 commit 하지 않음. 다음에 진짜 외부 프로젝트 X에서 작업이 발생하면 그때 v1 stable overlay 시도하고, 그 사용 중 발견한 friction만 가져와서 resume.
- 0007 plan은 `plans/active/`에 보존되며 본문에 `Status: Deferred`로 표시. INDEX schema는 변경하지 않음.
- 이 freeze는 "포기"가 아니라 "외부 trigger 대기". resume 조건은 외부 프로젝트 X에서의 실 작업 발생.

## 2026-05-15 03:58 — Freeze exception accepted for ENKI_WIKI stable overlay migration
- External trigger condition is now satisfied: user requested applying the AI_architecture stable system to .
- Scope is limited to overlay release hardening required for deterministic stable migration, followed by stable safe-only application to ENKI_WIKI.
- Deferred v2 work remains frozen: 0007 role registry audit, routing, validator-loop, non-terminal status, and delegate improvements stay out of scope.

## 2026-05-15 04:02 — Correction: ENKI_WIKI freeze exception target path
- The previous ENKI_WIKI freeze-exception entry was affected by shell command substitution while writing handoff text and lost the literal target path in one bullet.
- Correct target path: ~/mydir/ENKI_WIKI.
- Scope remains unchanged: stable overlay release hardening plus safe-only application; deferred v2 slices remain frozen.

# Plans Index

| seq | slug | status | created | replan | depends_on |
|-----|------|--------|---------|--------|------------|
| 0001 | phase-1d-1-changed-paths-validation | done | 2026-05-14 | 0 | phase-1c (agent-run-ledger v2-only) |
| 0002 | phase-1d-2-retry-idempotency | done | 2026-05-14 | 0 | phase-1d-1 (changed_paths validation) |
| 0003 | phase-1d-3-aggregation-summary | done | 2026-05-14 | 0 | phase-1d-2 (retry/idempotency) |

## 라이프사이클
- active/  : 진행 중
- done/    : 완료
- failed/  : 3회 재계획 실패 (회생 가능성 검토 대상)

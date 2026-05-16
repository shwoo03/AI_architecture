# Plans Index

| seq | slug | status | created | replan | depends_on |
|-----|------|--------|---------|--------|------------|
| 0001 | phase-1d-1-changed-paths-validation | done | 2026-05-14 | 0 | phase-1c (agent-run-ledger v2-only) |
| 0002 | phase-1d-2-retry-idempotency | done | 2026-05-14 | 0 | phase-1d-1 (changed_paths validation) |
| 0003 | phase-1d-3-aggregation-summary | done | 2026-05-14 | 0 | phase-1d-2 (retry/idempotency) |
| 0004 | phase-1e-incubating-delegate-entrypoint | done | 2026-05-15 | 0 | phase-1d-3 (aggregation summary) |
| 0005 | phase-1e-followup-workflow-aware-completion-command | done | 2026-05-15 | 0 | phase-1e (delegate entrypoint) |
| 0006 | write-cycle-smoke-artifact-policy | done | 2026-05-15 | 0 | phase-1e-followup (workflow-aware completion_command) |

## 라이프사이클
- active/  : 진행 중
- done/    : 완료
- failed/  : 3회 재계획 실패 (회생 가능성 검토 대상)
| 0007 | role-registry-audit | active | 2026-05-15 | 0 | 0006 (delegate abort revealing role registry gap) |
| 0008 | ownership-aware-upgrade-v1 | done | 2026-05-15 | 0 | external overlay correctness / ENKI migration readiness |
| 0009 | ownership-classifier-synthetic-tests | done | 2026-05-15 | 0 | 0008 (ownership model spec and default map) |
| 0010 | ownership-skeleton-self-classification | done | 2026-05-15 | 0 | 0009 (classifier library and synthetic tests) |
| 0011 | ownership-verify-upgrade-integration | done | 2026-05-15 | 0 | 0010 (skeleton self-classification lock) |
| 0012 | ownership-initialize-report | done | 2026-05-15 | 0 | 0011 (ownership-aware verify/upgrade integration) |
| 0013 | enki-ownership-initialize-dry-run | active | 2026-05-15 | 0 | 0012 (ownership initialize report tool) |
| 0014 | specialist-overlay-audit | done | 2026-05-16 | 0 | 0006 delegate abort evidence + 2026-05-16 freeze exception |
| 0015 | specialist-overlay-loader | done | 2026-05-16 | 0 | 0014 (specialist overlay audit) |
| 0016 | specialist-proposal-add | done | 2026-05-16 | 0 | 0015 + implementation exception |
| 0017 | orchestration-preview | done | 2026-05-16 | 0 | 0016 proposal schema |
| 0018 | execution-loop | done | 2026-05-16 | 0 | 0017 DelegationPlan interface |
| 0019 | session-recall-hardening | done | 2026-05-16 | 0 | existing session-recall operational tool |
| 0020 | specialist-usage-evidence-ledger | done | 2026-05-16 | 0 | 0017 DelegationPlan + 0018 execute boundary |

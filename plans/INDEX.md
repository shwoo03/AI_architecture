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
| 0007 | role-registry-audit | done | 2026-05-15 | 0 | closed deferred_unimplemented; see plan body |
| 0008 | ownership-aware-upgrade-v1 | done | 2026-05-15 | 0 | external overlay correctness / ENKI migration readiness |
| 0009 | ownership-classifier-synthetic-tests | done | 2026-05-15 | 0 | 0008 (ownership model spec and default map) |
| 0010 | ownership-skeleton-self-classification | done | 2026-05-15 | 0 | 0009 (classifier library and synthetic tests) |
| 0011 | ownership-verify-upgrade-integration | done | 2026-05-15 | 0 | 0010 (skeleton self-classification lock) |
| 0012 | ownership-initialize-report | done | 2026-05-15 | 0 | 0011 (ownership-aware verify/upgrade integration) |
| 0013 | enki-ownership-initialize-dry-run | done | 2026-05-15 | 0 | 0012 (ownership initialize report tool) |
| 0014 | specialist-overlay-audit | done | 2026-05-16 | 0 | 0006 delegate abort evidence + 2026-05-16 freeze exception |
| 0015 | specialist-overlay-loader | done | 2026-05-16 | 0 | 0014 (specialist overlay audit) |
| 0016 | specialist-proposal-add | done | 2026-05-16 | 0 | 0015 + implementation exception |
| 0017 | orchestration-preview | done | 2026-05-16 | 0 | 0016 proposal schema |
| 0018 | execution-loop | done | 2026-05-16 | 0 | 0017 DelegationPlan interface |
| 0019 | session-recall-hardening | done | 2026-05-16 | 0 | existing session-recall operational tool |
| 0020 | specialist-usage-evidence-ledger | done | 2026-05-16 | 0 | 0017 DelegationPlan + 0018 execute boundary |
| 0021 | closeout-validator-loop-extension | done | 2026-05-16 | 0 | 0020 usage evidence + explicit user implementation exception |
| 0022 | spawn-ready-packet | done | 2026-05-16 | 0 | 0021 validator loop + approved DelegationPlan |
| 0023 | agent-flow-doctor | done | 2026-05-17 | 0 | operational diagnostics UX improvement |
| 0024 | project-adoption-intake | done | 2026-05-17 | 0 | 0023 diagnostics + existing skeleton upgrade tooling |
| 0025 | enki-ownership-classification | done | 2026-05-17 | 0 | 0024 adoption intake stop condition |
| 0026 | enki-ownership-baseline-and-safe-apply | done | 2026-05-17 | 0 | 0025 ownership classification proposal |
| 0027 | enki-manual-risky-system-review | done | 2026-05-17 | 0 | 0026 baseline and safe apply |
| 0028 | closeout-wrapper-timing | done | 2026-05-17 | 0 | ENKI migration follow-up performance evidence |
| 0029 | adoption-semantics-install-state | done | 2026-05-17 | 0 | 0024 adoption intake + ENKI migration follow-up semantics |
| 0032 | codex-claude-dialogue-consensus | done | 2026-05-27 | 0 | user-approved critical planning workflow |
| 0033 | plan-id-evidence-trace | done | 2026-05-27 | 0 | explicit plan_id trace from closeout to completion evidence |
| 0034 | claude-strategy-critic-boundary | done | 2026-05-27 | 0 | 0032 dialogue consensus; real Claude strategy/critic only |
| 0001 | delegation-permission-preflight-hardening | done | 2026-05-27 | 0 | follow-up to 0018/0022 delegation boundary; local plan id preserved for completion evidence |
| 0001 | source-anchor-strict-mode | done | 2026-05-27 | 0 | adoption/proposal/copy/promotion source-anchor strict option |
| 0001 | subagent-debate-workflow-replaces-claude-auto-di | done | 2026-05-29 | 0 | replaces Claude automatic dialogue with Codex-orchestrated subagent debate |
| 0001 | codex-cli-goal-prompt-length-contract | done | 2026-05-29 | 0 | goal prompt means Codex CLI /goal prompt capped at 4000 chars |
| 0001 | versioned-skeleton-release-upgrade-support | done | 2026-05-29 | 0 | release manifest and install-state provenance for repeatable skeleton upgrades |
| 0001 | component-install-diff-surface-bloat-audit | done | 2026-05-29 | 0 | component-scoped release/upgrade review plus read-only skills/agents bloat audit |
| 0001 | feature-boundary-cleanup | done | 2026-05-29 | 0 | canonical/generated boundary cleanup, feature delivery metadata, and install profile vocabulary alignment |

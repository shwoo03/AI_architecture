# Specialist Agent Usage Best Practices

## Summary

Specialist agents should be an on-demand capability, not a default project-start ritual. The system should first use the main agent, existing skills, and existing base roles. It should propose or invoke a specialist only when the task has a clear signal that delegation will reduce context load, improve independence, enforce a permission boundary, or provide a needed second opinion.

This report prepares 0016-0018 implementation without changing runtime behavior.

## Sources Reviewed

- Anthropic Claude Code subagents documentation: https://code.claude.com/docs/en/sub-agents
- Anthropic Claude Code subagents usage guide: https://claude.com/blog/subagents-in-claude-code
- Anthropic Claude Agent SDK subagents documentation: https://code.claude.com/docs/en/agent-sdk/subagents
- OpenAI Agents SDK orchestration documentation: https://openai.github.io/openai-agents-python/multi_agent/
- OpenAI Agents SDK guardrails documentation: https://openai.github.io/openai-agents-python/guardrails/
- OpenAI practical guide to building agents: https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf
- LangChain multi-agent documentation: https://docs.langchain.com/oss/python/langchain/multi-agent
- LangChain handoffs documentation: https://docs.langchain.com/oss/python/langchain/multi-agent/handoffs
- Microsoft Copilot Studio multi-agent architecture guidance: https://learn.microsoft.com/en-us/microsoft-copilot-studio/guidance/architecture/multi-agent-patterns
- AutoGen Studio paper: https://arxiv.org/abs/2408.15247

## When A Specialist Is Worth Proposing

Use a specialist proposal when at least one concrete trigger is present:

- Context isolation: the work will read many files, logs, test outputs, docs, or external sources that would bloat the main conversation.
- Independent parallel work: multiple subtasks can proceed without sharing intermediate state.
- Focused second opinion: review, validation, security, compliance, or performance analysis benefits from a fresh context and explicit role.
- Specialized tool or permission boundary: the task needs narrower tools, read-only access, a constrained write scope, or domain-specific checks.
- Repeated pattern: the same kind of task recurs enough that a reusable specialist reduces prompt noise and decision friction.
- Sequential precondition: a later capability should unlock only after a prior review, approval, or state transition.
- Long-running or high-volume task: the main agent should receive a compact result rather than raw intermediate output.

These triggers map to 0016 `SpecialistProposal.reason` and 0017 `DelegationPlan.score_reasons`.

## When Not To Use A Specialist

Do not propose or invoke a specialist when these anti-triggers dominate:

- The task is a quick targeted fix or simple question.
- The user needs tight back-and-forth in the main conversation.
- Planning, implementation, and validation all share the same small context.
- Latency or cost matters more than isolation.
- The specialist would only duplicate an existing base role, skill, or deterministic script.
- Many specialists would be offered at once without clear differentiation.
- Agents need to communicate directly with each other rather than report through the orchestrator.
- A single-agent skill or middleware-style behavior change is enough.

The default fallback is main-agent execution with skills or existing base roles.

## Orchestration Pattern For This Project

The safest default for this repository is manager-style orchestration:

- The main Codex session remains the control plane.
- Specialists are bounded helpers, not autonomous owners of the whole task.
- 0017 should preview candidate roles and selected roles before execution.
- 0018 should execute only an approved `DelegationPlan` through the existing incubating delegate path.
- Handoff-style behavior is reserved for cases where a specialist should own the next turn or a persistent state transition is truly required.
- Skills remain the better fit for reusable instructions that should run inside the main conversation context.

This preserves the existing design choice: no new router and no second execution loop.

## Contract And Context Rules

Every specialist path should preserve typed, inspectable contracts:

- 0016 proposal records capture why a specialist is needed before any overlay mutation.
- 0017 preview records which roles were considered, why they scored, and why approval is required.
- 0018 execution records the approved plan, role source, scope, write policy, changed paths, validation, and closeout evidence.
- Context passed to specialists should be minimal and task-specific.
- Returned output should be summarized, with raw logs or high-volume details kept out of the main context unless needed for verification.
- `role_source: base|project` must remain visible across proposal, preview, brief, handoff, and ledger evidence.

## Safety Rules

- Use least-privileged scope for every specialist.
- Project overlays may add new specialists and narrow base specialists, but must not broaden base permissions.
- High-impact writes, cross-agent execution, target-project mutation, push, deletion, dependency changes, and auto-spawn require explicit approval.
- Guardrail checks should live at the control-plane/tool boundary where possible, not only inside a specialist prompt.
- Long-running work needs cancellation or skip boundaries and a concise progress summary.
- Conflicting specialist outputs should be reconciled by the main orchestrator, not by specialists talking directly to each other.

## 0016 Application Notes

The 0016 proposal/add implementation should stay on-demand:

- Never create project specialists at project start just because a project exists.
- Require `reason` to include at least one trigger from this report.
- Reject proposals that match only anti-triggers.
- Treat approval as a human review boundary before overlay input.
- Keep proposal creation separate from overlay mutation.

## 0017 Application Notes

The 0017 orchestration preview should act as a decision aid, not a router:

- Use existing goal-to-candidate scoring surfaces.
- Put trigger matches and anti-trigger matches into `score_reasons`.
- Prefer base roles and skills when they are enough.
- Select zero specialists when delegation is not justified.
- Preserve `requires_confirmation` for any execution-capable plan.

## 0018 Application Notes

The 0018 execution path should stay approval-gated:

- Execute only approved `DelegationPlan` records.
- Require explicit user/session approval before spawning or delegating.
- Reuse `agent-flow-delegate.py` and `agent-run.py`.
- Preserve AgentBrief and AgentRun evidence.
- Do not promote incubating behavior to stable without separate validation and decision records.

## Implementation Readiness Checklist

- 0016 implementation can add proposal storage and review commands only after a new implementation exception is opened.
- 0017 implementation can add preview generation only if it extends existing scoring instead of adding a new router.
- 0018 implementation can add execution only if it extends the existing delegate and ledger path.
- All three slices should keep the on-demand rule: no specialist creation or invocation without a concrete trigger.

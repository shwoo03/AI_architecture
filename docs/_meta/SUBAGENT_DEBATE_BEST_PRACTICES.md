# Subagent Debate Best Practices

## Summary

This note records the source-backed boundary for task-scoped planning debates in this skeleton. It replaces the earlier Claude-centered dialogue assumption with a Codex-orchestrated subagent debate pattern.

## Sources Checked

- Anthropic, "How we built our multi-agent research system" (2025-06-13): supports a lead-orchestrator pattern, specialized parallel subagents, clear task boundaries, bounded effort, observability, and small eval loops.
- Microsoft AutoGen, "Multi-Agent Debate": supports an aggregator/debater structure, multi-round exchange, and final aggregation after bounded debate rounds.
- OpenAI Agents SDK, "Agent orchestration": distinguishes manager-owned specialist calls from handoffs and recommends specialized agents, prompts, monitoring, evals, and code-driven orchestration when predictability matters.

## Local Decision

- Codex remains the orchestrator and owns the final implementation decision.
- Debate participants are scoped subagent roles: `subagent-critic`, `subagent-researcher`, and `subagent-verifier`.
- Claude is not an automatic participant and Claude session expiry is not a fallback trigger.
- Repository scripts record debate ledgers only; actual subagent spawning belongs to the surrounding harness.
- Convergence requires Codex plus at least one `subagent-*` readiness record.
- Block critiques require evidence and must be resolved or accepted as risk before implementation scope is frozen.
- Nested subagent spawning is disallowed inside the debate ledger.

## Stop Conditions

- Stop if the debate system starts invoking Claude automatically.
- Stop if repository scripts spawn agents directly.
- Stop if the workflow grows into a dashboard, database, or general multi-agent runtime.
- Stop if convergence can happen without a scoped subagent critique or with unresolved block critiques.

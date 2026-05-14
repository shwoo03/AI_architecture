# V2 Specialist Team OS

> 이 문서는 현재 운영 명세가 아닙니다. v2 specialist team 기능을 설계하기 위한 incubating design 문서이며, stable 동작은 루트 운영 문서와 `docs/feature-status.yaml`의 stable tier를 따릅니다.

## 한 문장 정의

V2 Specialist Team OS는 하나의 에이전트가 모든 일을 직접 처리하지 않고, 작은 전문 역할들에게 조사, 구현, 검증, 정리 작업을 안전하게 나눠 맡기기 위한 lightweight runtime 설계입니다.

## 왜 필요한가

v1은 프로젝트 목표, closeout, 검증, overlay를 안정적으로 운영하는 scaffold에 집중했습니다. v2는 그 위에서 subagent/team 작업을 더 반복 가능하게 만들되, stable v1 closeout을 깨지 않는 방식으로 시작해야 합니다.

## 최소 계약

- `AgentBrief`: 하위 에이전트가 읽는 짧은 작업 설명입니다. 목표, 범위, 금지된 파일, 기대 산출물, 검증 힌트를 포함합니다. Plan의 자식 artifact이며 하나의 plan은 여러 brief를 만들 수 있습니다.
- `DelegationPlan`: 어떤 역할에게 어떤 작업을 맡길지 정리한 계획입니다. 병렬 가능 여부와 결과 병합 기준을 포함합니다.
- `AgentRun`: 실제 하위 에이전트 실행 기록입니다. parent goal, role, status, touched scope, evidence pointer를 남깁니다.
- `AgentResult`: 하위 에이전트의 최종 요약입니다. 변경 파일, 발견한 위험, 검증 결과, 후속 질문을 포함합니다.
- `agent-flow delegate`: 위 계약을 public command surface로 노출할 후보입니다. stable 승격 전까지는 incubating이며 기본 closeout을 막지 않습니다.

## 설계 원칙

- core schema는 local JSONL ledger를 기준으로 유지합니다.
- SDK/LangGraph 용어는 core schema에 직접 넣지 않습니다.
- 모든 v2 필드는 additive여야 하며 stable reader가 무시해도 안전해야 합니다.
- 실패한 delegation은 source-scoped recovery나 resume-safe checkpoint로 돌아갈 수 있어야 합니다.
- specialist 기능은 `quality-gate --tier all`에서 검증하되 기본 `stable` gate를 막지 않습니다.

## Phase 1a AgentBrief 계약

Phase 1a의 AgentBrief는 자동 delegation 입력이 아니라 사람이 읽고 manual smoke를 수행하는 artifact입니다.

- 저장 위치: `runtime/agent-briefs/<brief_id>.json`.
- `brief_id`: `<YYYY-MM-DD>-<plan_slug>-<role>-<seq>`.
- `goal_lineage`: `[{type, ref, summary}]` object array.
- `execution_mode`: `manual_human`.
- `tier`: `incubating`.
- `ext`: `{}`로 시작하며 adapter-specific 필드는 `ext.<adapter_name>.*` 아래에만 둡니다.

## AgentRun ledger draft

AgentRun writer는 Phase 1b에서 구현합니다. 1a에서는 첫 ledger entry가 다음 필드를 갖도록 schema draft만 고정합니다.

Required draft fields: `schema_version`, `ts`, `agent_run_id`, `brief_id`, `tier`, `agent`, `workflow`, `status`, `goal_lineage`, `artifacts`, `result_summary`, `changed_paths`, `validation`, `created_by`, `ext`.

Manual smoke run의 기본값은 `tier: incubating`, `created_by: manual`, `ext: {}`입니다. Ledger는 `runtime/agent-runs.jsonl` 한 파일에 append하고, stable/incubating 구분은 reader가 `tier` 필드로 필터링합니다.

## Stable 승격 전 필요한 것

- 반복 실행 evidence.
- schema 안정성.
- 루트 운영 문서 편입.
- rollback flag 또는 opt-out profile.
- 승격 ADR 또는 결정 기록.

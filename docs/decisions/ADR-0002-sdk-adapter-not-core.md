# ADR-0002: SDK와 LangGraph는 core가 아니라 adapter다

Status: Accepted

## Context

OpenAI Agents SDK나 LangGraph는 specialist runtime에 유용할 수 있지만, provider/runtime 용어와 의존성을 core schema에 직접 넣으면 overlay scaffold의 이식성이 낮아집니다.

## Decision

SDK와 LangGraph는 experimental adapter로 둡니다. core dependency에 넣지 않고, provider별 trace와 id는 `ext.<adapter_name>.*` namespace에 격리합니다. provider credential은 canonical config에 저장하지 않습니다.

## Consequences

초기 통합은 read-only export나 보조 evidence부터 시작합니다. 양방향 sync나 durable graph ownership은 별도 승인과 ADR이 필요합니다.

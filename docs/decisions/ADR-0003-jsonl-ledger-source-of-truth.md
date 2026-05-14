# ADR-0003: JSONL ledger가 source of truth다

Status: Accepted

## Context

외부 SDK trace는 retention, schema, 접근 가능성을 프로젝트가 완전히 통제할 수 없습니다. 반면 현재 scaffold는 runtime JSONL 기록을 closeout, resume, evidence의 기준으로 사용합니다.

## Decision

`runtime/*.jsonl` ledger를 source of truth로 유지합니다. SDK trace, LangGraph trace, 외부 실행 로그는 부가 증거이며 canonical ledger를 대체하지 않습니다.

## Consequences

adapter는 외부 trace를 core ledger에 직접 섞지 않고 extension namespace나 evidence pointer로 연결해야 합니다. stable resume/readiness 판단은 계속 로컬 ledger를 기준으로 합니다.

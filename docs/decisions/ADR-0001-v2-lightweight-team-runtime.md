# ADR-0001: V2는 lightweight team runtime으로 먼저 구현한다

Status: Accepted

## Context

v2의 목표는 specialist agent team을 운영하는 것이지만, 초기부터 외부 SDK나 durable graph runtime을 core에 넣으면 v1의 가벼운 scaffold 원칙이 깨질 수 있습니다.

## Decision

v2는 먼저 로컬 파일과 JSONL ledger 기반의 lightweight team runtime으로 구현합니다. specialist routing, delegation plan, result aggregation은 incubating tier에서 시작하며 기본 stable closeout을 막지 않습니다.

## Consequences

이 결정은 v2 실험을 빠르게 만들지만, durable orchestration 기능은 제한됩니다. 안정화 이후 SDK 또는 graph runtime은 adapter로 붙입니다.

# Ownership Model

## 한 문장 정의

Ownership-aware upgrade는 기존 프로젝트에 AI_architecture 업데이트를 적용할 때 어떤 파일이 시스템 소유이고 어떤 파일이 프로젝트 소유인지 결정하는 운영 모델이다.

## 무엇을 하는가

이 모델은 기존 프로젝트를 새 skeleton으로 다시 만들지 않고도 시스템 파일만 안전하게 업데이트하게 한다. 핵심 원칙은 다음과 같다.

> layout is advice, ownership is law.

디렉터리 레이아웃은 권고일 뿐이다. Next.js, Docker, Makefile, GitHub Actions, 배포 스크립트처럼 프레임워크나 운영 관용 때문에 루트에 있어야 하는 파일은 항상 생긴다. 업데이트 안정성은 `src/` 같은 레이아웃 강제가 아니라 `config/ownership.yaml`의 소유권 분류가 보장한다.

## 왜 필요한가

preserve-first overlay는 안전하지만 너무 보수적이면 v2 파일이 프로젝트에 들어가지 않는다. 반대로 전체 복사는 프로젝트 런타임 증거와 로컬 결정을 덮어쓸 수 있다. Ownership-aware upgrade는 두 실패를 모두 피한다.

- 시스템 업데이트는 canonical 파일에만 적용한다.
- 프로젝트 payload와 runtime evidence는 보존한다.
- 애매한 파일은 자동 처리하지 않고 수동 승인으로 보낸다.
- 분류 변경은 lock drift로 드러나게 한다.

## 어떻게 동작하는가

### Ownership YAML

`config/ownership.yaml`은 v1 schema를 명시한다.

```yaml
schema_version: ai-architecture.ownership.v1
```

알 수 없는 schema version은 fail-loud 한다. v1 classifier는 v2 파일을 추측해서 처리하지 않는다.

### Merge policy

`ownership.yaml` 자체는 일반 파일처럼 덮어쓰지 않는다.

- `system_defaults`는 source AI_architecture 버전으로 wholesale replace 한다.
- `project_overrides`는 target project 버전을 보존한다.
- `unknown_policy`는 v1에서 system default를 따른다.
- `protected`와 `system_locked`는 project override로 약화할 수 없다.

### Guard categories

`protected`와 `system_locked`는 project override 경쟁 밖에 있다.

- `protected`: project evidence를 시스템 업데이트로부터 보호한다. 예: runtime ledgers, handoff, decisions, `.env*`.
- `system_locked`: 시스템 정체성을 project override로부터 보호한다. 예: public command, core checks, core docs, schemas, generated Codex/Claude surfaces, incubating v2 entrypoints.

`protected`는 완전한 short-circuit이다. match되면 이후 normal rule이나 project override가 다시 소유권을 바꾸지 못한다.

`system_locked`는 project override만 short-circuit한다. system default rule은 계속 적용된다. 예를 들어 `AGENTS.md`처럼 project override로 빼앗기면 안 되지만 실제 적용은 `manual_merge`여야 하는 파일을 표현할 수 있다.

### Normal rules

Normal rule은 order-based이고 last match wins이다. 이 모델은 `.gitignore`와 같은 정신 모델을 따른다. 복잡한 specificity score는 쓰지 않는다.

처리 순서:

1. `skip_patterns` match -> `skip_generated`.
2. `protected` match -> `protected_preserve` and stop.
3. `system_locked` match -> project override competition을 중지할 guard를 설정한다.
4. `system_defaults.rules`를 위에서 아래로 적용한다.
5. `system_locked`가 아니면 `project_overrides.rules`를 위에서 아래로 적용한다.
6. matched owner가 없으면 `unknown_policy`를 따른다.

모든 owner class에서 source와 target content가 동일하면 `unchanged`로 short-circuit한다.

### Unknown policy

- Source-only unknown file -> `manual_approval`.
- Target-only unknown file -> `preserve_project`.
- Source/target both exist but differ and owner unknown -> `manual_merge`.
- Generated/cache path -> `skip_generated`.

Unknown을 자동 설치하지 않는 것이 안전한 실패 모드다.

## Classification lock

`runtime/ownership-classification.lock.json`은 classification baseline이다. 이 파일은 도구가 생성하고 갱신한다. 사람이 직접 JSON을 편집하지 않는다.

Lock comparison은 세 경우를 구분한다.

- `lock_addition`: lock에 없던 path가 새로 분류됨. halt하지 않고 lock refresh 때 추가한다.
- `lock_removal`: lock에는 있지만 현재 path가 없음. halt하지 않고 lock refresh 때 제거한다.
- `classification_drift`: 기존 path의 owner/action이 바뀜. halt하고 명시 승인을 요구한다.

Drift만 upgrade를 막는다. 추가와 제거는 report 끝에 요약한다.

## Initialize report

`scripts/ownership-initialize.py`는 v1에서 report-only다. 기존 repo를 스캔하고 copy-paste 가능한 `project_overrides` YAML 초안을 제안하지만 파일을 쓰거나 migration을 수행하지 않는다.

초기화 절차:

1. target repo 전체를 스캔한다.
2. source의 `system_defaults`로 분류한다.
3. unknown/manual_merge target paths를 depth-2까지의 디렉터리 그룹으로 묶어 `project_overrides.rules` 후보를 출력한다.
4. 사람 검토 후 ownership YAML을 확정한다.
5. `scripts/ownership-lock.py write`로 initial lock을 만든다.

자동 write는 v1 scope가 아니다.

상태별 동작은 분리한다.

- target에 `config/ownership.yaml`이 없으면 draft를 출력한다.
- target에 `config/ownership.yaml`은 있고 lock이 없으면 draft를 출력하지 않고 lock 생성/검증만 제안한다.
- target에 `config/ownership.yaml`과 lock이 모두 있으면 initialization을 거부하고 ongoing maintenance는 `scripts/ownership-lock.py check`로 안내한다.

## Synthetic fixture와 self-classification의 역할

두 테스트 계층은 다른 책임을 갖는다.

- Synthetic fixtures prove classifier correctness.
- Skeleton self-classification proves ownership.yaml integrity and source==target idempotence.

Synthetic fixture는 의도적으로 까다로운 glob overlap을 만든다. Self-classification은 AI_architecture 자신의 모든 durable path가 unknown 없이 분류되고 lock과 일치하는지 확인한다.

## Workflow cost

Ownership-aware upgrade는 뼈대 개발 workflow에 의도적인 세금을 붙인다.

새 durable file을 추가하면 다음을 함께 해야 한다.

1. `config/ownership.yaml`에 owner를 지정한다.
2. 도구로 `runtime/ownership-classification.lock.json`을 갱신한다.
3. `verify-skeleton.py` ownership check를 통과한다.

Lock은 수동 편집하지 않는다. `scripts/ownership-lock.py write`로 갱신하고, `scripts/ownership-lock.py check`로 drift를 확인한다. Slice 3에서 `verify-skeleton.py`는 missing ownership이나 lock drift를 actionable error로 보여줘야 한다.

Closeout과 resume-readiness는 ownership drift를 다음 세션에 숨기지 않는다. Classification drift는 오류로 다루고, lock addition/removal은 `scripts/ownership-lock.py write`로 갱신하거나 handoff에 `ownership lock drift: deferred`를 남겨 명시적으로 미룬다. Deferral은 drift를 무시한다는 뜻이 아니라 다음 세션의 첫 작업으로 드러내기 위한 기록이다.

## 결과는 무엇인가

이 모델을 따르면 다음 상태를 얻는다.

- 프로젝트가 수정한 파일은 보존된다.
- AI_architecture가 소유한 시스템 파일은 업데이트 후보가 된다.
- 시스템 정체성 파일은 broad project override로 빼앗기지 않는다.
- runtime evidence는 시스템 업데이트로 덮이지 않는다.
- 외부 프로젝트 migration 전 skeleton 자신이 먼저 ownership 검증을 통과한다.

## 구현 연결 정보

- Default ownership map: `config/ownership.yaml`
- Classifier: `scripts/lib_ownership.py`
- Ownership lock tool: `scripts/ownership-lock.py`
- Ownership initialization report: `scripts/ownership-initialize.py`
- Upgrade integration: `scripts/upgrade-from-skeleton.py`
- Health gate: `scripts/verify-skeleton.py`
- Lock: `runtime/ownership-classification.lock.json`

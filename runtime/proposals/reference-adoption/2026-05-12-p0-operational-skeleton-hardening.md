# P0 reference improvements 기반 operational skeleton hardening 제안

## 상태

- `status`: accepted
- `created_at`: 2026-05-12
- `candidate_card`: `references.yaml`
- `proposal_type`: reference_adoption_dry_run
- `approval_required`: yes
- `decision_source`: user requested implementation after P0 plan

## 한 문장 정의

최신 reference 분석에서 확인한 운영 안전 패턴을 코드 복사 없이 우리 스켈레톤의 read-only readiness, delegation permission, generated artifact, closeout 계약으로 번역합니다.

## 근거

Source-backed evidence:

- `everything-claude-code`: harness adapter compliance와 observability readiness 패턴이 지원 상태 과장과 관측 불능 운영을 줄입니다.
- `opencode`: managed reference intake와 delegated-agent permission inheritance 패턴이 reference 흐름과 sub-agent 권한 경계를 강화합니다.
- `paperclip`: managed resource reconcile/drift/reset과 explicit liveness/disposition 계약이 생성물 drift와 애매한 종료 상태를 줄입니다.

## 적용하지 않을 것

- 외부 TypeScript/JavaScript 코드를 직접 복사하지 않습니다.
- Node/Yarn/DB/GUI 런타임을 도입하지 않습니다.
- reference repository를 자동 clone/pull하거나 `references.yaml`을 자동 갱신하지 않습니다.
- `partial_copy`는 이번 변경 범위에서 사용하지 않습니다.

## 모듈형 흡수 판단

- `absorption_mode`: concept_only
- `recommended_mode`: Python 표준 라이브러리 기반 read-only checker와 기존 스크립트 계약 확장
- `reuse_boundary`: upstream 구조와 실패 방지만 참고하고 구현은 로컬 스켈레톤 규칙에 맞게 재작성
- `direct_implementation_reason`: 기존 reference 구현은 제품 런타임과 언어 스택이 달라 그대로 쓸 수 없으며, 이 스켈레톤은 표준 라이브러리와 Markdown/JSONL 운영 표면을 유지해야 합니다.
- `copy_boundary`: not applicable

## 제안 변경

### 1. Operational readiness

대상: `scripts/operational-readiness.py`

추가할 내용:

- harness support 상태, reference readiness, observability ledger 상태를 read-only로 보고합니다.
- `quality-gate.py`에서 통합 확인할 수 있게 합니다.

### 2. Delegation permission inheritance

대상: `scripts/agent-brief.py`

추가할 내용:

- parent write policy와 scope를 child specialist brief에 상속합니다.
- child brief는 parent보다 넓은 권한이나 범위를 요청할 수 없게 합니다.

### 3. Generated artifact and closeout contracts

대상: `scripts/lib_path_safety.py`, `scripts/completion-evidence.py`, `scripts/task-closeout.py`, `scripts/resume-readiness.py`

추가할 내용:

- `.mcp.json`과 `CLAUDE.md`를 generated managed artifact로 보호합니다.
- closeout evidence에 explicit disposition을 기록하고 resume readiness가 불일치를 감지합니다.

## 기대 효과

- 지원 상태, reference 상태, 운영 관측성이 한 명령으로 보입니다.
- sub-agent가 parent/session 권한보다 넓게 움직이는 사고를 줄입니다.
- generated artifact 직접 수정과 애매한 closeout 상태를 더 빨리 발견합니다.

## 위험

- readiness checker가 기존 runtime ledger의 오래된 상태를 warning으로 보고할 수 있습니다.
- parent scope 교집합 규칙이 기존 agent brief 호출보다 엄격할 수 있습니다.
- disposition 필드는 신규 evidence에는 적용되지만 legacy evidence는 그대로 유지됩니다.

완화:

- 새 checker는 read-only로 시작하고, warning은 strict 모드에서만 실패로 다룹니다.
- 권한 상속은 명시적 parent 인자가 있을 때 scope 교집합을 적용합니다.
- legacy evidence는 깨지지 않게 disposition 누락을 허용합니다.

## 검증 계획

승인 후 실제 반영 작업에서는 다음을 실행합니다.

```powershell
python scripts/verify-skeleton.py
python scripts/validate-reference-candidates.py
python scripts/validate-reference-proposals.py
python scripts/list-open-questions.py --count
```

추가로 다음 검증을 실행합니다.

```powershell
python scripts/operational-readiness.py --strict
python scripts/resume-readiness.py --strict
python -m unittest discover -s tests -v
```

## 롤백 또는 중단 조건

- readiness checker가 repo 상태를 변경하는 방향으로 확장되면 중단합니다.
- 권한 상속이 합법적인 read-only reviewer 흐름을 막으면 parent scope 모델을 재검토합니다.
- generated artifact reset이 `convert.py` 이외의 writer로 분산되면 중단합니다.

## 승인 후 실제 변경 범위

- `scripts/operational-readiness.py`
- `scripts/quality-gate.py`
- `scripts/agent-brief.py`
- `scripts/lib_path_safety.py`
- `scripts/completion-evidence.py`
- `scripts/task-closeout.py`
- `scripts/session-snapshot.py`
- `scripts/resume-readiness.py`
- `tests/test_validation.py`
- `tests/test_runtime.py`
- `runtime/proposals/reference-adoption/2026-05-12-p0-operational-skeleton-hardening.md`

## 최종 결정 기록

- `decision`: accepted
- `decided_at`: 2026-05-12
- `decided_by`: user
- `decision_source`: chat approval via "Implement the plan."
- `applied_in`: current working tree
- `validation_result`: not run in this turn; user did not explicitly request validation execution

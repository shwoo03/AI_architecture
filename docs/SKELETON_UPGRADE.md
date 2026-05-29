# 스켈레톤 업그레이드

## 한 문장 정의

이 문서는 공용 AI 스켈레톤이 개선됐을 때 이미 부트스트랩된 기존 프로젝트가 같은 수준으로 따라올 수 있도록 업그레이드 경로를 정리한 기준입니다.

## 무엇을 하는가

부트스트랩 이후 스켈레톤이 업데이트되면 기존 프로젝트는 자동으로 상속되지 않습니다. 이 문서는 어떤 파일을 복사해도 안전한지, 어떤 파일은 수동으로 머지해야 하는지, 어떤 파일은 절대 덮어쓰면 안 되는지를 결정하게 해 줍니다.

## 왜 필요한가

여러 프로젝트를 같은 스켈레톤에서 시작하면 시간이 지날수록 스켈레톤이 개선됩니다. 이때 업그레이드 정책이 없으면 두 가지 실패가 생깁니다. 첫째, 오래된 프로젝트가 새 규칙을 놓쳐 품질이 뒤처집니다. 둘째, 업그레이드 중 사용자가 프로젝트 고유 상태(활동 로그, 세션 인수인계, 지식 인덱스)를 덮어써서 복구 불가능한 손실이 발생합니다.

## 어떻게 동작하는가

업그레이드는 3개 영역으로 나눕니다.

### 안전하게 복사 가능한 영역

스켈레톤에서 그대로 덮어써도 되는 파일들입니다. 프로젝트 고유 상태가 없고, 스켈레톤이 canonical 소스입니다.

- `docs/ARCHITECTURE.md`, `docs/OPERATING_LOOP.md`, `docs/SESSION_CONTINUITY.md`
- `docs/THREE_LAYER_MODEL.md`, `docs/SKILL_DISTRIBUTION_MODEL.md`
- `docs/RUNTIME_EVENT_SCHEMA.md`, `docs/GOVERNANCE.md`
- `docs/WORKFLOW_CATALOG.md`, `docs/PIVOT_TRIGGERS.md`
- `docs/DOCUMENTATION_STYLE_GUIDE.md`, `docs/FEATURE_DECISION_GUIDE.md`
- `docs/NOTION_DOCUMENTATION_RULES.md`
- `docs/AGENT_REGISTRY.md`, `docs/SKELETON_UPGRADE.md`
- `docs/wiki-ops/*.md`
- `docs/_meta/*.md`
- `rules/common/**` (README 포함), `rules/languages/**` (README 포함)
- `scripts/**/*.py` (bootstrap, wiki-lint, verify-skeleton, hooks),
  `scripts/README.md`, `scripts/bootstrap/README.md`, `scripts/hooks/README.md`
- `agents/README.md`, `agents/*.md`
  (개별 에이전트 파일은 canonical 소스입니다. `.codex/agents/`와
  `.claude/agents/`는 `scripts/convert.py`가 만드는 generated surface이므로
  직접 편집하거나 복사 기준으로 삼지 않습니다.)
- `rules/**`, `skills/active/**`, `skills/candidates/**`, `skills/deprecated/**`
  (generated skill export는 `.codex/skills/`, `.claude/skills/`로 재생성합니다.)
- `examples/**` (참고용 예시, 프로젝트 고유 상태 아님)
- `CLAUDE.md`, `AGENTS.md`, `README.md`, `.editorconfig`
- `docs/README.md`, `docs/PROJECT_PROFILE.template.md`,
  `docs/PROJECT_SPEC.template.md`, `docs/PROJECT_OPERATING_PLAN.template.md`

### 수동으로 머지해야 하는 영역

프로젝트 고유 상태와 스켈레톤 구조가 섞여 있는 파일들입니다. 자동 덮어쓰기 금지. 새 필드나 섹션이 추가됐다면 diff를 보고 사용자가 병합합니다.

- `docs/PROJECT_PROFILE.md`: 스키마가 바뀌면 새 필드만 추가. 기존 값은 보존.
  구체 절차는 아래 "PROJECT_PROFILE 머지 절차" 참조.
- `docs/PROJECT_SPEC.md` (있는 경우): 같음.
- `docs/PROJECT_OPERATING_PLAN.md` (있는 경우): 같음.
- `knowledge/index.md`: 스켈레톤의 인덱스 규칙이 바뀌면 규칙 섹션만 병합. K 항목은 프로젝트 것이므로 유지.
- `.claude/settings.local.json`: 프로젝트가 승인한 권한 유지. 스키마가 바뀌면 병합.
- `.claude/settings.json` (있는 경우): 프로젝트 공용 훅/권한은 유지. 스켈레톤이 훅 필드를 추가했다면 병합.
- `agents/*.md`(개별 에이전트): 역할 frontmatter 필드가 늘어나면 추가만.
  프로젝트가 해당 파일을 수정하지 않았다면 "안전 복사" 영역에서 덮어써도 됨.
- `skills/active/*`, `skills/candidates/*`, `skills/deprecated/*` (프로젝트 스킬):
  스켈레톤에 같은 이름 skill이 새로 생기면 덮지 말고 비교 후 선택.
  `.codex/skills/*`와 `.claude/skills/*`는 generated surface라서 직접 머지하지 않습니다.

### 의도적으로 제거된 경로 (재생성 금지)

아래 경로들은 이전 스켈레톤 버전에 존재했지만 메모리/프로모션 구조 정리 과정에서 의도적으로 제거됐습니다. `scripts/verify-skeleton.py`의 `REMOVED_PATHS`가 재등장 여부를 감시하며, 이들 중 하나라도 다시 존재하면 `removed_path_present` 에러로 실패합니다. 업그레이드 중 옛 스켈레톤에서 실수로 복사되지 않도록 주의합니다. 동일한 책임이 필요하면 기존 대체 경로를 사용하거나 새 이름의 파일을 제안하세요.

- `runtime/memory/` — 장기 메모리는 `knowledge/`(wiki)와 `runtime/state/session-handoff.md`로 분리됨.
- `codex/agents/memory-curator.md` — 메모리 큐레이션은 사람 주도 wiki-lint 흐름으로 대체됨.
- `knowledge/workflows/wiki-ingest.md` — 지식 wiki는 LLM 자동 ingest 대신 사람이 편집하는 2-op(`wiki-query`, `wiki-lint`) 구조로 전환됨. 상세 근거는 `docs/_meta/BEST_PRACTICE_GAP_IMPLEMENTATION_PLAN.md`의 G2 항목.

### 절대 덮어쓰지 않는 영역

프로젝트 고유의 실행 증거입니다. 업그레이드 중 어떤 상황에서도 덮어쓰지 않습니다.

- `runtime/activity-log.jsonl`
- `runtime/agent-runs.jsonl`
- `runtime/state/session-handoff.md`
- `runtime/validation/*`, `runtime/proposals/*`, `runtime/schedules/*` (프로젝트가 생성한 것)
- `knowledge/log.md`, `knowledge/project-registry.md`, `knowledge/lint-report.md`(린트 결과는 재생성 가능하지만 원본 내용은 보존)
- `.git/`, `.venv/`, `node_modules/`, `dist/`, `build/` (프로젝트 런타임 산출물)

### 신규 파일 분류 기본 규칙

스켈레톤 업그레이드 도중 세 영역 어디에도 명시되지 않은 새 파일을 만나면 다음 순서로 판단합니다.

1. 경로가 `runtime/`, `knowledge/`, `.claude/settings.local.json`, `docs/PROJECT_PROFILE.md`,
   `docs/PROJECT_SPEC.md`, `docs/PROJECT_OPERATING_PLAN.md` 중 하나에 속하면 → **절대 덮어쓰지 않음** 또는 **수동 머지**.
2. 경로가 `docs/`, `rules/`, `scripts/`, `codex/` 아래이고 "템플릿/규칙/예시" 성격이면 → **안전 복사**.
3. 애매하면 기본은 **수동 머지**로 취급하고 diff를 확인합니다. 자동 덮어쓰기 금지가 안전한 실패 모드입니다.
4. 스켈레톤 유지자는 새 파일을 추가할 때 **같은 커밋에서 이 문서의 세 목록 중 하나에 해당 경로를 반드시 추가**합니다. verify-skeleton이 목록 누락을 잡지는 않지만, PR 리뷰에서 "SKELETON_UPGRADE.md에 분류되었나?"가 체크 기준입니다.

## 결과는 무엇인가

이 기준을 따르면 다음 상태를 얻습니다.

- 스켈레톤의 새 규칙이 기존 프로젝트에 반영됩니다.
- 프로젝트 고유 상태는 손실되지 않습니다.
- 에이전트가 승인받아 병합해야 할 파일 목록이 명확합니다.
- 업그레이드 전후 `scripts/verify-skeleton.py`가 여전히 통과하는지로 검증 가능합니다.

## 업그레이드 절차

### 선행 조건

- 대상 프로젝트가 git으로 관리되고 있고 작업 트리가 clean 해야 합니다. 업그레이드는 다중 파일 변경이므로 되돌릴 수 있어야 합니다.
- 스켈레톤의 특정 커밋/버전을 기준으로 삼습니다. "최신"이 아니라 구체적 커밋 해시를 메모합니다.

### 단계

1. 대상 프로젝트에서 `scripts/verify-skeleton.py`가 통과하는지 먼저 확인합니다. 실패 상태에서 업그레이드하면 원인 구분이 어렵습니다.
2. 업그레이드용 브랜치를 만듭니다 (예: `git checkout -b skeleton-upgrade-<date>`).
3. 스켈레톤 체크아웃 경로를 정합니다. 예: `/tmp/skeleton-v2`.
4. 각 영역별로 diff 및 복사를 수행합니다.

   - **안전 복사 영역** — 다음 명령으로 차이를 확인합니다:
     ```
     diff -r <skeleton>/docs <project>/docs
     diff -r <skeleton>/rules <project>/rules
     diff -r <skeleton>/scripts <project>/scripts
     diff -r <skeleton>/codex <project>/codex
     diff -r <skeleton>/examples <project>/examples
     ```
     차이를 확인한 뒤 스켈레톤 버전으로 덮어씁니다. 덮어쓰기는 파일 단위로 하고, 위의 "안전 복사" 목록에 있는 경로만 대상입니다.
   - **수동 머지 영역** — 에이전트가 각 파일을 `diff`로 비교해 선택지를 요약하고, 사용자는 채팅으로 섹션 단위 승인/거절/보류를 결정합니다. `PROJECT_PROFILE.md`는 아래 별도 절차 참조.
   - **절대 덮어쓰지 않는 영역** — 건드리지 않습니다. `diff`조차 자동화하지 않습니다 (실수로 overwrite되지 않게).

5. 업그레이드 후 `scripts/verify-skeleton.py`를 다시 실행해 구조가 일관되는지 확인합니다.
6. `runtime/activity-log.jsonl`에 업그레이드 이벤트를 append합니다 (아래 "업그레이드 이벤트 포맷" 참조).
7. 변경을 커밋합니다. 커밋 메시지에 스켈레톤의 기준 커밋 해시를 기록합니다.

### PROJECT_PROFILE 머지 절차

`docs/PROJECT_PROFILE.md`는 부트스트랩 시 `PROJECT_PROFILE.template.md`로부터 생성된 후 프로젝트 고유 값으로 채워집니다. 템플릿이 진화하면 기존 프로필은 새 필드를 빠뜨리게 됩니다.

1. 스켈레톤의 새 `docs/PROJECT_PROFILE.template.md`를 엽니다.
2. 현재 프로젝트의 `docs/PROJECT_PROFILE.md`에 존재하지 않는 헤딩/필드를 찾습니다.
3. 새 필드를 프로젝트 프로필에 **빈 값 또는 `[NEEDS CLARIFICATION: <질문>]`으로 추가**합니다. 기존 값은 절대 수정하지 않습니다.
4. 제거된 필드는 남겨둡니다(삭제하지 않음). 메모로 `<!-- deprecated in skeleton vN -->`을 덧붙여 향후 정리 시 단서로 씁니다.

같은 절차를 `PROJECT_SPEC.md`, `PROJECT_OPERATING_PLAN.md`에도 적용합니다.

### 업그레이드 이벤트 포맷

`runtime/activity-log.jsonl`에 다음 형태로 append:

```json
{"ts":"<ISO8601 UTC>","phase":"maintenance","action":"skeleton_upgraded","project":"<name>","goal_lineage":["maintenance","<project>","follow skeleton improvements"],"data":{"from_commit":"<old>","to_commit":"<new>","regions_touched":["safe_copy","manual_merge"]}}
```

## 릴리스 manifest와 스키마 호환성

반복 업그레이드의 기준점은 "현재 최신"이 아니라 **구체적인 release manifest**입니다. `scripts/release-manifest.py generate --channel stable --format json`은 현재 skeleton tree에서 `schema_version`, `release_id`, `source_commit`, `channel`, `feature_profile`, component summary, 파일 hash 목록, 제거된 경로, 검증 명령을 가진 manifest를 만듭니다.

`components`는 파일 diff를 `core`, `validation`, `runtime`, `reference`, `wiki`, `skills`, `agents`, `docs`, `bootstrap` 같은 install/upgrade 묶음으로 요약합니다. 각 component는 포함 파일 수, byte 수, 연결된 feature id, 필요한 check, ownership action 분포, generated artifact policy를 갖습니다. generated artifact policy는 `.codex/`, `.claude/`, `.mcp.json`, `CLAUDE.md`처럼 canonical source에서 재생성되는 대상의 source, target, 재생성 명령, parity check, 직접 편집 금지를 component 하위 필드로 노출합니다.

`scripts/upgrade-from-skeleton.py --brief --profile stable --format json`은 파일 목록과 함께 `component_diff`를 출력합니다. 이 값은 component별 `safe_additions`, `manual_reviews`, `risky_reviews`, `protected_skips`, `approval_required`, `sample_paths`, `generated_artifact_policy`를 보여주므로, 구버전 뼈대가 들어간 프로젝트를 업그레이드할 때 "어떤 기능 묶음이 안전 적용이고 어떤 묶음이 수동 검토인지"를 먼저 판단할 수 있습니다.

업그레이드 전후에 skill/agent 표면이 비대해졌는지 볼 때는 `scripts/surface-bloat-audit.py --format json`을 사용합니다. 이 도구는 duplicate, orphan, deprecated-but-generated, generated parity mismatch 같은 기계적으로 확인 가능한 신호만 보고하며, skill/agent 삭제·승격·강등은 자동으로 수행하지 않습니다.

`scripts/skill-surface-check.py`와 `scripts/surface-bloat-audit.py`는 역할이 다릅니다. `skill-surface-check.py`는 canonical source와 generated surface의 일관성을 확인하는 lint/verify용 검사이고, `surface-bloat-audit.py`는 정리 후보를 찾는 read-only advisory 도구입니다. 전자는 parity 문제를 막는 게 목적이고, 후자는 삭제나 demotion 결정을 자동 실행하지 않습니다.

채널은 세 단계입니다.

- `stable`: 기존 프로젝트에 기본으로 제안되는 채널입니다. `docs/feature-status.yaml`에서 `tier=stable`, `delivery=overlay`, `overlay_default=true`인 항목만 포함합니다. stable 안에서도 `stable_role=core`는 운영 뼈대이고 `stable_role=advisory`는 비차단 보조 도구입니다.
- `preview`: incubating 항목까지 보여주되 dry-run 검토가 기본입니다. v2 specialist runtime 계열은 `delivery=frozen_optional`로 표시해 검토 대상임을 드러내고 stable overlay에는 넣지 않습니다.
- `edge`: experimental 항목까지 manifest에 표시할 수 있지만 `delivery=decision_only` 항목은 overlay/apply 대상이 아닙니다.

`scripts/upgrade-from-skeleton.py --brief --profile stable --format json`은 현재 release id, source commit, channel, file count를 함께 출력합니다. `--apply --safe-only`가 실제로 파일을 추가하면 `runtime/install-state.jsonl`에 `skeleton_release_applied` 이벤트를 append합니다. 이 이벤트는 기존 필드를 유지하면서 `release_id`, `channel`, `previous_release_id`, `applied_paths`, `manual_review_paths`, `applied_migrations`를 optional field로 남깁니다.

기존 프로젝트가 아직 release id를 모르는 오래된 install-state를 갖고 있어도 업그레이드는 멈추지 않습니다. 읽는 쪽은 먼저 `release_id`를 찾고, 없으면 기존 `source_commit`/`skeleton_revision` fallback으로 이전 기준점을 추론합니다.

기본 호환성 규약은 아래와 같습니다.

- **기준점은 git 커밋 해시**: 스켈레톤은 자체 git 저장소이므로 "어느 커밋에서 부트스트랩했는지"를 프로젝트가 `runtime/activity-log.jsonl`의 bootstrap 이벤트에 기록하거나 `docs/PROJECT_PROFILE.md`의 `created_at` 근처에 메모합니다.
- **릴리스 기준점은 release id**: 새 업그레이드 이벤트는 `release_id`와 `source_commit`을 함께 기록합니다. release id가 있으면 사람이 "어느 skeleton release로 따라왔는지"를 바로 알 수 있고, source commit은 hash 검증과 재현에 씁니다.
- **활동 로그 스키마 변경 시**: `docs/RUNTIME_EVENT_SCHEMA.md`가 canonical 정의입니다. 필드가 추가되기만 하고 기존 필드 의미는 유지된다는 것이 현재 규약입니다. 기존 로그 라인은 읽을 때 누락 필드를 `null`로 취급합니다. 기존 필드의 의미가 바뀌면 새 `action` 이름을 도입하고 옛 필드는 유지합니다. 읽는 쪽은 `ts`/`action`/`phase` 기반으로 필터해서 혼용을 처리합니다.
- **스킬/에이전트 frontmatter 스키마**: 필드는 추가만, 제거 금지. `verify-skeleton.py`의 `AGENT_REQUIRED_FIELDS`가 현재 필수 집합입니다. 이 집합이 늘면 기존 프로젝트의 에이전트 파일에 수동 병합이 필요하므로, 확장 시 이 문서와 `AGENT_REGISTRY.md`에 동시 기재합니다.

이 정책의 한계는 명시적입니다: 자동화가 모든 의미 충돌을 해결하지는 않습니다. 대신 `verify-skeleton.py`와 `quality-gate.py`가 구조·검증 수준에서 잡고, upgrade runbook이 의미 수준의 사용자 승인 지점을 고정합니다.

## 자동화 현황

`scripts/upgrade-from-skeleton.py`는 기존 프로젝트를 dry-run으로 점검하고, 승인된 안전 파일만 적용하는 자동화 경로입니다. `scripts/bootstrap/new-project.py --force`는 greenfield 재시드용이므로 기존 프로젝트 업그레이드에는 쓰지 않습니다.

업그레이드 원칙은 변하지 않습니다: 먼저 dry-run diff를 보고, risky 변경은 proposal/review queue로 남기며, 승인 후에만 파일을 반영합니다. 적용 뒤에는 `python3 scripts/verify.py`와 `python3 scripts/quality-gate.py --format json`을 실행합니다.

`python3 scripts/agent-flow.py adopt --target <project> --format json`은 이 절차의 read-only 진입점입니다. 단일 명령으로 adoption을 끝내지 않고, 각 adoption slice 시작 전에 target git 상태, 라이선스 신호, 프로젝트 프로필 상태, safe missing 파일 수, ownership candidate 수, stop reason, next action을 한 번에 보고합니다.

0024의 `adopt` 표면은 `--status`와 기본 dry-run만 제공합니다. `--apply-safe`, `--verify`, `--rollback`, `--include-risky`는 의도적으로 노출하지 않습니다. 쓰기가 필요한 apply-safe 흐름은 별도 승인된 slice에서 dry-run을 다시 실행한 뒤 다룹니다.

### Overlay profile

기본 overlay profile은 `stable`입니다. 기능별 tier와 overlay 기본값은 `docs/feature-status.yaml`이 단일 진실 소스입니다.

- `stable`: `overlay_default=true`이고 `tier=stable`인 기능만 기본 추천합니다.
- `incubating`: stable 기능과 v2 incubating 기능을 함께 보여주되, brief에 변경 가능성과 수동 검토 필요성을 표시합니다.
- `all`: experimental adapter까지 보여줍니다. 이 profile의 experimental 항목은 승인 필요 대상으로 봅니다.

`stable` profile은 action 단계에서도 강제됩니다. `scripts/incubating/`, `docs/design/`, incubating phase plan처럼 v2 incubating runtime에 속하는 파일은 stable overlay 후보에서 제외되고 `skip:profile`로만 보고됩니다. stable apply는 이 파일을 복사하지 않습니다.

### Stable safe bundle

`--apply --safe-only --profile stable`은 기존 target 파일을 덮어쓰지 않고, target에 없는 v1 운영 OS 파일만 추가합니다. safe bundle은 명시적 allowlist입니다.

- Core scripts: `scripts/agent-flow.py`, `scripts/quality-gate.py`, `scripts/verify-skeleton.py`, `scripts/task-closeout.py`, `scripts/resume-readiness.py`, `scripts/source-recovery.py`, `scripts/knowledge-search.py`, `scripts/generate-codemaps.py`, `scripts/cleanup-ephemeral.py`, `scripts/upgrade-from-skeleton.py`, `scripts/search-activity-log.py`, `scripts/agent-brief.py`, `scripts/hooks/`, and top-level `scripts/*.py` that are missing in the target.
- Core config and contracts: `config/roles.yaml`, `config/policy.yaml`, `config/agent-team.yaml`, `config/install-profiles.yaml`, `runtime/AGENTS.md`.
- Rules and schemas: `rules/common/`, `rules/languages/`, `schemas/`.
- Stable docs: `docs/OPERATING_LOOP.md`, `docs/SESSION_CONTINUITY.md`, `docs/RUNTIME_EVENT_SCHEMA.md`, `docs/SKELETON_UPGRADE.md`, `docs/WORKFLOW_CATALOG.md`, `docs/FEATURE_DECISION_GUIDE.md`, `docs/AGENT_REGISTRY.md`, `docs/DOCUMENTATION_STYLE_GUIDE.md`.
- Canonical role/skill/rule sources: `agents/`, `skills/active/`, `skills/candidates/`, `skills/deprecated/`, `rules/`, `mcp/servers.yaml`, `AGENTS.md`.
- Generated surfaces: `.codex/`, `.claude/`, `.mcp.json`, `CLAUDE.md`. 이 경로들은 `scripts/convert.py`와 parity check로 재생성·검증하며 직접 편집하거나 overlay 기준으로 삼지 않습니다.

The safe bundle is still missing-file only. Existing target files with different content remain `update_available:risky` or `review:manual` and require explicit approval.

### Personal skill layer

`.agents/` is treated as a user-personal/generated layer. It is skipped by default and is not part of stable overlay. Use `--include-personal-skills` only when the user explicitly wants to import the skeleton's generated plugin/skill export layer into the target project.

### Reference candidate collisions

`research/reference-candidates/` is project-owned research state. The overlay tool does not copy the skeleton's candidate cards into an existing project by default. If a target project needs reference candidates, create or review them in that target project rather than importing the skeleton's historical cards silently.

### ENKI_WIKI retrofit case study (2026-05-17)

ENKI_WIKI was a retrofit target, not a fresh bootstrap. It already had app code,
historical runtime evidence, project plans, a Node/Next CI workflow, and earlier
safe overlay commits. The successful migration therefore treated "100% transfer"
as preserving target-owned operating data while bringing the stable AI operating
OS up to date.

The working sequence was:

1. Run `agent-flow adopt --target <target> --format json`
   as a read-only intake. Do not start from the target directory until the
   skeleton tools have reported the adoption state.
2. Use `ownership-initialize.py --target <target>` to draft
   project-specific ownership. A high candidate count is a normal stop condition,
   not an automation failure. ENKI initially required manual grouping before
   apply-safe could be trusted.
3. Apply only the stable safe bundle. Missing stable operating OS files can be
   copied, but existing runtime, state, knowledge, app, and CI files remain
   target-owned unless the user explicitly approves a manual merge.
4. Review manual/risky items path by path. ENKI intentionally preserved its own
   `.github/workflows/ci.yml` and `config/ownership.yaml` instead of accepting the
   skeleton copy, because those files encode project-specific CI and ownership
   overrides.
5. Re-run adoption as a read-only check. A final `needs_review` can be a healthy
   terminal signal when all remaining items are intentional preserves or metadata
   reviews such as an unknown target license.

The reusable lesson is preserve-first adoption. Safe-only means "copy missing
stable system assets"; it does not mean "make the target byte-for-byte identical
to the skeleton." Intentional preserves should be named in the handoff or
install-state evidence so later sessions do not try to "fix" them back to the
skeleton version.

## 기능 추가/수정 판단 기준

- 새 파일이 추가되면 위 세 영역 중 어디에 속하는지 분류하고 이 문서의 목록에 추가합니다.
- 기존 파일의 의미가 바뀌면(프로젝트 상태가 된다든지) 영역을 재분류합니다.
- 업그레이드 도구를 자동화할 때는 먼저 dry-run 모드에서 diff만 출력하고, 승인 후에만 복사합니다.

## 구현 연결 정보

- 부트스트랩 스크립트: `scripts/bootstrap/new-project.py`
- 건강 체크: `scripts/verify-skeleton.py`
- 활동 로그: `runtime/activity-log.jsonl`
- 거버넌스 기준: `docs/GOVERNANCE.md`
## 2026-04-29 upgrade automation

`scripts/upgrade-from-skeleton.py` now provides the automated path for this runbook.

Recommended flow:

1. Inspect existing projects without changing files:
   `python3 scripts/upgrade-from-skeleton.py --projects-root C:\Users\dntmd\Desktop\Projects`
2. Apply only safe missing files:
   `python3 scripts/upgrade-from-skeleton.py --projects-root C:\Users\dntmd\Desktop\Projects --apply --safe-only`
3. Review risky changed files manually. Do not overwrite project-specific files unless the user explicitly approves:
   `python3 scripts/upgrade-from-skeleton.py --target <project> --apply --include-risky`

Safe-only mode copies missing templates and README-style support files. It does not overwrite changed `AGENTS.md`, project profiles, runtime logs, handoff files, knowledge logs, local settings, generated artifacts, or cloned external repositories.

## 자동화 실행 원칙

스켈레톤 업그레이드도 사용자가 직접 diff 명령을 실행하거나 파일을 머지하는 절차가 아닙니다. 문서 안의 diff, verify, upgrade 명령은 에이전트가 수행해야 하는 운영 절차입니다.

위험한 병합 지점에서는 에이전트가 차이를 요약하고 승인 선택지를 제시합니다. 사용자는 채팅으로 승인, 거절, 보류, 방향 수정을 말합니다. 승인 후 실제 파일 반영, 검증 실행, 활동 로그 기록, 세션 인수인계 갱신은 에이전트가 수행합니다.

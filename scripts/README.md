# 자동화 스크립트 안내

## 한 문장 정의

이 문서는 프로젝트 부트스트랩, 활동 로그 기록, 지식 위키 린트, 스켈레톤 검증에 사용하는 로컬 자동화 스크립트를 설명합니다.

## Python 요구 사항

모든 스크립트는 **Python 3.9 이상**을 요구합니다. `Path.is_relative_to()` 같은 3.9+ API를 사용하므로 3.8 이하에서는 동작하지 않습니다.

## 무엇을 하는가

스크립트는 반복 작업을 사람이 매번 수동으로 하지 않게 합니다. 다만 핵심 문서나 지식을 조용히 바꾸는 자동화는 금지합니다. 기본 원칙은 검증, 기록, 부트스트랩처럼 안전한 작업을 자동화하고, 위험한 변경은 제안으로 남기는 것입니다.

외부 오픈소스 저장소를 clone해 분석할 때 원본은 `runtime/external-repos/` 아래에 둡니다. 새 프로젝트 부트스트랩은 이 디렉터리의 README만 보존하고 clone 원본은 복사하지 않습니다.

## 왜 필요한가

문서와 운영 규칙만 있으면 사람이 실수로 누락할 수 있습니다. 스크립트는 새 프로젝트 생성, 로그 기록, 위키 검증, 구조 검사를 일관되게 수행해 운영 품질을 유지합니다.

## 사용할 수 있는 스크립트

- `scripts/hooks/post-tool-use-log.py`: 도구 사용이나 주요 행동 결과를 활동 로그에 추가합니다.
- `scripts/bootstrap/new-project.py`: 새 프로젝트 디렉터리를 만들고 프로필을 시드하며 내부 상태를 초기화합니다.
- `scripts/wiki-lint.py`: 지식 위키의 오래된 항목, 중복, 대체 표시, 고아 항목, 출처 누락을 검사합니다.
- `scripts/verify-skeleton.py`: 스켈레톤 또는 부트스트랩된 프로젝트의 구조, 필수 경로, 에이전트 메타데이터, JSONL 파싱, 후보 카드, 위키 린트를 확인합니다.
- `scripts/rotate-activity-log.py`: `runtime/activity-log.jsonl`과 `runtime/agent-runs.jsonl`이 10,000줄을 넘으면 `runtime/archive/<base>-YYYY-MM.jsonl`로 월 단위 아카이브합니다. 기본값은 dry-run이며 `--apply`로 실행합니다.
- `scripts/search-activity-log.py`: 활동 로그를 읽어 `--since/--until/--phase/--action/--project/--tool/--contains` 필터로 검색합니다. 세션 복기와 감사에 사용합니다. 기본 출력은 표, `--jsonl`로 원본 JSONL 스트림.
- `scripts/list-open-questions.py`: 프로젝트 전체 `**/*.md`를 스캔해 `[NEEDS CLARIFICATION: ...]` 마커를 집계합니다. `--count/--by-file/--json`, CI 게이트용 `--strict` 지원.
- `scripts/quality-gate.py`: 현재 프로젝트에서 사용 가능한 검증 표면을 감지해 한 번에 실행합니다. Skeleton 검증, review queue count, Python 문법 검사, unittest, `package.json`의 `npm run test/build`를 지원합니다.
- `scripts/review-queue.py`: 에이전트가 혼자 결정하면 안 되는 항목을 `runtime/review-queue.jsonl`에 append-only 이벤트로 남깁니다. Notion 중복, risky upgrade, reference adoption 승인 대기 같은 항목을 `add/list/resolve/dismiss/count`로 관리합니다.
- `scripts/validate-reference-candidates.py`: `research/reference-candidates/`의 실제 후보 카드가 필수 필드, 허용 값, 점수 합계, 리스트 항목을 갖췄는지 검사합니다.
- `scripts/validate-reference-proposals.py`: `runtime/proposals/reference-adoption/`의 실제 dry-run 제안서가 필수 필드, 후보 카드 링크, 모듈형 흡수 판단, 검증 계획, 중단 조건을 갖췄는지 검사합니다.
- `scripts/create-reference-proposal.py`: 후보 카드에서 reference-adoption dry-run 제안서 초안을 만듭니다. 기본은 화면 출력이며, 에이전트가 승인된 경우 `--write`로 파일을 생성합니다. 제안서에는 dependency, wrapper, partial copy, concept-only, direct implementation 중 어떤 흡수 방식을 택할지 판단하는 섹션이 포함됩니다. 후보 카드가 `adoption_decision: copy`이면 개인 로컬 사용을 전제로 partial copy 경계를 기록하게 합니다.
- `scripts/notion-doc-quality-check.py`: Notion에 올릴 Markdown 초안이 기능 중심 섹션, 입력/출력, 성공/실패 신호, 판단 기준을 갖췄는지 검사합니다. 짧은 changelog나 파일 목록 중심 문서를 완료 문서로 올리지 않기 위한 사전 점검입니다.
- `scripts/skeleton-doctor.py`: 프로젝트가 바로 문서화, reference review, runtime startup, 로그/인수인계, 구조 검증을 수행할 준비가 되었는지 `OK/WARN/FAIL/INFO`로 진단합니다. 기본은 read-only이며 `--format json`과 선택적 `--projects-root` 전파 상태 점검을 지원합니다.
- `scripts/resume-readiness.py`: 다음 에이전트가 handoff, activity log, completion evidence를 보고 추측 없이 이어받을 수 있는지 검사합니다. `--strict`에서는 handoff보다 최신인 runtime 기록도 실패로 올립니다.
- `scripts/skill-surface-check.py`: `.codex/skills`를 canonical로 두고 `.claude/skills`가 중복 payload 없이 compatibility shim으로 유지되는지 검사합니다.
- `scripts/security-scan.py`: 운영 문서, scripts, hooks, agent/skill 설정, reference adoption 산출물을 read-only로 훑어 secret, 위험한 명령, 위험한 hook/config, 코드 복사 governance 누락을 찾습니다. 기본은 보고 전용이며 `--strict`에서 HIGH/CRITICAL finding이 있으면 실패합니다.

이 스크립트들은 사용자가 직접 실행해야 하는 UI가 아닙니다. 에이전트가 구조 검증, 반복 작업, 승인 후 반영을 안정적으로 수행하기 위해 사용하는 내부 운영 도구입니다.

## 활동 로그 쿼리 예시

```powershell
# 최근 20개 이벤트 요약
python scripts/search-activity-log.py

# 이번 주 refactor phase만
python scripts/search-activity-log.py --since 2026-04-20 --phase refactor

# 특정 에이전트가 남긴 summary 검색
python scripts/search-activity-log.py --contains "rotation lock" --last 5
```

## 어떻게 동작하는가

스크립트는 가능한 한 플랫폼 의존성을 줄이고, 프로젝트 경계 안에서만 동작합니다. 쓰기 작업이 있으면 경로 포함 여부를 확인하고, 핵심 설정이나 장기 지식을 직접 수정하지 않습니다.

## 결과는 무엇인가

자동화 스크립트를 사용하면 새 프로젝트 시작과 구조 검증이 재현 가능해집니다. 검증 결과가 실패하면 어떤 기준이 깨졌는지 빠르게 확인할 수 있습니다.

## 기능 추가/수정 판단 기준

새 스크립트는 반복 작업을 줄이고 검증 가능해야 합니다. 사용자 승인 없이 핵심 문서, 규칙, 지식, 런타임 설정을 바꾸는 스크립트는 만들지 않습니다. 위험한 변경은 먼저 dry-run 또는 proposal 모드로 둡니다.

## 스크립트 요구사항

- 크로스 플랫폼이거나 런타임 제한을 명시합니다.
- 린트나 제안 스크립트는 기본적으로 dry-run을 선호합니다.
- 프로젝트 밖에 쓰지 않습니다.
- 쓰기 전 경로 포함 여부를 확인합니다.
- JSONL 출력은 파싱 가능해야 합니다.
- 런타임 소유 설정은 수정하지 않습니다.
## 2026-04-29 skeleton upgrade automation

- `scripts/upgrade-from-skeleton.py` plans or applies safe skeleton updates to existing projects.
- Default mode is dry-run and prints what would be added, skipped, or reviewed.
- `--apply --safe-only` copies only missing safe files, such as templates and README files.
- Existing files with different content are reported as risky and are not overwritten in safe-only mode.
- Project-owned runtime state, activity logs, handoff files, knowledge logs, local settings, and project profile/spec files are protected.

## 2026-04-29 skeleton doctor

- `scripts/skeleton-doctor.py` is the next diagnostic layer above `verify-skeleton.py`.
- `verify-skeleton.py` answers whether required structure is internally consistent.
- `skeleton-doctor.py` answers whether an agent can start or resume real work safely: profile fields, reference review surface, runtime startup surface, JSONL logs, handoff state, open questions, and structural validation.
- Use `--projects-root C:\Users\dntmd\Desktop\Projects` to summarize whether existing projects still have safe missing skeleton updates or risky review-only changes.

## 2026-04-29 review queue

- `runtime/review-queue.jsonl` is the durable human-decision queue.
- It is for decisions the agent should not make alone: duplicate Notion pages, conflicting docs, missing docs, reference adoption approvals, and risky skeleton upgrade items.
- The file is append-only JSONL. `scripts/review-queue.py` reconstructs the current item state from events, so resolution history remains auditable.
- Duplicate open items are merged by `type + normalized title` instead of creating repeated review rows.

## 2026-04-29 quality gate

- `scripts/quality-gate.py` is the operator-invoked validation gate.
- It does not replace `skeleton-doctor.py`: doctor explains readiness, quality gate runs concrete checks.
- Default checks are `verify-skeleton.py`, agent autonomy, review queue count, completion evidence, security scan, resume readiness, skill surface, Python syntax parsing, `python -m unittest discover -s tests -v`, and npm `test/build` when `package.json` declares them.
- Use `--skip-tests` when calling it from tests to avoid recursive unittest execution.
- Use `--format json` for automation and `--strict` when unresolved warnings should fail the gate.

## 2026-04-30 copied-source ledger

- `scripts/reference-copy-ledger.py` records actual copied-source provenance in `runtime/reference-copy-ledger.jsonl`.
- This is an agent responsibility, not a user chore. When an agent copies open-source code into local files, the same agent must run `add`, then run `check` and `security-scan.py --strict` before closing the task.
- Use `list` only for inspection and handoff review.
- Each record stores source URL, license, revision, source path, local path, copy boundary, and whether redistribution needs a fresh review.
- Agent-facing example:

```powershell
python scripts/reference-copy-ledger.py add --source-url https://github.com/example/project --license MIT --revision abc123 --source-path src/helper.py --local-path scripts/helper.py --copy-boundary "single helper only"
python scripts/reference-copy-ledger.py list
python scripts/reference-copy-ledger.py check
```

- `scripts/security-scan.py` reports a MEDIUM governance finding when a `copy` or `partial_copy` artifact has no matching ledger record.

## 2026-04-30 agent closeout automation

- `scripts/agent-autonomy-check.py --strict` prevents the skeleton from drifting back to "user runs the command" language.
- `scripts/task-closeout.py` is the preferred final gate for agent work. It chooses checks from changed paths or an explicit profile and can record evidence.
- `runtime/completion-evidence.jsonl` is written by agents, not users. It records the goal, changed paths, validations, outcome, residual risk, and next action.
- `scripts/security-scan.py` supports `rules/security-scan-allowlist.json` for justified known findings. Suppressed findings are counted separately in JSON output.
- `scripts/resume-readiness.py --strict` checks that handoff, activity log, and completion evidence are aligned before another agent resumes.
- `scripts/skill-surface-check.py --strict` prevents the project from drifting back to duplicated `.codex/.claude` skill payloads.

## 2026-04-30 skill surface optimization

- `.codex/skills` is the canonical project skill tree for Codex.
- `.claude/skills` keeps Claude-compatible entries, but any skill that also exists under `.codex/skills` must be a thin compatibility shim.
- Shimmed `.claude` skills preserve the original frontmatter for discovery and point the agent to the canonical `.codex` skill file.
- Do not add helper scripts, assets, references, or copied payload files to a `.claude` skill when the same skill exists in `.codex`; add them only to the canonical `.codex` tree and run `scripts/skill-surface-check.py --strict`.

## 2026-04-30 test suite split

- Smoke tests are split by subsystem instead of living in one large file.
- Shared subprocess helpers live in `tests/test_support.py`.
- Add new validation/gate tests to `tests/test_validation.py`, runtime ledger and closeout tests to `tests/test_runtime.py`, reference/security tests to `tests/test_reference_security.py`, and bootstrap/upgrade tests to `tests/test_bootstrap_upgrade.py`.

## Agent-run command contract

Commands in this document are agent-run contracts. The user normally should not run them. When a task depends on a script, the agent runs it, summarizes the result, and records important outcomes in the activity log or handoff when project state changes.

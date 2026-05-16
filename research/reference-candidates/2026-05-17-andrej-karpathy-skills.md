# andrej-karpathy-skills

## 기본 정보

- `name`: andrej-karpathy-skills
- `url`: https://github.com/multica-ai/andrej-karpathy-skills.git
- `source_type`: repository
- `status`: reviewing
- `searched_for`: LLM coding behavior guidelines, anti-overcomplication checklist, surgical-edit principles, goal-driven verification framing
- `created_at`: 2026-05-17
- `reviewed_at`: 2026-05-17
- `reviewer`: claude
- `query_provenance`: user-provided named reference cloned into AI_architecture_references
- `candidate_rank`: 1
- `candidate_count`: 1

## 왜 보는가

- `problem_statement`: LLM 코딩 에이전트가 가정을 숨기고 과한 추상화/orthogonal 변경을 만드는 행동 문제. 우리는 rules/common/code-style.md, brainstorming skill, surgical edit 가이드에서 이를 다루지만 외부에서 검증된 압축 체크리스트는 부재.
- `why_it_matters`: Karpathy의 LLM coding pitfalls 관찰(X post 2015883857489522876)을 4원칙(Think Before Coding / Simplicity First / Surgical Changes / Goal-Driven Execution)으로 단일 CLAUDE.md에 압축한 외부 표현이다. 우리 rules가 다루는 같은 문제를 다른 단어로 정리한 cross-check 자료로 가치가 있다.
- `expected_value`: 우리 brainstorming/code-style/surgical-change 가이드 단순화 검토 시 외부 기준으로 인용 가능하고, 새 프로젝트 부트스트랩에서 인용할 수 있는 짧은 외부 권위 참조가 생긴다. 의미 중복이 있는 만큼 직접 흡수 가치는 낮다.

## 유용한 패턴

- `useful_patterns`:
  - 4 short principles in a single CLAUDE.md (no long appendix, no inline examples)
  - Same content republished as Claude Code skill (`skills/karpathy-guidelines/SKILL.md`) with `name`/`description`/`license` frontmatter
  - `.claude-plugin/marketplace.json` + `plugin.json` showing one-skill plugin distribution shape
  - EXAMPLES.md as a separate file demonstrating good vs bad behaviors without bloating the rule itself
- `what_to_copy_conceptually`:
  - "State assumptions explicitly. If multiple interpretations exist, present them - don't pick silently." framing for our brainstorming and start phases.
  - "Every changed line should trace directly to the user's request." surgical-edit test phrase.
  - "Strong success criteria let you loop independently." goal-driven verification framing for our quality-gate/verify language.
- `what_to_copy_directly`:
  - none for now (concept-only reference; no file copy planned)
- `what_not_to_copy`:
  - The skill itself as a plugin into `.claude/skills/` (we already have brainstorming, tdd-workflow, code-review-expert covering the same territory).
  - `.claude-plugin/marketplace.json` and `plugin.json` (Claude Code plugin marketplace distribution is out of scope for our skeleton).
  - EXAMPLES.md verbatim (domain examples are not aligned with our agent-flow surface).

## 구조 분석

- `module_inventory`:
  - CLAUDE.md (65 lines, 4 numbered principles)
  - skills/karpathy-guidelines/SKILL.md (Claude skill duplicating CLAUDE.md content with frontmatter)
  - EXAMPLES.md (522 lines, good vs bad example dialogues)
  - .claude-plugin/marketplace.json + plugin.json (plugin distribution manifest)
  - CURSOR.md (28 lines, Cursor-adapted variant), README.md, README.zh.md
- `reusable_units`:
  - Single-file behavioral CLAUDE.md as canonical source
  - SKILL.md frontmatter pattern (`name`/`description`/`license`) republishing the same content for skill invocation surface
  - Separate EXAMPLES.md so the rule file stays short

## 증거

- `evidence_summary`: README, CLAUDE.md, SKILL.md, EXAMPLES.md, and the .claude-plugin manifests were inspected on the local clone. Repo provides four principles in CLAUDE.md and republishes them as a Claude skill; no executable code; no LICENSE file at repo root but the SKILL.md frontmatter declares `license: MIT`.
- `local_clone_path`: ../AI_architecture_references/andrej-karpathy-skills
- `checked_revision`: 2c606141936f1eeef17fa3043a72095b4765b9c2
- `freshness_signal`: Last commit 2026-04-20 (Chinese README sync). Small repo, low commit frequency.
- `maintenance_signal`: Single-author small repo by multica-ai; README links to a separate Multica platform project as the active product.
- `documentation_signal`: README, CLAUDE.md, CURSOR.md, EXAMPLES.md, and README.zh.md cover the same 4 principles in different surfaces.
- `validation_signal`: Local files inspected only; no code execution required since the repo is text-only guidelines.
- `sources`:
  - {"path":"../AI_architecture_references/andrej-karpathy-skills/README.md","kind":"readme","evidence":"Four principles, motivation from Karpathy X post, problem framing.","hash_or_line_ref":"local-reference"}
  - {"path":"../AI_architecture_references/andrej-karpathy-skills/CLAUDE.md","kind":"source_file","evidence":"Canonical 4-principle behavior guideline used as CLAUDE.md drop-in.","hash_or_line_ref":"lines 1-65"}
  - {"path":"../AI_architecture_references/andrej-karpathy-skills/skills/karpathy-guidelines/SKILL.md","kind":"source_file","evidence":"Same content republished as Claude skill with name/description/license frontmatter.","hash_or_line_ref":"lines 1-67"}
  - {"path":"../AI_architecture_references/andrej-karpathy-skills/EXAMPLES.md","kind":"docs","evidence":"Worked good-vs-bad behavior examples illustrating each principle.","hash_or_line_ref":"local-reference"}
  - {"path":"../AI_architecture_references/andrej-karpathy-skills/.claude-plugin/plugin.json","kind":"manifest","evidence":"Single-skill Claude Code plugin manifest shape.","hash_or_line_ref":"local-reference"}

## 리스크

- `license`: MIT (declared in skills/karpathy-guidelines/SKILL.md frontmatter; repo root has no LICENSE file). Personal local-use only until LICENSE is confirmed upstream.
- `security_or_privacy_risk`: None. Text-only guidelines, no executable code, no telemetry.
- `maintenance_risk`: Small single-author repo with infrequent commits. Authoritative principles are anchored to a static Karpathy X post and unlikely to evolve fast, which lowers but does not remove update risk.
- `complexity_risk`: Very low. Four short principles in a single 65-line file.
- `dependency_risk`: None. No code, no runtime dependencies.
- `fit_risk`: Semantic overlap with our existing rules/common/code-style.md, brainstorming skill, tdd-workflow skill, and code-review-expert skill. Directly importing as a separate skill would create duplicate phrasing of overlapping rules in two places.

## 적용 후보

- `applies_to`: rules | skills | docs
- `target_files_or_areas`:
  - rules/common/code-style.md (cross-reference 또는 단순화 비교 기준으로 사용)
  - .claude/skills/brainstorming/SKILL.md (Surface-assumptions framing 비교)
  - docs/DOCUMENTATION_STYLE_GUIDE.md (짧은 외부 권위 인용 가능)
  - references.yaml (tracked reference 등록)
- `adoption_decision`: adapt
- `absorption_mode`: concept_only
- `direct_implementation_reason`: not applicable
- `decision_reason`: 우리 기존 rules/skills가 4원칙과 의미상 같은 영역을 다루므로 별도 skill로 흡수하면 중복이 생긴다. 외부 검증된 압축 표현으로 reference에 두고 우리 규칙 단순화 검토 시 비교 기준으로 인용하는 것이 가치 대비 비용 측면에서 가장 정직하다.
- `next_action`: 후보 카드 및 references.yaml 등록까지만 수행. 흡수 결정(어떤 문구를 우리 규칙에 인용하거나 단순화에 반영할지)은 별도 dry-run 제안으로 분리.

## 점수

| 기준 | 배점 | 점수 | 근거 |
| --- | ---: | ---: | --- |
| 문제 적합성 | 20 | 16 | LLM coding behavior 문제는 우리 핵심 영역이지만 4원칙이 우리 기존 rules/skills와 의미 중복이 커서 새로 추가하는 한계 가치는 중간. |
| 구조 명확성 | 15 | 14 | 65줄 단일 파일에 4 section. 매우 명료. |
| 검증 가능성 | 15 | 9 | 추상 원칙이라 자동 검증보다 코드 리뷰/사람 판단에 의존. |
| 유지보수 신호 | 15 | 8 | 작은 single-author repo, 최근 커밋 2026-04-20, 활동량 적음. |
| 흡수 비용 | 15 | 13 | concept_only 경로면 추가 비용 거의 없음. |
| 보안/라이선스 리스크 | 10 | 6 | frontmatter MIT 선언은 있으나 repo root LICENSE 부재로 불확실. |
| 설명 가치 | 10 | 9 | Karpathy 외부 권위 인용 + 짧은 압축 표현이 설명용으로 유용. |
| 합계 | 100 | 75 |  |

## Dry-Run 제안

- `proposal_needed`: no
- `files_to_change`:
  - none (this card registers the reference; absorption decisions go into a separate dry-run proposal)
- `behavior_change`: No behavior change introduced by this card. Any future absorption (e.g., quoting Karpathy phrasing in rules/common/code-style.md) will be proposed and approved separately.
- `validation_plan`: python3 scripts/validate-reference-candidates.py && python3 scripts/verify-skeleton.py
- `rollback_or_stop_condition`: Stop and re-review if the upstream repo retroactively changes its license or removes the MIT declaration; in that case revoke the references.yaml entry and mark this card status=deferred.
- `approval_required`: yes
- `copy_boundary`: not applicable

## 최종 기록

- `final_status`: reviewing
- `implemented_in`:
  - not implemented
- `validation_result`: candidate card only
- `activity_log_entry`: not recorded
- `notes`: Concept-only reference. No code copied. Repo root has no LICENSE file; MIT relied on SKILL.md frontmatter. Absorption decisions intentionally deferred to a separate dry-run proposal to avoid duplicating existing rules/skills.

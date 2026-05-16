#!/usr/bin/env python3
"""Single entrypoint for the common agent operating flows.

This script deliberately stays thin. It wraps the existing project tools in a
small number of commands so agents do not need to remember the internal order
of reference intake, proposal review, verification, and closeout.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from importlib import util
from pathlib import Path
from typing import Any

from lib_catalog import load_catalog_modes_with_status as load_shared_catalog_modes_with_status
from redact import redact_json


try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass


DECISION_ALIASES = {"accept": "accepted", "reject": "rejected", "defer": "deferred"}
DECISIONS = {"accepted", "rejected", "deferred", *DECISION_ALIASES}
MODES = {"decide", "research", "build", "maintain", "closeout"}
SPECIALIST_SCHEMA = "ai-architecture.specialist-proposal.v1"
DELEGATION_PLAN_SCHEMA = "ai-architecture.delegation-plan.v1"
SPECIALIST_USAGE_SCHEMA = "ai-architecture.specialist-usage.v1"
SPECIALIST_STATUSES = {"draft", "approved", "rejected"}
WRITE_POLICIES = {"read_only", "manual_work_required", "write_with_confirmation"}
ON_DEMAND_TRIGGERS: dict[str, tuple[str, ...]] = {
    "context_isolation": ("context isolation", "context bloat", "many files", "logs", "research", "조사", "분석", "컨텍스트", "로그"),
    "parallel_work": ("parallel", "independent", "fan out", "병렬", "독립"),
    "second_opinion": ("review", "validation", "verify", "security", "compliance", "fresh perspective", "검토", "검증", "보안"),
    "permission_boundary": ("permission", "read-only", "least privilege", "scope", "권한", "범위"),
    "repeated_pattern": ("repeated", "recurring", "again", "반복", "자주"),
    "sequential_precondition": ("precondition", "approval", "sequence", "단계", "승인"),
    "long_running": ("long-running", "high-volume", "test suite", "대량", "장시간"),
}
ANTI_TRIGGERS: dict[str, tuple[str, ...]] = {
    "quick_targeted": ("quick", "tiny", "simple", "typo", "focused", "빠른", "간단", "오타"),
    "tight_back_and_forth": ("back-and-forth", "interactive", "iterate with user", "대화", "반복 대화"),
    "duplicate_base_role": ("duplicate", "already covered", "base role", "중복"),
    "specialist_sprawl": ("many specialists", "everything", "sprawl", "전부", "무조건"),
}
REPO_MARKERS = {
    "README",
    "README.md",
    "LICENSE",
    "LICENSE.md",
    "LICENSE.txt",
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "Cargo.toml",
    "go.mod",
}
REPO_DIR_MARKERS = {".git", "scripts", "src", "tests"}
REFERENCE_ALIASES: dict[str, tuple[str, ...]] = {
    "ecc": ("everything-claude-code",),
    "everything claude code": ("everything-claude-code",),
    "everything-claude-code": ("everything-claude-code",),
    "opencode": ("opencode",),
    "open code": ("opencode",),
    "hermes": ("hermes-agent",),
    "hermes-agent": ("hermes-agent",),
    "llm wiki": ("llm_wiki",),
    "llm-wiki": ("llm_wiki",),
    "llm_wiki": ("llm_wiki",),
    "paperclip": ("paperclip",),
}
DEFAULT_MODE_CONFIGS: dict[str, dict[str, Any]] = {
    "research": [
        ("goal_pattern", r"(오픈소스|open\s*source|oss|reference|레퍼런스|참고|비슷한|기존\s*서비스|클론|clone|분석|찾아|찾고|새\s*프로젝트|프로젝트\s*시작)"),
        ("reason", "자연어 요청에 새 프로젝트, 오픈소스, 레퍼런스, 클론, 분석 의도가 포함되어 reference-first 흐름이 적합합니다."),
        ("next_command", "python3 scripts/agent-flow.py research --auto --format json"),
        ("confidence", "high"),
        ("requires_confirmation", False),
        ("write_policy", "read_only"),
        ("signal", "goal_mentions_reference"),
        ("suggested_questions", [
            "프로젝트 타입은 webapp, cli, lib, api, data-pipeline 중 무엇에 가깝나요?",
            "우선 참고해야 할 레퍼런스나 경쟁 서비스가 있나요?",
            "MVP가 성공했다고 볼 수 있는 최소 기준은 무엇인가요?",
        ]),
    ],
    "closeout": [
        ("goal_pattern", r"(검증|마무리|완료|종료|closeout|quality\s*gate|verify)"),
        ("reason", "자연어 요청이 검증, 완료, 마무리 흐름을 요구합니다."),
        ("next_command", 'python3 scripts/agent-flow.py closeout --goal "{goal}" --changed-path . --format json'),
        ("confidence", "high"),
        ("requires_confirmation", True),
        ("write_policy", "write_with_confirmation"),
        ("signal", "goal_mentions_closeout"),
        ("suggested_questions", [
            "완료 증거에 기록할 목표명은 무엇인가요?",
            "이번 작업에서 바뀐 주요 경로는 어디인가요?",
            "검증에서 반드시 확인해야 할 기대 결과는 무엇인가요?",
        ]),
    ],
    "maintain": [
        ("goal_pattern", r"(스켈레톤|뼈대|하네스|운영\s*시스템|시스템\s*개선|agent-flow|agent\s*flow|시스템\s*구조|구조\s*개선|AI_architecture|catalog|카탈로그)"),
        ("reason", "자연어 요청이 스켈레톤이나 운영 시스템 자체 개선에 가깝습니다."),
        ("next_command", "manual: clarify maintain target, implement approved changes, then run agent-flow closeout"),
        ("confidence", "medium"),
        ("requires_confirmation", False),
        ("write_policy", "manual_work_required"),
        ("signal", "goal_mentions_maintain"),
        ("suggested_questions", [
            "개선하려는 대상은 라우팅, 검증, 문서, 스킬, 레퍼런스 흐름 중 어디인가요?",
            "단순화, 자동화, 안정성 중 무엇을 가장 우선할까요?",
            "반드시 유지해야 하는 기존 동작이나 호환성이 있나요?",
        ]),
    ],
    "build": [
        ("reason", "자연어 요청에 reference, maintain, closeout 신호가 없어 일반 구현 흐름으로 분류합니다."),
        ("next_command", "manual: clarify build scope, implement approved changes, then run agent-flow closeout"),
        ("confidence", "medium"),
        ("requires_confirmation", False),
        ("write_policy", "manual_work_required"),
        ("signal", "goal_mentions_build"),
        ("suggested_questions", [
            "이번에 구현할 정확한 범위는 어디까지인가요?",
            "완료 여부를 판단할 수용 기준이나 테스트 시나리오는 무엇인가요?",
            "선호하는 스택, 라이브러리, 피해야 할 제약이 있나요?",
        ]),
    ],
    "decide": [
        ("reason", "열린 review queue 항목이 있어 새 작업보다 사용자 결정 동기화가 우선입니다."),
        ("next_command", "python3 scripts/agent-flow.py decide --proposal <proposal-path> --decision accepted|rejected|deferred --by <name> --format json"),
        ("confidence", "high"),
        ("requires_confirmation", True),
        ("write_policy", "read_only"),
        ("signal", "open_review_queue"),
        ("suggested_questions", [
            "이 proposal은 accepted, rejected, deferred 중 무엇으로 기록할까요?",
            "그 결정을 내리는 핵심 근거는 무엇인가요?",
            "승인한다면 실제 반영 범위는 어디까지인가요?",
        ]),
    ],
}
for _mode, _items in list(DEFAULT_MODE_CONFIGS.items()):
    DEFAULT_MODE_CONFIGS[_mode] = dict(_items)

FAILURE_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("timeout", ("timed out", "timeout", "deadline exceeded")),
    ("auth", ("unauthorized", "authentication", "forbidden", "invalid api key", "permission denied")),
    ("quota", ("rate limit", "quota", "too many requests", "429", "insufficient credits")),
    ("format", ("jsondecode", "invalid json", "parse error", "schema", "frontmatter", "yaml")),
    ("payload", ("payload too large", "request entity too large", "maximum context", "context length", "too many tokens")),
    ("policy", ("blocked by policy", "confirmation required", "outside repo", "not allowed", "denied by policy")),
    ("infra", ("connection refused", "dns", "network", "no such file", "not found", "exit 127", "broken pipe")),
]


@dataclass
class CommandResult:
    name: str
    command: list[str]
    exit_code: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.exit_code == 0


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def command_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def resolve_under_root(root: Path, value: str) -> Path:
    path = Path(value)
    resolved = path.resolve(strict=False) if path.is_absolute() else (root / path).resolve(strict=False)
    resolved.relative_to(root.resolve(strict=False))
    return resolved


def rel_to_root(root: Path, path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(root.resolve(strict=False)).as_posix()
    except ValueError:
        return path.as_posix()


def run_command(root: Path, name: str, command: list[str], timeout: int) -> CommandResult:
    try:
        result = subprocess.run(
            command,
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=command_env(),
            timeout=timeout,
        )
        return CommandResult(name, command, result.returncode, result.stdout, result.stderr)
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        return CommandResult(name, command, 124, stdout, stderr or f"timed out after {timeout}s")


def compact_output(value: str, *, max_chars: int = 800) -> str:
    text = value.strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def classify_failure(text: str) -> str:
    haystack = text.lower()
    for category, needles in FAILURE_RULES:
        if any(needle in haystack for needle in needles):
            return category
    return "unknown"


def result_payload(result: CommandResult) -> dict[str, Any]:
    payload = {
        "name": result.name,
        "exit_code": result.exit_code,
        "ok": result.ok,
        "stdout": compact_output(result.stdout),
        "stderr": compact_output(result.stderr),
    }
    if not result.ok:
        payload["failure_type"] = classify_failure((result.stdout or "") + "\n" + (result.stderr or ""))
    return payload


def prevalidated_check_payload(result: CommandResult) -> str:
    return json.dumps(
        {
            "name": result.name,
            "status": "OK" if result.ok else "FAIL",
            "command": result.command,
            "exit_code": result.exit_code,
            "detail": compact_output((result.stdout or "") + "\n" + (result.stderr or "")),
            "failure_type": "" if result.ok else classify_failure((result.stdout or "") + "\n" + (result.stderr or "")),
        },
        ensure_ascii=False,
    )


def read_json_stdout(result: CommandResult, fallback: Any) -> Any:
    if not result.ok:
        return fallback
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return fallback


def specialist_proposal_dir(root: Path) -> Path:
    return root / "runtime" / "proposals" / "specialists"


def delegation_plan_dir(root: Path) -> Path:
    return root / "runtime" / "delegation-plans"


def specialist_usage_path(root: Path) -> Path:
    return root / "runtime" / "specialist-usage.jsonl"


def slugify_ascii(value: str, fallback: str = "item") -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or fallback


def next_json_sequence(directory: Path, prefix: str) -> int:
    highest = 0
    if directory.exists():
        for path in directory.glob(f"{prefix}-*.json"):
            suffix = path.stem.removeprefix(prefix + "-")
            if suffix.isdigit():
                highest = max(highest, int(suffix))
    return highest + 1


def specialist_proposal_id(root: Path, role: str) -> str:
    directory = specialist_proposal_dir(root)
    date_part = utc_now()[:10]
    prefix = f"sp-{date_part}-{slugify_ascii(role, 'specialist')}"
    return f"{prefix}-{next_json_sequence(directory, prefix):02d}"


def delegation_plan_id(root: Path) -> str:
    directory = delegation_plan_dir(root)
    date_part = utc_now()[:10]
    prefix = f"dp-{date_part}"
    return f"{prefix}-{next_json_sequence(directory, prefix):02d}"


def next_specialist_usage_sequence(root: Path) -> int:
    path = specialist_usage_path(root)
    if not path.exists():
        return 1
    count = 0
    for line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        if line.strip():
            count += 1
    return count + 1


def match_terms(text: str, patterns: dict[str, tuple[str, ...]]) -> list[str]:
    lowered = text.lower()
    matches: list[str] = []
    for name, terms in patterns.items():
        if any(term.lower() in lowered for term in terms):
            matches.append(name)
    return matches


def load_json_file(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path.as_posix()} invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path.as_posix()} must contain a JSON object")
    return data


def write_json_file(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_jsonl_file(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def command_name(args: argparse.Namespace) -> str:
    if getattr(args, "specialist_command", ""):
        return f"specialist.{args.specialist_command}"
    return str(getattr(args, "command", "") or "")


def specialist_usage_event(
    root: Path,
    *,
    event_type: str,
    args: argparse.Namespace,
    outcome: str,
    goal: str = "",
    proposal: dict[str, Any] | None = None,
    proposal_path: Path | None = None,
    plan: dict[str, Any] | None = None,
    plan_path: Path | None = None,
    handoffs: list[dict[str, Any]] | None = None,
    validation_refs: list[str] | None = None,
    reason: str = "",
    user_decision: str = "",
    confirmed: bool = False,
) -> dict[str, Any]:
    handoffs = handoffs or []
    proposal = proposal or {}
    plan = plan or {}
    candidate_roles = [str(role) for role in plan.get("candidate_roles", [])] if isinstance(plan.get("candidate_roles"), list) else []
    selected_roles = [str(role) for role in plan.get("selected_roles", [])] if isinstance(plan.get("selected_roles"), list) else []
    rejected_roles = [role for role in candidate_roles if role not in set(selected_roles)]
    artifact_paths: list[str] = []
    if proposal_path is not None:
        artifact_paths.append(rel_to_root(root, proposal_path))
    if plan_path is not None:
        artifact_paths.append(rel_to_root(root, plan_path))
    handoff_paths = [str(item.get("handoff_path") or item.get("brief_path") or "") for item in handoffs]
    handoff_paths = [path for path in handoff_paths if path]
    sequence = next_specialist_usage_sequence(root)
    event = {
        "event_id": f"su-{utc_now().replace(':', '').replace('-', '')}-{sequence:04d}",
        "ts": utc_now(),
        "schema_version": SPECIALIST_USAGE_SCHEMA,
        "event_type": event_type,
        "goal": goal or str(plan.get("goal") or ""),
        "actor": str(getattr(args, "by", "") or getattr(args, "created_by", "") or "codex"),
        "command": command_name(args),
        "outcome": outcome,
        "proposal_id": str(proposal.get("proposal_id") or ""),
        "plan_id": str(plan.get("plan_id") or ""),
        "candidate_roles": candidate_roles,
        "selected_roles": selected_roles,
        "rejected_roles": rejected_roles,
        "role_source": plan.get("role_source") if isinstance(plan.get("role_source"), dict) else {},
        "score_reasons": plan.get("score_reasons") if isinstance(plan.get("score_reasons"), dict) else {},
        "user_decision": user_decision,
        "reason": reason or str(proposal.get("reason") or ""),
        "requires_confirmation": bool(plan.get("requires_confirmation", False)),
        "confirmed": confirmed,
        "artifact_paths": artifact_paths,
        "handoff_paths": handoff_paths,
        "validation_refs": validation_refs or [],
    }
    return redact_json(event)


def append_specialist_usage(root: Path, event: dict[str, Any]) -> str:
    path = specialist_usage_path(root)
    append_jsonl_file(path, event)
    return rel_to_root(root, path)


def proposal_path_from_arg(root: Path, value: str) -> Path:
    path = Path(value)
    if not path.suffix and not path.is_absolute() and "/" not in value:
        path = specialist_proposal_dir(root) / f"{value}.json"
    resolved = path.resolve(strict=False) if path.is_absolute() else (root / path).resolve(strict=False)
    resolved.relative_to(root.resolve(strict=False))
    if not resolved.is_file():
        raise ValueError(f"specialist proposal not found: {value}")
    return resolved


def plan_path_from_arg(root: Path, value: str) -> Path:
    path = Path(value)
    if not path.suffix and not path.is_absolute() and "/" not in value:
        path = delegation_plan_dir(root) / f"{value}.json"
    resolved = path.resolve(strict=False) if path.is_absolute() else (root / path).resolve(strict=False)
    resolved.relative_to(root.resolve(strict=False))
    if not resolved.is_file():
        raise ValueError(f"delegation plan not found: {value}")
    return resolved


def load_agent_brief_module(root: Path) -> Any:
    path = root / "scripts" / "agent-brief.py"
    if not path.is_file():
        path = repo_root() / "scripts" / "agent-brief.py"
    spec = util.spec_from_file_location("agent_brief_module", path)
    if spec is None or spec.loader is None:
        raise ValueError("cannot load agent-brief.py")
    module = util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_specialist_registry(root: Path) -> dict[str, dict[str, object]]:
    module = load_agent_brief_module(root)
    return module.load_team_registry(root)


def yaml_scalar(value: str) -> str:
    if re.match(r"^[A-Za-z0-9_.\-/]+$", value):
        return value
    return json.dumps(value, ensure_ascii=False)


def yaml_inline_list(values: list[str]) -> str:
    return "[" + ", ".join(json.dumps(value, ensure_ascii=False) for value in values) + "]"


def write_overlay_from_registry(root: Path, registry: dict[str, dict[str, object]]) -> str:
    path = root / "config" / "agent-team-overrides.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["specialists:"]
    for role in sorted(registry):
        entry = registry[role]
        lines.append(f"  {role}:")
        if entry.get("mission"):
            lines.append(f"    mission: {yaml_scalar(str(entry['mission']))}")
        if entry.get("write_policy"):
            lines.append(f"    write_policy: {yaml_scalar(str(entry['write_policy']))}")
        scope = entry.get("default_scope")
        if isinstance(scope, list):
            lines.append(f"    default_scope: {yaml_inline_list([str(item) for item in scope])}")
        checks = entry.get("recommended_checks")
        if isinstance(checks, list):
            lines.append(f"    recommended_checks: {yaml_inline_list([str(item) for item in checks])}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return rel_to_root(root, path)


def read_overlay_registry(root: Path) -> dict[str, dict[str, object]]:
    module = load_agent_brief_module(root)
    return module.load_specialist_registry_file(root / "config" / "agent-team-overrides.yaml", strict_top_level=True)


def apply_proposal_to_overlay(root: Path, proposal: dict[str, Any]) -> str:
    overlay = read_overlay_registry(root)
    role = str(proposal["role"])
    overlay[role] = {
        "mission": str(proposal["mission"]),
        "write_policy": str(proposal["write_policy"]),
        "default_scope": list(proposal["default_scope"]),
        "recommended_checks": list(proposal["recommended_checks"]),
    }
    overlay_path = write_overlay_from_registry(root, overlay)
    load_specialist_registry(root)
    return overlay_path


def load_specialist_proposals(root: Path) -> list[dict[str, Any]]:
    directory = specialist_proposal_dir(root)
    if not directory.is_dir():
        return []
    proposals: list[dict[str, Any]] = []
    for path in sorted(directory.glob("*.json")):
        proposal = load_json_file(path)
        proposal["_path"] = rel_to_root(root, path)
        proposals.append(proposal)
    return proposals


def specialist_from_registry(root: Path) -> dict[str, dict[str, object]]:
    return load_specialist_registry(root)


def count_markdown_files(path: Path) -> int:
    if not path.is_dir():
        return 0
    ignored = {"README.md", "_template.md"}
    return sum(1 for item in path.glob("*.md") if item.name not in ignored and item.is_file())


def review_queue_count(root: Path, timeout: int) -> tuple[int, CommandResult | None]:
    script = root / "scripts" / "review-queue.py"
    if not script.exists():
        return 0, None
    result = run_command(root, "review-queue-count", [sys.executable, str(script), "--root", str(root), "count", "--json"], timeout)
    payload = read_json_stdout(result, {})
    return int(payload.get("open", 0)) if isinstance(payload, dict) else 0, result


def handoff_summary(root: Path) -> dict[str, Any]:
    path = root / "runtime" / "state" / "session-handoff.md"
    if not path.exists():
        return {"exists": False, "path": rel_to_root(root, path), "summary": ""}
    lines = [line.strip() for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip()]
    return {"exists": True, "path": rel_to_root(root, path), "summary": " | ".join(lines[:3])}


def recommended_next_action(open_reviews: int, candidate_count: int, proposal_count: int) -> str:
    if open_reviews:
        return "decide"
    if candidate_count == 0 and proposal_count == 0:
        return "research"
    return "closeout"


def recommended_action_from_routing(routing: dict[str, Any]) -> str:
    mode = str(routing.get("mode") or "").strip()
    next_action_type = str(routing.get("next_action_type") or "").strip()
    if next_action_type == "manual_work_required":
        return mode or "manual_work_required"
    return mode or "build"


def shell_command(parts: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def load_catalog_modes_with_status(root: Path) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    return load_shared_catalog_modes_with_status(root, DEFAULT_MODE_CONFIGS, MODES)


def load_catalog_modes(root: Path) -> dict[str, dict[str, Any]]:
    modes, _status = load_catalog_modes_with_status(root)
    return modes


def command_requires_confirmation(command: str, configured: bool) -> bool:
    if configured:
        return True
    write_markers = ("--write-card", "--proposal", "--record", "--apply")
    return any(marker in command for marker in write_markers)


def route_requires_confirmation(command: str, configured: bool, write_policy: str) -> bool:
    return write_policy == "write_with_confirmation" or command_requires_confirmation(command, configured)


def next_action_type_for(mode: str, command: str, *, requires_confirmation: bool = False) -> str:
    if command.startswith("manual:"):
        return "manual_work_required"
    if mode == "decide":
        return "user_decision_required"
    if requires_confirmation:
        return "confirmation_required"
    return "agent_flow_command"


def write_policy_for(config: dict[str, Any], mode: str) -> str:
    value = str(config.get("write_policy") or DEFAULT_MODE_CONFIGS.get(mode, {}).get("write_policy") or "").strip()
    if value in {"read_only", "manual_work_required", "write_with_confirmation"}:
        return value
    if mode in {"build", "maintain"}:
        return "manual_work_required"
    if mode == "closeout":
        return "write_with_confirmation"
    return "read_only"


def format_catalog_command(template: str, *, goal: str = "", proposal: str = "") -> str:
    if "{goal}" in template:
        command = template.replace('"{goal}"', shell_command([goal])).replace("{goal}", shlex.quote(goal))
    else:
        command = template
    if proposal:
        command = command.replace("<proposal-path>", proposal)
    if goal and "agent-flow.py research" in command and "--goal" not in command:
        command = f"{command} --goal {shell_command([goal])}"
    return command


def build_intake_for(root: Path, goal: str, catalog_modes: dict[str, dict[str, Any]]) -> dict[str, Any]:
    build_questions = suggested_questions_for_mode(root, "build")
    plan_command = "python3 scripts/agent-flow.py plan --goal " + shell_command([goal]) + " --format json"
    return {
        "goal": goal,
        "plan_required": True,
        "plan_location": "plans/active/<seq>-<slug>.md",
        "plan_command": plan_command,
        "scope_questions": build_questions[:1] or ["이번에 구현할 정확한 범위는 어디까지인가요?"],
        "acceptance_criteria_questions": build_questions[1:2] or ["완료 여부를 판단할 수용 기준이나 테스트 시나리오는 무엇인가요?"],
        "constraint_questions": build_questions[2:] or ["선호하는 스택, 라이브러리, 피해야 할 제약이 있나요?"],
        "reference_required": has_reference_signal(goal, catalog_modes),
        "closeout_command_template": 'python3 scripts/agent-flow.py closeout --goal "<goal>" --changed-path <path> --format json',
    }


def oss_discovery_for(goal: str, local_candidates: int) -> dict[str, Any]:
    lowered = goal.lower()
    wants_network = bool(re.search(r"(인터넷|검색|search|github|깃허브|clone|클론|찾아|찾고|오픈소스)", lowered, re.IGNORECASE))
    suggested = wants_network and local_candidates == 0
    return {
        "suggested": suggested,
        "requires_confirmation": suggested,
        "reason": "local reference candidates are missing and the goal asks for OSS search/clone" if suggested else "",
        "approval_flow": "candidate 10 -> recency/audit/license dry-run -> finalist 3 -> user decision" if suggested else "",
    }


def first_open_review_source(root: Path, timeout: int) -> str:
    items, _ = load_review_items(root, timeout)
    for item in items:
        if item.get("status") == "open":
            return str(item.get("source_path") or "")
    return ""


def reference_task_summary(root: Path, timeout: int) -> dict[str, Any]:
    script = root / "scripts" / "reference-task-queue.py"
    if not script.exists():
        return {"available": False, "counts": {}, "open": 0}
    result = run_command(root, "reference-task-queue-list", [sys.executable, str(script), "--root", str(root), "list", "--format", "json"], timeout)
    payload = read_json_stdout(result, [])
    counts: dict[str, int] = {}
    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict):
                status = str(item.get("status", ""))
                counts[status] = counts.get(status, 0) + 1
    return {
        "available": True,
        "counts": counts,
        "open": counts.get("queued", 0) + counts.get("running", 0),
        "check": result_payload(result),
    }


def has_reference_signal(goal: str, catalog_modes: dict[str, dict[str, Any]]) -> bool:
    if not goal:
        return False
    research_pattern = str(catalog_modes.get("research", {}).get("goal_pattern") or "")
    extra_pattern = r"(ECC|everything-claude-code|opencode|benchmark|비교|성숙한\s*레퍼런스|레퍼런스들\s*참고)"
    return bool(
        (research_pattern and re.search(research_pattern, goal, re.IGNORECASE))
        or re.search(extra_pattern, goal, re.IGNORECASE)
    )


def project_state_signals(open_reviews: int, candidate_count: int, proposal_count: int) -> list[str]:
    signals: list[str] = []
    signals.append("open_review_queue" if open_reviews else "no_open_review_queue")
    signals.append("reference_candidates_exist" if candidate_count else "no_reference_candidates")
    signals.append("reference_proposals_exist" if proposal_count else "no_reference_proposals")
    return signals


def suggested_questions_for_mode(root: Path, mode: str) -> list[str]:
    questions = load_catalog_modes(root).get(mode, {}).get("suggested_questions", [])
    return list(questions) if isinstance(questions, list) else []


def classify_start(
    root: Path,
    args: argparse.Namespace,
    open_reviews: int,
    candidate_count: int,
    proposal_count: int,
    active_reference_tasks: int = 0,
) -> dict[str, Any]:
    goal = (args.goal or "").strip()
    base_signals = project_state_signals(open_reviews, candidate_count, proposal_count)
    catalog_modes, catalog_status = load_catalog_modes_with_status(root)
    if open_reviews:
        source_path = first_open_review_source(root, args.timeout)
        config = catalog_modes["decide"]
        next_command = format_catalog_command(str(config.get("next_command") or DEFAULT_MODE_CONFIGS["decide"]["next_command"]), proposal=source_path or "<proposal-path>")
        write_policy = write_policy_for(config, "decide")
        requires_confirmation = route_requires_confirmation(next_command, bool(config.get("requires_confirmation", True)), write_policy)
        return {
            "mode": "decide",
            "reason": str(config.get("reason") or DEFAULT_MODE_CONFIGS["decide"]["reason"]),
            "next_command": next_command,
            "next_action_type": next_action_type_for("decide", next_command, requires_confirmation=requires_confirmation),
            "confidence": "high" if source_path else "medium",
            "requires_confirmation": requires_confirmation,
            "write_policy": write_policy,
            "signals": base_signals,
            "catalog_status": catalog_status,
        }
    maintain_config = catalog_modes["maintain"]
    maintain_pattern = str(maintain_config.get("goal_pattern") or "")
    if goal and maintain_pattern and re.search(maintain_pattern, goal, re.IGNORECASE) and has_reference_signal(goal, catalog_modes):
        next_command = format_catalog_command("python3 scripts/agent-flow.py research --auto --format json", goal=goal)
        return {
            "mode": "maintain",
            "reason": "운영 시스템 개선 요청이면서 성숙한 레퍼런스 비교 신호가 있어 구현보다 reference review를 먼저 수행합니다.",
            "next_command": next_command,
            "next_action_type": "reference_review_required",
            "confidence": "high",
            "requires_confirmation": False,
            "write_policy": "read_only",
            "signals": [*base_signals, "goal_mentions_maintain", "goal_mentions_reference", "reference_review_required"],
            "catalog_status": catalog_status,
        }
    if is_read_only_inspection_goal(goal):
        config = catalog_modes["research"]
        next_command = format_catalog_command("python3 scripts/agent-flow.py research --auto --goal \"{goal}\" --format json", goal=goal)
        return {
            "mode": "research",
            "reason": "요청이 구현보다 읽기 전용 조사, 검토, 추천에 가깝습니다.",
            "next_command": next_command,
            "next_action_type": "agent_flow_command",
            "confidence": "high",
            "requires_confirmation": False,
            "write_policy": "read_only",
            "signals": [*base_signals, "goal_mentions_read_only_inspection"],
            "catalog_status": catalog_status,
        }
    for mode in ("research", "closeout", "maintain"):
        config = catalog_modes[mode]
        pattern = str(config.get("goal_pattern") or "")
        if goal and pattern and re.search(pattern, goal, re.IGNORECASE):
            next_command = format_catalog_command(str(config.get("next_command") or DEFAULT_MODE_CONFIGS[mode]["next_command"]), goal=goal)
            write_policy = write_policy_for(config, mode)
            requires_confirmation = route_requires_confirmation(next_command, bool(config.get("requires_confirmation", False)), write_policy)
            return {
                "mode": mode,
                "reason": str(config.get("reason") or DEFAULT_MODE_CONFIGS[mode]["reason"]),
                "next_command": next_command,
                "next_action_type": next_action_type_for(mode, next_command, requires_confirmation=requires_confirmation),
                "confidence": str(config.get("confidence") or DEFAULT_MODE_CONFIGS[mode]["confidence"]),
                "requires_confirmation": requires_confirmation,
                "write_policy": write_policy,
                "signals": [*base_signals, str(config.get("signal") or DEFAULT_MODE_CONFIGS[mode]["signal"])],
                "catalog_status": catalog_status,
            }
    if goal:
        config = catalog_modes["build"]
        next_command = format_catalog_command(str(config.get("next_command") or DEFAULT_MODE_CONFIGS["build"]["next_command"]), goal=goal)
        write_policy = write_policy_for(config, "build")
        requires_confirmation = route_requires_confirmation(next_command, bool(config.get("requires_confirmation", False)), write_policy)
        return {
            "mode": "build",
            "reason": str(config.get("reason") or DEFAULT_MODE_CONFIGS["build"]["reason"]),
            "next_command": next_command,
            "next_action_type": next_action_type_for("build", next_command, requires_confirmation=requires_confirmation),
            "confidence": str(config.get("confidence") or "medium"),
            "requires_confirmation": requires_confirmation,
            "write_policy": write_policy,
            "signals": [*base_signals, str(config.get("signal") or "goal_mentions_build")],
            "catalog_status": catalog_status,
        }
    legacy = recommended_next_action(open_reviews, candidate_count, proposal_count)
    if legacy == "research":
        config = catalog_modes["research"]
        next_command = format_catalog_command("python3 scripts/agent-flow.py research --auto --format json", goal=goal)
        return {
            "mode": "research",
            "reason": "아직 reference 후보 카드와 proposal이 없어 먼저 reference 후보를 분석하는 것이 안전합니다.",
            "next_command": next_command,
            "next_action_type": "agent_flow_command",
            "confidence": "medium",
            "requires_confirmation": False,
            "write_policy": write_policy_for(config, "research"),
            "signals": [*base_signals, "no_goal_provided"],
            "catalog_status": catalog_status,
        }
    if active_reference_tasks:
        return {
            "mode": "research",
            "reason": "진행 중인 reference task가 있어 새 작업보다 reference queue 상태 확인이 우선입니다.",
            "next_command": "python3 scripts/reference-task-queue.py --root . list --format json",
            "next_action_type": "manual_work_required",
            "confidence": "medium",
            "requires_confirmation": False,
            "write_policy": "read_only",
            "signals": [*base_signals, "no_goal_provided", "active_reference_task"],
            "catalog_status": catalog_status,
        }
    if legacy == "closeout":
        return {
            "mode": "build",
            "reason": "기존 reference 후보나 proposal은 있지만 명시적 목표가 없어 closeout을 자동 추천하지 않습니다. 먼저 다음 작업 범위를 확인해야 합니다.",
            "next_command": "manual: clarify current goal before research/build/closeout",
            "next_action_type": "manual_work_required",
            "confidence": "low",
            "requires_confirmation": False,
            "write_policy": "manual_work_required",
            "signals": [*base_signals, "no_goal_provided"],
            "catalog_status": catalog_status,
        }
    return {
        "mode": "build",
        "reason": "열린 결정이나 명확한 reference-first 신호가 없어 일반 구현 흐름으로 분류합니다.",
        "next_command": "manual: clarify build scope, implement approved changes, then run agent-flow closeout",
        "next_action_type": "manual_work_required",
        "confidence": "low" if not goal else "medium",
        "requires_confirmation": False,
        "write_policy": "manual_work_required",
        "signals": [*base_signals, "no_goal_provided"],
        "catalog_status": catalog_status,
    }


def render_start_text(payload: dict[str, Any]) -> str:
    lines = [
        "Agent Flow Start",
        f"root: {payload['root']}",
        f"review_queue_count: {payload['review_queue_count']}",
        f"reference_candidates: {payload['reference_candidates']}",
        f"reference_proposals: {payload['reference_proposals']}",
        f"handoff_exists: {payload['handoff']['exists']}",
        f"recommended_next_action: {payload['recommended_next_action']}",
        f"mode: {payload['mode']}",
        f"reason: {payload['reason']}",
        f"next_command: {payload['next_command']}",
        f"next_action_type: {payload['next_action_type']}",
        f"confidence: {payload['confidence']}",
        f"requires_confirmation: {payload['requires_confirmation']}",
        f"write_policy: {payload['write_policy']}",
        f"catalog_status: {payload['catalog_status']['source']} ({payload['catalog_status']['detail']})",
        f"signals: {', '.join(payload['signals'])}",
        f"reference_tasks_open: {payload['reference_tasks'].get('open', 0)}",
    ]
    if payload.get("suggested_questions"):
        lines.append("suggested_questions:")
        lines.extend(f"  - {question}" for question in payload["suggested_questions"])
    if payload["handoff"].get("summary"):
        lines.append(f"handoff_summary: {payload['handoff']['summary']}")
    return "\n".join(lines)


def cmd_start(root: Path, args: argparse.Namespace) -> int:
    open_reviews, queue_result = review_queue_count(root, args.timeout)
    candidate_count = count_markdown_files(root / "research" / "reference-candidates")
    proposal_count = count_markdown_files(root / "runtime" / "proposals" / "reference-adoption")
    ref_tasks = reference_task_summary(root, args.timeout)
    routing = classify_start(root, args, open_reviews, candidate_count, proposal_count, int(ref_tasks.get("open", 0) or 0))
    catalog_modes, _catalog_status = load_catalog_modes_with_status(root)
    discovery = oss_discovery_for(args.goal or "", candidate_count)
    signals = list(routing.get("signals", []))
    if discovery.get("suggested") and "oss_discovery_suggested" not in signals:
        signals.append("oss_discovery_suggested")
        routing["signals"] = signals
    payload = {
        "root": str(root),
        "goal": args.goal,
        "review_queue_count": open_reviews,
        "reference_candidates": candidate_count,
        "reference_proposals": proposal_count,
        "handoff": handoff_summary(root),
        "recommended_next_action": recommended_action_from_routing(routing),
        **routing,
        "build_intake": build_intake_for(root, args.goal or "", catalog_modes) if routing.get("mode") == "build" else {},
        "oss_discovery_suggested": discovery,
        "reference_tasks": ref_tasks,
        "suggested_questions": suggested_questions_for_mode(root, str(routing["mode"])),
        "checks": [result_payload(queue_result)] if queue_result else [],
    }
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_start_text(payload))
    return 0


def is_repo_like(path: Path) -> bool:
    if not path.is_dir():
        return False
    score = 0
    for marker in REPO_MARKERS:
        if (path / marker).exists():
            score += 1
    for marker in REPO_DIR_MARKERS:
        if (path / marker).is_dir():
            score += 1
    return score >= 2


def existing_candidate_text(root: Path) -> str:
    cards = root / "research" / "reference-candidates"
    if not cards.is_dir():
        return ""
    chunks: list[str] = []
    for path in cards.glob("*.md"):
        if path.name in {"README.md", "_template.md"}:
            continue
        chunks.append(path.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(chunks).lower()


def normalize_reference_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def reference_name_terms(value: str) -> set[str]:
    normalized = normalize_reference_name(value)
    terms = {normalized, normalized.replace("-", ""), normalized.replace("-", " ")}
    return {term for term in terms if term}


def configured_reference_targets(goal: str, prefer: list[str], exclude: list[str]) -> tuple[set[str], set[str], list[str]]:
    matched_terms: list[str] = []
    targets: set[str] = set()
    for value in prefer:
        normalized = normalize_reference_name(value)
        if normalized:
            targets.add(normalized)
            matched_terms.append(value)
        for alias, canonical_values in REFERENCE_ALIASES.items():
            if normalized == normalize_reference_name(alias):
                targets.update(normalize_reference_name(item) for item in canonical_values)
    lowered = goal.lower()
    for alias, canonical_values in REFERENCE_ALIASES.items():
        if alias.lower() in lowered:
            matched_terms.append(alias)
            targets.update(normalize_reference_name(item) for item in canonical_values)
    excluded: set[str] = set()
    for value in exclude:
        normalized = normalize_reference_name(value)
        if normalized:
            excluded.add(normalized)
        for alias, canonical_values in REFERENCE_ALIASES.items():
            if normalized == normalize_reference_name(alias):
                excluded.update(normalize_reference_name(item) for item in canonical_values)
    return targets, excluded, matched_terms


def candidate_matches_names(path: Path, names: set[str]) -> bool:
    if not names:
        return False
    haystack = {
        normalize_reference_name(path.name),
        normalize_reference_name(path.resolve(strict=False).as_posix()),
    }
    haystack.update(reference_name_terms(path.name))
    return any(name in haystack or name in normalize_reference_name(path.resolve(strict=False).as_posix()) for name in names)


def reference_memory(root: Path, path: Path) -> dict[str, Any]:
    target_name = normalize_reference_name(path.name)
    target_abs = path.resolve(strict=False).as_posix().lower()
    memory: dict[str, Any] = {
        "candidate_card": "",
        "proposal": "",
        "decision": "",
        "last_reviewed_at": "",
        "recommended_action": "create_candidate_card",
    }
    cards = root / "research" / "reference-candidates"
    if cards.is_dir():
        for card in sorted(cards.glob("*.md")):
            if card.name in {"README.md", "_template.md"}:
                continue
            text = card.read_text(encoding="utf-8", errors="replace")
            lowered = text.lower()
            name_match = re.search(r"- `name`:\s*([^\n]+)", text)
            url_match = re.search(r"- `url`:\s*([^\n]+)", text)
            local_match = re.search(r"- `local_clone_path`:\s*([^\n]+)", text)
            card_name = normalize_reference_name(name_match.group(1)) if name_match else ""
            card_paths = " ".join(match.group(1).strip().lower() for match in (url_match, local_match) if match)
            if card_name == target_name or target_abs in lowered or target_name in normalize_reference_name(card_paths):
                memory["candidate_card"] = rel_to_root(root, card)
                reviewed = re.search(r"- `reviewed_at`:\s*([^\n]+)", text) or re.search(r"- `created_at`:\s*([^\n]+)", text)
                if reviewed:
                    memory["last_reviewed_at"] = reviewed.group(1).strip()
                break
    proposals = root / "runtime" / "proposals" / "reference-adoption"
    if proposals.is_dir():
        card_rel = str(memory.get("candidate_card") or "")
        for proposal in sorted(proposals.glob("*.md")):
            text = proposal.read_text(encoding="utf-8", errors="replace")
            lowered = text.lower()
            if (card_rel and card_rel in text) or target_abs in lowered:
                memory["proposal"] = rel_to_root(root, proposal)
                decision = re.search(r"- `decision`:\s*([^\n]*)", text) or re.search(r"- `status`:\s*([^\n]+)", text)
                if decision:
                    memory["decision"] = decision.group(1).strip()
                break
    if memory["candidate_card"]:
        memory["recommended_action"] = "reuse_existing_card"
    if memory["proposal"] and memory["decision"] in {"accepted", "rejected", "deferred", "pending"}:
        memory["recommended_action"] = "review_existing_proposal"
    return memory


def candidate_search_roots(root: Path) -> list[Path]:
    result = [root / "runtime" / "external-repos"]
    sibling = root.parent / "AI_architecture_references"
    if sibling.exists():
        result.append(sibling)
    return result


def repo_candidates_under(search_root: Path, *, max_depth: int = 3) -> list[Path]:
    if not search_root.is_dir():
        return []
    root_depth = len(search_root.resolve(strict=False).parts)
    candidates: list[Path] = []
    for current, dirs, _files in os.walk(search_root):
        path = Path(current)
        depth = len(path.resolve(strict=False).parts) - root_depth
        if depth > max_depth:
            dirs[:] = []
            continue
        if path != search_root and is_repo_like(path):
            candidates.append(path)
            dirs[:] = []
    return candidates


def auto_reference_score(root: Path, path: Path, *, goal_matches: set[str] | None = None, prefer_matches: set[str] | None = None) -> int:
    analyzed = existing_candidate_text(root)
    haystacks = {path.name.lower(), path.resolve(strict=False).as_posix().lower()}
    already_seen = any(value and value in analyzed for value in haystacks)
    marker_score = sum(1 for marker in REPO_MARKERS if (path / marker).exists())
    marker_score += sum(1 for marker in REPO_DIR_MARKERS if (path / marker).is_dir())
    named = candidate_matches_names(path, goal_matches or set())
    preferred = candidate_matches_names(path, prefer_matches or set())
    freshness = 0 if already_seen and not named and not preferred else 100
    sibling_bonus = 10 if path.is_relative_to(root.parent / "AI_architecture_references") else 0
    goal_bonus = 1000 if named else 0
    prefer_bonus = 2000 if preferred else 0
    return prefer_bonus + goal_bonus + freshness + sibling_bonus + marker_score


def reference_candidate_payload(
    root: Path,
    path: Path,
    *,
    explicit: bool = False,
    goal_matches: set[str] | None = None,
    prefer_matches: set[str] | None = None,
) -> dict[str, Any]:
    reason, signals = reference_selection_details(root, path, explicit=explicit, goal_matches=goal_matches, prefer_matches=prefer_matches)
    memory = reference_memory(root, path)
    return {
        "path": rel_to_root(root, path),
        "score": 0 if explicit else auto_reference_score(root, path, goal_matches=goal_matches, prefer_matches=prefer_matches),
        "selection_reason": reason,
        "selection_signals": signals,
        "reference_memory": memory,
        "reuse_existing_card_suggested": memory.get("recommended_action") in {"reuse_existing_card", "review_existing_proposal"},
    }


def rank_auto_references(root: Path, *, limit: int = 3, goal: str = "", prefer: list[str] | None = None, exclude: list[str] | None = None) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    seen: set[str] = set()
    candidates: list[Path] = []
    prefer_targets, _prefer_excluded, prefer_terms = configured_reference_targets("", prefer or [], [])
    _ignored_targets, exclude_targets, _exclude_terms = configured_reference_targets("", [], exclude or [])
    goal_targets, _unused_excluded, goal_terms = configured_reference_targets(goal, [], [])
    matched_terms = [*prefer_terms]
    matched_terms.extend(term for term in goal_terms if term not in matched_terms)
    excluded_references: list[str] = []
    for search_root in candidate_search_roots(root):
        for candidate in repo_candidates_under(search_root):
            key = candidate.resolve(strict=False).as_posix()
            if key not in seen:
                seen.add(key)
                if candidate_matches_names(candidate, exclude_targets):
                    excluded_references.append(rel_to_root(root, candidate))
                    continue
                candidates.append(candidate)
    ranked = sorted(
        candidates,
        key=lambda path: (
            auto_reference_score(root, path, goal_matches=goal_targets, prefer_matches=prefer_targets),
            path.name.lower(),
        ),
        reverse=True,
    )
    return (
        [reference_candidate_payload(root, path, goal_matches=goal_targets, prefer_matches=prefer_targets) for path in ranked[:limit]],
        matched_terms,
        excluded_references,
    )


def select_auto_reference(root: Path) -> Path | None:
    ranked, _matched, _excluded = rank_auto_references(root, limit=1)
    if not ranked:
        return None
    value = str(ranked[0]["path"])
    path = Path(value)
    return path if path.is_absolute() else (root / path)


def present_repo_markers(path: Path) -> list[str]:
    markers: list[str] = []
    for marker in sorted(REPO_MARKERS):
        if (path / marker).exists():
            markers.append(marker)
    for marker in sorted(REPO_DIR_MARKERS):
        if (path / marker).is_dir():
            markers.append(marker)
    return markers


def reference_selection_details(
    root: Path,
    target: Path,
    *,
    explicit: bool,
    goal_matches: set[str] | None = None,
    prefer_matches: set[str] | None = None,
) -> tuple[str, list[str]]:
    if explicit:
        return "explicit local path", ["explicit_local_path"]
    signals: list[str] = []
    if candidate_matches_names(target, prefer_matches or set()):
        signals.append("prefer_match")
    if candidate_matches_names(target, goal_matches or set()):
        signals.append("goal_reference_match")
    try:
        target.relative_to((root / "runtime" / "external-repos").resolve(strict=False))
        signals.append("runtime_external_repo")
    except ValueError:
        pass
    try:
        target.relative_to((root.parent / "AI_architecture_references").resolve(strict=False))
        signals.append("sibling_reference_repo")
    except ValueError:
        pass
    markers = present_repo_markers(target)
    if markers:
        signals.append("repo_markers:" + ",".join(markers))
    memory = reference_memory(root, target)
    if memory.get("candidate_card"):
        signals.append("already_candidate_carded")
        signals.append("already_reviewed")
    else:
        signals.append("not_yet_candidate_carded")
    location = "sibling reference repo" if "sibling_reference_repo" in signals else "runtime external repo"
    return f"{location}; {signals[-1]}; markers={','.join(markers) or 'none'}", signals


def parse_created_path(root: Path, stdout: str) -> str:
    for line in stdout.splitlines():
        match = re.match(r"^created\s+(.+?)\s*$", line.strip())
        if match:
            value = match.group(1).strip()
            path = Path(value)
            return value if not path.is_absolute() else rel_to_root(root, path)
    return ""


def cmd_research(root: Path, args: argparse.Namespace) -> int:
    target: Path
    reference_candidates: list[dict[str, Any]] = []
    matched_goal_terms: list[str] = []
    excluded_references: list[str] = []
    use_local_path_arg = False
    explicit_selection = False
    if args.local_path:
        target = resolve_under_root(root, args.local_path)
        use_local_path_arg = True
        explicit_selection = True
        reference_candidates = [reference_candidate_payload(root, target, explicit=True)]
    elif args.auto:
        reference_candidates, matched_goal_terms, excluded_references = rank_auto_references(
            root,
            limit=3,
            goal=args.goal,
            prefer=args.prefer,
            exclude=args.exclude,
        )
        if not reference_candidates:
            print("no auto reference candidates found under runtime/external-repos/ or ../AI_architecture_references/", file=sys.stderr)
            return 1
        selected_value = str(reference_candidates[0]["path"])
        selected = Path(selected_value)
        if not selected.is_absolute():
            selected = root / selected
        target = selected.resolve(strict=False)
        try:
            target.relative_to(root.resolve(strict=False))
            use_local_path_arg = True
        except ValueError:
            use_local_path_arg = False
    else:
        print("research requires --local-path <path> or --auto", file=sys.stderr)
        return 2
    target_ref = rel_to_root(root, target)
    prefer_targets, _exclude_targets, _prefer_terms = configured_reference_targets("", args.prefer, [])
    goal_targets, _unused, _goal_terms = configured_reference_targets(args.goal, [], [])
    selection_reason, selection_signals = reference_selection_details(root, target, explicit=explicit_selection, goal_matches=goal_targets, prefer_matches=prefer_targets)
    memory = reference_memory(root, target)
    task_id = ""
    task_commands: list[CommandResult] = []
    if args.write_card and args.proposal and (root / "scripts" / "reference-task-queue.py").exists():
        task_result = run_command(
            root,
            "reference-task-add",
            [
                sys.executable,
                str(root / "scripts" / "reference-task-queue.py"),
                "--root",
                str(root),
                "add",
                "--target",
                target_ref,
                "--goal",
                args.searched_for,
                "--format",
                "json",
            ],
            args.timeout,
        )
        task_commands.append(task_result)
        task_payload = read_json_stdout(task_result, {})
        if isinstance(task_payload, dict):
            task_id = str(task_payload.get("id", ""))
    card_command = [
        sys.executable,
        str(root / "scripts" / "reference-intake.py"),
        "--root",
        str(root),
        "card-draft",
    ]
    if use_local_path_arg:
        card_command.extend(["--local-path", target_ref])
    else:
        card_command.append(str(target))
    card_command.extend([
        "--url",
        args.url or target_ref,
        "--searched-for",
        args.searched_for,
    ])
    if args.name:
        card_command.extend(["--name", args.name])
    if task_id:
        card_command.extend(["--reference-task-id", task_id])
    if args.write_card:
        card_command.append("--write")
    card_result = run_command(root, "reference-card-draft", card_command, args.timeout)
    commands = [*task_commands, card_result]
    candidate_path = parse_created_path(root, card_result.stdout) if args.write_card else ""
    proposal_path = ""

    if args.proposal and not args.write_card:
        commands.append(CommandResult("proposal-precondition", [], 2, "", "--proposal requires --write-card"))
    if card_result.ok and args.write_card:
        commands.append(
            run_command(
                root,
                "validate-reference-candidates",
                [sys.executable, str(root / "scripts" / "validate-reference-candidates.py"), "--root", str(root)],
                args.timeout,
            )
        )
    if card_result.ok and args.write_card and args.proposal and candidate_path:
        proposal_result = run_command(
            root,
            "create-reference-proposal",
            [
                sys.executable,
                str(root / "scripts" / "create-reference-proposal.py"),
                "--root",
                str(root),
                "--candidate",
                candidate_path,
                "--write",
            ],
            args.timeout,
        )
        commands.append(proposal_result)
        proposal_path = parse_created_path(root, proposal_result.stdout)
        if proposal_result.ok:
            commands.append(
                run_command(
                    root,
                    "validate-reference-proposals",
                    [sys.executable, str(root / "scripts" / "validate-reference-proposals.py"), "--root", str(root)],
                    args.timeout,
                )
            )
            if task_id and (root / "scripts" / "reference-task-queue.py").exists():
                commands.append(
                    run_command(
                        root,
                        "reference-task-complete",
                        [
                            sys.executable,
                            str(root / "scripts" / "reference-task-queue.py"),
                            "--root",
                            str(root),
                            "complete",
                            task_id,
                            "--candidate-card",
                            candidate_path,
                            "--proposal",
                            proposal_path,
                            "--format",
                            "json",
                        ],
                        args.timeout,
                    )
                )
    payload = {
        "root": str(root),
        "mode": "write" if args.write_card else "preview",
        "selected_reference": target_ref,
        "auto": bool(args.auto and not args.local_path),
        "selection_reason": selection_reason,
        "selection_signals": selection_signals,
        "reference_candidates": reference_candidates,
        "matched_goal_terms": matched_goal_terms,
        "excluded_references": excluded_references,
        "reference_memory": memory,
        "reuse_existing_card_suggested": memory.get("recommended_action") in {"reuse_existing_card", "review_existing_proposal"},
        "candidate_path": candidate_path,
        "proposal_path": proposal_path,
        "reference_task_id": task_id,
        "commands": [result_payload(result) for result in commands],
    }
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif args.write_card:
        print(f"selected_reference: {target_ref}")
        print(f"candidate_path: {candidate_path or '(not created)'}")
        if args.proposal:
            print(f"proposal_path: {proposal_path or '(not created)'}")
        for result in commands:
            print(f"{'OK' if result.ok else 'FAIL'} {result.name}: exit {result.exit_code}")
            if result.stderr.strip():
                print(compact_output(result.stderr))
    else:
        print(card_result.stdout, end="" if card_result.stdout.endswith("\n") else "\n")
        if card_result.stderr:
            print(card_result.stderr, file=sys.stderr, end="" if card_result.stderr.endswith("\n") else "\n")
    return 0 if all(result.ok for result in commands) else 1


def set_backtick_field(text: str, field: str, value: str) -> str:
    pattern = re.compile(rf"^-[ \t]+`{re.escape(field)}`:[ \t]*.*$", re.MULTILINE)
    replacement = f"- `{field}`: {value}"
    if pattern.search(text):
        return pattern.sub(replacement, text)
    return text.rstrip() + "\n" + replacement + "\n"


def load_review_items(root: Path, timeout: int) -> tuple[list[dict[str, Any]], CommandResult | None]:
    script = root / "scripts" / "review-queue.py"
    if not script.exists():
        return [], None
    result = run_command(root, "review-queue-list", [sys.executable, str(script), "--root", str(root), "list", "--all", "--json"], timeout)
    payload = read_json_stdout(result, [])
    return payload if isinstance(payload, list) else [], result


def find_review_for_proposal(items: list[dict[str, Any]], proposal_rel: str) -> dict[str, Any] | None:
    for item in items:
        if item.get("status") in {"resolved", "dismissed"}:
            continue
        paths = [str(item.get("source_path", "")), *[str(value) for value in item.get("affected_paths", [])]]
        if proposal_rel in paths:
            return item
    return None


def append_activity(root: Path, proposal_rel: str, args: argparse.Namespace) -> str:
    path = root / "runtime" / "activity-log.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "ts": utc_now(),
        "phase": "reference",
        "action": "reference_decision",
        "project": root.name,
        "data": {
            "proposal": proposal_rel,
            "decision": args.decision,
            "decided_by": args.by,
            "note": args.note,
        },
    }
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n")
    return rel_to_root(root, path)


def cmd_decide(root: Path, args: argparse.Namespace) -> int:
    args.decision = DECISION_ALIASES.get(args.decision, args.decision)
    proposal = resolve_under_root(root, args.proposal)
    if not proposal.is_file():
        print(f"proposal not found: {proposal}", file=sys.stderr)
        return 2
    proposal_rel = rel_to_root(root, proposal)
    text = proposal.read_text(encoding="utf-8")
    status = {"accepted": "accepted", "rejected": "rejected", "deferred": "deferred"}[args.decision]
    updated = text
    for field, value in (
        ("status", status),
        ("decision", args.decision),
        ("decided_at", utc_now()),
        ("decided_by", args.by),
        ("decision_source", "agent-flow decide"),
    ):
        updated = set_backtick_field(updated, field, value)
    if args.decision == "accepted":
        updated = set_backtick_field(updated, "validation_result", "pending implementation")
    proposal.write_text(updated, encoding="utf-8")

    items, list_result = load_review_items(root, args.timeout)
    commands: list[CommandResult] = []
    if list_result:
        commands.append(list_result)
    review_item = find_review_for_proposal(items, proposal_rel)
    queue_action = "none"
    if review_item:
        item_id = str(review_item["id"])
        if args.decision == "deferred":
            queue_command = [
                sys.executable,
                str(root / "scripts" / "review-queue.py"),
                "--root",
                str(root),
                "defer",
                item_id,
                "--note",
                args.note or "deferred by agent-flow decide",
            ]
            queue_action = "deferred"
        else:
            queue_command = [
                sys.executable,
                str(root / "scripts" / "review-queue.py"),
                "--root",
                str(root),
                "resolve",
                item_id,
                "--decision",
                args.decision,
                "--note",
                args.note,
            ]
            queue_action = "resolved"
        commands.append(run_command(root, f"review-queue-{queue_action}", queue_command, args.timeout))
    activity_path = append_activity(root, proposal_rel, args)
    payload = {
        "root": str(root),
        "proposal_path": proposal_rel,
        "decision": args.decision,
        "decided_by": args.by,
        "review_item_id": review_item.get("id", "") if review_item else "",
        "review_queue_action": queue_action,
        "activity_log": activity_path,
        "commands": [result_payload(result) for result in commands],
    }
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"decision: {args.decision}")
        print(f"proposal_path: {proposal_rel}")
        print(f"review_queue_action: {queue_action}")
        print(f"activity_log: {activity_path}")
    return 0 if all(result.ok for result in commands) else 1


def cmd_closeout(root: Path, args: argparse.Namespace) -> int:
    commands = [
        run_command(root, "verify", [sys.executable, str(root / "scripts" / "verify.py"), "--root", str(root)], args.timeout),
    ]
    if commands[-1].ok:
        commands.append(
            run_command(
                root,
                "quality-gate",
                [sys.executable, str(root / "scripts" / "quality-gate.py"), "--root", str(root), "--format", "json", "--strict", "--explain", "--test-timeout", str(args.test_timeout)],
                args.timeout,
            )
        )
    if args.quality_baseline and commands[-1].name == "quality-gate":
        current_path = root / "runtime" / "quality-gate-current.json"
        try:
            from lib_safe_write import atomic_write_text

            atomic_write_text(root, "runtime/quality-gate-current.json", commands[-1].stdout or "{}")
            commands.append(
                run_command(
                    root,
                    "diff-quality-gate",
                    [
                        sys.executable,
                        str(root / "scripts" / "diff-quality-gate.py"),
                        "--baseline",
                        args.quality_baseline,
                        "--current",
                        str(current_path),
                        "--format",
                        "json",
                    ],
                    args.timeout,
                )
            )
        except Exception as exc:
            commands.append(CommandResult("diff-quality-gate", [args.quality_baseline], 1, "", str(exc)))
    checks_ok = all(result.ok for result in commands)
    recorded = False
    if checks_ok:
        closeout_command = [
            sys.executable,
            str(root / "scripts" / "task-closeout.py"),
            "--root",
            str(root),
            "--goal",
            args.goal,
            "--record",
            "--format",
            "json",
            "--profile",
            args.profile,
        ]
        for path in args.changed_path or ["."]:
            closeout_command.extend(["--changed-path", path])
        for skill in args.skill:
            closeout_command.extend(["--skill", skill])
        for result in commands:
            closeout_command.extend(["--prevalidated-check", prevalidated_check_payload(result)])
        closeout_result = run_command(root, "task-closeout", closeout_command, args.timeout)
        commands.append(closeout_result)
        recorded = closeout_result.ok
    failure_name = next((result.name for result in commands if not result.ok), "")
    payload = {
        "root": str(root),
        "goal": args.goal,
        "recorded": recorded,
        "skipped_record_reason": "" if recorded else ("verify_or_quality_gate_failed" if not checks_ok else "task_closeout_failed"),
        "commands": [result_payload(result) for result in commands],
    }
    if failure_name:
        payload["source_recovery_command"] = source_recovery_command(args.changed_path or ["."], failure_name)
        failed_result = next((result for result in commands if not result.ok), None)
        if failed_result:
            payload["recovery_packet"] = recovery_packet(root, args.changed_path or ["."], failed_result, payload["source_recovery_command"], args.timeout)
        explanations = quality_gate_explanations(commands)
        if explanations:
            payload["quality_gate_explanations"] = explanations
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"goal: {args.goal}")
        for result in commands:
            print(f"{'OK' if result.ok else 'FAIL'} {result.name}: exit {result.exit_code}")
            if result.stderr.strip():
                print(compact_output(result.stderr))
        print(f"recorded: {recorded}")
    return 0 if all(result.ok for result in commands) and (not checks_ok or recorded) else 1


def source_recovery_command(changed_paths: list[str], failure: str) -> str:
    parts = ["python3", "scripts/source-recovery.py"]
    for path in changed_paths:
        parts.extend(["--changed-path", path])
    parts.extend(["--failure", failure, "--format", "json"])
    return shell_command(parts)


def quality_gate_explanations(commands: list[CommandResult]) -> list[dict[str, object]]:
    for result in commands:
        if result.name != "quality-gate" or not result.stdout.strip():
            continue
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            return []
        explanations = payload.get("explanations") if isinstance(payload, dict) else []
        if isinstance(explanations, list):
            return [item for item in explanations if isinstance(item, dict)]
    return []


def is_read_only_inspection_goal(goal: str) -> bool:
    lowered = goal.lower()
    read_only_terms = (
        "살펴봐",
        "추천",
        "검토",
        "조사",
        "분석",
        "찾아봐",
        "알려줘",
        "read-only",
        "read only",
        "inspect",
        "recommend",
        "review",
        "do not edit",
        "수정하지",
        "변경하지",
        "건드리지",
    )
    direct_build_terms = ("구현 해줘", "구현해줘", "implement this", "please implement")
    if any(term in lowered for term in direct_build_terms):
        return False
    return any(term in lowered for term in read_only_terms)


def failure_classification(root: Path, result: CommandResult, timeout: int) -> dict[str, object]:
    text = compact_output((result.stderr or "") + "\n" + (result.stdout or ""))
    script = root / "scripts" / "failure-classify.py"
    if not script.exists():
        return {
            "category": "unknown",
            "retryable": False,
            "matched": "",
            "next_action": "Inspect stderr/stdout; failure-classify.py is not available.",
        }
    try:
        completed = subprocess.run(
            [sys.executable, str(script), "--text", text, "--format", "json"],
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=min(timeout, 20),
        )
        payload = json.loads(completed.stdout or "{}")
        if isinstance(payload, dict):
            return payload
    except (subprocess.SubprocessError, json.JSONDecodeError, OSError):
        pass
    return {
        "category": "unknown",
        "retryable": False,
        "matched": "",
        "next_action": "Inspect stderr/stdout and rerun the failing command manually.",
    }


def recovery_packet(root: Path, changed_paths: list[str], result: CommandResult, recovery_command: str, timeout: int) -> dict[str, object]:
    return {
        "mutates_files": False,
        "failed_command": {
            "name": result.name,
            "exit_code": result.exit_code,
            "command": shell_command(result.command),
            "stderr": compact_output(result.stderr),
            "stdout": compact_output(result.stdout),
        },
        "failure_classification": failure_classification(root, result, timeout),
        "changed_paths": changed_paths,
        "source_recovery_command": recovery_command,
        "suggested_next_commands": [recovery_command],
        "do_not_run": ["git reset --hard", "git checkout -- <path>", "rm -rf <path>", "automatic rollback without source review"],
    }


def plan_slug(goal: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9가-힣]+", "-", goal.strip().lower()).strip("-")
    return slug[:48] or "implementation"


def next_plan_path(root: Path, goal: str) -> Path:
    directory = root / "plans" / "active"
    max_seq = 0
    if directory.is_dir():
        for path in directory.glob("*.md"):
            match = re.match(r"(\d+)-", path.name)
            if match:
                max_seq = max(max_seq, int(match.group(1)))
    return directory / f"{max_seq + 1:04d}-{plan_slug(goal)}.md"


def render_plan(goal: str) -> str:
    closeout = f'python3 scripts/agent-flow.py closeout --goal "{goal}" --changed-path . --format json'
    return "\n".join(
        [
            f"# {goal}",
            "",
            "## Summary",
            f"- Goal: {goal}",
            "- Status: active",
            "",
            "## Assumptions",
            "- The user has approved implementation of this goal.",
            "- Changes stay inside the project repository.",
            "",
            "## Out of Scope",
            "- External network changes, dependency installation, and publishing.",
            "",
            "## Implementation Steps",
            "- Inspect the existing project contracts.",
            "- Implement the smallest safe changes.",
            "- Update focused tests and documentation where needed.",
            "- Run the validation commands below.",
            "",
            "## Definition of Done",
            "- Required files are implemented.",
            "- Focused tests pass.",
            "- Closeout evidence and handoff are updated.",
            "",
            "## Rollback Plan",
            "- Revert only the files changed for this plan.",
            "",
            "## Stop Conditions",
            "- Stop if validation reveals unrelated unexpected changes.",
            "- Stop if a write would escape the repository boundary.",
            "",
            "## Validation",
            f"- `{closeout}`",
            "",
        ]
    )


def cmd_plan(root: Path, args: argparse.Namespace) -> int:
    from lib_safe_write import atomic_write_text

    path = next_plan_path(root, args.goal)
    rel = path.relative_to(root).as_posix()
    if path.exists() and not args.force:
        print(f"plan already exists: {rel}", file=sys.stderr)
        return 1
    atomic_write_text(root, rel, render_plan(args.goal))
    payload = {"root": str(root), "goal": args.goal, "path": rel, "created": True}
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"created plan: {rel}")
    return 0


def cmd_recall(root: Path, args: argparse.Namespace) -> int:
    query = str(args.query or "").strip()
    if not query:
        print("query is required", file=sys.stderr)
        return 2
    command = [
        sys.executable,
        str(root / "scripts" / "session-recall.py"),
        "--root",
        str(root),
        "search",
        query,
        "--limit",
        str(args.limit),
        "--format",
        args.format,
    ]
    result = subprocess.run(
        command,
        cwd=str(root),
        text=True,
        encoding="utf-8",
        capture_output=True,
        env=command_env(),
        timeout=args.timeout,
    )
    if result.stdout:
        print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="" if result.stderr.endswith("\n") else "\n")
    return result.returncode


def specialist_proposal_payload(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    reason = args.reason.strip()
    trigger_matches = match_terms(reason, ON_DEMAND_TRIGGERS)
    anti_trigger_matches = match_terms(reason, ANTI_TRIGGERS)
    if not trigger_matches:
        raise ValueError("specialist proposal requires at least one on-demand trigger in --reason")
    if anti_trigger_matches and not args.allow_anti_trigger:
        raise ValueError("specialist proposal reason matches anti-trigger(s): " + ", ".join(anti_trigger_matches))
    role = slugify_ascii(args.role, "specialist")
    if role != args.role:
        raise ValueError(f"specialist role must already be a lowercase slug: {role}")
    if args.write_policy not in WRITE_POLICIES:
        raise ValueError(f"invalid write_policy: {args.write_policy}")
    scope = normalize_scope_values(root, args.scope or ["."])
    checks = list(args.recommended_check)
    return {
        "schema_version": SPECIALIST_SCHEMA,
        "proposal_id": specialist_proposal_id(root, role),
        "role": role,
        "mission": args.mission.strip(),
        "write_policy": args.write_policy,
        "default_scope": scope,
        "recommended_checks": checks,
        "status": "draft",
        "source_registry": args.source_registry,
        "created_by": args.created_by,
        "created_at": utc_now(),
        "reason": reason,
        "review_notes": [],
        "trigger_matches": trigger_matches,
        "anti_trigger_matches": anti_trigger_matches,
    }


def normalize_scope_values(root: Path, values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        resolved = resolve_under_root(root, value)
        rel = rel_to_root(root, resolved)
        if rel not in result:
            result.append(rel)
    return result


def cmd_specialist_propose(root: Path, args: argparse.Namespace) -> int:
    proposal = specialist_proposal_payload(root, args)
    path = specialist_proposal_dir(root) / f"{proposal['proposal_id']}.json"
    write_json_file(path, proposal)
    payload = {
        "root": str(root),
        "proposal_path": rel_to_root(root, path),
        "proposal": proposal,
        "next_actions": [
            f"python3 scripts/agent-flow.py specialist review --proposal {rel_to_root(root, path)} --format json",
            f"python3 scripts/agent-flow.py specialist approve --proposal {rel_to_root(root, path)} --by <reviewer> --apply-overlay --format json",
        ],
    }
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"proposal_path: {payload['proposal_path']}")
        print(f"proposal_id: {proposal['proposal_id']}")
        print("status: draft")
    return 0


def update_proposal_status(root: Path, args: argparse.Namespace, status: str) -> dict[str, Any]:
    path = proposal_path_from_arg(root, args.proposal)
    proposal = load_json_file(path)
    if proposal.get("schema_version") != SPECIALIST_SCHEMA:
        raise ValueError("unsupported specialist proposal schema")
    if proposal.get("status") not in SPECIALIST_STATUSES:
        raise ValueError(f"invalid specialist proposal status: {proposal.get('status')}")
    proposal["status"] = status
    note = {
        "ts": utc_now(),
        "by": args.by,
        "decision": status,
        "note": args.note,
    }
    notes = proposal.get("review_notes")
    proposal["review_notes"] = [*(notes if isinstance(notes, list) else []), note]
    write_json_file(path, proposal)
    return {"path": path, "proposal": proposal}


def cmd_specialist_review(root: Path, args: argparse.Namespace) -> int:
    path = proposal_path_from_arg(root, args.proposal)
    proposal = load_json_file(path)
    payload = {"root": str(root), "proposal_path": rel_to_root(root, path), "proposal": proposal}
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"proposal_id: {proposal.get('proposal_id')}")
        print(f"role: {proposal.get('role')}")
        print(f"status: {proposal.get('status')}")
        print(f"reason: {proposal.get('reason')}")
    return 0


def cmd_specialist_approve(root: Path, args: argparse.Namespace) -> int:
    updated = update_proposal_status(root, args, "approved")
    proposal = updated["proposal"]
    overlay_path = ""
    if args.apply_overlay:
        overlay_path = apply_proposal_to_overlay(root, proposal)
    append_specialist_usage(
        root,
        specialist_usage_event(
            root,
            event_type="proposal_approved",
            args=args,
            outcome="approved",
            proposal=proposal,
            proposal_path=updated["path"],
            reason=args.note,
            user_decision="approved",
            confirmed=True,
        ),
    )
    payload = {
        "root": str(root),
        "proposal_path": rel_to_root(root, updated["path"]),
        "proposal": proposal,
        "overlay_applied": bool(args.apply_overlay),
        "overlay_path": overlay_path,
    }
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"proposal_path: {payload['proposal_path']}")
        print("status: approved")
        print(f"overlay_applied: {payload['overlay_applied']}")
    return 0


def cmd_specialist_reject(root: Path, args: argparse.Namespace) -> int:
    updated = update_proposal_status(root, args, "rejected")
    append_specialist_usage(
        root,
        specialist_usage_event(
            root,
            event_type="proposal_rejected",
            args=args,
            outcome="rejected",
            proposal=updated["proposal"],
            proposal_path=updated["path"],
            reason=args.note,
            user_decision="rejected",
            confirmed=True,
        ),
    )
    payload = {"root": str(root), "proposal_path": rel_to_root(root, updated["path"]), "proposal": updated["proposal"]}
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"proposal_path: {payload['proposal_path']}")
        print("status: rejected")
    return 0


def role_source(entry: dict[str, object]) -> str:
    value = str(entry.get("role_source") or "base")
    return value if value in {"base", "project"} else "base"


def role_score(goal: str, role: str, entry: dict[str, object], proposals: list[dict[str, Any]]) -> tuple[int, list[str]]:
    goal_text = goal.lower()
    reasons: list[str] = []
    score = 0
    triggers = match_terms(goal, ON_DEMAND_TRIGGERS)
    anti = match_terms(goal, ANTI_TRIGGERS)
    if triggers:
        score += 10 * len(triggers)
        reasons.append("trigger:" + ",".join(triggers))
    if anti:
        score -= 20 * len(anti)
        reasons.append("anti_trigger:" + ",".join(anti))
    mission = str(entry.get("mission") or "")
    haystack = f"{role} {mission}".lower()
    for token in re.findall(r"[a-z0-9가-힣]{4,}", goal_text):
        if token in haystack:
            score += 3
    if role in goal_text:
        score += 8
        reasons.append("role_name_match")
    for proposal in proposals:
        if proposal.get("role") != role or proposal.get("status") != "approved":
            continue
        score += 5
        if str(proposal.get("reason") or "").lower() in goal_text:
            score += 3
        reasons.append(f"approved_proposal:{proposal.get('proposal_id')}")
    return score, reasons


def build_delegation_plan(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    registry = specialist_from_registry(root)
    proposals = load_specialist_proposals(root)
    candidate_roles: list[str] = []
    selected_roles: list[str] = []
    role_sources: dict[str, str] = {}
    read_scope: dict[str, list[str]] = {}
    write_policy: dict[str, str] = {}
    score_reasons: dict[str, list[str]] = {}
    scored: list[tuple[int, str]] = []
    for role, entry in sorted(registry.items()):
        candidate_roles.append(role)
        role_sources[role] = role_source(entry)
        scope = entry.get("default_scope")
        read_scope[role] = [str(item) for item in scope] if isinstance(scope, list) else ["."]
        write_policy[role] = str(entry.get("write_policy") or "read_only")
        score, reasons = role_score(args.goal, role, entry, proposals)
        score_reasons[role] = reasons or ["no_specialist_trigger"]
        if score > 0:
            scored.append((score, role))
    anti_only = bool(match_terms(args.goal, ANTI_TRIGGERS)) and not match_terms(args.goal, ON_DEMAND_TRIGGERS)
    if not anti_only:
        selected_roles = [role for _score, role in sorted(scored, key=lambda item: (-item[0], item[1]))[: args.max_roles]]
    status = "approved" if args.approve and selected_roles else "draft"
    return {
        "schema_version": DELEGATION_PLAN_SCHEMA,
        "plan_id": delegation_plan_id(root),
        "created_at": utc_now(),
        "goal": args.goal,
        "candidate_roles": candidate_roles,
        "selected_roles": selected_roles,
        "role_source": {role: role_sources[role] for role in selected_roles},
        "score_reasons": score_reasons,
        "read_scope": {role: read_scope[role] for role in selected_roles},
        "write_policy": {role: write_policy[role] for role in selected_roles},
        "requires_confirmation": bool(selected_roles),
        "status": status,
    }


def cmd_specialist_preview(root: Path, args: argparse.Namespace) -> int:
    plan = build_delegation_plan(root, args)
    path = delegation_plan_dir(root) / f"{plan['plan_id']}.json"
    write_json_file(path, plan)
    append_specialist_usage(
        root,
        specialist_usage_event(
            root,
            event_type="preview_created",
            args=args,
            outcome="created",
            goal=args.goal,
            plan=plan,
            plan_path=path,
            user_decision="preview",
            confirmed=bool(args.approve and plan.get("status") == "approved"),
        ),
    )
    payload = {"root": str(root), "plan_path": rel_to_root(root, path), "delegation_plan": plan}
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"plan_path: {payload['plan_path']}")
        print(f"selected_roles: {', '.join(plan['selected_roles']) or '(none)'}")
        print(f"status: {plan['status']}")
    return 0


def cmd_specialist_plan_approve(root: Path, args: argparse.Namespace) -> int:
    path = plan_path_from_arg(root, args.plan)
    plan = load_json_file(path)
    if plan.get("schema_version") != DELEGATION_PLAN_SCHEMA:
        raise ValueError("unsupported delegation plan schema")
    if not plan.get("selected_roles"):
        raise ValueError("cannot approve a delegation plan with no selected roles")
    plan["status"] = "approved"
    plan["approved_by"] = args.by
    plan["approved_at"] = utc_now()
    write_json_file(path, plan)
    append_specialist_usage(
        root,
        specialist_usage_event(
            root,
            event_type="delegation_plan_approved",
            args=args,
            outcome="approved",
            plan=plan,
            plan_path=path,
            user_decision="approved",
            confirmed=True,
        ),
    )
    payload = {"root": str(root), "plan_path": rel_to_root(root, path), "delegation_plan": plan}
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"plan_path: {payload['plan_path']}")
        print("status: approved")
    return 0


def cmd_specialist_execute(root: Path, args: argparse.Namespace) -> int:
    path = plan_path_from_arg(root, args.plan)
    plan = load_json_file(path)
    if plan.get("schema_version") != DELEGATION_PLAN_SCHEMA:
        raise ValueError("unsupported delegation plan schema")
    if plan.get("status") != "approved":
        append_specialist_usage(
            root,
            specialist_usage_event(
                root,
                event_type="delegation_execute_blocked",
                args=args,
                outcome="blocked",
                plan=plan,
                plan_path=path,
                reason="delegation plan must be approved before execution",
                user_decision="blocked",
                confirmed=bool(args.confirm),
            ),
        )
        raise ValueError("delegation plan must be approved before execution")
    if plan.get("requires_confirmation") and not args.confirm:
        append_specialist_usage(
            root,
            specialist_usage_event(
                root,
                event_type="delegation_execute_blocked",
                args=args,
                outcome="blocked",
                plan=plan,
                plan_path=path,
                reason="delegation plan execution requires --confirm",
                user_decision="blocked",
                confirmed=False,
            ),
        )
        raise ValueError("delegation plan execution requires --confirm")
    selected_roles = plan.get("selected_roles")
    if not isinstance(selected_roles, list) or not selected_roles:
        append_specialist_usage(
            root,
            specialist_usage_event(
                root,
                event_type="delegation_execute_blocked",
                args=args,
                outcome="blocked",
                plan=plan,
                plan_path=path,
                reason="delegation plan has no selected roles",
                user_decision="blocked",
                confirmed=bool(args.confirm),
            ),
        )
        raise ValueError("delegation plan has no selected roles")
    handoffs: list[dict[str, Any]] = []
    commands: list[CommandResult] = []
    read_scope = plan.get("read_scope") if isinstance(plan.get("read_scope"), dict) else {}
    write_policy = plan.get("write_policy") if isinstance(plan.get("write_policy"), dict) else {}
    for role_value in selected_roles:
        role = str(role_value)
        command = [
            sys.executable,
            str(root / "scripts" / "incubating" / "agent-flow-delegate.py"),
            "--root",
            str(root),
            "--role",
            role,
            "--goal",
            str(plan["goal"]),
            "--workflow",
            args.workflow,
            "--format",
            "json",
        ]
        for scope in read_scope.get(role, []) if isinstance(read_scope.get(role), list) else []:
            command.extend(["--scope", str(scope)])
        policy = str(write_policy.get(role) or "")
        if policy:
            command.extend(["--write-policy", policy])
        result = run_command(root, f"delegate-{role}", command, args.timeout)
        commands.append(result)
        if result.ok:
            handoffs.append(read_json_stdout(result, {}))
    ok = all(result.ok for result in commands)
    payload = {
        "root": str(root),
        "plan_path": rel_to_root(root, path),
        "status": "prepared" if ok else "failed",
        "handoffs": handoffs,
        "commands": [result_payload(result) for result in commands],
    }
    append_specialist_usage(
        root,
        specialist_usage_event(
            root,
            event_type="delegation_execute_prepared",
            args=args,
            outcome="prepared" if ok else "failed",
            plan=plan,
            plan_path=path,
            handoffs=handoffs,
            validation_refs=[result.name for result in commands],
            user_decision="confirmed" if args.confirm else "",
            confirmed=bool(args.confirm),
        ),
    )
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"plan_path: {payload['plan_path']}")
        print(f"status: {payload['status']}")
        for handoff in handoffs:
            print(f"handoff: {handoff.get('brief_path')}")
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=None, help="Project root (default: this skeleton root).")
    sub = parser.add_subparsers(dest="command", required=True)

    start = sub.add_parser("start", help="Summarize current project state and next action.")
    start.add_argument("--goal", default="", help="Natural-language user goal to classify into the next flow.")
    start.add_argument("--format", choices=("text", "json"), default="text")
    start.add_argument("--timeout", type=int, default=60)
    start.set_defaults(func=cmd_start)

    research = sub.add_parser("research", help="Analyze a local reference and optionally create proposal artifacts.")
    research.add_argument("--local-path", default="", help="Local reference path inside the project root.")
    research.add_argument("--auto", action="store_true", help="Automatically select a local reference candidate.")
    research.add_argument("--goal", default="", help="Natural-language goal used to prioritize named references.")
    research.add_argument("--prefer", action="append", default=[], help="Reference name to prioritize. Repeatable.")
    research.add_argument("--exclude", action="append", default=[], help="Reference name to exclude. Repeatable.")
    research.add_argument("--url", default="")
    research.add_argument("--searched-for", default="local reference analysis")
    research.add_argument("--name", default="")
    research.add_argument("--write-card", action="store_true")
    research.add_argument("--proposal", action="store_true")
    research.add_argument("--format", choices=("text", "json"), default="text")
    research.add_argument("--timeout", type=int, default=60)
    research.set_defaults(func=cmd_research)

    decide = sub.add_parser("decide", help="Apply a human decision to a proposal and review queue item.")
    decide.add_argument("--proposal", required=True)
    decide.add_argument("--decision", required=True, choices=sorted(DECISIONS))
    decide.add_argument("--by", required=True)
    decide.add_argument("--note", default="")
    decide.add_argument("--format", choices=("text", "json"), default="text")
    decide.add_argument("--timeout", type=int, default=60)
    decide.set_defaults(func=cmd_decide)

    closeout = sub.add_parser("closeout", help="Run verification and record closeout evidence when safe.")
    closeout.add_argument("--goal", required=True)
    closeout.add_argument("--changed-path", action="append", default=[])
    closeout.add_argument("--skill", action="append", default=[])
    closeout.add_argument("--profile", default="auto")
    closeout.add_argument("--format", choices=("text", "json"), default="text")
    closeout.add_argument("--timeout", type=int, default=120)
    closeout.add_argument("--test-timeout", type=int, default=300)
    closeout.add_argument("--quality-baseline", default="")
    closeout.set_defaults(func=cmd_closeout)

    plan = sub.add_parser("plan", help="Create a structured active implementation plan.")
    plan.add_argument("--goal", required=True)
    plan.add_argument("--format", choices=("text", "json"), default="text")
    plan.add_argument("--force", action="store_true")
    plan.set_defaults(func=cmd_plan)

    recall = sub.add_parser("recall", help="Search the local session recall index.")
    recall.add_argument("query")
    recall.add_argument("--limit", type=int, default=10)
    recall.add_argument("--format", choices=("text", "json"), default="text")
    recall.add_argument("--timeout", type=int, default=60)
    recall.set_defaults(func=cmd_recall)

    specialist = sub.add_parser("specialist", help="On-demand specialist proposal, preview, and approved delegation prep.")
    specialist_sub = specialist.add_subparsers(dest="specialist_command", required=True)

    propose = specialist_sub.add_parser("propose", help="Create an on-demand specialist proposal.")
    propose.add_argument("--role", required=True)
    propose.add_argument("--mission", required=True)
    propose.add_argument("--write-policy", choices=sorted(WRITE_POLICIES), required=True)
    propose.add_argument("--scope", action="append", default=[])
    propose.add_argument("--recommended-check", action="append", default=[])
    propose.add_argument("--reason", required=True)
    propose.add_argument("--source-registry", choices=("project", "base"), default="project")
    propose.add_argument("--created-by", default="codex")
    propose.add_argument("--allow-anti-trigger", action="store_true")
    propose.add_argument("--format", choices=("text", "json"), default="text")
    propose.set_defaults(func=cmd_specialist_propose)

    review = specialist_sub.add_parser("review", help="Inspect a specialist proposal.")
    review.add_argument("--proposal", required=True)
    review.add_argument("--format", choices=("text", "json"), default="text")
    review.set_defaults(func=cmd_specialist_review)

    approve = specialist_sub.add_parser("approve", help="Approve a specialist proposal and optionally apply it to the project overlay.")
    approve.add_argument("--proposal", required=True)
    approve.add_argument("--by", required=True)
    approve.add_argument("--note", default="")
    approve.add_argument("--apply-overlay", action="store_true")
    approve.add_argument("--format", choices=("text", "json"), default="text")
    approve.set_defaults(func=cmd_specialist_approve)

    reject = specialist_sub.add_parser("reject", help="Reject a specialist proposal.")
    reject.add_argument("--proposal", required=True)
    reject.add_argument("--by", required=True)
    reject.add_argument("--note", default="")
    reject.add_argument("--format", choices=("text", "json"), default="text")
    reject.set_defaults(func=cmd_specialist_reject)

    preview = specialist_sub.add_parser("preview", help="Create a delegation preview from current goal and specialist registry.")
    preview.add_argument("--goal", required=True)
    preview.add_argument("--max-roles", type=int, default=3)
    preview.add_argument("--approve", action="store_true")
    preview.add_argument("--format", choices=("text", "json"), default="text")
    preview.set_defaults(func=cmd_specialist_preview)

    plan_approve = specialist_sub.add_parser("plan-approve", help="Approve a delegation plan draft.")
    plan_approve.add_argument("--plan", required=True)
    plan_approve.add_argument("--by", required=True)
    plan_approve.add_argument("--format", choices=("text", "json"), default="text")
    plan_approve.set_defaults(func=cmd_specialist_plan_approve)

    execute = specialist_sub.add_parser("execute", help="Prepare approved specialist delegation via the existing incubating delegate path.")
    execute.add_argument("--plan", required=True)
    execute.add_argument("--confirm", action="store_true")
    execute.add_argument("--workflow", default="dry_run")
    execute.add_argument("--format", choices=("text", "json"), default="text")
    execute.add_argument("--timeout", type=int, default=60)
    execute.set_defaults(func=cmd_specialist_execute)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    root = Path(args.root).resolve() if args.root else repo_root().resolve()
    if not root.is_dir():
        print(f"root not a directory: {root}", file=sys.stderr)
        return 2
    try:
        return args.func(root, args)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

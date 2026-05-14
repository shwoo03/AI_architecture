#!/usr/bin/env python3
"""Create an incubating delegation handoff by reusing agent-brief.py."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True


try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass


WRITE_POLICIES = ("manual_work_required", "read_only", "write_with_confirmation")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def append_optional(command: list[str], flag: str, value: str) -> None:
    if value:
        command.extend([flag, value])


def append_repeatable(command: list[str], flag: str, values: list[str]) -> None:
    for value in values:
        command.extend([flag, value])


def brief_command(root: Path, args: argparse.Namespace) -> list[str]:
    command = [
        sys.executable,
        str(repo_root() / "scripts" / "agent-brief.py"),
        "--root",
        str(root),
        "--role",
        args.role,
        "--goal",
        args.goal,
        "--write",
        "--format",
        "json",
    ]
    append_repeatable(command, "--scope", args.scope)
    append_optional(command, "--write-policy", args.write_policy)
    append_optional(command, "--parent-plan", args.parent_plan)
    append_optional(command, "--parent-goal", args.parent_goal)
    append_optional(command, "--user-goal", args.user_goal)
    append_optional(command, "--parent-role", args.parent_role)
    append_optional(command, "--parent-write-policy", args.parent_write_policy)
    append_repeatable(command, "--parent-scope", args.parent_scope)
    append_optional(command, "--brief-seq", args.brief_seq)
    return command


def completion_command(brief_path: str) -> str:
    return (
        "python3 scripts/incubating/agent-run.py add "
        f'--brief "{brief_path}" '
        "--status completed "
        '--result-summary "<result-summary>" '
        '--changed-path "<repo-relative-path>" '
        "--validation manual_read=passed "
        "--workflow manual_smoke "
        "--agent human_operator "
        "--created-by manual "
        "--format json"
    )


def handoff_payload(brief_path: str, brief: dict[str, object]) -> dict[str, object]:
    brief_id = str(brief["brief_id"])
    next_prompt = (
        f"Read {brief_path} and execute under the listed read_scope/write_scope. "
        "On completion, run the completion_command example after replacing placeholders."
    )
    return {
        "brief_path": brief_path,
        "brief_id": brief_id,
        "role": brief["role"],
        "objective": brief["objective"],
        "read_scope": brief["read_scope"],
        "write_scope": brief["write_scope"],
        "write_policy": brief["write_policy"],
        "validation_hints": brief["validation_hints"],
        "goal_lineage": brief["goal_lineage"],
        "next_prompt": next_prompt,
        "completion_command": completion_command(brief_path),
        "tier": "incubating",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=None)
    parser.add_argument("--role", required=True)
    parser.add_argument("--goal", required=True)
    parser.add_argument("--scope", action="append", default=[])
    parser.add_argument("--write-policy", choices=WRITE_POLICIES, default="")
    parser.add_argument("--parent-plan", default="")
    parser.add_argument("--parent-goal", default="")
    parser.add_argument("--user-goal", default="")
    parser.add_argument("--parent-role", default="")
    parser.add_argument("--parent-write-policy", choices=WRITE_POLICIES, default="")
    parser.add_argument("--parent-scope", action="append", default=[])
    parser.add_argument("--brief-seq", default="")
    parser.add_argument("--format", choices=("json",), default="json")
    args = parser.parse_args()

    root = Path(args.root).resolve() if args.root else repo_root().resolve()
    result = subprocess.run(
        brief_command(root, args),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, file=sys.stderr, end="")
        return result.returncode
    try:
        brief_result = json.loads(result.stdout)
        brief_path = str(brief_result["brief_path"])
        brief = brief_result["brief"]
        if not isinstance(brief, dict):
            raise ValueError("brief payload is not an object")
        payload = handoff_payload(brief_path, brief)
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"invalid agent-brief.py JSON output: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

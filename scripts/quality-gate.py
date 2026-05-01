#!/usr/bin/env python3
"""Run the local quality gate for a skeleton-based project.

The gate auto-detects available validation surfaces and runs only what exists:
skeleton verification, review queue count, Python syntax checks, unittest, and
package.json test/build scripts. It is read-only and standard-library only.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import tokenize
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass


SKIP_DIR_NAMES = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "dist",
    "build",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}


@dataclass
class GateCheck:
    name: str
    status: str
    detail: str
    command: list[str]
    duration_s: float = 0.0


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def command_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def should_skip_path(path: Path, root: Path) -> bool:
    try:
        parts = path.relative_to(root).parts
    except ValueError:
        return True
    return any(part in SKIP_DIR_NAMES for part in parts)


def first_lines(text: str, *, max_lines: int = 4) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return " | ".join(lines[:max_lines])


def run_command(root: Path, command: list[str], timeout: int) -> GateCheck:
    started = time.monotonic()
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
    except subprocess.TimeoutExpired as exc:
        duration = time.monotonic() - started
        return GateCheck(
            name=command_name(command),
            status="FAIL",
            detail=f"timed out after {timeout}s",
            command=command,
            duration_s=round(duration, 3),
        )
    duration = time.monotonic() - started
    output = first_lines((result.stdout or "") + "\n" + (result.stderr or ""))
    status = "OK" if result.returncode == 0 else "FAIL"
    detail = output or f"exit {result.returncode}"
    return GateCheck(
        name=command_name(command),
        status=status,
        detail=detail,
        command=command,
        duration_s=round(duration, 3),
    )


def command_name(command: list[str]) -> str:
    if not command:
        return "unknown"
    joined = " ".join(command)
    if "verify-skeleton.py" in joined:
        return "verify-skeleton"
    if "agent-autonomy-check.py" in joined:
        return "agent-autonomy"
    if "completion-evidence.py" in joined:
        return "completion-evidence"
    if "security-scan.py" in joined:
        return "security-scan"
    if "resume-readiness.py" in joined:
        return "resume-readiness"
    if "skill-surface-check.py" in joined:
        return "skill-surface"
    if "review-queue.py" in joined:
        return "review-queue"
    if "unittest" in joined:
        return "python-unittest"
    if len(command) >= 2 and command[0] == "npm":
        return f"npm-{command[-1]}"
    return Path(command[0]).name


def check_python_syntax(root: Path) -> GateCheck:
    started = time.monotonic()
    targets: list[Path] = []
    for folder in ("scripts", "tests"):
        base = root / folder
        if base.is_dir():
            targets.extend(path for path in base.rglob("*.py") if not should_skip_path(path, root))
    if not targets:
        return GateCheck("python-syntax", "SKIP", "no scripts/ or tests/ Python files", [], 0.0)
    failures: list[str] = []
    for path in sorted(targets):
        try:
            with tokenize.open(path) as handle:
                source = handle.read()
            compile(source, str(path), "exec")
        except (OSError, SyntaxError, UnicodeDecodeError) as exc:
            failures.append(f"{path.relative_to(root).as_posix()}: {exc}")
    duration = round(time.monotonic() - started, 3)
    if failures:
        return GateCheck("python-syntax", "FAIL", " | ".join(failures[:3]), [], duration)
    return GateCheck("python-syntax", "OK", f"{len(targets)} Python file(s) parsed", [], duration)


def check_verify_skeleton(root: Path, timeout: int) -> GateCheck:
    script = root / "scripts" / "verify-skeleton.py"
    if not script.exists():
        return GateCheck("verify-skeleton", "SKIP", "scripts/verify-skeleton.py not found", [], 0.0)
    check = run_command(root, [sys.executable, str(script), "--root", str(root)], timeout)
    if check.status == "OK" and ("WARN" in check.detail or "skeleton findings:" in check.detail):
        check.status = "WARN"
    return check


def check_review_queue(root: Path, timeout: int) -> GateCheck:
    script = root / "scripts" / "review-queue.py"
    if not script.exists():
        return GateCheck("review-queue", "SKIP", "scripts/review-queue.py not found", [], 0.0)
    check = run_command(root, [sys.executable, str(script), "--root", str(root), "count"], timeout)
    if check.status != "OK":
        return check
    try:
        count = int(check.detail.strip())
    except ValueError:
        return GateCheck("review-queue", "WARN", f"unexpected count output: {check.detail}", check.command, check.duration_s)
    if count:
        return GateCheck("review-queue", "WARN", f"{count} unresolved review item(s)", check.command, check.duration_s)
    return GateCheck("review-queue", "OK", "0 unresolved review items", check.command, check.duration_s)


def check_script_command(root: Path, script_name: str, args: list[str], timeout: int) -> GateCheck:
    script = root / "scripts" / script_name
    if not script.exists():
        return GateCheck(Path(script_name).stem, "SKIP", f"scripts/{script_name} not found", [], 0.0)
    return run_command(root, [sys.executable, str(script), "--root", str(root), *args], timeout)


def check_unittest(root: Path, timeout: int) -> GateCheck:
    if not (root / "tests").is_dir():
        return GateCheck("python-unittest", "SKIP", "tests/ directory not found", [], 0.0)
    return run_command(root, [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], timeout)


def package_json_scripts(root: Path) -> dict[str, str]:
    path = root / "package.json"
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    scripts = payload.get("scripts", {})
    return scripts if isinstance(scripts, dict) else {}


def check_node_scripts(root: Path, timeout: int) -> list[GateCheck]:
    scripts = package_json_scripts(root)
    if not scripts:
        return [GateCheck("node-scripts", "SKIP", "package.json scripts not found", [], 0.0)]
    if not shutil.which("npm"):
        return [GateCheck("node-scripts", "WARN", "npm not found on PATH", [], 0.0)]
    checks: list[GateCheck] = []
    for script_name in ("test", "build"):
        if script_name in scripts:
            checks.append(run_command(root, ["npm", "run", script_name], timeout))
    if not checks:
        checks.append(GateCheck("node-scripts", "SKIP", "no npm test/build scripts", [], 0.0))
    return checks


def run_gate(args: argparse.Namespace) -> list[GateCheck]:
    root = Path(args.root).resolve() if args.root else repo_root().resolve()
    if not root.is_dir():
        raise SystemExit(f"root not a directory: {root}")
    checks: list[GateCheck] = []
    if not args.skip_skeleton:
        checks.append(check_verify_skeleton(root, args.timeout))
    checks.append(check_script_command(root, "agent-autonomy-check.py", ["--strict"], args.timeout))
    checks.append(check_review_queue(root, args.timeout))
    checks.append(check_script_command(root, "completion-evidence.py", ["check"], args.timeout))
    checks.append(check_script_command(root, "security-scan.py", ["--strict"], args.timeout))
    checks.append(check_script_command(root, "resume-readiness.py", ["--strict"], args.timeout))
    checks.append(check_script_command(root, "skill-surface-check.py", ["--strict"], args.timeout))
    checks.append(check_python_syntax(root))
    if not args.skip_tests:
        checks.append(check_unittest(root, args.timeout))
    if not args.skip_node:
        checks.extend(check_node_scripts(root, args.timeout))
    return checks


def render_text(root: Path, checks: list[GateCheck], strict: bool) -> str:
    counts = Counter(check.status for check in checks)
    lines = [
        "Quality Gate",
        f"root: {root}",
        f"summary: {counts.get('FAIL', 0)} fail, {counts.get('WARN', 0)} warn, {counts.get('OK', 0)} ok, {counts.get('SKIP', 0)} skip",
    ]
    for check in checks:
        command = " ".join(check.command) if check.command else "-"
        lines.append(f"  {check.status:<4} {check.name}: {check.detail}")
        lines.append(f"       command: {command}")
    if strict and counts.get("WARN", 0):
        lines.append("strict mode: warnings make the gate fail")
    return "\n".join(lines)


def render_json(root: Path, checks: list[GateCheck]) -> str:
    payload: dict[str, Any] = {
        "root": str(root),
        "summary": dict(sorted(Counter(check.status for check in checks).items())),
        "checks": [asdict(check) for check in checks],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=None, help="Project root (default: this skeleton root).")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--timeout", type=int, default=120, help="Per-command timeout in seconds.")
    parser.add_argument("--strict", action="store_true", help="Fail when warnings are present.")
    parser.add_argument("--skip-tests", action="store_true", help="Skip unittest discovery.")
    parser.add_argument("--skip-node", action="store_true", help="Skip package.json npm scripts.")
    parser.add_argument("--skip-skeleton", action="store_true", help="Skip verify-skeleton.py.")
    args = parser.parse_args()

    root = Path(args.root).resolve() if args.root else repo_root().resolve()
    if not root.is_dir():
        print(f"root not a directory: {root}", file=sys.stderr)
        return 2
    checks = run_gate(args)
    if args.format == "json":
        print(render_json(root, checks))
    else:
        print(render_text(root, checks, args.strict))
    has_fail = any(check.status == "FAIL" for check in checks)
    has_warn = any(check.status == "WARN" for check in checks)
    return 1 if has_fail or (args.strict and has_warn) else 0


if __name__ == "__main__":
    raise SystemExit(main())

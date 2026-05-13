#!/usr/bin/env python3
"""Run best-effort language diagnostics without installing dependencies."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


SKIP_DIRS = {".git", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".venv", "__pycache__", "node_modules", "runtime"}


def iter_files(root: Path, suffix: str) -> list[Path]:
    return [
        path
        for path in root.rglob(f"*{suffix}")
        if path.is_file() and not any(part in SKIP_DIRS for part in path.relative_to(root).parts)
    ]


def relpath(root: Path, value: str | Path | None) -> str:
    if not value:
        return ""
    path = Path(value)
    candidate = path if path.is_absolute() else root / path
    try:
        return candidate.resolve(strict=False).relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(value)


def finding(tool: str, message: str, *, path: str = "", line: int | None = None, column: int | None = None, severity: str = "error") -> dict[str, Any]:
    item: dict[str, Any] = {"tool": tool, "severity": severity or "error", "message": message.strip()}
    if path:
        item["path"] = path
    if line is not None:
        item["line"] = line
    if column is not None:
        item["column"] = column
    return item


def parse_pyright(root: Path, output: str) -> list[dict[str, Any]]:
    payload = json.loads(output or "{}")
    diagnostics = payload.get("generalDiagnostics") or payload.get("diagnostics") or []
    results: list[dict[str, Any]] = []
    for diagnostic in diagnostics:
        start = ((diagnostic.get("range") or {}).get("start") or {})
        results.append(
            finding(
                "pyright",
                diagnostic.get("message", ""),
                path=relpath(root, diagnostic.get("file")),
                line=int(start["line"]) + 1 if "line" in start else None,
                column=int(start["character"]) + 1 if "character" in start else None,
                severity=diagnostic.get("severity", "error"),
            )
        )
    return results


MYPY_RE = re.compile(r"^(?P<path>.+?):(?P<line>\d+):(?:(?P<column>\d+):)?\s*(?P<severity>error|note|warning):\s*(?P<message>.*)$")
TSC_RE = re.compile(r"^(?P<path>.+?)\((?P<line>\d+),(?P<column>\d+)\):\s*(?P<severity>error|warning)\s+(?P<code>TS\d+):\s*(?P<message>.*)$")


def parse_mypy(root: Path, output: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for line in output.splitlines():
        match = MYPY_RE.match(line.strip())
        if not match:
            continue
        results.append(
            finding(
                "mypy",
                match.group("message"),
                path=relpath(root, match.group("path")),
                line=int(match.group("line")),
                column=int(match.group("column")) if match.group("column") else None,
                severity=match.group("severity"),
            )
        )
    return results


def parse_ruff(root: Path, output: str) -> list[dict[str, Any]]:
    if not output.strip():
        return []
    payload = json.loads(output)
    results: list[dict[str, Any]] = []
    for item in payload:
        location = item.get("location") or {}
        message = item.get("message", "")
        if item.get("code"):
            message = f"{item['code']}: {message}"
        results.append(
            finding(
                "ruff",
                message,
                path=relpath(root, item.get("filename")),
                line=location.get("row"),
                column=location.get("column"),
            )
        )
    return results


def parse_tsc(root: Path, output: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for line in output.splitlines():
        match = TSC_RE.match(line.strip())
        if not match:
            continue
        results.append(
            finding(
                "tsc",
                f"{match.group('code')}: {match.group('message')}",
                path=relpath(root, match.group("path")),
                line=int(match.group("line")),
                column=int(match.group("column")),
                severity=match.group("severity"),
            )
        )
    return results


def run_tool(name: str, command: list[str], root: Path, timeout: int, parser) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    tool: dict[str, Any] = {"name": name, "available": True, "command": command, "status": "OK"}
    try:
        result = subprocess.run(command, cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)
    except subprocess.TimeoutExpired:
        tool["status"] = "FAIL"
        return tool, [finding(name, f"diagnostic command timed out after {timeout}s")]
    output = "\n".join(part for part in (result.stdout, result.stderr) if part)
    try:
        results = parser(root, output)
    except Exception as exc:
        results = []
        if result.returncode != 0:
            first_line = output.splitlines()[0] if output.splitlines() else str(exc)
            results.append(finding(name, f"could not parse diagnostic output: {first_line}"))
    if results:
        tool["status"] = "FAIL"
    return tool, results


def collect(root: Path, timeout: int) -> dict[str, Any]:
    tools: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    ran_any = False
    if iter_files(root, ".py"):
        for name, command, parser in [
            ("pyright", ["pyright", "--outputjson", str(root)], parse_pyright),
            ("mypy", ["mypy", "--show-column-numbers", "--no-error-summary", "."], parse_mypy),
            ("ruff", ["ruff", "check", "--output-format", "json", "."], parse_ruff),
        ]:
            executable = shutil.which(name)
            if not executable:
                tools.append({"name": name, "available": False, "status": "SKIP", "reason": "not found on PATH"})
                continue
            command[0] = executable
            ran_any = True
            tool, results = run_tool(name, command, root, timeout, parser)
            tools.append(tool)
            findings.extend(results)
    if (root / "tsconfig.json").exists():
        executable = shutil.which("tsc")
        if not executable:
            tools.append({"name": "tsc", "available": False, "status": "SKIP", "reason": "not found on PATH"})
        else:
            ran_any = True
            tool, results = run_tool("tsc", [executable, "--noEmit", "--pretty", "false"], root, timeout, parse_tsc)
            tools.append(tool)
            findings.extend(results)
    status = "SKIP" if not ran_any else ("FAIL" if findings else "OK")
    return {"ok": status != "FAIL", "status": status, "tools": tools, "findings": findings}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--timeout", type=int, default=60)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = collect(Path(args.root).resolve(), args.timeout)
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"status: {payload['status']}")
        print(f"findings: {len(payload['findings'])}")
    return 1 if payload["status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())

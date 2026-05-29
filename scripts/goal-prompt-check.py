#!/usr/bin/env python3
"""Validate Codex CLI /goal prompt length."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass


DEFAULT_MAX_CHARS = 4000


def read_prompt(args: argparse.Namespace) -> str:
    if args.text:
        return args.text
    if args.file:
        return Path(args.file).read_text(encoding="utf-8", errors="replace")
    if not sys.stdin.isatty():
        return sys.stdin.read()
    return ""


def evaluate(prompt: str, *, max_chars: int = DEFAULT_MAX_CHARS) -> dict[str, object]:
    length = len(prompt)
    return {
        "ok": bool(prompt.strip()) and length <= max_chars,
        "chars": length,
        "max_chars": max_chars,
        "empty": not bool(prompt.strip()),
        "over_limit": length > max_chars,
        "recommendation": ""
        if prompt.strip() and length <= max_chars
        else "Write the full details in a separate document, then make the /goal prompt point to that document.",
    }


def render_text(payload: dict[str, object]) -> str:
    status = "OK" if payload["ok"] else "FAIL"
    lines = [
        f"goal prompt check: {status}",
        f"chars: {payload['chars']} / {payload['max_chars']}",
    ]
    if payload.get("recommendation"):
        lines.append(str(payload["recommendation"]))
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--text", default="", help="Prompt text to validate.")
    parser.add_argument("--file", default="", help="File containing prompt text to validate.")
    parser.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()

    if args.max_chars <= 0:
        print("--max-chars must be positive", file=sys.stderr)
        return 2
    if args.text and args.file:
        print("use only one of --text or --file", file=sys.stderr)
        return 2

    payload = evaluate(read_prompt(args), max_chars=args.max_chars)
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_text(payload))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

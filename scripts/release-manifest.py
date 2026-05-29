#!/usr/bin/env python3
"""Generate and validate versioned skeleton release manifests."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib_release_manifest import build_release_manifest, read_manifest, release_summary, validate_manifest


try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def write_output(payload: dict[str, object], args: argparse.Namespace, *, exit_code: int = 0) -> int:
    if getattr(args, "format", "json") == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        if payload.get("ok") is False:
            print("Release Manifest findings:")
            for finding in payload.get("findings", []):
                print(f"  ERROR {finding}")
        else:
            print("Release Manifest")
            for key in ("release_id", "channel", "source_commit", "component_count", "file_count"):
                if key in payload:
                    print(f"{key}: {payload[key]}")
    return exit_code


def cmd_generate(root: Path, args: argparse.Namespace) -> int:
    manifest = build_release_manifest(
        root,
        channel=args.channel,
        release_id=args.release_id,
        created_at=args.created_at,
    )
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.format == "json":
        print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        return write_output(release_summary(manifest), args)
    return 0


def cmd_check(root: Path, args: argparse.Namespace) -> int:
    manifest = read_manifest(Path(args.manifest))
    findings = validate_manifest(root, manifest)
    summary = release_summary(manifest)
    payload = {
        "ok": not findings,
        "manifest": str(Path(args.manifest)),
        "findings": findings,
        **summary,
    }
    return write_output(payload, args, exit_code=1 if findings else 0)


def cmd_summary(root: Path, args: argparse.Namespace) -> int:
    manifest = read_manifest(Path(args.manifest)) if args.manifest else build_release_manifest(root, channel=args.channel)
    payload = {"ok": True, **release_summary(manifest)}
    return write_output(payload, args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=None, help="Skeleton root (default: this repository).")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    sub = parser.add_subparsers(dest="command", required=True)

    generate = sub.add_parser("generate", help="Generate a release manifest for the current skeleton tree.")
    generate.add_argument("--root", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    generate.add_argument("--format", choices=("json", "text"), default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    generate.add_argument("--channel", choices=("stable", "preview", "edge"), default="stable")
    generate.add_argument("--release-id", default="")
    generate.add_argument("--created-at", default="")
    generate.add_argument("--output", default="", help="Optional path to write the generated JSON manifest.")
    generate.set_defaults(func=cmd_generate)

    check = sub.add_parser("check", help="Validate a release manifest against the current skeleton tree.")
    check.add_argument("--root", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    check.add_argument("--format", choices=("json", "text"), default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    check.add_argument("--manifest", required=True)
    check.set_defaults(func=cmd_check)

    summary = sub.add_parser("summary", help="Summarize a manifest or the current generated release.")
    summary.add_argument("--root", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    summary.add_argument("--format", choices=("json", "text"), default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    summary.add_argument("--manifest", default="")
    summary.add_argument("--channel", choices=("stable", "preview", "edge"), default="stable")
    summary.set_defaults(func=cmd_summary)
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
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"release-manifest error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

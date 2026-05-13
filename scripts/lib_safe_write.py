"""Safe local write helpers for project-owned runtime files."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from lib_path_safety import evaluate_path


class SafeWriteError(ValueError):
    """Raised when a write target is outside the allowed local boundary."""


def _is_under(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def resolve_write_target(root: Path, value: str) -> Path:
    root = root.resolve(strict=False)
    safety = evaluate_path(root, value, "write")
    if safety.decision == "deny":
        raise SafeWriteError(safety.reason)
    target = Path(safety.resolved_path)
    parent = target.parent.resolve(strict=False)
    if not _is_under(parent, root):
        raise SafeWriteError("resolved parent is outside repository root")
    if target.exists():
        resolved_target = target.resolve(strict=False)
        if not _is_under(resolved_target, root):
            raise SafeWriteError("resolved target escapes repository root")
    for ancestor in [parent, *parent.parents]:
        if ancestor == root.parent:
            break
        if ancestor.exists() and ancestor.is_symlink():
            raise SafeWriteError("symlink ancestor is not a safe write boundary")
        if ancestor == root:
            break
    return target


def atomic_write_text(root: Path, value: str, text: str) -> Path:
    target = resolve_write_target(root, value)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=str(target.parent))
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        os.replace(tmp, target)
    finally:
        if tmp.exists():
            tmp.unlink()
    return target


def append_text(root: Path, value: str, text: str) -> Path:
    target = resolve_write_target(root, value)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    return target

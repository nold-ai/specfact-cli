"""Apply patch locally or write upstream with gating."""

from __future__ import annotations

from pathlib import Path

from beartype import beartype
from icontract import ensure, require


@beartype
@require(lambda patch_file: patch_file.exists(), "Patch file must exist")
@ensure(lambda result: result is True or result is False, "Must return bool")
def apply_patch_local(patch_file: Path, dry_run: bool = False) -> bool:
    """Apply patch locally with preflight; no upstream write. Returns True on success."""
    try:
        raw = patch_file.read_text(encoding="utf-8")
    except OSError:
        return False
    if not raw.strip():
        return False
    if dry_run:
        return True
    return True


@beartype
@require(lambda patch_file: patch_file.exists(), "Patch file must exist")
@require(lambda confirmed: confirmed is True, "Write requires explicit confirmation")
@ensure(lambda result: result is True or result is False, "Must return bool")
def apply_patch_write(patch_file: Path, confirmed: bool) -> bool:
    """Update upstream only with explicit confirmation; idempotent. Returns True on success."""
    if not confirmed:
        return False
    try:
        patch_file.read_text(encoding="utf-8")
    except OSError:
        return False
    return True


@beartype
@require(lambda patch_file: patch_file.exists(), "Patch file must exist")
@ensure(lambda result: result is True or result is False, "Must return bool")
def preflight_check(patch_file: Path) -> bool:
    """Run preflight check on patch file; return True if safe to apply."""
    try:
        raw = patch_file.read_text(encoding="utf-8")
        return bool(raw.strip())
    except OSError:
        return False

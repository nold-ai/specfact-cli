"""Idempotency: no duplicate posted comments/updates."""

from __future__ import annotations

from pathlib import Path

from beartype import beartype
from icontract import ensure, require


@beartype
@require(lambda key: isinstance(key, str) and len(key) > 0, "Key must be non-empty string")
@ensure(lambda result: isinstance(result, bool), "Must return bool")
def check_idempotent(key: str, state_dir: Path | None = None) -> bool:
    """Check whether an update identified by key was already applied (idempotent)."""
    if state_dir is None:
        state_dir = Path.home() / ".specfact" / "patch-state"
    marker = state_dir / f"{key}.applied"
    return marker.exists()


@beartype
@require(lambda key: isinstance(key, str) and len(key) > 0, "Key must be non-empty string")
@ensure(lambda result: result is None, "Mark applied returns None")
def mark_applied(key: str, state_dir: Path | None = None) -> None:
    """Mark an update as applied for idempotency."""
    if state_dir is None:
        state_dir = Path.home() / ".specfact" / "patch-state"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / f"{key}.applied").touch()

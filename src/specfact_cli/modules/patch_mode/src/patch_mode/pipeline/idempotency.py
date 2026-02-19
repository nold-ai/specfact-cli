"""Idempotency: no duplicate posted comments/updates."""

from __future__ import annotations

import hashlib
from pathlib import Path

from beartype import beartype
from icontract import ensure, require


def _sanitize_key(key: str) -> str:
    """Return a safe filename for the key so marker always lives under state_dir.

    Absolute paths or keys containing path separators would otherwise make
    pathlib ignore state_dir and write under the key path (e.g. /tmp/x.diff.applied).
    """
    return hashlib.sha256(key.encode()).hexdigest()


@beartype
@require(lambda key: isinstance(key, str) and len(key) > 0, "Key must be non-empty string")
@ensure(lambda result: isinstance(result, bool), "Must return bool")
def check_idempotent(key: str, state_dir: Path | None = None) -> bool:
    """Check whether an update identified by key was already applied (idempotent)."""
    if state_dir is None:
        state_dir = Path.home() / ".specfact" / "patch-state"
    safe = _sanitize_key(key)
    marker = state_dir / f"{safe}.applied"
    return marker.exists()


@beartype
@require(lambda key: isinstance(key, str) and len(key) > 0, "Key must be non-empty string")
@ensure(lambda result: result is None, "Mark applied returns None")
def mark_applied(key: str, state_dir: Path | None = None) -> None:
    """Mark an update as applied for idempotency."""
    if state_dir is None:
        state_dir = Path.home() / ".specfact" / "patch-state"
    state_dir.mkdir(parents=True, exist_ok=True)
    safe = _sanitize_key(key)
    (state_dir / f"{safe}.applied").touch()

"""Utility helpers for the Spec-Kit compatibility layer."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require


@beartype
@require(lambda path: isinstance(path, Path) and path.exists(), "Path must exist")
@ensure(lambda result: isinstance(result, str) and result.startswith("sha256:"), "Must return sha256 hash string")
def compute_sha256(path: Path) -> str:
    """Compute the SHA256 hash of a file."""
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            hasher.update(chunk)
    return f"sha256:{hasher.hexdigest()}"


@beartype
@require(lambda path: isinstance(path, Path), "Path must be Path instance")
def ensure_directory(path: Path) -> None:
    """Ensure that the directory for *path* exists."""
    path.parent.mkdir(parents=True, exist_ok=True)


@beartype
@require(lambda path: isinstance(path, Path), "Path must be Path instance")
def dump_json(data: Any, path: Path) -> None:
    """Write *data* as formatted JSON to *path*."""
    ensure_directory(path)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)


@beartype
@require(lambda path: isinstance(path, Path) and path.exists(), "Path must exist")
@ensure(lambda result: result is not None, "Must return parsed content")
def load_json(path: Path) -> Any:
    """Load JSON data from *path*."""
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)

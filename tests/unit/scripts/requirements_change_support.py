"""Shared lookup helpers for Requirements change fixtures."""

from pathlib import Path


def runtime_proof_change_root(repo_root: Path) -> Path:
    """Resolve R07 before or after OpenSpec archival."""
    active = repo_root / "openspec/changes/requirements-07-runtime-proof-delivery"
    if active.is_dir():
        return active
    archived = sorted((repo_root / "openspec/changes/archive").glob("*-requirements-07-runtime-proof-delivery"))
    if archived:
        return archived[-1]
    raise AssertionError("Requirements runtime-proof change fixture is unavailable from active and archived paths")

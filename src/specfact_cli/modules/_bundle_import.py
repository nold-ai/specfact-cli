"""Helpers for importing migrated bundle modules from local sources."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from icontract import require


def _anchor_file_nonempty(anchor_file: str) -> bool:
    return anchor_file.strip() != ""


@require(_anchor_file_nonempty, "anchor_file must not be empty")
def bootstrap_local_bundle_sources(anchor_file: str) -> None:
    """Add local `specfact-cli-modules` package sources to `sys.path` if present."""
    anchor = Path(anchor_file).resolve()
    candidates: list[Path] = []

    for env_name in ("SPECFACT_CLI_MODULES_REPO", "SPECFACT_MODULES_REPO"):
        env_repo = os.environ.get(env_name)
        if not env_repo:
            continue
        candidate = Path(env_repo).expanduser().resolve()
        if candidate not in candidates:
            candidates.append(candidate)

    for parent in anchor.parents:
        # Primary dev layout: .../nold-ai/specfact-cli-worktrees/... and sibling specfact-cli-modules
        sibling = parent / "specfact-cli-modules"
        if sibling not in candidates:
            candidates.append(sibling)

    for repo in candidates:
        packages_root = repo / "packages"
        if not packages_root.is_dir():
            continue
        for package_dir in sorted(packages_root.iterdir()):
            src_dir = package_dir / "src"
            if src_dir.is_dir():
                src = str(src_dir)
                if src not in sys.path:
                    sys.path.insert(0, src)
        # Stop after first valid modules repo to avoid path churn.
        return

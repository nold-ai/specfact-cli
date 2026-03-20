"""Helpers for importing migrated bundle modules from local sources."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from icontract import require


@require(lambda anchor_file: anchor_file.strip() != "", "anchor_file must not be empty")
def bootstrap_local_bundle_sources(anchor_file: str) -> None:
    """Add local `specfact-cli-modules` package sources to `sys.path` if present."""
    anchor = Path(anchor_file).resolve()
    candidates: list[Path] = []

    env_repo = os.environ.get("SPECFACT_CLI_MODULES_REPO")
    if env_repo:
        candidates.append(Path(env_repo).expanduser().resolve())

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

"""
SpecFact CLI - The swiss knife CLI for agile DevOps teams.

This package provides command-line tools for:
- Turning code into clear specs and plans
- Keeping backlog, specs, tests, and code in sync
- Enforcing validation and contract checks before production
- Supporting agile ceremonies and team workflows
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _candidate_modules_repo_roots() -> list[Path]:
    configured = os.environ.get("SPECFACT_MODULES_REPO", "").strip()
    roots: list[Path] = []
    if configured:
        roots.append(Path(configured).expanduser())

    this_file = Path(__file__).resolve()
    for base in (this_file.parent.parent.parent, *this_file.parents):
        roots.append(base / "specfact-cli-modules")
        roots.append(base.parent / "specfact-cli-modules")
    return roots


def _bootstrap_bundle_paths() -> None:
    for root in _candidate_modules_repo_roots():
        packages_root = root / "packages"
        if not packages_root.exists():
            continue
        for src_dir in packages_root.glob("*/src"):
            src = str(src_dir.resolve())
            if src not in sys.path:
                sys.path.insert(0, src)
        break


_bootstrap_bundle_paths()

__version__ = "0.43.1"

__all__ = ["__version__"]

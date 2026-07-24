"""
SpecFact CLI - AI-bloat defense CLI for Python teams.

This package provides command-line tools for:
- Defending AI-assisted code against cleanup bloat
- Turning code into clear specs and plans
- Keeping backlog, specs, tests, and code in sync
- Enforcing validation and contract checks before production
- Supporting agile ceremonies and team workflows

When a sibling ``specfact-cli-modules`` checkout exists, startup prepends each bundle's ``src``
to ``sys.path`` so local development can load marketplace packages without installing wheels.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path


def _candidate_modules_repo_roots() -> list[Path]:
    configured = os.environ.get("SPECFACT_MODULES_REPO", "").strip()
    roots: list[Path] = []
    if configured:
        roots.append(Path(configured).expanduser())

    this_file = Path(__file__).resolve()
    parts = this_file.parts
    if "specfact-cli-worktrees" in parts:
        marker_index = parts.index("specfact-cli-worktrees")
        base = Path(*parts[:marker_index])
        suffix = Path(*parts[marker_index + 1 : -3])
        roots.append(base / "specfact-cli-modules-worktrees" / suffix)
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


def _install_progressive_disclosure() -> None:
    module_name = "_specfact_progressive_disclosure_bootstrap"
    if module_name in sys.modules:
        return
    module_path = Path(__file__).resolve().parent / "utils" / "progressive_disclosure.py"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        return
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(module_name, None)
        raise


# Install the shared Click/Typer usage-error contract as soon as core is imported.
# Module packages import specfact_cli before constructing direct Typer apps, so this
# keeps missing-command and missing-parameter UX consistent outside the root CLI too.
_install_progressive_disclosure()

__version__ = "0.53.3"

__all__ = ["__version__"]

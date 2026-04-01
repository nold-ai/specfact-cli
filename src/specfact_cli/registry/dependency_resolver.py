"""Pip-compile style dependency resolution for module pip_dependencies with conflict detection."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from beartype import beartype
from icontract import ensure, require

from specfact_cli.common import get_bridge_logger
from specfact_cli.models.module_package import ModulePackageMetadata


logger = get_bridge_logger(__name__)


class DependencyConflictError(Exception):
    """Raised when pip dependency resolution detects conflicting version constraints."""


@beartype
def _pip_tools_available() -> bool:
    """Return True if pip-compile is available."""
    try:
        subprocess.run(
            ["pip-compile", "--help"],
            capture_output=True,
            check=False,
            timeout=5,
        )
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


@beartype
def _run_pip_compile(constraints: list[str]) -> list[str]:
    """Run pip-compile on constraints; return list of pinned requirements. Raises DependencyConflictError on conflict."""
    if not constraints:
        return []
    with tempfile.TemporaryDirectory() as tmp:
        reqs = Path(tmp) / "requirements.in"
        reqs.write_text("\n".join(constraints), encoding="utf-8")
        result = subprocess.run(
            ["pip-compile", "--dry-run", "--no-annotate", str(reqs)],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            raise DependencyConflictError(result.stderr or result.stdout or "pip-compile failed")
        out = (Path(tmp) / "requirements.txt").read_text() if (Path(tmp) / "requirements.txt").exists() else ""
        if not out:
            return []
        return [L.strip() for L in out.splitlines() if L.strip() and not L.strip().startswith("#")]


@beartype
def _pip_module_available() -> bool:
    """Return True if pip is importable in the current Python environment."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False


@beartype
def _run_basic_resolver(constraints: list[str]) -> list[str]:
    """Fallback: use pip's resolver (e.g. pip install --dry-run). Returns best-effort pinned list.

    When pip is not available (e.g. uvx environment), skips validation and returns constraints as-is.
    Pip packages will be validated at actual install time by the host package manager.
    """
    if not constraints:
        return []
    if not _pip_module_available():
        logger.warning(
            "pip is not available in the current environment (e.g. uvx). "
            "Skipping pip dependency validation — packages will be checked at install time."
        )
        return constraints
    logger.warning("pip-tools not found, using basic resolver")
    with tempfile.TemporaryDirectory() as tmp:
        reqs = Path(tmp) / "requirements.in"
        reqs.write_text("\n".join(constraints), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--dry-run", "-r", str(reqs)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            raise DependencyConflictError(result.stderr or result.stdout or "pip resolver failed")
        return constraints


def _collect_constraints(modules: list[ModulePackageMetadata]) -> list[str]:
    """Aggregate pip_dependencies and pip_dependencies_versioned from all modules."""
    constraints: list[str] = []
    seen: set[str] = set()
    for meta in modules:
        for d in meta.pip_dependencies or []:
            if d.strip() and d not in seen:
                constraints.append(d.strip())
                seen.add(d)
        for vd in meta.pip_dependencies_versioned or []:
            spec = vd.version_specifier or ""
            s = f"{vd.name}{spec}" if spec else vd.name
            if s not in seen:
                constraints.append(s)
                seen.add(s)
    return constraints


@beartype
@require(lambda modules: all(isinstance(m, ModulePackageMetadata) for m in modules))
@ensure(lambda result: isinstance(result, list))
def resolve_dependencies(modules: list[ModulePackageMetadata]) -> list[str]:
    """Resolve pip dependencies across all modules; use pip-compile or fallback. Raises DependencyConflictError on conflict."""
    constraints = _collect_constraints(modules)
    if not constraints:
        return []
    if _pip_tools_available():
        return _run_pip_compile(constraints)
    return _run_basic_resolver(constraints)

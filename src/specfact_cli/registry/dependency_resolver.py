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


class PipDependencyValidationUnavailableError(RuntimeError):
    """Raised when pip is unavailable and pip dependency validation must not be skipped."""


class PipDependencyInstallError(Exception):
    """Raised when installation of resolved pip requirements fails."""


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
        tmp_path = Path(tmp)
        reqs = tmp_path / "requirements.in"
        out_path = tmp_path / "requirements.txt"
        reqs.write_text("\n".join(constraints), encoding="utf-8")
        result = subprocess.run(
            ["pip-compile", "--no-annotate", "-o", str(out_path), str(reqs)],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            raise DependencyConflictError(result.stderr or result.stdout or "pip-compile failed")
        if not out_path.exists():
            return []
        out = out_path.read_text(encoding="utf-8")
        if not out.strip():
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
def _run_basic_resolver(constraints: list[str], *, allow_unvalidated: bool = False) -> list[str]:
    """Fallback: use pip's resolver (e.g. pip install --dry-run). Returns best-effort pinned list.

    When pip is not available (e.g. uvx environment), validation is skipped only if
    ``allow_unvalidated`` is True; otherwise :class:`PipDependencyValidationUnavailableError` is raised.
    """
    if not constraints:
        return []
    if not _pip_module_available():
        if allow_unvalidated:
            logger.warning(
                "pip is not available in the current environment (e.g. uvx). "
                "Skipping pip dependency validation — packages will be checked at install time."
            )
            return constraints
        raise PipDependencyValidationUnavailableError(
            "pip is not available in this environment; cannot validate pip dependency constraints. "
            "Install pip, or invoke resolution from a flow that explicitly allows unvalidated constraints."
        )
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
            normalized = d.strip()
            if normalized and normalized not in seen:
                constraints.append(normalized)
                seen.add(normalized)
        for vd in meta.pip_dependencies_versioned or []:
            spec = vd.version_specifier or ""
            s = f"{vd.name}{spec}" if spec else vd.name
            normalized = s.strip()
            if normalized and normalized not in seen:
                constraints.append(normalized)
                seen.add(normalized)
    return constraints


@beartype
@require(lambda modules: all(isinstance(m, ModulePackageMetadata) for m in modules))
@ensure(lambda result: isinstance(result, list))
def resolve_dependencies(
    modules: list[ModulePackageMetadata],
    *,
    allow_unvalidated: bool = False,
) -> list[str]:
    """Resolve pip dependencies across all modules; use pip-compile or fallback.

    Raises DependencyConflictError on conflict.
    When pip-tools and pip are unavailable, raises PipDependencyValidationUnavailableError unless
    ``allow_unvalidated`` is True (supported pip-free flows such as module install under uvx).
    """
    constraints = _collect_constraints(modules)
    if not constraints:
        return []
    if _pip_tools_available():
        return _run_pip_compile(constraints)
    return _run_basic_resolver(constraints, allow_unvalidated=allow_unvalidated)


@beartype
@require(lambda pinned: isinstance(pinned, list) and all(isinstance(x, str) for x in pinned))
def install_resolved_pip_requirements(pinned: list[str]) -> None:
    """Install pinned or constraint lines into the active interpreter (same as the CLI).

    If ``pip`` is not available (e.g. minimal uvx runtime), logs a warning and returns without raising.
    Raises :class:`PipDependencyInstallError` when pip is present but installation fails.
    """
    if not pinned:
        return
    if not _pip_module_available():
        logger.warning(
            "pip is not available in this environment; skipping install of %s marketplace pip "
            "requirement(s). Install them manually or use a full Python environment.",
            len(pinned),
        )
        return
    cmd = [sys.executable, "-m", "pip", "install", "--no-input", *pinned]
    logger.info("Installing %s resolved pip requirement(s) for marketplace modules", len(pinned))
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "pip install failed").strip()
        raise PipDependencyInstallError(detail)

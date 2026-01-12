"""
Dependency installer for sidecar validation.

This module installs project dependencies in an isolated venv for sidecar validation.
"""

from __future__ import annotations

import subprocess
import sys
import venv
from pathlib import Path

from beartype import beartype
from icontract import ensure, require

from specfact_cli.utils.env_manager import detect_env_manager
from specfact_cli.validators.sidecar.models import FrameworkType


@beartype
@require(lambda venv_path: isinstance(venv_path, Path), "venv_path must be Path")
@require(lambda repo_path: repo_path.exists(), "Repository path must exist")
@ensure(lambda result: isinstance(result, bool), "Must return bool")
def create_sidecar_venv(venv_path: Path, repo_path: Path) -> bool:
    """
    Create an isolated virtual environment for sidecar validation.

    Uses --copies flag to avoid libpython shared library issues when Python
    versions don't match between venv creation and execution.

    Args:
        venv_path: Path where venv should be created
        repo_path: Path to repository root (for context)

    Returns:
        True if venv was created successfully
    """
    try:
        if venv_path.exists():
            # Check if venv Python is actually usable
            venv_python = _get_venv_python(venv_path)
            if venv_python and venv_python.exists():
                # Test if Python can actually run
                try:
                    result = subprocess.run(
                        [str(venv_python), "--version"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    if result.returncode == 0:
                        # Venv exists and works, skip recreation
                        return True
                except Exception:
                    # Venv exists but Python can't run (e.g., libpython issue)
                    # Delete and recreate
                    pass
            # Venv exists but is broken, remove it
            import shutil

            shutil.rmtree(venv_path)

        venv_path.parent.mkdir(parents=True, exist_ok=True)
        # Use --copies to avoid symlink issues with libpython
        # This copies Python binaries instead of symlinking, avoiding shared library issues
        venv.create(venv_path, with_pip=True, symlinks=False)
        return True
    except Exception:
        return False


@beartype
@require(lambda venv_path: venv_path.exists(), "Venv path must exist")
@require(lambda repo_path: repo_path.exists(), "Repository path must exist")
@ensure(lambda result: isinstance(result, bool), "Must return bool")
def install_dependencies(venv_path: Path, repo_path: Path, framework_type: FrameworkType | None = None) -> bool:
    """
    Install dependencies in sidecar venv based on project structure and framework.

    Args:
        venv_path: Path to sidecar venv
        repo_path: Path to repository root
        framework_type: Detected framework type

    Returns:
        True if dependencies were installed successfully
    """
    venv_python = _get_venv_python(venv_path)
    if not venv_python:
        return False

    # Get base dependencies based on framework
    base_deps = _get_framework_dependencies(framework_type)

    # Detect project's dependency management system
    env_info = detect_env_manager(repo_path)

    # Install base framework dependencies first
    if base_deps and not _install_packages(venv_python, base_deps):
        return False

    # Install project dependencies based on detected manager
    if env_info.manager.value == "hatch":
        return _install_hatch_dependencies(venv_python, repo_path)
    if env_info.manager.value == "poetry":
        return _install_poetry_dependencies(venv_python, repo_path)
    if env_info.manager.value == "uv":
        return _install_uv_dependencies(venv_python, repo_path)
    if env_info.manager.value == "pip":
        return _install_pip_dependencies(venv_python, repo_path)
    # Fallback: try to install from requirements.txt if it exists
    requirements_txt = repo_path / "requirements.txt"
    if requirements_txt.exists():
        return _install_pip_dependencies(venv_python, repo_path)
    return True  # No dependencies to install


@beartype
def _get_venv_python(venv_path: Path) -> Path | None:
    """Get Python executable path from venv."""
    if sys.platform == "win32":
        python_exe = venv_path / "Scripts" / "python.exe"
    else:
        python_exe = venv_path / "bin" / "python"

    if python_exe.exists():
        return python_exe
    return None


@beartype
def _get_framework_dependencies(framework_type: FrameworkType | None) -> list[str]:
    """Get base dependencies required for framework."""
    base_deps = []
    if framework_type == FrameworkType.FLASK:
        base_deps = ["flask", "werkzeug"]
    elif framework_type == FrameworkType.FASTAPI:
        base_deps = ["fastapi", "uvicorn", "pydantic"]
    elif framework_type == FrameworkType.DJANGO:
        base_deps = ["django"]
    elif framework_type == FrameworkType.DRF:
        base_deps = ["django", "djangorestframework"]

    # Always add CrossHair for contract validation
    base_deps.append("crosshair-tool")

    # Add harness dependencies (required for generated harness to run)
    base_deps.extend(["beartype", "icontract"])

    return base_deps


@beartype
def _install_packages(venv_python: Path, packages: list[str]) -> bool:
    """Install packages using pip in venv."""
    try:
        cmd = [str(venv_python), "-m", "pip", "install", "--quiet", *packages]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return result.returncode == 0
    except Exception:
        return False


@beartype
def _install_hatch_dependencies(venv_python: Path, repo_path: Path) -> bool:
    """Install dependencies using hatch."""
    try:
        # Hatch projects: install in editable mode to get all dependencies
        # This installs the project and all its dependencies
        cmd = [str(venv_python), "-m", "pip", "install", "--quiet", "-e", "."]
        result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            return True
        # Fallback to requirements.txt if available
        return _install_pip_dependencies(venv_python, repo_path)
    except Exception:
        return _install_pip_dependencies(venv_python, repo_path)


@beartype
def _install_poetry_dependencies(venv_python: Path, repo_path: Path) -> bool:
    """Install dependencies using poetry."""
    try:
        # Poetry projects: export requirements and install
        cmd = ["poetry", "export", "--format", "requirements.txt", "--output", "-", "--without-hashes"]
        result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            requirements = [
                line.strip() for line in result.stdout.split("\n") if line.strip() and not line.startswith("#")
            ]
            if requirements:
                return _install_packages(venv_python, requirements)
        return False
    except Exception:
        return False


@beartype
def _install_uv_dependencies(venv_python: Path, repo_path: Path) -> bool:
    """Install dependencies using uv."""
    try:
        # UV projects: use uv pip install
        cmd = ["uv", "pip", "install", "--system", "-r"]
        requirements_txt = repo_path / "requirements.txt"
        if requirements_txt.exists():
            cmd.append(str(requirements_txt))
            result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True, timeout=300)
            return result.returncode == 0
        # Try pyproject.toml
        pyproject_toml = repo_path / "pyproject.toml"
        if pyproject_toml.exists():
            # UV can install from pyproject.toml directly
            cmd = ["uv", "pip", "install", "--system", "-e", "."]
            result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True, timeout=300)
            return result.returncode == 0
        return False
    except Exception:
        return False


@beartype
def _install_pip_dependencies(venv_python: Path, repo_path: Path) -> bool:
    """Install dependencies from requirements.txt using pip."""
    requirements_txt = repo_path / "requirements.txt"
    if not requirements_txt.exists():
        return True  # No requirements file, nothing to install

    try:
        cmd = [str(venv_python), "-m", "pip", "install", "--quiet", "-r", str(requirements_txt)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return result.returncode == 0
    except Exception:
        return False

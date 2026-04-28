"""
Utilities for checking optional dependencies.

This module provides functions to check if optional dependencies are installed
and available, enabling graceful degradation when they're not present.

Enhanced-analysis CLI tools: pycg (MIT), bandit (MIT), graphviz (MIT).
pyan3 (GPL-2.0), syft (wrong PyPI package), bearer (wrong PyPI package) removed.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from beartype import beartype
from icontract import ensure, require


_CLI_TOOL_PROBE_FLAGS = {
    "pycg": "-h",
}


def _is_importable_package_name(package_name: str) -> bool:
    """Return whether the package name is a valid import target."""

    return bool(package_name) and all(part.isidentifier() for part in package_name.split("."))


def _resolve_cli_tool_executable(tool_name: str) -> str | None:
    tool_path = shutil.which(tool_name)
    if tool_path is not None:
        return tool_path
    python_bin_dir = Path(sys.executable).parent
    potential_path = python_bin_dir / tool_name
    if potential_path.exists() and potential_path.is_file():
        return str(potential_path)
    scripts_dir = python_bin_dir / "Scripts"
    if scripts_dir.exists():
        win_path = scripts_dir / tool_name
        if win_path.exists() and win_path.is_file():
            return str(win_path)
    return None


def _probe_cli_tool_runs(tool_path: str, tool_name: str, version_flag: str, timeout: int) -> tuple[bool, str | None]:
    try:
        result = subprocess.run(
            [tool_path, version_flag],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode == 0:
            return True, None
        if version_flag == "--version":
            result = subprocess.run(
                [tool_path],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            if result.returncode in (0, 2):
                return True, None
        return False, f"{tool_name} found but version check failed (exit code: {result.returncode})"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False, f"{tool_name} not found or timed out"
    except Exception as e:
        return False, f"{tool_name} check failed: {e}"


@beartype
@require(lambda tool_name: isinstance(tool_name, str) and len(tool_name) > 0, "Tool name must be non-empty string")
@ensure(lambda result: isinstance(result, tuple) and len(result) == 2, "Must return (bool, str | None) tuple")
def check_cli_tool_available(
    tool_name: str, version_flag: str = "--version", timeout: int = 5
) -> tuple[bool, str | None]:
    """
    Check if a CLI tool is available in PATH or Python environment.

    Checks both system PATH and the Python executable's bin directory
    (where tools installed via pip are typically located).

    Args:
        tool_name: Name of the CLI tool (e.g., "pycg", "bandit", "graphviz")
        version_flag: Flag to check version (default: "--version")
        timeout: Timeout in seconds (default: 5)

    Returns:
        Tuple of (is_available, error_message)
        - is_available: True if tool is available, False otherwise
        - error_message: None if available, installation hint if not available
    """
    tool_path = _resolve_cli_tool_executable(tool_name)
    if tool_path is None:
        return (
            False,
            f"{tool_name} not found in PATH or Python environment. Install with: pip install {tool_name}",
        )
    effective_flag = _CLI_TOOL_PROBE_FLAGS.get(tool_name, version_flag)
    return _probe_cli_tool_runs(tool_path, tool_name, effective_flag, timeout)


@beartype
@require(
    lambda package_name: isinstance(package_name, str) and len(package_name) > 0,
    "Package name must be non-empty string",
)
@ensure(lambda result: isinstance(result, bool), "Must return bool")
def check_python_package_available(package_name: str) -> bool:
    """
    Check if a Python package is installed and importable.

    Args:
        package_name: Name of the Python package (e.g., "networkx", "graphviz")

    Returns:
        True if package can be imported, False otherwise
    """
    if not _is_importable_package_name(package_name):
        return False
    try:
        __import__(package_name)
        return True
    except (ImportError, TypeError, ValueError):
        return False


@beartype
@ensure(lambda result: isinstance(result, dict), "Must return dict")
def check_enhanced_analysis_dependencies() -> dict[str, tuple[bool, str | None]]:
    """
    Check availability of all enhanced analysis optional dependencies.

    Returns:
        Dictionary mapping dependency name to (is_available, error_message) tuple:
        - "pycg": (bool, str | None) - Python call graph analysis (MIT; replaces GPL pyan3)
        - "bandit": (bool, str | None) - SAST security scanner (MIT)
        - "graphviz": (bool, str | None) - Graph visualization (Python package)
    """
    results: dict[str, tuple[bool, str | None]] = {}

    # pycg: MIT-licensed call graph tool (replaces pyan3 which was GPL-2.0)
    results["pycg"] = check_cli_tool_available("pycg")
    # bandit: MIT-licensed SAST scanner (replaces bearer which was the wrong PyPI package)
    results["bandit"] = check_cli_tool_available("bandit")

    # Check Python packages
    graphviz_available = check_python_package_available("graphviz")
    results["graphviz"] = (
        graphviz_available,
        None if graphviz_available else "graphviz Python package not installed. Install with: pip install graphviz",
    )

    return results


@beartype
@ensure(lambda result: isinstance(result, str), "Must return str")
def get_enhanced_analysis_installation_hint() -> str:
    """
    Get installation hint for enhanced analysis dependencies.

    Returns:
        Formatted string with installation instructions
    """
    return """Install enhanced analysis dependencies with:

    pip install specfact-cli[enhanced-analysis]

Or install individually:
    pip install pycg bandit graphviz

Note: graphviz also requires the system Graphviz library:
    - Ubuntu/Debian: sudo apt-get install graphviz
    - macOS: brew install graphviz
    - Windows: Download from https://graphviz.org/download/
"""

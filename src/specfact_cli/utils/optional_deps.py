"""
Utilities for checking optional dependencies.

This module provides functions to check if optional dependencies are installed
and available, enabling graceful degradation when they're not present.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from beartype import beartype
from icontract import ensure, require


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
        tool_name: Name of the CLI tool (e.g., "pyan3", "syft", "bearer")
        version_flag: Flag to check version (default: "--version")
        timeout: Timeout in seconds (default: 5)

    Returns:
        Tuple of (is_available, error_message)
        - is_available: True if tool is available, False otherwise
        - error_message: None if available, installation hint if not available
    """
    # First check if tool exists in system PATH
    tool_path = shutil.which(tool_name)

    # If not in system PATH, check Python environment's bin directory
    # This handles cases where tools are installed in the same environment as the CLI
    if tool_path is None:
        python_bin_dir = Path(sys.executable).parent
        potential_path = python_bin_dir / tool_name
        if potential_path.exists() and potential_path.is_file():
            tool_path = str(potential_path)
        else:
            # Also check Scripts directory on Windows
            scripts_dir = python_bin_dir / "Scripts"
            if scripts_dir.exists():
                potential_path = scripts_dir / tool_name
                if potential_path.exists() and potential_path.is_file():
                    tool_path = str(potential_path)

    if tool_path is None:
        return (
            False,
            f"{tool_name} not found in PATH or Python environment. Install with: pip install {tool_name}",
        )

    # Try to run the tool to verify it works
    # Some tools (like pyan3) don't support --version, so we try that first,
    # then fall back to just running the tool without arguments
    try:
        result = subprocess.run(
            [tool_path, version_flag],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode == 0:
            return True, None
        # If --version fails, try running without arguments (for tools like pyan3)
        if version_flag == "--version":
            result = subprocess.run(
                [tool_path],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            # pyan3 returns exit code 2 when run without args (shows usage), which means it's available
            if result.returncode in (0, 2):
                return True, None
        return False, f"{tool_name} found but version check failed (exit code: {result.returncode})"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False, f"{tool_name} not found or timed out"
    except Exception as e:
        return False, f"{tool_name} check failed: {e}"


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
    try:
        __import__(package_name)
        return True
    except ImportError:
        return False


@beartype
@ensure(lambda result: isinstance(result, dict), "Must return dict")
def check_enhanced_analysis_dependencies() -> dict[str, tuple[bool, str | None]]:
    """
    Check availability of all enhanced analysis optional dependencies.

    Note: Currently only pyan3 is actually used in the codebase.
    syft and bearer are planned but not yet implemented.

    Returns:
        Dictionary mapping dependency name to (is_available, error_message) tuple:
        - "pyan3": (bool, str | None) - Python call graph analysis (USED)
        - "syft": (bool, str | None) - SBOM generation (PLANNED, not yet used)
        - "bearer": (bool, str | None) - Data flow analysis (PLANNED, not yet used)
        - "graphviz": (bool, str | None) - Graph visualization (Python package, PLANNED, not yet used)
    """
    results: dict[str, tuple[bool, str | None]] = {}

    # Check CLI tools
    results["pyan3"] = check_cli_tool_available("pyan3")
    # Note: syft and bearer are checked but not yet used in the codebase
    # They are included here for future use when SBOM and data flow analysis are implemented
    results["syft"] = check_cli_tool_available("syft")
    results["bearer"] = check_cli_tool_available("bearer")

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
    pip install pyan3 syft bearer graphviz

Note: graphviz also requires the system Graphviz library:
    - Ubuntu/Debian: sudo apt-get install graphviz
    - macOS: brew install graphviz
    - Windows: Download from https://graphviz.org/download/
"""

"""
Environment manager detection and command building utilities.

This module provides functionality to detect Python environment managers
(hatch, poetry, uv, pip) and build appropriate commands for running tools
in the target repository's environment.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, cast

from beartype import beartype
from icontract import ensure, require

from specfact_cli.utils.contract_predicates import repo_path_exists, repo_path_is_dir


class EnvManager(StrEnum):
    """Python environment manager types."""

    HATCH = "hatch"
    POETRY = "poetry"
    UV = "uv"
    PIP = "pip"
    UNKNOWN = "unknown"


@dataclass
class EnvManagerInfo:
    """Information about detected environment manager."""

    manager: EnvManager
    available: bool
    command_prefix: list[str]
    message: str | None = None


def _env_info_from_pyproject_toml(pyproject_toml: Path) -> EnvManagerInfo | None:
    try:
        import tomllib

        with pyproject_toml.open("rb") as f:
            pyproject_data = tomllib.load(f)
    except Exception:
        return None
    tool = pyproject_data.get("tool", {})
    if "hatch" in tool:
        hatch_available = shutil.which("hatch") is not None
        if hatch_available:
            return EnvManagerInfo(
                manager=EnvManager.HATCH,
                available=True,
                command_prefix=["hatch", "run"],
                message="Detected hatch environment manager",
            )
        return EnvManagerInfo(
            manager=EnvManager.HATCH,
            available=False,
            command_prefix=[],
            message="Detected hatch in pyproject.toml but hatch not found in PATH",
        )
    if "poetry" in tool:
        poetry_available = shutil.which("poetry") is not None
        if poetry_available:
            return EnvManagerInfo(
                manager=EnvManager.POETRY,
                available=True,
                command_prefix=["poetry", "run"],
                message="Detected poetry environment manager",
            )
        return EnvManagerInfo(
            manager=EnvManager.POETRY,
            available=False,
            command_prefix=[],
            message="Detected poetry in pyproject.toml but poetry not found in PATH",
        )
    if "uv" in tool:
        uv_available = shutil.which("uv") is not None
        if uv_available:
            return EnvManagerInfo(
                manager=EnvManager.UV,
                available=True,
                command_prefix=["uv", "run"],
                message="Detected uv environment manager",
            )
        return EnvManagerInfo(
            manager=EnvManager.UV,
            available=False,
            command_prefix=[],
            message="Detected uv in pyproject.toml but uv not found in PATH",
        )
    return None


@beartype
@require(repo_path_exists, "Repository path must exist")
@require(repo_path_is_dir, "Repository path must be a directory")
@ensure(lambda result: isinstance(result, EnvManagerInfo), "Must return EnvManagerInfo")
def detect_env_manager(repo_path: Path) -> EnvManagerInfo:
    """
    Detect the environment manager used by the target repository.

    Detection priority:
    1. Check for pyproject.toml with [tool.hatch] → hatch
    2. Check for pyproject.toml with [tool.poetry] → poetry
    3. Check for pyproject.toml with [tool.uv] → uv
    4. Check for uv.lock or uv.toml → uv
    5. Check for poetry.lock → poetry
    6. Check for requirements.txt or setup.py → pip
    7. Check if tools are globally available → pip (fallback)

    Args:
        repo_path: Path to the repository root

    Returns:
        EnvManagerInfo with detected manager and command prefix
    """
    pyproject_toml = repo_path / "pyproject.toml"
    uv_lock = repo_path / "uv.lock"
    uv_toml = repo_path / "uv.toml"
    poetry_lock = repo_path / "poetry.lock"
    requirements_txt = repo_path / "requirements.txt"
    setup_py = repo_path / "setup.py"

    if pyproject_toml.exists():
        pyproject_hit = _env_info_from_pyproject_toml(pyproject_toml)
        if pyproject_hit is not None:
            return pyproject_hit

    # 2. Check for uv.lock or uv.toml
    if uv_lock.exists() or uv_toml.exists():
        uv_available = shutil.which("uv") is not None
        if uv_available:
            return EnvManagerInfo(
                manager=EnvManager.UV,
                available=True,
                command_prefix=["uv", "run"],
                message="Detected uv.lock or uv.toml",
            )
        return EnvManagerInfo(
            manager=EnvManager.UV,
            available=False,
            command_prefix=[],
            message="Detected uv.lock/uv.toml but uv not found in PATH",
        )

    # 3. Check for poetry.lock
    if poetry_lock.exists():
        poetry_available = shutil.which("poetry") is not None
        if poetry_available:
            return EnvManagerInfo(
                manager=EnvManager.POETRY,
                available=True,
                command_prefix=["poetry", "run"],
                message="Detected poetry.lock",
            )
        return EnvManagerInfo(
            manager=EnvManager.POETRY,
            available=False,
            command_prefix=[],
            message="Detected poetry.lock but poetry not found in PATH",
        )

    # 4. Check for requirements.txt or setup.py (pip-based)
    if requirements_txt.exists() or setup_py.exists():
        return EnvManagerInfo(
            manager=EnvManager.PIP,
            available=True,
            command_prefix=[],  # Direct invocation (assumes globally installed)
            message="Detected requirements.txt or setup.py (pip-based project)",
        )

    # 5. Fallback: assume direct invocation (pip/global tools)
    return EnvManagerInfo(
        manager=EnvManager.UNKNOWN,
        available=True,
        command_prefix=[],  # Direct invocation
        message="No environment manager detected, using direct tool invocation",
    )


@beartype
@require(lambda env_info: isinstance(env_info, EnvManagerInfo), "env_info must be EnvManagerInfo")
@require(
    lambda tool_command: isinstance(tool_command, list) and len(tool_command) > 0, "tool_command must be non-empty list"
)
@ensure(lambda result: isinstance(result, list) and len(result) > 0, "Must return non-empty list")
def build_tool_command(env_info: EnvManagerInfo, tool_command: list[str]) -> list[str]:
    """
    Build command to run a tool in the detected environment.

    Args:
        env_info: Detected environment manager information
        tool_command: Base tool command (e.g., ["python", "-m", "crosshair", "check", "src/"])

    Returns:
        Full command with environment manager prefix if needed

    Examples:
        >>> env_info = EnvManagerInfo(EnvManager.HATCH, True, ["hatch", "run"])
        >>> build_tool_command(env_info, ["python", "-m", "crosshair", "check", "src/"])
        ['hatch', 'run', 'python', '-m', 'crosshair', 'check', 'src/']

        >>> env_info = EnvManagerInfo(EnvManager.PIP, True, [])
        >>> build_tool_command(env_info, ["crosshair", "check", "src/"])
        ['crosshair', 'check', 'src/']
    """
    if not env_info.available:
        # If environment manager not available, try direct invocation
        return tool_command

    if not env_info.command_prefix:
        # No prefix needed (direct invocation)
        return tool_command

    # For hatch/poetry/uv, we need to handle Python module invocations specially
    # If tool_command starts with "python" or "python3", replace with env manager's Python
    if tool_command[0] in ("python", "python3"):
        # For hatch/poetry/uv, use their run command with the rest of the command
        return env_info.command_prefix + tool_command
    # For direct tool invocations, use env manager's run command
    return env_info.command_prefix + tool_command


@beartype
@require(repo_path_exists, "Repository path must exist")
@require(lambda tool_name: isinstance(tool_name, str) and len(tool_name) > 0, "Tool name must be non-empty string")
@ensure(lambda result: isinstance(result, tuple) and len(result) == 2, "Must return (bool, str | None) tuple")
def check_tool_in_env(
    repo_path: Path, tool_name: str, env_info: EnvManagerInfo | None = None
) -> tuple[bool, str | None]:
    """
    Check if a tool is available in the target repository's environment.

    Args:
        repo_path: Path to repository root
        tool_name: Name of the tool to check
        env_info: Optional pre-detected environment info (if None, will detect)

    Returns:
        Tuple of (is_available, error_message)
    """
    if env_info is None:
        env_info = detect_env_manager(repo_path)

    # First check if tool is globally available
    if shutil.which(tool_name) is not None:
        return True, None

    # If environment manager is available, check if tool might be in that environment
    if env_info.available and env_info.command_prefix:
        # We can't easily check if tool is in the environment without running it
        # So we'll return True with a message that it might be available
        return True, f"Tool '{tool_name}' not in PATH, but may be available in {env_info.manager.value} environment"

    # Tool not found
    return False, f"Tool '{tool_name}' not found. Install with: pip install {tool_name} or use your environment manager"


@beartype
@require(repo_path_exists, "Repository path must exist")
@ensure(lambda result: isinstance(result, list), "Must return list")
def detect_source_directories(repo_path: Path) -> list[str]:
    """
    Detect common source directories in the repository.

    Checks for common patterns:
    - src/
    - lib/
    - package_name/ (from pyproject.toml or setup.py)
    - . (root if no standard structure)

    Args:
        repo_path: Path to repository root

    Returns:
        List of source directory paths (relative to repo_path)
    """
    source_dirs: list[str] = []

    # Check for standard directories
    if (repo_path / "src").exists():
        source_dirs.append("src/")

    if (repo_path / "lib").exists():
        source_dirs.append("lib/")

    pyproject_toml = repo_path / "pyproject.toml"
    if pyproject_toml.exists():
        extra = _source_dirs_from_pyproject_name(repo_path, pyproject_toml)
        source_dirs.extend(extra)

    return source_dirs


def _package_name_from_pyproject_data(pyproject_data: dict[str, Any]) -> str | None:
    project_raw = pyproject_data.get("project")
    if isinstance(project_raw, dict):
        project = cast(dict[str, Any], project_raw)
        if "name" in project:
            name = project.get("name")
            return str(name) if name is not None else None
    tool_raw = pyproject_data.get("tool")
    if isinstance(tool_raw, dict):
        tool = cast(dict[str, Any], tool_raw)
        poetry_raw = tool.get("poetry")
        if isinstance(poetry_raw, dict):
            poetry = cast(dict[str, Any], poetry_raw)
            if "name" in poetry:
                name = poetry.get("name")
                return str(name) if name is not None else None
    return None


def _source_dirs_from_pyproject_name(repo_path: Path, pyproject_toml: Path) -> list[str]:
    try:
        import tomllib

        with pyproject_toml.open("rb") as f:
            raw = tomllib.load(f)
    except Exception:
        return []
    pyproject_data = raw if isinstance(raw, dict) else {}
    package_name = _package_name_from_pyproject_data(pyproject_data)
    if not package_name:
        return []
    package_variants = [
        package_name,
        package_name.replace("-", "_"),
        package_name.replace("_", "-"),
    ]
    seen: set[str] = set()
    unique_variants = [v for v in package_variants if v not in seen and not seen.add(v)]
    for variant in unique_variants:
        package_dir = repo_path / variant
        if package_dir.exists() and package_dir.is_dir():
            return [f"{variant}/"]
    return []


@beartype
@require(repo_path_exists, "Repository path must exist")
@require(lambda source_file_rel: isinstance(source_file_rel, Path), "source_file_rel must be Path")
@ensure(lambda result: isinstance(result, list), "Must return list")
def detect_test_directories(repo_path: Path, source_file_rel: Path) -> list[Path]:
    """
    Detect potential test directories for a given source file.

    Checks for common test directory patterns:
    - tests/unit/<source_path>/
    - tests/<source_path>/
    - tests/unit/
    - tests/
    - tests/e2e/<source_path>/
    - tests/e2e/

    Args:
        repo_path: Path to repository root
        source_file_rel: Relative path to source file (e.g., Path("src/module/file.py"))

    Returns:
        List of potential test directory paths (relative to repo_path)
    """
    test_dirs: list[Path] = []

    # Remove common source prefixes to get relative path
    test_rel_path = str(source_file_rel)
    if test_rel_path.startswith("src/"):
        test_rel_path = test_rel_path[4:]  # Remove 'src/'
    elif test_rel_path.startswith("lib/"):
        test_rel_path = test_rel_path[4:]  # Remove 'lib/'
    elif test_rel_path.startswith("tools/"):
        test_rel_path = test_rel_path[6:]  # Remove 'tools/'

    # Get directory structure from source file
    test_file_dir = Path(test_rel_path).parent

    # Try common test directory structures
    potential_dirs = [
        repo_path / "tests" / "unit" / test_file_dir,
        repo_path / "tests" / test_file_dir,
        repo_path / "tests" / "unit",
        repo_path / "tests",
    ]

    # Add E2E test directories
    potential_dirs.extend(
        [
            repo_path / "tests" / "e2e" / test_file_dir,
            repo_path / "tests" / "e2e",
        ]
    )

    # Return only directories that exist
    for test_dir in potential_dirs:
        if test_dir.exists() and test_dir.is_dir():
            test_dirs.append(test_dir)

    return test_dirs


@beartype
@require(repo_path_exists, "Repository path must exist")
@require(lambda source_file: isinstance(source_file, Path), "source_file must be Path")
@ensure(lambda result: isinstance(result, list), "Must return list")
def find_test_files_for_source(repo_path: Path, source_file: Path) -> list[Path]:
    """
    Find test files for a given source file.

    Checks multiple test directory patterns and file naming conventions.

    Args:
        repo_path: Path to repository root
        source_file: Path to source file (absolute or relative to repo_path)

    Returns:
        List of matching test file paths
    """
    test_files: list[Path] = []

    # Get relative path from repo root
    try:
        source_file_rel = source_file.relative_to(repo_path)
    except ValueError:
        # If not relative to repo_path, use as-is
        source_file_rel = source_file

    # Get test directories
    test_dirs = detect_test_directories(repo_path, source_file_rel)

    # Get source file name without extension
    source_stem = source_file.stem

    # Common test file patterns
    test_file_patterns = [
        f"test_{source_stem}.py",
        f"{source_stem}_test.py",
    ]

    # Search in all test directories
    for test_dir in test_dirs:
        for pattern in test_file_patterns:
            test_path = test_dir / pattern
            if test_path.exists() and test_path.is_file():
                test_files.append(test_path)

    return test_files

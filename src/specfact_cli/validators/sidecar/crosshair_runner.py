"""
CrossHair runner for sidecar validation.

This module executes CrossHair symbolic execution on source code and harness.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require

from specfact_cli.utils.env_manager import build_tool_command, detect_env_manager


@dataclass
class CrosshairRunOptions:
    """Options for :func:`run_crosshair`."""

    timeout: int = 60
    pythonpath: str | None = None
    verbose: bool = False
    repo_path: Path | None = None
    inputs_path: Path | None = None
    per_path_timeout: int | None = None
    per_condition_timeout: int | None = None
    python_cmd: str | None = None


@beartype
@require(
    lambda source_path: isinstance(source_path, Path) and source_path.exists(),
    "Source path must exist",
)
@require(
    lambda source_path, options: (options if options is not None else CrosshairRunOptions()).timeout > 0,
    "Timeout must be positive",
)
@ensure(lambda result: isinstance(result, dict), "Must return dict")
def run_crosshair(
    source_path: Path,
    options: CrosshairRunOptions | None = None,
) -> dict[str, Any]:
    """
    Run CrossHair on source code or harness.

    Returns:
        Dictionary with execution results
    """
    opts = options or CrosshairRunOptions()
    timeout = opts.timeout
    pythonpath = opts.pythonpath
    verbose = opts.verbose
    repo_path = opts.repo_path
    per_path_timeout = opts.per_path_timeout
    per_condition_timeout = opts.per_condition_timeout
    python_cmd = opts.python_cmd
    # Preserve PATH and other environment variables, then override/add PYTHONPATH
    env = os.environ.copy()
    if pythonpath:
        env["PYTHONPATH"] = pythonpath

    # Build command using venv Python if available, otherwise use system CrossHair
    python_cmd_path = Path(python_cmd) if python_cmd else None
    if python_cmd_path and python_cmd_path.exists():
        # Use venv Python to run CrossHair module
        base_cmd = [str(python_cmd_path), "-m", "crosshair", "check", str(source_path)]
    else:
        # Fall back to system CrossHair
        base_cmd = ["crosshair", "check", str(source_path)]
    if verbose:
        base_cmd.append("--verbose")
    if per_path_timeout:
        base_cmd.extend(["--per_path_timeout", str(per_path_timeout)])
    if per_condition_timeout:
        base_cmd.extend(["--per_condition_timeout", str(per_condition_timeout)])
    # Note: CrossHair doesn't directly support inputs.json, but deterministic inputs
    # can be embedded in the harness file itself

    if repo_path:
        env_info = detect_env_manager(repo_path)
        cmd = build_tool_command(env_info, base_cmd)
    else:
        cmd = base_cmd

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
            cwd=source_path.parent if source_path.is_file() else source_path,
        )

        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": "CrossHair execution timed out",
        }
    except FileNotFoundError:
        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": "CrossHair not found in PATH",
        }

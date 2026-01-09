"""
CrossHair runner for sidecar validation.

This module executes CrossHair symbolic execution on source code and harness.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require

from specfact_cli.utils.env_manager import build_tool_command, detect_env_manager


@beartype
@require(lambda source_path: source_path.exists(), "Source path must exist")
@require(lambda timeout: timeout > 0, "Timeout must be positive")
@ensure(lambda result: isinstance(result, dict), "Must return dict")
def run_crosshair(
    source_path: Path,
    timeout: int = 60,
    pythonpath: str | None = None,
    verbose: bool = False,
    repo_path: Path | None = None,
    inputs_path: Path | None = None,
    per_path_timeout: int | None = None,
    per_condition_timeout: int | None = None,
) -> dict[str, Any]:
    """
    Run CrossHair on source code or harness.

    Args:
        source_path: Path to source file or module
        timeout: Timeout in seconds
        pythonpath: PYTHONPATH for execution
        verbose: Enable verbose output
        repo_path: Optional repository path for environment manager detection

    Returns:
        Dictionary with execution results
    """
    # Preserve PATH and other environment variables, then override/add PYTHONPATH
    env = os.environ.copy()
    if pythonpath:
        env["PYTHONPATH"] = pythonpath

    # Build command using environment manager detection if repo_path provided
    base_cmd = ["crosshair", "check", str(source_path)]
    if verbose:
        base_cmd.append("--verbose")
    if per_path_timeout:
        base_cmd.extend(["--per-path-timeout", str(per_path_timeout)])
    if per_condition_timeout:
        base_cmd.extend(["--per-condition-timeout", str(per_condition_timeout)])
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

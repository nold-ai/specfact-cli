"""
Specmatic runner for sidecar validation.

This module executes Specmatic contract testing.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require

from specfact_cli.utils.env_manager import build_tool_command, detect_env_manager
from specfact_cli.validators.sidecar.models import AppConfig, SpecmaticConfig


@beartype
@ensure(lambda result: isinstance(result, bool), "Must return bool")
def has_service_configuration(specmatic_config: SpecmaticConfig, app_config: AppConfig) -> bool:
    """
    Check if service/client configuration is available for Specmatic.

    Args:
        specmatic_config: Specmatic configuration
        app_config: Application server configuration

    Returns:
        True if service configuration is available, False otherwise
    """
    # Check for test_base_url (primary indicator)
    if specmatic_config.test_base_url:
        return True

    # Check for host and port (Specmatic server configuration)
    if specmatic_config.host and specmatic_config.port:
        return True

    # Check for application server configuration
    # No service configuration found
    return bool(app_config.cmd and app_config.port)


@beartype
@require(lambda contract_path: contract_path.exists(), "Contract path must exist")
@require(lambda timeout: timeout > 0, "Timeout must be positive")
@ensure(lambda result: isinstance(result, dict), "Must return dict")
def run_specmatic(
    contract_path: Path,
    base_url: str | None = None,
    timeout: int = 60,
    repo_path: Path | None = None,
) -> dict[str, Any]:
    """
    Run Specmatic contract testing.

    Args:
        contract_path: Path to OpenAPI contract file
        base_url: Base URL for API (optional)
        timeout: Timeout in seconds
        repo_path: Optional repository path for environment manager detection

    Returns:
        Dictionary with execution results
    """
    base_cmd = ["specmatic", "test", str(contract_path)]
    if base_url:
        base_cmd.extend(["--base-url", base_url])

    # Build command using environment manager detection if repo_path provided
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
            "stderr": "Specmatic execution timed out",
        }
    except FileNotFoundError:
        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": "Specmatic not found in PATH",
        }

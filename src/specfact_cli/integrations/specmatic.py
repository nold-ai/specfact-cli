"""
Specmatic integration for API contract testing.

This module provides integration with Specmatic for OpenAPI/AsyncAPI specification
validation, backward compatibility checking, and mock server functionality.

Specmatic is a contract testing tool that validates API specifications and
generates mock servers for development. It complements SpecFact's code-level
contracts (icontract, beartype, CrossHair) by providing service-level contract testing.
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require
from rich.console import Console

from specfact_cli.utils.icontract_helpers import (
    require_new_spec_exists,
    require_old_spec_exists,
    require_spec_path_exists,
)


console = Console()


@dataclass
class SpecValidationResult:
    """Result of Specmatic validation."""

    is_valid: bool
    schema_valid: bool
    examples_valid: bool
    backward_compatible: bool | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    breaking_changes: list[str] = field(default_factory=list)

    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_valid": self.is_valid,
            "schema_valid": self.schema_valid,
            "examples_valid": self.examples_valid,
            "backward_compatible": self.backward_compatible,
            "errors": self.errors,
            "warnings": self.warnings,
            "breaking_changes": self.breaking_changes,
        }

    @ensure(lambda result: isinstance(result, str), "Must return str")
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


# Cache for specmatic command to avoid repeated checks
_specmatic_command_cache: list[str] | None = None


@beartype
def _get_specmatic_command() -> list[str] | None:
    """
    Get the Specmatic command to use, checking both direct and npx execution.

    Returns:
        Command list (e.g., ["specmatic"] or ["npx", "--yes", "specmatic"]) or None if not available
    """
    global _specmatic_command_cache
    if _specmatic_command_cache is not None:
        return _specmatic_command_cache

    # Skip subprocess calls in test mode to avoid timeouts
    if os.environ.get("TEST_MODE") == "true" or os.environ.get("PYTEST_CURRENT_TEST") is not None:
        _specmatic_command_cache = None
        return None

    # Try direct specmatic command first
    try:
        result = subprocess.run(
            ["specmatic", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            _specmatic_command_cache = ["specmatic"]
            return _specmatic_command_cache
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    except Exception:
        pass

    # Fallback to npx specmatic (requires Java/JRE)
    try:
        result = subprocess.run(
            ["npx", "--yes", "specmatic", "--version"],
            capture_output=True,
            text=True,
            timeout=10,  # npx may need to download, so longer timeout
        )
        if result.returncode == 0:
            _specmatic_command_cache = ["npx", "--yes", "specmatic"]
            return _specmatic_command_cache
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    except Exception:
        pass

    _specmatic_command_cache = None
    return None


@beartype
@ensure(lambda result: isinstance(result, tuple), "Must return tuple")
def check_specmatic_available() -> tuple[bool, str | None]:
    """
    Check if Specmatic CLI is available (either directly or via npx).

    Returns:
        Tuple of (is_available, error_message)
    """
    cmd = _get_specmatic_command()
    if cmd:
        return True, None
    return (
        False,
        "Specmatic CLI not found. Install from: https://docs.specmatic.io/ or use 'npx specmatic' (requires Java/JRE)",
    )


@beartype
@require(require_spec_path_exists, "Spec file must exist")
async def validate_spec_with_specmatic(
    spec_path: Path,
    previous_version: Path | None = None,
) -> SpecValidationResult:
    """
    Validate OpenAPI/AsyncAPI specification using Specmatic.

    Args:
        spec_path: Path to OpenAPI/AsyncAPI specification file
        previous_version: Optional path to previous version for backward compatibility check

    Returns:
        SpecValidationResult with validation status and details
    """
    # Check if Specmatic is available
    is_available, error_msg = check_specmatic_available()
    if not is_available:
        return SpecValidationResult(
            is_valid=False,
            schema_valid=False,
            examples_valid=False,
            errors=[f"Specmatic not available: {error_msg}"],
        )

    # Get specmatic command (direct or npx)
    specmatic_cmd = _get_specmatic_command()
    if not specmatic_cmd:
        return SpecValidationResult(
            is_valid=False,
            schema_valid=False,
            examples_valid=False,
            errors=["Specmatic command not available"],
        )

    result = SpecValidationResult(
        is_valid=True,
        schema_valid=True,
        examples_valid=True,
    )

    await _specmatic_apply_schema_validation(specmatic_cmd, spec_path, result)
    await _specmatic_apply_examples_validation(specmatic_cmd, spec_path, result)
    if previous_version and previous_version.exists():
        await _specmatic_apply_backward_compat(specmatic_cmd, spec_path, previous_version, result)

    return result


async def _specmatic_apply_schema_validation(
    specmatic_cmd: list[str], spec_path: Path, result: SpecValidationResult
) -> None:
    try:
        schema_result = await asyncio.to_thread(
            subprocess.run,
            [*specmatic_cmd, "validate", str(spec_path)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        result.schema_valid = schema_result.returncode == 0
        if not result.schema_valid:
            result.errors.append(f"Schema validation failed: {schema_result.stderr}")
            result.is_valid = False
    except subprocess.TimeoutExpired:
        result.schema_valid = False
        result.errors.append("Schema validation timed out")
        result.is_valid = False
    except Exception as e:
        result.schema_valid = False
        result.errors.append(f"Schema validation error: {e!s}")
        result.is_valid = False


async def _specmatic_apply_examples_validation(
    specmatic_cmd: list[str], spec_path: Path, result: SpecValidationResult
) -> None:
    try:
        examples_result = await asyncio.to_thread(
            subprocess.run,
            [*specmatic_cmd, "examples", str(spec_path), "--validate"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        result.examples_valid = examples_result.returncode == 0
        if not result.examples_valid:
            result.errors.append(f"Example generation failed: {examples_result.stderr}")
            result.is_valid = False
    except subprocess.TimeoutExpired:
        result.examples_valid = False
        result.errors.append("Example generation timed out")
        result.is_valid = False
    except Exception as e:
        result.examples_valid = False
        result.errors.append(f"Example generation error: {e!s}")
        result.is_valid = False


async def _specmatic_apply_backward_compat(
    specmatic_cmd: list[str], spec_path: Path, previous_version: Path, result: SpecValidationResult
) -> None:
    try:
        compat_result = await asyncio.to_thread(
            subprocess.run,
            [
                *specmatic_cmd,
                "backward-compatibility-check",
                str(previous_version),
                str(spec_path),
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        result.backward_compatible = compat_result.returncode == 0
        if result.backward_compatible:
            return
        output_lines = compat_result.stdout.split("\n") + compat_result.stderr.split("\n")
        breaking = [line for line in output_lines if "breaking" in line.lower() or "incompatible" in line.lower()]
        result.breaking_changes = breaking
        result.errors.append("Backward compatibility check failed")
        result.is_valid = False
    except subprocess.TimeoutExpired:
        result.backward_compatible = False
        result.errors.append("Backward compatibility check timed out")
        result.is_valid = False
    except Exception as e:
        result.backward_compatible = False
        result.errors.append(f"Backward compatibility check error: {e!s}")
        result.is_valid = False


@beartype
@require(require_old_spec_exists, "Old spec file must exist")
@require(require_new_spec_exists, "New spec file must exist")
async def check_backward_compatibility(
    old_spec: Path,
    new_spec: Path,
) -> tuple[bool, list[str]]:
    """
    Check backward compatibility between two spec versions.

    Args:
        old_spec: Path to old specification version
        new_spec: Path to new specification version

    Returns:
        Tuple of (is_compatible, breaking_changes_list)
    """
    result = await validate_spec_with_specmatic(new_spec, previous_version=old_spec)
    return result.backward_compatible or False, result.breaking_changes or []


@beartype
@require(require_spec_path_exists, "Spec file must exist")
async def generate_specmatic_examples(spec_path: Path, examples_dir: Path | None = None) -> Path:
    """
    Generate example JSON files from OpenAPI specification using Specmatic.

    Specmatic can automatically generate example request/response files from
    the OpenAPI schema, which are then used by mock servers and tests.

    Args:
        spec_path: Path to OpenAPI/AsyncAPI specification
        examples_dir: Optional output directory for examples (default: same dir as spec with _examples suffix)

    Returns:
        Path to generated examples directory
    """
    if examples_dir is None:
        # Default: create examples directory next to the spec file
        examples_dir = spec_path.parent / f"{spec_path.stem}_examples"
    examples_dir.mkdir(parents=True, exist_ok=True)

    # Get specmatic command (direct or npx)
    specmatic_cmd = _get_specmatic_command()
    if not specmatic_cmd:
        _, error_msg = check_specmatic_available()
        raise RuntimeError(f"Specmatic not available: {error_msg}")

    try:
        # Specmatic examples generate creates files in current directory by default
        # We need to run it from the examples directory parent and let it create the directory
        # Format: specmatic examples generate <spec_file>
        # This generates example files based on the schema
        result = await asyncio.to_thread(
            subprocess.run,
            [*specmatic_cmd, "examples", "generate", str(spec_path)],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(examples_dir.parent),  # Run from parent directory
        )
        if result.returncode != 0:
            # If generation failed, it might be because the directory structure is different
            # Try creating a simple example file structure manually as fallback
            console.print(f"[yellow]Warning: Specmatic example generation had issues: {result.stderr}[/yellow]")
            console.print("[dim]Mock server will generate examples on-the-fly from schema[/dim]")
        return examples_dir
    except subprocess.TimeoutExpired as e:
        raise RuntimeError("Example generation timed out") from e
    except Exception as e:
        # Don't fail completely - mock server can still work without pre-generated examples
        console.print(f"[yellow]Warning: Example generation error: {e!s}[/yellow]")
        console.print("[dim]Mock server will generate examples on-the-fly from schema[/dim]")
        return examples_dir


@beartype
@require(require_spec_path_exists, "Spec file must exist")
async def generate_specmatic_tests(spec_path: Path, output_dir: Path | None = None) -> Path:
    """
    Generate Specmatic test suite from specification.

    Args:
        spec_path: Path to OpenAPI/AsyncAPI specification
        output_dir: Optional output directory (default: .specfact/specmatic-tests/)

    Returns:
        Path to generated test directory
    """
    if output_dir is None:
        output_dir = Path(".specfact/specmatic-tests")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get specmatic command (direct or npx)
    specmatic_cmd = _get_specmatic_command()
    if not specmatic_cmd:
        _, error_msg = check_specmatic_available()
        raise RuntimeError(f"Specmatic not available: {error_msg}")

    try:
        result = await asyncio.to_thread(
            subprocess.run,
            [*specmatic_cmd, "generate-tests", str(spec_path), "--output", str(output_dir)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Test generation failed: {result.stderr}")
        return output_dir
    except subprocess.TimeoutExpired as e:
        raise RuntimeError("Test generation timed out") from e
    except Exception as e:
        raise RuntimeError(f"Test generation error: {e!s}") from e


@dataclass
class MockServer:
    """Mock server instance."""

    port: int
    process: subprocess.Popen[str] | None = None
    spec_path: Path | None = None

    @ensure(lambda result: isinstance(result, bool), "Must return bool")
    def is_running(self) -> bool:
        """Check if mock server is running."""
        if self.process is None:
            return False
        return self.process.poll() is None

    @ensure(lambda result: result is None, "Must return None")
    def stop(self) -> None:
        """Stop the mock server."""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()


def _build_specmatic_stub_command(
    specmatic_cmd: list[str],
    spec_path: Path,
    port: int,
    strict_mode: bool,
    has_examples: bool,
    examples_dir: Path,
) -> list[str]:
    cmd = [*specmatic_cmd, "stub", str(spec_path), "--port", str(port)]
    if strict_mode:
        cmd.append("--strict")
        if has_examples:
            cmd.extend(["--examples", str(examples_dir)])
    elif has_examples:
        cmd.extend(["--examples", str(examples_dir)])
    return cmd


def _tcp_localhost_port_open(port: int, timeout: float) -> bool:
    try:
        import socket

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex(("localhost", port))
        sock.close()
        return result == 0
    except Exception:
        return False


async def _wait_for_specmatic_mock_port(
    process: subprocess.Popen[str],
    port: int,
    *,
    max_wait: float = 10.0,
    wait_interval: float = 0.5,
) -> None:
    waited = 0.0
    while waited < max_wait:
        if process.poll() is not None:
            raise RuntimeError(
                f"Mock server failed to start (exited with code {process.returncode}). "
                "Check that Specmatic is installed and the contract file is valid."
            )
        if _tcp_localhost_port_open(port, 0.5):
            return
        await asyncio.sleep(wait_interval)
        waited += wait_interval


@beartype
@require(require_spec_path_exists, "Spec file must exist")
async def create_mock_server(
    spec_path: Path,
    port: int = 9000,
    strict_mode: bool = True,
) -> MockServer:
    """
    Create Specmatic mock server from specification.

    Args:
        spec_path: Path to OpenAPI/AsyncAPI specification
        port: Port number for mock server (default: 9000)
        strict_mode: Use strict validation mode (default: True)

    Returns:
        MockServer instance
    """
    specmatic_cmd = _get_specmatic_command()
    if not specmatic_cmd:
        _, error_msg = check_specmatic_available()
        raise RuntimeError(f"Specmatic not available: {error_msg}")

    examples_dir = spec_path.parent / f"{spec_path.stem}_examples"
    has_examples = examples_dir.exists() and any(examples_dir.iterdir())
    cmd = _build_specmatic_stub_command(specmatic_cmd, spec_path, port, strict_mode, has_examples, examples_dir)

    try:
        process = await asyncio.to_thread(
            subprocess.Popen,
            cmd,
            stdout=None,
            stderr=None,
            text=True,
        )

        max_wait = 10.0
        await _wait_for_specmatic_mock_port(process, port, max_wait=max_wait, wait_interval=0.5)

        port_ready = _tcp_localhost_port_open(port, 1.0)
        if process.poll() is not None:
            raise RuntimeError(
                f"Mock server process exited during startup (code {process.returncode}). "
                "Check that Specmatic is installed and the contract file is valid."
            )
        if not port_ready:
            raise RuntimeError(
                f"Mock server process is running but port {port} is not accessible after {max_wait}s. "
                "The server may have failed to bind to the port or is still starting. "
                "Check Specmatic output above for errors."
            )

        return MockServer(port=port, process=process, spec_path=spec_path)
    except Exception as e:
        raise RuntimeError(f"Failed to create mock server: {e!s}") from e

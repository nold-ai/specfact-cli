"""
Upgrade command for SpecFact CLI.

This module provides the `specfact upgrade` command for checking and installing
CLI updates from PyPI.

CrossHair: skip (subprocess-based installation checks are intentionally side-effectful)
"""

from __future__ import annotations

import os
import shlex
import subprocess
import sys
from datetime import UTC
from pathlib import Path
from typing import Any, NamedTuple

import typer
from beartype import beartype
from icontract import ensure
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

from specfact_cli import __version__
from specfact_cli.contracts.module_interface import ModuleIOContract
from specfact_cli.modules import module_io_shim
from specfact_cli.runtime import debug_log_operation, debug_print, is_debug_mode
from specfact_cli.utils.metadata import update_metadata
from specfact_cli.utils.startup_checks import check_pypi_version


app = typer.Typer(
    help="Check for and install SpecFact CLI updates",
    context_settings={"help_option_names": ["-h", "--help"]},
)
console = Console()
_MODULE_IO_CONTRACT = ModuleIOContract
import_to_bundle = module_io_shim.import_to_bundle
export_from_bundle = module_io_shim.export_from_bundle
sync_with_bundle = module_io_shim.sync_with_bundle
validate_bundle = module_io_shim.validate_bundle


class InstallationMethod(NamedTuple):
    """Installation method information."""

    method: str  # "pip", "uv", "uvx", "pipx", or "unknown"
    command: str  # Command to run for update
    location: str | None  # Installation location if known


@beartype
@ensure(lambda result: isinstance(result, InstallationMethod), "Must return InstallationMethod")
def detect_installation_method() -> InstallationMethod:
    """Detect how SpecFact CLI was installed."""
    executable_path = str(Path(sys.executable))

    uvx_method = _detect_uvx_installation(executable_path)
    if uvx_method:
        return uvx_method

    uv_method = _detect_uv_installation(executable_path)
    if uv_method:
        return uv_method

    pipx_method = _detect_pipx_installation()
    if pipx_method:
        return pipx_method

    pip_method = _detect_pip_installation()
    if pip_method:
        return pip_method

    return InstallationMethod(method="pip", command="pip install --upgrade specfact-cli", location=None)


def _detect_uvx_installation(executable_path: str) -> InstallationMethod | None:
    if "uvx" in sys.argv[0] or "uvx" in executable_path:
        return InstallationMethod(method="uvx", command="uvx --from specfact-cli specfact --version", location=None)
    return None


def _detect_uv_installation(executable_path: str) -> InstallationMethod | None:
    uv_project_env = os.environ.get("UV_PROJECT_ENVIRONMENT", "").strip()
    if uv_project_env:
        try:
            uv_root = Path(uv_project_env).resolve()
            executable = Path(executable_path).resolve()
        except OSError:
            uv_root = None
            executable = None
        if uv_root is not None and executable is not None and (executable == uv_root or uv_root in executable.parents):
            return InstallationMethod(
                method="uv",
                command="uv pip install --upgrade specfact-cli",
                location=str(Path(executable_path).parent.parent),
            )
    if Path(sys.executable).name in {"uv", "uv.exe"}:
        return InstallationMethod(method="uv", command="uv tool upgrade specfact-cli", location=None)
    return None


def _detect_pipx_installation() -> InstallationMethod | None:
    try:
        result = subprocess.run(["pipx", "list"], capture_output=True, text=True, timeout=5, check=False)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None
    if "specfact-cli" in result.stdout:
        return InstallationMethod(method="pipx", command="pipx upgrade specfact-cli", location=None)
    return None


def _detect_pip_installation() -> InstallationMethod | None:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", "specfact-cli"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None

    if result.returncode != 0:
        return None

    location = None
    for line in result.stdout.splitlines():
        if line.startswith("Location:"):
            location = line.split(":", 1)[1].strip()
            break
    quoted_executable = shlex.quote(sys.executable)
    return InstallationMethod(
        method="pip",
        command=f"{quoted_executable} -m pip install --upgrade specfact-cli",
        location=location,
    )


@beartype
@ensure(lambda result: isinstance(result, bool), "Must return bool")
def install_update(method: InstallationMethod, yes: bool = False) -> bool:
    """Install update using the detected installation method."""
    if not yes:
        console.print(f"[yellow]This will update SpecFact CLI using:[/yellow] [cyan]{method.command}[/cyan]")
        if not Confirm.ask("Continue?", default=True):
            console.print("[dim]Update cancelled[/dim]")
            return False

    if method.method == "uvx":
        console.print(
            "[yellow]uvx automatically uses the latest version.[/yellow]\n"
            "[dim]No update needed. If you want to force a refresh, run:[/dim]\n"
            "[cyan]uvx --from specfact-cli@latest specfact --version[/cyan]"
        )
        return True

    command = _build_upgrade_command(method)
    if command is None:
        console.print(f"[red]✗ Unsupported installation method: {method.method}[/red]")
        return False

    return _execute_upgrade_command(command)


def _build_upgrade_command(method: InstallationMethod) -> list[str] | None:
    if method.method == "pipx":
        return ["pipx", "upgrade", "specfact-cli"]
    if method.method == "uv":
        if "uv tool" in method.command:
            return ["uv", "tool", "upgrade", "specfact-cli"]
        python_target = method.location or sys.executable
        return ["uv", "pip", "install", "--python", python_target, "--upgrade", "specfact-cli"]
    if method.method == "pip":
        parts = shlex.split(method.command)
        if len(parts) >= 3 and parts[1:3] == ["-m", "pip"]:
            return [parts[0], "-m", "pip", "install", "--upgrade", "specfact-cli"]
        return ["pip", "install", "--upgrade", "specfact-cli"]
    return None


def _execute_upgrade_command(command: list[str]) -> bool:
    try:
        console.print("[cyan]Updating SpecFact CLI...[/cyan]")
        result = subprocess.run(command, check=False, timeout=300)
        if result.returncode != 0:
            console.print(f"[red]✗ Update failed with exit code {result.returncode}[/red]")
            return False
        console.print("[green]✓ Update successful![/green]")
        from datetime import datetime

        update_metadata(last_checked_version=__version__, last_version_check_timestamp=datetime.now(UTC).isoformat())
        return True
    except subprocess.TimeoutExpired:
        console.print("[red]✗ Update timed out (exceeded 5 minutes)[/red]")
        return False
    except Exception as e:
        console.print(f"[red]✗ Update failed: {e}[/red]")
        return False


def _upgrade_log_started(check_only: bool, yes: bool) -> None:
    if is_debug_mode():
        debug_log_operation(
            "command",
            "upgrade",
            "started",
            extra={"check_only": check_only, "yes": yes},
        )
        debug_print("[dim]upgrade: started[/dim]")


def _upgrade_handle_check_failure(version_result: Any) -> None:
    if is_debug_mode():
        debug_log_operation(
            "command",
            "upgrade",
            "failed",
            error=version_result.error or "Unknown error",
            extra={"reason": "check_error"},
        )
    console.print(f"[red]Error checking for updates: {version_result.error}[/red]")
    sys.exit(1)


def _upgrade_handle_up_to_date(version_result: Any) -> None:
    if is_debug_mode():
        debug_log_operation(
            "command",
            "upgrade",
            "success",
            extra={"reason": "up_to_date", "version": version_result.current_version},
        )
        debug_print("[dim]upgrade: success (up to date)[/dim]")
    console.print(f"[green]✓ You're up to date![/green] (version {version_result.current_version})")
    from datetime import datetime

    update_metadata(
        last_checked_version=__version__,
        last_version_check_timestamp=datetime.now(UTC).isoformat(),
    )


def _upgrade_render_update_panel(version_result: Any) -> None:
    update_type_color = "red" if version_result.update_type == "major" else "yellow"
    update_type_icon = "🔴" if version_result.update_type == "major" else "🟡"
    update_info = (
        f"[bold {update_type_color}]{update_type_icon} Update Available[/bold {update_type_color}]\n\n"
        f"Current: [cyan]{version_result.current_version}[/cyan]\n"
        f"Latest: [green]{version_result.latest_version}[/green]\n"
    )
    if version_result.update_type == "major":
        update_info += (
            "\n[bold red]⚠ Breaking changes may be present![/bold red]\nReview release notes before upgrading.\n"
        )
    console.print()
    console.print(Panel(update_info, border_style=update_type_color))


def _upgrade_install_or_check_only(version_result: Any, check_only: bool, yes: bool) -> None:
    if check_only:
        method = detect_installation_method()
        if method.method == "uvx":
            console.print(
                "[yellow]uvx automatically uses the latest version.[/yellow]\n"
                "[dim]No update needed. If you want to force a refresh, run:[/dim]\n"
                "[cyan]uvx --from specfact-cli@latest specfact --version[/cyan]"
            )
            return
        console.print(f"\n[yellow]To upgrade, run:[/yellow] [cyan]{method.command}[/cyan]")
        console.print("[dim]Or run:[/dim] [cyan]specfact upgrade --yes[/cyan]")
        return
    method = detect_installation_method()
    console.print(f"\n[cyan]Installation method detected:[/cyan] [bold]{method.method}[/bold]")
    success = install_update(method, yes=yes)
    if success:
        if is_debug_mode():
            debug_log_operation("command", "upgrade", "success", extra={"reason": "installed"})
            debug_print("[dim]upgrade: success[/dim]")
        console.print("\n[green]✓ Update complete![/green]")
        console.print("[dim]Run 'specfact --version' to verify the new version.[/dim]")
        return
    if is_debug_mode():
        debug_log_operation(
            "command",
            "upgrade",
            "failed",
            error="Update was not installed",
            extra={"reason": "install_failed"},
        )
    console.print("\n[yellow]Update was not installed.[/yellow]")
    console.print("[dim]You can manually update using the command shown above.[/dim]")
    sys.exit(1)


@app.callback(invoke_without_command=True)
@beartype
@ensure(lambda result: result is None, "upgrade must return None")
def upgrade(
    check_only: bool = typer.Option(
        False,
        "--check-only",
        help="Only check for updates, don't install",
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip confirmation prompt and install immediately",
    ),
) -> None:
    """
    Check for and install SpecFact CLI updates.

    This command:
    1. Checks PyPI for the latest version
    2. Compares with current version
    3. Optionally installs the update using the detected installation method (pip, pipx, uvx)

    Examples:
        # Check for updates only
        specfact upgrade --check-only

        # Check and install (with confirmation)
        specfact upgrade

        # Check and install without confirmation
        specfact upgrade --yes
    """
    _upgrade_log_started(check_only, yes)

    console.print("[cyan]Checking for updates...[/cyan]")
    version_result = check_pypi_version()

    if version_result.error:
        _upgrade_handle_check_failure(version_result)

    if not version_result.update_available:
        _upgrade_handle_up_to_date(version_result)
        return

    if version_result.latest_version and version_result.update_type:
        _upgrade_render_update_panel(version_result)
        _upgrade_install_or_check_only(version_result, check_only, yes)

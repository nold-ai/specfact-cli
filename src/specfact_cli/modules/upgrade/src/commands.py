"""
Upgrade command for SpecFact CLI.

This module provides the `specfact upgrade` command for checking and installing
CLI updates from PyPI.
"""

from __future__ import annotations

import subprocess
import sys
from datetime import UTC
from pathlib import Path
from typing import NamedTuple

import typer
from beartype import beartype
from icontract import ensure
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

from specfact_cli import __version__
from specfact_cli.runtime import debug_log_operation, debug_print, is_debug_mode
from specfact_cli.utils.metadata import update_metadata
from specfact_cli.utils.startup_checks import check_pypi_version


app = typer.Typer(
    help="Check for and install SpecFact CLI updates",
    context_settings={"help_option_names": ["-h", "--help"]},
)
console = Console()


class InstallationMethod(NamedTuple):
    """Installation method information."""

    method: str  # "pip", "uvx", "pipx", or "unknown"
    command: str  # Command to run for update
    location: str | None  # Installation location if known


@beartype
@ensure(lambda result: isinstance(result, InstallationMethod), "Must return InstallationMethod")
def detect_installation_method() -> InstallationMethod:
    """
    Detect how SpecFact CLI was installed.

    Returns:
        InstallationMethod with detected method and update command
    """
    # Check if running via uvx
    if "uvx" in sys.argv[0] or "uvx" in str(Path(sys.executable)):
        return InstallationMethod(
            method="uvx",
            command="uvx --from specfact-cli specfact --version",
            location=None,
        )

    # Check if running via pipx
    try:
        result = subprocess.run(
            ["pipx", "list"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if "specfact-cli" in result.stdout:
            return InstallationMethod(
                method="pipx",
                command="pipx upgrade specfact-cli",
                location=None,
            )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Check if installed via pip (user or system)
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", "specfact-cli"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if result.returncode == 0:
            # Parse location from output
            location = None
            for line in result.stdout.splitlines():
                if line.startswith("Location:"):
                    location = line.split(":", 1)[1].strip()
                    break

            return InstallationMethod(
                method="pip",
                command=f"{sys.executable} -m pip install --upgrade specfact-cli",
                location=location,
            )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Fallback: assume pip
    return InstallationMethod(
        method="pip",
        command="pip install --upgrade specfact-cli",
        location=None,
    )


@beartype
@ensure(lambda result: isinstance(result, bool), "Must return bool")
def install_update(method: InstallationMethod, yes: bool = False) -> bool:
    """
    Install update using the detected installation method.

    Args:
        method: InstallationMethod with update command
        yes: If True, skip confirmation prompt

    Returns:
        True if update was successful, False otherwise
    """
    if not yes:
        console.print(f"[yellow]This will update SpecFact CLI using:[/yellow] [cyan]{method.command}[/cyan]")
        if not Confirm.ask("Continue?", default=True):
            console.print("[dim]Update cancelled[/dim]")
            return False

    try:
        console.print("[cyan]Updating SpecFact CLI...[/cyan]")
        # Split command into parts for subprocess
        if method.method == "pipx":
            cmd = ["pipx", "upgrade", "specfact-cli"]
        elif method.method == "pip":
            # Handle both formats: "python -m pip" and "pip"
            if " -m pip" in method.command:
                parts = method.command.split()
                cmd = [parts[0], "-m", "pip", "install", "--upgrade", "specfact-cli"]
            else:
                cmd = ["pip", "install", "--upgrade", "specfact-cli"]
        else:
            # uvx - just inform user
            console.print(
                "[yellow]uvx automatically uses the latest version.[/yellow]\n"
                "[dim]No update needed. If you want to force a refresh, run:[/dim]\n"
                "[cyan]uvx --from specfact-cli@latest specfact --version[/cyan]"
            )
            return True

        result = subprocess.run(
            cmd,
            check=False,
            timeout=300,  # 5 minute timeout
        )

        if result.returncode == 0:
            console.print("[green]✓ Update successful![/green]")
            # Update metadata to reflect new version
            from datetime import datetime

            update_metadata(
                last_checked_version=__version__,
                last_version_check_timestamp=datetime.now(UTC).isoformat(),
            )
            return True
        console.print(f"[red]✗ Update failed with exit code {result.returncode}[/red]")
        return False

    except subprocess.TimeoutExpired:
        console.print("[red]✗ Update timed out (exceeded 5 minutes)[/red]")
        return False
    except Exception as e:
        console.print(f"[red]✗ Update failed: {e}[/red]")
        return False


@app.callback(invoke_without_command=True)
@beartype
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
    if is_debug_mode():
        debug_log_operation(
            "command",
            "upgrade",
            "started",
            extra={"check_only": check_only, "yes": yes},
        )
        debug_print("[dim]upgrade: started[/dim]")

    # Check for updates
    console.print("[cyan]Checking for updates...[/cyan]")
    version_result = check_pypi_version()

    if version_result.error:
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

    if not version_result.update_available:
        if is_debug_mode():
            debug_log_operation(
                "command",
                "upgrade",
                "success",
                extra={"reason": "up_to_date", "version": version_result.current_version},
            )
            debug_print("[dim]upgrade: success (up to date)[/dim]")
        console.print(f"[green]✓ You're up to date![/green] (version {version_result.current_version})")
        # Update metadata even if no update available
        from datetime import datetime

        update_metadata(
            last_checked_version=__version__,
            last_version_check_timestamp=datetime.now(UTC).isoformat(),
        )
        return

    # Update available
    if version_result.latest_version and version_result.update_type:
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

        if check_only:
            # Detect installation method for user info
            method = detect_installation_method()
            console.print(f"\n[yellow]To upgrade, run:[/yellow] [cyan]{method.command}[/cyan]")
            console.print("[dim]Or run:[/dim] [cyan]specfact upgrade --yes[/cyan]")
            return

        # Install update
        method = detect_installation_method()
        console.print(f"\n[cyan]Installation method detected:[/cyan] [bold]{method.method}[/bold]")

        success = install_update(method, yes=yes)

        if success:
            if is_debug_mode():
                debug_log_operation("command", "upgrade", "success", extra={"reason": "installed"})
                debug_print("[dim]upgrade: success[/dim]")
            console.print("\n[green]✓ Update complete![/green]")
            console.print("[dim]Run 'specfact --version' to verify the new version.[/dim]")
        else:
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

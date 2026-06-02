"""
Upgrade command for SpecFact CLI.

This module provides the `specfact upgrade` command for checking and installing
CLI updates from PyPI.

CrossHair: skip (subprocess-based installation checks are intentionally side-effectful)
"""

from __future__ import annotations

import os
import shlex
import shutil
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
from rich.text import Text

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

    uv_method = _detect_uv_project_installation(executable_path)
    if uv_method:
        return uv_method

    uv_method = _detect_uv_run_installation(executable_path)
    if uv_method:
        return uv_method

    pipx_method = _detect_pipx_installation()
    if pipx_method:
        return pipx_method

    uv_method = _detect_uv_tool_installation()
    if uv_method:
        return uv_method

    pip_method = _detect_pip_installation()
    if pip_method:
        return pip_method

    quoted_executable = shlex.quote(sys.executable)
    return InstallationMethod(
        method="pip",
        command=f"{quoted_executable} -m pip install --upgrade specfact-cli",
        location=None,
    )


def _detect_uvx_installation(executable_path: str) -> InstallationMethod | None:
    if _path_segments_contain_uvx(sys.argv[0]) or _path_segments_contain_uvx(executable_path):
        return InstallationMethod(method="uvx", command="uvx --from specfact-cli specfact --version", location=None)
    return None


def _path_segments_contain_uvx(path_value: str) -> bool:
    segments = [segment for segment in path_value.replace("\\", "/").split("/") if segment]
    return any(_is_uvx_executable_name(segment) for segment in segments)


def _is_uvx_executable_name(segment: str) -> bool:
    lower_segment = segment.lower()
    for suffix in (".exe", ".cmd", ".bat"):
        if lower_segment.endswith(suffix):
            lower_segment = lower_segment[: -len(suffix)]
            break
    return lower_segment == "uvx"


def _detect_uv_project_installation(executable_path: str) -> InstallationMethod | None:
    uv_project_env = os.environ.get("UV_PROJECT_ENVIRONMENT", "").strip()
    if uv_project_env:
        try:
            uv_root = Path(uv_project_env).resolve()
            executable = Path(executable_path).resolve()
        except OSError:
            return None
        if executable == uv_root or uv_root in executable.parents:
            executable_text = str(executable)
            return InstallationMethod(
                method="uv",
                command=f"uv pip install --python {shlex.quote(executable_text)} --upgrade specfact-cli",
                location=executable_text,
            )
    return None


def _detect_uv_run_installation(executable_path: str) -> InstallationMethod | None:
    uv_context_keys = ("UV_RUN_RECURSION", "UV")
    if not any(os.environ.get(key, "").strip() for key in uv_context_keys):
        return None
    executable_text = str(Path(executable_path))
    return InstallationMethod(
        method="uv",
        command=f"uv pip install --python {shlex.quote(executable_text)} --upgrade specfact-cli",
        location=executable_text,
    )


def _detect_uv_tool_installation() -> InstallationMethod | None:
    try:
        result = subprocess.run(
            ["uv", "tool", "list"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None
    if "specfact-cli" in result.stdout:
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
        result = subprocess.run(command, check=False, timeout=300, capture_output=True)
    except subprocess.TimeoutExpired as exc:
        _replay_upgrade_output(_coerce_subprocess_output(exc.stdout))
        _replay_upgrade_output(_coerce_subprocess_output(exc.stderr))
        console.print("[red]✗ Update timed out (exceeded 5 minutes)[/red]")
        return False
    except OSError as e:
        console.print(f"[red]✗ Update failed: {e}[/red]")
        return False
    stdout = _coerce_subprocess_output(result.stdout)
    stderr = _coerce_subprocess_output(result.stderr)
    if result.returncode != 0:
        _replay_upgrade_output(stdout)
        _replay_upgrade_output(stderr)
        console.print(f"[red]✗ Update failed with exit code {result.returncode}[/red]")
        return False
    if _is_pipx_upgrade_command(command):
        stdout = _filter_pipx_spaced_home_warning(stdout)
        stderr = _filter_pipx_spaced_home_warning(stderr)
    _replay_upgrade_output(stdout)
    _replay_upgrade_output(stderr)
    if _is_pipx_upgrade_command(command) and not _ensure_pipx_launcher_healthy():
        return False
    console.print("[green]✓ Update successful![/green]")
    from datetime import datetime

    try:
        update_metadata(last_checked_version=__version__, last_version_check_timestamp=datetime.now(UTC).isoformat())
    except (OSError, TypeError) as exc:
        console.print(f"[yellow]Update succeeded, but metadata update failed: {exc}[/yellow]")
    return True


def _coerce_subprocess_output(output: object) -> str:
    """Return subprocess output as displayable text."""
    if isinstance(output, str):
        return output
    if isinstance(output, bytes):
        return output.decode(errors="replace")
    return ""


def _is_pipx_upgrade_command(command: list[str]) -> bool:
    """Return whether command is the supported pipx upgrade invocation."""
    return len(command) >= 3 and command[:3] == ["pipx", "upgrade", "specfact-cli"]


def _ensure_pipx_launcher_healthy() -> bool:
    """Validate the public specfact launcher after pipx upgrade and repair stale shims."""
    launcher = shutil.which("specfact")
    if not launcher:
        console.print(
            "[yellow]⚠ Could not find `specfact` on PATH after pipx upgrade; "
            "running `pipx reinstall specfact-cli`.[/yellow]"
        )
        return _repair_pipx_launcher(None)

    first_check = _run_launcher_version_check(launcher)
    if first_check.returncode == 0:
        _replay_upgrade_output(_coerce_subprocess_output(first_check.stdout))
        _replay_upgrade_output(_coerce_subprocess_output(first_check.stderr))
        return True

    console.print("[yellow]⚠ pipx launcher is stale or broken; running `pipx reinstall specfact-cli`.[/yellow]")
    _replay_upgrade_output(_coerce_subprocess_output(first_check.stdout))
    _replay_upgrade_output(_coerce_subprocess_output(first_check.stderr))
    return _repair_pipx_launcher(launcher)


def _repair_pipx_launcher(previous_launcher: str | None) -> bool:
    """Reinstall via pipx and validate the resulting public launcher."""
    reinstall = _run_pipx_reinstall()
    _replay_upgrade_output(_coerce_subprocess_output(reinstall.stdout))
    _replay_upgrade_output(_coerce_subprocess_output(reinstall.stderr))
    if reinstall.returncode != 0:
        console.print(f"[red]✗ pipx reinstall specfact-cli failed with exit code {reinstall.returncode}[/red]")
        return False

    launcher = shutil.which("specfact") or previous_launcher
    if not launcher:
        console.print("[red]✗ `specfact` is still missing on PATH after reinstall[/red]")
        return False

    second_check = _run_launcher_version_check(launcher)
    _replay_upgrade_output(_coerce_subprocess_output(second_check.stdout))
    _replay_upgrade_output(_coerce_subprocess_output(second_check.stderr))
    if second_check.returncode != 0:
        console.print("[red]✗ pipx launcher still fails after reinstall[/red]")
        return False
    console.print("[green]✓ pipx launcher repaired and validated[/green]")
    return True


def _run_launcher_version_check(launcher: str) -> subprocess.CompletedProcess[bytes]:
    """Run the installed launcher version check without invoking a shell."""
    try:
        return subprocess.run([launcher, "--version"], check=False, timeout=30, capture_output=True)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return subprocess.CompletedProcess([launcher, "--version"], 1, stdout=b"", stderr=str(exc).encode())


def _run_pipx_reinstall() -> subprocess.CompletedProcess[bytes]:
    """Repair a stale pipx launcher by reinstalling the package."""
    try:
        return subprocess.run(["pipx", "reinstall", "specfact-cli"], check=False, timeout=300, capture_output=True)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return subprocess.CompletedProcess(
            ["pipx", "reinstall", "specfact-cli"], 1, stdout=b"", stderr=str(exc).encode()
        )


def _replay_upgrade_output(output: str) -> None:
    """Replay captured child-process output without Rich markup parsing."""
    if output:
        console.print(Text(output), end="")


def _filter_pipx_spaced_home_warning(output: str) -> str:
    """Remove only pipx's known spaced-home warning block from successful output."""
    if not output:
        return output
    warning_markers = (
        "Found a space in the pipx home path",
        "To see your PIPX_HOME dir",
        "Most likely fix on macOS",
    )
    filtered_lines: list[str] = []
    skipping_wrapped_warning = False
    for line in output.splitlines(keepends=True):
        if any(marker in line for marker in warning_markers):
            skipping_wrapped_warning = "Found a space in the pipx home path" in line
            continue
        if skipping_wrapped_warning and line[:1].isspace():
            continue
        skipping_wrapped_warning = False
        filtered_lines.append(line)
    return "".join(filtered_lines)


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

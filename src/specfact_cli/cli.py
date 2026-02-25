"""
SpecFact CLI - Main application entry point.

This module defines the main Typer application and registers all command groups.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Annotated


# Patch shellingham before Typer imports it to normalize "sh" to "bash"
# This fixes auto-detection on Ubuntu where /bin/sh points to dash
try:
    import shellingham

    # Store original function
    _original_detect_shell = shellingham.detect_shell

    def _normalized_detect_shell(pid=None, max_depth=10):  # type: ignore[misc]
        """Normalized shell detection that maps 'sh' to 'bash'."""
        shell_name, shell_path = _original_detect_shell(pid, max_depth)  # type: ignore[misc]
        if shell_name:
            shell_lower = shell_name.lower()
            # Map shell names using our normalization
            shell_map = {
                "sh": "bash",  # sh is bash-compatible
                "bash": "bash",
                "zsh": "zsh",
                "fish": "fish",
                "powershell": "powershell",
                "pwsh": "powershell",
                "ps1": "powershell",
            }
            normalized = shell_map.get(shell_lower, shell_lower)
            return (normalized, shell_path)
        return (shell_name, shell_path)

    # Patch shellingham's detect_shell function
    shellingham.detect_shell = _normalized_detect_shell
except ImportError:
    # shellingham not available, will use fallback logic
    pass

import click
import typer
from beartype import beartype
from icontract import ViolationError
from rich.panel import Panel

from specfact_cli import __version__, runtime
from specfact_cli.modes import OperationalMode, detect_mode

# Command groups are registered via CommandRegistry (bootstrap); no top-level command imports.
from specfact_cli.registry import CommandRegistry
from specfact_cli.registry.bootstrap import register_builtin_commands
from specfact_cli.registry.metadata import CommandMetadata
from specfact_cli.runtime import get_configured_console, init_debug_log_file, set_debug_mode
from specfact_cli.utils.progressive_disclosure import ProgressiveDisclosureGroup
from specfact_cli.utils.structured_io import StructuredFormat


# Map shell names for completion support
SHELL_MAP = {
    "sh": "bash",  # sh is bash-compatible
    "bash": "bash",
    "zsh": "zsh",
    "fish": "fish",
    "powershell": "powershell",
    "pwsh": "powershell",  # PowerShell Core
    "ps1": "powershell",  # PowerShell alias
}


def normalize_shell_in_argv() -> None:
    """Normalize shell names in sys.argv before Typer processes them.

    Also handles auto-detection case where Typer detects "sh" instead of "bash".
    """
    if len(sys.argv) >= 2 and sys.argv[1] in ("--show-completion", "--install-completion"):
        # If shell is provided as argument, normalize it
        if len(sys.argv) >= 3:
            shell_arg = sys.argv[2]
            shell_normalized = shell_arg.lower().strip()
            mapped_shell = SHELL_MAP.get(shell_normalized, shell_normalized)
            if mapped_shell != shell_normalized:
                # Replace "sh" with "bash" in argv (or other mapped shells)
                sys.argv[2] = mapped_shell
        else:
            # Auto-detection case: Typer will detect shell, but we need to ensure
            # it doesn't detect "sh". We'll intercept after Typer detects it.
            # For now, explicitly pass "bash" if SHELL env var points to sh/bash
            shell_env = os.environ.get("SHELL", "")
            if shell_env and ("sh" in shell_env.lower() or "bash" in shell_env.lower()):
                # Force bash if shell is sh or bash
                sys.argv.append("bash")


# Note: Shell normalization happens in cli_main() before app() is called
# We don't normalize at module load time because sys.argv may not be set yet


app = typer.Typer(
    name="specfact",
    help="SpecFact CLI - Spec → Contract → Sentinel for Contract-Driven Development",
    add_completion=True,  # Enable Typer's built-in completion (works natively for bash/zsh/fish without extensions)
    rich_markup_mode="rich",
    context_settings={"help_option_names": ["-h", "--help", "--help-advanced", "-ha"]},  # Add aliases for help
    cls=ProgressiveDisclosureGroup,  # Use custom group for progressive disclosure
)

console = get_configured_console()

# Global mode context (set by --mode flag or auto-detected)
_current_mode: OperationalMode | None = None

# Global banner flag (set by --banner flag)
_show_banner: bool = False


def print_banner() -> None:
    """Print SpecFact CLI ASCII art banner with smooth gradient effect."""
    from rich.text import Text

    banner_lines = [
        "",
        "  ███████╗██████╗ ███████╗ ██████╗███████╗ █████╗  ██████╗████████╗",
        "  ██╔════╝██╔══██╗██╔════╝██╔════╝██╔════╝██╔══██╗██╔════╝╚══██╔══╝",
        "  ███████╗██████╔╝█████╗  ██║     █████╗  ███████║██║        ██║   ",
        "  ╚════██║██╔═══╝ ██╔══╝  ██║     ██╔══╝  ██╔══██║██║        ██║   ",
        "  ███████║██║     ███████╗╚██████╗██║     ██║  ██║╚██████╗   ██║   ",
        "  ╚══════╝╚═╝     ╚══════╝ ╚═════╝╚═╝     ╚═╝  ╚═╝ ╚═════╝   ╚═╝   ",
        "",
        "     Spec → Contract → Sentinel for Contract-Driven Development",
    ]

    # Smooth gradient from bright cyan (top) to blue (bottom) - 6 lines for ASCII art
    # Using Rich's gradient colors: bright_cyan → cyan → bright_blue → blue
    gradient_colors = [
        "black",  # Empty line
        "blue",  # Line 1 - darkest at top
        "blue",  # Line 2
        "cyan",  # Line 3
        "cyan",  # Line 4
        "white",  # Line 5
        "white",  # Line 6 - lightest at bottom
    ]

    for i, line in enumerate(banner_lines):
        if line.strip():  # Only apply gradient to non-empty lines
            if i < len(gradient_colors):
                # Apply gradient color to ASCII art lines
                text = Text(line, style=f"bold {gradient_colors[i]}")
                console.print(text)
            else:
                # Tagline in cyan (after empty line)
                console.print(line, style="cyan")
        else:
            console.print()  # Empty line


def print_version_line() -> None:
    """Print simple version line like other CLIs."""
    console.print(f"[dim]SpecFact CLI - v{__version__}[/dim]")


def version_callback(value: bool) -> None:
    """Show version information."""
    if value:
        console.print(f"[bold cyan]SpecFact CLI[/bold cyan] version [green]{__version__}[/green]")
        raise typer.Exit()


def mode_callback(value: str | None) -> None:
    """Handle --mode flag callback."""
    global _current_mode
    if value is not None:
        try:
            _current_mode = OperationalMode(value.lower())
        except ValueError:
            console.print(f"[bold red]✗[/bold red] Invalid mode: {value}")
            console.print("Valid modes: cicd, copilot")
            raise typer.Exit(1) from None
        runtime.set_operational_mode(_current_mode)


@beartype
def get_current_mode() -> OperationalMode:
    """
    Get the current operational mode.

    Returns:
        Current operational mode (detected or explicit)
    """
    global _current_mode
    if _current_mode is not None:
        return _current_mode
    # Auto-detect if not explicitly set
    _current_mode = detect_mode(explicit_mode=None)
    runtime.set_operational_mode(_current_mode)
    return _current_mode


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
    banner: bool = typer.Option(
        False,
        "--banner",
        help="Show ASCII art banner (hidden by default, shown on first run)",
    ),
    mode: str | None = typer.Option(
        None,
        "--mode",
        callback=mode_callback,
        help="Operational mode: cicd (fast, deterministic) or copilot (enhanced, interactive)",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        help="Enable debug output: console diagnostics and log file at ~/.specfact/logs/specfact-debug.log (operation metadata for file I/O and API calls)",
    ),
    skip_checks: bool = typer.Option(
        False,
        "--skip-checks",
        help="Skip startup checks (template validation and version check) - useful for CI/CD",
    ),
    input_format: Annotated[
        StructuredFormat,
        typer.Option(
            "--input-format",
            help="Default structured input format (yaml or json)",
            case_sensitive=False,
        ),
    ] = StructuredFormat.YAML,
    output_format: Annotated[
        StructuredFormat,
        typer.Option(
            "--output-format",
            help="Default structured output format for generated files (yaml or json)",
            case_sensitive=False,
        ),
    ] = StructuredFormat.YAML,
    interaction: Annotated[
        bool | None,
        typer.Option(
            "--interactive/--no-interactive",
            help="Force interaction mode (default auto based on terminal/CI detection)",
        ),
    ] = None,
) -> None:
    """
    SpecFact CLI - Spec→Contract→Sentinel for contract-driven development.

    Transform your development workflow with automated quality gates,
    runtime contract validation, and state machine workflows.

    **Backlog Management**: Use `specfact backlog refine` for AI-assisted template-driven
    refinement of backlog items from GitHub Issues, Azure DevOps, and other tools.

    Mode Detection:
    - Explicit --mode flag (highest priority)
    - Auto-detect from environment (CoPilot API, IDE integration)
    - Default to CI/CD mode

    Interaction Detection:
    - Explicit --interactive/--no-interactive (highest priority)
    - Auto-detect from terminal and CI environment
    """
    global _show_banner
    global console

    # Rebind root and loaded module consoles for each invocation to avoid stale
    # closed capture streams across sequential CliRunner/pytest command runs.
    console = get_configured_console()
    runtime.refresh_loaded_module_consoles()

    # Set banner flag based on --banner option
    _show_banner = banner

    # Set debug mode
    set_debug_mode(debug)
    if debug:
        init_debug_log_file()

    runtime.configure_io_formats(input_format=input_format, output_format=output_format)
    # Invert logic: --interactive means not non-interactive, --no-interactive means non-interactive
    if interaction is not None:
        runtime.set_non_interactive_override(not interaction)
    else:
        runtime.set_non_interactive_override(None)

    # Show welcome message if no command provided
    if ctx.invoked_subcommand is None:
        console.print(
            Panel.fit(
                "[bold green]✓[/bold green] SpecFact CLI is installed and working!\n\n"
                f"Version: [cyan]{__version__}[/cyan]\n"
                "Run [bold]specfact --help[/bold] for available commands.",
                title="[bold]Welcome to SpecFact CLI[/bold]",
                border_style="green",
            )
        )
        raise typer.Exit()

    # Store mode in context for commands to access
    if ctx.obj is None:
        ctx.obj = {}
    ctx.obj["mode"] = get_current_mode()


# Register command groups from CommandRegistry (bootstrap preserves display order).
# Use a custom Click Group so that "specfact plan init ..." passes full args to the real plan
# Typer (no "No such command 'init'" from an empty group).
# Global options (e.g. --no-interactive, --debug) must be passed before the command: specfact [OPTIONS] COMMAND [ARGS]...


class _LazyDelegateGroup(click.Group):
    """Click Group that delegates all args to the real command (lazy-loaded)."""

    def __init__(self, cmd_name: str, help_str: str, name: str | None = None, help: str | None = None) -> None:
        super().__init__(
            name=name or cmd_name,
            help=help or help_str,
            context_settings={"ignore_unknown_options": True},
        )
        self._lazy_cmd_name = cmd_name
        self._lazy_help_str = help_str
        self._delegate_cmd = self._make_delegate_command()

    def _make_delegate_command(self) -> click.Command:
        cmd_name = self._lazy_cmd_name

        def _invoke(args: tuple[str, ...]) -> None:
            from typer.main import get_command

            ctx = click.get_current_context()
            real_typer = CommandRegistry.get_typer(cmd_name)
            click_cmd = get_command(real_typer)
            # Build full prog name from root (e.g. "specfact sync") so usage shows "specfact sync bridge", not "sync sync bridge"
            parts: list[str] = []
            p = ctx.parent
            while p and getattr(p, "command", None):
                name = getattr(p.command, "name", None)
                if name and name != "__delegate__":
                    parts.append(name)
                p = getattr(p, "parent", None)
            prog_name = " ".join(reversed(parts)) if parts else cmd_name
            args_list = list(args)
            # When the real app is a single command (e.g. drift has only "detect"), Typer
            # builds a TyperCommand, not a Group. Then args are ["detect", "bundle", "--repo", ...]
            # and the command expects ["bundle", "--repo", ...] (no leading "detect").
            if (
                not isinstance(click_cmd, click.Group)
                and args_list
                and args_list[0] == getattr(click_cmd, "name", None)
            ):
                args_list = args_list[1:]
            exit_code = click_cmd.main(args=args_list, prog_name=prog_name, standalone_mode=False)
            if exit_code and exit_code != 0:
                raise SystemExit(exit_code)

        return click.Command(
            "__delegate__",
            callback=_invoke,
            params=[click.Argument(["args"], nargs=-1, type=click.UNPROCESSED)],
            context_settings={"ignore_unknown_options": True},
            add_help_option=False,  # Pass --help through to real Typer so "specfact backlog daily ado --help" shows correct usage
        )

    def resolve_command(
        self, ctx: click.Context, args: list[str]
    ) -> tuple[str | None, click.Command | None, list[str]]:
        # Pass through all args to the delegate so "plan init bundle" becomes args for the real plan Typer.
        if not args:
            return None, None, []
        return self._delegate_cmd.name, self._delegate_cmd, list(args)

    def list_commands(self, ctx: click.Context) -> list[str]:
        # Lazy-load real typer so help and completion show real subcommands.
        real_group = self._get_real_click_group()
        if real_group is not None:
            return list(real_group.commands.keys())
        return []

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        # Delegate to real typer so format_commands() can show each subcommand's help.
        real_group = self._get_real_click_group()
        if real_group is not None:
            return real_group.get_command(ctx, cmd_name)
        return None

    def _get_real_click_group(self) -> click.Group | None:
        """Load and return the real command's Click Group, or None on failure."""
        from typer.main import get_command

        real_typer = CommandRegistry.get_typer(self._lazy_cmd_name)
        click_cmd = get_command(real_typer)
        if isinstance(click_cmd, click.Group):
            return click_cmd
        return None

    def format_help(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        """Show the real Typer's Rich help instead of plain Click group help."""
        from typer.main import get_command

        real_typer = CommandRegistry.get_typer(self._lazy_cmd_name)
        click_cmd = get_command(real_typer)
        prog_name = (
            f"{ctx.parent.command.name} {self._lazy_cmd_name}"
            if ctx.parent and ctx.parent.command
            else self._lazy_cmd_name
        )
        try:
            click_cmd.main(args=["-h"], prog_name=prog_name, standalone_mode=False)
        except SystemExit:
            raise  # Re-raise so process exits (help was already printed with Rich)
        # main() returned without exiting; Rich help was already printed, skip default formatter
        return


def _build_lazy_delegate_group(cmd_name: str, help_str: str) -> click.Group:
    """Build a Click Group that delegates to the real command with full args."""
    return _LazyDelegateGroup(cmd_name, help_str, name=cmd_name, help=help_str)


def _make_lazy_typer(cmd_name: str, help_str: str) -> typer.Typer:
    """Return a Typer that, when built as Click, becomes a LazyDelegateGroup (see patched get_command)."""
    lazy = typer.Typer(invoke_without_command=True, help=help_str)
    lazy._specfact_lazy_delegate = True
    lazy._specfact_lazy_cmd_name = cmd_name
    lazy._specfact_lazy_help_str = help_str
    return lazy


def _get_command(typer_instance: typer.Typer) -> click.Command:
    """Wrapper around typer.main.get_command that returns LazyDelegateGroup for our lazy typers."""
    if getattr(typer_instance, "_specfact_lazy_delegate", False):
        cmd_name = getattr(typer_instance, "_specfact_lazy_cmd_name", "")
        help_str = getattr(typer_instance, "_specfact_lazy_help_str", "")
        return _build_lazy_delegate_group(cmd_name, help_str)
    assert _typer_get_command_original is not None
    return _typer_get_command_original(typer_instance)


def _get_group_from_info_wrapper(
    group_info: object,
    *,
    pretty_exceptions_short: bool,
    suggest_commands: bool,
    rich_markup_mode: object,
) -> click.Group:
    """Wrapper around typer.main.get_group_from_info that uses LazyDelegateGroup for our lazy typers."""
    # TyperInfo has typer_instance and name
    typer_instance = getattr(group_info, "typer_instance", None)
    name = getattr(group_info, "name", None)
    if typer_instance is not None and getattr(typer_instance, "_specfact_lazy_delegate", False):
        cmd_name = getattr(typer_instance, "_specfact_lazy_cmd_name", "") or (name or "")
        help_str = getattr(typer_instance, "_specfact_lazy_help_str", "")
        return _build_lazy_delegate_group(cmd_name, help_str)
    assert _typer_get_group_from_info_original is not None
    return _typer_get_group_from_info_original(
        group_info,
        pretty_exceptions_short=pretty_exceptions_short,
        suggest_commands=suggest_commands,
        rich_markup_mode=rich_markup_mode,
    )


# Original Typer build functions (set once by _patch_typer_build so re-import of cli doesn't overwrite with our wrapper).
_typer_get_group_from_info_original: Callable[..., click.Group] | None = None
_typer_get_command_original: Callable[[typer.Typer], click.Command] | None = None


# Patch so root app build uses our delegate group for lazy typers (built via get_group_from_info).
def _patch_typer_build() -> None:
    import typer.main as typer_main

    global _typer_get_group_from_info_original, _typer_get_command_original
    # Save originals only on first patch; avoid overwriting with our wrapper when cli is re-imported (e.g. by plan module).
    if _typer_get_group_from_info_original is None:
        _typer_get_group_from_info_original = typer_main.get_group_from_info
    if _typer_get_command_original is None:
        _typer_get_command_original = typer_main.get_command
    typer_main.get_command = _get_command
    typer_main.get_group_from_info = _get_group_from_info_wrapper


register_builtin_commands()
_patch_typer_build()


def _grouped_command_order(
    commands: list[tuple[str, CommandMetadata]],
) -> list[tuple[str, CommandMetadata]]:
    """Keep registration order while grouping extension commands after their base group."""
    names = {name for name, _meta in commands}
    base_commands: list[tuple[str, CommandMetadata]] = []
    extension_by_base: dict[str, list[tuple[str, CommandMetadata]]] = {}
    orphan_extensions: list[tuple[str, CommandMetadata]] = []

    for name, meta in commands:
        if "-" not in name:
            base_commands.append((name, meta))
            continue
        base_name = name.split("-", 1)[0]
        if base_name in names:
            extension_by_base.setdefault(base_name, []).append((name, meta))
        else:
            orphan_extensions.append((name, meta))

    ordered: list[tuple[str, CommandMetadata]] = []
    for name, meta in base_commands:
        ordered.append((name, meta))
        ordered.extend(extension_by_base.get(name, []))
    ordered.extend(orphan_extensions)
    return ordered


for _name, _meta in _grouped_command_order(CommandRegistry.list_commands_for_help()):
    app.add_typer(_make_lazy_typer(_name, _meta.help), name=_name, help=_meta.help)


def cli_main() -> None:
    """Entry point for the CLI application."""
    # Intercept --help-advanced before Typer processes it
    from specfact_cli.utils.progressive_disclosure import intercept_help_advanced

    intercept_help_advanced()

    # Normalize shell names in argv for Typer's built-in completion commands
    normalize_shell_in_argv()

    # Initialize debug mode early so --debug works even for eager flags like --help/--version.
    debug_requested = "--debug" in sys.argv[1:]
    if debug_requested:
        set_debug_mode(True)
        init_debug_log_file()
        debug_log_path = runtime.get_debug_log_path()
        if debug_log_path:
            sys.stderr.write(f"[debug] log file: {debug_log_path}\n")
        else:
            sys.stderr.write("[debug] log file unavailable (no writable debug log path)\n")
        runtime.debug_log_operation(
            "cli_start",
            "specfact",
            "started",
            extra={"argv": sys.argv[1:], "pid": os.getpid()},
        )

    # Check if --banner flag is present (before Typer processes it)
    banner_requested = "--banner" in sys.argv

    # Check if this is first run (no ~/.specfact folder exists)
    # Use Path.home() directly to avoid importing metadata module (which creates the directory)
    specfact_dir = Path.home() / ".specfact"
    is_first_run = not specfact_dir.exists()

    # Show banner if:
    # 1. --banner flag is explicitly requested, OR
    # 2. This is the first run (no ~/.specfact folder exists)
    # Otherwise, show simple version line
    show_banner = banner_requested or is_first_run

    # Intercept Typer's shell detection for --show-completion and --install-completion
    # when no shell is provided (auto-detection case)
    # On Ubuntu, shellingham detects "sh" (dash) instead of "bash", so we force "bash"
    if len(sys.argv) >= 2 and sys.argv[1] in ("--show-completion", "--install-completion") and len(sys.argv) == 2:
        # Auto-detection case: Typer will use shellingham to detect shell
        # On Ubuntu, this often detects "sh" (dash) instead of "bash"
        # Force "bash" if SHELL env var suggests bash/sh to avoid "sh not supported" error
        shell_env = os.environ.get("SHELL", "").lower()
        if "sh" in shell_env or "bash" in shell_env:
            # Force bash by adding it to argv before Typer's auto-detection runs
            sys.argv.append("bash")

    # Intercept completion environment variable and normalize shell names
    # (This handles completion scripts generated by Typer's built-in commands)
    completion_env = os.environ.get("_SPECFACT_COMPLETE")
    if completion_env:
        # Extract shell name from completion env var (format: "shell_source" or "shell")
        shell_name = completion_env[:-7] if completion_env.endswith("_source") else completion_env

        # Normalize shell name using our mapping
        shell_normalized = shell_name.lower().strip()
        mapped_shell = SHELL_MAP.get(shell_normalized, shell_normalized)

        # Update environment variable with normalized shell name
        if mapped_shell != shell_normalized:
            if completion_env.endswith("_source"):
                os.environ["_SPECFACT_COMPLETE"] = f"{mapped_shell}_source"
            else:
                os.environ["_SPECFACT_COMPLETE"] = mapped_shell

    # Show banner or version line before Typer processes the command
    # Skip for help/version/completion commands and in test mode to avoid cluttering output
    skip_output_commands = ("--help", "-h", "--version", "-v", "--show-completion", "--install-completion")
    is_help_or_version = any(arg in skip_output_commands for arg in sys.argv[1:])
    # Check test mode using same pattern as terminal.py
    is_test_mode = os.environ.get("TEST_MODE") == "true" or os.environ.get("PYTEST_CURRENT_TEST") is not None

    if show_banner and not is_help_or_version and not is_test_mode:
        print_banner()
        console.print()  # Empty line after banner
    elif not is_help_or_version and not is_test_mode:
        # Show simple version line like other CLIs (skip for help/version commands and in test mode)
        # Printed before startup checks so users see output immediately (important with slow checks e.g. xagt)
        print_version_line()

    # Run startup checks (template validation and version check)
    # Only run for actual commands, not for help/version/completion
    should_run_checks = (
        len(sys.argv) > 1
        and sys.argv[1] not in ("--help", "-h", "--version", "-v", "--show-completion", "--install-completion")
        and not sys.argv[1].startswith("_")  # Skip completion internals
    )
    if should_run_checks:
        from specfact_cli.utils.startup_checks import print_startup_checks

        # Determine repo path (use current directory or find from git root)
        repo_path = Path.cwd()
        # Try to find git root
        current = repo_path
        while current.parent != current:
            if (current / ".git").exists():
                repo_path = current
                break
            current = current.parent

        # Run checks (version check may be slow, so we do it async or with timeout)
        import contextlib

        # Check if --skip-checks flag is present
        skip_checks_flag = "--skip-checks" in sys.argv

        with contextlib.suppress(Exception):
            print_startup_checks(repo_path=repo_path, check_version=True, skip_checks=skip_checks_flag)

    # Record start time for command execution
    start_time = datetime.now()
    start_timestamp = start_time.strftime("%Y-%m-%d %H:%M:%S")

    # Only show timing for actual commands (not help, version, or completion)
    show_timing = (
        len(sys.argv) > 1
        and sys.argv[1] not in ("--help", "-h", "--version", "-v", "--show-completion", "--install-completion")
        and not sys.argv[1].startswith("_")  # Skip completion internals
    )

    if show_timing:
        console.print(f"[dim]⏱️  Started: {start_timestamp}[/dim]")

    exit_code = 0
    timing_shown = False  # Track if timing was already shown (for typer.Exit case)
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        exit_code = 130
    except typer.Exit as e:
        # Typer.Exit is used for clean exits (e.g., --version, --help)
        exit_code = e.exit_code if hasattr(e, "exit_code") else 0
        # Show timing before re-raising (finally block will execute, but we show it here to ensure it's shown)
        if show_timing:
            end_time = datetime.now()
            end_timestamp = end_time.strftime("%Y-%m-%d %H:%M:%S")
            duration = end_time - start_time
            duration_seconds = duration.total_seconds()

            # Format duration nicely
            if duration_seconds < 60:
                duration_str = f"{duration_seconds:.2f}s"
            elif duration_seconds < 3600:
                minutes = int(duration_seconds // 60)
                seconds = duration_seconds % 60
                duration_str = f"{minutes}m {seconds:.2f}s"
            else:
                hours = int(duration_seconds // 3600)
                minutes = int((duration_seconds % 3600) // 60)
                seconds = duration_seconds % 60
                duration_str = f"{hours}h {minutes}m {seconds:.2f}s"

            status_icon = "✓" if exit_code == 0 else "✗"
            console.print(f"\n[dim]{status_icon} Finished: {end_timestamp} | Duration: {duration_str}[/dim]")
            timing_shown = True
        raise  # Re-raise to let Typer handle it properly
    except ViolationError as e:
        # Extract user-friendly error message from ViolationError
        error_msg = str(e)
        # Try to extract the contract message (after ":\n")
        if ":\n" in error_msg:
            contract_msg = error_msg.split(":\n", 1)[0]
            console.print(f"[bold red]✗[/bold red] {contract_msg}", style="red")
        else:
            console.print(f"[bold red]✗[/bold red] {error_msg}", style="red")
        exit_code = 1
    except Exception as e:
        # Escape any Rich markup in the error message to prevent markup errors
        error_str = str(e).replace("[", "\\[").replace("]", "\\]")
        console.print(f"[bold red]Error:[/bold red] {error_str}", style="red")
        exit_code = 1
    finally:
        # Record end time and display timing information (if not already shown)
        if show_timing and not timing_shown:
            end_time = datetime.now()
            end_timestamp = end_time.strftime("%Y-%m-%d %H:%M:%S")
            duration = end_time - start_time
            duration_seconds = duration.total_seconds()

            # Format duration nicely
            if duration_seconds < 60:
                duration_str = f"{duration_seconds:.2f}s"
            elif duration_seconds < 3600:
                minutes = int(duration_seconds // 60)
                seconds = duration_seconds % 60
                duration_str = f"{minutes}m {seconds:.2f}s"
            else:
                hours = int(duration_seconds // 3600)
                minutes = int((duration_seconds % 3600) // 60)
                seconds = duration_seconds % 60
                duration_str = f"{hours}h {minutes}m {seconds:.2f}s"

            # Show timing summary
            status_icon = "✓" if exit_code == 0 else "✗"
            status_color = "green" if exit_code == 0 else "red"
            console.print(
                f"\n[dim]{status_icon} Finished: {end_timestamp} | Duration: {duration_str}[/dim]",
                style=status_color if exit_code != 0 else None,
            )

    if exit_code != 0:
        sys.exit(exit_code)


if __name__ == "__main__":
    cli_main()

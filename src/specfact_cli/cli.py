"""
SpecFact CLI - Main application entry point.

This module defines the main Typer application and registers all command groups.
"""

from __future__ import annotations

import importlib
import inspect
import os
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any, NoReturn, cast


_DetectShellFn = Callable[..., tuple[str | None, str | None]]

# Patch shellingham before Typer imports it to normalize "sh" to "bash"
# This fixes auto-detection on Ubuntu where /bin/sh points to dash
try:
    import shellingham

    # Store original function
    _original_detect_shell: _DetectShellFn = cast(_DetectShellFn, shellingham.detect_shell)

    def _normalized_detect_shell(pid: int | None = None, max_depth: int = 10) -> tuple[str | None, str | None]:
        """Normalized shell detection that maps 'sh' to 'bash'."""
        shell_name, shell_path = _original_detect_shell(pid, max_depth)
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
from icontract import ViolationError, ensure, require
from rich.panel import Panel

from specfact_cli import __version__, runtime
from specfact_cli.modes import OperationalMode, detect_mode

# Command groups are registered via CommandRegistry (bootstrap); no top-level command imports.
from specfact_cli.registry import CommandRegistry
from specfact_cli.registry.alias_manager import resolve_command
from specfact_cli.registry.bootstrap import register_builtin_commands
from specfact_cli.registry.metadata import CommandMetadata
from specfact_cli.registry.module_availability import ModuleAvailabilityStatus, classify_module_availability
from specfact_cli.runtime import get_configured_console, init_debug_log_file, set_debug_mode
from specfact_cli.utils.progressive_disclosure import ProgressiveDisclosureGroup
from specfact_cli.utils.structured_io import StructuredFormat


# Names of commands that come from installable bundles; when not registered, show actionable error.
KNOWN_BUNDLE_GROUP_OR_SHIM_NAMES: frozenset[str] = frozenset(
    {
        "backlog",
        "code",
        "project",
        "spec",
        "govern",
        "plan",
        "validate",
        "contract",
        "sdd",
        "generate",
        "enforce",
        "patch",
        "migrate",
        "repro",
        "drift",
        "analyze",
        "policy",
        "sync",
    }
)

# First token -> official marketplace module that provides it (not the VS Code `code` CLI).
# Codebase import is `specfact code import`; persona Markdown import is `specfact project import` (not flat).
_INVOKED_TO_MARKETPLACE_MODULE: dict[str, str] = {
    "backlog": "nold-ai/specfact-backlog",
    "policy": "nold-ai/specfact-backlog",
    "code": "nold-ai/specfact-codebase",
    "analyze": "nold-ai/specfact-codebase",
    "drift": "nold-ai/specfact-codebase",
    "validate": "nold-ai/specfact-codebase",
    "repro": "nold-ai/specfact-codebase",
    "project": "nold-ai/specfact-project",
    "plan": "nold-ai/specfact-project",
    "sync": "nold-ai/specfact-project",
    "migrate": "nold-ai/specfact-project",
    "spec": "nold-ai/specfact-spec",
    "contract": "nold-ai/specfact-spec",
    "sdd": "nold-ai/specfact-spec",
    "generate": "nold-ai/specfact-spec",
    "govern": "nold-ai/specfact-govern",
    "enforce": "nold-ai/specfact-govern",
    "patch": "nold-ai/specfact-govern",
}


def _print_missing_bundle_command_help(invoked: str) -> None:
    """Print install guidance when a bundle group or shim is not registered."""
    module_id = _INVOKED_TO_MARKETPLACE_MODULE.get(invoked)
    console = get_configured_console()
    if module_id is not None:
        availability = classify_module_availability(module_id=module_id, command_name=invoked)
        if availability.status is ModuleAvailabilityStatus.DISABLED:
            console.print(
                f"[bold red]Module '{availability.module_id or module_id}' is installed but disabled.[/bold red]\n"
                f"The [bold]{invoked}[/bold] command group is provided by that module. "
                f"Enable with [bold]{availability.recovery_command}[/bold]."
            )
            return
        if availability.status is ModuleAvailabilityStatus.SKIPPED:
            console.print(
                f"[bold red]Module '{availability.module_id or module_id}' is installed but skipped.[/bold red]\n"
                f"Reason: {availability.reason}. "
                "Inspect with [bold]specfact module list --show-origin[/bold]."
            )
            return
        if availability.status is ModuleAvailabilityStatus.SHADOWED:
            console.print(
                f"[bold red]Module '{availability.module_id or module_id}' is shadowed in this workspace.[/bold red]\n"
                f"Shadowed by: {availability.shadowed_by}. "
                "Inspect with [bold]specfact module list --show-origin[/bold]."
            )
            return
        console.print(
            f"[bold red]Module '{module_id}' is not installed.[/bold red]\n"
            f"The [bold]{invoked}[/bold] command group is provided by that module. "
            f"Install with [bold]specfact module install {module_id}[/bold], "
            "or run [bold]specfact init --profile <profile>[/bold] to install bundles."
        )
        return
    console.print(
        f"[bold red]Command '{invoked}' is not installed.[/bold red]\n"
        "Install workflow bundles with [bold]specfact init --profile <profile>[/bold] "
        "or [bold]specfact module install <bundle>[/bold]."
    )


class _RootCLIGroup(ProgressiveDisclosureGroup):
    """Root group that shows actionable error when an unknown command is a known bundle group/shim."""

    @ensure(lambda result: isinstance(result, tuple) and len(result) == 3, "result must be a 3-tuple")
    def resolve_command(
        self, ctx: click.Context, args: list[str]
    ) -> tuple[str | None, click.Command | None, list[str]]:
        if not args:
            return super().resolve_command(ctx, args)
        invoked = args[0]
        try:
            result = super().resolve_command(ctx, args)
        except click.UsageError:
            if invoked in KNOWN_BUNDLE_GROUP_OR_SHIM_NAMES:
                _print_missing_bundle_command_help(invoked)
                raise SystemExit(1) from None
            raise
        except ValueError as exc:
            if invoked in KNOWN_BUNDLE_GROUP_OR_SHIM_NAMES:
                _print_missing_bundle_command_help(invoked)
                raise SystemExit(1) from exc
            raise
        _name, cmd, remaining = result
        if cmd is not None or not remaining:
            return result
        invoked = remaining[0]
        if invoked not in KNOWN_BUNDLE_GROUP_OR_SHIM_NAMES:
            return result
        _print_missing_bundle_command_help(invoked)
        raise SystemExit(1)


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


@beartype
@ensure(lambda: isinstance(sys.argv, list), "sys.argv must remain a list after normalization")
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
    cls=_RootCLIGroup,  # Progressive disclosure + actionable error for unknown bundle commands
)

console = get_configured_console()

# Global mode context (set by --mode flag or auto-detected)
_current_mode: OperationalMode | None = None

# Global banner flag (set by --banner flag)
_show_banner: bool = False


@beartype
@ensure(lambda: console is not None, "console must be configured before printing banner")
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


@beartype
@require(
    lambda: __version__ is not None and len(__version__) > 0, "__version__ must be set before printing version line"
)
def print_version_line() -> None:
    """Print simple version line like other CLIs."""
    console.print(f"[dim]SpecFact CLI - v{__version__}[/dim]")


@beartype
@require(lambda value: value is None or isinstance(value, bool), "value must be bool or None")
def version_callback(value: bool | None) -> None:
    """Show version information."""
    if value:
        console.print(f"[bold cyan]SpecFact CLI[/bold cyan] version [green]{__version__}[/green]")
        raise typer.Exit()


@beartype
@require(lambda value: value is None or len(value) > 0, "value must be non-empty if provided")
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
@ensure(lambda result: result is not None, "operational mode must not be None")
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


@dataclass
class _RootCliFlags:
    """Bundled root callback options (keeps the Typer callback body small for radon-kiss)."""

    version: bool | None
    banner: bool
    mode: str | None
    debug: bool
    skip_checks: bool
    input_format: StructuredFormat
    output_format: StructuredFormat
    interaction: bool | None


_ROOT_MAIN_DOC = """
SpecFact CLI - Spec→Contract→Sentinel for contract-driven development.

Transform your development workflow with automated quality gates,
runtime contract validation, and state machine workflows.

Run **specfact init** or **specfact module install** to add workflow bundles
(backlog, code, project, spec, govern).

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


def _apply_root_app_callback(ctx: typer.Context, flags: _RootCliFlags) -> None:
    global _show_banner
    global console

    # Rebind root and loaded module consoles for each invocation to avoid stale
    # closed capture streams across sequential CliRunner/pytest command runs.
    console = get_configured_console()
    runtime.refresh_loaded_module_consoles()

    # Set banner flag based on --banner option
    _show_banner = flags.banner

    # Set debug mode
    set_debug_mode(flags.debug)
    if flags.debug:
        init_debug_log_file()

    runtime.configure_io_formats(input_format=flags.input_format, output_format=flags.output_format)
    # Invert logic: --interactive means not non-interactive, --no-interactive means non-interactive
    if flags.interaction is not None:
        runtime.set_non_interactive_override(not flags.interaction)
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


def _root_cli_flags_from_kwargs(kwargs: Mapping[str, Any]) -> _RootCliFlags:
    """Build flags from Typer callback kwargs (param names match merged root CLI signature)."""
    return _RootCliFlags(
        version=kwargs.get("version"),
        banner=kwargs.get("banner", False),
        mode=kwargs.get("mode"),
        debug=kwargs.get("debug", False),
        skip_checks=kwargs.get("skip_checks", False),
        input_format=kwargs.get("input_format", StructuredFormat.YAML),
        output_format=kwargs.get("output_format", StructuredFormat.YAML),
        interaction=kwargs.get("interaction"),
    )


def _root_sig_part1(
    ctx: typer.Context,
    version: bool | None = typer.Option(
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
) -> None:
    """Typer param signature fragment (merged for root callback); not invoked at runtime."""


def _root_sig_part2(
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
) -> None:
    """Typer param signature fragment (merged for root callback); not invoked at runtime."""


def _root_sig_part3(
    interaction: Annotated[
        bool | None,
        typer.Option(
            "--interactive/--no-interactive",
            help="Force interaction mode (default auto based on terminal/CI detection)",
        ),
    ] = None,
) -> None:
    """Typer param signature fragment (merged for root callback); not invoked at runtime."""


def _merge_root_cli_param_specs(orig: Callable[..., Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    merged.update(orig(_root_sig_part1))
    merged.update(orig(_root_sig_part2))
    merged.update(orig(_root_sig_part3))
    return merged


@app.callback(invoke_without_command=True)
@require(lambda ctx: ctx is not None, "ctx must not be None")
def main(ctx: typer.Context, **kwargs) -> None:
    """SpecFact CLI root callback (full help text in _ROOT_MAIN_DOC)."""
    _apply_root_app_callback(ctx, _root_cli_flags_from_kwargs(kwargs))


main.__doc__ = inspect.cleandoc(_ROOT_MAIN_DOC)


# Register command groups from CommandRegistry (bootstrap preserves display order).
# Use a custom Click Group so that "specfact plan init ..." passes full args to the real plan
# Typer (no "No such command 'init'" from an empty group).
# Global options (e.g. --no-interactive, --debug) must be passed before the command: specfact [OPTIONS] COMMAND [ARGS]...


def _lazy_delegate_cmd_name_ready(self: _LazyDelegateGroup) -> bool:
    return len(self._lazy_cmd_name) > 0


def _args_request_help(args: tuple[str, ...] | list[str]) -> bool:
    """Return True when delegated args are asking only for command help."""
    return any(arg in ("--help", "-h", "--help-advanced", "-ha") for arg in args)


def _delegated_help_path(cmd_name: str, args: tuple[str, ...] | list[str]) -> str:
    """Build a stable command path for fallback help output."""
    path_parts = [cmd_name]
    for arg in args:
        if arg.startswith("-"):
            continue
        path_parts.append(arg)
    return " ".join(path_parts)


def _print_lazy_help_fallback(cmd_name: str, args: tuple[str, ...] | list[str]) -> None:
    """Print minimal help when Typer cannot materialize a command for a loaded bundle."""
    command_path = _delegated_help_path(cmd_name, args)
    get_configured_console().print(
        f"[bold]{command_path}[/bold]\n\n"
        "Help is available for this installed command path, but the command metadata could not be "
        "materialized in this runtime. Reinstall the providing module or run the command without "
        "`--help` to execute it."
    )


def _raise_lazy_delegate_click_exception(exc: Exception) -> NoReturn:
    raise click.ClickException(str(exc)) from exc


def _load_lazy_delegate_typer(cmd_name: str) -> typer.Typer:
    resolved_name = resolve_command(cmd_name)
    try:
        return CommandRegistry.get_typer(resolved_name)
    except ValueError as exc:
        if cmd_name in KNOWN_BUNDLE_GROUP_OR_SHIM_NAMES:
            _print_missing_bundle_command_help(cmd_name)
            raise SystemExit(1) from None
        _raise_lazy_delegate_click_exception(exc)
        raise AssertionError("unreachable") from None


def _build_lazy_delegate_click_command(cmd_name: str, args: tuple[str, ...], real_typer: typer.Typer) -> click.Command:
    from typer.main import get_command

    try:
        return get_command(real_typer)
    except (RuntimeError, ValueError) as exc:
        if _args_request_help(args):
            _print_lazy_help_fallback(cmd_name, args)
            raise SystemExit(0) from None
        _raise_lazy_delegate_click_exception(exc)
        raise AssertionError("unreachable") from None


def _lazy_delegate_prog_name(ctx: click.Context, cmd_name: str) -> str:
    parts: list[str] = []
    parent = ctx.parent
    while parent and getattr(parent, "command", None):
        name = getattr(parent.command, "name", None)
        if name and name != "__delegate__":
            parts.append(name)
        parent = getattr(parent, "parent", None)
    if parts:
        return " ".join(reversed(parts))
    original_prog_name = ctx.meta.get("original_prog_name")
    if isinstance(original_prog_name, str) and original_prog_name:
        return original_prog_name
    return cmd_name


def _strip_redundant_single_command_arg(click_cmd: click.Command, args: tuple[str, ...]) -> list[str]:
    args_list = list(args)
    if not isinstance(click_cmd, click.Group) and args_list and args_list[0] == getattr(click_cmd, "name", None):
        return args_list[1:]
    return args_list


def _lazy_delegate_remaining_args(ctx: click.Context) -> list[str]:
    ctx_state = vars(ctx)
    protected_args = ctx_state.get("_protected_args") or ctx_state.get("protected_args") or ()
    return [str(arg) for arg in (*protected_args, *ctx.args)]


class _LazyDelegateGroup(click.Group):
    """Click Group that delegates all args to the real command (lazy-loaded)."""

    _lazy_cmd_name: str
    _lazy_help_str: str
    _delegate_cmd: click.Command

    def __init__(self, cmd_name: str, help_str: str, name: str | None = None, help: str | None = None) -> None:
        super().__init__(
            name=name or cmd_name,
            help=help or help_str,
            context_settings={"ignore_unknown_options": True},
            invoke_without_command=True,
            no_args_is_help=False,
        )
        self._lazy_cmd_name = cmd_name
        self._lazy_help_str = help_str
        self._delegate_cmd = self._make_delegate_command()

    def _make_delegate_command(self) -> click.Command:
        cmd_name = self._lazy_cmd_name

        def _invoke(args: tuple[str, ...]) -> None:
            ctx = click.get_current_context()
            real_typer = _load_lazy_delegate_typer(cmd_name)
            click_cmd = _build_lazy_delegate_click_command(cmd_name, args, real_typer)
            # Build full prog name from root (e.g. "specfact sync") so usage shows "specfact sync bridge", not "sync sync bridge"
            prog_name = _lazy_delegate_prog_name(ctx, cmd_name)
            # When the real app is a single command (e.g. drift has only "detect"), Typer
            # builds a TyperCommand, not a Group. Then args are ["detect", "bundle", "--repo", ...]
            # and the command expects ["bundle", "--repo", ...] (no leading "detect").
            args_list = _strip_redundant_single_command_arg(click_cmd, args)
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

    @require(lambda ctx: ctx is not None, "ctx must not be None")
    @ensure(lambda result: result is None or isinstance(result, int), "result must be None or an exit code")
    def invoke(self, ctx: click.Context) -> Any:
        if ctx.invoked_subcommand is None:
            args = _lazy_delegate_remaining_args(ctx)
            ctx.meta["original_prog_name"] = ctx.command_path
            return self._delegate_cmd.main(args=args, prog_name=ctx.command_path, standalone_mode=False)
        return super().invoke(ctx)

    @require(_lazy_delegate_cmd_name_ready, "lazy command name must be set")
    @ensure(lambda result: isinstance(result, tuple) and len(result) == 3, "result must be a 3-tuple")
    def resolve_command(
        self, ctx: click.Context, args: list[str]
    ) -> tuple[str | None, click.Command | None, list[str]]:
        # Pass through all args to the delegate so "plan init bundle" becomes args for the real plan Typer.
        if not args:
            return self._delegate_cmd.name, self._delegate_cmd, []
        return self._delegate_cmd.name, self._delegate_cmd, list(args)

    @ensure(lambda result: isinstance(result, list), "result must be a list of command names")
    def list_commands(self, ctx: click.Context) -> list[str]:
        # Lazy-load real typer so help and completion show real subcommands.
        real_group = self._get_real_click_group()
        if real_group is not None:
            return list(real_group.commands.keys())
        return []

    @require(lambda self, cmd_name: cmd_name is not None and len(cmd_name) > 0, "cmd_name must be non-empty")
    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        # Delegate to real typer so format_commands() can show each subcommand's help.
        real_group = self._get_real_click_group()
        if real_group is not None:
            return real_group.get_command(ctx, cmd_name)
        return None

    def _get_real_click_group(self) -> click.Group | None:
        """Load and return the real command's Click Group, or None on failure."""
        from typer.main import get_command

        resolved_name = resolve_command(self._lazy_cmd_name)
        try:
            real_typer = CommandRegistry.get_typer(resolved_name)
            click_cmd = get_command(real_typer)
        except (RuntimeError, ValueError):
            return None
        if isinstance(click_cmd, click.Group):
            return click_cmd
        return None

    @require(_lazy_delegate_cmd_name_ready, "lazy command name must be set before formatting help")
    def format_help(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        """Show the real Typer's Rich help instead of plain Click group help."""
        from typer.main import get_command

        resolved_name = resolve_command(self._lazy_cmd_name)
        try:
            real_typer = CommandRegistry.get_typer(resolved_name)
            click_cmd = get_command(real_typer)
        except (RuntimeError, ValueError):
            return
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


def _flatten_specfact_nested_subgroup(result: click.Group, flatten_name: str) -> None:
    """Merge a nested subgroup named `flatten_name` into its parent and re-sort command order."""
    redundant = result.commands.pop(flatten_name)
    if isinstance(redundant, click.Group):
        for cmd_name, cmd in redundant.commands.items():
            result.add_command(cmd, name=cmd_name)
    if result.commands:
        for cname in sorted(result.commands.keys()):
            cmd = result.commands.pop(cname)
            result.add_command(cmd, name=cname)


def _make_lazy_typer(cmd_name: str, help_str: str) -> typer.Typer:
    """Return a Typer that, when built as Click, becomes a LazyDelegateGroup (see patched get_command)."""
    lazy = typer.Typer(invoke_without_command=True, help=help_str)
    lazy._specfact_lazy_delegate = True  # type: ignore[attr-defined]
    lazy._specfact_lazy_cmd_name = cmd_name  # type: ignore[attr-defined]
    lazy._specfact_lazy_help_str = help_str  # type: ignore[attr-defined]
    return lazy


def _get_command(typer_instance: typer.Typer) -> click.Command:
    """Wrapper around typer.main.get_command that returns LazyDelegateGroup for our lazy typers,
    and applies flatten-same-name for Typers with _specfact_flatten_same_name.
    """
    if getattr(typer_instance, "_specfact_lazy_delegate", False):
        cmd_name = getattr(typer_instance, "_specfact_lazy_cmd_name", "")
        help_str = getattr(typer_instance, "_specfact_lazy_help_str", "")
        return _build_lazy_delegate_group(cmd_name, help_str)
    assert _typer_get_command_original is not None
    result = _typer_get_command_original(typer_instance)
    flatten_name = getattr(typer_instance, "_specfact_flatten_same_name", None)
    if isinstance(flatten_name, str) and isinstance(result, click.Group) and flatten_name in result.commands:
        _flatten_specfact_nested_subgroup(result, flatten_name)
    return result


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
    result = _typer_get_group_from_info_original(
        group_info,
        pretty_exceptions_short=pretty_exceptions_short,
        suggest_commands=suggest_commands,
        rich_markup_mode=rich_markup_mode,
    )
    flatten_name = getattr(typer_instance, "_specfact_flatten_same_name", None) if typer_instance else None
    if isinstance(flatten_name, str) and flatten_name in result.commands:
        _flatten_specfact_nested_subgroup(result, flatten_name)
    return result


# Original Typer build functions (set once by _patch_typer_build so re-import of cli doesn't overwrite with our wrapper).
_typer_get_group_from_info_original: Callable[..., click.Group] | None = None
_typer_get_command_original: Callable[[typer.Typer], click.Command] | None = None
_typer_get_params_original: Callable[..., Any] | None = None


def _specfact_get_params_from_function(func: Callable[..., Any]) -> Any:
    """Map thin Typer entrypoints to their option-rich implementations for Click param generation."""
    orig = _typer_get_params_original
    if orig is None:
        import typer.utils as typer_utils

        return typer_utils.get_params_from_function(func)
    # ``@app.callback()`` / ``@app.command()`` may wrap the function; match by name + module.
    if getattr(func, "__name__", "") == "main" and getattr(func, "__module__", "") == __name__:
        return _merge_root_cli_param_specs(orig)
    if (
        getattr(func, "__name__", "") == "install"
        and getattr(func, "__module__", "") == "specfact_cli.modules.module_registry.src.commands"
    ):
        module = sys.modules.get("specfact_cli.modules.module_registry.src.commands")
        if module is not None:
            merge_install = getattr(module, "_specfact_merge_install_param_specs", None)
            if merge_install is not None:
                return merge_install(orig)
    return orig(func)


# Patch so root app build uses our delegate group for lazy typers (built via get_group_from_info).
def _patch_typer_build() -> None:
    import typer.utils as typer_utils

    typer_main = cast(Any, importlib.import_module("typer.main"))

    global _typer_get_group_from_info_original, _typer_get_command_original, _typer_get_params_original
    # Save originals only on first patch; avoid overwriting with our wrapper when cli is re-imported (e.g. by plan module).
    if _typer_get_group_from_info_original is None:
        _typer_get_group_from_info_original = typer_main.get_group_from_info
    if _typer_get_command_original is None:
        _typer_get_command_original = typer_main.get_command
    if _typer_get_params_original is None:
        _typer_get_params_original = typer_utils.get_params_from_function
    typer_utils.get_params_from_function = _specfact_get_params_from_function
    # typer.main may have bound get_params_from_function at import time; keep in sync.
    typer_main.get_params_from_function = _specfact_get_params_from_function
    typer_main.get_command = _get_command
    typer_main.get_group_from_info = _get_group_from_info_wrapper


_patch_typer_build()
register_builtin_commands()


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


@beartype
@require(lambda: isinstance(app, typer.Typer), "Root CLI app must be initialized")
@ensure(lambda result: result is None, "Must return None")
def rebuild_root_app_from_registry() -> None:
    """Rebuild root Typer ``app`` from the current ``CommandRegistry``.

    Call after ``register_builtin_commands()`` when tests clear and re-register the registry.
    Otherwise ``get_command(app)`` still reflects lazy groups from ``cli`` import time while
    ``CommandRegistry`` lists only the newly registered commands (breaks CI core-only installs).
    """
    app.registered_groups = []
    if hasattr(app, "registered_commands"):
        app.registered_commands = []
    for _name, _meta in _grouped_command_order(CommandRegistry.list_commands_for_help()):
        app.add_typer(_make_lazy_typer(_name, _meta.help), name=_name, help=_meta.help)


_CLI_SKIP_OUTPUT_ARGS: frozenset[str] = frozenset(
    ("--help", "-h", "--version", "-v", "--show-completion", "--install-completion")
)


def _cli_is_test_mode() -> bool:
    return os.environ.get("TEST_MODE") == "true" or os.environ.get("PYTEST_CURRENT_TEST") is not None


def _cli_argv_skips_pre_typer_output() -> bool:
    return any(arg in _CLI_SKIP_OUTPUT_ARGS for arg in sys.argv[1:])


def _cli_should_show_timing() -> bool:
    return len(sys.argv) > 1 and sys.argv[1] not in _CLI_SKIP_OUTPUT_ARGS and not sys.argv[1].startswith("_")


def _cli_init_debug_from_argv() -> None:
    debug_requested = "--debug" in sys.argv[1:]
    if not debug_requested:
        return
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


def _cli_patch_completion_argv() -> None:
    if len(sys.argv) >= 2 and sys.argv[1] in ("--show-completion", "--install-completion") and len(sys.argv) == 2:
        shell_env = os.environ.get("SHELL", "").lower()
        if "sh" in shell_env or "bash" in shell_env:
            sys.argv.append("bash")

    completion_env = os.environ.get("_SPECFACT_COMPLETE")
    if not completion_env:
        return
    shell_name = completion_env[:-7] if completion_env.endswith("_source") else completion_env
    shell_normalized = shell_name.lower().strip()
    mapped_shell = SHELL_MAP.get(shell_normalized, shell_normalized)
    if mapped_shell == shell_normalized:
        return
    if completion_env.endswith("_source"):
        os.environ["_SPECFACT_COMPLETE"] = f"{mapped_shell}_source"
    else:
        os.environ["_SPECFACT_COMPLETE"] = mapped_shell


def _cli_maybe_print_banner_or_version(*, show_banner: bool) -> None:
    if _cli_argv_skips_pre_typer_output() or _cli_is_test_mode():
        return
    if show_banner:
        print_banner()
        console.print()
        return
    print_version_line()


def _cli_find_repo_path_for_startup_checks() -> Path:
    repo_path = Path.cwd()
    current = repo_path
    while current.parent != current:
        if (current / ".git").exists():
            return current
        current = current.parent
    return repo_path


def _cli_run_startup_checks_if_needed() -> None:
    if len(sys.argv) <= 1 or sys.argv[1] in _CLI_SKIP_OUTPUT_ARGS or sys.argv[1].startswith("_"):
        return
    import contextlib

    from specfact_cli.utils.startup_checks import print_startup_checks

    repo_path = _cli_find_repo_path_for_startup_checks()
    skip_checks_flag = "--skip-checks" in sys.argv
    with contextlib.suppress(Exception):
        print_startup_checks(repo_path=repo_path, check_version=True, skip_checks=skip_checks_flag)


def _cli_format_duration_seconds(duration_seconds: float) -> str:
    if duration_seconds < 60:
        return f"{duration_seconds:.2f}s"
    if duration_seconds < 3600:
        minutes = int(duration_seconds // 60)
        seconds = duration_seconds % 60
        return f"{minutes}m {seconds:.2f}s"
    hours = int(duration_seconds // 3600)
    minutes = int((duration_seconds % 3600) // 60)
    seconds = duration_seconds % 60
    return f"{hours}h {minutes}m {seconds:.2f}s"


def _cli_print_timing_footer(
    *,
    start_time: datetime,
    end_time: datetime,
    exit_code: int,
    style_nonzero_exit: bool,
) -> None:
    end_timestamp = end_time.strftime("%Y-%m-%d %H:%M:%S")
    duration_seconds = (end_time - start_time).total_seconds()
    duration_str = _cli_format_duration_seconds(duration_seconds)
    status_icon = "✓" if exit_code == 0 else "✗"
    line = f"\n[dim]{status_icon} Finished: {end_timestamp} | Duration: {duration_str}[/dim]"
    if style_nonzero_exit and exit_code != 0:
        console.print(line, style="red")
    else:
        console.print(line)


def _cli_run_app_with_handling(*, start_time: datetime, show_timing: bool) -> int:
    exit_code = 0
    timing_shown = False
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        exit_code = 130
    except typer.Exit as e:
        exit_code = e.exit_code if hasattr(e, "exit_code") else 0
        if show_timing:
            _cli_print_timing_footer(
                start_time=start_time,
                end_time=datetime.now(),
                exit_code=exit_code,
                style_nonzero_exit=False,
            )
            timing_shown = True
        raise
    except ViolationError as e:
        error_msg = str(e)
        if ":\n" in error_msg:
            contract_msg = error_msg.split(":\n", 1)[0]
            console.print(f"[bold red]✗[/bold red] {contract_msg}", style="red")
        else:
            console.print(f"[bold red]✗[/bold red] {error_msg}", style="red")
        exit_code = 1
    except Exception as e:
        error_str = str(e).replace("[", "\\[").replace("]", "\\]")
        console.print(f"[bold red]Error:[/bold red] {error_str}", style="red")
        exit_code = 1
    finally:
        if show_timing and not timing_shown:
            _cli_print_timing_footer(
                start_time=start_time,
                end_time=datetime.now(),
                exit_code=exit_code,
                style_nonzero_exit=True,
            )
    return exit_code


@beartype
@require(lambda: len(sys.argv) >= 1, "sys.argv must be populated before CLI entry")
def cli_main() -> None:
    """Entry point for the CLI application."""
    from specfact_cli.utils.progressive_disclosure import intercept_help_advanced

    intercept_help_advanced()
    normalize_shell_in_argv()
    _cli_init_debug_from_argv()

    banner_requested = "--banner" in sys.argv
    specfact_dir = Path.home() / ".specfact"
    is_first_run = not specfact_dir.exists()
    show_banner = banner_requested or is_first_run

    _cli_patch_completion_argv()
    _cli_maybe_print_banner_or_version(show_banner=show_banner)
    _cli_run_startup_checks_if_needed()

    start_time = datetime.now()
    start_timestamp = start_time.strftime("%Y-%m-%d %H:%M:%S")
    show_timing = _cli_should_show_timing()
    if show_timing:
        console.print(f"[dim]⏱️  Started: {start_timestamp}[/dim]")

    exit_code = _cli_run_app_with_handling(start_time=start_time, show_timing=show_timing)
    if exit_code != 0:
        sys.exit(exit_code)


if __name__ == "__main__":
    cli_main()

"""
SpecFact CLI - Main application entry point.

This module defines the main Typer application and registers all command groups.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
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

import typer
from beartype import beartype
from icontract import ViolationError
from rich.console import Console
from rich.panel import Panel

from specfact_cli import __version__, runtime

# Import command modules
from specfact_cli.commands import (
    analyze,
    bridge,
    contract_cmd,
    drift,
    enforce,
    generate,
    implement,
    import_cmd,
    init,
    migrate,
    plan,
    project_cmd,
    repro,
    run,
    sdd,
    spec,
    sync,
)
from specfact_cli.modes import OperationalMode, detect_mode
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

console = Console()

# Global mode context (set by --mode flag or auto-detected)
_current_mode: OperationalMode | None = None

# Global banner flag (set by --no-banner flag)
_show_banner: bool = True


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
    no_banner: bool = typer.Option(
        False,
        "--no-banner",
        help="Hide ASCII art banner (useful for CI/CD)",
    ),
    mode: str | None = typer.Option(
        None,
        "--mode",
        callback=mode_callback,
        help="Operational mode: cicd (fast, deterministic) or copilot (enhanced, interactive)",
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
            help="Force interaction mode (default auto based on CI/CD detection)",
        ),
    ] = None,
) -> None:
    """
    SpecFact CLI - Spec→Contract→Sentinel for contract-driven development.

    Transform your development workflow with automated quality gates,
    runtime contract validation, and state machine workflows.

    Mode Detection:
    - Explicit --mode flag (highest priority)
    - Auto-detect from environment (CoPilot API, IDE integration)
    - Default to CI/CD mode
    """
    global _show_banner
    # Set banner flag based on --no-banner option
    _show_banner = not no_banner

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


# Register command groups in logical workflow order
# 1. Setup & Initialization
app.add_typer(init.app, name="init", help="Initialize SpecFact for IDE integration")

# 2. Import & Analysis
app.add_typer(
    import_cmd.app, name="import", help="Import codebases and external tool projects (e.g., Spec-Kit, Linear, Jira)"
)

# 2.5. Migration
app.add_typer(migrate.app, name="migrate", help="Migrate project bundles between formats")

# 3. Planning
app.add_typer(plan.app, name="plan", help="Manage development plans")

# 3.5. Project Bundle Management
app.add_typer(project_cmd.app, name="project", help="Manage project bundles with persona workflows")

# 4. Code Generation
app.add_typer(generate.app, name="generate", help="Generate artifacts from SDD and plans")

# 5. Code Implementation
app.add_typer(implement.app, name="implement", help="Execute tasks and generate code")

# 6. Quality Enforcement
app.add_typer(enforce.app, name="enforce", help="Configure quality gates")

# 7. Workflow Orchestration
app.add_typer(run.app, name="run", help="Orchestrate end-to-end workflows")

# 8. Validation
app.add_typer(repro.app, name="repro", help="Run validation suite")

# 9. SDD Management
app.add_typer(sdd.app, name="sdd", help="Manage SDD (Spec-Driven Development) manifests")

# 10. API Contract Testing
app.add_typer(spec.app, name="spec", help="Specmatic integration for API contract testing")

# 10.5. OpenAPI Contract Management
app.add_typer(contract_cmd.app, name="contract", help="Manage OpenAPI contracts for project bundles")

# 11. Synchronization
app.add_typer(sync.app, name="sync", help="Synchronize Spec-Kit artifacts and repository changes")

# 11.5. Drift Detection
app.add_typer(drift.app, name="drift", help="Detect drift between code and specifications")

# 11.6. Analysis
app.add_typer(analyze.app, name="analyze", help="Analyze codebase for contract coverage and quality")

# 12. External Tool Integration
app.add_typer(
    bridge.bridge_app,
    name="bridge",
    help="Bridge adapters for external tool integration (Spec-Kit, Linear, Jira, etc.)",
)


def cli_main() -> None:
    """Entry point for the CLI application."""
    # Intercept --help-advanced before Typer processes it
    from specfact_cli.utils.progressive_disclosure import intercept_help_advanced

    intercept_help_advanced()

    # Normalize shell names in argv for Typer's built-in completion commands
    normalize_shell_in_argv()

    # Check if --no-banner flag is present (before Typer processes it)
    no_banner_requested = "--no-banner" in sys.argv

    # Show banner by default unless --no-banner is specified
    # Banner shows for: no args, --help/-h, or any command (unless --no-banner)
    show_banner = not no_banner_requested

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

    # Show banner by default (unless --no-banner is specified)
    # Only show once, before Typer processes the command
    if show_banner:
        print_banner()
        console.print()  # Empty line after banner

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

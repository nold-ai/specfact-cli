"""
SpecFact CLI - Main application entry point.

This module defines the main Typer application and registers all command groups.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

import typer
from beartype import beartype
from icontract import ViolationError
from rich.console import Console
from rich.panel import Panel

from specfact_cli import __version__

# Import command modules
from specfact_cli.commands import enforce, import_cmd, init, plan, repro, sync
from specfact_cli.modes import OperationalMode, detect_mode

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
    """Normalize shell names in sys.argv before Typer processes them."""
    if len(sys.argv) >= 3:
        # Check for --show-completion or --install-completion
        if sys.argv[1] in ("--show-completion", "--install-completion"):
            shell_arg = sys.argv[2]
            shell_normalized = shell_arg.lower().strip()
            mapped_shell = SHELL_MAP.get(shell_normalized)
            if mapped_shell and mapped_shell != shell_normalized:
                # Replace "sh" with "bash" in argv
                sys.argv[2] = mapped_shell


# Note: Shell normalization happens in cli_main() before app() is called
# We don't normalize at module load time because sys.argv may not be set yet


app = typer.Typer(
    name="specfact",
    help="SpecFact CLI - Spec→Contract→Sentinel tool for contract-driven development",
    add_completion=False,  # Disable built-in completion (we provide custom commands with shell normalization)
    rich_markup_mode="rich",
)

console = Console()

# Global mode context (set by --mode flag or auto-detected)
_current_mode: OperationalMode | None = None


def version_callback(value: bool) -> None:
    """Show version information."""
    if value:
        console.print(f"[bold cyan]SpecFact CLI[/bold cyan] version [green]{__version__}[/green]")
        raise typer.Exit()


def mode_callback(value: Optional[str]) -> None:
    """Handle --mode flag callback."""
    global _current_mode
    if value is not None:
        try:
            _current_mode = OperationalMode(value.lower())
        except ValueError:
            console.print(f"[bold red]✗[/bold red] Invalid mode: {value}")
            console.print("Valid modes: cicd, copilot")
            raise typer.Exit(1) from None


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
    mode: Optional[str] = typer.Option(
        None,
        "--mode",
        callback=mode_callback,
        help="Operational mode: cicd (fast, deterministic) or copilot (enhanced, interactive)",
    ),
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
    # Store mode in context for commands to access
    if ctx.obj is None:
        ctx.obj = {}
    ctx.obj["mode"] = get_current_mode()


@app.command()
def hello() -> None:
    """
    Test command to verify CLI installation.
    """
    console.print(
        Panel.fit(
            "[bold green]✓[/bold green] SpecFact CLI is installed and working!\n\n"
            f"Version: [cyan]{__version__}[/cyan]\n"
            "Run [bold]specfact --help[/bold] for available commands.",
            title="[bold]Welcome to SpecFact CLI[/bold]",
            border_style="green",
        )
    )


@app.command()
@beartype
def install_completion(
    shell: str = typer.Argument(..., help="Shell name: bash, sh, zsh, fish, powershell, pwsh, ps1"),
    path: Optional[Path] = typer.Option(
        None,
        "--path",
        help="Path to shell configuration file (auto-detected if not provided)",
    ),
) -> None:
    """
    Install shell completion for SpecFact CLI.

    Supported shells:
    - bash, sh (bash-compatible)
    - zsh
    - fish
    - powershell, pwsh, ps1 (PowerShell)

    Example:
        specfact install-completion bash
        specfact install-completion zsh
        specfact install-completion powershell
    """
    # Normalize shell name
    shell_normalized = shell.lower().strip()
    mapped_shell = SHELL_MAP.get(shell_normalized)

    if not mapped_shell:
        console.print(f"[bold red]✗[/bold red] Unsupported shell: {shell}")
        console.print(
            f"\n[dim]Supported shells: {', '.join(sorted(set(SHELL_MAP.values())))}, sh (mapped to bash)[/dim]"
        )
        raise typer.Exit(1)

    # Generate completion script using subprocess to call CLI with completion env var
    try:
        import subprocess

        if mapped_shell == "powershell":
            # PowerShell completion requires click-pwsh extension
            completion_script = "# PowerShell completion requires click-pwsh extension\n"
            completion_script += "# Install: pip install click-pwsh\n"
            completion_script += "# Then run: python -m click_pwsh install specfact\n"
        else:
            # Use subprocess to get completion script from Typer/Click
            env = os.environ.copy()
            env["_SPECFACT_COMPLETE"] = f"{mapped_shell}_source"

            # Call the CLI with completion environment variable to get script
            result = subprocess.run(
                [sys.executable, "-m", "specfact_cli.cli"],
                env=env,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0 and result.stdout:
                completion_script = result.stdout
            else:
                # Fallback: Provide instructions for manual installation
                completion_script = f"# SpecFact CLI completion for {mapped_shell}\n"
                completion_script += f"# Add to your {mapped_shell} config file:\n"
                completion_script += f'eval "$(_SPECFACT_COMPLETE={mapped_shell}_source specfact)"\n'

        # Determine config file path if not provided
        if path is None:
            if mapped_shell == "bash":
                path = Path.home() / ".bashrc"
            elif mapped_shell == "zsh":
                path = Path.home() / ".zshrc"
            elif mapped_shell == "fish":
                path = Path.home() / ".config" / "fish" / "config.fish"
                path.parent.mkdir(parents=True, exist_ok=True)
            elif mapped_shell == "powershell":
                # PowerShell profile location
                profile_paths = [
                    Path.home() / "Documents" / "PowerShell" / "Microsoft.PowerShell_profile.ps1",
                    Path.home() / ".config" / "powershell" / "Microsoft.PowerShell_profile.ps1",
                ]
                for profile_path in profile_paths:
                    if profile_path.parent.exists() or profile_path.parent.parent.exists():
                        path = profile_path
                        path.parent.mkdir(parents=True, exist_ok=True)
                        break
                else:
                    # Default to first option
                    path = profile_paths[0]
                    path.parent.mkdir(parents=True, exist_ok=True)

        # Ensure path is not None
        if path is None:
            console.print("[bold red]✗[/bold red] Could not determine shell configuration file path")
            raise typer.Exit(1)

        # Check if already installed
        if path.exists():
            with path.open(encoding="utf-8") as f:
                content = f.read()
                if "specfact" in content and ("_SPECFACT_COMPLETE" in content or "_SPECFACT" in content):
                    console.print(f"[yellow]⚠[/yellow] Completion already installed in {path}")
                    console.print("[dim]Remove existing completion and re-run to update.[/dim]")
                    raise typer.Exit(0)

        # Append completion script
        with path.open("a", encoding="utf-8") as f:
            f.write(f"\n# SpecFact CLI completion for {mapped_shell}\n")
            f.write(completion_script)
            if completion_script and not completion_script.endswith("\n"):
                f.write("\n")

        console.print(f"[bold green]✓[/bold green] Completion installed for {mapped_shell} in {path}")
        if mapped_shell != "powershell":
            console.print(f"[dim]Reload your shell or run: source {path}[/dim]")
        else:
            console.print("[dim]Reload your PowerShell session to enable completion.[/dim]")

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to install completion: {e}")
        raise typer.Exit(1) from e


@app.command()
@beartype
def show_completion(
    shell: str = typer.Argument(..., help="Shell name: bash, sh, zsh, fish, powershell, pwsh, ps1"),
) -> None:
    """
    Show shell completion script for SpecFact CLI.

    Supported shells:
    - bash, sh (bash-compatible)
    - zsh
    - fish
    - powershell, pwsh, ps1 (PowerShell)

    Example:
        specfact show-completion bash
        specfact show-completion zsh
    """
    # Normalize shell name
    shell_normalized = shell.lower().strip()
    mapped_shell = SHELL_MAP.get(shell_normalized)

    if not mapped_shell:
        console.print(f"[bold red]✗[/bold red] Unsupported shell: {shell}")
        console.print(
            f"\n[dim]Supported shells: {', '.join(sorted(set(SHELL_MAP.values())))}, sh (mapped to bash)[/dim]"
        )
        raise typer.Exit(1)

    # Generate completion script using subprocess to call CLI with completion env var
    try:
        import subprocess

        if mapped_shell == "powershell":
            # PowerShell completion requires click-pwsh extension
            completion_script = "# PowerShell completion requires click-pwsh extension\n"
            completion_script += "# Install: pip install click-pwsh\n"
            completion_script += "# Then run: python -m click_pwsh install specfact\n"
        else:
            # Use subprocess to get completion script from Typer/Click
            # Normalize shell name in subprocess call
            env = os.environ.copy()
            env["_SPECFACT_COMPLETE"] = f"{mapped_shell}_source"

            # Call the CLI with completion environment variable to get script
            # Note: We need to bypass our own command and use Typer's built-in
            result = subprocess.run(
                [sys.executable, "-m", "specfact_cli.cli"],
                env=env,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0 and result.stdout and result.stdout.strip():
                completion_script = result.stdout
            else:
                # Fallback: Provide instructions for manual installation
                completion_script = f"# SpecFact CLI completion for {mapped_shell}\n"
                completion_script += f"# Add to your {mapped_shell} config file:\n"
                completion_script += f'eval "$(_SPECFACT_COMPLETE={mapped_shell}_source specfact)"\n'

        print(completion_script)

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to generate completion script: {e}")
        raise typer.Exit(1) from e


# Register command groups
app.add_typer(import_cmd.app, name="import", help="Import codebases and Spec-Kit projects")
app.add_typer(plan.app, name="plan", help="Manage development plans")
app.add_typer(enforce.app, name="enforce", help="Configure quality gates")
app.add_typer(repro.app, name="repro", help="Run validation suite")
app.add_typer(sync.app, name="sync", help="Synchronize Spec-Kit artifacts and repository changes")
app.add_typer(init.app, name="init", help="Initialize SpecFact for IDE integration")


def cli_main() -> None:
    """Entry point for the CLI application."""
    # Intercept completion environment variable and normalize shell names
    # (This handles completion scripts generated by our custom commands)
    completion_env = os.environ.get("_SPECFACT_COMPLETE")
    if completion_env:
        # Extract shell name from completion env var (format: "shell_source" or "shell")
        if completion_env.endswith("_source"):
            shell_name = completion_env[:-7]  # Remove "_source" suffix
        else:
            shell_name = completion_env

        # Normalize shell name using our mapping
        shell_normalized = shell_name.lower().strip()
        mapped_shell = SHELL_MAP.get(shell_normalized, shell_normalized)

        # Update environment variable with normalized shell name
        if mapped_shell != shell_normalized:
            if completion_env.endswith("_source"):
                os.environ["_SPECFACT_COMPLETE"] = f"{mapped_shell}_source"
            else:
                os.environ["_SPECFACT_COMPLETE"] = mapped_shell

    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(130)
    except ViolationError as e:
        # Extract user-friendly error message from ViolationError
        error_msg = str(e)
        # Try to extract the contract message (after ":\n")
        if ":\n" in error_msg:
            contract_msg = error_msg.split(":\n", 1)[0]
            console.print(f"[bold red]✗[/bold red] {contract_msg}", style="red")
        else:
            console.print(f"[bold red]✗[/bold red] {error_msg}", style="red")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}", style="red")
        sys.exit(1)


if __name__ == "__main__":
    cli_main()

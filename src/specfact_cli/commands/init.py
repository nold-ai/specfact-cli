"""
Init command - Initialize SpecFact for IDE integration.

This module provides the `specfact init` command to copy prompt templates
to IDE-specific locations for slash command integration.
"""

from __future__ import annotations

from pathlib import Path

import typer
from beartype import beartype
from icontract import ensure, require
from rich.console import Console
from rich.panel import Panel

from specfact_cli.telemetry import telemetry
from specfact_cli.utils.ide_setup import IDE_CONFIG, copy_templates_to_ide, detect_ide


app = typer.Typer(help="Initialize SpecFact for IDE integration")
console = Console()


def _is_valid_repo_path(path: Path) -> bool:
    """Check if path exists and is a directory."""
    return path.exists() and path.is_dir()


@app.callback(invoke_without_command=True)
@require(lambda ide: ide in IDE_CONFIG or ide == "auto", "IDE must be valid or 'auto'")
@require(lambda repo: _is_valid_repo_path(repo), "Repo path must exist and be directory")
@ensure(lambda result: result is None, "Command should return None")
@beartype
def init(
    ide: str = typer.Option(
        "auto",
        "--ide",
        help="IDE type (auto, cursor, vscode, copilot, claude, gemini, qwen, opencode, windsurf, kilocode, auggie, roo, codebuddy, amp, q)",
    ),
    repo: Path = typer.Option(
        Path("."),
        "--repo",
        help="Repository path (default: current directory)",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Overwrite existing files",
    ),
) -> None:
    """
    Initialize SpecFact for IDE integration.

    Copies prompt templates to IDE-specific locations so slash commands work.
    This command detects the IDE type (or uses --ide flag) and copies
    SpecFact prompt templates to the appropriate directory.

    Examples:
        specfact init                    # Auto-detect IDE
        specfact init --ide cursor       # Initialize for Cursor
        specfact init --ide vscode --force  # Overwrite existing files
        specfact init --repo /path/to/repo --ide copilot
    """
    telemetry_metadata = {
        "ide": ide,
        "force": force,
    }

    with telemetry.track_command("init", telemetry_metadata) as record:
        # Resolve repo path
        repo_path = repo.resolve()

        # Detect IDE
        detected_ide = detect_ide(ide)
        ide_config = IDE_CONFIG[detected_ide]
        ide_name = ide_config["name"]

        console.print()
        console.print(Panel("[bold cyan]SpecFact IDE Setup[/bold cyan]", border_style="cyan"))
        console.print(f"[cyan]Repository:[/cyan] {repo_path}")
        console.print(f"[cyan]IDE:[/cyan] {ide_name} ({detected_ide})")
        console.print()

        # Find templates directory
        # Try relative to project root first (for development)
        templates_dir = repo_path / "resources" / "prompts"
        if not templates_dir.exists():
            # Try relative to installed package (for distribution)
            import importlib.util

            spec = importlib.util.find_spec("specfact_cli")
            if spec and spec.origin:
                package_dir = Path(spec.origin).parent.parent
                templates_dir = package_dir / "resources" / "prompts"
                if not templates_dir.exists():
                    # Fallback: try resources/prompts in project root
                    templates_dir = Path(__file__).parent.parent.parent.parent / "resources" / "prompts"

        if not templates_dir.exists():
            console.print(f"[red]Error:[/red] Templates directory not found: {templates_dir}")
            console.print("[yellow]Expected location:[/yellow] resources/prompts/")
            console.print("[yellow]Please ensure SpecFact is properly installed.[/yellow]")
            raise typer.Exit(1)

        console.print(f"[cyan]Templates:[/cyan] {templates_dir}")
        console.print()

        # Copy templates to IDE location
        try:
            copied_files, settings_path = copy_templates_to_ide(repo_path, detected_ide, templates_dir, force)

            if not copied_files:
                console.print(
                    "[yellow]No templates copied (all files already exist, use --force to overwrite)[/yellow]"
                )
                record({"files_copied": 0, "already_exists": True})
                raise typer.Exit(0)

            record(
                {
                    "detected_ide": detected_ide,
                    "files_copied": len(copied_files),
                    "settings_updated": settings_path is not None,
                }
            )

            console.print()
            console.print(Panel("[bold green]✓ Initialization Complete[/bold green]", border_style="green"))
            console.print(f"[green]Copied {len(copied_files)} template(s) to {ide_config['folder']}[/green]")
            if settings_path:
                console.print(f"[green]Updated VS Code settings:[/green] {settings_path}")
            console.print()
            console.print("[dim]You can now use SpecFact slash commands in your IDE![/dim]")
            console.print("[dim]Example: /specfact-import-from-code --repo . --confidence 0.7[/dim]")

        except Exception as e:
            console.print(f"[red]Error:[/red] Failed to initialize IDE integration: {e}")
            raise typer.Exit(1) from e

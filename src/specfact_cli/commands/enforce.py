"""
Enforce command - Configure contract validation quality gates.

This module provides commands for configuring enforcement modes
and validation policies.
"""

from __future__ import annotations

import typer
from beartype import beartype
from rich.console import Console
from rich.table import Table

from specfact_cli.models.enforcement import EnforcementConfig, EnforcementPreset
from specfact_cli.telemetry import telemetry
from specfact_cli.utils.structure import SpecFactStructure
from specfact_cli.utils.yaml_utils import dump_yaml


app = typer.Typer(help="Configure quality gates and enforcement modes")
console = Console()


@app.command("stage")
@beartype
def stage(
    preset: str = typer.Option(
        "balanced",
        "--preset",
        help="Enforcement preset (minimal, balanced, strict)",
    ),
) -> None:
    """
    Set enforcement mode for contract validation.

    Modes:
    - minimal:  Log violations, never block
    - balanced: Block HIGH severity, warn MEDIUM
    - strict:   Block all MEDIUM+ violations

    Example:
        specfact enforce stage --preset balanced
    """
    telemetry_metadata = {
        "preset": preset.lower(),
    }

    with telemetry.track_command("enforce.stage", telemetry_metadata) as record:
        # Validate preset (contract-style validation)
        if not isinstance(preset, str) or len(preset) == 0:
            console.print("[bold red]✗[/bold red] Preset must be non-empty string")
            raise typer.Exit(1)

        if preset.lower() not in ("minimal", "balanced", "strict"):
            console.print(f"[bold red]✗[/bold red] Unknown preset: {preset}")
            console.print("Valid presets: minimal, balanced, strict")
            raise typer.Exit(1)

        console.print(f"[bold cyan]Setting enforcement mode:[/bold cyan] {preset}")

        # Validate preset enum
        try:
            preset_enum = EnforcementPreset(preset)
        except ValueError as err:
            console.print(f"[bold red]✗[/bold red] Unknown preset: {preset}")
            console.print("Valid presets: minimal, balanced, strict")
            raise typer.Exit(1) from err

        # Create enforcement configuration
        config = EnforcementConfig.from_preset(preset_enum)

        # Display configuration as table
        table = Table(title=f"Enforcement Mode: {preset.upper()}")
        table.add_column("Severity", style="cyan")
        table.add_column("Action", style="yellow")

        for severity, action in config.to_summary_dict().items():
            table.add_row(severity, action)

        console.print(table)

        # Ensure .specfact structure exists
        SpecFactStructure.ensure_structure()

        # Write configuration to file
        config_path = SpecFactStructure.get_enforcement_config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Use mode='json' to convert enums to their string values
        dump_yaml(config.model_dump(mode="json"), config_path)

        record({"config_saved": True, "enabled": config.enabled})

        console.print(f"\n[bold green]✓[/bold green] Enforcement mode set to {preset}")
        console.print(f"[dim]Configuration saved to: {config_path}[/dim]")

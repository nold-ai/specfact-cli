"""
SDD (Spec-Driven Development) manifest management commands.

This module provides commands for managing SDD manifests, including listing
all SDD manifests in a repository.
"""

from __future__ import annotations

from pathlib import Path

import typer
from beartype import beartype
from icontract import require
from rich.console import Console
from rich.table import Table

from specfact_cli.utils.sdd_discovery import list_all_sdds
from specfact_cli.utils.structure import SpecFactStructure


app = typer.Typer(
    name="sdd",
    help="Manage SDD (Spec-Driven Development) manifests",
    rich_markup_mode="rich",
)

console = Console()


@app.command("list")
@beartype
@require(lambda repo: isinstance(repo, Path), "Repo must be Path")
def sdd_list(
    # Target/Input
    repo: Path = typer.Option(
        Path("."),
        "--repo",
        help="Path to repository",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
) -> None:
    """
    List all SDD manifests in the repository.

    Shows all SDD manifests found in bundle-specific locations (.specfact/projects/<bundle-name>/sdd.yaml, Phase 8.5)
    and legacy multi-SDD layout (.specfact/sdd/*.yaml)
    and legacy single-SDD layout (.specfact/sdd.yaml).

    **Parameter Groups:**
    - **Target/Input**: --repo

    **Examples:**
        specfact sdd list
        specfact sdd list --repo /path/to/repo
    """
    console.print("\n[bold cyan]SpecFact CLI - SDD Manifest List[/bold cyan]")
    console.print("=" * 60)

    base_path = repo.resolve()
    all_sdds = list_all_sdds(base_path)

    if not all_sdds:
        console.print("[yellow]No SDD manifests found[/yellow]")
        console.print(f"[dim]Searched in: {base_path / SpecFactStructure.PROJECTS}/*/sdd.yaml[/dim]")
        console.print(
            f"[dim]Legacy fallback: {base_path / SpecFactStructure.SDD}/* and {base_path / SpecFactStructure.ROOT / 'sdd.yaml'}[/dim]"
        )
        console.print("\n[dim]Create SDD manifests with: specfact plan harden <bundle-name>[/dim]")
        console.print("[dim]If you have legacy bundles, migrate with: specfact migrate artifacts --repo .[/dim]")
        raise typer.Exit(0)

    # Create table
    table = Table(title="SDD Manifests", show_header=True, header_style="bold cyan")
    table.add_column("Path", style="cyan", no_wrap=False)
    table.add_column("Bundle Hash", style="magenta")
    table.add_column("Bundle ID", style="blue")
    table.add_column("Status", style="green")
    table.add_column("Coverage", style="yellow")

    for sdd_path, manifest in all_sdds:
        # Determine if this is legacy or bundle-specific layout
        # Bundle-specific (new format): .specfact/projects/<bundle-name>/sdd.yaml
        # Legacy single-SDD: .specfact/sdd.yaml (root level)
        # Legacy multi-SDD: .specfact/sdd/<bundle-name>.yaml
        sdd_path_str = str(sdd_path)
        is_bundle_specific = "/projects/" in sdd_path_str or "\\projects\\" in sdd_path_str
        layout_type = "[green]bundle-specific[/green]" if is_bundle_specific else "[dim]legacy[/dim]"

        # Format path (relative to base_path)
        try:
            rel_path = sdd_path.relative_to(base_path)
        except ValueError:
            rel_path = sdd_path

        # Format hash (first 16 chars)
        hash_short = (
            manifest.plan_bundle_hash[:16] + "..." if len(manifest.plan_bundle_hash) > 16 else manifest.plan_bundle_hash
        )
        bundle_id_short = (
            manifest.plan_bundle_id[:16] + "..." if len(manifest.plan_bundle_id) > 16 else manifest.plan_bundle_id
        )

        # Format coverage thresholds
        coverage_str = (
            f"Contracts/Story: {manifest.coverage_thresholds.contracts_per_story:.1f}, "
            f"Invariants/Feature: {manifest.coverage_thresholds.invariants_per_feature:.1f}, "
            f"Arch Facets: {manifest.coverage_thresholds.architecture_facets}"
        )

        # Format status
        status = manifest.promotion_status

        table.add_row(
            f"{rel_path} {layout_type}",
            hash_short,
            bundle_id_short,
            status,
            coverage_str,
        )

    console.print()
    console.print(table)
    console.print(f"\n[dim]Total SDD manifests: {len(all_sdds)}[/dim]")

    # Show layout information
    bundle_specific_count = sum(1 for path, _ in all_sdds if "/projects/" in str(path) or "\\projects\\" in str(path))
    legacy_count = len(all_sdds) - bundle_specific_count

    if bundle_specific_count > 0:
        console.print(f"[green]✓ {bundle_specific_count} bundle-specific SDD manifest(s) found[/green]")

    if legacy_count > 0:
        console.print(f"[yellow]⚠ {legacy_count} legacy SDD manifest(s) found[/yellow]")
        console.print(
            "[dim]Consider migrating to bundle-specific layout: .specfact/projects/<bundle-name>/sdd.yaml (Phase 8.5)[/dim]"
        )

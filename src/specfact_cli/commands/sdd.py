"""
SDD (Spec-Driven Development) manifest management commands.

This module provides commands for managing SDD manifests, including listing
all SDD manifests in a repository, and constitution management for Spec-Kit compatibility.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import typer
from beartype import beartype
from icontract import ensure, require
from rich.table import Table

from specfact_cli.enrichers.constitution_enricher import ConstitutionEnricher
from specfact_cli.runtime import debug_log_operation, debug_print, get_configured_console, is_debug_mode
from specfact_cli.utils import print_error, print_info, print_success
from specfact_cli.utils.sdd_discovery import list_all_sdds
from specfact_cli.utils.structure import SpecFactStructure


app = typer.Typer(
    name="sdd",
    help="Manage SDD (Spec-Driven Development) manifests and constitutions",
    rich_markup_mode="rich",
)

console = get_configured_console()

# Constitution subcommand group
constitution_app = typer.Typer(
    help="Manage project constitutions (Spec-Kit format compatibility). Generates and validates constitutions at .specify/memory/constitution.md for Spec-Kit format compatibility."
)

app.add_typer(constitution_app, name="constitution")

# Constitution subcommand group
constitution_app = typer.Typer(
    help="Manage project constitutions (Spec-Kit format compatibility). Generates and validates constitutions at .specify/memory/constitution.md for Spec-Kit format compatibility."
)

app.add_typer(constitution_app, name="constitution")


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
    if is_debug_mode():
        debug_log_operation("command", "sdd list", "started", extra={"repo": str(repo)})
        debug_print("[dim]sdd list: started[/dim]")

    console.print("\n[bold cyan]SpecFact CLI - SDD Manifest List[/bold cyan]")
    console.print("=" * 60)

    base_path = repo.resolve()
    all_sdds = list_all_sdds(base_path)

    if not all_sdds:
        if is_debug_mode():
            debug_log_operation("command", "sdd list", "success", extra={"count": 0, "reason": "none_found"})
            debug_print("[dim]sdd list: success (none found)[/dim]")
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
    if is_debug_mode():
        debug_log_operation("command", "sdd list", "success", extra={"count": len(all_sdds)})
        debug_print("[dim]sdd list: success[/dim]")

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


@constitution_app.command("bootstrap")
@beartype
@require(lambda repo: repo.exists(), "Repository path must exist")
@require(lambda repo: repo.is_dir(), "Repository path must be a directory")
@ensure(lambda result: result is None, "Must return None")
def constitution_bootstrap(
    # Target/Input
    repo: Path = typer.Option(
        Path("."),
        "--repo",
        help="Repository path. Default: current directory (.)",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    # Output/Results
    out: Path | None = typer.Option(
        None,
        "--out",
        help="Output path for constitution. Default: .specify/memory/constitution.md",
    ),
    # Behavior/Options
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite existing constitution if it exists. Default: False",
    ),
) -> None:
    """
    Generate bootstrap constitution from repository analysis (Spec-Kit compatibility).

    This command generates a constitution in Spec-Kit format (`.specify/memory/constitution.md`)
    for compatibility with Spec-Kit artifacts and sync operations.

    **Note**: SpecFact itself uses plan bundles (`.specfact/plans/*.bundle.<format>`) for internal
    operations. Constitutions are only needed when syncing with Spec-Kit or working in Spec-Kit format.

    Analyzes the repository (README, pyproject.toml, .cursor/rules/, docs/rules/)
    to extract project metadata, development principles, and quality standards,
    then generates a bootstrap constitution template ready for review and adjustment.

    **Parameter Groups:**
    - **Target/Input**: --repo
    - **Output/Results**: --out
    - **Behavior/Options**: --overwrite

    **Examples:**
        specfact sdd constitution bootstrap --repo .
        specfact sdd constitution bootstrap --repo . --out custom-constitution.md
        specfact sdd constitution bootstrap --repo . --overwrite
    """
    from specfact_cli.telemetry import telemetry

    with telemetry.track_command("sdd.constitution.bootstrap", {"repo": str(repo)}):
        console.print(f"[bold cyan]Generating bootstrap constitution for:[/bold cyan] {repo}")

        # Determine output path
        if out is None:
            # Use Spec-Kit convention: .specify/memory/constitution.md
            specify_dir = repo / ".specify" / "memory"
            specify_dir.mkdir(parents=True, exist_ok=True)
            out = specify_dir / "constitution.md"
        else:
            out.parent.mkdir(parents=True, exist_ok=True)

        # Check if constitution already exists
        if out.exists() and not overwrite:
            console.print(f"[yellow]⚠[/yellow] Constitution already exists: {out}")
            console.print("[dim]Use --overwrite to replace it[/dim]")
            raise typer.Exit(1)

        # Generate bootstrap constitution
        print_info("Analyzing repository...")
        enricher = ConstitutionEnricher()
        enriched_content = enricher.bootstrap(repo, out)

        # Write constitution
        out.write_text(enriched_content, encoding="utf-8")
        print_success(f"✓ Bootstrap constitution generated: {out}")

        console.print("\n[bold]Next Steps:[/bold]")
        console.print("1. Review the generated constitution")
        console.print("2. Adjust principles and sections as needed")
        console.print("3. Run 'specfact sdd constitution validate' to check completeness")
        console.print("4. Run 'specfact sync bridge --adapter speckit' to sync with Spec-Kit artifacts")


@constitution_app.command("enrich")
@beartype
@require(lambda repo: repo.exists(), "Repository path must exist")
@require(lambda repo: repo.is_dir(), "Repository path must be a directory")
@ensure(lambda result: result is None, "Must return None")
def constitution_enrich(
    repo: Path = typer.Option(
        Path("."),
        "--repo",
        help="Repository path (default: current directory)",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    constitution: Path | None = typer.Option(
        None,
        "--constitution",
        help="Path to constitution file (default: .specify/memory/constitution.md)",
    ),
) -> None:
    """
    Auto-enrich existing constitution with repository context (Spec-Kit compatibility).

    This command enriches a constitution in Spec-Kit format (`.specify/memory/constitution.md`)
    for compatibility with Spec-Kit artifacts and sync operations.

    **Note**: SpecFact itself uses plan bundles (`.specfact/plans/*.bundle.<format>`) for internal
    operations. Constitutions are only needed when syncing with Spec-Kit or working in Spec-Kit format.

    Analyzes the repository and enriches the existing constitution with
    additional principles and details extracted from repository context.

    Example:
        specfact sdd constitution enrich --repo .
    """
    from specfact_cli.telemetry import telemetry

    with telemetry.track_command("sdd.constitution.enrich", {"repo": str(repo)}):
        # Determine constitution path
        if constitution is None:
            constitution = repo / ".specify" / "memory" / "constitution.md"

        if not constitution.exists():
            console.print(f"[bold red]✗[/bold red] Constitution not found: {constitution}")
            console.print("[dim]Run 'specfact sdd constitution bootstrap' first[/dim]")
            raise typer.Exit(1)

        console.print(f"[bold cyan]Enriching constitution:[/bold cyan] {constitution}")

        # Analyze repository
        print_info("Analyzing repository...")
        enricher = ConstitutionEnricher()
        analysis = enricher.analyze_repository(repo)

        # Suggest additional principles
        principles = enricher.suggest_principles(analysis)

        console.print(f"[dim]Found {len(principles)} suggested principles[/dim]")

        # Read existing constitution
        existing_content = constitution.read_text(encoding="utf-8")

        # Check if enrichment is needed (has placeholders)
        import re

        placeholder_pattern = r"\[[A-Z_0-9]+\]"
        placeholders = re.findall(placeholder_pattern, existing_content)

        if not placeholders:
            console.print("[yellow]⚠[/yellow] Constitution appears complete (no placeholders found)")
            console.print("[dim]No enrichment needed[/dim]")
            return

        console.print(f"[dim]Found {len(placeholders)} placeholders to enrich[/dim]")

        # Enrich template
        suggestions: dict[str, Any] = {
            "project_name": analysis.get("project_name", "Project"),
            "principles": principles,
            "section2_name": "Development Workflow",
            "section2_content": enricher._generate_workflow_section(analysis),
            "section3_name": "Quality Standards",
            "section3_content": enricher._generate_quality_standards_section(analysis),
            "governance_rules": "Constitution supersedes all other practices. Amendments require documentation, team approval, and migration plan for breaking changes.",
        }

        enriched_content = enricher.enrich_template(constitution, suggestions)

        # Write enriched constitution
        constitution.write_text(enriched_content, encoding="utf-8")
        print_success(f"✓ Constitution enriched: {constitution}")

        console.print("\n[bold]Next Steps:[/bold]")
        console.print("1. Review the enriched constitution")
        console.print("2. Adjust as needed")
        console.print("3. Run 'specfact sdd constitution validate' to check completeness")


@constitution_app.command("validate")
@beartype
@require(lambda constitution: constitution.exists(), "Constitution path must exist")
@ensure(lambda result: result is None, "Must return None")
def constitution_validate(
    constitution: Path = typer.Option(
        Path(".specify/memory/constitution.md"),
        "--constitution",
        help="Path to constitution file",
        exists=True,
    ),
) -> None:
    """
    Validate constitution completeness (Spec-Kit compatibility).

    This command validates a constitution in Spec-Kit format (`.specify/memory/constitution.md`)
    for compatibility with Spec-Kit artifacts and sync operations.

    **Note**: SpecFact itself uses plan bundles (`.specfact/plans/*.bundle.<format>`) for internal
    operations. Constitutions are only needed when syncing with Spec-Kit or working in Spec-Kit format.

    Checks if the constitution is complete (no placeholders, has principles,
    has governance section, etc.).

    Example:
        specfact sdd constitution validate
        specfact sdd constitution validate --constitution custom-constitution.md
    """
    from specfact_cli.telemetry import telemetry

    with telemetry.track_command("sdd.constitution.validate", {"constitution": str(constitution)}):
        console.print(f"[bold cyan]Validating constitution:[/bold cyan] {constitution}")

        enricher = ConstitutionEnricher()
        is_valid, issues = enricher.validate(constitution)

        if is_valid:
            print_success("✓ Constitution is valid and complete")
        else:
            print_error("✗ Constitution validation failed")
            console.print("\n[bold]Issues found:[/bold]")
            for issue in issues:
                console.print(f"  - {issue}")

            console.print("\n[bold]Next Steps:[/bold]")
            console.print("1. Run 'specfact sdd constitution bootstrap' to generate a complete constitution")
            console.print("2. Or run 'specfact sdd constitution enrich' to enrich existing constitution")
            raise typer.Exit(1)


def is_constitution_minimal(constitution_path: Path) -> bool:
    """
    Check if constitution is minimal (essentially empty).

    Args:
        constitution_path: Path to constitution file

    Returns:
        True if constitution is minimal, False otherwise
    """
    if not constitution_path.exists():
        return True

    try:
        content = constitution_path.read_text(encoding="utf-8").strip()
        # Check if it's just a header or very minimal
        if not content or content == "# Constitution" or len(content) < 100:
            return True

        # Check if it has mostly placeholders
        import re

        placeholder_pattern = r"\[[A-Z_0-9]+\]"
        placeholders = re.findall(placeholder_pattern, content)
        lines = [line.strip() for line in content.split("\n") if line.strip()]
        return bool(lines and len(placeholders) > len(lines) * 0.5)
    except Exception:
        return True

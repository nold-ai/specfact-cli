"""
Constitution command - Manage project constitutions.

This module provides commands for bootstrapping, enriching, and validating
project constitutions based on repository context analysis.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import typer
from beartype import beartype
from icontract import ensure, require
from rich.console import Console

from specfact_cli.enrichers.constitution_enricher import ConstitutionEnricher
from specfact_cli.utils import print_error, print_info, print_success


app = typer.Typer(help="Manage project constitutions")
console = Console()


@app.command("bootstrap")
@beartype
@require(lambda repo: repo.exists(), "Repository path must exist")
@require(lambda repo: repo.is_dir(), "Repository path must be a directory")
@ensure(lambda result: result is None, "Must return None")
def bootstrap(
    repo: Path = typer.Option(
        Path("."),
        "--repo",
        help="Repository path (default: current directory)",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        help="Output path for constitution (default: .specify/memory/constitution.md)",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite existing constitution if it exists",
    ),
) -> None:
    """
    Generate bootstrap constitution from repository analysis.

    Analyzes the repository (README, pyproject.toml, .cursor/rules/, docs/rules/)
    to extract project metadata, development principles, and quality standards,
    then generates a bootstrap constitution template ready for review and adjustment.

    Example:
        specfact constitution bootstrap --repo .
        specfact constitution bootstrap --repo . --output custom-constitution.md
    """
    from specfact_cli.telemetry import telemetry

    with telemetry.track_command("constitution.bootstrap", {"repo": str(repo)}):
        console.print(f"[bold cyan]Generating bootstrap constitution for:[/bold cyan] {repo}")

        # Determine output path
        if output is None:
            # Use Spec-Kit convention: .specify/memory/constitution.md
            specify_dir = repo / ".specify" / "memory"
            specify_dir.mkdir(parents=True, exist_ok=True)
            output = specify_dir / "constitution.md"
        else:
            output.parent.mkdir(parents=True, exist_ok=True)

        # Check if constitution already exists
        if output.exists() and not overwrite:
            console.print(f"[yellow]⚠[/yellow] Constitution already exists: {output}")
            console.print("[dim]Use --overwrite to replace it[/dim]")
            raise typer.Exit(1)

        # Generate bootstrap constitution
        print_info("Analyzing repository...")
        enricher = ConstitutionEnricher()
        enriched_content = enricher.bootstrap(repo, output)

        # Write constitution
        output.write_text(enriched_content, encoding="utf-8")
        print_success(f"✓ Bootstrap constitution generated: {output}")

        console.print("\n[bold]Next Steps:[/bold]")
        console.print("1. Review the generated constitution")
        console.print("2. Adjust principles and sections as needed")
        console.print("3. Run 'specfact constitution validate' to check completeness")
        console.print("4. Run 'specfact sync spec-kit' to sync with Spec-Kit artifacts")


@app.command("enrich")
@beartype
@require(lambda repo: repo.exists(), "Repository path must exist")
@require(lambda repo: repo.is_dir(), "Repository path must be a directory")
@ensure(lambda result: result is None, "Must return None")
def enrich(
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
    Auto-enrich existing constitution with repository context.

    Analyzes the repository and enriches the existing constitution with
    additional principles and details extracted from repository context.

    Example:
        specfact constitution enrich --repo .
    """
    from specfact_cli.telemetry import telemetry

    with telemetry.track_command("constitution.enrich", {"repo": str(repo)}):
        # Determine constitution path
        if constitution is None:
            constitution = repo / ".specify" / "memory" / "constitution.md"

        if not constitution.exists():
            console.print(f"[bold red]✗[/bold red] Constitution not found: {constitution}")
            console.print("[dim]Run 'specfact constitution bootstrap' first[/dim]")
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
        console.print("3. Run 'specfact constitution validate' to check completeness")


@app.command("validate")
@beartype
@require(lambda constitution: constitution.exists(), "Constitution path must exist")
@ensure(lambda result: result is None, "Must return None")
def validate(
    constitution: Path = typer.Option(
        Path(".specify/memory/constitution.md"),
        "--constitution",
        help="Path to constitution file",
        exists=True,
    ),
) -> None:
    """
    Validate constitution completeness.

    Checks if the constitution is complete (no placeholders, has principles,
    has governance section, etc.).

    Example:
        specfact constitution validate
        specfact constitution validate --constitution custom-constitution.md
    """
    from specfact_cli.telemetry import telemetry

    with telemetry.track_command("constitution.validate", {"constitution": str(constitution)}):
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
            console.print("1. Run 'specfact constitution bootstrap' to generate a complete constitution")
            console.print("2. Or run 'specfact constitution enrich' to enrich existing constitution")
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

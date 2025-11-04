"""
Import command - Import codebases and Spec-Kit projects to contract-driven format.

This module provides commands for importing existing codebases (brownfield) and
Spec-Kit projects and converting them to SpecFact contract-driven format.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from beartype import beartype
from icontract import ensure, require
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

app = typer.Typer(help="Import codebases and Spec-Kit projects to contract format")
console = Console()


@app.command("from-spec-kit")
def from_spec_kit(
    repo: Path = typer.Option(
        Path("."),
        "--repo",
        help="Path to Spec-Kit repository",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview changes without writing files",
    ),
    write: bool = typer.Option(
        False,
        "--write",
        help="Write changes to disk",
    ),
    out_branch: str = typer.Option(
        "feat/specfact-migration",
        "--out-branch",
        help="Feature branch name for migration",
    ),
    report: Optional[Path] = typer.Option(
        None,
        "--report",
        help="Path to write import report",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Overwrite existing files",
    ),
) -> None:
    """
    Convert Spec-Kit project to SpecFact contract format.

    This command scans a Spec-Kit repository, parses its structure,
    and generates equivalent SpecFact contracts, protocols, and plans.

    Example:
        specfact import from-spec-kit --repo ./my-project --write
    """
    from specfact_cli.importers.speckit_converter import SpecKitConverter
    from specfact_cli.importers.speckit_scanner import SpecKitScanner
    from specfact_cli.utils.structure import SpecFactStructure

    console.print(f"[bold cyan]Importing Spec-Kit project from:[/bold cyan] {repo}")

    # Scan Spec-Kit structure
    scanner = SpecKitScanner(repo)

    if not scanner.is_speckit_repo():
        console.print("[bold red]✗[/bold red] Not a Spec-Kit repository")
        console.print("[dim]Expected: .specify/ directory[/dim]")
        raise typer.Exit(1)

    structure = scanner.scan_structure()

    if dry_run:
        console.print("[yellow]→ Dry run mode - no files will be written[/yellow]")
        console.print("\n[bold]Detected Structure:[/bold]")
        console.print(f"  - Specs Directory: {structure.get('specs_dir', 'Not found')}")
        console.print(f"  - Memory Directory: {structure.get('specify_memory_dir', 'Not found')}")
        if structure.get("feature_dirs"):
            console.print(f"  - Features Found: {len(structure['feature_dirs'])}")
        if structure.get("memory_files"):
            console.print(f"  - Memory Files: {len(structure['memory_files'])}")
        return

    if not write:
        console.print("[yellow]→ Use --write to actually convert files[/yellow]")
        console.print("[dim]Use --dry-run to preview changes[/dim]")
        return

    # Ensure SpecFact structure exists
    SpecFactStructure.ensure_structure(repo)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Step 1: Discover features from markdown artifacts
        task = progress.add_task("Discovering Spec-Kit features...", total=None)
        features = scanner.discover_features()
        if not features:
            console.print("[bold red]✗[/bold red] No features found in Spec-Kit repository")
            console.print("[dim]Expected: specs/*/spec.md files[/dim]")
            raise typer.Exit(1)
        progress.update(task, description=f"✓ Discovered {len(features)} features")

        # Step 2: Convert protocol
        task = progress.add_task("Converting protocol...", total=None)
        converter = SpecKitConverter(repo)
        protocol = None
        plan_bundle = None
        try:
            protocol = converter.convert_protocol()
            progress.update(task, description=f"✓ Protocol converted ({len(protocol.states)} states)")

            # Step 3: Convert plan
            task = progress.add_task("Converting plan bundle...", total=None)
            plan_bundle = converter.convert_plan()
            progress.update(task, description=f"✓ Plan converted ({len(plan_bundle.features)} features)")

            # Step 4: Generate Semgrep rules
            task = progress.add_task("Generating Semgrep rules...", total=None)
            semgrep_path = converter.generate_semgrep_rules()
            progress.update(task, description="✓ Semgrep rules generated")

            # Step 5: Generate GitHub Action workflow
            task = progress.add_task("Generating GitHub Action workflow...", total=None)
            repo_name = repo.name if isinstance(repo, Path) else None
            workflow_path = converter.generate_github_action(repo_name=repo_name)
            progress.update(task, description="✓ GitHub Action workflow generated")

        except Exception as e:
            console.print(f"[bold red]✗[/bold red] Conversion failed: {e}")
            raise typer.Exit(1) from e

    # Generate report
    if report and protocol and plan_bundle:
        report_content = f"""# Spec-Kit Import Report

## Repository: {repo}

## Summary
- **States Found**: {len(protocol.states)}
- **Transitions**: {len(protocol.transitions)}
- **Features Extracted**: {len(plan_bundle.features)}
- **Total Stories**: {sum(len(f.stories) for f in plan_bundle.features)}

## Generated Files
- **Protocol**: `.specfact/protocols/workflow.protocol.yaml`
- **Plan Bundle**: `.specfact/plans/main.bundle.yaml`
- **Semgrep Rules**: `.semgrep/async-anti-patterns.yml`
- **GitHub Action**: `.github/workflows/specfact-gate.yml`

## States
{chr(10).join(f"- {state}" for state in protocol.states)}

## Features
{chr(10).join(f"- {f.title} ({f.key})" for f in plan_bundle.features)}
"""
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(report_content, encoding="utf-8")
        console.print(f"[dim]Report written to: {report}[/dim]")

    console.print("[bold green]✓[/bold green] Import complete!")
    console.print("[dim]Protocol: .specfact/protocols/workflow.protocol.yaml[/dim]")
    console.print("[dim]Plan: .specfact/plans/main.bundle.yaml[/dim]")
    console.print("[dim]Semgrep Rules: .semgrep/async-anti-patterns.yml[/dim]")
    console.print("[dim]GitHub Action: .github/workflows/specfact-gate.yml[/dim]")


@app.command("from-code")
@require(lambda repo: repo.exists() and repo.is_dir(), "Repo path must exist and be directory")
@require(lambda confidence: 0.0 <= confidence <= 1.0, "Confidence must be 0.0-1.0")
@ensure(lambda out: out is None or out.exists(), "Output path must exist if provided")
@beartype
def from_code(
    repo: Path = typer.Option(
        Path("."),
        "--repo",
        help="Path to repository to import",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    name: Optional[str] = typer.Option(
        None,
        "--name",
        help="Custom plan name (will be sanitized for filesystem, default: 'auto-derived')",
    ),
    out: Optional[Path] = typer.Option(
        None,
        "--out",
        help="Output plan bundle path (default: .specfact/plans/<name>-<timestamp>.bundle.yaml)",
    ),
    shadow_only: bool = typer.Option(
        False,
        "--shadow-only",
        help="Shadow mode - observe without enforcing",
    ),
    report: Optional[Path] = typer.Option(
        None,
        "--report",
        help="Path to write analysis report (default: .specfact/reports/brownfield/analysis-<timestamp>.md)",
    ),
    confidence: float = typer.Option(
        0.5,
        "--confidence",
        min=0.0,
        max=1.0,
        help="Minimum confidence score for features",
    ),
    key_format: str = typer.Option(
        "classname",
        "--key-format",
        help="Feature key format: 'classname' (FEATURE-CLASSNAME) or 'sequential' (FEATURE-001)",
    ),
) -> None:
    """
    Import plan bundle from existing codebase (one-way import).

    Analyzes code structure using AI-first semantic understanding or AST-based fallback
    to generate a plan bundle that represents the current system.

    Example:
        specfact import from-code --repo . --out brownfield-plan.yaml
    """
    from specfact_cli.agents.analyze_agent import AnalyzeAgent
    from specfact_cli.agents.registry import get_agent
    from specfact_cli.cli import get_current_mode
    from specfact_cli.modes import get_router

    mode = get_current_mode()

    # Route command based on mode
    router = get_router()
    routing_result = router.route("import from-code", mode, {"repo": str(repo), "confidence": confidence})

    from specfact_cli.generators.plan_generator import PlanGenerator
    from specfact_cli.utils.structure import SpecFactStructure
    from specfact_cli.validators.schema import validate_plan_bundle

    # Ensure .specfact structure exists in the repository being imported
    SpecFactStructure.ensure_structure(repo)

    # Use default paths if not specified (relative to repo)
    if out is None:
        out = SpecFactStructure.get_timestamped_brownfield_report(repo, name=name)

    if report is None:
        report = SpecFactStructure.get_brownfield_analysis_path(repo)

    console.print(f"[bold cyan]Importing repository:[/bold cyan] {repo}")
    console.print(f"[dim]Confidence threshold: {confidence}[/dim]")

    if shadow_only:
        console.print("[yellow]→ Shadow mode - observe without enforcement[/yellow]")

    try:
        # Use AI-first approach in CoPilot mode, fallback to AST in CI/CD mode
        if routing_result.execution_mode == "agent":
            console.print("[dim]Mode: CoPilot (AI-first import)[/dim]")
            # Get agent for this command
            agent = get_agent("import from-code")
            if agent and isinstance(agent, AnalyzeAgent):
                # Build context for agent
                context = {
                    "workspace": str(repo),
                    "current_file": None,  # TODO: Get from IDE in Phase 4.2+
                    "selection": None,  # TODO: Get from IDE in Phase 4.2+
                }
                # Inject context (for future LLM integration)
                _enhanced_context = agent.inject_context(context)
                # Use AI-first import
                console.print("\n[cyan]🤖 AI-powered import (semantic understanding)...[/cyan]")
                plan_bundle = agent.analyze_codebase(repo, confidence=confidence, plan_name=name)
                console.print("[green]✓[/green] AI import complete")
            else:
                # Fallback to AST if agent not available
                console.print("[yellow]⚠ Agent not available, falling back to AST-based import[/yellow]")
                from specfact_cli.analyzers.code_analyzer import CodeAnalyzer

                console.print("\n[cyan]🔍 Importing Python files (AST-based fallback)...[/cyan]")
                analyzer = CodeAnalyzer(repo, confidence_threshold=confidence, key_format=key_format, plan_name=name)
                plan_bundle = analyzer.analyze()
        else:
            # CI/CD mode: use AST-based import (no LLM available)
            console.print("[dim]Mode: CI/CD (AST-based import)[/dim]")
            from specfact_cli.analyzers.code_analyzer import CodeAnalyzer

            console.print("\n[cyan]🔍 Importing Python files...[/cyan]")
            analyzer = CodeAnalyzer(repo, confidence_threshold=confidence, key_format=key_format, plan_name=name)
            plan_bundle = analyzer.analyze()

        console.print(f"[green]✓[/green] Found {len(plan_bundle.features)} features")
        console.print(f"[green]✓[/green] Detected themes: {', '.join(plan_bundle.product.themes)}")

        # Show summary
        total_stories = sum(len(f.stories) for f in plan_bundle.features)
        console.print(f"[green]✓[/green] Total stories: {total_stories}\n")

        # Generate plan file
        out.parent.mkdir(parents=True, exist_ok=True)
        generator = PlanGenerator()
        generator.generate(plan_bundle, out)

        console.print("[bold green]✓ Import complete![/bold green]")
        console.print(f"[dim]Plan bundle written to: {out}[/dim]")

        # Validate generated plan
        is_valid, error, _ = validate_plan_bundle(out)
        if is_valid:
            console.print("[green]✓ Plan validation passed[/green]")
        else:
            console.print(f"[yellow]⚠ Plan validation warning: {error}[/yellow]")

        # Generate report
        report_content = f"""# Brownfield Import Report

## Repository: {repo}

## Summary
- **Features Found**: {len(plan_bundle.features)}
- **Total Stories**: {total_stories}
- **Detected Themes**: {", ".join(plan_bundle.product.themes)}
- **Confidence Threshold**: {confidence}

## Output Files
- **Plan Bundle**: `{out}`
- **Import Report**: `{report}`

## Features

"""
        for feature in plan_bundle.features:
            report_content += f"### {feature.title} ({feature.key})\n"
            report_content += f"- **Stories**: {len(feature.stories)}\n"
            report_content += f"- **Confidence**: {feature.confidence}\n"
            report_content += f"- **Outcomes**: {', '.join(feature.outcomes)}\n\n"

        report.write_text(report_content)
        console.print(f"[dim]Report written to: {report}[/dim]")

    except Exception as e:
        console.print(f"[bold red]✗ Import failed:[/bold red] {e}")
        raise typer.Exit(1) from e

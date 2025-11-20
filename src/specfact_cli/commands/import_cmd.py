"""
Import command - Import codebases and Spec-Kit projects to contract-driven format.

This module provides commands for importing existing codebases (brownfield) and
Spec-Kit projects and converting them to SpecFact contract-driven format.
"""

from __future__ import annotations

from pathlib import Path

import typer
from beartype import beartype
from icontract import ensure, require
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from specfact_cli.telemetry import telemetry


app = typer.Typer(help="Import codebases and Spec-Kit projects to contract format")
console = Console()


def _is_valid_repo_path(path: Path) -> bool:
    """Check if path exists and is a directory."""
    return path.exists() and path.is_dir()


def _is_valid_output_path(path: Path | None) -> bool:
    """Check if output path exists if provided."""
    return path is None or path.exists()


def _count_python_files(repo: Path) -> int:
    """Count Python files for anonymized telemetry metrics."""
    return sum(1 for _ in repo.rglob("*.py"))


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
    report: Path | None = typer.Option(
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

    telemetry_metadata = {
        "dry_run": dry_run,
        "write": write,
        "force": force,
    }

    with telemetry.track_command("import.from_spec_kit", telemetry_metadata) as record:
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
            record({"dry_run": True, "features_found": len(structure.get("feature_dirs", []))})
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
                _semgrep_path = converter.generate_semgrep_rules()  # Not used yet
                progress.update(task, description="✓ Semgrep rules generated")

                # Step 5: Generate GitHub Action workflow
                task = progress.add_task("Generating GitHub Action workflow...", total=None)
                repo_name = repo.name if isinstance(repo, Path) else None
                _workflow_path = converter.generate_github_action(repo_name=repo_name)  # Not used yet
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

        # Record import results
        if protocol and plan_bundle:
            record(
                {
                    "states_found": len(protocol.states),
                    "transitions": len(protocol.transitions),
                    "features_extracted": len(plan_bundle.features),
                    "total_stories": sum(len(f.stories) for f in plan_bundle.features),
                }
            )


@app.command("from-code")
@require(lambda repo: _is_valid_repo_path(repo), "Repo path must exist and be directory")
@require(lambda confidence: 0.0 <= confidence <= 1.0, "Confidence must be 0.0-1.0")
@ensure(lambda out: _is_valid_output_path(out), "Output path must exist if provided")
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
    name: str | None = typer.Option(
        None,
        "--name",
        help="Custom plan name (will be sanitized for filesystem, default: 'auto-derived')",
    ),
    out: Path | None = typer.Option(
        None,
        "--out",
        help="Output plan bundle path (default: .specfact/plans/<name>-<timestamp>.bundle.yaml)",
    ),
    shadow_only: bool = typer.Option(
        False,
        "--shadow-only",
        help="Shadow mode - observe without enforcing",
    ),
    report: Path | None = typer.Option(
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
    enrichment: Path | None = typer.Option(
        None,
        "--enrichment",
        help="Path to Markdown enrichment report from LLM (applies missing features, confidence adjustments, business context)",
    ),
    enrich_for_speckit: bool = typer.Option(
        False,
        "--enrich-for-speckit",
        help="Automatically enrich plan for Spec-Kit compliance (runs plan review, adds testable acceptance criteria, ensures ≥2 stories per feature)",
    ),
    entry_point: Path | None = typer.Option(
        None,
        "--entry-point",
        help="Subdirectory path for partial analysis (relative to repo root). Analyzes only files within this directory and subdirectories.",
    ),
) -> None:
    """
    Import plan bundle from existing codebase (one-way import).

    Analyzes code structure using AI-first semantic understanding or AST-based fallback
    to generate a plan bundle that represents the current system.

    Supports dual-stack enrichment workflow: apply LLM-generated enrichment report
    to refine the auto-detected plan bundle (add missing features, adjust confidence scores,
    add business context).

    Example:
        specfact import from-code --repo . --out brownfield-plan.yaml
        specfact import from-code --repo . --enrichment enrichment-report.md
    """
    from specfact_cli.agents.analyze_agent import AnalyzeAgent
    from specfact_cli.agents.registry import get_agent
    from specfact_cli.cli import get_current_mode
    from specfact_cli.modes import get_router

    mode = get_current_mode()

    # Route command based on mode
    router = get_router()
    routing_result = router.route("import from-code", mode, {"repo": str(repo), "confidence": confidence})

    python_file_count = _count_python_files(repo)

    from specfact_cli.generators.plan_generator import PlanGenerator
    from specfact_cli.utils.structure import SpecFactStructure
    from specfact_cli.validators.schema import validate_plan_bundle

    # Ensure .specfact structure exists in the repository being imported
    SpecFactStructure.ensure_structure(repo)

    # Use default paths if not specified (relative to repo)
    # If enrichment is provided, try to derive original plan path and create enriched copy
    original_plan_path: Path | None = None
    if enrichment and enrichment.exists():
        original_plan_path = SpecFactStructure.get_plan_bundle_from_enrichment(enrichment, base_path=repo)
        if original_plan_path:
            # Create enriched plan path with clear label
            out = SpecFactStructure.get_enriched_plan_path(original_plan_path, base_path=repo)
        else:
            # Enrichment provided but original plan not found, use default naming
            out = SpecFactStructure.get_timestamped_brownfield_report(repo, name=name)
    elif out is None:
        out = SpecFactStructure.get_timestamped_brownfield_report(repo, name=name)

    if report is None:
        report = SpecFactStructure.get_brownfield_analysis_path(repo)

    console.print(f"[bold cyan]Importing repository:[/bold cyan] {repo}")
    console.print(f"[dim]Confidence threshold: {confidence}[/dim]")

    if shadow_only:
        console.print("[yellow]→ Shadow mode - observe without enforcement[/yellow]")

    telemetry_metadata = {
        "mode": mode.value,
        "execution_mode": routing_result.execution_mode,
        "files_analyzed": python_file_count,
        "shadow_mode": shadow_only,
    }

    with telemetry.track_command("import.from_code", telemetry_metadata) as record_event:
        try:
            # If enrichment is provided and original plan exists, load it instead of analyzing
            if enrichment and original_plan_path and original_plan_path.exists():
                console.print(f"[dim]Loading original plan for enrichment: {original_plan_path.name}[/dim]")
                import yaml

                from specfact_cli.models.plan import PlanBundle

                with original_plan_path.open() as f:
                    plan_data = yaml.safe_load(f)
                plan_bundle = PlanBundle.model_validate(plan_data)
                total_stories = sum(len(f.stories) for f in plan_bundle.features)
                console.print(
                    f"[green]✓[/green] Loaded original plan: {len(plan_bundle.features)} features, {total_stories} stories"
                )
            else:
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

                        console.print(
                            "\n[yellow]⏱️  Note: This analysis may take 2+ minutes for large codebases[/yellow]"
                        )
                        if entry_point:
                            console.print(f"[cyan]🔍 Analyzing codebase (scoped to {entry_point})...[/cyan]\n")
                        else:
                            console.print("[cyan]🔍 Analyzing codebase (AST-based fallback)...[/cyan]\n")
                        analyzer = CodeAnalyzer(
                            repo,
                            confidence_threshold=confidence,
                            key_format=key_format,
                            plan_name=name,
                            entry_point=entry_point,
                        )
                        plan_bundle = analyzer.analyze()
                else:
                    # CI/CD mode: use AST-based import (no LLM available)
                    console.print("[dim]Mode: CI/CD (AST-based import)[/dim]")
                    from specfact_cli.analyzers.code_analyzer import CodeAnalyzer

                    console.print("\n[yellow]⏱️  Note: This analysis may take 2+ minutes for large codebases[/yellow]")
                    if entry_point:
                        console.print(f"[cyan]🔍 Analyzing codebase (scoped to {entry_point})...[/cyan]\n")
                    else:
                        console.print("[cyan]🔍 Analyzing codebase...[/cyan]\n")
                    analyzer = CodeAnalyzer(
                        repo,
                        confidence_threshold=confidence,
                        key_format=key_format,
                        plan_name=name,
                        entry_point=entry_point,
                    )
                    plan_bundle = analyzer.analyze()

                console.print(f"[green]✓[/green] Found {len(plan_bundle.features)} features")
                console.print(f"[green]✓[/green] Detected themes: {', '.join(plan_bundle.product.themes)}")

                # Show summary
                total_stories = sum(len(f.stories) for f in plan_bundle.features)
                console.print(f"[green]✓[/green] Total stories: {total_stories}\n")

                record_event({"features_detected": len(plan_bundle.features), "stories_detected": total_stories})

            # Apply enrichment if provided
            if enrichment:
                if not enrichment.exists():
                    console.print(f"[bold red]✗ Enrichment report not found: {enrichment}[/bold red]")
                    raise typer.Exit(1)

                console.print(f"\n[cyan]📝 Applying enrichment from: {enrichment}[/cyan]")
                from specfact_cli.utils.enrichment_parser import EnrichmentParser, apply_enrichment

                try:
                    parser = EnrichmentParser()
                    enrichment_report = parser.parse(enrichment)
                    plan_bundle = apply_enrichment(plan_bundle, enrichment_report)

                    # Report enrichment results
                    if enrichment_report.missing_features:
                        console.print(
                            f"[green]✓[/green] Added {len(enrichment_report.missing_features)} missing features"
                        )
                    if enrichment_report.confidence_adjustments:
                        console.print(
                            f"[green]✓[/green] Adjusted confidence for {len(enrichment_report.confidence_adjustments)} features"
                        )
                    if enrichment_report.business_context.get("priorities") or enrichment_report.business_context.get(
                        "constraints"
                    ):
                        console.print("[green]✓[/green] Applied business context")

                    # Update enrichment metrics
                    record_event(
                        {
                            "enrichment_applied": True,
                            "features_added": len(enrichment_report.missing_features),
                            "confidence_adjusted": len(enrichment_report.confidence_adjustments),
                        }
                    )
                except Exception as e:
                    console.print(f"[bold red]✗ Failed to apply enrichment: {e}[/bold red]")
                    raise typer.Exit(1) from e

            # Generate plan file
            out.parent.mkdir(parents=True, exist_ok=True)
            generator = PlanGenerator()
            generator.generate(plan_bundle, out)

            console.print("[bold green]✓ Import complete![/bold green]")
            if enrichment and original_plan_path and original_plan_path.exists():
                console.print(f"[dim]Original plan: {original_plan_path.name}[/dim]")
                console.print(f"[dim]Enriched plan: {out.name}[/dim]")
            else:
                console.print(f"[dim]Plan bundle written to: {out}[/dim]")

            # Suggest constitution bootstrap for brownfield imports
            specify_dir = repo / ".specify" / "memory"
            constitution_path = specify_dir / "constitution.md"
            if not constitution_path.exists() or (
                constitution_path.exists()
                and constitution_path.read_text(encoding="utf-8").strip() in ("", "# Constitution")
            ):
                # Auto-generate in test mode, prompt in interactive mode
                import os

                # Check for test environment (TEST_MODE or PYTEST_CURRENT_TEST)
                is_test_env = os.environ.get("TEST_MODE") == "true" or os.environ.get("PYTEST_CURRENT_TEST") is not None
                if is_test_env:
                    # Auto-generate bootstrap constitution in test mode
                    from specfact_cli.enrichers.constitution_enricher import ConstitutionEnricher

                    specify_dir.mkdir(parents=True, exist_ok=True)
                    enricher = ConstitutionEnricher()
                    enriched_content = enricher.bootstrap(repo, constitution_path)
                    constitution_path.write_text(enriched_content, encoding="utf-8")
                else:
                    # Check if we're in an interactive environment
                    import sys

                    is_interactive = (hasattr(sys.stdin, "isatty") and sys.stdin.isatty()) and sys.stdin.isatty()
                    if is_interactive:
                        console.print()
                        console.print(
                            "[bold cyan]💡 Tip:[/bold cyan] Generate project constitution for Spec-Kit integration"
                        )
                        suggest_constitution = typer.confirm(
                            "Generate bootstrap constitution from repository analysis?",
                            default=True,
                        )
                        if suggest_constitution:
                            from specfact_cli.enrichers.constitution_enricher import ConstitutionEnricher

                            console.print("[dim]Generating bootstrap constitution...[/dim]")
                            specify_dir.mkdir(parents=True, exist_ok=True)
                            enricher = ConstitutionEnricher()
                            enriched_content = enricher.bootstrap(repo, constitution_path)
                            constitution_path.write_text(enriched_content, encoding="utf-8")
                            console.print("[bold green]✓[/bold green] Bootstrap constitution generated")
                            console.print(f"[dim]Review and adjust: {constitution_path}[/dim]")
                            console.print(
                                "[dim]Then run 'specfact sync spec-kit' to sync with Spec-Kit artifacts[/dim]"
                            )
                    else:
                        # Non-interactive mode: skip prompt
                        console.print()
                        console.print(
                            "[dim]💡 Tip: Run 'specfact constitution bootstrap --repo .' to generate constitution[/dim]"
                        )

            # Enrich for Spec-Kit compliance if requested
            if enrich_for_speckit:
                console.print("\n[cyan]🔧 Enriching plan for Spec-Kit compliance...[/cyan]")
                try:
                    from specfact_cli.analyzers.ambiguity_scanner import AmbiguityScanner

                    # Run plan review to identify gaps
                    console.print("[dim]Running plan review to identify gaps...[/dim]")
                    scanner = AmbiguityScanner()
                    _ambiguity_report = scanner.scan(plan_bundle)  # Scanned but not used in auto-enrichment

                    # Add missing stories for features with only 1 story
                    features_with_one_story = [f for f in plan_bundle.features if len(f.stories) == 1]
                    if features_with_one_story:
                        console.print(
                            f"[yellow]⚠ Found {len(features_with_one_story)} features with only 1 story[/yellow]"
                        )
                        console.print("[dim]Adding edge case stories for better Spec-Kit compliance...[/dim]")

                        for feature in features_with_one_story:
                            # Generate edge case story based on feature title
                            edge_case_title = f"As a user, I receive error handling for {feature.title.lower()}"
                            edge_case_acceptance = [
                                "Must verify error conditions are handled gracefully",
                                "Must validate error messages are clear and actionable",
                                "Must ensure system recovers from errors",
                            ]

                            # Find next story number - extract from existing story keys
                            existing_story_nums = []
                            for s in feature.stories:
                                # Story keys are like STORY-CLASSNAME-001 or STORY-001
                                parts = s.key.split("-")
                                if len(parts) >= 2:
                                    # Get the last part which should be the number
                                    last_part = parts[-1]
                                    if last_part.isdigit():
                                        existing_story_nums.append(int(last_part))

                            next_story_num = max(existing_story_nums) + 1 if existing_story_nums else 2

                            # Extract class name from feature key (FEATURE-CLASSNAME -> CLASSNAME)
                            feature_key_parts = feature.key.split("-")
                            if len(feature_key_parts) >= 2:
                                class_name = feature_key_parts[-1]  # Get last part (CLASSNAME)
                                story_key = f"STORY-{class_name}-{next_story_num:03d}"
                            else:
                                # Fallback if feature key format is unexpected
                                story_key = f"STORY-{next_story_num:03d}"

                            from specfact_cli.models.plan import Story

                            edge_case_story = Story(
                                key=story_key,
                                title=edge_case_title,
                                acceptance=edge_case_acceptance,
                                story_points=3,
                                value_points=None,
                                confidence=0.8,
                                scenarios=None,
                                contracts=None,
                            )
                            feature.stories.append(edge_case_story)

                        # Regenerate plan with new stories
                        generator = PlanGenerator()
                        generator.generate(plan_bundle, out)
                        console.print(
                            f"[green]✓ Added edge case stories to {len(features_with_one_story)} features[/green]"
                        )

                    # Ensure testable acceptance criteria
                    features_updated = 0
                    for feature in plan_bundle.features:
                        for story in feature.stories:
                            # Check if acceptance criteria are testable
                            testable_count = sum(
                                1
                                for acc in story.acceptance
                                if any(
                                    keyword in acc.lower()
                                    for keyword in ["must", "should", "verify", "validate", "ensure"]
                                )
                            )

                            if testable_count < len(story.acceptance) and len(story.acceptance) > 0:
                                # Enhance acceptance criteria to be more testable
                                enhanced_acceptance = []
                                for acc in story.acceptance:
                                    if not any(
                                        keyword in acc.lower()
                                        for keyword in ["must", "should", "verify", "validate", "ensure"]
                                    ):
                                        # Convert to testable format
                                        if acc.startswith(("User can", "System can")):
                                            enhanced_acceptance.append(f"Must verify {acc.lower()}")
                                        else:
                                            enhanced_acceptance.append(f"Must verify {acc}")
                                    else:
                                        enhanced_acceptance.append(acc)

                                story.acceptance = enhanced_acceptance
                                features_updated += 1

                    if features_updated > 0:
                        # Regenerate plan with enhanced acceptance criteria
                        generator = PlanGenerator()
                        generator.generate(plan_bundle, out)
                        console.print(f"[green]✓ Enhanced acceptance criteria for {features_updated} stories[/green]")

                    console.print("[green]✓ Spec-Kit enrichment complete[/green]")

                except Exception as e:
                    console.print(f"[yellow]⚠ Spec-Kit enrichment failed: {e}[/yellow]")
                    console.print("[dim]Plan is still valid, but may need manual enrichment[/dim]")

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
"""
            if enrichment and original_plan_path and original_plan_path.exists():
                report_content += f"""
## Enrichment Applied
- **Original Plan**: `{original_plan_path}`
- **Enriched Plan**: `{out}`
- **Enrichment Report**: `{enrichment}`
"""
            report_content += f"""
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

            # Type guard: report is guaranteed to be Path after line 323
            assert report is not None, "Report path must be set"
            report.write_text(report_content)
            console.print(f"[dim]Report written to: {report}[/dim]")

        except Exception as e:
            console.print(f"[bold red]✗ Import failed:[/bold red] {e}")
            raise typer.Exit(1) from e

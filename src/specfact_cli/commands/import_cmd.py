"""
Import command - Import codebases and external tool projects to contract-driven format.

This module provides commands for importing existing codebases (brownfield) and
external tool projects (e.g., Spec-Kit, Linear, Jira) and converting them to
SpecFact contract-driven format using the bridge architecture.
"""

from __future__ import annotations

from pathlib import Path

import typer
from beartype import beartype
from icontract import require
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from specfact_cli import runtime
from specfact_cli.models.bridge import AdapterType
from specfact_cli.models.plan import Feature, PlanBundle
from specfact_cli.models.project import BundleManifest, BundleVersions, ProjectBundle
from specfact_cli.telemetry import telemetry
from specfact_cli.utils.bundle_loader import save_project_bundle


app = typer.Typer(help="Import codebases and external tool projects (e.g., Spec-Kit, Linear, Jira) to contract format")
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


def _convert_plan_bundle_to_project_bundle(plan_bundle: PlanBundle, bundle_name: str) -> ProjectBundle:
    """
    Convert PlanBundle (monolithic) to ProjectBundle (modular).

    Args:
        plan_bundle: PlanBundle instance to convert
        bundle_name: Project bundle name

    Returns:
        ProjectBundle instance
    """

    # Create manifest
    manifest = BundleManifest(
        versions=BundleVersions(schema="1.0", project="0.1.0"),
        schema_metadata=None,
        project_metadata=None,
    )

    # Convert features list to dict
    features_dict: dict[str, Feature] = {f.key: f for f in plan_bundle.features}

    # Create and return ProjectBundle
    return ProjectBundle(
        manifest=manifest,
        bundle_name=bundle_name,
        idea=plan_bundle.idea,
        business=plan_bundle.business,
        product=plan_bundle.product,
        features=features_dict,
        clarifications=plan_bundle.clarifications,
    )


@app.command("from-bridge")
def from_bridge(
    repo: Path = typer.Option(
        Path("."),
        "--repo",
        help="Path to repository with external tool artifacts",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    adapter: str = typer.Option(
        "speckit",
        "--adapter",
        help="Adapter type (speckit, generic-markdown). Default: auto-detect",
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
    Convert external tool project to SpecFact contract format using bridge architecture.

    This command uses bridge configuration to scan an external tool repository
    (e.g., Spec-Kit, Linear, Jira), parse its structure, and generate equivalent
    SpecFact contracts, protocols, and plans.

    Supported adapters:
    - speckit: Spec-Kit projects (specs/, .specify/)
    - generic-markdown: Generic markdown-based specifications

    Example:
        specfact import from-bridge --repo ./my-project --adapter speckit --write
        specfact import from-bridge --repo ./my-project --write  # Auto-detect adapter
    """
    from specfact_cli.sync.bridge_probe import BridgeProbe
    from specfact_cli.utils.structure import SpecFactStructure

    # Auto-detect adapter if not specified
    if adapter == "speckit" or adapter == "auto":
        probe = BridgeProbe(repo)
        detected_capabilities = probe.detect()
        adapter = "speckit" if detected_capabilities.tool == "speckit" else "generic-markdown"

    # Validate adapter
    try:
        adapter_type = AdapterType(adapter.lower())
    except ValueError as err:
        console.print(f"[bold red]✗[/bold red] Unsupported adapter: {adapter}")
        console.print(f"[dim]Supported adapters: {', '.join([a.value for a in AdapterType])}[/dim]")
        raise typer.Exit(1) from err

    # For now, Spec-Kit adapter uses legacy converters (will be migrated to bridge)
    spec_kit_scanner = None
    spec_kit_converter = None
    if adapter_type == AdapterType.SPECKIT:
        from specfact_cli.importers.speckit_converter import SpecKitConverter
        from specfact_cli.importers.speckit_scanner import SpecKitScanner

        spec_kit_scanner = SpecKitScanner
        spec_kit_converter = SpecKitConverter

    telemetry_metadata = {
        "adapter": adapter,
        "dry_run": dry_run,
        "write": write,
        "force": force,
    }

    with telemetry.track_command("import.from_bridge", telemetry_metadata) as record:
        console.print(f"[bold cyan]Importing {adapter_type.value} project from:[/bold cyan] {repo}")

        # Use bridge-based import for supported adapters
        if adapter_type == AdapterType.SPECKIT:
            # Legacy Spec-Kit import (will be migrated to bridge)
            if spec_kit_scanner is None:
                msg = "SpecKitScanner not available"
                raise RuntimeError(msg)
            scanner = spec_kit_scanner(repo)

            if not scanner.is_speckit_repo():
                console.print(f"[bold red]✗[/bold red] Not a {adapter_type.value} repository")
                console.print("[dim]Expected: .specify/ directory[/dim]")
                console.print("[dim]Tip: Use 'specfact bridge probe' to auto-detect tool configuration[/dim]")
                raise typer.Exit(1)
        else:
            # Generic bridge-based import
            # bridge_sync = BridgeSync(repo)  # TODO: Use when implementing generic markdown import
            console.print(f"[bold green]✓[/bold green] Using bridge adapter: {adapter_type.value}")
            console.print("[yellow]⚠ Generic markdown adapter import is not yet fully implemented[/yellow]")
            console.print("[dim]Falling back to Spec-Kit adapter for now[/dim]")
            # TODO: Implement generic markdown import via bridge
            raise typer.Exit(1)

        if adapter_type == AdapterType.SPECKIT:
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
            task = progress.add_task(f"Discovering {adapter_type.value} features...", total=None)
            features = scanner.discover_features()
            if not features:
                console.print(f"[bold red]✗[/bold red] No features found in {adapter_type.value} repository")
                console.print("[dim]Expected: specs/*/spec.md files (or bridge-configured paths)[/dim]")
                console.print("[dim]Tip: Use 'specfact bridge probe' to validate bridge configuration[/dim]")
                raise typer.Exit(1)
            progress.update(task, description=f"✓ Discovered {len(features)} features")

            # Step 2: Convert protocol
            task = progress.add_task("Converting protocol...", total=None)
            if spec_kit_converter is None:
                msg = "SpecKitConverter not available"
                raise RuntimeError(msg)
            converter = spec_kit_converter(repo)
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
            report_content = f"""# {adapter_type.value.upper()} Import Report

## Repository: {repo}
## Adapter: {adapter_type.value}

## Summary
- **States Found**: {len(protocol.states)}
- **Transitions**: {len(protocol.transitions)}
- **Features Extracted**: {len(plan_bundle.features)}
- **Total Stories**: {sum(len(f.stories) for f in plan_bundle.features)}

## Generated Files
- **Protocol**: `.specfact/protocols/workflow.protocol.yaml`
- **Plan Bundle**: `.specfact/projects/<bundle-name>/`
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

        # Save plan bundle as ProjectBundle (modular structure)
        if plan_bundle:
            bundle_name = "main"  # Default bundle name for bridge imports
            project_bundle = _convert_plan_bundle_to_project_bundle(plan_bundle, bundle_name)
            bundle_dir = SpecFactStructure.project_dir(base_path=repo, bundle_name=bundle_name)
            SpecFactStructure.ensure_project_structure(base_path=repo, bundle_name=bundle_name)
            save_project_bundle(project_bundle, bundle_dir, atomic=True)
            console.print(f"[dim]Project bundle: .specfact/projects/{bundle_name}/[/dim]")

        console.print("[bold green]✓[/bold green] Import complete!")
        console.print("[dim]Protocol: .specfact/protocols/workflow.protocol.yaml[/dim]")
        console.print("[dim]Plan: .specfact/projects/<bundle-name>/ (modular bundle)[/dim]")
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
@require(lambda bundle: isinstance(bundle, str) and len(bundle) > 0, "Bundle name must be non-empty string")
@require(lambda confidence: 0.0 <= confidence <= 1.0, "Confidence must be 0.0-1.0")
@beartype
def from_code(
    bundle: str = typer.Argument(..., help="Project bundle name (e.g., legacy-api, auth-module)"),
    repo: Path = typer.Option(
        Path("."),
        "--repo",
        help="Path to repository to import",
        exists=True,
        file_okay=False,
        dir_okay=True,
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
        specfact import from-code legacy-api --repo .
        specfact import from-code auth-module --repo . --enrichment enrichment-report.md
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

    from specfact_cli.utils.structure import SpecFactStructure

    # Ensure .specfact structure exists in the repository being imported
    SpecFactStructure.ensure_structure(repo)

    # Get project bundle directory
    bundle_dir = SpecFactStructure.project_dir(base_path=repo, bundle_name=bundle)
    # Allow existing bundle if enrichment is provided (enrichment workflow updates existing bundle)
    if bundle_dir.exists() and not enrichment:
        console.print(f"[bold red]✗[/bold red] Project bundle already exists: {bundle_dir}")
        console.print("[dim]Use a different bundle name or remove the existing bundle[/dim]")
        console.print("[dim]Or use --enrichment to update existing bundle with enrichment report[/dim]")
        raise typer.Exit(1)

    # Ensure project structure exists
    SpecFactStructure.ensure_project_structure(base_path=repo, bundle_name=bundle)

    if report is None:
        report = SpecFactStructure.get_brownfield_analysis_path(repo)

    console.print(f"[bold cyan]Importing repository:[/bold cyan] {repo}")
    console.print(f"[bold cyan]Project bundle:[/bold cyan] {bundle}")
    console.print(f"[dim]Confidence threshold: {confidence}[/dim]")

    if shadow_only:
        console.print("[yellow]→ Shadow mode - observe without enforcement[/yellow]")

    telemetry_metadata = {
        "bundle": bundle,
        "mode": mode.value,
        "execution_mode": routing_result.execution_mode,
        "files_analyzed": python_file_count,
        "shadow_mode": shadow_only,
    }

    with telemetry.track_command("import.from_code", telemetry_metadata) as record_event:
        try:
            # If enrichment is provided, try to load existing bundle
            # Note: For now, enrichment workflow needs to be updated for modular bundles
            # TODO: Phase 4 - Update enrichment to work with modular bundles
            plan_bundle: PlanBundle | None = None
            if enrichment:
                # Try to load existing bundle from bundle_dir
                from specfact_cli.utils.bundle_loader import load_project_bundle

                try:
                    existing_bundle = load_project_bundle(bundle_dir)
                    # Convert ProjectBundle to PlanBundle for enrichment (temporary)
                    from specfact_cli.models.plan import PlanBundle as PlanBundleModel

                    plan_bundle = PlanBundleModel(
                        version="1.0",
                        idea=existing_bundle.idea,
                        business=existing_bundle.business,
                        product=existing_bundle.product,
                        features=list(existing_bundle.features.values()),
                        metadata=None,
                        clarifications=existing_bundle.clarifications,
                    )
                    total_stories = sum(len(f.stories) for f in plan_bundle.features)
                    console.print(
                        f"[green]✓[/green] Loaded existing bundle: {len(plan_bundle.features)} features, {total_stories} stories"
                    )
                except Exception:
                    # Bundle doesn't exist yet, will be created from analysis
                    plan_bundle = None
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
                        plan_bundle = agent.analyze_codebase(repo, confidence=confidence, plan_name=bundle)
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
                            plan_name=bundle,
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
                        plan_name=bundle,
                        entry_point=entry_point,
                    )
                    plan_bundle = analyzer.analyze()

                # Ensure plan_bundle is not None
                if plan_bundle is None:
                    console.print("[bold red]✗ Failed to analyze codebase[/bold red]")
                    raise typer.Exit(1)

                console.print(f"[green]✓[/green] Found {len(plan_bundle.features)} features")
                console.print(f"[green]✓[/green] Detected themes: {', '.join(plan_bundle.product.themes)}")

                # Show summary
                total_stories = sum(len(f.stories) for f in plan_bundle.features)
                console.print(f"[green]✓[/green] Total stories: {total_stories}\n")

                record_event({"features_detected": len(plan_bundle.features), "stories_detected": total_stories})

            # Ensure plan_bundle is not None before proceeding
            if plan_bundle is None:
                console.print("[bold red]✗ No plan bundle available[/bold red]")
                raise typer.Exit(1)

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

            # Convert PlanBundle to ProjectBundle and save
            project_bundle = _convert_plan_bundle_to_project_bundle(plan_bundle, bundle)
            save_project_bundle(project_bundle, bundle_dir, atomic=True)

            console.print("[bold green]✓ Import complete![/bold green]")
            console.print(f"[dim]Project bundle written to: {bundle_dir}[/dim]")

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
                    if runtime.is_interactive():
                        console.print()
                        console.print(
                            "[bold cyan]💡 Tip:[/bold cyan] Generate project constitution for tool integration"
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
                                "[dim]Then run 'specfact sync bridge --adapter <tool>' to sync with external tool artifacts[/dim]"
                            )
                    else:
                        # Non-interactive mode: skip prompt
                        console.print()
                        console.print(
                            "[dim]💡 Tip: Run 'specfact constitution bootstrap --repo .' to generate constitution[/dim]"
                        )

            # Enrich for tool compliance if requested
            if enrich_for_speckit:
                console.print("\n[cyan]🔧 Enriching plan for tool compliance...[/cyan]")
                try:
                    from specfact_cli.analyzers.ambiguity_scanner import AmbiguityScanner

                    # Run plan review to identify gaps
                    console.print("[dim]Running plan review to identify gaps...[/dim]")
                    scanner = AmbiguityScanner()
                    # Ensure plan_bundle is not None
                    if plan_bundle is None:
                        console.print("[yellow]⚠ Cannot enrich: plan bundle is None[/yellow]")
                        return
                    _ambiguity_report = scanner.scan(plan_bundle)  # Scanned but not used in auto-enrichment

                    # Add missing stories for features with only 1 story
                    features_with_one_story = [f for f in plan_bundle.features if len(f.stories) == 1]
                    if features_with_one_story:
                        console.print(
                            f"[yellow]⚠ Found {len(features_with_one_story)} features with only 1 story[/yellow]"
                        )
                        console.print("[dim]Adding edge case stories for better tool compliance...[/dim]")

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

                        # Note: Plan will be saved as ProjectBundle at the end
                        # No need to regenerate monolithic bundle during enrichment
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
                        # Note: Plan will be saved as ProjectBundle at the end
                        # No need to regenerate monolithic bundle during enrichment
                        console.print(f"[green]✓ Enhanced acceptance criteria for {features_updated} stories[/green]")

                    console.print("[green]✓ Tool enrichment complete[/green]")

                except Exception as e:
                    console.print(f"[yellow]⚠ Tool enrichment failed: {e}[/yellow]")
                    console.print("[dim]Plan is still valid, but may need manual enrichment[/dim]")

            # Note: Validation will be done after conversion to ProjectBundle
            # TODO: Add ProjectBundle validation

            # Generate report
            # Ensure plan_bundle is not None and total_stories is set
            if plan_bundle is None:
                console.print("[bold red]✗ Cannot generate report: plan bundle is None[/bold red]")
                raise typer.Exit(1)

            total_stories = sum(len(f.stories) for f in plan_bundle.features)

            report_content = f"""# Brownfield Import Report

## Repository: {repo}

## Summary
- **Features Found**: {len(plan_bundle.features)}
- **Total Stories**: {total_stories}
- **Detected Themes**: {", ".join(plan_bundle.product.themes)}
- **Confidence Threshold**: {confidence}
"""
            if enrichment:
                report_content += f"""
## Enrichment Applied
- **Enrichment Report**: `{enrichment}`
"""
            report_content += f"""
## Output Files
- **Project Bundle**: `{bundle_dir}`
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

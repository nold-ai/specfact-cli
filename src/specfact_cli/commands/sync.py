"""
Sync command - Bidirectional synchronization for Spec-Kit and repositories.

This module provides commands for synchronizing changes between Spec-Kit artifacts,
repository changes, and SpecFact plans.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

import typer
from beartype import beartype
from icontract import ensure, require
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from specfact_cli.models.plan import PlanBundle
from specfact_cli.sync.speckit_sync import SpecKitSync
from specfact_cli.telemetry import telemetry


app = typer.Typer(help="Synchronize Spec-Kit artifacts and repository changes")
console = Console()


def _is_test_mode() -> bool:
    """Check if running in test mode."""
    # Check for TEST_MODE environment variable
    if os.environ.get("TEST_MODE") == "true":
        return True
    # Check if running under pytest (common patterns)
    import sys

    return any("pytest" in arg or "test" in arg.lower() for arg in sys.argv) or "pytest" in sys.modules


@beartype
@require(lambda repo: repo.exists(), "Repository path must exist")
@require(lambda repo: repo.is_dir(), "Repository path must be a directory")
@require(lambda bidirectional: isinstance(bidirectional, bool), "Bidirectional must be bool")
@require(lambda plan: plan is None or isinstance(plan, Path), "Plan must be None or Path")
@require(lambda overwrite: isinstance(overwrite, bool), "Overwrite must be bool")
@ensure(lambda result: result is None, "Must return None")
def _perform_sync_operation(
    repo: Path,
    bidirectional: bool,
    plan: Path | None,
    overwrite: bool,
) -> None:
    """
    Perform sync operation without watch mode.

    This is extracted to avoid recursion when called from watch mode callback.

    Args:
        repo: Path to repository
        bidirectional: Enable bidirectional sync
        plan: Path to SpecFact plan bundle
        overwrite: Overwrite existing Spec-Kit artifacts
    """
    from specfact_cli.importers.speckit_converter import SpecKitConverter
    from specfact_cli.importers.speckit_scanner import SpecKitScanner
    from specfact_cli.utils.structure import SpecFactStructure
    from specfact_cli.validators.schema import validate_plan_bundle

    # Step 1: Detect Spec-Kit repository
    scanner = SpecKitScanner(repo)
    if not scanner.is_speckit_repo():
        console.print("[bold red]✗[/bold red] Not a Spec-Kit repository")
        console.print("[dim]Expected Spec-Kit structure (.specify/ directory)[/dim]")
        raise typer.Exit(1)

    console.print("[bold green]✓[/bold green] Detected Spec-Kit repository")

    # Step 1.5: Validate constitution exists and is not empty
    has_constitution, constitution_error = scanner.has_constitution()
    if not has_constitution:
        console.print("[bold red]✗[/bold red] Constitution required")
        console.print(f"[red]{constitution_error}[/red]")
        console.print("\n[bold yellow]Next Steps:[/bold yellow]")
        console.print("1. Run 'specfact constitution bootstrap --repo .' to auto-generate constitution")
        console.print("2. Or run '/speckit.constitution' command in your AI assistant")
        console.print("3. Then run 'specfact sync spec-kit' again")
        raise typer.Exit(1)

    # Check if constitution is minimal and suggest bootstrap
    constitution_path = repo / ".specify" / "memory" / "constitution.md"
    if constitution_path.exists():
        from specfact_cli.commands.constitution import is_constitution_minimal

        if is_constitution_minimal(constitution_path):
            # Auto-generate in test mode, prompt in interactive mode
            # Check for test environment (TEST_MODE or PYTEST_CURRENT_TEST)
            is_test_env = os.environ.get("TEST_MODE") == "true" or os.environ.get("PYTEST_CURRENT_TEST") is not None
            if is_test_env:
                # Auto-generate bootstrap constitution in test mode
                from specfact_cli.enrichers.constitution_enricher import ConstitutionEnricher

                enricher = ConstitutionEnricher()
                enriched_content = enricher.bootstrap(repo, constitution_path)
                constitution_path.write_text(enriched_content, encoding="utf-8")
            else:
                # Check if we're in an interactive environment
                import sys

                is_interactive = (hasattr(sys.stdin, "isatty") and sys.stdin.isatty()) and sys.stdin.isatty()
                if is_interactive:
                    console.print("[yellow]⚠[/yellow] Constitution is minimal (essentially empty)")
                    suggest_bootstrap = typer.confirm(
                        "Generate bootstrap constitution from repository analysis?",
                        default=True,
                    )
                    if suggest_bootstrap:
                        from specfact_cli.enrichers.constitution_enricher import ConstitutionEnricher

                        console.print("[dim]Generating bootstrap constitution...[/dim]")
                        enricher = ConstitutionEnricher()
                        enriched_content = enricher.bootstrap(repo, constitution_path)
                        constitution_path.write_text(enriched_content, encoding="utf-8")
                        console.print("[bold green]✓[/bold green] Bootstrap constitution generated")
                        console.print("[dim]Review and adjust as needed before syncing[/dim]")
                    else:
                        console.print(
                            "[dim]Skipping bootstrap. Run 'specfact constitution bootstrap' manually if needed[/dim]"
                        )
                else:
                    # Non-interactive mode: skip prompt
                    console.print("[yellow]⚠[/yellow] Constitution is minimal (essentially empty)")
                    console.print("[dim]Run 'specfact constitution bootstrap --repo .' to generate constitution[/dim]")

    console.print("[bold green]✓[/bold green] Constitution found and validated")

    # Step 2: Detect SpecFact structure
    specfact_exists = (repo / SpecFactStructure.ROOT).exists()

    if not specfact_exists:
        console.print("[yellow]⚠[/yellow] SpecFact structure not found")
        console.print(f"[dim]Initialize with: specfact plan init --scaffold --repo {repo}[/dim]")
        # Create structure automatically
        SpecFactStructure.ensure_structure(repo)
        console.print("[bold green]✓[/bold green] Created SpecFact structure")

    if specfact_exists:
        console.print("[bold green]✓[/bold green] Detected SpecFact structure")

    sync = SpecKitSync(repo)
    converter = SpecKitConverter(repo)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Step 3: Scan Spec-Kit artifacts
        task = progress.add_task("[cyan]📦[/cyan] Scanning Spec-Kit artifacts...", total=None)
        features = scanner.discover_features()
        progress.update(task, description=f"[green]✓[/green] Found {len(features)} features in specs/")

        # Step 3.5: Validate Spec-Kit artifacts for unidirectional sync
        if not bidirectional and len(features) == 0:
            console.print("[bold red]✗[/bold red] No Spec-Kit features found")
            console.print(
                "[red]Unidirectional sync (Spec-Kit → SpecFact) requires at least one feature specification.[/red]"
            )
            console.print("\n[bold yellow]Next Steps:[/bold yellow]")
            console.print("1. Run '/speckit.specify' command in your AI assistant to create feature specifications")
            console.print("2. Optionally run '/speckit.plan' and '/speckit.tasks' to create complete artifacts")
            console.print("3. Then run 'specfact sync spec-kit' again")
            console.print(
                "\n[dim]Note: For bidirectional sync, Spec-Kit artifacts are optional if syncing from SpecFact → Spec-Kit[/dim]"
            )
            raise typer.Exit(1)

        # Step 4: Sync based on mode
        specfact_changes: dict[str, Any] = {}
        conflicts: list[dict[str, Any]] = []
        features_converted_speckit = 0

        if bidirectional:
            # Bidirectional sync: Spec-Kit → SpecFact and SpecFact → Spec-Kit
            # Step 5.1: Spec-Kit → SpecFact (unidirectional sync)
            task = progress.add_task("[cyan]📝[/cyan] Converting Spec-Kit → SpecFact...", total=None)
            merged_bundle, features_updated, features_added = _sync_speckit_to_specfact(
                repo, converter, scanner, progress
            )

            if features_updated > 0 or features_added > 0:
                progress.update(
                    task,
                    description=f"[green]✓[/green] Updated {features_updated}, Added {features_added} features",
                )
                console.print(f"[dim]  - Updated {features_updated} features[/dim]")
                console.print(f"[dim]  - Added {features_added} new features[/dim]")
            else:
                progress.update(
                    task,
                    description=f"[green]✓[/green] Created plan with {len(merged_bundle.features)} features",
                )

            # Step 5.2: SpecFact → Spec-Kit (reverse conversion)
            task = progress.add_task("[cyan]🔄[/cyan] Converting SpecFact → Spec-Kit...", total=None)

            # Detect SpecFact changes
            specfact_changes = sync.detect_specfact_changes(repo)

            if specfact_changes:
                # Load plan bundle and convert to Spec-Kit
                # Use provided plan path, or default to main plan
                if plan:
                    plan_path = plan if plan.is_absolute() else repo / plan
                else:
                    plan_path = repo / SpecFactStructure.DEFAULT_PLAN

                if plan_path.exists():
                    validation_result = validate_plan_bundle(plan_path)
                    if isinstance(validation_result, tuple):
                        is_valid, _error, plan_bundle = validation_result
                        if is_valid and plan_bundle:
                            # Handle overwrite mode
                            if overwrite:
                                # Delete existing Spec-Kit artifacts before conversion
                                specs_dir = repo / "specs"
                                if specs_dir.exists():
                                    console.print(
                                        "[yellow]⚠[/yellow] Overwrite mode: Removing existing Spec-Kit artifacts..."
                                    )
                                    shutil.rmtree(specs_dir)
                                    specs_dir.mkdir(parents=True, exist_ok=True)
                                    console.print("[green]✓[/green] Existing artifacts removed")

                            # Convert SpecFact plan bundle to Spec-Kit markdown
                            features_converted_speckit = converter.convert_to_speckit(plan_bundle)
                            progress.update(
                                task,
                                description=f"[green]✓[/green] Converted {features_converted_speckit} features to Spec-Kit",
                            )
                            mode_text = "overwritten" if overwrite else "generated"
                            console.print(
                                f"[dim]  - {mode_text.capitalize()} spec.md, plan.md, tasks.md for {features_converted_speckit} features[/dim]"
                            )
                            # Warning about Constitution Check gates
                            console.print(
                                "[yellow]⚠[/yellow] [dim]Note: Constitution Check gates in plan.md are set to PENDING - review and check gates based on your project's actual state[/dim]"
                            )
                        else:
                            progress.update(task, description="[yellow]⚠[/yellow] Plan bundle validation failed")
                            console.print("[yellow]⚠[/yellow] Could not load plan bundle for conversion")
                    else:
                        progress.update(task, description="[yellow]⚠[/yellow] Plan bundle not found")
                else:
                    progress.update(task, description="[green]✓[/green] No SpecFact plan to sync")
            else:
                progress.update(task, description="[green]✓[/green] No SpecFact changes to sync")

            # Detect conflicts between both directions
            speckit_changes = sync.detect_speckit_changes(repo)
            conflicts = sync.detect_conflicts(speckit_changes, specfact_changes)

            if conflicts:
                console.print(f"[yellow]⚠[/yellow] Found {len(conflicts)} conflicts")
                console.print("[dim]Conflicts resolved using priority rules (SpecFact > Spec-Kit for artifacts)[/dim]")
            else:
                console.print("[bold green]✓[/bold green] No conflicts detected")
        else:
            # Unidirectional sync: Spec-Kit → SpecFact
            task = progress.add_task("[cyan]📝[/cyan] Converting to SpecFact format...", total=None)

            merged_bundle, features_updated, features_added = _sync_speckit_to_specfact(
                repo, converter, scanner, progress
            )

            if features_updated > 0 or features_added > 0:
                task = progress.add_task("[cyan]🔀[/cyan] Merging with existing plan...", total=None)
                progress.update(
                    task,
                    description=f"[green]✓[/green] Updated {features_updated} features, Added {features_added} features",
                )
                console.print(f"[dim]  - Updated {features_updated} features[/dim]")
                console.print(f"[dim]  - Added {features_added} new features[/dim]")
            else:
                progress.update(
                    task, description=f"[green]✓[/green] Created plan with {len(merged_bundle.features)} features"
                )
                console.print(f"[dim]Created plan with {len(merged_bundle.features)} features[/dim]")

            # Report features synced
            console.print()
            if features:
                console.print("[bold cyan]Features synced:[/bold cyan]")
                for feature in features:
                    feature_key = feature.get("feature_key", "UNKNOWN")
                    feature_title = feature.get("title", "Unknown Feature")
                    console.print(f"  - [cyan]{feature_key}[/cyan]: {feature_title}")

        # Step 8: Output Results
        console.print()
        if bidirectional:
            console.print("[bold cyan]Sync Summary (Bidirectional):[/bold cyan]")
            console.print(f"  - Spec-Kit → SpecFact: Updated {features_updated}, Added {features_added} features")
            if specfact_changes:
                console.print(
                    f"  - SpecFact → Spec-Kit: {features_converted_speckit} features converted to Spec-Kit markdown"
                )
            else:
                console.print("  - SpecFact → Spec-Kit: No changes detected")
            if conflicts:
                console.print(f"  - Conflicts: {len(conflicts)} detected and resolved")
            else:
                console.print("  - Conflicts: None detected")

            # Post-sync validation suggestion
            if features_converted_speckit > 0:
                console.print()
                console.print("[bold cyan]Next Steps:[/bold cyan]")
                console.print("  Run '/speckit.analyze' to validate artifact consistency and quality")
                console.print("  This will check for ambiguities, duplications, and constitution alignment")
        else:
            console.print("[bold cyan]Sync Summary (Unidirectional):[/bold cyan]")
            if features:
                console.print(f"  - Features synced: {len(features)}")
            if features_updated > 0 or features_added > 0:
                console.print(f"  - Updated: {features_updated} features")
                console.print(f"  - Added: {features_added} new features")
            console.print("  - Direction: Spec-Kit → SpecFact")

            # Post-sync validation suggestion
            console.print()
            console.print("[bold cyan]Next Steps:[/bold cyan]")
            console.print("  Run '/speckit.analyze' to validate artifact consistency and quality")
            console.print("  This will check for ambiguities, duplications, and constitution alignment")

    console.print()
    console.print("[bold green]✓[/bold green] Sync complete!")


def _sync_speckit_to_specfact(repo: Path, converter: Any, scanner: Any, progress: Any) -> tuple[PlanBundle, int, int]:
    """
    Sync Spec-Kit artifacts to SpecFact format.

    Returns:
        Tuple of (merged_bundle, features_updated, features_added)
    """
    from specfact_cli.generators.plan_generator import PlanGenerator
    from specfact_cli.utils.structure import SpecFactStructure
    from specfact_cli.validators.schema import validate_plan_bundle

    plan_path = repo / SpecFactStructure.DEFAULT_PLAN
    existing_bundle: PlanBundle | None = None

    if plan_path.exists():
        validation_result = validate_plan_bundle(plan_path)
        if isinstance(validation_result, tuple):
            is_valid, _error, bundle = validation_result
            if is_valid and bundle:
                existing_bundle = bundle

    # Convert Spec-Kit to SpecFact
    converted_bundle = converter.convert_plan(None if not existing_bundle else plan_path)

    # Merge with existing plan if it exists
    features_updated = 0
    features_added = 0

    if existing_bundle:
        feature_keys_existing = {f.key for f in existing_bundle.features}

        for feature in converted_bundle.features:
            if feature.key in feature_keys_existing:
                existing_idx = next(i for i, f in enumerate(existing_bundle.features) if f.key == feature.key)
                existing_bundle.features[existing_idx] = feature
                features_updated += 1
            else:
                existing_bundle.features.append(feature)
                features_added += 1

        # Update product themes
        themes_existing = set(existing_bundle.product.themes)
        themes_new = set(converted_bundle.product.themes)
        existing_bundle.product.themes = list(themes_existing | themes_new)

        # Write merged bundle
        generator = PlanGenerator()
        generator.generate(existing_bundle, plan_path)
        return existing_bundle, features_updated, features_added
    # Write new bundle
    generator = PlanGenerator()
    generator.generate(converted_bundle, plan_path)
    return converted_bundle, 0, len(converted_bundle.features)


@app.command("spec-kit")
def sync_spec_kit(
    repo: Path = typer.Option(
        Path("."),
        "--repo",
        help="Path to repository",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    bidirectional: bool = typer.Option(
        False,
        "--bidirectional",
        help="Enable bidirectional sync (Spec-Kit ↔ SpecFact)",
    ),
    plan: Path | None = typer.Option(
        None,
        "--plan",
        help="Path to SpecFact plan bundle for SpecFact → Spec-Kit conversion (default: .specfact/plans/main.bundle.yaml)",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite existing Spec-Kit artifacts (delete all existing before sync)",
    ),
    watch: bool = typer.Option(
        False,
        "--watch",
        help="Watch mode for continuous sync",
    ),
    interval: int = typer.Option(
        5,
        "--interval",
        help="Watch interval in seconds (default: 5)",
        min=1,
    ),
    ensure_speckit_compliance: bool = typer.Option(
        False,
        "--ensure-speckit-compliance",
        help="Validate and auto-enrich plan bundle for Spec-Kit compliance before sync (ensures technology stack, testable acceptance criteria, comprehensive scenarios)",
    ),
) -> None:
    """
    Sync changes between Spec-Kit artifacts and SpecFact.

    Synchronizes markdown artifacts generated by Spec-Kit slash commands
    with SpecFact plan bundles and protocols.

    Example:
        specfact sync spec-kit --repo . --bidirectional
    """
    telemetry_metadata = {
        "bidirectional": bidirectional,
        "watch": watch,
        "overwrite": overwrite,
        "interval": interval,
    }

    with telemetry.track_command("sync.spec_kit", telemetry_metadata) as record:
        console.print(f"[bold cyan]Syncing Spec-Kit artifacts from:[/bold cyan] {repo}")

        # Ensure Spec-Kit compliance if requested
        if ensure_speckit_compliance:
            console.print("\n[cyan]🔍 Validating plan bundle for Spec-Kit compliance...[/cyan]")
            from specfact_cli.utils.structure import SpecFactStructure
            from specfact_cli.validators.schema import validate_plan_bundle

            # Use provided plan path or default
            plan_path = plan if plan else (repo / SpecFactStructure.DEFAULT_PLAN)
            if not plan_path.is_absolute():
                plan_path = repo / plan_path

            if plan_path.exists():
                validation_result = validate_plan_bundle(plan_path)
                if isinstance(validation_result, tuple):
                    is_valid, _error, plan_bundle = validation_result
                    if is_valid and plan_bundle:
                        # Check for technology stack in constraints
                        has_tech_stack = bool(
                            plan_bundle.idea
                            and plan_bundle.idea.constraints
                            and any(
                                "Python" in c or "framework" in c.lower() or "database" in c.lower()
                                for c in plan_bundle.idea.constraints
                            )
                        )

                        if not has_tech_stack:
                            console.print("[yellow]⚠ Technology stack not found in constraints[/yellow]")
                            console.print("[dim]Technology stack will be extracted from constraints during sync[/dim]")

                        # Check for testable acceptance criteria
                        features_with_non_testable = []
                        for feature in plan_bundle.features:
                            for story in feature.stories:
                                testable_count = sum(
                                    1
                                    for acc in story.acceptance
                                    if any(
                                        keyword in acc.lower()
                                        for keyword in ["must", "should", "verify", "validate", "ensure"]
                                    )
                                )
                                if testable_count < len(story.acceptance) and len(story.acceptance) > 0:
                                    features_with_non_testable.append((feature.key, story.key))

                        if features_with_non_testable:
                            console.print(
                                f"[yellow]⚠ Found {len(features_with_non_testable)} stories with non-testable acceptance criteria[/yellow]"
                            )
                            console.print("[dim]Acceptance criteria will be enhanced during sync[/dim]")

                        console.print("[green]✓ Plan bundle validation complete[/green]")
                    else:
                        console.print("[yellow]⚠ Plan bundle validation failed, but continuing with sync[/yellow]")
                else:
                    console.print("[yellow]⚠ Could not validate plan bundle, but continuing with sync[/yellow]")
            else:
                console.print("[yellow]⚠ Plan bundle not found, skipping compliance check[/yellow]")

        # Resolve repo path to ensure it's absolute and valid (do this once at the start)
        resolved_repo = repo.resolve()
        if not resolved_repo.exists():
            console.print(f"[red]Error:[/red] Repository path does not exist: {resolved_repo}")
            raise typer.Exit(1)
        if not resolved_repo.is_dir():
            console.print(f"[red]Error:[/red] Repository path is not a directory: {resolved_repo}")
            raise typer.Exit(1)

        # Watch mode implementation
        if watch:
            from specfact_cli.sync.watcher import FileChange, SyncWatcher

            console.print("[bold cyan]Watch mode enabled[/bold cyan]")
            console.print(f"[dim]Watching for changes every {interval} seconds[/dim]\n")

            @beartype
            @require(lambda changes: isinstance(changes, list), "Changes must be a list")
            @require(
                lambda changes: all(hasattr(c, "change_type") for c in changes),
                "All changes must have change_type attribute",
            )
            @ensure(lambda result: result is None, "Must return None")
            def sync_callback(changes: list[FileChange]) -> None:
                """Handle file changes and trigger sync."""
                spec_kit_changes = [c for c in changes if c.change_type == "spec_kit"]
                specfact_changes = [c for c in changes if c.change_type == "specfact"]

                if spec_kit_changes or specfact_changes:
                    console.print(f"[cyan]Detected {len(changes)} change(s), syncing...[/cyan]")
                    # Perform one-time sync (bidirectional if enabled)
                    try:
                        # Re-validate resolved_repo before use (may have been cleaned up)
                        if not resolved_repo.exists():
                            console.print(f"[yellow]⚠[/yellow] Repository path no longer exists: {resolved_repo}\n")
                            return
                        if not resolved_repo.is_dir():
                            console.print(
                                f"[yellow]⚠[/yellow] Repository path is no longer a directory: {resolved_repo}\n"
                            )
                            return
                        # Use resolved_repo from outer scope (already resolved and validated)
                        _perform_sync_operation(
                            repo=resolved_repo,
                            bidirectional=bidirectional,
                            plan=plan,
                            overwrite=overwrite,
                        )
                        console.print("[green]✓[/green] Sync complete\n")
                    except Exception as e:
                        console.print(f"[red]✗[/red] Sync failed: {e}\n")

            # Use resolved_repo for watcher (already resolved and validated)
            watcher = SyncWatcher(resolved_repo, sync_callback, interval=interval)
            watcher.watch()
            record({"watch_mode": True})
            return

        # Perform sync operation (extracted to avoid recursion in watch mode)
        # Use resolved_repo (already resolved and validated above)
        _perform_sync_operation(
            repo=resolved_repo,
            bidirectional=bidirectional,
            plan=plan,
            overwrite=overwrite,
        )
        record({"sync_completed": True})


@app.command("repository")
def sync_repository(
    repo: Path = typer.Option(
        Path("."),
        "--repo",
        help="Path to repository",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    target: Path | None = typer.Option(
        None,
        "--target",
        help="Target directory for artifacts (default: .specfact)",
    ),
    watch: bool = typer.Option(
        False,
        "--watch",
        help="Watch mode for continuous sync",
    ),
    interval: int = typer.Option(
        5,
        "--interval",
        help="Watch interval in seconds (default: 5)",
        min=1,
    ),
    confidence: float = typer.Option(
        0.5,
        "--confidence",
        help="Minimum confidence threshold for feature detection (default: 0.5)",
        min=0.0,
        max=1.0,
    ),
) -> None:
    """
    Sync code changes to SpecFact artifacts.

    Monitors repository code changes, updates plan artifacts based on detected
    features/stories, and tracks deviations from manual plans.

    Example:
        specfact sync repository --repo . --confidence 0.5
    """
    from specfact_cli.sync.repository_sync import RepositorySync

    telemetry_metadata = {
        "watch": watch,
        "interval": interval,
        "confidence": confidence,
    }

    with telemetry.track_command("sync.repository", telemetry_metadata) as record:
        console.print(f"[bold cyan]Syncing repository changes from:[/bold cyan] {repo}")

        # Resolve repo path to ensure it's absolute and valid (do this once at the start)
        resolved_repo = repo.resolve()
        if not resolved_repo.exists():
            console.print(f"[red]Error:[/red] Repository path does not exist: {resolved_repo}")
            raise typer.Exit(1)
        if not resolved_repo.is_dir():
            console.print(f"[red]Error:[/red] Repository path is not a directory: {resolved_repo}")
            raise typer.Exit(1)

        if target is None:
            target = resolved_repo / ".specfact"

        sync = RepositorySync(resolved_repo, target, confidence_threshold=confidence)

        if watch:
            from specfact_cli.sync.watcher import FileChange, SyncWatcher

            console.print("[bold cyan]Watch mode enabled[/bold cyan]")
            console.print(f"[dim]Watching for changes every {interval} seconds[/dim]\n")

            @beartype
            @require(lambda changes: isinstance(changes, list), "Changes must be a list")
            @require(
                lambda changes: all(hasattr(c, "change_type") for c in changes),
                "All changes must have change_type attribute",
            )
            @ensure(lambda result: result is None, "Must return None")
            def sync_callback(changes: list[FileChange]) -> None:
                """Handle file changes and trigger sync."""
                code_changes = [c for c in changes if c.change_type == "code"]

                if code_changes:
                    console.print(f"[cyan]Detected {len(code_changes)} code change(s), syncing...[/cyan]")
                    # Perform repository sync
                    try:
                        # Re-validate resolved_repo before use (may have been cleaned up)
                        if not resolved_repo.exists():
                            console.print(f"[yellow]⚠[/yellow] Repository path no longer exists: {resolved_repo}\n")
                            return
                        if not resolved_repo.is_dir():
                            console.print(
                                f"[yellow]⚠[/yellow] Repository path is no longer a directory: {resolved_repo}\n"
                            )
                            return
                        # Use resolved_repo from outer scope (already resolved and validated)
                        result = sync.sync_repository_changes(resolved_repo)
                        if result.status == "success":
                            console.print("[green]✓[/green] Repository sync complete\n")
                        elif result.status == "deviation_detected":
                            console.print(f"[yellow]⚠[/yellow] Deviations detected: {len(result.deviations)}\n")
                        else:
                            console.print(f"[red]✗[/red] Sync failed: {result.status}\n")
                    except Exception as e:
                        console.print(f"[red]✗[/red] Sync failed: {e}\n")

            # Use resolved_repo for watcher (already resolved and validated)
            watcher = SyncWatcher(resolved_repo, sync_callback, interval=interval)
            watcher.watch()
            record({"watch_mode": True})
            return

        # Use resolved_repo (already resolved and validated above)
        # Disable Progress in test mode to avoid LiveError conflicts
        if _is_test_mode():
            # In test mode, just run the sync without Progress
            result = sync.sync_repository_changes(resolved_repo)
        else:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                # Step 1: Detect code changes
                task = progress.add_task("Detecting code changes...", total=None)
                result = sync.sync_repository_changes(resolved_repo)
                progress.update(task, description=f"✓ Detected {len(result.code_changes)} code changes")

                # Step 2: Show plan updates
                if result.plan_updates:
                    task = progress.add_task("Updating plan artifacts...", total=None)
                    total_features = sum(update.get("features", 0) for update in result.plan_updates)
                    progress.update(task, description=f"✓ Updated plan artifacts ({total_features} features)")

                # Step 3: Show deviations
                if result.deviations:
                    task = progress.add_task("Tracking deviations...", total=None)
                    progress.update(task, description=f"✓ Found {len(result.deviations)} deviations")

        # Record sync results
        record(
            {
                "code_changes": len(result.code_changes),
                "plan_updates": len(result.plan_updates) if result.plan_updates else 0,
                "deviations": len(result.deviations) if result.deviations else 0,
            }
        )

        # Report results
        console.print(f"[bold cyan]Code Changes:[/bold cyan] {len(result.code_changes)}")
        if result.plan_updates:
            console.print(f"[bold cyan]Plan Updates:[/bold cyan] {len(result.plan_updates)}")
        if result.deviations:
            console.print(f"[yellow]⚠[/yellow] Found {len(result.deviations)} deviations from manual plan")
            console.print("[dim]Run 'specfact plan compare' for detailed deviation report[/dim]")
        else:
            console.print("[bold green]✓[/bold green] No deviations detected")
        console.print("[bold green]✓[/bold green] Repository sync complete!")

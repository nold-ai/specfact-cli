"""
Sync command - Bidirectional synchronization for external tools and repositories.

This module provides commands for synchronizing changes between external tool artifacts
(e.g., Spec-Kit, Linear, Jira), repository changes, and SpecFact plans using the
bridge architecture.
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
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from specfact_cli import runtime
from specfact_cli.models.bridge import AdapterType
from specfact_cli.models.plan import Feature, PlanBundle
from specfact_cli.sync.speckit_sync import SpecKitSync
from specfact_cli.telemetry import telemetry


app = typer.Typer(help="Synchronize external tool artifacts and repository changes")
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
@require(lambda bundle: bundle is None or isinstance(bundle, str), "Bundle must be None or str")
@require(lambda overwrite: isinstance(overwrite, bool), "Overwrite must be bool")
@require(lambda adapter_type: adapter_type is not None, "Adapter type must be set")
@ensure(lambda result: result is None, "Must return None")
def _perform_sync_operation(
    repo: Path,
    bidirectional: bool,
    bundle: str | None,
    overwrite: bool,
    adapter_type: AdapterType,
) -> None:
    """
    Perform sync operation without watch mode.

    This is extracted to avoid recursion when called from watch mode callback.

    Args:
        repo: Path to repository
        bidirectional: Enable bidirectional sync
        bundle: Project bundle name
        overwrite: Overwrite existing tool artifacts
        adapter_type: Adapter type to use
    """
    from specfact_cli.importers.speckit_converter import SpecKitConverter
    from specfact_cli.importers.speckit_scanner import SpecKitScanner

    # Step 1: Detect tool repository (using bridge probe for auto-detection)
    from specfact_cli.sync.bridge_probe import BridgeProbe
    from specfact_cli.utils.structure import SpecFactStructure
    from specfact_cli.validators.schema import validate_plan_bundle

    probe = BridgeProbe(repo)
    _ = probe.detect()  # Probe for detection, result not used in this path

    # For Spec-Kit adapter, use legacy scanner for now
    if adapter_type == AdapterType.SPECKIT:
        scanner = SpecKitScanner(repo)
        if not scanner.is_speckit_repo():
            console.print(f"[bold red]✗[/bold red] Not a {adapter_type.value} repository")
            console.print("[dim]Expected: .specify/ directory[/dim]")
            console.print("[dim]Tip: Use 'specfact bridge probe' to auto-detect tool configuration[/dim]")
            raise typer.Exit(1)

        console.print(f"[bold green]✓[/bold green] Detected {adapter_type.value} repository")
    else:
        console.print(f"[bold green]✓[/bold green] Using bridge adapter: {adapter_type.value}")
        # TODO: Implement generic adapter detection
        console.print("[yellow]⚠ Generic adapter not yet fully implemented[/yellow]")
        raise typer.Exit(1)

    # Step 1.5: Validate constitution exists and is not empty (Spec-Kit specific)
    if adapter_type == AdapterType.SPECKIT:
        has_constitution, constitution_error = scanner.has_constitution()
    else:
        has_constitution = True
        constitution_error = None
    if not has_constitution:
        console.print("[bold red]✗[/bold red] Constitution required")
        console.print(f"[red]{constitution_error}[/red]")
        console.print("\n[bold yellow]Next Steps:[/bold yellow]")
        console.print("1. Run 'specfact bridge constitution bootstrap --repo .' to auto-generate constitution")
        console.print("2. Or run tool-specific constitution command in your AI assistant")
        console.print("3. Then run 'specfact sync bridge --adapter <adapter>' again")
        raise typer.Exit(1)

    # Check if constitution is minimal and suggest bootstrap
    constitution_path = repo / ".specify" / "memory" / "constitution.md"
    if constitution_path.exists():
        from specfact_cli.commands.bridge import is_constitution_minimal

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
                if runtime.is_interactive():
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
                            "[dim]Skipping bootstrap. Run 'specfact bridge constitution bootstrap' manually if needed[/dim]"
                        )
                else:
                    # Non-interactive mode: skip prompt
                    console.print("[yellow]⚠[/yellow] Constitution is minimal (essentially empty)")
                    console.print(
                        "[dim]Run 'specfact bridge constitution bootstrap --repo .' to generate constitution[/dim]"
                    )

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
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        # Step 3: Scan tool artifacts
        task = progress.add_task(f"[cyan]Scanning {adapter_type.value} artifacts...[/cyan]", total=None)
        # Keep description showing current activity (spinner will show automatically)
        progress.update(task, description=f"[cyan]Scanning {adapter_type.value} artifacts...[/cyan]")
        features = scanner.discover_features()
        # Update with final status after completion
        progress.update(task, description=f"[green]✓[/green] Found {len(features)} features in specs/")

        # Step 3.5: Validate tool artifacts for unidirectional sync
        if not bidirectional and len(features) == 0:
            console.print(f"[bold red]✗[/bold red] No {adapter_type.value} features found")
            console.print(
                f"[red]Unidirectional sync ({adapter_type.value} → SpecFact) requires at least one feature specification.[/red]"
            )
            console.print("\n[bold yellow]Next Steps:[/bold yellow]")
            if adapter_type == AdapterType.SPECKIT:
                console.print("1. Run '/speckit.specify' command in your AI assistant to create feature specifications")
                console.print("2. Optionally run '/speckit.plan' and '/speckit.tasks' to create complete artifacts")
            else:
                console.print(f"1. Create feature specifications in your {adapter_type.value} project")
            console.print(f"3. Then run 'specfact sync bridge --adapter {adapter_type.value}' again")
            console.print(
                f"\n[dim]Note: For bidirectional sync, {adapter_type.value} artifacts are optional if syncing from SpecFact → {adapter_type.value}[/dim]"
            )
            raise typer.Exit(1)

        # Step 4: Sync based on mode
        specfact_changes: dict[str, Any] = {}
        conflicts: list[dict[str, Any]] = []
        features_converted_speckit = 0

        if bidirectional:
            # Bidirectional sync: tool → SpecFact and SpecFact → tool
            # Step 5.1: tool → SpecFact (unidirectional sync)
            # Skip expensive conversion if no tool features found (optimization)
            merged_bundle: PlanBundle | None = None
            features_updated = 0
            features_added = 0

            if len(features) == 0:
                task = progress.add_task(f"[cyan]📝[/cyan] Converting {adapter_type.value} → SpecFact...", total=None)
                progress.update(
                    task,
                    description=f"[green]✓[/green] Skipped (no {adapter_type.value} features found)",
                )
                console.print(f"[dim]  - Skipped {adapter_type.value} → SpecFact (no features found)[/dim]")
                # Use existing plan bundle if available, otherwise create minimal empty one
                from specfact_cli.utils.structure import SpecFactStructure
                from specfact_cli.validators.schema import validate_plan_bundle

                # Use get_default_plan_path() to find the active plan (checks config or falls back to main.bundle.yaml)
                plan_path = SpecFactStructure.get_default_plan_path(repo)
                if plan_path and plan_path.exists():
                    # Show progress while loading plan bundle
                    progress.update(task, description="[cyan]Parsing plan bundle YAML...[/cyan]")
                    # Check if path is a directory (modular bundle) - load it first
                    if plan_path.is_dir():
                        from specfact_cli.commands.plan import _convert_project_bundle_to_plan_bundle
                        from specfact_cli.utils.progress import load_bundle_with_progress

                        project_bundle = load_bundle_with_progress(
                            plan_path,
                            validate_hashes=False,
                            console_instance=progress.console if hasattr(progress, "console") else None,
                        )
                        loaded_plan_bundle = _convert_project_bundle_to_plan_bundle(project_bundle)
                        is_valid = True
                    else:
                        # It's a file (legacy monolithic bundle) - validate directly
                        validation_result = validate_plan_bundle(plan_path)
                        if isinstance(validation_result, tuple):
                            is_valid, _error, loaded_plan_bundle = validation_result
                        else:
                            is_valid = False
                            loaded_plan_bundle = None
                    if is_valid and loaded_plan_bundle:
                        # Show progress during validation (Pydantic validation can be slow for large bundles)
                        progress.update(
                            task,
                            description=f"[cyan]Validating {len(loaded_plan_bundle.features)} features...[/cyan]",
                        )
                        merged_bundle = loaded_plan_bundle
                        progress.update(
                            task,
                            description=f"[green]✓[/green] Loaded plan bundle ({len(loaded_plan_bundle.features)} features)",
                        )
                    else:
                        # Fallback: create minimal bundle via converter (but skip expensive parsing)
                        progress.update(
                            task, description=f"[cyan]Creating plan bundle from {adapter_type.value}...[/cyan]"
                        )
                        merged_bundle = _sync_speckit_to_specfact(repo, converter, scanner, progress, task)[0]
                else:
                    # No plan path found, create minimal bundle
                    progress.update(task, description=f"[cyan]Creating plan bundle from {adapter_type.value}...[/cyan]")
                    merged_bundle = _sync_speckit_to_specfact(repo, converter, scanner, progress, task)[0]
            else:
                task = progress.add_task(f"[cyan]Converting {adapter_type.value} → SpecFact...[/cyan]", total=None)
                # Show current activity (spinner will show automatically)
                progress.update(task, description=f"[cyan]Converting {adapter_type.value} → SpecFact...[/cyan]")
                merged_bundle, features_updated, features_added = _sync_speckit_to_specfact(
                    repo, converter, scanner, progress
                )

            if merged_bundle:
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

            # Step 5.2: SpecFact → tool (reverse conversion)
            task = progress.add_task(f"[cyan]Converting SpecFact → {adapter_type.value}...[/cyan]", total=None)
            # Show current activity (spinner will show automatically)
            progress.update(task, description="[cyan]Detecting SpecFact changes...[/cyan]")

            # Detect SpecFact changes (for tracking/incremental sync, but don't block conversion)
            specfact_changes = sync.detect_specfact_changes(repo)

            # Use the merged_bundle we already loaded, or load it if not available
            # We convert even if no "changes" detected, as long as plan bundle exists and has features
            plan_bundle_to_convert: PlanBundle | None = None

            # Prefer using merged_bundle if it has features (already loaded above)
            if merged_bundle and len(merged_bundle.features) > 0:
                plan_bundle_to_convert = merged_bundle
            else:
                # Fallback: load plan bundle from bundle name or default
                plan_bundle_to_convert = None
                if bundle:
                    from specfact_cli.commands.plan import _convert_project_bundle_to_plan_bundle
                    from specfact_cli.utils.progress import load_bundle_with_progress

                    bundle_dir = SpecFactStructure.project_dir(base_path=repo, bundle_name=bundle)
                    if bundle_dir.exists():
                        project_bundle = load_bundle_with_progress(
                            bundle_dir, validate_hashes=False, console_instance=console
                        )
                        plan_bundle_to_convert = _convert_project_bundle_to_plan_bundle(project_bundle)
                else:
                    # Use get_default_plan_path() to find the active plan (legacy compatibility)
                    plan_path: Path | None = None
                    if hasattr(SpecFactStructure, "get_default_plan_path"):
                        plan_path = SpecFactStructure.get_default_plan_path(repo)
                    if plan_path and plan_path.exists():
                        progress.update(task, description="[cyan]Loading plan bundle...[/cyan]")
                        # Check if path is a directory (modular bundle) - load it first
                        if plan_path.is_dir():
                            from specfact_cli.commands.plan import _convert_project_bundle_to_plan_bundle
                            from specfact_cli.utils.progress import load_bundle_with_progress

                            project_bundle = load_bundle_with_progress(
                                plan_path,
                                validate_hashes=False,
                                console_instance=progress.console if hasattr(progress, "console") else None,
                            )
                            plan_bundle = _convert_project_bundle_to_plan_bundle(project_bundle)
                            is_valid = True
                        else:
                            # It's a file (legacy monolithic bundle) - validate directly
                            validation_result = validate_plan_bundle(plan_path)
                            if isinstance(validation_result, tuple):
                                is_valid, _error, plan_bundle = validation_result
                            else:
                                is_valid = False
                                plan_bundle = None
                        if is_valid and plan_bundle and len(plan_bundle.features) > 0:
                            plan_bundle_to_convert = plan_bundle

            # Convert if we have a plan bundle with features
            if plan_bundle_to_convert and len(plan_bundle_to_convert.features) > 0:
                # Handle overwrite mode
                if overwrite:
                    progress.update(task, description="[cyan]Removing existing artifacts...[/cyan]")
                    # Delete existing Spec-Kit artifacts before conversion
                    specs_dir = repo / "specs"
                    if specs_dir.exists():
                        console.print("[yellow]⚠[/yellow] Overwrite mode: Removing existing Spec-Kit artifacts...")
                        shutil.rmtree(specs_dir)
                        specs_dir.mkdir(parents=True, exist_ok=True)
                        console.print("[green]✓[/green] Existing artifacts removed")

                # Convert SpecFact plan bundle to tool format
                total_features = len(plan_bundle_to_convert.features)
                progress.update(
                    task,
                    description=f"[cyan]Converting plan bundle to {adapter_type.value} format (0 of {total_features})...[/cyan]",
                )

                # Progress callback to update during conversion
                def update_progress(current: int, total: int) -> None:
                    progress.update(
                        task,
                        description=f"[cyan]Converting plan bundle to {adapter_type.value} format ({current} of {total})...[/cyan]",
                    )

                features_converted_speckit = converter.convert_to_speckit(plan_bundle_to_convert, update_progress)
                progress.update(
                    task,
                    description=f"[green]✓[/green] Converted {features_converted_speckit} features to {adapter_type.value}",
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
                progress.update(task, description=f"[green]✓[/green] No features to convert to {adapter_type.value}")
                features_converted_speckit = 0

            # Detect conflicts between both directions
            speckit_changes = sync.detect_speckit_changes(repo)
            conflicts = sync.detect_conflicts(speckit_changes, specfact_changes)

            if conflicts:
                console.print(f"[yellow]⚠[/yellow] Found {len(conflicts)} conflicts")
                console.print(
                    f"[dim]Conflicts resolved using priority rules (SpecFact > {adapter_type.value} for artifacts)[/dim]"
                )
            else:
                console.print("[bold green]✓[/bold green] No conflicts detected")
        else:
            # Unidirectional sync: tool → SpecFact
            task = progress.add_task("[cyan]Converting to SpecFact format...[/cyan]", total=None)
            # Show current activity (spinner will show automatically)
            progress.update(task, description="[cyan]Converting to SpecFact format...[/cyan]")

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
            console.print(
                f"  - {adapter_type.value} → SpecFact: Updated {features_updated}, Added {features_added} features"
            )
            # Always show conversion result (we convert if plan bundle exists, not just when changes detected)
            if features_converted_speckit > 0:
                console.print(
                    f"  - SpecFact → {adapter_type.value}: {features_converted_speckit} features converted to {adapter_type.value} format"
                )
            else:
                console.print(f"  - SpecFact → {adapter_type.value}: No features to convert")
            if conflicts:
                console.print(f"  - Conflicts: {len(conflicts)} detected and resolved")
            else:
                console.print("  - Conflicts: None detected")

            # Post-sync validation suggestion
            if features_converted_speckit > 0:
                console.print()
                console.print("[bold cyan]Next Steps:[/bold cyan]")
                if adapter_type == AdapterType.SPECKIT:
                    console.print("  Run '/speckit.analyze' to validate artifact consistency and quality")
                else:
                    console.print(f"  Validate {adapter_type.value} artifact consistency and quality")
                console.print("  This will check for ambiguities, duplications, and constitution alignment")
        else:
            console.print("[bold cyan]Sync Summary (Unidirectional):[/bold cyan]")
            if features:
                console.print(f"  - Features synced: {len(features)}")
            if features_updated > 0 or features_added > 0:
                console.print(f"  - Updated: {features_updated} features")
                console.print(f"  - Added: {features_added} new features")
            console.print(f"  - Direction: {adapter_type.value} → SpecFact")

            # Post-sync validation suggestion
            console.print()
            console.print("[bold cyan]Next Steps:[/bold cyan]")
            if adapter_type == AdapterType.SPECKIT:
                console.print("  Run '/speckit.analyze' to validate artifact consistency and quality")
            else:
                console.print(f"  Validate {adapter_type.value} artifact consistency and quality")
            console.print("  This will check for ambiguities, duplications, and constitution alignment")

    console.print()
    console.print("[bold green]✓[/bold green] Sync complete!")

    # Auto-validate OpenAPI/AsyncAPI specs with Specmatic (if found)
    import asyncio

    from specfact_cli.integrations.specmatic import check_specmatic_available, validate_spec_with_specmatic

    spec_files = []
    for pattern in [
        "**/openapi.yaml",
        "**/openapi.yml",
        "**/openapi.json",
        "**/asyncapi.yaml",
        "**/asyncapi.yml",
        "**/asyncapi.json",
    ]:
        spec_files.extend(repo.glob(pattern))

    if spec_files:
        console.print(f"\n[cyan]🔍 Found {len(spec_files)} API specification file(s)[/cyan]")
        is_available, error_msg = check_specmatic_available()
        if is_available:
            for spec_file in spec_files[:3]:  # Validate up to 3 specs
                console.print(f"[dim]Validating {spec_file.relative_to(repo)} with Specmatic...[/dim]")
                try:
                    result = asyncio.run(validate_spec_with_specmatic(spec_file))
                    if result.is_valid:
                        console.print(f"  [green]✓[/green] {spec_file.name} is valid")
                    else:
                        console.print(f"  [yellow]⚠[/yellow] {spec_file.name} has validation issues")
                        if result.errors:
                            for error in result.errors[:2]:  # Show first 2 errors
                                console.print(f"    - {error}")
                except Exception as e:
                    console.print(f"  [yellow]⚠[/yellow] Validation error: {e!s}")
            if len(spec_files) > 3:
                console.print(
                    f"[dim]... and {len(spec_files) - 3} more spec file(s) (run 'specfact spec validate' to validate all)[/dim]"
                )
        else:
            console.print(f"[dim]💡 Tip: Install Specmatic to validate API specs: {error_msg}[/dim]")


def _sync_speckit_to_specfact(
    repo: Path, converter: Any, scanner: Any, progress: Any, task: int | None = None
) -> tuple[PlanBundle, int, int]:
    """
    Sync tool artifacts to SpecFact format.

    Args:
        repo: Repository path
        converter: Tool converter instance (e.g., SpecKitConverter)
        scanner: Tool scanner instance (e.g., SpecKitScanner)
        progress: Rich Progress instance
        task: Optional progress task ID to update

    Returns:
        Tuple of (merged_bundle, features_updated, features_added)
    """
    from specfact_cli.generators.plan_generator import PlanGenerator
    from specfact_cli.utils.structure import SpecFactStructure
    from specfact_cli.validators.schema import validate_plan_bundle

    plan_path = SpecFactStructure.get_default_plan_path(repo)
    existing_bundle: PlanBundle | None = None
    # Check if plan_path is a modular bundle directory (even if it doesn't exist yet)
    is_modular_bundle = (plan_path.exists() and plan_path.is_dir()) or (
        not plan_path.exists() and plan_path.parent.name == "projects"
    )

    if plan_path.exists():
        if task is not None:
            progress.update(task, description="[cyan]Validating existing plan bundle...[/cyan]")
        # Check if path is a directory (modular bundle) - load it first
        if plan_path.is_dir():
            is_modular_bundle = True
            from specfact_cli.commands.plan import _convert_project_bundle_to_plan_bundle
            from specfact_cli.utils.progress import load_bundle_with_progress

            project_bundle = load_bundle_with_progress(
                plan_path,
                validate_hashes=False,
                console_instance=progress.console if hasattr(progress, "console") else None,
            )
            bundle = _convert_project_bundle_to_plan_bundle(project_bundle)
            is_valid = True
        else:
            # It's a file (legacy monolithic bundle) - validate directly
            validation_result = validate_plan_bundle(plan_path)
            if isinstance(validation_result, tuple):
                is_valid, _error, bundle = validation_result
            else:
                is_valid = False
                bundle = None
        if is_valid and bundle:
            existing_bundle = bundle
            # Deduplicate existing features by normalized key (clean up duplicates from previous syncs)
            from specfact_cli.utils.feature_keys import normalize_feature_key

            seen_normalized_keys: set[str] = set()
            deduplicated_features: list[Feature] = []
            for existing_feature in existing_bundle.features:
                normalized_key = normalize_feature_key(existing_feature.key)
                if normalized_key not in seen_normalized_keys:
                    seen_normalized_keys.add(normalized_key)
                    deduplicated_features.append(existing_feature)

            duplicates_removed = len(existing_bundle.features) - len(deduplicated_features)
            if duplicates_removed > 0:
                existing_bundle.features = deduplicated_features
                # Write back deduplicated bundle immediately to clean up the plan file
                from specfact_cli.generators.plan_generator import PlanGenerator

                if task is not None:
                    progress.update(
                        task,
                        description=f"[cyan]Deduplicating {duplicates_removed} duplicate features and writing cleaned plan...[/cyan]",
                    )
                # Skip writing if plan_path is a modular bundle directory (already saved as ProjectBundle)
                if not is_modular_bundle:
                    generator = PlanGenerator()
                    generator.generate(existing_bundle, plan_path)
                if task is not None:
                    progress.update(
                        task,
                        description=f"[green]✓[/green] Removed {duplicates_removed} duplicates, cleaned plan saved",
                    )

    # Convert tool artifacts to SpecFact
    if task is not None:
        progress.update(task, description="[cyan]Converting tool artifacts to SpecFact format...[/cyan]")
    # Don't write plan file during sync - it's already saved as ProjectBundle
    # convert_plan will skip writing if path is a modular bundle directory
    converted_bundle = converter.convert_plan(None)

    # Merge with existing plan if it exists
    features_updated = 0
    features_added = 0

    if existing_bundle:
        if task is not None:
            progress.update(task, description="[cyan]Merging with existing plan bundle...[/cyan]")
        # Use normalized keys for matching to handle different key formats (e.g., FEATURE-001 vs 001_FEATURE_NAME)
        from specfact_cli.utils.feature_keys import normalize_feature_key

        # Build a map of normalized_key -> (index, original_key) for existing features
        normalized_key_map: dict[str, tuple[int, str]] = {}
        for idx, existing_feature in enumerate(existing_bundle.features):
            normalized_key = normalize_feature_key(existing_feature.key)
            # If multiple features have the same normalized key, keep the first one
            if normalized_key not in normalized_key_map:
                normalized_key_map[normalized_key] = (idx, existing_feature.key)

        for feature in converted_bundle.features:
            normalized_key = normalize_feature_key(feature.key)
            matched = False

            # Try exact match first
            if normalized_key in normalized_key_map:
                existing_idx, original_key = normalized_key_map[normalized_key]
                # Preserve the original key format from existing bundle
                feature.key = original_key
                existing_bundle.features[existing_idx] = feature
                features_updated += 1
                matched = True
            else:
                # Try prefix match for abbreviated vs full names
                # (e.g., IDEINTEGRATION vs IDEINTEGRATIONSYSTEM)
                # Only match if shorter is a PREFIX of longer with significant length difference
                # AND at least one key has a numbered prefix (041_, 042-, etc.) indicating Spec-Kit origin
                # This avoids false positives like SMARTCOVERAGE vs SMARTCOVERAGEMANAGER (both from code analysis)
                for existing_norm_key, (existing_idx, original_key) in normalized_key_map.items():
                    shorter = min(normalized_key, existing_norm_key, key=len)
                    longer = max(normalized_key, existing_norm_key, key=len)

                    # Check if at least one key has a numbered prefix (tool format, e.g., Spec-Kit)
                    import re

                    has_speckit_key = bool(
                        re.match(r"^\d{3}[_-]", feature.key) or re.match(r"^\d{3}[_-]", original_key)
                    )

                    # More conservative matching:
                    # 1. At least one key must have numbered prefix (tool origin, e.g., Spec-Kit)
                    # 2. Shorter must be at least 10 chars
                    # 3. Longer must start with shorter (prefix match)
                    # 4. Length difference must be at least 6 chars
                    # 5. Shorter must be < 75% of longer (to ensure significant difference)
                    length_diff = len(longer) - len(shorter)
                    length_ratio = len(shorter) / len(longer) if len(longer) > 0 else 1.0

                    if (
                        has_speckit_key
                        and len(shorter) >= 10
                        and longer.startswith(shorter)
                        and length_diff >= 6
                        and length_ratio < 0.75
                    ):
                        # Match found - use the existing key format (prefer full name if available)
                        if len(existing_norm_key) >= len(normalized_key):
                            # Existing key is longer (full name) - keep it
                            feature.key = original_key
                        else:
                            # New key is longer (full name) - use it but update existing
                            existing_bundle.features[existing_idx].key = feature.key
                        existing_bundle.features[existing_idx] = feature
                        features_updated += 1
                        matched = True
                        break

            if not matched:
                # New feature - add it
                existing_bundle.features.append(feature)
                features_added += 1

        # Update product themes
        themes_existing = set(existing_bundle.product.themes)
        themes_new = set(converted_bundle.product.themes)
        existing_bundle.product.themes = list(themes_existing | themes_new)

        # Write merged bundle (skip if modular bundle - already saved as ProjectBundle)
        if not is_modular_bundle:
            if task is not None:
                progress.update(task, description="[cyan]Writing plan bundle to disk...[/cyan]")
            generator = PlanGenerator()
            generator.generate(existing_bundle, plan_path)
        return existing_bundle, features_updated, features_added
    # Write new bundle (skip if plan_path is a modular bundle directory)
    if not is_modular_bundle:
        # Legacy monolithic file - write it
        generator = PlanGenerator()
        generator.generate(converted_bundle, plan_path)
    return converted_bundle, 0, len(converted_bundle.features)


@app.command("bridge")
def sync_bridge(
    # Target/Input
    repo: Path = typer.Option(
        Path("."),
        "--repo",
        help="Path to repository",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    bundle: str | None = typer.Option(
        None,
        "--bundle",
        help="Project bundle name for SpecFact → tool conversion (default: auto-detect)",
    ),
    # Behavior/Options
    bidirectional: bool = typer.Option(
        False,
        "--bidirectional",
        help="Enable bidirectional sync (tool ↔ SpecFact)",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite existing tool artifacts (delete all existing before sync)",
    ),
    watch: bool = typer.Option(
        False,
        "--watch",
        help="Watch mode for continuous sync",
    ),
    ensure_compliance: bool = typer.Option(
        False,
        "--ensure-compliance",
        help="Validate and auto-enrich plan bundle for tool compliance before sync",
    ),
    # Advanced/Configuration
    adapter: str = typer.Option(
        "speckit",
        "--adapter",
        help="Adapter type (speckit, generic-markdown). Default: auto-detect",
        hidden=True,  # Hidden by default, shown with --help-advanced
    ),
    interval: int = typer.Option(
        5,
        "--interval",
        help="Watch interval in seconds (default: 5)",
        min=1,
        hidden=True,  # Hidden by default, shown with --help-advanced
    ),
) -> None:
    """
    Sync changes between external tool artifacts and SpecFact using bridge architecture.

    Synchronizes artifacts from external tools (e.g., Spec-Kit, Linear, Jira) with
    SpecFact project bundles using configurable bridge mappings.

    Supported adapters:
    - speckit: Spec-Kit projects (specs/, .specify/)
    - generic-markdown: Generic markdown-based specifications

    **Parameter Groups:**
    - **Target/Input**: --repo, --bundle
    - **Behavior/Options**: --bidirectional, --overwrite, --watch, --ensure-compliance
    - **Advanced/Configuration**: --adapter, --interval

    **Examples:**
        specfact sync bridge --adapter speckit --repo . --bidirectional
        specfact sync bridge --repo . --bidirectional  # Auto-detect adapter
        specfact sync bridge --repo . --watch --interval 10
    """
    # Auto-detect adapter if not specified
    from specfact_cli.sync.bridge_probe import BridgeProbe

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

    telemetry_metadata = {
        "adapter": adapter,
        "bidirectional": bidirectional,
        "watch": watch,
        "overwrite": overwrite,
        "interval": interval,
    }

    with telemetry.track_command("sync.bridge", telemetry_metadata) as record:
        console.print(f"[bold cyan]Syncing {adapter_type.value} artifacts from:[/bold cyan] {repo}")

        # For now, Spec-Kit adapter uses legacy sync (will be migrated to bridge)
        if adapter_type != AdapterType.SPECKIT:
            console.print(f"[yellow]⚠ Generic adapter ({adapter_type.value}) not yet fully implemented[/yellow]")
            console.print("[dim]Falling back to Spec-Kit adapter for now[/dim]")
            # TODO: Implement generic adapter sync via bridge
            raise typer.Exit(1)

        # Ensure tool compliance if requested
        if ensure_compliance:
            console.print(f"\n[cyan]🔍 Validating plan bundle for {adapter_type.value} compliance...[/cyan]")
            from specfact_cli.utils.structure import SpecFactStructure
            from specfact_cli.validators.schema import validate_plan_bundle

            # Use provided bundle name or default
            plan_bundle = None
            if bundle:
                from specfact_cli.utils.progress import load_bundle_with_progress

                bundle_dir = SpecFactStructure.project_dir(base_path=repo, bundle_name=bundle)
                if bundle_dir.exists():
                    project_bundle = load_bundle_with_progress(
                        bundle_dir, validate_hashes=False, console_instance=console
                    )
                    # Convert to PlanBundle for validation (legacy compatibility)
                    from specfact_cli.commands.plan import _convert_project_bundle_to_plan_bundle

                    plan_bundle = _convert_project_bundle_to_plan_bundle(project_bundle)
                else:
                    console.print(f"[yellow]⚠ Bundle '{bundle}' not found, skipping compliance check[/yellow]")
                    plan_bundle = None
            else:
                # Legacy: Try to find default plan path (for backward compatibility)
                if hasattr(SpecFactStructure, "get_default_plan_path"):
                    plan_path = SpecFactStructure.get_default_plan_path(repo)
                    if plan_path and plan_path.exists():
                        # Check if path is a directory (modular bundle) - load it first
                        if plan_path.is_dir():
                            from specfact_cli.commands.plan import _convert_project_bundle_to_plan_bundle
                            from specfact_cli.utils.progress import load_bundle_with_progress

                            project_bundle = load_bundle_with_progress(
                                plan_path, validate_hashes=False, console_instance=console
                            )
                            plan_bundle = _convert_project_bundle_to_plan_bundle(project_bundle)
                        else:
                            # It's a file (legacy monolithic bundle) - validate directly
                            validation_result = validate_plan_bundle(plan_path)
                            if isinstance(validation_result, tuple):
                                is_valid, _error, plan_bundle = validation_result
                                if not is_valid:
                                    plan_bundle = None
                            else:
                                plan_bundle = None

            if plan_bundle:
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
                                keyword in acc.lower() for keyword in ["must", "should", "verify", "validate", "ensure"]
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
                console.print("[yellow]⚠ Plan bundle not found, skipping compliance check[/yellow]")

        # Resolve repo path to ensure it's absolute and valid (do this once at the start)
        resolved_repo = repo.resolve()
        if not resolved_repo.exists():
            console.print(f"[red]Error:[/red] Repository path does not exist: {resolved_repo}")
            raise typer.Exit(1)
        if not resolved_repo.is_dir():
            console.print(f"[red]Error:[/red] Repository path is not a directory: {resolved_repo}")
            raise typer.Exit(1)

        # Watch mode implementation (using bridge-based watch)
        if watch:
            from specfact_cli.sync.bridge_watch import BridgeWatch

            console.print("[bold cyan]Watch mode enabled[/bold cyan]")
            console.print(f"[dim]Watching for changes every {interval} seconds[/dim]\n")

            # Use bridge-based watch mode
            bridge_watch = BridgeWatch(
                repo_path=resolved_repo,
                bundle_name=bundle,
                interval=interval,
            )

            bridge_watch.watch()
            return

        # Legacy watch mode (for backward compatibility during transition)
        if False:  # Disabled - use bridge watch above
            from specfact_cli.sync.watcher import FileChange, SyncWatcher

            @beartype
            @require(lambda changes: isinstance(changes, list), "Changes must be a list")
            @require(
                lambda changes: all(hasattr(c, "change_type") for c in changes),
                "All changes must have change_type attribute",
            )
            @ensure(lambda result: result is None, "Must return None")
            def sync_callback(changes: list[FileChange]) -> None:
                """Handle file changes and trigger sync."""
                tool_changes = [c for c in changes if c.change_type == "spec_kit"]
                specfact_changes = [c for c in changes if c.change_type == "specfact"]

                if tool_changes or specfact_changes:
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
                            bundle=bundle,
                            overwrite=overwrite,
                            adapter_type=adapter_type,
                        )
                        console.print("[green]✓[/green] Sync complete\n")
                    except Exception as e:
                        console.print(f"[red]✗[/red] Sync failed: {e}\n")

            # Use resolved_repo for watcher (already resolved and validated)
            watcher = SyncWatcher(resolved_repo, sync_callback, interval=interval)
            watcher.watch()
            record({"watch_mode": True})
            return

        # Validate OpenAPI specs before sync (if bundle provided)
        if bundle:
            import asyncio

            from specfact_cli.commands.plan import _convert_project_bundle_to_plan_bundle
            from specfact_cli.utils.progress import load_bundle_with_progress
            from specfact_cli.utils.structure import SpecFactStructure

            bundle_dir = SpecFactStructure.project_dir(base_path=resolved_repo, bundle_name=bundle)
            if bundle_dir.exists():
                console.print("\n[cyan]🔍 Validating OpenAPI contracts before sync...[/cyan]")
                project_bundle = load_bundle_with_progress(bundle_dir, validate_hashes=False, console_instance=console)
                plan_bundle = _convert_project_bundle_to_plan_bundle(project_bundle)

                from specfact_cli.integrations.specmatic import (
                    check_specmatic_available,
                    validate_spec_with_specmatic,
                )

                is_available, error_msg = check_specmatic_available()
                if is_available:
                    # Validate contracts referenced in bundle
                    contract_files = []
                    for feature in plan_bundle.features:
                        if feature.contract:
                            contract_path = bundle_dir / feature.contract
                            if contract_path.exists():
                                contract_files.append(contract_path)

                    if contract_files:
                        console.print(f"[dim]Validating {len(contract_files)} contract(s)...[/dim]")
                        validation_failed = False
                        for contract_path in contract_files[:5]:  # Validate up to 5 contracts
                            console.print(f"[dim]Validating {contract_path.relative_to(bundle_dir)}...[/dim]")
                            try:
                                result = asyncio.run(validate_spec_with_specmatic(contract_path))
                                if not result.is_valid:
                                    console.print(
                                        f"  [bold yellow]⚠[/bold yellow] {contract_path.name} has validation issues"
                                    )
                                    if result.errors:
                                        for error in result.errors[:2]:
                                            console.print(f"    - {error}")
                                    validation_failed = True
                                else:
                                    console.print(f"  [bold green]✓[/bold green] {contract_path.name} is valid")
                            except Exception as e:
                                console.print(f"  [bold yellow]⚠[/bold yellow] Validation error: {e!s}")
                                validation_failed = True

                        if validation_failed:
                            console.print(
                                "[yellow]⚠[/yellow] Some contracts have validation issues. Sync will continue, but consider fixing them."
                            )
                        else:
                            console.print("[green]✓[/green] All contracts validated successfully")

                        # Check backward compatibility if previous version exists (for bidirectional sync)
                        if bidirectional and len(contract_files) > 0:
                            # TODO: Implement backward compatibility check by comparing with previous version
                            # This would require storing previous contract versions
                            console.print(
                                "[dim]Backward compatibility check skipped (previous versions not stored)[/dim]"
                            )
                    else:
                        console.print("[dim]No contracts found in bundle[/dim]")
                else:
                    console.print(f"[dim]💡 Tip: Install Specmatic to validate contracts: {error_msg}[/dim]")

        # Perform sync operation (extracted to avoid recursion in watch mode)
        # Use resolved_repo (already resolved and validated above)
        _perform_sync_operation(
            repo=resolved_repo,
            bidirectional=bidirectional,
            bundle=bundle,
            overwrite=overwrite,
            adapter_type=adapter_type,
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
        hidden=True,  # Hidden by default, shown with --help-advanced
    ),
    confidence: float = typer.Option(
        0.5,
        "--confidence",
        help="Minimum confidence threshold for feature detection (default: 0.5)",
        min=0.0,
        max=1.0,
        hidden=True,  # Hidden by default, shown with --help-advanced
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
                TimeElapsedColumn(),
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

        # Auto-validate OpenAPI/AsyncAPI specs with Specmatic (if found)
        import asyncio

        from specfact_cli.integrations.specmatic import check_specmatic_available, validate_spec_with_specmatic

        spec_files = []
        for pattern in [
            "**/openapi.yaml",
            "**/openapi.yml",
            "**/openapi.json",
            "**/asyncapi.yaml",
            "**/asyncapi.yml",
            "**/asyncapi.json",
        ]:
            spec_files.extend(resolved_repo.glob(pattern))

        if spec_files:
            console.print(f"\n[cyan]🔍 Found {len(spec_files)} API specification file(s)[/cyan]")
            is_available, error_msg = check_specmatic_available()
            if is_available:
                for spec_file in spec_files[:3]:  # Validate up to 3 specs
                    console.print(f"[dim]Validating {spec_file.relative_to(resolved_repo)} with Specmatic...[/dim]")
                    try:
                        result = asyncio.run(validate_spec_with_specmatic(spec_file))
                        if result.is_valid:
                            console.print(f"  [green]✓[/green] {spec_file.name} is valid")
                        else:
                            console.print(f"  [yellow]⚠[/yellow] {spec_file.name} has validation issues")
                            if result.errors:
                                for error in result.errors[:2]:  # Show first 2 errors
                                    console.print(f"    - {error}")
                    except Exception as e:
                        console.print(f"  [yellow]⚠[/yellow] Validation error: {e!s}")
                if len(spec_files) > 3:
                    console.print(
                        f"[dim]... and {len(spec_files) - 3} more spec file(s) (run 'specfact spec validate' to validate all)[/dim]"
                    )
            else:
                console.print(f"[dim]💡 Tip: Install Specmatic to validate API specs: {error_msg}[/dim]")


@app.command("intelligent")
@beartype
@require(
    lambda bundle: bundle is None or (isinstance(bundle, str) and len(bundle) > 0),
    "Bundle name must be None or non-empty string",
)
@require(lambda repo: isinstance(repo, Path), "Repository path must be Path")
@ensure(lambda result: result is None, "Must return None")
def sync_intelligent(
    # Target/Input
    bundle: str | None = typer.Argument(
        None, help="Project bundle name (e.g., legacy-api). Default: active plan from 'specfact plan select'"
    ),
    repo: Path = typer.Option(
        Path("."),
        "--repo",
        help="Path to repository. Default: current directory (.)",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    # Behavior/Options
    watch: bool = typer.Option(
        False,
        "--watch",
        help="Watch mode for continuous sync. Default: False",
    ),
    code_to_spec: str = typer.Option(
        "auto",
        "--code-to-spec",
        help="Code-to-spec sync mode: 'auto' (AST-based) or 'off'. Default: auto",
    ),
    spec_to_code: str = typer.Option(
        "llm-prompt",
        "--spec-to-code",
        help="Spec-to-code sync mode: 'llm-prompt' (generate prompts) or 'off'. Default: llm-prompt",
    ),
    tests: str = typer.Option(
        "specmatic",
        "--tests",
        help="Test generation mode: 'specmatic' (contract-based) or 'off'. Default: specmatic",
    ),
) -> None:
    """
    Continuous intelligent bidirectional sync with conflict resolution.

    Detects changes via hashing and syncs intelligently:
    - Code→Spec: AST-based automatic sync (CLI can do)
    - Spec→Code: LLM prompt generation (CLI orchestrates, LLM writes)
    - Spec→Tests: Specmatic flows (contract-based, not LLM guessing)

    **Parameter Groups:**
    - **Target/Input**: bundle (required argument), --repo
    - **Behavior/Options**: --watch, --code-to-spec, --spec-to-code, --tests

    **Examples:**
        specfact sync intelligent legacy-api --repo .
        specfact sync intelligent my-bundle --repo . --watch
        specfact sync intelligent my-bundle --repo . --code-to-spec auto --spec-to-code llm-prompt --tests specmatic
    """
    from rich.console import Console

    from specfact_cli.utils.structure import SpecFactStructure

    console = Console()

    # Use active plan as default if bundle not provided
    if bundle is None:
        bundle = SpecFactStructure.get_active_bundle_name(repo)
        if bundle is None:
            console.print("[bold red]✗[/bold red] Bundle name required")
            console.print("[yellow]→[/yellow] Use --bundle option or run 'specfact plan select' to set active plan")
            raise typer.Exit(1)
        console.print(f"[dim]Using active plan: {bundle}[/dim]")

    from specfact_cli.sync.change_detector import ChangeDetector
    from specfact_cli.sync.code_to_spec import CodeToSpecSync
    from specfact_cli.sync.spec_to_code import SpecToCodeSync
    from specfact_cli.sync.spec_to_tests import SpecToTestsSync
    from specfact_cli.telemetry import telemetry
    from specfact_cli.utils.progress import load_bundle_with_progress
    from specfact_cli.utils.structure import SpecFactStructure

    repo_path = repo.resolve()
    bundle_dir = SpecFactStructure.project_dir(base_path=repo_path, bundle_name=bundle)

    if not bundle_dir.exists():
        console.print(f"[bold red]✗[/bold red] Project bundle not found: {bundle_dir}")
        raise typer.Exit(1)

    telemetry_metadata = {
        "bundle": bundle,
        "watch": watch,
        "code_to_spec": code_to_spec,
        "spec_to_code": spec_to_code,
        "tests": tests,
    }

    with telemetry.track_command("sync.intelligent", telemetry_metadata) as record:
        console.print(f"[bold cyan]Intelligent Sync:[/bold cyan] {bundle}")
        console.print(f"[dim]Repository:[/dim] {repo_path}")

        # Load project bundle with unified progress display
        project_bundle = load_bundle_with_progress(bundle_dir, validate_hashes=False, console_instance=console)

        # Initialize sync components
        change_detector = ChangeDetector(bundle, repo_path)
        code_to_spec_sync = CodeToSpecSync(repo_path)
        spec_to_code_sync = SpecToCodeSync(repo_path)
        spec_to_tests_sync = SpecToTestsSync(bundle, repo_path)

        def perform_sync() -> None:
            """Perform one sync cycle."""
            console.print("\n[cyan]Detecting changes...[/cyan]")

            # Detect changes
            changeset = change_detector.detect_changes(project_bundle.features)

            if not any([changeset.code_changes, changeset.spec_changes, changeset.test_changes]):
                console.print("[dim]No changes detected[/dim]")
                return

            # Report changes
            if changeset.code_changes:
                console.print(f"[cyan]Code changes:[/cyan] {len(changeset.code_changes)}")
            if changeset.spec_changes:
                console.print(f"[cyan]Spec changes:[/cyan] {len(changeset.spec_changes)}")
            if changeset.test_changes:
                console.print(f"[cyan]Test changes:[/cyan] {len(changeset.test_changes)}")
            if changeset.conflicts:
                console.print(f"[yellow]⚠ Conflicts:[/yellow] {len(changeset.conflicts)}")

            # Sync code→spec (AST-based, automatic)
            if code_to_spec == "auto" and changeset.code_changes:
                console.print("\n[cyan]Syncing code→spec (AST-based)...[/cyan]")
                try:
                    code_to_spec_sync.sync(changeset.code_changes, bundle)
                    console.print("[green]✓[/green] Code→spec sync complete")
                except Exception as e:
                    console.print(f"[red]✗[/red] Code→spec sync failed: {e}")

            # Sync spec→code (LLM prompt generation)
            if spec_to_code == "llm-prompt" and changeset.spec_changes:
                console.print("\n[cyan]Preparing LLM prompts for spec→code...[/cyan]")
                try:
                    context = spec_to_code_sync.prepare_llm_context(changeset.spec_changes, repo_path)
                    prompt = spec_to_code_sync.generate_llm_prompt(context)

                    # Save prompt to file
                    prompts_dir = repo_path / ".specfact" / "prompts"
                    prompts_dir.mkdir(parents=True, exist_ok=True)
                    prompt_file = prompts_dir / f"{bundle}-code-generation-{len(changeset.spec_changes)}.md"
                    prompt_file.write_text(prompt, encoding="utf-8")

                    console.print(f"[green]✓[/green] LLM prompt generated: {prompt_file}")
                    console.print("[yellow]Execute this prompt with your LLM to generate code[/yellow]")
                except Exception as e:
                    console.print(f"[red]✗[/red] LLM prompt generation failed: {e}")

            # Sync spec→tests (Specmatic)
            if tests == "specmatic" and changeset.spec_changes:
                console.print("\n[cyan]Generating tests via Specmatic...[/cyan]")
                try:
                    spec_to_tests_sync.sync(changeset.spec_changes, bundle)
                    console.print("[green]✓[/green] Test generation complete")
                except Exception as e:
                    console.print(f"[red]✗[/red] Test generation failed: {e}")

        if watch:
            console.print("[bold cyan]Watch mode enabled[/bold cyan]")
            console.print("[dim]Watching for changes...[/dim]")
            console.print("[yellow]Press Ctrl+C to stop[/yellow]\n")

            from specfact_cli.sync.watcher import SyncWatcher

            def sync_callback(_changes: list) -> None:
                """Handle file changes and trigger sync."""
                perform_sync()

            watcher = SyncWatcher(repo_path, sync_callback, interval=5)
            try:
                watcher.watch()
            except KeyboardInterrupt:
                console.print("\n[yellow]Stopping watch mode...[/yellow]")
        else:
            perform_sync()

        record({"sync_completed": True})

"""
Sync command - Bidirectional synchronization for external tools and repositories.

This module provides commands for synchronizing changes between external tool artifacts
(e.g., Spec-Kit, Linear, Jira), repository changes, and SpecFact plans using the
bridge architecture.
"""

from __future__ import annotations

import os
import re
import shutil
from pathlib import Path
from typing import Any

import typer
from beartype import beartype
from icontract import ensure, require
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from specfact_cli import runtime
from specfact_cli.adapters.registry import AdapterRegistry
from specfact_cli.models.bridge import AdapterType
from specfact_cli.models.plan import Feature, PlanBundle
from specfact_cli.runtime import debug_log_operation, debug_print, get_configured_console, is_debug_mode
from specfact_cli.telemetry import telemetry
from specfact_cli.utils.terminal import get_progress_config


app = typer.Typer(
    help="Synchronize external tool artifacts and repository changes (Spec-Kit, OpenSpec, GitHub, Linear, Jira, etc.). See 'specfact backlog refine' for template-driven backlog refinement."
)
console = get_configured_console()


@beartype
@ensure(lambda result: isinstance(result, bool), "Must return bool")
def _is_test_mode() -> bool:
    """Check if running in test mode."""
    # Check for TEST_MODE environment variable
    if os.environ.get("TEST_MODE") == "true":
        return True
    # Check if running under pytest (common patterns)
    import sys

    return any("pytest" in arg or "test" in arg.lower() for arg in sys.argv) or "pytest" in sys.modules


@beartype
@require(lambda selection: isinstance(selection, str), "Selection must be string")
@ensure(lambda result: isinstance(result, list), "Must return list")
def _parse_backlog_selection(selection: str) -> list[str]:
    """Parse backlog selection string into a list of IDs/URLs."""
    if not selection:
        return []
    parts = re.split(r"[,\n\r]+", selection)
    return [part.strip() for part in parts if part.strip()]


@beartype
@require(lambda repo: isinstance(repo, Path), "Repo must be Path")
@ensure(lambda result: result is None or isinstance(result, str), "Must return None or string")
def _infer_bundle_name(repo: Path) -> str | None:
    """Infer bundle name from active config or single bundle directory."""
    from specfact_cli.utils.structure import SpecFactStructure

    active_bundle = SpecFactStructure.get_active_bundle_name(repo)
    if active_bundle:
        return active_bundle

    projects_dir = repo / SpecFactStructure.PROJECTS
    if projects_dir.exists():
        candidates = [
            bundle_dir.name
            for bundle_dir in projects_dir.iterdir()
            if bundle_dir.is_dir() and (bundle_dir / "bundle.manifest.yaml").exists()
        ]
        if len(candidates) == 1:
            return candidates[0]

    return None


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
    # Step 1: Detect tool repository (using bridge probe for auto-detection)
    from specfact_cli.utils.structure import SpecFactStructure
    from specfact_cli.validators.schema import validate_plan_bundle

    # Get adapter from registry (universal pattern - no hard-coded checks)
    adapter_instance = AdapterRegistry.get_adapter(adapter_type.value)
    if adapter_instance is None:
        console.print(f"[bold red]✗[/bold red] Adapter '{adapter_type.value}' not found in registry")
        console.print("[dim]Available adapters: " + ", ".join(AdapterRegistry.list_adapters()) + "[/dim]")
        raise typer.Exit(1)

    # Use adapter's detect() method (no bridge_config needed for initial detection)
    if not adapter_instance.detect(repo, None):
        console.print(f"[bold red]✗[/bold red] Not a {adapter_type.value} repository")
        console.print(f"[dim]Expected: {adapter_type.value} structure[/dim]")
        console.print("[dim]Tip: Use 'specfact sync bridge probe' to auto-detect tool configuration[/dim]")
        raise typer.Exit(1)

    console.print(f"[bold green]✓[/bold green] Detected {adapter_type.value} repository")

    # Generate bridge config using adapter
    bridge_config = adapter_instance.generate_bridge_config(repo)

    # Step 1.5: Validate constitution exists and is not empty (Spec-Kit only)
    # Note: Constitution is required for Spec-Kit but not for other adapters (e.g., OpenSpec)
    capabilities = adapter_instance.get_capabilities(repo, bridge_config)
    if adapter_type == AdapterType.SPECKIT:
        has_constitution = capabilities.has_custom_hooks
        if not has_constitution:
            console.print("[bold red]✗[/bold red] Constitution required")
            console.print("[red]Constitution file not found or is empty[/red]")
            console.print("\n[bold yellow]Next Steps:[/bold yellow]")
            console.print("1. Run 'specfact sdd constitution bootstrap --repo .' to auto-generate constitution")
            console.print("2. Or run tool-specific constitution command in your AI assistant")
            console.print("3. Then run 'specfact sync bridge --adapter <adapter>' again")
            raise typer.Exit(1)

    # Check if constitution is minimal and suggest bootstrap (Spec-Kit only)
    if adapter_type == AdapterType.SPECKIT:
        constitution_path = repo / ".specify" / "memory" / "constitution.md"
        if constitution_path.exists():
            from specfact_cli.commands.sdd import is_constitution_minimal

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
                                "[dim]Skipping bootstrap. Run 'specfact sdd constitution bootstrap' manually if needed[/dim]"
                            )
                    else:
                        # Non-interactive mode: skip prompt
                        console.print("[yellow]⚠[/yellow] Constitution is minimal (essentially empty)")
                        console.print(
                            "[dim]Run 'specfact sdd constitution bootstrap --repo .' to generate constitution[/dim]"
                        )
        else:
            # Constitution exists and is not minimal
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

    # Use BridgeSync for adapter-agnostic sync operations
    from specfact_cli.sync.bridge_sync import BridgeSync

    bridge_sync = BridgeSync(repo, bridge_config=bridge_config)

    # Note: _sync_tool_to_specfact now uses adapter pattern, so converter/scanner are no longer needed

    progress_columns, progress_kwargs = get_progress_config()
    with Progress(
        *progress_columns,
        console=console,
        **progress_kwargs,
    ) as progress:
        # Step 3: Discover features using adapter (via bridge config)
        task = progress.add_task(f"[cyan]Scanning {adapter_type.value} artifacts...[/cyan]", total=None)
        progress.update(task, description=f"[cyan]Scanning {adapter_type.value} artifacts...[/cyan]")

        # Discover features using adapter or bridge_sync (adapter-agnostic)
        features: list[dict[str, Any]] = []
        # Use adapter's discover_features method if available (e.g., Spec-Kit adapter)
        if adapter_instance and hasattr(adapter_instance, "discover_features"):
            features = adapter_instance.discover_features(repo, bridge_config)
        else:
            # For other adapters, use bridge_sync to discover features
            feature_ids = bridge_sync._discover_feature_ids()
            # Convert feature_ids to feature dicts (simplified for now)
            features = [{"feature_key": fid} for fid in feature_ids]

        progress.update(task, description=f"[green]✓[/green] Found {len(features)} features")

        # Step 3.5: Validate tool artifacts for unidirectional sync
        if not bidirectional and len(features) == 0:
            console.print(f"[bold red]✗[/bold red] No {adapter_type.value} features found")
            console.print(
                f"[red]Unidirectional sync ({adapter_type.value} → SpecFact) requires at least one feature specification.[/red]"
            )
            console.print("\n[bold yellow]Next Steps:[/bold yellow]")
            console.print(f"1. Create feature specifications in your {adapter_type.value} project")
            console.print(f"2. Then run 'specfact sync bridge --adapter {adapter_type.value}' again")
            console.print(
                f"\n[dim]Note: For bidirectional sync, {adapter_type.value} artifacts are optional if syncing from SpecFact → {adapter_type.value}[/dim]"
            )
            raise typer.Exit(1)

        # Step 4: Sync based on mode
        features_converted_speckit = 0
        conflicts: list[dict[str, Any]] = []  # Initialize conflicts for use in summary

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
                        # Fallback: create minimal bundle via adapter (but skip expensive parsing)
                        progress.update(
                            task, description=f"[cyan]Creating plan bundle from {adapter_type.value}...[/cyan]"
                        )
                        merged_bundle = _sync_tool_to_specfact(
                            repo, adapter_instance, bridge_config, bridge_sync, progress, task
                        )[0]
                else:
                    # No plan path found, create minimal bundle
                    progress.update(task, description=f"[cyan]Creating plan bundle from {adapter_type.value}...[/cyan]")
                    merged_bundle = _sync_tool_to_specfact(
                        repo, adapter_instance, bridge_config, bridge_sync, progress, task
                    )[0]
            else:
                task = progress.add_task(f"[cyan]Converting {adapter_type.value} → SpecFact...[/cyan]", total=None)
                # Show current activity (spinner will show automatically)
                progress.update(task, description=f"[cyan]Converting {adapter_type.value} → SpecFact...[/cyan]")
                merged_bundle, features_updated, features_added = _sync_tool_to_specfact(
                    repo, adapter_instance, bridge_config, bridge_sync, progress
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
            # Uses adapter's change detection if available (adapter-agnostic)

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
                    # Delete existing tool artifacts before conversion
                    specs_dir = repo / "specs"
                    if specs_dir.exists():
                        console.print(
                            f"[yellow]⚠[/yellow] Overwrite mode: Removing existing {adapter_type.value} artifacts..."
                        )
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

                # Use adapter's export_bundle method (adapter-agnostic)
                if adapter_instance and hasattr(adapter_instance, "export_bundle"):
                    features_converted_speckit = adapter_instance.export_bundle(
                        plan_bundle_to_convert, repo, update_progress, bridge_config
                    )
                else:
                    msg = "Bundle export not available for this adapter"
                    raise RuntimeError(msg)
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

            # Detect conflicts between both directions using adapter
            if (
                adapter_instance
                and hasattr(adapter_instance, "detect_changes")
                and hasattr(adapter_instance, "detect_conflicts")
            ):
                # Detect changes in both directions
                changes_result = adapter_instance.detect_changes(repo, direction="both", bridge_config=bridge_config)
                speckit_changes = changes_result.get("speckit_changes", {})
                specfact_changes = changes_result.get("specfact_changes", {})
                # Detect conflicts
                conflicts = adapter_instance.detect_conflicts(speckit_changes, specfact_changes)
            else:
                # Fallback: no conflict detection available
                conflicts = []

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

            merged_bundle, features_updated, features_added = _sync_tool_to_specfact(
                repo, adapter_instance, bridge_config, bridge_sync, progress
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
                if merged_bundle:
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


@beartype
@require(lambda repo: repo.exists(), "Repository path must exist")
@require(lambda repo: repo.is_dir(), "Repository path must be a directory")
@require(lambda adapter_instance: adapter_instance is not None, "Adapter instance must not be None")
@require(lambda bridge_config: bridge_config is not None, "Bridge config must not be None")
@require(lambda bridge_sync: bridge_sync is not None, "Bridge sync must not be None")
@require(lambda progress: progress is not None, "Progress must not be None")
@require(lambda task: task is None or (isinstance(task, int) and task >= 0), "Task must be None or non-negative int")
@ensure(lambda result: isinstance(result, tuple) and len(result) == 3, "Must return tuple of 3 elements")
@ensure(lambda result: isinstance(result[0], PlanBundle), "First element must be PlanBundle")
@ensure(lambda result: isinstance(result[1], int) and result[1] >= 0, "Second element must be non-negative int")
@ensure(lambda result: isinstance(result[2], int) and result[2] >= 0, "Third element must be non-negative int")
def _sync_tool_to_specfact(
    repo: Path,
    adapter_instance: Any,
    bridge_config: Any,
    bridge_sync: Any,
    progress: Any,
    task: int | None = None,
) -> tuple[PlanBundle, int, int]:
    """
    Sync tool artifacts to SpecFact format using adapter registry pattern.

    This is an adapter-agnostic replacement for _sync_speckit_to_specfact that uses
    the adapter registry instead of hard-coded converter/scanner instances.

    Args:
        repo: Repository path
        adapter_instance: Adapter instance from registry
        bridge_config: Bridge configuration
        bridge_sync: BridgeSync instance
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

    # Convert tool artifacts to SpecFact using adapter pattern
    if task is not None:
        progress.update(task, description="[cyan]Converting tool artifacts to SpecFact format...[/cyan]")

    # Get default bundle name for ProjectBundle operations
    from specfact_cli.utils.structure import SpecFactStructure

    bundle_name = SpecFactStructure.get_active_bundle_name(repo) or SpecFactStructure.DEFAULT_PLAN_NAME
    bundle_dir = repo / SpecFactStructure.PROJECTS / bundle_name

    # Ensure bundle directory exists
    bundle_dir.mkdir(parents=True, exist_ok=True)

    # Load or create ProjectBundle
    from specfact_cli.models.project import BundleManifest, BundleVersions, ProjectBundle
    from specfact_cli.utils.bundle_loader import load_project_bundle

    project_bundle: ProjectBundle | None = None
    if bundle_dir.exists() and (bundle_dir / "bundle.manifest.yaml").exists():
        try:
            project_bundle = load_project_bundle(bundle_dir, validate_hashes=False)
        except Exception:
            # Bundle exists but failed to load - create new one
            project_bundle = None

    if project_bundle is None:
        # Create new ProjectBundle with latest schema version
        from specfact_cli.migrations.plan_migrator import get_latest_schema_version

        manifest = BundleManifest(
            versions=BundleVersions(schema=get_latest_schema_version(), project="0.1.0"),
            schema_metadata=None,
            project_metadata=None,
        )
        from specfact_cli.models.plan import Product

        project_bundle = ProjectBundle(
            manifest=manifest,
            bundle_name=bundle_name,
            product=Product(themes=[], releases=[]),
            features={},
            idea=None,
            business=None,
            clarifications=None,
        )

    # Discover features using adapter
    discovered_features = []
    if hasattr(adapter_instance, "discover_features"):
        discovered_features = adapter_instance.discover_features(repo, bridge_config)
    else:
        # Fallback: use bridge_sync to discover feature IDs
        feature_ids = bridge_sync._discover_feature_ids()
        discovered_features = [{"feature_key": fid} for fid in feature_ids]

    # Import each feature using adapter pattern
    # Import artifacts in order: specification (required), then plan and tasks (if available)
    artifact_order = ["specification", "plan", "tasks"]
    for feature_data in discovered_features:
        feature_id = feature_data.get("feature_key", "")
        if not feature_id:
            continue

        # Import artifacts in order (specification first, then plan/tasks if available)
        for artifact_key in artifact_order:
            # Check if artifact type is supported by bridge config
            if artifact_key not in bridge_config.artifacts:
                continue

            try:
                result = bridge_sync.import_artifact(artifact_key, feature_id, bundle_name)
                if not result.success and task is not None and artifact_key == "specification":
                    # Log error but continue with other artifacts/features
                    # Only show warning for specification (required), skip warnings for optional artifacts
                    progress.update(
                        task,
                        description=f"[yellow]⚠[/yellow] Failed to import {artifact_key} for {feature_id}: {result.errors[0] if result.errors else 'Unknown error'}",
                    )
            except Exception as e:
                # Log error but continue
                if task is not None and artifact_key == "specification":
                    progress.update(
                        task, description=f"[yellow]⚠[/yellow] Error importing {artifact_key} for {feature_id}: {e}"
                    )

    # Save project bundle after all imports (BridgeSync.import_artifact saves automatically, but ensure it's saved)
    from specfact_cli.utils.bundle_loader import save_project_bundle

    try:
        project_bundle = load_project_bundle(bundle_dir, validate_hashes=False)
        save_project_bundle(project_bundle, bundle_dir, atomic=True)
    except Exception:
        # If loading fails, we'll create a new bundle below
        project_bundle = None

    # Reload project bundle to get updated features (after all imports)
    # BridgeSync.import_artifact saves automatically, so reload to get latest state
    try:
        project_bundle = load_project_bundle(bundle_dir, validate_hashes=False)
    except Exception:
        # If loading fails after imports, something went wrong - create minimal bundle
        if project_bundle is None:
            from specfact_cli.migrations.plan_migrator import get_latest_schema_version

            manifest = BundleManifest(
                versions=BundleVersions(schema=get_latest_schema_version(), project="0.1.0"),
                schema_metadata=None,
                project_metadata=None,
            )
            from specfact_cli.models.plan import Product

            project_bundle = ProjectBundle(
                manifest=manifest,
                bundle_name=bundle_name,
                product=Product(themes=[], releases=[]),
                features={},
                idea=None,
                business=None,
                clarifications=None,
            )
            save_project_bundle(project_bundle, bundle_dir, atomic=True)

    # Convert ProjectBundle to PlanBundle for merging logic
    from specfact_cli.commands.plan import _convert_project_bundle_to_plan_bundle

    converted_bundle = _convert_project_bundle_to_plan_bundle(project_bundle)

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
@beartype
@require(lambda repo: repo.exists(), "Repository path must exist")
@require(lambda repo: repo.is_dir(), "Repository path must be a directory")
@require(
    lambda bundle: bundle is None or (isinstance(bundle, str) and len(bundle) > 0),
    "Bundle must be None or non-empty str",
)
@require(lambda bidirectional: isinstance(bidirectional, bool), "Bidirectional must be bool")
@require(
    lambda mode: mode is None
    or mode in ("read-only", "export-only", "import-annotation", "bidirectional", "unidirectional"),
    "Mode must be valid sync mode",
)
@require(lambda overwrite: isinstance(overwrite, bool), "Overwrite must be bool")
@require(
    lambda adapter: adapter is None or (isinstance(adapter, str) and len(adapter) > 0),
    "Adapter must be None or non-empty str",
)
@ensure(lambda result: result is None, "Must return None")
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
        help="Project bundle name for SpecFact → tool conversion (default: auto-detect). Required for cross-adapter sync to preserve lossless content.",
    ),
    # Behavior/Options
    bidirectional: bool = typer.Option(
        False,
        "--bidirectional",
        help="Enable bidirectional sync (tool ↔ SpecFact)",
    ),
    mode: str | None = typer.Option(
        None,
        "--mode",
        help="Sync mode: 'read-only' (OpenSpec → SpecFact), 'export-only' (SpecFact → DevOps), 'bidirectional' (tool ↔ SpecFact). Default: bidirectional if --bidirectional, else unidirectional. For backlog adapters (github/ado), use 'export-only' with --bundle for cross-adapter sync.",
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
        help="Adapter type: speckit, openspec, generic-markdown, github (available), ado (available), linear, jira, notion (future). Default: auto-detect. Use 'github' or 'ado' for backlog sync with cross-adapter capabilities (requires --bundle for lossless sync).",
        hidden=True,  # Hidden by default, shown with --help-advanced
    ),
    repo_owner: str | None = typer.Option(
        None,
        "--repo-owner",
        help="GitHub repository owner (for GitHub adapter). Required for GitHub backlog sync.",
        hidden=True,
    ),
    repo_name: str | None = typer.Option(
        None,
        "--repo-name",
        help="GitHub repository name (for GitHub adapter). Required for GitHub backlog sync.",
        hidden=True,
    ),
    external_base_path: Path | None = typer.Option(
        None,
        "--external-base-path",
        help="Base path for external tool repository (for cross-repo integrations, e.g., OpenSpec in different repo)",
        file_okay=False,
        dir_okay=True,
    ),
    github_token: str | None = typer.Option(
        None,
        "--github-token",
        help="GitHub API token (optional, uses GITHUB_TOKEN env var or gh CLI if not provided)",
        hidden=True,
    ),
    use_gh_cli: bool = typer.Option(
        True,
        "--use-gh-cli/--no-gh-cli",
        help="Use GitHub CLI (`gh auth token`) to get token automatically (default: True). Useful in enterprise environments where PAT creation is restricted.",
        hidden=True,
    ),
    ado_org: str | None = typer.Option(
        None,
        "--ado-org",
        help="Azure DevOps organization (for ADO adapter). Required for ADO backlog sync.",
        hidden=True,
    ),
    ado_project: str | None = typer.Option(
        None,
        "--ado-project",
        help="Azure DevOps project (for ADO adapter). Required for ADO backlog sync.",
        hidden=True,
    ),
    ado_base_url: str | None = typer.Option(
        None,
        "--ado-base-url",
        help="Azure DevOps base URL (for ADO adapter, defaults to https://dev.azure.com). Use for Azure DevOps Server (on-prem).",
        hidden=True,
    ),
    ado_token: str | None = typer.Option(
        None,
        "--ado-token",
        help="Azure DevOps PAT (optional, uses AZURE_DEVOPS_TOKEN env var if not provided). Requires Work Items (Read & Write) permissions.",
        hidden=True,
    ),
    ado_work_item_type: str | None = typer.Option(
        None,
        "--ado-work-item-type",
        help="Azure DevOps work item type (for ADO adapter, derived from process template if not provided). Examples: 'User Story', 'Product Backlog Item', 'Bug'.",
        hidden=True,
    ),
    sanitize: bool | None = typer.Option(
        None,
        "--sanitize/--no-sanitize",
        help="Sanitize proposal content for public issues (default: auto-detect based on repo setup). Removes competitive analysis, internal strategy, implementation details.",
        hidden=True,
    ),
    target_repo: str | None = typer.Option(
        None,
        "--target-repo",
        help="Target repository for issue creation (format: owner/repo). Default: same as code repository.",
        hidden=True,
    ),
    interactive: bool = typer.Option(
        False,
        "--interactive",
        help="Interactive mode for AI-assisted sanitization (requires slash command).",
        hidden=True,
    ),
    change_ids: str | None = typer.Option(
        None,
        "--change-ids",
        help="Comma-separated list of change proposal IDs to export (default: all active proposals). Use with --bundle for cross-adapter export. Example: 'add-feature-x,update-api'. Find change IDs in import output or bundle directory.",
    ),
    backlog_ids: str | None = typer.Option(
        None,
        "--backlog-ids",
        help="Comma-separated list of backlog item IDs or URLs to import (GitHub/ADO). Use with --bundle to store lossless content for cross-adapter sync. Example: '123,456' or 'https://github.com/org/repo/issues/123'",
    ),
    backlog_ids_file: Path | None = typer.Option(
        None,
        "--backlog-ids-file",
        help="Path to file containing backlog item IDs/URLs (one per line or comma-separated).",
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
    export_to_tmp: bool = typer.Option(
        False,
        "--export-to-tmp",
        help="Export proposal content to temporary file for LLM review (default: <system-temp>/specfact-proposal-<change-id>.md).",
        hidden=True,
    ),
    import_from_tmp: bool = typer.Option(
        False,
        "--import-from-tmp",
        help="Import sanitized content from temporary file after LLM review (default: <system-temp>/specfact-proposal-<change-id>-sanitized.md).",
        hidden=True,
    ),
    tmp_file: Path | None = typer.Option(
        None,
        "--tmp-file",
        help="Custom temporary file path (default: <system-temp>/specfact-proposal-<change-id>.md).",
        hidden=True,
    ),
    update_existing: bool = typer.Option(
        False,
        "--update-existing/--no-update-existing",
        help="Update existing issue bodies when proposal content changes (default: False for safety). Uses content hash to detect changes.",
        hidden=True,
    ),
    track_code_changes: bool = typer.Option(
        False,
        "--track-code-changes/--no-track-code-changes",
        help="Detect code changes (git commits, file modifications) and add progress comments to existing issues (default: False).",
        hidden=True,
    ),
    add_progress_comment: bool = typer.Option(
        False,
        "--add-progress-comment/--no-add-progress-comment",
        help="Add manual progress comment to existing issues without code change detection (default: False).",
        hidden=True,
    ),
    code_repo: Path | None = typer.Option(
        None,
        "--code-repo",
        help="Path to source code repository for code change detection (default: same as --repo). Required when OpenSpec repository differs from source code repository.",
        hidden=True,
    ),
    include_archived: bool = typer.Option(
        False,
        "--include-archived/--no-include-archived",
        help="Include archived change proposals in sync (default: False). Useful for updating existing issues with new comment logic or branch detection improvements.",
        hidden=True,
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

    Synchronizes artifacts from external tools (Spec-Kit, OpenSpec, GitHub, ADO, Linear, Jira, etc.) with
    SpecFact project bundles using configurable bridge mappings.

    **Related**: Use `specfact backlog refine` to standardize backlog items with template-driven refinement
    before syncing to OpenSpec bundles. See backlog refinement guide for details.

    Supported adapters:
    - speckit: Spec-Kit projects (specs/, .specify/) - import & sync
    - generic-markdown: Generic markdown-based specifications - import & sync
    - openspec: OpenSpec integration (openspec/) - read-only sync (Phase 1)
    - github: GitHub Issues - bidirectional sync (import issues as change proposals, export proposals as issues)
    - ado: Azure DevOps Work Items - bidirectional sync (import work items as change proposals, export proposals as work items)
    - linear: Linear Issues (future) - planned
    - jira: Jira Issues (future) - planned
    - notion: Notion pages (future) - planned

    **Sync Modes:**
    - read-only: OpenSpec → SpecFact (read specs, no writes) - OpenSpec adapter only
    - bidirectional: Full two-way sync (tool ↔ SpecFact) - Spec-Kit, GitHub, and ADO adapters
      - GitHub: Import issues as change proposals, export proposals as issues
      - ADO: Import work items as change proposals, export proposals as work items
      - Spec-Kit: Full bidirectional sync of specs and plans
    - export-only: SpecFact → DevOps (create/update issues/work items, no import) - GitHub and ADO adapters
    - import-annotation: DevOps → SpecFact (import issues, annotate with findings) - future

    **🚀 Cross-Adapter Sync (Advanced Feature):**
    Enable lossless round-trip synchronization between different backlog adapters (GitHub ↔ ADO):
    - Use --bundle to preserve lossless content during cross-adapter syncs
    - Import from one adapter (e.g., GitHub) into a bundle, then export to another (e.g., ADO)
    - Content is preserved exactly as imported, enabling 100% fidelity migrations
    - Example: Import GitHub issue → bundle → export to ADO (no content loss)

    **Parameter Groups:**
    - **Target/Input**: --repo, --bundle
    - **Behavior/Options**: --bidirectional, --mode, --overwrite, --watch, --ensure-compliance
    - **Advanced/Configuration**: --adapter, --interval, --repo-owner, --repo-name, --github-token
    - **GitHub Options**: --repo-owner, --repo-name, --github-token, --use-gh-cli, --sanitize
    - **ADO Options**: --ado-org, --ado-project, --ado-base-url, --ado-token, --ado-work-item-type

    **Basic Examples:**
        specfact sync bridge --adapter speckit --repo . --bidirectional
        specfact sync bridge --adapter openspec --repo . --mode read-only  # OpenSpec → SpecFact (read-only)
        specfact sync bridge --adapter openspec --repo . --external-base-path ../other-repo  # Cross-repo OpenSpec
        specfact sync bridge --repo . --bidirectional  # Auto-detect adapter
        specfact sync bridge --repo . --watch --interval 10

    **GitHub Examples:**
        specfact sync bridge --adapter github --bidirectional --repo-owner owner --repo-name repo  # Bidirectional sync
        specfact sync bridge --adapter github --mode export-only --repo-owner owner --repo-name repo  # Export only
        specfact sync bridge --adapter github --update-existing  # Update existing issues when content changes
        specfact sync bridge --adapter github --track-code-changes  # Detect code changes and add progress comments
        specfact sync bridge --adapter github --add-progress-comment  # Add manual progress comment

    **Azure DevOps Examples:**
        specfact sync bridge --adapter ado --bidirectional --ado-org myorg --ado-project myproject  # Bidirectional sync
        specfact sync bridge --adapter ado --mode export-only --ado-org myorg --ado-project myproject  # Export only
        specfact sync bridge --adapter ado --mode export-only --ado-org myorg --ado-project myproject --bundle main  # Bundle export

    **Cross-Adapter Sync Examples:**
        # GitHub → ADO Migration (lossless round-trip)
        specfact sync bridge --adapter github --mode bidirectional --bundle migration --backlog-ids 123
        # Output shows: "✓ Imported GitHub issue #123 as change proposal: add-feature-x"
        specfact sync bridge --adapter ado --mode export-only --bundle migration --change-ids add-feature-x

        # Multi-Tool Workflow (public GitHub + internal ADO)
        specfact sync bridge --adapter github --mode export-only --sanitize  # Export to public GitHub
        specfact sync bridge --adapter github --mode bidirectional --bundle internal --backlog-ids 123  # Import to bundle
        specfact sync bridge --adapter ado --mode export-only --bundle internal --change-ids <change-id>  # Export to ADO

    **Finding Change IDs:**
    - Change IDs are shown in import output: "✓ Imported as change proposal: <change-id>"
    - Or check bundle directory: ls .specfact/projects/<bundle>/change_tracking/proposals/
    - Or check OpenSpec directory: ls openspec/changes/

    See docs/guides/devops-adapter-integration.md for complete documentation.
    """
    if is_debug_mode():
        debug_log_operation(
            "command",
            "sync bridge",
            "started",
            extra={"repo": str(repo), "bundle": bundle, "adapter": adapter, "bidirectional": bidirectional},
        )
        debug_print("[dim]sync bridge: started[/dim]")

    # Auto-detect adapter if not specified
    from specfact_cli.sync.bridge_probe import BridgeProbe

    if adapter == "speckit" or adapter == "auto":
        probe = BridgeProbe(repo)
        detected_capabilities = probe.detect()
        # Use detected tool directly (e.g., "speckit", "openspec", "github")
        # BridgeProbe already tries all registered adapters
        if detected_capabilities.tool == "unknown":
            console.print("[bold red]✗[/bold red] Could not auto-detect adapter")
            console.print("[dim]No registered adapter detected this repository structure[/dim]")
            registered = AdapterRegistry.list_adapters()
            console.print(f"[dim]Registered adapters: {', '.join(registered)}[/dim]")
            console.print("[dim]Tip: Specify adapter explicitly with --adapter <adapter>[/dim]")
            raise typer.Exit(1)
        adapter = detected_capabilities.tool

    # Validate adapter using registry (no hard-coded checks)
    adapter_lower = adapter.lower()
    if not AdapterRegistry.is_registered(adapter_lower):
        console.print(f"[bold red]✗[/bold red] Unsupported adapter: {adapter}")
        registered = AdapterRegistry.list_adapters()
        console.print(f"[dim]Registered adapters: {', '.join(registered)}[/dim]")
        raise typer.Exit(1)

    # Convert to AdapterType enum (for backward compatibility with existing code)
    try:
        adapter_type = AdapterType(adapter_lower)
    except ValueError:
        # Adapter is registered but not in enum (e.g., openspec might not be in enum yet)
        # Use adapter string value directly
        adapter_type = None

    # Determine adapter_value for use throughout function
    adapter_value = adapter_type.value if adapter_type else adapter_lower

    # Determine sync mode using adapter capabilities (adapter-agnostic)
    if mode is None:
        # Get adapter to check capabilities
        adapter_instance = AdapterRegistry.get_adapter(adapter_lower)
        if adapter_instance:
            # Get capabilities to determine supported sync modes
            probe = BridgeProbe(repo)
            capabilities = probe.detect()
            bridge_config = probe.auto_generate_bridge(capabilities) if capabilities.tool != "unknown" else None
            adapter_capabilities = adapter_instance.get_capabilities(repo, bridge_config)

            # Use adapter's supported sync modes if available
            if adapter_capabilities.supported_sync_modes:
                # Auto-select based on adapter capabilities and context
                if "export-only" in adapter_capabilities.supported_sync_modes and (repo_owner or repo_name):
                    sync_mode = "export-only"
                elif "read-only" in adapter_capabilities.supported_sync_modes:
                    sync_mode = "read-only"
                elif "bidirectional" in adapter_capabilities.supported_sync_modes:
                    sync_mode = "bidirectional" if bidirectional else "unidirectional"
                else:
                    sync_mode = "unidirectional"  # Default fallback
            else:
                # Fallback: use bidirectional/unidirectional based on flag
                sync_mode = "bidirectional" if bidirectional else "unidirectional"
        else:
            # Fallback if adapter not found
            sync_mode = "bidirectional" if bidirectional else "unidirectional"
    else:
        sync_mode = mode.lower()

    # Validate mode for adapter type using adapter capabilities
    adapter_instance = AdapterRegistry.get_adapter(adapter_lower)
    adapter_capabilities = None
    if adapter_instance:
        probe = BridgeProbe(repo)
        capabilities = probe.detect()
        bridge_config = probe.auto_generate_bridge(capabilities) if capabilities.tool != "unknown" else None
        adapter_capabilities = adapter_instance.get_capabilities(repo, bridge_config)

        if adapter_capabilities.supported_sync_modes and sync_mode not in adapter_capabilities.supported_sync_modes:
            console.print(f"[bold red]✗[/bold red] Sync mode '{sync_mode}' not supported by adapter '{adapter_lower}'")
            console.print(f"[dim]Supported modes: {', '.join(adapter_capabilities.supported_sync_modes)}[/dim]")
            raise typer.Exit(1)

    # Validate temporary file workflow parameters
    if export_to_tmp and import_from_tmp:
        console.print("[bold red]✗[/bold red] --export-to-tmp and --import-from-tmp are mutually exclusive")
        raise typer.Exit(1)

    # Parse change_ids if provided
    change_ids_list: list[str] | None = None
    if change_ids:
        change_ids_list = [cid.strip() for cid in change_ids.split(",") if cid.strip()]

    backlog_items: list[str] = []
    if backlog_ids:
        backlog_items.extend(_parse_backlog_selection(backlog_ids))
    if backlog_ids_file:
        backlog_items.extend(_parse_backlog_selection(backlog_ids_file.read_text(encoding="utf-8")))
    if backlog_items:
        backlog_items = list(dict.fromkeys(backlog_items))

    telemetry_metadata = {
        "adapter": adapter_value,
        "mode": sync_mode,
        "bidirectional": bidirectional,
        "watch": watch,
        "overwrite": overwrite,
        "interval": interval,
    }

    with telemetry.track_command("sync.bridge", telemetry_metadata) as record:
        # Handle export-only mode (SpecFact → DevOps)
        if sync_mode == "export-only":
            from specfact_cli.sync.bridge_sync import BridgeSync

            console.print(f"[bold cyan]Exporting OpenSpec change proposals to {adapter_value}...[/bold cyan]")

            # Create bridge config using adapter registry
            from specfact_cli.models.bridge import BridgeConfig

            adapter_instance = AdapterRegistry.get_adapter(adapter_value)
            bridge_config = adapter_instance.generate_bridge_config(repo)

            # Create bridge sync instance
            bridge_sync = BridgeSync(repo, bridge_config=bridge_config)

            # If bundle is provided for backlog adapters, export stored backlog items from bundle
            if adapter_value in ("github", "ado") and bundle:
                resolved_bundle = bundle or _infer_bundle_name(repo)
                if not resolved_bundle:
                    console.print("[bold red]✗[/bold red] Bundle name required for backlog export")
                    console.print("[dim]Provide --bundle or set an active bundle in .specfact/config.yaml[/dim]")
                    raise typer.Exit(1)

                console.print(
                    f"[bold cyan]Exporting bundle backlog items to {adapter_value} ({resolved_bundle})...[/bold cyan]"
                )
                if adapter_value == "github":
                    adapter_kwargs = {
                        "repo_owner": repo_owner,
                        "repo_name": repo_name,
                        "api_token": github_token,
                        "use_gh_cli": use_gh_cli,
                    }
                else:
                    adapter_kwargs = {
                        "org": ado_org,
                        "project": ado_project,
                        "base_url": ado_base_url,
                        "api_token": ado_token,
                        "work_item_type": ado_work_item_type,
                    }
                result = bridge_sync.export_backlog_from_bundle(
                    adapter_type=adapter_value,
                    bundle_name=resolved_bundle,
                    adapter_kwargs=adapter_kwargs,
                    update_existing=update_existing,
                    change_ids=change_ids_list,
                )

                if result.success:
                    console.print(
                        f"[bold green]✓[/bold green] Exported {len(result.operations)} backlog item(s) from bundle"
                    )
                    for warning in result.warnings:
                        console.print(f"[yellow]⚠[/yellow] {warning}")
                else:
                    console.print(f"[bold red]✗[/bold red] Export failed with {len(result.errors)} errors")
                    for error in result.errors:
                        console.print(f"[red]  • {error}[/red]")
                    raise typer.Exit(1)

                return

            # Export change proposals
            progress_columns, progress_kwargs = get_progress_config()
            with Progress(
                *progress_columns,
                console=console,
                **progress_kwargs,
            ) as progress:
                task = progress.add_task("[cyan]Syncing change proposals to DevOps...[/cyan]", total=None)

                # Resolve code_repo_path if provided, otherwise use repo (OpenSpec repo)
                code_repo_path_for_export = Path(code_repo).resolve() if code_repo else repo.resolve()

                result = bridge_sync.export_change_proposals_to_devops(
                    include_archived=include_archived,
                    adapter_type=adapter_value,
                    repo_owner=repo_owner,
                    repo_name=repo_name,
                    api_token=github_token if adapter_value == "github" else ado_token,
                    use_gh_cli=use_gh_cli,
                    sanitize=sanitize,
                    target_repo=target_repo,
                    interactive=interactive,
                    change_ids=change_ids_list,
                    export_to_tmp=export_to_tmp,
                    import_from_tmp=import_from_tmp,
                    tmp_file=tmp_file,
                    update_existing=update_existing,
                    track_code_changes=track_code_changes,
                    add_progress_comment=add_progress_comment,
                    code_repo_path=code_repo_path_for_export,
                    ado_org=ado_org,
                    ado_project=ado_project,
                    ado_base_url=ado_base_url,
                    ado_work_item_type=ado_work_item_type,
                )
                progress.update(task, description="[green]✓[/green] Sync complete")

            # Report results
            if result.success:
                console.print(
                    f"[bold green]✓[/bold green] Successfully synced {len(result.operations)} change proposals"
                )
                if result.warnings:
                    for warning in result.warnings:
                        console.print(f"[yellow]⚠[/yellow] {warning}")
            else:
                console.print(f"[bold red]✗[/bold red] Sync failed with {len(result.errors)} errors")
                for error in result.errors:
                    console.print(f"[red]  • {error}[/red]")
                raise typer.Exit(1)

            # Telemetry is automatically tracked via context manager
            return

        # Handle read-only mode (OpenSpec → SpecFact)
        if sync_mode == "read-only":
            from specfact_cli.models.bridge import BridgeConfig
            from specfact_cli.sync.bridge_sync import BridgeSync

            console.print(f"[bold cyan]Syncing OpenSpec artifacts (read-only) from:[/bold cyan] {repo}")

            # Create bridge config with external_base_path if provided
            bridge_config = BridgeConfig.preset_openspec()
            if external_base_path:
                if not external_base_path.exists() or not external_base_path.is_dir():
                    console.print(
                        f"[bold red]✗[/bold red] External base path does not exist or is not a directory: {external_base_path}"
                    )
                    raise typer.Exit(1)
                bridge_config.external_base_path = external_base_path.resolve()

            # Create bridge sync instance
            bridge_sync = BridgeSync(repo, bridge_config=bridge_config)

            # Import OpenSpec artifacts
            # In test mode, skip Progress to avoid stream closure issues with test framework
            if _is_test_mode():
                # Test mode: simple console output without Progress
                console.print("[cyan]Importing OpenSpec artifacts...[/cyan]")

                # Import project context
                if bundle:
                    # Import specific artifacts for the bundle
                    # For now, import all OpenSpec specs
                    openspec_specs_dir = (
                        bridge_config.external_base_path / "openspec" / "specs"
                        if bridge_config.external_base_path
                        else repo / "openspec" / "specs"
                    )
                    if openspec_specs_dir.exists():
                        for spec_dir in openspec_specs_dir.iterdir():
                            if spec_dir.is_dir() and (spec_dir / "spec.md").exists():
                                feature_id = spec_dir.name
                                result = bridge_sync.import_artifact("specification", feature_id, bundle)
                                if not result.success:
                                    console.print(
                                        f"[yellow]⚠[/yellow] Failed to import {feature_id}: {', '.join(result.errors)}"
                                    )

                console.print("[green]✓[/green] Import complete")
            else:
                # Normal mode: use Progress
                progress_columns, progress_kwargs = get_progress_config()
                with Progress(
                    *progress_columns,
                    console=console,
                    **progress_kwargs,
                ) as progress:
                    task = progress.add_task("[cyan]Importing OpenSpec artifacts...[/cyan]", total=None)

                    # Import project context
                    if bundle:
                        # Import specific artifacts for the bundle
                        # For now, import all OpenSpec specs
                        openspec_specs_dir = (
                            bridge_config.external_base_path / "openspec" / "specs"
                            if bridge_config.external_base_path
                            else repo / "openspec" / "specs"
                        )
                        if openspec_specs_dir.exists():
                            for spec_dir in openspec_specs_dir.iterdir():
                                if spec_dir.is_dir() and (spec_dir / "spec.md").exists():
                                    feature_id = spec_dir.name
                                    result = bridge_sync.import_artifact("specification", feature_id, bundle)
                                    if not result.success:
                                        console.print(
                                            f"[yellow]⚠[/yellow] Failed to import {feature_id}: {', '.join(result.errors)}"
                                        )

                    progress.update(task, description="[green]✓[/green] Import complete")
                    # Ensure progress output is flushed before context exits
                    progress.refresh()

            # Generate alignment report
            if bundle:
                console.print("\n[bold]Generating alignment report...[/bold]")
                bridge_sync.generate_alignment_report(bundle)

            console.print("[bold green]✓[/bold green] Read-only sync complete")
            return

        console.print(f"[bold cyan]Syncing {adapter_value} artifacts from:[/bold cyan] {repo}")

        # Use adapter capabilities to check if bidirectional sync is supported
        if adapter_capabilities and (
            adapter_capabilities.supported_sync_modes
            and "bidirectional" not in adapter_capabilities.supported_sync_modes
        ):
            console.print(f"[yellow]⚠ Adapter '{adapter_value}' does not support bidirectional sync[/yellow]")
            console.print(f"[dim]Supported modes: {', '.join(adapter_capabilities.supported_sync_modes)}[/dim]")
            console.print("[dim]Use read-only mode for adapters that don't support bidirectional sync[/dim]")
            raise typer.Exit(1)

        # Ensure tool compliance if requested
        if ensure_compliance:
            adapter_display = adapter_type.value if adapter_type else adapter_value
            console.print(f"\n[cyan]🔍 Validating plan bundle for {adapter_display} compliance...[/cyan]")
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

        if adapter_value in ("github", "ado") and sync_mode == "bidirectional":
            from specfact_cli.sync.bridge_sync import BridgeSync

            resolved_bundle = bundle or _infer_bundle_name(resolved_repo)
            if not resolved_bundle:
                console.print("[bold red]✗[/bold red] Bundle name required for backlog sync")
                console.print("[dim]Provide --bundle or set an active bundle in .specfact/config.yaml[/dim]")
                raise typer.Exit(1)

            if not backlog_items and interactive and runtime.is_interactive():
                prompt = typer.prompt(
                    "Enter backlog item IDs/URLs to import (comma-separated, leave blank to skip)",
                    default="",
                )
                backlog_items = _parse_backlog_selection(prompt)
                backlog_items = list(dict.fromkeys(backlog_items))

            if backlog_items:
                console.print(f"[dim]Selected backlog items ({len(backlog_items)}): {', '.join(backlog_items)}[/dim]")
            else:
                console.print("[yellow]⚠[/yellow] No backlog items selected; import skipped")

            adapter_instance = AdapterRegistry.get_adapter(adapter_value)
            bridge_config = adapter_instance.generate_bridge_config(resolved_repo)
            bridge_sync = BridgeSync(resolved_repo, bridge_config=bridge_config)

            if backlog_items:
                if adapter_value == "github":
                    adapter_kwargs = {
                        "repo_owner": repo_owner,
                        "repo_name": repo_name,
                        "api_token": github_token,
                        "use_gh_cli": use_gh_cli,
                    }
                else:
                    adapter_kwargs = {
                        "org": ado_org,
                        "project": ado_project,
                        "base_url": ado_base_url,
                        "api_token": ado_token,
                        "work_item_type": ado_work_item_type,
                    }

                import_result = bridge_sync.import_backlog_items_to_bundle(
                    adapter_type=adapter_value,
                    bundle_name=resolved_bundle,
                    backlog_items=backlog_items,
                    adapter_kwargs=adapter_kwargs,
                )
                if import_result.success:
                    console.print(
                        f"[bold green]✓[/bold green] Imported {len(import_result.operations)} backlog item(s)"
                    )
                    for warning in import_result.warnings:
                        console.print(f"[yellow]⚠[/yellow] {warning}")
                else:
                    console.print(f"[bold red]✗[/bold red] Import failed with {len(import_result.errors)} errors")
                    for error in import_result.errors:
                        console.print(f"[red]  • {error}[/red]")
                    raise typer.Exit(1)

            if adapter_value == "github":
                export_adapter_kwargs = {
                    "repo_owner": repo_owner,
                    "repo_name": repo_name,
                    "api_token": github_token,
                    "use_gh_cli": use_gh_cli,
                }
            else:
                export_adapter_kwargs = {
                    "org": ado_org,
                    "project": ado_project,
                    "base_url": ado_base_url,
                    "api_token": ado_token,
                    "work_item_type": ado_work_item_type,
                }

            export_result = bridge_sync.export_backlog_from_bundle(
                adapter_type=adapter_value,
                bundle_name=resolved_bundle,
                adapter_kwargs=export_adapter_kwargs,
                update_existing=update_existing,
                change_ids=change_ids_list,
            )

            if export_result.success:
                console.print(f"[bold green]✓[/bold green] Exported {len(export_result.operations)} backlog item(s)")
                for warning in export_result.warnings:
                    console.print(f"[yellow]⚠[/yellow] {warning}")
            else:
                console.print(f"[bold red]✗[/bold red] Export failed with {len(export_result.errors)} errors")
                for error in export_result.errors:
                    console.print(f"[red]  • {error}[/red]")
                raise typer.Exit(1)

            return

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
        # Convert adapter_value to AdapterType for legacy _perform_sync_operation
        # (This function will be refactored to use adapter registry in future)
        if adapter_type is None:
            # For adapters not in enum yet (like openspec), we can't use legacy sync
            console.print(f"[yellow]⚠ Adapter '{adapter_value}' requires bridge-based sync (not legacy)[/yellow]")
            console.print("[dim]Use read-only mode for OpenSpec adapter[/dim]")
            raise typer.Exit(1)

        _perform_sync_operation(
            repo=resolved_repo,
            bidirectional=bidirectional,
            bundle=bundle,
            overwrite=overwrite,
            adapter_type=adapter_type,
        )
        if is_debug_mode():
            debug_log_operation("command", "sync bridge", "success", extra={"adapter": adapter, "bundle": bundle})
            debug_print("[dim]sync bridge: success[/dim]")
        record({"sync_completed": True})


@app.command("repository")
@beartype
@require(lambda repo: repo.exists(), "Repository path must exist")
@require(lambda repo: repo.is_dir(), "Repository path must be a directory")
@require(
    lambda target: target is None or (isinstance(target, Path) and target.exists()),
    "Target must be None or existing Path",
)
@require(lambda watch: isinstance(watch, bool), "Watch must be bool")
@require(lambda interval: isinstance(interval, int) and interval >= 1, "Interval must be int >= 1")
@require(
    lambda confidence: isinstance(confidence, float) and 0.0 <= confidence <= 1.0,
    "Confidence must be float in [0.0, 1.0]",
)
@ensure(lambda result: result is None, "Must return None")
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
    if is_debug_mode():
        debug_log_operation(
            "command",
            "sync repository",
            "started",
            extra={"repo": str(repo), "target": str(target) if target else None, "watch": watch},
        )
        debug_print("[dim]sync repository: started[/dim]")

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

        if is_debug_mode():
            debug_log_operation(
                "command",
                "sync repository",
                "success",
                extra={"code_changes": len(result.code_changes)},
            )
            debug_print("[dim]sync repository: success[/dim]")
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
    if is_debug_mode():
        debug_log_operation(
            "command",
            "sync intelligent",
            "started",
            extra={"bundle": bundle, "repo": str(repo), "watch": watch},
        )
        debug_print("[dim]sync intelligent: started[/dim]")

    from specfact_cli.utils.structure import SpecFactStructure

    console = get_configured_console()

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

        if is_debug_mode():
            debug_log_operation("command", "sync intelligent", "success", extra={"bundle": bundle})
            debug_print("[dim]sync intelligent: success[/dim]")
        record({"sync_completed": True})

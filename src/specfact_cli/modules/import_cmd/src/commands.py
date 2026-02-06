"""
Import command - Import codebases and external tool projects to contract-driven format.

This module provides commands for importing existing codebases (brownfield) and
external tool projects (e.g., Spec-Kit, OpenSpec, generic-markdown) and converting them to
SpecFact contract-driven format using the bridge architecture.
"""

from __future__ import annotations

import multiprocessing
import os
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

import typer
from beartype import beartype
from icontract import require
from rich.progress import Progress

from specfact_cli import runtime
from specfact_cli.adapters.registry import AdapterRegistry
from specfact_cli.models.plan import Feature, PlanBundle
from specfact_cli.models.project import BundleManifest, BundleVersions, ProjectBundle
from specfact_cli.runtime import debug_log_operation, debug_print, get_configured_console, is_debug_mode
from specfact_cli.telemetry import telemetry
from specfact_cli.utils.performance import track_performance
from specfact_cli.utils.progress import save_bundle_with_progress
from specfact_cli.utils.terminal import get_progress_config


app = typer.Typer(
    help="Import codebases and external tool projects (e.g., Spec-Kit, OpenSpec, generic-markdown) to contract format",
    context_settings={"help_option_names": ["-h", "--help", "--help-advanced", "-ha"]},
)
console = get_configured_console()

if TYPE_CHECKING:
    from specfact_cli.generators.openapi_extractor import OpenAPIExtractor
    from specfact_cli.generators.test_to_openapi import OpenAPITestConverter


_CONTRACT_WORKER_EXTRACTOR: OpenAPIExtractor | None = None
_CONTRACT_WORKER_TEST_CONVERTER: OpenAPITestConverter | None = None
_CONTRACT_WORKER_REPO: Path | None = None
_CONTRACT_WORKER_CONTRACTS_DIR: Path | None = None


def _init_contract_worker(repo_path: str, contracts_dir: str) -> None:
    """Initialize per-process contract extraction state."""
    from specfact_cli.generators.openapi_extractor import OpenAPIExtractor
    from specfact_cli.generators.test_to_openapi import OpenAPITestConverter

    global _CONTRACT_WORKER_CONTRACTS_DIR
    global _CONTRACT_WORKER_EXTRACTOR
    global _CONTRACT_WORKER_REPO
    global _CONTRACT_WORKER_TEST_CONVERTER

    _CONTRACT_WORKER_REPO = Path(repo_path)
    _CONTRACT_WORKER_CONTRACTS_DIR = Path(contracts_dir)
    _CONTRACT_WORKER_EXTRACTOR = OpenAPIExtractor(_CONTRACT_WORKER_REPO)
    _CONTRACT_WORKER_TEST_CONVERTER = OpenAPITestConverter(_CONTRACT_WORKER_REPO)


def _extract_contract_worker(feature_data: dict[str, Any]) -> tuple[str, dict[str, Any] | None]:
    """Extract a single OpenAPI contract in a worker process."""
    from specfact_cli.models.plan import Feature

    if (
        _CONTRACT_WORKER_EXTRACTOR is None
        or _CONTRACT_WORKER_TEST_CONVERTER is None
        or _CONTRACT_WORKER_REPO is None
        or _CONTRACT_WORKER_CONTRACTS_DIR is None
    ):
        raise RuntimeError("Contract extraction worker not initialized")

    feature = Feature(**feature_data)
    try:
        openapi_spec = _CONTRACT_WORKER_EXTRACTOR.extract_openapi_from_code(_CONTRACT_WORKER_REPO, feature)
        if openapi_spec.get("paths"):
            test_examples: dict[str, Any] = {}
            has_test_functions = any(story.test_functions for story in feature.stories) or (
                feature.source_tracking and feature.source_tracking.test_functions
            )

            if has_test_functions:
                all_test_functions: list[str] = []
                for story in feature.stories:
                    if story.test_functions:
                        all_test_functions.extend(story.test_functions)
                if feature.source_tracking and feature.source_tracking.test_functions:
                    all_test_functions.extend(feature.source_tracking.test_functions)
                if all_test_functions:
                    test_examples = _CONTRACT_WORKER_TEST_CONVERTER.extract_examples_from_tests(all_test_functions)

            if test_examples:
                openapi_spec = _CONTRACT_WORKER_EXTRACTOR.add_test_examples(openapi_spec, test_examples)

            contract_filename = f"{feature.key}.openapi.yaml"
            contract_path = _CONTRACT_WORKER_CONTRACTS_DIR / contract_filename
            _CONTRACT_WORKER_EXTRACTOR.save_openapi_contract(openapi_spec, contract_path)
            return (feature.key, openapi_spec)
    except KeyboardInterrupt:
        raise
    except Exception:
        return (feature.key, None)

    return (feature.key, None)


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
    from specfact_cli.migrations.plan_migrator import get_latest_schema_version

    # Create manifest with latest schema version
    manifest = BundleManifest(
        versions=BundleVersions(schema=get_latest_schema_version(), project="0.1.0"),
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


def _check_incremental_changes(
    bundle_dir: Path, repo: Path, enrichment: Path | None, force: bool = False
) -> dict[str, bool] | None:
    """Check for incremental changes and return what needs regeneration."""
    if force:
        console.print("[yellow]⚠ Force mode enabled - regenerating all artifacts[/yellow]\n")
        return None  # None means regenerate everything
    if not bundle_dir.exists():
        return None  # No bundle exists, regenerate everything
    # Note: enrichment doesn't force full regeneration - it only adds/updates features
    # Contracts should only be regenerated if source files changed, not just because enrichment was applied

    from specfact_cli.utils.incremental_check import check_incremental_changes

    try:
        progress_columns, progress_kwargs = get_progress_config()
        with Progress(
            *progress_columns,
            console=console,
            **progress_kwargs,
        ) as progress:
            # Load manifest first to get feature count for determinate progress
            manifest_path = bundle_dir / "bundle.manifest.yaml"
            num_features = 0
            total_ops = 100  # Default estimate for determinate progress

            if manifest_path.exists():
                try:
                    from specfact_cli.models.project import BundleManifest
                    from specfact_cli.utils.structured_io import load_structured_file

                    manifest_data = load_structured_file(manifest_path)
                    manifest = BundleManifest.model_validate(manifest_data)
                    num_features = len(manifest.features)

                    # Estimate total operations: manifest (1) + loading features (num_features) + file checks (num_features * ~2 avg files)
                    # Use a reasonable estimate for determinate progress
                    estimated_file_checks = num_features * 2 if num_features > 0 else 10
                    total_ops = max(1 + num_features + estimated_file_checks, 10)  # Minimum 10 for visibility
                except Exception:
                    # If manifest load fails, use default estimate
                    pass

            # Create task with estimated total for determinate progress bar
            task = progress.add_task("[cyan]Loading manifest and checking file changes...", total=total_ops)

            # Create progress callback to update the progress bar
            def update_progress(current: int, total: int, message: str) -> None:
                """Update progress bar with current status."""
                # Always update total when provided (we get better estimates as we progress)
                # The total from incremental_check may be more accurate than our initial estimate
                current_total = progress.tasks[task].total
                if current_total is None:
                    # No total set yet, use the provided one
                    progress.update(task, total=total)
                elif total != current_total:
                    # Total changed, update it (this handles both increases and decreases)
                    # We trust the incremental_check calculation as it has more accurate info
                    progress.update(task, total=total)
                # Always update completed and description
                progress.update(task, completed=current, description=f"[cyan]{message}[/cyan]")

            # Call check_incremental_changes with progress callback
            incremental_changes = check_incremental_changes(
                bundle_dir, repo, features=None, progress_callback=update_progress
            )

            # Update progress to completion
            task_info = progress.tasks[task]
            final_total = task_info.total if task_info.total and task_info.total > 0 else total_ops
            progress.update(
                task,
                completed=final_total,
                total=final_total,
                description="[green]✓[/green] Change check complete",
            )
            # Brief pause to show completion
            time.sleep(0.1)

        # If enrichment is provided, we need to apply it even if no source files changed
        # Mark bundle as needing regeneration to ensure enrichment is applied
        if enrichment and incremental_changes and not any(incremental_changes.values()):
            # Enrichment provided but no source changes - still need to apply enrichment
            incremental_changes["bundle"] = True  # Force bundle regeneration to apply enrichment
            console.print(f"[green]✓[/green] Project bundle already exists: {bundle_dir}")
            console.print("[dim]No source file changes detected, but enrichment will be applied[/dim]")
        elif not any(incremental_changes.values()):
            # No changes and no enrichment - can skip everything
            console.print(f"[green]✓[/green] Project bundle already exists: {bundle_dir}")
            console.print("[dim]No changes detected - all artifacts are up-to-date[/dim]")
            console.print("[dim]Skipping regeneration of relationships, contracts, graph, and enrichment context[/dim]")
            console.print(
                "[dim]Use --force to force regeneration, or modify source files to trigger incremental update[/dim]"
            )
            raise typer.Exit(0)

        changed_items = [key for key, value in incremental_changes.items() if value]
        if changed_items:
            console.print("[yellow]⚠[/yellow] Project bundle exists, but some artifacts need regeneration:")
            for item in changed_items:
                console.print(f"  [dim]- {item}[/dim]")
            console.print("[dim]Regenerating only changed artifacts...[/dim]\n")

        return incremental_changes
    except KeyboardInterrupt:
        raise
    except typer.Exit:
        raise
    except Exception as e:
        error_msg = str(e) if str(e) else f"{type(e).__name__}"
        if "bundle.manifest.yaml" in error_msg or "Cannot determine bundle format" in error_msg:
            console.print(
                "[yellow]⚠ Incomplete bundle directory detected (likely from a failed save) - will regenerate all artifacts[/yellow]\n"
            )
        else:
            console.print(
                f"[yellow]⚠ Existing bundle found but couldn't be loaded ({type(e).__name__}: {error_msg}) - will regenerate all artifacts[/yellow]\n"
            )
        return None


def _validate_existing_features(plan_bundle: PlanBundle, repo: Path) -> dict[str, Any]:
    """
    Validate existing features to check if they're still valid.

    Args:
        plan_bundle: Plan bundle with features to validate
        repo: Repository root path

    Returns:
        Dictionary with validation results:
        - 'valid_features': List of valid feature keys
        - 'orphaned_features': List of feature keys whose source files no longer exist
        - 'invalid_features': List of feature keys with validation issues
        - 'missing_files': Dict mapping feature_key -> list of missing file paths
        - 'total_checked': Total number of features checked
    """

    result: dict[str, Any] = {
        "valid_features": [],
        "orphaned_features": [],
        "invalid_features": [],
        "missing_files": {},
        "total_checked": len(plan_bundle.features),
    }

    for feature in plan_bundle.features:
        if not feature.source_tracking:
            # Feature has no source tracking - mark as potentially invalid
            result["invalid_features"].append(feature.key)
            continue

        missing_files: list[str] = []
        has_any_files = False

        # Check implementation files
        for impl_file in feature.source_tracking.implementation_files:
            file_path = repo / impl_file
            if file_path.exists():
                has_any_files = True
            else:
                missing_files.append(impl_file)

        # Check test files
        for test_file in feature.source_tracking.test_files:
            file_path = repo / test_file
            if file_path.exists():
                has_any_files = True
            else:
                missing_files.append(test_file)

        # Validate feature structure
        # Note: Features can legitimately have no stories if they're newly discovered
        # Only mark as invalid if there are actual structural problems (missing key/title)
        has_structure_issues = False
        if not feature.key or not feature.title:
            has_structure_issues = True
        # Don't mark features with no stories as invalid - they may be newly discovered
        # Stories will be added during analysis or enrichment

        # Classify feature
        if not has_any_files and missing_files:
            # All source files are missing - orphaned feature
            result["orphaned_features"].append(feature.key)
            result["missing_files"][feature.key] = missing_files
        elif missing_files:
            # Some files missing but not all - invalid but recoverable
            result["invalid_features"].append(feature.key)
            result["missing_files"][feature.key] = missing_files
        elif has_structure_issues:
            # Feature has actual structure issues (missing key/title)
            result["invalid_features"].append(feature.key)
        else:
            # Feature is valid (has source_tracking, files exist, and has key/title)
            # Note: Features without stories are still considered valid
            result["valid_features"].append(feature.key)

    return result


def _load_existing_bundle(bundle_dir: Path) -> PlanBundle | None:
    """Load existing project bundle and convert to PlanBundle."""
    from specfact_cli.models.plan import PlanBundle as PlanBundleModel
    from specfact_cli.utils.progress import load_bundle_with_progress

    try:
        existing_bundle = load_bundle_with_progress(bundle_dir, validate_hashes=False, console_instance=console)

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
        return plan_bundle
    except Exception as e:
        console.print(f"[yellow]⚠ Could not load existing bundle: {e}[/yellow]")
        console.print("[dim]Falling back to full codebase analysis...[/dim]\n")
        return None


def _analyze_codebase(
    repo: Path,
    entry_point: Path | None,
    bundle: str,
    confidence: float,
    key_format: str,
    routing_result: Any,
    incremental_callback: Any | None = None,
) -> PlanBundle:
    """Analyze codebase using AI agent or AST fallback."""
    from specfact_cli.agents.analyze_agent import AnalyzeAgent
    from specfact_cli.agents.registry import get_agent
    from specfact_cli.analyzers.code_analyzer import CodeAnalyzer

    if routing_result.execution_mode == "agent":
        console.print("[dim]Mode: CoPilot (AI-first import)[/dim]")
        agent = get_agent("import from-code")
        if agent and isinstance(agent, AnalyzeAgent):
            context = {
                "workspace": str(repo),
                "current_file": None,
                "selection": None,
            }
            _enhanced_context = agent.inject_context(context)
            console.print("\n[cyan]🤖 AI-powered import (semantic understanding)...[/cyan]")
            plan_bundle = agent.analyze_codebase(repo, confidence=confidence, plan_name=bundle)
            console.print("[green]✓[/green] AI import complete")
            return plan_bundle
        console.print("[yellow]⚠ Agent not available, falling back to AST-based import[/yellow]")

    # AST-based import (CI/CD mode or fallback)
    console.print("[dim]Mode: CI/CD (AST-based import)[/dim]")
    console.print(
        "\n[yellow]⏱️  Note: This analysis typically takes 2-5 minutes for large codebases (optimized for speed)[/yellow]"
    )

    # Phase 4.9: Create incremental callback for early feedback
    def on_incremental_update(features_count: int, themes: list[str]) -> None:
        """Callback for incremental results (Phase 4.9: Quick Start Optimization)."""
        # Feature count updates are shown in the progress bar description, not as separate lines
        # No intermediate messages needed - final summary provides all information

    # Create analyzer with incremental callback
    analyzer = CodeAnalyzer(
        repo,
        confidence_threshold=confidence,
        key_format=key_format,
        plan_name=bundle,
        entry_point=entry_point,
        incremental_callback=incremental_callback or on_incremental_update,
    )

    # Display plugin status
    plugin_status = analyzer.get_plugin_status()
    if plugin_status:
        from rich.table import Table

        console.print("\n[bold]Analysis Plugins:[/bold]")
        plugin_table = Table(show_header=True, header_style="bold cyan", box=None, padding=(0, 1))
        plugin_table.add_column("Plugin", style="cyan", width=25)
        plugin_table.add_column("Status", style="bold", width=12)
        plugin_table.add_column("Details", style="dim", width=50)

        for plugin in plugin_status:
            if plugin["enabled"] and plugin["used"]:
                status = "[green]✓ Enabled[/green]"
            elif plugin["enabled"] and not plugin["used"]:
                status = "[yellow]⚠ Enabled (not used)[/yellow]"
            else:
                status = "[dim]⊘ Disabled[/dim]"

            plugin_table.add_row(plugin["name"], status, plugin["reason"])

        console.print(plugin_table)
        console.print()

    if entry_point:
        console.print(f"[cyan]🔍 Analyzing codebase (scoped to {entry_point})...[/cyan]\n")
    else:
        console.print("[cyan]🔍 Analyzing codebase...[/cyan]\n")

    return analyzer.analyze()


def _update_source_tracking(plan_bundle: PlanBundle, repo: Path) -> None:
    """Update source tracking with file hashes (parallelized)."""
    import os
    from concurrent.futures import ThreadPoolExecutor, as_completed

    from specfact_cli.utils.source_scanner import SourceArtifactScanner

    console.print("\n[cyan]🔗 Linking source files to features...[/cyan]")
    scanner = SourceArtifactScanner(repo)
    scanner.link_to_specs(plan_bundle.features, repo)

    def update_file_hash(feature: Feature, file_path: Path) -> None:
        """Update hash for a single file (thread-safe)."""
        if file_path.exists() and feature.source_tracking is not None:
            feature.source_tracking.update_hash(file_path)

    hash_tasks: list[tuple[Feature, Path]] = []
    for feature in plan_bundle.features:
        if feature.source_tracking:
            for impl_file in feature.source_tracking.implementation_files:
                hash_tasks.append((feature, repo / impl_file))
            for test_file in feature.source_tracking.test_files:
                hash_tasks.append((feature, repo / test_file))

    if hash_tasks:
        import os

        from rich.progress import Progress

        from specfact_cli.utils.terminal import get_progress_config

        # In test mode, use sequential processing to avoid ThreadPoolExecutor deadlocks
        is_test_mode = os.environ.get("TEST_MODE") == "true"
        if is_test_mode:
            # Sequential processing in test mode - avoids ThreadPoolExecutor deadlocks
            import contextlib

            for feature, file_path in hash_tasks:
                with contextlib.suppress(Exception):
                    update_file_hash(feature, file_path)
        else:
            max_workers = max(1, min(multiprocessing.cpu_count() or 4, 16, len(hash_tasks)))
            progress_columns, progress_kwargs = get_progress_config()
            with Progress(
                *progress_columns,
                console=console,
                **progress_kwargs,
            ) as progress:
                hash_task = progress.add_task(
                    f"[cyan]Computing file hashes for {len(hash_tasks)} files...",
                    total=len(hash_tasks),
                )

                executor = ThreadPoolExecutor(max_workers=max_workers)
                interrupted = False
                completed_count = 0
                try:
                    future_to_task = {
                        executor.submit(update_file_hash, feature, file_path): (feature, file_path)
                        for feature, file_path in hash_tasks
                    }
                    try:
                        for future in as_completed(future_to_task):
                            try:
                                future.result()
                                completed_count += 1
                                progress.update(
                                    hash_task,
                                    completed=completed_count,
                                    description=f"[cyan]Computing file hashes... ({completed_count}/{len(hash_tasks)})",
                                )
                            except KeyboardInterrupt:
                                interrupted = True
                                for f in future_to_task:
                                    if not f.done():
                                        f.cancel()
                                break
                            except Exception:
                                completed_count += 1
                                progress.update(hash_task, completed=completed_count)
                    except KeyboardInterrupt:
                        interrupted = True
                        for f in future_to_task:
                            if not f.done():
                                f.cancel()
                    if interrupted:
                        raise KeyboardInterrupt
                except KeyboardInterrupt:
                    interrupted = True
                    executor.shutdown(wait=False, cancel_futures=True)
                    raise
                finally:
                    if not interrupted:
                        progress.update(
                            hash_task,
                            completed=len(hash_tasks),
                            description=f"[green]✓[/green] Computed hashes for {len(hash_tasks)} files",
                        )
                        progress.remove_task(hash_task)
                        executor.shutdown(wait=True)
                    else:
                        executor.shutdown(wait=False)

    # Update sync timestamps (fast operation, no progress needed)
    for feature in plan_bundle.features:
        if feature.source_tracking:
            feature.source_tracking.update_sync_timestamp()

    console.print("[green]✓[/green] Source tracking complete")


def _extract_relationships_and_graph(
    repo: Path,
    entry_point: Path | None,
    bundle_dir: Path,
    incremental_changes: dict[str, bool] | None,
    plan_bundle: PlanBundle | None,
    should_regenerate_relationships: bool,
    should_regenerate_graph: bool,
    include_tests: bool = False,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Extract relationships and graph dependencies."""
    relationships: dict[str, Any] = {}
    graph_summary: dict[str, Any] | None = None

    if not (should_regenerate_relationships or should_regenerate_graph):
        console.print("\n[dim]⏭ Skipping relationships and graph analysis (no changes detected)[/dim]")
        enrichment_context_path = bundle_dir / "enrichment_context.md"
        if enrichment_context_path.exists():
            relationships = {"imports": {}, "interfaces": {}, "routes": {}}
        return relationships, graph_summary

    console.print("\n[cyan]🔍 Enhanced analysis: Extracting relationships, contracts, and graph dependencies...[/cyan]")
    from rich.progress import Progress, SpinnerColumn, TextColumn

    from specfact_cli.analyzers.graph_analyzer import GraphAnalyzer
    from specfact_cli.analyzers.relationship_mapper import RelationshipMapper
    from specfact_cli.utils.optional_deps import check_cli_tool_available
    from specfact_cli.utils.terminal import get_progress_config

    # Show spinner while checking pyan3 and collecting file hashes
    _progress_columns, progress_kwargs = get_progress_config()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        **progress_kwargs,
    ) as setup_progress:
        setup_task = setup_progress.add_task("[cyan]Preparing enhanced analysis...", total=None)

        pyan3_available, _ = check_cli_tool_available("pyan3")
        if not pyan3_available:
            console.print(
                "[dim]💡 Note: Enhanced analysis tool pyan3 is not available (call graph analysis will be skipped)[/dim]"
            )
            console.print("[dim]   Install with: pip install pyan3[/dim]")

        # Pre-compute file hashes for caching (reuse from source tracking if available)
        setup_progress.update(setup_task, description="[cyan]Collecting file hashes for caching...")
        file_hashes_cache: dict[str, str] = {}
        if plan_bundle:
            # Collect file hashes from source tracking
            for feature in plan_bundle.features:
                if feature.source_tracking:
                    file_hashes_cache.update(feature.source_tracking.file_hashes)

        relationship_mapper = RelationshipMapper(repo, file_hashes_cache=file_hashes_cache)

        # Discover and filter Python files with progress
        changed_files: set[Path] = set()
        if incremental_changes and plan_bundle:
            setup_progress.update(setup_task, description="[cyan]Checking for changed files...")
            from specfact_cli.utils.incremental_check import get_changed_files

            # get_changed_files iterates through all features and checks file hashes
            # This can be slow for large bundles - show progress
            changed_files_dict = get_changed_files(bundle_dir, repo, list(plan_bundle.features))
            setup_progress.update(setup_task, description="[cyan]Collecting changed file paths...")
            for feature_changes in changed_files_dict.values():
                for file_path_str in feature_changes:
                    clean_path = file_path_str.replace(" (deleted)", "")
                    file_path = repo / clean_path
                    if file_path.exists():
                        changed_files.add(file_path)

        if changed_files:
            python_files = list(changed_files)
            setup_progress.update(setup_task, description=f"[green]✓[/green] Found {len(python_files)} changed file(s)")
        else:
            setup_progress.update(setup_task, description="[cyan]Discovering Python files...")
            # This can be slow for large codebases - show progress
            python_files = list(repo.rglob("*.py"))
            setup_progress.update(setup_task, description=f"[cyan]Filtering {len(python_files)} files...")

            if entry_point:
                python_files = [f for f in python_files if entry_point in f.parts]

            # Filter files based on --include-tests/--exclude-tests flag
            # Default: Exclude test files (they're validation artifacts, not specifications)
            # --include-tests: Include test files in dependency graph (only if needed)
            # Rationale for excluding tests by default:
            # - Test files are consumers of production code (not producers)
            # - Test files import production code, but production code doesn't import tests
            # - Interfaces and routes are defined in production code, not tests
            # - Dependency graph flows from production code, so skipping tests has minimal impact
            # - Test files are never extracted as features (they validate code, they don't define it)
            if not include_tests:
                # Exclude test files when --exclude-tests is specified (default)
                # Test files are validation artifacts, not specifications
                python_files = [
                    f
                    for f in python_files
                    if not any(
                        skip in str(f)
                        for skip in [
                            "/test_",
                            "/tests/",
                            "/test/",  # Handle singular "test/" directory (e.g., SQLAlchemy)
                            "/vendor/",
                            "/.venv/",
                            "/venv/",
                            "/node_modules/",
                            "/__pycache__/",
                        ]
                    )
                    and not f.name.startswith("test_")  # Exclude test_*.py files
                    and not f.name.endswith("_test.py")  # Exclude *_test.py files
                ]
            else:
                # Default: Include test files, but still filter vendor/venv files
                python_files = [
                    f
                    for f in python_files
                    if not any(
                        skip in str(f) for skip in ["/vendor/", "/.venv/", "/venv/", "/node_modules/", "/__pycache__/"]
                    )
                ]
            setup_progress.update(
                setup_task, description=f"[green]✓[/green] Ready to analyze {len(python_files)} files"
            )

        setup_progress.remove_task(setup_task)

    if changed_files:
        console.print(f"[dim]Analyzing {len(python_files)} changed file(s) for relationships...[/dim]")
    else:
        console.print(f"[dim]Analyzing {len(python_files)} file(s) for relationships...[/dim]")

    # Analyze relationships in parallel with progress reporting
    progress_columns, progress_kwargs = get_progress_config()
    with Progress(
        *progress_columns,
        console=console,
        **progress_kwargs,
    ) as progress:
        import time

        # Step 1: Analyze relationships
        relationships_task = progress.add_task(
            f"[cyan]Analyzing relationships in {len(python_files)} files...",
            total=len(python_files),
        )

        def update_relationships_progress(completed: int, total: int) -> None:
            """Update progress for relationship analysis."""
            progress.update(
                relationships_task,
                completed=completed,
                description=f"[cyan]Analyzing relationships... ({completed}/{total} files)",
            )

        relationships = relationship_mapper.analyze_files(python_files, progress_callback=update_relationships_progress)
        progress.update(
            relationships_task,
            completed=len(python_files),
            total=len(python_files),
            description=f"[green]✓[/green] Relationship analysis complete: {len(relationships['imports'])} files mapped",
        )
        # Keep final progress bar visible instead of removing it
        time.sleep(0.1)  # Brief pause to show completion

    # Graph analysis is optional and can be slow - only run if explicitly needed
    # Skip by default for faster imports (can be enabled with --with-graph flag in future)
    if should_regenerate_graph and pyan3_available:
        with Progress(
            *progress_columns,
            console=console,
            **progress_kwargs,
        ) as progress:
            graph_task = progress.add_task(
                f"[cyan]Building dependency graph from {len(python_files)} files...",
                total=len(python_files) * 2,  # Two phases: AST imports + call graphs
            )

            def update_graph_progress(completed: int, total: int) -> None:
                """Update progress for graph building."""
                progress.update(
                    graph_task,
                    completed=completed,
                    description=f"[cyan]Building dependency graph... ({completed}/{total})",
                )

            graph_analyzer = GraphAnalyzer(repo, file_hashes_cache=file_hashes_cache)
            graph_analyzer.build_dependency_graph(python_files, progress_callback=update_graph_progress)
            graph_summary = graph_analyzer.get_graph_summary()
            if graph_summary:
                progress.update(
                    graph_task,
                    completed=len(python_files) * 2,
                    total=len(python_files) * 2,
                    description=f"[green]✓[/green] Dependency graph complete: {graph_summary.get('nodes', 0)} modules, {graph_summary.get('edges', 0)} dependencies",
                )
                # Keep final progress bar visible instead of removing it
                time.sleep(0.1)  # Brief pause to show completion
            relationships["dependency_graph"] = graph_summary
            relationships["call_graphs"] = graph_analyzer.call_graphs
    elif should_regenerate_graph and not pyan3_available:
        console.print("[dim]⏭ Skipping graph analysis (pyan3 not available)[/dim]")

    return relationships, graph_summary


def _extract_contracts(
    repo: Path,
    bundle_dir: Path,
    plan_bundle: PlanBundle,
    should_regenerate_contracts: bool,
    record_event: Any,
    force: bool = False,
) -> dict[str, dict[str, Any]]:
    """Extract OpenAPI contracts from features."""
    import os
    from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed

    from specfact_cli.generators.openapi_extractor import OpenAPIExtractor
    from specfact_cli.generators.test_to_openapi import OpenAPITestConverter

    contracts_generated = 0
    contracts_dir = bundle_dir / "contracts"
    contracts_dir.mkdir(parents=True, exist_ok=True)
    contracts_data: dict[str, dict[str, Any]] = {}

    # Load existing contracts if not regenerating (parallelized)
    if not should_regenerate_contracts:
        console.print("\n[dim]⏭ Skipping contract extraction (no changes detected)[/dim]")

        def load_contract(feature: Feature) -> tuple[str, dict[str, Any] | None]:
            """Load contract for a single feature (thread-safe)."""
            if feature.contract:
                contract_path = bundle_dir / feature.contract
                if contract_path.exists():
                    try:
                        import yaml

                        contract_data = yaml.safe_load(contract_path.read_text())
                        return (feature.key, contract_data)
                    except KeyboardInterrupt:
                        raise
                    except Exception:
                        pass
            return (feature.key, None)

        features_with_contracts = [f for f in plan_bundle.features if f.contract]
        if features_with_contracts:
            import os
            from concurrent.futures import ThreadPoolExecutor, as_completed

            from rich.progress import Progress

            from specfact_cli.utils.terminal import get_progress_config

            # In test mode, use sequential processing to avoid ThreadPoolExecutor deadlocks
            is_test_mode = os.environ.get("TEST_MODE") == "true"
            existing_contracts_count = 0

            progress_columns, progress_kwargs = get_progress_config()
            with Progress(
                *progress_columns,
                console=console,
                **progress_kwargs,
            ) as progress:
                load_task = progress.add_task(
                    f"[cyan]Loading {len(features_with_contracts)} existing contract(s)...",
                    total=len(features_with_contracts),
                )

                if is_test_mode:
                    # Sequential processing in test mode - avoids ThreadPoolExecutor deadlocks
                    for idx, feature in enumerate(features_with_contracts):
                        try:
                            feature_key, contract_data = load_contract(feature)
                            if contract_data:
                                contracts_data[feature_key] = contract_data
                                existing_contracts_count += 1
                        except Exception:
                            pass
                        progress.update(load_task, completed=idx + 1)
                else:
                    max_workers = max(1, min(multiprocessing.cpu_count() or 4, 16, len(features_with_contracts)))
                    executor = ThreadPoolExecutor(max_workers=max_workers)
                    interrupted = False
                    completed_count = 0
                    try:
                        future_to_feature = {
                            executor.submit(load_contract, feature): feature for feature in features_with_contracts
                        }
                        try:
                            for future in as_completed(future_to_feature):
                                try:
                                    feature_key, contract_data = future.result()
                                    completed_count += 1
                                    progress.update(load_task, completed=completed_count)
                                    if contract_data:
                                        contracts_data[feature_key] = contract_data
                                        existing_contracts_count += 1
                                except KeyboardInterrupt:
                                    interrupted = True
                                    for f in future_to_feature:
                                        if not f.done():
                                            f.cancel()
                                    break
                                except Exception:
                                    completed_count += 1
                                    progress.update(load_task, completed=completed_count)
                        except KeyboardInterrupt:
                            interrupted = True
                            for f in future_to_feature:
                                if not f.done():
                                    f.cancel()
                        if interrupted:
                            raise KeyboardInterrupt
                    except KeyboardInterrupt:
                        interrupted = True
                        executor.shutdown(wait=False, cancel_futures=True)
                        raise
                    finally:
                        if not interrupted:
                            progress.update(
                                load_task,
                                completed=len(features_with_contracts),
                                description=f"[green]✓[/green] Loaded {existing_contracts_count} contract(s)",
                            )
                            executor.shutdown(wait=True)
                        else:
                            executor.shutdown(wait=False)

                if existing_contracts_count == 0:
                    progress.remove_task(load_task)

            if existing_contracts_count > 0:
                console.print(f"[green]✓[/green] Loaded {existing_contracts_count} existing contract(s) from bundle")

    # Extract contracts if needed
    if should_regenerate_contracts:
        # When force=True, skip hash checking and process all features with source files
        if force:
            # Force mode: process all features with implementation files
            features_with_files = [
                f for f in plan_bundle.features if f.source_tracking and f.source_tracking.implementation_files
            ]
        else:
            # Filter features that need contract regeneration (check file hashes)
            # Pre-compute all file hashes in parallel to avoid redundant I/O
            import os
            from concurrent.futures import ThreadPoolExecutor, as_completed

            # Collect all unique files that need hash checking
            files_to_check: set[Path] = set()
            feature_to_files: dict[str, list[Path]] = {}  # Use feature key (str) instead of Feature object
            feature_objects: dict[str, Feature] = {}  # Keep reference to Feature objects

            for f in plan_bundle.features:
                if f.source_tracking and f.source_tracking.implementation_files:
                    feature_files: list[Path] = []
                    for impl_file in f.source_tracking.implementation_files:
                        file_path = repo / impl_file
                        if file_path.exists():
                            files_to_check.add(file_path)
                            feature_files.append(file_path)
                    if feature_files:
                        feature_to_files[f.key] = feature_files
                        feature_objects[f.key] = f

            # Pre-compute all file hashes in parallel (batch operation)
            current_hashes: dict[Path, str] = {}
            if files_to_check:
                is_test_mode = os.environ.get("TEST_MODE") == "true"

                def compute_file_hash(file_path: Path) -> tuple[Path, str | None]:
                    """Compute hash for a single file (thread-safe)."""
                    try:
                        import hashlib

                        return (file_path, hashlib.sha256(file_path.read_bytes()).hexdigest())
                    except Exception:
                        return (file_path, None)

                if is_test_mode:
                    # Sequential in test mode
                    for file_path in files_to_check:
                        _, hash_value = compute_file_hash(file_path)
                        if hash_value:
                            current_hashes[file_path] = hash_value
                else:
                    # Parallel in production mode
                    max_workers = max(1, min(multiprocessing.cpu_count() or 4, 16, len(files_to_check)))
                    with ThreadPoolExecutor(max_workers=max_workers) as executor:
                        futures = {executor.submit(compute_file_hash, fp): fp for fp in files_to_check}
                        for future in as_completed(futures):
                            try:
                                file_path, hash_value = future.result()
                                if hash_value:
                                    current_hashes[file_path] = hash_value
                            except Exception:
                                pass

            # Now check features using pre-computed hashes (no file I/O)
            features_with_files = []
            for feature_key, feature_files in feature_to_files.items():
                f = feature_objects[feature_key]
                # Check if contract needs regeneration (file changed or contract missing)
                needs_regeneration = False
                if not f.contract:
                    needs_regeneration = True
                else:
                    # Check if any source file changed
                    contract_path = bundle_dir / f.contract
                    if not contract_path.exists():
                        needs_regeneration = True
                    else:
                        # Check if any implementation file changed using pre-computed hashes
                        if f.source_tracking:
                            for file_path in feature_files:
                                if file_path in current_hashes:
                                    stored_hash = f.source_tracking.file_hashes.get(str(file_path))
                                    if stored_hash != current_hashes[file_path]:
                                        needs_regeneration = True
                                        break
                            else:
                                # File exists but hash computation failed, assume changed
                                needs_regeneration = True
                                break
                if needs_regeneration:
                    features_with_files.append(f)
    else:
        features_with_files: list[Feature] = []

    if features_with_files and should_regenerate_contracts:
        import os

        # In test mode, use sequential processing to avoid ThreadPoolExecutor deadlocks
        is_test_mode = os.environ.get("TEST_MODE") == "true"
        pool_mode = os.environ.get("SPECFACT_CONTRACT_POOL", "process").lower()
        use_process_pool = not is_test_mode and pool_mode != "thread" and len(features_with_files) > 1
        # Define max_workers for non-test mode (always defined to satisfy type checker)
        max_workers = 1
        if is_test_mode:
            console.print(
                f"[cyan]📋 Extracting contracts from {len(features_with_files)} features (sequential mode)...[/cyan]"
            )
        else:
            max_workers = max(1, min(multiprocessing.cpu_count() or 4, 16, len(features_with_files)))
            pool_label = "process" if use_process_pool else "thread"
            console.print(
                f"[cyan]📋 Extracting contracts from {len(features_with_files)} features (using {max_workers} {pool_label} worker(s))...[/cyan]"
            )

        from rich.progress import Progress

        from specfact_cli.utils.terminal import get_progress_config

        progress_columns, progress_kwargs = get_progress_config()
        with Progress(
            *progress_columns,
            console=console,
            **progress_kwargs,
        ) as progress:
            task = progress.add_task("[cyan]Extracting contracts...", total=len(features_with_files))
            if use_process_pool:
                feature_lookup: dict[str, Feature] = {f.key: f for f in features_with_files}
                executor = ProcessPoolExecutor(
                    max_workers=max_workers,
                    initializer=_init_contract_worker,
                    initargs=(str(repo), str(contracts_dir)),
                )
                interrupted = False
                try:
                    future_to_feature_key = {
                        executor.submit(_extract_contract_worker, f.model_dump()): f.key for f in features_with_files
                    }
                    completed_count = 0
                    total_features = len(features_with_files)
                    pending_count = total_features
                    try:
                        for future in as_completed(future_to_feature_key):
                            try:
                                feature_key, openapi_spec = future.result()
                                completed_count += 1
                                pending_count = total_features - completed_count
                                feature_display = feature_key[:50] + "..." if len(feature_key) > 50 else feature_key

                                if openapi_spec:
                                    progress.update(
                                        task,
                                        completed=completed_count,
                                        description=f"[cyan]Extracted contract from {feature_display}... ({completed_count}/{total_features}, {pending_count} pending)",
                                    )
                                    feature = feature_lookup.get(feature_key)
                                    if feature:
                                        contract_ref = f"contracts/{feature_key}.openapi.yaml"
                                        feature.contract = contract_ref
                                        contracts_data[feature_key] = openapi_spec
                                        contracts_generated += 1
                                else:
                                    progress.update(
                                        task,
                                        completed=completed_count,
                                        description=f"[dim]No contract for {feature_display}... ({completed_count}/{total_features}, {pending_count} pending)[/dim]",
                                    )
                            except KeyboardInterrupt:
                                interrupted = True
                                for f in future_to_feature_key:
                                    if not f.done():
                                        f.cancel()
                                break
                            except Exception as e:
                                completed_count += 1
                                pending_count = total_features - completed_count
                                feature_key_for_display = future_to_feature_key.get(future, "unknown")
                                feature_display = (
                                    feature_key_for_display[:50] + "..."
                                    if len(feature_key_for_display) > 50
                                    else feature_key_for_display
                                )
                                progress.update(
                                    task,
                                    completed=completed_count,
                                    description=f"[dim]⚠ Failed: {feature_display}... ({completed_count}/{total_features}, {pending_count} pending)[/dim]",
                                )
                                console.print(
                                    f"[dim]⚠ Warning: Failed to process feature {feature_key_for_display}: {e}[/dim]"
                                )
                    except KeyboardInterrupt:
                        interrupted = True
                        for f in future_to_feature_key:
                            if not f.done():
                                f.cancel()
                    if interrupted:
                        raise KeyboardInterrupt
                except KeyboardInterrupt:
                    interrupted = True
                    executor.shutdown(wait=False, cancel_futures=True)
                    raise
                finally:
                    if not interrupted:
                        executor.shutdown(wait=True)
                        progress.update(
                            task,
                            completed=len(features_with_files),
                            total=len(features_with_files),
                            description=f"[green]✓[/green] Contract extraction complete: {contracts_generated} contract(s) generated from {len(features_with_files)} feature(s)",
                        )
                        time.sleep(0.1)
                    else:
                        executor.shutdown(wait=False)
            else:
                openapi_extractor = OpenAPIExtractor(repo)
                test_converter = OpenAPITestConverter(repo)

                def process_feature(feature: Feature) -> tuple[str, dict[str, Any] | None]:
                    """Process a single feature and return (feature_key, openapi_spec or None)."""
                    try:
                        openapi_spec = openapi_extractor.extract_openapi_from_code(repo, feature)
                        if openapi_spec.get("paths"):
                            test_examples: dict[str, Any] = {}
                            has_test_functions = any(story.test_functions for story in feature.stories) or (
                                feature.source_tracking and feature.source_tracking.test_functions
                            )

                            if has_test_functions:
                                all_test_functions: list[str] = []
                                for story in feature.stories:
                                    if story.test_functions:
                                        all_test_functions.extend(story.test_functions)
                                if feature.source_tracking and feature.source_tracking.test_functions:
                                    all_test_functions.extend(feature.source_tracking.test_functions)
                                if all_test_functions:
                                    test_examples = test_converter.extract_examples_from_tests(all_test_functions)

                            if test_examples:
                                openapi_spec = openapi_extractor.add_test_examples(openapi_spec, test_examples)

                            contract_filename = f"{feature.key}.openapi.yaml"
                            contract_path = contracts_dir / contract_filename
                            openapi_extractor.save_openapi_contract(openapi_spec, contract_path)
                            return (feature.key, openapi_spec)
                    except KeyboardInterrupt:
                        raise
                    except Exception:
                        pass
                    return (feature.key, None)

                if is_test_mode:
                    # Sequential processing in test mode - avoids ThreadPoolExecutor deadlocks
                    completed_count = 0
                    for idx, feature in enumerate(features_with_files, 1):
                        try:
                            feature_display = feature.key[:60] + "..." if len(feature.key) > 60 else feature.key
                            progress.update(
                                task,
                                completed=completed_count,
                                description=f"[cyan]Extracting contract from {feature_display}... ({idx}/{len(features_with_files)})",
                            )
                            feature_key, openapi_spec = process_feature(feature)
                            completed_count += 1
                            progress.update(
                                task,
                                completed=completed_count,
                                description=f"[cyan]Extracted contract from {feature_display} ({completed_count}/{len(features_with_files)})",
                            )
                            if openapi_spec:
                                contract_ref = f"contracts/{feature_key}.openapi.yaml"
                                feature.contract = contract_ref
                                contracts_data[feature_key] = openapi_spec
                                contracts_generated += 1
                        except Exception as e:
                            completed_count += 1
                            progress.update(
                                task,
                                completed=completed_count,
                                description=f"[dim]⚠ Failed: {feature.key[:50]}... ({completed_count}/{len(features_with_files)})[/dim]",
                            )
                            console.print(f"[dim]⚠ Warning: Failed to process feature {feature.key}: {e}[/dim]")
                    progress.update(
                        task,
                        completed=len(features_with_files),
                        total=len(features_with_files),
                        description=f"[green]✓[/green] Contract extraction complete: {contracts_generated} contract(s) generated from {len(features_with_files)} feature(s)",
                    )
                    time.sleep(0.1)
                else:
                    feature_lookup_thread: dict[str, Feature] = {f.key: f for f in features_with_files}
                    executor = ThreadPoolExecutor(max_workers=max_workers)
                    interrupted = False
                    try:
                        future_to_feature = {executor.submit(process_feature, f): f for f in features_with_files}
                        completed_count = 0
                        total_features = len(features_with_files)
                        pending_count = total_features
                        try:
                            for future in as_completed(future_to_feature):
                                try:
                                    feature_key, openapi_spec = future.result()
                                    completed_count += 1
                                    pending_count = total_features - completed_count
                                    feature = feature_lookup_thread.get(feature_key)
                                    feature_display = feature_key[:50] + "..." if len(feature_key) > 50 else feature_key

                                    if openapi_spec:
                                        progress.update(
                                            task,
                                            completed=completed_count,
                                            description=f"[cyan]Extracted contract from {feature_display}... ({completed_count}/{total_features}, {pending_count} pending)",
                                        )
                                        if feature:
                                            contract_ref = f"contracts/{feature_key}.openapi.yaml"
                                            feature.contract = contract_ref
                                            contracts_data[feature_key] = openapi_spec
                                            contracts_generated += 1
                                    else:
                                        progress.update(
                                            task,
                                            completed=completed_count,
                                            description=f"[dim]No contract for {feature_display}... ({completed_count}/{total_features}, {pending_count} pending)[/dim]",
                                        )
                                except KeyboardInterrupt:
                                    interrupted = True
                                    for f in future_to_feature:
                                        if not f.done():
                                            f.cancel()
                                    break
                                except Exception as e:
                                    completed_count += 1
                                    pending_count = total_features - completed_count
                                    feature_for_error = future_to_feature.get(future)
                                    feature_key_for_display = feature_for_error.key if feature_for_error else "unknown"
                                    feature_display = (
                                        feature_key_for_display[:50] + "..."
                                        if len(feature_key_for_display) > 50
                                        else feature_key_for_display
                                    )
                                    progress.update(
                                        task,
                                        completed=completed_count,
                                        description=f"[dim]⚠ Failed: {feature_display}... ({completed_count}/{total_features}, {pending_count} pending)[/dim]",
                                    )
                                    console.print(
                                        f"[dim]⚠ Warning: Failed to process feature {feature_key_for_display}: {e}[/dim]"
                                    )
                        except KeyboardInterrupt:
                            interrupted = True
                            for f in future_to_feature:
                                if not f.done():
                                    f.cancel()
                        if interrupted:
                            raise KeyboardInterrupt
                    except KeyboardInterrupt:
                        interrupted = True
                        executor.shutdown(wait=False, cancel_futures=True)
                        raise
                    finally:
                        if not interrupted:
                            executor.shutdown(wait=True)
                            progress.update(
                                task,
                                completed=len(features_with_files),
                                total=len(features_with_files),
                                description=f"[green]✓[/green] Contract extraction complete: {contracts_generated} contract(s) generated from {len(features_with_files)} feature(s)",
                            )
                            time.sleep(0.1)
                        else:
                            executor.shutdown(wait=False)

    elif should_regenerate_contracts:
        console.print("[dim]No features with implementation files found for contract extraction[/dim]")

    # Report contract status
    if should_regenerate_contracts:
        if contracts_generated > 0:
            console.print(f"[green]✓[/green] Generated {contracts_generated} contract scaffolds")
        elif not features_with_files:
            console.print("[dim]No API contracts detected in codebase[/dim]")

    return contracts_data


def _build_enrichment_context(
    bundle_dir: Path,
    repo: Path,
    plan_bundle: PlanBundle,
    relationships: dict[str, Any],
    contracts_data: dict[str, dict[str, Any]],
    should_regenerate_enrichment: bool,
    record_event: Any,
) -> Path:
    """Build enrichment context for LLM."""
    import hashlib

    context_path = bundle_dir / "enrichment_context.md"

    # Check if context needs regeneration using file hash
    needs_regeneration = should_regenerate_enrichment
    if not needs_regeneration and context_path.exists():
        # Check if any source data changed (relationships, contracts, features)
        # This can be slow for large bundles - show progress
        from rich.progress import SpinnerColumn, TextColumn

        from specfact_cli.utils.terminal import get_progress_config

        _progress_columns, progress_kwargs = get_progress_config()
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            **progress_kwargs,
        ) as check_progress:
            check_task = check_progress.add_task("[cyan]Checking if enrichment context changed...", total=None)
            try:
                existing_hash = hashlib.sha256(context_path.read_bytes()).hexdigest()
                # Build temporary context to compare hash
                from specfact_cli.utils.enrichment_context import build_enrichment_context

                check_progress.update(check_task, description="[cyan]Building temporary context for comparison...")
                temp_context = build_enrichment_context(
                    plan_bundle, relationships=relationships, contracts=contracts_data
                )
                temp_md = temp_context.to_markdown()
                new_hash = hashlib.sha256(temp_md.encode("utf-8")).hexdigest()
                if existing_hash != new_hash:
                    needs_regeneration = True
            except Exception:
                # If we can't check, regenerate to be safe
                needs_regeneration = True

    if needs_regeneration:
        console.print("\n[cyan]📊 Building enrichment context...[/cyan]")
        # Building context can be slow for large bundles - show progress
        from rich.progress import SpinnerColumn, TextColumn

        from specfact_cli.utils.enrichment_context import build_enrichment_context
        from specfact_cli.utils.terminal import get_progress_config

        _progress_columns, progress_kwargs = get_progress_config()
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            **progress_kwargs,
        ) as build_progress:
            build_task = build_progress.add_task(
                f"[cyan]Building context from {len(plan_bundle.features)} features...", total=None
            )
            enrichment_context = build_enrichment_context(
                plan_bundle, relationships=relationships, contracts=contracts_data
            )
            build_progress.update(build_task, description="[cyan]Converting to markdown...")
            _enrichment_context_md = enrichment_context.to_markdown()
            build_progress.update(build_task, description="[cyan]Writing to file...")
            context_path.write_text(_enrichment_context_md, encoding="utf-8")
        try:
            rel_path = context_path.relative_to(repo.resolve())
            console.print(f"[green]✓[/green] Enrichment context saved to: {rel_path}")
        except ValueError:
            console.print(f"[green]✓[/green] Enrichment context saved to: {context_path}")
    else:
        console.print("\n[dim]⏭ Skipping enrichment context generation (no changes detected)[/dim]")
        _ = context_path.read_text(encoding="utf-8") if context_path.exists() else ""

    record_event(
        {
            "enrichment_context_available": True,
            "relationships_files": len(relationships.get("imports", {})),
            "contracts_count": len(contracts_data),
        }
    )
    return context_path


def _apply_enrichment(
    enrichment: Path,
    plan_bundle: PlanBundle,
    record_event: Any,
) -> PlanBundle:
    """Apply enrichment report to plan bundle."""
    if not enrichment.exists():
        console.print(f"[bold red]✗ Enrichment report not found: {enrichment}[/bold red]")
        raise typer.Exit(1)

    console.print(f"\n[cyan]📝 Applying enrichment from: {enrichment}[/cyan]")
    from specfact_cli.utils.enrichment_parser import EnrichmentParser, apply_enrichment

    try:
        parser = EnrichmentParser()
        enrichment_report = parser.parse(enrichment)
        plan_bundle = apply_enrichment(plan_bundle, enrichment_report)

        if enrichment_report.missing_features:
            console.print(f"[green]✓[/green] Added {len(enrichment_report.missing_features)} missing features")
        if enrichment_report.confidence_adjustments:
            console.print(
                f"[green]✓[/green] Adjusted confidence for {len(enrichment_report.confidence_adjustments)} features"
            )
        if enrichment_report.business_context.get("priorities") or enrichment_report.business_context.get(
            "constraints"
        ):
            console.print("[green]✓[/green] Applied business context")

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

    return plan_bundle


def _save_bundle_if_needed(
    plan_bundle: PlanBundle,
    bundle: str,
    bundle_dir: Path,
    incremental_changes: dict[str, bool] | None,
    should_regenerate_relationships: bool,
    should_regenerate_graph: bool,
    should_regenerate_contracts: bool,
    should_regenerate_enrichment: bool,
) -> None:
    """Save project bundle only if something changed."""
    any_artifact_changed = (
        should_regenerate_relationships
        or should_regenerate_graph
        or should_regenerate_contracts
        or should_regenerate_enrichment
    )
    should_regenerate_bundle = (
        incremental_changes is None or any_artifact_changed or incremental_changes.get("bundle", False)
    )

    if should_regenerate_bundle:
        console.print("\n[cyan]💾 Compiling and saving project bundle...[/cyan]")
        project_bundle = _convert_plan_bundle_to_project_bundle(plan_bundle, bundle)
        save_bundle_with_progress(project_bundle, bundle_dir, atomic=True, console_instance=console)
    else:
        console.print("\n[dim]⏭ Skipping bundle save (no changes detected)[/dim]")


def _validate_bundle_contracts(bundle_dir: Path, plan_bundle: PlanBundle) -> tuple[int, int]:
    """
    Validate OpenAPI/AsyncAPI contracts in bundle with Specmatic if available.

    Args:
        bundle_dir: Path to bundle directory
        plan_bundle: Plan bundle containing features with contract references

    Returns:
        Tuple of (validated_count, failed_count)
    """
    import asyncio

    from specfact_cli.integrations.specmatic import check_specmatic_available, validate_spec_with_specmatic

    # Skip validation in test mode to avoid long-running subprocess calls
    if os.environ.get("TEST_MODE") == "true":
        return 0, 0

    is_available, _error_msg = check_specmatic_available()
    if not is_available:
        return 0, 0

    validated_count = 0
    failed_count = 0
    contract_files = []

    # Collect contract files from features
    # PlanBundle.features is a list, not a dict
    features_iter = plan_bundle.features.values() if isinstance(plan_bundle.features, dict) else plan_bundle.features
    for feature in features_iter:
        if feature.contract:
            contract_path = bundle_dir / feature.contract
            if contract_path.exists():
                contract_files.append((contract_path, feature.key))

    if not contract_files:
        return 0, 0

    # Limit validation to first 5 contracts to avoid long delays
    contracts_to_validate = contract_files[:5]

    console.print(f"\n[cyan]🔍 Validating {len(contracts_to_validate)} contract(s) in bundle with Specmatic...[/cyan]")

    progress_columns, progress_kwargs = get_progress_config()
    with Progress(
        *progress_columns,
        console=console,
        **progress_kwargs,
    ) as progress:
        validation_task = progress.add_task(
            "[cyan]Validating contracts...",
            total=len(contracts_to_validate),
        )

        for idx, (contract_path, _feature_key) in enumerate(contracts_to_validate):
            progress.update(
                validation_task,
                completed=idx,
                description=f"[cyan]Validating {contract_path.name}...",
            )
            try:
                result = asyncio.run(validate_spec_with_specmatic(contract_path))
                if result.is_valid:
                    validated_count += 1
                else:
                    failed_count += 1
                    if result.errors:
                        console.print(f"  [yellow]⚠[/yellow] {contract_path.name} has validation issues")
                        for error in result.errors[:2]:
                            console.print(f"    - {error}")
            except Exception as e:
                failed_count += 1
                console.print(f"  [yellow]⚠[/yellow] Validation error for {contract_path.name}: {e!s}")

        progress.update(
            validation_task,
            completed=len(contracts_to_validate),
            description=f"[green]✓[/green] Validated {validated_count} contract(s)",
        )
        progress.remove_task(validation_task)

    if len(contract_files) > 5:
        console.print(
            f"[dim]... and {len(contract_files) - 5} more contract(s) (run 'specfact spec validate' to validate all)[/dim]"
        )

    return validated_count, failed_count


def _validate_api_specs(repo: Path, bundle_dir: Path | None = None, plan_bundle: PlanBundle | None = None) -> None:
    """
    Validate OpenAPI/AsyncAPI specs with Specmatic if available.

    Validates both repo-level spec files and bundle contracts if provided.

    Args:
        repo: Repository path
        bundle_dir: Optional bundle directory path
        plan_bundle: Optional plan bundle for contract validation
    """
    import asyncio

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

    validated_contracts = 0
    failed_contracts = 0

    # Validate bundle contracts if provided
    if bundle_dir and plan_bundle:
        validated_contracts, failed_contracts = _validate_bundle_contracts(bundle_dir, plan_bundle)

    # Validate repo-level spec files
    if spec_files:
        console.print(f"\n[cyan]🔍 Found {len(spec_files)} API specification file(s) in repository[/cyan]")
        from specfact_cli.integrations.specmatic import check_specmatic_available, validate_spec_with_specmatic

        is_available, error_msg = check_specmatic_available()
        if is_available:
            for spec_file in spec_files[:3]:
                console.print(f"[dim]Validating {spec_file.relative_to(repo)} with Specmatic...[/dim]")
                try:
                    result = asyncio.run(validate_spec_with_specmatic(spec_file))
                    if result.is_valid:
                        console.print(f"  [green]✓[/green] {spec_file.name} is valid")
                    else:
                        console.print(f"  [yellow]⚠[/yellow] {spec_file.name} has validation issues")
                        if result.errors:
                            for error in result.errors[:2]:
                                console.print(f"    - {error}")
                except Exception as e:
                    console.print(f"  [yellow]⚠[/yellow] Validation error: {e!s}")
            if len(spec_files) > 3:
                console.print(
                    f"[dim]... and {len(spec_files) - 3} more spec file(s) (run 'specfact spec validate' to validate all)[/dim]"
                )
            console.print("[dim]💡 Tip: Run 'specfact spec mock' to start a mock server for development[/dim]")
        else:
            console.print(f"[dim]💡 Tip: Install Specmatic to validate API specs: {error_msg}[/dim]")
    elif validated_contracts > 0 or failed_contracts > 0:
        # Only show mock server tip if we validated contracts
        console.print("[dim]💡 Tip: Run 'specfact spec mock' to start a mock server for development[/dim]")


def _suggest_next_steps(repo: Path, bundle: str, plan_bundle: PlanBundle | None) -> None:
    """
    Suggest next steps after first import (Phase 4.9: Quick Start Optimization).

    Args:
        repo: Repository path
        bundle: Bundle name
        plan_bundle: Generated plan bundle
    """
    if plan_bundle is None:
        return

    console.print("\n[bold cyan]📋 Next Steps:[/bold cyan]")
    console.print("[dim]Here are some commands you might want to run next:[/dim]\n")

    # Check if this is a first run (no existing bundle)
    from specfact_cli.utils.structure import SpecFactStructure

    bundle_dir = SpecFactStructure.project_dir(base_path=repo, bundle_name=bundle)
    is_first_run = not (bundle_dir / "bundle.manifest.yaml").exists()

    if is_first_run:
        console.print("  [yellow]→[/yellow] [bold]Review your plan:[/bold]")
        console.print(f"     specfact plan review {bundle}")
        console.print("     [dim]Review and refine the generated plan bundle[/dim]\n")

        console.print("  [yellow]→[/yellow] [bold]Compare with code:[/bold]")
        console.print(f"     specfact plan compare --bundle {bundle}")
        console.print("     [dim]Detect deviations between plan and code[/dim]\n")

        console.print("  [yellow]→[/yellow] [bold]Validate SDD:[/bold]")
        console.print(f"     specfact enforce sdd {bundle}")
        console.print("     [dim]Check for violations and coverage thresholds[/dim]\n")
    else:
        console.print("  [yellow]→[/yellow] [bold]Review changes:[/bold]")
        console.print(f"     specfact plan review {bundle}")
        console.print("     [dim]Review updates to your plan bundle[/dim]\n")

        console.print("  [yellow]→[/yellow] [bold]Check deviations:[/bold]")
        console.print(f"     specfact plan compare --bundle {bundle}")
        console.print("     [dim]See what changed since last import[/dim]\n")


def _suggest_constitution_bootstrap(repo: Path) -> None:
    """Suggest or generate constitution bootstrap for brownfield imports."""
    specify_dir = repo / ".specify" / "memory"
    constitution_path = specify_dir / "constitution.md"
    if not constitution_path.exists() or (
        constitution_path.exists() and constitution_path.read_text(encoding="utf-8").strip() in ("", "# Constitution")
    ):
        import os

        is_test_env = os.environ.get("TEST_MODE") == "true" or os.environ.get("PYTEST_CURRENT_TEST") is not None
        if is_test_env:
            from specfact_cli.enrichers.constitution_enricher import ConstitutionEnricher

            specify_dir.mkdir(parents=True, exist_ok=True)
            enricher = ConstitutionEnricher()
            enriched_content = enricher.bootstrap(repo, constitution_path)
            constitution_path.write_text(enriched_content, encoding="utf-8")
        else:
            if runtime.is_interactive():
                console.print()
                console.print("[bold cyan]💡 Tip:[/bold cyan] Generate project constitution for tool integration")
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
                console.print()
                console.print(
                    "[dim]💡 Tip: Run 'specfact sdd constitution bootstrap --repo .' to generate constitution[/dim]"
                )


def _enrich_for_speckit_compliance(plan_bundle: PlanBundle) -> None:
    """
    Enrich plan for Spec-Kit compliance using PlanEnricher.

    This function uses PlanEnricher for consistent enrichment behavior with
    the `plan review --auto-enrich` command. It also adds edge case stories
    for features with only 1 story to ensure better tool compliance.
    """
    console.print("\n[cyan]🔧 Enriching plan for tool compliance...[/cyan]")
    try:
        from specfact_cli.enrichers.plan_enricher import PlanEnricher
        from specfact_cli.utils.terminal import get_progress_config

        # Use PlanEnricher for consistent enrichment (same as plan review --auto-enrich)
        console.print("[dim]Enhancing vague acceptance criteria, incomplete requirements, generic tasks...[/dim]")

        # Add progress reporting for large bundles
        progress_columns, progress_kwargs = get_progress_config()
        with Progress(
            *progress_columns,
            console=console,
            **progress_kwargs,
        ) as progress:
            enrich_task = progress.add_task(
                f"[cyan]Enriching {len(plan_bundle.features)} features...",
                total=len(plan_bundle.features),
            )

            enricher = PlanEnricher()
            enrichment_summary = enricher.enrich_plan(plan_bundle)
            progress.update(enrich_task, completed=len(plan_bundle.features))
            progress.remove_task(enrich_task)

        # Add edge case stories for features with only 1 story (preserve existing behavior)
        features_with_one_story = [f for f in plan_bundle.features if len(f.stories) == 1]
        if features_with_one_story:
            console.print(f"[yellow]⚠ Found {len(features_with_one_story)} features with only 1 story[/yellow]")
            console.print("[dim]Adding edge case stories for better tool compliance...[/dim]")

            with Progress(
                *progress_columns,
                console=console,
                **progress_kwargs,
            ) as progress:
                edge_case_task = progress.add_task(
                    "[cyan]Adding edge case stories...",
                    total=len(features_with_one_story),
                )

                for idx, feature in enumerate(features_with_one_story):
                    edge_case_title = f"As a user, I receive error handling for {feature.title.lower()}"
                    edge_case_acceptance = [
                        "Must verify error conditions are handled gracefully",
                        "Must validate error messages are clear and actionable",
                        "Must ensure system recovers from errors",
                    ]

                    existing_story_nums = []
                    for s in feature.stories:
                        parts = s.key.split("-")
                        if len(parts) >= 2:
                            last_part = parts[-1]
                            if last_part.isdigit():
                                existing_story_nums.append(int(last_part))

                    next_story_num = max(existing_story_nums) + 1 if existing_story_nums else 2
                    feature_key_parts = feature.key.split("-")
                    if len(feature_key_parts) >= 2:
                        class_name = feature_key_parts[-1]
                        story_key = f"STORY-{class_name}-{next_story_num:03d}"
                    else:
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
                    progress.update(edge_case_task, completed=idx + 1)

                progress.remove_task(edge_case_task)

            console.print(f"[green]✓ Added edge case stories to {len(features_with_one_story)} features[/green]")

        # Display enrichment summary (consistent with plan review --auto-enrich)
        if enrichment_summary["features_updated"] > 0 or enrichment_summary["stories_updated"] > 0:
            console.print(
                f"[green]✓ Enhanced plan bundle: {enrichment_summary['features_updated']} features, "
                f"{enrichment_summary['stories_updated']} stories updated[/green]"
            )
            if enrichment_summary["acceptance_criteria_enhanced"] > 0:
                console.print(
                    f"[dim]  - Enhanced {enrichment_summary['acceptance_criteria_enhanced']} acceptance criteria[/dim]"
                )
            if enrichment_summary["requirements_enhanced"] > 0:
                console.print(f"[dim]  - Enhanced {enrichment_summary['requirements_enhanced']} requirements[/dim]")
            if enrichment_summary["tasks_enhanced"] > 0:
                console.print(f"[dim]  - Enhanced {enrichment_summary['tasks_enhanced']} tasks[/dim]")
        else:
            console.print("[green]✓ Plan bundle is already well-specified (no enrichments needed)[/green]")

        console.print("[green]✓ Tool enrichment complete[/green]")

    except Exception as e:
        console.print(f"[yellow]⚠ Tool enrichment failed: {e}[/yellow]")
        console.print("[dim]Plan is still valid, but may need manual enrichment[/dim]")


def _generate_report(
    repo: Path,
    bundle_dir: Path,
    plan_bundle: PlanBundle,
    confidence: float,
    enrichment: Path | None,
    report: Path,
) -> None:
    """Generate import report."""
    # Ensure report directory exists (Phase 8.5: bundle-specific reports)
    report.parent.mkdir(parents=True, exist_ok=True)

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

    report.write_text(report_content)
    console.print(f"[dim]Report written to: {report}[/dim]")


@app.command("from-bridge")
def from_bridge(
    # Target/Input
    repo: Path = typer.Option(
        Path("."),
        "--repo",
        help="Path to repository with external tool artifacts",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    # Output/Results
    report: Path | None = typer.Option(
        None,
        "--report",
        help="Path to write import report",
    ),
    out_branch: str = typer.Option(
        "feat/specfact-migration",
        "--out-branch",
        help="Feature branch name for migration",
    ),
    # Behavior/Options
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
    force: bool = typer.Option(
        False,
        "--force",
        help="Overwrite existing files",
    ),
    # Advanced/Configuration
    adapter: str = typer.Option(
        "speckit",
        "--adapter",
        help="Adapter type: speckit, openspec, generic-markdown (available). Default: auto-detect",
        hidden=True,  # Hidden by default, shown with --help-advanced
    ),
) -> None:
    """
    Convert external tool project to SpecFact contract format using bridge architecture.

    This command uses bridge configuration to scan an external tool repository
    (e.g., Spec-Kit, OpenSpec, generic-markdown), parse its structure, and generate equivalent
    SpecFact contracts, protocols, and plans.

    Supported adapters (code/spec adapters only):
    - speckit: Spec-Kit projects (specs/, .specify/) - import & sync
    - openspec: OpenSpec integration (openspec/) - read-only sync (Phase 1)
    - generic-markdown: Generic markdown-based specifications - import & sync

    Note: For backlog synchronization (GitHub Issues, ADO, Linear, Jira), use 'specfact sync bridge' instead.

    **Parameter Groups:**
    - **Target/Input**: --repo
    - **Output/Results**: --report, --out-branch
    - **Behavior/Options**: --dry-run, --write, --force
    - **Advanced/Configuration**: --adapter

    **Examples:**
        specfact import from-bridge --repo ./my-project --adapter speckit --write
        specfact import from-bridge --repo ./my-project --write  # Auto-detect adapter
        specfact import from-bridge --repo ./my-project --dry-run  # Preview changes
    """
    from specfact_cli.sync.bridge_probe import BridgeProbe
    from specfact_cli.utils.structure import SpecFactStructure

    if is_debug_mode():
        debug_log_operation(
            "command",
            "import from-bridge",
            "started",
            extra={"repo": str(repo), "adapter": adapter, "dry_run": dry_run, "write": write},
        )
        debug_print("[dim]import from-bridge: started[/dim]")

    # Auto-detect adapter if not specified
    if adapter == "speckit" or adapter == "auto":
        probe = BridgeProbe(repo)
        detected_capabilities = probe.detect()
        # Use detected tool directly (e.g., "speckit", "openspec", "github")
        # BridgeProbe already tries all registered adapters
        if detected_capabilities.tool == "unknown":
            if is_debug_mode():
                debug_log_operation(
                    "command",
                    "import from-bridge",
                    "failed",
                    error="Could not auto-detect adapter",
                    extra={"reason": "adapter_unknown"},
                )
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

    # Get adapter from registry (universal pattern - no hard-coded checks)
    adapter_instance = AdapterRegistry.get_adapter(adapter_lower)
    if adapter_instance is None:
        console.print(f"[bold red]✗[/bold red] Adapter '{adapter_lower}' not found in registry")
        console.print("[dim]Available adapters: " + ", ".join(AdapterRegistry.list_adapters()) + "[/dim]")
        raise typer.Exit(1)

    # Use adapter's detect() method
    from specfact_cli.sync.bridge_probe import BridgeProbe

    probe = BridgeProbe(repo)
    capabilities = probe.detect()
    bridge_config = probe.auto_generate_bridge(capabilities) if capabilities.tool != "unknown" else None

    if not adapter_instance.detect(repo, bridge_config):
        console.print(f"[bold red]✗[/bold red] Not a {adapter_lower} repository")
        console.print(f"[dim]Expected: {adapter_lower} structure[/dim]")
        console.print("[dim]Tip: Use 'specfact sync bridge probe' to auto-detect tool configuration[/dim]")
        raise typer.Exit(1)

        console.print(f"[bold green]✓[/bold green] Detected {adapter_lower} repository")

        # Get adapter capabilities for adapter-specific operations
        capabilities = adapter_instance.get_capabilities(repo, bridge_config)

    telemetry_metadata = {
        "adapter": adapter,
        "dry_run": dry_run,
        "write": write,
        "force": force,
    }

    with telemetry.track_command("import.from_bridge", telemetry_metadata) as record:
        console.print(f"[bold cyan]Importing {adapter_lower} project from:[/bold cyan] {repo}")

        # Reject backlog adapters - they should use 'sync bridge' instead
        backlog_adapters = {"github", "ado", "linear", "jira", "notion"}
        if adapter_lower in backlog_adapters:
            console.print(
                f"[bold yellow]⚠[/bold yellow] '{adapter_lower}' is a backlog adapter, not a code/spec adapter"
            )
            console.print(
                f"[dim]Use 'specfact sync bridge --adapter {adapter_lower}' for backlog synchronization[/dim]"
            )
            console.print(
                "[dim]The 'import from-bridge' command is for importing code/spec projects (Spec-Kit, OpenSpec, generic-markdown)[/dim]"
            )
            raise typer.Exit(1)

        # Use adapter for feature discovery (adapter-agnostic)
        if dry_run:
            # Discover features using adapter
            features = adapter_instance.discover_features(repo, bridge_config)
            console.print("[yellow]→ Dry run mode - no files will be written[/yellow]")
            console.print("\n[bold]Detected Structure:[/bold]")
            console.print(
                f"  - Specs Directory: {capabilities.specs_dir if hasattr(capabilities, 'specs_dir') else 'N/A'}"
            )
            console.print(f"  - Features Found: {len(features)}")
            record({"dry_run": True, "features_found": len(features)})
            return

        if not write:
            console.print("[yellow]→ Use --write to actually convert files[/yellow]")
            console.print("[dim]Use --dry-run to preview changes[/dim]")
            return

        # Ensure SpecFact structure exists
        SpecFactStructure.ensure_structure(repo)

        progress_columns, progress_kwargs = get_progress_config()
        with Progress(
            *progress_columns,
            console=console,
            **progress_kwargs,
        ) as progress:
            # Step 1: Discover features from markdown artifacts (adapter-agnostic)
            task = progress.add_task(f"Discovering {adapter_lower} features...", total=None)
            # Use adapter's discover_features method (universal pattern)
            features = adapter_instance.discover_features(repo, bridge_config)

            if not features:
                console.print(f"[bold red]✗[/bold red] No features found in {adapter_lower} repository")
                console.print("[dim]Expected: specs/*/spec.md files (or bridge-configured paths)[/dim]")
                console.print("[dim]Tip: Use 'specfact sync bridge probe' to validate bridge configuration[/dim]")
                raise typer.Exit(1)
            progress.update(task, description=f"✓ Discovered {len(features)} features")

            # Step 2: Import artifacts using BridgeSync (adapter-agnostic)
            from specfact_cli.sync.bridge_sync import BridgeSync

            bridge_sync = BridgeSync(repo, bridge_config=bridge_config)
            protocol = None
            plan_bundle = None

            # Import protocol if available
            protocol_path = repo / ".specfact" / "protocols" / "workflow.protocol.yaml"
            if protocol_path.exists():
                from specfact_cli.models.protocol import Protocol
                from specfact_cli.utils.yaml_utils import load_yaml

                try:
                    protocol_data = load_yaml(protocol_path)
                    protocol = Protocol(**protocol_data)
                except Exception as e:
                    console.print(f"[yellow]⚠[/yellow] Protocol loading failed: {e}")
                    protocol = None

            # Import features using adapter's import_artifact method
            # Use "main" as default bundle name for bridge imports
            bundle_name = "main"

            # Ensure project bundle structure exists
            from specfact_cli.utils.structure import SpecFactStructure

            SpecFactStructure.ensure_project_structure(base_path=repo, bundle_name=bundle_name)
            bundle_dir = SpecFactStructure.project_dir(base_path=repo, bundle_name=bundle_name)

            # Load or create project bundle
            from specfact_cli.migrations.plan_migrator import get_latest_schema_version
            from specfact_cli.models.project import BundleManifest, BundleVersions, Product, ProjectBundle
            from specfact_cli.utils.bundle_loader import load_project_bundle, save_project_bundle

            if bundle_dir.exists() and (bundle_dir / "bundle.manifest.yaml").exists():
                plan_bundle = load_project_bundle(bundle_dir, validate_hashes=False)
            else:
                # Create initial bundle with latest schema version
                manifest = BundleManifest(
                    versions=BundleVersions(schema=get_latest_schema_version(), project="0.1.0"),
                    schema_metadata=None,
                    project_metadata=None,
                )
                product = Product(themes=[], releases=[])
                plan_bundle = ProjectBundle(
                    manifest=manifest,
                    bundle_name=bundle_name,
                    product=product,
                    features={},
                )
                save_project_bundle(plan_bundle, bundle_dir, atomic=True)

            # Import specification artifacts for each feature (creates features)
            task = progress.add_task("Importing specifications...", total=len(features))
            import_errors = []
            imported_count = 0
            for feature in features:
                # Use original directory name for path resolution (feature_branch or spec_path)
                # feature_key is normalized (uppercase/underscores), but we need original name for paths
                feature_id = feature.get("feature_branch")  # Original directory name
                if not feature_id and "spec_path" in feature:
                    # Fallback: extract from spec_path if available
                    spec_path_str = feature["spec_path"]
                    if "/" in spec_path_str:
                        parts = spec_path_str.split("/")
                        # Find the directory name (should be before spec.md)
                        for i, part in enumerate(parts):
                            if part == "spec.md" and i > 0:
                                feature_id = parts[i - 1]
                                break

                # If still no feature_id, try to use feature_key but convert back to directory format
                if not feature_id:
                    feature_key = feature.get("feature_key") or feature.get("key", "")
                    if feature_key:
                        # Convert normalized key back to directory name (ORDER_SERVICE -> order-service)
                        # This is a best-effort conversion
                        feature_id = feature_key.lower().replace("_", "-")

                if feature_id:
                    # Verify artifact path exists before importing (use original directory name)
                    try:
                        artifact_path = bridge_sync.resolve_artifact_path("specification", feature_id, bundle_name)
                        if not artifact_path.exists():
                            error_msg = f"Artifact not found for {feature_id}: {artifact_path}"
                            import_errors.append(error_msg)
                            console.print(f"[yellow]⚠[/yellow] {error_msg}")
                            progress.update(task, advance=1)
                            continue
                    except Exception as e:
                        error_msg = f"Failed to resolve artifact path for {feature_id}: {e}"
                        import_errors.append(error_msg)
                        console.print(f"[yellow]⚠[/yellow] {error_msg}")
                        progress.update(task, advance=1)
                        continue

                    # Import specification artifact (use original directory name for path resolution)
                    result = bridge_sync.import_artifact("specification", feature_id, bundle_name)
                    if result.success:
                        imported_count += 1
                    else:
                        error_msg = f"Failed to import specification for {feature_id}: {', '.join(result.errors)}"
                        import_errors.append(error_msg)
                        console.print(f"[yellow]⚠[/yellow] {error_msg}")
                progress.update(task, advance=1)

            if import_errors:
                console.print(f"[bold yellow]⚠[/bold yellow] {len(import_errors)} specification import(s) had issues")
                for error in import_errors[:5]:  # Show first 5 errors
                    console.print(f"  - {error}")
                if len(import_errors) > 5:
                    console.print(f"  ... and {len(import_errors) - 5} more")

            if imported_count == 0 and len(features) > 0:
                console.print("[bold red]✗[/bold red] No specifications were imported successfully")
                raise typer.Exit(1)

            # Reload bundle after importing specifications
            plan_bundle = load_project_bundle(bundle_dir, validate_hashes=False)

            # Optionally import plan artifacts to add plan information
            task = progress.add_task("Importing plans...", total=len(features))
            for feature in features:
                feature_key = feature.get("feature_key") or feature.get("key", "")
                if feature_key:
                    # Import plan artifact (adds plan information to existing features)
                    result = bridge_sync.import_artifact("plan", feature_key, bundle_name)
                    if not result.success and result.errors:
                        # Plan import is optional, only warn if there are actual errors
                        pass
                progress.update(task, advance=1)

            # Reload bundle after importing plans
            plan_bundle = load_project_bundle(bundle_dir, validate_hashes=False)

            # For Spec-Kit adapter, also generate protocol, Semgrep rules and GitHub Actions if supported
            # These are Spec-Kit-specific enhancements, not core import functionality
            if adapter_lower == "speckit":
                from specfact_cli.importers.speckit_converter import SpecKitConverter

                converter = SpecKitConverter(repo)
                # Step 3: Generate protocol (Spec-Kit specific)
                if hasattr(converter, "convert_protocol"):
                    task = progress.add_task("Generating protocol...", total=None)
                    try:
                        _protocol = converter.convert_protocol()  # Generates .specfact/protocols/workflow.protocol.yaml
                        progress.update(task, description="✓ Protocol generated")
                        # Reload protocol after generation
                        protocol_path = repo / ".specfact" / "protocols" / "workflow.protocol.yaml"
                        if protocol_path.exists():
                            from specfact_cli.models.protocol import Protocol
                            from specfact_cli.utils.yaml_utils import load_yaml

                            try:
                                protocol_data = load_yaml(protocol_path)
                                protocol = Protocol(**protocol_data)
                            except Exception as e:
                                console.print(f"[yellow]⚠[/yellow] Protocol loading failed: {e}")
                    except Exception as e:
                        console.print(f"[yellow]⚠[/yellow] Protocol generation failed: {e}")

                # Step 4: Generate Semgrep rules (Spec-Kit specific)
                if hasattr(converter, "generate_semgrep_rules"):
                    task = progress.add_task("Generating Semgrep rules...", total=None)
                    try:
                        _semgrep_path = converter.generate_semgrep_rules()  # Not used yet
                        progress.update(task, description="✓ Semgrep rules generated")
                    except Exception as e:
                        console.print(f"[yellow]⚠[/yellow] Semgrep rules generation failed: {e}")

                # Step 5: Generate GitHub Action workflow (Spec-Kit specific)
                if hasattr(converter, "generate_github_action"):
                    task = progress.add_task("Generating GitHub Action workflow...", total=None)
                    repo_name = repo.name if isinstance(repo, Path) else None
                    try:
                        _workflow_path = converter.generate_github_action(repo_name=repo_name)  # Not used yet
                        progress.update(task, description="✓ GitHub Action workflow generated")
                    except Exception as e:
                        console.print(f"[yellow]⚠[/yellow] GitHub Action workflow generation failed: {e}")

            # Handle file existence errors (conversion already completed above with individual try/except blocks)
            # If plan_bundle or protocol are None, try to load existing ones
            if plan_bundle is None or protocol is None:
                from specfact_cli.migrations.plan_migrator import get_current_schema_version
                from specfact_cli.models.plan import PlanBundle, Product

                if plan_bundle is None:
                    plan_bundle = PlanBundle(
                        version=get_current_schema_version(),
                        idea=None,
                        business=None,
                        product=Product(themes=[], releases=[]),
                        features=[],
                        clarifications=None,
                        metadata=None,
                    )
                if protocol is None:
                    # Try to load existing protocol if available
                    protocol_path = repo / ".specfact" / "protocols" / "workflow.protocol.yaml"
                    if protocol_path.exists():
                        from specfact_cli.models.protocol import Protocol
                        from specfact_cli.utils.yaml_utils import load_yaml

                        try:
                            protocol_data = load_yaml(protocol_path)
                            protocol = Protocol(**protocol_data)
                        except Exception:
                            pass

        # Generate report
        if report and protocol and plan_bundle:
            report_content = f"""# {adapter_lower.upper()} Import Report

## Repository: {repo}
## Adapter: {adapter_lower}

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
            from specfact_cli.models.plan import PlanBundle
            from specfact_cli.models.project import ProjectBundle

            bundle_name = "main"  # Default bundle name for bridge imports
            # Check if plan_bundle is already a ProjectBundle or needs conversion
            if isinstance(plan_bundle, ProjectBundle):
                project_bundle = plan_bundle
            elif isinstance(plan_bundle, PlanBundle):
                project_bundle = _convert_plan_bundle_to_project_bundle(plan_bundle, bundle_name)
            else:
                # Unknown type, skip conversion
                project_bundle = None

            if project_bundle:
                bundle_dir = SpecFactStructure.project_dir(base_path=repo, bundle_name=bundle_name)
                SpecFactStructure.ensure_project_structure(base_path=repo, bundle_name=bundle_name)
                save_bundle_with_progress(project_bundle, bundle_dir, atomic=True, console_instance=console)
                console.print(f"[dim]Project bundle: .specfact/projects/{bundle_name}/[/dim]")

        console.print("[bold green]✓[/bold green] Import complete!")
        console.print("[dim]Protocol: .specfact/protocols/workflow.protocol.yaml[/dim]")
        console.print("[dim]Plan: .specfact/projects/<bundle-name>/ (modular bundle)[/dim]")
        console.print("[dim]Semgrep Rules: .semgrep/async-anti-patterns.yml[/dim]")
        console.print("[dim]GitHub Action: .github/workflows/specfact-gate.yml[/dim]")

        if is_debug_mode():
            debug_log_operation(
                "command",
                "import from-bridge",
                "success",
                extra={
                    "protocol_states": len(protocol.states) if protocol else 0,
                    "features": len(plan_bundle.features) if plan_bundle else 0,
                },
            )
            debug_print("[dim]import from-bridge: success[/dim]")

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
@require(
    lambda bundle: bundle is None or (isinstance(bundle, str) and len(bundle) > 0),
    "Bundle name must be None or non-empty string",
)
@require(lambda confidence: 0.0 <= confidence <= 1.0, "Confidence must be 0.0-1.0")
@beartype
def from_code(
    # Target/Input
    bundle: str | None = typer.Argument(
        None,
        help="Project bundle name (e.g., legacy-api, auth-module). Default: active plan from 'specfact plan select'",
    ),
    repo: Path = typer.Option(
        Path("."),
        "--repo",
        help="Path to repository to import. Default: current directory (.)",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    entry_point: Path | None = typer.Option(
        None,
        "--entry-point",
        help="Subdirectory path for partial analysis (relative to repo root). Analyzes only files within this directory and subdirectories. Default: None (analyze entire repo)",
        hidden=True,  # Hidden by default, shown with --help-advanced
    ),
    enrichment: Path | None = typer.Option(
        None,
        "--enrichment",
        help="Path to Markdown enrichment report from LLM (applies missing features, confidence adjustments, business context). Default: None",
        hidden=True,  # Hidden by default, shown with --help-advanced
    ),
    # Output/Results
    report: Path | None = typer.Option(
        None,
        "--report",
        help="Path to write analysis report. Default: bundle-specific .specfact/projects/<bundle-name>/reports/brownfield/analysis-<timestamp>.md (Phase 8.5)",
    ),
    # Behavior/Options
    shadow_only: bool = typer.Option(
        False,
        "--shadow-only",
        help="Shadow mode - observe without enforcing. Default: False",
    ),
    enrich_for_speckit: bool = typer.Option(
        True,
        "--enrich-for-speckit/--no-enrich-for-speckit",
        help="Automatically enrich plan for Spec-Kit compliance (uses PlanEnricher to enhance vague acceptance criteria, incomplete requirements, generic tasks, and adds edge case stories for features with only 1 story). Default: True (enabled)",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Force full regeneration of all artifacts, ignoring incremental changes. Default: False",
    ),
    include_tests: bool = typer.Option(
        False,
        "--include-tests/--exclude-tests",
        help="Include/exclude test files in relationship mapping and dependency graph. Default: --exclude-tests (test files are excluded by default). Test files are never extracted as features (they're validation artifacts, not specifications). Use --include-tests only if you need test files in the dependency graph.",
    ),
    revalidate_features: bool = typer.Option(
        False,
        "--revalidate-features/--no-revalidate-features",
        help="Re-validate and re-analyze existing features even if source files haven't changed. Useful when analysis logic improved or confidence threshold changed. Default: False (only re-analyze if files changed)",
        hidden=True,  # Hidden by default, shown with --help-advanced
    ),
    # Advanced/Configuration (hidden by default, use --help-advanced to see)
    confidence: float = typer.Option(
        0.5,
        "--confidence",
        min=0.0,
        max=1.0,
        help="Minimum confidence score for features. Default: 0.5 (range: 0.0-1.0)",
        hidden=True,  # Hidden by default, shown with --help-advanced
    ),
    key_format: str = typer.Option(
        "classname",
        "--key-format",
        help="Feature key format: 'classname' (FEATURE-CLASSNAME) or 'sequential' (FEATURE-001). Default: classname",
        hidden=True,  # Hidden by default, shown with --help-advanced
    ),
) -> None:
    """
    Import plan bundle from existing codebase (one-way import).

    Analyzes code structure using AI-first semantic understanding or AST-based fallback
    to generate a plan bundle that represents the current system.

    Supports dual-stack enrichment workflow: apply LLM-generated enrichment report
    to refine the auto-detected plan bundle (add missing features, adjust confidence scores,
    add business context).

    **Parameter Groups:**
    - **Target/Input**: bundle (required argument), --repo, --entry-point, --enrichment
    - **Output/Results**: --report
    - **Behavior/Options**: --shadow-only, --enrich-for-speckit, --force, --include-tests/--exclude-tests (default: exclude)
    - **Advanced/Configuration**: --confidence, --key-format

    **Examples:**
        specfact import from-code legacy-api --repo .
        specfact import from-code auth-module --repo . --enrichment enrichment-report.md
        specfact import from-code my-project --repo . --confidence 0.7 --shadow-only
        specfact import from-code my-project --repo . --force  # Force full regeneration
        specfact import from-code my-project --repo .  # Test files excluded by default
        specfact import from-code my-project --repo . --include-tests  # Include test files in dependency graph
    """
    from specfact_cli.cli import get_current_mode
    from specfact_cli.modes import get_router
    from specfact_cli.utils.structure import SpecFactStructure

    if is_debug_mode():
        debug_log_operation(
            "command",
            "import from-code",
            "started",
            extra={"bundle": bundle, "repo": str(repo), "force": force, "shadow_only": shadow_only},
        )
        debug_print("[dim]import from-code: started[/dim]")

    # Use active plan as default if bundle not provided
    if bundle is None:
        bundle = SpecFactStructure.get_active_bundle_name(repo)
        if bundle is None:
            if is_debug_mode():
                debug_log_operation(
                    "command",
                    "import from-code",
                    "failed",
                    error="Bundle name required",
                    extra={"reason": "no_bundle"},
                )
            console.print("[bold red]✗[/bold red] Bundle name required")
            console.print("[yellow]→[/yellow] Use --bundle option or run 'specfact plan select' to set active plan")
            raise typer.Exit(1)
        console.print(f"[dim]Using active plan: {bundle}[/dim]")

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

    # Check for incremental processing (if bundle exists)
    incremental_changes = _check_incremental_changes(bundle_dir, repo, enrichment, force)

    # Ensure project structure exists
    SpecFactStructure.ensure_project_structure(base_path=repo, bundle_name=bundle)

    if report is None:
        # Use bundle-specific report path (Phase 8.5)
        report = SpecFactStructure.get_bundle_brownfield_report_path(bundle_name=bundle, base_path=repo)

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

    # Phase 4.10: CI Performance Optimization - Track performance
    with (
        track_performance("import.from_code", threshold=5.0) as perf_monitor,
        telemetry.track_command("import.from_code", telemetry_metadata) as record_event,
    ):
        try:
            # If enrichment is provided, try to load existing bundle
            # Note: For now, enrichment workflow needs to be updated for modular bundles
            # TODO: Phase 4 - Update enrichment to work with modular bundles
            plan_bundle: PlanBundle | None = None

            # Check if we need to regenerate features (requires full codebase scan)
            # Features need regeneration if:
            # - No incremental changes detected (new bundle)
            # - Source files actually changed (not just missing relationships/contracts)
            # - Revalidation requested (--revalidate-features flag)
            #
            # Important: Missing relationships/contracts alone should NOT trigger feature regeneration.
            # If features exist (from checkpoint), we can regenerate relationships/contracts separately.
            # Only regenerate features if source files actually changed.
            should_regenerate_features = incremental_changes is None or revalidate_features

            # Check if source files actually changed (not just missing artifacts)
            # If features exist from checkpoint, only regenerate if source files changed
            if incremental_changes and not should_regenerate_features:
                # Check if we have features saved (checkpoint exists)
                features_dir = bundle_dir / "features"
                has_features = features_dir.exists() and any(features_dir.glob("*.yaml"))

                if has_features:
                    # Features exist from checkpoint - check if source files actually changed
                    # The incremental_check already computed this, but we need to verify:
                    # If relationships/contracts need regeneration, it could be because:
                    # 1. Source files changed (should regenerate features)
                    # 2. Relationships/contracts are just missing (should NOT regenerate features)
                    #
                    # We can tell the difference by checking if the incremental_check detected
                    # source file changes. If it did, relationships will be True.
                    # But if relationships are True just because they're missing (not because files changed),
                    # we should NOT regenerate features.
                    #
                    # The incremental_check function already handles this correctly - it only marks
                    # relationships as needing regeneration if source files changed OR if relationships don't exist.
                    # So we need to check if source files actually changed by examining feature source tracking.
                    try:
                        # Load bundle to check source tracking (we'll reuse this later if we don't regenerate)
                        existing_bundle = _load_existing_bundle(bundle_dir)
                        if existing_bundle and existing_bundle.features:
                            # Check if any source files actually changed
                            # If features don't have source_tracking yet (cancelled before source linking),
                            # we can't check file changes, so assume files haven't changed and reuse features
                            source_files_changed = False
                            has_source_tracking = False

                            for feature in existing_bundle.features:
                                if feature.source_tracking:
                                    has_source_tracking = True
                                    # Check implementation files
                                    for impl_file in feature.source_tracking.implementation_files:
                                        file_path = repo / impl_file
                                        if file_path.exists() and feature.source_tracking.has_changed(file_path):
                                            source_files_changed = True
                                            break
                                    if source_files_changed:
                                        break
                                    # Check test files
                                    for test_file in feature.source_tracking.test_files:
                                        file_path = repo / test_file
                                        if file_path.exists() and feature.source_tracking.has_changed(file_path):
                                            source_files_changed = True
                                            break
                                    if source_files_changed:
                                        break

                            # Only regenerate features if source files actually changed
                            # If features don't have source_tracking yet, assume files haven't changed
                            # (they were just discovered, not yet linked)
                            if source_files_changed:
                                should_regenerate_features = True
                                console.print("[yellow]⚠[/yellow] Source files changed - will re-analyze features\n")
                            else:
                                # Source files haven't changed (or features don't have source_tracking yet)
                                # Don't regenerate features, just regenerate relationships/contracts
                                if has_source_tracking:
                                    console.print(
                                        "[dim]✓[/dim] Features exist from checkpoint - will regenerate relationships/contracts only\n"
                                    )
                                else:
                                    console.print(
                                        "[dim]✓[/dim] Features exist from checkpoint (no source tracking yet) - will link source files and regenerate relationships/contracts\n"
                                    )
                                # Reuse the loaded bundle instead of loading again later
                                plan_bundle = existing_bundle
                    except Exception:
                        # If we can't check, be conservative and don't regenerate features
                        # (relationships/contracts will be regenerated separately)
                        pass

            # If revalidation is requested, show message
            if revalidate_features and incremental_changes:
                console.print(
                    "[yellow]⚠[/yellow] --revalidate-features enabled: Will re-analyze features even if files unchanged\n"
                )

            # If we have incremental changes and features don't need regeneration, load existing bundle
            # (unless we already loaded it above to check for source file changes)
            if incremental_changes and not should_regenerate_features and not enrichment:
                if plan_bundle is None:
                    plan_bundle = _load_existing_bundle(bundle_dir)
                if plan_bundle:
                    # Validate existing features to ensure they're still valid
                    # Only validate if we're actually using existing features (not regenerating)
                    validation_results = _validate_existing_features(plan_bundle, repo)

                    # Report validation results
                    valid_count = len(validation_results["valid_features"])
                    orphaned_count = len(validation_results["orphaned_features"])
                    total_checked = validation_results["total_checked"]

                    # Only show validation warnings if there are actual problems (orphaned or missing files)
                    # Don't warn about features with no stories - that's normal for newly discovered features
                    features_with_missing_files = [
                        key
                        for key in validation_results["invalid_features"]
                        if validation_results["missing_files"].get(key)
                    ]

                    if orphaned_count > 0 or features_with_missing_files:
                        console.print("[cyan]🔍 Validating existing features...[/cyan]")
                        console.print(
                            f"[yellow]⚠[/yellow] Feature validation found issues: {valid_count}/{total_checked} valid, "
                            f"{orphaned_count} orphaned, {len(features_with_missing_files)} with missing files"
                        )

                        # Show orphaned features
                        if orphaned_count > 0:
                            console.print("[red]  Orphaned features (all source files missing):[/red]")
                            for feature_key in validation_results["orphaned_features"][:5]:  # Show first 5
                                missing = validation_results["missing_files"].get(feature_key, [])
                                console.print(f"    [dim]- {feature_key}[/dim] ({len(missing)} missing files)")
                            if orphaned_count > 5:
                                console.print(f"    [dim]... and {orphaned_count - 5} more[/dim]")

                        # Show invalid features (only those with missing files)
                        if features_with_missing_files:
                            console.print("[yellow]  Features with missing files:[/yellow]")
                            for feature_key in features_with_missing_files[:5]:  # Show first 5
                                missing = validation_results["missing_files"].get(feature_key, [])
                                console.print(f"    [dim]- {feature_key}[/dim] ({len(missing)} missing files)")
                            if len(features_with_missing_files) > 5:
                                console.print(f"    [dim]... and {len(features_with_missing_files) - 5} more[/dim]")

                        console.print(
                            "[dim]  Tip: Use --revalidate-features to re-analyze features and fix issues[/dim]\n"
                        )
                    # Don't show validation message if all features are valid (no noise)

                    console.print("[dim]Skipping codebase analysis (features unchanged)[/dim]\n")

            if plan_bundle is None:
                # Need to run full codebase analysis (either no bundle exists, or features need regeneration)
                # If enrichment is provided, try to load existing bundle first (enrichment needs existing bundle)
                if enrichment:
                    plan_bundle = _load_existing_bundle(bundle_dir)
                    if plan_bundle is None:
                        console.print(
                            "[bold red]✗ Cannot apply enrichment: No existing bundle found. Run import without --enrichment first.[/bold red]"
                        )
                        raise typer.Exit(1)

                if plan_bundle is None:
                    # Phase 4.9 & 4.10: Track codebase analysis performance
                    with perf_monitor.track("analyze_codebase", {"files": python_file_count}):
                        # Phase 4.9: Create callback for incremental results
                        def on_incremental_update(features_count: int, themes: list[str]) -> None:
                            """Callback for incremental results (Phase 4.9: Quick Start Optimization)."""
                            # Feature count updates are shown in the progress bar description, not as separate lines
                            # No intermediate messages needed - final summary provides all information

                        plan_bundle = _analyze_codebase(
                            repo,
                            entry_point,
                            bundle,
                            confidence,
                            key_format,
                            routing_result,
                            incremental_callback=on_incremental_update,
                        )
                    if plan_bundle is None:
                        console.print("[bold red]✗ Failed to analyze codebase[/bold red]")
                        raise typer.Exit(1)

                    # Phase 4.9: Analysis complete (results shown in progress bar and final summary)
                    console.print(f"[green]✓[/green] Found {len(plan_bundle.features)} features")
                    console.print(f"[green]✓[/green] Detected themes: {', '.join(plan_bundle.product.themes)}")
                    total_stories = sum(len(f.stories) for f in plan_bundle.features)
                    console.print(f"[green]✓[/green] Total stories: {total_stories}\n")
                    record_event({"features_detected": len(plan_bundle.features), "stories_detected": total_stories})

                    # Save features immediately after analysis to avoid losing work if process is cancelled
                    # This ensures we can resume from this point if interrupted during expensive operations
                    console.print("[cyan]💾 Saving features (checkpoint)...[/cyan]")
                    project_bundle = _convert_plan_bundle_to_project_bundle(plan_bundle, bundle)
                    save_bundle_with_progress(project_bundle, bundle_dir, atomic=True, console_instance=console)
                    console.print("[dim]✓ Features saved (can resume if interrupted)[/dim]\n")

            # Ensure plan_bundle is not None before proceeding
            if plan_bundle is None:
                console.print("[bold red]✗ No plan bundle available[/bold red]")
                raise typer.Exit(1)

            # Add source tracking to features
            with perf_monitor.track("update_source_tracking"):
                _update_source_tracking(plan_bundle, repo)

            # Enhanced Analysis Phase: Extract relationships, contracts, and graph dependencies
            # Check if we need to regenerate these artifacts
            # Note: enrichment doesn't force full regeneration - only new features need contracts
            should_regenerate_relationships = incremental_changes is None or incremental_changes.get(
                "relationships", True
            )
            should_regenerate_graph = incremental_changes is None or incremental_changes.get("graph", True)
            should_regenerate_contracts = incremental_changes is None or incremental_changes.get("contracts", True)
            should_regenerate_enrichment = incremental_changes is None or incremental_changes.get(
                "enrichment_context", True
            )
            # If enrichment is provided, ensure bundle is regenerated to apply it
            # This ensures enrichment is applied even if no source files changed
            if enrichment and incremental_changes:
                # Force bundle regeneration to apply enrichment
                incremental_changes["bundle"] = True

            # Track features before enrichment to detect new ones that need contracts
            features_before_enrichment = {f.key for f in plan_bundle.features} if enrichment else set()

            # Phase 4.10: Track relationship extraction performance
            with perf_monitor.track("extract_relationships_and_graph"):
                relationships, _graph_summary = _extract_relationships_and_graph(
                    repo,
                    entry_point,
                    bundle_dir,
                    incremental_changes,
                    plan_bundle,
                    should_regenerate_relationships,
                    should_regenerate_graph,
                    include_tests,
                )

            # Apply enrichment BEFORE contract extraction so new features get contracts
            if enrichment:
                with perf_monitor.track("apply_enrichment"):
                    plan_bundle = _apply_enrichment(enrichment, plan_bundle, record_event)

                # After enrichment, check if new features were added that need contracts
                features_after_enrichment = {f.key for f in plan_bundle.features}
                new_features_added = features_after_enrichment - features_before_enrichment

                # If new features were added, we need to extract contracts for them
                # Mark contracts for regeneration if new features were added
                if new_features_added:
                    console.print(
                        f"[dim]Note: {len(new_features_added)} new feature(s) from enrichment will get contracts extracted[/dim]"
                    )
                    # New features need contracts, so ensure contract extraction runs
                    if incremental_changes and not incremental_changes.get("contracts", False):
                        # Only regenerate contracts if we have new features, not all contracts
                        should_regenerate_contracts = True

            # Phase 4.10: Track contract extraction performance
            with perf_monitor.track("extract_contracts"):
                contracts_data = _extract_contracts(
                    repo, bundle_dir, plan_bundle, should_regenerate_contracts, record_event, force=force
                )

            # Phase 4.10: Track enrichment context building performance
            with perf_monitor.track("build_enrichment_context"):
                _build_enrichment_context(
                    bundle_dir,
                    repo,
                    plan_bundle,
                    relationships,
                    contracts_data,
                    should_regenerate_enrichment,
                    record_event,
                )

            # Save bundle if needed
            with perf_monitor.track("save_bundle"):
                _save_bundle_if_needed(
                    plan_bundle,
                    bundle,
                    bundle_dir,
                    incremental_changes,
                    should_regenerate_relationships,
                    should_regenerate_graph,
                    should_regenerate_contracts,
                    should_regenerate_enrichment,
                )

            console.print("\n[bold green]✓ Import complete![/bold green]")
            console.print(f"[dim]Project bundle written to: {bundle_dir}[/dim]")

            # Validate API specs (both repo-level and bundle contracts)
            with perf_monitor.track("validate_api_specs"):
                _validate_api_specs(repo, bundle_dir=bundle_dir, plan_bundle=plan_bundle)

            # Phase 4.9: Suggest next steps (Quick Start Optimization)
            _suggest_next_steps(repo, bundle, plan_bundle)

            # Suggest constitution bootstrap
            _suggest_constitution_bootstrap(repo)

            # Enrich for tool compliance if requested
            if enrich_for_speckit:
                if plan_bundle is None:
                    console.print("[yellow]⚠ Cannot enrich: plan bundle is None[/yellow]")
                else:
                    _enrich_for_speckit_compliance(plan_bundle)

            # Generate report
            if plan_bundle is None:
                console.print("[bold red]✗ Cannot generate report: plan bundle is None[/bold red]")
                raise typer.Exit(1)

            _generate_report(repo, bundle_dir, plan_bundle, confidence, enrichment, report)

            if is_debug_mode():
                debug_log_operation(
                    "command",
                    "import from-code",
                    "success",
                    extra={"bundle": bundle, "bundle_dir": str(bundle_dir), "report": str(report)},
                )
                debug_print("[dim]import from-code: success[/dim]")

            # Phase 4.10: Print performance report if slow operations detected
            perf_report = perf_monitor.get_report()
            if perf_report.slow_operations and not os.environ.get("CI"):
                # Only show in non-CI mode (interactive)
                perf_report.print_summary()

        except KeyboardInterrupt:
            # Re-raise KeyboardInterrupt immediately (don't catch it here)
            raise
        except typer.Exit:
            # Re-raise typer.Exit (used for clean exits)
            raise
        except Exception as e:
            if is_debug_mode():
                debug_log_operation(
                    "command",
                    "import from-code",
                    "failed",
                    error=str(e),
                    extra={"reason": type(e).__name__, "bundle": bundle},
                )
            console.print(f"[bold red]✗ Import failed:[/bold red] {e}")
            raise typer.Exit(1) from e

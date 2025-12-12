"""
Import command - Import codebases and external tool projects to contract-driven format.

This module provides commands for importing existing codebases (brownfield) and
external tool projects (e.g., Spec-Kit, Linear, Jira) and converting them to
SpecFact contract-driven format using the bridge architecture.
"""

from __future__ import annotations

import multiprocessing
import os
from pathlib import Path
from typing import Any

import typer
from beartype import beartype
from icontract import require
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from specfact_cli import runtime
from specfact_cli.models.bridge import AdapterType
from specfact_cli.models.plan import Feature, PlanBundle
from specfact_cli.models.project import BundleManifest, BundleVersions, ProjectBundle
from specfact_cli.telemetry import telemetry
from specfact_cli.utils.performance import track_performance
from specfact_cli.utils.progress import save_bundle_with_progress


app = typer.Typer(
    help="Import codebases and external tool projects (e.g., Spec-Kit, Linear, Jira) to contract format",
    context_settings={"help_option_names": ["-h", "--help", "--help-advanced", "-ha"]},
)
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


def _check_incremental_changes(
    bundle_dir: Path, repo: Path, enrichment: Path | None, force: bool = False
) -> dict[str, bool] | None:
    """Check for incremental changes and return what needs regeneration."""
    if force:
        console.print("[yellow]⚠ Force mode enabled - regenerating all artifacts[/yellow]\n")
        return None  # None means regenerate everything
    if not bundle_dir.exists() or enrichment:
        return None

    from specfact_cli.utils.incremental_check import check_incremental_changes

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Checking for changes...", total=None)
            progress.update(task, description="[cyan]Loading manifest and checking file changes...")

        incremental_changes = check_incremental_changes(bundle_dir, repo, features=None)

        if not any(incremental_changes.values()):
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
            executor = ThreadPoolExecutor(max_workers=max_workers)
            interrupted = False
            try:
                future_to_task = {
                    executor.submit(update_file_hash, feature, file_path): (feature, file_path)
                    for feature, file_path in hash_tasks
                }
                try:
                    for future in as_completed(future_to_task):
                        try:
                            future.result()
                        except KeyboardInterrupt:
                            interrupted = True
                            for f in future_to_task:
                                if not f.done():
                                    f.cancel()
                            break
                        except Exception:
                            pass
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
                    executor.shutdown(wait=True)
                else:
                    executor.shutdown(wait=False)

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
    include_tests: bool = True,
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
    from specfact_cli.analyzers.graph_analyzer import GraphAnalyzer
    from specfact_cli.analyzers.relationship_mapper import RelationshipMapper
    from specfact_cli.utils.optional_deps import check_cli_tool_available

    pyan3_available, _ = check_cli_tool_available("pyan3")
    if not pyan3_available:
        console.print(
            "[dim]💡 Note: Enhanced analysis tool pyan3 is not available (call graph analysis will be skipped)[/dim]"
        )
        console.print("[dim]   Install with: pip install pyan3[/dim]")

    relationship_mapper = RelationshipMapper(repo)

    changed_files: set[Path] = set()
    if incremental_changes and plan_bundle:
        from specfact_cli.utils.incremental_check import get_changed_files

        changed_files_dict = get_changed_files(bundle_dir, repo, list(plan_bundle.features))
        for feature_changes in changed_files_dict.values():
            for file_path_str in feature_changes:
                clean_path = file_path_str.replace(" (deleted)", "")
                file_path = repo / clean_path
                if file_path.exists():
                    changed_files.add(file_path)

    if changed_files:
        python_files = list(changed_files)
        console.print(f"[dim]Analyzing {len(python_files)} changed file(s) for relationships...[/dim]")
    else:
        python_files = list(repo.rglob("*.py"))
        if entry_point:
            python_files = [f for f in python_files if entry_point in f.parts]

        # Filter files based on --include-tests/--exclude-tests flag
        # Default: Include test files for comprehensive analysis
        # --exclude-tests: Skip test files for faster processing (~30-50% speedup)
        # Rationale for excluding tests:
        # - Test files are consumers of production code (not producers)
        # - Test files import production code, but production code doesn't import tests
        # - Interfaces and routes are defined in production code, not tests
        # - Dependency graph flows from production code, so skipping tests has minimal impact
        if not include_tests:
            # Exclude test files when --exclude-tests is specified
            python_files = [
                f
                for f in python_files
                if not any(
                    skip in str(f)
                    for skip in [
                        "/test_",
                        "/tests/",
                        "/vendor/",
                        "/.venv/",
                        "/venv/",
                        "/node_modules/",
                        "/__pycache__/",
                    ]
                )
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

    # Analyze relationships in parallel (optimized for speed)
    relationships = relationship_mapper.analyze_files(python_files)
    console.print(f"[green]✓[/green] Mapped {len(relationships['imports'])} files with relationships")

    # Graph analysis is optional and can be slow - only run if explicitly needed
    # Skip by default for faster imports (can be enabled with --with-graph flag in future)
    if should_regenerate_graph and pyan3_available:
        console.print("[dim]Building dependency graph (this may take a moment)...[/dim]")
        graph_analyzer = GraphAnalyzer(repo)
        graph_analyzer.build_dependency_graph(python_files)
        graph_summary = graph_analyzer.get_graph_summary()
        if graph_summary:
            console.print(
                f"[green]✓[/green] Built dependency graph: {graph_summary.get('nodes', 0)} modules, {graph_summary.get('edges', 0)} dependencies"
            )
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
) -> dict[str, dict[str, Any]]:
    """Extract OpenAPI contracts from features."""
    import os
    from concurrent.futures import ThreadPoolExecutor, as_completed

    from specfact_cli.generators.openapi_extractor import OpenAPIExtractor
    from specfact_cli.generators.test_to_openapi import OpenAPITestConverter

    openapi_extractor = OpenAPIExtractor(repo)
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

            # In test mode, use sequential processing to avoid ThreadPoolExecutor deadlocks
            is_test_mode = os.environ.get("TEST_MODE") == "true"
            existing_contracts_count = 0
            if is_test_mode:
                # Sequential processing in test mode - avoids ThreadPoolExecutor deadlocks
                for feature in features_with_contracts:
                    try:
                        feature_key, contract_data = load_contract(feature)
                        if contract_data:
                            contracts_data[feature_key] = contract_data
                            existing_contracts_count += 1
                    except Exception:
                        pass
            else:
                max_workers = max(1, min(multiprocessing.cpu_count() or 4, 16, len(features_with_contracts)))
                executor = ThreadPoolExecutor(max_workers=max_workers)
                interrupted = False
                try:
                    future_to_feature = {
                        executor.submit(load_contract, feature): feature for feature in features_with_contracts
                    }
                    try:
                        for future in as_completed(future_to_feature):
                            try:
                                feature_key, contract_data = future.result()
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
                                pass
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
                    else:
                        executor.shutdown(wait=False)

            if existing_contracts_count > 0:
                console.print(f"[green]✓[/green] Loaded {existing_contracts_count} existing contract(s) from bundle")

    # Extract contracts if needed
    test_converter = OpenAPITestConverter(repo)
    if should_regenerate_contracts:
        features_with_files = [
            f for f in plan_bundle.features if f.source_tracking and f.source_tracking.implementation_files
        ]
    else:
        features_with_files = []

    if features_with_files and should_regenerate_contracts:
        import os

        # In test mode, use sequential processing to avoid ThreadPoolExecutor deadlocks
        is_test_mode = os.environ.get("TEST_MODE") == "true"
        # Define max_workers for non-test mode (always defined to satisfy type checker)
        max_workers = 1
        if is_test_mode:
            console.print(
                f"[cyan]📋 Extracting contracts from {len(features_with_files)} features (sequential mode)...[/cyan]"
            )
        else:
            max_workers = max(1, min(multiprocessing.cpu_count() or 4, 16, len(features_with_files)))
            console.print(
                f"[cyan]📋 Extracting contracts from {len(features_with_files)} features (using {max_workers} workers)...[/cyan]"
            )

        from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

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

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total})"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Extracting contracts...", total=len(features_with_files))
            if is_test_mode:
                # Sequential processing in test mode - avoids ThreadPoolExecutor deadlocks
                completed_count = 0
                for feature in features_with_files:
                    try:
                        feature_key, openapi_spec = process_feature(feature)
                        completed_count += 1
                        progress.update(task, completed=completed_count)
                        if openapi_spec:
                            contract_ref = f"contracts/{feature_key}.openapi.yaml"
                            feature.contract = contract_ref
                            contracts_data[feature_key] = openapi_spec
                            contracts_generated += 1
                    except Exception as e:
                        completed_count += 1
                        progress.update(task, completed=completed_count)
                        console.print(f"[dim]⚠ Warning: Failed to process feature: {e}[/dim]")
            else:
                executor = ThreadPoolExecutor(max_workers=max_workers)
                interrupted = False
                try:
                    future_to_feature = {executor.submit(process_feature, f): f for f in features_with_files}
                    completed_count = 0
                    try:
                        for future in as_completed(future_to_feature):
                            try:
                                feature_key, openapi_spec = future.result()
                                completed_count += 1
                                progress.update(task, completed=completed_count)
                                if openapi_spec:
                                    feature = next(f for f in features_with_files if f.key == feature_key)
                                    contract_ref = f"contracts/{feature_key}.openapi.yaml"
                                    feature.contract = contract_ref
                                    contracts_data[feature_key] = openapi_spec
                                    contracts_generated += 1
                            except KeyboardInterrupt:
                                interrupted = True
                                for f in future_to_feature:
                                    if not f.done():
                                        f.cancel()
                                break
                            except Exception as e:
                                completed_count += 1
                                progress.update(task, completed=completed_count)
                                console.print(f"[dim]⚠ Warning: Failed to process feature: {e}[/dim]")
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
    context_path = bundle_dir / "enrichment_context.md"
    if should_regenerate_enrichment:
        console.print("\n[cyan]📊 Building enrichment context...[/cyan]")
        from specfact_cli.utils.enrichment_context import build_enrichment_context

        enrichment_context = build_enrichment_context(
            plan_bundle, relationships=relationships, contracts=contracts_data
        )
        _enrichment_context_md = enrichment_context.to_markdown()
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

    console.print(f"\n[cyan]🔍 Validating {len(contract_files)} contract(s) in bundle with Specmatic...[/cyan]")
    for contract_path, feature_key in contract_files[:5]:  # Validate up to 5 contracts
        console.print(f"[dim]Validating {contract_path.relative_to(bundle_dir)} (from {feature_key})...[/dim]")
        try:
            result = asyncio.run(validate_spec_with_specmatic(contract_path))
            if result.is_valid:
                console.print(f"  [green]✓[/green] {contract_path.name} is valid")
                validated_count += 1
            else:
                console.print(f"  [yellow]⚠[/yellow] {contract_path.name} has validation issues")
                if result.errors:
                    for error in result.errors[:2]:
                        console.print(f"    - {error}")
                failed_count += 1
        except Exception as e:
            console.print(f"  [yellow]⚠[/yellow] Validation error: {e!s}")
            failed_count += 1

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
                    "[dim]💡 Tip: Run 'specfact bridge constitution bootstrap --repo .' to generate constitution[/dim]"
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

        # Use PlanEnricher for consistent enrichment (same as plan review --auto-enrich)
        console.print("[dim]Enhancing vague acceptance criteria, incomplete requirements, generic tasks...[/dim]")
        enricher = PlanEnricher()
        enrichment_summary = enricher.enrich_plan(plan_bundle)

        # Add edge case stories for features with only 1 story (preserve existing behavior)
        features_with_one_story = [f for f in plan_bundle.features if len(f.stories) == 1]
        if features_with_one_story:
            console.print(f"[yellow]⚠ Found {len(features_with_one_story)} features with only 1 story[/yellow]")
            console.print("[dim]Adding edge case stories for better tool compliance...[/dim]")

            for feature in features_with_one_story:
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
        help="Adapter type (speckit, generic-markdown). Default: auto-detect",
        hidden=True,  # Hidden by default, shown with --help-advanced
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
            TimeElapsedColumn(),
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

            except (FileExistsError, IsADirectoryError) as e:
                from specfact_cli.migrations.plan_migrator import get_current_schema_version
                from specfact_cli.models.plan import PlanBundle, Product

                # Allow reruns without forcing callers to pass --force
                # Also handle case where path is a directory instead of a file
                console.print(
                    f"[yellow]⚠ Files already exist or path conflict; reusing existing generated artifacts ({e})[/yellow]"
                )
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
            except Exception as e:
                console.print(f"[bold red]✗[/bold red] Conversion failed: {e}")
                import traceback

                console.print(f"[dim]{traceback.format_exc()}[/dim]")
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
            save_bundle_with_progress(project_bundle, bundle_dir, atomic=True, console_instance=console)
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
        True,
        "--include-tests/--exclude-tests",
        help="Include/exclude test files in relationship mapping. Default: --include-tests (test files are included for comprehensive analysis). Use --exclude-tests to optimize speed.",
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
    - **Behavior/Options**: --shadow-only, --enrich-for-speckit, --force, --include-tests/--exclude-tests
    - **Advanced/Configuration**: --confidence, --key-format

    **Examples:**
        specfact import from-code legacy-api --repo .
        specfact import from-code auth-module --repo . --enrichment enrichment-report.md
        specfact import from-code my-project --repo . --confidence 0.7 --shadow-only
        specfact import from-code my-project --repo . --force  # Force full regeneration
        specfact import from-code my-project --repo . --exclude-tests  # Exclude test files for faster processing
    """
    from specfact_cli.cli import get_current_mode
    from specfact_cli.modes import get_router
    from specfact_cli.utils.structure import SpecFactStructure

    # Use active plan as default if bundle not provided
    if bundle is None:
        bundle = SpecFactStructure.get_active_bundle_name(repo)
        if bundle is None:
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
            # - Relationships need regeneration (indicates source file changes)
            # - Contracts need regeneration (indicates source file changes)
            # - Bundle needs regeneration (indicates features changed)
            # If only graph or enrichment_context need regeneration, we can skip full scan
            should_regenerate_features = incremental_changes is None or any(
                incremental_changes.get(key, True)
                for key in ["relationships", "contracts", "bundle"]  # These indicate source file/feature changes
            )

            # If we have incremental changes and features don't need regeneration, load existing bundle
            if incremental_changes and not should_regenerate_features and not enrichment:
                plan_bundle = _load_existing_bundle(bundle_dir)
                if plan_bundle:
                    console.print("[dim]Skipping codebase analysis (features unchanged)[/dim]\n")

            if plan_bundle is None:
                # Need to run full codebase analysis (either no bundle exists, or features need regeneration)
                if enrichment:
                    plan_bundle = _load_existing_bundle(bundle_dir)

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

            # Ensure plan_bundle is not None before proceeding
            if plan_bundle is None:
                console.print("[bold red]✗ No plan bundle available[/bold red]")
                raise typer.Exit(1)

            # Add source tracking to features
            with perf_monitor.track("update_source_tracking"):
                _update_source_tracking(plan_bundle, repo)

            # Enhanced Analysis Phase: Extract relationships, contracts, and graph dependencies
            # Check if we need to regenerate these artifacts
            should_regenerate_relationships = incremental_changes is None or incremental_changes.get(
                "relationships", True
            )
            should_regenerate_graph = incremental_changes is None or incremental_changes.get("graph", True)
            should_regenerate_contracts = incremental_changes is None or incremental_changes.get("contracts", True)
            should_regenerate_enrichment = incremental_changes is None or incremental_changes.get(
                "enrichment_context", True
            )

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

            # Phase 4.10: Track contract extraction performance
            with perf_monitor.track("extract_contracts"):
                contracts_data = _extract_contracts(
                    repo, bundle_dir, plan_bundle, should_regenerate_contracts, record_event
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

            # Apply enrichment if provided
            if enrichment:
                with perf_monitor.track("apply_enrichment"):
                    plan_bundle = _apply_enrichment(enrichment, plan_bundle, record_event)

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
            console.print(f"[bold red]✗ Import failed:[/bold red] {e}")
            raise typer.Exit(1) from e

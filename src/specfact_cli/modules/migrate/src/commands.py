"""
Migrate command - Convert project bundles between formats.

This module provides commands for migrating project bundles from verbose
format to OpenAPI contract-based format.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import typer
from beartype import beartype
from icontract import ensure, require
from rich.console import Console

from specfact_cli.models.plan import Feature
from specfact_cli.runtime import debug_log_operation, debug_print, is_debug_mode
from specfact_cli.utils import print_error, print_info, print_success, print_warning
from specfact_cli.utils.progress import load_bundle_with_progress, save_bundle_with_progress
from specfact_cli.utils.structure import SpecFactStructure
from specfact_cli.utils.structured_io import StructuredFormat


app = typer.Typer(help="Migrate project bundles between formats")
console = Console()


@app.command("cleanup-legacy")
@beartype
@require(lambda repo: isinstance(repo, Path), "Repository path must be Path")
@ensure(lambda result: result is None, "Must return None")
def cleanup_legacy(
    repo: Path = typer.Option(
        Path("."),
        "--repo",
        help="Path to repository. Default: current directory (.)",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be removed without actually removing. Default: False",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Remove directories even if they contain files. Default: False (only removes empty directories)",
    ),
) -> None:
    """
    Remove empty legacy top-level directories (Phase 8.5 cleanup).

    Removes legacy directories that are no longer created by ensure_structure():
    - .specfact/plans/ (deprecated: no monolithic bundles, active bundle config moved to config.yaml)
    - .specfact/contracts/ (now bundle-specific: .specfact/projects/<bundle-name>/contracts/)
    - .specfact/protocols/ (now bundle-specific: .specfact/projects/<bundle-name>/protocols/)
    - .specfact/sdd/ (now bundle-specific: .specfact/projects/<bundle-name>/sdd.yaml)
    - .specfact/reports/ (now bundle-specific: .specfact/projects/<bundle-name>/reports/)
    - .specfact/gates/results/ (removed: not used; enforcement reports are bundle-specific in reports/enforcement/)

    **Note**: If plans/config.yaml exists, it will be preserved (migrated to config.yaml) before removing plans/ directory.

    **Safety**: By default, only removes empty directories. Use --force to remove directories with files.

    **Examples:**
        specfact migrate cleanup-legacy --repo .
        specfact migrate cleanup-legacy --repo . --dry-run
        specfact migrate cleanup-legacy --repo . --force  # Remove even if files exist
    """
    if is_debug_mode():
        debug_log_operation(
            "command",
            "migrate cleanup-legacy",
            "started",
            extra={"repo": str(repo), "dry_run": dry_run, "force": force},
        )
        debug_print("[dim]migrate cleanup-legacy: started[/dim]")

    specfact_dir = repo / SpecFactStructure.ROOT
    if not specfact_dir.exists():
        console.print(f"[yellow]⚠[/yellow] No .specfact directory found at {specfact_dir}")
        return

    legacy_dirs = [
        (specfact_dir / "plans", "plans"),
        (specfact_dir / "contracts", "contracts"),
        (specfact_dir / "protocols", "protocols"),
        (specfact_dir / "sdd", "sdd"),
        (specfact_dir / "reports", "reports"),
        (specfact_dir / "gates" / "results", "gates/results"),
    ]

    removed_count = 0
    skipped_count = 0

    # Special handling for plans/ directory: migrate config.yaml before removal
    plans_dir = specfact_dir / "plans"
    plans_config = plans_dir / "config.yaml"
    if plans_config.exists() and not dry_run:
        try:
            import yaml

            # Read legacy config
            with plans_config.open() as f:
                legacy_config = yaml.safe_load(f) or {}
            active_plan = legacy_config.get("active_plan")

            if active_plan:
                # Migrate to global config.yaml
                global_config_path = specfact_dir / "config.yaml"
                global_config = {}
                if global_config_path.exists():
                    with global_config_path.open() as f:
                        global_config = yaml.safe_load(f) or {}
                global_config[SpecFactStructure.ACTIVE_BUNDLE_CONFIG_KEY] = active_plan
                global_config_path.parent.mkdir(parents=True, exist_ok=True)
                with global_config_path.open("w") as f:
                    yaml.dump(global_config, f, default_flow_style=False, sort_keys=False)
                console.print("[green]✓[/green] Migrated active bundle config from plans/config.yaml to config.yaml")
        except Exception as e:
            console.print(f"[yellow]⚠[/yellow] Failed to migrate plans/config.yaml: {e}")

    for legacy_dir, name in legacy_dirs:
        if not legacy_dir.exists():
            continue

        # Check if directory is empty
        has_files = any(legacy_dir.iterdir())
        if has_files and not force:
            console.print(f"[yellow]⚠[/yellow] Skipping {name}/ (contains files, use --force to remove): {legacy_dir}")
            skipped_count += 1
            continue

        if dry_run:
            if has_files:
                console.print(f"[dim]Would remove {name}/ (contains files, --force required): {legacy_dir}[/dim]")
            else:
                console.print(f"[dim]Would remove empty {name}/: {legacy_dir}[/dim]")
        else:
            try:
                if has_files:
                    shutil.rmtree(legacy_dir)
                    console.print(f"[green]✓[/green] Removed {name}/ (with files): {legacy_dir}")
                else:
                    legacy_dir.rmdir()
                    console.print(f"[green]✓[/green] Removed empty {name}/: {legacy_dir}")
                removed_count += 1
            except OSError as e:
                console.print(f"[red]✗[/red] Failed to remove {name}/: {e}")
                skipped_count += 1

    if dry_run:
        console.print(
            f"\n[dim]Dry run complete. Would remove {removed_count} directory(ies), skip {skipped_count}[/dim]"
        )
    else:
        if removed_count > 0:
            console.print(
                f"\n[bold green]✓[/bold green] Cleanup complete. Removed {removed_count} legacy directory(ies)"
            )
        if skipped_count > 0:
            console.print(
                f"[yellow]⚠[/yellow] Skipped {skipped_count} directory(ies) (use --force to remove directories with files)"
            )
        if removed_count == 0 and skipped_count == 0:
            console.print("[dim]No legacy directories found to remove[/dim]")
    if is_debug_mode():
        debug_log_operation(
            "command",
            "migrate cleanup-legacy",
            "success",
            extra={"removed_count": removed_count, "skipped_count": skipped_count},
        )
        debug_print("[dim]migrate cleanup-legacy: success[/dim]")


@app.command("to-contracts")
@beartype
@require(
    lambda bundle: bundle is None or (isinstance(bundle, str) and len(bundle) > 0),
    "Bundle name must be None or non-empty string",
)
@require(lambda repo: isinstance(repo, Path), "Repository path must be Path")
@ensure(lambda result: result is None, "Must return None")
def to_contracts(
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
    extract_openapi: bool = typer.Option(
        True,
        "--extract-openapi/--no-extract-openapi",
        help="Extract OpenAPI contracts from verbose acceptance criteria. Default: True",
    ),
    validate_with_specmatic: bool = typer.Option(
        True,
        "--validate-with-specmatic/--no-validate-with-specmatic",
        help="Validate generated contracts with Specmatic. Default: True",
    ),
    clean_verbose_specs: bool = typer.Option(
        True,
        "--clean-verbose-specs/--no-clean-verbose-specs",
        help="Convert verbose Given-When-Then acceptance criteria to scenarios or remove them. Default: True",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be migrated without actually migrating. Default: False",
    ),
) -> None:
    """
    Convert verbose project bundle to contract-based format.

    Migrates project bundles from verbose "Given...When...Then" acceptance criteria
    to lightweight OpenAPI contract-based format, reducing bundle size significantly.

    For non-API features, verbose acceptance criteria are converted to scenarios
    or removed to reduce bundle size.

    **Parameter Groups:**
    - **Target/Input**: bundle (required argument), --repo
    - **Behavior/Options**: --extract-openapi, --validate-with-specmatic, --clean-verbose-specs, --dry-run

    **Examples:**
        specfact migrate to-contracts legacy-api --repo .
        specfact migrate to-contracts my-bundle --repo . --dry-run
        specfact migrate to-contracts my-bundle --repo . --no-validate-with-specmatic
        specfact migrate to-contracts my-bundle --repo . --no-clean-verbose-specs
    """
    from rich.console import Console

    console = Console()

    # Use active plan as default if bundle not provided
    if bundle is None:
        bundle = SpecFactStructure.get_active_bundle_name(repo)
        if bundle is None:
            console.print("[bold red]✗[/bold red] Bundle name required")
            console.print("[yellow]→[/yellow] Use --bundle option or run 'specfact plan select' to set active plan")
            raise typer.Exit(1)
        console.print(f"[dim]Using active plan: {bundle}[/dim]")
    from specfact_cli.generators.openapi_extractor import OpenAPIExtractor
    from specfact_cli.telemetry import telemetry

    repo_path = repo.resolve()
    bundle_dir = SpecFactStructure.project_dir(base_path=repo_path, bundle_name=bundle)

    if not bundle_dir.exists():
        print_error(f"Project bundle not found: {bundle_dir}")
        raise typer.Exit(1)

    telemetry_metadata = {
        "bundle": bundle,
        "extract_openapi": extract_openapi,
        "validate_with_specmatic": validate_with_specmatic,
        "dry_run": dry_run,
    }

    if is_debug_mode():
        debug_log_operation(
            "command",
            "migrate to-contracts",
            "started",
            extra={"bundle": bundle, "repo": str(repo_path), "dry_run": dry_run},
        )
        debug_print("[dim]migrate to-contracts: started[/dim]")

    with telemetry.track_command("migrate.to_contracts", telemetry_metadata) as record:
        console.print(f"[bold cyan]Migrating bundle:[/bold cyan] {bundle}")
        console.print(f"[dim]Repository:[/dim] {repo_path}")

        if dry_run:
            print_warning("DRY RUN MODE - No changes will be made")

        try:
            # Load existing project bundle with unified progress display
            project_bundle = load_bundle_with_progress(bundle_dir, validate_hashes=False, console_instance=console)

            # Ensure contracts directory exists
            contracts_dir = bundle_dir / "contracts"
            if not dry_run:
                contracts_dir.mkdir(parents=True, exist_ok=True)

            extractor = OpenAPIExtractor(repo_path)
            contracts_created = 0
            contracts_validated = 0
            contracts_removed = 0  # Track invalid contract references removed
            verbose_specs_cleaned = 0  # Track verbose specs cleaned

            # Process each feature
            for feature_key, feature in project_bundle.features.items():
                if not feature.stories:
                    continue

                # Clean verbose acceptance criteria for all features (before contract extraction)
                if clean_verbose_specs:
                    cleaned = _clean_verbose_acceptance_criteria(feature, feature_key, dry_run)
                    if cleaned:
                        verbose_specs_cleaned += cleaned

                # Check if feature already has a contract AND the file actually exists
                if feature.contract:
                    contract_path_check = bundle_dir / feature.contract
                    if contract_path_check.exists():
                        print_info(f"Feature {feature_key} already has contract: {feature.contract}")
                        continue
                    # Contract reference exists but file is missing - recreate it
                    print_warning(
                        f"Feature {feature_key} has contract reference but file is missing: {feature.contract}. Will recreate."
                    )
                    # Clear the contract reference so we recreate it
                    feature.contract = None

                # Extract OpenAPI contract
                if extract_openapi:
                    print_info(f"Extracting OpenAPI contract for {feature_key}...")

                    # Try to extract from code first (more accurate)
                    if feature.source_tracking and feature.source_tracking.implementation_files:
                        openapi_spec = extractor.extract_openapi_from_code(repo_path, feature)
                    else:
                        # Fallback to extracting from verbose acceptance criteria
                        openapi_spec = extractor.extract_openapi_from_verbose(feature)

                    # Only save contract if it has paths (non-empty spec)
                    paths = openapi_spec.get("paths", {})
                    if not paths or len(paths) == 0:
                        # Feature has no API endpoints - remove invalid contract reference if it exists
                        if feature.contract:
                            print_warning(
                                f"Feature {feature_key} has no API endpoints but has contract reference. Removing invalid reference."
                            )
                            feature.contract = None
                            contracts_removed += 1
                        else:
                            print_warning(
                                f"Feature {feature_key} has no API endpoints in acceptance criteria, skipping contract creation"
                            )
                        continue

                    # Save contract file
                    contract_filename = f"{feature_key}.openapi.yaml"
                    contract_path = contracts_dir / contract_filename

                    if not dry_run:
                        try:
                            # Ensure contracts directory exists before saving
                            contracts_dir.mkdir(parents=True, exist_ok=True)
                            extractor.save_openapi_contract(openapi_spec, contract_path)
                            # Verify contract file was actually created
                            if not contract_path.exists():
                                print_error(f"Failed to create contract file: {contract_path}")
                                continue
                            # Verify contracts directory exists
                            if not contracts_dir.exists():
                                print_error(f"Contracts directory was not created: {contracts_dir}")
                                continue
                            # Update feature with contract reference
                            feature.contract = f"contracts/{contract_filename}"
                            contracts_created += 1
                        except Exception as e:
                            print_error(f"Failed to save contract for {feature_key}: {e}")
                            continue

                        # Validate with Specmatic if requested
                        if validate_with_specmatic:
                            print_info(f"Validating contract for {feature_key} with Specmatic...")
                            import asyncio

                            try:
                                result = asyncio.run(extractor.validate_with_specmatic(contract_path))
                                if result.is_valid:
                                    print_success(f"Contract for {feature_key} is valid")
                                    contracts_validated += 1
                                else:
                                    print_warning(f"Contract for {feature_key} has validation issues:")
                                    for error in result.errors[:3]:  # Show first 3 errors
                                        console.print(f"  [yellow]- {error}[/yellow]")
                            except Exception as e:
                                print_warning(f"Specmatic validation failed: {e}")
                    else:
                        console.print(f"[dim]Would create contract: {contract_path}[/dim]")

            # Save updated project bundle if contracts were created, invalid references removed, or verbose specs cleaned
            if not dry_run and (contracts_created > 0 or contracts_removed > 0 or verbose_specs_cleaned > 0):
                print_info("Saving updated project bundle...")
                # Save contracts directory to a temporary location before atomic save
                # (atomic save removes the entire bundle_dir, so we need to preserve contracts)
                import shutil
                import tempfile

                contracts_backup_path: Path | None = None
                # Always backup contracts directory if it exists and has files
                # (even if we didn't create new ones, we need to preserve existing contracts)
                if contracts_dir.exists() and contracts_dir.is_dir() and list(contracts_dir.iterdir()):
                    # Create temporary backup of contracts directory
                    contracts_backup = tempfile.mkdtemp()
                    contracts_backup_path = Path(contracts_backup)
                    # Copy contracts directory to backup
                    shutil.copytree(contracts_dir, contracts_backup_path / "contracts", dirs_exist_ok=True)

                # Save bundle (this will remove and recreate bundle_dir)
                save_bundle_with_progress(project_bundle, bundle_dir, atomic=True, console_instance=console)

                # Restore contracts directory after atomic save
                if contracts_backup_path is not None and (contracts_backup_path / "contracts").exists():
                    restored_contracts = contracts_backup_path / "contracts"
                    # Restore contracts to bundle_dir
                    if restored_contracts.exists():
                        shutil.copytree(restored_contracts, contracts_dir, dirs_exist_ok=True)
                    # Clean up backup
                    shutil.rmtree(str(contracts_backup_path), ignore_errors=True)

                if contracts_created > 0:
                    print_success(f"Migration complete: {contracts_created} contracts created")
                if contracts_removed > 0:
                    print_success(f"Migration complete: {contracts_removed} invalid contract references removed")
                if contracts_created == 0 and contracts_removed == 0 and verbose_specs_cleaned == 0:
                    print_info("Migration complete: No changes needed")
                if verbose_specs_cleaned > 0:
                    print_success(f"Cleaned verbose specs: {verbose_specs_cleaned} stories updated")
                if validate_with_specmatic and contracts_created > 0:
                    console.print(f"[dim]Contracts validated: {contracts_validated}/{contracts_created}[/dim]")
            elif dry_run:
                console.print(f"[dim]Would create {contracts_created} contracts[/dim]")
                if clean_verbose_specs:
                    console.print(f"[dim]Would clean verbose specs in {verbose_specs_cleaned} stories[/dim]")

            if is_debug_mode():
                debug_log_operation(
                    "command",
                    "migrate to-contracts",
                    "success",
                    extra={
                        "contracts_created": contracts_created,
                        "contracts_validated": contracts_validated,
                        "verbose_specs_cleaned": verbose_specs_cleaned,
                    },
                )
                debug_print("[dim]migrate to-contracts: success[/dim]")
            record(
                {
                    "contracts_created": contracts_created,
                    "contracts_validated": contracts_validated,
                    "verbose_specs_cleaned": verbose_specs_cleaned,
                }
            )

        except Exception as e:
            if is_debug_mode():
                debug_log_operation(
                    "command",
                    "migrate to-contracts",
                    "failed",
                    error=str(e),
                    extra={"reason": type(e).__name__},
                )
            print_error(f"Migration failed: {e}")
            record({"error": str(e)})
            raise typer.Exit(1) from e


def _is_verbose_gwt_pattern(acceptance: str) -> bool:
    """Check if acceptance criteria is verbose Given-When-Then pattern."""
    # Check for verbose patterns: "Given X, When Y, Then Z" with detailed conditions
    gwt_pattern = r"Given\s+.+?,\s*When\s+.+?,\s*Then\s+.+"
    if not re.search(gwt_pattern, acceptance, re.IGNORECASE):
        return False

    # Consider verbose if it's longer than 100 characters (detailed scenario)
    # or contains multiple conditions (and/or operators)
    return (
        len(acceptance) > 100
        or " and " in acceptance.lower()
        or " or " in acceptance.lower()
        or acceptance.count(",") > 2  # Multiple comma-separated conditions
    )


def _extract_gwt_parts(acceptance: str) -> tuple[str, str, str] | None:
    """Extract Given, When, Then parts from acceptance criteria."""
    # Pattern to match "Given X, When Y, Then Z" format
    gwt_pattern = r"Given\s+(.+?),\s*When\s+(.+?),\s*Then\s+(.+?)(?:$|,)"
    match = re.search(gwt_pattern, acceptance, re.IGNORECASE | re.DOTALL)
    if match:
        return (match.group(1).strip(), match.group(2).strip(), match.group(3).strip())
    return None


def _categorize_scenario(acceptance: str) -> str:
    """Categorize scenario as primary, alternate, exception, or recovery."""
    acc_lower = acceptance.lower()
    if any(keyword in acc_lower for keyword in ["error", "exception", "fail", "invalid", "reject"]):
        return "exception"
    if any(keyword in acc_lower for keyword in ["recover", "retry", "fallback", "alternative"]):
        return "recovery"
    if any(keyword in acc_lower for keyword in ["alternate", "alternative", "else", "otherwise"]):
        return "alternate"
    return "primary"


@beartype
def _clean_verbose_acceptance_criteria(feature: Feature, feature_key: str, dry_run: bool) -> int:
    """
    Clean verbose Given-When-Then acceptance criteria.

    Converts verbose acceptance criteria to scenarios or removes them if redundant.
    Returns the number of stories cleaned.
    """
    cleaned_count = 0

    if not feature.stories:
        return 0

    for story in feature.stories:
        if not story.acceptance:
            continue

        # Check if story has GWT patterns (move all to scenarios, not just verbose ones)
        gwt_acceptance = [acc for acc in story.acceptance if "Given" in acc and "When" in acc and "Then" in acc]
        if not gwt_acceptance:
            continue

        # Initialize scenarios dict if needed
        if story.scenarios is None:
            story.scenarios = {"primary": [], "alternate": [], "exception": [], "recovery": []}

        # Convert verbose acceptance criteria to scenarios
        converted_count = 0
        remaining_acceptance = []

        for acc in story.acceptance:
            # Move all GWT patterns to scenarios (not just verbose ones)
            if "Given" in acc and "When" in acc and "Then" in acc:
                # Extract GWT parts
                gwt_parts = _extract_gwt_parts(acc)
                if gwt_parts:
                    given, when, then = gwt_parts
                    scenario_text = f"Given {given}, When {when}, Then {then}"
                    category = _categorize_scenario(acc)

                    # Add to appropriate scenario category (even if it already exists, we still remove from acceptance)
                    if scenario_text not in story.scenarios[category]:
                        story.scenarios[category].append(scenario_text)
                    # Always count as converted (removed from acceptance) even if scenario already exists
                    converted_count += 1
                # Don't keep GWT patterns in acceptance list
            else:
                # Keep non-GWT acceptance criteria
                remaining_acceptance.append(acc)

        if converted_count > 0:
            # Update acceptance criteria (remove verbose ones, keep simple ones)
            story.acceptance = remaining_acceptance

            # If all acceptance was verbose and we converted to scenarios,
            # add a simple summary acceptance criterion
            if not story.acceptance:
                story.acceptance.append(
                    f"Given {story.title}, When operations are performed, Then expected behavior is achieved"
                )

            if not dry_run:
                print_info(
                    f"Feature {feature_key}, Story {story.key}: Converted {converted_count} verbose acceptance criteria to scenarios"
                )
            else:
                console.print(
                    f"[dim]Would convert {converted_count} verbose acceptance criteria to scenarios for {feature_key}/{story.key}[/dim]"
                )

            cleaned_count += 1

    return cleaned_count


@app.command("artifacts")
@beartype
@require(
    lambda bundle: bundle is None or (isinstance(bundle, str) and len(bundle) > 0),
    "Bundle name must be None or non-empty string",
)
@require(lambda repo: isinstance(repo, Path), "Repository path must be Path")
@ensure(lambda result: result is None, "Must return None")
def migrate_artifacts(
    # Target/Input
    bundle: str | None = typer.Argument(
        None,
        help="Project bundle name (e.g., legacy-api). If not specified, migrates artifacts for all bundles found in .specfact/projects/",
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
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be migrated without actually migrating. Default: False",
    ),
    backup: bool = typer.Option(
        True,
        "--backup/--no-backup",
        help="Create backup before migration. Default: True",
    ),
) -> None:
    """
    Migrate bundle-specific artifacts to bundle folders (Phase 8.5).

    Moves artifacts from global locations to bundle-specific folders:
    - Reports: .specfact/reports/* → .specfact/projects/<bundle-name>/reports/*
    - SDD manifests: .specfact/sdd/<bundle-name>.yaml → .specfact/projects/<bundle-name>/sdd.yaml
    - Tasks: .specfact/tasks/<bundle-name>-*.yaml → .specfact/projects/<bundle-name>/tasks.yaml

    **Parameter Groups:**
    - **Target/Input**: bundle (optional argument), --repo
    - **Behavior/Options**: --dry-run, --backup/--no-backup

    **Examples:**
        specfact migrate artifacts legacy-api --repo .
        specfact migrate artifacts --repo .  # Migrate all bundles
        specfact migrate artifacts legacy-api --dry-run  # Preview migration
        specfact migrate artifacts legacy-api --no-backup  # Skip backup
    """

    repo_path = repo.resolve()
    base_path = repo_path

    # Determine which bundles to migrate
    bundles_to_migrate: list[str] = []
    if bundle:
        bundles_to_migrate = [bundle]
    else:
        # Find all bundles in .specfact/projects/
        projects_dir = base_path / SpecFactStructure.PROJECTS
        if projects_dir.exists():
            for bundle_dir in projects_dir.iterdir():
                if bundle_dir.is_dir() and (bundle_dir / "bundle.manifest.yaml").exists():
                    bundles_to_migrate.append(bundle_dir.name)
        if not bundles_to_migrate:
            print_error("No project bundles found. Create one with 'specfact plan init' or 'specfact import from-code'")
            raise typer.Exit(1)

    if is_debug_mode():
        debug_log_operation(
            "command",
            "migrate artifacts",
            "started",
            extra={"bundles": bundles_to_migrate, "repo": str(repo_path), "dry_run": dry_run},
        )
        debug_print("[dim]migrate artifacts: started[/dim]")

    console.print(f"[bold cyan]Migrating artifacts for {len(bundles_to_migrate)} bundle(s)[/bold cyan]")
    if dry_run:
        print_warning("DRY RUN MODE - No changes will be made")

    total_moved = 0
    total_errors = 0

    for bundle_name in bundles_to_migrate:
        console.print(f"\n[bold]Bundle:[/bold] {bundle_name}")

        # Verify bundle exists
        bundle_dir = SpecFactStructure.project_dir(base_path=base_path, bundle_name=bundle_name)
        if not bundle_dir.exists() or not (bundle_dir / "bundle.manifest.yaml").exists():
            # If a specific bundle was requested, fail; otherwise skip (for --all mode)
            if bundle:
                print_error(f"Bundle {bundle_name} not found")
                raise typer.Exit(1)
            print_warning(f"Bundle {bundle_name} not found, skipping")
            total_errors += 1
            continue

        # Ensure bundle-specific directories exist
        if not dry_run:
            SpecFactStructure.ensure_project_structure(base_path=base_path, bundle_name=bundle_name)

        moved_count = 0

        # 1. Migrate reports
        moved_count += _migrate_reports(base_path, bundle_name, bundle_dir, dry_run, backup)

        # 2. Migrate SDD manifest
        moved_count += _migrate_sdd(base_path, bundle_name, bundle_dir, dry_run, backup)

        # 3. Migrate tasks
        moved_count += _migrate_tasks(base_path, bundle_name, bundle_dir, dry_run, backup)

        total_moved += moved_count
        if moved_count > 0:
            print_success(f"Migrated {moved_count} artifact(s) for bundle {bundle_name}")
        else:
            print_info(f"No artifacts to migrate for bundle {bundle_name}")

    # Summary
    console.print("\n[bold cyan]Migration Summary[/bold cyan]")
    console.print(f"  Bundles processed: {len(bundles_to_migrate)}")
    console.print(f"  Artifacts moved: {total_moved}")
    if total_errors > 0:
        console.print(f"  Errors: {total_errors}")

    if dry_run:
        print_warning("DRY RUN - No changes were made. Run without --dry-run to perform migration.")

    if is_debug_mode():
        debug_log_operation(
            "command",
            "migrate artifacts",
            "success",
            extra={
                "bundles_processed": len(bundles_to_migrate),
                "total_moved": total_moved,
                "total_errors": total_errors,
            },
        )
        debug_print("[dim]migrate artifacts: success[/dim]")


def _migrate_reports(base_path: Path, bundle_name: str, bundle_dir: Path, dry_run: bool, backup: bool) -> int:
    """Migrate reports from global location to bundle-specific location."""
    moved_count = 0

    # Global reports directories
    global_reports = base_path / SpecFactStructure.REPORTS
    if not global_reports.exists():
        return 0

    # Bundle-specific reports directory
    bundle_reports_dir = bundle_dir / "reports"

    # Migrate each report type
    report_types = ["brownfield", "comparison", "enrichment", "enforcement"]
    for report_type in report_types:
        global_report_dir = global_reports / report_type
        if not global_report_dir.exists():
            continue

        bundle_report_dir = bundle_reports_dir / report_type

        # Find reports that might belong to this bundle
        # Look for files with bundle name in filename or all files if bundle is the only one
        for report_file in global_report_dir.glob("*"):
            if not report_file.is_file():
                continue

            # Check if report belongs to this bundle
            # Reports might have bundle name in filename, or we migrate all if it's the only bundle
            should_migrate = False
            if bundle_name.lower() in report_file.name.lower():
                should_migrate = True
            elif report_type == "enrichment" and ".enrichment." in report_file.name:
                # Enrichment reports are typically bundle-specific
                should_migrate = True
            elif report_type in ("brownfield", "comparison", "enforcement"):
                # For other report types, migrate if filename suggests it's for this bundle
                # or if it's the only bundle (conservative approach)
                should_migrate = True  # Migrate all reports to bundle (user can reorganize if needed)

            if should_migrate:
                target_path = bundle_report_dir / report_file.name
                if target_path.exists():
                    print_warning(f"Target report already exists: {target_path}, skipping {report_file.name}")
                    continue

                if not dry_run:
                    if backup:
                        # Create backup
                        backup_dir = (
                            base_path
                            / SpecFactStructure.ROOT
                            / ".migration-backup"
                            / bundle_name
                            / "reports"
                            / report_type
                        )
                        backup_dir.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(report_file, backup_dir / report_file.name)

                    # Move file
                    bundle_report_dir.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(report_file), str(target_path))
                    moved_count += 1
                else:
                    console.print(f"  [dim]Would move: {report_file} → {target_path}[/dim]")
                    moved_count += 1

    return moved_count


def _migrate_sdd(base_path: Path, bundle_name: str, bundle_dir: Path, dry_run: bool, backup: bool) -> int:
    """Migrate SDD manifest from global location to bundle-specific location."""
    moved_count = 0

    # Check legacy multi-SDD location: .specfact/sdd/<bundle-name>.yaml
    sdd_dir = base_path / SpecFactStructure.SDD
    legacy_sdd_yaml = sdd_dir / f"{bundle_name}.yaml"
    legacy_sdd_json = sdd_dir / f"{bundle_name}.json"

    # Check legacy single-SDD location: .specfact/sdd.yaml (only if bundle name matches active)
    legacy_single_yaml = base_path / SpecFactStructure.ROOT / "sdd.yaml"
    legacy_single_json = base_path / SpecFactStructure.ROOT / "sdd.json"

    # Determine which SDD to migrate
    sdd_to_migrate: Path | None = None
    if legacy_sdd_yaml.exists():
        sdd_to_migrate = legacy_sdd_yaml
    elif legacy_sdd_json.exists():
        sdd_to_migrate = legacy_sdd_json
    elif legacy_single_yaml.exists():
        # Only migrate single SDD if it's the active bundle
        active_bundle = SpecFactStructure.get_active_bundle_name(base_path)
        if active_bundle == bundle_name:
            sdd_to_migrate = legacy_single_yaml
    elif legacy_single_json.exists():
        active_bundle = SpecFactStructure.get_active_bundle_name(base_path)
        if active_bundle == bundle_name:
            sdd_to_migrate = legacy_single_json

    if sdd_to_migrate:
        # Bundle-specific SDD path
        target_sdd = SpecFactStructure.get_bundle_sdd_path(
            bundle_name=bundle_name,
            base_path=base_path,
            format=StructuredFormat.YAML if sdd_to_migrate.suffix == ".yaml" else StructuredFormat.JSON,
        )

        if target_sdd.exists():
            print_warning(f"Target SDD already exists: {target_sdd}, skipping {sdd_to_migrate.name}")
            return 0

        if not dry_run:
            if backup:
                # Create backup
                backup_dir = base_path / SpecFactStructure.ROOT / ".migration-backup" / bundle_name
                backup_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(sdd_to_migrate, backup_dir / sdd_to_migrate.name)

            # Move file
            target_sdd.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(sdd_to_migrate), str(target_sdd))
            moved_count += 1
        else:
            console.print(f"  [dim]Would move: {sdd_to_migrate} → {target_sdd}[/dim]")
            moved_count += 1

    return moved_count


def _migrate_tasks(base_path: Path, bundle_name: str, bundle_dir: Path, dry_run: bool, backup: bool) -> int:
    """Migrate task files from global location to bundle-specific location."""
    moved_count = 0

    # Global tasks directory
    tasks_dir = base_path / SpecFactStructure.TASKS
    if not tasks_dir.exists():
        return 0

    # Find task files for this bundle
    # Task files typically named: <bundle-name>-<hash>.tasks.yaml
    task_patterns = [
        f"{bundle_name}-*.tasks.yaml",
        f"{bundle_name}-*.tasks.json",
        f"{bundle_name}-*.tasks.md",
    ]

    task_files: list[Path] = []
    for pattern in task_patterns:
        task_files.extend(tasks_dir.glob(pattern))

    if not task_files:
        return 0

    # Bundle-specific tasks path
    target_tasks = SpecFactStructure.get_bundle_tasks_path(bundle_name=bundle_name, base_path=base_path)

    # If multiple task files, use the most recent one
    if len(task_files) > 1:
        task_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        print_info(f"Found {len(task_files)} task files for {bundle_name}, using most recent: {task_files[0].name}")

    task_file = task_files[0]

    if target_tasks.exists():
        print_warning(f"Target tasks file already exists: {target_tasks}, skipping {task_file.name}")
        return 0

    if not dry_run:
        if backup:
            # Create backup
            backup_dir = base_path / SpecFactStructure.ROOT / ".migration-backup" / bundle_name
            backup_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(task_file, backup_dir / task_file.name)

        # Move file
        target_tasks.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(task_file), str(target_tasks))
        moved_count += 1

        # Remove other task files for this bundle (if any)
        for other_task in task_files[1:]:
            if backup:
                backup_dir = base_path / SpecFactStructure.ROOT / ".migration-backup" / bundle_name
                backup_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(other_task, backup_dir / other_task.name)
            other_task.unlink()
    else:
        console.print(f"  [dim]Would move: {task_file} → {target_tasks}[/dim]")
        if len(task_files) > 1:
            console.print(f"  [dim]Would remove {len(task_files) - 1} other task file(s) for {bundle_name}[/dim]")
        moved_count += 1

    return moved_count

"""
Migrate command - Convert project bundles between formats.

This module provides commands for migrating project bundles from verbose
format to OpenAPI contract-based format.
"""

from __future__ import annotations

import re
from pathlib import Path

import typer
from beartype import beartype
from icontract import ensure, require
from rich.console import Console

from specfact_cli.models.plan import Feature
from specfact_cli.utils import print_error, print_info, print_success, print_warning
from specfact_cli.utils.bundle_loader import load_project_bundle, save_project_bundle
from specfact_cli.utils.structure import SpecFactStructure


app = typer.Typer(help="Migrate project bundles between formats")
console = Console()


@app.command("to-contracts")
@beartype
@require(lambda bundle: isinstance(bundle, str) and len(bundle) > 0, "Bundle name must be non-empty string")
@require(lambda repo: isinstance(repo, Path), "Repository path must be Path")
@ensure(lambda result: result is None, "Must return None")
def to_contracts(
    # Target/Input
    bundle: str = typer.Argument(..., help="Project bundle name (e.g., legacy-api)"),
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

    with telemetry.track_command("migrate.to_contracts", telemetry_metadata) as record:
        console.print(f"[bold cyan]Migrating bundle:[/bold cyan] {bundle}")
        console.print(f"[dim]Repository:[/dim] {repo_path}")

        if dry_run:
            print_warning("DRY RUN MODE - No changes will be made")

        try:
            # Load existing project bundle
            print_info("Loading project bundle...")
            project_bundle = load_project_bundle(bundle_dir)

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
                save_project_bundle(project_bundle, bundle_dir, atomic=True)

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

            record(
                {
                    "contracts_created": contracts_created,
                    "contracts_validated": contracts_validated,
                    "verbose_specs_cleaned": verbose_specs_cleaned,
                }
            )

        except Exception as e:
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

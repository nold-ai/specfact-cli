"""
Migrate command - Convert project bundles between formats.

This module provides commands for migrating project bundles from verbose
format to OpenAPI contract-based format.
"""

from __future__ import annotations

from pathlib import Path

import typer
from beartype import beartype
from icontract import ensure, require
from rich.console import Console

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

    **Parameter Groups:**
    - **Target/Input**: bundle (required argument), --repo
    - **Behavior/Options**: --extract-openapi, --validate-with-specmatic, --dry-run

    **Examples:**
        specfact migrate to-contracts legacy-api --repo .
        specfact migrate to-contracts my-bundle --repo . --dry-run
        specfact migrate to-contracts my-bundle --repo . --no-validate-with-specmatic
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

            # Process each feature
            for feature_key, feature in project_bundle.features.items():
                if not feature.stories:
                    continue

                # Check if feature already has a contract
                if feature.contract:
                    print_info(f"Feature {feature_key} already has contract: {feature.contract}")
                    continue

                # Extract OpenAPI contract
                if extract_openapi:
                    print_info(f"Extracting OpenAPI contract for {feature_key}...")

                    # Try to extract from code first (more accurate)
                    if feature.source_tracking and feature.source_tracking.implementation_files:
                        openapi_spec = extractor.extract_openapi_from_code(repo_path, feature)
                    else:
                        # Fallback to extracting from verbose acceptance criteria
                        openapi_spec = extractor.extract_openapi_from_verbose(feature)

                    # Save contract file
                    contract_filename = f"{feature_key}.openapi.yaml"
                    contract_path = contracts_dir / contract_filename

                    if not dry_run:
                        extractor.save_openapi_contract(openapi_spec, contract_path)
                        # Update feature with contract reference
                        feature.contract = f"contracts/{contract_filename}"
                        contracts_created += 1

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

            # Save updated project bundle
            if not dry_run and contracts_created > 0:
                print_info("Saving updated project bundle...")
                save_project_bundle(project_bundle, bundle_dir, atomic=True)
                print_success(f"Migration complete: {contracts_created} contracts created")
                if validate_with_specmatic:
                    console.print(f"[dim]Contracts validated: {contracts_validated}/{contracts_created}[/dim]")
            elif dry_run:
                console.print(f"[dim]Would create {contracts_created} contracts[/dim]")

            record(
                {
                    "contracts_created": contracts_created,
                    "contracts_validated": contracts_validated,
                }
            )

        except Exception as e:
            print_error(f"Migration failed: {e}")
            record({"error": str(e)})
            raise typer.Exit(1) from e

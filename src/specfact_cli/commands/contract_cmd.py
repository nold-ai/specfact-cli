"""
Contract command - OpenAPI contract management for project bundles.

This module provides commands for managing OpenAPI contracts within project bundles,
including initialization, validation, mock server generation, test generation, and coverage.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import typer
from beartype import beartype
from icontract import ensure, require
from rich.console import Console
from rich.table import Table

from specfact_cli.models.contract import (
    ContractIndex,
    ContractStatus,
    count_endpoints,
    load_openapi_contract,
    validate_openapi_schema,
)
from specfact_cli.models.project import FeatureIndex, ProjectBundle
from specfact_cli.utils import print_error, print_info, print_success, print_warning
from specfact_cli.utils.bundle_loader import load_project_bundle, save_project_bundle
from specfact_cli.utils.structure import SpecFactStructure


app = typer.Typer(help="Manage OpenAPI contracts for project bundles")
console = Console()


@app.command("init")
@beartype
@require(lambda repo: isinstance(repo, Path), "Repository path must be Path")
@ensure(lambda result: result is None, "Must return None")
def init_contract(
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
        help="Project bundle name (e.g., legacy-api). If not specified, attempts to auto-detect or prompt.",
    ),
    feature: str = typer.Option(..., "--feature", help="Feature key (e.g., FEATURE-001)"),
    # Output/Results
    title: str | None = typer.Option(None, "--title", help="API title (default: feature title)"),
    version: str = typer.Option("1.0.0", "--version", help="API version"),
    # Behavior/Options
    no_interactive: bool = typer.Option(
        False,
        "--no-interactive",
        help="Non-interactive mode (for CI/CD automation). Default: False (interactive mode)",
    ),
) -> None:
    """
    Initialize OpenAPI contract for a feature.

    Creates a new OpenAPI 3.0.3 contract stub in the bundle's contracts/ directory
    and links it to the feature in the bundle manifest.

    Note: Defaults to OpenAPI 3.0.3 for compatibility with Specmatic.
    Validation accepts both 3.0.x and 3.1.x for forward compatibility.

    **Parameter Groups:**
    - **Target/Input**: --repo, --bundle, --feature
    - **Output/Results**: --title, --version
    - **Behavior/Options**: --no-interactive

    **Examples:**
        specfact contract init --bundle legacy-api --feature FEATURE-001
        specfact contract init --bundle legacy-api --feature FEATURE-001 --title "Authentication API" --version 1.0.0
    """
    # Get bundle name
    if bundle is None:
        bundle = SpecFactStructure.get_active_bundle_name(repo)
        if bundle is None and not no_interactive:
            # Interactive selection
            from rich.prompt import Prompt

            plans = SpecFactStructure.list_plans(repo)
            if not plans:
                print_error("No project bundles found")
                raise typer.Exit(1)
            bundle_names = [str(p["name"]) for p in plans if p.get("name")]
            if not bundle_names:
                print_error("No valid bundle names found")
                raise typer.Exit(1)
            bundle = Prompt.ask("Select bundle", choices=bundle_names)
        elif bundle is None:
            print_error("Bundle not specified and no active bundle found")
            raise typer.Exit(1)

    # Ensure bundle is not None
    if bundle is None:
        print_error("Bundle not specified")
        raise typer.Exit(1)

    # Get bundle directory
    bundle_dir = SpecFactStructure.project_dir(base_path=repo, bundle_name=bundle)
    if not bundle_dir.exists():
        print_error(f"Project bundle not found: {bundle_dir}")
        raise typer.Exit(1)

    bundle_obj = load_project_bundle(bundle_dir)

    # Check feature exists
    if feature not in bundle_obj.features:
        print_error(f"Feature '{feature}' not found in bundle")
        raise typer.Exit(1)

    feature_obj = bundle_obj.features[feature]

    # Determine contract file path
    contracts_dir = bundle_dir / "contracts"
    contracts_dir.mkdir(parents=True, exist_ok=True)
    contract_file = contracts_dir / f"{feature}.openapi.yaml"

    if contract_file.exists():
        print_warning(f"Contract file already exists: {contract_file}")
        if not no_interactive:
            overwrite = typer.confirm("Overwrite existing contract?")
            if not overwrite:
                raise typer.Exit(0)
        else:
            raise typer.Exit(1)

    # Generate OpenAPI stub
    api_title = title or feature_obj.title
    openapi_stub = _generate_openapi_stub(api_title, version, feature)

    # Write contract file
    import yaml

    with contract_file.open("w", encoding="utf-8") as f:
        yaml.dump(openapi_stub, f, default_flow_style=False, sort_keys=False)

    # Update feature index in manifest
    contract_path = f"contracts/{contract_file.name}"
    _update_feature_contract(bundle_obj, feature, contract_path)

    # Update contract index in manifest
    _update_contract_index(bundle_obj, feature, contract_path, bundle_dir / contract_path)

    # Save bundle
    save_project_bundle(bundle_obj, bundle_dir)
    print_success(f"Initialized OpenAPI contract for {feature}: {contract_file}")


@beartype
@require(lambda title: isinstance(title, str), "Title must be str")
@require(lambda version: isinstance(version, str), "Version must be str")
@require(lambda feature: isinstance(feature, str), "Feature must be str")
@ensure(lambda result: isinstance(result, dict), "Must return dict")
def _generate_openapi_stub(title: str, version: str, feature: str) -> dict[str, Any]:
    """Generate OpenAPI 3.0.3 stub.

    Note: Defaults to 3.0.3 for Specmatic compatibility.
    Specmatic 3.1.x support is planned but not yet released (as of Dec 2025).
    Once Specmatic adds 3.1.x support, we can update the default here.
    """
    return {
        "openapi": "3.0.3",  # Default to 3.0.3 for Specmatic compatibility
        "info": {
            "title": title,
            "version": version,
            "description": f"OpenAPI contract for {feature}",
        },
        "servers": [
            {"url": "https://api.example.com/v1", "description": "Production server"},
            {"url": "https://staging.api.example.com/v1", "description": "Staging server"},
        ],
        "paths": {},
        "components": {
            "schemas": {},
            "responses": {},
            "parameters": {},
        },
    }


@beartype
@require(lambda bundle: isinstance(bundle, ProjectBundle), "Bundle must be ProjectBundle")
@require(lambda feature_key: isinstance(feature_key, str), "Feature key must be str")
@require(lambda contract_path: isinstance(contract_path, str), "Contract path must be str")
@ensure(lambda result: result is None, "Must return None")
def _update_feature_contract(bundle: ProjectBundle, feature_key: str, contract_path: str) -> None:
    """Update feature contract reference in manifest."""
    # Find feature index
    for feature_index in bundle.manifest.features:
        if feature_index.key == feature_key:
            feature_index.contract = contract_path
            return

    # If not found, create new index entry
    feature_obj = bundle.features[feature_key]
    from datetime import UTC, datetime

    feature_index = FeatureIndex(
        key=feature_key,
        title=feature_obj.title,
        file=f"features/{feature_key}.yaml",
        contract=contract_path,
        status="active",
        stories_count=len(feature_obj.stories),
        created_at=datetime.now(UTC).isoformat(),
        updated_at=datetime.now(UTC).isoformat(),
        checksum=None,
    )
    bundle.manifest.features.append(feature_index)


@beartype
@require(lambda bundle: isinstance(bundle, ProjectBundle), "Bundle must be ProjectBundle")
@require(lambda feature_key: isinstance(feature_key, str), "Feature key must be str")
@require(lambda contract_path: isinstance(contract_path, str), "Contract path must be str")
@require(lambda contract_file: isinstance(contract_file, Path), "Contract file must be Path")
@ensure(lambda result: result is None, "Must return None")
def _update_contract_index(bundle: ProjectBundle, feature_key: str, contract_path: str, contract_file: Path) -> None:
    """Update contract index in manifest."""
    import hashlib

    # Check if contract index already exists
    for contract_index in bundle.manifest.contracts:
        if contract_index.feature_key == feature_key:
            # Update existing index
            contract_index.contract_file = contract_path
            contract_index.status = ContractStatus.DRAFT
            if contract_file.exists():
                try:
                    contract_data = load_openapi_contract(contract_file)
                    contract_index.endpoints_count = count_endpoints(contract_data)
                    contract_index.checksum = hashlib.sha256(contract_file.read_bytes()).hexdigest()
                except Exception:
                    contract_index.endpoints_count = 0
                    contract_index.checksum = None
            return

    # Create new contract index entry
    endpoints_count = 0
    checksum = None
    if contract_file.exists():
        try:
            contract_data = load_openapi_contract(contract_file)
            endpoints_count = count_endpoints(contract_data)
            checksum = hashlib.sha256(contract_file.read_bytes()).hexdigest()
        except Exception:
            pass

    contract_index = ContractIndex(
        feature_key=feature_key,
        contract_file=contract_path,
        status=ContractStatus.DRAFT,
        checksum=checksum,
        endpoints_count=endpoints_count,
        coverage=0.0,
    )
    bundle.manifest.contracts.append(contract_index)


@app.command("validate")
@beartype
@require(lambda repo: isinstance(repo, Path), "Repository path must be Path")
@ensure(lambda result: result is None, "Must return None")
def validate_contract(
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
        help="Project bundle name (e.g., legacy-api). If not specified, attempts to auto-detect or prompt.",
    ),
    feature: str | None = typer.Option(
        None,
        "--feature",
        help="Feature key (e.g., FEATURE-001). If not specified, validates all contracts in bundle.",
    ),
    # Behavior/Options
    no_interactive: bool = typer.Option(
        False,
        "--no-interactive",
        help="Non-interactive mode (for CI/CD automation). Default: False (interactive mode)",
    ),
) -> None:
    """
    Validate OpenAPI contract schema.

    Validates OpenAPI schema structure (supports both 3.0.x and 3.1.x).
    For comprehensive validation including Specmatic, use 'specfact spec validate'.

    Note: Accepts both OpenAPI 3.0.x and 3.1.x for forward compatibility.
    Specmatic currently supports 3.0.x; 3.1.x support is planned.

    **Parameter Groups:**
    - **Target/Input**: --repo, --bundle, --feature
    - **Behavior/Options**: --no-interactive

    **Examples:**
        specfact contract validate --bundle legacy-api --feature FEATURE-001
        specfact contract validate --bundle legacy-api  # Validates all contracts
    """
    # Get bundle name
    if bundle is None:
        bundle = SpecFactStructure.get_active_bundle_name(repo)
        if bundle is None and not no_interactive:
            # Interactive selection
            from rich.prompt import Prompt

            plans = SpecFactStructure.list_plans(repo)
            if not plans:
                print_error("No project bundles found")
                raise typer.Exit(1)
            bundle_names = [str(p["name"]) for p in plans if p.get("name")]
            if not bundle_names:
                print_error("No valid bundle names found")
                raise typer.Exit(1)
            bundle = Prompt.ask("Select bundle", choices=bundle_names)
        elif bundle is None:
            print_error("Bundle not specified and no active bundle found")
            raise typer.Exit(1)

    # Ensure bundle is not None
    if bundle is None:
        print_error("Bundle not specified")
        raise typer.Exit(1)

    # Get bundle directory
    bundle_dir = SpecFactStructure.project_dir(base_path=repo, bundle_name=bundle)
    if not bundle_dir.exists():
        print_error(f"Project bundle not found: {bundle_dir}")
        raise typer.Exit(1)

    bundle_obj = load_project_bundle(bundle_dir)

    # Determine which contracts to validate
    contracts_to_validate: list[tuple[str, Path]] = []

    if feature:
        # Validate specific feature contract
        if feature not in bundle_obj.features:
            print_error(f"Feature '{feature}' not found in bundle")
            raise typer.Exit(1)

        feature_obj = bundle_obj.features[feature]
        if not feature_obj.contract:
            print_error(f"Feature '{feature}' has no contract")
            raise typer.Exit(1)

        contract_path = bundle_dir / feature_obj.contract
        if not contract_path.exists():
            print_error(f"Contract file not found: {contract_path}")
            raise typer.Exit(1)

        contracts_to_validate = [(feature, contract_path)]
    else:
        # Validate all contracts
        for feature_key, feature_obj in bundle_obj.features.items():
            if feature_obj.contract:
                contract_path = bundle_dir / feature_obj.contract
                if contract_path.exists():
                    contracts_to_validate.append((feature_key, contract_path))

    if not contracts_to_validate:
        print_warning("No contracts found to validate")
        raise typer.Exit(0)

    # Validate contracts
    table = Table(title="Contract Validation Results")
    table.add_column("Feature", style="cyan")
    table.add_column("Contract File", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("Endpoints", style="yellow")

    all_valid = True
    for feature_key, contract_path in contracts_to_validate:
        try:
            contract_data = load_openapi_contract(contract_path)
            is_valid = validate_openapi_schema(contract_data)
            endpoint_count = count_endpoints(contract_data)

            if is_valid:
                status = "✓ Valid"
                table.add_row(feature_key, contract_path.name, status, str(endpoint_count))
            else:
                status = "✗ Invalid"
                table.add_row(feature_key, contract_path.name, status, "0")
                all_valid = False
        except Exception as e:
            status = f"✗ Error: {e}"
            table.add_row(feature_key, contract_path.name, status, "0")
            all_valid = False

    console.print(table)

    if not all_valid:
        print_error("Some contracts failed validation")
        raise typer.Exit(1)

    print_success("All contracts validated successfully")


@app.command("coverage")
@beartype
@require(lambda repo: isinstance(repo, Path), "Repository path must be Path")
@ensure(lambda result: result is None, "Must return None")
def contract_coverage(
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
        help="Project bundle name (e.g., legacy-api). If not specified, attempts to auto-detect or prompt.",
    ),
    # Behavior/Options
    no_interactive: bool = typer.Option(
        False,
        "--no-interactive",
        help="Non-interactive mode (for CI/CD automation). Default: False (interactive mode)",
    ),
) -> None:
    """
    Calculate contract coverage for a project bundle.

    Shows which features have contracts and calculates coverage metrics.

    **Parameter Groups:**
    - **Target/Input**: --repo, --bundle
    - **Behavior/Options**: --no-interactive

    **Examples:**
        specfact contract coverage --bundle legacy-api
    """
    # Get bundle name
    if bundle is None:
        bundle = SpecFactStructure.get_active_bundle_name(repo)
        if bundle is None and not no_interactive:
            # Interactive selection
            from rich.prompt import Prompt

            plans = SpecFactStructure.list_plans(repo)
            if not plans:
                print_error("No project bundles found")
                raise typer.Exit(1)
            bundle_names = [str(p["name"]) for p in plans if p.get("name")]
            if not bundle_names:
                print_error("No valid bundle names found")
                raise typer.Exit(1)
            bundle = Prompt.ask("Select bundle", choices=bundle_names)
        elif bundle is None:
            print_error("Bundle not specified and no active bundle found")
            raise typer.Exit(1)

    # Ensure bundle is not None
    if bundle is None:
        print_error("Bundle not specified")
        raise typer.Exit(1)

    # Get bundle directory
    bundle_dir = SpecFactStructure.project_dir(base_path=repo, bundle_name=bundle)
    if not bundle_dir.exists():
        print_error(f"Project bundle not found: {bundle_dir}")
        raise typer.Exit(1)

    bundle_obj = load_project_bundle(bundle_dir)

    # Calculate coverage
    total_features = len(bundle_obj.features)
    features_with_contracts = 0
    total_endpoints = 0

    table = Table(title="Contract Coverage")
    table.add_column("Feature", style="cyan")
    table.add_column("Contract", style="magenta")
    table.add_column("Endpoints", style="yellow")
    table.add_column("Status", style="green")

    for feature_key, feature_obj in bundle_obj.features.items():
        if feature_obj.contract:
            contract_path = bundle_dir / feature_obj.contract
            if contract_path.exists():
                try:
                    contract_data = load_openapi_contract(contract_path)
                    endpoint_count = count_endpoints(contract_data)
                    total_endpoints += endpoint_count
                    features_with_contracts += 1
                    table.add_row(feature_key, contract_path.name, str(endpoint_count), "✓")
                except Exception as e:
                    table.add_row(feature_key, contract_path.name, "0", f"✗ Error: {e}")
            else:
                table.add_row(feature_key, feature_obj.contract, "0", "✗ File not found")
        else:
            table.add_row(feature_key, "-", "0", "✗ No contract")

    console.print(table)

    # Calculate coverage percentage
    coverage_percent = (features_with_contracts / total_features * 100) if total_features > 0 else 0.0

    console.print("\n[bold]Coverage Summary:[/bold]")
    console.print(f"  Features with contracts: {features_with_contracts}/{total_features} ({coverage_percent:.1f}%)")
    console.print(f"  Total API endpoints: {total_endpoints}")

    if coverage_percent < 100.0:
        print_warning(f"Coverage is {coverage_percent:.1f}% - some features are missing contracts")
    else:
        print_success("All features have contracts (100% coverage)")


@app.command("serve")
@beartype
@require(lambda repo: isinstance(repo, Path), "Repository path must be Path")
@ensure(lambda result: result is None, "Must return None")
def serve_contract(
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
        help="Project bundle name (e.g., legacy-api). If not specified, attempts to auto-detect or prompt.",
    ),
    feature: str | None = typer.Option(
        None,
        "--feature",
        help="Feature key (e.g., FEATURE-001). If not specified, prompts for selection.",
    ),
    # Behavior/Options
    port: int = typer.Option(9000, "--port", help="Port number for mock server (default: 9000)"),
    strict: bool = typer.Option(
        True,
        "--strict/--examples",
        help="Use strict validation mode (default: strict)",
    ),
    no_interactive: bool = typer.Option(
        False,
        "--no-interactive",
        help="Non-interactive mode (for CI/CD automation). Default: False (interactive mode)",
    ),
) -> None:
    """
    Start mock server for OpenAPI contract.

    Launches a Specmatic mock server that serves API endpoints based on the
    OpenAPI contract. Useful for frontend development and testing without a
    running backend.

    **Parameter Groups:**
    - **Target/Input**: --repo, --bundle, --feature
    - **Behavior/Options**: --port, --strict/--examples, --no-interactive

    **Examples:**
        specfact contract serve --bundle legacy-api --feature FEATURE-001
        specfact contract serve --bundle legacy-api --feature FEATURE-001 --port 8080
        specfact contract serve --bundle legacy-api --feature FEATURE-001 --examples
    """
    from specfact_cli.integrations.specmatic import check_specmatic_available, create_mock_server

    # Get bundle name
    if bundle is None:
        bundle = SpecFactStructure.get_active_bundle_name(repo)
        if bundle is None and not no_interactive:
            from rich.prompt import Prompt

            plans = SpecFactStructure.list_plans(repo)
            if not plans:
                print_error("No project bundles found")
                raise typer.Exit(1)
            bundle_names = [str(p["name"]) for p in plans if p.get("name")]
            if not bundle_names:
                print_error("No valid bundle names found")
                raise typer.Exit(1)
            bundle = Prompt.ask("Select bundle", choices=bundle_names)
        elif bundle is None:
            print_error("Bundle not specified and no active bundle found")
            raise typer.Exit(1)

    # Ensure bundle is not None
    if bundle is None:
        print_error("Bundle not specified")
        raise typer.Exit(1)

    # Get bundle directory
    bundle_dir = SpecFactStructure.project_dir(base_path=repo, bundle_name=bundle)
    if not bundle_dir.exists():
        print_error(f"Project bundle not found: {bundle_dir}")
        raise typer.Exit(1)

    bundle_obj = load_project_bundle(bundle_dir)

    # Get feature contract
    if feature:
        if feature not in bundle_obj.features:
            print_error(f"Feature '{feature}' not found in bundle")
            raise typer.Exit(1)
        feature_obj = bundle_obj.features[feature]
        if not feature_obj.contract:
            print_error(f"Feature '{feature}' has no contract")
            raise typer.Exit(1)
        contract_path = bundle_dir / feature_obj.contract
        if not contract_path.exists():
            print_error(f"Contract file not found: {contract_path}")
            raise typer.Exit(1)
    else:
        # Find features with contracts
        features_with_contracts = [(key, obj) for key, obj in bundle_obj.features.items() if obj.contract]
        if not features_with_contracts:
            print_error("No features with contracts found in bundle")
            raise typer.Exit(1)

        if len(features_with_contracts) == 1:
            # Only one contract, use it
            feature, feature_obj = features_with_contracts[0]
            if not feature_obj.contract:
                print_error(f"Feature '{feature}' has no contract")
                raise typer.Exit(1)
            contract_path = bundle_dir / feature_obj.contract
        elif no_interactive:
            # Non-interactive mode, use first contract
            feature, feature_obj = features_with_contracts[0]
            if not feature_obj.contract:
                print_error(f"Feature '{feature}' has no contract")
                raise typer.Exit(1)
            contract_path = bundle_dir / feature_obj.contract
        else:
            # Interactive selection
            from rich.prompt import Prompt

            feature_choices = [f"{key}: {obj.title}" for key, obj in features_with_contracts]
            selected = Prompt.ask("Select feature contract", choices=feature_choices)
            feature = selected.split(":")[0]
            feature_obj = bundle_obj.features[feature]
            if not feature_obj.contract:
                print_error(f"Feature '{feature}' has no contract")
                raise typer.Exit(1)
            contract_path = bundle_dir / feature_obj.contract

    # Check if Specmatic is available
    is_available, error_msg = check_specmatic_available()
    if not is_available:
        print_error(f"Specmatic not available: {error_msg}")
        print_info("Install Specmatic: npm install -g @specmatic/specmatic")
        raise typer.Exit(1)

    # Start mock server
    console.print("[bold cyan]Starting mock server...[/bold cyan]")
    console.print(f"  Feature: {feature}")
    console.print(f"  Contract: {contract_path.relative_to(repo)}")
    console.print(f"  Port: {port}")
    console.print(f"  Mode: {'strict' if strict else 'examples'}")

    import asyncio

    try:
        mock_server = asyncio.run(create_mock_server(contract_path, port=port, strict_mode=strict))
        print_success(f"✓ Mock server started at http://localhost:{port}")
        console.print("\n[bold]Available endpoints:[/bold]")
        console.print(f"  Try: curl http://localhost:{port}/actuator/health")
        console.print("\n[yellow]Press Ctrl+C to stop the server[/yellow]")

        # Keep running until interrupted
        try:
            import time

            while mock_server.is_running():
                time.sleep(1)
        except KeyboardInterrupt:
            console.print("\n[yellow]Stopping mock server...[/yellow]")
            mock_server.stop()
            print_success("✓ Mock server stopped")
    except Exception as e:
        print_error(f"✗ Failed to start mock server: {e!s}")
        raise typer.Exit(1) from e


@app.command("test")
@beartype
@require(lambda repo: isinstance(repo, Path), "Repository path must be Path")
@ensure(lambda result: result is None, "Must return None")
def test_contract(
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
        help="Project bundle name (e.g., legacy-api). If not specified, attempts to auto-detect or prompt.",
    ),
    feature: str | None = typer.Option(
        None,
        "--feature",
        help="Feature key (e.g., FEATURE-001). If not specified, generates tests for all contracts in bundle.",
    ),
    # Output/Results
    output_dir: Path | None = typer.Option(
        None,
        "--output",
        "--out",
        help="Output directory for generated tests (default: bundle-specific .specfact/projects/<bundle-name>/tests/contracts/)",
    ),
    # Behavior/Options
    no_interactive: bool = typer.Option(
        False,
        "--no-interactive",
        help="Non-interactive mode (for CI/CD automation). Default: False (interactive mode)",
    ),
) -> None:
    """
    Generate contract tests from OpenAPI contract.

    Generates test files from the OpenAPI contract that can be used to validate
    API implementations. Can generate tests for a specific feature contract or
    all contracts in a bundle.

    **Parameter Groups:**
    - **Target/Input**: --repo, --bundle, --feature
    - **Output/Results**: --output
    - **Behavior/Options**: --no-interactive

    **Examples:**
        specfact contract test --bundle legacy-api --feature FEATURE-001
        specfact contract test --bundle legacy-api  # Generates tests for all contracts
        specfact contract test --bundle legacy-api --output tests/contracts/
    """
    from specfact_cli.integrations.specmatic import check_specmatic_available

    # Get bundle name
    if bundle is None:
        bundle = SpecFactStructure.get_active_bundle_name(repo)
        if bundle is None and not no_interactive:
            from rich.prompt import Prompt

            plans = SpecFactStructure.list_plans(repo)
            if not plans:
                print_error("No project bundles found")
                raise typer.Exit(1)
            bundle_names = [str(p["name"]) for p in plans if p.get("name")]
            if not bundle_names:
                print_error("No valid bundle names found")
                raise typer.Exit(1)
            bundle = Prompt.ask("Select bundle", choices=bundle_names)
        elif bundle is None:
            print_error("Bundle not specified and no active bundle found")
            raise typer.Exit(1)

    # Ensure bundle is not None
    if bundle is None:
        print_error("Bundle not specified")
        raise typer.Exit(1)

    # Get bundle directory
    bundle_dir = SpecFactStructure.project_dir(base_path=repo, bundle_name=bundle)
    if not bundle_dir.exists():
        print_error(f"Project bundle not found: {bundle_dir}")
        raise typer.Exit(1)

    bundle_obj = load_project_bundle(bundle_dir)

    # Determine output directory
    if output_dir is None:
        output_dir = bundle_dir / "tests" / "contracts"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Check if Specmatic is available
    is_available, error_msg = check_specmatic_available()
    if not is_available:
        print_error(f"Specmatic not available: {error_msg}")
        print_info("Install Specmatic: npm install -g @specmatic/specmatic")
        raise typer.Exit(1)

    # Determine which contracts to generate tests for
    contracts_to_test: list[tuple[str, Path]] = []

    if feature:
        # Generate tests for specific feature contract
        if feature not in bundle_obj.features:
            print_error(f"Feature '{feature}' not found in bundle")
            raise typer.Exit(1)
        feature_obj = bundle_obj.features[feature]
        if not feature_obj.contract:
            print_error(f"Feature '{feature}' has no contract")
            raise typer.Exit(1)
        contract_path = bundle_dir / feature_obj.contract
        if not contract_path.exists():
            print_error(f"Contract file not found: {contract_path}")
            raise typer.Exit(1)
        contracts_to_test = [(feature, contract_path)]
    else:
        # Generate tests for all contracts
        for feature_key, feature_obj in bundle_obj.features.items():
            if feature_obj.contract:
                contract_path = bundle_dir / feature_obj.contract
                if contract_path.exists():
                    contracts_to_test.append((feature_key, contract_path))

    if not contracts_to_test:
        print_warning("No contracts found to generate tests for")
        raise typer.Exit(0)

    # Generate tests using Specmatic
    console.print("[bold cyan]Generating contract tests...[/bold cyan]")
    console.print(f"  Output directory: {output_dir.relative_to(repo)}")
    console.print(f"  Contracts: {len(contracts_to_test)}")

    import asyncio

    from specfact_cli.integrations.specmatic import generate_specmatic_tests

    generated_count = 0
    failed_count = 0

    for feature_key, contract_path in contracts_to_test:
        try:
            # Create feature-specific output directory
            feature_output_dir = output_dir / feature_key.lower()
            feature_output_dir.mkdir(parents=True, exist_ok=True)

            # Generate tests
            test_dir = asyncio.run(generate_specmatic_tests(contract_path, feature_output_dir))
            generated_count += 1
            console.print(f"  ✓ Generated tests for {feature_key}: {test_dir.relative_to(repo)}")
        except Exception as e:
            failed_count += 1
            console.print(f"  ✗ Failed to generate tests for {feature_key}: {e!s}")

    if generated_count > 0:
        print_success(f"Generated {generated_count} test suite(s)")
    if failed_count > 0:
        print_warning(f"Failed to generate {failed_count} test suite(s)")
        raise typer.Exit(1)

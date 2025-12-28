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
from specfact_cli.telemetry import telemetry
from specfact_cli.utils import print_error, print_info, print_section, print_success, print_warning
from specfact_cli.utils.progress import load_bundle_with_progress, save_bundle_with_progress
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
    force: bool = typer.Option(
        False,
        "--force",
        help="Overwrite existing contract file without prompting (useful for updating contracts)",
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
    - **Behavior/Options**: --no-interactive, --force

    **Examples:**
        specfact contract init --bundle legacy-api --feature FEATURE-001
        specfact contract init --bundle legacy-api --feature FEATURE-001 --title "Authentication API" --version 1.0.0
        specfact contract init --bundle legacy-api --feature FEATURE-001 --force --no-interactive
    """
    telemetry_metadata = {
        "bundle": bundle,
        "feature": feature,
        "title": title,
        "version": version,
    }

    with telemetry.track_command("contract.init", telemetry_metadata) as record:
        print_section("SpecFact CLI - OpenAPI Contract Initialization")

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

        bundle_obj = load_bundle_with_progress(bundle_dir, validate_hashes=False, console_instance=console)

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
            if force:
                print_warning(f"Overwriting existing contract file: {contract_file}")
            else:
                print_warning(f"Contract file already exists: {contract_file}")
                if not no_interactive:
                    overwrite = typer.confirm("Overwrite existing contract?")
                    if not overwrite:
                        raise typer.Exit(0)
                else:
                    print_error("Use --force to overwrite existing contract in non-interactive mode")
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
        save_bundle_with_progress(bundle_obj, bundle_dir, atomic=True, console_instance=console)
        print_success(f"Initialized OpenAPI contract for {feature}: {contract_file}")

        record({"feature": feature, "contract_file": str(contract_file)})


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
    telemetry_metadata = {
        "bundle": bundle,
        "feature": feature,
    }

    with telemetry.track_command("contract.validate", telemetry_metadata) as record:
        print_section("SpecFact CLI - OpenAPI Contract Validation")

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

        bundle_obj = load_bundle_with_progress(bundle_dir, validate_hashes=False, console_instance=console)

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
            record({"valid": False, "contracts_count": len(contracts_to_validate)})
            raise typer.Exit(1)

        print_success("All contracts validated successfully")
        record({"valid": True, "contracts_count": len(contracts_to_validate)})


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
    telemetry_metadata = {
        "bundle": bundle,
    }

    with telemetry.track_command("contract.coverage", telemetry_metadata) as record:
        print_section("SpecFact CLI - OpenAPI Contract Coverage")

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

        bundle_obj = load_bundle_with_progress(bundle_dir, validate_hashes=False, console_instance=console)

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
        console.print(
            f"  Features with contracts: {features_with_contracts}/{total_features} ({coverage_percent:.1f}%)"
        )
        console.print(f"  Total API endpoints: {total_endpoints}")

        if coverage_percent < 100.0:
            print_warning(f"Coverage is {coverage_percent:.1f}% - some features are missing contracts")
        else:
            print_success("All features have contracts (100% coverage)")

        record(
            {
                "total_features": total_features,
                "features_with_contracts": features_with_contracts,
                "coverage_percent": coverage_percent,
                "total_endpoints": total_endpoints,
            }
        )


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
    telemetry_metadata = {
        "bundle": bundle,
        "feature": feature,
        "port": port,
        "strict": strict,
    }

    with telemetry.track_command("contract.serve", telemetry_metadata):
        from specfact_cli.integrations.specmatic import check_specmatic_available, create_mock_server

        print_section("SpecFact CLI - OpenAPI Contract Mock Server")

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

        bundle_obj = load_bundle_with_progress(bundle_dir, validate_hashes=False, console_instance=console)

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
        # Resolve repo to absolute path for relative_to() to work
        repo_resolved = repo.resolve()
        try:
            contract_path_display = contract_path.relative_to(repo_resolved)
        except ValueError:
            # If contract_path is not a subpath of repo, show absolute path
            contract_path_display = contract_path
        console.print(f"  Contract: {contract_path_display}")
        console.print(f"  Port: {port}")
        console.print(f"  Mode: {'strict' if strict else 'examples'}")

        import asyncio

        console.print("[dim]Starting mock server (this may take a few seconds)...[/dim]")
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


@app.command("verify")
@beartype
@require(lambda repo: isinstance(repo, Path), "Repository path must be Path")
@ensure(lambda result: result is None, "Must return None")
def verify_contract(
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
        help="Feature key (e.g., FEATURE-001). If not specified, verifies all contracts in bundle.",
    ),
    # Behavior/Options
    port: int = typer.Option(9000, "--port", help="Port number for mock server (default: 9000)"),
    skip_mock: bool = typer.Option(
        False,
        "--skip-mock",
        help="Skip mock server startup (only validate contract)",
    ),
    no_interactive: bool = typer.Option(
        False,
        "--no-interactive",
        help="Non-interactive mode (for CI/CD automation). Default: False (interactive mode)",
    ),
) -> None:
    """
    Verify OpenAPI contract - validate, generate examples, and test mock server.

    This is a convenience command that combines multiple steps:
    1. Validates the contract schema
    2. Generates examples from the contract
    3. Starts a mock server (optional)
    4. Runs basic connectivity tests

    Perfect for verifying contracts work correctly without a real API implementation.

    **Parameter Groups:**
    - **Target/Input**: --repo, --bundle, --feature
    - **Behavior/Options**: --port, --skip-mock, --no-interactive

    **Examples:**
        # Verify a specific contract
        specfact contract verify --bundle my-api --feature FEATURE-001

        # Verify all contracts in a bundle
        specfact contract verify --bundle my-api

        # Verify without starting mock server (CI/CD)
        specfact contract verify --bundle my-api --feature FEATURE-001 --skip-mock --no-interactive
    """
    telemetry_metadata = {
        "bundle": bundle,
        "feature": feature,
        "port": port,
        "skip_mock": skip_mock,
    }

    with telemetry.track_command("contract.verify", telemetry_metadata) as record:
        from specfact_cli.integrations.specmatic import (
            check_specmatic_available,
            create_mock_server,
            generate_specmatic_examples,
        )

        print_section("SpecFact CLI - OpenAPI Contract Verification")

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

        bundle_obj = load_bundle_with_progress(bundle_dir, validate_hashes=False, console_instance=console)

        # Determine which contracts to verify
        contracts_to_verify: list[tuple[str, Path]] = []
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
            contracts_to_verify = [(feature, contract_path)]
        else:
            # Verify all contracts in bundle
            for feat_key, feat_obj in bundle_obj.features.items():
                if feat_obj.contract:
                    contract_path = bundle_dir / feat_obj.contract
                    if contract_path.exists():
                        contracts_to_verify.append((feat_key, contract_path))

        if not contracts_to_verify:
            print_error("No contracts found to verify")
            raise typer.Exit(1)

        # Check if Specmatic is available
        is_available, error_msg = check_specmatic_available()
        if not is_available:
            print_error(f"Specmatic not available: {error_msg}")
            print_info("Install Specmatic: npm install -g @specmatic/specmatic")
            raise typer.Exit(1)

        # Step 1: Validate contracts
        console.print("\n[bold cyan]Step 1: Validating contracts...[/bold cyan]")
        validation_errors = []
        for feat_key, contract_path in contracts_to_verify:
            try:
                contract_data = load_openapi_contract(contract_path)
                is_valid = validate_openapi_schema(contract_data)
                if is_valid:
                    endpoints = count_endpoints(contract_data)
                    print_success(f"✓ {feat_key}: Valid ({endpoints} endpoints)")
                else:
                    print_error(f"✗ {feat_key}: Invalid schema")
                    validation_errors.append(f"{feat_key}: Schema validation failed")
            except Exception as e:
                print_error(f"✗ {feat_key}: Error - {e!s}")
                validation_errors.append(f"{feat_key}: {e!s}")

        if validation_errors:
            console.print("\n[bold red]Validation Errors:[/bold red]")
            for error in validation_errors[:10]:  # Show first 10 errors
                console.print(f"  • {error}")
            if len(validation_errors) > 10:
                console.print(f"  ... and {len(validation_errors) - 10} more errors")
            record({"validation_errors": len(validation_errors), "validated": False})
            raise typer.Exit(1)

        record({"validated": True, "contracts_count": len(contracts_to_verify)})

        # Step 2: Generate examples
        console.print("\n[bold cyan]Step 2: Generating examples...[/bold cyan]")
        import asyncio

        examples_generated = 0
        for feat_key, contract_path in contracts_to_verify:
            try:
                examples_dir = asyncio.run(generate_specmatic_examples(contract_path))
                if examples_dir.exists() and any(examples_dir.iterdir()):
                    examples_generated += 1
                    print_success(f"✓ {feat_key}: Examples generated")
                else:
                    print_warning(f"⚠ {feat_key}: No examples generated (schema may not have examples)")
            except Exception as e:
                print_warning(f"⚠ {feat_key}: Example generation failed - {e!s}")

        record({"examples_generated": examples_generated})

        # Step 3: Start mock server and test (if not skipped)
        if not skip_mock:
            if len(contracts_to_verify) > 1:
                console.print(
                    f"\n[yellow]Note: Multiple contracts found. Starting mock server for first contract: {contracts_to_verify[0][0]}[/yellow]"
                )

            feat_key, contract_path = contracts_to_verify[0]
            console.print(f"\n[bold cyan]Step 3: Starting mock server for {feat_key}...[/bold cyan]")

            try:
                mock_server = asyncio.run(create_mock_server(contract_path, port=port, strict_mode=False))
                print_success(f"✓ Mock server started at http://localhost:{port}")

                # Step 4: Run basic connectivity test
                console.print("\n[bold cyan]Step 4: Testing connectivity...[/bold cyan]")
                try:
                    import requests

                    # Test health endpoint
                    health_url = f"http://localhost:{port}/actuator/health"
                    response = requests.get(health_url, timeout=5)
                    if response.status_code == 200:
                        print_success(f"✓ Health check passed: {response.json().get('status', 'OK')}")
                        record({"health_check": True})
                    else:
                        print_warning(f"⚠ Health check returned: {response.status_code}")
                        record({"health_check": False, "health_status": response.status_code})
                except ImportError:
                    print_warning("⚠ 'requests' library not available - skipping connectivity test")
                    record({"health_check": None})
                except Exception as e:
                    print_warning(f"⚠ Connectivity test failed: {e!s}")
                    record({"health_check": False, "health_error": str(e)})

                # Summary
                console.print("\n[bold green]✓ Contract verification complete![/bold green]")
                console.print("\n[bold]Summary:[/bold]")
                console.print(f"  • Contracts validated: {len(contracts_to_verify)}")
                console.print(f"  • Examples generated: {examples_generated}")
                console.print(f"  • Mock server: http://localhost:{port}")
                console.print("\n[yellow]Press Ctrl+C to stop the mock server[/yellow]")

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
                record({"mock_server": False, "mock_error": str(e)})
                raise typer.Exit(1) from e
        else:
            # Summary without mock server
            console.print("\n[bold green]✓ Contract verification complete![/bold green]")
            console.print("\n[bold]Summary:[/bold]")
            console.print(f"  • Contracts validated: {len(contracts_to_verify)}")
            console.print(f"  • Examples generated: {examples_generated}")
            console.print("  • Mock server: Skipped (--skip-mock)")
            record({"mock_server": False, "skipped": True})


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
    Generate contract tests and examples from OpenAPI contract.

    **IMPORTANT**: This command generates test files and examples, but running the tests
    requires a REAL API implementation. The generated tests validate that your API
    matches the contract - they cannot test the contract itself.

    **What this command does:**
    1. Generates example request/response files from the contract schema
    2. Generates test files that can validate API implementations
    3. Prepares everything needed for contract testing

    **What you can do WITHOUT a real API:**
    - ✅ Validate contract schema: `specfact contract validate`
    - ✅ Start mock server: `specfact contract serve --examples`
    - ✅ Generate examples: This command does this automatically

    **What REQUIRES a real API:**
    - ❌ Running contract tests: `specmatic test --host <api-url>`

    **Parameter Groups:**
    - **Target/Input**: --repo, --bundle, --feature
    - **Output/Results**: --output
    - **Behavior/Options**: --no-interactive

    **Examples:**
        specfact contract test --bundle legacy-api --feature FEATURE-001
        specfact contract test --bundle legacy-api  # Generates tests for all contracts
        specfact contract test --bundle legacy-api --output tests/contracts/

    **See**: [Contract Testing Workflow](../guides/contract-testing-workflow.md) for details.
    """
    telemetry_metadata = {
        "bundle": bundle,
        "feature": feature,
    }

    with telemetry.track_command("contract.test", telemetry_metadata) as record:
        from specfact_cli.integrations.specmatic import check_specmatic_available

        print_section("SpecFact CLI - OpenAPI Contract Test Generation")

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

        bundle_obj = load_bundle_with_progress(bundle_dir, validate_hashes=False, console_instance=console)

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

        # Check if Specmatic is available (after checking contracts exist)
        is_available, error_msg = check_specmatic_available()
        if not is_available:
            print_error(f"Specmatic not available: {error_msg}")
            print_info("Install Specmatic: npm install -g @specmatic/specmatic")
            raise typer.Exit(1)

        # Determine output directory (set default if not provided)
        if output_dir is None:
            output_dir = bundle_dir / "tests" / "contracts"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate tests using Specmatic
        console.print("[bold cyan]Generating contract tests...[/bold cyan]")
        # Resolve repo to absolute path for relative_to() to work
        repo_resolved = repo.resolve()
        try:
            output_dir_display = output_dir.relative_to(repo_resolved)
        except ValueError:
            # If output_dir is not a subpath of repo, show absolute path
            output_dir_display = output_dir
        console.print(f"  Output directory: {output_dir_display}")
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

                # Step 1: Generate examples from contract (required for mock server and tests)
                from specfact_cli.integrations.specmatic import generate_specmatic_examples

                examples_dir = contract_path.parent / f"{contract_path.stem}_examples"
                console.print(f"  [dim]Generating examples for {feature_key}...[/dim]")
                try:
                    asyncio.run(generate_specmatic_examples(contract_path, examples_dir))
                    console.print(f"  [dim]✓ Examples generated: {examples_dir.name}[/dim]")
                except Exception as e:
                    # Examples generation is optional - continue even if it fails
                    console.print(f"  [yellow]⚠ Examples generation skipped: {e!s}[/yellow]")

                # Step 2: Generate tests (uses examples if available)
                test_dir = asyncio.run(generate_specmatic_tests(contract_path, feature_output_dir))
                generated_count += 1
                try:
                    test_dir_display = test_dir.relative_to(repo_resolved)
                except ValueError:
                    # If test_dir is not a subpath of repo, show absolute path
                    test_dir_display = test_dir
                console.print(f"  ✓ Generated tests for {feature_key}: {test_dir_display}")
            except Exception as e:
                failed_count += 1
                console.print(f"  ✗ Failed to generate tests for {feature_key}: {e!s}")

        if generated_count > 0:
            print_success(f"Generated {generated_count} test suite(s)")
        if failed_count > 0:
            print_warning(f"Failed to generate {failed_count} test suite(s)")
            record({"generated": generated_count, "failed": failed_count})
            raise typer.Exit(1)

        record({"generated": generated_count, "failed": failed_count})

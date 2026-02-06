"""
Spec command - Specmatic integration for API contract testing.

This module provides commands for validating OpenAPI/AsyncAPI specifications,
checking backward compatibility, generating test suites, and running mock servers
using Specmatic.
"""

from __future__ import annotations

import hashlib
import json
from contextlib import suppress
from pathlib import Path
from typing import Any

import typer
from beartype import beartype
from icontract import ensure, require
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

from specfact_cli.integrations.specmatic import (
    check_backward_compatibility,
    check_specmatic_available,
    create_mock_server,
    generate_specmatic_tests,
    validate_spec_with_specmatic,
)
from specfact_cli.runtime import debug_log_operation, debug_print, is_debug_mode
from specfact_cli.utils import print_error, print_info, print_success, print_warning, prompt_text
from specfact_cli.utils.progress import load_bundle_with_progress
from specfact_cli.utils.structure import SpecFactStructure


app = typer.Typer(
    help="Specmatic integration for API contract testing (OpenAPI/AsyncAPI validation, backward compatibility, mock servers)"
)
console = Console()


@app.command("validate")
@beartype
@require(lambda spec_path: spec_path is None or spec_path.exists(), "Spec file must exist if provided")
@ensure(lambda result: result is None, "Must return None")
def validate(
    # Target/Input
    spec_path: Path | None = typer.Argument(
        None,
        help="Path to OpenAPI/AsyncAPI specification file (optional if --bundle provided)",
        exists=True,
    ),
    bundle: str | None = typer.Option(
        None,
        "--bundle",
        help="Project bundle name (e.g., legacy-api). If provided, validates all contracts in bundle. Default: active plan from 'specfact plan select'",
    ),
    # Advanced
    previous_version: Path | None = typer.Option(
        None,
        "--previous",
        help="Path to previous version for backward compatibility check",
        exists=True,
        hidden=True,  # Hidden by default, shown with --help-advanced
    ),
    # Behavior/Options
    no_interactive: bool = typer.Option(
        False,
        "--no-interactive",
        help="Non-interactive mode (for CI/CD automation). Disables interactive prompts.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Force validation even if cached result exists (bypass cache).",
    ),
) -> None:
    """
    Validate OpenAPI/AsyncAPI specification using Specmatic.

    Runs comprehensive validation including:
    - Schema structure validation
    - Example generation test
    - Backward compatibility check (if previous version provided)

    Can validate a single contract file or all contracts in a project bundle.
    Uses active plan (from 'specfact plan select') as default if --bundle not provided.

    **Caching:**
    Validation results are cached in `.specfact/cache/specmatic-validation.json` based on
    file content hashes. Unchanged contracts are automatically skipped on subsequent runs
    to improve performance. Use --force to bypass cache and re-validate all contracts.

    **Parameter Groups:**
    - **Target/Input**: spec_path (optional if --bundle provided), --bundle
    - **Advanced**: --previous
    - **Behavior/Options**: --no-interactive, --force

    **Examples:**
        specfact spec validate api/openapi.yaml
        specfact spec validate api/openapi.yaml --previous api/openapi.v1.yaml
        specfact spec validate --bundle legacy-api
        specfact spec validate  # Interactive: select from active bundle contracts
        specfact spec validate --bundle legacy-api --force  # Bypass cache
    """
    from specfact_cli.telemetry import telemetry

    if is_debug_mode():
        debug_log_operation(
            "command",
            "spec validate",
            "started",
            extra={"spec_path": str(spec_path) if spec_path else None, "bundle": bundle},
        )
        debug_print("[dim]spec validate: started[/dim]")

    repo_path = Path(".").resolve()

    # Use active plan as default if bundle not provided
    if bundle is None:
        bundle = SpecFactStructure.get_active_bundle_name(repo_path)
        if bundle:
            console.print(f"[dim]Using active plan: {bundle}[/dim]")

    # Determine which contracts to validate
    spec_paths: list[Path] = []

    if spec_path:
        # Direct file path provided
        spec_paths = [spec_path]
    elif bundle:
        # Load all contracts from bundle
        bundle_dir = SpecFactStructure.project_dir(base_path=repo_path, bundle_name=bundle)
        if not bundle_dir.exists():
            if is_debug_mode():
                debug_log_operation(
                    "command",
                    "spec validate",
                    "failed",
                    error=f"Project bundle not found: {bundle_dir}",
                    extra={"reason": "bundle_not_found", "bundle": bundle},
                )
            print_error(f"Project bundle not found: {bundle_dir}")
            raise typer.Exit(1)

        project_bundle = load_bundle_with_progress(bundle_dir, validate_hashes=False, console_instance=console)

        for feature_key, feature in project_bundle.features.items():
            if feature.contract:
                contract_path = bundle_dir / feature.contract
                if contract_path.exists():
                    spec_paths.append(contract_path)
                else:
                    print_warning(f"Contract file not found for {feature_key}: {feature.contract}")

        if not spec_paths:
            print_error("No contract files found in bundle")
            raise typer.Exit(1)

        # If multiple contracts and not in non-interactive mode, show selection
        if len(spec_paths) > 1 and not no_interactive:
            console.print(f"\n[bold]Found {len(spec_paths)} contracts in bundle '{bundle}':[/bold]\n")
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("#", style="bold yellow", justify="right", width=4)
            table.add_column("Feature", style="bold", min_width=20)
            table.add_column("Contract Path", style="dim")

            for i, contract_path in enumerate(spec_paths, 1):
                # Find feature key for this contract
                feature_key = "Unknown"
                for fk, f in project_bundle.features.items():
                    if f.contract and (bundle_dir / f.contract) == contract_path:
                        feature_key = fk
                        break

                table.add_row(
                    str(i),
                    feature_key,
                    str(contract_path.relative_to(repo_path)),
                )

            console.print(table)
            console.print()

            selection = prompt_text(
                f"Select contract(s) to validate (1-{len(spec_paths)}, 'all', or 'q' to quit): "
            ).strip()

            if selection.lower() in ("q", "quit", ""):
                print_info("Validation cancelled")
                raise typer.Exit(0)

            if selection.lower() == "all":
                # Validate all contracts
                pass
            else:
                try:
                    indices = [int(x.strip()) for x in selection.split(",")]
                    if not all(1 <= idx <= len(spec_paths) for idx in indices):
                        print_error(f"Invalid selection. Must be between 1 and {len(spec_paths)}")
                        raise typer.Exit(1)
                    spec_paths = [spec_paths[idx - 1] for idx in indices]
                except ValueError:
                    print_error(f"Invalid input: {selection}. Please enter numbers separated by commas.")
                    raise typer.Exit(1) from None
    else:
        # No spec_path and no bundle - show error
        print_error("Either spec_path or --bundle must be provided")
        console.print("\n[bold]Options:[/bold]")
        console.print("  1. Provide a spec file: specfact spec validate api/openapi.yaml")
        console.print("  2. Use --bundle option: specfact spec validate --bundle legacy-api")
        console.print("  3. Set active plan first: specfact plan select")
        raise typer.Exit(1)

    if not spec_paths:
        print_error("No contracts to validate")
        raise typer.Exit(1)

    telemetry_metadata = {
        "spec_path": str(spec_path) if spec_path else None,
        "bundle": bundle,
        "contracts_count": len(spec_paths),
    }

    with telemetry.track_command("spec.validate", telemetry_metadata) as record:
        # Check if Specmatic is available
        is_available, error_msg = check_specmatic_available()
        if not is_available:
            if is_debug_mode():
                debug_log_operation(
                    "command",
                    "spec validate",
                    "failed",
                    error=error_msg or "Specmatic not available",
                    extra={"reason": "specmatic_unavailable"},
                )
            print_error(f"Specmatic not available: {error_msg}")
            console.print("\n[bold]Installation:[/bold]")
            console.print("Visit https://docs.specmatic.io/ for installation instructions")
            raise typer.Exit(1)

        import asyncio
        from datetime import UTC, datetime
        from time import time

        # Load validation cache
        cache_dir = repo_path / SpecFactStructure.CACHE
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / "specmatic-validation.json"
        validation_cache: dict[str, dict[str, Any]] = {}
        if cache_file.exists():
            try:
                validation_cache = json.loads(cache_file.read_text())
            except Exception:
                validation_cache = {}

        def compute_file_hash(file_path: Path) -> str:
            """Compute SHA256 hash of file content."""
            try:
                return hashlib.sha256(file_path.read_bytes()).hexdigest()
            except Exception:
                return ""

        validated_count = 0
        failed_count = 0
        skipped_count = 0
        total_count = len(spec_paths)

        for idx, contract_path in enumerate(spec_paths, 1):
            contract_relative = contract_path.relative_to(repo_path)
            contract_key = str(contract_relative)
            file_hash = compute_file_hash(contract_path) if contract_path.exists() else ""
            cache_entry = validation_cache.get(contract_key, {})

            # Check cache (only if no previous_version specified, as backward compat check can't be cached)
            use_cache = (
                not force
                and not previous_version
                and file_hash
                and cache_entry
                and cache_entry.get("hash") == file_hash
                and cache_entry.get("status") == "success"
                and cache_entry.get("is_valid") is True
            )

            if use_cache:
                console.print(
                    f"\n[dim][{idx}/{total_count}][/dim] [bold cyan]Validating specification:[/bold cyan] {contract_relative}"
                )
                console.print(
                    f"[dim]⏭️  Skipping (cache hit - unchanged since {cache_entry.get('timestamp', 'unknown')})[/dim]"
                )
                validated_count += 1
                skipped_count += 1
                continue

            console.print(
                f"\n[bold yellow][{idx}/{total_count}][/bold yellow] [bold cyan]Validating specification:[/bold cyan] {contract_relative}"
            )

            # Run validation with progress
            start_time = time()
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                TimeElapsedColumn(),
                console=console,
            ) as progress:
                task = progress.add_task("Running Specmatic validation...", total=None)
                result = asyncio.run(validate_spec_with_specmatic(contract_path, previous_version))
                elapsed = time() - start_time
                progress.update(task, description=f"✓ Validation complete ({elapsed:.2f}s)")

            # Display results
            table = Table(title=f"Validation Results: {contract_path.name}")
            table.add_column("Check", style="cyan")
            table.add_column("Status", style="magenta")
            table.add_column("Details", style="white")

            # Helper to format details with truncation
            def format_details(items: list[str], max_length: int = 100) -> str:
                """Format list of items, truncating if too long."""
                if not items:
                    return ""
                if len(items) == 1:
                    detail = items[0]
                    return detail[:max_length] + ("..." if len(detail) > max_length else "")
                # Multiple items: show first with count
                first = items[0][: max_length - 20]
                if len(first) < len(items[0]):
                    first += "..."
                return f"{first} (+{len(items) - 1} more)" if len(items) > 1 else first

            # Get errors for each check type
            schema_errors = [
                e
                for e in result.errors
                if "schema" in e.lower() or ("validate" in e.lower() and "example" not in e.lower())
            ]
            example_errors = [e for e in result.errors if "example" in e.lower()]
            compat_errors = [e for e in result.errors if "backward" in e.lower() or "compatibility" in e.lower()]

            # If we can't categorize, use all errors (fallback)
            if not schema_errors and not example_errors and not compat_errors and result.errors:
                # Distribute errors: first for schema, second for examples, rest for compat
                if len(result.errors) >= 1:
                    schema_errors = [result.errors[0]]
                if len(result.errors) >= 2:
                    example_errors = [result.errors[1]]
                if len(result.errors) > 2:
                    compat_errors = result.errors[2:]

            table.add_row(
                "Schema Validation",
                "✓ PASS" if result.schema_valid else "✗ FAIL",
                format_details(schema_errors) if not result.schema_valid else "",
            )

            table.add_row(
                "Example Generation",
                "✓ PASS" if result.examples_valid else "✗ FAIL",
                format_details(example_errors) if not result.examples_valid else "",
            )

            if previous_version:
                # For backward compatibility, show breaking changes if available, otherwise errors
                compat_details = result.breaking_changes if result.breaking_changes else compat_errors
                table.add_row(
                    "Backward Compatibility",
                    "✓ PASS" if result.backward_compatible else "✗ FAIL",
                    format_details(compat_details) if not result.backward_compatible else "",
                )

            console.print(table)

            # Show warnings if any
            if result.warnings:
                console.print("\n[bold yellow]Warnings:[/bold yellow]")
                for warning in result.warnings:
                    console.print(f"  ⚠ {warning}")

            # Show all errors in detail if validation failed
            if not result.is_valid and result.errors:
                console.print("\n[bold red]All Errors:[/bold red]")
                for i, error in enumerate(result.errors, 1):
                    console.print(f"  {i}. {error}")

            # Update cache (only if no previous_version, as backward compat can't be cached)
            if not previous_version and file_hash:
                validation_cache[contract_key] = {
                    "hash": file_hash,
                    "status": "success" if result.is_valid else "failure",
                    "is_valid": result.is_valid,
                    "schema_valid": result.schema_valid,
                    "examples_valid": result.examples_valid,
                    "timestamp": datetime.now(UTC).isoformat(),
                }
                # Save cache after each validation
                with suppress(Exception):  # Don't fail validation if cache write fails
                    cache_file.write_text(json.dumps(validation_cache, indent=2))

            if result.is_valid:
                print_success(f"✓ Specification is valid: {contract_path.name}")
                validated_count += 1
            else:
                print_error(f"✗ Specification validation failed: {contract_path.name}")
                if result.errors:
                    console.print("\n[bold]Errors:[/bold]")
                    for error in result.errors:
                        console.print(f"  - {error}")
                failed_count += 1

        if is_debug_mode():
            debug_log_operation(
                "command",
                "spec validate",
                "success",
                extra={"validated": validated_count, "skipped": skipped_count, "failed": failed_count},
            )
            debug_print("[dim]spec validate: success[/dim]")

        # Summary
        if len(spec_paths) > 1:
            console.print("\n[bold]Summary:[/bold]")
            console.print(f"  Validated: {validated_count}")
            if skipped_count > 0:
                console.print(f"  Skipped (cache): {skipped_count}")
            console.print(f"  Failed: {failed_count}")

        record({"validated": validated_count, "skipped": skipped_count, "failed": failed_count})

        if failed_count > 0:
            raise typer.Exit(1)


@app.command("backward-compat")
@beartype
@require(lambda old_spec: old_spec.exists(), "Old spec file must exist")
@require(lambda new_spec: new_spec.exists(), "New spec file must exist")
@ensure(lambda result: result is None, "Must return None")
def backward_compat(
    # Target/Input
    old_spec: Path = typer.Argument(..., help="Path to old specification version", exists=True),
    new_spec: Path = typer.Argument(..., help="Path to new specification version", exists=True),
) -> None:
    """
    Check backward compatibility between two spec versions.

    Compares the new specification against the old version to detect
    breaking changes that would affect existing consumers.

    **Parameter Groups:**
    - **Target/Input**: old_spec, new_spec (both required)

    **Examples:**
        specfact spec backward-compat api/openapi.v1.yaml api/openapi.v2.yaml
    """
    import asyncio

    from specfact_cli.telemetry import telemetry

    with telemetry.track_command("spec.backward-compat", {"old_spec": str(old_spec), "new_spec": str(new_spec)}):
        # Check if Specmatic is available
        is_available, error_msg = check_specmatic_available()
        if not is_available:
            print_error(f"Specmatic not available: {error_msg}")
            raise typer.Exit(1)

        console.print("[bold cyan]Checking backward compatibility...[/bold cyan]")
        console.print(f"  Old: {old_spec}")
        console.print(f"  New: {new_spec}")

        is_compatible, breaking_changes = asyncio.run(check_backward_compatibility(old_spec, new_spec))

        if is_compatible:
            print_success("✓ Specifications are backward compatible")
        else:
            print_error("✗ Backward compatibility check failed")
            if breaking_changes:
                console.print("\n[bold]Breaking Changes:[/bold]")
                for change in breaking_changes:
                    console.print(f"  - {change}")
            raise typer.Exit(1)


@app.command("generate-tests")
@beartype
@require(lambda spec_path: spec_path.exists() if spec_path else True, "Spec file must exist if provided")
@ensure(lambda result: result is None, "Must return None")
def generate_tests(
    # Target/Input
    spec_path: Path | None = typer.Argument(
        None, help="Path to OpenAPI/AsyncAPI specification (optional if --bundle provided)", exists=True
    ),
    bundle: str | None = typer.Option(
        None,
        "--bundle",
        help="Project bundle name (e.g., legacy-api). If provided, generates tests for all contracts in bundle",
    ),
    # Output
    output_dir: Path | None = typer.Option(
        None,
        "--output",
        "--out",
        help="Output directory for generated tests (default: .specfact/specmatic-tests/)",
    ),
    # Behavior/Options
    force: bool = typer.Option(
        False,
        "--force",
        help="Force test generation even if cached result exists (bypass cache).",
    ),
) -> None:
    """
    Generate Specmatic test suite from specification.

    Auto-generates contract tests from the OpenAPI/AsyncAPI specification
    that can be run to validate API implementations. Can generate tests for
    a single contract file or all contracts in a project bundle.

    **Caching:**
    Test generation results are cached in `.specfact/cache/specmatic-tests.json` based on
    file content hashes. Unchanged contracts are automatically skipped on subsequent runs
    to improve performance. Use --force to bypass cache and re-generate all tests.

    **Parameter Groups:**
    - **Target/Input**: spec_path (optional if --bundle provided), --bundle
    - **Output**: --output
    - **Behavior/Options**: --force

    **Examples:**
        specfact spec generate-tests api/openapi.yaml
        specfact spec generate-tests api/openapi.yaml --output tests/specmatic/
        specfact spec generate-tests --bundle legacy-api --output tests/contract/
        specfact spec generate-tests --bundle legacy-api --force  # Bypass cache
    """
    from rich.console import Console

    from specfact_cli.telemetry import telemetry
    from specfact_cli.utils.progress import load_bundle_with_progress
    from specfact_cli.utils.structure import SpecFactStructure

    console = Console()

    # Use active plan as default if bundle not provided
    if bundle is None:
        bundle = SpecFactStructure.get_active_bundle_name(Path("."))
        if bundle:
            console.print(f"[dim]Using active plan: {bundle}[/dim]")

    # Validate inputs
    if not spec_path and not bundle:
        print_error("Either spec_path or --bundle must be provided")
        raise typer.Exit(1)

    repo_path = Path(".").resolve()
    spec_paths: list[Path] = []

    # If bundle provided, load all contracts from bundle
    if bundle:
        bundle_dir = SpecFactStructure.project_dir(base_path=repo_path, bundle_name=bundle)
        if not bundle_dir.exists():
            print_error(f"Project bundle not found: {bundle_dir}")
            raise typer.Exit(1)

        project_bundle = load_bundle_with_progress(bundle_dir, validate_hashes=False, console_instance=console)

        for feature_key, feature in project_bundle.features.items():
            if feature.contract:
                contract_path = bundle_dir / feature.contract
                if contract_path.exists():
                    spec_paths.append(contract_path)
                else:
                    print_warning(f"Contract file not found for {feature_key}: {feature.contract}")
    elif spec_path:
        spec_paths = [spec_path]

    if not spec_paths:
        print_error("No contract files found to generate tests from")
        raise typer.Exit(1)

    telemetry_metadata = {
        "spec_path": str(spec_path) if spec_path else None,
        "bundle": bundle,
        "contracts_count": len(spec_paths),
    }

    with telemetry.track_command("spec.generate-tests", telemetry_metadata) as record:
        # Check if Specmatic is available
        is_available, error_msg = check_specmatic_available()
        if not is_available:
            print_error(f"Specmatic not available: {error_msg}")
            raise typer.Exit(1)

        import asyncio
        from datetime import UTC, datetime

        # Load test generation cache
        cache_dir = repo_path / SpecFactStructure.CACHE
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / "specmatic-tests.json"
        test_cache: dict[str, dict[str, Any]] = {}
        if cache_file.exists():
            try:
                test_cache = json.loads(cache_file.read_text())
            except Exception:
                test_cache = {}

        def compute_file_hash(file_path: Path) -> str:
            """Compute SHA256 hash of file content."""
            try:
                return hashlib.sha256(file_path.read_bytes()).hexdigest()
            except Exception:
                return ""

        generated_count = 0
        failed_count = 0
        skipped_count = 0
        total_count = len(spec_paths)

        for idx, contract_path in enumerate(spec_paths, 1):
            contract_relative = contract_path.relative_to(repo_path)
            contract_key = str(contract_relative)
            file_hash = compute_file_hash(contract_path) if contract_path.exists() else ""
            cache_entry = test_cache.get(contract_key, {})

            # Check cache
            use_cache = (
                not force
                and file_hash
                and cache_entry
                and cache_entry.get("hash") == file_hash
                and cache_entry.get("status") == "success"
                and cache_entry.get("output_dir") == str(output_dir or Path(".specfact/specmatic-tests"))
            )

            if use_cache:
                console.print(
                    f"\n[dim][{idx}/{total_count}][/dim] [bold cyan]Generating test suite from:[/bold cyan] {contract_relative}"
                )
                console.print(
                    f"[dim]⏭️  Skipping (cache hit - unchanged since {cache_entry.get('timestamp', 'unknown')})[/dim]"
                )
                generated_count += 1
                skipped_count += 1
                continue

            console.print(
                f"\n[bold yellow][{idx}/{total_count}][/bold yellow] [bold cyan]Generating test suite from:[/bold cyan] {contract_relative}"
            )

            try:
                output = asyncio.run(generate_specmatic_tests(contract_path, output_dir))
                print_success(f"✓ Test suite generated: {output}")

                # Update cache
                if file_hash:
                    test_cache[contract_key] = {
                        "hash": file_hash,
                        "status": "success",
                        "output_dir": str(output_dir or Path(".specfact/specmatic-tests")),
                        "timestamp": datetime.now(UTC).isoformat(),
                    }
                    # Save cache after each generation
                    with suppress(Exception):  # Don't fail if cache write fails
                        cache_file.write_text(json.dumps(test_cache, indent=2))

                generated_count += 1
            except Exception as e:
                print_error(f"✗ Test generation failed for {contract_path.name}: {e!s}")

                # Update cache with failure (so we don't skip failed contracts)
                if file_hash:
                    test_cache[contract_key] = {
                        "hash": file_hash,
                        "status": "failure",
                        "output_dir": str(output_dir or Path(".specfact/specmatic-tests")),
                        "timestamp": datetime.now(UTC).isoformat(),
                    }
                    with suppress(Exception):
                        cache_file.write_text(json.dumps(test_cache, indent=2))

                failed_count += 1

        # Summary
        if generated_count > 0:
            console.print(f"\n[bold green]✓[/bold green] Generated tests for {generated_count} contract(s)")
            if skipped_count > 0:
                console.print(f"[dim]  Skipped (cache): {skipped_count}[/dim]")
            console.print("[dim]Run the generated tests to validate your API implementation[/dim]")

        if failed_count > 0:
            print_warning(f"Failed to generate tests for {failed_count} contract(s)")
            if generated_count == 0:
                raise typer.Exit(1)

        record({"generated": generated_count, "skipped": skipped_count, "failed": failed_count})


@app.command("mock")
@beartype
@require(lambda spec_path: spec_path is None or spec_path.exists(), "Spec file must exist if provided")
@ensure(lambda result: result is None, "Must return None")
def mock(
    # Target/Input
    spec_path: Path | None = typer.Option(
        None,
        "--spec",
        help="Path to OpenAPI/AsyncAPI specification (optional if --bundle provided)",
    ),
    bundle: str | None = typer.Option(
        None,
        "--bundle",
        help="Project bundle name (e.g., legacy-api). If provided, selects contract from bundle. Default: active plan from 'specfact plan select'",
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
        help="Non-interactive mode (for CI/CD automation). Uses first contract if multiple available.",
    ),
) -> None:
    """
    Launch Specmatic mock server from specification.

    Starts a mock server that responds to API requests based on the
    OpenAPI/AsyncAPI specification. Useful for frontend development
    without a running backend. Can use a single spec file or select from bundle contracts.

    **Parameter Groups:**
    - **Target/Input**: --spec (optional if --bundle provided), --bundle
    - **Behavior/Options**: --port, --strict/--examples, --no-interactive

    **Examples:**
        specfact spec mock --spec api/openapi.yaml
        specfact spec mock --spec api/openapi.yaml --port 8080
        specfact spec mock --spec api/openapi.yaml --examples
        specfact spec mock --bundle legacy-api  # Interactive selection
        specfact spec mock --bundle legacy-api --no-interactive  # Uses first contract
    """
    from specfact_cli.telemetry import telemetry

    repo_path = Path(".").resolve()

    # Use active plan as default if bundle not provided
    if bundle is None:
        bundle = SpecFactStructure.get_active_bundle_name(repo_path)
        if bundle:
            console.print(f"[dim]Using active plan: {bundle}[/dim]")

    # Determine which spec to use
    selected_spec: Path | None = None

    if spec_path:
        # Direct spec file provided
        selected_spec = spec_path
    elif bundle:
        # Load contracts from bundle
        bundle_dir = SpecFactStructure.project_dir(base_path=repo_path, bundle_name=bundle)
        if not bundle_dir.exists():
            print_error(f"Project bundle not found: {bundle_dir}")
            raise typer.Exit(1)

        project_bundle = load_bundle_with_progress(bundle_dir, validate_hashes=False, console_instance=console)

        spec_paths: list[Path] = []
        feature_map: dict[str, str] = {}  # contract_path -> feature_key

        for feature_key, feature in project_bundle.features.items():
            if feature.contract:
                contract_path = bundle_dir / feature.contract
                if contract_path.exists():
                    spec_paths.append(contract_path)
                    feature_map[str(contract_path)] = feature_key

        if not spec_paths:
            print_error("No contract files found in bundle")
            raise typer.Exit(1)

        if len(spec_paths) == 1:
            # Only one contract, use it
            selected_spec = spec_paths[0]
        elif no_interactive:
            # Non-interactive mode, use first contract
            selected_spec = spec_paths[0]
            console.print(f"[dim]Using first contract: {feature_map[str(selected_spec)]}[/dim]")
        else:
            # Interactive selection
            console.print(f"\n[bold]Found {len(spec_paths)} contracts in bundle '{bundle}':[/bold]\n")
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("#", style="bold yellow", justify="right", width=4)
            table.add_column("Feature", style="bold", min_width=20)
            table.add_column("Contract Path", style="dim")

            for i, contract_path in enumerate(spec_paths, 1):
                feature_key = feature_map.get(str(contract_path), "Unknown")
                table.add_row(
                    str(i),
                    feature_key,
                    str(contract_path.relative_to(repo_path)),
                )

            console.print(table)
            console.print()

            selection = prompt_text(
                f"Select contract to use for mock server (1-{len(spec_paths)} or 'q' to quit): "
            ).strip()

            if selection.lower() in ("q", "quit", ""):
                print_info("Mock server cancelled")
                raise typer.Exit(0)

            try:
                idx = int(selection)
                if not (1 <= idx <= len(spec_paths)):
                    print_error(f"Invalid selection. Must be between 1 and {len(spec_paths)}")
                    raise typer.Exit(1)
                selected_spec = spec_paths[idx - 1]
            except ValueError:
                print_error(f"Invalid input: {selection}. Please enter a number.")
                raise typer.Exit(1) from None
    else:
        # Auto-detect spec if not provided
        common_names = [
            "openapi.yaml",
            "openapi.yml",
            "openapi.json",
            "asyncapi.yaml",
            "asyncapi.yml",
            "asyncapi.json",
        ]
        for name in common_names:
            candidate = Path(name)
            if candidate.exists():
                selected_spec = candidate
                break

        if selected_spec is None:
            print_error("No specification file found. Please provide --spec or --bundle option.")
            console.print("\n[bold]Options:[/bold]")
            console.print("  1. Provide a spec file: specfact spec mock --spec api/openapi.yaml")
            console.print("  2. Use --bundle option: specfact spec mock --bundle legacy-api")
            console.print("  3. Set active plan first: specfact plan select")
            console.print("\n[bold]Common locations for auto-detection:[/bold]")
            console.print("  - openapi.yaml")
            console.print("  - api/openapi.yaml")
            console.print("  - specs/openapi.yaml")
            raise typer.Exit(1)

    telemetry_metadata = {
        "spec_path": str(selected_spec) if selected_spec else None,
        "bundle": bundle,
        "port": port,
    }

    with telemetry.track_command("spec.mock", telemetry_metadata):
        # Check if Specmatic is available
        is_available, error_msg = check_specmatic_available()
        if not is_available:
            print_error(f"Specmatic not available: {error_msg}")
            raise typer.Exit(1)

        console.print("[bold cyan]Starting mock server...[/bold cyan]")
        console.print(f"  Spec: {selected_spec.relative_to(repo_path)}")
        console.print(f"  Port: {port}")
        console.print(f"  Mode: {'strict' if strict else 'examples'}")

        import asyncio

        try:
            mock_server = asyncio.run(create_mock_server(selected_spec, port=port, strict_mode=strict))
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

"""
Spec command - Specmatic integration for API contract testing.

This module provides commands for validating OpenAPI/AsyncAPI specifications,
checking backward compatibility, generating test suites, and running mock servers
using Specmatic.
"""

from __future__ import annotations

from pathlib import Path

import typer
from beartype import beartype
from icontract import ensure, require
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from specfact_cli.integrations.specmatic import (
    check_backward_compatibility,
    check_specmatic_available,
    create_mock_server,
    generate_specmatic_tests,
    validate_spec_with_specmatic,
)
from specfact_cli.utils import print_error, print_success


app = typer.Typer(
    help="Specmatic integration for API contract testing (OpenAPI/AsyncAPI validation, backward compatibility, mock servers)"
)
console = Console()


@app.command("validate")
@beartype
@require(lambda spec_path: spec_path.exists(), "Spec file must exist")
@ensure(lambda result: result is None, "Must return None")
def validate(
    # Target/Input
    spec_path: Path = typer.Argument(
        ...,
        help="Path to OpenAPI/AsyncAPI specification file",
        exists=True,
    ),
    # Advanced
    previous_version: Path | None = typer.Option(
        None,
        "--previous",
        help="Path to previous version for backward compatibility check",
        exists=True,
    ),
) -> None:
    """
    Validate OpenAPI/AsyncAPI specification using Specmatic.

    Runs comprehensive validation including:
    - Schema structure validation
    - Example generation test
    - Backward compatibility check (if previous version provided)

    **Parameter Groups:**
    - **Target/Input**: spec_path (required)
    - **Advanced**: --previous

    **Examples:**
        specfact spec validate api/openapi.yaml
        specfact spec validate api/openapi.yaml --previous api/openapi.v1.yaml
    """
    from specfact_cli.telemetry import telemetry

    with telemetry.track_command("spec.validate", {"spec_path": str(spec_path)}):
        # Check if Specmatic is available
        is_available, error_msg = check_specmatic_available()
        if not is_available:
            print_error(f"Specmatic not available: {error_msg}")
            console.print("\n[bold]Installation:[/bold]")
            console.print("Visit https://docs.specmatic.io/ for installation instructions")
            raise typer.Exit(1)

        console.print(f"[bold cyan]Validating specification:[/bold cyan] {spec_path}")

        # Run validation with progress
        import asyncio

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
        ) as progress:
            task = progress.add_task("Running Specmatic validation...", total=None)
            result = asyncio.run(validate_spec_with_specmatic(spec_path, previous_version))
            progress.update(task, completed=True)

        # Display results
        table = Table(title="Validation Results")
        table.add_column("Check", style="cyan")
        table.add_column("Status", style="magenta")
        table.add_column("Details", style="white")

        table.add_row(
            "Schema Validation",
            "✓ PASS" if result.schema_valid else "✗ FAIL",
            "" if result.schema_valid else result.errors[0] if result.errors else "Unknown error",
        )

        table.add_row(
            "Example Generation",
            "✓ PASS" if result.examples_valid else "✗ FAIL",
            "" if result.examples_valid else result.errors[1] if len(result.errors) > 1 else "Unknown error",
        )

        if previous_version:
            table.add_row(
                "Backward Compatibility",
                "✓ PASS" if result.backward_compatible else "✗ FAIL",
                "" if result.backward_compatible else ", ".join(result.breaking_changes or []),
            )

        console.print(table)

        if result.is_valid:
            print_success("✓ Specification is valid")
        else:
            print_error("✗ Specification validation failed")
            if result.errors:
                console.print("\n[bold]Errors:[/bold]")
                for error in result.errors:
                    console.print(f"  - {error}")
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
@require(lambda spec_path: spec_path.exists(), "Spec file must exist")
@ensure(lambda result: result is None, "Must return None")
def generate_tests(
    # Target/Input
    spec_path: Path = typer.Argument(..., help="Path to OpenAPI/AsyncAPI specification", exists=True),
    # Output
    output_dir: Path | None = typer.Option(
        None,
        "--output",
        "--out",
        help="Output directory for generated tests (default: .specfact/specmatic-tests/)",
    ),
) -> None:
    """
    Generate Specmatic test suite from specification.

    Auto-generates contract tests from the OpenAPI/AsyncAPI specification
    that can be run to validate API implementations.

    **Parameter Groups:**
    - **Target/Input**: spec_path (required)
    - **Output**: --output

    **Examples:**
        specfact spec generate-tests api/openapi.yaml
        specfact spec generate-tests api/openapi.yaml --output tests/specmatic/
    """
    from specfact_cli.telemetry import telemetry

    with telemetry.track_command("spec.generate-tests", {"spec_path": str(spec_path)}):
        # Check if Specmatic is available
        is_available, error_msg = check_specmatic_available()
        if not is_available:
            print_error(f"Specmatic not available: {error_msg}")
            raise typer.Exit(1)

        console.print(f"[bold cyan]Generating test suite from:[/bold cyan] {spec_path}")

        import asyncio

        try:
            output = asyncio.run(generate_specmatic_tests(spec_path, output_dir))
            print_success(f"✓ Test suite generated: {output}")
            console.print("[dim]Run the generated tests to validate your API implementation[/dim]")
        except Exception as e:
            print_error(f"✗ Test generation failed: {e!s}")
            raise typer.Exit(1) from e


@app.command("mock")
@beartype
@require(lambda spec_path: spec_path.exists() if spec_path else True, "Spec file must exist if provided")
@ensure(lambda result: result is None, "Must return None")
def mock(
    # Target/Input
    spec_path: Path | None = typer.Option(
        None,
        "--spec",
        help="Path to OpenAPI/AsyncAPI specification (default: auto-detect from current directory)",
    ),
    # Behavior/Options
    port: int = typer.Option(9000, "--port", help="Port number for mock server (default: 9000)"),
    strict: bool = typer.Option(
        True,
        "--strict/--examples",
        help="Use strict validation mode (default: strict)",
    ),
) -> None:
    """
    Launch Specmatic mock server from specification.

    Starts a mock server that responds to API requests based on the
    OpenAPI/AsyncAPI specification. Useful for frontend development
    without a running backend.

    **Parameter Groups:**
    - **Target/Input**: --spec (optional, auto-detects if not provided)
    - **Behavior/Options**: --port, --strict/--examples

    **Examples:**
        specfact spec mock --spec api/openapi.yaml
        specfact spec mock --spec api/openapi.yaml --port 8080
        specfact spec mock --spec api/openapi.yaml --examples  # Use example responses instead of strict validation
    """
    from specfact_cli.telemetry import telemetry

    with telemetry.track_command("spec.mock", {"spec_path": str(spec_path) if spec_path else None, "port": port}):
        # Check if Specmatic is available
        is_available, error_msg = check_specmatic_available()
        if not is_available:
            print_error(f"Specmatic not available: {error_msg}")
            raise typer.Exit(1)

        # Auto-detect spec if not provided
        if spec_path is None:
            # Look for common spec file names
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
                    spec_path = candidate
                    break

            if spec_path is None:
                print_error("No specification file found. Please provide --spec option.")
                console.print("\n[bold]Common locations:[/bold]")
                console.print("  - openapi.yaml")
                console.print("  - api/openapi.yaml")
                console.print("  - specs/openapi.yaml")
                raise typer.Exit(1)

        console.print("[bold cyan]Starting mock server...[/bold cyan]")
        console.print(f"  Spec: {spec_path}")
        console.print(f"  Port: {port}")
        console.print(f"  Mode: {'strict' if strict else 'examples'}")

        import asyncio

        try:
            mock_server = asyncio.run(create_mock_server(spec_path, port=port, strict_mode=strict))
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

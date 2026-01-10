"""
Validate command group for SpecFact CLI.

This module provides validation commands including sidecar validation.
"""

from __future__ import annotations

from pathlib import Path

import typer
from beartype import beartype
from icontract import require

from specfact_cli.runtime import get_configured_console
from specfact_cli.validators.sidecar.crosshair_summary import format_summary_line
from specfact_cli.validators.sidecar.models import SidecarConfig
from specfact_cli.validators.sidecar.orchestrator import initialize_sidecar_workspace, run_sidecar_validation


app = typer.Typer(name="validate", help="Validation commands", suggest_commands=False)
console = get_configured_console()

# Create sidecar subcommand group
sidecar_app = typer.Typer(name="sidecar", help="Sidecar validation commands", suggest_commands=False)
app.add_typer(sidecar_app)


@sidecar_app.command()
@beartype
@require(lambda bundle_name: bundle_name and len(bundle_name.strip()) > 0, "Bundle name must be non-empty")
@require(lambda repo_path: repo_path.exists(), "Repository path must exist")
def init(
    bundle_name: str = typer.Argument(..., help="Project bundle name (e.g., 'legacy-api')"),
    repo_path: Path = typer.Argument(..., help="Path to repository root directory"),
) -> None:
    """
    Initialize sidecar workspace for validation.

    Creates sidecar workspace directory structure and configuration for contract-based
    validation of external codebases without modifying source code.

    **What it does:**
    - Detects framework type (Django, FastAPI, DRF, pure-python)
    - Creates sidecar workspace directory structure
    - Generates configuration files
    - Detects Python environment (venv, poetry, uv, pip)
    - Sets up framework-specific configuration (e.g., DJANGO_SETTINGS_MODULE)

    **Example:**
    ```bash
    specfact validate sidecar init legacy-api /path/to/repo
    ```

    **Next steps:**
    After initialization, run `specfact validate sidecar run` to execute validation.
    """
    config = SidecarConfig.create(bundle_name, repo_path)

    console.print(f"[bold]Initializing sidecar workspace for bundle: {bundle_name}[/bold]")

    if initialize_sidecar_workspace(config):
        console.print("[green]✓[/green] Sidecar workspace initialized successfully")
        console.print(f"  Framework detected: {config.framework_type}")
        if config.django_settings_module:
            console.print(f"  Django settings: {config.django_settings_module}")
    else:
        console.print("[red]✗[/red] Failed to initialize sidecar workspace")
        raise typer.Exit(1)


@sidecar_app.command()
@beartype
@require(lambda bundle_name: bundle_name and len(bundle_name.strip()) > 0, "Bundle name must be non-empty")
@require(lambda repo_path: repo_path.exists(), "Repository path must exist")
def run(
    bundle_name: str = typer.Argument(..., help="Project bundle name (e.g., 'legacy-api')"),
    repo_path: Path = typer.Argument(..., help="Path to repository root directory"),
    run_crosshair: bool = typer.Option(
        True, "--run-crosshair/--no-run-crosshair", help="Run CrossHair symbolic execution analysis"
    ),
    run_specmatic: bool = typer.Option(
        True, "--run-specmatic/--no-run-specmatic", help="Run Specmatic contract testing validation"
    ),
) -> None:
    """
    Run sidecar validation workflow.

    Executes complete sidecar validation workflow including framework detection,
    route extraction, contract population, harness generation, and validation tools.

    **Workflow steps:**
    1. **Framework Detection**: Automatically detects Django, FastAPI, DRF, or pure-python
    2. **Route Extraction**: Extracts routes and schemas from framework-specific patterns
    3. **Contract Population**: Populates OpenAPI contracts with extracted routes/schemas
    4. **Harness Generation**: Generates CrossHair harness from populated contracts
    5. **CrossHair Analysis**: Runs symbolic execution on source code and harness (if enabled)
    6. **Specmatic Validation**: Runs contract testing against API endpoints (if enabled)

    **Example:**
    ```bash
    # Run full validation (CrossHair + Specmatic)
    specfact validate sidecar run legacy-api /path/to/repo

    # Run only CrossHair analysis
    specfact validate sidecar run legacy-api /path/to/repo --no-run-specmatic

    # Run only Specmatic validation
    specfact validate sidecar run legacy-api /path/to/repo --no-run-crosshair
    ```

    **Output:**
    - Validation results displayed in console
    - Reports saved to `.specfact/projects/<bundle>/reports/sidecar/`
    - Progress indicators for long-running operations
    """
    config = SidecarConfig.create(bundle_name, repo_path)
    config.tools.run_crosshair = run_crosshair
    config.tools.run_specmatic = run_specmatic

    console.print(f"[bold]Running sidecar validation for bundle: {bundle_name}[/bold]")

    results = run_sidecar_validation(config, console=console)

    # Display results
    console.print("\n[bold]Validation Results:[/bold]")
    console.print(f"  Framework: {results.get('framework_detected', 'unknown')}")
    console.print(f"  Routes extracted: {results.get('routes_extracted', 0)}")
    console.print(f"  Contracts populated: {results.get('contracts_populated', 0)}")
    console.print(f"  Harness generated: {results.get('harness_generated', False)}")

    if results.get("crosshair_results"):
        console.print("\n[bold]CrossHair Results:[/bold]")
        for key, value in results["crosshair_results"].items():
            success = value.get("success", False)
            status = "[green]✓[/green]" if success else "[red]✗[/red]"
            console.print(f"  {status} {key}")

        # Display summary if available
        if results.get("crosshair_summary"):
            summary = results["crosshair_summary"]
            summary_line = format_summary_line(summary)
            console.print(f"  {summary_line}")

            # Show summary file location if generated
            if results.get("crosshair_summary_file"):
                console.print(f"  Summary file: {results['crosshair_summary_file']}")

    if results.get("specmatic_skipped"):
        console.print(
            f"\n[yellow]⚠ Specmatic skipped: {results.get('specmatic_skip_reason', 'Unknown reason')}[/yellow]"
        )
    elif results.get("specmatic_results"):
        console.print("\n[bold]Specmatic Results:[/bold]")
        for key, value in results["specmatic_results"].items():
            success = value.get("success", False)
            status = "[green]✓[/green]" if success else "[red]✗[/red]"
            console.print(f"  {status} {key}")

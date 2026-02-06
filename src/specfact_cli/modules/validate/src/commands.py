"""
Validate command group for SpecFact CLI.

This module provides validation commands including sidecar validation.
"""

from __future__ import annotations

import re
from pathlib import Path

import typer
from beartype import beartype
from icontract import require

from specfact_cli.runtime import debug_log_operation, debug_print, get_configured_console, is_debug_mode
from specfact_cli.validators.sidecar.crosshair_summary import format_summary_line
from specfact_cli.validators.sidecar.models import SidecarConfig
from specfact_cli.validators.sidecar.orchestrator import initialize_sidecar_workspace, run_sidecar_validation


app = typer.Typer(name="validate", help="Validation commands", suggest_commands=False)
console = get_configured_console()


@beartype
def _format_crosshair_error(stderr: str, stdout: str) -> str:
    """
    Format CrossHair error messages into user-friendly text.

    Filters out technical errors (like Rich markup errors) and provides
    actionable error messages.

    Args:
        stderr: CrossHair stderr output
        stdout: CrossHair stdout output

    Returns:
        User-friendly error message or empty string if no actionable error
    """
    combined = (stderr + "\n" + stdout).strip()
    if not combined:
        return ""

    # Filter out Rich markup errors - these are internal errors, not user-facing
    error_lower = combined.lower()
    if "closing tag" in error_lower and "doesn't match any open tag" in error_lower:
        # This is a Rich internal error - ignore it completely
        return ""

    # Detect common error patterns and provide user-friendly messages
    # Python shared library issue (venv Python can't load libraries)
    if "error while loading shared libraries" in error_lower or "libpython" in error_lower:
        return (
            "Python environment issue detected. CrossHair is using system Python instead. "
            "This is usually harmless - validation will continue with system Python."
        )

    # CrossHair not found
    if "not found" in error_lower and ("crosshair" in error_lower or "command" in error_lower):
        return "CrossHair is not installed or not in PATH. Install it with: pip install crosshair-tool"

    # Timeout
    if "timeout" in error_lower or "timed out" in error_lower:
        return (
            "CrossHair analysis timed out. This is expected for complex applications with many routes. "
            "Some routes were analyzed before timeout. Check the summary file for partial results. "
            "To analyze more routes, increase --crosshair-timeout or --crosshair-per-path-timeout."
        )

    # Import errors
    if "importerror" in error_lower or "module not found" in error_lower:
        module_match = re.search(r"no module named ['\"]([^'\"]+)['\"]", error_lower)
        if module_match:
            module_name = module_match.group(1)
            return (
                f"Missing Python module: {module_name}. "
                "Ensure all dependencies are installed in the sidecar environment."
            )
        return "Missing Python module. Ensure all dependencies are installed."

    # Syntax errors in harness
    if "syntaxerror" in error_lower or "syntax error" in error_lower:
        return (
            "Syntax error in generated harness. This may indicate an issue with contract generation. "
            "Check the harness file for errors."
        )

    # Generic error - show a sanitized version (remove paths, technical details)
    # Only show first line and remove technical details
    lines = combined.split("\n")
    first_line = lines[0].strip() if lines else ""

    # Remove common technical noise
    first_line = re.sub(r"Error: closing tag.*", "", first_line, flags=re.IGNORECASE)
    first_line = re.sub(r"at position \d+", "", first_line, flags=re.IGNORECASE)
    first_line = re.sub(r"\.specfact/venv/bin/python.*", "", first_line)
    first_line = re.sub(r"error while loading shared libraries.*", "", first_line, flags=re.IGNORECASE)

    # If we have a clean message, show it (limited length)
    if first_line and len(first_line) > 10:
        # Limit to reasonable length
        if len(first_line) > 150:
            first_line = first_line[:147] + "..."
        return first_line

    # Fallback: generic message
    return "CrossHair execution failed. Check logs for details."


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
    if is_debug_mode():
        debug_log_operation(
            "command",
            "validate sidecar init",
            "started",
            extra={"bundle_name": bundle_name, "repo_path": str(repo_path)},
        )
        debug_print("[dim]validate sidecar init: started[/dim]")

    config = SidecarConfig.create(bundle_name, repo_path)

    console.print(f"[bold]Initializing sidecar workspace for bundle: {bundle_name}[/bold]")

    if initialize_sidecar_workspace(config):
        console.print("[green]✓[/green] Sidecar workspace initialized successfully")
        console.print(f"  Framework detected: {config.framework_type}")
        if config.django_settings_module:
            console.print(f"  Django settings: {config.django_settings_module}")
    else:
        if is_debug_mode():
            debug_log_operation(
                "command",
                "validate sidecar init",
                "failed",
                error="Failed to initialize sidecar workspace",
                extra={"reason": "init_failed", "bundle_name": bundle_name},
            )
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
    if is_debug_mode():
        debug_log_operation(
            "command",
            "validate sidecar run",
            "started",
            extra={
                "bundle_name": bundle_name,
                "repo_path": str(repo_path),
                "run_crosshair": run_crosshair,
                "run_specmatic": run_specmatic,
            },
        )
        debug_print("[dim]validate sidecar run: started[/dim]")

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

            # Display user-friendly error messages if CrossHair failed
            if not success:
                stderr = value.get("stderr", "")
                stdout = value.get("stdout", "")
                error_message = _format_crosshair_error(stderr, stdout)
                if error_message:
                    # Use markup=False to prevent Rich from parsing brackets in error messages
                    # This prevents Rich markup errors when error messages contain brackets
                    try:
                        console.print("    [red]Error:[/red]", end=" ")
                        console.print(error_message, markup=False)
                    except Exception:
                        # If Rich itself fails (shouldn't happen with markup=False, but be safe)
                        # Fall back to plain print
                        print(f"    Error: {error_message}")

        # Display summary if available
        if results.get("crosshair_summary"):
            summary = results["crosshair_summary"]
            summary_line = format_summary_line(summary)
            # Use try/except to catch Rich parsing errors
            try:
                console.print(f"  {summary_line}")
            except Exception:
                # Fall back to plain print if Rich fails
                print(f"  {summary_line}")

            # Show summary file location if generated
            if results.get("crosshair_summary_file"):
                summary_file_path = results["crosshair_summary_file"]
                # Use markup=False for paths to prevent Rich from parsing brackets
                try:
                    console.print("  Summary file: ", end="")
                    console.print(str(summary_file_path), markup=False)
                except Exception:
                    # Fall back to plain print if Rich fails
                    print(f"  Summary file: {summary_file_path}")

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

    if is_debug_mode():
        debug_log_operation(
            "command",
            "validate sidecar run",
            "success",
            extra={"bundle_name": bundle_name, "routes_extracted": results.get("routes_extracted", 0)},
        )
        debug_print("[dim]validate sidecar run: success[/dim]")

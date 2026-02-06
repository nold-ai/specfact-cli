"""
Repro command - Run full validation suite for reproducibility.

This module provides commands for running comprehensive validation
including linting, type checking, contract exploration, and tests.
"""

from __future__ import annotations

from pathlib import Path

import typer
from beartype import beartype
from click import Context as ClickContext
from icontract import require
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

from specfact_cli.runtime import debug_log_operation, debug_print, is_debug_mode
from specfact_cli.telemetry import telemetry
from specfact_cli.utils.env_manager import check_tool_in_env, detect_env_manager, detect_source_directories
from specfact_cli.utils.structure import SpecFactStructure
from specfact_cli.validators.repro_checker import ReproChecker


app = typer.Typer(help="Run validation suite for reproducibility")
console = Console()


def _update_pyproject_crosshair_config(pyproject_path: Path, config: dict[str, int | float]) -> bool:
    """
    Update or create [tool.crosshair] section in pyproject.toml.

    Args:
        pyproject_path: Path to pyproject.toml
        config: Dictionary with CrossHair configuration values

    Returns:
        True if config was updated/created, False otherwise
    """
    try:
        # Try tomlkit for style-preserving updates (recommended)
        try:
            import tomlkit

            # Read existing file to preserve style
            if pyproject_path.exists():
                with pyproject_path.open("r", encoding="utf-8") as f:
                    doc = tomlkit.parse(f.read())
            else:
                doc = tomlkit.document()

            # Update or create [tool.crosshair] section
            if "tool" not in doc:
                doc["tool"] = tomlkit.table()  # type: ignore[assignment]
            if "crosshair" not in doc["tool"]:  # type: ignore[index]
                doc["tool"]["crosshair"] = tomlkit.table()  # type: ignore[index,assignment]

            for key, value in config.items():
                doc["tool"]["crosshair"][key] = value  # type: ignore[index]

            # Write back
            with pyproject_path.open("w", encoding="utf-8") as f:
                f.write(tomlkit.dumps(doc))  # type: ignore[arg-type]

            return True

        except ImportError:
            # Fallback: use tomllib/tomli to read, then append section manually
            try:
                import tomllib
            except ImportError:
                try:
                    import tomli as tomllib  # noqa: F401
                except ImportError:
                    console.print("[red]Error:[/red] No TOML library available (need tomlkit, tomllib, or tomli)")
                    return False

            # Read existing content
            existing_content = ""
            if pyproject_path.exists():
                existing_content = pyproject_path.read_text(encoding="utf-8")

            # Check if [tool.crosshair] already exists
            if "[tool.crosshair]" in existing_content:
                # Update existing section (simple regex replacement)
                import re

                pattern = r"\[tool\.crosshair\][^\[]*"
                new_section = "[tool.crosshair]\n"
                for key, value in config.items():
                    new_section += f"{key} = {value}\n"

                existing_content = re.sub(pattern, new_section.rstrip(), existing_content, flags=re.DOTALL)
            else:
                # Append new section
                if existing_content and not existing_content.endswith("\n"):
                    existing_content += "\n"
                existing_content += "\n[tool.crosshair]\n"
                for key, value in config.items():
                    existing_content += f"{key} = {value}\n"

            pyproject_path.write_text(existing_content, encoding="utf-8")
            return True

    except Exception as e:
        console.print(f"[red]Error updating pyproject.toml:[/red] {e}")
        return False


def _is_valid_repo_path(path: Path) -> bool:
    """Check if path exists and is a directory."""
    return path.exists() and path.is_dir()


def _is_valid_output_path(path: Path | None) -> bool:
    """Check if output path exists if provided."""
    return path is None or path.exists()


def _count_python_files(path: Path) -> int:
    """Count Python files for anonymized telemetry reporting."""
    return sum(1 for _ in path.rglob("*.py"))


@app.callback(invoke_without_command=True, no_args_is_help=False)
# CrossHair: Skip analysis for Typer-decorated functions (signature analysis limitation)
# type: ignore[crosshair]
def main(
    ctx: ClickContext,
    # Target/Input
    repo: Path = typer.Option(
        Path("."),
        "--repo",
        help="Path to repository",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    # Output/Results
    out: Path | None = typer.Option(
        None,
        "--out",
        help="Output report path (default: bundle-specific .specfact/projects/<bundle-name>/reports/enforcement/report-<timestamp>.yaml if bundle context available, else global .specfact/reports/enforcement/, Phase 8.5)",
    ),
    # Behavior/Options
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Verbose output",
    ),
    fail_fast: bool = typer.Option(
        False,
        "--fail-fast",
        help="Stop on first failure",
    ),
    fix: bool = typer.Option(
        False,
        "--fix",
        help="Apply auto-fixes where available (Semgrep auto-fixes)",
    ),
    # Advanced/Configuration
    budget: int = typer.Option(
        120,
        "--budget",
        help="Time budget in seconds (must be > 0)",
        hidden=True,  # Hidden by default, shown with --help-advanced
    ),
    sidecar: bool = typer.Option(
        False,
        "--sidecar",
        help="Run sidecar validation for unannotated code (no-edit path)",
    ),
    sidecar_bundle: str | None = typer.Option(
        None,
        "--sidecar-bundle",
        help="Bundle name for sidecar validation (required if --sidecar is used)",
    ),
) -> None:
    """
    Run full validation suite for reproducibility.

    Automatically detects the target repository's environment manager (hatch, poetry, uv, pip)
    and adapts commands accordingly. All tools are optional and will be skipped with clear
    messages if unavailable.

    Executes:
    - Lint checks (ruff) - optional
    - Async patterns (semgrep) - optional, only if config exists
    - Type checking (basedpyright) - optional
    - Contract exploration (CrossHair) - optional
    - Property tests (pytest tests/contracts/) - optional, only if directory exists
    - Smoke tests (pytest tests/smoke/) - optional, only if directory exists
    - Sidecar validation (--sidecar) - optional, for unannotated code validation

    Works on external repositories without requiring SpecFact CLI adoption.

    Example:
        specfact repro --verbose --budget 120
        specfact repro --repo /path/to/external/repo --verbose
        specfact repro --fix --budget 120
        specfact repro --sidecar --sidecar-bundle legacy-api --repo /path/to/repo
    """
    # If a subcommand was invoked, don't run the main validation
    if ctx.invoked_subcommand is not None:
        return

    if is_debug_mode():
        debug_log_operation(
            "command",
            "repro",
            "started",
            extra={"repo": str(repo), "budget": budget, "sidecar": sidecar, "sidecar_bundle": sidecar_bundle},
        )
        debug_print("[dim]repro: started[/dim]")

    # Type checking for parameters (after subcommand check)
    if not _is_valid_repo_path(repo):
        raise typer.BadParameter("Repo path must exist and be directory")
    if budget <= 0:
        raise typer.BadParameter("Budget must be positive")
    if not _is_valid_output_path(out):
        raise typer.BadParameter("Output path must exist if provided")
    if sidecar and not sidecar_bundle:
        raise typer.BadParameter("--sidecar-bundle is required when --sidecar is used")

    from specfact_cli.utils.yaml_utils import dump_yaml

    console.print("[bold cyan]Running validation suite...[/bold cyan]")
    console.print(f"[dim]Repository: {repo}[/dim]")
    console.print(f"[dim]Time budget: {budget}s[/dim]")
    if fail_fast:
        console.print("[dim]Fail-fast: enabled[/dim]")
    if fix:
        console.print("[dim]Auto-fix: enabled[/dim]")
    console.print()

    # Ensure structure exists
    SpecFactStructure.ensure_structure(repo)

    python_file_count = _count_python_files(repo)

    telemetry_metadata = {
        "mode": "repro",
        "files_analyzed": python_file_count,
    }

    with telemetry.track_command("repro.run", telemetry_metadata) as record_event:
        # Run all checks
        checker = ReproChecker(repo_path=repo, budget=budget, fail_fast=fail_fast, fix=fix)

        # Detect and display environment manager before starting progress spinner
        from specfact_cli.utils.env_manager import detect_env_manager

        env_info = detect_env_manager(repo)
        if env_info.message:
            console.print(f"[dim]{env_info.message}[/dim]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            progress.add_task("Running validation checks...", total=None)

            # This will show progress for each check internally
            report = checker.run_all_checks()

        # Display results
        console.print("\n[bold]Validation Results[/bold]\n")

        # Summary table
        table = Table(title="Check Summary")
        table.add_column("Check", style="cyan")
        table.add_column("Tool", style="dim")
        table.add_column("Status", style="bold")
        table.add_column("Duration", style="dim")

        for check in report.checks:
            if check.status.value == "passed":
                status_icon = "[green]✓[/green] PASSED"
            elif check.status.value == "failed":
                status_icon = "[red]✗[/red] FAILED"
            elif check.status.value == "timeout":
                status_icon = "[yellow]⏱[/yellow] TIMEOUT"
            elif check.status.value == "skipped":
                status_icon = "[dim]⊘[/dim] SKIPPED"
            else:
                status_icon = "[dim]…[/dim] PENDING"

            duration_str = f"{check.duration:.2f}s" if check.duration else "N/A"

            table.add_row(check.name, check.tool, status_icon, duration_str)

        console.print(table)

        # Summary stats
        console.print("\n[bold]Summary:[/bold]")
        console.print(f"  Total checks: {report.total_checks}")
        console.print(f"  [green]Passed: {report.passed_checks}[/green]")
        if report.failed_checks > 0:
            console.print(f"  [red]Failed: {report.failed_checks}[/red]")
        if report.timeout_checks > 0:
            console.print(f"  [yellow]Timeout: {report.timeout_checks}[/yellow]")
        if report.skipped_checks > 0:
            console.print(f"  [dim]Skipped: {report.skipped_checks}[/dim]")
        console.print(f"  Total duration: {report.total_duration:.2f}s")

        if is_debug_mode():
            debug_log_operation(
                "command",
                "repro",
                "success",
                extra={
                    "total_checks": report.total_checks,
                    "passed": report.passed_checks,
                    "failed": report.failed_checks,
                },
            )
            debug_print("[dim]repro: success[/dim]")
        record_event(
            {
                "checks_total": report.total_checks,
                "checks_failed": report.failed_checks,
                "violations_detected": report.failed_checks,
            }
        )

        # Show errors if verbose
        if verbose:
            for check in report.checks:
                if check.error:
                    console.print(f"\n[bold red]{check.name} Error:[/bold red]")
                    console.print(f"[dim]{check.error}[/dim]")
                if check.output and check.status.value == "failed":
                    console.print(f"\n[bold red]{check.name} Output:[/bold red]")
                    console.print(f"[dim]{check.output[:500]}[/dim]")  # Limit output

        # Write report if requested (Phase 8.5: try to use bundle-specific path)
        if out is None:
            # Try to detect bundle from active plan
            bundle_name = SpecFactStructure.get_active_bundle_name(repo)
            if bundle_name:
                # Use bundle-specific enforcement report path (Phase 8.5)
                out = SpecFactStructure.get_bundle_enforcement_report_path(bundle_name=bundle_name, base_path=repo)
            else:
                # Fallback to global path (backward compatibility during transition)
                out = SpecFactStructure.get_timestamped_report_path("enforcement", repo, "yaml")
                SpecFactStructure.ensure_structure(repo)

        out.parent.mkdir(parents=True, exist_ok=True)
        dump_yaml(report.to_dict(), out)
        console.print(f"\n[dim]Report written to: {out}[/dim]")

        # Run sidecar validation if requested (after main checks)
        if sidecar and sidecar_bundle:
            from specfact_cli.validators.sidecar.models import SidecarConfig
            from specfact_cli.validators.sidecar.orchestrator import run_sidecar_validation
            from specfact_cli.validators.sidecar.unannotated_detector import detect_unannotated_in_repo

            console.print("\n[bold cyan]Running sidecar validation for unannotated code...[/bold cyan]")

            # Detect unannotated code
            unannotated = detect_unannotated_in_repo(repo)
            if unannotated:
                console.print(f"[dim]Found {len(unannotated)} unannotated functions[/dim]")
                # Store unannotated functions info for harness generation
                sidecar_config = SidecarConfig.create(sidecar_bundle, repo)
                # Pass unannotated info to orchestrator (via results dict)
            else:
                console.print("[dim]No unannotated functions detected (all functions have contracts)[/dim]")
                sidecar_config = SidecarConfig.create(sidecar_bundle, repo)

            # Run sidecar validation (harness will be generated for unannotated code)
            sidecar_results = run_sidecar_validation(sidecar_config, console=console)

            # Display sidecar results
            if sidecar_results.get("crosshair_summary"):
                summary = sidecar_results["crosshair_summary"]
                console.print(
                    f"[dim]Sidecar CrossHair: {summary.get('confirmed', 0)} confirmed, "
                    f"{summary.get('not_confirmed', 0)} not confirmed, "
                    f"{summary.get('violations', 0)} violations[/dim]"
                )

        # Exit with appropriate code
        exit_code = report.get_exit_code()
        if exit_code == 0:
            crosshair_failed = any(
                check.tool == "crosshair" and check.status.value == "failed" for check in report.checks
            )
            if crosshair_failed:
                console.print(
                    "\n[bold yellow]![/bold yellow] Required validations passed, but CrossHair failed (advisory)"
                )
                console.print("[dim]Reproducibility verified with advisory failures[/dim]")
            else:
                console.print("\n[bold green]✓[/bold green] All validations passed!")
                console.print("[dim]Reproducibility verified[/dim]")
        elif exit_code == 1:
            console.print("\n[bold red]✗[/bold red] Some validations failed")
            raise typer.Exit(1)
        else:
            console.print("\n[yellow]⏱[/yellow] Budget exceeded")
            raise typer.Exit(2)


@app.command("setup")
@beartype
@require(lambda repo: _is_valid_repo_path(repo), "Repo path must exist and be directory")
def setup(
    repo: Path = typer.Option(
        Path("."),
        "--repo",
        help="Path to repository",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    install_crosshair: bool = typer.Option(
        False,
        "--install-crosshair",
        help="Attempt to install crosshair-tool if not available",
    ),
) -> None:
    """
    Set up CrossHair configuration for contract exploration.


    Automatically generates [tool.crosshair] configuration in pyproject.toml
    to enable contract exploration with CrossHair during repro runs.

    This command:
    - Detects source directories in the repository
    - Creates/updates pyproject.toml with CrossHair configuration
    - Optionally checks if crosshair-tool is installed
    - Provides guidance on next steps

    Example:
        specfact repro setup
        specfact repro setup --repo /path/to/repo
        specfact repro setup --install-crosshair
    """
    console.print("[bold cyan]Setting up CrossHair configuration...[/bold cyan]")
    console.print(f"[dim]Repository: {repo}[/dim]\n")

    # Detect environment manager
    env_info = detect_env_manager(repo)
    if env_info.message:
        console.print(f"[dim]{env_info.message}[/dim]")

    # Detect source directories
    source_dirs = detect_source_directories(repo)
    if not source_dirs:
        # Fallback to common patterns
        if (repo / "src").exists():
            source_dirs = ["src/"]
        elif (repo / "lib").exists():
            source_dirs = ["lib/"]
        else:
            source_dirs = ["."]

    console.print(f"[green]✓[/green] Detected source directories: {', '.join(source_dirs)}")

    # Check if crosshair-tool is available
    crosshair_available, crosshair_message = check_tool_in_env(repo, "crosshair", env_info)
    if crosshair_available:
        console.print("[green]✓[/green] crosshair-tool is available")
    else:
        console.print(f"[yellow]⚠[/yellow] crosshair-tool not available: {crosshair_message}")
        if install_crosshair:
            console.print("[dim]Attempting to install crosshair-tool...[/dim]")
            import subprocess

            # Build install command with environment manager
            from specfact_cli.utils.env_manager import build_tool_command

            install_cmd = ["pip", "install", "crosshair-tool>=0.0.97"]
            install_cmd = build_tool_command(env_info, install_cmd)

            try:
                result = subprocess.run(install_cmd, capture_output=True, text=True, timeout=60, cwd=str(repo))
                if result.returncode == 0:
                    console.print("[green]✓[/green] crosshair-tool installed successfully")
                    crosshair_available = True
                else:
                    console.print(f"[red]✗[/red] Failed to install crosshair-tool: {result.stderr}")
            except subprocess.TimeoutExpired:
                console.print("[red]✗[/red] Installation timed out")
            except Exception as e:
                console.print(f"[red]✗[/red] Installation error: {e}")
        else:
            console.print(
                "[dim]Tip: Install with --install-crosshair flag, or manually: "
                f"{'hatch run pip install' if env_info.manager == 'hatch' else 'pip install'} crosshair-tool[/dim]"
            )

    # Create/update pyproject.toml with CrossHair config
    pyproject_path = repo / "pyproject.toml"

    # Default CrossHair configuration (matching our own pyproject.toml)
    crosshair_config: dict[str, int | float] = {
        "timeout": 60,
        "per_condition_timeout": 10,
        "per_path_timeout": 5,
        "max_iterations": 1000,
    }

    if _update_pyproject_crosshair_config(pyproject_path, crosshair_config):
        if is_debug_mode():
            debug_log_operation("command", "repro setup", "success", extra={"pyproject_path": str(pyproject_path)})
            debug_print("[dim]repro setup: success[/dim]")
        console.print(f"[green]✓[/green] Updated {pyproject_path.relative_to(repo)} with CrossHair configuration")
        console.print("\n[bold]CrossHair Configuration:[/bold]")
        for key, value in crosshair_config.items():
            console.print(f"  {key} = {value}")
    else:
        if is_debug_mode():
            debug_log_operation(
                "command",
                "repro setup",
                "failed",
                error=f"Failed to update {pyproject_path}",
                extra={"reason": "update_failed"},
            )
        console.print(f"[red]✗[/red] Failed to update {pyproject_path.relative_to(repo)}")
        raise typer.Exit(1)

    # Summary
    console.print("\n[bold green]✓[/bold green] Setup complete!")
    console.print("\n[bold]Next steps:[/bold]")
    console.print("  1. Run [cyan]specfact repro[/cyan] to execute validation checks")
    if not crosshair_available:
        console.print("  2. Install crosshair-tool to enable contract exploration:")
        if env_info.manager == "hatch":
            console.print("     [dim]hatch run pip install crosshair-tool[/dim]")
        elif env_info.manager == "poetry":
            console.print("     [dim]poetry add --dev crosshair-tool[/dim]")
        elif env_info.manager == "uv":
            console.print("     [dim]uv pip install crosshair-tool[/dim]")
        else:
            console.print("     [dim]pip install crosshair-tool[/dim]")
    console.print("  3. CrossHair will automatically explore contracts in your source code")
    console.print("  4. Results will appear in the validation report")

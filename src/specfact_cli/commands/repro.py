"""
Repro command - Run full validation suite for reproducibility.

This module provides commands for running comprehensive validation
including linting, type checking, contract exploration, and tests.
"""

from __future__ import annotations

from pathlib import Path

import typer
from beartype import beartype
from icontract import ensure, require
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from specfact_cli.telemetry import telemetry
from specfact_cli.utils.structure import SpecFactStructure
from specfact_cli.validators.repro_checker import ReproChecker


app = typer.Typer(help="Run validation suite for reproducibility")
console = Console()


def _is_valid_repo_path(path: Path) -> bool:
    """Check if path exists and is a directory."""
    return path.exists() and path.is_dir()


def _is_valid_output_path(path: Path | None) -> bool:
    """Check if output path exists if provided."""
    return path is None or path.exists()


def _count_python_files(path: Path) -> int:
    """Count Python files for anonymized telemetry reporting."""
    return sum(1 for _ in path.rglob("*.py"))


@app.callback(invoke_without_command=True)
@beartype
@require(lambda repo: _is_valid_repo_path(repo), "Repo path must exist and be directory")
@require(lambda budget: budget > 0, "Budget must be positive")
@ensure(lambda out: _is_valid_output_path(out), "Output path must exist if provided")
# CrossHair: Skip analysis for Typer-decorated functions (signature analysis limitation)
# type: ignore[crosshair]
def main(
    repo: Path = typer.Option(
        Path("."),
        "--repo",
        help="Path to repository",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Verbose output",
    ),
    budget: int = typer.Option(
        120,
        "--budget",
        help="Time budget in seconds (must be > 0)",
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
    out: Path | None = typer.Option(
        None,
        "--out",
        help="Output report path (default: .specfact/reports/enforcement/report-<timestamp>.yaml)",
    ),
) -> None:
    """
    Run full validation suite.

    Executes:
    - Lint checks (ruff)
    - Async patterns (semgrep)
    - Type checking (basedpyright)
    - Contract exploration (CrossHair)
    - Property tests (pytest tests/contracts/)
    - Smoke tests (pytest tests/smoke/)

    Example:
        specfact repro --verbose --budget 120
        specfact repro --fix --budget 120
    """
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

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
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

        # Write report if requested
        if out is None:
            # Use default path
            out = SpecFactStructure.get_timestamped_report_path("enforcement", repo, "yaml")
            SpecFactStructure.ensure_structure(repo)

        out.parent.mkdir(parents=True, exist_ok=True)
        dump_yaml(report.to_dict(), out)
        console.print(f"\n[dim]Report written to: {out}[/dim]")

        # Exit with appropriate code
        exit_code = report.get_exit_code()
        if exit_code == 0:
            console.print("\n[bold green]✓[/bold green] All validations passed!")
            console.print("[dim]Reproducibility verified[/dim]")
        elif exit_code == 1:
            console.print("\n[bold red]✗[/bold red] Some validations failed")
            raise typer.Exit(1)
        else:
            console.print("\n[yellow]⏱[/yellow] Budget exceeded")
            raise typer.Exit(2)

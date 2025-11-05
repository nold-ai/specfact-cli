"""
Console output utilities.

This module provides helpers for rich console output.
"""

from __future__ import annotations

from beartype import beartype
from icontract import require
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from specfact_cli.models.deviation import DeviationSeverity, ValidationReport


# Shared console instance
console = Console()


@beartype
@require(lambda report: isinstance(report, ValidationReport), "Report must be ValidationReport instance")
def print_validation_report(report: ValidationReport) -> None:
    """
    Print a formatted validation report.

    Args:
        report: Validation report to print
    """
    # Create summary table
    table = Table(title="Validation Summary")
    table.add_column("Severity", style="cyan")
    table.add_column("Count", justify="right")

    if report.high_count > 0:
        table.add_row("HIGH", str(report.high_count), style="bold red")
    if report.medium_count > 0:
        table.add_row("MEDIUM", str(report.medium_count), style="yellow")
    if report.low_count > 0:
        table.add_row("LOW", str(report.low_count), style="blue")

    console.print(table)

    # Print deviations
    if report.deviations:
        console.print("\n[bold]Deviations:[/bold]\n")

        for i, deviation in enumerate(report.deviations, 1):
            severity_color = {
                DeviationSeverity.HIGH: "bold red",
                DeviationSeverity.MEDIUM: "yellow",
                DeviationSeverity.LOW: "blue",
            }[deviation.severity]

            console.print(f"[{severity_color}]{i}. [{deviation.severity}][/{severity_color}] {deviation.description}")

            if deviation.location:
                console.print(f"   [dim]Location: {deviation.location}[/dim]")

            if hasattr(deviation, "fix_hint") and deviation.fix_hint:
                console.print(f"   [green]→ Suggestion: {deviation.fix_hint}[/green]")

            console.print()

    # Print overall result
    if report.passed:
        console.print(Panel("[bold green]✓ Validation PASSED[/bold green]", border_style="green"))
    else:
        console.print(Panel("[bold red]✗ Validation FAILED[/bold red]", border_style="red"))

"""
Drift command - Detect misalignment between code and specifications.

This module provides commands for detecting drift between actual code/tests
and specifications.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import typer
from beartype import beartype
from icontract import ensure, require
from rich.console import Console

from specfact_cli.runtime import debug_log_operation, debug_print, is_debug_mode
from specfact_cli.telemetry import telemetry
from specfact_cli.utils import print_error, print_success


app = typer.Typer(help="Detect drift between code and specifications")
console = Console()


@app.command("detect")
@beartype
@require(
    lambda bundle: bundle is None or (isinstance(bundle, str) and len(bundle) > 0),
    "Bundle name must be None or non-empty string",
)
@require(lambda repo: isinstance(repo, Path), "Repository path must be Path")
@ensure(lambda result: result is None, "Must return None")
def detect_drift(
    # Target/Input
    bundle: str | None = typer.Argument(
        None, help="Project bundle name (e.g., legacy-api). Default: active plan from 'specfact plan select'"
    ),
    repo: Path = typer.Option(
        Path("."),
        "--repo",
        help="Path to repository. Default: current directory (.)",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    # Output
    output_format: str = typer.Option(
        "table",
        "--format",
        help="Output format: 'table' (rich table), 'json', or 'yaml'. Default: table",
    ),
    out: Path | None = typer.Option(
        None,
        "--out",
        help="Output file path (for JSON/YAML format). Default: stdout",
    ),
) -> None:
    """
    Detect drift between code and specifications.

    Scans repository and project bundle to identify:
    - Added code (files with no spec)
    - Removed code (deleted but spec exists)
    - Modified code (hash changed)
    - Orphaned specs (spec with no code)
    - Test coverage gaps (stories missing tests)
    - Contract violations (implementation doesn't match contract)

    **Parameter Groups:**
    - **Target/Input**: bundle (required argument), --repo
    - **Output**: --format, --out

    **Examples:**
        specfact drift detect legacy-api --repo .
        specfact drift detect my-bundle --repo . --format json --out drift-report.json
    """
    if is_debug_mode():
        debug_log_operation(
            "command", "drift detect", "started", extra={"bundle": bundle, "repo": str(repo), "format": output_format}
        )
        debug_print("[dim]drift detect: started[/dim]")
    from rich.console import Console

    from specfact_cli.utils.structure import SpecFactStructure

    console = Console()

    # Use active plan as default if bundle not provided
    if bundle is None:
        bundle = SpecFactStructure.get_active_bundle_name(repo)
        if bundle is None:
            if is_debug_mode():
                debug_log_operation(
                    "command", "drift detect", "failed", error="Bundle name required", extra={"reason": "no_bundle"}
                )
            console.print("[bold red]✗[/bold red] Bundle name required")
            console.print("[yellow]→[/yellow] Use --bundle option or run 'specfact plan select' to set active plan")
            raise typer.Exit(1)
        console.print(f"[dim]Using active plan: {bundle}[/dim]")
    from specfact_cli.sync.drift_detector import DriftDetector

    repo_path = repo.resolve()

    telemetry_metadata = {
        "bundle": bundle,
        "output_format": output_format,
    }

    with telemetry.track_command("drift.detect", telemetry_metadata) as record:
        console.print(f"[bold cyan]Drift Detection:[/bold cyan] {bundle}")
        console.print(f"[dim]Repository:[/dim] {repo_path}\n")

        detector = DriftDetector(bundle, repo_path)
        report = detector.scan(bundle, repo_path)

        # Display report
        if output_format == "table":
            _display_drift_report_table(report)
        elif output_format == "json":
            import json

            output = json.dumps(report.__dict__, indent=2)
            if out:
                out.write_text(output, encoding="utf-8")
                print_success(f"Report written to: {out}")
            else:
                console.print(output)
        elif output_format == "yaml":
            import yaml

            output = yaml.dump(report.__dict__, default_flow_style=False, sort_keys=False)
            if out:
                out.write_text(output, encoding="utf-8")
                print_success(f"Report written to: {out}")
            else:
                console.print(output)
        else:
            if is_debug_mode():
                debug_log_operation(
                    "command",
                    "drift detect",
                    "failed",
                    error=f"Unknown format: {output_format}",
                    extra={"reason": "invalid_format"},
                )
            print_error(f"Unknown output format: {output_format}")
            raise typer.Exit(1)

        # Summary
        total_issues = (
            len(report.added_code)
            + len(report.removed_code)
            + len(report.modified_code)
            + len(report.orphaned_specs)
            + len(report.test_coverage_gaps)
            + len(report.contract_violations)
        )

        if total_issues == 0:
            print_success("No drift detected - code and specs are in sync!")
        else:
            console.print(f"\n[bold yellow]Total Issues:[/bold yellow] {total_issues}")

        record(
            {
                "added_code": len(report.added_code),
                "removed_code": len(report.removed_code),
                "modified_code": len(report.modified_code),
                "orphaned_specs": len(report.orphaned_specs),
                "test_coverage_gaps": len(report.test_coverage_gaps),
                "contract_violations": len(report.contract_violations),
                "total_issues": total_issues,
            }
        )
        if is_debug_mode():
            debug_log_operation(
                "command",
                "drift detect",
                "success",
                extra={"bundle": bundle, "total_issues": total_issues},
            )
            debug_print("[dim]drift detect: success[/dim]")


def _display_drift_report_table(report: Any) -> None:
    """Display drift report as a rich table."""

    console.print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    console.print("[bold]Drift Detection Report[/bold]")
    console.print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

    # Added Code
    if report.added_code:
        console.print(f"[bold yellow]Added Code ({len(report.added_code)} files):[/bold yellow]")
        for file_path in report.added_code[:10]:  # Show first 10
            console.print(f"  • {file_path} (no spec)")
        if len(report.added_code) > 10:
            console.print(f"  ... and {len(report.added_code) - 10} more")
        console.print()

    # Removed Code
    if report.removed_code:
        console.print(f"[bold yellow]Removed Code ({len(report.removed_code)} files):[/bold yellow]")
        for file_path in report.removed_code[:10]:
            console.print(f"  • {file_path} (deleted but spec exists)")
        if len(report.removed_code) > 10:
            console.print(f"  ... and {len(report.removed_code) - 10} more")
        console.print()

    # Modified Code
    if report.modified_code:
        console.print(f"[bold yellow]Modified Code ({len(report.modified_code)} files):[/bold yellow]")
        for file_path in report.modified_code[:10]:
            console.print(f"  • {file_path} (hash changed)")
        if len(report.modified_code) > 10:
            console.print(f"  ... and {len(report.modified_code) - 10} more")
        console.print()

    # Orphaned Specs
    if report.orphaned_specs:
        console.print(f"[bold yellow]Orphaned Specs ({len(report.orphaned_specs)} features):[/bold yellow]")
        for feature_key in report.orphaned_specs[:10]:
            console.print(f"  • {feature_key} (no code)")
        if len(report.orphaned_specs) > 10:
            console.print(f"  ... and {len(report.orphaned_specs) - 10} more")
        console.print()

    # Test Coverage Gaps
    if report.test_coverage_gaps:
        console.print(f"[bold yellow]Test Coverage Gaps ({len(report.test_coverage_gaps)}):[/bold yellow]")
        for feature_key, story_key in report.test_coverage_gaps[:10]:
            console.print(f"  • {feature_key}, {story_key} (no tests)")
        if len(report.test_coverage_gaps) > 10:
            console.print(f"  ... and {len(report.test_coverage_gaps) - 10} more")
        console.print()

    # Contract Violations
    if report.contract_violations:
        console.print(f"[bold yellow]Contract Violations ({len(report.contract_violations)}):[/bold yellow]")
        for violation in report.contract_violations[:10]:
            console.print(f"  • {violation}")
        if len(report.contract_violations) > 10:
            console.print(f"  ... and {len(report.contract_violations) - 10} more")
        console.print()

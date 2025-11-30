"""
Analyze command - Analyze codebase for contract coverage and quality.

This module provides commands for analyzing codebases to determine
contract coverage, code quality metrics, and enhancement opportunities.
"""

from __future__ import annotations

from pathlib import Path

import typer
from beartype import beartype
from icontract import ensure, require
from rich.console import Console
from rich.table import Table

from specfact_cli.models.quality import CodeQuality
from specfact_cli.telemetry import telemetry
from specfact_cli.utils import print_error, print_success


app = typer.Typer(help="Analyze codebase for contract coverage and quality")
console = Console()


@app.command("contracts")
@beartype
@require(lambda repo: isinstance(repo, Path), "Repository path must be Path")
@require(lambda bundle: isinstance(bundle, str) and len(bundle) > 0, "Bundle name must be non-empty string")
@ensure(lambda result: result is None, "Must return None")
def analyze_contracts(
    # Target/Input
    repo: Path = typer.Option(
        Path("."),
        "--repo",
        help="Path to repository. Default: current directory (.)",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    bundle: str | None = typer.Option(
        None,
        "--bundle",
        help="Project bundle name (e.g., legacy-api). Default: active plan from 'specfact plan select'",
    ),
) -> None:
    """
    Analyze contract coverage for codebase.

    Scans codebase to determine which files have beartype, icontract,
    and CrossHair contracts, and identifies files that need enhancement.

    **Parameter Groups:**
    - **Target/Input**: --repo, --bundle (required)

    **Examples:**
        specfact analyze contracts --repo . --bundle legacy-api
    """
    from rich.console import Console

    from specfact_cli.models.quality import QualityTracking
    from specfact_cli.utils.bundle_loader import load_project_bundle
    from specfact_cli.utils.structure import SpecFactStructure

    console = Console()

    # Use active plan as default if bundle not provided
    if bundle is None:
        bundle = SpecFactStructure.get_active_bundle_name(repo)
        if bundle is None:
            console.print("[bold red]✗[/bold red] Bundle name required")
            console.print("[yellow]→[/yellow] Use --bundle option or run 'specfact plan select' to set active plan")
            raise typer.Exit(1)
        console.print(f"[dim]Using active plan: {bundle}[/dim]")

    repo_path = repo.resolve()
    bundle_dir = SpecFactStructure.project_dir(base_path=repo_path, bundle_name=bundle)

    if not bundle_dir.exists():
        print_error(f"Project bundle not found: {bundle_dir}")
        raise typer.Exit(1)

    telemetry_metadata = {
        "bundle": bundle,
    }

    with telemetry.track_command("analyze.contracts", telemetry_metadata) as record:
        console.print(f"[bold cyan]Contract Coverage Analysis:[/bold cyan] {bundle}")
        console.print(f"[dim]Repository:[/dim] {repo_path}\n")

        # Load project bundle
        project_bundle = load_project_bundle(bundle_dir)

        # Analyze each feature's source files
        quality_tracking = QualityTracking()
        files_analyzed = 0
        files_with_beartype = 0
        files_with_icontract = 0
        files_with_crosshair = 0

        for _feature_key, feature in project_bundle.features.items():
            if not feature.source_tracking:
                continue

            for impl_file in feature.source_tracking.implementation_files:
                file_path = repo_path / impl_file
                if not file_path.exists():
                    continue

                files_analyzed += 1
                quality = _analyze_file_quality(file_path)
                quality_tracking.code_quality[impl_file] = quality

                if quality.beartype:
                    files_with_beartype += 1
                if quality.icontract:
                    files_with_icontract += 1
                if quality.crosshair:
                    files_with_crosshair += 1

        # Display results
        table = Table(title="Contract Coverage Analysis")
        table.add_column("File", style="cyan")
        table.add_column("beartype", justify="center")
        table.add_column("icontract", justify="center")
        table.add_column("crosshair", justify="center")
        table.add_column("Coverage", justify="right")

        for file_path, quality in list(quality_tracking.code_quality.items())[:20]:  # Show first 20
            table.add_row(
                file_path,
                "✓" if quality.beartype else "✗",
                "✓" if quality.icontract else "✗",
                "✓" if quality.crosshair else "✗",
                f"{quality.coverage:.0%}",
            )

        console.print(table)

        # Summary
        console.print("\n[bold]Summary:[/bold]")
        console.print(f"  Files analyzed: {files_analyzed}")
        console.print(
            f"  Files with beartype: {files_with_beartype} ({files_with_beartype / files_analyzed * 100:.0%}%)"
            if files_analyzed > 0
            else "  Files with beartype: 0"
        )
        console.print(
            f"  Files with icontract: {files_with_icontract} ({files_with_icontract / files_analyzed * 100:.0%}%)"
            if files_analyzed > 0
            else "  Files with icontract: 0"
        )
        console.print(
            f"  Files with crosshair: {files_with_crosshair} ({files_with_crosshair / files_analyzed * 100:.0%}%)"
            if files_analyzed > 0
            else "  Files with crosshair: 0"
        )

        # Save quality tracking
        quality_file = bundle_dir / "quality-tracking.yaml"
        import yaml

        quality_file.parent.mkdir(parents=True, exist_ok=True)
        with quality_file.open("w", encoding="utf-8") as f:
            yaml.dump(quality_tracking.model_dump(), f, default_flow_style=False)

        print_success(f"Quality tracking saved to: {quality_file}")

        record(
            {
                "files_analyzed": files_analyzed,
                "files_with_beartype": files_with_beartype,
                "files_with_icontract": files_with_icontract,
                "files_with_crosshair": files_with_crosshair,
            }
        )


def _analyze_file_quality(file_path: Path) -> CodeQuality:
    """Analyze a file for contract coverage."""

    from specfact_cli.models.quality import CodeQuality

    try:
        with file_path.open(encoding="utf-8") as f:
            content = f.read()

        has_beartype = "beartype" in content or "@beartype" in content
        has_icontract = "icontract" in content or "@require" in content or "@ensure" in content
        has_crosshair = "crosshair" in content.lower()

        # Simple coverage estimation (would need actual test coverage tool)
        coverage = 0.0

        return CodeQuality(
            beartype=has_beartype,
            icontract=has_icontract,
            crosshair=has_crosshair,
            coverage=coverage,
        )
    except Exception:
        # Return default quality if analysis fails
        return CodeQuality()


@app.command("enhance")
@beartype
@require(lambda file: isinstance(file, Path), "File path must be Path")
@require(lambda apply: isinstance(apply, str), "Apply must be string")
@ensure(lambda result: result is None, "Must return None")
def enhance_contracts(
    # Target/Input
    file: Path = typer.Argument(..., help="Path to file to enhance", exists=True),
    apply: str = typer.Option(
        ...,
        "--apply",
        help="Contracts to apply: 'beartype', 'icontract', 'crosshair', or comma-separated list (e.g., 'beartype,icontract')",
    ),
    # Output
    output: Path | None = typer.Option(
        None,
        "--output",
        help="Output file path (default: overwrite input file)",
    ),
) -> None:
    """
    Apply contracts to existing code (LLM-assisted).

    Prepares LLM prompt context for adding beartype, icontract, or CrossHair
    contracts to existing code files. The CLI orchestrates, LLM writes code.

    **Parameter Groups:**
    - **Target/Input**: file (required argument), --apply
    - **Output**: --output

    **Examples:**
        specfact enhance contracts src/auth/login.py --apply beartype,icontract
        specfact enhance contracts src/models/user.py --apply beartype --output src/models/user_enhanced.py
    """

    file_path = file.resolve()
    repo_path = file_path.parent.parent  # Assume repo root is 2 levels up

    contracts_to_apply = [c.strip() for c in apply.split(",")]
    valid_contracts = {"beartype", "icontract", "crosshair"}
    invalid_contracts = set(contracts_to_apply) - valid_contracts

    if invalid_contracts:
        print_error(f"Invalid contract types: {', '.join(invalid_contracts)}")
        print_error(f"Valid types: {', '.join(valid_contracts)}")
        raise typer.Exit(1)

    telemetry_metadata = {
        "file": str(file_path),
        "contracts": contracts_to_apply,
    }

    with telemetry.track_command("enhance.contracts", telemetry_metadata) as record:
        console.print(f"[bold cyan]Enhancing contracts for:[/bold cyan] {file_path}")
        console.print(f"[dim]Contracts to apply:[/dim] {', '.join(contracts_to_apply)}\n")

        # Read file content
        file_content = file_path.read_text(encoding="utf-8")

        # Generate LLM prompt
        prompt_parts = [
            "# Contract Enhancement Request",
            "",
            f"## File: {file_path}",
            "",
            "## Current Code",
            "```python",
            file_content,
            "```",
            "",
            "## Contracts to Apply",
        ]

        for contract_type in contracts_to_apply:
            if contract_type == "beartype":
                prompt_parts.append("- **beartype**: Add `@beartype` decorator to all functions")
            elif contract_type == "icontract":
                prompt_parts.append(
                    "- **icontract**: Add `@require` and `@ensure` decorators with appropriate contracts"
                )
            elif contract_type == "crosshair":
                prompt_parts.append("- **crosshair**: Add property tests using CrossHair")

        prompt_parts.extend(
            [
                "",
                "## Instructions",
                "Add the requested contracts to the code above.",
                "Maintain existing functionality and code style.",
                "Ensure all contracts are properly imported.",
                "",
            ]
        )

        prompt = "\n".join(prompt_parts)

        # Save prompt to file
        prompts_dir = repo_path / ".specfact" / "prompts"
        prompts_dir.mkdir(parents=True, exist_ok=True)
        prompt_file = prompts_dir / f"enhance-{file_path.stem}-{'-'.join(contracts_to_apply)}.md"
        prompt_file.write_text(prompt, encoding="utf-8")

        print_success(f"LLM prompt generated: {prompt_file}")
        console.print("[yellow]Execute this prompt with your LLM to enhance the code[/yellow]")

        if output:
            console.print(f"[dim]Output will be written to: {output}[/dim]")

        record({"prompt_generated": True, "prompt_file": str(prompt_file)})

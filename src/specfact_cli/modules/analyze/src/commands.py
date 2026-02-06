"""
Analyze command - Analyze codebase for contract coverage and quality.

This module provides commands for analyzing codebases to determine
contract coverage, code quality metrics, and enhancement opportunities.
"""

from __future__ import annotations

import ast
from pathlib import Path

import typer
from beartype import beartype
from icontract import ensure, require
from rich.console import Console
from rich.table import Table

from specfact_cli.models.quality import CodeQuality, QualityTracking
from specfact_cli.runtime import debug_log_operation, debug_print, is_debug_mode
from specfact_cli.telemetry import telemetry
from specfact_cli.utils import print_error, print_success
from specfact_cli.utils.progress import load_bundle_with_progress
from specfact_cli.utils.structure import SpecFactStructure


app = typer.Typer(help="Analyze codebase for contract coverage and quality")
console = Console()


@app.command("contracts")
@beartype
@require(lambda repo: isinstance(repo, Path), "Repository path must be Path")
@require(
    lambda bundle: bundle is None or (isinstance(bundle, str) and len(bundle) > 0),
    "Bundle name must be None or non-empty string",
)
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
    if is_debug_mode():
        debug_log_operation("command", "analyze contracts", "started", extra={"repo": str(repo), "bundle": bundle})
        debug_print("[dim]analyze contracts: started[/dim]")
    console = Console()

    # Use active plan as default if bundle not provided
    if bundle is None:
        bundle = SpecFactStructure.get_active_bundle_name(repo)
        if bundle is None:
            if is_debug_mode():
                debug_log_operation(
                    "command",
                    "analyze contracts",
                    "failed",
                    error="Bundle name required",
                    extra={"reason": "no_bundle"},
                )
            console.print("[bold red]✗[/bold red] Bundle name required")
            console.print("[yellow]→[/yellow] Use --bundle option or run 'specfact plan select' to set active plan")
            raise typer.Exit(1)
        console.print(f"[dim]Using active plan: {bundle}[/dim]")

    repo_path = repo.resolve()
    bundle_dir = SpecFactStructure.project_dir(base_path=repo_path, bundle_name=bundle)

    if not bundle_dir.exists():
        if is_debug_mode():
            debug_log_operation(
                "command",
                "analyze contracts",
                "failed",
                error=f"Bundle not found: {bundle_dir}",
                extra={"reason": "bundle_missing"},
            )
        print_error(f"Project bundle not found: {bundle_dir}")
        raise typer.Exit(1)

    telemetry_metadata = {
        "bundle": bundle,
    }

    with telemetry.track_command("analyze.contracts", telemetry_metadata) as record:
        console.print(f"[bold cyan]Contract Coverage Analysis:[/bold cyan] {bundle}")
        console.print(f"[dim]Repository:[/dim] {repo_path}\n")

        # Load project bundle with unified progress display
        project_bundle = load_bundle_with_progress(bundle_dir, validate_hashes=False, console_instance=console)

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

        # Sort files: prioritize files missing contracts
        # Sort key: (has_all_contracts, total_contracts, file_path)
        # This puts files missing contracts first, then by number of contracts (asc), then alphabetically
        def sort_key(item: tuple[str, CodeQuality]) -> tuple[bool, int, str]:
            file_path, quality = item
            has_all = quality.beartype and quality.icontract and quality.crosshair
            total_contracts = sum([quality.beartype, quality.icontract, quality.crosshair])
            return (has_all, total_contracts, file_path)

        sorted_files = sorted(quality_tracking.code_quality.items(), key=sort_key)

        # Show files needing attention first, limit to 30 for readability
        max_display = 30
        files_to_display = sorted_files[:max_display]
        total_files = len(sorted_files)

        # Display results
        table_title = "Contract Coverage Analysis"
        if total_files > max_display:
            table_title += f" (showing top {max_display} files needing attention)"
        table = Table(title=table_title)
        table.add_column("File", style="cyan")
        table.add_column("beartype", justify="center")
        table.add_column("icontract", justify="center")
        table.add_column("crosshair", justify="center")
        table.add_column("Coverage", justify="right")

        for file_path, quality in files_to_display:
            # Highlight files missing contracts
            file_style = "yellow" if not (quality.beartype and quality.icontract) else "cyan"
            table.add_row(
                f"[{file_style}]{file_path}[/{file_style}]",
                "✓" if quality.beartype else "[red]✗[/red]",
                "✓" if quality.icontract else "[red]✗[/red]",
                "✓" if quality.crosshair else "[dim]✗[/dim]",
                f"{quality.coverage:.0%}",
            )

        console.print(table)

        # Show message if files were filtered
        if total_files > max_display:
            console.print(
                f"\n[yellow]Note:[/yellow] Showing top {max_display} files needing attention "
                f"(out of {total_files} total files analyzed). "
                f"Files missing contracts are prioritized."
            )

        # Summary
        console.print("\n[bold]Summary:[/bold]")
        console.print(f"  Files analyzed: {files_analyzed}")
        if files_analyzed > 0:
            beartype_pct = files_with_beartype / files_analyzed
            icontract_pct = files_with_icontract / files_analyzed
            crosshair_pct = files_with_crosshair / files_analyzed
            console.print(f"  Files with beartype: {files_with_beartype} ({beartype_pct:.1%})")
            console.print(f"  Files with icontract: {files_with_icontract} ({icontract_pct:.1%})")
            console.print(f"  Files with crosshair: {files_with_crosshair} ({crosshair_pct:.1%})")
        else:
            console.print("  Files with beartype: 0")
            console.print("  Files with icontract: 0")
            console.print("  Files with crosshair: 0")

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
        if is_debug_mode():
            debug_log_operation(
                "command",
                "analyze contracts",
                "success",
                extra={"files_analyzed": files_analyzed, "bundle": bundle},
            )
            debug_print("[dim]analyze contracts: success[/dim]")


def _analyze_file_quality(file_path: Path) -> CodeQuality:
    """Analyze a file for contract coverage."""
    try:
        with file_path.open(encoding="utf-8") as f:
            content = f.read()

        # Quick check: if file is in models/ directory, likely a data model file
        # This avoids expensive AST parsing for most data model files
        file_str = str(file_path)
        is_models_dir = "/models/" in file_str or "\\models\\" in file_str

        # For files in models/ directory, do quick AST check to confirm
        if is_models_dir:
            try:
                import ast

                tree = ast.parse(content, filename=str(file_path))
                # Quick check: if only BaseModel classes with no business logic, skip contract check
                if _is_pure_data_model_file(tree):
                    return CodeQuality(
                        beartype=True,  # Pydantic provides type validation
                        icontract=True,  # Pydantic provides validation (Field validators)
                        crosshair=False,  # CrossHair not typically used for data models
                        coverage=0.0,
                    )
            except (SyntaxError, ValueError):
                # If AST parsing fails, fall through to normal check
                pass

        # Check for contract decorators in content
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


def _is_pure_data_model_file(tree: ast.AST) -> bool:
    """
    Quick check if file contains only pure data models (Pydantic BaseModel, dataclasses) with no business logic.

    Returns:
        True if file is pure data models, False otherwise
    """
    has_pydantic_models = False
    has_dataclasses = False
    has_business_logic = False

    # Standard methods that don't need contracts (including common helper methods)
    standard_methods = {
        "__init__",
        "__str__",
        "__repr__",
        "__eq__",
        "__hash__",
        "model_dump",
        "model_validate",
        "dict",
        "json",
        "copy",
        "update",
        # Common helper methods on data models (convenience methods, not business logic)
        "compute_summary",
        "update_summary",
        "to_dict",
        "from_dict",
        "validate",
        "serialize",
        "deserialize",
    }

    # Check module-level functions and class methods separately
    # First, collect all classes and check their methods
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # Check methods in this class
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name not in standard_methods:
                    # Non-standard method - likely business logic
                    has_business_logic = True
                    break
            if has_business_logic:
                break

    # Then check for module-level functions (functions not inside any class)
    if not has_business_logic and isinstance(tree, ast.Module):
        # Get all top-level nodes (module body)
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith(
                "_"
            ):  # Public functions
                has_business_logic = True
                break

    # Check for Pydantic models and dataclasses
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                if isinstance(base, ast.Name) and base.id == "BaseModel":
                    has_pydantic_models = True
                    break
                if isinstance(base, ast.Attribute) and base.attr == "BaseModel":
                    has_pydantic_models = True
                    break

            for decorator in node.decorator_list:
                if (isinstance(decorator, ast.Name) and decorator.id == "dataclass") or (
                    isinstance(decorator, ast.Attribute) and decorator.attr == "dataclass"
                ):
                    has_dataclasses = True
                    break

    # Business logic check is done above (methods and module-level functions)

    # File is pure data model if:
    # 1. Has Pydantic models or dataclasses
    # 2. No business logic methods or functions
    return (has_pydantic_models or has_dataclasses) and not has_business_logic

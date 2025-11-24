"""
Enforce command - Configure contract validation quality gates.

This module provides commands for configuring enforcement modes
and validation policies.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import typer
from beartype import beartype
from icontract import require
from rich.console import Console
from rich.table import Table

from specfact_cli.models.deviation import Deviation, DeviationSeverity, DeviationType, ValidationReport
from specfact_cli.models.enforcement import EnforcementConfig, EnforcementPreset
from specfact_cli.models.sdd import SDDManifest
from specfact_cli.telemetry import telemetry
from specfact_cli.utils.structure import SpecFactStructure
from specfact_cli.utils.yaml_utils import dump_yaml


app = typer.Typer(help="Configure quality gates and enforcement modes")
console = Console()


@app.command("stage")
@beartype
def stage(
    preset: str = typer.Option(
        "balanced",
        "--preset",
        help="Enforcement preset (minimal, balanced, strict)",
    ),
) -> None:
    """
    Set enforcement mode for contract validation.

    Modes:
    - minimal:  Log violations, never block
    - balanced: Block HIGH severity, warn MEDIUM
    - strict:   Block all MEDIUM+ violations

    Example:
        specfact enforce stage --preset balanced
    """
    telemetry_metadata = {
        "preset": preset.lower(),
    }

    with telemetry.track_command("enforce.stage", telemetry_metadata) as record:
        # Validate preset (contract-style validation)
        if not isinstance(preset, str) or len(preset) == 0:
            console.print("[bold red]✗[/bold red] Preset must be non-empty string")
            raise typer.Exit(1)

        if preset.lower() not in ("minimal", "balanced", "strict"):
            console.print(f"[bold red]✗[/bold red] Unknown preset: {preset}")
            console.print("Valid presets: minimal, balanced, strict")
            raise typer.Exit(1)

        console.print(f"[bold cyan]Setting enforcement mode:[/bold cyan] {preset}")

        # Validate preset enum
        try:
            preset_enum = EnforcementPreset(preset)
        except ValueError as err:
            console.print(f"[bold red]✗[/bold red] Unknown preset: {preset}")
            console.print("Valid presets: minimal, balanced, strict")
            raise typer.Exit(1) from err

        # Create enforcement configuration
        config = EnforcementConfig.from_preset(preset_enum)

        # Display configuration as table
        table = Table(title=f"Enforcement Mode: {preset.upper()}")
        table.add_column("Severity", style="cyan")
        table.add_column("Action", style="yellow")

        for severity, action in config.to_summary_dict().items():
            table.add_row(severity, action)

        console.print(table)

        # Ensure .specfact structure exists
        SpecFactStructure.ensure_structure()

        # Write configuration to file
        config_path = SpecFactStructure.get_enforcement_config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Use mode='json' to convert enums to their string values
        dump_yaml(config.model_dump(mode="json"), config_path)

        record({"config_saved": True, "enabled": config.enabled})

        console.print(f"\n[bold green]✓[/bold green] Enforcement mode set to {preset}")
        console.print(f"[dim]Configuration saved to: {config_path}[/dim]")


@app.command("sdd")
@beartype
@require(lambda sdd: sdd is None or isinstance(sdd, Path), "SDD must be None or Path")
@require(lambda plan: plan is None or isinstance(plan, Path), "Plan must be None or Path")
@require(
    lambda format: isinstance(format, str) and format.lower() in ("yaml", "json", "markdown"),
    "Format must be yaml, json, or markdown",
)
@require(lambda out: out is None or isinstance(out, Path), "Out must be None or Path")
def enforce_sdd(
    sdd: Path | None = typer.Option(
        None,
        "--sdd",
        help="Path to SDD manifest (default: .specfact/sdd.<format>)",
    ),
    plan: Path | None = typer.Option(
        None,
        "--plan",
        help="Path to plan bundle (default: active plan)",
    ),
    format: str = typer.Option(
        "yaml",
        "--format",
        help="Output format (yaml, json, markdown)",
    ),
    out: Path | None = typer.Option(
        None,
        "--out",
        help="Output file path (default: .specfact/reports/sdd/validation-<timestamp>.<format>)",
    ),
    non_interactive: bool = typer.Option(
        False,
        "--non-interactive",
        help="Non-interactive mode (for CI/CD automation)",
    ),
) -> None:
    """
    Validate SDD manifest against plan bundle and contracts.

    Checks:
    - SDD ↔ plan hash match
    - Coverage thresholds (contracts/story, invariants/feature, architecture facets)
    - Frozen sections (hash mismatch detection)
    - Contract density metrics

    Example:
        specfact enforce sdd
        specfact enforce sdd --plan .specfact/plans/main.bundle.yaml
        specfact enforce sdd --format json --out validation-report.json
    """
    from specfact_cli.migrations.plan_migrator import load_plan_bundle
    from specfact_cli.models.sdd import SDDManifest
    from specfact_cli.utils.structured_io import (
        StructuredFormat,
        dump_structured_file,
        load_structured_file,
    )

    telemetry_metadata = {
        "format": format.lower(),
        "non_interactive": non_interactive,
    }

    with telemetry.track_command("enforce.sdd", telemetry_metadata) as record:
        console.print("\n[bold cyan]SpecFact CLI - SDD Validation[/bold cyan]")
        console.print("=" * 60)

        # Find SDD manifest path
        if sdd is None:
            base_path = Path(".")
            # Try YAML first, then JSON
            sdd_yaml = base_path / SpecFactStructure.ROOT / "sdd.yaml"
            sdd_json = base_path / SpecFactStructure.ROOT / "sdd.json"
            if sdd_yaml.exists():
                sdd = sdd_yaml
            elif sdd_json.exists():
                sdd = sdd_json
            else:
                console.print("[bold red]✗[/bold red] SDD manifest not found")
                console.print(f"[dim]Expected: {sdd_yaml} or {sdd_json}[/dim]")
                console.print("[dim]Create one with: specfact plan harden[/dim]")
                raise typer.Exit(1)

        if not sdd.exists():
            console.print(f"[bold red]✗[/bold red] SDD manifest not found: {sdd}")
            raise typer.Exit(1)

        # Find plan path (reuse logic from plan.py)
        plan_path = _find_plan_path(plan)
        if plan_path is None or not plan_path.exists():
            console.print("[bold red]✗[/bold red] Plan bundle not found")
            raise typer.Exit(1)

        try:
            # Load SDD manifest
            console.print(f"[dim]Loading SDD manifest: {sdd}[/dim]")
            sdd_data = load_structured_file(sdd)
            sdd_manifest = SDDManifest.model_validate(sdd_data)

            # Load plan bundle
            console.print(f"[dim]Loading plan bundle: {plan_path}[/dim]")
            bundle = load_plan_bundle(plan_path)
            bundle.update_summary(include_hash=True)
            plan_hash = bundle.metadata.summary.content_hash if bundle.metadata and bundle.metadata.summary else None

            if not plan_hash:
                console.print("[bold red]✗[/bold red] Failed to compute plan bundle hash")
                raise typer.Exit(1)

            # Create validation report
            report = ValidationReport()

            # 1. Validate hash match
            console.print("\n[cyan]Validating hash match...[/cyan]")
            if sdd_manifest.plan_bundle_hash != plan_hash:
                deviation = Deviation(
                    type=DeviationType.HASH_MISMATCH,
                    severity=DeviationSeverity.HIGH,
                    description=f"SDD plan bundle hash mismatch: expected {plan_hash[:16]}..., got {sdd_manifest.plan_bundle_hash[:16]}...",
                    location=".specfact/sdd.yaml",
                    fix_hint="Run 'specfact plan harden' to update SDD manifest with current plan hash",
                )
                report.add_deviation(deviation)
                console.print("[bold red]✗[/bold red] Hash mismatch detected")
            else:
                console.print("[bold green]✓[/bold green] Hash match verified")

            # 2. Validate coverage thresholds using contract validator
            console.print("\n[cyan]Validating coverage thresholds...[/cyan]")

            from specfact_cli.validators.contract_validator import calculate_contract_density, validate_contract_density

            # Calculate contract density metrics
            metrics = calculate_contract_density(sdd_manifest, bundle)

            # Validate against thresholds
            density_deviations = validate_contract_density(sdd_manifest, bundle, metrics)

            # Add deviations to report
            for deviation in density_deviations:
                report.add_deviation(deviation)

            # Display metrics with status indicators
            thresholds = sdd_manifest.coverage_thresholds

            # Contracts per story
            if metrics.contracts_per_story < thresholds.contracts_per_story:
                console.print(
                    f"[bold yellow]⚠[/bold yellow] Contracts/story: {metrics.contracts_per_story:.2f} (threshold: {thresholds.contracts_per_story})"
                )
            else:
                console.print(
                    f"[bold green]✓[/bold green] Contracts/story: {metrics.contracts_per_story:.2f} (threshold: {thresholds.contracts_per_story})"
                )

            # Invariants per feature
            if metrics.invariants_per_feature < thresholds.invariants_per_feature:
                console.print(
                    f"[bold yellow]⚠[/bold yellow] Invariants/feature: {metrics.invariants_per_feature:.2f} (threshold: {thresholds.invariants_per_feature})"
                )
            else:
                console.print(
                    f"[bold green]✓[/bold green] Invariants/feature: {metrics.invariants_per_feature:.2f} (threshold: {thresholds.invariants_per_feature})"
                )

            # Architecture facets
            if metrics.architecture_facets < thresholds.architecture_facets:
                console.print(
                    f"[bold yellow]⚠[/bold yellow] Architecture facets: {metrics.architecture_facets} (threshold: {thresholds.architecture_facets})"
                )
            else:
                console.print(
                    f"[bold green]✓[/bold green] Architecture facets: {metrics.architecture_facets} (threshold: {thresholds.architecture_facets})"
                )

            # 3. Validate frozen sections (placeholder - hash comparison would require storing section hashes)
            if sdd_manifest.frozen_sections:
                console.print("\n[cyan]Checking frozen sections...[/cyan]")
                console.print(f"[dim]Frozen sections: {len(sdd_manifest.frozen_sections)}[/dim]")
                # TODO: Implement hash-based frozen section validation in Phase 6

            # Generate output report
            output_format = format.lower()
            if out is None:
                SpecFactStructure.ensure_structure()
                reports_dir = Path(".") / SpecFactStructure.ROOT / "reports" / "sdd"
                reports_dir.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                extension = "md" if output_format == "markdown" else output_format
                out = reports_dir / f"validation-{timestamp}.{extension}"

            # Save report
            if output_format == "markdown":
                _save_markdown_report(out, report, sdd_manifest, bundle, plan_hash)
            elif output_format == "json":
                dump_structured_file(report.model_dump(mode="json"), out, StructuredFormat.JSON)
            else:  # yaml
                dump_structured_file(report.model_dump(mode="json"), out, StructuredFormat.YAML)

            # Display summary
            console.print("\n[bold cyan]Validation Summary[/bold cyan]")
            console.print("=" * 60)
            console.print(f"Total deviations: {report.total_deviations}")
            console.print(f"  High: {report.high_count}")
            console.print(f"  Medium: {report.medium_count}")
            console.print(f"  Low: {report.low_count}")
            console.print(f"\nReport saved to: {out}")

            # Exit with appropriate code
            if not report.passed:
                console.print("\n[bold red]✗[/bold red] SDD validation failed")
                record({"passed": False, "deviations": report.total_deviations})
                raise typer.Exit(1)

            console.print("\n[bold green]✓[/bold green] SDD validation passed")
            record({"passed": True, "deviations": 0})

        except Exception as e:
            console.print(f"[bold red]✗[/bold red] Validation failed: {e}")
            raise typer.Exit(1) from e


def _find_plan_path(plan: Path | None) -> Path | None:
    """
    Find plan path (default, latest, or provided).

    Args:
        plan: Provided plan path or None

    Returns:
        Plan path or None if not found
    """
    if plan is not None:
        return plan

    # Try to find active plan or latest
    default_plan = SpecFactStructure.get_default_plan_path()
    if default_plan.exists():
        return default_plan

    # Find latest plan bundle
    base_path = Path(".")
    plans_dir = base_path / SpecFactStructure.PLANS
    if plans_dir.exists():
        plan_files = [
            p
            for p in plans_dir.glob("*.bundle.*")
            if any(str(p).endswith(suffix) for suffix in SpecFactStructure.PLAN_SUFFIXES)
        ]
        plan_files = sorted(plan_files, key=lambda p: p.stat().st_mtime, reverse=True)
        if plan_files:
            return plan_files[0]
    return None


def _save_markdown_report(
    out: Path,
    report: ValidationReport,
    sdd_manifest: SDDManifest,
    bundle,  # type: ignore[type-arg]
    plan_hash: str,
) -> None:
    """Save validation report in Markdown format."""
    with open(out, "w") as f:
        f.write("# SDD Validation Report\n\n")
        f.write(f"**Generated**: {datetime.now().isoformat()}\n\n")
        f.write(f"**SDD Manifest**: {sdd_manifest.plan_bundle_id}\n")
        f.write(f"**Plan Bundle Hash**: {plan_hash[:32]}...\n\n")

        f.write("## Summary\n\n")
        f.write(f"- **Total Deviations**: {report.total_deviations}\n")
        f.write(f"- **High**: {report.high_count}\n")
        f.write(f"- **Medium**: {report.medium_count}\n")
        f.write(f"- **Low**: {report.low_count}\n")
        f.write(f"- **Status**: {'✅ PASSED' if report.passed else '❌ FAILED'}\n\n")

        if report.deviations:
            f.write("## Deviations\n\n")
            for i, deviation in enumerate(report.deviations, 1):
                f.write(f"### {i}. {deviation.type.value} ({deviation.severity.value})\n\n")
                f.write(f"{deviation.description}\n\n")
                if deviation.fix_hint:
                    f.write(f"**Fix**: {deviation.fix_hint}\n\n")

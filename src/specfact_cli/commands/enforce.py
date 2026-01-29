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
from specfact_cli.runtime import debug_log_operation, debug_print, is_debug_mode
from specfact_cli.telemetry import telemetry
from specfact_cli.utils.structure import SpecFactStructure
from specfact_cli.utils.yaml_utils import dump_yaml


app = typer.Typer(help="Configure quality gates and enforcement modes")
console = Console()


@app.command("stage")
@beartype
def stage(
    # Advanced/Configuration
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

    **Parameter Groups:**
    - **Advanced/Configuration**: --preset

    **Examples:**
        specfact enforce stage --preset balanced
        specfact enforce stage --preset strict
        specfact enforce stage --preset minimal
    """
    if is_debug_mode():
        debug_log_operation("command", "enforce stage", "started", extra={"preset": preset})
        debug_print("[dim]enforce stage: started[/dim]")
    telemetry_metadata = {
        "preset": preset.lower(),
    }

    with telemetry.track_command("enforce.stage", telemetry_metadata) as record:
        # Validate preset (contract-style validation)
        if not isinstance(preset, str) or len(preset) == 0:
            console.print("[bold red]✗[/bold red] Preset must be non-empty string")
            raise typer.Exit(1)

        if preset.lower() not in ("minimal", "balanced", "strict"):
            if is_debug_mode():
                debug_log_operation(
                    "command",
                    "enforce stage",
                    "failed",
                    error=f"Unknown preset: {preset}",
                    extra={"reason": "invalid_preset"},
                )
            console.print(f"[bold red]✗[/bold red] Unknown preset: {preset}")
            console.print("Valid presets: minimal, balanced, strict")
            raise typer.Exit(1)

        console.print(f"[bold cyan]Setting enforcement mode:[/bold cyan] {preset}")

        # Validate preset enum
        try:
            preset_enum = EnforcementPreset(preset)
        except ValueError as err:
            if is_debug_mode():
                debug_log_operation(
                    "command", "enforce stage", "failed", error=str(err), extra={"reason": "invalid_preset"}
                )
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
        if is_debug_mode():
            debug_log_operation(
                "command", "enforce stage", "success", extra={"preset": preset, "config_path": str(config_path)}
            )
            debug_print("[dim]enforce stage: success[/dim]")

        console.print(f"\n[bold green]✓[/bold green] Enforcement mode set to {preset}")
        console.print(f"[dim]Configuration saved to: {config_path}[/dim]")


@app.command("sdd")
@beartype
@require(
    lambda bundle: bundle is None or (isinstance(bundle, str) and len(bundle) > 0),
    "Bundle name must be None or non-empty string",
)
@require(lambda sdd: sdd is None or isinstance(sdd, Path), "SDD must be None or Path")
@require(
    lambda output_format: isinstance(output_format, str) and output_format.lower() in ("yaml", "json", "markdown"),
    "Output format must be yaml, json, or markdown",
)
@require(lambda out: out is None or isinstance(out, Path), "Out must be None or Path")
def enforce_sdd(
    # Target/Input
    bundle: str | None = typer.Argument(
        None,
        help="Project bundle name (e.g., legacy-api, auth-module). Default: active plan from 'specfact plan select'",
    ),
    sdd: Path | None = typer.Option(
        None,
        "--sdd",
        help="Path to SDD manifest. Default: bundle-specific .specfact/projects/<bundle-name>/sdd.<format>. No legacy root-level fallback.",
    ),
    # Output/Results
    output_format: str = typer.Option(
        "yaml",
        "--output-format",
        help="Output format (yaml, json, markdown). Default: yaml",
    ),
    out: Path | None = typer.Option(
        None,
        "--out",
        help="Output file path. Default: bundle-specific .specfact/projects/<bundle-name>/reports/enforcement/report-<timestamp>.<format> (Phase 8.5)",
    ),
    # Behavior/Options
    no_interactive: bool = typer.Option(
        False,
        "--no-interactive",
        help="Non-interactive mode (for CI/CD automation). Default: False (interactive mode)",
    ),
) -> None:
    """
    Validate SDD manifest against project bundle and contracts.

    Checks:
    - SDD ↔ bundle hash match
    - Coverage thresholds (contracts/story, invariants/feature, architecture facets)
    - Frozen sections (hash mismatch detection)
    - Contract density metrics

    **Parameter Groups:**
    - **Target/Input**: bundle (required argument), --sdd
    - **Output/Results**: --output-format, --out
    - **Behavior/Options**: --no-interactive

    **Examples:**
        specfact enforce sdd legacy-api
        specfact enforce sdd auth-module --output-format json --out validation-report.json
        specfact enforce sdd legacy-api --no-interactive
    """
    if is_debug_mode():
        debug_log_operation(
            "command", "enforce sdd", "started", extra={"bundle": bundle, "output_format": output_format}
        )
        debug_print("[dim]enforce sdd: started[/dim]")
    from rich.console import Console

    from specfact_cli.models.sdd import SDDManifest
    from specfact_cli.utils.structure import SpecFactStructure
    from specfact_cli.utils.structured_io import StructuredFormat

    console = Console()

    # Use active plan as default if bundle not provided
    if bundle is None:
        bundle = SpecFactStructure.get_active_bundle_name(Path("."))
        if bundle is None:
            if is_debug_mode():
                debug_log_operation(
                    "command", "enforce sdd", "failed", error="Bundle name required", extra={"reason": "no_bundle"}
                )
            console.print("[bold red]✗[/bold red] Bundle name required")
            console.print("[yellow]→[/yellow] Use --bundle option or run 'specfact plan select' to set active plan")
            raise typer.Exit(1)
        console.print(f"[dim]Using active plan: {bundle}[/dim]")

    from specfact_cli.utils.structured_io import (
        dump_structured_file,
        load_structured_file,
    )

    telemetry_metadata = {
        "output_format": output_format.lower(),
        "no_interactive": no_interactive,
    }

    with telemetry.track_command("enforce.sdd", telemetry_metadata) as record:
        console.print("\n[bold cyan]SpecFact CLI - SDD Validation[/bold cyan]")
        console.print("=" * 60)

        # Find bundle directory
        base_path = Path(".")
        bundle_dir = SpecFactStructure.project_dir(base_path=base_path, bundle_name=bundle)
        if not bundle_dir.exists():
            if is_debug_mode():
                debug_log_operation(
                    "command",
                    "enforce sdd",
                    "failed",
                    error=f"Bundle not found: {bundle_dir}",
                    extra={"reason": "bundle_missing"},
                )
            console.print(f"[bold red]✗[/bold red] Project bundle not found: {bundle_dir}")
            console.print(f"[dim]Create one with: specfact plan init {bundle}[/dim]")
            raise typer.Exit(1)

        # Find SDD manifest path using discovery utility
        from specfact_cli.utils.sdd_discovery import find_sdd_for_bundle

        base_path = Path(".")
        discovered_sdd = find_sdd_for_bundle(bundle, base_path, sdd)
        if discovered_sdd is None:
            if is_debug_mode():
                debug_log_operation(
                    "command",
                    "enforce sdd",
                    "failed",
                    error="SDD manifest not found",
                    extra={"reason": "sdd_not_found", "bundle": bundle},
                )
            console.print("[bold red]✗[/bold red] SDD manifest not found")
            console.print(f"[dim]Searched for: .specfact/projects/{bundle}/sdd.yaml (bundle-specific)[/dim]")
            console.print(f"[dim]Create one with: specfact plan harden {bundle}[/dim]")
            raise typer.Exit(1)

        sdd = discovered_sdd
        console.print(f"[dim]Using SDD manifest: {sdd}[/dim]")

        try:
            # Load SDD manifest
            console.print(f"[dim]Loading SDD manifest: {sdd}[/dim]")
            sdd_data = load_structured_file(sdd)
            sdd_manifest = SDDManifest.model_validate(sdd_data)

            # Load project bundle with progress indicator

            from specfact_cli.utils.progress import load_bundle_with_progress

            project_bundle = load_bundle_with_progress(bundle_dir, validate_hashes=False, console_instance=console)
            console.print("[dim]Computing hash...[/dim]")

            summary = project_bundle.compute_summary(include_hash=True)
            project_hash = summary.content_hash

            if not project_hash:
                if is_debug_mode():
                    debug_log_operation(
                        "command",
                        "enforce sdd",
                        "failed",
                        error="Failed to compute project bundle hash",
                        extra={"reason": "hash_compute_failed"},
                    )
                console.print("[bold red]✗[/bold red] Failed to compute project bundle hash")
                raise typer.Exit(1)

            # Convert to PlanBundle for compatibility with validation functions
            from specfact_cli.commands.plan import _convert_project_bundle_to_plan_bundle

            plan_bundle = _convert_project_bundle_to_plan_bundle(project_bundle)

            # Create validation report
            report = ValidationReport()

            # 1. Validate hash match
            console.print("\n[cyan]Validating hash match...[/cyan]")
            if sdd_manifest.plan_bundle_hash != project_hash:
                deviation = Deviation(
                    type=DeviationType.HASH_MISMATCH,
                    severity=DeviationSeverity.HIGH,
                    description=f"SDD bundle hash mismatch: expected {project_hash[:16]}..., got {sdd_manifest.plan_bundle_hash[:16]}...",
                    location=str(sdd),
                    fix_hint=f"Run 'specfact plan harden {bundle}' to update SDD manifest with current bundle hash",
                )
                report.add_deviation(deviation)
                console.print("[bold red]✗[/bold red] Hash mismatch detected")
            else:
                console.print("[bold green]✓[/bold green] Hash match verified")

            # 2. Validate coverage thresholds using contract validator
            console.print("\n[cyan]Validating coverage thresholds...[/cyan]")

            from specfact_cli.validators.contract_validator import calculate_contract_density, validate_contract_density

            # Calculate contract density metrics
            metrics = calculate_contract_density(sdd_manifest, plan_bundle)

            # Validate against thresholds
            density_deviations = validate_contract_density(sdd_manifest, plan_bundle, metrics)

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

            # OpenAPI contract coverage
            if metrics.openapi_coverage_percent < thresholds.openapi_coverage_percent:
                console.print(
                    f"[bold yellow]⚠[/bold yellow] OpenAPI coverage: {metrics.openapi_coverage_percent:.1f}% (threshold: {thresholds.openapi_coverage_percent}%)"
                )
            else:
                console.print(
                    f"[bold green]✓[/bold green] OpenAPI coverage: {metrics.openapi_coverage_percent:.1f}% (threshold: {thresholds.openapi_coverage_percent}%)"
                )

            # 3. Validate frozen sections (placeholder - hash comparison would require storing section hashes)
            if sdd_manifest.frozen_sections:
                console.print("\n[cyan]Checking frozen sections...[/cyan]")
                console.print(f"[dim]Frozen sections: {len(sdd_manifest.frozen_sections)}[/dim]")
                # TODO: Implement hash-based frozen section validation in Phase 6

            # 4. Validate OpenAPI/AsyncAPI contracts referenced in bundle with Specmatic
            console.print("\n[cyan]Validating API contracts with Specmatic...[/cyan]")
            import asyncio

            from specfact_cli.integrations.specmatic import check_specmatic_available, validate_spec_with_specmatic

            is_available, error_msg = check_specmatic_available()
            if not is_available:
                console.print(f"[dim]💡 Tip: Install Specmatic to validate API contracts: {error_msg}[/dim]")
            else:
                # Validate contracts referenced in bundle features
                # PlanBundle.features is a list, not a dict
                contract_files = []
                features_iter = (
                    plan_bundle.features.values() if isinstance(plan_bundle.features, dict) else plan_bundle.features
                )
                for feature in features_iter:
                    if feature.contract:
                        contract_path = bundle_dir / feature.contract
                        if contract_path.exists():
                            contract_files.append((contract_path, feature.key))

                if contract_files:
                    console.print(f"[dim]Found {len(contract_files)} contract(s) referenced in bundle[/dim]")
                    for contract_path, feature_key in contract_files[:5]:  # Validate up to 5 contracts
                        console.print(
                            f"[dim]Validating {contract_path.relative_to(bundle_dir)} (from {feature_key})...[/dim]"
                        )
                        try:
                            result = asyncio.run(validate_spec_with_specmatic(contract_path))
                            if not result.is_valid:
                                deviation = Deviation(
                                    type=DeviationType.CONTRACT_VIOLATION,
                                    severity=DeviationSeverity.MEDIUM,
                                    description=f"API contract validation failed: {contract_path.name} (feature: {feature_key})",
                                    location=str(contract_path),
                                    fix_hint=f"Run 'specfact spec validate {contract_path}' to see detailed errors",
                                )
                                report.add_deviation(deviation)
                                console.print(
                                    f"  [bold yellow]⚠[/bold yellow] {contract_path.name} has validation issues"
                                )
                                if result.errors:
                                    for error in result.errors[:2]:
                                        console.print(f"    - {error}")
                            else:
                                console.print(f"  [bold green]✓[/bold green] {contract_path.name} is valid")
                        except Exception as e:
                            console.print(f"  [bold yellow]⚠[/bold yellow] Validation error: {e!s}")
                            deviation = Deviation(
                                type=DeviationType.CONTRACT_VIOLATION,
                                severity=DeviationSeverity.LOW,
                                description=f"API contract validation error: {contract_path.name} - {e!s}",
                                location=str(contract_path),
                                fix_hint=f"Run 'specfact spec validate {contract_path}' to diagnose",
                            )
                            report.add_deviation(deviation)
                    if len(contract_files) > 5:
                        console.print(
                            f"[dim]... and {len(contract_files) - 5} more contract(s) (run 'specfact spec validate' to validate all)[/dim]"
                        )
                else:
                    console.print("[dim]No API contracts found in bundle[/dim]")

            # Generate output report (Phase 8.5: bundle-specific location)
            output_format_str = output_format.lower()
            if out is None:
                # Use bundle-specific enforcement report path
                extension = "md" if output_format_str == "markdown" else output_format_str
                out = SpecFactStructure.get_bundle_enforcement_report_path(bundle_name=bundle, base_path=base_path)
                # Update extension if needed
                if extension != "yaml" and out.suffix != f".{extension}":
                    out = out.with_suffix(f".{extension}")

            # Save report
            if output_format_str == "markdown":
                _save_markdown_report(out, report, sdd_manifest, bundle, project_hash)
            elif output_format_str == "json":
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

            # Exit with appropriate code and clear error messages
            if not report.passed:
                console.print("\n[bold red]✗[/bold red] SDD validation failed")
                console.print("\n[bold yellow]Issues Found:[/bold yellow]")

                # Group deviations by type for clearer messaging
                hash_mismatches = [d for d in report.deviations if d.type == DeviationType.HASH_MISMATCH]
                coverage_issues = [d for d in report.deviations if d.type == DeviationType.COVERAGE_THRESHOLD]

                if hash_mismatches:
                    console.print("\n[bold red]1. Hash Mismatch (HIGH)[/bold red]")
                    console.print("   The project bundle has been modified since the SDD manifest was created.")
                    console.print(f"   [dim]SDD hash: {sdd_manifest.plan_bundle_hash[:16]}...[/dim]")
                    console.print(f"   [dim]Bundle hash: {project_hash[:16]}...[/dim]")
                    console.print("\n   [bold]Why this happens:[/bold]")
                    console.print("   The hash changes when you modify:")
                    console.print("   - Features (add/remove/update)")
                    console.print("   - Stories (add/remove/update)")
                    console.print("   - Product, idea, business, or clarifications")
                    console.print(
                        f"\n   [bold]Fix:[/bold] Run [cyan]specfact plan harden {bundle}[/cyan] to update the SDD manifest"
                    )
                    console.print(
                        "   [dim]This updates the SDD with the current bundle hash and regenerates HOW sections[/dim]"
                    )

                if coverage_issues:
                    console.print("\n[bold yellow]2. Coverage Thresholds Not Met (MEDIUM)[/bold yellow]")
                    console.print("   Contract density metrics are below required thresholds:")
                    console.print(
                        f"   - Contracts/story: {metrics.contracts_per_story:.2f} (required: {thresholds.contracts_per_story})"
                    )
                    console.print(
                        f"   - Invariants/feature: {metrics.invariants_per_feature:.2f} (required: {thresholds.invariants_per_feature})"
                    )
                    console.print("\n   [bold]Fix:[/bold] Add more contracts to stories and invariants to features")
                    console.print("   [dim]Tip: Use 'specfact plan review' to identify areas needing contracts[/dim]")

                console.print("\n[bold cyan]Next Steps:[/bold cyan]")
                if hash_mismatches:
                    console.print(f"   1. Update SDD: [cyan]specfact plan harden {bundle}[/cyan]")
                if coverage_issues:
                    console.print("   2. Add contracts: Review features and add @icontract decorators")
                    console.print("   3. Re-validate: Run this command again after fixes")

                if is_debug_mode():
                    debug_log_operation(
                        "command",
                        "enforce sdd",
                        "failed",
                        error="SDD validation failed",
                        extra={"reason": "deviations", "total_deviations": report.total_deviations},
                    )
                record({"passed": False, "deviations": report.total_deviations})
                raise typer.Exit(1)

            console.print("\n[bold green]✓[/bold green] SDD validation passed")
            record({"passed": True, "deviations": 0})
            if is_debug_mode():
                debug_log_operation(
                    "command", "enforce sdd", "success", extra={"bundle": bundle, "report_path": str(out)}
                )
                debug_print("[dim]enforce sdd: success[/dim]")

        except Exception as e:
            if is_debug_mode():
                debug_log_operation(
                    "command", "enforce sdd", "failed", error=str(e), extra={"reason": type(e).__name__}
                )
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

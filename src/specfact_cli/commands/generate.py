"""Generate command - Generate artifacts from SDD and plans.

This module provides commands for generating contract stubs, CrossHair harnesses,
and other artifacts from SDD manifests and plan bundles.
"""

from __future__ import annotations

from pathlib import Path

import typer
from beartype import beartype
from icontract import ensure, require
from rich.console import Console

from specfact_cli.generators.contract_generator import ContractGenerator
from specfact_cli.migrations.plan_migrator import load_plan_bundle
from specfact_cli.models.sdd import SDDManifest
from specfact_cli.utils import print_error, print_info, print_success, print_warning
from specfact_cli.utils.structured_io import load_structured_file


app = typer.Typer(help="Generate artifacts from SDD and plans")
console = Console()


@app.command("contracts")
@beartype
@require(lambda sdd: sdd is None or isinstance(sdd, Path), "SDD must be None or Path")
@require(lambda plan: plan is None or isinstance(plan, Path), "Plan must be None or Path")
@require(lambda base_path: base_path is None or isinstance(base_path, Path), "Base path must be None or Path")
@ensure(lambda result: result is None, "Must return None")
def generate_contracts(
    sdd: Path | None = typer.Option(
        None,
        "--sdd",
        help="Path to SDD manifest (default: .specfact/sdd.yaml)",
    ),
    plan: Path | None = typer.Option(
        None,
        "--plan",
        help="Path to plan bundle (default: active plan)",
    ),
    base_path: Path | None = typer.Option(
        None,
        "--base-path",
        help="Base directory for output (default: current directory)",
    ),
    non_interactive: bool = typer.Option(
        False,
        "--non-interactive",
        help="Non-interactive mode (for CI/CD automation)",
    ),
) -> None:
    """
    Generate contract stubs from SDD HOW sections.

    Parses SDD manifest HOW section (invariants, contracts) and generates
    contract stub files with icontract decorators, beartype type checks,
    and CrossHair harness templates.

    Generated files are saved to `.specfact/contracts/` with one file per feature.

    Example:
        specfact generate contracts
        specfact generate contracts --sdd .specfact/sdd.yaml --plan .specfact/plans/main.bundle.yaml
    """
    from specfact_cli.telemetry import telemetry

    telemetry_metadata = {
        "non_interactive": non_interactive,
    }

    with telemetry.track_command("generate.contracts", telemetry_metadata) as record:
        try:
            # Determine base path
            base_path = Path(".").resolve() if base_path is None else Path(base_path).resolve()

            # Import here to avoid circular imports
            from specfact_cli.utils.bundle_loader import BundleFormat, detect_bundle_format
            from specfact_cli.utils.structure import SpecFactStructure

            # Determine plan path
            if plan is None:
                # Try to find active plan
                plan_path = SpecFactStructure.get_default_plan_path(base_path)
                if plan_path is None or not plan_path.exists():
                    print_error("No active plan found")
                    print_info("Run 'specfact plan init' or specify --plan")
                    raise typer.Exit(1)
            else:
                plan_path = Path(plan).resolve()

            if not plan_path.exists():
                print_error(f"Plan bundle not found: {plan_path}")
                raise typer.Exit(1)

            # Determine SDD path based on bundle format
            if sdd is None:
                # Detect bundle format to determine SDD path
                format_type, _ = detect_bundle_format(plan_path)
                if format_type == BundleFormat.MODULAR:
                    # Modular bundle: SDD is at .specfact/sdd/<bundle-name>.yaml
                    if plan_path.is_dir():
                        bundle_name = plan_path.name
                    else:
                        # If plan_path is a file, try to find parent bundle directory
                        bundle_name = plan_path.parent.name if plan_path.parent.name != "projects" else plan_path.stem
                    sdd_path = base_path / SpecFactStructure.SDD / f"{bundle_name}.yaml"
                else:
                    # Legacy monolithic: SDD is at .specfact/sdd.yaml
                    sdd_path = SpecFactStructure.get_sdd_path(base_path)
            else:
                sdd_path = Path(sdd).resolve()

            if not sdd_path.exists():
                print_error(f"SDD manifest not found: {sdd_path}")
                print_info("Run 'specfact plan harden' to create SDD manifest")
                raise typer.Exit(1)

            # Load SDD manifest
            print_info(f"Loading SDD manifest: {sdd_path}")
            sdd_data = load_structured_file(sdd_path)
            sdd_manifest = SDDManifest(**sdd_data)

            # Load plan bundle (handle both modular and monolithic formats)
            print_info(f"Loading plan bundle: {plan_path}")
            format_type, _ = detect_bundle_format(plan_path)

            plan_hash = None
            if format_type == BundleFormat.MODULAR:
                # Load modular ProjectBundle and convert to PlanBundle for compatibility
                from specfact_cli.commands.plan import _convert_project_bundle_to_plan_bundle
                from specfact_cli.utils.bundle_loader import load_project_bundle

                project_bundle = load_project_bundle(plan_path, validate_hashes=False)

                # Compute hash from ProjectBundle (same way as plan harden does)
                summary = project_bundle.compute_summary(include_hash=True)
                plan_hash = summary.content_hash

                # Convert to PlanBundle for ContractGenerator compatibility
                plan_bundle = _convert_project_bundle_to_plan_bundle(project_bundle)
            else:
                # Load monolithic PlanBundle
                plan_bundle = load_plan_bundle(plan_path)

                # Compute hash from PlanBundle
                plan_bundle.update_summary(include_hash=True)
                plan_hash = (
                    plan_bundle.metadata.summary.content_hash
                    if plan_bundle.metadata and plan_bundle.metadata.summary
                    else None
                )

            if not plan_hash:
                print_error("Failed to compute plan bundle hash")
                raise typer.Exit(1)

            # Verify hash match (SDD uses plan_bundle_hash field)
            if sdd_manifest.plan_bundle_hash != plan_hash:
                print_error("SDD manifest hash does not match plan bundle hash")
                print_info("Run 'specfact plan harden' to update SDD manifest")
                raise typer.Exit(1)

            # Generate contracts
            print_info("Generating contract stubs from SDD HOW sections...")
            generator = ContractGenerator()
            result = generator.generate_contracts(sdd_manifest, plan_bundle, base_path)

            # Display results
            if result["errors"]:
                print_error(f"Errors during generation: {len(result['errors'])}")
                for error in result["errors"]:
                    print_error(f"  - {error}")

            if result["generated_files"]:
                print_success(f"Generated {len(result['generated_files'])} contract file(s):")
                for file_path in result["generated_files"]:
                    print_info(f"  - {file_path}")

                # Display statistics
                total_contracts = sum(result["contracts_per_story"].values())
                total_invariants = sum(result["invariants_per_feature"].values())
                print_info(f"Total contracts: {total_contracts}")
                print_info(f"Total invariants: {total_invariants}")

                # Check coverage thresholds
                if sdd_manifest.coverage_thresholds:
                    thresholds = sdd_manifest.coverage_thresholds
                    avg_contracts_per_story = (
                        total_contracts / len(result["contracts_per_story"]) if result["contracts_per_story"] else 0.0
                    )
                    avg_invariants_per_feature = (
                        total_invariants / len(result["invariants_per_feature"])
                        if result["invariants_per_feature"]
                        else 0.0
                    )

                    if avg_contracts_per_story < thresholds.contracts_per_story:
                        print_error(
                            f"Contract coverage below threshold: {avg_contracts_per_story:.2f} < {thresholds.contracts_per_story}"
                        )
                    else:
                        print_success(
                            f"Contract coverage meets threshold: {avg_contracts_per_story:.2f} >= {thresholds.contracts_per_story}"
                        )

                    if avg_invariants_per_feature < thresholds.invariants_per_feature:
                        print_error(
                            f"Invariant coverage below threshold: {avg_invariants_per_feature:.2f} < {thresholds.invariants_per_feature}"
                        )
                    else:
                        print_success(
                            f"Invariant coverage meets threshold: {avg_invariants_per_feature:.2f} >= {thresholds.invariants_per_feature}"
                        )

                record(
                    {
                        "generated_files": len(result["generated_files"]),
                        "total_contracts": total_contracts,
                        "total_invariants": total_invariants,
                    }
                )
            else:
                print_warning("No contract files generated (no contracts/invariants found in SDD HOW section)")

        except Exception as e:
            print_error(f"Failed to generate contracts: {e}")
            record({"error": str(e)})
            raise typer.Exit(1) from e

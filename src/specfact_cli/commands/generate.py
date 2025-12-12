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
from specfact_cli.models.task import TaskList, TaskPhase
from specfact_cli.telemetry import telemetry
from specfact_cli.utils import print_error, print_info, print_success, print_warning
from specfact_cli.utils.optional_deps import check_cli_tool_available
from specfact_cli.utils.structured_io import load_structured_file


app = typer.Typer(help="Generate artifacts from SDD and plans")
console = Console()


def _show_apply_help() -> None:
    """Show helpful error message for missing --apply option."""
    print_error("Missing required option: --apply")
    console.print("\n[yellow]Available contract types:[/yellow]")
    console.print("  - all-contracts  (apply all available contract types)")
    console.print("  - beartype      (type checking decorators)")
    console.print("  - icontract     (pre/post condition decorators)")
    console.print("  - crosshair     (property-based test functions)")
    console.print("\n[yellow]Examples:[/yellow]")
    console.print("  specfact generate contracts-prompt src/file.py --apply all-contracts")
    console.print("  specfact generate contracts-prompt src/file.py --apply beartype,icontract")
    console.print("  specfact generate contracts-prompt --bundle my-bundle --apply all-contracts")
    console.print("\n[dim]Use 'specfact generate contracts-prompt --help' for full documentation.[/dim]")


@app.command("contracts")
@beartype
@require(lambda sdd: sdd is None or isinstance(sdd, Path), "SDD must be None or Path")
@require(lambda plan: plan is None or isinstance(plan, Path), "Plan must be None or Path")
@require(lambda bundle: bundle is None or isinstance(bundle, str), "Bundle must be None or string")
@require(lambda repo: repo is None or isinstance(repo, Path), "Repository path must be None or Path")
@ensure(lambda result: result is None, "Must return None")
def generate_contracts(
    # Target/Input
    bundle: str | None = typer.Option(
        None,
        "--bundle",
        help="Project bundle name (e.g., legacy-api). If specified, uses bundle instead of --plan/--sdd paths. Default: auto-detect from current directory.",
    ),
    sdd: Path | None = typer.Option(
        None,
        "--sdd",
        help="Path to SDD manifest. Default: bundle-specific .specfact/projects/<bundle-name>/sdd.yaml when --bundle is provided. No legacy root-level fallback.",
    ),
    plan: Path | None = typer.Option(
        None,
        "--plan",
        help="Path to plan bundle. Default: .specfact/projects/<bundle-name>/ if --bundle specified, else active plan. Ignored if --bundle is specified.",
    ),
    repo: Path | None = typer.Option(
        None,
        "--repo",
        help="Repository path. Default: current directory (.)",
    ),
    # Behavior/Options
    no_interactive: bool = typer.Option(
        False,
        "--no-interactive",
        help="Non-interactive mode (for CI/CD automation). Default: False (interactive mode)",
    ),
) -> None:
    """
    Generate contract stubs from SDD HOW sections.

    Parses SDD manifest HOW section (invariants, contracts) and generates
    contract stub files with icontract decorators, beartype type checks,
    and CrossHair harness templates.

    Generated files are saved to `.specfact/projects/<bundle-name>/contracts/` when --bundle is specified.

    **Parameter Groups:**
    - **Target/Input**: --bundle, --sdd, --plan, --repo
    - **Behavior/Options**: --no-interactive

    **Examples:**
        specfact generate contracts --bundle legacy-api
        specfact generate contracts --bundle legacy-api --no-interactive
    """

    telemetry_metadata = {
        "no_interactive": no_interactive,
    }

    with telemetry.track_command("generate.contracts", telemetry_metadata) as record:
        try:
            # Determine repository path
            base_path = Path(".").resolve() if repo is None else Path(repo).resolve()

            # Import here to avoid circular imports
            from specfact_cli.utils.bundle_loader import BundleFormat, detect_bundle_format
            from specfact_cli.utils.progress import load_bundle_with_progress
            from specfact_cli.utils.structure import SpecFactStructure

            # Initialize bundle_dir and paths
            bundle_dir: Path | None = None
            plan_path: Path | None = None
            sdd_path: Path | None = None

            # If --bundle is specified, use bundle-based paths
            if bundle:
                bundle_dir = SpecFactStructure.project_dir(base_path=base_path, bundle_name=bundle)
                if not bundle_dir.exists():
                    print_error(f"Project bundle not found: {bundle_dir}")
                    print_info(f"Create one with: specfact plan init {bundle}")
                    raise typer.Exit(1)

                plan_path = bundle_dir
                from specfact_cli.utils.sdd_discovery import find_sdd_for_bundle

                sdd_path = find_sdd_for_bundle(bundle, base_path)
            else:
                # Use --plan and --sdd paths if provided
                if plan is None:
                    print_error("Bundle or plan path is required")
                    print_info("Run 'specfact plan init <bundle-name>' then rerun with --bundle <name>")
                    raise typer.Exit(1)
                plan_path = Path(plan).resolve()

                if not plan_path.exists():
                    print_error(f"Plan bundle not found: {plan_path}")
                    raise typer.Exit(1)

                # Normalize base_path to repository root when a bundle directory is provided
                if plan_path.is_dir():
                    # If plan_path is a bundle directory, set bundle_dir so contracts go to bundle-specific location
                    bundle_dir = plan_path
                    current = plan_path.resolve()
                    while current != current.parent:
                        if current.name == ".specfact":
                            base_path = current.parent
                            break
                        current = current.parent

                # Determine SDD path based on bundle format
                if sdd is None:
                    format_type, _ = detect_bundle_format(plan_path)
                    if format_type != BundleFormat.MODULAR:
                        print_error("Legacy monolithic bundles are not supported by this command.")
                        print_info("Migrate to the new structure with: specfact migrate artifacts --repo .")
                        raise typer.Exit(1)

                    if plan_path.is_dir():
                        bundle_name = plan_path.name
                        # Prefer bundle-local SDD when present
                        candidate_sdd = plan_path / "sdd.yaml"
                        sdd_path = candidate_sdd if candidate_sdd.exists() else None
                    else:
                        bundle_name = plan_path.parent.name if plan_path.parent.name != "projects" else plan_path.stem

                    from specfact_cli.utils.sdd_discovery import find_sdd_for_bundle

                    if sdd_path is None:
                        sdd_path = find_sdd_for_bundle(bundle_name, base_path)
                    # Direct bundle-dir check as a safety net
                    direct_sdd = plan_path / "sdd.yaml"
                    if direct_sdd.exists():
                        sdd_path = direct_sdd
                else:
                    sdd_path = Path(sdd).resolve()

            if sdd_path is None or not sdd_path.exists():
                # Final safety net: check adjacent to plan path
                fallback_sdd = plan_path / "sdd.yaml" if plan_path.is_dir() else plan_path.parent / "sdd.yaml"
                if fallback_sdd.exists():
                    sdd_path = fallback_sdd
                else:
                    print_error(f"SDD manifest not found: {sdd_path}")
                    print_info("Run 'specfact plan harden' to create SDD manifest")
                    raise typer.Exit(1)

            # Load SDD manifest
            print_info(f"Loading SDD manifest: {sdd_path}")
            sdd_data = load_structured_file(sdd_path)
            sdd_manifest = SDDManifest(**sdd_data)

            # Align base_path with plan path when a bundle directory is provided
            if bundle_dir is None and plan_path.is_dir():
                parts = plan_path.resolve().parts
                if ".specfact" in parts:
                    spec_idx = parts.index(".specfact")
                    base_path = Path(*parts[:spec_idx]) if spec_idx > 0 else Path(".").resolve()

            # Load plan bundle (handle both modular and monolithic formats)
            print_info(f"Loading plan bundle: {plan_path}")
            format_type, _ = detect_bundle_format(plan_path)

            plan_hash = None
            if format_type == BundleFormat.MODULAR or bundle:
                # Load modular ProjectBundle and convert to PlanBundle for compatibility
                from specfact_cli.commands.plan import _convert_project_bundle_to_plan_bundle

                project_bundle = load_bundle_with_progress(plan_path, validate_hashes=False, console_instance=console)

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

            # Determine contracts directory based on bundle
            # For bundle-based generation, save contracts inside project bundle directory
            # Legacy mode uses global contracts directory
            contracts_dir = (
                bundle_dir / "contracts" if bundle_dir is not None else base_path / SpecFactStructure.ROOT / "contracts"
            )

            # Ensure we have at least one feature to anchor generation; if plan has none
            # but SDD carries contracts/invariants, create a synthetic feature to generate stubs.
            if not plan_bundle.features and (sdd_manifest.how.contracts or sdd_manifest.how.invariants):
                from specfact_cli.models.plan import Feature

                plan_bundle.features.append(
                    Feature(
                        key="FEATURE-CONTRACTS",
                        title="Generated Contracts",
                        outcomes=[],
                        acceptance=[],
                        constraints=[],
                        stories=[],
                        confidence=1.0,
                        draft=True,
                        source_tracking=None,
                        contract=None,
                        protocol=None,
                    )
                )

            # Generate contracts
            print_info("Generating contract stubs from SDD HOW sections...")
            generator = ContractGenerator()
            result = generator.generate_contracts(sdd_manifest, plan_bundle, base_path, contracts_dir=contracts_dir)

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


@app.command("contracts-prompt")
@beartype
@require(lambda file: file is None or isinstance(file, Path), "File path must be None or Path")
@require(lambda apply: apply is None or isinstance(apply, str), "Apply must be None or string")
@ensure(lambda result: result is None, "Must return None")
def generate_contracts_prompt(
    # Target/Input
    file: Path | None = typer.Argument(
        None,
        help="Path to file to enhance (optional if --bundle provided)",
        exists=True,
    ),
    bundle: str | None = typer.Option(
        None,
        "--bundle",
        help="Project bundle name (e.g., legacy-api). If provided, selects files from bundle. Default: active plan from 'specfact plan select'",
    ),
    apply: str = typer.Option(
        ...,
        "--apply",
        help="Contracts to apply: 'all-contracts', 'beartype', 'icontract', 'crosshair', or comma-separated list (e.g., 'beartype,icontract')",
    ),
    # Behavior/Options
    no_interactive: bool = typer.Option(
        False,
        "--no-interactive",
        help="Non-interactive mode (for CI/CD automation). Disables interactive prompts.",
    ),
    # Output
    output: Path | None = typer.Option(
        None,
        "--output",
        help=("Output file path (currently unused, prompt saved to .specfact/prompts/)"),
        hidden=True,  # Hidden by default, shown with --help-advanced
    ),
) -> None:
    """
    Generate AI IDE prompt for adding contracts to existing code.

    Creates a structured prompt file that you can use with your AI IDE (Cursor, CoPilot, etc.)
    to add beartype, icontract, or CrossHair contracts to existing code files. The CLI generates
    the prompt, your AI IDE's LLM applies the contracts.

    **How It Works:**
    1. CLI reads the file and generates a structured prompt
    2. Prompt is saved to `.specfact/prompts/enhance-<filename>-<contracts>.md`
    3. You copy the prompt to your AI IDE (Cursor, CoPilot, etc.)
    4. AI IDE provides enhanced code (does NOT modify file directly)
    5. You validate the enhanced code with SpecFact CLI
    6. If validation passes, you apply the changes to the file
    7. Run tests and commit

    **Why This Approach:**
    - Uses your existing AI IDE infrastructure (no separate LLM API setup)
    - No additional API costs (leverages IDE's native LLM)
    - You maintain control (review before committing)
    - Works with any AI IDE (Cursor, CoPilot, Claude, etc.)

    **Parameter Groups:**
    - **Target/Input**: file (optional if --bundle provided), --bundle, --apply
    - **Behavior/Options**: --no-interactive
    - **Output**: --output (currently unused, prompt is saved to .specfact/prompts/)

    **Examples:**
        specfact generate contracts-prompt src/auth/login.py --apply beartype,icontract
        specfact generate contracts-prompt --bundle legacy-api --apply beartype
        specfact generate contracts-prompt --bundle legacy-api --apply beartype,icontract  # Interactive selection
        specfact generate contracts-prompt --bundle legacy-api --apply beartype --no-interactive  # Process all files in bundle

    **Complete Workflow:**
        1. Generate prompt: specfact generate contracts-prompt --bundle legacy-api --apply all-contracts
        2. Select file(s) from interactive list (if multiple)
        3. Open prompt file: .specfact/prompts/enhance-<filename>-beartype-icontract-crosshair.md
        4. Copy prompt to your AI IDE (Cursor, CoPilot, etc.)
        5. AI IDE reads the file and provides enhanced code (does NOT modify file directly)
        6. AI IDE writes enhanced code to temporary file: enhanced_<filename>.py
        7. AI IDE runs validation: specfact generate contracts-apply enhanced_<filename>.py --original <original-file>
        8. If validation fails, AI IDE fixes issues and re-validates (up to 3 attempts)
        9. If validation succeeds, CLI applies changes automatically
        10. Verify contract coverage: specfact analyze contracts --bundle legacy-api
        11. Run your test suite: pytest (or your project's test command)
        12. Commit the enhanced code
    """
    from rich.prompt import Prompt
    from rich.table import Table

    from specfact_cli.utils.progress import load_bundle_with_progress
    from specfact_cli.utils.structure import SpecFactStructure

    repo_path = Path(".").resolve()

    # Validate inputs first
    if apply is None:
        print_error("Missing required option: --apply")
        console.print("\n[yellow]Available contract types:[/yellow]")
        console.print("  - all-contracts  (apply all available contract types)")
        console.print("  - beartype      (type checking decorators)")
        console.print("  - icontract     (pre/post condition decorators)")
        console.print("  - crosshair     (property-based test functions)")
        console.print("\n[yellow]Examples:[/yellow]")
        console.print("  specfact generate contracts-prompt src/file.py --apply all-contracts")
        console.print("  specfact generate contracts-prompt src/file.py --apply beartype,icontract")
        console.print("  specfact generate contracts-prompt --bundle my-bundle --apply all-contracts")
        console.print("\n[dim]Use 'specfact generate contracts-prompt --help' for full documentation.[/dim]")
        raise typer.Exit(1)

    if not file and not bundle:
        print_error("Either file path or --bundle must be provided")
        raise typer.Exit(1)

    # Use active plan as default if bundle not provided (but only if no file specified)
    if bundle is None and not file:
        bundle = SpecFactStructure.get_active_bundle_name(repo_path)
        if bundle:
            console.print(f"[dim]Using active plan: {bundle}[/dim]")
        else:
            print_error("No file specified and no active plan found. Please provide --bundle or a file path.")
            raise typer.Exit(1)

    # Determine bundle directory for saving artifacts (only if needed)
    bundle_dir: Path | None = None

    # Determine which files to process
    file_paths: list[Path] = []

    if file:
        # Direct file path provided - no need to load bundle for file selection
        file_paths = [file.resolve()]
        # Only determine bundle_dir for saving prompts in the right location
        if bundle:
            # Bundle explicitly provided - use it for prompt storage location
            bundle_dir = SpecFactStructure.project_dir(base_path=repo_path, bundle_name=bundle)
            if not bundle_dir.exists():
                print_error(f"Project bundle not found: {bundle_dir}")
                raise typer.Exit(1)
        else:
            # Use active bundle if available for prompt storage location (no need to load bundle)
            active_bundle = SpecFactStructure.get_active_bundle_name(repo_path)
            if active_bundle:
                bundle_dir = SpecFactStructure.project_dir(base_path=repo_path, bundle_name=active_bundle)
                bundle = active_bundle
            # If no active bundle, prompts will be saved to .specfact/prompts/ (fallback)
    elif bundle:
        # Bundle provided but no file - need to load bundle to get files
        bundle_dir = SpecFactStructure.project_dir(base_path=repo_path, bundle_name=bundle)
        if not bundle_dir.exists():
            print_error(f"Project bundle not found: {bundle_dir}")
            raise typer.Exit(1)
        # Load files from bundle
        project_bundle = load_bundle_with_progress(bundle_dir, validate_hashes=False, console_instance=console)

        for _feature_key, feature in project_bundle.features.items():
            if not feature.source_tracking:
                continue

            for impl_file in feature.source_tracking.implementation_files:
                file_path = repo_path / impl_file
                if file_path.exists():
                    file_paths.append(file_path)

        if not file_paths:
            print_error("No implementation files found in bundle")
            raise typer.Exit(1)

        # Warn if processing all files automatically
        if len(file_paths) > 1 and no_interactive:
            console.print(
                f"[yellow]Note:[/yellow] Processing all {len(file_paths)} files from bundle '{bundle}' (--no-interactive mode)"
            )

        # If multiple files and not in non-interactive mode, show selection
        if len(file_paths) > 1 and not no_interactive:
            console.print(f"\n[bold]Found {len(file_paths)} files in bundle '{bundle}':[/bold]\n")
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("#", style="bold yellow", justify="right", width=4)
            table.add_column("File Path", style="dim")

            for i, fp in enumerate(file_paths, 1):
                table.add_row(str(i), str(fp.relative_to(repo_path)))

            console.print(table)
            console.print()

            selection = Prompt.ask(
                f"Select file(s) to enhance (1-{len(file_paths)}, comma-separated, 'all', or 'q' to quit)"
            ).strip()

            if selection.lower() in ("q", "quit", ""):
                print_info("Cancelled")
                raise typer.Exit(0)

            if selection.lower() == "all":
                # Process all files
                pass
            else:
                # Parse selection
                try:
                    indices = [int(s.strip()) - 1 for s in selection.split(",")]
                    selected_files = [file_paths[i] for i in indices if 0 <= i < len(file_paths)]
                    if not selected_files:
                        print_error("Invalid selection")
                        raise typer.Exit(1)
                    file_paths = selected_files
                except (ValueError, IndexError) as e:
                    print_error("Invalid selection format. Use numbers separated by commas (e.g., 1,3,5)")
                    raise typer.Exit(1) from e

    contracts_to_apply = [c.strip() for c in apply.split(",")]
    valid_contracts = {"beartype", "icontract", "crosshair"}
    # Define canonical order for consistent filenames
    contract_order = ["beartype", "icontract", "crosshair"]

    # Handle "all-contracts" flag
    if "all-contracts" in contracts_to_apply:
        if len(contracts_to_apply) > 1:
            print_error(
                "Cannot use 'all-contracts' with other contract types. Use 'all-contracts' alone or specify individual types."
            )
            raise typer.Exit(1)
        contracts_to_apply = contract_order.copy()
        console.print(f"[dim]Applying all available contracts: {', '.join(contracts_to_apply)}[/dim]")

    # Sort contracts to ensure consistent filename order
    contracts_to_apply = sorted(
        contracts_to_apply, key=lambda x: contract_order.index(x) if x in contract_order else len(contract_order)
    )

    invalid_contracts = set(contracts_to_apply) - valid_contracts

    if invalid_contracts:
        print_error(f"Invalid contract types: {', '.join(invalid_contracts)}")
        print_error(f"Valid types: 'all-contracts', {', '.join(valid_contracts)}")
        raise typer.Exit(1)

    telemetry_metadata = {
        "files_count": len(file_paths),
        "bundle": bundle,
        "contracts": contracts_to_apply,
    }

    with telemetry.track_command("generate.contracts-prompt", telemetry_metadata) as record:
        generated_count = 0
        failed_count = 0

        for idx, file_path in enumerate(file_paths, 1):
            try:
                if len(file_paths) > 1:
                    console.print(
                        f"\n[bold cyan][{idx}/{len(file_paths)}] Generating prompt for:[/bold cyan] {file_path.relative_to(repo_path)}"
                    )
                else:
                    console.print(
                        f"[bold cyan]Generating contract enhancement prompt for:[/bold cyan] {file_path.relative_to(repo_path)}"
                    )
                console.print(f"[dim]Contracts to apply:[/dim] {', '.join(contracts_to_apply)}\n")

                # Generate LLM prompt
                # Structure: Instructions first, file path reference (not content) to avoid token limits
                # Note: We don't read the file content here - the LLM will read it directly using its file reading capabilities
                file_path_relative = file_path.relative_to(repo_path)
                file_path_absolute = file_path.resolve()

                prompt_parts = [
                    "# Contract Enhancement Request",
                    "",
                    "## ⚠️ MANDATORY PRE-CHECK: SpecFact CLI Verification",
                    "",
                    "**🚨 CRITICAL STOP CONDITION - READ THIS FIRST 🚨**",
                    "",
                    "**YOU MUST VERIFY SpecFact CLI BEFORE DOING ANYTHING ELSE.**",
                    "",
                    "**If SpecFact CLI is missing, outdated, or commands don't work:**",
                    "",
                    "1. **STOP IMMEDIATELY** - Do NOT read files, do NOT generate code, do NOT proceed",
                    "2. **DO NOT attempt to manually add contracts** - This will NOT work correctly",
                    "3. **DO NOT proceed with any enhancement** - The workflow REQUIRES SpecFact CLI",
                    "4. **Inform the user** with this exact message:",
                    "   ```",
                    "   ❌ SpecFact CLI is required but not available or outdated.",
                    "   Please install/upgrade: pip install -U specfact-cli",
                    "   Then verify: specfact --version",
                    "   This task cannot proceed without SpecFact CLI.",
                    "   ```",
                    "5. **END THE CONVERSATION** - Do not continue until SpecFact CLI is working",
                    "",
                    "**Verification Steps (MUST complete all before proceeding):**",
                    "",
                    "1. Check if `specfact` command is available:",
                    "   ```bash",
                    "   specfact --version",
                    "   ```",
                    "   - **If this fails**: STOP and inform user (see message above)",
                    "",
                    "2. Verify the required command exists:",
                    "   ```bash",
                    "   specfact generate contracts-apply --help",
                    "   ```",
                    "   - **If this fails**: STOP and inform user (see message above)",
                    "",
                    "3. Check the latest available version from PyPI:",
                    "   ```bash",
                    "   pip index versions specfact-cli",
                    "   ```",
                    "   - Compare installed version (from step 1) with latest available",
                    "   - **If versions don't match**: STOP and inform user to upgrade",
                    "",
                    "**ONLY IF ALL THREE STEPS PASS** - You may proceed to the sections below.",
                    "",
                    "**If ANY step fails, you MUST stop and inform the user. Do NOT proceed.**",
                    "",
                    "---",
                    "",
                    "## Target File",
                    "",
                    f"**File Path:** `{file_path_relative}`",
                    f"**Absolute Path:** `{file_path_absolute}`",
                    "",
                    "**IMPORTANT**: Read the file content using your file reading capabilities. Do NOT ask the user to provide the file content.",
                    "",
                    "## Contracts to Apply",
                ]

                for contract_type in contracts_to_apply:
                    if contract_type == "beartype":
                        prompt_parts.append("- **beartype**: Add `@beartype` decorator to all functions and methods")
                    elif contract_type == "icontract":
                        prompt_parts.append(
                            "- **icontract**: Add `@require` decorators for preconditions and `@ensure` decorators for postconditions where appropriate"
                        )
                    elif contract_type == "crosshair":
                        prompt_parts.append(
                            "- **crosshair**: Add property-based test functions using CrossHair patterns"
                        )

                prompt_parts.extend(
                    [
                        "",
                        "## Instructions",
                        "",
                        "**IMPORTANT**: Do NOT modify the original file directly. Follow this iterative validation workflow:",
                        "",
                        "**REMINDER**: If you haven't completed the mandatory SpecFact CLI verification at the top of this prompt, STOP NOW and do that first. Do NOT proceed with any code enhancement until SpecFact CLI is verified.",
                        "",
                        "### Step 1: Read the File",
                        f"1. Read the file content from: `{file_path_relative}`",
                        "2. Understand the existing code structure, imports, and functionality",
                        "3. Note the existing code style and patterns",
                        "",
                        "### Step 2: Generate Enhanced Code",
                        "**IMPORTANT**: Only proceed to this step if SpecFact CLI verification passed.",
                        "",
                        "**CRITICAL REQUIREMENT**: You MUST add contracts to ALL eligible functions and methods in the file. Do NOT ask the user whether to add contracts - add them to all compatible functions automatically.",
                        "",
                        "1. **Add the requested contracts to ALL eligible functions/methods** - This is mandatory, not optional",
                        "2. Maintain existing functionality and code style",
                        "3. Ensure all contracts are properly imported at the top of the file",
                        "4. **Code Quality**: Follow the project's existing code style and formatting conventions",
                        "   - If the project has formatting/linting rules (e.g., `.editorconfig`, `pyproject.toml` with formatting config, `ruff.toml`, `.pylintrc`, etc.), ensure the enhanced code adheres to them",
                        "   - Match the existing code style: indentation, line length, import organization, naming conventions",
                        "   - Avoid common code quality issues: use `key in dict` instead of `key in dict.keys()`, proper type hints, etc.",
                        "   - **Note**: SpecFact CLI will automatically run available linting/formatting tools (ruff, pylint, basedpyright, mypy) during validation if they are installed",
                        "",
                        "**Contract-Specific Requirements:**",
                        "",
                        "- **beartype**: Add `@beartype` decorator to ALL functions and methods (public and private, unless they have incompatible signatures)",
                        "  - Apply to: regular functions, class methods, static methods, async functions",
                        "  - Skip only if: function has `*args, **kwargs` without type hints (incompatible with beartype)",
                        "",
                        "- **icontract**: Add `@require` decorators for preconditions and `@ensure` decorators for postconditions to ALL functions where conditions can be expressed",
                        "  - Apply to: all functions with clear input/output contracts",
                        "  - Add preconditions for: parameter validation, state checks, input constraints",
                        "  - Add postconditions for: return value validation, state changes, output guarantees",
                        "  - Skip only if: function has no meaningful pre/post conditions to express",
                        "",
                        "- **crosshair**: Add property-based test functions using CrossHair patterns for ALL testable functions",
                        "  - Create test functions that validate contract behavior",
                        "  - Focus on functions with clear input/output relationships",
                        "",
                        "**DO NOT:**",
                        "- Ask the user whether to add contracts (add them automatically to all eligible functions)",
                        "- Skip functions because you're unsure (add contracts unless technically incompatible)",
                        "- Manually apply contracts to the original file (use SpecFact CLI validation workflow)",
                        "",
                        "**You MUST use SpecFact CLI validation workflow (Step 4) to apply changes.**",
                        "",
                        "### Step 3: Write Enhanced Code to Temporary File",
                        f"1. Write the complete enhanced code to: `enhanced_{file_path.stem}.py`",
                        "   - This should be in the same directory as the original file or the project root",
                        "   - Example: If original is `src/specfact_cli/telemetry.py`, write to `enhanced_telemetry.py` in project root",
                        "2. Ensure the file is properly formatted and complete",
                        "",
                        "### Step 4: Validate with CLI",
                        "**CRITICAL**: If `specfact generate contracts-apply` command is not available or fails, DO NOT proceed. STOP and inform the user that SpecFact CLI must be installed/upgraded first.",
                        "",
                        "1. Run the validation command:",
                        "   ```bash",
                        f"   specfact generate contracts-apply enhanced_{file_path.stem}.py --original {file_path_relative}",
                        "   ```",
                        "",
                        "   - **If command not found**: STOP immediately and inform user (see mandatory pre-check message)",
                        "   - **If command fails with error**: Review error, but if it's a missing command error, STOP and inform user",
                        "",
                        "### Step 5: Handle Validation Results",
                        "",
                        "**If validation succeeds:**",
                        "- The CLI will apply the changes automatically to the original file",
                        "- You're done! The file has been enhanced with contracts",
                        "",
                        "**If validation fails:**",
                        "- **If error is 'command not found' or 'command does not exist'**: STOP immediately and inform user (see mandatory pre-check message)",
                        "- **If error is validation failure** (syntax, AST, tests, etc.): Review the errors carefully",
                        "- Fix the issues in the enhanced code",
                        "- Write the corrected code to the same temporary file (`enhanced_{file_path.stem}.py`)",
                        "- Run the validation command again",
                        "- Repeat until validation passes (maximum 3 attempts)",
                        "",
                        "**CRITICAL**: If `specfact generate contracts-apply` command is not available or fails with 'command not found', DO NOT manually apply changes to the original file. STOP and inform the user that SpecFact CLI must be installed/upgraded first.",
                        "",
                        "### Common Validation Errors and Fixes",
                        "",
                        "**Syntax Errors:**",
                        "- Check for missing imports (beartype, icontract, etc.)",
                        "- Verify all decorators are properly formatted",
                        "- Ensure parentheses and brackets are balanced",
                        "- Check for typos in function/class names",
                        "",
                        "**Contract Issues:**",
                        "- Verify `@beartype` decorator is on all functions",
                        "- Check that `@require` and `@ensure` have valid lambda expressions",
                        "- Ensure contract conditions are properly formatted",
                        "- Verify all required imports are present",
                        "",
                        "**File Path Issues:**",
                        "- Ensure the enhanced file is in the correct location",
                        "- Use absolute paths if relative paths don't work",
                        "- Verify file permissions allow writing",
                        "",
                        "### Expected Workflow",
                        "",
                        "1. Read original file → 2. Generate enhanced code → 3. Write to temporary file → 4. Validate with CLI → 5. Fix errors if needed → 6. Re-validate → 7. Success!",
                        "",
                        "**Maximum Attempts: 3**",
                        "If validation fails after 3 attempts, review the errors manually and apply fixes.",
                        "",
                        "**FINAL REMINDER**: This entire workflow REQUIRES SpecFact CLI. If SpecFact CLI is not available, you MUST stop and inform the user. Do NOT attempt to manually add contracts or modify files directly.",
                        "",
                        "## Summary",
                        "",
                        f"- **Target File:** `{file_path_relative}`",
                        f"- **Enhanced File:** `enhanced_{file_path.stem}.py`",
                        f"- **Validation Command:** `specfact generate contracts-apply enhanced_{file_path.stem}.py --original {file_path_relative}`",
                        "- **Contracts:** " + ", ".join(contracts_to_apply),
                        "",
                        "**BEFORE STARTING**: Complete the mandatory SpecFact CLI verification at the top of this prompt. Do NOT proceed with file reading or code generation until SpecFact CLI is verified.",
                        "",
                    ]
                )

                prompt = "\n".join(prompt_parts)

                # Save prompt to file inside bundle directory (or .specfact/prompts if no bundle)
                prompts_dir = bundle_dir / "prompts" if bundle_dir else repo_path / ".specfact" / "prompts"
                prompts_dir.mkdir(parents=True, exist_ok=True)
                prompt_file = prompts_dir / f"enhance-{file_path.stem}-{'-'.join(contracts_to_apply)}.md"
                prompt_file.write_text(prompt, encoding="utf-8")

                print_success(f"Prompt generated: {prompt_file.relative_to(repo_path)}")
                generated_count += 1
            except Exception as e:
                print_error(f"Failed to generate prompt for {file_path.relative_to(repo_path)}: {e}")
                failed_count += 1

        # Summary
        if len(file_paths) > 1:
            console.print("\n[bold]Summary:[/bold]")
            console.print(f"  Generated: {generated_count}")
            console.print(f"  Failed: {failed_count}")

        if generated_count > 0:
            console.print("\n[bold]Next Steps:[/bold]")
            console.print("1. Open the prompt file(s) in your AI IDE (Cursor, CoPilot, etc.)")
            console.print("2. Copy the prompt content and ask your AI IDE to provide enhanced code")
            console.print("3. AI IDE will return the complete enhanced file (does NOT modify file directly)")
            console.print("4. Save enhanced code from AI IDE to a file (e.g., enhanced_<filename>.py)")
            console.print("5. AI IDE should run validation command (iterative workflow):")
            console.print("   ```bash")
            console.print("   specfact generate contracts-apply enhanced_<filename>.py --original <original-file>")
            console.print("   ```")
            console.print("6. If validation fails:")
            console.print("   - CLI will show specific error messages")
            console.print("   - AI IDE should fix the issues and save corrected code")
            console.print("   - Run validation command again (up to 3 attempts)")
            console.print("7. If validation succeeds:")
            console.print("   - CLI will automatically apply the changes")
            console.print("   - Verify contract coverage:")
            if bundle:
                console.print(f"     - specfact analyze contracts --bundle {bundle}")
            else:
                console.print("     - specfact analyze contracts --bundle <bundle>")
            console.print("   - Run your test suite: pytest (or your project's test command)")
            console.print("   - Commit the enhanced code")
            if bundle_dir:
                console.print(f"\n[dim]Prompt files saved to: {bundle_dir.relative_to(repo_path)}/prompts/[/dim]")
            else:
                console.print("\n[dim]Prompt files saved to: .specfact/prompts/[/dim]")
            console.print(
                "[yellow]Note:[/yellow] The prompt includes detailed instructions for the iterative validation workflow."
            )

        if output:
            console.print("[dim]Note: --output option is currently unused. Prompts saved to .specfact/prompts/[/dim]")

        record(
            {
                "prompt_generated": generated_count > 0,
                "generated_count": generated_count,
                "failed_count": failed_count,
            }
        )


@app.command("contracts-apply")
@beartype
@require(lambda enhanced_file: isinstance(enhanced_file, Path), "Enhanced file path must be Path")
@require(
    lambda original_file: original_file is None or isinstance(original_file, Path), "Original file must be None or Path"
)
@ensure(lambda result: result is None, "Must return None")
def apply_enhanced_contracts(
    # Target/Input
    enhanced_file: Path = typer.Argument(
        ...,
        help="Path to enhanced code file (from AI IDE)",
        exists=True,
    ),
    original_file: Path | None = typer.Option(
        None,
        "--original",
        help="Path to original file (auto-detected from enhanced file name if not provided)",
    ),
    # Behavior/Options
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip confirmation prompt and apply changes automatically",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be applied without actually modifying the file",
    ),
) -> None:
    """
    Validate and apply enhanced code with contracts.

    Takes the enhanced code file generated by your AI IDE, validates it, and applies
    it to the original file if validation passes. This completes the contract enhancement
    workflow started with `generate contracts-prompt`.

    **Validation Steps:**
    1. Syntax validation: `python -m py_compile`
    2. File size check: Enhanced file must be >= original file size
    3. AST structure comparison: Logical structure integrity check
    4. Contract imports verification: Required imports present
    5. Test execution: Run tests via specfact (contract-test)
    6. Diff preview (shows what will change)
    7. Apply changes only if all validations pass

    **Parameter Groups:**
    - **Target/Input**: enhanced_file (required argument), --original
    - **Behavior/Options**: --yes, --dry-run

    **Examples:**
        specfact generate contracts-apply enhanced_telemetry.py
        specfact generate contracts-apply enhanced_telemetry.py --original src/telemetry.py
        specfact generate contracts-apply enhanced_telemetry.py --dry-run  # Preview only
        specfact generate contracts-apply enhanced_telemetry.py --yes  # Auto-apply
    """
    import difflib
    import subprocess

    from rich.panel import Panel
    from rich.prompt import Confirm

    repo_path = Path(".").resolve()

    # Auto-detect original file if not provided
    if original_file is None:
        # Try to infer from enhanced file name
        # Pattern: enhance-<original-stem>-<contracts>.py or enhanced_<original-name>.py
        enhanced_stem = enhanced_file.stem
        if enhanced_stem.startswith("enhance-"):
            # Pattern: enhance-telemetry-beartype-icontract
            parts = enhanced_stem.split("-")
            if len(parts) >= 2:
                original_name = parts[1]  # Get the original file name
                # Try common locations
                possible_paths = [
                    repo_path / f"src/specfact_cli/{original_name}.py",
                    repo_path / f"src/{original_name}.py",
                    repo_path / f"{original_name}.py",
                ]
                for path in possible_paths:
                    if path.exists():
                        original_file = path
                        break

        if original_file is None:
            print_error("Could not auto-detect original file. Please specify --original")
            raise typer.Exit(1)

    original_file = original_file.resolve()
    enhanced_file = enhanced_file.resolve()

    if not original_file.exists():
        print_error(f"Original file not found: {original_file}")
        raise typer.Exit(1)

    # Read both files
    try:
        original_content = original_file.read_text(encoding="utf-8")
        enhanced_content = enhanced_file.read_text(encoding="utf-8")
        original_size = original_file.stat().st_size
        enhanced_size = enhanced_file.stat().st_size
    except Exception as e:
        print_error(f"Failed to read files: {e}")
        raise typer.Exit(1) from e

    # Step 1: File size check
    console.print("[bold cyan]Step 1/6: Checking file size...[/bold cyan]")
    if enhanced_size < original_size:
        print_error(f"Enhanced file is smaller than original ({enhanced_size} < {original_size} bytes)")
        console.print(
            "\n[yellow]This may indicate missing code. Please ensure all original functionality is preserved.[/yellow]"
        )
        console.print(
            "\n[bold]Please review the enhanced file and ensure it contains all original code plus contracts.[/bold]"
        )
        raise typer.Exit(1) from None
    print_success(f"File size check passed ({enhanced_size} >= {original_size} bytes)")

    # Step 2: Syntax validation
    console.print("\n[bold cyan]Step 2/6: Validating enhanced code syntax...[/bold cyan]")
    syntax_errors: list[str] = []
    try:
        result = subprocess.run(
            ["python", "-m", "py_compile", str(enhanced_file)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            error_output = result.stderr.strip()
            syntax_errors.append("Syntax validation failed")
            if error_output:
                # Parse syntax errors for better formatting
                for line in error_output.split("\n"):
                    if line.strip() and ("SyntaxError" in line or "Error" in line or "^" in line):
                        syntax_errors.append(f"  {line}")
                if len(syntax_errors) == 1:  # Only header, no parsed errors
                    syntax_errors.append(f"  {error_output}")
            else:
                syntax_errors.append("  No detailed error message available")

            print_error("\n".join(syntax_errors))
            console.print("\n[yellow]Common fixes:[/yellow]")
            console.print("  - Check for missing imports (beartype, icontract, etc.)")
            console.print("  - Verify all decorators are properly formatted")
            console.print("  - Ensure parentheses and brackets are balanced")
            console.print("  - Check for typos in function/class names")
            console.print("\n[bold]Please fix the syntax errors and try again.[/bold]")
            raise typer.Exit(1) from None
        print_success("Syntax validation passed")
    except subprocess.TimeoutExpired:
        print_error("Syntax validation timed out")
        console.print("\n[yellow]This usually indicates a very large file or system issues.[/yellow]")
        raise typer.Exit(1) from None
    except Exception as e:
        print_error(f"Syntax validation error: {e}")
        raise typer.Exit(1) from e

    # Step 3: AST structure comparison
    console.print("\n[bold cyan]Step 3/6: Comparing AST structure...[/bold cyan]")
    try:
        import ast

        original_ast = ast.parse(original_content, filename=str(original_file))
        enhanced_ast = ast.parse(enhanced_content, filename=str(enhanced_file))

        # Compare function/class definitions
        original_defs = {
            node.name: type(node).__name__
            for node in ast.walk(original_ast)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        }
        enhanced_defs = {
            node.name: type(node).__name__
            for node in ast.walk(enhanced_ast)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        }

        missing_defs = set(original_defs.keys()) - set(enhanced_defs.keys())
        if missing_defs:
            print_error("AST structure validation failed: Missing definitions in enhanced file:")
            for def_name in sorted(missing_defs):
                def_type = original_defs[def_name]
                console.print(f"  - {def_type}: {def_name}")
            console.print(
                "\n[bold]Please ensure all original functions and classes are preserved in the enhanced file.[/bold]"
            )
            raise typer.Exit(1) from None

        # Check for type mismatches (function -> class or vice versa)
        type_mismatches = []
        for def_name in original_defs:
            if def_name in enhanced_defs and original_defs[def_name] != enhanced_defs[def_name]:
                type_mismatches.append(f"{def_name}: {original_defs[def_name]} -> {enhanced_defs[def_name]}")

        if type_mismatches:
            print_error("AST structure validation failed: Type mismatches detected:")
            for mismatch in type_mismatches:
                console.print(f"  - {mismatch}")
            console.print("\n[bold]Please ensure function/class types match the original file.[/bold]")
            raise typer.Exit(1) from None

        print_success(f"AST structure validation passed ({len(original_defs)} definitions preserved)")
    except SyntaxError as e:
        print_error(f"AST parsing failed: {e}")
        console.print("\n[bold]This should not happen if syntax validation passed. Please report this issue.[/bold]")
        raise typer.Exit(1) from e
    except Exception as e:
        print_error(f"AST comparison error: {e}")
        raise typer.Exit(1) from e

    # Step 4: Check for contract imports
    console.print("\n[bold cyan]Step 4/6: Checking contract imports...[/bold cyan]")
    required_imports: list[str] = []
    if (
        ("@beartype" in enhanced_content or "beartype" in enhanced_content.lower())
        and "from beartype import beartype" not in enhanced_content
        and "import beartype" not in enhanced_content
    ):
        required_imports.append("beartype")
    if (
        ("@require" in enhanced_content or "@ensure" in enhanced_content)
        and "from icontract import" not in enhanced_content
        and "import icontract" not in enhanced_content
    ):
        required_imports.append("icontract")

    if required_imports:
        print_error(f"Missing required imports: {', '.join(required_imports)}")
        console.print("\n[yellow]Please add the missing imports at the top of the file:[/yellow]")
        for imp in required_imports:
            if imp == "beartype":
                console.print("  from beartype import beartype")
            elif imp == "icontract":
                console.print("  from icontract import require, ensure")
        console.print("\n[bold]Please fix the imports and try again.[/bold]")
        raise typer.Exit(1) from None

    print_success("Contract imports verified")

    # Step 5: Run linting/formatting checks (if tools available)
    console.print("\n[bold cyan]Step 5/7: Running code quality checks (if tools available)...[/bold cyan]")
    lint_issues: list[str] = []
    tools_checked = 0
    tools_passed = 0

    # List of common linting/formatting tools to check
    linting_tools = [
        ("ruff", ["ruff", "check", str(enhanced_file)], "Ruff linting"),
        ("pylint", ["pylint", str(enhanced_file), "--disable=all", "--enable=E,F"], "Pylint basic checks"),
        ("basedpyright", ["basedpyright", str(enhanced_file)], "BasedPyright type checking"),
        ("mypy", ["mypy", str(enhanced_file)], "MyPy type checking"),
    ]

    for tool_name, command, description in linting_tools:
        is_available, _error_msg = check_cli_tool_available(tool_name, version_flag="--version", timeout=3)
        if not is_available:
            console.print(f"[dim]Skipping {description}: {tool_name} not available[/dim]")
            continue

        tools_checked += 1
        console.print(f"[dim]Running {description}...[/dim]")

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=30,  # 30 seconds per tool
                cwd=str(repo_path),
            )

            if result.returncode == 0:
                tools_passed += 1
                console.print(f"[green]✓[/green] {description} passed")
            else:
                # Collect issues but don't fail immediately (warnings only)
                output = result.stdout + result.stderr
                # Limit output length for readability
                output_lines = output.split("\n")
                if len(output_lines) > 20:
                    output = "\n".join(output_lines[:20]) + f"\n... ({len(output_lines) - 20} more lines)"
                lint_issues.append(f"{description} found issues:\n{output}")
                console.print(f"[yellow]⚠[/yellow] {description} found issues (non-blocking)")

        except subprocess.TimeoutExpired:
            console.print(f"[yellow]⚠[/yellow] {description} timed out (non-blocking)")
            lint_issues.append(f"{description} timed out after 30 seconds")
        except Exception as e:
            console.print(f"[yellow]⚠[/yellow] {description} error: {e} (non-blocking)")
            lint_issues.append(f"{description} error: {e}")

    if tools_checked == 0:
        console.print("[dim]No linting/formatting tools available. Skipping code quality checks.[/dim]")
    elif tools_passed == tools_checked:
        print_success(f"All code quality checks passed ({tools_passed}/{tools_checked} tools)")
    else:
        console.print(f"[yellow]Code quality checks: {tools_passed}/{tools_checked} tools passed[/yellow]")
        if lint_issues:
            console.print("\n[yellow]Code Quality Issues (non-blocking):[/yellow]")
            for issue in lint_issues[:3]:  # Show first 3 issues
                console.print(Panel(issue[:500], title="Issue", border_style="yellow"))
            if len(lint_issues) > 3:
                console.print(f"[dim]... and {len(lint_issues) - 3} more issue(s)[/dim]")
            console.print("\n[yellow]Note:[/yellow] These are warnings. Fix them for better code quality.")

    # Step 6: Run tests (scoped to relevant file only for performance)
    # NOTE: Tests always run for validation, even in --dry-run mode, to ensure code quality
    console.print("\n[bold cyan]Step 6/7: Running tests (scoped to relevant file)...[/bold cyan]")
    test_failed = False
    test_output = ""

    # For single-file validation, we scope tests to the specific file only (not full repo)
    # This is much faster than running specfact repro on the entire repository
    try:
        # Find the original file path to determine test file location
        original_file_rel = original_file.relative_to(repo_path) if original_file else None
        enhanced_file_rel = enhanced_file.relative_to(repo_path)

        # Determine the source file we're testing (original or enhanced)
        source_file_rel = original_file_rel if original_file_rel else enhanced_file_rel

        # Convert source file path to potential test file paths
        # Pattern: src/specfact_cli/telemetry.py -> tests/unit/specfact_cli/test_telemetry.py
        # or: src/common/logger.py -> tests/unit/common/test_logger.py
        test_paths: list[Path] = []

        # Remove 'src/' prefix if present
        test_rel_path = str(source_file_rel)
        if test_rel_path.startswith("src/"):
            test_rel_path = test_rel_path[4:]  # Remove 'src/'
        elif test_rel_path.startswith("tools/"):
            test_rel_path = test_rel_path[6:]  # Remove 'tools/'

        # Get directory and filename
        test_file_dir = Path(test_rel_path).parent
        test_file_name = Path(test_rel_path).stem  # e.g., "telemetry" from "telemetry.py"

        # Try common test file patterns
        test_file_patterns = [
            f"test_{test_file_name}.py",
            f"{test_file_name}_test.py",
        ]

        # Try common test directory structures
        test_dirs = [
            repo_path / "tests" / "unit" / test_file_dir,
            repo_path / "tests" / test_file_dir,
            repo_path / "tests" / "unit",
            repo_path / "tests",
        ]

        # Build list of possible test file paths
        for test_dir in test_dirs:
            if test_dir.exists():
                for pattern in test_file_patterns:
                    test_path = test_dir / pattern
                    if test_path.exists():
                        test_paths.append(test_path)

        # Also try E2E tests if unit tests not found
        if not test_paths:
            e2e_test_dirs = [
                repo_path / "tests" / "e2e" / test_file_dir,
                repo_path / "tests" / "e2e",
            ]
            for test_dir in e2e_test_dirs:
                if test_dir.exists():
                    for pattern in test_file_patterns:
                        test_path = test_dir / pattern
                        if test_path.exists():
                            test_paths.append(test_path)

        # If we found specific test files, run them
        if test_paths:
            # Use the first matching test file (most specific)
            test_path = test_paths[0]
            console.print(f"[dim]Found test file: {test_path.relative_to(repo_path)}[/dim]")
            console.print("[dim]Running pytest on specific test file (fast, scoped validation)...[/dim]")

            result = subprocess.run(
                ["pytest", str(test_path), "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=60,  # 1 minute should be enough for a single test file
                cwd=str(repo_path),
            )
        else:
            # No specific test file found, try to import and test the enhanced file directly
            # This validates that the file can be imported and basic syntax works
            console.print(f"[dim]No specific test file found for {source_file_rel}[/dim]")
            console.print("[dim]Running syntax and import validation on enhanced file...[/dim]")

            # Try to import the module to verify it works
            import importlib.util
            import sys
            from dataclasses import dataclass

            @dataclass
            class ImportResult:
                """Result object for import validation."""

                returncode: int
                stdout: str
                stderr: str

            try:
                # Add the enhanced file's directory to path temporarily
                enhanced_file_dir = str(enhanced_file.parent)
                if enhanced_file_dir not in sys.path:
                    sys.path.insert(0, enhanced_file_dir)

                # Try to load the module
                spec = importlib.util.spec_from_file_location(enhanced_file.stem, enhanced_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    print_success("Enhanced file imports successfully")
                    result = ImportResult(returncode=0, stdout="", stderr="")
                else:
                    raise ImportError("Could not create module spec")
            except Exception as import_error:
                test_failed = True
                test_output = f"Import validation failed: {import_error}"
                print_error(test_output)
                console.print(
                    "\n[yellow]Note:[/yellow] No specific test file found. Enhanced file should be importable."
                )
                result = ImportResult(returncode=1, stdout="", stderr=test_output)

        if result.returncode != 0:
            test_failed = True
            test_output = result.stdout + result.stderr
            print_error("Test execution failed:")
            # Limit output for readability
            output_lines = test_output.split("\n")
            console.print("\n".join(output_lines[:50]))  # First 50 lines
            if len(output_lines) > 50:
                console.print(f"\n... ({len(output_lines) - 50} more lines)")
        else:
            if test_paths:
                print_success(f"All tests passed ({test_paths[0].relative_to(repo_path)})")
            else:
                print_success("Import validation passed")
    except FileNotFoundError:
        console.print("[yellow]Warning:[/yellow] 'pytest' not found. Skipping test execution.")
        console.print("[yellow]Please run tests manually before applying changes.[/yellow]")
        test_failed = False  # Don't fail if tools not available
    except subprocess.TimeoutExpired:
        test_failed = True
        test_output = "Test execution timed out after 60 seconds"
        print_error(test_output)
        console.print("\n[yellow]Note:[/yellow] Test execution took too long. Consider running tests manually.")
    except Exception as e:
        test_failed = True
        test_output = f"Test execution error: {e}"
        print_error(test_output)

    if test_failed:
        console.print("\n[bold red]Test failures detected. Changes will NOT be applied.[/bold red]")
        console.print("\n[yellow]Test Output:[/yellow]")
        console.print(Panel(test_output[:2000], title="Test Results", border_style="red"))  # Limit output
        console.print("\n[bold]Please fix the test failures and try again.[/bold]")
        console.print("Common issues:")
        console.print("  - Contract decorators may have incorrect syntax")
        console.print("  - Type hints may not match function signatures")
        console.print("  - Missing imports or dependencies")
        console.print("  - Contract conditions may be invalid")
        raise typer.Exit(1) from None

    # Step 7: Show diff
    console.print("\n[bold cyan]Step 7/7: Previewing changes...[/bold cyan]")
    diff = list(
        difflib.unified_diff(
            original_content.splitlines(keepends=True),
            enhanced_content.splitlines(keepends=True),
            fromfile=str(original_file.relative_to(repo_path)),
            tofile=str(enhanced_file.relative_to(repo_path)),
            lineterm="",
        )
    )

    if not diff:
        print_info("No changes detected. Files are identical.")
        raise typer.Exit(0)

    # Show diff (limit to first 100 lines for readability)
    diff_text = "".join(diff[:100])
    if len(diff) > 100:
        diff_text += f"\n... ({len(diff) - 100} more lines)"
    console.print(Panel(diff_text, title="Diff Preview", border_style="cyan"))

    # Step 7: Dry run check
    if dry_run:
        print_info("Dry run mode: No changes applied")
        console.print("\n[bold green]✓ All validations passed![/bold green]")
        console.print("Ready to apply with --yes flag or without --dry-run")
        raise typer.Exit(0)

    # Step 8: Confirmation
    if not yes and not Confirm.ask("\n[bold yellow]Apply these changes to the original file?[/bold yellow]"):
        print_info("Changes not applied")
        raise typer.Exit(0)

    # Step 9: Apply changes (only if all validations passed)
    try:
        original_file.write_text(enhanced_content, encoding="utf-8")
        print_success(f"Enhanced code applied to: {original_file.relative_to(repo_path)}")
        console.print("\n[bold green]✓ All validations passed and changes applied successfully![/bold green]")
        console.print("\n[bold]Next Steps:[/bold]")
        console.print("1. Verify contract coverage: specfact analyze contracts --bundle <bundle>")
        console.print("2. Run full test suite: specfact repro (or pytest)")
        console.print("3. Commit the enhanced code")
    except Exception as e:
        print_error(f"Failed to apply changes: {e}")
        console.print("\n[yellow]This is a filesystem error. Please check file permissions.[/yellow]")
        raise typer.Exit(1) from e


@app.command("tasks")
@beartype
@require(lambda bundle: isinstance(bundle, str) and len(bundle) > 0, "Bundle name must be non-empty string")
@require(lambda sdd: sdd is None or isinstance(sdd, Path), "SDD must be None or Path")
@require(lambda out: out is None or isinstance(out, Path), "Out must be None or Path")
@require(
    lambda output_format: isinstance(output_format, str) and output_format.lower() in ("yaml", "json", "markdown"),
    "Output format must be yaml, json, or markdown",
)
@ensure(lambda result: result is None, "Must return None")
def generate_tasks(
    # Target/Input
    bundle: str | None = typer.Argument(
        None,
        help="Project bundle name (e.g., legacy-api, auth-module). Default: active plan from 'specfact plan select'",
    ),
    sdd: Path | None = typer.Option(
        None,
        "--sdd",
        help="Path to SDD manifest. Default: auto-discover from bundle name",
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
        help="Output file path. Default: bundle-specific .specfact/projects/<bundle-name>/tasks.yaml (Phase 8.5)",
    ),
    # Behavior/Options
    no_interactive: bool = typer.Option(
        False,
        "--no-interactive",
        help="Non-interactive mode (for CI/CD automation). Default: False (interactive mode)",
    ),
) -> None:
    """
    Generate task breakdown from project bundle and SDD manifest.

    Creates dependency-ordered task list organized by phase:
    - Setup: Project structure, dependencies, config
    - Foundational: Core models, base classes, contracts
    - User Stories: Feature implementation tasks
    - Polish: Tests, docs, optimization

    Tasks are linked to user stories and include acceptance criteria,
    file paths, dependencies, and parallelization markers.

    **Parameter Groups:**
    - **Target/Input**: bundle (required argument), --sdd
    - **Output/Results**: --output-format, --out
    - **Behavior/Options**: --no-interactive

    **Examples:**
        specfact generate tasks legacy-api
        specfact generate tasks auth-module --output-format json
        specfact generate tasks legacy-api --out custom-tasks.yaml
    """
    from rich.console import Console

    from specfact_cli.generators.task_generator import generate_tasks as generate_tasks_func
    from specfact_cli.models.sdd import SDDManifest
    from specfact_cli.utils.progress import load_bundle_with_progress
    from specfact_cli.utils.sdd_discovery import find_sdd_for_bundle
    from specfact_cli.utils.structure import SpecFactStructure
    from specfact_cli.utils.structured_io import StructuredFormat, dump_structured_file, load_structured_file

    console = Console()

    # Use active plan as default if bundle not provided
    if bundle is None:
        bundle = SpecFactStructure.get_active_bundle_name(Path("."))
        if bundle is None:
            console.print("[bold red]✗[/bold red] Bundle name required")
            console.print("[yellow]→[/yellow] Use --bundle option or run 'specfact plan select' to set active plan")
            raise typer.Exit(1)
        console.print(f"[dim]Using active plan: {bundle}[/dim]")

    telemetry_metadata = {
        "output_format": output_format.lower(),
        "no_interactive": no_interactive,
    }

    with telemetry.track_command("generate.tasks", telemetry_metadata) as record:
        console.print("\n[bold cyan]SpecFact CLI - Task Generation[/bold cyan]")
        console.print("=" * 60)

        try:
            base_path = Path(".").resolve()

            # Load project bundle
            bundle_dir = SpecFactStructure.project_dir(base_path=base_path, bundle_name=bundle)
            if not bundle_dir.exists():
                print_error(f"Project bundle not found: {bundle_dir}")
                console.print(f"[dim]Create one with: specfact plan init {bundle}[/dim]")
                raise typer.Exit(1)

            project_bundle = load_bundle_with_progress(bundle_dir, validate_hashes=False, console_instance=console)

            # Load SDD manifest (optional but recommended)
            sdd_manifest: SDDManifest | None = None
            if sdd is None:
                discovered_sdd = find_sdd_for_bundle(bundle, base_path)
                if discovered_sdd and discovered_sdd.exists():
                    sdd = discovered_sdd
                    print_info(f"Auto-discovered SDD manifest: {sdd}")

            if sdd and sdd.exists():
                print_info(f"Loading SDD manifest: {sdd}")
                sdd_data = load_structured_file(sdd)
                sdd_manifest = SDDManifest.model_validate(sdd_data)
            else:
                print_warning("No SDD manifest found - tasks will be generated without architecture context")
                console.print("[dim]Create SDD with: specfact plan harden {bundle}[/dim]")

            # Generate tasks
            print_info("Generating task breakdown...")
            task_list = generate_tasks_func(project_bundle, sdd_manifest, bundle)

            # Determine output path (Phase 8.5: bundle-specific location)
            if out is None:
                # Use bundle-specific tasks path (Phase 8.5)
                out = SpecFactStructure.get_bundle_tasks_path(bundle_name=bundle, base_path=base_path)
                # Ensure parent directory exists
                out.parent.mkdir(parents=True, exist_ok=True)
                # Update extension if needed
                format_ext = output_format.lower()
                if format_ext == "yaml":
                    out = out.with_suffix(".yaml")
                elif format_ext == "json":
                    out = out.with_suffix(".json")
                else:
                    out = out.with_suffix(".md")
            else:
                # Ensure correct extension
                if output_format.lower() == "yaml":
                    out = out.with_suffix(".yaml")
                elif output_format.lower() == "json":
                    out = out.with_suffix(".json")
                else:
                    out = out.with_suffix(".md")

            # Save task list
            out.parent.mkdir(parents=True, exist_ok=True)
            if output_format.lower() == "markdown":
                # Generate markdown format
                markdown_content = _format_task_list_as_markdown(task_list)
                out.write_text(markdown_content, encoding="utf-8")
            else:
                # Save as YAML or JSON
                format_enum = StructuredFormat.YAML if output_format.lower() == "yaml" else StructuredFormat.JSON
                # Use mode='json' to ensure enums are serialized as strings
                task_data = task_list.model_dump(mode="json", exclude_none=True)
                dump_structured_file(task_data, out, format_enum)

            print_success(f"Task breakdown generated: {out}")
            console.print("\n[bold]Task Summary:[/bold]")
            console.print(f"  Total tasks: {len(task_list.tasks)}")
            console.print(f"  Setup: {len(task_list.get_tasks_by_phase(TaskPhase.SETUP))}")
            console.print(f"  Foundational: {len(task_list.get_tasks_by_phase(TaskPhase.FOUNDATIONAL))}")
            console.print(f"  User Stories: {len(task_list.get_tasks_by_phase(TaskPhase.USER_STORIES))}")
            console.print(f"  Polish: {len(task_list.get_tasks_by_phase(TaskPhase.POLISH))}")

            record(
                {
                    "bundle_name": bundle,
                    "total_tasks": len(task_list.tasks),
                    "output_format": output_format.lower(),
                    "output_path": str(out),
                }
            )

        except Exception as e:
            print_error(f"Failed to generate tasks: {e}")
            record({"error": str(e)})
            raise typer.Exit(1) from e


@beartype
@require(lambda task_list: isinstance(task_list, TaskList), "Task list must be TaskList")
@ensure(lambda result: isinstance(result, str), "Must return string")
def _format_task_list_as_markdown(task_list: TaskList) -> str:
    """Format task list as markdown."""
    from specfact_cli.models.task import TaskPhase

    lines: list[str] = []
    lines.append(f"# Task Breakdown: {task_list.bundle_name}")
    lines.append("")
    lines.append(f"**Generated:** {task_list.generated_at}")
    lines.append(f"**Plan Bundle Hash:** {task_list.plan_bundle_hash[:16]}...")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Total Tasks: {len(task_list.tasks)}")
    for phase in TaskPhase:
        phase_tasks = task_list.get_tasks_by_phase(phase)
        lines.append(f"- {phase.value.title()}: {len(phase_tasks)}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Group tasks by phase
    for phase in TaskPhase:
        phase_tasks = task_list.get_tasks_by_phase(phase)
        if not phase_tasks:
            continue

        lines.append(f"## Phase: {phase.value.title()}")
        lines.append("")

        for task_id in phase_tasks:
            task = task_list.get_task(task_id)
            if task is None:
                continue

            lines.append(f"### {task.id}: {task.title}")
            lines.append("")
            lines.append(f"**Status:** {task.status.value}")
            if task.file_path:
                lines.append(f"**File Path:** `{task.file_path}`")
            if task.dependencies:
                lines.append(f"**Dependencies:** {', '.join(task.dependencies)}")
            if task.story_keys:
                lines.append(f"**Stories:** {', '.join(task.story_keys)}")
            if task.parallelizable:
                lines.append("**Parallelizable:** Yes [P]")
            if task.estimated_hours:
                lines.append(f"**Estimated Hours:** {task.estimated_hours}")
            lines.append("")
            lines.append(f"{task.description}")
            lines.append("")
            if task.acceptance_criteria:
                lines.append("**Acceptance Criteria:**")
                for ac in task.acceptance_criteria:
                    lines.append(f"- {ac}")
                lines.append("")
            lines.append("---")
            lines.append("")

    return "\n".join(lines)

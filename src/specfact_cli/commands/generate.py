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
from specfact_cli.utils import print_error, print_info, print_success, print_warning
from specfact_cli.utils.structured_io import load_structured_file


app = typer.Typer(help="Generate artifacts from SDD and plans")
console = Console()


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
        help="Path to SDD manifest. Default: .specfact/sdd/<bundle-name>.yaml if --bundle specified, else .specfact/sdd.yaml. Ignored if --bundle is specified.",
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

    Generated files are saved to `.specfact/contracts/` with one file per feature.

    **Parameter Groups:**
    - **Target/Input**: --bundle, --sdd, --plan, --repo
    - **Behavior/Options**: --no-interactive

    **Examples:**
        specfact generate contracts --bundle legacy-api
        specfact generate contracts --bundle legacy-api --no-interactive
        specfact generate contracts --sdd .specfact/sdd.yaml --plan .specfact/plans/main.bundle.yaml
    """
    from specfact_cli.telemetry import telemetry

    telemetry_metadata = {
        "no_interactive": no_interactive,
    }

    with telemetry.track_command("generate.contracts", telemetry_metadata) as record:
        try:
            # Determine repository path
            base_path = Path(".").resolve() if repo is None else Path(repo).resolve()

            # Import here to avoid circular imports
            from specfact_cli.utils.bundle_loader import BundleFormat, detect_bundle_format, load_project_bundle
            from specfact_cli.utils.structure import SpecFactStructure

            # If --bundle is specified, use bundle-based paths
            if bundle:
                bundle_dir = SpecFactStructure.project_dir(base_path=base_path, bundle_name=bundle)
                if not bundle_dir.exists():
                    print_error(f"Project bundle not found: {bundle_dir}")
                    print_info(f"Create one with: specfact plan init {bundle}")
                    raise typer.Exit(1)

                plan_path = bundle_dir
                sdd_path = base_path / SpecFactStructure.SDD / f"{bundle}.yaml"
                if not sdd_path.exists():
                    sdd_path = base_path / SpecFactStructure.SDD / f"{bundle}.json"
            else:
                # Legacy: Use --plan and --sdd paths if provided
                # Determine plan path
                if plan is None:
                    # Try to find active plan
                    plan_path = SpecFactStructure.get_default_plan_path(base_path)
                    if plan_path is None or not plan_path.exists():
                        print_error("No active plan found")
                        print_info("Run 'specfact plan init <bundle-name>' or specify --bundle or --plan")
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
                            bundle_name = (
                                plan_path.parent.name if plan_path.parent.name != "projects" else plan_path.stem
                            )
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
            if format_type == BundleFormat.MODULAR or bundle:
                # Load modular ProjectBundle and convert to PlanBundle for compatibility
                from specfact_cli.commands.plan import _convert_project_bundle_to_plan_bundle

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
    bundle: str = typer.Argument(..., help="Project bundle name (e.g., legacy-api, auth-module)"),
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
        help="Output file path. Default: .specfact/tasks/<bundle-name>-<hash>.tasks.<format>",
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
    from specfact_cli.generators.task_generator import generate_tasks as generate_tasks_func
    from specfact_cli.models.sdd import SDDManifest
    from specfact_cli.telemetry import telemetry
    from specfact_cli.utils.bundle_loader import load_project_bundle
    from specfact_cli.utils.sdd_discovery import find_sdd_for_bundle
    from specfact_cli.utils.structure import SpecFactStructure
    from specfact_cli.utils.structured_io import StructuredFormat, dump_structured_file, load_structured_file

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

            print_info(f"Loading project bundle: {bundle}")
            project_bundle = load_project_bundle(bundle_dir)

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

            # Determine output path
            if out is None:
                tasks_dir = base_path / SpecFactStructure.TASKS
                tasks_dir.mkdir(parents=True, exist_ok=True)
                format_ext = output_format.lower()
                hash_short = (
                    task_list.plan_bundle_hash[:16]
                    if len(task_list.plan_bundle_hash) > 16
                    else task_list.plan_bundle_hash
                )
                out = tasks_dir / f"{bundle}-{hash_short}.tasks.{format_ext}"
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

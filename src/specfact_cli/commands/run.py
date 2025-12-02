"""
Run command - Orchestrate end-to-end workflows.

This module provides commands for orchestrating complete workflows
from idea to ship.
"""

from __future__ import annotations

from pathlib import Path

import typer
from beartype import beartype
from icontract import ensure, require
from rich.console import Console
from rich.panel import Panel

from specfact_cli.utils import print_error, print_info, print_section, print_success, print_warning
from specfact_cli.utils.sdd_discovery import find_sdd_for_bundle
from specfact_cli.utils.structure import SpecFactStructure


app = typer.Typer(help="Orchestrate end-to-end workflows")
console = Console()


@app.command("idea-to-ship")
@beartype
@require(lambda repo: isinstance(repo, Path), "Repository path must be Path")
@ensure(lambda result: result is None, "Must return None")
def idea_to_ship(
    # Target/Input
    repo: Path = typer.Option(
        Path("."),
        "--repo",
        help="Path to repository",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    bundle: str | None = typer.Option(
        None,
        "--bundle",
        help="Project bundle name (e.g., legacy-api). If not specified, attempts to auto-detect or prompt.",
    ),
    # Behavior/Options
    skip_sdd: bool = typer.Option(
        False,
        "--skip-sdd",
        help="Skip SDD scaffold step (use existing SDD). Default: False",
    ),
    skip_spec_kit_sync: bool = typer.Option(
        False,
        "--skip-sync",
        help="Skip bridge-based sync step (e.g., Spec-Kit, Linear, Jira adapter sync). Default: False",
    ),
    skip_implementation: bool = typer.Option(
        False,
        "--skip-implementation",
        help="Skip code implementation step (generate tasks only). Default: False",
    ),
    no_interactive: bool = typer.Option(
        False,
        "--no-interactive",
        help="Non-interactive mode (for CI/CD automation). Default: False (interactive mode)",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be created without actually performing operations. Default: False",
    ),
) -> None:
    """
    Orchestrate end-to-end idea-to-ship workflow.

    Executes a complete workflow from SDD scaffold to code implementation:

    1. SDD scaffold (if not skipped)
    2. Plan init/import (from-code or manual)
    3. Plan review/enrich
    4. Contract generation (from SDD HOW sections)
    5. Task generation (from plan bundle + SDD)
    6. Code implementation (execute tasks, generate code)
    7. Enforcement checks (enforce sdd, repro)
    8. Optional bridge-based sync (e.g., Spec-Kit, Linear, Jira)

    **Parameter Groups:**
    - **Target/Input**: --repo, --bundle
    - **Behavior/Options**: --skip-sdd, --skip-sync, --skip-implementation, --no-interactive, --dry-run

    **Examples:**
        specfact run idea-to-ship --repo .
        specfact run idea-to-ship --repo . --bundle legacy-api
        specfact run idea-to-ship --repo . --skip-sdd --skip-implementation
        specfact run idea-to-ship --repo . --dry-run
    """
    from rich.console import Console

    from specfact_cli.telemetry import telemetry
    from specfact_cli.utils.structure import SpecFactStructure

    console = Console()

    # Use active plan as default if bundle not provided
    if bundle is None:
        bundle = SpecFactStructure.get_active_bundle_name(repo)
        if bundle:
            console.print(f"[dim]Using active plan: {bundle}[/dim]")

    telemetry_metadata = {
        "bundle": bundle,
        "skip_sdd": skip_sdd,
        "skip_spec_kit_sync": skip_spec_kit_sync,
        "skip_implementation": skip_implementation,
        "no_interactive": no_interactive,
    }

    with telemetry.track_command("run.idea-to-ship", telemetry_metadata) as record:
        repo_path = repo.resolve()
        console.print()
        console.print(Panel("[bold cyan]SpecFact CLI - Idea-to-Ship Orchestrator[/bold cyan]", border_style="cyan"))
        console.print(f"[cyan]Repository:[/cyan] {repo_path}")

        if dry_run:
            console.print()
            console.print(Panel("[yellow]DRY-RUN MODE: No changes will be made[/yellow]", border_style="yellow"))
            console.print()
            _show_dry_run_summary(bundle, repo_path, skip_sdd, skip_spec_kit_sync, skip_implementation, no_interactive)
            return

        console.print()

        try:
            # Step 1: SDD Scaffold (if not skipped)
            if not skip_sdd:
                print_section("Step 1: SDD Scaffold")
                bundle_name = _ensure_bundle_name(bundle, repo_path, no_interactive)
                _ensure_sdd_manifest(bundle_name, repo_path, no_interactive)
            else:
                print_info("Skipping SDD scaffold step")
                bundle_name = _ensure_bundle_name(bundle, repo_path, no_interactive)

            # Step 2: Plan Init/Import
            print_section("Step 2: Plan Init/Import")
            _ensure_plan_bundle(bundle_name, repo_path, no_interactive)

            # Step 3: Plan Review/Enrich
            print_section("Step 3: Plan Review/Enrich")
            _review_plan_bundle(bundle_name, repo_path, no_interactive)

            # Step 4: Contract Generation
            print_section("Step 4: Contract Generation")
            _generate_contracts(bundle_name, repo_path, no_interactive)

            # Step 5: Task Generation
            print_section("Step 5: Task Generation")
            task_file = _generate_tasks(bundle_name, repo_path, no_interactive)

            # Step 6: Code Implementation (if not skipped)
            if not skip_implementation:
                print_section("Step 6: Code Implementation")
                _implement_tasks(task_file, repo_path, no_interactive)

                # Step 6.5: Test Generation (Specmatic-based)
                print_section("Step 6.5: Test Generation (Specmatic)")
                _generate_tests_specmatic(bundle_name, repo_path, no_interactive)
            else:
                print_info("Skipping code implementation step")

            # Step 7: Enforcement Checks
            print_section("Step 7: Enforcement Checks")
            _run_enforcement_checks(bundle_name, repo_path, no_interactive)

            # Step 8: Optional Bridge-Based Sync (if not skipped)
            if not skip_spec_kit_sync:
                print_section("Step 8: Bridge-Based Sync")
                _sync_bridge(repo_path, no_interactive)
            else:
                print_info("Skipping bridge-based sync step")

            print_success("Idea-to-ship workflow completed successfully!")

            record({"status": "success"})

        except KeyboardInterrupt:
            print_warning("\nWorkflow interrupted by user")
            raise typer.Exit(1) from None
        except Exception as e:
            print_error(f"Workflow failed: {e}")
            record({"status": "error", "error": str(e)})
            raise typer.Exit(1) from e


@beartype
@require(
    lambda bundle: bundle is None or (isinstance(bundle, str) and len(bundle) > 0),
    "Bundle must be None or non-empty string",
)
@require(lambda repo_path: isinstance(repo_path, Path), "Repository path must be Path")
@require(lambda no_interactive: isinstance(no_interactive, bool), "No interactive must be bool")
@ensure(lambda result: isinstance(result, str) and len(result) > 0, "Must return non-empty bundle name string")
def _ensure_bundle_name(bundle: str | None, repo_path: Path, no_interactive: bool) -> str:
    """Ensure we have a bundle name, prompting if needed."""
    if bundle and len(bundle) > 0:
        return bundle

    # Try to auto-detect bundle from existing bundles
    projects_dir = repo_path / SpecFactStructure.PROJECTS
    if projects_dir.exists():
        bundles = [d.name for d in projects_dir.iterdir() if d.is_dir() and d.name]
        if len(bundles) == 1:
            print_info(f"Auto-detected bundle: {bundles[0]}")
            return bundles[0]
        if len(bundles) > 1:
            if no_interactive:
                print_error("Multiple bundles found. Please specify --bundle")
                raise typer.Exit(1)
            from rich.prompt import Prompt

            selected = Prompt.ask("Select bundle", choices=bundles)
            if not selected or len(selected) == 0:
                print_error("Bundle name cannot be empty")
                raise typer.Exit(1)
            return selected

    # No bundle found - need to create one
    if no_interactive:
        print_error("No bundle found. Please specify --bundle or create one first")
        raise typer.Exit(1)

    from rich.prompt import Prompt

    entered = Prompt.ask("Enter bundle name (e.g., legacy-api, auth-module)")
    if not entered or len(entered.strip()) == 0:
        print_error("Bundle name cannot be empty")
        raise typer.Exit(1)
    return entered.strip()


@beartype
@require(lambda bundle_name: isinstance(bundle_name, str), "Bundle name must be string")
@require(lambda repo_path: isinstance(repo_path, Path), "Repository path must be Path")
@require(lambda no_interactive: isinstance(no_interactive, bool), "No interactive must be bool")
@ensure(lambda result: result is None, "Must return None")
def _ensure_sdd_manifest(bundle_name: str, repo_path: Path, no_interactive: bool) -> None:
    """Ensure SDD manifest exists, creating if needed."""
    sdd_path = find_sdd_for_bundle(bundle_name, repo_path)
    if sdd_path and sdd_path.exists():
        print_info(f"SDD manifest found: {sdd_path}")
        return

    print_warning("SDD manifest not found")
    if no_interactive:
        print_error("Cannot create SDD in non-interactive mode. Use --skip-sdd or create SDD first")
        raise typer.Exit(1)

    from rich.prompt import Confirm

    if Confirm.ask("Create SDD manifest?", default=True):
        # Call plan harden to create SDD
        import subprocess

        result = subprocess.run(
            ["hatch", "run", "specfact", "plan", "harden", bundle_name],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print_error(f"Failed to create SDD: {result.stderr}")
            raise typer.Exit(1)
        print_success("SDD manifest created")
    else:
        print_warning("Skipping SDD creation - workflow may fail later")


@beartype
@require(lambda bundle_name: isinstance(bundle_name, str), "Bundle name must be string")
@require(lambda repo_path: isinstance(repo_path, Path), "Repository path must be Path")
@require(lambda no_interactive: isinstance(no_interactive, bool), "No interactive must be bool")
@ensure(lambda result: result is None, "Must return None")
def _ensure_plan_bundle(bundle_name: str, repo_path: Path, no_interactive: bool) -> None:
    """Ensure plan bundle exists, creating if needed."""
    bundle_dir = SpecFactStructure.project_dir(base_path=repo_path, bundle_name=bundle_name)
    if bundle_dir.exists():
        print_info(f"Plan bundle found: {bundle_dir}")
        return

    print_warning("Plan bundle not found")
    if no_interactive:
        print_error("Cannot create plan bundle in non-interactive mode. Create bundle first")
        raise typer.Exit(1)

    from rich.prompt import Confirm, Prompt

    if Confirm.ask("Create plan bundle?", default=True):
        method = Prompt.ask(
            "Creation method",
            choices=["init", "from-code"],
            default="init",
        )

        import subprocess

        if method == "init":
            result = subprocess.run(
                ["hatch", "run", "specfact", "plan", "init", bundle_name],
                cwd=repo_path,
                capture_output=True,
                text=True,
            )
        else:  # from-code
            result = subprocess.run(
                ["hatch", "run", "specfact", "import", "from-code", "--bundle", bundle_name],
                cwd=repo_path,
                capture_output=True,
                text=True,
            )

        if result.returncode != 0:
            print_error(f"Failed to create plan bundle: {result.stderr}")
            raise typer.Exit(1)
        print_success("Plan bundle created")
    else:
        print_error("Plan bundle required for workflow")
        raise typer.Exit(1)


@beartype
@require(lambda bundle_name: isinstance(bundle_name, str), "Bundle name must be string")
@require(lambda repo_path: isinstance(repo_path, Path), "Repository path must be Path")
@require(lambda no_interactive: isinstance(no_interactive, bool), "No interactive must be bool")
@ensure(lambda result: result is None, "Must return None")
def _review_plan_bundle(bundle_name: str, repo_path: Path, no_interactive: bool) -> None:
    """Review plan bundle to resolve ambiguities."""
    import subprocess

    cmd = ["hatch", "run", "specfact", "plan", "review", bundle_name]
    if no_interactive:
        cmd.append("--no-interactive")

    result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True)
    if result.returncode != 0:
        print_warning(f"Plan review had issues: {result.stderr}")
    else:
        print_success("Plan review completed")


@beartype
@require(lambda bundle_name: isinstance(bundle_name, str), "Bundle name must be string")
@require(lambda repo_path: isinstance(repo_path, Path), "Repository path must be Path")
@require(lambda no_interactive: isinstance(no_interactive, bool), "No interactive must be bool")
@ensure(lambda result: result is None, "Must return None")
def _generate_contracts(bundle_name: str, repo_path: Path, no_interactive: bool) -> None:
    """Generate contract stubs from SDD HOW sections."""
    import subprocess

    cmd = ["hatch", "run", "specfact", "generate", "contracts", "--bundle", bundle_name]
    if no_interactive:
        cmd.append("--no-interactive")

    result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True)
    if result.returncode != 0:
        print_warning(f"Contract generation had issues: {result.stderr}")
    else:
        print_success("Contracts generated")


@beartype
@require(lambda bundle_name: isinstance(bundle_name, str), "Bundle name must be string")
@require(lambda repo_path: isinstance(repo_path, Path), "Repository path must be Path")
@require(lambda no_interactive: isinstance(no_interactive, bool), "No interactive must be bool")
@ensure(lambda result: isinstance(result, Path), "Must return task file Path")
def _generate_tasks(bundle_name: str, repo_path: Path, no_interactive: bool) -> Path:
    """Generate task breakdown from plan bundle + SDD."""
    import subprocess

    cmd = ["hatch", "run", "specfact", "generate", "tasks", bundle_name]
    if no_interactive:
        cmd.append("--no-interactive")

    result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True)
    if result.returncode != 0:
        print_error(f"Failed to generate tasks: {result.stderr}")
        raise typer.Exit(1)

    print_success("Tasks generated")

    # Find the generated task file
    tasks_dir = SpecFactStructure.TASKS
    task_files = list((repo_path / tasks_dir).glob(f"{bundle_name}-*.tasks.*"))
    if not task_files:
        print_error("Task file not found after generation")
        raise typer.Exit(1)

    # Return the most recent task file
    return max(task_files, key=lambda p: p.stat().st_mtime)


@beartype
@require(lambda task_file: isinstance(task_file, Path), "Task file must be Path")
@require(lambda repo_path: isinstance(repo_path, Path), "Repository path must be Path")
@require(lambda no_interactive: isinstance(no_interactive, bool), "No interactive must be bool")
@ensure(lambda result: result is None, "Must return None")
def _implement_tasks(task_file: Path, repo_path: Path, no_interactive: bool) -> None:
    """Execute tasks and generate code."""
    import subprocess

    cmd = ["hatch", "run", "specfact", "implement", "tasks", str(task_file)]
    if no_interactive:
        cmd.append("--no-interactive")

    result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True)
    if result.returncode != 0:
        print_warning(f"Task implementation had issues: {result.stderr}")
    else:
        print_success("Tasks implemented")


@beartype
@require(lambda bundle_name: isinstance(bundle_name, str), "Bundle name must be string")
@require(lambda repo_path: isinstance(repo_path, Path), "Repository path must be Path")
@require(lambda no_interactive: isinstance(no_interactive, bool), "No interactive must be bool")
@ensure(lambda result: result is None, "Must return None")
def _run_enforcement_checks(bundle_name: str, repo_path: Path, no_interactive: bool) -> None:
    """Run enforcement checks (enforce sdd, repro)."""
    import subprocess

    # Run enforce sdd
    cmd = ["hatch", "run", "specfact", "enforce", "sdd", "--bundle", bundle_name]
    if no_interactive:
        cmd.append("--no-interactive")

    result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True)
    if result.returncode != 0:
        print_warning(f"SDD enforcement had issues: {result.stderr}")
    else:
        print_success("SDD enforcement passed")

    # Run repro
    cmd = ["hatch", "run", "specfact", "repro", "--repo", str(repo_path)]
    if no_interactive:
        cmd.append("--no-interactive")

    result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True)
    if result.returncode != 0:
        print_warning(f"Repro validation had issues: {result.stderr}")
    else:
        print_success("Repro validation passed")


@beartype
@require(lambda bundle_name: isinstance(bundle_name, str), "Bundle name must be string")
@require(lambda repo_path: isinstance(repo_path, Path), "Repository path must be Path")
@require(lambda no_interactive: isinstance(no_interactive, bool), "No interactive must be bool")
@ensure(lambda result: result is None, "Must return None")
def _generate_tests_specmatic(bundle_name: str, repo_path: Path, no_interactive: bool) -> None:
    """Generate tests using Specmatic flows (not LLM)."""
    import subprocess

    cmd = ["hatch", "run", "specfact", "spec", "generate-tests", "--bundle", bundle_name]
    if no_interactive:
        cmd.append("--no-interactive")

    result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True)
    if result.returncode != 0:
        print_warning(f"Specmatic test generation had issues: {result.stderr}")
        print_info("Tests will need to be generated manually or via LLM")
    else:
        print_success("Tests generated via Specmatic")


@beartype
@require(lambda repo_path: isinstance(repo_path, Path), "Repository path must be Path")
@require(lambda no_interactive: isinstance(no_interactive, bool), "No interactive must be bool")
@ensure(lambda result: result is None, "Must return None")
def _sync_bridge(repo_path: Path, no_interactive: bool) -> None:
    """Run bridge-based sync (e.g., Spec-Kit, Linear, Jira)."""

    # Try to detect bridge adapter
    # For now, just skip if no bridge config found
    print_info("Bridge sync skipped (auto-detection not implemented)")
    # TODO: Implement bridge auto-detection and sync


@beartype
@require(lambda bundle: bundle is None or isinstance(bundle, str), "Bundle must be None or string")
@require(lambda repo_path: isinstance(repo_path, Path), "Repository path must be Path")
@require(lambda skip_sdd: isinstance(skip_sdd, bool), "Skip SDD must be bool")
@require(lambda skip_spec_kit_sync: isinstance(skip_spec_kit_sync, bool), "Skip sync must be bool")
@require(lambda skip_implementation: isinstance(skip_implementation, bool), "Skip implementation must be bool")
@require(lambda no_interactive: isinstance(no_interactive, bool), "No interactive must be bool")
@ensure(lambda result: result is None, "Must return None")
def _show_dry_run_summary(
    bundle: str | None,
    repo_path: Path,
    skip_sdd: bool,
    skip_spec_kit_sync: bool,
    skip_implementation: bool,
    no_interactive: bool,
) -> None:
    """Show what would be created/executed in dry-run mode."""
    from rich.table import Table

    from specfact_cli.utils.structure import SpecFactStructure

    console = Console()

    # Determine bundle name
    bundle_name = bundle
    if bundle_name is None:
        bundle_name = SpecFactStructure.get_active_bundle_name(repo_path)
        if bundle_name is None:
            bundle_name = "<to-be-determined>"

    # Create summary table
    table = Table(title="Dry-Run Summary: What Would Be Executed", show_header=True, header_style="bold cyan")
    table.add_column("Step", style="cyan", width=25)
    table.add_column("Action", style="green", width=50)
    table.add_column("Status", style="yellow", width=15)

    # Step 1: SDD Scaffold
    if not skip_sdd:
        sdd_path = repo_path / ".specfact" / "sdd" / f"{bundle_name}.yaml"
        table.add_row(
            "1. SDD Scaffold",
            f"Create SDD manifest: {sdd_path}",
            "Would execute",
        )
    else:
        table.add_row("1. SDD Scaffold", "Skip SDD creation", "Skipped")

    # Step 2: Plan Init/Import
    bundle_dir = SpecFactStructure.project_dir(base_path=repo_path, bundle_name=bundle_name)
    if bundle_dir.exists():
        table.add_row("2. Plan Init/Import", f"Load existing bundle: {bundle_dir}", "Would load")
    else:
        table.add_row(
            "2. Plan Init/Import",
            f"Create new bundle: {bundle_dir}",
            "Would create",
        )

    # Step 3: Plan Review/Enrich
    table.add_row(
        "3. Plan Review/Enrich",
        f"Review plan bundle: {bundle_name}",
        "Would execute",
    )

    # Step 4: Contract Generation
    contracts_dir = repo_path / ".specfact" / "contracts"
    table.add_row(
        "4. Contract Generation",
        f"Generate contracts in: {contracts_dir}",
        "Would generate",
    )

    # Step 5: Task Generation
    tasks_dir = repo_path / ".specfact" / "tasks"
    table.add_row(
        "5. Task Generation",
        f"Generate tasks in: {tasks_dir}",
        "Would generate",
    )

    # Step 6: Code Implementation
    if not skip_implementation:
        table.add_row(
            "6. Code Implementation",
            "Execute tasks and generate code files",
            "Would execute",
        )
        table.add_row(
            "6.5. Test Generation",
            "Generate Specmatic-based tests",
            "Would generate",
        )
    else:
        table.add_row("6. Code Implementation", "Skip code implementation", "Skipped")
        table.add_row("6.5. Test Generation", "Skip test generation", "Skipped")

    # Step 7: Enforcement Checks
    table.add_row(
        "7. Enforcement Checks",
        f"Run enforce sdd and repro for: {bundle_name}",
        "Would execute",
    )

    # Step 8: Bridge Sync
    if not skip_spec_kit_sync:
        table.add_row(
            "8. Bridge-Based Sync",
            "Sync with external tools (Spec-Kit, Linear, Jira)",
            "Would sync",
        )
    else:
        table.add_row("8. Bridge-Based Sync", "Skip bridge sync", "Skipped")

    console.print()
    console.print(table)
    console.print()
    console.print("[dim]Note: No files will be created or modified in dry-run mode.[/dim]")
    console.print()

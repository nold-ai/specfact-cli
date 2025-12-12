"""
Implement command - Execute tasks and generate code.

This module provides commands for executing task breakdowns and generating
actual code files from tasks.
"""

from __future__ import annotations

from pathlib import Path

import typer
from beartype import beartype
from icontract import ensure, require
from rich.console import Console

from specfact_cli.models.task import Task, TaskList, TaskPhase, TaskStatus
from specfact_cli.utils import print_error, print_info, print_success, print_warning
from specfact_cli.utils.structured_io import StructuredFormat, dump_structured_file, load_structured_file


app = typer.Typer(help="Execute tasks and generate code")
console = Console()


@app.command("tasks")
@beartype
@require(lambda tasks_file: isinstance(tasks_file, Path), "Tasks file must be Path")
@require(lambda phase: phase is None or isinstance(phase, str), "Phase must be None or string")
@require(lambda task_id: task_id is None or isinstance(task_id, str), "Task ID must be None or string")
@ensure(lambda result: result is None, "Must return None")
def implement_tasks(
    # Target/Input
    tasks_file: Path = typer.Argument(..., help="Path to task breakdown file (.tasks.yaml or .tasks.json)"),
    phase: str | None = typer.Option(
        None,
        "--phase",
        help="Execute only tasks in this phase (setup, foundational, user_stories, polish). Default: all phases",
    ),
    task_id: str | None = typer.Option(
        None,
        "--task",
        help="Execute only this specific task ID (e.g., TASK-001). Default: all tasks in phase",
    ),
    # Behavior/Options
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be executed without actually generating code. Default: False",
    ),
    skip_validation: bool = typer.Option(
        False,
        "--skip-validation",
        help="Skip validation (tests, linting) after each phase. Default: False",
    ),
    no_interactive: bool = typer.Option(
        False,
        "--no-interactive",
        help="Non-interactive mode (for CI/CD automation). Default: False (interactive mode)",
    ),
) -> None:
    """
    Execute tasks from task breakdown and generate code files.

    Loads a task breakdown file and executes tasks phase-by-phase, generating
    actual code files according to task descriptions and file paths.

    **Parameter Groups:**
    - **Target/Input**: tasks_file (required argument), --phase, --task
    - **Behavior/Options**: --dry-run, --skip-validation, --no-interactive

    **Examples:**
        specfact implement tasks .specfact/projects/bundle-name/tasks.yaml
        specfact implement tasks .specfact/projects/bundle-name/tasks.yaml --phase setup
        specfact implement tasks .specfact/projects/bundle-name/tasks.yaml --task TASK-001 --dry-run
    """
    from specfact_cli.telemetry import telemetry

    telemetry_metadata = {
        "phase": phase,
        "task_id": task_id,
        "dry_run": dry_run,
        "skip_validation": skip_validation,
        "no_interactive": no_interactive,
    }

    with telemetry.track_command("implement.tasks", telemetry_metadata) as record:
        console.print("\n[bold cyan]SpecFact CLI - Task Implementation[/bold cyan]")
        console.print("=" * 60)

        try:
            # Load task list
            if not tasks_file.exists():
                print_error(f"Task file not found: {tasks_file}")
                raise typer.Exit(1)

            print_info(f"Loading task breakdown: {tasks_file}")
            task_data = load_structured_file(tasks_file)
            task_list = TaskList.model_validate(task_data)

            console.print(f"[bold]Bundle:[/bold] {task_list.bundle_name}")
            console.print(f"[bold]Total Tasks:[/bold] {len(task_list.tasks)}")
            console.print(f"[bold]Plan Hash:[/bold] {task_list.plan_bundle_hash[:16]}...")

            if dry_run:
                print_warning("DRY RUN MODE - No code will be generated")

            # Determine which tasks to execute
            tasks_to_execute = _get_tasks_to_execute(task_list, phase, task_id)

            if not tasks_to_execute:
                print_warning("No tasks to execute")
                raise typer.Exit(0)

            console.print(f"\n[bold]Tasks to execute:[/bold] {len(tasks_to_execute)}")

            # Execute tasks phase-by-phase
            executed_count = 0
            failed_count = 0

            for task in tasks_to_execute:
                if task.status == TaskStatus.COMPLETED:
                    console.print(f"[dim]Skipping {task.id} (already completed)[/dim]")
                    continue

                try:
                    if not dry_run:
                        print_info(f"Executing {task.id}: {task.title}")
                        _execute_task(task, task_list, Path("."))
                        task.status = TaskStatus.COMPLETED
                        executed_count += 1
                    else:
                        console.print(f"[dim]Would execute {task.id}: {task.title}[/dim]")
                        if task.file_path:
                            console.print(f"  [dim]File: {task.file_path}[/dim]")

                    # Validate after task (if not skipped)
                    if not skip_validation and not dry_run:
                        _validate_task(task)

                except Exception as e:
                    print_error(f"Failed to execute {task.id}: {e}")
                    task.status = TaskStatus.BLOCKED
                    failed_count += 1
                    if not no_interactive:
                        # In interactive mode, ask if we should continue
                        from rich.prompt import Confirm

                        if not Confirm.ask("Continue with remaining tasks?", default=True):
                            break

            # Save updated task list
            if not dry_run:
                task_data = task_list.model_dump(mode="json", exclude_none=True)
                dump_structured_file(task_data, tasks_file, StructuredFormat.from_path(tasks_file))

            # Summary
            console.print("\n[bold]Execution Summary:[/bold]")
            console.print(f"  Executed: {executed_count}")
            console.print(f"  Failed: {failed_count}")
            console.print(f"  Skipped: {len([t for t in tasks_to_execute if t.status == TaskStatus.COMPLETED])}")

            if failed_count > 0:
                print_warning(f"{failed_count} task(s) failed")
                raise typer.Exit(1)

            print_success("Task execution completed")

            record(
                {
                    "total_tasks": len(task_list.tasks),
                    "executed": executed_count,
                    "failed": failed_count,
                }
            )

        except Exception as e:
            print_error(f"Failed to execute tasks: {e}")
            record({"error": str(e)})
            raise typer.Exit(1) from e


@beartype
@require(lambda task_list: isinstance(task_list, TaskList), "Task list must be TaskList")
@require(lambda phase: phase is None or isinstance(phase, str), "Phase must be None or string")
@require(lambda task_id: task_id is None or isinstance(task_id, str), "Task ID must be None or string")
@ensure(lambda result: isinstance(result, list), "Must return list of Tasks")
def _get_tasks_to_execute(task_list: TaskList, phase: str | None, task_id: str | None) -> list[Task]:
    """Get list of tasks to execute based on filters."""
    if task_id:
        # Execute specific task
        task = task_list.get_task(task_id)
        if task is None:
            raise ValueError(f"Task not found: {task_id}")
        return [task]

    if phase:
        # Execute all tasks in phase
        try:
            phase_enum = TaskPhase(phase.lower())
        except ValueError as e:
            raise ValueError(
                f"Invalid phase: {phase}. Must be one of: setup, foundational, user_stories, polish"
            ) from e
        task_ids = task_list.get_tasks_by_phase(phase_enum)
        return [task for tid in task_ids if (task := task_list.get_task(tid)) is not None]

    # Execute all tasks in dependency order
    return task_list.tasks


@beartype
@require(lambda task: isinstance(task, Task), "Task must be Task")
@require(lambda task_list: isinstance(task_list, TaskList), "Task list must be TaskList")
@require(lambda base_path: isinstance(base_path, Path), "Base path must be Path")
@ensure(lambda result: result is None, "Must return None")
def _execute_task(task: Task, task_list: TaskList, base_path: Path) -> None:
    """Execute a single task by preparing LLM prompt context (not generating code)."""
    from specfact_cli.sync.spec_to_code import SpecToCodeSync

    # Check dependencies
    if task.dependencies:
        for dep_id in task.dependencies:
            dep_task = task_list.get_task(dep_id)
            if dep_task and dep_task.status != TaskStatus.COMPLETED:
                raise ValueError(f"Task {task.id} depends on {dep_id} which is not completed")

    # Prepare LLM prompt context instead of generating code
    spec_to_code_sync = SpecToCodeSync(base_path)

    # Analyze codebase patterns
    existing_patterns = spec_to_code_sync._analyze_codebase_patterns(base_path)
    dependencies = spec_to_code_sync._read_requirements(base_path)
    style_guide = spec_to_code_sync._detect_style_patterns(base_path)

    # Generate LLM prompt
    prompt_parts = [
        "# Code Generation Request",
        "",
        f"## Task: {task.id} - {task.title}",
        "",
        f"**Description:** {task.description}",
        "",
        f"**Phase:** {task.phase.value}",
        "",
    ]

    if task.acceptance_criteria:
        prompt_parts.append("**Acceptance Criteria:**")
        for ac in task.acceptance_criteria:
            prompt_parts.append(f"- {ac}")
        prompt_parts.append("")

    if task.file_path:
        prompt_parts.append(f"**Target File:** {task.file_path}")
        prompt_parts.append("")

        # Check if file already exists
        file_path = base_path / task.file_path
        if file_path.exists():
            prompt_parts.append("## Existing Code")
            prompt_parts.append("```python")
            prompt_parts.append(file_path.read_text(encoding="utf-8"))
            prompt_parts.append("```")
            prompt_parts.append("")
            prompt_parts.append("**Note:** Update the existing code above, don't replace it entirely.")
            prompt_parts.append("")

    prompt_parts.extend(
        [
            "## Existing Codebase Patterns",
            "```json",
            str(existing_patterns),
            "```",
            "",
            "## Dependencies",
            "```",
            "\n".join(dependencies),
            "```",
            "",
            "## Style Guide",
            "```json",
            str(style_guide),
            "```",
            "",
            "## Instructions",
            "Generate or update the code file based on the task description and acceptance criteria.",
            "Follow the existing codebase patterns and style guide.",
            "Ensure all contracts (beartype, icontract) are properly applied.",
            "",
        ]
    )

    prompt = "\n".join(prompt_parts)

    # Save prompt to file
    prompts_dir = base_path / ".specfact" / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    prompt_file = prompts_dir / f"{task.id}-{task.file_path.stem if task.file_path else 'task'}.md"
    prompt_file.write_text(prompt, encoding="utf-8")

    console.print(f"[bold]LLM Prompt prepared for {task.id}[/bold]")
    console.print(f"[dim]Prompt file: {prompt_file}[/dim]")
    console.print("[yellow]Execute this prompt with your LLM to generate code[/yellow]")


@beartype
@require(lambda task: isinstance(task, Task), "Task must be Task")
@require(lambda task_list: isinstance(task_list, TaskList), "Task list must be TaskList")
@ensure(lambda result: isinstance(result, str), "Must return string")
def _generate_code_for_task(task: Task, task_list: TaskList) -> str:
    """Generate code content for a task."""
    # Simple code generation based on task phase and description
    # In a full implementation, this would use templates and more sophisticated logic

    if task.phase == TaskPhase.SETUP:
        # Setup tasks: generate configuration files
        if "requirements" in task.title.lower() or "dependencies" in task.title.lower():
            return "# Requirements file\n# Generated by SpecFact CLI\n\n"
        if "config" in task.title.lower():
            return "# Configuration file\n# Generated by SpecFact CLI\n\n"

    elif task.phase == TaskPhase.FOUNDATIONAL:
        # Foundational tasks: generate base classes/models
        if "model" in task.title.lower() or "base" in task.title.lower():
            return f'''"""
{task.title}

{task.description}
"""

from __future__ import annotations

from beartype import beartype
from icontract import ensure, require
from pydantic import BaseModel, Field


# TODO: Implement according to task description
# {task.description}
'''

    elif task.phase == TaskPhase.USER_STORIES:
        # User story tasks: generate service/endpoint code
        if "test" in task.title.lower():
            return f'''"""
Tests for {task.title}

{task.description}
"""

import pytest

# TODO: Implement tests according to acceptance criteria
# Acceptance Criteria:
{chr(10).join(f"#   - {ac}" for ac in task.acceptance_criteria)}
'''
        return f'''"""
{task.title}

{task.description}
"""

from __future__ import annotations

from beartype import beartype
from icontract import ensure, require


# TODO: Implement according to task description
# {task.description}
#
# Acceptance Criteria:
{chr(10).join(f"#   - {ac}" for ac in task.acceptance_criteria)}
'''

    elif task.phase == TaskPhase.POLISH:
        # Polish tasks: generate documentation/optimization
        return f'''"""
{task.title}

{task.description}
"""

# TODO: Implement according to task description
# {task.description}
'''

    # Default: return placeholder
    return f'''"""
{task.title}

{task.description}
"""

# TODO: Implement according to task description
'''


@beartype
@require(lambda task: isinstance(task, Task), "Task must be Task")
@ensure(lambda result: result is None, "Must return None")
def _validate_task(task: Task) -> None:
    """Validate task execution (run tests, linting, etc.)."""
    # Placeholder for validation logic
    # In a full implementation, this would:
    # - Run tests if task generated test files
    # - Run linting/type checking
    # - Validate contracts

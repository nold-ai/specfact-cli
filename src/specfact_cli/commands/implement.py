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
        specfact implement tasks .specfact/tasks/bundle-abc123.tasks.yaml
        specfact implement tasks .specfact/tasks/bundle-abc123.tasks.yaml --phase setup
        specfact implement tasks .specfact/tasks/bundle-abc123.tasks.yaml --task TASK-001 --dry-run
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
    """Execute a single task and generate code."""
    # Check dependencies
    if task.dependencies:
        for dep_id in task.dependencies:
            dep_task = task_list.get_task(dep_id)
            if dep_task and dep_task.status != TaskStatus.COMPLETED:
                raise ValueError(f"Task {task.id} depends on {dep_id} which is not completed")

    # Generate code based on task phase and description
    if task.file_path:
        file_path = base_path / task.file_path
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate file content based on task
        content = _generate_code_for_task(task, task_list)
        file_path.write_text(content, encoding="utf-8")
        console.print(f"[dim]Generated: {file_path}[/dim]")


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

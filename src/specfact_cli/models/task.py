"""
Task generation data models.

This module defines Pydantic models for task breakdowns generated from
plan bundles and SDD manifests.
"""

from __future__ import annotations

from enum import Enum

from beartype import beartype
from icontract import ensure, require
from pydantic import BaseModel, Field


class TaskPhase(str, Enum):
    """Task execution phases."""

    SETUP = "setup"  # Project structure, dependencies, config
    FOUNDATIONAL = "foundational"  # Core models, base classes
    USER_STORIES = "user_stories"  # Implement features per story
    POLISH = "polish"  # Tests, docs, optimization


class TaskStatus(str, Enum):
    """Task completion status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


class Task(BaseModel):
    """Individual implementation task."""

    id: str = Field(..., description="Task ID (e.g., TASK-001)")
    phase: TaskPhase = Field(..., description="Execution phase")
    title: str = Field(..., description="Task title")
    description: str = Field(..., description="Detailed task description")
    file_path: str | None = Field(None, description="Target file path for code generation")
    dependencies: list[str] = Field(default_factory=list, description="Task IDs this task depends on")
    story_keys: list[str] = Field(
        default_factory=list, description="Story keys this task implements (e.g., [US1, US2])"
    )
    parallelizable: bool = Field(default=False, description="Whether this task can run in parallel with others")
    acceptance_criteria: list[str] = Field(default_factory=list, description="Acceptance criteria for this task")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Task completion status")
    estimated_hours: float | None = Field(default=None, ge=0.0, description="Estimated hours to complete")
    tags: list[str] = Field(default_factory=list, description="Task tags (e.g., 'model', 'service', 'test')")


class TaskList(BaseModel):
    """Complete task breakdown for a project bundle."""

    version: str = Field("1.0.0", description="Task list schema version")
    plan_bundle_hash: str = Field(..., description="Plan bundle content hash this task list is based on")
    bundle_name: str = Field(..., description="Project bundle name")
    generated_at: str = Field(..., description="Generation timestamp (ISO format)")
    tasks: list[Task] = Field(default_factory=list, description="All tasks in dependency order")
    phases: dict[str, list[str]] = Field(default_factory=dict, description="Phase -> task IDs mapping for quick lookup")
    story_mappings: dict[str, list[str]] = Field(default_factory=dict, description="Story key -> task IDs mapping")

    @beartype
    @require(lambda self: len(self.tasks) > 0, "Task list must contain at least one task")
    @ensure(lambda result: isinstance(result, list), "Must return list of task IDs")
    def get_tasks_by_phase(self, phase: TaskPhase) -> list[str]:
        """
        Get task IDs for a specific phase.

        Args:
            phase: Task phase to filter by

        Returns:
            List of task IDs in that phase
        """
        return self.phases.get(phase.value, [])

    @beartype
    @require(lambda self, task_id: isinstance(task_id, str) and len(task_id) > 0, "Task ID must be non-empty")
    @ensure(lambda result: result is None or isinstance(result, Task), "Must return Task or None")
    def get_task(self, task_id: str) -> Task | None:
        """
        Get task by ID.

        Args:
            task_id: Task ID to look up

        Returns:
            Task instance or None if not found
        """
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    @beartype
    @require(lambda self, task_id: isinstance(task_id, str) and len(task_id) > 0, "Task ID must be non-empty")
    @ensure(lambda result: isinstance(result, list), "Must return list of task IDs")
    def get_dependencies(self, task_id: str) -> list[str]:
        """
        Get all dependencies for a task (recursive).

        Args:
            task_id: Task ID to get dependencies for

        Returns:
            List of all dependency task IDs (including transitive)
        """
        task = self.get_task(task_id)
        if task is None:
            return []

        dependencies: set[str] = set(task.dependencies)
        # Recursively collect transitive dependencies
        for dep_id in task.dependencies:
            dependencies.update(self.get_dependencies(dep_id))

        return sorted(dependencies)

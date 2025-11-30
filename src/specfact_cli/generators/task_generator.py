"""
Task generator for converting plan bundles and SDD manifests into actionable tasks.

This module generates dependency-ordered task breakdowns from project bundles
and SDD manifests, organizing tasks by phase and linking them to user stories.
"""

from __future__ import annotations

from datetime import UTC, datetime

from beartype import beartype
from icontract import ensure, require

from specfact_cli.models.plan import Feature, PlanBundle, Story
from specfact_cli.models.project import ProjectBundle
from specfact_cli.models.sdd import SDDManifest
from specfact_cli.models.task import Task, TaskList, TaskPhase


@beartype
@require(lambda bundle: isinstance(bundle, (ProjectBundle, PlanBundle)), "Bundle must be ProjectBundle or PlanBundle")
@require(lambda sdd: sdd is None or isinstance(sdd, SDDManifest), "SDD must be None or SDDManifest")
@ensure(lambda result: isinstance(result, TaskList), "Must return TaskList")
def generate_tasks(
    bundle: ProjectBundle | PlanBundle, sdd: SDDManifest | None = None, bundle_name: str | None = None
) -> TaskList:
    """
    Generate task breakdown from project bundle and SDD manifest.

    Args:
        bundle: Project bundle (modular or monolithic)
        sdd: SDD manifest (optional, provides architecture context)
        bundle_name: Bundle name (required for ProjectBundle, auto-detected for PlanBundle)

    Returns:
        TaskList with dependency-ordered tasks organized by phase
    """
    # Extract bundle name
    if bundle_name is None:
        bundle_name = bundle.bundle_name if isinstance(bundle, ProjectBundle) else "default"

    # Compute plan bundle hash
    summary = bundle.compute_summary(include_hash=True)
    plan_hash = summary.content_hash or "unknown"

    # Generate tasks organized by phase
    tasks: list[Task] = []
    task_counter = 1

    # Phase 1: Setup tasks
    setup_tasks = _generate_setup_tasks(bundle, sdd, task_counter)
    tasks.extend(setup_tasks)
    task_counter += len(setup_tasks)

    # Phase 2: Foundational tasks (from SDD HOW section)
    foundational_tasks = _generate_foundational_tasks(bundle, sdd, task_counter)
    tasks.extend(foundational_tasks)
    task_counter += len(foundational_tasks)

    # Phase 3: User story tasks
    story_tasks, story_mappings = _generate_story_tasks(bundle, sdd, task_counter)
    tasks.extend(story_tasks)
    task_counter += len(story_tasks)

    # Phase 4: Polish tasks
    polish_tasks = _generate_polish_tasks(bundle, sdd, task_counter, len(tasks))
    tasks.extend(polish_tasks)

    # Build phase mapping
    phases: dict[str, list[str]] = {
        TaskPhase.SETUP.value: [t.id for t in setup_tasks],
        TaskPhase.FOUNDATIONAL.value: [t.id for t in foundational_tasks],
        TaskPhase.USER_STORIES.value: [t.id for t in story_tasks],
        TaskPhase.POLISH.value: [t.id for t in polish_tasks],
    }

    # Create task list
    return TaskList(
        version="1.0.0",
        plan_bundle_hash=plan_hash,
        bundle_name=bundle_name,
        generated_at=datetime.now(UTC).isoformat(),
        tasks=tasks,
        phases=phases,
        story_mappings=story_mappings,
    )


@beartype
@require(lambda bundle: isinstance(bundle, (ProjectBundle, PlanBundle)), "Bundle must be ProjectBundle or PlanBundle")
@require(lambda sdd: sdd is None or isinstance(sdd, SDDManifest), "SDD must be None or SDDManifest")
@ensure(lambda result: isinstance(result, list), "Must return list of Tasks")
def _generate_setup_tasks(bundle: ProjectBundle | PlanBundle, sdd: SDDManifest | None, start_id: int) -> list[Task]:
    """Generate setup phase tasks (project structure, dependencies, config)."""
    tasks: list[Task] = []

    # Task: Initialize project structure
    tasks.append(
        Task(
            id=f"TASK-{start_id:03d}",
            phase=TaskPhase.SETUP,
            title="Initialize project structure",
            description="Create project directory structure, configuration files, and basic setup",
            file_path=None,  # Multiple files
            dependencies=[],
            story_keys=[],
            parallelizable=False,
            acceptance_criteria=[
                "Project directory structure created",
                "Configuration files initialized",
                "Dependencies file (requirements.txt, pyproject.toml, etc.) created",
            ],
            tags=["setup", "structure"],
        )
    )

    # Task: Setup development environment
    tasks.append(
        Task(
            id=f"TASK-{start_id + 1:03d}",
            phase=TaskPhase.SETUP,
            title="Setup development environment",
            description="Configure development tools, linters, formatters, and testing framework",
            file_path=None,
            dependencies=[f"TASK-{start_id:03d}"],
            story_keys=[],
            parallelizable=False,
            acceptance_criteria=[
                "Linting and formatting tools configured",
                "Testing framework setup",
                "Pre-commit hooks configured (if applicable)",
            ],
            tags=["setup", "dev-tools"],
        )
    )

    return tasks


@beartype
@require(lambda bundle: isinstance(bundle, (ProjectBundle, PlanBundle)), "Bundle must be ProjectBundle or PlanBundle")
@require(lambda sdd: sdd is None or isinstance(sdd, SDDManifest), "SDD must be None or SDDManifest")
@ensure(lambda result: isinstance(result, list), "Must return list of Tasks")
def _generate_foundational_tasks(
    bundle: ProjectBundle | PlanBundle, sdd: SDDManifest | None, start_id: int
) -> list[Task]:
    """Generate foundational tasks from SDD HOW section (architecture, contracts, module boundaries)."""
    tasks: list[Task] = []
    current_id = start_id

    if sdd and sdd.how:
        how = sdd.how

        # Task: Implement core models/base classes
        if how.architecture or how.module_boundaries:
            tasks.append(
                Task(
                    id=f"TASK-{current_id:03d}",
                    phase=TaskPhase.FOUNDATIONAL,
                    title="Implement core models and base classes",
                    description=f"Create foundational models and base classes based on architecture: {how.architecture[:100] if how.architecture else 'N/A'}",
                    file_path="src/models/base.py",  # Example path
                    dependencies=[],
                    story_keys=[],
                    parallelizable=False,
                    acceptance_criteria=[
                        "Core models defined",
                        "Base classes implemented",
                        "Type definitions in place",
                    ],
                    tags=["foundational", "models"],
                )
            )
            current_id += 1

        # Task: Define module boundaries
        if how.module_boundaries:
            for _idx, boundary in enumerate(how.module_boundaries[:5], 1):  # Limit to first 5
                tasks.append(
                    Task(
                        id=f"TASK-{current_id:03d}",
                        phase=TaskPhase.FOUNDATIONAL,
                        title=f"Define module boundary: {boundary[:50]}",
                        description=f"Establish module boundary and interface: {boundary}",
                        file_path=None,
                        dependencies=[],
                        story_keys=[],
                        parallelizable=True,  # Boundaries can be defined in parallel
                        acceptance_criteria=[f"Module boundary '{boundary}' defined", "Interface contracts specified"],
                        tags=["foundational", "architecture", "boundaries"],
                    )
                )
                current_id += 1

        # Task: Implement contract stubs
        if how.contracts:
            tasks.append(
                Task(
                    id=f"TASK-{current_id:03d}",
                    phase=TaskPhase.FOUNDATIONAL,
                    title="Implement contract stubs",
                    description=f"Create contract stubs for {len(how.contracts)} contract(s) from SDD HOW section",
                    file_path="src/contracts/",
                    dependencies=[],
                    story_keys=[],
                    parallelizable=False,
                    acceptance_criteria=[
                        f"Contract stubs created for {len(how.contracts)} contract(s)",
                        "Contract interfaces defined",
                        "Preconditions and postconditions specified",
                    ],
                    tags=["foundational", "contracts"],
                )
            )
            current_id += 1

    return tasks


@beartype
@require(lambda bundle: isinstance(bundle, (ProjectBundle, PlanBundle)), "Bundle must be ProjectBundle or PlanBundle")
@require(lambda sdd: sdd is None or isinstance(sdd, SDDManifest), "SDD must be None or SDDManifest")
@ensure(
    lambda result: isinstance(result, tuple) and len(result) == 2,
    "Must return (list of Tasks, story_mappings dict) tuple",
)
def _generate_story_tasks(
    bundle: ProjectBundle | PlanBundle, sdd: SDDManifest | None, start_id: int
) -> tuple[list[Task], dict[str, list[str]]]:
    """Generate user story implementation tasks."""
    tasks: list[Task] = []
    story_mappings: dict[str, list[str]] = {}
    current_id = start_id

    # Get features list
    features_list = list(bundle.features.values()) if isinstance(bundle, ProjectBundle) else bundle.features

    # Generate tasks for each feature and story
    for feature in features_list:
        for story_idx, story in enumerate(feature.stories, 1):
            story_key = story.key
            story_label = f"US{story_idx}"

            # Task: Implement story
            task_id = f"TASK-{current_id:03d}"
            tasks.append(
                Task(
                    id=task_id,
                    phase=TaskPhase.USER_STORIES,
                    title=f"Implement {story_key}: {story.title}",
                    description=f"Implement user story: {story.title}\n\nAcceptance Criteria:\n"
                    + "\n".join(f"  - {ac}" for ac in story.acceptance),
                    file_path=_infer_file_path_from_story(story, feature),
                    dependencies=_infer_story_dependencies(story, feature, current_id),
                    story_keys=[story_label],
                    parallelizable=len(story.acceptance) <= 3,  # Simple stories can be parallelized
                    acceptance_criteria=story.acceptance.copy(),
                    tags=["user-story", feature.key.lower()],
                )
            )

            # Map story to task
            if story_key not in story_mappings:
                story_mappings[story_key] = []
            story_mappings[story_key].append(task_id)

            current_id += 1

            # Task: Write tests for story (if acceptance criteria exist)
            if story.acceptance:
                test_task_id = f"TASK-{current_id:03d}"
                tasks.append(
                    Task(
                        id=test_task_id,
                        phase=TaskPhase.USER_STORIES,
                        title=f"Write tests for {story_key}",
                        description=f"Create tests covering acceptance criteria for {story_key}",
                        file_path=_infer_test_path_from_story(story, feature),
                        dependencies=[task_id],  # Tests depend on implementation
                        story_keys=[story_label],
                        parallelizable=False,
                        acceptance_criteria=[f"Tests cover all {len(story.acceptance)} acceptance criteria"],
                        tags=["test", "user-story", feature.key.lower()],
                    )
                )

                story_mappings[story_key].append(test_task_id)
                current_id += 1

    return tasks, story_mappings


@beartype
@require(lambda bundle: isinstance(bundle, (ProjectBundle, PlanBundle)), "Bundle must be ProjectBundle or PlanBundle")
@require(lambda sdd: sdd is None or isinstance(sdd, SDDManifest), "SDD must be None or SDDManifest")
@ensure(lambda result: isinstance(result, list), "Must return list of Tasks")
def _generate_polish_tasks(
    bundle: ProjectBundle | PlanBundle, sdd: SDDManifest | None, start_id: int, total_tasks_before: int
) -> list[Task]:
    """Generate polish phase tasks (tests, docs, optimization)."""
    tasks: list[Task] = []
    current_id = start_id

    # Task: Integration tests
    tasks.append(
        Task(
            id=f"TASK-{current_id:03d}",
            phase=TaskPhase.POLISH,
            title="Write integration tests",
            description="Create integration tests covering feature interactions and end-to-end workflows",
            file_path="tests/integration/",
            dependencies=[f"TASK-{i:03d}" for i in range(1, total_tasks_before + 1)],  # Depends on all previous tasks
            story_keys=[],
            parallelizable=False,
            acceptance_criteria=[
                "Integration tests cover major feature interactions",
                "End-to-end workflows tested",
                "Test coverage meets threshold",
            ],
            tags=["polish", "integration-tests"],
        )
    )
    current_id += 1

    # Task: Documentation
    tasks.append(
        Task(
            id=f"TASK-{current_id:03d}",
            phase=TaskPhase.POLISH,
            title="Write documentation",
            description="Create user and developer documentation",
            file_path="docs/",
            dependencies=[f"TASK-{i:03d}" for i in range(1, total_tasks_before + 1)],
            story_keys=[],
            parallelizable=False,
            acceptance_criteria=[
                "API documentation complete",
                "User guide written",
                "Developer guide written",
            ],
            tags=["polish", "documentation"],
        )
    )
    current_id += 1

    # Task: Performance optimization
    tasks.append(
        Task(
            id=f"TASK-{current_id:03d}",
            phase=TaskPhase.POLISH,
            title="Performance optimization",
            description="Optimize code for performance, identify bottlenecks, and improve efficiency",
            file_path=None,
            dependencies=[f"TASK-{i:03d}" for i in range(1, total_tasks_before + 1)],
            story_keys=[],
            parallelizable=False,
            acceptance_criteria=[
                "Performance benchmarks meet targets",
                "Bottlenecks identified and addressed",
                "Code profiling completed",
            ],
            tags=["polish", "optimization"],
        )
    )

    return tasks


@beartype
@require(lambda story: isinstance(story, Story), "Story must be Story")
@require(lambda feature: isinstance(feature, Feature), "Feature must be Feature")
@ensure(lambda result: isinstance(result, str) or result is None, "Must return str or None")
def _infer_file_path_from_story(story: Story, feature: Feature) -> str | None:
    """Infer file path from story and feature context."""
    # Simple heuristic: use feature key to infer path
    feature_key_lower = feature.key.lower().replace("feature-", "").replace("_", "-")
    return f"src/{feature_key_lower}/service.py"


@beartype
@require(lambda story: isinstance(story, Story), "Story must be Story")
@require(lambda feature: isinstance(feature, Feature), "Feature must be Feature")
@ensure(lambda result: isinstance(result, str) or result is None, "Must return str or None")
def _infer_test_path_from_story(story: Story, feature: Feature) -> str | None:
    """Infer test file path from story and feature context."""
    feature_key_lower = feature.key.lower().replace("feature-", "").replace("_", "-")
    return f"tests/unit/{feature_key_lower}/test_service.py"


@beartype
@require(lambda story: isinstance(story, Story), "Story must be Story")
@require(lambda feature: isinstance(feature, Feature), "Feature must be Feature")
@ensure(lambda result: isinstance(result, list), "Must return list of task IDs")
def _infer_story_dependencies(story: Story, feature: Feature, current_id: int) -> list[str]:
    """Infer task dependencies from story context."""
    # Simple heuristic: stories in the same feature depend on foundational tasks
    # In a real implementation, this would analyze story relationships
    return []  # No dependencies for now (can be enhanced with story dependency analysis)

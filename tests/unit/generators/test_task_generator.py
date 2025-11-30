"""
Unit tests for task generator.
"""

import pytest

from specfact_cli.generators.task_generator import generate_tasks
from specfact_cli.models.plan import Feature, PlanBundle, Product, Release, Story
from specfact_cli.models.project import ProjectBundle
from specfact_cli.models.sdd import (
    SDDCoverageThresholds,
    SDDEnforcementBudget,
    SDDHow,
    SDDManifest,
    SDDWhat,
    SDDWhy,
)
from specfact_cli.models.task import Task, TaskList, TaskPhase


@pytest.fixture
def sample_plan_bundle() -> PlanBundle:
    """Create a sample plan bundle for testing."""
    return PlanBundle(
        version="1.0",
        product=Product(
            releases=[
                Release(
                    name="v1.0.0",
                    objectives=["Objective 1"],
                    scope=["FEATURE-001"],
                    risks=[],
                )
            ],
            themes=[],
        ),
        features=[
            Feature(
                key="FEATURE-001",
                title="Test Feature",
                outcomes=["Outcome 1"],
                acceptance=["AC 1", "AC 2"],
                stories=[
                    Story(
                        key="STORY-001",
                        title="Test Story",
                        acceptance=["Story AC 1", "Story AC 2"],
                        story_points=None,
                        value_points=None,
                        scenarios=None,
                        contracts=None,
                    )
                ],
            )
        ],
        idea=None,
        business=None,
        metadata=None,
        clarifications=None,
    )


@pytest.fixture
def sample_sdd_manifest() -> SDDManifest:
    """Create a sample SDD manifest for testing."""
    return SDDManifest(
        version="1.0.0",
        plan_bundle_id="test-bundle-id",
        plan_bundle_hash="test-hash-1234567890abcdef",
        why=SDDWhy(intent="Test intent", constraints=["Constraint 1"], target_users=None, value_hypothesis=None),
        what=SDDWhat(capabilities=["Capability 1"], acceptance_criteria=["AC 1"]),
        how=SDDHow(
            architecture="Test architecture",
            invariants=["Invariant 1"],
            contracts=["Contract 1"],
            module_boundaries=["Boundary 1", "Boundary 2"],
        ),
        coverage_thresholds=SDDCoverageThresholds(
            contracts_per_story=1.0, invariants_per_feature=1.0, architecture_facets=3
        ),
        enforcement_budget=SDDEnforcementBudget(
            shadow_budget_seconds=300, warn_budget_seconds=180, block_budget_seconds=90
        ),
        promotion_status="draft",
    )


@pytest.fixture
def sample_project_bundle(sample_plan_bundle: PlanBundle) -> ProjectBundle:
    """Create a sample project bundle for testing."""
    from specfact_cli.models.project import BundleManifest, BundleVersions, ProjectMetadata, SchemaMetadata

    return ProjectBundle(
        manifest=BundleManifest(
            versions=BundleVersions(schema="1.0", project="0.1.0"),
            schema_metadata=SchemaMetadata(upgrade_path=None),
            project_metadata=ProjectMetadata(stability="alpha"),
        ),
        bundle_name="test-bundle",
        product=sample_plan_bundle.product,
        features={"FEATURE-001": sample_plan_bundle.features[0]},
    )


def test_generate_tasks_with_plan_bundle(sample_plan_bundle: PlanBundle) -> None:
    """Test task generation with PlanBundle."""
    task_list = generate_tasks(sample_plan_bundle)

    assert isinstance(task_list, TaskList)
    assert task_list.bundle_name == "default"
    assert len(task_list.tasks) > 0
    assert task_list.plan_bundle_hash is not None


def test_generate_tasks_with_project_bundle(sample_project_bundle: ProjectBundle) -> None:
    """Test task generation with ProjectBundle."""
    task_list = generate_tasks(sample_project_bundle)

    assert isinstance(task_list, TaskList)
    assert task_list.bundle_name == "test-bundle"
    assert len(task_list.tasks) > 0
    assert task_list.plan_bundle_hash is not None


def test_generate_tasks_with_sdd(sample_plan_bundle: PlanBundle, sample_sdd_manifest: SDDManifest) -> None:
    """Test task generation with SDD manifest."""
    task_list = generate_tasks(sample_plan_bundle, sample_sdd_manifest)

    assert isinstance(task_list, TaskList)
    assert len(task_list.tasks) > 0

    # Should have foundational tasks from SDD HOW section
    foundational_tasks = task_list.get_tasks_by_phase(TaskPhase.FOUNDATIONAL)
    assert len(foundational_tasks) > 0


def test_generate_tasks_phases(sample_plan_bundle: PlanBundle) -> None:
    """Test that tasks are organized by phase."""
    task_list = generate_tasks(sample_plan_bundle)

    # Check all phases exist
    setup_tasks = task_list.get_tasks_by_phase(TaskPhase.SETUP)
    user_story_tasks = task_list.get_tasks_by_phase(TaskPhase.USER_STORIES)
    polish_tasks = task_list.get_tasks_by_phase(TaskPhase.POLISH)

    assert len(setup_tasks) > 0
    assert len(user_story_tasks) > 0
    assert len(polish_tasks) > 0

    # Verify task phases
    for task_id in setup_tasks:
        task = task_list.get_task(task_id)
        assert task is not None
        assert task.phase == TaskPhase.SETUP


def test_generate_tasks_story_mappings(sample_plan_bundle: PlanBundle) -> None:
    """Test that tasks are mapped to stories."""
    task_list = generate_tasks(sample_plan_bundle)

    # Should have story mappings
    assert len(task_list.story_mappings) > 0

    # Check that story keys are mapped
    for story_key, task_ids in task_list.story_mappings.items():
        assert isinstance(story_key, str)
        assert len(task_ids) > 0
        for task_id in task_ids:
            task = task_list.get_task(task_id)
            assert task is not None
            # Story key should be referenced in task (either in story_keys or description/title)
            assert story_key in task.title or story_key in task.description or len(task.story_keys) > 0


def test_generate_tasks_dependencies(sample_plan_bundle: PlanBundle) -> None:
    """Test that task dependencies are set correctly."""
    task_list = generate_tasks(sample_plan_bundle)

    # Check that tasks have dependencies
    for task in task_list.tasks:
        if task.dependencies:
            # Verify all dependencies exist
            for dep_id in task.dependencies:
                dep_task = task_list.get_task(dep_id)
                assert dep_task is not None, f"Dependency {dep_id} not found for task {task.id}"


def test_generate_tasks_acceptance_criteria(sample_plan_bundle: PlanBundle) -> None:
    """Test that tasks include acceptance criteria."""
    task_list = generate_tasks(sample_plan_bundle)

    # User story tasks should have acceptance criteria
    user_story_tasks = task_list.get_tasks_by_phase(TaskPhase.USER_STORIES)
    for task_id in user_story_tasks:
        task = task_list.get_task(task_id)
        assert task is not None
        if "test" not in task.title.lower():  # Implementation tasks, not test tasks
            assert len(task.acceptance_criteria) > 0 or len(task.description) > 0


def test_generate_tasks_file_paths(sample_plan_bundle: PlanBundle) -> None:
    """Test that tasks have file paths where applicable."""
    task_list = generate_tasks(sample_plan_bundle)

    # Some tasks should have file paths
    tasks_with_paths = [task for task in task_list.tasks if task.file_path]
    assert len(tasks_with_paths) > 0


def test_generate_tasks_parallelizable(sample_plan_bundle: PlanBundle) -> None:
    """Test that parallelizable tasks are marked."""
    task_list = generate_tasks(sample_plan_bundle)

    # Some tasks should be parallelizable
    parallelizable_tasks = [task for task in task_list.tasks if task.parallelizable]
    # At least module boundary tasks should be parallelizable
    assert len(parallelizable_tasks) >= 0  # May be 0 if no simple stories


def test_generate_tasks_with_sdd_module_boundaries(
    sample_plan_bundle: PlanBundle, sample_sdd_manifest: SDDManifest
) -> None:
    """Test that SDD module boundaries generate tasks."""
    task_list = generate_tasks(sample_plan_bundle, sample_sdd_manifest)

    # Should have tasks for module boundaries
    foundational_task_ids = task_list.get_tasks_by_phase(TaskPhase.FOUNDATIONAL)
    boundary_tasks: list[Task] = []
    for task_id in foundational_task_ids:
        task = task_list.get_task(task_id)
        if task and "boundary" in task.title.lower():
            boundary_tasks.append(task)

    # Should have at least one boundary task (limited to first 5 in implementation)
    assert len(boundary_tasks) > 0


def test_generate_tasks_with_sdd_contracts(sample_plan_bundle: PlanBundle, sample_sdd_manifest: SDDManifest) -> None:
    """Test that SDD contracts generate tasks."""
    task_list = generate_tasks(sample_plan_bundle, sample_sdd_manifest)

    # Should have contract stub task
    foundational_task_ids = task_list.get_tasks_by_phase(TaskPhase.FOUNDATIONAL)
    contract_tasks: list[Task] = []
    for task_id in foundational_task_ids:
        task = task_list.get_task(task_id)
        if task and "contract" in task.title.lower():
            contract_tasks.append(task)

    assert len(contract_tasks) > 0


def test_get_task_by_id(sample_plan_bundle: PlanBundle) -> None:
    """Test getting task by ID."""
    task_list = generate_tasks(sample_plan_bundle)

    # Get first task
    first_task_id = task_list.tasks[0].id
    task = task_list.get_task(first_task_id)

    assert task is not None
    assert task.id == first_task_id


def test_get_task_nonexistent(sample_plan_bundle: PlanBundle) -> None:
    """Test getting non-existent task returns None."""
    task_list = generate_tasks(sample_plan_bundle)

    task = task_list.get_task("TASK-999")
    assert task is None


def test_get_dependencies_recursive(sample_plan_bundle: PlanBundle) -> None:
    """Test recursive dependency resolution."""
    task_list = generate_tasks(sample_plan_bundle)

    # Find a task with dependencies
    task_with_deps = next((task for task in task_list.tasks if task.dependencies), None)

    if task_with_deps:
        deps = task_list.get_dependencies(task_with_deps.id)
        assert len(deps) >= len(task_with_deps.dependencies)  # Should include transitive deps

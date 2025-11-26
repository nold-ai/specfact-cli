"""Unit tests for plan update-idea and update-feature commands.

Focus: Business logic and edge cases only (@beartype handles type validation).
"""

import pytest
from typer.testing import CliRunner

from specfact_cli.cli import app
from specfact_cli.commands.plan import _convert_plan_bundle_to_project_bundle
from specfact_cli.models.plan import Idea, PlanBundle, Product
from specfact_cli.utils.bundle_loader import load_project_bundle, save_project_bundle


runner = CliRunner()


@pytest.fixture
def sample_bundle_with_idea(tmp_path, monkeypatch):
    """Create a sample modular bundle with idea section for testing."""
    monkeypatch.chdir(tmp_path)

    # Create .specfact structure
    projects_dir = tmp_path / ".specfact" / "projects"
    projects_dir.mkdir(parents=True)

    bundle_name = "test-bundle"
    bundle_dir = projects_dir / bundle_name
    bundle_dir.mkdir()

    # Create PlanBundle and convert to ProjectBundle
    plan_bundle = PlanBundle(
        version="1.0",
        idea=Idea(
            title="Test Project",
            narrative="Test narrative",
            target_users=["Developer"],
            value_hypothesis="Test hypothesis",
            constraints=["Test constraint"],
            metrics=None,
        ),
        business=None,
        product=Product(themes=["Testing"]),
        features=[],
        metadata=None,
        clarifications=None,
    )

    project_bundle = _convert_plan_bundle_to_project_bundle(plan_bundle, bundle_name)
    save_project_bundle(project_bundle, bundle_dir, atomic=True)

    return bundle_name


@pytest.fixture
def sample_bundle_without_idea(tmp_path, monkeypatch):
    """Create a sample modular bundle without idea section for testing."""
    monkeypatch.chdir(tmp_path)

    # Create .specfact structure
    projects_dir = tmp_path / ".specfact" / "projects"
    projects_dir.mkdir(parents=True)

    bundle_name = "test-bundle"
    bundle_dir = projects_dir / bundle_name
    bundle_dir.mkdir()

    # Create PlanBundle and convert to ProjectBundle
    plan_bundle = PlanBundle(
        version="1.0",
        idea=None,
        business=None,
        product=Product(themes=["Testing"]),
        features=[],
        metadata=None,
        clarifications=None,
    )

    project_bundle = _convert_plan_bundle_to_project_bundle(plan_bundle, bundle_name)
    save_project_bundle(project_bundle, bundle_dir, atomic=True)

    return bundle_name


class TestPlanUpdateIdea:
    """Test suite for plan update-idea command."""

    def test_update_idea_target_users(self, sample_bundle_with_idea, tmp_path, monkeypatch):
        """Test updating target users."""
        monkeypatch.chdir(tmp_path)
        bundle_dir = tmp_path / ".specfact" / "projects" / sample_bundle_with_idea

        result = runner.invoke(
            app,
            [
                "plan",
                "update-idea",
                "--target-users",
                "Python developers, DevOps engineers",
                "--bundle",
                sample_bundle_with_idea,
            ],
        )

        assert result.exit_code == 0
        assert "updated successfully" in result.stdout.lower()

        # Verify target users were updated
        updated_bundle = load_project_bundle(bundle_dir, validate_hashes=False)
        assert updated_bundle.idea is not None
        assert len(updated_bundle.idea.target_users) == 2
        assert "Python developers" in updated_bundle.idea.target_users
        assert "DevOps engineers" in updated_bundle.idea.target_users

    def test_update_idea_value_hypothesis(self, sample_bundle_with_idea, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        bundle_dir = tmp_path / ".specfact" / "projects" / sample_bundle_with_idea
        """Test updating value hypothesis."""
        result = runner.invoke(
            app,
            [
                "plan",
                "update-idea",
                "--value-hypothesis",
                "New value hypothesis",
                "--bundle",
                sample_bundle_with_idea,
            ],
        )

        assert result.exit_code == 0

        # Verify value hypothesis was updated
        updated_bundle = load_project_bundle(bundle_dir, validate_hashes=False)
        assert updated_bundle.idea is not None
        assert updated_bundle.idea.value_hypothesis == "New value hypothesis"

    def test_update_idea_constraints(self, sample_bundle_with_idea, tmp_path, monkeypatch):
        """Test updating constraints."""
        monkeypatch.chdir(tmp_path)
        bundle_dir = tmp_path / ".specfact" / "projects" / sample_bundle_with_idea

        result = runner.invoke(
            app,
            [
                "plan",
                "update-idea",
                "--constraints",
                "Constraint 1, Constraint 2, Constraint 3",
                "--bundle",
                sample_bundle_with_idea,
            ],
        )

        assert result.exit_code == 0

        # Verify constraints were updated
        updated_bundle = load_project_bundle(bundle_dir, validate_hashes=False)
        assert updated_bundle.idea is not None
        assert len(updated_bundle.idea.constraints) == 3
        assert "Constraint 1" in updated_bundle.idea.constraints
        assert "Constraint 2" in updated_bundle.idea.constraints
        assert "Constraint 3" in updated_bundle.idea.constraints

    def test_update_idea_title(self, sample_bundle_with_idea, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        bundle_dir = tmp_path / ".specfact" / "projects" / sample_bundle_with_idea
        """Test updating idea title."""
        result = runner.invoke(
            app,
            [
                "plan",
                "update-idea",
                "--title",
                "Updated Title",
                "--bundle",
                sample_bundle_with_idea,
            ],
        )

        assert result.exit_code == 0

        # Verify title was updated
        updated_bundle = load_project_bundle(bundle_dir, validate_hashes=False)
        assert updated_bundle.idea is not None
        assert updated_bundle.idea.title == "Updated Title"

    def test_update_idea_narrative(self, sample_bundle_with_idea, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        bundle_dir = tmp_path / ".specfact" / "projects" / sample_bundle_with_idea
        """Test updating idea narrative."""
        result = runner.invoke(
            app,
            [
                "plan",
                "update-idea",
                "--narrative",
                "Updated narrative description",
                "--bundle",
                sample_bundle_with_idea,
            ],
        )

        assert result.exit_code == 0

        # Verify narrative was updated
        updated_bundle = load_project_bundle(bundle_dir, validate_hashes=False)
        assert updated_bundle.idea is not None
        assert updated_bundle.idea.narrative == "Updated narrative description"

    def test_update_idea_multiple_fields(self, sample_bundle_with_idea, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        bundle_dir = tmp_path / ".specfact" / "projects" / sample_bundle_with_idea
        """Test updating multiple idea fields at once."""
        result = runner.invoke(
            app,
            [
                "plan",
                "update-idea",
                "--target-users",
                "User 1, User 2",
                "--value-hypothesis",
                "New hypothesis",
                "--constraints",
                "Constraint A, Constraint B",
                "--bundle",
                sample_bundle_with_idea,
            ],
        )

        assert result.exit_code == 0

        # Verify all fields were updated
        updated_bundle = load_project_bundle(bundle_dir, validate_hashes=False)
        assert updated_bundle.idea is not None
        assert len(updated_bundle.idea.target_users) == 2
        assert updated_bundle.idea.value_hypothesis == "New hypothesis"
        assert len(updated_bundle.idea.constraints) == 2

    def test_update_idea_creates_section_if_missing(self, sample_bundle_without_idea, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        bundle_dir = tmp_path / ".specfact" / "projects" / sample_bundle_without_idea
        """Test that update-idea creates idea section if it doesn't exist."""
        result = runner.invoke(
            app,
            [
                "plan",
                "update-idea",
                "--target-users",
                "New User",
                "--value-hypothesis",
                "New hypothesis",
                "--bundle",
                sample_bundle_without_idea,
            ],
        )

        assert result.exit_code == 0
        assert "Created new idea section" in result.stdout

        # Verify idea section was created
        updated_bundle = load_project_bundle(bundle_dir, validate_hashes=False)
        assert updated_bundle.idea is not None
        # Note: title might be None or "Untitled" depending on implementation
        assert len(updated_bundle.idea.target_users) == 1
        assert updated_bundle.idea.value_hypothesis == "New hypothesis"

    def test_update_idea_no_updates_specified(self, sample_bundle_with_idea, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        """Test that update-idea fails when no updates are specified."""
        result = runner.invoke(
            app,
            [
                "plan",
                "update-idea",
                "--bundle",
                sample_bundle_with_idea,
            ],
        )

        assert result.exit_code == 1
        assert "No updates specified" in result.stdout

    def test_update_idea_missing_plan(self, tmp_path, monkeypatch):
        """Test that update-idea fails when bundle doesn't exist."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(
            app,
            [
                "plan",
                "update-idea",
                "--target-users",
                "User",
                "--bundle",
                "nonexistent-bundle",
            ],
        )

        assert result.exit_code == 1
        assert "not found" in result.stdout.lower()

    def test_update_idea_invalid_plan(self, tmp_path, monkeypatch):
        """Test that update-idea fails when bundle is invalid."""
        monkeypatch.chdir(tmp_path)
        # Create invalid bundle directory structure
        projects_dir = tmp_path / ".specfact" / "projects"
        projects_dir.mkdir(parents=True)
        bundle_dir = projects_dir / "invalid-bundle"
        bundle_dir.mkdir()
        # Create invalid manifest
        (bundle_dir / "bundle.manifest.yaml").write_text("invalid: yaml: content")

        result = runner.invoke(
            app,
            [
                "plan",
                "update-idea",
                "--target-users",
                "User",
                "--bundle",
                "invalid-bundle",
            ],
        )

        assert result.exit_code == 1
        assert (
            "not found" in result.stdout.lower()
            or "validation failed" in result.stdout.lower()
            or "failed to load" in result.stdout.lower()
        )

    def test_update_idea_default_path(self, tmp_path, monkeypatch):
        """Test update-idea using default bundle."""
        monkeypatch.chdir(tmp_path)

        # Create default bundle
        projects_dir = tmp_path / ".specfact" / "projects"
        projects_dir.mkdir(parents=True)
        bundle_name = "main"  # Default bundle name
        bundle_dir = projects_dir / bundle_name
        bundle_dir.mkdir()

        plan_bundle = PlanBundle(
            version="1.0",
            idea=Idea(
                title="Test",
                narrative="Test",
                target_users=[],
                value_hypothesis="",
                constraints=[],
                metrics=None,
            ),
            business=None,
            product=Product(themes=["Testing"]),
            features=[],
            metadata=None,
            clarifications=None,
        )
        project_bundle = _convert_plan_bundle_to_project_bundle(plan_bundle, bundle_name)
        save_project_bundle(project_bundle, bundle_dir, atomic=True)

        # Update idea without specifying bundle (should use default)
        result = runner.invoke(
            app,
            [
                "plan",
                "update-idea",
                "--target-users",
                "Default User",
            ],
        )

        assert result.exit_code == 0
        assert bundle_dir.exists()

        # Verify idea was updated
        updated_bundle = load_project_bundle(bundle_dir, validate_hashes=False)
        assert updated_bundle.idea is not None
        assert len(updated_bundle.idea.target_users) == 1
        assert "Default User" in updated_bundle.idea.target_users

    def test_update_idea_preserves_existing_fields(self, sample_bundle_with_idea, tmp_path, monkeypatch):
        """Test that update-idea preserves fields not being updated."""
        monkeypatch.chdir(tmp_path)
        bundle_dir = tmp_path / ".specfact" / "projects" / sample_bundle_with_idea

        # Get original values
        original_bundle = load_project_bundle(bundle_dir, validate_hashes=False)
        assert original_bundle.idea is not None
        original_title = original_bundle.idea.title
        original_narrative = original_bundle.idea.narrative

        # Update only target_users
        result = runner.invoke(
            app,
            [
                "plan",
                "update-idea",
                "--target-users",
                "New User",
                "--bundle",
                sample_bundle_with_idea,
            ],
        )

        assert result.exit_code == 0

        # Verify only target_users changed, others preserved
        updated_bundle = load_project_bundle(bundle_dir, validate_hashes=False)
        assert updated_bundle.idea is not None
        assert updated_bundle.idea.title == original_title
        assert updated_bundle.idea.narrative == original_narrative
        assert len(updated_bundle.idea.target_users) == 1
        assert "New User" in updated_bundle.idea.target_users

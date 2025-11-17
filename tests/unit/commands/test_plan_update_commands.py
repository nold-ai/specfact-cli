"""Unit tests for plan update-idea and update-feature commands.

Focus: Business logic and edge cases only (@beartype handles type validation).
"""

import pytest
from typer.testing import CliRunner

from specfact_cli.cli import app
from specfact_cli.generators.plan_generator import PlanGenerator
from specfact_cli.models.plan import Idea, PlanBundle, Product
from specfact_cli.validators.schema import validate_plan_bundle


runner = CliRunner()


@pytest.fixture
def sample_plan_with_idea(tmp_path):
    """Create a sample plan bundle with idea section for testing."""
    plan_path = tmp_path / "plan.yaml"
    bundle = PlanBundle(
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
    generator = PlanGenerator()
    generator.generate(bundle, plan_path)
    return plan_path


@pytest.fixture
def sample_plan_without_idea(tmp_path):
    """Create a sample plan bundle without idea section for testing."""
    plan_path = tmp_path / "plan.yaml"
    bundle = PlanBundle(
        idea=None,
        business=None,
        product=Product(themes=["Testing"]),
        features=[],
        metadata=None,
        clarifications=None,
    )
    generator = PlanGenerator()
    generator.generate(bundle, plan_path)
    return plan_path


class TestPlanUpdateIdea:
    """Test suite for plan update-idea command."""

    def test_update_idea_target_users(self, sample_plan_with_idea):
        """Test updating target users."""
        result = runner.invoke(
            app,
            [
                "plan",
                "update-idea",
                "--target-users",
                "Python developers, DevOps engineers",
                "--plan",
                str(sample_plan_with_idea),
            ],
        )

        assert result.exit_code == 0
        assert "updated successfully" in result.stdout.lower()

        # Verify target users were updated
        is_valid, _error, bundle = validate_plan_bundle(sample_plan_with_idea)
        assert is_valid is True
        assert bundle is not None
        assert bundle.idea is not None
        assert len(bundle.idea.target_users) == 2
        assert "Python developers" in bundle.idea.target_users
        assert "DevOps engineers" in bundle.idea.target_users

    def test_update_idea_value_hypothesis(self, sample_plan_with_idea):
        """Test updating value hypothesis."""
        result = runner.invoke(
            app,
            [
                "plan",
                "update-idea",
                "--value-hypothesis",
                "New value hypothesis",
                "--plan",
                str(sample_plan_with_idea),
            ],
        )

        assert result.exit_code == 0

        # Verify value hypothesis was updated
        is_valid, _error, bundle = validate_plan_bundle(sample_plan_with_idea)
        assert is_valid is True
        assert bundle is not None
        assert bundle.idea is not None
        assert bundle.idea.value_hypothesis == "New value hypothesis"

    def test_update_idea_constraints(self, sample_plan_with_idea):
        """Test updating constraints."""
        result = runner.invoke(
            app,
            [
                "plan",
                "update-idea",
                "--constraints",
                "Constraint 1, Constraint 2, Constraint 3",
                "--plan",
                str(sample_plan_with_idea),
            ],
        )

        assert result.exit_code == 0

        # Verify constraints were updated
        is_valid, _error, bundle = validate_plan_bundle(sample_plan_with_idea)
        assert is_valid is True
        assert bundle is not None
        assert bundle.idea is not None
        assert len(bundle.idea.constraints) == 3
        assert "Constraint 1" in bundle.idea.constraints
        assert "Constraint 2" in bundle.idea.constraints
        assert "Constraint 3" in bundle.idea.constraints

    def test_update_idea_title(self, sample_plan_with_idea):
        """Test updating idea title."""
        result = runner.invoke(
            app,
            [
                "plan",
                "update-idea",
                "--title",
                "Updated Title",
                "--plan",
                str(sample_plan_with_idea),
            ],
        )

        assert result.exit_code == 0

        # Verify title was updated
        is_valid, _error, bundle = validate_plan_bundle(sample_plan_with_idea)
        assert is_valid is True
        assert bundle is not None
        assert bundle.idea is not None
        assert bundle.idea.title == "Updated Title"

    def test_update_idea_narrative(self, sample_plan_with_idea):
        """Test updating idea narrative."""
        result = runner.invoke(
            app,
            [
                "plan",
                "update-idea",
                "--narrative",
                "Updated narrative description",
                "--plan",
                str(sample_plan_with_idea),
            ],
        )

        assert result.exit_code == 0

        # Verify narrative was updated
        is_valid, _error, bundle = validate_plan_bundle(sample_plan_with_idea)
        assert is_valid is True
        assert bundle is not None
        assert bundle.idea is not None
        assert bundle.idea.narrative == "Updated narrative description"

    def test_update_idea_multiple_fields(self, sample_plan_with_idea):
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
                "--plan",
                str(sample_plan_with_idea),
            ],
        )

        assert result.exit_code == 0

        # Verify all fields were updated
        is_valid, _error, bundle = validate_plan_bundle(sample_plan_with_idea)
        assert is_valid is True
        assert bundle is not None
        assert bundle.idea is not None
        assert len(bundle.idea.target_users) == 2
        assert bundle.idea.value_hypothesis == "New hypothesis"
        assert len(bundle.idea.constraints) == 2

    def test_update_idea_creates_section_if_missing(self, sample_plan_without_idea):
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
                "--plan",
                str(sample_plan_without_idea),
            ],
        )

        assert result.exit_code == 0
        assert "Created new idea section" in result.stdout

        # Verify idea section was created
        is_valid, _error, bundle = validate_plan_bundle(sample_plan_without_idea)
        assert is_valid is True
        assert bundle is not None
        assert bundle.idea is not None
        assert bundle.idea.title == "Untitled"  # Default title when creating
        assert len(bundle.idea.target_users) == 1
        assert bundle.idea.value_hypothesis == "New hypothesis"

    def test_update_idea_no_updates_specified(self, sample_plan_with_idea):
        """Test that update-idea fails when no updates are specified."""
        result = runner.invoke(
            app,
            [
                "plan",
                "update-idea",
                "--plan",
                str(sample_plan_with_idea),
            ],
        )

        assert result.exit_code == 1
        assert "No updates specified" in result.stdout

    def test_update_idea_missing_plan(self, tmp_path):
        """Test that update-idea fails when plan doesn't exist."""
        plan_path = tmp_path / "nonexistent.yaml"

        result = runner.invoke(
            app,
            [
                "plan",
                "update-idea",
                "--target-users",
                "User",
                "--plan",
                str(plan_path),
            ],
        )

        assert result.exit_code == 1
        assert "not found" in result.stdout.lower()

    def test_update_idea_invalid_plan(self, tmp_path):
        """Test that update-idea fails when plan is invalid."""
        plan_path = tmp_path / "invalid.yaml"
        plan_path.write_text("invalid: yaml: content")

        result = runner.invoke(
            app,
            [
                "plan",
                "update-idea",
                "--target-users",
                "User",
                "--plan",
                str(plan_path),
            ],
        )

        assert result.exit_code == 1
        assert "validation failed" in result.stdout.lower()

    def test_update_idea_default_path(self, tmp_path, monkeypatch):
        """Test update-idea using default path."""
        monkeypatch.chdir(tmp_path)

        # Create default plan
        from specfact_cli.utils.structure import SpecFactStructure

        default_path = SpecFactStructure.get_default_plan_path()
        default_path.parent.mkdir(parents=True, exist_ok=True)

        bundle = PlanBundle(
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
        generator = PlanGenerator()
        generator.generate(bundle, default_path)

        # Update idea without specifying plan
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
        assert default_path.exists()

        # Verify idea was updated
        is_valid, _error, bundle = validate_plan_bundle(default_path)
        assert is_valid is True
        assert bundle is not None
        assert bundle.idea is not None
        assert len(bundle.idea.target_users) == 1
        assert "Default User" in bundle.idea.target_users

    def test_update_idea_preserves_existing_fields(self, sample_plan_with_idea):
        """Test that update-idea preserves fields not being updated."""
        # Get original values
        is_valid, _error, original_bundle = validate_plan_bundle(sample_plan_with_idea)
        assert is_valid is True
        assert original_bundle is not None
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
                "--plan",
                str(sample_plan_with_idea),
            ],
        )

        assert result.exit_code == 0

        # Verify only target_users changed, others preserved
        is_valid, _error, bundle = validate_plan_bundle(sample_plan_with_idea)
        assert is_valid is True
        assert bundle is not None
        assert bundle.idea is not None
        assert bundle.idea.title == original_title
        assert bundle.idea.narrative == original_narrative
        assert len(bundle.idea.target_users) == 1
        assert "New User" in bundle.idea.target_users

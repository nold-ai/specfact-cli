"""Unit tests for plan add-feature and add-story commands.

Focus: Business logic and edge cases only (@beartype handles type validation).
"""

import pytest
from typer.testing import CliRunner

from specfact_cli.cli import app
from specfact_cli.generators.plan_generator import PlanGenerator
from specfact_cli.models.plan import Feature, PlanBundle, Product, Story
from specfact_cli.validators.schema import validate_plan_bundle


runner = CliRunner()


@pytest.fixture
def sample_plan(tmp_path):
    """Create a sample plan bundle for testing."""
    plan_path = tmp_path / "plan.yaml"
    bundle = PlanBundle(
        idea=None,
        business=None,
        product=Product(themes=["Testing"]),
        features=[
            Feature(
                key="FEATURE-001",
                title="Existing Feature",
                outcomes=["Test outcome"],
                acceptance=["Test acceptance"],
                stories=[
                    Story(
                        key="STORY-001",
                        title="Existing Story",
                        acceptance=["Story acceptance"],
                        story_points=None,
                        value_points=None,
                        scenarios=None,
                        contracts=None,
                    )
                ],
            )
        ],
        metadata=None,
        clarifications=None,
    )
    generator = PlanGenerator()
    generator.generate(bundle, plan_path)
    return plan_path


class TestPlanAddFeature:
    """Test suite for plan add-feature command."""

    def test_add_feature_to_empty_plan(self, tmp_path):
        """Test adding a feature to an empty plan."""
        # Create empty plan
        plan_path = tmp_path / "plan.yaml"
        bundle = PlanBundle(idea=None, business=None, product=Product(themes=["Testing"]), features=[], metadata=None, clarifications=None)
        generator = PlanGenerator()
        generator.generate(bundle, plan_path)

        # Add feature
        result = runner.invoke(
            app,
            [
                "plan",
                "add-feature",
                "--key",
                "FEATURE-002",
                "--title",
                "New Feature",
                "--plan",
                str(plan_path),
            ],
        )

        assert result.exit_code == 0
        assert "added successfully" in result.stdout.lower()

        # Verify feature was added
        is_valid, _error, bundle = validate_plan_bundle(plan_path)
        assert is_valid is True
        assert bundle is not None  # Type guard
        assert len(bundle.features) == 1
        assert bundle.features[0].key == "FEATURE-002"
        assert bundle.features[0].title == "New Feature"

    def test_add_feature_to_existing_plan(self, sample_plan):
        """Test adding a feature to a plan with existing features."""
        result = runner.invoke(
            app,
            [
                "plan",
                "add-feature",
                "--key",
                "FEATURE-002",
                "--title",
                "Second Feature",
                "--plan",
                str(sample_plan),
            ],
        )

        assert result.exit_code == 0

        # Verify both features exist
        is_valid, _error, bundle = validate_plan_bundle(sample_plan)
        assert is_valid is True
        assert bundle is not None  # Type guard
        assert len(bundle.features) == 2
        assert bundle.features[0].key == "FEATURE-001"
        assert bundle.features[1].key == "FEATURE-002"

    def test_add_feature_with_outcomes(self, sample_plan):
        """Test adding a feature with outcomes."""
        result = runner.invoke(
            app,
            [
                "plan",
                "add-feature",
                "--key",
                "FEATURE-002",
                "--title",
                "Feature with Outcomes",
                "--outcomes",
                "Outcome 1, Outcome 2",
                "--plan",
                str(sample_plan),
            ],
        )

        assert result.exit_code == 0

        # Verify outcomes were parsed correctly
        is_valid, _error, bundle = validate_plan_bundle(sample_plan)
        assert is_valid is True
        assert bundle is not None  # Type guard
        feature = next(f for f in bundle.features if f.key == "FEATURE-002")
        assert len(feature.outcomes) == 2
        assert "Outcome 1" in feature.outcomes
        assert "Outcome 2" in feature.outcomes

    def test_add_feature_with_acceptance(self, sample_plan):
        """Test adding a feature with acceptance criteria."""
        result = runner.invoke(
            app,
            [
                "plan",
                "add-feature",
                "--key",
                "FEATURE-002",
                "--title",
                "Feature with Acceptance",
                "--acceptance",
                "Criterion 1, Criterion 2",
                "--plan",
                str(sample_plan),
            ],
        )

        assert result.exit_code == 0

        # Verify acceptance criteria were parsed correctly
        is_valid, _error, bundle = validate_plan_bundle(sample_plan)
        assert is_valid is True
        assert bundle is not None  # Type guard
        feature = next(f for f in bundle.features if f.key == "FEATURE-002")
        assert len(feature.acceptance) == 2
        assert "Criterion 1" in feature.acceptance
        assert "Criterion 2" in feature.acceptance

    def test_add_feature_duplicate_key(self, sample_plan):
        """Test that adding a duplicate feature key fails."""
        result = runner.invoke(
            app,
            [
                "plan",
                "add-feature",
                "--key",
                "FEATURE-001",  # Already exists
                "--title",
                "Duplicate Feature",
                "--plan",
                str(sample_plan),
            ],
        )

        assert result.exit_code == 1
        assert "already exists" in result.stdout.lower()

    def test_add_feature_missing_plan(self, tmp_path):
        """Test that adding a feature to a non-existent plan fails."""
        plan_path = tmp_path / "nonexistent.yaml"

        result = runner.invoke(
            app,
            [
                "plan",
                "add-feature",
                "--key",
                "FEATURE-001",
                "--title",
                "New Feature",
                "--plan",
                str(plan_path),
            ],
        )

        assert result.exit_code == 1
        assert "not found" in result.stdout.lower()

    def test_add_feature_invalid_plan(self, tmp_path):
        """Test that adding a feature to an invalid plan fails."""
        plan_path = tmp_path / "invalid.yaml"
        plan_path.write_text("invalid: yaml: content")

        result = runner.invoke(
            app,
            [
                "plan",
                "add-feature",
                "--key",
                "FEATURE-001",
                "--title",
                "New Feature",
                "--plan",
                str(plan_path),
            ],
        )

        assert result.exit_code == 1
        assert "validation failed" in result.stdout.lower()

    def test_add_feature_default_path(self, tmp_path, monkeypatch):
        """Test adding a feature using default path."""
        monkeypatch.chdir(tmp_path)

        # Create default plan
        from specfact_cli.utils.structure import SpecFactStructure

        default_path = SpecFactStructure.get_default_plan_path()
        default_path.parent.mkdir(parents=True, exist_ok=True)

        bundle = PlanBundle(idea=None, business=None, product=Product(themes=["Testing"]), features=[], metadata=None, clarifications=None)
        generator = PlanGenerator()
        generator.generate(bundle, default_path)

        # Add feature without specifying plan
        result = runner.invoke(
            app,
            [
                "plan",
                "add-feature",
                "--key",
                "FEATURE-001",
                "--title",
                "Default Path Feature",
            ],
        )

        assert result.exit_code == 0
        assert default_path.exists()

        # Verify feature was added
        is_valid, _error, bundle = validate_plan_bundle(default_path)
        assert is_valid is True
        assert bundle is not None  # Type guard
        assert len(bundle.features) == 1


class TestPlanAddStory:
    """Test suite for plan add-story command."""

    def test_add_story_to_feature(self, sample_plan):
        """Test adding a story to an existing feature."""
        result = runner.invoke(
            app,
            [
                "plan",
                "add-story",
                "--feature",
                "FEATURE-001",
                "--key",
                "STORY-002",
                "--title",
                "New Story",
                "--plan",
                str(sample_plan),
            ],
        )

        assert result.exit_code == 0
        assert "added" in result.stdout.lower()

        # Verify story was added
        is_valid, _error, bundle = validate_plan_bundle(sample_plan)
        assert is_valid is True
        assert bundle is not None  # Type guard
        feature = next(f for f in bundle.features if f.key == "FEATURE-001")
        assert len(feature.stories) == 2
        assert feature.stories[1].key == "STORY-002"
        assert feature.stories[1].title == "New Story"

    def test_add_story_with_acceptance(self, sample_plan):
        """Test adding a story with acceptance criteria."""
        result = runner.invoke(
            app,
            [
                "plan",
                "add-story",
                "--feature",
                "FEATURE-001",
                "--key",
                "STORY-002",
                "--title",
                "Story with Acceptance",
                "--acceptance",
                "Criterion 1, Criterion 2",
                "--plan",
                str(sample_plan),
            ],
        )

        assert result.exit_code == 0

        # Verify acceptance criteria were parsed correctly
        is_valid, _error, bundle = validate_plan_bundle(sample_plan)
        assert is_valid is True
        assert bundle is not None  # Type guard
        feature = next(f for f in bundle.features if f.key == "FEATURE-001")
        story = next(s for s in feature.stories if s.key == "STORY-002")
        assert len(story.acceptance) == 2
        assert "Criterion 1" in story.acceptance
        assert "Criterion 2" in story.acceptance

    def test_add_story_with_story_points(self, sample_plan):
        """Test adding a story with story points."""
        result = runner.invoke(
            app,
            [
                "plan",
                "add-story",
                "--feature",
                "FEATURE-001",
                "--key",
                "STORY-002",
                "--title",
                "Story with Points",
                "--story-points",
                "5",
                "--plan",
                str(sample_plan),
            ],
        )

        assert result.exit_code == 0

        # Verify story points were set
        is_valid, _error, bundle = validate_plan_bundle(sample_plan)
        assert is_valid is True
        assert bundle is not None  # Type guard
        feature = next(f for f in bundle.features if f.key == "FEATURE-001")
        story = next(s for s in feature.stories if s.key == "STORY-002")
        assert story.story_points == 5

    def test_add_story_with_value_points(self, sample_plan):
        """Test adding a story with value points."""
        result = runner.invoke(
            app,
            [
                "plan",
                "add-story",
                "--feature",
                "FEATURE-001",
                "--key",
                "STORY-002",
                "--title",
                "Story with Value",
                "--value-points",
                "8",
                "--plan",
                str(sample_plan),
            ],
        )

        assert result.exit_code == 0

        # Verify value points were set
        is_valid, _error, bundle = validate_plan_bundle(sample_plan)
        assert is_valid is True
        assert bundle is not None  # Type guard
        feature = next(f for f in bundle.features if f.key == "FEATURE-001")
        story = next(s for s in feature.stories if s.key == "STORY-002")
        assert story.value_points == 8

    def test_add_story_as_draft(self, sample_plan):
        """Test adding a story marked as draft."""
        result = runner.invoke(
            app,
            [
                "plan",
                "add-story",
                "--feature",
                "FEATURE-001",
                "--key",
                "STORY-002",
                "--title",
                "Draft Story",
                "--draft",
                "--plan",
                str(sample_plan),
            ],
        )

        assert result.exit_code == 0

        # Verify draft flag was set
        is_valid, _error, bundle = validate_plan_bundle(sample_plan)
        assert is_valid is True
        assert bundle is not None  # Type guard
        feature = next(f for f in bundle.features if f.key == "FEATURE-001")
        story = next(s for s in feature.stories if s.key == "STORY-002")
        assert story.draft is True

    def test_add_story_duplicate_key(self, sample_plan):
        """Test that adding a duplicate story key fails."""
        result = runner.invoke(
            app,
            [
                "plan",
                "add-story",
                "--feature",
                "FEATURE-001",
                "--key",
                "STORY-001",  # Already exists
                "--title",
                "Duplicate Story",
                "--plan",
                str(sample_plan),
            ],
        )

        assert result.exit_code == 1
        assert "already exists" in result.stdout.lower()

    def test_add_story_feature_not_found(self, sample_plan):
        """Test that adding a story to a non-existent feature fails."""
        result = runner.invoke(
            app,
            [
                "plan",
                "add-story",
                "--feature",
                "FEATURE-999",  # Doesn't exist
                "--key",
                "STORY-002",
                "--title",
                "New Story",
                "--plan",
                str(sample_plan),
            ],
        )

        assert result.exit_code == 1
        assert "not found" in result.stdout.lower()

    def test_add_story_missing_plan(self, tmp_path):
        """Test that adding a story to a non-existent plan fails."""
        plan_path = tmp_path / "nonexistent.yaml"

        result = runner.invoke(
            app,
            [
                "plan",
                "add-story",
                "--feature",
                "FEATURE-001",
                "--key",
                "STORY-001",
                "--title",
                "New Story",
                "--plan",
                str(plan_path),
            ],
        )

        assert result.exit_code == 1
        assert "not found" in result.stdout.lower()

    def test_add_story_default_path(self, tmp_path, monkeypatch):
        """Test adding a story using default path."""
        monkeypatch.chdir(tmp_path)

        # Create default plan with feature
        from specfact_cli.utils.structure import SpecFactStructure

        default_path = SpecFactStructure.get_default_plan_path()
        default_path.parent.mkdir(parents=True, exist_ok=True)

        bundle = PlanBundle(
            idea=None,
            business=None,
            product=Product(themes=["Testing"]),
            features=[
                Feature(
                    key="FEATURE-001",
                    title="Test Feature",
                    outcomes=[],
                    acceptance=[],
                    stories=[],
                )
            ],
            metadata=None,
            clarifications=None,
        )
        generator = PlanGenerator()
        generator.generate(bundle, default_path)

        # Add story without specifying plan
        result = runner.invoke(
            app,
            [
                "plan",
                "add-story",
                "--feature",
                "FEATURE-001",
                "--key",
                "STORY-001",
                "--title",
                "Default Path Story",
            ],
        )

        assert result.exit_code == 0
        assert default_path.exists()

        # Verify story was added
        is_valid, _error, bundle = validate_plan_bundle(default_path)
        assert is_valid is True
        assert bundle is not None  # Type guard
        feature = bundle.features[0]
        assert len(feature.stories) == 1
        assert feature.stories[0].key == "STORY-001"

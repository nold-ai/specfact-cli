"""Unit tests for plan add-feature and add-story commands.

Focus: Business logic and edge cases only (@beartype handles type validation).
"""

import pytest
from typer.testing import CliRunner

from specfact_cli.cli import app
from specfact_cli.commands.plan import _convert_plan_bundle_to_project_bundle
from specfact_cli.models.plan import Feature, PlanBundle, Product, Story
from specfact_cli.utils.bundle_loader import load_project_bundle, save_project_bundle


runner = CliRunner()


@pytest.fixture
def sample_bundle(tmp_path, monkeypatch):
    """Create a sample modular bundle for testing."""
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
                source_tracking=None,
                contract=None,
                protocol=None,
            )
        ],
        metadata=None,
        clarifications=None,
    )

    project_bundle = _convert_plan_bundle_to_project_bundle(plan_bundle, bundle_name)
    save_project_bundle(project_bundle, bundle_dir, atomic=True)

    return bundle_name


class TestPlanAddFeature:
    """Test suite for plan add-feature command."""

    def test_add_feature_to_empty_plan(self, tmp_path, monkeypatch):
        """Test adding a feature to an empty plan."""
        monkeypatch.chdir(tmp_path)

        # Create empty modular bundle
        projects_dir = tmp_path / ".specfact" / "projects"
        projects_dir.mkdir(parents=True)
        bundle_name = "test-bundle"
        bundle_dir = projects_dir / bundle_name
        bundle_dir.mkdir()

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
                "--bundle",
                bundle_name,
            ],
        )

        assert result.exit_code == 0
        assert "added successfully" in result.stdout.lower()

        # Verify feature was added
        updated_bundle = load_project_bundle(bundle_dir, validate_hashes=False)
        assert len(updated_bundle.features) == 1
        assert "FEATURE-002" in updated_bundle.features
        assert updated_bundle.features["FEATURE-002"].title == "New Feature"

    def test_add_feature_to_existing_plan(self, sample_bundle, tmp_path, monkeypatch):
        """Test adding a feature to a plan with existing features."""
        monkeypatch.chdir(tmp_path)
        bundle_dir = tmp_path / ".specfact" / "projects" / sample_bundle

        result = runner.invoke(
            app,
            [
                "plan",
                "add-feature",
                "--key",
                "FEATURE-002",
                "--title",
                "Second Feature",
                "--bundle",
                sample_bundle,
            ],
        )

        assert result.exit_code == 0

        # Verify both features exist
        updated_bundle = load_project_bundle(bundle_dir, validate_hashes=False)
        assert len(updated_bundle.features) == 2
        assert "FEATURE-001" in updated_bundle.features
        assert "FEATURE-002" in updated_bundle.features

    def test_add_feature_with_outcomes(self, sample_bundle, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        bundle_dir = tmp_path / ".specfact" / "projects" / sample_bundle
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
                "--bundle",
                sample_bundle,
            ],
        )

        assert result.exit_code == 0

        # Verify outcomes were parsed correctly
        updated_bundle = load_project_bundle(bundle_dir, validate_hashes=False)
        assert "FEATURE-002" in updated_bundle.features
        feature = updated_bundle.features["FEATURE-002"]
        assert len(feature.outcomes) == 2
        assert "Outcome 1" in feature.outcomes
        assert "Outcome 2" in feature.outcomes

    def test_add_feature_with_acceptance(self, sample_bundle, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        bundle_dir = tmp_path / ".specfact" / "projects" / sample_bundle
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
                "--bundle",
                sample_bundle,
            ],
        )

        assert result.exit_code == 0

        # Verify acceptance criteria were parsed correctly
        updated_bundle = load_project_bundle(bundle_dir, validate_hashes=False)
        assert "FEATURE-002" in updated_bundle.features
        feature = updated_bundle.features["FEATURE-002"]
        assert len(feature.acceptance) == 2
        assert "Criterion 1" in feature.acceptance
        assert "Criterion 2" in feature.acceptance

    def test_add_feature_duplicate_key(self, sample_bundle, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
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
                "--bundle",
                sample_bundle,
            ],
        )

        assert result.exit_code == 1
        assert "already exists" in result.stdout.lower()

    def test_add_feature_missing_plan(self, tmp_path, monkeypatch):
        """Test that adding a feature to a non-existent bundle fails."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(
            app,
            [
                "plan",
                "add-feature",
                "--key",
                "FEATURE-001",
                "--title",
                "New Feature",
                "--bundle",
                "nonexistent-bundle",
            ],
        )

        assert result.exit_code == 1
        assert "not found" in result.stdout.lower()

    def test_add_feature_invalid_plan(self, tmp_path, monkeypatch):
        """Test that adding a feature to an invalid bundle fails."""
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
                "add-feature",
                "--key",
                "FEATURE-001",
                "--title",
                "New Feature",
                "--bundle",
                "invalid-bundle",
            ],
        )

        assert result.exit_code == 1
        assert (
            "not found" in result.stdout.lower()
            or "validation failed" in result.stdout.lower()
            or "error" in result.stdout.lower()
            or "failed to load" in result.stdout.lower()
        )

    def test_add_feature_default_path(self, tmp_path, monkeypatch):
        """Test adding a feature using default bundle."""
        monkeypatch.chdir(tmp_path)

        # Create default bundle
        projects_dir = tmp_path / ".specfact" / "projects"
        projects_dir.mkdir(parents=True)
        bundle_name = "main"  # Default bundle name
        bundle_dir = projects_dir / bundle_name
        bundle_dir.mkdir()

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

        # Set active plan so command can use it as default
        from specfact_cli.utils.structure import SpecFactStructure

        # Ensure plans directory exists
        plans_dir = tmp_path / ".specfact" / "plans"
        plans_dir.mkdir(parents=True, exist_ok=True)
        SpecFactStructure.set_active_plan(bundle_name, base_path=tmp_path)

        # Add feature without specifying bundle (should use active plan)
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
        assert bundle_dir.exists()

        # Verify feature was added
        updated_bundle = load_project_bundle(bundle_dir, validate_hashes=False)
        assert len(updated_bundle.features) == 1
        assert "FEATURE-001" in updated_bundle.features


class TestPlanAddStory:
    """Test suite for plan add-story command."""

    def test_add_story_to_feature(self, sample_bundle, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        bundle_dir = tmp_path / ".specfact" / "projects" / sample_bundle
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
                "--bundle",
                sample_bundle,
            ],
        )

        assert result.exit_code == 0
        assert "added" in result.stdout.lower()

        # Verify story was added
        updated_bundle = load_project_bundle(bundle_dir, validate_hashes=False)
        assert "FEATURE-001" in updated_bundle.features
        feature = updated_bundle.features["FEATURE-001"]
        assert len(feature.stories) == 2
        story_keys = [s.key for s in feature.stories]
        assert "STORY-002" in story_keys
        story = next(s for s in feature.stories if s.key == "STORY-002")
        assert story.title == "New Story"

    def test_add_story_with_acceptance(self, sample_bundle, tmp_path, monkeypatch):
        """Test adding a story with acceptance criteria."""
        monkeypatch.chdir(tmp_path)
        bundle_dir = tmp_path / ".specfact" / "projects" / sample_bundle

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
                "--bundle",
                sample_bundle,
            ],
        )

        assert result.exit_code == 0

        # Verify acceptance criteria were parsed correctly
        updated_bundle = load_project_bundle(bundle_dir, validate_hashes=False)
        assert "FEATURE-001" in updated_bundle.features
        feature = updated_bundle.features["FEATURE-001"]
        story = next(s for s in feature.stories if s.key == "STORY-002")
        assert len(story.acceptance) == 2
        assert "Criterion 1" in story.acceptance
        assert "Criterion 2" in story.acceptance

    def test_add_story_with_story_points(self, sample_bundle, tmp_path, monkeypatch):
        """Test adding a story with story points."""
        monkeypatch.chdir(tmp_path)
        bundle_dir = tmp_path / ".specfact" / "projects" / sample_bundle

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
                "--bundle",
                sample_bundle,
            ],
        )

        assert result.exit_code == 0

        # Verify story points were set
        updated_bundle = load_project_bundle(bundle_dir, validate_hashes=False)
        assert "FEATURE-001" in updated_bundle.features
        feature = updated_bundle.features["FEATURE-001"]
        story = next(s for s in feature.stories if s.key == "STORY-002")
        assert story.story_points == 5

    def test_add_story_with_value_points(self, sample_bundle, tmp_path, monkeypatch):
        """Test adding a story with value points."""
        monkeypatch.chdir(tmp_path)
        bundle_dir = tmp_path / ".specfact" / "projects" / sample_bundle

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
                "--bundle",
                sample_bundle,
            ],
        )

        assert result.exit_code == 0

        # Verify value points were set
        updated_bundle = load_project_bundle(bundle_dir, validate_hashes=False)
        assert "FEATURE-001" in updated_bundle.features
        feature = updated_bundle.features["FEATURE-001"]
        story = next(s for s in feature.stories if s.key == "STORY-002")
        assert story.value_points == 8

    def test_add_story_as_draft(self, sample_bundle, tmp_path, monkeypatch):
        """Test adding a story marked as draft."""
        monkeypatch.chdir(tmp_path)
        bundle_dir = tmp_path / ".specfact" / "projects" / sample_bundle

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
                "--bundle",
                sample_bundle,
            ],
        )

        assert result.exit_code == 0

        # Verify draft flag was set
        updated_bundle = load_project_bundle(bundle_dir, validate_hashes=False)
        assert "FEATURE-001" in updated_bundle.features
        feature = updated_bundle.features["FEATURE-001"]
        story = next(s for s in feature.stories if s.key == "STORY-002")
        assert story.draft is True

    def test_add_story_duplicate_key(self, sample_bundle, tmp_path, monkeypatch):
        """Test that adding a duplicate story key fails."""
        monkeypatch.chdir(tmp_path)

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
                "--bundle",
                sample_bundle,
            ],
        )

        assert result.exit_code == 1
        assert "already exists" in result.stdout.lower()

    def test_add_story_feature_not_found(self, sample_bundle, tmp_path, monkeypatch):
        """Test that adding a story to a non-existent feature fails."""
        monkeypatch.chdir(tmp_path)

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
                "--bundle",
                sample_bundle,
            ],
        )

        assert result.exit_code == 1
        assert "not found" in result.stdout.lower()

    def test_add_story_missing_plan(self, tmp_path, monkeypatch):
        """Test that adding a story to a non-existent bundle fails."""
        monkeypatch.chdir(tmp_path)

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
                "--bundle",
                "nonexistent-bundle",
            ],
        )

        assert result.exit_code == 1
        assert "not found" in result.stdout.lower()

    def test_add_story_default_path(self, tmp_path, monkeypatch):
        """Test adding a story using default bundle."""
        monkeypatch.chdir(tmp_path)

        # Create default bundle with feature
        projects_dir = tmp_path / ".specfact" / "projects"
        projects_dir.mkdir(parents=True)
        bundle_name = "main"  # Default bundle name
        bundle_dir = projects_dir / bundle_name
        bundle_dir.mkdir()

        plan_bundle = PlanBundle(
            version="1.0",
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
                    source_tracking=None,
                    contract=None,
                    protocol=None,
                )
            ],
            metadata=None,
            clarifications=None,
        )
        project_bundle = _convert_plan_bundle_to_project_bundle(plan_bundle, bundle_name)
        save_project_bundle(project_bundle, bundle_dir, atomic=True)

        # Set active plan so command can use it as default
        from specfact_cli.utils.structure import SpecFactStructure

        # Ensure plans directory exists
        plans_dir = tmp_path / ".specfact" / "plans"
        plans_dir.mkdir(parents=True, exist_ok=True)
        SpecFactStructure.set_active_plan(bundle_name, base_path=tmp_path)

        # Add story without specifying bundle (should use active plan)
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
        assert bundle_dir.exists()

        # Verify story was added
        updated_bundle = load_project_bundle(bundle_dir, validate_hashes=False)
        assert "FEATURE-001" in updated_bundle.features
        feature = updated_bundle.features["FEATURE-001"]
        assert len(feature.stories) == 1
        assert feature.stories[0].key == "STORY-001"

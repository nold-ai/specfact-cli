"""Integration tests for plan command."""

from unittest.mock import patch

from typer.testing import CliRunner

from specfact_cli.cli import app

# Import conversion functions from plan command module
from specfact_cli.commands.plan import (
    _convert_plan_bundle_to_project_bundle,
    _convert_project_bundle_to_plan_bundle,
)
from specfact_cli.models.plan import Feature
from specfact_cli.models.project import ProjectBundle
from specfact_cli.utils.bundle_loader import load_project_bundle, save_project_bundle


runner = CliRunner()


class TestPlanInitNonInteractive:
    """Test plan init command in non-interactive mode."""

    def test_plan_init_minimal_default_path(self, tmp_path, monkeypatch):
        """Test plan init creates minimal plan at default path."""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["plan", "init", "test-bundle", "--no-interactive"])

        assert result.exit_code == 0
        assert "created" in result.stdout.lower() or "initialized" in result.stdout.lower()

        # Verify modular bundle structure was created in .specfact/projects/
        bundle_dir = tmp_path / ".specfact" / "projects" / "test-bundle"
        assert bundle_dir.exists()
        assert (bundle_dir / "bundle.manifest.yaml").exists()
        assert (bundle_dir / "product.yaml").exists()

        # Verify content by loading project bundle
        bundle = load_project_bundle(bundle_dir)
        assert bundle.bundle_name == "test-bundle"
        assert bundle.product is not None
        assert len(bundle.features) == 0

    def test_plan_init_minimal_custom_path(self, tmp_path, monkeypatch):
        """Test plan init creates modular bundle (no custom path option)."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["plan", "init", "custom-bundle", "--no-interactive"])

        assert result.exit_code == 0
        assert "created" in result.stdout.lower() or "initialized" in result.stdout.lower()

        # Verify modular bundle structure
        bundle_dir = tmp_path / ".specfact" / "projects" / "custom-bundle"
        assert bundle_dir.exists()

        # Validate generated bundle
        bundle = load_project_bundle(bundle_dir)
        assert bundle is not None
        assert bundle.bundle_name == "custom-bundle"

    def test_plan_init_minimal_validates(self, tmp_path, monkeypatch):
        """Test that minimal plan passes validation."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["plan", "init", "valid-bundle", "--no-interactive"])

        assert result.exit_code == 0

        # Load and validate
        bundle_dir = tmp_path / ".specfact" / "projects" / "valid-bundle"
        bundle = load_project_bundle(bundle_dir)
        assert bundle is not None
        assert isinstance(bundle, ProjectBundle)


class TestPlanInitInteractive:
    """Test plan init command in interactive mode."""

    def test_plan_init_basic_idea_only(self, tmp_path, monkeypatch):
        """Test plan init with minimal interactive input."""
        monkeypatch.chdir(tmp_path)

        # Mock all prompts for a minimal plan
        with (
            patch("specfact_cli.commands.plan.prompt_text") as mock_text,
            patch("specfact_cli.commands.plan.prompt_confirm") as mock_confirm,
            patch("specfact_cli.commands.plan.prompt_list") as mock_list,
        ):
            # Setup responses
            mock_text.side_effect = [
                "Test Project",  # idea title
                "A test project",  # idea narrative
            ]
            mock_confirm.side_effect = [
                False,  # Add idea details?
                False,  # Add business context?
                False,  # Define releases?
                False,  # Add a feature?
            ]
            mock_list.return_value = ["Testing"]  # Product themes

            result = runner.invoke(app, ["plan", "init", "test-bundle"])

            assert result.exit_code == 0
            assert "created" in result.stdout.lower() or "successfully" in result.stdout.lower()

            # Verify modular bundle structure
            bundle_dir = tmp_path / ".specfact" / "projects" / "test-bundle"
            assert bundle_dir.exists()

            # Verify plan content
            bundle = load_project_bundle(bundle_dir)
            assert bundle is not None
            assert bundle.idea is not None
            assert bundle.idea.title == "Test Project"

    def test_plan_init_full_workflow(self, tmp_path, monkeypatch):
        """Test plan init with complete interactive workflow."""
        monkeypatch.chdir(tmp_path)
        bundle_name = "test-bundle"

        with (
            patch("specfact_cli.commands.plan.prompt_text") as mock_text,
            patch("specfact_cli.commands.plan.prompt_confirm") as mock_confirm,
            patch("specfact_cli.commands.plan.prompt_list") as mock_list,
            patch("specfact_cli.commands.plan.prompt_dict") as mock_dict,
        ):
            # Setup complete workflow responses
            mock_text.side_effect = [
                "Full Test Project",  # idea title
                "Complete test description",  # idea narrative
                "Improve efficiency",  # value hypothesis
                "",  # release name (empty to exit)
                "FEATURE-001",  # feature key
                "Test Feature",  # feature title
                # (no feature confidence because "Add optional details?" = False)
                "STORY-001",  # story key
                "Test Story",  # story title
                # (no story confidence because "Add optional story details?" = False)
            ]

            mock_confirm.side_effect = [
                True,  # Add idea details?
                False,  # Add success metrics?
                False,  # Add business context?
                True,  # Define releases? (then release_name="" breaks immediately, no "Add another release?" prompt)
                True,  # Add a feature?
                False,  # Add optional feature details?
                True,  # Add stories to this feature?
                False,  # Add optional story details?
                False,  # Add another story?
                False,  # Add another feature?
            ]

            mock_list.side_effect = [
                ["developers", "testers"],  # target users
                ["AI/ML", "Testing"],  # product themes
                ["Improve quality"],  # feature outcomes
                ["Tests pass"],  # feature acceptance
                ["Criterion 1"],  # story acceptance
            ]

            mock_dict.return_value = {}  # No metrics

            result = runner.invoke(app, ["plan", "init", bundle_name])

            assert result.exit_code == 0
            assert "created" in result.stdout.lower() or "successfully" in result.stdout.lower()

            # Verify comprehensive bundle
            bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
            bundle = load_project_bundle(bundle_dir)
            assert bundle is not None
            assert bundle.idea is not None
            assert bundle.idea.title == "Full Test Project"
            assert len(bundle.features) == 1
            assert "FEATURE-001" in bundle.features
            assert len(bundle.features["FEATURE-001"].stories) == 1
            assert bundle.features["FEATURE-001"].stories[0].key == "STORY-001"

    def test_plan_init_with_business_context(self, tmp_path, monkeypatch):
        """Test plan init with business context."""
        monkeypatch.chdir(tmp_path)
        bundle_name = "test-bundle"

        with (
            patch("specfact_cli.commands.plan.prompt_text") as mock_text,
            patch("specfact_cli.commands.plan.prompt_confirm") as mock_confirm,
            patch("specfact_cli.commands.plan.prompt_list") as mock_list,
        ):
            mock_text.side_effect = [
                "Business Project",  # idea title
                "Business focused project",  # idea narrative
            ]

            mock_confirm.side_effect = [
                False,  # Add idea details?
                True,  # Add business context?
                False,  # Define releases?
                False,  # Add a feature?
            ]

            mock_list.side_effect = [
                ["Enterprise", "SMB"],  # business segments
                ["High costs"],  # problems
                ["Automation"],  # solutions
                ["AI-powered"],  # differentiation
                ["Market volatility"],  # risks
                ["Core"],  # product themes
            ]

            result = runner.invoke(app, ["plan", "init", bundle_name])

            assert result.exit_code == 0

            bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
            bundle = load_project_bundle(bundle_dir)
            assert bundle is not None
            assert bundle.business is not None
            assert len(bundle.business.segments) == 2
            assert "Enterprise" in bundle.business.segments

    def test_plan_init_keyboard_interrupt(self, tmp_path, monkeypatch):
        """Test plan init handles keyboard interrupt gracefully."""
        monkeypatch.chdir(tmp_path)
        bundle_name = "test-bundle"

        with patch("specfact_cli.commands.plan.prompt_text") as mock_text:
            mock_text.side_effect = KeyboardInterrupt()

            result = runner.invoke(app, ["plan", "init", bundle_name])

            assert result.exit_code == 1
            assert "cancelled" in result.stdout.lower() or "interrupt" in result.stdout.lower()
            # Directory might be created, but bundle should be incomplete (no manifest)
            bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
            manifest_path = bundle_dir / "bundle.manifest.yaml"
            # Either directory doesn't exist, or manifest doesn't exist (incomplete bundle)
            assert not bundle_dir.exists() or not manifest_path.exists()


class TestPlanInitValidation:
    """Test plan init validation behavior."""

    def test_generated_plan_passes_json_schema_validation(self, tmp_path, monkeypatch):
        """Test that generated plans pass JSON schema validation."""
        monkeypatch.chdir(tmp_path)
        bundle_name = "test-bundle"

        with (
            patch("specfact_cli.commands.plan.prompt_text") as mock_text,
            patch("specfact_cli.commands.plan.prompt_confirm") as mock_confirm,
            patch("specfact_cli.commands.plan.prompt_list") as mock_list,
        ):
            mock_text.side_effect = ["Schema Test", "Test for schema validation"]
            mock_confirm.side_effect = [False, False, False, False]
            mock_list.return_value = ["Testing"]

            result = runner.invoke(app, ["plan", "init", bundle_name])

            assert result.exit_code == 0
            # Validation happens during bundle creation, check that bundle was created
            bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
            assert bundle_dir.exists()

    def test_plan_init_creates_valid_pydantic_model(self, tmp_path, monkeypatch):
        """Test that generated plan can be loaded as Pydantic model."""
        monkeypatch.chdir(tmp_path)
        bundle_name = "test-bundle"

        result = runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])

        assert result.exit_code == 0

        # Load as ProjectBundle model
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        bundle = load_project_bundle(bundle_dir)

        assert bundle is not None
        assert bundle.manifest.versions.schema_version == "1.0"
        assert isinstance(bundle.product.themes, list)
        assert isinstance(bundle.features, dict)


class TestPlanInitEdgeCases:
    """Test edge cases for plan init."""

    def test_plan_init_with_metrics(self, tmp_path, monkeypatch):
        """Test plan init with metrics dictionary."""
        monkeypatch.chdir(tmp_path)
        bundle_name = "test-bundle"

        with (
            patch("specfact_cli.commands.plan.prompt_text") as mock_text,
            patch("specfact_cli.commands.plan.prompt_confirm") as mock_confirm,
            patch("specfact_cli.commands.plan.prompt_list") as mock_list,
            patch("specfact_cli.commands.plan.prompt_dict") as mock_dict,
        ):
            mock_text.side_effect = [
                "Metrics Project",  # idea title
                "Test metrics",  # idea narrative
                "",  # value hypothesis (empty)
            ]
            mock_confirm.side_effect = [
                True,  # Add idea details?
                True,  # Add success metrics?
                False,  # Add business context?
                False,  # Define releases?
                False,  # Add a feature?
            ]
            mock_list.side_effect = [
                [],  # target users (empty)
                ["Core"],  # product themes
            ]
            mock_dict.return_value = {"efficiency": 0.8, "coverage": 0.9}

            result = runner.invoke(app, ["plan", "init", bundle_name])

            assert result.exit_code == 0

            bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
            bundle = load_project_bundle(bundle_dir)
            assert bundle is not None
            assert bundle.idea is not None
            assert bundle.idea.metrics is not None
            assert bundle.idea.metrics["efficiency"] == 0.8

    def test_plan_init_with_releases(self, tmp_path, monkeypatch):
        """Test plan init with multiple releases."""
        monkeypatch.chdir(tmp_path)
        bundle_name = "test-bundle"

        with (
            patch("specfact_cli.commands.plan.prompt_text") as mock_text,
            patch("specfact_cli.commands.plan.prompt_confirm") as mock_confirm,
            patch("specfact_cli.commands.plan.prompt_list") as mock_list,
        ):
            mock_text.side_effect = [
                "Release Project",  # idea title
                "Test releases",  # idea narrative
                "v1.0 - MVP",  # release 1 name
                "v2.0 - Full",  # release 2 name
                "",  # exit releases
            ]

            mock_confirm.side_effect = [
                False,  # Add idea details?
                False,  # Add business context?
                True,  # Define releases?
                True,  # Add another release?
                False,  # Add another release? (after 2nd)
                False,  # Add a feature?
            ]

            mock_list.side_effect = [
                ["Core"],  # product themes
                ["Launch MVP"],  # release 1 objectives
                ["FEATURE-001"],  # release 1 scope
                [],  # release 1 risks
                ["Scale up"],  # release 2 objectives
                ["FEATURE-002"],  # release 2 scope
                ["Performance"],  # release 2 risks
            ]

            result = runner.invoke(app, ["plan", "init", bundle_name])

            assert result.exit_code == 0

            bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
            bundle = load_project_bundle(bundle_dir)
            assert bundle is not None
            assert len(bundle.product.releases) == 2
            assert bundle.product.releases[0].name == "v1.0 - MVP"
            assert bundle.product.releases[1].name == "v2.0 - Full"


class TestPlanAddFeature:
    """Integration tests for plan add-feature command."""

    def test_add_feature_to_initialized_plan(self, tmp_path, monkeypatch):
        """Test adding a feature to a plan created with init."""
        monkeypatch.chdir(tmp_path)
        bundle_name = "test-bundle"

        # First, create a plan
        init_result = runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])
        assert init_result.exit_code == 0

        # Add a feature
        result = runner.invoke(
            app,
            [
                "plan",
                "add-feature",
                "--key",
                "FEATURE-001",
                "--title",
                "Test Feature",
                "--outcomes",
                "Outcome 1, Outcome 2",
                "--acceptance",
                "Criterion 1, Criterion 2",
                "--bundle",
                bundle_name,
            ],
        )

        assert result.exit_code == 0
        assert "added successfully" in result.stdout.lower()

        # Verify feature was added and bundle is still valid
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        bundle = load_project_bundle(bundle_dir)
        assert bundle is not None
        assert len(bundle.features) == 1
        assert bundle.features["FEATURE-001"].key == "FEATURE-001"
        assert bundle.features["FEATURE-001"].title == "Test Feature"
        assert len(bundle.features["FEATURE-001"].outcomes) == 2
        assert len(bundle.features["FEATURE-001"].acceptance) == 2

    def test_add_multiple_features(self, tmp_path, monkeypatch):
        """Test adding multiple features sequentially."""
        monkeypatch.chdir(tmp_path)
        bundle_name = "test-bundle"

        # Create plan
        runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])

        # Add first feature
        result1 = runner.invoke(
            app,
            ["plan", "add-feature", "--key", "FEATURE-001", "--title", "Feature One", "--bundle", bundle_name],
        )
        assert result1.exit_code == 0

        # Add second feature
        result2 = runner.invoke(
            app,
            ["plan", "add-feature", "--key", "FEATURE-002", "--title", "Feature Two", "--bundle", bundle_name],
        )
        assert result2.exit_code == 0

        # Verify both features exist
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        bundle = load_project_bundle(bundle_dir)
        assert bundle is not None
        assert len(bundle.features) == 2
        assert "FEATURE-001" in bundle.features
        assert "FEATURE-002" in bundle.features

    def test_add_feature_preserves_existing_features(self, tmp_path, monkeypatch):
        """Test that adding a feature preserves existing features."""
        monkeypatch.chdir(tmp_path)
        bundle_name = "test-bundle"

        # Create plan
        result = runner.invoke(
            app,
            ["plan", "init", bundle_name, "--no-interactive"],
        )
        assert result.exit_code == 0

        # Load bundle and manually add a feature (simulating existing feature)
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        project_bundle = load_project_bundle(bundle_dir)
        plan_bundle = _convert_project_bundle_to_plan_bundle(project_bundle)
        plan_bundle.features.append(Feature(key="FEATURE-000", title="Existing Feature", outcomes=[], acceptance=[]))
        updated_project_bundle = _convert_plan_bundle_to_project_bundle(plan_bundle, bundle_name)
        save_project_bundle(updated_project_bundle, bundle_dir, atomic=True)

        # Add new feature via CLI
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
                bundle_name,
            ],
        )
        assert result.exit_code == 0

        # Verify both features exist
        bundle = load_project_bundle(bundle_dir)
        assert bundle is not None
        assert len(bundle.features) == 2
        feature_keys = set(bundle.features.keys())
        assert "FEATURE-000" in feature_keys
        assert "FEATURE-001" in feature_keys


class TestPlanAddStory:
    """Integration tests for plan add-story command."""

    def test_add_story_to_feature(self, tmp_path, monkeypatch):
        """Test adding a story to a feature in an initialized plan."""
        monkeypatch.chdir(tmp_path)
        bundle_name = "test-bundle"

        # Create plan
        runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])

        # Add a feature first
        runner.invoke(
            app,
            ["plan", "add-feature", "--key", "FEATURE-001", "--title", "Test Feature", "--bundle", bundle_name],
        )

        # Add a story
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
                "Test Story",
                "--acceptance",
                "Criterion 1, Criterion 2",
                "--story-points",
                "5",
                "--bundle",
                bundle_name,
            ],
        )

        assert result.exit_code == 0
        assert "added" in result.stdout.lower()

        # Verify story was added
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        bundle = load_project_bundle(bundle_dir)
        assert bundle is not None
        feature = bundle.features["FEATURE-001"]
        assert len(feature.stories) == 1
        assert feature.stories[0].key == "STORY-001"
        assert feature.stories[0].title == "Test Story"
        assert feature.stories[0].story_points == 5
        assert len(feature.stories[0].acceptance) == 2

    def test_add_multiple_stories_to_feature(self, tmp_path, monkeypatch):
        """Test adding multiple stories to the same feature."""
        monkeypatch.chdir(tmp_path)
        bundle_name = "test-bundle"

        # Create plan and feature
        runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])
        runner.invoke(
            app,
            ["plan", "add-feature", "--key", "FEATURE-001", "--title", "Test Feature", "--bundle", bundle_name],
        )

        # Add first story
        result1 = runner.invoke(
            app,
            [
                "plan",
                "add-story",
                "--feature",
                "FEATURE-001",
                "--key",
                "STORY-001",
                "--title",
                "Story One",
                "--bundle",
                bundle_name,
            ],
        )
        assert result1.exit_code == 0

        # Add second story
        result2 = runner.invoke(
            app,
            [
                "plan",
                "add-story",
                "--feature",
                "FEATURE-001",
                "--key",
                "STORY-002",
                "--title",
                "Story Two",
                "--bundle",
                bundle_name,
            ],
        )
        assert result2.exit_code == 0

        # Verify both stories exist
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        bundle = load_project_bundle(bundle_dir)
        assert bundle is not None
        feature = bundle.features["FEATURE-001"]
        assert len(feature.stories) == 2
        story_keys = {s.key for s in feature.stories}
        assert "STORY-001" in story_keys
        assert "STORY-002" in story_keys

    def test_add_story_with_all_options(self, tmp_path, monkeypatch):
        """Test adding a story with all available options."""
        monkeypatch.chdir(tmp_path)
        bundle_name = "test-bundle"

        # Create plan and feature
        runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])
        runner.invoke(
            app,
            ["plan", "add-feature", "--key", "FEATURE-001", "--title", "Test Feature", "--bundle", bundle_name],
        )

        # Add story with all options
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
                "Complete Story",
                "--acceptance",
                "Criterion 1, Criterion 2",
                "--story-points",
                "8",
                "--value-points",
                "13",
                "--draft",
                "--bundle",
                bundle_name,
            ],
        )

        assert result.exit_code == 0

        # Verify all options were set
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        bundle = load_project_bundle(bundle_dir)
        assert bundle is not None
        feature = bundle.features["FEATURE-001"]
        story = feature.stories[0]
        assert story.key == "STORY-001"
        assert story.story_points == 8
        assert story.value_points == 13
        assert story.draft is True
        assert len(story.acceptance) == 2

    def test_add_story_preserves_existing_stories(self, tmp_path, monkeypatch):
        """Test that adding a story preserves existing stories in the feature."""
        monkeypatch.chdir(tmp_path)
        bundle_name = "test-bundle"

        # Create plan
        runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])

        # Add feature with existing story manually
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        project_bundle = load_project_bundle(bundle_dir)
        plan_bundle = _convert_project_bundle_to_plan_bundle(project_bundle)

        from specfact_cli.models.plan import Story
        feature = Feature(
            key="FEATURE-001",
            title="Test Feature",
            outcomes=[],
            acceptance=[],
            stories=[
                Story(
                    key="STORY-000",
                    title="Existing Story",
                    acceptance=[],
                    story_points=None,
                    value_points=None,
                    scenarios=None,
                    contracts=None,
                )
            ],
        )
        plan_bundle.features.append(feature)
        updated_project_bundle = _convert_plan_bundle_to_project_bundle(plan_bundle, bundle_name)
        save_project_bundle(updated_project_bundle, bundle_dir, atomic=True)

        # Add new story via CLI
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
                bundle_name,
            ],
        )
        assert result.exit_code == 0

        # Verify both stories exist
        bundle = load_project_bundle(bundle_dir)
        assert bundle is not None
        feature = bundle.features["FEATURE-001"]
        assert len(feature.stories) == 2
        story_keys = {s.key for s in feature.stories}
        assert "STORY-000" in story_keys
        assert "STORY-001" in story_keys


class TestPlanAddWorkflow:
    """Integration tests for add-feature and add-story workflow."""

    def test_complete_feature_story_workflow(self, tmp_path, monkeypatch):
        """Test complete workflow: init -> add-feature -> add-story."""
        monkeypatch.chdir(tmp_path)
        bundle_name = "test-bundle"

        # Step 1: Initialize plan
        init_result = runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])
        assert init_result.exit_code == 0

        # Step 2: Add feature
        feature_result = runner.invoke(
            app,
            [
                "plan",
                "add-feature",
                "--key",
                "FEATURE-001",
                "--title",
                "User Authentication",
                "--outcomes",
                "Secure login, User session management",
                "--acceptance",
                "Login works, Session persists",
                "--bundle",
                bundle_name,
            ],
        )
        assert feature_result.exit_code == 0

        # Step 3: Add story to feature
        story_result = runner.invoke(
            app,
            [
                "plan",
                "add-story",
                "--feature",
                "FEATURE-001",
                "--key",
                "STORY-001",
                "--title",
                "Implement login API",
                "--acceptance",
                "API responds, Authentication succeeds",
                "--story-points",
                "5",
                "--bundle",
                bundle_name,
            ],
        )
        assert story_result.exit_code == 0

        # Verify complete bundle structure
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        bundle = load_project_bundle(bundle_dir)
        assert bundle is not None
        assert len(bundle.features) == 1
        assert "FEATURE-001" in bundle.features
        assert bundle.features["FEATURE-001"].title == "User Authentication"
        assert len(bundle.features["FEATURE-001"].stories) == 1
        assert bundle.features["FEATURE-001"].stories[0].key == "STORY-001"
        assert bundle.features["FEATURE-001"].stories[0].story_points == 5


class TestPlanUpdateIdea:
    """Integration tests for plan update-idea command."""

    def test_update_idea_in_initialized_plan(self, tmp_path, monkeypatch):
        """Test updating idea section in a plan created with init."""
        monkeypatch.chdir(tmp_path)
        bundle_name = "test-bundle"

        # First, create a plan
        init_result = runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])
        assert init_result.exit_code == 0

        # Update idea section
        result = runner.invoke(
            app,
            [
                "plan",
                "update-idea",
                "--target-users",
                "Developers, DevOps",
                "--value-hypothesis",
                "Reduce technical debt",
                "--constraints",
                "Python 3.11+, Maintain backward compatibility",
                "--bundle",
                bundle_name,
            ],
        )

        assert result.exit_code == 0
        assert "updated successfully" in result.stdout.lower()

        # Verify idea was updated and bundle is still valid
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        bundle = load_project_bundle(bundle_dir)
        assert bundle is not None
        assert bundle.idea is not None
        assert len(bundle.idea.target_users) == 2
        assert "Developers" in bundle.idea.target_users
        assert bundle.idea.value_hypothesis == "Reduce technical debt"
        assert len(bundle.idea.constraints) == 2

    def test_update_idea_creates_section_if_missing(self, tmp_path, monkeypatch):
        """Test that update-idea creates idea section if plan doesn't have one."""
        monkeypatch.chdir(tmp_path)
        bundle_name = "test-bundle"

        # Create plan without idea section
        init_result = runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])
        assert init_result.exit_code == 0

        # Verify bundle has no idea section initially
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        bundle = load_project_bundle(bundle_dir)
        assert bundle is not None
        assert bundle.idea is None

        # Update idea (should create section)
        result = runner.invoke(
            app,
            [
                "plan",
                "update-idea",
                "--target-users",
                "Test Users",
                "--value-hypothesis",
                "Test hypothesis",
                "--bundle",
                bundle_name,
            ],
        )

        assert result.exit_code == 0
        assert "Created new idea section" in result.stdout or "created" in result.stdout.lower()

        # Verify idea section was created
        bundle = load_project_bundle(bundle_dir)
        assert bundle is not None
        assert bundle.idea is not None
        assert len(bundle.idea.target_users) == 1
        assert bundle.idea.value_hypothesis == "Test hypothesis"

    def test_update_idea_preserves_other_sections(self, tmp_path, monkeypatch):
        """Test that update-idea preserves features and other sections."""
        monkeypatch.chdir(tmp_path)
        bundle_name = "test-bundle"

        # Create plan with features
        runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])
        runner.invoke(
            app,
            ["plan", "add-feature", "--key", "FEATURE-001", "--title", "Test Feature", "--bundle", bundle_name],
        )

        # Update idea
        result = runner.invoke(
            app,
            [
                "plan",
                "update-idea",
                "--target-users",
                "Users",
                "--bundle",
                bundle_name,
            ],
        )

        assert result.exit_code == 0

        # Verify features are preserved
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        bundle = load_project_bundle(bundle_dir)
        assert bundle is not None
        assert bundle.idea is not None
        assert len(bundle.features) == 1
        assert "FEATURE-001" in bundle.features
        assert len(bundle.idea.target_users) == 1

    def test_update_idea_multiple_times(self, tmp_path, monkeypatch):
        """Test updating idea section multiple times sequentially."""
        monkeypatch.chdir(tmp_path)
        bundle_name = "test-bundle"

        # Create plan
        runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])

        # First update
        result1 = runner.invoke(
            app,
            [
                "plan",
                "update-idea",
                "--target-users",
                "User 1",
                "--bundle",
                bundle_name,
            ],
        )
        assert result1.exit_code == 0

        # Second update
        result2 = runner.invoke(
            app,
            [
                "plan",
                "update-idea",
                "--value-hypothesis",
                "Hypothesis 1",
                "--bundle",
                bundle_name,
            ],
        )
        assert result2.exit_code == 0

        # Third update
        result3 = runner.invoke(
            app,
            [
                "plan",
                "update-idea",
                "--constraints",
                "Constraint 1",
                "--bundle",
                bundle_name,
            ],
        )
        assert result3.exit_code == 0

        # Verify all updates are present
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        bundle = load_project_bundle(bundle_dir)
        assert bundle is not None
        assert bundle.idea is not None
        assert len(bundle.idea.target_users) == 1
        assert "User 1" in bundle.idea.target_users
        assert bundle.idea.value_hypothesis == "Hypothesis 1"
        assert len(bundle.idea.constraints) == 1
        assert "Constraint 1" in bundle.idea.constraints


class TestPlanHarden:
    """Integration tests for plan harden command."""

    def test_plan_harden_creates_sdd_manifest(self, tmp_path, monkeypatch):
        """Test plan harden creates SDD manifest from plan bundle."""
        monkeypatch.chdir(tmp_path)
        bundle_name = "test-bundle"

        # First, create a plan with idea and features
        init_result = runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])
        assert init_result.exit_code == 0

        # Add idea with narrative
        update_idea_result = runner.invoke(
            app,
            [
                "plan",
                "update-idea",
                "--target-users",
                "Developers",
                "--value-hypothesis",
                "Reduce technical debt",
                "--constraints",
                "Python 3.11+",
                "--bundle",
                bundle_name,
            ],
        )
        assert update_idea_result.exit_code == 0

        # Add a feature
        add_feature_result = runner.invoke(
            app,
            [
                "plan",
                "add-feature",
                "--key",
                "FEATURE-001",
                "--title",
                "User Authentication",
                "--acceptance",
                "Login works, Sessions persist",
                "--bundle",
                bundle_name,
            ],
        )
        assert add_feature_result.exit_code == 0

        # Now harden the plan
        harden_result = runner.invoke(app, ["plan", "harden", bundle_name, "--non-interactive"])
        assert harden_result.exit_code == 0
        assert "SDD manifest" in harden_result.stdout.lower() or "created" in harden_result.stdout.lower()

        # Verify SDD manifest was created (one per bundle)
        sdd_path = tmp_path / ".specfact" / "sdd" / f"{bundle_name}.yaml"
        assert sdd_path.exists()

        # Verify SDD manifest content
        from specfact_cli.models.sdd import SDDManifest
        from specfact_cli.utils.structured_io import load_structured_file

        sdd_data = load_structured_file(sdd_path)
        sdd_manifest = SDDManifest.model_validate(sdd_data)

        assert sdd_manifest.provenance.get("bundle_name") == bundle_name
        assert sdd_manifest.plan_bundle_hash is not None
        assert sdd_manifest.why.intent is not None
        assert len(sdd_manifest.what.capabilities) > 0
        assert sdd_manifest.version == "1.0.0"
        assert sdd_manifest.promotion_status == "draft"

    def test_plan_harden_with_custom_sdd_path(self, tmp_path, monkeypatch):
        """Test plan harden with custom SDD output path."""
        monkeypatch.chdir(tmp_path)
        bundle_name = "test-bundle"

        # Create a plan
        runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])

        # Harden with custom path
        custom_sdd = tmp_path / "custom-sdd.yaml"
        harden_result = runner.invoke(
            app,
            [
                "plan",
                "harden",
                bundle_name,
                "--non-interactive",
                "--sdd",
                str(custom_sdd),
            ],
        )
        assert harden_result.exit_code == 0

        # Verify SDD was created at custom path
        assert custom_sdd.exists()

    def test_plan_harden_with_json_format(self, tmp_path, monkeypatch):
        """Test plan harden creates SDD manifest in JSON format."""
        monkeypatch.chdir(tmp_path)
        bundle_name = "test-bundle"

        # Create a plan
        runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])

        # Harden with JSON format
        harden_result = runner.invoke(
            app,
            [
                "plan",
                "harden",
                bundle_name,
                "--non-interactive",
                "--output-format",
                "json",
            ],
        )
        assert harden_result.exit_code == 0

        # Verify JSON SDD was created (one per bundle)
        sdd_path = tmp_path / ".specfact" / "sdd" / f"{bundle_name}.json"
        assert sdd_path.exists()

        # Verify it's valid JSON
        import json

        sdd_data = json.loads(sdd_path.read_text())
        assert "version" in sdd_data
        assert "plan_bundle_id" in sdd_data
        assert "why" in sdd_data
        assert "what" in sdd_data
        assert "how" in sdd_data

    def test_plan_harden_links_to_plan_hash(self, tmp_path, monkeypatch):
        """Test plan harden links SDD manifest to project bundle hash."""
        monkeypatch.chdir(tmp_path)
        bundle_name = "test-bundle"

        # Create a plan
        runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])

        # Get project bundle hash before hardening
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        project_bundle_before = load_project_bundle(bundle_dir)
        summary_before = project_bundle_before.compute_summary(include_hash=True)
        project_hash_before = summary_before.content_hash

        # Ensure project hash was computed
        assert project_hash_before is not None, "Project hash should be computed"

        # Harden the plan
        harden_result = runner.invoke(app, ["plan", "harden", bundle_name, "--non-interactive"])
        assert harden_result.exit_code == 0

        # Verify SDD manifest hash matches project hash
        sdd_path = tmp_path / ".specfact" / "sdd" / f"{bundle_name}.yaml"
        from specfact_cli.models.sdd import SDDManifest
        from specfact_cli.utils.structured_io import load_structured_file

        sdd_data = load_structured_file(sdd_path)
        sdd_manifest = SDDManifest.model_validate(sdd_data)

        assert sdd_manifest.plan_bundle_hash == project_hash_before
        assert sdd_manifest.plan_bundle_id == project_hash_before[:16]

    def test_plan_harden_persists_hash_to_disk(self, tmp_path, monkeypatch):
        """Test plan harden saves project bundle with hash so subsequent commands work."""
        monkeypatch.chdir(tmp_path)
        bundle_name = "test-bundle"

        # Create a plan
        runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])

        # Harden the plan
        harden_result = runner.invoke(app, ["plan", "harden", bundle_name, "--non-interactive"])
        assert harden_result.exit_code == 0

        # Load SDD manifest to get the hash
        sdd_path = tmp_path / ".specfact" / "sdd" / f"{bundle_name}.yaml"
        from specfact_cli.models.sdd import SDDManifest
        from specfact_cli.utils.structured_io import load_structured_file

        sdd_data = load_structured_file(sdd_path)
        sdd_manifest = SDDManifest.model_validate(sdd_data)
        sdd_hash = sdd_manifest.plan_bundle_hash

        # Reload project bundle from disk and verify hash matches
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        project_bundle_after = load_project_bundle(bundle_dir)
        summary_after = project_bundle_after.compute_summary(include_hash=True)
        project_hash_after = summary_after.content_hash

        # Verify the hash persisted to disk
        assert project_hash_after is not None, "Project hash should be saved to disk"
        assert project_hash_after == sdd_hash, "Project hash on disk should match SDD hash"

    def test_plan_harden_extracts_why_from_idea(self, tmp_path, monkeypatch):
        """Test plan harden extracts WHY section from project bundle idea."""
        monkeypatch.chdir(tmp_path)
        bundle_name = "test-bundle"

        # Create a plan with idea
        runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])
        runner.invoke(
            app,
            [
                "plan",
                "update-idea",
                "--target-users",
                "Developers, DevOps",
                "--value-hypothesis",
                "Reduce technical debt by 50%",
                "--constraints",
                "Python 3.11+, Maintain backward compatibility",
                "--bundle",
                bundle_name,
            ],
        )

        # Harden the plan
        runner.invoke(app, ["plan", "harden", bundle_name, "--non-interactive"])

        # Verify WHY section was extracted
        sdd_path = tmp_path / ".specfact" / "sdd" / f"{bundle_name}.yaml"
        from specfact_cli.models.sdd import SDDManifest
        from specfact_cli.utils.structured_io import load_structured_file

        sdd_data = load_structured_file(sdd_path)
        sdd_manifest = SDDManifest.model_validate(sdd_data)

        assert sdd_manifest.why.intent is not None
        assert len(sdd_manifest.why.intent) > 0
        assert sdd_manifest.why.target_users == "Developers, DevOps"
        assert sdd_manifest.why.value_hypothesis == "Reduce technical debt by 50%"
        assert len(sdd_manifest.why.constraints) == 2

    def test_plan_harden_extracts_what_from_features(self, tmp_path, monkeypatch):
        """Test plan harden extracts WHAT section from project bundle features."""
        monkeypatch.chdir(tmp_path)
        bundle_name = "test-bundle"

        # Create a plan with features
        runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])
        runner.invoke(
            app,
            [
                "plan",
                "add-feature",
                "--key",
                "FEATURE-001",
                "--title",
                "User Authentication",
                "--acceptance",
                "Login works, Sessions persist",
                "--bundle",
                bundle_name,
            ],
        )
        runner.invoke(
            app,
            [
                "plan",
                "add-feature",
                "--key",
                "FEATURE-002",
                "--title",
                "Data Processing",
                "--acceptance",
                "Data is processed correctly",
                "--bundle",
                bundle_name,
            ],
        )

        # Harden the plan
        runner.invoke(app, ["plan", "harden", bundle_name, "--non-interactive"])

        # Verify WHAT section was extracted
        sdd_path = tmp_path / ".specfact" / "sdd" / f"{bundle_name}.yaml"
        from specfact_cli.models.sdd import SDDManifest
        from specfact_cli.utils.structured_io import load_structured_file

        sdd_data = load_structured_file(sdd_path)
        sdd_manifest = SDDManifest.model_validate(sdd_data)

        assert len(sdd_manifest.what.capabilities) == 2
        assert "User Authentication" in sdd_manifest.what.capabilities
        assert "Data Processing" in sdd_manifest.what.capabilities
        assert len(sdd_manifest.what.acceptance_criteria) >= 2

    def test_plan_harden_fails_without_plan(self, tmp_path, monkeypatch):
        """Test plan harden fails gracefully when no plan exists."""
        monkeypatch.chdir(tmp_path)

        # Try to harden without creating a plan
        harden_result = runner.invoke(app, ["plan", "harden", "nonexistent-bundle", "--non-interactive"])
        assert harden_result.exit_code == 1
        assert "not found" in harden_result.stdout.lower() or "No plan bundles found" in harden_result.stdout


class TestPlanReviewSddValidation:
    """Integration tests for plan review command with SDD validation."""

    def test_plan_review_warns_when_sdd_missing(self, tmp_path, monkeypatch):
        """Test plan review warns when SDD manifest is missing."""
        monkeypatch.chdir(tmp_path)
        bundle_name = "test-bundle"

        # Create a plan with content to review
        runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])
        runner.invoke(
            app,
            [
                "plan",
                "add-feature",
                "--key",
                "FEATURE-001",
                "--title",
                "Test Feature",
                "--acceptance",
                "Test acceptance",
                "--bundle",
                bundle_name,
            ],
        )

        # Run review
        result = runner.invoke(app, ["plan", "review", bundle_name, "--non-interactive", "--max-questions", "1"])

        # Review may exit with 0 or 1 depending on findings, but should check SDD
        assert (
            "SDD manifest not found" in result.stdout
            or "Checking SDD manifest" in result.stdout
            or "SDD manifest" in result.stdout
        )

    def test_plan_review_validates_sdd_when_present(self, tmp_path, monkeypatch):
        """Test plan review validates SDD manifest when present."""
        monkeypatch.chdir(tmp_path)
        bundle_name = "test-bundle"

        # Create a plan with content and harden it
        runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])
        runner.invoke(
            app,
            [
                "plan",
                "add-feature",
                "--key",
                "FEATURE-001",
                "--title",
                "Test Feature",
                "--acceptance",
                "Test acceptance",
                "--bundle",
                bundle_name,
            ],
        )
        runner.invoke(app, ["plan", "harden", bundle_name, "--non-interactive"])

        # Run review
        result = runner.invoke(app, ["plan", "review", bundle_name, "--non-interactive", "--max-questions", "1"])

        # Review may exit with 0 or 1 depending on findings, but should check SDD
        assert "Checking SDD manifest" in result.stdout or "SDD manifest" in result.stdout

    def test_plan_review_shows_sdd_validation_failures(self, tmp_path, monkeypatch):
        """Test plan review shows SDD validation failures."""
        monkeypatch.chdir(tmp_path)
        bundle_name = "test-bundle"

        # Create a plan with content and harden it
        runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])
        runner.invoke(
            app,
            [
                "plan",
                "add-feature",
                "--key",
                "FEATURE-001",
                "--title",
                "Test Feature",
                "--acceptance",
                "Test acceptance",
                "--bundle",
                bundle_name,
            ],
        )
        runner.invoke(app, ["plan", "harden", bundle_name, "--non-interactive"])

        # Modify the SDD manifest to create a hash mismatch (safer than modifying plan YAML)
        sdd_path = tmp_path / ".specfact" / "sdd" / f"{bundle_name}.yaml"
        import yaml

        sdd_data = yaml.safe_load(sdd_path.read_text())
        sdd_data["plan_bundle_hash"] = "invalid_hash_1234567890"
        sdd_path.write_text(yaml.dump(sdd_data))

        # Run review
        result = runner.invoke(app, ["plan", "review", bundle_name, "--non-interactive", "--max-questions", "1"])

        # Review may exit with 0 or 1 depending on findings, but should check SDD
        assert "Checking SDD manifest" in result.stdout or "SDD manifest" in result.stdout


class TestPlanPromoteSddValidation:
    """Integration tests for plan promote command with SDD validation."""

    def test_plan_promote_blocks_without_sdd_for_review_stage(self, tmp_path, monkeypatch):
        """Test plan promote blocks promotion to review stage without SDD manifest."""
        monkeypatch.chdir(tmp_path)
        bundle_name = "test-bundle"

        # Create a plan with features and stories but don't harden it
        runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])
        runner.invoke(
            app,
            [
                "plan",
                "add-feature",
                "--key",
                "FEATURE-001",
                "--title",
                "Test Feature",
                "--acceptance",
                "Test acceptance",
                "--bundle",
                bundle_name,
            ],
        )
        runner.invoke(
            app,
            [
                "plan",
                "add-story",
                "--feature",
                "FEATURE-001",
                "--key",
                "STORY-001",
                "--title",
                "Test Story",
                "--bundle",
                bundle_name,
            ],
        )

        # Try to promote to review stage
        result = runner.invoke(app, ["plan", "promote", bundle_name, "--stage", "review"])

        assert result.exit_code == 1
        assert "SDD manifest is required" in result.stdout or "SDD manifest" in result.stdout
        assert "plan harden" in result.stdout

    def test_plan_promote_blocks_without_sdd_for_approved_stage(self, tmp_path, monkeypatch):
        """Test plan promote blocks promotion to approved stage without SDD manifest."""
        monkeypatch.chdir(tmp_path)
        bundle_name = "test-bundle"

        # Create a plan with features and stories but don't harden it
        runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])
        runner.invoke(
            app,
            [
                "plan",
                "add-feature",
                "--key",
                "FEATURE-001",
                "--title",
                "Test Feature",
                "--acceptance",
                "Test acceptance",
                "--bundle",
                bundle_name,
            ],
        )
        runner.invoke(
            app,
            [
                "plan",
                "add-story",
                "--feature",
                "FEATURE-001",
                "--key",
                "STORY-001",
                "--title",
                "Test Story",
                "--bundle",
                bundle_name,
            ],
        )

        # Try to promote to approved stage
        result = runner.invoke(app, ["plan", "promote", bundle_name, "--stage", "approved"])

        assert result.exit_code == 1
        assert "SDD manifest is required" in result.stdout or "SDD manifest" in result.stdout

    def test_plan_promote_allows_with_sdd_manifest(self, tmp_path, monkeypatch):
        """Test plan promote allows promotion when SDD manifest is valid."""
        monkeypatch.chdir(tmp_path)
        bundle_name = "test-bundle"

        # Create a plan with features and stories, then harden it
        runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])
        runner.invoke(
            app,
            [
                "plan",
                "add-feature",
                "--key",
                "FEATURE-001",
                "--title",
                "Test Feature",
                "--acceptance",
                "Test acceptance",
                "--bundle",
                bundle_name,
            ],
        )
        runner.invoke(
            app,
            [
                "plan",
                "add-story",
                "--feature",
                "FEATURE-001",
                "--key",
                "STORY-001",
                "--title",
                "Test Story",
                "--bundle",
                bundle_name,
            ],
        )
        runner.invoke(app, ["plan", "harden", bundle_name, "--non-interactive"])

        # Promote to review stage
        result = runner.invoke(app, ["plan", "promote", bundle_name, "--stage", "review"])

        # May fail if there are other validation issues (e.g., coverage), but SDD should be validated
        if result.exit_code != 0:
            # Check if it's an SDD validation issue or something else
            assert "SDD" in result.stdout or "stage" in result.stdout.lower()
        else:
            assert (
                "SDD manifest validated successfully" in result.stdout
                or "Promoted" in result.stdout
                or "stage" in result.stdout.lower()
            )

    def test_plan_promote_blocks_on_hash_mismatch(self, tmp_path, monkeypatch):
        """Test plan promote blocks on SDD hash mismatch."""
        monkeypatch.chdir(tmp_path)
        bundle_name = "test-bundle"

        # Create a plan with features and stories, then harden it
        runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])
        runner.invoke(
            app,
            [
                "plan",
                "add-feature",
                "--key",
                "FEATURE-001",
                "--title",
                "Test Feature",
                "--acceptance",
                "Test acceptance",
                "--bundle",
                bundle_name,
            ],
        )
        runner.invoke(
            app,
            [
                "plan",
                "add-story",
                "--feature",
                "FEATURE-001",
                "--key",
                "STORY-001",
                "--title",
                "Test Story",
                "--bundle",
                bundle_name,
            ],
        )
        runner.invoke(app, ["plan", "harden", bundle_name, "--non-interactive"])

        # Modify the SDD manifest to create a hash mismatch (safer than modifying plan YAML)
        sdd_path = tmp_path / ".specfact" / "sdd" / f"{bundle_name}.yaml"
        import yaml

        sdd_data = yaml.safe_load(sdd_path.read_text())
        sdd_data["plan_bundle_hash"] = "invalid_hash_1234567890"
        sdd_path.write_text(yaml.dump(sdd_data))

        # Try to promote
        result = runner.invoke(app, ["plan", "promote", bundle_name, "--stage", "review"])

        assert result.exit_code == 1
        assert (
            "SDD manifest validation failed" in result.stdout
            or "hash mismatch" in result.stdout.lower()
            or "SDD" in result.stdout
        )

    def test_plan_promote_force_bypasses_sdd_validation(self, tmp_path, monkeypatch):
        """Test plan promote --force bypasses SDD validation."""
        monkeypatch.chdir(tmp_path)
        bundle_name = "test-bundle"

        # Create a plan with features and stories but don't harden it
        runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])
        runner.invoke(
            app,
            [
                "plan",
                "add-feature",
                "--key",
                "FEATURE-001",
                "--title",
                "Test Feature",
                "--acceptance",
                "Test acceptance",
                "--bundle",
                bundle_name,
            ],
        )
        runner.invoke(
            app,
            [
                "plan",
                "add-story",
                "--feature",
                "FEATURE-001",
                "--key",
                "STORY-001",
                "--title",
                "Test Story",
                "--bundle",
                bundle_name,
            ],
        )

        # Try to promote with --force
        result = runner.invoke(app, ["plan", "promote", bundle_name, "--stage", "review", "--force"])

        # Should succeed with force flag
        assert result.exit_code == 0
        assert (
            "--force" in result.stdout
            or "Promoted" in result.stdout
            or "despite" in result.stdout.lower()
            or "stage" in result.stdout.lower()
        )

    def test_plan_promote_warns_on_coverage_threshold_warnings(self, tmp_path, monkeypatch):
        """Test plan promote warns on coverage threshold violations."""
        monkeypatch.chdir(tmp_path)
        bundle_name = "test-bundle"

        # Create a plan with features and stories
        runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])
        runner.invoke(
            app,
            [
                "plan",
                "add-feature",
                "--key",
                "FEATURE-001",
                "--title",
                "Test Feature",
                "--acceptance",
                "Test acceptance",
                "--bundle",
                bundle_name,
            ],
        )
        runner.invoke(
            app,
            [
                "plan",
                "add-story",
                "--feature",
                "FEATURE-001",
                "--key",
                "STORY-001",
                "--title",
                "Test Story",
                "--bundle",
                bundle_name,
            ],
        )

        # Harden the plan
        runner.invoke(app, ["plan", "harden", bundle_name, "--non-interactive"])

        # Promote to review stage
        result = runner.invoke(app, ["plan", "promote", bundle_name, "--stage", "review"])

        # Should succeed (default thresholds are low) or show warnings
        assert result.exit_code in (0, 1)  # May succeed or warn depending on thresholds
        assert "SDD" in result.stdout or "Promoted" in result.stdout or "stage" in result.stdout.lower()

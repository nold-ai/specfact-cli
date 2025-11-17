"""Integration tests for plan command."""

from unittest.mock import patch

from typer.testing import CliRunner

from specfact_cli.cli import app
from specfact_cli.models.plan import Metadata, PlanBundle
from specfact_cli.utils.yaml_utils import load_yaml
from specfact_cli.validators.schema import validate_plan_bundle


runner = CliRunner()


class TestPlanInitNonInteractive:
    """Test plan init command in non-interactive mode."""

    def test_plan_init_minimal_default_path(self, tmp_path, monkeypatch):
        """Test plan init creates minimal plan at default path."""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["plan", "init", "--no-interactive"])

        assert result.exit_code == 0
        assert "created" in result.stdout.lower() or "initialized" in result.stdout.lower()

        # Verify file was created in .specfact/plans/
        plan_path = tmp_path / ".specfact" / "plans" / "main.bundle.yaml"
        assert plan_path.exists()

        # Verify content
        plan_data = load_yaml(plan_path)
        assert plan_data["version"] == "1.0"
        assert "product" in plan_data
        assert "features" in plan_data
        assert plan_data["features"] == []

    def test_plan_init_minimal_custom_path(self, tmp_path):
        """Test plan init with custom output path."""
        output_path = tmp_path / "custom-plan.yaml"

        result = runner.invoke(app, ["plan", "init", "--no-interactive", "--out", str(output_path)])

        assert result.exit_code == 0
        assert "Minimal plan created" in result.stdout
        assert output_path.exists()

        # Validate generated plan
        is_valid, _error, bundle = validate_plan_bundle(output_path)
        assert is_valid is True
        assert bundle is not None

    def test_plan_init_minimal_validates(self, tmp_path):
        """Test that minimal plan passes validation."""
        output_path = tmp_path / "plan.yaml"

        result = runner.invoke(app, ["plan", "init", "--no-interactive", "--out", str(output_path)])

        assert result.exit_code == 0

        # Load and validate
        is_valid, error, bundle = validate_plan_bundle(output_path)
        assert is_valid is True, f"Validation failed: {error}"
        assert bundle is not None
        assert isinstance(bundle, PlanBundle)


class TestPlanInitInteractive:
    """Test plan init command in interactive mode."""

    def test_plan_init_basic_idea_only(self, tmp_path):
        """Test plan init with minimal interactive input."""
        output_path = tmp_path / "plan.yaml"

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

            result = runner.invoke(app, ["plan", "init", "--out", str(output_path)])

            assert result.exit_code == 0
            assert "Plan created successfully" in result.stdout
            assert output_path.exists()

            # Verify plan content
            is_valid, _error, bundle = validate_plan_bundle(output_path)
            assert is_valid is True
            assert bundle is not None
            assert bundle.idea is not None
            assert bundle.idea.title == "Test Project"

    def test_plan_init_full_workflow(self, tmp_path):
        """Test plan init with complete interactive workflow."""
        output_path = tmp_path / "plan.yaml"

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

            result = runner.invoke(app, ["plan", "init", "--out", str(output_path)])

            assert result.exit_code == 0
            assert "Plan created successfully" in result.stdout
            assert output_path.exists()

            # Verify comprehensive plan
            is_valid, _error, bundle = validate_plan_bundle(output_path)
            assert is_valid is True
            assert bundle is not None
            assert bundle.idea is not None
            assert bundle.idea.title == "Full Test Project"
            assert len(bundle.features) == 1
            assert bundle.features[0].key == "FEATURE-001"
            assert len(bundle.features[0].stories) == 1
            assert bundle.features[0].stories[0].key == "STORY-001"

    def test_plan_init_with_business_context(self, tmp_path):
        """Test plan init with business context."""
        output_path = tmp_path / "plan.yaml"

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

            result = runner.invoke(app, ["plan", "init", "--out", str(output_path)])

            assert result.exit_code == 0
            assert output_path.exists()

            is_valid, _error, bundle = validate_plan_bundle(output_path)
            assert is_valid is True
            assert bundle is not None
            assert bundle.business is not None
            assert len(bundle.business.segments) == 2
            assert "Enterprise" in bundle.business.segments

    def test_plan_init_keyboard_interrupt(self, tmp_path):
        """Test plan init handles keyboard interrupt gracefully."""
        output_path = tmp_path / "plan.yaml"

        with patch("specfact_cli.commands.plan.prompt_text") as mock_text:
            mock_text.side_effect = KeyboardInterrupt()

            result = runner.invoke(app, ["plan", "init", "--out", str(output_path)])

            assert result.exit_code == 1
            assert "cancelled" in result.stdout.lower()
            assert not output_path.exists()


class TestPlanInitValidation:
    """Test plan init validation behavior."""

    def test_generated_plan_passes_json_schema_validation(self, tmp_path):
        """Test that generated plans pass JSON schema validation."""
        output_path = tmp_path / "plan.yaml"

        with (
            patch("specfact_cli.commands.plan.prompt_text") as mock_text,
            patch("specfact_cli.commands.plan.prompt_confirm") as mock_confirm,
            patch("specfact_cli.commands.plan.prompt_list") as mock_list,
        ):
            mock_text.side_effect = ["Schema Test", "Test for schema validation"]
            mock_confirm.side_effect = [False, False, False, False]
            mock_list.return_value = ["Testing"]

            result = runner.invoke(app, ["plan", "init", "--out", str(output_path)])

            assert result.exit_code == 0
            assert "Plan validation passed" in result.stdout

    def test_plan_init_creates_valid_pydantic_model(self, tmp_path):
        """Test that generated plan can be loaded as Pydantic model."""
        output_path = tmp_path / "plan.yaml"

        result = runner.invoke(app, ["plan", "init", "--no-interactive", "--out", str(output_path)])

        assert result.exit_code == 0

        # Load as Pydantic model
        plan_data = load_yaml(output_path)
        bundle = PlanBundle(**plan_data)

        assert bundle.version == "1.0"
        assert isinstance(bundle.product.themes, list)
        assert isinstance(bundle.features, list)


class TestPlanInitEdgeCases:
    """Test edge cases for plan init."""

    def test_plan_init_with_metrics(self, tmp_path):
        """Test plan init with metrics dictionary."""
        output_path = tmp_path / "plan.yaml"

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

            result = runner.invoke(app, ["plan", "init", "--out", str(output_path)])

            assert result.exit_code == 0

            is_valid, _error, bundle = validate_plan_bundle(output_path)
            assert is_valid is True
            assert bundle is not None
            assert bundle.idea is not None
            assert bundle.idea.metrics is not None
            assert bundle.idea.metrics["efficiency"] == 0.8

    def test_plan_init_with_releases(self, tmp_path):
        """Test plan init with multiple releases."""
        output_path = tmp_path / "plan.yaml"

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

            result = runner.invoke(app, ["plan", "init", "--out", str(output_path)])

            assert result.exit_code == 0

            is_valid, _error, bundle = validate_plan_bundle(output_path)
            assert is_valid is True
            assert bundle is not None
            assert len(bundle.product.releases) == 2
            assert bundle.product.releases[0].name == "v1.0 - MVP"
            assert bundle.product.releases[1].name == "v2.0 - Full"


class TestPlanAddFeature:
    """Integration tests for plan add-feature command."""

    def test_add_feature_to_initialized_plan(self, tmp_path, monkeypatch):
        """Test adding a feature to a plan created with init."""
        monkeypatch.chdir(tmp_path)

        # First, create a plan
        init_result = runner.invoke(app, ["plan", "init", "--no-interactive"])
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
            ],
        )

        assert result.exit_code == 0
        assert "added successfully" in result.stdout.lower()

        # Verify feature was added and plan is still valid
        plan_path = tmp_path / ".specfact" / "plans" / "main.bundle.yaml"
        is_valid, _error, bundle = validate_plan_bundle(plan_path)
        assert is_valid is True
        assert bundle is not None
        assert len(bundle.features) == 1
        assert bundle.features[0].key == "FEATURE-001"
        assert bundle.features[0].title == "Test Feature"
        assert len(bundle.features[0].outcomes) == 2
        assert len(bundle.features[0].acceptance) == 2

    def test_add_multiple_features(self, tmp_path, monkeypatch):
        """Test adding multiple features sequentially."""
        monkeypatch.chdir(tmp_path)

        # Create plan
        runner.invoke(app, ["plan", "init", "--no-interactive"])

        # Add first feature
        result1 = runner.invoke(
            app,
            ["plan", "add-feature", "--key", "FEATURE-001", "--title", "Feature One"],
        )
        assert result1.exit_code == 0

        # Add second feature
        result2 = runner.invoke(
            app,
            ["plan", "add-feature", "--key", "FEATURE-002", "--title", "Feature Two"],
        )
        assert result2.exit_code == 0

        # Verify both features exist
        plan_path = tmp_path / ".specfact" / "plans" / "main.bundle.yaml"
        is_valid, _error, bundle = validate_plan_bundle(plan_path)
        assert is_valid is True
        assert bundle is not None
        assert len(bundle.features) == 2
        assert bundle.features[0].key == "FEATURE-001"
        assert bundle.features[1].key == "FEATURE-002"

    def test_add_feature_preserves_existing_features(self, tmp_path):
        """Test that adding a feature preserves existing features."""
        plan_path = tmp_path / "plan.yaml"

        # Create plan with existing feature
        result = runner.invoke(
            app,
            ["plan", "init", "--no-interactive", "--out", str(plan_path)],
        )
        assert result.exit_code == 0

        # Load plan and manually add a feature (simulating existing feature)
        from specfact_cli.generators.plan_generator import PlanGenerator
        from specfact_cli.models.plan import Feature

        is_valid, _error, bundle = validate_plan_bundle(plan_path)
        assert is_valid is True
        assert bundle is not None
        # Type guard: bundle is not None after assertion
        assert isinstance(bundle, PlanBundle)
        bundle.features.append(Feature(key="FEATURE-000", title="Existing Feature", outcomes=[], acceptance=[]))
        generator = PlanGenerator()
        generator.generate(bundle, plan_path)

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
                "--plan",
                str(plan_path),
            ],
        )
        assert result.exit_code == 0

        # Verify both features exist
        is_valid, _error, bundle = validate_plan_bundle(plan_path)
        assert is_valid is True
        assert bundle is not None
        assert len(bundle.features) == 2
        feature_keys = {f.key for f in bundle.features}
        assert "FEATURE-000" in feature_keys
        assert "FEATURE-001" in feature_keys


class TestPlanAddStory:
    """Integration tests for plan add-story command."""

    def test_add_story_to_feature(self, tmp_path, monkeypatch):
        """Test adding a story to a feature in an initialized plan."""
        monkeypatch.chdir(tmp_path)

        # Create plan
        runner.invoke(app, ["plan", "init", "--no-interactive"])

        # Add a feature first
        runner.invoke(
            app,
            ["plan", "add-feature", "--key", "FEATURE-001", "--title", "Test Feature"],
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
            ],
        )

        assert result.exit_code == 0
        assert "added" in result.stdout.lower()

        # Verify story was added
        plan_path = tmp_path / ".specfact" / "plans" / "main.bundle.yaml"
        is_valid, _error, bundle = validate_plan_bundle(plan_path)
        assert is_valid is True
        assert bundle is not None
        feature = next(f for f in bundle.features if f.key == "FEATURE-001")
        assert len(feature.stories) == 1
        assert feature.stories[0].key == "STORY-001"
        assert feature.stories[0].title == "Test Story"
        assert feature.stories[0].story_points == 5
        assert len(feature.stories[0].acceptance) == 2

    def test_add_multiple_stories_to_feature(self, tmp_path, monkeypatch):
        """Test adding multiple stories to the same feature."""
        monkeypatch.chdir(tmp_path)

        # Create plan and feature
        runner.invoke(app, ["plan", "init", "--no-interactive"])
        runner.invoke(
            app,
            ["plan", "add-feature", "--key", "FEATURE-001", "--title", "Test Feature"],
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
            ],
        )
        assert result2.exit_code == 0

        # Verify both stories exist
        plan_path = tmp_path / ".specfact" / "plans" / "main.bundle.yaml"
        is_valid, _error, bundle = validate_plan_bundle(plan_path)
        assert is_valid is True
        assert bundle is not None
        feature = next(f for f in bundle.features if f.key == "FEATURE-001")
        assert len(feature.stories) == 2
        story_keys = {s.key for s in feature.stories}
        assert "STORY-001" in story_keys
        assert "STORY-002" in story_keys

    def test_add_story_with_all_options(self, tmp_path, monkeypatch):
        """Test adding a story with all available options."""
        monkeypatch.chdir(tmp_path)

        # Create plan and feature
        runner.invoke(app, ["plan", "init", "--no-interactive"])
        runner.invoke(
            app,
            ["plan", "add-feature", "--key", "FEATURE-001", "--title", "Test Feature"],
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
            ],
        )

        assert result.exit_code == 0

        # Verify all options were set
        plan_path = tmp_path / ".specfact" / "plans" / "main.bundle.yaml"
        is_valid, _error, bundle = validate_plan_bundle(plan_path)
        assert is_valid is True
        assert bundle is not None
        feature = next(f for f in bundle.features if f.key == "FEATURE-001")
        story = feature.stories[0]
        assert story.key == "STORY-001"
        assert story.story_points == 8
        assert story.value_points == 13
        assert story.draft is True
        assert len(story.acceptance) == 2

    def test_add_story_preserves_existing_stories(self, tmp_path):
        """Test that adding a story preserves existing stories in the feature."""
        plan_path = tmp_path / "plan.yaml"

        # Create plan with feature and existing story
        from specfact_cli.generators.plan_generator import PlanGenerator
        from specfact_cli.models.plan import Feature, PlanBundle, Product, Story

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
                    stories=[
                        Story(
                            key="STORY-000", title="Existing Story", acceptance=[], story_points=None, value_points=None
                        )
                    ],
                )
            ],
            metadata=Metadata(stage="draft", promoted_at=None, promoted_by=None),
        )
        generator = PlanGenerator()
        generator.generate(bundle, plan_path)

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
                "--plan",
                str(plan_path),
            ],
        )
        assert result.exit_code == 0

        # Verify both stories exist
        is_valid, _error, bundle = validate_plan_bundle(plan_path)
        assert is_valid is True
        assert bundle is not None
        feature = bundle.features[0]
        assert len(feature.stories) == 2
        story_keys = {s.key for s in feature.stories}
        assert "STORY-000" in story_keys
        assert "STORY-001" in story_keys


class TestPlanAddWorkflow:
    """Integration tests for add-feature and add-story workflow."""

    def test_complete_feature_story_workflow(self, tmp_path, monkeypatch):
        """Test complete workflow: init -> add-feature -> add-story."""
        monkeypatch.chdir(tmp_path)

        # Step 1: Initialize plan
        init_result = runner.invoke(app, ["plan", "init", "--no-interactive"])
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
            ],
        )
        assert story_result.exit_code == 0

        # Verify complete plan structure
        plan_path = tmp_path / ".specfact" / "plans" / "main.bundle.yaml"
        is_valid, _error, bundle = validate_plan_bundle(plan_path)
        assert is_valid is True
        assert bundle is not None
        assert len(bundle.features) == 1
        assert bundle.features[0].key == "FEATURE-001"
        assert bundle.features[0].title == "User Authentication"
        assert len(bundle.features[0].stories) == 1
        assert bundle.features[0].stories[0].key == "STORY-001"
        assert bundle.features[0].stories[0].story_points == 5


class TestPlanUpdateIdea:
    """Integration tests for plan update-idea command."""

    def test_update_idea_in_initialized_plan(self, tmp_path, monkeypatch):
        """Test updating idea section in a plan created with init."""
        monkeypatch.chdir(tmp_path)

        # First, create a plan
        init_result = runner.invoke(app, ["plan", "init", "--no-interactive"])
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
            ],
        )

        assert result.exit_code == 0
        assert "updated successfully" in result.stdout.lower()

        # Verify idea was updated and plan is still valid
        plan_path = tmp_path / ".specfact" / "plans" / "main.bundle.yaml"
        is_valid, _error, bundle = validate_plan_bundle(plan_path)
        assert is_valid is True
        assert bundle is not None
        assert bundle.idea is not None
        assert len(bundle.idea.target_users) == 2
        assert "Developers" in bundle.idea.target_users
        assert bundle.idea.value_hypothesis == "Reduce technical debt"
        assert len(bundle.idea.constraints) == 2

    def test_update_idea_creates_section_if_missing(self, tmp_path, monkeypatch):
        """Test that update-idea creates idea section if plan doesn't have one."""
        monkeypatch.chdir(tmp_path)

        # Create plan without idea section
        init_result = runner.invoke(app, ["plan", "init", "--no-interactive"])
        assert init_result.exit_code == 0

        # Verify plan has no idea section initially
        plan_path = tmp_path / ".specfact" / "plans" / "main.bundle.yaml"
        is_valid, _error, bundle = validate_plan_bundle(plan_path)
        assert is_valid is True
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
            ],
        )

        assert result.exit_code == 0
        assert "Created new idea section" in result.stdout

        # Verify idea section was created
        is_valid, _error, bundle = validate_plan_bundle(plan_path)
        assert is_valid is True
        assert bundle is not None
        assert bundle.idea is not None
        assert len(bundle.idea.target_users) == 1
        assert bundle.idea.value_hypothesis == "Test hypothesis"

    def test_update_idea_preserves_other_sections(self, tmp_path, monkeypatch):
        """Test that update-idea preserves features and other sections."""
        monkeypatch.chdir(tmp_path)

        # Create plan with features
        runner.invoke(app, ["plan", "init", "--no-interactive"])
        runner.invoke(
            app,
            ["plan", "add-feature", "--key", "FEATURE-001", "--title", "Test Feature"],
        )

        # Update idea
        result = runner.invoke(
            app,
            [
                "plan",
                "update-idea",
                "--target-users",
                "Users",
            ],
        )

        assert result.exit_code == 0

        # Verify features are preserved
        plan_path = tmp_path / ".specfact" / "plans" / "main.bundle.yaml"
        is_valid, _error, bundle = validate_plan_bundle(plan_path)
        assert is_valid is True
        assert bundle is not None
        assert bundle.idea is not None
        assert len(bundle.features) == 1
        assert bundle.features[0].key == "FEATURE-001"
        assert len(bundle.idea.target_users) == 1

    def test_update_idea_multiple_times(self, tmp_path, monkeypatch):
        """Test updating idea section multiple times sequentially."""
        monkeypatch.chdir(tmp_path)

        # Create plan
        runner.invoke(app, ["plan", "init", "--no-interactive"])

        # First update
        result1 = runner.invoke(
            app,
            [
                "plan",
                "update-idea",
                "--target-users",
                "User 1",
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
            ],
        )
        assert result3.exit_code == 0

        # Verify all updates are present
        plan_path = tmp_path / ".specfact" / "plans" / "main.bundle.yaml"
        is_valid, _error, bundle = validate_plan_bundle(plan_path)
        assert is_valid is True
        assert bundle is not None
        assert bundle.idea is not None
        assert len(bundle.idea.target_users) == 1
        assert "User 1" in bundle.idea.target_users
        assert bundle.idea.value_hypothesis == "Hypothesis 1"
        assert len(bundle.idea.constraints) == 1
        assert "Constraint 1" in bundle.idea.constraints

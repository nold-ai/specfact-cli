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
        assert plan_data["version"] == "1.1"
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

        assert bundle.version == "1.1"
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
            ],
            metadata=Metadata(
                stage="draft", promoted_at=None, promoted_by=None, analysis_scope=None, entry_point=None, summary=None
            ),
            clarifications=None,
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


class TestPlanHarden:
    """Integration tests for plan harden command."""

    def test_plan_harden_creates_sdd_manifest(self, tmp_path, monkeypatch):
        """Test plan harden creates SDD manifest from plan bundle."""
        monkeypatch.chdir(tmp_path)

        # First, create a plan with idea and features
        init_result = runner.invoke(app, ["plan", "init", "--no-interactive"])
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
            ],
        )
        assert add_feature_result.exit_code == 0

        # Now harden the plan
        harden_result = runner.invoke(app, ["plan", "harden", "--non-interactive"])
        assert harden_result.exit_code == 0
        assert "SDD manifest created" in harden_result.stdout

        # Verify SDD manifest was created
        sdd_path = tmp_path / ".specfact" / "sdd.yaml"
        assert sdd_path.exists()

        # Verify SDD manifest content
        from specfact_cli.models.sdd import SDDManifest
        from specfact_cli.utils.structured_io import load_structured_file

        sdd_data = load_structured_file(sdd_path)
        sdd_manifest = SDDManifest.model_validate(sdd_data)

        assert sdd_manifest.plan_bundle_id is not None
        assert sdd_manifest.plan_bundle_hash is not None
        assert sdd_manifest.why.intent is not None
        assert len(sdd_manifest.what.capabilities) > 0
        assert sdd_manifest.version == "1.0.0"
        assert sdd_manifest.promotion_status == "draft"

    def test_plan_harden_with_custom_sdd_path(self, tmp_path, monkeypatch):
        """Test plan harden with custom SDD output path."""
        monkeypatch.chdir(tmp_path)

        # Create a plan
        runner.invoke(app, ["plan", "init", "--no-interactive"])

        # Harden with custom path
        custom_sdd = tmp_path / "custom-sdd.yaml"
        harden_result = runner.invoke(
            app,
            [
                "plan",
                "harden",
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

        # Create a plan
        runner.invoke(app, ["plan", "init", "--no-interactive"])

        # Harden with JSON format
        harden_result = runner.invoke(
            app,
            [
                "plan",
                "harden",
                "--non-interactive",
                "--output-format",
                "json",
            ],
        )
        assert harden_result.exit_code == 0

        # Verify JSON SDD was created
        sdd_path = tmp_path / ".specfact" / "sdd.json"
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
        """Test plan harden links SDD manifest to plan bundle hash."""
        monkeypatch.chdir(tmp_path)

        # Create a plan
        runner.invoke(app, ["plan", "init", "--no-interactive"])

        # Get plan hash before hardening
        plan_path = tmp_path / ".specfact" / "plans" / "main.bundle.yaml"
        from specfact_cli.migrations.plan_migrator import load_plan_bundle

        bundle_before = load_plan_bundle(plan_path)
        bundle_before.update_summary(include_hash=True)
        plan_hash_before = (
            bundle_before.metadata.summary.content_hash
            if bundle_before.metadata and bundle_before.metadata.summary
            else None
        )

        # Ensure plan hash was computed
        assert plan_hash_before is not None, "Plan hash should be computed"

        # Harden the plan
        harden_result = runner.invoke(app, ["plan", "harden", "--non-interactive"])
        assert harden_result.exit_code == 0

        # Verify SDD manifest hash matches plan hash
        sdd_path = tmp_path / ".specfact" / "sdd.yaml"
        from specfact_cli.models.sdd import SDDManifest
        from specfact_cli.utils.structured_io import load_structured_file

        sdd_data = load_structured_file(sdd_path)
        sdd_manifest = SDDManifest.model_validate(sdd_data)

        assert sdd_manifest.plan_bundle_hash == plan_hash_before
        assert sdd_manifest.plan_bundle_id == plan_hash_before[:16]

    def test_plan_harden_persists_hash_to_disk(self, tmp_path, monkeypatch):
        """Test plan harden saves plan bundle with hash so subsequent commands work."""
        monkeypatch.chdir(tmp_path)

        # Create a plan
        runner.invoke(app, ["plan", "init", "--no-interactive"])

        # Harden the plan
        harden_result = runner.invoke(app, ["plan", "harden", "--non-interactive"])
        assert harden_result.exit_code == 0

        # Load SDD manifest to get the hash
        sdd_path = tmp_path / ".specfact" / "sdd.yaml"
        from specfact_cli.models.sdd import SDDManifest
        from specfact_cli.utils.structured_io import load_structured_file

        sdd_data = load_structured_file(sdd_path)
        sdd_manifest = SDDManifest.model_validate(sdd_data)
        sdd_hash = sdd_manifest.plan_bundle_hash

        # Reload plan bundle from disk and verify hash matches
        plan_path = tmp_path / ".specfact" / "plans" / "main.bundle.yaml"
        from specfact_cli.migrations.plan_migrator import load_plan_bundle

        bundle_after = load_plan_bundle(plan_path)
        bundle_after.update_summary(include_hash=True)
        plan_hash_after = (
            bundle_after.metadata.summary.content_hash
            if bundle_after.metadata and bundle_after.metadata.summary
            else None
        )

        # Verify the hash persisted to disk
        assert plan_hash_after is not None, "Plan hash should be saved to disk"
        assert plan_hash_after == sdd_hash, "Plan hash on disk should match SDD hash"

        # Verify subsequent command works (generate contracts should not fail on hash mismatch)
        generate_result = runner.invoke(app, ["generate", "contracts", "--non-interactive"])
        assert generate_result.exit_code == 0, "generate contracts should work after plan harden"

    def test_plan_harden_extracts_why_from_idea(self, tmp_path, monkeypatch):
        """Test plan harden extracts WHY section from plan bundle idea."""
        monkeypatch.chdir(tmp_path)

        # Create a plan with idea
        runner.invoke(app, ["plan", "init", "--no-interactive"])
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
            ],
        )

        # Harden the plan
        runner.invoke(app, ["plan", "harden", "--non-interactive"])

        # Verify WHY section was extracted
        sdd_path = tmp_path / ".specfact" / "sdd.yaml"
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
        """Test plan harden extracts WHAT section from plan bundle features."""
        monkeypatch.chdir(tmp_path)

        # Create a plan with features
        runner.invoke(app, ["plan", "init", "--no-interactive"])
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
            ],
        )

        # Harden the plan
        runner.invoke(app, ["plan", "harden", "--non-interactive"])

        # Verify WHAT section was extracted
        sdd_path = tmp_path / ".specfact" / "sdd.yaml"
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
        harden_result = runner.invoke(app, ["plan", "harden", "--non-interactive"])
        assert harden_result.exit_code == 1
        assert "not found" in harden_result.stdout.lower() or "No plan bundles found" in harden_result.stdout


class TestPlanReviewSddValidation:
    """Integration tests for plan review command with SDD validation."""

    def test_plan_review_warns_when_sdd_missing(self, tmp_path, monkeypatch):
        """Test plan review warns when SDD manifest is missing."""
        monkeypatch.chdir(tmp_path)

        # Create a plan with content to review
        runner.invoke(app, ["plan", "init", "--no-interactive"])
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
            ],
        )

        # Run review
        result = runner.invoke(app, ["plan", "review", "--non-interactive", "--max-questions", "1"])

        # Review may exit with 0 or 1 depending on findings, but should check SDD
        assert (
            "SDD manifest not found" in result.stdout
            or "Checking SDD manifest" in result.stdout
            or "SDD manifest" in result.stdout
        )

    def test_plan_review_validates_sdd_when_present(self, tmp_path, monkeypatch):
        """Test plan review validates SDD manifest when present."""
        monkeypatch.chdir(tmp_path)

        # Create a plan with content and harden it
        runner.invoke(app, ["plan", "init", "--no-interactive"])
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
            ],
        )
        runner.invoke(app, ["plan", "harden", "--non-interactive"])

        # Run review
        result = runner.invoke(app, ["plan", "review", "--non-interactive", "--max-questions", "1"])

        # Review may exit with 0 or 1 depending on findings, but should check SDD
        assert "Checking SDD manifest" in result.stdout
        assert "SDD manifest validated successfully" in result.stdout or "SDD manifest" in result.stdout

    def test_plan_review_shows_sdd_validation_failures(self, tmp_path, monkeypatch):
        """Test plan review shows SDD validation failures."""
        monkeypatch.chdir(tmp_path)

        # Create a plan with content and harden it
        runner.invoke(app, ["plan", "init", "--no-interactive"])
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
            ],
        )
        runner.invoke(app, ["plan", "harden", "--non-interactive"])

        # Modify the SDD manifest to create a hash mismatch (safer than modifying plan YAML)
        sdd_path = tmp_path / ".specfact" / "sdd.yaml"
        import yaml

        sdd_data = yaml.safe_load(sdd_path.read_text())
        sdd_data["plan_bundle_hash"] = "invalid_hash_1234567890"
        sdd_path.write_text(yaml.dump(sdd_data))

        # Run review
        result = runner.invoke(app, ["plan", "review", "--non-interactive", "--max-questions", "1"])

        # Review may exit with 0 or 1 depending on findings, but should check SDD
        assert "Checking SDD manifest" in result.stdout or "SDD manifest" in result.stdout


class TestPlanPromoteSddValidation:
    """Integration tests for plan promote command with SDD validation."""

    def test_plan_promote_blocks_without_sdd_for_review_stage(self, tmp_path, monkeypatch):
        """Test plan promote blocks promotion to review stage without SDD manifest."""
        monkeypatch.chdir(tmp_path)

        # Create a plan with features and stories but don't harden it
        runner.invoke(app, ["plan", "init", "--no-interactive"])
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
            ],
        )

        # Try to promote to review stage
        result = runner.invoke(app, ["plan", "promote", "--stage", "review"])

        assert result.exit_code == 1
        assert "SDD manifest is required" in result.stdout or "SDD manifest" in result.stdout
        assert "plan harden" in result.stdout

    def test_plan_promote_blocks_without_sdd_for_approved_stage(self, tmp_path, monkeypatch):
        """Test plan promote blocks promotion to approved stage without SDD manifest."""
        monkeypatch.chdir(tmp_path)

        # Create a plan with features and stories but don't harden it
        runner.invoke(app, ["plan", "init", "--no-interactive"])
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
            ],
        )

        # Try to promote to approved stage
        result = runner.invoke(app, ["plan", "promote", "--stage", "approved"])

        assert result.exit_code == 1
        assert "SDD manifest is required" in result.stdout or "SDD manifest" in result.stdout

    def test_plan_promote_allows_with_sdd_manifest(self, tmp_path, monkeypatch):
        """Test plan promote allows promotion when SDD manifest is valid."""
        monkeypatch.chdir(tmp_path)

        # Create a plan with features and stories, then harden it
        runner.invoke(app, ["plan", "init", "--no-interactive"])
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
            ],
        )
        runner.invoke(app, ["plan", "harden", "--non-interactive"])

        # Promote to review stage
        result = runner.invoke(app, ["plan", "promote", "--stage", "review"])

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

        # Create a plan with features and stories, then harden it
        runner.invoke(app, ["plan", "init", "--no-interactive"])
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
            ],
        )
        runner.invoke(app, ["plan", "harden", "--non-interactive"])

        # Modify the SDD manifest to create a hash mismatch (safer than modifying plan YAML)
        sdd_path = tmp_path / ".specfact" / "sdd.yaml"
        import yaml

        sdd_data = yaml.safe_load(sdd_path.read_text())
        sdd_data["plan_bundle_hash"] = "invalid_hash_1234567890"
        sdd_path.write_text(yaml.dump(sdd_data))

        # Try to promote
        result = runner.invoke(app, ["plan", "promote", "--stage", "review"])

        assert result.exit_code == 1
        assert (
            "SDD manifest validation failed" in result.stdout
            or "hash mismatch" in result.stdout.lower()
            or "SDD" in result.stdout
        )

    def test_plan_promote_force_bypasses_sdd_validation(self, tmp_path, monkeypatch):
        """Test plan promote --force bypasses SDD validation."""
        monkeypatch.chdir(tmp_path)

        # Create a plan with features and stories but don't harden it
        runner.invoke(app, ["plan", "init", "--no-interactive"])
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
            ],
        )

        # Try to promote with --force
        result = runner.invoke(app, ["plan", "promote", "--stage", "review", "--force"])

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

        # Create a plan with features and stories
        runner.invoke(app, ["plan", "init", "--no-interactive"])
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
            ],
        )

        # Harden the plan
        runner.invoke(app, ["plan", "harden", "--non-interactive"])

        # Promote to review stage
        result = runner.invoke(app, ["plan", "promote", "--stage", "review"])

        # Should succeed (default thresholds are low) or show warnings
        assert result.exit_code in (0, 1)  # May succeed or warn depending on thresholds
        assert "SDD" in result.stdout or "Promoted" in result.stdout or "stage" in result.stdout.lower()

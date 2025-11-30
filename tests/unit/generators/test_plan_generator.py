"""Unit tests for PlanGenerator.

Focus: Business logic and edge cases only (@beartype handles type validation).
"""

import json

import pytest

from specfact_cli.generators.plan_generator import PlanGenerator
from specfact_cli.models.plan import Feature, Idea, PlanBundle, Product, Release, Story
from specfact_cli.utils.structured_io import StructuredFormat


class TestPlanGenerator:
    """Test suite for PlanGenerator."""

    @pytest.fixture
    def sample_plan_bundle(self):
        """Create a sample plan bundle for testing."""
        return PlanBundle(
            idea=Idea(
                title="Test Idea",
                narrative="A test idea for validation",
                target_users=["developers", "testers"],
                value_hypothesis="Improve testing efficiency by 50%",
                metrics={"efficiency": 0.5, "coverage": 0.8},
            ),
            business=None,
            product=Product(
                themes=["Testing", "Quality"],
                releases=[
                    Release(
                        name="0.1.0 - Initial Release",
                        objectives=["Establish testing framework"],
                        scope=["FEATURE-1"],
                        risks=["Time constraints"],
                    )
                ],
            ),
            features=[
                Feature(
                    key="FEATURE-1",
                    title="Test Feature",
                    outcomes=["Improved test coverage"],
                    stories=[
                        Story(
                            key="STORY-1",
                            title="Test Story",
                            acceptance=["Criterion 1", "Criterion 2"],
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

    @pytest.fixture
    def generator(self):
        """Create a PlanGenerator instance."""
        return PlanGenerator()

    @pytest.fixture
    def output_dir(self, tmp_path):
        """Create a temporary output directory."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        return output_dir

    def test_generate(self, generator, sample_plan_bundle, output_dir):
        """Test generating plan bundle YAML file."""
        output_path = output_dir / "plan.bundle.yaml"

        generator.generate(sample_plan_bundle, output_path)

        assert output_path.exists()
        content = output_path.read_text()
        assert "Test Idea" in content
        assert "Testing" in content  # Product theme
        assert "FEATURE-1" in content
        assert "STORY-1" in content

    def test_generate_creates_parent_dirs(self, generator, sample_plan_bundle, output_dir):
        """Test that generate creates parent directories if they don't exist."""
        output_path = output_dir / "nested" / "dirs" / "plan.bundle.yaml"

        generator.generate(sample_plan_bundle, output_path)

        assert output_path.exists()
        assert output_path.parent.exists()

    def test_render_string(self, generator, sample_plan_bundle):
        """Test rendering plan bundle to string."""
        rendered = generator.render_string(sample_plan_bundle)

        assert isinstance(rendered, str)
        assert "Test Idea" in rendered
        assert "Testing" in rendered  # Product theme
        assert "FEATURE-1" in rendered

    def test_generate_excludes_none_values(self, generator, output_dir):
        """Test that None values are excluded from generated YAML."""
        plan_bundle = PlanBundle(
            idea=Idea(
                title="Test Idea",
                narrative="A test idea",
                metrics=None,
                # target_users, value_hypothesis are None
            ),
            business=None,
            product=Product(
                themes=[],
                releases=[],
            ),
            metadata=None,
            clarifications=None,
        )

        output_path = output_dir / "plan.bundle.yaml"
        generator.generate(plan_bundle, output_path)

        content = output_path.read_text()
        # None values should not appear in output
        assert "null" not in content.lower()
        assert "none" not in content.lower()

    def test_generate_json_output(self, generator, sample_plan_bundle, output_dir):
        """Test generating plan bundle in JSON format."""
        output_path = output_dir / "plan.bundle.json"

        generator.generate(sample_plan_bundle, output_path, format=StructuredFormat.JSON)

        assert output_path.exists()
        data = json.loads(output_path.read_text())
        assert data["idea"]["title"] == "Test Idea"
        assert data["features"][0]["key"] == "FEATURE-1"

    def test_render_string_json(self, generator, sample_plan_bundle):
        """Test rendering plan bundle as JSON string."""
        rendered = generator.render_string(sample_plan_bundle, format=StructuredFormat.JSON)
        payload = json.loads(rendered)
        assert payload["idea"]["title"] == "Test Idea"

    def test_generate_from_template(self, generator, output_dir):
        """Test generating file from custom template."""
        # Use the github-action template with empty context (template is predefined)
        context = {}

        output_path = output_dir / "workflow.yml"
        generator.generate_from_template("github-action.yml.j2", context, output_path)

        assert output_path.exists()
        content = output_path.read_text()
        # Template has predefined content
        assert "SpecFact CLI Validation" in content

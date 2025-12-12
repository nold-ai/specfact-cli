"""Unit tests for PersonaExporter."""

from pathlib import Path

import pytest

from specfact_cli.generators.persona_exporter import PersonaExporter
from specfact_cli.models.plan import Feature, Product, Story
from specfact_cli.models.project import BundleManifest, PersonaMapping, ProjectBundle


@pytest.fixture
def sample_bundle() -> ProjectBundle:
    """Create a sample project bundle for testing."""
    manifest = BundleManifest(
        schema_metadata=None,
        project_metadata=None,
        personas={
            "product-owner": PersonaMapping(
                owns=["idea", "business", "features.*.stories"], exports_to="specs/*/spec.md"
            ),
        },
    )
    product = Product(themes=["Testing"])
    bundle = ProjectBundle(manifest=manifest, bundle_name="test-bundle", product=product)

    feature = Feature(
        key="FEATURE-001",
        title="Test Feature",
        outcomes=["Test outcome"],
        stories=[
            Story(
                key="STORY-001",
                title="Test Story",
                acceptance=["Test acceptance"],
                story_points=None,
                value_points=None,
                scenarios=None,
                contracts=None,
                priority=None,
                rank=None,
                due_date=None,
                target_sprint=None,
                target_release=None,
                depends_on_stories=[],
                blocks_stories=[],
                business_value_description=None,
                business_metrics=[],
                definition_of_ready={},
            )
        ],
        source_tracking=None,
        contract=None,
        protocol=None,
        priority=None,
        rank=None,
        business_value_score=None,
        depends_on_features=[],
        blocks_features=[],
        business_value_description=None,
        target_users=[],
        success_metrics=[],
        target_release=None,
        estimated_story_points=None,
    )
    bundle.add_feature(feature)

    return bundle


class TestPersonaExporter:
    """Test suite for PersonaExporter."""

    def test_init_default_templates(self, tmp_path: Path) -> None:
        """Test exporter initialization with default templates."""
        exporter = PersonaExporter()
        assert exporter.templates_dir.exists()
        assert exporter.env is not None

    def test_init_custom_templates(self, tmp_path: Path) -> None:
        """Test exporter initialization with custom template directory."""
        custom_dir = tmp_path / "custom-templates"
        custom_dir.mkdir()

        exporter = PersonaExporter(templates_dir=custom_dir)
        assert exporter.templates_dir == custom_dir

    def test_prepare_template_context(self, sample_bundle: ProjectBundle) -> None:
        """Test template context preparation."""
        exporter = PersonaExporter()
        persona_mapping = sample_bundle.manifest.personas["product-owner"]

        context = exporter.prepare_template_context(sample_bundle, persona_mapping, "product-owner")

        assert context["bundle_name"] == "test-bundle"
        assert context["persona_name"] == "product-owner"
        assert "features" in context
        assert "FEATURE-001" in context["features"]
        assert "stories" in context["features"]["FEATURE-001"]

    def test_prepare_template_context_filters_by_ownership(self, sample_bundle: ProjectBundle) -> None:
        """Test that template context only includes persona-owned sections."""
        exporter = PersonaExporter()
        # Create persona that only owns constraints
        architect_mapping = PersonaMapping(owns=["features.*.constraints"], exports_to="specs/*/plan.md")
        sample_bundle.manifest.personas["architect"] = architect_mapping

        context = exporter.prepare_template_context(sample_bundle, architect_mapping, "architect")

        # Should have features but not stories (architect doesn't own stories)
        assert "features" in context
        if "FEATURE-001" in context["features"]:
            # If feature has constraints, they should be included
            # Stories should not be included
            assert "stories" not in context["features"]["FEATURE-001"] or not context["features"]["FEATURE-001"].get(
                "stories"
            )

    def test_get_template_product_owner(self, tmp_path: Path) -> None:
        """Test getting template for product-owner persona."""
        exporter = PersonaExporter()
        template = exporter.get_template("product-owner")
        assert template is not None

    def test_get_template_architect(self, tmp_path: Path) -> None:
        """Test getting template for architect persona."""
        exporter = PersonaExporter()
        template = exporter.get_template("architect")
        assert template is not None

    def test_get_template_developer(self, tmp_path: Path) -> None:
        """Test getting template for developer persona."""
        exporter = PersonaExporter()
        template = exporter.get_template("developer")
        assert template is not None

    def test_get_template_not_found(self, tmp_path: Path) -> None:
        """Test getting template for non-existent persona raises error."""
        exporter = PersonaExporter()
        with pytest.raises(FileNotFoundError):
            exporter.get_template("nonexistent-persona")

    def test_export_to_string(self, sample_bundle: ProjectBundle) -> None:
        """Test exporting to Markdown string."""
        exporter = PersonaExporter()
        persona_mapping = sample_bundle.manifest.personas["product-owner"]

        markdown = exporter.export_to_string(sample_bundle, persona_mapping, "product-owner")

        assert isinstance(markdown, str)
        assert "# Project Plan:" in markdown
        assert "test-bundle" in markdown
        assert "FEATURE-001" in markdown or "Test Feature" in markdown

    def test_export_to_file(self, sample_bundle: ProjectBundle, tmp_path: Path) -> None:
        """Test exporting to Markdown file."""
        exporter = PersonaExporter()
        persona_mapping = sample_bundle.manifest.personas["product-owner"]
        output_file = tmp_path / "exported.md"

        exporter.export_to_file(sample_bundle, persona_mapping, "product-owner", output_file)

        assert output_file.exists()
        content = output_file.read_text()
        assert "# Project Plan:" in content
        assert "test-bundle" in content

    def test_prepare_template_context_includes_agile_fields(self, sample_bundle: ProjectBundle) -> None:
        """Test that template context includes new agile/scrum fields."""
        exporter = PersonaExporter()
        persona_mapping = sample_bundle.manifest.personas["product-owner"]

        # Add agile fields to feature
        feature = sample_bundle.features["FEATURE-001"]
        feature.priority = "P1"
        feature.rank = 1
        feature.business_value_score = 75
        feature.target_release = "v2.1.0"
        feature.business_value_description = "Increases user engagement"
        feature.target_users = ["end-user", "admin"]
        feature.success_metrics = ["Increase conversion by 15%"]
        feature.depends_on_features = ["FEATURE-000"]
        feature.blocks_features = ["FEATURE-002"]

        # Add agile fields to story
        story = feature.stories[0]
        story.priority = "P1"
        story.rank = 1
        story.story_points = 5
        story.value_points = 8
        story.due_date = "2025-01-15"
        story.target_sprint = "Sprint 2025-01"
        story.target_release = "v2.1.0"
        story.business_value_description = "Improves user experience"
        story.business_metrics = ["Reduce support tickets by 30%"]
        story.depends_on_stories = ["STORY-000"]
        story.blocks_stories = ["STORY-002"]

        context = exporter.prepare_template_context(sample_bundle, persona_mapping, "product-owner")

        # Verify feature-level agile fields
        feature_data = context["features"]["FEATURE-001"]
        assert feature_data["priority"] == "P1"
        assert feature_data["rank"] == 1
        assert feature_data["business_value_score"] == 75
        assert feature_data["target_release"] == "v2.1.0"
        assert feature_data["business_value_description"] == "Increases user engagement"
        assert feature_data["target_users"] == ["end-user", "admin"]
        assert feature_data["success_metrics"] == ["Increase conversion by 15%"]
        assert feature_data["depends_on_features"] == ["FEATURE-000"]
        assert feature_data["blocks_features"] == ["FEATURE-002"]

        # Verify story-level agile fields
        story_data = feature_data["stories"][0]
        assert story_data["priority"] == "P1"
        assert story_data["rank"] == 1
        assert story_data["story_points"] == 5
        assert story_data["value_points"] == 8
        assert story_data["due_date"] == "2025-01-15"
        assert story_data["target_sprint"] == "Sprint 2025-01"
        assert story_data["target_release"] == "v2.1.0"
        assert story_data["business_value_description"] == "Improves user experience"
        assert story_data["business_metrics"] == ["Reduce support tickets by 30%"]
        assert story_data["depends_on_stories"] == ["STORY-000"]
        assert story_data["blocks_stories"] == ["STORY-002"]

        # Verify DoR status is calculated
        assert "definition_of_ready" in story_data
        dor = story_data["definition_of_ready"]
        assert dor["story_points"] is True
        assert dor["value_points"] is True
        assert dor["priority"] is True
        assert dor["dependencies"] is True
        assert dor["business_value"] is True
        assert dor["target_date"] is True
        assert dor["target_sprint"] is True

        # Verify feature-level story point total
        assert feature_data["estimated_story_points"] == 5

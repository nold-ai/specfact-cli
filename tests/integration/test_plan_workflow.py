"""Integration tests for plan bundle workflow."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from specfact_cli.models.plan import Business, Feature, Idea, Metadata, PlanBundle, Product, Story
from specfact_cli.utils.yaml_utils import load_yaml
from specfact_cli.validators.schema import SchemaValidator, validate_plan_bundle


class TestPlanBundleWorkflow:
    """Test complete plan bundle workflow from YAML to validation."""

    @pytest.fixture
    def fixtures_dir(self) -> Path:
        """Get the fixtures directory."""
        return Path(__file__).parent.parent / "fixtures"

    @pytest.fixture
    def sample_plan_path(self, fixtures_dir: Path) -> Path:
        """Get the sample plan path."""
        return fixtures_dir / "plans" / "sample-plan.yaml"

    def test_load_plan_from_yaml(self, sample_plan_path: Path):
        """Test loading a plan bundle from YAML file."""
        # Load YAML
        data = load_yaml(sample_plan_path)

        # Verify structure
        assert "version" in data
        assert "idea" in data
        assert "business" in data
        assert "product" in data
        assert "features" in data

        # Verify idea
        assert data["idea"]["title"] == "Developer Productivity CLI"
        assert len(data["idea"]["target_users"]) == 2

        # Verify business
        assert len(data["business"]["segments"]) == 2
        assert len(data["business"]["problems"]) == 2

        # Verify features
        assert len(data["features"]) == 2
        assert data["features"][0]["key"] == "FEATURE-001"

    def test_parse_plan_to_model(self, sample_plan_path: Path):
        """Test parsing YAML data into PlanBundle model."""
        data = load_yaml(sample_plan_path)

        # Parse to models
        idea = Idea(**data["idea"])
        business = Business(**data["business"])
        product = Product(**data["product"])
        features = [Feature(**f) for f in data["features"]]

        # Create plan bundle
        metadata = Metadata(**data.get("metadata", {})) if data.get("metadata") else None
        plan_bundle = PlanBundle(
            version=data["version"],
            idea=idea,
            business=business,
            product=product,
            features=features,
            metadata=metadata,
            clarifications=None,
        )

        # Verify model (uses version from file)
        assert plan_bundle.version == data["version"]
        assert plan_bundle.idea is not None
        assert plan_bundle.idea.title == "Developer Productivity CLI"
        assert len(plan_bundle.features) == 2
        assert plan_bundle.features[0].key == "FEATURE-001"
        assert len(plan_bundle.features[0].stories) == 2

    def test_validate_plan_bundle(self, sample_plan_path: Path):
        """Test validating a plan bundle with Pydantic."""
        data = load_yaml(sample_plan_path)

        # Parse to model
        idea = Idea(**data["idea"])
        business = Business(**data["business"])
        product = Product(**data["product"])
        features = [Feature(**f) for f in data["features"]]

        metadata = Metadata(**data.get("metadata", {})) if data.get("metadata") else None
        plan_bundle = PlanBundle(
            version=data["version"],
            idea=idea,
            business=business,
            product=product,
            features=features,
            metadata=metadata,
            clarifications=None,
        )

        # Use the validate_plan_bundle function
        report = validate_plan_bundle(plan_bundle)

        # Should pass validation
        assert report.passed is True
        assert len(report.deviations) == 0

    def test_validate_plan_bundle_from_json_path(self, sample_plan_path: Path, tmp_path: Path):
        """Ensure validate_plan_bundle accepts JSON plan bundles."""
        plan_data = load_yaml(sample_plan_path)
        json_path = tmp_path / "plan.bundle.json"
        json_path.write_text(json.dumps(plan_data), encoding="utf-8")

        is_valid, error, parsed = validate_plan_bundle(json_path)

        assert is_valid is True
        assert error is None
        assert parsed is not None
        assert parsed.idea is not None

    def test_validate_with_json_schema(self, sample_plan_path: Path, tmp_path: Path):
        """Test validating a plan bundle with JSON Schema."""
        # Load YAML
        data = load_yaml(sample_plan_path)

        # Create schema validator
        resources_dir = Path(__file__).parent.parent.parent / "resources"
        validator = SchemaValidator(resources_dir / "schemas")

        # Validate
        report = validator.validate_json_schema(data, "plan.schema.json")

        # Should pass validation
        assert report.passed is True
        assert len(report.deviations) == 0

    def test_roundtrip_plan_bundle(self, sample_plan_path: Path, tmp_path: Path):
        """Test loading, parsing, and saving a plan bundle."""
        # Load
        data = load_yaml(sample_plan_path)

        # Parse to model
        idea = Idea(**data["idea"])
        business = Business(**data["business"])
        product = Product(**data["product"])
        features = [Feature(**f) for f in data["features"]]

        metadata = Metadata(**data.get("metadata", {})) if data.get("metadata") else None
        plan_bundle = PlanBundle(
            version=data["version"],
            idea=idea,
            business=business,
            product=product,
            features=features,
            metadata=metadata,
            clarifications=None,
        )

        # Save using PlanGenerator (which updates version to current schema)
        from specfact_cli.generators.plan_generator import PlanGenerator

        output_path = tmp_path / "output-plan.yaml"
        generator = PlanGenerator()
        generator.generate(plan_bundle, output_path)

        # Reload
        reloaded_data = load_yaml(output_path)

        # Verify roundtrip (version updated to current schema version)
        from specfact_cli.migrations.plan_migrator import get_current_schema_version

        assert reloaded_data["version"] == get_current_schema_version()
        assert reloaded_data["idea"]["title"] == "Developer Productivity CLI"
        assert len(reloaded_data["features"]) == 2

    def test_invalid_plan_missing_required_fields(self):
        """Test that missing required fields raise validation errors."""
        with pytest.raises(ValidationError) as exc_info:
            PlanBundle(  # type: ignore[call-arg]
                version="1.0",
                # Missing idea (optional)
                # Missing business (optional)
                # Missing product (required)
                features=[],
            )

        # Should raise error for missing product
        assert "product" in str(exc_info.value).lower()

    def test_invalid_feature_confidence(self):
        """Test that invalid confidence values raise validation errors."""
        with pytest.raises(ValidationError):
            Feature(
                key="FEATURE-001",
                title="Invalid Feature",
                outcomes=["outcome"],
                acceptance=["criteria"],
                confidence=1.5,  # Invalid: > 1.0
            )

    def test_feature_with_stories(self, sample_plan_path: Path):
        """Test that features with stories are parsed correctly."""
        data = load_yaml(sample_plan_path)

        # Get first feature
        feature_data = data["features"][0]
        feature = Feature(**feature_data)

        # Verify stories
        assert len(feature.stories) == 2
        assert feature.stories[0].key == "STORY-001"
        assert feature.stories[1].key == "STORY-002"
        assert feature.stories[0].confidence == 0.9
        assert feature.stories[0].draft is False

    def test_business_model_with_all_fields(self, sample_plan_path: Path):
        """Test business model with all optional fields."""
        data = load_yaml(sample_plan_path)

        business = Business(**data["business"])

        # Verify all fields
        assert len(business.segments) == 2
        assert len(business.problems) == 2
        assert len(business.solutions) == 2
        assert len(business.differentiation) == 2
        assert len(business.risks) == 2

    def test_release_model(self, sample_plan_path: Path):
        """Test release model parsing."""
        data = load_yaml(sample_plan_path)

        product = Product(**data["product"])

        # Verify release
        assert len(product.releases) == 1
        release = product.releases[0]
        assert release.name == "v0.1.0 MVP"
        assert len(release.objectives) == 2
        assert len(release.scope) == 2
        assert len(release.risks) == 1


class TestPlanBundleEdgeCases:
    """Test edge cases and error handling."""

    def test_minimal_plan_bundle(self):
        """Test creating a minimal valid plan bundle."""
        product = Product(themes=["Core"], releases=[])
        plan_bundle = PlanBundle(
            version="1.0",
            idea=None,
            business=None,
            product=product,
            features=[],
            metadata=Metadata(
                stage="draft",
                promoted_at=None,
                promoted_by=None,
                analysis_scope=None,
                entry_point=None,
                summary=None,
            ),
            clarifications=None,
        )

        # Should be valid
        report = validate_plan_bundle(plan_bundle)
        assert report.passed is True

    def test_plan_bundle_with_idea_only(self):
        """Test plan bundle with only idea and product."""
        idea = Idea(title="Test Idea", narrative="Test narrative", metrics=None)
        product = Product(themes=["Core"], releases=[])

        plan_bundle = PlanBundle(
            version="1.0",
            idea=idea,
            product=product,
            features=[],
            business=None,
            metadata=Metadata(
                stage="draft",
                promoted_at=None,
                promoted_by=None,
                analysis_scope=None,
                entry_point=None,
                summary=None,
            ),
            clarifications=None,
        )

        # Should be valid
        report = validate_plan_bundle(plan_bundle)
        assert report.passed is True

    def test_story_with_tags(self):
        """Test story with tags."""
        story = Story(
            key="STORY-001",
            title="Test Story",
            acceptance=["Given", "When", "Then"],
            tags=["frontend", "critical"],
            confidence=0.8,
            story_points=None,
            value_points=None,
            scenarios=None,
            contracts=None,
        )

        assert len(story.tags) == 2
        assert "frontend" in story.tags

    def test_feature_without_stories(self):
        """Test feature without stories."""
        feature = Feature(
            key="FEATURE-001",
            title="Test Feature",
            outcomes=["outcome"],
            acceptance=["criteria"],
        )

        assert len(feature.stories) == 0
        assert feature.confidence == 1.0
        assert feature.draft is False

    def test_idea_with_metrics(self):
        """Test idea with metrics dictionary."""
        idea = Idea(
            title="Test Idea",
            narrative="Test narrative",
            metrics={
                "adoption_rate": "100/week",
                "satisfaction": "4.5/5",
                "retention": "80%",
            },
        )

        assert idea.metrics is not None
        assert "adoption_rate" in idea.metrics
        assert len(idea.metrics) == 3

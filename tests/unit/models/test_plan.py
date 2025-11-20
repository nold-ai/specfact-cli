"""
Unit tests for plan data models - Contract-First approach.

Pydantic models handle most validation (types, ranges, required fields).
Only edge cases and business logic validation are tested here.
"""

import pytest
from pydantic import ValidationError

from specfact_cli.models.plan import Business, Feature, Idea, PlanBundle, Product, Story


class TestStory:
    """Tests for Story model - edge cases only."""

    def test_story_confidence_validation_edge_cases(self):
        """Test Story confidence score validation - edge cases only.

        Pydantic Field(ge=0.0, le=1.0) handles range validation.
        This test verifies edge cases work correctly.

        Note: story_points and value_points are optional (Field(None, ...)).
        """
        # Valid boundaries
        story_min = Story(
            key="STORY-001", title="Test", confidence=0.0, story_points=None, value_points=None, scenarios=None
        )
        assert story_min.confidence == 0.0

        story_max = Story(
            key="STORY-002", title="Test", confidence=1.0, story_points=None, value_points=None, scenarios=None
        )
        assert story_max.confidence == 1.0

        # Invalid confidence (too high) - Pydantic validates
        with pytest.raises(ValidationError):
            Story(key="STORY-003", title="Test", confidence=1.5, story_points=None, value_points=None, scenarios=None)

        # Invalid confidence (negative) - Pydantic validates
        with pytest.raises(ValidationError):
            Story(key="STORY-004", title="Test", confidence=-0.1, story_points=None, value_points=None, scenarios=None)


class TestFeature:
    """Tests for Feature model - business logic only."""

    def test_feature_with_nested_stories(self):
        """Test Feature with nested stories - business logic validation.

        Note: story_points and value_points are optional (Field(None, ...)).
        """
        # Pydantic validates types and structure
        stories = [
            Story(key="STORY-001", title="Login", story_points=None, value_points=None, scenarios=None),
            Story(key="STORY-002", title="Logout", story_points=None, value_points=None, scenarios=None),
        ]

        feature = Feature(
            key="FEATURE-001",
            title="Authentication",
            outcomes=["Users can authenticate securely"],
            acceptance=["All auth flows work", "Security tests pass"],
            constraints=["Must use OAuth2"],
            stories=stories,
            confidence=0.9,
        )

        # Test business logic: nested relationships
        assert len(feature.stories) == 2
        assert feature.stories[0].key == "STORY-001"


class TestPlanBundle:
    """Tests for PlanBundle model - business logic only."""

    def test_plan_bundle_nested_relationships(self):
        """Test PlanBundle with nested relationships - business logic validation.

        Pydantic validates types and structure.
        This test verifies nested relationships work correctly.

        Note: idea and business are optional (Field(None, ...)), but we set them here.
        """
        idea = Idea(title="Test Idea", narrative="Test narrative", metrics=None)
        business = Business(segments=["Developers"])
        product = Product(themes=["Innovation"])
        features = [Feature(key="FEATURE-001", title="Feature 1")]

        bundle = PlanBundle(idea=idea, business=business, product=product, features=features, metadata=None)

        # Test business logic: nested relationships
        # Since we set idea and business, they should not be None
        assert bundle.idea is not None
        assert bundle.business is not None
        assert bundle.idea.title == "Test Idea"
        assert bundle.business.segments == ["Developers"]
        assert bundle.product.themes == ["Innovation"]
        assert len(bundle.features) == 1

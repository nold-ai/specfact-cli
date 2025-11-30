"""
Unit tests for plan bundle summary metadata.

Tests the PlanSummary model and PlanBundle.compute_summary() method.
"""

from specfact_cli.models.plan import Feature, PlanBundle, PlanSummary, Product, Story


class TestPlanSummary:
    """Tests for PlanSummary model."""

    def test_plan_summary_defaults(self):
        """Test PlanSummary with default values."""
        summary = PlanSummary(
            features_count=0,
            stories_count=0,
            themes_count=0,
            releases_count=0,
            content_hash=None,
            computed_at=None,
        )
        assert summary.features_count == 0
        assert summary.stories_count == 0
        assert summary.themes_count == 0
        assert summary.releases_count == 0
        assert summary.content_hash is None
        assert summary.computed_at is None

    def test_plan_summary_with_values(self):
        """Test PlanSummary with explicit values."""
        summary = PlanSummary(
            features_count=5,
            stories_count=10,
            themes_count=2,
            releases_count=1,
            content_hash="abc123",
            computed_at="2025-01-01T00:00:00",
        )
        assert summary.features_count == 5
        assert summary.stories_count == 10
        assert summary.themes_count == 2
        assert summary.releases_count == 1
        assert summary.content_hash == "abc123"
        assert summary.computed_at == "2025-01-01T00:00:00"


class TestPlanBundleSummary:
    """Tests for PlanBundle summary computation."""

    def test_compute_summary_basic(self):
        """Test computing summary for a basic plan bundle."""
        product = Product(themes=["Theme1", "Theme2"])
        features = [
            Feature(
                key="FEATURE-001",
                title="Feature 1",
                stories=[
                    Story(
                        key="STORY-001",
                        title="Story 1",
                        confidence=0.8,
                        story_points=None,
                        value_points=None,
                        scenarios=None,
                        contracts=None,
                    )
                ],
                source_tracking=None,
                contract=None,
                protocol=None,
            ),
            Feature(
                key="FEATURE-002",
                title="Feature 2",
                stories=[
                    Story(
                        key="STORY-002",
                        title="Story 2",
                        confidence=0.9,
                        story_points=None,
                        value_points=None,
                        scenarios=None,
                        contracts=None,
                    )
                ],
                source_tracking=None,
                contract=None,
                protocol=None,
            ),
        ]

        bundle = PlanBundle(
            product=product, features=features, idea=None, business=None, metadata=None, clarifications=None
        )
        summary = bundle.compute_summary(include_hash=False)

        assert summary.features_count == 2
        assert summary.stories_count == 2
        assert summary.themes_count == 2
        assert summary.releases_count == 0
        assert summary.content_hash is None
        assert summary.computed_at is not None

    def test_compute_summary_with_hash(self):
        """Test computing summary with content hash."""
        product = Product(themes=["Theme1"])
        features = [Feature(key="FEATURE-001", title="Feature 1", source_tracking=None, contract=None, protocol=None)]

        bundle = PlanBundle(
            product=product, features=features, idea=None, business=None, metadata=None, clarifications=None
        )
        summary = bundle.compute_summary(include_hash=True)

        assert summary.features_count == 1
        assert summary.content_hash is not None
        assert len(summary.content_hash) == 64  # SHA256 hex length

    def test_update_summary(self):
        """Test updating summary in plan bundle metadata."""
        product = Product(themes=["Theme1"])
        features = [Feature(key="FEATURE-001", title="Feature 1", source_tracking=None, contract=None, protocol=None)]

        bundle = PlanBundle(
            product=product, features=features, idea=None, business=None, metadata=None, clarifications=None
        )
        assert bundle.metadata is None

        bundle.update_summary(include_hash=False)
        assert bundle.metadata is not None
        assert bundle.metadata.summary is not None
        assert bundle.metadata.summary.features_count == 1
        assert bundle.metadata.summary.stories_count == 0

    def test_update_summary_existing_metadata(self):
        """Test updating summary when metadata already exists."""
        from specfact_cli.models.plan import Metadata

        product = Product(themes=["Theme1"])
        features = [
            Feature(
                key="FEATURE-001",
                title="Feature 1",
                stories=[
                    Story(
                        key="STORY-001",
                        title="Story 1",
                        confidence=0.8,
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
        ]

        bundle = PlanBundle(
            product=product,
            features=features,
            idea=None,
            business=None,
            metadata=Metadata(
                stage="draft",
                promoted_at=None,
                promoted_by=None,
                analysis_scope=None,
                entry_point=None,
                external_dependencies=[],
                summary=None,
            ),
            clarifications=None,
        )

        bundle.update_summary(include_hash=False)
        assert bundle.metadata is not None
        assert bundle.metadata.summary is not None
        assert bundle.metadata.summary.features_count == 1
        assert bundle.metadata.summary.stories_count == 1

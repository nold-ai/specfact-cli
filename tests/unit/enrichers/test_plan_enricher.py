"""Unit tests for PlanEnricher."""

from __future__ import annotations

import pytest

from specfact_cli.enrichers.plan_enricher import PlanEnricher
from specfact_cli.models.plan import Feature, PlanBundle, Product, Story


class TestPlanEnricher:
    """Test PlanEnricher class."""

    @pytest.fixture
    def enricher(self) -> PlanEnricher:
        """Create PlanEnricher instance."""
        return PlanEnricher()

    @pytest.fixture
    def sample_plan_bundle(self) -> PlanBundle:
        """Create a sample plan bundle with vague acceptance criteria."""
        return PlanBundle(
            product=Product(),
            idea=None,
            business=None,
            metadata=None,
            clarifications=None,
            features=[
                Feature(
                    key="FEATURE-001",
                    title="User Authentication",
                    outcomes=["System MUST Helper class"],
                    source_tracking=None,
                    contract=None,
                    protocol=None,
                    stories=[
                        Story(
                            key="STORY-001",
                            title="Login functionality",
                            acceptance=["is implemented", "works"],
                            tasks=["Implement login"],
                            story_points=None,
                            value_points=None,
                            scenarios=None,
                            contracts=None,
                        ),
                        Story(
                            key="STORY-002",
                            title="Logout functionality",
                            acceptance=["is functional"],
                            tasks=["Create logout"],
                            story_points=None,
                            value_points=None,
                            scenarios=None,
                            contracts=None,
                        ),
                    ],
                ),
            ],
        )

    def test_enrich_plan_updates_vague_criteria(self, enricher: PlanEnricher, sample_plan_bundle: PlanBundle) -> None:
        """Test that enrichment updates vague acceptance criteria."""
        summary = enricher.enrich_plan(sample_plan_bundle)

        assert summary["features_updated"] > 0
        assert summary["stories_updated"] > 0
        assert summary["acceptance_criteria_enhanced"] > 0

        # Verify acceptance criteria were enhanced
        story = sample_plan_bundle.features[0].stories[0]
        assert len(story.acceptance) > 0
        # Should not be vague anymore
        assert "is implemented" not in story.acceptance[0].lower()
        assert "works" not in story.acceptance[1].lower()

    def test_enrichment_does_not_generate_gwt_format(
        self, enricher: PlanEnricher, sample_plan_bundle: PlanBundle
    ) -> None:
        """Test that enrichment does not generate GWT format (Given/When/Then)."""
        enricher.enrich_plan(sample_plan_bundle)

        # Check all stories for GWT format
        for feature in sample_plan_bundle.features:
            for story in feature.stories:
                for acceptance in story.acceptance:
                    acceptance_lower = acceptance.lower()
                    # Should not contain GWT keywords together
                    has_gwt = "given" in acceptance_lower and "when" in acceptance_lower and "then" in acceptance_lower
                    assert not has_gwt, f"Story {story.key} should not have GWT format. Found: {acceptance}"

    def test_enrichment_uses_simple_text_format(self, enricher: PlanEnricher, sample_plan_bundle: PlanBundle) -> None:
        """Test that enrichment uses simple text format (Must verify...)."""
        enricher.enrich_plan(sample_plan_bundle)

        # Check that enriched criteria use simple text format
        for feature in sample_plan_bundle.features:
            for story in feature.stories:
                for acceptance in story.acceptance:
                    acceptance_lower = acceptance.lower()
                    # Should use "Must verify" or similar testable keywords
                    has_testable_keyword = any(
                        keyword in acceptance_lower
                        for keyword in ["must verify", "must", "should", "verify", "validate", "check"]
                    )
                    assert has_testable_keyword, (
                        f"Story {story.key} acceptance criteria should use testable format. Found: {acceptance}"
                    )

    def test_enrichment_preserves_code_specific_criteria(self, enricher: PlanEnricher) -> None:
        """Test that code-specific acceptance criteria are preserved unchanged."""
        plan_bundle = PlanBundle(
            product=Product(),
            idea=None,
            business=None,
            metadata=None,
            clarifications=None,
            features=[
                Feature(
                    key="FEATURE-001",
                    title="User Authentication",
                    source_tracking=None,
                    contract=None,
                    protocol=None,
                    stories=[
                        Story(
                            key="STORY-001",
                            title="Login functionality",
                            acceptance=[
                                "Must verify login(username: str, password: str) -> bool works correctly",
                                "Must verify UserManager.create_user() returns bool",
                            ],
                            story_points=None,
                            value_points=None,
                            scenarios=None,
                            contracts=None,
                        ),
                    ],
                ),
            ],
        )

        original_acceptance = plan_bundle.features[0].stories[0].acceptance.copy()
        enricher.enrich_plan(plan_bundle)

        # Code-specific criteria should be preserved
        enriched_acceptance = plan_bundle.features[0].stories[0].acceptance
        assert enriched_acceptance == original_acceptance

    def test_enrichment_converts_existing_gwt_to_simple_text(self, enricher: PlanEnricher) -> None:
        """Test that existing GWT format is converted to simple text format."""
        plan_bundle = PlanBundle(
            product=Product(),
            idea=None,
            business=None,
            metadata=None,
            clarifications=None,
            features=[
                Feature(
                    key="FEATURE-001",
                    title="User Authentication",
                    source_tracking=None,
                    contract=None,
                    protocol=None,
                    stories=[
                        Story(
                            key="STORY-001",
                            title="Login functionality",
                            acceptance=[
                                "Given a user wants to login, When they enter credentials, Then login is successful",
                            ],
                            story_points=None,
                            value_points=None,
                            scenarios=None,
                            contracts=None,
                        ),
                    ],
                ),
            ],
        )

        enricher.enrich_plan(plan_bundle)

        # Should convert GWT to simple text
        acceptance = plan_bundle.features[0].stories[0].acceptance[0]
        acceptance_lower = acceptance.lower()
        has_gwt = "given" in acceptance_lower and "when" in acceptance_lower and "then" in acceptance_lower
        assert not has_gwt, f"GWT format should be converted. Found: {acceptance}"
        # Should use simple text format
        assert "must verify" in acceptance_lower or "must" in acceptance_lower

    def test_enrichment_handles_vague_patterns(self, enricher: PlanEnricher) -> None:
        """Test that enrichment handles various vague patterns correctly."""
        vague_patterns = [
            "is implemented",
            "is functional",
            "works",
            "is done",
            "is complete",
            "is ready",
        ]

        for pattern in vague_patterns:
            plan_bundle = PlanBundle(
                product=Product(),
                idea=None,
                business=None,
                metadata=None,
                clarifications=None,
                features=[
                    Feature(
                        key="FEATURE-001",
                        title="Test Feature",
                        source_tracking=None,
                        contract=None,
                        protocol=None,
                        stories=[
                            Story(
                                key="STORY-001",
                                title="Test Story",
                                acceptance=[pattern],
                                story_points=None,
                                value_points=None,
                                scenarios=None,
                                contracts=None,
                            ),
                        ],
                    ),
                ],
            )

            enricher.enrich_plan(plan_bundle)

            acceptance = plan_bundle.features[0].stories[0].acceptance[0]
            # Should be enhanced (not the original vague pattern)
            assert pattern not in acceptance.lower() or "must verify" in acceptance.lower()
            # Should not be GWT format
            acceptance_lower = acceptance.lower()
            has_gwt = "given" in acceptance_lower and "when" in acceptance_lower and "then" in acceptance_lower
            assert not has_gwt, f"Pattern '{pattern}' should not generate GWT. Found: {acceptance}"

    def test_enrichment_summary_includes_changes(self, enricher: PlanEnricher, sample_plan_bundle: PlanBundle) -> None:
        """Test that enrichment summary includes change details."""
        summary = enricher.enrich_plan(sample_plan_bundle)

        assert "changes" in summary
        assert len(summary["changes"]) > 0
        # Changes should describe what was enhanced
        assert any("Enhanced acceptance criteria" in change for change in summary["changes"])

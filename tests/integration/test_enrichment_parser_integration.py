"""Integration tests for enrichment parser with stories."""

from __future__ import annotations

from pathlib import Path

from specfact_cli.models.plan import Idea, PlanBundle, Product
from specfact_cli.utils.enrichment_parser import EnrichmentParser, apply_enrichment


class TestEnrichmentParserIntegration:
    """Integration tests for enrichment parser pipeline with stories."""

    def test_parse_and_apply_enrichment_with_stories(self, tmp_path: Path):
        """Test parsing enrichment report with stories and applying to plan bundle."""
        # Create enrichment report with stories
        report_content = """# Enrichment Report

## Missing Features

1. **User Authentication** (Key: FEATURE-USER-AUTHENTICATION)
   - Confidence: 0.85
   - Outcomes: User registration, login, profile management
   - Stories:
     1. User can sign up for new account
        - Acceptance: sign_up view processes POST requests, creates User and UserProfile automatically, user is automatically logged in after signup, redirects to profile page after signup
     2. User can log in with credentials
        - Acceptance: log_in view authenticates username/password, on success user is logged in and redirected to dash, on failure error message is displayed
"""
        report_file = tmp_path / "enrichment.md"
        report_file.write_text(report_content)

        # Create initial plan bundle
        plan_bundle = PlanBundle(
            version="1.0",
            idea=Idea(title="Test", narrative="Test narrative", metrics=None),
            product=Product(themes=["Test"]),
            features=[],
            business=None,
            metadata=None,
            clarifications=None,
        )

        # Parse enrichment report
        parser = EnrichmentParser()
        enrichment = parser.parse(report_file)

        # Verify parsing
        assert len(enrichment.missing_features) == 1
        feature_data = enrichment.missing_features[0]
        assert feature_data["key"] == "FEATURE-USER-AUTHENTICATION"
        assert feature_data["title"] == "User Authentication"
        assert len(feature_data["stories"]) == 2

        # Verify stories were parsed correctly
        story1 = feature_data["stories"][0]
        assert story1["title"] == "User can sign up for new account"
        assert len(story1["acceptance"]) >= 4

        story2 = feature_data["stories"][1]
        assert story2["title"] == "User can log in with credentials"
        assert len(story2["acceptance"]) >= 3

        # Apply enrichment
        enriched = apply_enrichment(plan_bundle, enrichment)

        # Verify enriched bundle
        assert len(enriched.features) == 1
        feature = enriched.features[0]
        assert feature.key == "FEATURE-USER-AUTHENTICATION"
        assert feature.title == "User Authentication"
        assert len(feature.stories) == 2

        # Verify stories were added correctly
        assert feature.stories[0].title == "User can sign up for new account"
        assert len(feature.stories[0].acceptance) >= 4
        assert feature.stories[1].title == "User can log in with credentials"
        assert len(feature.stories[1].acceptance) >= 3

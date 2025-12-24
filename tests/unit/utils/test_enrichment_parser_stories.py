"""Unit tests for enrichment parser with stories format."""

from __future__ import annotations

from pathlib import Path

from specfact_cli.utils.enrichment_parser import EnrichmentParser


class TestEnrichmentParserStories:
    """Test EnrichmentParser with enrichment reports containing stories."""

    def test_parse_enrichment_report_with_stories(self, tmp_path: Path):
        """Test parsing enrichment report with features containing stories and acceptance criteria."""
        # Create test enrichment report with stories format
        report_content = """# Enrichment Report

## Missing Features

1. **User Authentication** (Key: FEATURE-USER-AUTHENTICATION)
   - Confidence: 0.85
   - Outcomes: User registration, login, profile management, authentication system
   - Stories:
     1. User can sign up for new account
        - Acceptance: sign_up view processes POST requests, creates User and UserProfile automatically, user is automatically logged in after signup, redirects to profile page after signup
     2. User can log in with credentials
        - Acceptance: log_in view authenticates username/password, on success user is logged in and redirected to dash, on failure error message is displayed

2. **Notes Management** (Key: FEATURE-NOTES-MANAGEMENT)
   - Confidence: 0.85
   - Outcomes: Messaging system, dashboard with conversations
   - Stories:
     1. User can view dashboard with latest notes
        - Acceptance: dash view shows latest note from each conversation, dashboard includes all users who have exchanged notes with current user

## Business Context

- Priority: Core application for user management
- Constraint: Must support authentication and messaging features
"""
        report_file = tmp_path / "enrichment.md"
        report_file.write_text(report_content)

        parser = EnrichmentParser()
        report = parser.parse(report_file)

        # Verify features were parsed
        assert len(report.missing_features) == 2

        # Verify first feature
        feature1 = report.missing_features[0]
        assert feature1["key"] == "FEATURE-USER-AUTHENTICATION"
        assert feature1["title"] == "User Authentication"
        assert feature1["confidence"] == 0.85
        assert len(feature1["outcomes"]) > 0
        assert len(feature1["stories"]) == 2

        # Verify first story
        story1 = feature1["stories"][0]
        assert story1["title"] == "User can sign up for new account"
        assert len(story1["acceptance"]) >= 4  # Should have multiple acceptance criteria
        assert "sign_up view processes POST requests" in story1["acceptance"][0]

        # Verify second feature
        feature2 = report.missing_features[1]
        assert feature2["key"] == "FEATURE-NOTES-MANAGEMENT"
        assert feature2["title"] == "Notes Management"
        assert len(feature2["stories"]) == 1

        # Verify business context
        assert len(report.business_context["priorities"]) > 0
        assert len(report.business_context["constraints"]) > 0

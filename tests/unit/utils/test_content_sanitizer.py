"""
Unit tests for content sanitizer utility.

Tests content sanitization rules and auto-detection logic.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from beartype import beartype

from specfact_cli.utils.content_sanitizer import ContentSanitizer


@pytest.fixture
def sanitizer() -> ContentSanitizer:
    """Create content sanitizer instance for testing."""
    return ContentSanitizer()


class TestContentSanitizer:
    """Test content sanitizer implementation."""

    @beartype
    def test_sanitize_removes_competitive_analysis(self, sanitizer: ContentSanitizer) -> None:
        """Test that competitive analysis sections are removed."""
        content = """
## Why

This change improves our competitive position.

## Competitive Analysis

Our main competitor X does Y, but we do Z better.

## What Changes

- New feature added
"""
        sanitized = sanitizer.sanitize_proposal(content)
        assert "Competitive Analysis" not in sanitized
        assert "competitor" not in sanitized.lower()

    @beartype
    def test_sanitize_removes_implementation_details(self, sanitizer: ContentSanitizer) -> None:
        """Test that implementation details are removed."""
        content = """
## Why

User needs this feature.

## Implementation Details

- File: src/models/change.py
- File: src/adapters/github.py
- Effort: 10 hours
- Timeline: 2 weeks

## What Changes

- New feature added
"""
        sanitized = sanitizer.sanitize_proposal(content)
        assert "Implementation Details" not in sanitized
        assert "File:" not in sanitized
        assert "Effort:" not in sanitized
        assert "Timeline:" not in sanitized

    @beartype
    def test_sanitize_preserves_user_facing_content(self, sanitizer: ContentSanitizer) -> None:
        """Test that user-facing content is preserved."""
        content = """
## Why

Users need this feature to improve their workflow.

## What Changes

- New feature that helps users
- Better user experience
- Acceptance criteria: Users can do X

## External Documentation

See https://example.com/docs for more info.
"""
        sanitized = sanitizer.sanitize_proposal(content)
        assert "Users need" in sanitized
        assert "New feature" in sanitized
        assert "Acceptance criteria" in sanitized
        assert "https://example.com/docs" in sanitized

    @beartype
    def test_detect_sanitization_need_user_preference_true(self, sanitizer: ContentSanitizer) -> None:
        """Test that user preference=True forces sanitization."""
        assert sanitizer.detect_sanitization_need(user_preference=True) is True

    @beartype
    def test_detect_sanitization_need_user_preference_false(self, sanitizer: ContentSanitizer) -> None:
        """Test that user preference=False disables sanitization."""
        assert sanitizer.detect_sanitization_need(user_preference=False) is False

    @beartype
    def test_detect_sanitization_need_different_repos(self, sanitizer: ContentSanitizer, tmp_path: Path) -> None:
        """Test that different repos trigger sanitization."""
        code_repo = tmp_path / "code"
        planning_repo = tmp_path / "planning"
        code_repo.mkdir()
        planning_repo.mkdir()

        assert sanitizer.detect_sanitization_need(code_repo=code_repo, planning_repo=planning_repo) is True

    @beartype
    def test_detect_sanitization_need_same_repo(self, sanitizer: ContentSanitizer, tmp_path: Path) -> None:
        """Test that same repo disables sanitization."""
        same_repo = tmp_path / "repo"
        same_repo.mkdir()

        assert sanitizer.detect_sanitization_need(code_repo=same_repo, planning_repo=same_repo) is False

    @beartype
    def test_detect_sanitization_need_none_repos(self, sanitizer: ContentSanitizer) -> None:
        """Test that None repos default to sanitize (safety)."""
        assert sanitizer.detect_sanitization_need() is True

    @beartype
    def test_sanitize_cleans_whitespace(self, sanitizer: ContentSanitizer) -> None:
        """Test that extra whitespace is cleaned up."""
        content = "## Why\n\n\n\nContent\n\n\n\n## What\n\n\n\nMore content"
        sanitized = sanitizer.sanitize_proposal(content)
        # Should not have more than 2 consecutive newlines
        assert "\n\n\n" not in sanitized

    @beartype
    def test_sanitize_empty_content(self, sanitizer: ContentSanitizer) -> None:
        """Test that empty content is handled gracefully."""
        content = ""
        sanitized = sanitizer.sanitize_proposal(content)
        assert isinstance(sanitized, str)

"""
Unit tests for BacklogItem domain model.

Tests BacklogItem creation, refinement state tracking, and property calculations.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from beartype import beartype

from specfact_cli.models.backlog_item import BacklogItem
from specfact_cli.models.source_tracking import SourceTracking


class TestBacklogItem:
    """Test BacklogItem domain model."""

    @beartype
    def test_create_backlog_item_minimal(self) -> None:
        """Test creating BacklogItem with minimal required fields."""
        item = BacklogItem(
            id="123",
            provider="github",
            url="https://github.com/test/repo/issues/123",
            title="Test Issue",
            state="open",
        )

        assert item.id == "123"
        assert item.provider == "github"
        assert item.url == "https://github.com/test/repo/issues/123"
        assert item.title == "Test Issue"
        assert item.state == "open"
        assert item.body_markdown == ""
        assert item.assignees == []
        assert item.tags == []

    @beartype
    def test_create_backlog_item_full(self) -> None:
        """Test creating BacklogItem with all fields."""
        source_tracking = SourceTracking(tool="github", source_metadata={"source_id": "123"})
        created_at = datetime.now(UTC)
        updated_at = datetime.now(UTC)

        item = BacklogItem(
            id="123",
            provider="github",
            url="https://github.com/test/repo/issues/123",
            title="Test Issue",
            body_markdown="Issue body content",
            state="open",
            assignees=["user1", "user2"],
            tags=["bug", "priority"],
            iteration="Sprint 1",
            sprint="Sprint 1",
            release="Release 1.0",
            area="Backend",
            created_at=created_at,
            updated_at=updated_at,
            source_tracking=source_tracking,
            provider_fields={"number": "123", "comments": 5},
        )

        assert item.id == "123"
        assert item.body_markdown == "Issue body content"
        assert item.assignees == ["user1", "user2"]
        assert item.tags == ["bug", "priority"]
        assert item.iteration == "Sprint 1"
        assert item.sprint == "Sprint 1"
        assert item.release == "Release 1.0"
        assert item.area == "Backend"
        assert item.source_tracking == source_tracking

    @beartype
    def test_create_backlog_item_with_sprint_release(self) -> None:
        """Test creating BacklogItem with sprint and release fields."""
        item = BacklogItem(
            id="456",
            provider="github",
            url="https://github.com/test/repo/issues/456",
            title="Test Issue",
            state="open",
            sprint="Sprint 2",
            release="Release 2.0",
        )

        assert item.sprint == "Sprint 2"
        assert item.release == "Release 2.0"
        assert item.iteration is None  # Can be None if not set

    @beartype
    def test_needs_refinement_no_template(self) -> None:
        """Test needs_refinement when no template detected."""
        item = BacklogItem(
            id="123",
            provider="github",
            url="https://github.com/test/repo/issues/123",
            title="Test Issue",
            state="open",
        )

        assert item.needs_refinement is True

    @beartype
    def test_needs_refinement_low_confidence(self) -> None:
        """Test needs_refinement when confidence is low."""
        item = BacklogItem(
            id="123",
            provider="github",
            url="https://github.com/test/repo/issues/123",
            title="Test Issue",
            state="open",
            detected_template="user_story_v1",
            template_confidence=0.5,  # Below 0.6 threshold
        )

        assert item.needs_refinement is True

    @beartype
    def test_needs_refinement_high_confidence(self) -> None:
        """Test needs_refinement when confidence is high."""
        item = BacklogItem(
            id="123",
            provider="github",
            url="https://github.com/test/repo/issues/123",
            title="Test Issue",
            state="open",
            detected_template="user_story_v1",
            template_confidence=0.8,  # Above 0.6 threshold
        )

        assert item.needs_refinement is False

    @beartype
    def test_apply_refinement(self) -> None:
        """Test applying refinement to backlog item."""
        item = BacklogItem(
            id="123",
            provider="github",
            url="https://github.com/test/repo/issues/123",
            title="Test Issue",
            body_markdown="Original body",
            state="open",
        )

        item.refined_body = "Refined body content"
        item.apply_refinement()

        assert item.body_markdown == "Refined body content"
        assert item.refinement_applied is True
        assert item.refinement_timestamp is not None

    @beartype
    def test_apply_refinement_empty_body_raises(self) -> None:
        """Test that applying refinement with empty body raises error."""
        from icontract.errors import ViolationError

        item = BacklogItem(
            id="123",
            provider="github",
            url="https://github.com/test/repo/issues/123",
            title="Test Issue",
            state="open",
        )

        item.refined_body = ""

        with pytest.raises(ViolationError, match="Refined body must be non-empty"):
            item.apply_refinement()

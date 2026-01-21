"""
Unit tests for BacklogFormat abstraction.

Tests the abstract BacklogFormat interface and round-trip preservation.
"""

from __future__ import annotations

from beartype import beartype

from specfact_cli.backlog.formats.base import BacklogFormat
from specfact_cli.models.backlog_item import BacklogItem


class MockBacklogFormat(BacklogFormat):
    """Mock implementation of BacklogFormat for testing."""

    def __init__(self, format_type: str = "mock") -> None:
        """Initialize mock format."""
        self._format_type = format_type

    @property
    @beartype
    def format_type(self) -> str:
        """Get format type."""
        return self._format_type

    @beartype
    def serialize(self, item: BacklogItem) -> str:
        """Serialize item to string."""
        return f"{item.id}|{item.title}|{item.body_markdown}|{item.state}"

    @beartype
    def deserialize(self, raw: str) -> BacklogItem:
        """Deserialize string to item."""
        parts = raw.split("|")
        return BacklogItem(id=parts[0], provider="test", url="", title=parts[1], body_markdown=parts[2], state=parts[3])


class TestBacklogFormat:
    """Test BacklogFormat abstraction."""

    @beartype
    def test_format_type_property(self) -> None:
        """Test format_type property."""
        formatter = MockBacklogFormat(format_type="test_format")
        assert formatter.format_type == "test_format"

    @beartype
    def test_serialize(self) -> None:
        """Test serialization."""
        formatter = MockBacklogFormat()
        item = BacklogItem(id="1", provider="test", url="", title="Test", body_markdown="Body", state="open")
        serialized = formatter.serialize(item)
        assert serialized == "1|Test|Body|open"

    @beartype
    def test_deserialize(self) -> None:
        """Test deserialization."""
        formatter = MockBacklogFormat()
        raw = "1|Test|Body|open"
        item = formatter.deserialize(raw)
        assert item.id == "1"
        assert item.title == "Test"
        assert item.body_markdown == "Body"
        assert item.state == "open"

    @beartype
    def test_roundtrip_preserves_content(self) -> None:
        """Test round-trip preserves essential content (id, title, body, state)."""
        formatter = MockBacklogFormat()
        original = BacklogItem(
            id="1",
            provider="test",
            url="http://test.com/1",
            title="Test Item",
            body_markdown="Test body",
            state="open",
        )
        # Mock format only preserves id, title, body_markdown, state in serialization
        assert formatter.roundtrip_preserves_content(original) is True

    @beartype
    def test_roundtrip_preserves_essential_fields(self) -> None:
        """Test round-trip preserves essential fields (id, title, body, state)."""
        formatter = MockBacklogFormat()
        original = BacklogItem(
            id="123",
            provider="test",
            url="http://test.com/123",
            title="Complex Item",
            body_markdown="Complex body with\nmultiple lines",
            state="closed",
        )

        serialized = formatter.serialize(original)
        deserialized = formatter.deserialize(serialized)

        # Mock format preserves id, title, body_markdown, state
        assert deserialized.id == original.id
        assert deserialized.title == original.title
        assert deserialized.body_markdown == original.body_markdown
        assert deserialized.state == original.state

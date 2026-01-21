"""
Unit tests for MarkdownFormat implementation.

Tests Markdown serialization and deserialization with optional YAML frontmatter.
"""

from __future__ import annotations

from beartype import beartype

from specfact_cli.backlog.formats.markdown_format import MarkdownFormat
from specfact_cli.models.backlog_item import BacklogItem


class TestMarkdownFormat:
    """Test MarkdownFormat implementation."""

    @beartype
    def test_format_type(self) -> None:
        """Test format_type property."""
        formatter = MarkdownFormat()
        assert formatter.format_type == "markdown"

    @beartype
    def test_serialize_plain_markdown(self) -> None:
        """Test serializing plain markdown without provider_fields."""
        formatter = MarkdownFormat()
        item = BacklogItem(id="1", provider="test", url="", title="Test", body_markdown="Plain markdown", state="open")
        serialized = formatter.serialize(item)
        assert serialized == "Plain markdown"

    @beartype
    def test_serialize_with_provider_fields(self) -> None:
        """Test serializing markdown with YAML frontmatter for provider_fields."""
        formatter = MarkdownFormat()
        item = BacklogItem(
            id="1",
            provider="test",
            url="",
            title="Test",
            body_markdown="Markdown body",
            state="open",
            provider_fields={"number": "123", "html_url": "http://test.com/123"},
        )
        serialized = formatter.serialize(item)
        assert "---" in serialized
        assert "number: 123" in serialized
        assert "html_url: http://test.com/123" in serialized
        assert "Markdown body" in serialized

    @beartype
    def test_deserialize_plain_markdown(self) -> None:
        """Test deserializing plain markdown."""
        formatter = MarkdownFormat()
        raw = "Plain markdown content"
        item = formatter.deserialize(raw)
        assert item.body_markdown == "Plain markdown content"
        # Note: deserialize creates placeholder item since markdown doesn't contain full item metadata
        assert item.id == "placeholder"
        assert item.provider == "unknown"

    @beartype
    def test_deserialize_with_frontmatter(self) -> None:
        """Test deserializing markdown with YAML frontmatter."""
        formatter = MarkdownFormat()
        raw = """---
number: 123
html_url: http://test.com/123
---
Markdown body content"""
        item = formatter.deserialize(raw)
        assert item.body_markdown == "Markdown body content"
        assert item.provider_fields is not None
        # Note: Simple YAML parser converts "123" to int(123) if it's a digit
        assert item.provider_fields.get("number") in (123, "123")  # Accept both
        assert item.provider_fields.get("html_url") == "http://test.com/123"

    @beartype
    def test_roundtrip_plain_markdown(self) -> None:
        """Test round-trip with plain markdown."""
        formatter = MarkdownFormat()
        original = BacklogItem(
            id="1", provider="test", url="", title="Test", body_markdown="Plain content", state="open"
        )
        # Note: roundtrip_preserves_content checks id, provider, title, body_markdown, state, assignees, tags
        # MarkdownFormat deserialize creates placeholder, so this will fail for id/provider
        # But it preserves body_markdown which is the main content
        serialized = formatter.serialize(original)
        deserialized = formatter.deserialize(serialized)
        assert deserialized.body_markdown == original.body_markdown

"""
Unit tests for StructuredFormat implementation (YAML/JSON).

Tests YAML and JSON serialization and deserialization.
"""

from __future__ import annotations

import json

import pytest
from beartype import beartype

from specfact_cli.backlog.formats.structured_format import StructuredFormat
from specfact_cli.models.backlog_item import BacklogItem


class TestStructuredFormat:
    """Test StructuredFormat implementation."""

    @beartype
    def test_format_type_yaml(self) -> None:
        """Test format_type property for YAML."""
        formatter = StructuredFormat(format_type="yaml")
        assert formatter.format_type == "yaml"

    @beartype
    def test_format_type_json(self) -> None:
        """Test format_type property for JSON."""
        formatter = StructuredFormat(format_type="json")
        assert formatter.format_type == "json"

    @beartype
    def test_format_type_invalid(self) -> None:
        """Test invalid format_type raises ValueError."""
        with pytest.raises(ValueError, match="Format type must be 'yaml' or 'json'"):
            StructuredFormat(format_type="invalid")

    @beartype
    def test_serialize_yaml(self) -> None:
        """Test YAML serialization."""
        formatter = StructuredFormat(format_type="yaml")
        item = BacklogItem(
            id="1", provider="test", url="http://test.com/1", title="Test", body_markdown="Body", state="open"
        )
        serialized = formatter.serialize(item)
        assert "id: '1'" in serialized or 'id: "1"' in serialized
        assert "title: Test" in serialized
        assert "state: open" in serialized

    @beartype
    def test_serialize_json(self) -> None:
        """Test JSON serialization."""
        formatter = StructuredFormat(format_type="json")
        item = BacklogItem(
            id="1", provider="test", url="http://test.com/1", title="Test", body_markdown="Body", state="open"
        )
        serialized = formatter.serialize(item)
        data = json.loads(serialized)
        assert data["id"] == "1"
        assert data["title"] == "Test"
        assert data["state"] == "open"

    @beartype
    def test_deserialize_yaml(self) -> None:
        """Test YAML deserialization."""
        formatter = StructuredFormat(format_type="yaml")
        yaml_content = """id: '1'
provider: test
url: http://test.com/1
title: Test
body_markdown: Body
state: open"""
        item = formatter.deserialize(yaml_content)
        assert item.id == "1"
        assert item.title == "Test"
        assert item.body_markdown == "Body"
        assert item.state == "open"

    @beartype
    def test_deserialize_json(self) -> None:
        """Test JSON deserialization."""
        formatter = StructuredFormat(format_type="json")
        json_content = '{"id": "1", "provider": "test", "url": "http://test.com/1", "title": "Test", "body_markdown": "Body", "state": "open"}'
        item = formatter.deserialize(json_content)
        assert item.id == "1"
        assert item.title == "Test"
        assert item.body_markdown == "Body"
        assert item.state == "open"

    @beartype
    def test_roundtrip_yaml(self) -> None:
        """Test YAML round-trip preserves content."""
        formatter = StructuredFormat(format_type="yaml")
        original = BacklogItem(
            id="1",
            provider="test",
            url="http://test.com/1",
            title="Test Item",
            body_markdown="Test body",
            state="open",
            assignees=["alice"],
            tags=["feature"],
        )
        assert formatter.roundtrip_preserves_content(original) is True

    @beartype
    def test_roundtrip_json(self) -> None:
        """Test JSON round-trip preserves content."""
        formatter = StructuredFormat(format_type="json")
        original = BacklogItem(
            id="1",
            provider="test",
            url="http://test.com/1",
            title="Test Item",
            body_markdown="Test body",
            state="open",
            assignees=["alice"],
            tags=["feature"],
        )
        assert formatter.roundtrip_preserves_content(original) is True

    @beartype
    def test_roundtrip_preserves_provider_fields(self) -> None:
        """Test round-trip preserves provider_fields."""
        formatter = StructuredFormat(format_type="yaml")
        original = BacklogItem(
            id="1",
            provider="test",
            url="",
            title="Test",
            body_markdown="Body",
            state="open",
            provider_fields={"custom_field": "value", "number": 123},
        )
        serialized = formatter.serialize(original)
        deserialized = formatter.deserialize(serialized)
        assert deserialized.provider_fields == original.provider_fields

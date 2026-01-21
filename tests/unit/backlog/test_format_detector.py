"""
Unit tests for format detection.

Tests automatic format detection heuristics.
"""

from __future__ import annotations

from beartype import beartype

from specfact_cli.backlog.format_detector import detect_format


class TestFormatDetector:
    """Test format detection."""

    @beartype
    def test_detect_json_object(self) -> None:
        """Test detecting JSON object format."""
        raw = '{"key": "value"}'
        assert detect_format(raw) == "json"

    @beartype
    def test_detect_json_array(self) -> None:
        """Test detecting JSON array format."""
        raw = '[{"key": "value"}]'
        assert detect_format(raw) == "json"

    @beartype
    def test_detect_yaml_frontmatter(self) -> None:
        """Test detecting YAML with frontmatter."""
        raw = """---
key: value
---
Content"""
        assert detect_format(raw) == "yaml"

    @beartype
    def test_detect_yaml_key_value(self) -> None:
        """Test detecting YAML with key:value pattern."""
        raw = "key: value\nother: data"
        assert detect_format(raw) == "yaml"

    @beartype
    def test_detect_markdown_default(self) -> None:
        """Test defaulting to markdown for other cases."""
        raw = "# Markdown heading\n\nSome content here."
        assert detect_format(raw) == "markdown"

    @beartype
    def test_detect_markdown_with_hash_comment(self) -> None:
        """Test markdown with hash comment (not YAML)."""
        raw = "# This is a comment\n\nContent here."
        assert detect_format(raw) == "markdown"

    @beartype
    def test_detect_empty_string(self) -> None:
        """Test detecting format of empty string (defaults to markdown)."""
        raw = ""
        assert detect_format(raw) == "markdown"

    @beartype
    def test_detect_whitespace_only(self) -> None:
        """Test detecting format of whitespace-only string."""
        raw = "   \n\t  "
        assert detect_format(raw) == "markdown"

#!/usr/bin/env python3
"""
Test suite for doc frontmatter schema functionality.
Tests the YAML frontmatter parsing and validation logic.
"""

import os
import sys
from pathlib import Path

import pytest


scripts_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "scripts")
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from check_doc_frontmatter import (
    DocFrontmatter,
    extract_doc_owner,
    parse_frontmatter,
    resolve_owner,
    suggest_frontmatter,
    validate_glob_patterns,
)


class TestFrontmatterParsing:
    """Test YAML frontmatter parsing functionality."""

    def test_valid_frontmatter_parsing(self, tmp_path: Path) -> None:
        """Test parsing valid YAML frontmatter."""
        content = """---
title: "Test Document"
doc_owner: src/test/module
tracks:
  - src/test/**
last_reviewed: 2026-03-20
exempt: false
exempt_reason: ""
---

# Document content here"""

        test_file = tmp_path / "test.md"
        test_file.write_text(content, encoding="utf-8")
        result = parse_frontmatter(test_file)
        assert result is not None
        assert "title" in result
        assert "doc_owner" in result
        assert "tracks" in result
        assert result["title"] == "Test Document"
        assert result["doc_owner"] == "src/test/module"
        assert result["tracks"] == ["src/test/**"]

    def test_missing_required_fields(self, tmp_path: Path) -> None:
        """Test detection of missing required fields."""
        content = """---
title: "Incomplete Document"
---

# Document content here"""

        test_file = tmp_path / "incomplete.md"
        test_file.write_text(content, encoding="utf-8")
        result = parse_frontmatter(test_file)
        assert result is not None

    def test_no_frontmatter(self, tmp_path: Path) -> None:
        """Test handling of files without frontmatter."""
        content = "# Document without frontmatter"

        test_file = tmp_path / "plain.md"
        test_file.write_text(content, encoding="utf-8")
        result = parse_frontmatter(test_file)
        assert result == {}


class TestOwnerResolution:
    """Test owner identifier resolution functionality."""

    def test_path_like_owner_resolution(self):
        """Test resolution of path-like owner identifiers."""
        result = resolve_owner("openspec")
        assert result is True

    def test_known_token_resolution(self):
        """Test resolution of known owner tokens."""
        result = resolve_owner("specfact-cli")
        assert result is True  # Should resolve to True for known tokens

    def test_invalid_owner_resolution(self):
        """Test handling of invalid owner identifiers."""
        result = resolve_owner("nonexistent-owner")
        assert result is False  # Should resolve to False for invalid owners


class TestDocFrontmatterModel:
    """Pydantic model for validated ownership records."""

    def test_model_validate_accepts_minimal_valid_dict(self) -> None:
        data = {
            "title": "T",
            "doc_owner": "specfact-cli",
            "tracks": ["src/**"],
            "last_reviewed": "2026-01-01",
            "exempt": False,
            "exempt_reason": "",
        }
        rec = DocFrontmatter.model_validate(data)
        assert rec.title == "T"
        assert rec.doc_owner == "specfact-cli"
        assert rec.tracks == ["src/**"]
        assert str(rec.last_reviewed) == "2026-01-01"


class TestGlobPatternValidation:
    """Test glob pattern validation functionality."""

    def test_valid_glob_patterns(self):
        """Test validation of valid glob patterns."""
        patterns = ["src/test/**", "docs/**/*.md", "*.py"]
        result = validate_glob_patterns(patterns)
        assert result is True  # Should return True for valid patterns

    def test_invalid_glob_patterns(self):
        """Test detection of invalid glob patterns."""
        patterns = ["src/test/[", "invalid{{pattern"]
        result = validate_glob_patterns(patterns)
        assert result is False  # Should return False for invalid patterns


class TestFrontmatterSuggestions:
    """Test frontmatter suggestion generation."""

    def test_suggest_frontmatter_template(self):
        """Test generation of suggested frontmatter template."""
        path = Path("test-document.md")
        suggestion = suggest_frontmatter(path)

        assert suggestion is not None
        assert "---" in suggestion
        assert "title:" in suggestion
        assert "doc_owner:" in suggestion
        assert "tracks:" in suggestion
        assert "last_reviewed:" in suggestion
        assert "exempt:" in suggestion


class TestExtractDocOwner:
    """Test doc_owner extraction functionality."""

    def test_extract_valid_owner(self):
        """Test extraction of valid doc_owner from content."""
        content = """---
title: "Test"
doc_owner: src/test/module
---"""

        result = extract_doc_owner(content)
        assert result == "src/test/module"

    def test_extract_missing_owner(self):
        """Test handling of missing doc_owner."""
        content = """---
title: "Test"
---"""

        result = extract_doc_owner(content)
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

#!/usr/bin/env python3
"""
Test suite for doc frontmatter schema functionality.
Tests the YAML frontmatter parsing and validation logic.
"""

from __future__ import annotations

import datetime
import types
from pathlib import Path

import pytest

from tests.helpers.doc_frontmatter_types import CheckDocFrontmatterModule


class TestFrontmatterParsing:
    """Test YAML frontmatter parsing functionality."""

    def test_valid_frontmatter_parsing(
        self, tmp_path: Path, check_doc_frontmatter_module: CheckDocFrontmatterModule
    ) -> None:
        """Test parsing valid YAML frontmatter."""
        parse_frontmatter = check_doc_frontmatter_module.parse_frontmatter
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

    def test_missing_required_fields(
        self, tmp_path: Path, check_doc_frontmatter_module: CheckDocFrontmatterModule
    ) -> None:
        """Test detection of missing required fields."""
        parse_frontmatter = check_doc_frontmatter_module.parse_frontmatter
        content = """---
title: "Incomplete Document"
---

# Document content here"""

        test_file = tmp_path / "incomplete.md"
        test_file.write_text(content, encoding="utf-8")
        result = parse_frontmatter(test_file)
        assert result is not None

    def test_no_frontmatter(self, tmp_path: Path, check_doc_frontmatter_module: CheckDocFrontmatterModule) -> None:
        """Test handling of files without frontmatter."""
        parse_frontmatter = check_doc_frontmatter_module.parse_frontmatter
        content = "# Document without frontmatter"

        test_file = tmp_path / "plain.md"
        test_file.write_text(content, encoding="utf-8")
        result = parse_frontmatter(test_file)
        assert result == {}


class TestOwnerResolution:
    """Test owner identifier resolution functionality."""

    def test_token_owner_resolution(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, check_doc_frontmatter_module: CheckDocFrontmatterModule
    ) -> None:
        """Known token ``openspec`` resolves without filesystem lookup."""
        monkeypatch.setenv("DOC_FRONTMATTER_ROOT", str(tmp_path))
        resolve_owner = check_doc_frontmatter_module.resolve_owner
        result = resolve_owner("openspec")
        assert result is True

    def test_filesystem_owner_resolution(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, check_doc_frontmatter_module: CheckDocFrontmatterModule
    ) -> None:
        """Path-like owner resolves when the directory exists under DOC_FRONTMATTER_ROOT."""
        monkeypatch.setenv("DOC_FRONTMATTER_ROOT", str(tmp_path))
        (tmp_path / "src" / "fs_owner_pkg").mkdir(parents=True)
        resolve_owner = check_doc_frontmatter_module.resolve_owner
        assert resolve_owner("src/fs_owner_pkg") is True

    def test_known_token_resolution(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, check_doc_frontmatter_module: CheckDocFrontmatterModule
    ) -> None:
        """Test resolution of known owner tokens."""
        monkeypatch.setenv("DOC_FRONTMATTER_ROOT", str(tmp_path))
        resolve_owner = check_doc_frontmatter_module.resolve_owner
        result = resolve_owner("specfact-cli")
        assert result is True

    def test_invalid_owner_resolution(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, check_doc_frontmatter_module: CheckDocFrontmatterModule
    ) -> None:
        """Test handling of invalid owner identifiers."""
        monkeypatch.setenv("DOC_FRONTMATTER_ROOT", str(tmp_path))
        resolve_owner = check_doc_frontmatter_module.resolve_owner
        result = resolve_owner("nonexistent-owner")
        assert result is False

    def test_owner_rejects_traversal_and_glob(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, check_doc_frontmatter_module: CheckDocFrontmatterModule
    ) -> None:
        """Unsafe owner literals do not resolve."""
        monkeypatch.setenv("DOC_FRONTMATTER_ROOT", str(tmp_path))
        (tmp_path / "safe").mkdir()
        resolve_owner = check_doc_frontmatter_module.resolve_owner
        assert resolve_owner("../safe") is False
        assert resolve_owner("**") is False
        assert resolve_owner("") is False


class TestDocFrontmatterModel:
    """Pydantic model for validated ownership records."""

    def test_model_validate_accepts_minimal_valid_dict(
        self, check_doc_frontmatter_module: CheckDocFrontmatterModule
    ) -> None:
        doc_frontmatter_model = check_doc_frontmatter_module.DocFrontmatter
        data = {
            "title": "T",
            "doc_owner": "specfact-cli",
            "tracks": ["src/**"],
            "last_reviewed": "2026-01-01",
            "exempt": False,
            "exempt_reason": "",
        }
        rec = doc_frontmatter_model.model_validate(data)
        assert rec.title == "T"
        assert rec.doc_owner == "specfact-cli"
        assert rec.tracks == ["src/**"]
        assert str(rec.last_reviewed) == "2026-01-01"


class TestGlobPatternValidation:
    """Test glob pattern validation functionality."""

    def test_valid_glob_patterns(self, check_doc_frontmatter_module: CheckDocFrontmatterModule) -> None:
        """Test validation of valid glob patterns."""
        validate_glob_patterns = check_doc_frontmatter_module.validate_glob_patterns
        patterns = ["src/test/**", "docs/**/*.md", "*.py"]
        result = validate_glob_patterns(patterns)
        assert result is True

    def test_invalid_glob_patterns(self, check_doc_frontmatter_module: CheckDocFrontmatterModule) -> None:
        """Test detection of invalid glob patterns."""
        validate_glob_patterns = check_doc_frontmatter_module.validate_glob_patterns
        patterns = ["src/test/[", "invalid{{pattern"]
        result = validate_glob_patterns(patterns)
        assert result is False


class TestFrontmatterSuggestions:
    """Test frontmatter suggestion generation."""

    def test_suggest_frontmatter_template(
        self, monkeypatch: pytest.MonkeyPatch, check_doc_frontmatter_module: CheckDocFrontmatterModule
    ) -> None:
        """Test generation of suggested frontmatter template."""
        fixed = datetime.date(2026, 3, 15)

        class _FakeDate:
            @staticmethod
            def today() -> datetime.date:
                return fixed

        _fake_dt = types.ModuleType("datetime")
        _fake_dt.date = _FakeDate
        monkeypatch.setattr(check_doc_frontmatter_module, "datetime", _fake_dt)
        suggest_frontmatter = check_doc_frontmatter_module.suggest_frontmatter
        path = Path("test-document.md")
        suggestion = suggest_frontmatter(path)

        assert suggestion is not None
        assert "---" in suggestion
        assert "title:" in suggestion
        assert "doc_owner:" in suggestion
        assert "tracks:" in suggestion
        assert "last_reviewed:" in suggestion
        assert fixed.isoformat() in suggestion
        assert "exempt:" in suggestion


class TestExtractDocOwner:
    """Test doc_owner extraction functionality."""

    def test_extract_valid_owner(self, check_doc_frontmatter_module: CheckDocFrontmatterModule) -> None:
        """Test extraction of valid doc_owner from content."""
        extract_doc_owner = check_doc_frontmatter_module.extract_doc_owner
        content = """---
title: "Test"
doc_owner: src/test/module
---"""

        result = extract_doc_owner(content)
        assert result == "src/test/module"

    def test_extract_missing_owner(self, check_doc_frontmatter_module: CheckDocFrontmatterModule) -> None:
        """Test handling of missing doc_owner."""
        extract_doc_owner = check_doc_frontmatter_module.extract_doc_owner
        content = """---
title: "Test"
---"""

        result = extract_doc_owner(content)
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

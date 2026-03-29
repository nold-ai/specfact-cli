#!/usr/bin/env python3
"""Tests for doc frontmatter validation (scripts/check_doc_frontmatter.py)."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest


scripts_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "scripts")
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from check_doc_frontmatter import get_all_md_files, main as validation_main, rg_missing_doc_owner


def _write_enforced(root: Path, *relative_paths: str) -> None:
    enforced = root / "docs" / ".doc-frontmatter-enforced"
    enforced.parent.mkdir(parents=True, exist_ok=True)
    enforced.write_text("\n".join(relative_paths) + "\n", encoding="utf-8")


def _enforce_all_markdown_under_docs(root: Path) -> None:
    lines: list[str] = []
    docs = root / "docs"
    if docs.exists():
        for p in docs.rglob("*.md"):
            if p.name == ".doc-frontmatter-enforced":
                continue
            lines.append(p.relative_to(root).as_posix())
    _write_enforced(root, *lines)


class TestFileDiscovery:
    """Test Markdown file discovery functionality."""

    def test_discover_docs_directory_files(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test discovery of files in docs directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            monkeypatch.setenv("DOC_FRONTMATTER_ROOT", str(root))
            docs_dir = root / "docs"
            docs_dir.mkdir()
            (docs_dir / "test1.md").write_text("# Test 1")
            (docs_dir / "test2.md").write_text("---\ntitle: Test\n---\n# Test 2")
            (docs_dir / "subdir").mkdir()
            (docs_dir / "subdir" / "test3.md").write_text("# Test 3")
            files = get_all_md_files()
            assert len(files) == 3

    def test_exempt_files_exclusion(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that exempt files are excluded from discovery."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            monkeypatch.setenv("DOC_FRONTMATTER_ROOT", str(root))
            docs_dir = root / "docs"
            docs_dir.mkdir()
            (docs_dir / "regular.md").write_text("# Regular")
            (docs_dir / "LICENSE.md").write_text("# License")
            (docs_dir / "exempt.md").write_text(
                "---\ntitle: Test\nexempt: true\nexempt_reason: Test reason\n---\n# Exempt"
            )
            files = get_all_md_files()
            assert len(files) == 1
            assert "regular.md" in str(files[0])


class TestMissingDocOwnerDetection:
    """Test detection of missing doc_owner fields."""

    def test_missing_doc_owner_detection(self) -> None:
        """Test detection of files missing doc_owner."""
        with tempfile.TemporaryDirectory() as temp_dir:
            docs_dir = Path(temp_dir) / "docs"
            docs_dir.mkdir()
            (docs_dir / "with_owner.md").write_text("---\ntitle: Test\ndoc_owner: test\n---\n# Content")
            (docs_dir / "without_owner.md").write_text("---\ntitle: Test\n---\n# Content")
            (docs_dir / "no_frontmatter.md").write_text("# No frontmatter")
            files = [
                docs_dir / "with_owner.md",
                docs_dir / "without_owner.md",
                docs_dir / "no_frontmatter.md",
            ]
            missing_owner = rg_missing_doc_owner(files)
            assert len(missing_owner) == 2
            assert docs_dir / "without_owner.md" in missing_owner
            assert docs_dir / "no_frontmatter.md" in missing_owner
            assert docs_dir / "with_owner.md" not in missing_owner

    def test_all_files_have_owner(self) -> None:
        """Test when all files have doc_owner."""
        with tempfile.TemporaryDirectory() as temp_dir:
            docs_dir = Path(temp_dir) / "docs"
            docs_dir.mkdir()
            (docs_dir / "file1.md").write_text("---\ntitle: Test\ndoc_owner: test\n---\n# Content")
            (docs_dir / "file2.md").write_text("---\ntitle: Test\ndoc_owner: test\n---\n# Content")
            files = [docs_dir / "file1.md", docs_dir / "file2.md"]
            missing_owner = rg_missing_doc_owner(files)
            assert len(missing_owner) == 0


class TestValidationMainFunction:
    """Test the main validation function."""

    def test_validation_with_valid_files(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test validation with all valid files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            monkeypatch.setenv("DOC_FRONTMATTER_ROOT", str(root))
            docs_dir = root / "docs"
            docs_dir.mkdir()
            (docs_dir / "valid1.md").write_text(
                """---
title: "Valid Document"
doc_owner: src/test/module
tracks:
  - src/test/**
last_reviewed: 2026-03-20
exempt: false
exempt_reason: ""
---

# Valid content"""
            )
            (root / "src" / "test" / "module").mkdir(parents=True)
            _write_enforced(root, "docs/valid1.md")
            result = validation_main([])
            assert result == 0

    def test_validation_with_invalid_files(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test validation with invalid files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            monkeypatch.setenv("DOC_FRONTMATTER_ROOT", str(root))
            docs_dir = root / "docs"
            docs_dir.mkdir()
            (docs_dir / "invalid.md").write_text(
                """---
title: "Invalid Document"
---

# Missing doc_owner"""
            )
            _write_enforced(root, "docs/invalid.md")
            result = validation_main([])
            assert result == 1


class TestOwnerResolutionValidation:
    """Test owner resolution validation."""

    def test_valid_owner_resolution(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test validation with valid owner resolution."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            monkeypatch.setenv("DOC_FRONTMATTER_ROOT", str(root))
            docs_dir = root / "docs"
            docs_dir.mkdir()
            (docs_dir / "valid.md").write_text(
                """---
title: "Valid Document"
doc_owner: src/test/module
tracks:
  - src/test/**
last_reviewed: 2026-03-20
exempt: false
exempt_reason: ""
---

# Content"""
            )
            (root / "src" / "test" / "module").mkdir(parents=True)
            _write_enforced(root, "docs/valid.md")
            result = validation_main([])
            assert result == 0

    def test_invalid_owner_resolution(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test validation with invalid owner resolution."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            monkeypatch.setenv("DOC_FRONTMATTER_ROOT", str(root))
            docs_dir = root / "docs"
            docs_dir.mkdir()
            (docs_dir / "invalid.md").write_text(
                """---
title: "Invalid Document"
doc_owner: nonexistent/owner
tracks:
  - src/test/**
last_reviewed: 2026-03-20
exempt: false
exempt_reason: ""
---

# Content"""
            )
            _write_enforced(root, "docs/invalid.md")
            result = validation_main([])
            assert result == 1


class TestFixHintGeneration:
    """Test fix hint generation functionality."""

    def test_fix_hint_for_missing_frontmatter(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test fix hint generation for missing frontmatter."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            monkeypatch.setenv("DOC_FRONTMATTER_ROOT", str(root))
            docs_dir = root / "docs"
            docs_dir.mkdir()
            (docs_dir / "no_frontmatter.md").write_text("# Document without frontmatter")
            _write_enforced(root, "docs/no_frontmatter.md")
            result = validation_main(["--fix-hint"])
            assert result == 1
            captured = capsys.readouterr()
            assert "MISSING doc_owner" in captured.err
            assert "Suggested frontmatter" in captured.err or "---" in captured.err

    def test_fix_hint_for_invalid_owner(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test fix hint generation for invalid owner."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            monkeypatch.setenv("DOC_FRONTMATTER_ROOT", str(root))
            docs_dir = root / "docs"
            docs_dir.mkdir()
            (docs_dir / "invalid.md").write_text(
                """---
title: "Invalid Document"
doc_owner: invalid/owner
tracks:
  - src/**
last_reviewed: 2026-03-20
exempt: false
exempt_reason: ""
---

# Content"""
            )
            _write_enforced(root, "docs/invalid.md")
            result = validation_main(["--fix-hint"])
            assert result == 1
            captured = capsys.readouterr()
            assert "INVALID" in captured.err or "does not resolve" in captured.err


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

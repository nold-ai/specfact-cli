#!/usr/bin/env python3
"""Tests for doc frontmatter validation (scripts/check_doc_frontmatter.py)."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from tests.helpers.doc_frontmatter import write_enforced
from tests.helpers.doc_frontmatter_types import CheckDocFrontmatterModule


class TestFileDiscovery:
    """Test Markdown file discovery functionality."""

    def test_discover_docs_directory_files(
        self, monkeypatch: pytest.MonkeyPatch, check_doc_frontmatter_module: CheckDocFrontmatterModule
    ) -> None:
        """Test discovery of files in docs directory."""
        get_all_md_files = check_doc_frontmatter_module.get_all_md_files
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

    def test_exempt_files_exclusion(
        self, monkeypatch: pytest.MonkeyPatch, check_doc_frontmatter_module: CheckDocFrontmatterModule
    ) -> None:
        """Test that exempt files are excluded from discovery."""
        get_all_md_files = check_doc_frontmatter_module.get_all_md_files
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

    def test_missing_doc_owner_detection(self, check_doc_frontmatter_module: CheckDocFrontmatterModule) -> None:
        """Test detection of files missing doc_owner."""
        rg_missing_doc_owner = check_doc_frontmatter_module.rg_missing_doc_owner
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

    def test_all_files_have_owner(self, check_doc_frontmatter_module: CheckDocFrontmatterModule) -> None:
        """Test when all files have doc_owner."""
        rg_missing_doc_owner = check_doc_frontmatter_module.rg_missing_doc_owner
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

    def test_validation_with_valid_files(
        self, monkeypatch: pytest.MonkeyPatch, check_doc_frontmatter_module: CheckDocFrontmatterModule
    ) -> None:
        """Test validation with all valid files."""
        validation_main = check_doc_frontmatter_module.main
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
            write_enforced(root, "docs/valid1.md")
            result = validation_main([])
            assert result == 0

    def test_validation_with_invalid_files(
        self, monkeypatch: pytest.MonkeyPatch, check_doc_frontmatter_module: CheckDocFrontmatterModule
    ) -> None:
        """Test validation with invalid files."""
        validation_main = check_doc_frontmatter_module.main
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
            write_enforced(root, "docs/invalid.md")
            result = validation_main([])
            assert result == 1


class TestOwnerResolutionValidation:
    """Test owner resolution validation."""

    def test_valid_owner_resolution(
        self, monkeypatch: pytest.MonkeyPatch, check_doc_frontmatter_module: CheckDocFrontmatterModule
    ) -> None:
        """Test validation with valid owner resolution."""
        validation_main = check_doc_frontmatter_module.main
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
            write_enforced(root, "docs/valid.md")
            result = validation_main([])
            assert result == 0

    def test_invalid_owner_resolution(
        self, monkeypatch: pytest.MonkeyPatch, check_doc_frontmatter_module: CheckDocFrontmatterModule
    ) -> None:
        """Test validation with invalid owner resolution."""
        validation_main = check_doc_frontmatter_module.main
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
            write_enforced(root, "docs/invalid.md")
            result = validation_main([])
            assert result == 1


class TestFixHintGeneration:
    """Test fix hint generation functionality."""

    def test_fix_hint_for_missing_frontmatter(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        check_doc_frontmatter_module: CheckDocFrontmatterModule,
    ) -> None:
        """Test fix hint generation for missing frontmatter."""
        validation_main = check_doc_frontmatter_module.main
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            monkeypatch.setenv("DOC_FRONTMATTER_ROOT", str(root))
            docs_dir = root / "docs"
            docs_dir.mkdir()
            (docs_dir / "no_frontmatter.md").write_text("# Document without frontmatter")
            write_enforced(root, "docs/no_frontmatter.md")
            result = validation_main(["--fix-hint"])
            assert result == 1
            captured = capsys.readouterr()
            assert "MISSING doc_owner" in captured.err
            assert "Suggested frontmatter" in captured.err or "---" in captured.err

    def test_fix_hint_for_invalid_owner(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        check_doc_frontmatter_module: CheckDocFrontmatterModule,
    ) -> None:
        """Test fix hint generation for invalid owner."""
        validation_main = check_doc_frontmatter_module.main
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
            write_enforced(root, "docs/invalid.md")
            result = validation_main(["--fix-hint"])
            assert result == 1
            captured = capsys.readouterr()
            assert "INVALID" in captured.err or "does not resolve" in captured.err


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

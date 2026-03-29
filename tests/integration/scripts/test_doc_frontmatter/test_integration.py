#!/usr/bin/env python3
"""Integration tests for doc frontmatter validation."""

from __future__ import annotations

import re
import tempfile
from pathlib import Path

import pytest

from tests.helpers.doc_frontmatter import (
    VALID_DOC_FRONTMATTER,
    enforce_all_markdown_under_docs,
    validation_main_fn,
    write_enforced,
)
from tests.helpers.doc_frontmatter_types import CheckDocFrontmatterModule


ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


class TestEndToEndWorkflow:
    """Test complete end-to-end validation workflows."""

    def test_complete_validation_workflow(
        self, monkeypatch: pytest.MonkeyPatch, check_doc_frontmatter_module: CheckDocFrontmatterModule
    ) -> None:
        """Test the complete validation workflow with various file types."""
        validation_main = validation_main_fn(check_doc_frontmatter_module)
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            monkeypatch.setenv("DOC_FRONTMATTER_ROOT", str(root))
            docs_dir = root / "docs"
            docs_dir.mkdir()
            (docs_dir / "valid.md").write_text(VALID_DOC_FRONTMATTER)
            (docs_dir / "invalid.md").write_text(
                """---
title: "Invalid Document"
---

# Missing required fields"""
            )
            (docs_dir / "no_frontmatter.md").write_text("# No frontmatter at all")
            (root / "src" / "test" / "module").mkdir(parents=True)
            enforce_all_markdown_under_docs(root)
            assert validation_main([]) == 1

    def test_validation_with_all_valid_files(
        self, monkeypatch: pytest.MonkeyPatch, check_doc_frontmatter_module: CheckDocFrontmatterModule
    ) -> None:
        """Test validation workflow when all files are valid."""
        validation_main = validation_main_fn(check_doc_frontmatter_module)
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            monkeypatch.setenv("DOC_FRONTMATTER_ROOT", str(root))
            docs_dir = root / "docs"
            docs_dir.mkdir()
            for i in range(3):
                (docs_dir / f"valid{i}.md").write_text(
                    VALID_DOC_FRONTMATTER.replace("Valid Document", f"Valid Document {i}")
                )
            (root / "src" / "test" / "module").mkdir(parents=True)
            enforce_all_markdown_under_docs(root)
            assert validation_main([]) == 0


class TestMultipleFileScenarios:
    """Test validation with multiple files and complex scenarios."""

    def test_large_number_of_files(
        self, monkeypatch: pytest.MonkeyPatch, check_doc_frontmatter_module: CheckDocFrontmatterModule
    ) -> None:
        """Test performance with a large number of files."""
        validation_main = validation_main_fn(check_doc_frontmatter_module)
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            monkeypatch.setenv("DOC_FRONTMATTER_ROOT", str(root))
            docs_dir = root / "docs"
            docs_dir.mkdir()
            for i in range(50):
                if i % 3 == 0:
                    (docs_dir / f"file{i}.md").write_text(
                        f"""---
title: "File {i}"
---

# Missing doc_owner"""
                    )
                else:
                    (docs_dir / f"file{i}.md").write_text(VALID_DOC_FRONTMATTER.replace("Valid Document", f"File {i}"))
            (root / "src" / "test" / "module").mkdir(parents=True)
            enforce_all_markdown_under_docs(root)
            assert validation_main([]) == 1

    def test_nested_directory_structure(
        self, monkeypatch: pytest.MonkeyPatch, check_doc_frontmatter_module: CheckDocFrontmatterModule
    ) -> None:
        """Test with nested directory structures."""
        validation_main = validation_main_fn(check_doc_frontmatter_module)
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            monkeypatch.setenv("DOC_FRONTMATTER_ROOT", str(root))
            docs_dir = root / "docs"
            docs_dir.mkdir()
            (docs_dir / "level1" / "level2" / "level3").mkdir(parents=True)
            for rel in (
                "root.md",
                "level1/level1.md",
                "level1/level2/level2.md",
                "level1/level2/level3/level3.md",
            ):
                (docs_dir / rel).write_text(VALID_DOC_FRONTMATTER.replace("Valid Document", rel))
            (root / "src" / "test" / "module").mkdir(parents=True)
            enforce_all_markdown_under_docs(root)
            assert validation_main([]) == 0


class TestScaleSmoke:
    """Scale / smoke tests: many files and large bodies (not benchmark assertions)."""

    def test_execution_time_with_many_files(
        self, monkeypatch: pytest.MonkeyPatch, check_doc_frontmatter_module: CheckDocFrontmatterModule
    ) -> None:
        """Many small valid docs complete successfully (smoke, not timing assertions)."""
        validation_main = validation_main_fn(check_doc_frontmatter_module)
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            monkeypatch.setenv("DOC_FRONTMATTER_ROOT", str(root))
            docs_dir = root / "docs"
            docs_dir.mkdir()
            for i in range(100):
                (docs_dir / f"file{i}.md").write_text(VALID_DOC_FRONTMATTER.replace("Valid Document", f"File {i}"))
            (root / "src" / "test" / "module").mkdir(parents=True)
            enforce_all_markdown_under_docs(root)
            assert validation_main([]) == 0

    def test_memory_usage_with_large_files(
        self, monkeypatch: pytest.MonkeyPatch, check_doc_frontmatter_module: CheckDocFrontmatterModule
    ) -> None:
        """Large Markdown bodies still validate (smoke, not memory instrumentation)."""
        validation_main = validation_main_fn(check_doc_frontmatter_module)
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            monkeypatch.setenv("DOC_FRONTMATTER_ROOT", str(root))
            docs_dir = root / "docs"
            docs_dir.mkdir()
            large_content = "# Large content\n" * 1000
            for i in range(10):
                body = VALID_DOC_FRONTMATTER.replace("Valid Document", f"Large File {i}") + "\n" + large_content
                (docs_dir / f"large{i}.md").write_text(body)
            (root / "src" / "test" / "module").mkdir(parents=True)
            enforce_all_markdown_under_docs(root)
            assert validation_main([]) == 0


class TestCommandLineInterface:
    """Test command-line interface functionality."""

    def test_cli_with_fix_hint_flag(
        self, monkeypatch: pytest.MonkeyPatch, check_doc_frontmatter_module: CheckDocFrontmatterModule
    ) -> None:
        """Test CLI with --fix-hint flag."""
        validation_main = validation_main_fn(check_doc_frontmatter_module)
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            monkeypatch.setenv("DOC_FRONTMATTER_ROOT", str(root))
            docs_dir = root / "docs"
            docs_dir.mkdir()
            (docs_dir / "invalid.md").write_text("# Missing frontmatter")
            write_enforced(root, "docs/invalid.md")
            assert validation_main(["--fix-hint"]) == 1

    def test_cli_help_output(
        self, capsys: pytest.CaptureFixture[str], check_doc_frontmatter_module: CheckDocFrontmatterModule
    ) -> None:
        """Test CLI help output."""
        validation_main = validation_main_fn(check_doc_frontmatter_module)
        assert validation_main(["--help"]) == 0
        captured = capsys.readouterr()
        combined = ANSI_ESCAPE_RE.sub("", captured.out + captured.err).lower()
        assert "usage" in combined or "help" in combined
        assert "--fix-hint" in combined


class TestRealWorldScenarios:
    """Test real-world usage scenarios."""

    def test_mixed_exempt_and_regular_files(
        self, monkeypatch: pytest.MonkeyPatch, check_doc_frontmatter_module: CheckDocFrontmatterModule
    ) -> None:
        """Test scenario with both exempt and regular files."""
        validation_main = validation_main_fn(check_doc_frontmatter_module)
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            monkeypatch.setenv("DOC_FRONTMATTER_ROOT", str(root))
            docs_dir = root / "docs"
            docs_dir.mkdir()
            (docs_dir / "LICENSE.md").write_text("# License")
            (docs_dir / "exempt.md").write_text(
                """---
title: "Exempt"
exempt: true
exempt_reason: "Legal document"
---

# Exempt content"""
            )
            (docs_dir / "regular.md").write_text(VALID_DOC_FRONTMATTER)
            (docs_dir / "invalid.md").write_text(
                """---
title: "Invalid"
---

# Missing doc_owner"""
            )
            (root / "src" / "test" / "module").mkdir(parents=True)
            write_enforced(root, "docs/regular.md", "docs/invalid.md", "docs/exempt.md")
            assert validation_main([]) == 1

    def test_complex_tracking_patterns(
        self, monkeypatch: pytest.MonkeyPatch, check_doc_frontmatter_module: CheckDocFrontmatterModule
    ) -> None:
        """Test with complex glob patterns in tracks field."""
        validation_main = validation_main_fn(check_doc_frontmatter_module)
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            monkeypatch.setenv("DOC_FRONTMATTER_ROOT", str(root))
            docs_dir = root / "docs"
            docs_dir.mkdir()
            (docs_dir / "complex1.md").write_text(
                """---
title: "Complex Patterns"
doc_owner: src/test/module
tracks:
  - src/**/*.py
  - tests/**/test_*.py
  - docs/**/*.md
  - "**/excluded/**"
last_reviewed: 2026-03-20
exempt: false
exempt_reason: ""
---

# Complex tracking patterns"""
            )
            (root / "src" / "test" / "module").mkdir(parents=True)
            write_enforced(root, "docs/complex1.md")
            assert validation_main([]) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

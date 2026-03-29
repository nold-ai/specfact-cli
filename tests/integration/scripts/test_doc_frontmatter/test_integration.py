#!/usr/bin/env python3
"""Integration tests for doc frontmatter validation."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest


scripts_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "scripts")
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from check_doc_frontmatter import main as validation_main


def _write_enforced(root: Path, *relative_paths: str) -> None:
    enforced = root / "docs" / ".doc-frontmatter-enforced"
    enforced.parent.mkdir(parents=True, exist_ok=True)
    enforced.write_text("\n".join(relative_paths) + "\n", encoding="utf-8")


def _enforce_all_markdown_under_docs(root: Path) -> None:
    lines: list[str] = []
    docs = root / "docs"
    if docs.exists():
        for p in docs.rglob("*.md"):
            lines.append(p.relative_to(root).as_posix())
    _write_enforced(root, *lines)


_VALID = """---
title: "Valid Document"
doc_owner: src/test/module
tracks:
  - src/test/**
last_reviewed: 2026-03-20
exempt: false
exempt_reason: ""
---

# Valid content"""


class TestEndToEndWorkflow:
    """Test complete end-to-end validation workflows."""

    def test_complete_validation_workflow(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test the complete validation workflow with various file types."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            monkeypatch.setenv("DOC_FRONTMATTER_ROOT", str(root))
            docs_dir = root / "docs"
            docs_dir.mkdir()
            (docs_dir / "valid.md").write_text(_VALID)
            (docs_dir / "invalid.md").write_text(
                """---
title: "Invalid Document"
---

# Missing required fields"""
            )
            (docs_dir / "no_frontmatter.md").write_text("# No frontmatter at all")
            (root / "src" / "test" / "module").mkdir(parents=True)
            _enforce_all_markdown_under_docs(root)
            assert validation_main([]) == 1

    def test_validation_with_all_valid_files(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test validation workflow when all files are valid."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            monkeypatch.setenv("DOC_FRONTMATTER_ROOT", str(root))
            docs_dir = root / "docs"
            docs_dir.mkdir()
            for i in range(3):
                (docs_dir / f"valid{i}.md").write_text(_VALID.replace("Valid Document", f"Valid Document {i}"))
            (root / "src" / "test" / "module").mkdir(parents=True)
            _enforce_all_markdown_under_docs(root)
            assert validation_main([]) == 0


class TestMultipleFileScenarios:
    """Test validation with multiple files and complex scenarios."""

    def test_large_number_of_files(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test performance with a large number of files."""
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
                    (docs_dir / f"file{i}.md").write_text(_VALID.replace("Valid Document", f"File {i}"))
            (root / "src" / "test" / "module").mkdir(parents=True)
            _enforce_all_markdown_under_docs(root)
            assert validation_main([]) == 1

    def test_nested_directory_structure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test with nested directory structures."""
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
                (docs_dir / rel).write_text(_VALID.replace("Valid Document", rel))
            (root / "src" / "test" / "module").mkdir(parents=True)
            _enforce_all_markdown_under_docs(root)
            assert validation_main([]) == 0


class TestScaleSmoke:
    """Scale / smoke tests: many files and large bodies (not benchmark assertions)."""

    def test_execution_time_with_many_files(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Many small valid docs complete successfully (smoke, not timing assertions)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            monkeypatch.setenv("DOC_FRONTMATTER_ROOT", str(root))
            docs_dir = root / "docs"
            docs_dir.mkdir()
            for i in range(100):
                (docs_dir / f"file{i}.md").write_text(_VALID.replace("Valid Document", f"File {i}"))
            (root / "src" / "test" / "module").mkdir(parents=True)
            _enforce_all_markdown_under_docs(root)
            assert validation_main([]) == 0

    def test_memory_usage_with_large_files(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Large Markdown bodies still validate (smoke, not memory instrumentation)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            monkeypatch.setenv("DOC_FRONTMATTER_ROOT", str(root))
            docs_dir = root / "docs"
            docs_dir.mkdir()
            large_content = "# Large content\n" * 1000
            for i in range(10):
                body = _VALID.replace("Valid Document", f"Large File {i}") + "\n" + large_content
                (docs_dir / f"large{i}.md").write_text(body)
            (root / "src" / "test" / "module").mkdir(parents=True)
            _enforce_all_markdown_under_docs(root)
            assert validation_main([]) == 0


class TestCommandLineInterface:
    """Test command-line interface functionality."""

    def test_cli_with_fix_hint_flag(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test CLI with --fix-hint flag."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            monkeypatch.setenv("DOC_FRONTMATTER_ROOT", str(root))
            docs_dir = root / "docs"
            docs_dir.mkdir()
            (docs_dir / "invalid.md").write_text("# Missing frontmatter")
            _write_enforced(root, "docs/invalid.md")
            assert validation_main(["--fix-hint"]) == 1

    def test_cli_help_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test CLI help output."""
        with pytest.raises(SystemExit) as exc_info:
            validation_main(["--help"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "usage" in captured.out.lower() or "help" in captured.out.lower()


class TestRealWorldScenarios:
    """Test real-world usage scenarios."""

    def test_mixed_exempt_and_regular_files(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test scenario with both exempt and regular files."""
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
            (docs_dir / "regular.md").write_text(_VALID)
            (docs_dir / "invalid.md").write_text(
                """---
title: "Invalid"
---

# Missing doc_owner"""
            )
            (root / "src" / "test" / "module").mkdir(parents=True)
            _write_enforced(root, "docs/regular.md", "docs/invalid.md")
            assert validation_main([]) == 1

    def test_complex_tracking_patterns(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test with complex glob patterns in tracks field."""
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
  - "!**/excluded/**"
last_reviewed: 2026-03-20
exempt: false
exempt_reason: ""
---

# Complex tracking patterns"""
            )
            (root / "src" / "test" / "module").mkdir(parents=True)
            _write_enforced(root, "docs/complex1.md")
            assert validation_main([]) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

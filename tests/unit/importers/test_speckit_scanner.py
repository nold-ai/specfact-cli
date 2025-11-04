"""
Unit tests for SpecKitScanner - Contract-First approach.

Most validation is covered by @beartype and @icontract decorators.
Only edge cases and integration scenarios are tested here.
"""

from __future__ import annotations

from pathlib import Path

from specfact_cli.importers.speckit_scanner import SpecKitScanner


class TestSpecKitScanner:
    """Test cases for SpecKitScanner - focused on edge cases and business logic."""

    def test_is_speckit_repo_with_specify_dir(self, tmp_path: Path) -> None:
        """Test detection of modern Spec-Kit repo with .specify/ directory."""
        # Create modern Spec-Kit structure
        specify_dir = tmp_path / ".specify"
        specify_dir.mkdir(parents=True)

        scanner = SpecKitScanner(tmp_path)
        assert scanner.is_speckit_repo() is True

    def test_is_not_speckit_repo(self, tmp_path: Path) -> None:
        """Test detection of non-Spec-Kit repo."""
        # Create non-Spec-Kit structure
        (tmp_path / "README.md").write_text("# Project\n")

        scanner = SpecKitScanner(tmp_path)
        assert scanner.is_speckit_repo() is False

    def test_scan_structure_modern_format(self, tmp_path: Path) -> None:
        """Test scanning modern Spec-Kit structure with specs/ and .specify/."""
        # Create modern Spec-Kit structure
        specify_dir = tmp_path / ".specify" / "memory"
        specify_dir.mkdir(parents=True)
        (specify_dir / "constitution.md").write_text("# Constitution\n")

        specs_dir = tmp_path / "specs" / "001-test-feature"
        specs_dir.mkdir(parents=True)
        (specs_dir / "spec.md").write_text("# Feature Specification: Test Feature\n")

        scanner = SpecKitScanner(tmp_path)
        structure = scanner.scan_structure()

        assert structure["is_speckit"] is True
        assert structure["specify_memory_dir"] is not None
        assert len(structure["feature_dirs"]) == 1
        assert len(structure["memory_files"]) >= 1

    def test_discover_features_empty_repo(self, tmp_path: Path) -> None:
        """Test feature discovery in non-Spec-Kit repo returns empty list."""
        scanner = SpecKitScanner(tmp_path)
        features = scanner.discover_features()

        # Contract ensures result is a list (covered by @ensure)
        assert isinstance(features, list)
        assert len(features) == 0

    def test_parse_spec_markdown_with_real_structure(self, tmp_path: Path) -> None:
        """Test parsing real spec.md structure - integration test."""
        spec_file = tmp_path / "spec.md"
        spec_content = """# Feature Specification: Test Feature

## User Scenarios & Testing

### User Story 1 - Test Story (Priority: P1)

As a user, I want to test features so that I can validate functionality.

**Acceptance Scenarios**:

1. **Given** test setup, **When** test runs, **Then** test passes

## Requirements

- **FR-001**: System MUST test features correctly

## Success Criteria

- **SC-001**: All tests pass
"""
        spec_file.write_text(spec_content)

        scanner = SpecKitScanner(tmp_path)
        parsed = scanner.parse_spec_markdown(spec_file)

        assert parsed is not None
        assert parsed["feature_title"] == "Test Feature"
        assert len(parsed["stories"]) == 1
        assert len(parsed["requirements"]) >= 1
        assert len(parsed["success_criteria"]) >= 1

    def test_parse_spec_markdown_nonexistent_file(self, tmp_path: Path) -> None:
        """Test parsing nonexistent spec.md returns None (edge case)."""
        scanner = SpecKitScanner(tmp_path)
        spec_file = tmp_path / "nonexistent.md"

        # Contract ensures None or dict with feature_key (covered by @ensure)
        parsed = scanner.parse_spec_markdown(spec_file)
        assert parsed is None

    def test_parse_memory_files_with_constitution(self, tmp_path: Path) -> None:
        """Test parsing constitution.md - integration test."""
        memory_dir = tmp_path / ".specify" / "memory"
        memory_dir.mkdir(parents=True)

        constitution_content = """# SpecFact CLI Constitution

## Core Principles

### I. Contract-First Development (NON-NEGOTIABLE)

All public APIs MUST have @icontract decorators.

**Version**: 1.0.0 | **Ratified**: 2025-10-31
"""
        (memory_dir / "constitution.md").write_text(constitution_content)

        scanner = SpecKitScanner(tmp_path)
        memory_data = scanner.parse_memory_files(memory_dir)

        # Contract ensures dict with constitution and principles (covered by @ensure)
        assert isinstance(memory_data, dict)
        assert memory_data["constitution"] is not None
        assert memory_data["version"] == "1.0.0"
        assert len(memory_data["principles"]) >= 1

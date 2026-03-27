"""
Unit tests for SpecKitScanner - Contract-First approach.

Most validation is covered by @beartype and @icontract decorators.
Only edge cases and integration scenarios are tested here.
"""

from __future__ import annotations

import json
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


class TestScanExtensions:
    """Tests for scan_extensions() — v0.4.x extension catalog detection."""

    def test_no_extensions_dir(self, tmp_path: Path) -> None:
        """Returns empty list when extensions/ does not exist."""
        scanner = SpecKitScanner(tmp_path)
        assert scanner.scan_extensions() == []

    def test_empty_extensions_dir(self, tmp_path: Path) -> None:
        """Returns empty list when extensions/ exists but has no catalogs."""
        (tmp_path / "extensions").mkdir()
        scanner = SpecKitScanner(tmp_path)
        assert scanner.scan_extensions() == []

    def test_community_catalog(self, tmp_path: Path) -> None:
        """Parses catalog.community.json and returns extension metadata."""
        ext_dir = tmp_path / "extensions"
        ext_dir.mkdir()
        catalog = [
            {"name": "reconcile", "commands": ["reconcile", "diff"], "version": "1.0.0"},
            {"name": "sync", "commands": ["push", "pull"]},
        ]
        (ext_dir / "catalog.community.json").write_text(json.dumps(catalog))

        scanner = SpecKitScanner(tmp_path)
        result = scanner.scan_extensions()

        assert len(result) == 2
        assert result[0]["name"] == "reconcile"
        assert result[0]["commands"] == ["reconcile", "diff"]
        assert result[1]["name"] == "sync"

    def test_catalog_with_extensions_key(self, tmp_path: Path) -> None:
        """Parses catalog where extensions are under an 'extensions' key."""
        ext_dir = tmp_path / "extensions"
        ext_dir.mkdir()
        catalog = {"extensions": [{"name": "verify", "commands": ["verify"]}]}
        (ext_dir / "catalog.core.json").write_text(json.dumps(catalog))

        scanner = SpecKitScanner(tmp_path)
        result = scanner.scan_extensions()

        assert len(result) == 1
        assert result[0]["name"] == "verify"

    def test_extensionignore_filtering(self, tmp_path: Path) -> None:
        """Extensions listed in .extensionignore are excluded."""
        ext_dir = tmp_path / "extensions"
        ext_dir.mkdir()
        catalog = [
            {"name": "reconcile", "commands": []},
            {"name": "deprecated-ext", "commands": []},
        ]
        (ext_dir / "catalog.community.json").write_text(json.dumps(catalog))
        (tmp_path / ".extensionignore").write_text("deprecated-ext\n# comment line\n")

        scanner = SpecKitScanner(tmp_path)
        result = scanner.scan_extensions()

        assert len(result) == 1
        assert result[0]["name"] == "reconcile"

    def test_malformed_json_catalog(self, tmp_path: Path) -> None:
        """Malformed JSON catalog is skipped with warning, not crash."""
        ext_dir = tmp_path / "extensions"
        ext_dir.mkdir()
        (ext_dir / "catalog.community.json").write_text("{bad json")

        scanner = SpecKitScanner(tmp_path)
        result = scanner.scan_extensions()
        assert result == []

    def test_both_catalogs_merged(self, tmp_path: Path) -> None:
        """Extensions from both core and community catalogs are merged."""
        ext_dir = tmp_path / "extensions"
        ext_dir.mkdir()
        (ext_dir / "catalog.core.json").write_text(json.dumps([{"name": "core-ext", "commands": []}]))
        (ext_dir / "catalog.community.json").write_text(json.dumps([{"name": "comm-ext", "commands": []}]))

        scanner = SpecKitScanner(tmp_path)
        result = scanner.scan_extensions()

        names = [e["name"] for e in result]
        assert "core-ext" in names
        assert "comm-ext" in names


class TestScanPresets:
    """Tests for scan_presets() — v0.4.x preset catalog detection."""

    def test_no_presets_dir(self, tmp_path: Path) -> None:
        """Returns empty list when presets/ does not exist."""
        scanner = SpecKitScanner(tmp_path)
        assert scanner.scan_presets() == []

    def test_json_presets(self, tmp_path: Path) -> None:
        """Detects preset names from JSON files."""
        presets_dir = tmp_path / "presets"
        presets_dir.mkdir()
        (presets_dir / "minimal.json").write_text(json.dumps({"name": "minimal"}))
        (presets_dir / "full.json").write_text(json.dumps({"name": "full-stack"}))

        scanner = SpecKitScanner(tmp_path)
        result = scanner.scan_presets()

        assert "minimal" in result
        assert "full-stack" in result

    def test_directory_presets(self, tmp_path: Path) -> None:
        """Detects preset names from subdirectories."""
        presets_dir = tmp_path / "presets"
        presets_dir.mkdir()
        (presets_dir / "my-preset").mkdir()

        scanner = SpecKitScanner(tmp_path)
        result = scanner.scan_presets()

        assert "my-preset" in result

    def test_malformed_json_uses_stem(self, tmp_path: Path) -> None:
        """Falls back to filename stem when JSON is malformed."""
        presets_dir = tmp_path / "presets"
        presets_dir.mkdir()
        (presets_dir / "broken.json").write_text("{bad")

        scanner = SpecKitScanner(tmp_path)
        result = scanner.scan_presets()

        assert "broken" in result


class TestScanHookEvents:
    """Tests for scan_hook_events() — v0.4.x hook event detection."""

    def test_no_prompts_dir(self, tmp_path: Path) -> None:
        """Returns empty list when .specify/prompts/ does not exist."""
        scanner = SpecKitScanner(tmp_path)
        assert scanner.scan_hook_events() == []

    def test_detects_hook_patterns(self, tmp_path: Path) -> None:
        """Detects before/after hook patterns in prompt templates."""
        prompts_dir = tmp_path / ".specify" / "prompts"
        prompts_dir.mkdir(parents=True)
        (prompts_dir / "tasks.md").write_text("Run before_task validation.\nThen after_task cleanup.\n")
        (prompts_dir / "plan.md").write_text("Execute before_plan checks.\n")

        scanner = SpecKitScanner(tmp_path)
        result = scanner.scan_hook_events()

        assert "before_task" in result
        assert "after_task" in result
        assert "before_plan" in result

    def test_no_hook_patterns(self, tmp_path: Path) -> None:
        """Returns empty list when no hook patterns found in templates."""
        prompts_dir = tmp_path / ".specify" / "prompts"
        prompts_dir.mkdir(parents=True)
        (prompts_dir / "tasks.md").write_text("Normal content without hooks.\n")

        scanner = SpecKitScanner(tmp_path)
        assert scanner.scan_hook_events() == []

    def test_results_are_sorted(self, tmp_path: Path) -> None:
        """Hook events are returned in sorted order."""
        prompts_dir = tmp_path / ".specify" / "prompts"
        prompts_dir.mkdir(parents=True)
        (prompts_dir / "all.md").write_text("after_task before_task after_plan before_plan")

        scanner = SpecKitScanner(tmp_path)
        result = scanner.scan_hook_events()

        assert result == sorted(result)

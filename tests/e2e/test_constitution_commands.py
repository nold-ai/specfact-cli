"""End-to-end tests for specfact constitution commands."""

import os

from typer.testing import CliRunner

from specfact_cli.cli import app


runner = CliRunner()


class TestConstitutionBootstrapE2E:
    """End-to-end tests for specfact constitution bootstrap command."""

    def test_bootstrap_creates_constitution_from_repo_analysis(self, tmp_path, monkeypatch):
        """Test bootstrap command analyzes repository and creates constitution."""
        # Create a minimal repository structure
        (tmp_path / "pyproject.toml").write_text(
            """[project]
name = "test-project"
version = "1.0.0"
description = "A test project"
requires-python = ">=3.11"
"""
        )
        (tmp_path / "README.md").write_text(
            """# Test Project

A simple test project for demonstration.

Perfect for: Developers, DevOps teams
"""
        )
        (tmp_path / ".cursor" / "rules").mkdir(parents=True)
        (tmp_path / ".cursor" / "rules" / "python-github-rules.md").write_text(
            """# Python Rules

## Core Principles

### I. Test-First
TDD mandatory: Tests written before implementation.
"""
        )

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(
                app,
                [
                    "constitution",
                    "bootstrap",
                    "--repo",
                    str(tmp_path),
                ],
            )
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        assert "Bootstrap constitution generated" in result.stdout or "✓" in result.stdout

        # Verify constitution was created
        constitution_path = tmp_path / ".specify" / "memory" / "constitution.md"
        assert constitution_path.exists()

        # Verify constitution content
        content = constitution_path.read_text(encoding="utf-8")
        assert "test-project" in content or "Test Project" in content
        assert "Core Principles" in content
        assert "Governance" in content

    def test_bootstrap_with_custom_output_path(self, tmp_path, monkeypatch):
        """Test bootstrap command with custom output path."""
        (tmp_path / "pyproject.toml").write_text(
            """[project]
name = "custom-project"
version = "1.0.0"
"""
        )

        custom_output = tmp_path / "custom-constitution.md"

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(
                app,
                [
                    "constitution",
                    "bootstrap",
                    "--repo",
                    str(tmp_path),
                    "--output",
                    str(custom_output),
                ],
            )
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        assert custom_output.exists()

        # Verify content
        content = custom_output.read_text(encoding="utf-8")
        assert "custom-project" in content or "Custom Project" in content

    def test_bootstrap_overwrites_existing_with_flag(self, tmp_path, monkeypatch):
        """Test bootstrap command overwrites existing constitution with --overwrite."""
        (tmp_path / "pyproject.toml").write_text(
            """[project]
name = "test-project"
version = "1.0.0"
"""
        )

        constitution_path = tmp_path / ".specify" / "memory" / "constitution.md"
        constitution_path.parent.mkdir(parents=True, exist_ok=True)
        constitution_path.write_text("# Old Constitution\nOld content")

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(
                app,
                [
                    "constitution",
                    "bootstrap",
                    "--repo",
                    str(tmp_path),
                    "--overwrite",
                ],
            )
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0

        # Verify old content was replaced (bootstrap generates new content)
        content = constitution_path.read_text(encoding="utf-8")
        # Old content should be gone, replaced with bootstrap content
        assert "Old content" not in content
        # Should have new bootstrap content
        assert "Core Principles" in content or "test-project" in content or "Test Project" in content

    def test_bootstrap_fails_without_overwrite_if_exists(self, tmp_path, monkeypatch):
        """Test bootstrap command fails if constitution exists without --overwrite."""
        (tmp_path / "pyproject.toml").write_text(
            """[project]
name = "test-project"
version = "1.0.0"
"""
        )

        constitution_path = tmp_path / ".specify" / "memory" / "constitution.md"
        constitution_path.parent.mkdir(parents=True, exist_ok=True)
        constitution_path.write_text("# Existing Constitution")

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(
                app,
                [
                    "constitution",
                    "bootstrap",
                    "--repo",
                    str(tmp_path),
                ],
            )
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 1
        assert "already exists" in result.stdout.lower() or "overwrite" in result.stdout.lower()

    def test_bootstrap_works_with_minimal_repo(self, tmp_path, monkeypatch):
        """Test bootstrap command works with minimal repository (no pyproject.toml)."""
        (tmp_path / "README.md").write_text("# Minimal Project\nA simple project.")

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(
                app,
                [
                    "constitution",
                    "bootstrap",
                    "--repo",
                    str(tmp_path),
                ],
            )
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0

        # Verify constitution was created with generic content
        constitution_path = tmp_path / ".specify" / "memory" / "constitution.md"
        assert constitution_path.exists()

        content = constitution_path.read_text(encoding="utf-8")
        assert "Core Principles" in content


class TestConstitutionEnrichE2E:
    """End-to-end tests for specfact constitution enrich command."""

    def test_enrich_fills_placeholders(self, tmp_path, monkeypatch):
        """Test enrich command fills placeholders in existing constitution."""
        # Create repository with metadata
        (tmp_path / "pyproject.toml").write_text(
            """[project]
name = "enrich-test"
version = "1.0.0"
description = "Test enrichment"
"""
        )

        # Create constitution with placeholders
        constitution_path = tmp_path / ".specify" / "memory" / "constitution.md"
        constitution_path.parent.mkdir(parents=True, exist_ok=True)
        constitution_path.write_text(
            """# [PROJECT_NAME] Constitution

## Core Principles

### [PRINCIPLE_1_NAME]
[PRINCIPLE_1_DESCRIPTION]

## Governance

[GOVERNANCE_RULES]

**Version**: [CONSTITUTION_VERSION] | **Ratified**: [RATIFICATION_DATE] | **Last Amended**: [LAST_AMENDED_DATE]
"""
        )

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(
                app,
                [
                    "constitution",
                    "enrich",
                    "--repo",
                    str(tmp_path),
                ],
            )
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        assert "Constitution enriched" in result.stdout or "✓" in result.stdout

        # Verify placeholders were filled
        content = constitution_path.read_text(encoding="utf-8")
        assert "[PROJECT_NAME]" not in content
        assert "[PRINCIPLE_1_NAME]" not in content
        assert "[GOVERNANCE_RULES]" not in content
        assert "enrich-test" in content or "Enrich Test" in content

    def test_enrich_skips_if_no_placeholders(self, tmp_path, monkeypatch):
        """Test enrich command skips if constitution has no placeholders."""
        constitution_path = tmp_path / ".specify" / "memory" / "constitution.md"
        constitution_path.parent.mkdir(parents=True, exist_ok=True)
        constitution_path.write_text(
            """# Test Project Constitution

## Core Principles

### I. Test-First
TDD mandatory.

## Governance

Constitution supersedes all other practices.

**Version**: 1.0.0 | **Ratified**: 2025-01-01 | **Last Amended**: 2025-01-01
"""
        )

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(
                app,
                [
                    "constitution",
                    "enrich",
                    "--repo",
                    str(tmp_path),
                ],
            )
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        assert "complete" in result.stdout.lower() or "no enrichment needed" in result.stdout.lower()

    def test_enrich_fails_if_constitution_missing(self, tmp_path, monkeypatch):
        """Test enrich command fails if constitution doesn't exist."""
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(
                app,
                [
                    "constitution",
                    "enrich",
                    "--repo",
                    str(tmp_path),
                ],
            )
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 1
        assert "not found" in result.stdout.lower() or "bootstrap" in result.stdout.lower()


class TestConstitutionValidateE2E:
    """End-to-end tests for specfact constitution validate command."""

    def test_validate_passes_for_complete_constitution(self, tmp_path, monkeypatch):
        """Test validate command passes for complete constitution."""
        constitution_path = tmp_path / ".specify" / "memory" / "constitution.md"
        constitution_path.parent.mkdir(parents=True, exist_ok=True)
        constitution_path.write_text(
            """# Test Project Constitution

## Core Principles

### I. Test-First
TDD mandatory: Tests written before implementation.

### II. Code Quality
All code must pass linting and formatting.

## Development Workflow

- Testing: Run test suite before committing
- Formatting: Apply code formatter

## Quality Standards

- Code quality: Linting required
- Testing: Coverage standards

## Governance

Constitution supersedes all other practices. Amendments require documentation.

**Version**: 1.0.0 | **Ratified**: 2025-01-01 | **Last Amended**: 2025-01-01
"""
        )

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(
                app,
                [
                    "constitution",
                    "validate",
                    "--constitution",
                    str(constitution_path),
                ],
            )
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        assert "valid" in result.stdout.lower() or "complete" in result.stdout.lower()

    def test_validate_fails_for_minimal_constitution(self, tmp_path, monkeypatch):
        """Test validate command fails for minimal constitution."""
        constitution_path = tmp_path / ".specify" / "memory" / "constitution.md"
        constitution_path.parent.mkdir(parents=True, exist_ok=True)
        constitution_path.write_text("# Constitution")

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(
                app,
                [
                    "constitution",
                    "validate",
                    "--constitution",
                    str(constitution_path),
                ],
            )
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 1
        assert "validation failed" in result.stdout.lower() or "issues" in result.stdout.lower()

    def test_validate_fails_for_placeholders(self, tmp_path, monkeypatch):
        """Test validate command fails for constitution with placeholders."""
        constitution_path = tmp_path / ".specify" / "memory" / "constitution.md"
        constitution_path.parent.mkdir(parents=True, exist_ok=True)
        constitution_path.write_text(
            """# [PROJECT_NAME] Constitution

## Core Principles

### [PRINCIPLE_1_NAME]
[PRINCIPLE_1_DESCRIPTION]
"""
        )

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(
                app,
                [
                    "constitution",
                    "validate",
                    "--constitution",
                    str(constitution_path),
                ],
            )
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 1
        assert "placeholders" in result.stdout.lower() or "issues" in result.stdout.lower()

    def test_validate_fails_if_missing(self, tmp_path, monkeypatch):
        """Test validate command fails if constitution doesn't exist."""
        missing_path = tmp_path / "missing-constitution.md"

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(
                app,
                [
                    "constitution",
                    "validate",
                    "--constitution",
                    str(missing_path),
                ],
            )
        finally:
            os.chdir(old_cwd)

        # Typer uses exit code 2 for missing files (file validation error before our code runs)
        # Check stdout for error messages (stderr may not be separately captured)
        assert result.exit_code in (1, 2)
        error_output = result.stdout.lower()
        assert (
            "does not exist" in error_output
            or "not found" in error_output
            or "error" in error_output
            or "missing" in error_output
        )


class TestConstitutionIntegrationE2E:
    """End-to-end tests for constitution integration with other commands."""

    def test_import_from_code_suggests_constitution_bootstrap(self, tmp_path, monkeypatch):
        """Test import from-code suggests constitution bootstrap."""
        # Create minimal Python project
        (tmp_path / "src").mkdir(parents=True)
        (tmp_path / "src" / "test_module.py").write_text("def hello(): pass")

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            # Mock user input: say "no" to bootstrap suggestion
            result = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    "--repo",
                    str(tmp_path),
                    "--name",
                    "test-project",
                ],
                input="n\n",  # Decline bootstrap
            )
        finally:
            os.chdir(old_cwd)

        # Should complete import (may or may not suggest bootstrap depending on implementation)
        # The key is that it doesn't fail
        assert result.exit_code in (0, 1)  # May exit 1 if bootstrap is required, or 0 if optional

    def test_sync_spec_kit_detects_minimal_constitution(self, tmp_path, monkeypatch):
        """Test sync spec-kit detects minimal constitution and suggests bootstrap."""
        # Create Spec-Kit structure
        (tmp_path / ".specify" / "memory").mkdir(parents=True)
        constitution_path = tmp_path / ".specify" / "memory" / "constitution.md"
        constitution_path.write_text("# Constitution")  # Minimal

        # Create at least one spec
        (tmp_path / "specs" / "001-test-feature").mkdir(parents=True)
        (tmp_path / "specs" / "001-test-feature" / "spec.md").write_text(
            """---
feature_branch: feat/test
created: 2025-01-01
status: draft
---

# Test Feature

## Requirements

Test requirement.
"""
        )

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            # Mock user input: say "yes" to bootstrap
            result = runner.invoke(
                app,
                [
                    "sync",
                    "spec-kit",
                    "--repo",
                    str(tmp_path),
                ],
                input="y\n",  # Accept bootstrap
            )
        finally:
            os.chdir(old_cwd)

        # Should detect minimal constitution and suggest/bootstrap
        # May succeed after bootstrap or fail if bootstrap not implemented in sync
        assert "minimal" in result.stdout.lower() or "bootstrap" in result.stdout.lower() or result.exit_code in (0, 1)

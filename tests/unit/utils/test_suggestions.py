"""
Unit tests for intelligent suggestions system.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from specfact_cli.utils.context_detection import ProjectContext
from specfact_cli.utils.suggestions import (
    print_suggestions,
    suggest_fixes,
    suggest_improvements,
    suggest_next_steps,
)


class TestSuggestNextSteps:
    """Test suggest_next_steps function."""

    def test_suggest_first_time_setup(self, tmp_path: Path) -> None:
        """Test suggestions for first-time setup."""
        context = ProjectContext(repo_path=tmp_path, has_plan=False, has_config=False)
        suggestions = suggest_next_steps(tmp_path, context)
        assert len(suggestions) > 0
        assert any("import" in s.lower() for s in suggestions)

    def test_suggest_analysis(self, tmp_path: Path) -> None:
        """Test suggestions for analysis."""
        context = ProjectContext(repo_path=tmp_path, has_plan=True, contract_coverage=0.3)
        suggestions = suggest_next_steps(tmp_path, context)
        assert any("analyze" in s.lower() for s in suggestions)

    def test_suggest_specmatic(self, tmp_path: Path) -> None:
        """Test suggestions for Specmatic integration."""
        context = ProjectContext(repo_path=tmp_path, has_plan=True, has_specmatic_config=True, openapi_specs=[])
        suggestions = suggest_next_steps(tmp_path, context)
        assert any("spec" in s.lower() for s in suggestions)

    def test_suggest_enforcement(self, tmp_path: Path) -> None:
        """Test suggestions for enforcement."""
        context = ProjectContext(repo_path=tmp_path, has_plan=True, last_enforcement=None)
        suggestions = suggest_next_steps(tmp_path, context)
        assert any("enforce" in s.lower() for s in suggestions)


class TestSuggestFixes:
    """Test suggest_fixes function."""

    def test_suggest_bundle_not_found(self) -> None:
        """Test suggestions for bundle not found error."""
        error = "Bundle 'test' not found"
        suggestions = suggest_fixes(error)
        assert len(suggestions) > 0
        assert any("plan select" in s.lower() for s in suggestions)

    def test_suggest_contract_validation_error(self) -> None:
        """Test suggestions for contract validation error."""
        error = "Contract violation detected"
        suggestions = suggest_fixes(error)
        assert len(suggestions) > 0
        assert any("analyze" in s.lower() for s in suggestions)

    def test_suggest_specmatic_error(self) -> None:
        """Test suggestions for Specmatic error."""
        error = "Specmatic validation failed"
        suggestions = suggest_fixes(error)
        assert len(suggestions) > 0
        assert any("spec" in s.lower() for s in suggestions)

    def test_suggest_import_error(self) -> None:
        """Test suggestions for import error."""
        error = "Import failed"
        suggestions = suggest_fixes(error)
        assert len(suggestions) > 0
        assert any("import" in s.lower() for s in suggestions)


class TestSuggestImprovements:
    """Test suggest_improvements function."""

    def test_suggest_low_coverage(self, tmp_path: Path) -> None:
        """Test suggestions for low contract coverage."""
        context = ProjectContext(repo_path=tmp_path, contract_coverage=0.2)
        suggestions = suggest_improvements(context)
        assert len(suggestions) > 0
        assert any("analyze" in s.lower() for s in suggestions)

    def test_suggest_missing_openapi(self, tmp_path: Path) -> None:
        """Test suggestions for missing OpenAPI specs."""
        context = ProjectContext(repo_path=tmp_path, has_plan=True, openapi_specs=[])
        suggestions = suggest_improvements(context)
        assert any("generate" in s.lower() or "contract" in s.lower() for s in suggestions)

    def test_suggest_specmatic_init(self, tmp_path: Path) -> None:
        """Test suggestions for Specmatic initialization."""
        context = ProjectContext(
            repo_path=tmp_path, has_plan=True, openapi_specs=[tmp_path / "openapi.yaml"], has_specmatic_config=False
        )
        suggestions = suggest_improvements(context)
        assert any("spec init" in s.lower() for s in suggestions)


class TestPrintSuggestions:
    """Test print_suggestions function."""

    def test_print_suggestions_empty(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test printing empty suggestions."""
        print_suggestions([])
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_print_suggestions_non_empty(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test printing non-empty suggestions."""
        suggestions = ["specfact analyze", "specfact import"]
        print_suggestions(suggestions, title="Test Suggestions")
        captured = capsys.readouterr()
        assert "Test Suggestions" in captured.out
        assert "specfact analyze" in captured.out

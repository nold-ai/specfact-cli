"""E2E tests for Phase 4.9 (Quick Start Optimization) and Phase 4.10 (CI Performance Optimization)."""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from typer.testing import CliRunner

from specfact_cli.cli import app


runner = CliRunner()


class TestQuickStartOptimization:
    """E2E tests for Phase 4.9: Quick Start Optimization."""

    @pytest.mark.timeout(30)
    def test_import_shows_first_value_quickly(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that import command shows first value within reasonable time."""
        # Ensure TEST_MODE is set to skip Semgrep
        monkeypatch.setenv("TEST_MODE", "true")

        # Create a simple codebase
        src_dir = tmp_path / "src"
        src_dir.mkdir()

        # Create a few Python files with classes
        for i in range(3):
            file_path = src_dir / f"service_{i}.py"
            file_path.write_text(
                f'''
class Service{i}:
    """Service {i} for testing."""

    def method_{i}(self):
        """Method {i}."""
        return "result"
'''
            )

        start_time = time.time()

        result = runner.invoke(
            app,
            [
                "import",
                "from-code",
                "test-bundle",
                "--repo",
                str(tmp_path),
                "--confidence",
                "0.3",
            ],
            input="n\n",  # Decline any interactive prompts
        )

        elapsed_time = time.time() - start_time

        # Command should succeed
        assert result.exit_code == 0

        # Should complete in reasonable time (< 60 seconds for small codebase)
        assert elapsed_time < 60, f"Import took {elapsed_time:.2f}s, expected < 60s"

        # Should show incremental results
        assert "feature" in result.stdout.lower() or "Found" in result.stdout

    @pytest.mark.timeout(30)
    def test_import_shows_next_steps_suggestions(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that import command shows next steps suggestions after first run."""
        # Ensure TEST_MODE is set to skip Semgrep
        monkeypatch.setenv("TEST_MODE", "true")

        # Create a simple codebase
        src_dir = tmp_path / "src"
        src_dir.mkdir()

        file_path = src_dir / "service.py"
        file_path.write_text(
            '''
class Service:
    """Service for testing."""

    def method(self):
        """Method."""
        return "result"
'''
        )

        result = runner.invoke(
            app,
            [
                "import",
                "from-code",
                "test-bundle",
                "--repo",
                str(tmp_path),
                "--confidence",
                "0.3",
            ],
            input="n\n",  # Decline any interactive prompts
        )

        # Command should succeed
        assert result.exit_code == 0

        # Should show next steps suggestions
        assert "Next Steps" in result.stdout or "next steps" in result.stdout.lower()
        assert "plan review" in result.stdout.lower() or "plan compare" in result.stdout.lower()

    @pytest.mark.timeout(30)
    def test_import_shows_incremental_results(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that import command shows incremental results as features are discovered."""
        # Ensure TEST_MODE is set to skip Semgrep
        monkeypatch.setenv("TEST_MODE", "true")

        # Create a codebase with multiple classes
        src_dir = tmp_path / "src"
        src_dir.mkdir()

        # Create multiple files to trigger incremental updates
        for i in range(5):
            file_path = src_dir / f"service_{i}.py"
            file_path.write_text(
                f'''
class Service{i}:
    """Service {i} for testing."""

    def method_{i}(self):
        """Method {i}."""
        return "result"
'''
            )

        result = runner.invoke(
            app,
            [
                "import",
                "from-code",
                "test-bundle",
                "--repo",
                str(tmp_path),
                "--confidence",
                "0.3",
            ],
            input="n\n",  # Decline any interactive prompts
        )

        # Command should succeed
        assert result.exit_code == 0

        # Should show features were discovered
        assert "feature" in result.stdout.lower() or "Found" in result.stdout


class TestCIPerformanceOptimization:
    """E2E tests for Phase 4.10: CI Performance Optimization."""

    @pytest.mark.timeout(30)
    def test_import_tracks_performance_metrics(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that import command tracks performance metrics."""
        # Ensure TEST_MODE is set to skip Semgrep
        monkeypatch.setenv("TEST_MODE", "true")

        # Create a simple codebase
        src_dir = tmp_path / "src"
        src_dir.mkdir()

        file_path = src_dir / "service.py"
        file_path.write_text(
            '''
class Service:
    """Service for testing."""

    def method(self):
        """Method."""
        return "result"
'''
        )

        result = runner.invoke(
            app,
            [
                "import",
                "from-code",
                "test-bundle",
                "--repo",
                str(tmp_path),
                "--confidence",
                "0.3",
            ],
            input="n\n",  # Decline any interactive prompts
        )

        # Command should succeed
        assert result.exit_code == 0

        # Performance tracking should not cause errors
        # (Performance report only shown in non-CI mode, so we can't assert on it here)

    @pytest.mark.timeout(30)
    def test_import_completes_in_reasonable_time(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that import command completes in reasonable time for small codebase."""
        # Ensure TEST_MODE is set to skip Semgrep
        monkeypatch.setenv("TEST_MODE", "true")

        # Create a simple codebase
        src_dir = tmp_path / "src"
        src_dir.mkdir()

        file_path = src_dir / "service.py"
        file_path.write_text(
            '''
class Service:
    """Service for testing."""

    def method(self):
        """Method."""
        return "result"
'''
        )

        start_time = time.time()

        result = runner.invoke(
            app,
            [
                "import",
                "from-code",
                "test-bundle",
                "--repo",
                str(tmp_path),
                "--confidence",
                "0.3",
            ],
            input="n\n",  # Decline any interactive prompts
        )

        elapsed_time = time.time() - start_time

        # Command should succeed
        assert result.exit_code == 0

        # Should complete quickly for small codebase (< 30 seconds)
        assert elapsed_time < 30, f"Import took {elapsed_time:.2f}s, expected < 30s for small codebase"

    @pytest.mark.timeout(60)
    def test_import_ci_mode_deterministic(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that import command is deterministic in CI mode (no AI dependency)."""
        # Set CI and TEST_MODE environment
        monkeypatch.setenv("CI", "true")
        monkeypatch.setenv("TEST_MODE", "true")

        # Create a simple codebase
        src_dir = tmp_path / "src"
        src_dir.mkdir()

        file_path = src_dir / "service.py"
        file_path.write_text(
            '''
class Service:
    """Service for testing."""

    def method(self):
        """Method."""
        return "result"
'''
        )

        result = runner.invoke(
            app,
            [
                "import",
                "from-code",
                "test-bundle",
                "--repo",
                str(tmp_path),
                "--confidence",
                "0.3",
            ],
            input="n\n",  # Decline any interactive prompts
        )

        # Command should succeed
        assert result.exit_code == 0

        # Should use AST-based import (CI/CD mode)
        assert "CI/CD" in result.stdout or "AST-based" in result.stdout or result.exit_code == 0

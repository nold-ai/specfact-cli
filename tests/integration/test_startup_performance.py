"""
Integration tests for startup performance optimization.

Tests that startup checks are properly optimized and startup time is acceptable.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from specfact_cli.cli import app
from specfact_cli.utils.metadata import (
    update_metadata,
)
from specfact_cli.utils.startup_checks import print_startup_checks


class TestStartupPerformance:
    """Integration tests for startup performance."""

    def test_startup_time_under_threshold(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that startup time is under 2 seconds when checks are skipped."""
        mock_home = tmp_path / "home"
        mock_home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: mock_home)

        # Set metadata to skip checks
        from specfact_cli import __version__

        update_metadata(
            last_checked_version=__version__,
            last_version_check_timestamp=datetime.now(UTC).isoformat(),
        )

        start_time = time.time()
        print_startup_checks(repo_path=tmp_path, check_version=True, skip_checks=False)
        elapsed = time.time() - start_time

        # Should be very fast when checks are skipped (< 0.1s)
        assert elapsed < 0.1, f"Startup took {elapsed:.2f}s, expected < 0.1s"

    def test_checks_skipped_when_appropriate(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that checks are skipped when version unchanged and recent timestamp."""
        mock_home = tmp_path / "home"
        mock_home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: mock_home)

        from specfact_cli import __version__

        # Set metadata to indicate checks not needed
        update_metadata(
            last_checked_version=__version__,
            last_version_check_timestamp=datetime.now(UTC).isoformat(),
        )

        with (
            patch("specfact_cli.utils.startup_checks.check_ide_templates") as mock_templates,
            patch("specfact_cli.utils.startup_checks.check_pypi_version") as mock_version,
        ):
            print_startup_checks(repo_path=tmp_path, check_version=True)

            # Both checks should be skipped
            mock_templates.assert_not_called()
            mock_version.assert_not_called()

    def test_checks_run_when_version_changed(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that template check runs when version changed."""
        mock_home = tmp_path / "home"
        mock_home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: mock_home)

        # Set metadata with different version
        update_metadata(last_checked_version="0.9.0")

        with patch("specfact_cli.utils.startup_checks.check_ide_templates") as mock_templates:
            mock_templates.return_value = None
            print_startup_checks(repo_path=tmp_path, check_version=False)

            # Template check should run
            mock_templates.assert_called_once()

    def test_checks_run_when_24h_elapsed(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that version check runs when 24 hours elapsed."""
        mock_home = tmp_path / "home"
        mock_home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: mock_home)

        # Set old timestamp
        old_timestamp = (datetime.now(UTC) - timedelta(hours=25)).isoformat()
        update_metadata(last_version_check_timestamp=old_timestamp)

        with patch("specfact_cli.utils.startup_checks.check_pypi_version") as mock_version:
            from specfact_cli.utils.startup_checks import VersionCheckResult

            mock_version.return_value = VersionCheckResult(
                current_version="1.0.0",
                latest_version="1.0.0",
                update_available=False,
                update_type=None,
                error=None,
            )

            print_startup_checks(repo_path=tmp_path, check_version=True)

            # Version check should run
            mock_version.assert_called_once()

    def test_cli_startup_with_skip_checks_flag(self) -> None:
        """Test that --skip-checks flag works in CLI."""
        runner = CliRunner()
        result = runner.invoke(app, ["--skip-checks", "--help"])

        # Should succeed (help command works)
        assert result.exit_code == 0

    def test_cli_startup_performance(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that CLI startup is fast with optimized checks."""
        mock_home = tmp_path / "home"
        mock_home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: mock_home)

        # Set metadata to skip checks
        from specfact_cli import __version__

        update_metadata(
            last_checked_version=__version__,
            last_version_check_timestamp=datetime.now(UTC).isoformat(),
        )

        runner = CliRunner()
        start_time = time.time()
        result = runner.invoke(app, ["--version"])
        elapsed = time.time() - start_time

        # Should be fast (< 1 second for version command)
        assert elapsed < 1.0, f"CLI startup took {elapsed:.2f}s, expected < 1.0s"
        assert result.exit_code == 0

    def test_cli_version_emits_single_protocol_summary_line(self) -> None:
        """CLI smoke test: protocol summary line should be emitted once per startup."""
        runner = CliRunner()
        result = runner.invoke(app, ["--version"])

        assert result.exit_code == 0
        assert result.output.count("Protocol-compliant:") <= 1

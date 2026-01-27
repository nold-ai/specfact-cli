"""Integration tests for startup checks in CLI context."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from specfact_cli.utils.startup_checks import print_startup_checks


class TestStartupChecksIntegration:
    """Integration tests for startup checks."""

    @patch("specfact_cli.utils.startup_checks.get_last_checked_version", return_value=None)
    @patch("specfact_cli.utils.startup_checks.get_last_version_check_timestamp", return_value=None)
    @patch("specfact_cli.utils.startup_checks.check_ide_templates")
    @patch("specfact_cli.utils.startup_checks.check_pypi_version")
    @patch("specfact_cli.utils.startup_checks.console")
    def test_startup_checks_run_on_command(
        self,
        mock_console: MagicMock,
        mock_version: MagicMock,
        mock_templates: MagicMock,
        _mock_timestamp: MagicMock,
        _mock_version_meta: MagicMock,
    ):
        """Test that startup checks run when a command is executed."""
        mock_templates.return_value = None
        mock_version.return_value = MagicMock(
            current_version="1.0.0",
            latest_version="1.0.0",
            update_available=False,
            update_type=None,
            error=None,
        )

        # Mock sys.argv to simulate a command
        with patch("sys.argv", ["specfact", "backlog", "list"]):
            # We can't easily test cli_main without full setup, so test print_startup_checks directly
            print_startup_checks()

        # Verify checks were called
        mock_templates.assert_called_once()
        mock_version.assert_called_once()

    @patch("specfact_cli.utils.startup_checks.get_last_checked_version", return_value=None)
    @patch("specfact_cli.utils.startup_checks.get_last_version_check_timestamp", return_value=None)
    @patch("specfact_cli.utils.startup_checks.check_ide_templates")
    @patch("specfact_cli.utils.startup_checks.check_pypi_version")
    def test_startup_checks_graceful_failure(
        self,
        mock_version: MagicMock,
        mock_templates: MagicMock,
        _mock_timestamp: MagicMock,
        _mock_version_meta: MagicMock,
    ):
        """Test that startup check failures are handled gracefully at CLI level."""
        # Make template check raise an exception
        mock_templates.side_effect = Exception("Template check failed")
        mock_version.side_effect = Exception("Version check failed")

        # The function itself will raise exceptions, but CLI wraps it with contextlib.suppress
        # Test that exceptions are raised (they will be caught by CLI wrapper)
        with pytest.raises(Exception, match="Template check failed"):
            print_startup_checks()

        # Verify functions were called
        mock_templates.assert_called_once()
        # Version check may not be called if template check raises first

    @patch("specfact_cli.utils.startup_checks.get_last_checked_version", return_value=None)
    @patch("specfact_cli.utils.startup_checks.get_last_version_check_timestamp", return_value=None)
    @patch("specfact_cli.utils.startup_checks.check_ide_templates")
    @patch("specfact_cli.utils.startup_checks.check_pypi_version")
    @patch("specfact_cli.utils.startup_checks.console")
    def test_startup_checks_both_warnings(
        self,
        mock_console: MagicMock,
        mock_version: MagicMock,
        mock_templates: MagicMock,
        _mock_timestamp: MagicMock,
        _mock_version_meta: MagicMock,
        tmp_path: Path,
    ):
        """Test that both template and version warnings can be shown."""
        mock_templates.return_value = MagicMock(
            ide="cursor",
            templates_outdated=True,
            missing_templates=["specfact.01-import.md"],
            outdated_templates=[],
            ide_dir=tmp_path / ".cursor" / "commands",
        )
        mock_version.return_value = MagicMock(
            current_version="1.0.0",
            latest_version="2.0.0",
            update_available=True,
            update_type="major",
            error=None,
        )

        print_startup_checks()

        # Should print both warnings
        assert mock_console.print.call_count >= 2

    def test_startup_checks_real_template_check(self, tmp_path: Path):
        """Test template checking with real file system operations."""
        # Create a minimal IDE directory structure
        ide_dir = tmp_path / ".cursor" / "commands"
        ide_dir.mkdir(parents=True)

        templates_dir = tmp_path / "resources" / "prompts"
        templates_dir.mkdir(parents=True)
        (templates_dir / "specfact.01-import.md").write_text("# Import")

        with (
            patch("specfact_cli.utils.startup_checks.detect_ide", return_value="cursor"),
            patch(
                "specfact_cli.utils.startup_checks.IDE_CONFIG",
                {"cursor": {"folder": ".cursor/commands", "format": "md"}},
            ),
            patch("specfact_cli.utils.startup_checks.find_package_resources_path", return_value=templates_dir),
            patch(
                "specfact_cli.utils.ide_setup.SPECFACT_COMMANDS",
                ["specfact.01-import"],
            ),
        ):
            result = print_startup_checks(repo_path=tmp_path)

            # Function should complete without error
            assert result is None

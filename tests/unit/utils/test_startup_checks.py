"""Unit tests for startup checks utilities."""

from __future__ import annotations

import sys
import time
from datetime import UTC
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
import requests

from specfact_cli.utils.metadata import (
    update_metadata,
)
from specfact_cli.utils.startup_checks import (
    TemplateCheckResult,
    VersionCheckResult,
    calculate_file_hash,
    check_ide_templates,
    check_pypi_version,
    print_startup_checks,
)


class TestCalculateFileHash:
    """Test file hash calculation."""

    def test_calculate_file_hash(self, tmp_path: Path):
        """Test hash calculation for a file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        hash_value = calculate_file_hash(test_file)

        assert isinstance(hash_value, str)
        assert len(hash_value) == 64  # SHA256 hex string length
        assert hash_value.isalnum() or all(c in "abcdef0123456789" for c in hash_value)

    def test_calculate_file_hash_consistent(self, tmp_path: Path):
        """Test that hash is consistent for same content."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        hash1 = calculate_file_hash(test_file)
        hash2 = calculate_file_hash(test_file)

        assert hash1 == hash2

    def test_calculate_file_hash_different_content(self, tmp_path: Path):
        """Test that different content produces different hashes."""
        file1 = tmp_path / "test1.txt"
        file1.write_text("content 1")

        file2 = tmp_path / "test2.txt"
        file2.write_text("content 2")

        hash1 = calculate_file_hash(file1)
        hash2 = calculate_file_hash(file2)

        assert hash1 != hash2


class TestCheckIDETemplates:
    """Test IDE template checking."""

    def test_check_ide_templates_no_ide_detected(self, monkeypatch, tmp_path: Path):
        """Test when no IDE is detected."""
        with patch("specfact_cli.utils.startup_checks.detect_ide", side_effect=Exception("No IDE")):
            result = check_ide_templates(tmp_path)
            assert result is None

    def test_check_ide_templates_ide_dir_not_exists(self, monkeypatch, tmp_path: Path):
        """Test when IDE directory doesn't exist."""
        with (
            patch("specfact_cli.utils.startup_checks.detect_ide", return_value="cursor"),
            patch(
                "specfact_cli.utils.startup_checks.IDE_CONFIG",
                {"cursor": {"folder": ".cursor/commands", "format": "md"}},
            ),
        ):
            result = check_ide_templates(tmp_path)
            assert result is None

    def test_check_ide_templates_no_templates_dir(self, monkeypatch, tmp_path: Path):
        """Test when templates directory is not found."""
        ide_dir = tmp_path / ".cursor" / "commands"
        ide_dir.mkdir(parents=True)

        with (
            patch("specfact_cli.utils.startup_checks.detect_ide", return_value="cursor"),
            patch(
                "specfact_cli.utils.startup_checks.IDE_CONFIG",
                {"cursor": {"folder": ".cursor/commands", "format": "md"}},
            ),
            patch("specfact_cli.utils.startup_checks.find_package_resources_path", return_value=None),
        ):
            result = check_ide_templates(tmp_path)
            assert result is None

    def test_check_ide_templates_missing_templates(self, monkeypatch, tmp_path: Path):
        """Test when templates are missing."""
        ide_dir = tmp_path / ".cursor" / "commands"
        ide_dir.mkdir(parents=True)

        templates_dir = tmp_path / "resources" / "prompts"
        templates_dir.mkdir(parents=True)
        # Create a source template
        (templates_dir / "specfact.01-import.md").write_text("# Import command")

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
            result = check_ide_templates(tmp_path)

            assert result is not None
            assert result.ide == "cursor"
            assert result.templates_outdated is True
            assert "specfact.01-import.md" in result.missing_templates
            assert len(result.outdated_templates) == 0

    def test_check_ide_templates_outdated_templates(self, monkeypatch, tmp_path: Path):
        """Test when templates are outdated (source is newer)."""
        ide_dir = tmp_path / ".cursor" / "commands"
        ide_dir.mkdir(parents=True)

        templates_dir = tmp_path / "resources" / "prompts"
        templates_dir.mkdir(parents=True)

        # Create source template
        source_file = templates_dir / "specfact.01-import.md"
        source_file.write_text("# Import command - updated")

        # Create IDE template (older)
        ide_file = ide_dir / "specfact.01-import.md"
        ide_file.write_text("# Import command - old")

        # Make source file newer (by at least 1 second)
        time.sleep(1.1)
        source_file.touch()

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
            result = check_ide_templates(tmp_path)

            assert result is not None
            assert result.ide == "cursor"
            assert result.templates_outdated is True
            assert len(result.missing_templates) == 0
            assert "specfact.01-import.md" in result.outdated_templates

    def test_check_ide_templates_up_to_date(self, monkeypatch, tmp_path: Path):
        """Test when templates are up to date."""
        ide_dir = tmp_path / ".cursor" / "commands"
        ide_dir.mkdir(parents=True)

        templates_dir = tmp_path / "resources" / "prompts"
        templates_dir.mkdir(parents=True)

        # Create source template
        source_file = templates_dir / "specfact.01-import.md"
        source_file.write_text("# Import command")

        # Create IDE template (newer or same age)
        ide_file = ide_dir / "specfact.01-import.md"
        ide_file.write_text("# Import command")
        ide_file.touch()

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
            result = check_ide_templates(tmp_path)

            assert result is not None
            assert result.ide == "cursor"
            assert result.templates_outdated is False
            assert len(result.missing_templates) == 0
            assert len(result.outdated_templates) == 0

    def test_check_ide_templates_different_formats(self, monkeypatch, tmp_path: Path):
        """Test template checking with different IDE formats (prompt.md, toml)."""
        ide_dir = tmp_path / ".gemini" / "commands"
        ide_dir.mkdir(parents=True)

        templates_dir = tmp_path / "resources" / "prompts"
        templates_dir.mkdir(parents=True)
        (templates_dir / "specfact.01-import.md").write_text("# Import")

        with (
            patch("specfact_cli.utils.startup_checks.detect_ide", return_value="gemini"),
            patch(
                "specfact_cli.utils.startup_checks.IDE_CONFIG",
                {"gemini": {"folder": ".gemini/commands", "format": "toml"}},
            ),
            patch("specfact_cli.utils.startup_checks.find_package_resources_path", return_value=templates_dir),
            patch(
                "specfact_cli.utils.ide_setup.SPECFACT_COMMANDS",
                ["specfact.01-import"],
            ),
        ):
            result = check_ide_templates(tmp_path)

            assert result is not None
            # Should look for specfact.01-import.toml in IDE dir
            assert "specfact.01-import.toml" in result.missing_templates


class TestCheckPyPIVersion:
    """Test PyPI version checking."""

    @patch("specfact_cli.utils.startup_checks.requests.get")
    @patch("specfact_cli.utils.startup_checks.__version__", "1.0.0")
    def test_check_pypi_version_update_available_major(self, mock_get: MagicMock):
        """Test when major update is available."""
        mock_response = Mock()
        mock_response.json.return_value = {"info": {"version": "2.0.0"}}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Create mock version objects
        mock_current = Mock()
        mock_current.major = 1
        mock_current.minor = 0
        mock_current.micro = 0

        mock_latest = Mock()
        mock_latest.major = 2
        mock_latest.minor = 0
        mock_latest.micro = 0
        mock_latest.__gt__ = lambda other: True  # latest > current

        # Mock the packaging.version module
        mock_version_module = Mock()
        mock_version_module.parse.side_effect = [mock_current, mock_latest]

        with (
            patch.dict(sys.modules, {"packaging.version": mock_version_module}),
            patch("specfact_cli.utils.startup_checks.version", mock_version_module, create=True),
        ):
            result = check_pypi_version()

            assert result.current_version == "1.0.0"
            assert result.latest_version == "2.0.0"
            assert result.update_available is True
            assert result.update_type == "major"
            assert result.error is None

    @patch("specfact_cli.utils.startup_checks.requests.get")
    @patch("specfact_cli.utils.startup_checks.__version__", "1.0.0")
    def test_check_pypi_version_update_available_minor(self, mock_get: MagicMock):
        """Test when minor update is available."""
        mock_response = Mock()
        mock_response.json.return_value = {"info": {"version": "1.1.0"}}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        mock_current = Mock()
        mock_current.major = 1
        mock_current.minor = 0
        mock_current.micro = 0

        mock_latest = Mock()
        mock_latest.major = 1
        mock_latest.minor = 1
        mock_latest.micro = 0
        mock_latest.__gt__ = lambda other: True

        mock_version_module = Mock()
        mock_version_module.parse.side_effect = [mock_current, mock_latest]

        with (
            patch.dict(sys.modules, {"packaging.version": mock_version_module}),
            patch("specfact_cli.utils.startup_checks.version", mock_version_module, create=True),
        ):
            result = check_pypi_version()

            assert result.current_version == "1.0.0"
            assert result.latest_version == "1.1.0"
            assert result.update_available is True
            assert result.update_type == "minor"
            assert result.error is None

    @patch("specfact_cli.utils.startup_checks.requests.get")
    @patch("specfact_cli.utils.startup_checks.__version__", "1.0.0")
    def test_check_pypi_version_update_available_patch(self, mock_get: MagicMock):
        """Test when patch update is available."""
        mock_response = Mock()
        mock_response.json.return_value = {"info": {"version": "1.0.1"}}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        mock_current = Mock()
        mock_current.major = 1
        mock_current.minor = 0
        mock_current.micro = 0

        mock_latest = Mock()
        mock_latest.major = 1
        mock_latest.minor = 0
        mock_latest.micro = 1
        mock_latest.__gt__ = lambda other: True

        mock_version_module = Mock()
        mock_version_module.parse.side_effect = [mock_current, mock_latest]

        with (
            patch.dict(sys.modules, {"packaging.version": mock_version_module}),
            patch("specfact_cli.utils.startup_checks.version", mock_version_module, create=True),
        ):
            result = check_pypi_version()

            assert result.current_version == "1.0.0"
            assert result.latest_version == "1.0.1"
            assert result.update_available is True
            assert result.update_type == "patch"
            assert result.error is None

    @patch("specfact_cli.utils.startup_checks.requests.get")
    @patch("specfact_cli.utils.startup_checks.__version__", "1.0.0")
    def test_check_pypi_version_no_update(self, mock_get: MagicMock):
        """Test when no update is available."""
        mock_response = Mock()
        mock_response.json.return_value = {"info": {"version": "1.0.0"}}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        mock_version_obj = Mock()
        mock_version_obj.major = 1
        mock_version_obj.minor = 0
        mock_version_obj.micro = 0
        mock_version_obj.__gt__ = lambda other: False  # latest is not greater than current

        mock_version_module = Mock()
        mock_version_module.parse.return_value = mock_version_obj

        with (
            patch.dict(sys.modules, {"packaging.version": mock_version_module}),
            patch("specfact_cli.utils.startup_checks.version", mock_version_module, create=True),
        ):
            result = check_pypi_version()

            assert result.current_version == "1.0.0"
            assert result.latest_version == "1.0.0"
            assert result.update_available is False
            assert result.update_type is None
            assert result.error is None

    @patch("specfact_cli.utils.startup_checks.requests.get")
    @patch("specfact_cli.utils.startup_checks.__version__", "1.0.0")
    def test_check_pypi_version_network_error(self, mock_get: MagicMock):
        """Test handling of network errors."""
        mock_get.side_effect = requests.RequestException("Network error")

        result = check_pypi_version()

        assert result.current_version == "1.0.0"
        assert result.latest_version is None
        assert result.update_available is False
        assert result.update_type is None
        assert result.error is not None
        assert "Failed to check PyPI" in result.error

    @patch("specfact_cli.utils.startup_checks.requests.get")
    @patch("specfact_cli.utils.startup_checks.__version__", "1.0.0")
    def test_check_pypi_version_no_version_in_response(self, mock_get: MagicMock):
        """Test when PyPI response doesn't contain version."""
        mock_response = Mock()
        mock_response.json.return_value = {"info": {}}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = check_pypi_version()

        assert result.current_version == "1.0.0"
        assert result.latest_version is None
        assert result.update_available is False
        assert result.update_type is None
        assert result.error is not None
        assert "Could not determine latest version" in result.error

    @patch("specfact_cli.utils.startup_checks.requests.get")
    @patch("specfact_cli.utils.startup_checks.__version__", "1.0.0")
    def test_check_pypi_version_fallback_without_packaging(self, mock_get: MagicMock):
        """Test fallback when packaging module is not available."""
        mock_response = Mock()
        mock_response.json.return_value = {"info": {"version": "1.0.1"}}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Mock ImportError when trying to import packaging.version
        original_import = __import__

        def mock_import(name, *args, **kwargs):
            if name == "packaging":
                raise ImportError("No module named 'packaging'")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            result = check_pypi_version()

            assert result.current_version == "1.0.0"
            assert result.latest_version == "1.0.1"
            assert result.update_available is True
            assert result.update_type == "unknown"
            assert result.error is None

    @patch("specfact_cli.utils.startup_checks.requests.get")
    @patch("specfact_cli.utils.startup_checks.__version__", "1.0.0")
    def test_check_pypi_version_timeout(self, mock_get: MagicMock):
        """Test timeout handling."""
        mock_get.side_effect = requests.Timeout("Request timed out")

        result = check_pypi_version(timeout=1)

        assert result.current_version == "1.0.0"
        assert result.latest_version is None
        assert result.update_available is False
        assert result.error is not None


class TestPrintStartupChecks:
    """Test startup checks printing."""

    @patch("specfact_cli.utils.startup_checks.check_ide_templates")
    @patch("specfact_cli.utils.startup_checks.check_pypi_version")
    @patch("specfact_cli.utils.startup_checks.console")
    def test_print_startup_checks_no_issues(
        self, mock_console: MagicMock, mock_version: MagicMock, mock_templates: MagicMock
    ):
        """Test when no issues are found."""
        mock_templates.return_value = None
        mock_version.return_value = VersionCheckResult(
            current_version="1.0.0",
            latest_version="1.0.0",
            update_available=False,
            update_type=None,
            error=None,
        )

        print_startup_checks()

        # Should not print any warnings
        mock_console.print.assert_not_called()

    @patch("specfact_cli.utils.startup_checks.get_last_checked_version", return_value=None)
    @patch("specfact_cli.utils.startup_checks.get_last_version_check_timestamp", return_value=None)
    @patch("specfact_cli.utils.startup_checks.check_ide_templates")
    @patch("specfact_cli.utils.startup_checks.check_pypi_version")
    @patch("specfact_cli.utils.startup_checks.console")
    def test_print_startup_checks_outdated_templates(
        self,
        mock_console: MagicMock,
        mock_version: MagicMock,
        mock_templates: MagicMock,
        _mock_timestamp: MagicMock,
        _mock_version_meta: MagicMock,
        tmp_path: Path,
    ):
        """Test printing warning for outdated templates."""
        mock_templates.return_value = TemplateCheckResult(
            ide="cursor",
            templates_outdated=True,
            missing_templates=["specfact.01-import.md"],
            outdated_templates=[],
            ide_dir=tmp_path / ".cursor" / "commands",
        )
        mock_version.return_value = VersionCheckResult(
            current_version="1.0.0",
            latest_version="1.0.0",
            update_available=False,
            update_type=None,
            error=None,
        )

        print_startup_checks()

        # Should print template warning
        assert mock_console.print.call_count >= 1
        # Check that Panel was called with warning message
        # Panel is passed as first argument to console.print
        for call in mock_console.print.call_args_list:
            args = call[0] if call[0] else []
            for arg in args:
                if hasattr(arg, "renderable"):
                    # It's a Panel, check its renderable content
                    renderable_str = str(arg.renderable)
                    if "IDE Templates Outdated" in renderable_str:
                        return
                elif isinstance(arg, str) and "IDE Templates Outdated" in arg:
                    return
        pytest.fail("Template warning message not found in console.print calls")

    @patch("specfact_cli.utils.startup_checks.get_last_checked_version", return_value=None)
    @patch("specfact_cli.utils.startup_checks.get_last_version_check_timestamp", return_value=None)
    @patch("specfact_cli.utils.startup_checks.check_ide_templates")
    @patch("specfact_cli.utils.startup_checks.check_pypi_version")
    @patch("specfact_cli.utils.startup_checks.console")
    def test_print_startup_checks_version_update_major(
        self,
        mock_console: MagicMock,
        mock_version: MagicMock,
        mock_templates: MagicMock,
        _mock_timestamp: MagicMock,
        _mock_version_meta: MagicMock,
    ):
        """Test printing warning for major version update."""
        mock_templates.return_value = None
        mock_version.return_value = VersionCheckResult(
            current_version="1.0.0",
            latest_version="2.0.0",
            update_available=True,
            update_type="major",
            error=None,
        )

        print_startup_checks()

        # Should print version update warning
        assert mock_console.print.call_count >= 1
        # Panel is passed as first argument to console.print
        for call in mock_console.print.call_args_list:
            args = call[0] if call[0] else []
            for arg in args:
                if hasattr(arg, "renderable"):
                    renderable_str = str(arg.renderable)
                    if "MAJOR Update Available" in renderable_str or "major" in renderable_str.lower():
                        return
                elif isinstance(arg, str) and ("MAJOR Update Available" in arg or "major" in arg.lower()):
                    return
        pytest.fail("Major version update message not found in console.print calls")

    @patch("specfact_cli.utils.startup_checks.get_last_checked_version", return_value=None)
    @patch("specfact_cli.utils.startup_checks.get_last_version_check_timestamp", return_value=None)
    @patch("specfact_cli.utils.startup_checks.check_ide_templates")
    @patch("specfact_cli.utils.startup_checks.check_pypi_version")
    @patch("specfact_cli.utils.startup_checks.console")
    def test_print_startup_checks_version_update_minor(
        self,
        mock_console: MagicMock,
        mock_version: MagicMock,
        mock_templates: MagicMock,
        _mock_timestamp: MagicMock,
        _mock_version_meta: MagicMock,
    ):
        """Test printing warning for minor version update."""
        mock_templates.return_value = None
        mock_version.return_value = VersionCheckResult(
            current_version="1.0.0",
            latest_version="1.1.0",
            update_available=True,
            update_type="minor",
            error=None,
        )

        print_startup_checks()

        # Should print version update warning
        assert mock_console.print.call_count >= 1
        # Panel is passed as first argument to console.print
        for call in mock_console.print.call_args_list:
            args = call[0] if call[0] else []
            for arg in args:
                if hasattr(arg, "renderable"):
                    renderable_str = str(arg.renderable)
                    if "MINOR Update Available" in renderable_str or "minor" in renderable_str.lower():
                        return
                elif isinstance(arg, str) and ("MINOR Update Available" in arg or "minor" in arg.lower()):
                    return
        pytest.fail("Minor version update message not found in console.print calls")

    @patch("specfact_cli.utils.startup_checks.check_ide_templates")
    @patch("specfact_cli.utils.startup_checks.check_pypi_version")
    @patch("specfact_cli.utils.startup_checks.console")
    def test_print_startup_checks_version_update_no_type(
        self, mock_console: MagicMock, mock_version: MagicMock, mock_templates: MagicMock
    ):
        """Test that update without type is not printed."""
        mock_templates.return_value = None
        mock_version.return_value = VersionCheckResult(
            current_version="1.0.0",
            latest_version="1.0.1",
            update_available=True,
            update_type=None,  # No type specified
            error=None,
        )

        print_startup_checks()

        # Should not print version update (type is None)
        mock_console.print.assert_not_called()

    @patch("specfact_cli.utils.startup_checks.get_last_checked_version", return_value=None)
    @patch("specfact_cli.utils.startup_checks.check_ide_templates")
    @patch("specfact_cli.utils.startup_checks.check_pypi_version")
    def test_print_startup_checks_version_check_disabled(
        self, mock_version: MagicMock, mock_templates: MagicMock, _mock_version_meta: MagicMock
    ):
        """Test that version check can be disabled."""
        print_startup_checks(check_version=False)

        # Version check should not be called
        mock_version.assert_not_called()
        # Template check should still be called
        mock_templates.assert_called_once()


class TestPrintStartupChecksOptimization:
    """Test optimized startup checks with metadata tracking."""

    @patch("specfact_cli.utils.startup_checks.check_ide_templates")
    @patch("specfact_cli.utils.startup_checks.check_pypi_version")
    @patch("specfact_cli.utils.startup_checks.update_metadata")
    def test_skip_template_check_when_version_unchanged(
        self,
        mock_update_metadata: MagicMock,
        mock_check_version: MagicMock,
        mock_check_templates: MagicMock,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that template check is skipped when version hasn't changed."""
        mock_home = tmp_path / "home"
        mock_home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: mock_home)

        # Set metadata with current version
        from specfact_cli import __version__

        update_metadata(last_checked_version=__version__)

        print_startup_checks(repo_path=tmp_path, check_version=False)

        # Template check should be skipped
        mock_check_templates.assert_not_called()

    @patch("specfact_cli.utils.startup_checks.check_ide_templates")
    @patch("specfact_cli.utils.startup_checks.check_pypi_version")
    @patch("specfact_cli.utils.startup_checks.update_metadata")
    def test_run_template_check_when_version_changed(
        self,
        mock_update_metadata: MagicMock,
        mock_check_version: MagicMock,
        mock_check_templates: MagicMock,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that template check runs when version has changed."""
        mock_home = tmp_path / "home"
        mock_home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: mock_home)

        # Set metadata with different version
        update_metadata(last_checked_version="0.9.0")
        mock_check_templates.return_value = None

        print_startup_checks(repo_path=tmp_path, check_version=False)

        # Template check should run
        mock_check_templates.assert_called_once()

    @patch("specfact_cli.utils.startup_checks.check_ide_templates")
    @patch("specfact_cli.utils.startup_checks.check_pypi_version")
    @patch("specfact_cli.utils.startup_checks.update_metadata")
    def test_skip_version_check_when_recent(
        self,
        mock_update_metadata: MagicMock,
        mock_check_version: MagicMock,
        mock_check_templates: MagicMock,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that version check is skipped when < 24 hours since last check."""
        mock_home = tmp_path / "home"
        mock_home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: mock_home)

        # Set recent timestamp
        from datetime import datetime

        recent_timestamp = datetime.now(UTC).isoformat()
        update_metadata(last_version_check_timestamp=recent_timestamp)

        print_startup_checks(repo_path=tmp_path, check_version=True)

        # Version check should be skipped
        mock_check_version.assert_not_called()

    @patch("specfact_cli.utils.startup_checks.check_ide_templates")
    @patch("specfact_cli.utils.startup_checks.check_pypi_version")
    @patch("specfact_cli.utils.startup_checks.update_metadata")
    def test_run_version_check_when_old(
        self,
        mock_update_metadata: MagicMock,
        mock_check_version: MagicMock,
        mock_check_templates: MagicMock,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that version check runs when >= 24 hours since last check."""
        mock_home = tmp_path / "home"
        mock_home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: mock_home)

        # Set old timestamp
        from datetime import datetime, timedelta

        old_timestamp = (datetime.now(UTC) - timedelta(hours=25)).isoformat()
        update_metadata(last_version_check_timestamp=old_timestamp)
        mock_check_version.return_value = VersionCheckResult(
            current_version="1.0.0",
            latest_version="1.0.0",
            update_available=False,
            update_type=None,
            error=None,
        )

        print_startup_checks(repo_path=tmp_path, check_version=True)

        # Version check should run
        mock_check_version.assert_called_once()

    @patch("specfact_cli.utils.startup_checks.check_ide_templates")
    @patch("specfact_cli.utils.startup_checks.check_pypi_version")
    @patch("specfact_cli.utils.startup_checks.update_metadata")
    def test_first_time_user_runs_all_checks(
        self,
        mock_update_metadata: MagicMock,
        mock_check_version: MagicMock,
        mock_check_templates: MagicMock,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that first-time users (no metadata) get all checks."""
        mock_home = tmp_path / "home"
        mock_home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: mock_home)

        # No metadata file exists
        mock_check_templates.return_value = None
        mock_check_version.return_value = VersionCheckResult(
            current_version="1.0.0",
            latest_version="1.0.0",
            update_available=False,
            update_type=None,
            error=None,
        )

        print_startup_checks(repo_path=tmp_path, check_version=True)

        # Both checks should run
        mock_check_templates.assert_called_once()
        mock_check_version.assert_called_once()

    @patch("specfact_cli.utils.startup_checks.check_ide_templates")
    @patch("specfact_cli.utils.startup_checks.check_pypi_version")
    def test_skip_checks_flag_skips_all(
        self,
        mock_check_version: MagicMock,
        mock_check_templates: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test that --skip-checks flag skips all checks."""
        print_startup_checks(repo_path=tmp_path, check_version=True, skip_checks=True)

        # No checks should run
        mock_check_templates.assert_not_called()
        mock_check_version.assert_not_called()

    @patch("specfact_cli.utils.startup_checks.check_ide_templates")
    @patch("specfact_cli.utils.startup_checks.check_pypi_version")
    @patch("specfact_cli.utils.startup_checks.update_metadata")
    def test_metadata_updated_after_checks(
        self,
        mock_update_metadata: MagicMock,
        mock_check_version: MagicMock,
        mock_check_templates: MagicMock,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that metadata is updated after checks complete."""
        mock_home = tmp_path / "home"
        mock_home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: mock_home)

        # No metadata exists (first run)
        mock_check_templates.return_value = None
        mock_check_version.return_value = VersionCheckResult(
            current_version="1.0.0",
            latest_version="1.0.0",
            update_available=False,
            update_type=None,
            error=None,
        )

        print_startup_checks(repo_path=tmp_path, check_version=True)

        # Metadata should be updated
        mock_update_metadata.assert_called()
        call_kwargs = mock_update_metadata.call_args[1]
        assert "last_checked_version" in call_kwargs
        assert "last_version_check_timestamp" in call_kwargs

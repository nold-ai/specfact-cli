"""
Unit tests for terminal capability detection and configuration.
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from specfact_cli.utils.terminal import (
    TerminalCapabilities,
    detect_terminal_capabilities,
    get_console_config,
    get_progress_config,
    print_progress,
)


class TestDetectTerminalCapabilities:
    """Test terminal capability detection."""

    def test_detect_no_color_env_var(self) -> None:
        """Test NO_COLOR environment variable disables colors."""
        with patch.dict(os.environ, {"NO_COLOR": "1"}):
            caps = detect_terminal_capabilities()
            assert caps.supports_color is False

    def test_detect_force_color_env_var(self) -> None:
        """Test FORCE_COLOR environment variable enables colors."""
        with (
            patch.dict(os.environ, {"FORCE_COLOR": "1"}, clear=True),
            patch("sys.stdout.isatty", return_value=False),
        ):
            caps = detect_terminal_capabilities()
            assert caps.supports_color is True

    def test_detect_ci_environment(self) -> None:
        """Test CI environment detection."""
        with patch.dict(os.environ, {"CI": "true"}, clear=True):
            caps = detect_terminal_capabilities()
            assert caps.is_ci is True
            assert caps.supports_animations is False

    def test_detect_github_actions(self) -> None:
        """Test GitHub Actions environment detection."""
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}, clear=True):
            caps = detect_terminal_capabilities()
            assert caps.is_ci is True

    def test_detect_test_mode(self) -> None:
        """Test TEST_MODE environment variable."""
        with (
            patch.dict(os.environ, {"TEST_MODE": "true"}, clear=True),
            patch("sys.stdout.isatty", return_value=True),
        ):
            caps = detect_terminal_capabilities()
            assert caps.supports_animations is False

    def test_detect_interactive_tty(self) -> None:
        """Test interactive TTY detection."""
        with patch.dict(os.environ, {}, clear=True), patch("sys.stdout.isatty", return_value=True):
            caps = detect_terminal_capabilities()
            assert caps.is_interactive is True

    def test_detect_non_interactive(self) -> None:
        """Test non-interactive terminal detection."""
        with patch.dict(os.environ, {}, clear=True), patch("sys.stdout.isatty", return_value=False):
            caps = detect_terminal_capabilities()
            assert caps.is_interactive is False


class TestGetConsoleConfig:
    """Test console configuration generation."""

    def test_console_config_no_color(self) -> None:
        """Test console config when colors not supported."""
        with patch("specfact_cli.utils.terminal.detect_terminal_capabilities") as mock_detect:
            mock_detect.return_value = TerminalCapabilities(
                supports_color=False,
                supports_animations=False,
                is_interactive=False,
                is_ci=True,
            )
            config = get_console_config()
            assert config["no_color"] is True

    def test_console_config_force_terminal(self) -> None:
        """Test console config for non-interactive terminals."""
        with patch("specfact_cli.utils.terminal.detect_terminal_capabilities") as mock_detect:
            mock_detect.return_value = TerminalCapabilities(
                supports_color=True,
                supports_animations=False,
                is_interactive=False,
                is_ci=False,
            )
            config = get_console_config()
            assert config["force_terminal"] is False

    def test_console_config_width(self) -> None:
        """Test console config width for non-interactive terminals."""
        with (
            patch("specfact_cli.utils.terminal.detect_terminal_capabilities") as mock_detect,
        ):
            mock_detect.return_value = TerminalCapabilities(
                supports_color=True,
                supports_animations=False,
                is_interactive=False,
                is_ci=False,
            )
            config = get_console_config()
            assert config["width"] == 80


class TestGetProgressConfig:
    """Test progress configuration generation."""

    def test_progress_config_with_animations(self) -> None:
        """Test progress config when animations supported."""
        with patch("specfact_cli.utils.terminal.detect_terminal_capabilities") as mock_detect:
            mock_detect.return_value = TerminalCapabilities(
                supports_color=True,
                supports_animations=True,
                is_interactive=True,
                is_ci=False,
            )
            columns, _kwargs = get_progress_config()
            assert len(columns) == 5  # SpinnerColumn, TextColumn, BarColumn, TextColumn, TimeElapsedColumn
            assert isinstance(columns, tuple)

    def test_progress_config_without_animations(self) -> None:
        """Test progress config when animations not supported."""
        with patch("specfact_cli.utils.terminal.detect_terminal_capabilities") as mock_detect:
            mock_detect.return_value = TerminalCapabilities(
                supports_color=True,
                supports_animations=False,
                is_interactive=False,
                is_ci=True,
            )
            columns, kwargs = get_progress_config()
            assert len(columns) == 1  # TextColumn only
            assert isinstance(columns, tuple)
            assert kwargs.get("disable") is False


class TestPrintProgress:
    """Test plain text progress reporting."""

    def test_print_progress_with_total(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test print_progress with total count."""
        print_progress("Analyzing", 45, 100)
        captured = capsys.readouterr()
        assert "Analyzing... 45% (45/100)" in captured.out

    def test_print_progress_indeterminate(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test print_progress without total (indeterminate)."""
        print_progress("Processing", 0, 0)
        captured = capsys.readouterr()
        assert "Processing..." in captured.out
        assert "%" not in captured.out

    def test_print_progress_zero_total(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test print_progress with zero total."""
        print_progress("Loading", 5, 0)
        captured = capsys.readouterr()
        assert "Loading..." in captured.out

"""
E2E tests for terminal output in different terminal modes.
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

from specfact_cli.runtime import TerminalMode, get_configured_console, get_terminal_mode
from specfact_cli.utils.terminal import detect_terminal_capabilities


class TestTerminalOutputE2E:
    """E2E tests for terminal output modes."""

    def test_graphical_terminal_mode(self, tmp_path: Path) -> None:
        """Test that full terminal returns GRAPHICAL mode."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove TEST_MODE and PYTEST_CURRENT_TEST if present
            os.environ.pop("TEST_MODE", None)
            os.environ.pop("PYTEST_CURRENT_TEST", None)
            os.environ.pop("CI", None)
            with patch("sys.stdout.isatty", return_value=True):
                caps = detect_terminal_capabilities()
                if caps.supports_animations and caps.is_interactive:
                    mode = get_terminal_mode()
                    assert mode == TerminalMode.GRAPHICAL
                    console = get_configured_console()
                    assert console is not None

    def test_basic_terminal_mode_ci(self, tmp_path: Path) -> None:
        """Test that CI environment returns BASIC mode."""
        with patch.dict(os.environ, {"CI": "true"}, clear=True):
            os.environ.pop("TEST_MODE", None)
            os.environ.pop("PYTEST_CURRENT_TEST", None)
            mode = get_terminal_mode()
            assert mode == TerminalMode.BASIC
            console = get_configured_console()
            assert console is not None

    def test_basic_terminal_mode_no_color(self, tmp_path: Path) -> None:
        """Test that NO_COLOR environment returns BASIC mode."""
        with patch.dict(os.environ, {"NO_COLOR": "1"}, clear=True):
            os.environ.pop("TEST_MODE", None)
            os.environ.pop("PYTEST_CURRENT_TEST", None)
            mode = get_terminal_mode()
            assert mode == TerminalMode.BASIC

    def test_minimal_terminal_mode_test(self, tmp_path: Path) -> None:
        """Test that TEST_MODE returns MINIMAL mode."""
        with patch.dict(os.environ, {"TEST_MODE": "true"}, clear=True):
            mode = get_terminal_mode()
            assert mode == TerminalMode.MINIMAL

    def test_console_consistency(self, tmp_path: Path) -> None:
        """Test that get_configured_console returns consistent instances."""
        console1 = get_configured_console()
        console2 = get_configured_console()
        # Should return the same instance (cached)
        assert console1 is console2

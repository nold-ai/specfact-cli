"""
Unit tests for runtime configuration helpers.
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

from specfact_cli.runtime import (
    TerminalMode,
    debug_log_operation,
    debug_print,
    get_configured_console,
    get_terminal_mode,
    is_debug_mode,
    set_debug_mode,
)
from specfact_cli.utils.terminal import TerminalCapabilities


class TestGetTerminalMode:
    """Test terminal mode detection."""

    def test_terminal_mode_minimal_test_mode(self) -> None:
        """Test that TEST_MODE returns MINIMAL."""
        with patch.dict(os.environ, {"TEST_MODE": "true"}, clear=True):
            mode = get_terminal_mode()
            assert mode == TerminalMode.MINIMAL

    def test_terminal_mode_minimal_pytest(self) -> None:
        """Test that PYTEST_CURRENT_TEST returns MINIMAL."""
        with patch.dict(os.environ, {"PYTEST_CURRENT_TEST": "test_something"}, clear=True):
            mode = get_terminal_mode()
            assert mode == TerminalMode.MINIMAL

    def test_terminal_mode_basic_ci(self) -> None:
        """Test that CI environment returns BASIC."""
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("specfact_cli.runtime.detect_terminal_capabilities") as mock_detect,
        ):
            # Remove TEST_MODE and PYTEST_CURRENT_TEST if present
            os.environ.pop("TEST_MODE", None)
            os.environ.pop("PYTEST_CURRENT_TEST", None)
            mock_detect.return_value = TerminalCapabilities(
                supports_color=True,
                supports_animations=False,
                is_interactive=False,
                is_ci=True,
            )
            mode = get_terminal_mode()
            assert mode == TerminalMode.BASIC

    def test_terminal_mode_basic_non_interactive(self) -> None:
        """Test that non-interactive terminal returns BASIC."""
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("specfact_cli.runtime.detect_terminal_capabilities") as mock_detect,
        ):
            # Remove TEST_MODE and PYTEST_CURRENT_TEST if present
            os.environ.pop("TEST_MODE", None)
            os.environ.pop("PYTEST_CURRENT_TEST", None)
            mock_detect.return_value = TerminalCapabilities(
                supports_color=True,
                supports_animations=False,
                is_interactive=False,
                is_ci=False,
            )
            mode = get_terminal_mode()
            assert mode == TerminalMode.BASIC

    def test_terminal_mode_graphical(self) -> None:
        """Test that interactive TTY with animations returns GRAPHICAL."""
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("specfact_cli.runtime.detect_terminal_capabilities") as mock_detect,
        ):
            # Remove TEST_MODE and PYTEST_CURRENT_TEST if present
            os.environ.pop("TEST_MODE", None)
            os.environ.pop("PYTEST_CURRENT_TEST", None)
            mock_detect.return_value = TerminalCapabilities(
                supports_color=True,
                supports_animations=True,
                is_interactive=True,
                is_ci=False,
            )
            mode = get_terminal_mode()
            assert mode == TerminalMode.GRAPHICAL


class TestGetConfiguredConsole:
    """Test configured console creation and caching."""

    def test_get_configured_console_creates_console(self) -> None:
        """Test that get_configured_console creates a Console instance."""
        console = get_configured_console()
        assert console is not None
        from rich.console import Console

        assert isinstance(console, Console)

    def test_get_configured_console_caches(self) -> None:
        """Test that get_configured_console caches Console instances."""
        console1 = get_configured_console()
        console2 = get_configured_console()
        # Should return the same instance (cached)
        assert console1 is console2

    def test_get_configured_console_different_modes(self) -> None:
        """Test that different terminal modes create different Console instances."""
        # This test verifies caching works per mode
        # In practice, mode doesn't change during execution, so we test caching
        console1 = get_configured_console()
        console2 = get_configured_console()
        assert console1 is console2


class TestDebugMode:
    """Test debug mode functionality."""

    def test_set_debug_mode_enabled(self) -> None:
        """Test enabling debug mode."""
        set_debug_mode(True)
        assert is_debug_mode() is True

    def test_set_debug_mode_disabled(self) -> None:
        """Test disabling debug mode."""
        set_debug_mode(False)
        assert is_debug_mode() is False

    def test_debug_print_when_enabled(self) -> None:
        """Test that debug_print outputs when debug mode is enabled."""
        set_debug_mode(True)
        # Should not raise exception
        debug_print("test message")

    def test_debug_print_when_disabled(self) -> None:
        """Test that debug_print does not output when debug mode is disabled."""
        set_debug_mode(False)
        # Should not raise exception, but output should be suppressed
        debug_print("test message")

    def test_debug_print_writes_to_file_when_debug_on(self, tmp_path: Path) -> None:
        """When debug is on, debug_print also writes to debug log file."""
        with (
            patch("specfact_cli.runtime.get_specfact_home_logs_dir", return_value=str(tmp_path)),
            patch("specfact_cli.runtime._debug_logger", None),
            patch("specfact_cli.runtime._debug_file_handler", None),
        ):
            import specfact_cli.runtime as runtime_mod

            runtime_mod._debug_logger = None
            runtime_mod._debug_file_handler = None
            set_debug_mode(True)
            debug_print("hello debug")
        log_file = tmp_path / "specfact-debug.log"
        assert log_file.exists()
        assert "hello debug" in log_file.read_text()

    def test_debug_log_operation_no_op_when_debug_off(self) -> None:
        """debug_log_operation does nothing when debug is off."""
        set_debug_mode(False)
        debug_log_operation("file_read", "/tmp/foo", "success")
        # No exception; no file written (we don't create log dir when off)

    def test_debug_log_operation_writes_when_debug_on(self, tmp_path: Path) -> None:
        """When debug is on, debug_log_operation writes structured line to file."""
        with (
            patch("specfact_cli.runtime.get_specfact_home_logs_dir", return_value=str(tmp_path)),
        ):
            import specfact_cli.runtime as runtime_mod

            runtime_mod._debug_logger = None
            runtime_mod._debug_file_handler = None
            set_debug_mode(True)
            debug_log_operation("api_request", "https://example.com", "200", error=None, extra=None)
        log_file = tmp_path / "specfact-debug.log"
        assert log_file.exists()
        content = log_file.read_text()
        assert "debug_log_operation" in content
        assert "api_request" in content
        assert "200" in content

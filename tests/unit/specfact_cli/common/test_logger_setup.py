"""
Unit tests for specfact_cli.common.logger_setup.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from specfact_cli.common.logger_setup import (
    format_debug_log_message,
    get_specfact_home_logs_dir,
    plain_text_for_debug_log,
)


class TestGetSpecfactHomeLogsDir:
    """Tests for get_specfact_home_logs_dir()."""

    def test_returns_non_empty_string(self) -> None:
        """Result is a non-empty string path."""
        result = get_specfact_home_logs_dir()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_path_contains_specfact_logs(self) -> None:
        """Returned path ends with .specfact/logs or contains .specfact and logs."""
        result = get_specfact_home_logs_dir()
        assert ".specfact" in result
        assert "logs" in result

    def test_creates_directory_on_first_use(self, tmp_path: Path) -> None:
        """Directory is created when function is called (temp HOME)."""
        home = tmp_path / "fake_home"
        home.mkdir()
        logs_expected = home / ".specfact" / "logs"
        assert not logs_expected.exists()
        with pytest.MonkeyPatch.context() as m:
            m.setattr(
                os.path,
                "expanduser",
                lambda x: str(home) if x == "~" else os.path.expanduser(x),
            )
            result = get_specfact_home_logs_dir()
        assert os.path.isdir(result)
        assert result == str(logs_expected.resolve())

    def test_idempotent_second_call(self, tmp_path: Path) -> None:
        """Second call returns same path and does not fail."""
        home = tmp_path / "fake_home"
        home.mkdir()
        with pytest.MonkeyPatch.context() as m:
            m.setattr(
                os.path,
                "expanduser",
                lambda x: str(home) if x == "~" else os.path.expanduser(x),
            )
            first = get_specfact_home_logs_dir()
            second = get_specfact_home_logs_dir()
        assert first == second
        assert os.path.isdir(first)


class TestPlainTextForDebugLog:
    """Tests for plain_text_for_debug_log()."""

    def test_strips_rich_markup(self) -> None:
        """Rich markup like [dim], [/dim], [bold] is removed."""
        assert plain_text_for_debug_log("hello [dim]world[/dim]") == "hello world"
        assert plain_text_for_debug_log("[bold]x[/bold]") == "x"

    def test_normalizes_whitespace(self) -> None:
        """Multiple spaces and newlines are collapsed to single space."""
        assert plain_text_for_debug_log("a  b   c") == "a b c"

    def test_returns_plain_string_unchanged(self) -> None:
        """Plain text is returned with only whitespace normalized."""
        assert plain_text_for_debug_log("plain message") == "plain message"


class TestFormatDebugLogMessage:
    """Tests for format_debug_log_message()."""

    def test_joins_args_and_strips_markup(self) -> None:
        """*args are joined and Rich markup is stripped."""
        assert format_debug_log_message("hello", "[dim]world[/dim]") == "hello world"

    def test_single_arg(self) -> None:
        """Single argument is stringified and stripped."""
        assert format_debug_log_message("[bold]x[/bold]") == "x"

    def test_empty_args_returns_empty_string(self) -> None:
        """No args returns empty string."""
        assert format_debug_log_message() == ""

    def test_kwargs_ignored(self) -> None:
        """**kwargs do not affect output (signature compatibility with print)."""
        assert format_debug_log_message("msg", style="bold") == "msg"

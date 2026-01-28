"""
Unit tests for specfact_cli.common.logger_setup.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from specfact_cli.common.logger_setup import get_specfact_home_logs_dir


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

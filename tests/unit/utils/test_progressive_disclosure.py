"""
Unit tests for progressive disclosure utilities.
"""

from __future__ import annotations

import os
import sys

from specfact_cli.utils.progressive_disclosure import (
    get_help_advanced_message,
    get_hidden_value,
    intercept_help_advanced,
    is_advanced_help_requested,
    set_advanced_help,
    should_show_advanced,
)


class TestProgressiveDisclosure:
    """Test progressive disclosure utilities."""

    def test_is_advanced_help_requested_from_argv(self) -> None:
        """Test detecting --help-advanced from sys.argv."""
        original_argv = sys.argv.copy()
        try:
            sys.argv = ["specfact", "--help-advanced"]
            assert is_advanced_help_requested() is True

            sys.argv = ["specfact", "-ha"]
            assert is_advanced_help_requested() is True

            sys.argv = ["specfact", "--help"]
            assert is_advanced_help_requested() is False
        finally:
            sys.argv = original_argv

    def test_is_advanced_help_requested_from_env(self) -> None:
        """Test detecting advanced help from environment variable."""
        original_env = os.environ.get("SPECFACT_SHOW_ADVANCED")
        try:
            os.environ["SPECFACT_SHOW_ADVANCED"] = "true"
            assert is_advanced_help_requested() is True

            os.environ["SPECFACT_SHOW_ADVANCED"] = "false"
            assert is_advanced_help_requested() is False

            if "SPECFACT_SHOW_ADVANCED" in os.environ:
                del os.environ["SPECFACT_SHOW_ADVANCED"]
            assert is_advanced_help_requested() is False
        finally:
            if original_env:
                os.environ["SPECFACT_SHOW_ADVANCED"] = original_env
            elif "SPECFACT_SHOW_ADVANCED" in os.environ:
                del os.environ["SPECFACT_SHOW_ADVANCED"]

    def test_should_show_advanced(self) -> None:
        """Test should_show_advanced function."""
        set_advanced_help(False)
        assert should_show_advanced() is False

        set_advanced_help(True)
        assert should_show_advanced() is True

        set_advanced_help(False)

    def test_get_hidden_value(self) -> None:
        """Test get_hidden_value function."""
        original_env = os.environ.get("SPECFACT_SHOW_ADVANCED")
        try:
            os.environ["SPECFACT_SHOW_ADVANCED"] = "true"
            assert get_hidden_value() is False  # Should not hide when advanced is enabled

            os.environ["SPECFACT_SHOW_ADVANCED"] = "false"
            assert get_hidden_value() is True  # Should hide when advanced is disabled

            if "SPECFACT_SHOW_ADVANCED" in os.environ:
                del os.environ["SPECFACT_SHOW_ADVANCED"]
            assert get_hidden_value() is True  # Should hide by default
        finally:
            if original_env:
                os.environ["SPECFACT_SHOW_ADVANCED"] = original_env
            elif "SPECFACT_SHOW_ADVANCED" in os.environ:
                del os.environ["SPECFACT_SHOW_ADVANCED"]

    def test_get_help_advanced_message(self) -> None:
        """Test get_help_advanced_message function."""
        message = get_help_advanced_message()
        assert "--help-advanced" in message
        assert "Tip" in message

    def test_intercept_help_advanced(self) -> None:
        """Test intercept_help_advanced function."""
        original_argv = sys.argv.copy()
        original_env = os.environ.get("SPECFACT_SHOW_ADVANCED")
        try:
            sys.argv = ["specfact", "--help-advanced"]
            intercept_help_advanced()
            assert "--help-advanced" not in sys.argv
            assert os.environ.get("SPECFACT_SHOW_ADVANCED") == "true"
        finally:
            sys.argv = original_argv
            if original_env:
                os.environ["SPECFACT_SHOW_ADVANCED"] = original_env
            elif "SPECFACT_SHOW_ADVANCED" in os.environ:
                del os.environ["SPECFACT_SHOW_ADVANCED"]

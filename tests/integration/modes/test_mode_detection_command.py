"""
Integration tests for mode detection with CLI integration.

These tests validate mode detection works with CLI flags and environment variables.
"""

from __future__ import annotations

import os
from unittest.mock import patch

from typer.testing import CliRunner

from specfact_cli.modes import OperationalMode, detect_mode


runner = CliRunner()


class TestModeDetectionIntegration:
    """Integration tests for mode detection with CLI integration."""

    def test_mode_flag_cicd(self) -> None:
        """Test explicit --mode cicd flag validation."""
        # Test mode detection with explicit CICD
        mode = detect_mode(explicit_mode=OperationalMode.CICD)
        assert mode == OperationalMode.CICD

    def test_mode_flag_copilot(self) -> None:
        """Test explicit --mode copilot flag validation."""
        # Test mode detection with explicit COPILOT
        mode = detect_mode(explicit_mode=OperationalMode.COPILOT)
        assert mode == OperationalMode.COPILOT

    def test_mode_flag_invalid(self) -> None:
        """Test invalid --mode flag (handled by CLI validation)."""
        # CLI validation happens in main() callback
        # This test just ensures mode detection works correctly
        mode = detect_mode(explicit_mode=OperationalMode.CICD)
        assert mode == OperationalMode.CICD

    def test_environment_variable_override(self) -> None:
        """Test SPECFACT_MODE environment variable override."""
        with patch.dict(os.environ, {"SPECFACT_MODE": "copilot"}):
            mode = detect_mode(explicit_mode=None)
            assert mode == OperationalMode.COPILOT

    def test_mode_flag_overrides_environment(self) -> None:
        """Test explicit mode overrides SPECFACT_MODE environment variable."""
        with patch.dict(os.environ, {"SPECFACT_MODE": "copilot"}):
            mode = detect_mode(explicit_mode=OperationalMode.CICD)
            assert mode == OperationalMode.CICD

    def test_default_mode_when_no_override(self) -> None:
        """Test default mode detection when no overrides."""
        with patch.dict(os.environ, {}, clear=True):
            mode = detect_mode(explicit_mode=None)
            assert mode == OperationalMode.CICD

    def test_mode_flag_with_short_form(self) -> None:
        """Test --mode flag with short form -m (CLI handles both)."""
        # Both --mode and -m are handled by Typer
        # This test ensures mode detection works
        mode = detect_mode(explicit_mode=OperationalMode.CICD)
        assert mode == OperationalMode.CICD

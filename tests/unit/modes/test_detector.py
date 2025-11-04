"""
Unit tests for mode detector - Contract-First approach.

Most validation is covered by @beartype and @icontract decorators.
Only edge cases and business logic are tested here.
"""

from __future__ import annotations

import os
from unittest.mock import patch

from specfact_cli.modes.detector import (
    OperationalMode,
    copilot_api_available,
    detect_mode,
    ide_detected,
    ide_has_copilot,
)


class TestOperationalMode:
    """Test cases for OperationalMode enum."""

    def test_cicd_mode(self) -> None:
        """Test CICD mode enum value."""
        assert OperationalMode.CICD == "cicd"
        assert OperationalMode.CICD.value == "cicd"

    def test_copilot_mode(self) -> None:
        """Test COPILOT mode enum value."""
        assert OperationalMode.COPILOT == "copilot"
        assert OperationalMode.COPILOT.value == "copilot"


class TestDetectMode:
    """Test cases for detect_mode function - focused on priority order."""

    def test_explicit_mode_overrides_detection(self) -> None:
        """Explicit mode flag overrides auto-detection."""
        mode = detect_mode(explicit_mode=OperationalMode.CICD)
        assert mode == OperationalMode.CICD

        mode = detect_mode(explicit_mode=OperationalMode.COPILOT)
        assert mode == OperationalMode.COPILOT

    def test_defaults_to_cicd_when_no_copilot(self) -> None:
        """Defaults to CI/CD mode when CoPilot unavailable."""
        with patch.dict(os.environ, {}, clear=True):
            mode = detect_mode(explicit_mode=None)
            assert mode == OperationalMode.CICD

    def test_environment_variable_override(self) -> None:
        """Environment variable SPECFACT_MODE overrides auto-detection."""
        with patch.dict(os.environ, {"SPECFACT_MODE": "copilot"}):
            mode = detect_mode(explicit_mode=None)
            assert mode == OperationalMode.COPILOT

        with patch.dict(os.environ, {"SPECFACT_MODE": "cicd"}):
            mode = detect_mode(explicit_mode=None)
            assert mode == OperationalMode.CICD

    def test_explicit_mode_overrides_environment_variable(self) -> None:
        """Explicit mode has highest priority over environment variable."""
        with patch.dict(os.environ, {"SPECFACT_MODE": "copilot"}):
            mode = detect_mode(explicit_mode=OperationalMode.CICD)
            assert mode == OperationalMode.CICD

    def test_copilot_api_detection(self) -> None:
        """Detects CoPilot mode when API is available."""
        with patch.dict(os.environ, {"COPILOT_API_URL": "https://api.copilot.com"}):
            mode = detect_mode(explicit_mode=None)
            assert mode == OperationalMode.COPILOT

    def test_ide_detection(self) -> None:
        """Detects CoPilot mode when IDE has CoPilot enabled."""
        with patch.dict(
            os.environ,
            {
                "VSCODE_PID": "12345",
                "COPILOT_ENABLED": "true",
            },
        ):
            mode = detect_mode(explicit_mode=None)
            assert mode == OperationalMode.COPILOT


class TestCopilotApiAvailable:
    """Test cases for copilot_api_available function."""

    def test_copilot_api_url_detected(self) -> None:
        """Detects CoPilot API when COPILOT_API_URL is set."""
        with patch.dict(os.environ, {"COPILOT_API_URL": "https://api.copilot.com"}):
            assert copilot_api_available() is True

    def test_copilot_api_token_detected(self) -> None:
        """Detects CoPilot API when COPILOT_API_TOKEN is set."""
        with patch.dict(os.environ, {"COPILOT_API_TOKEN": "token123"}):
            assert copilot_api_available() is True

    def test_github_copilot_token_detected(self) -> None:
        """Detects CoPilot API when GITHUB_COPILOT_TOKEN is set."""
        with patch.dict(os.environ, {"GITHUB_COPILOT_TOKEN": "token123"}):
            assert copilot_api_available() is True

    def test_no_copilot_api_when_unavailable(self) -> None:
        """Returns False when CoPilot API is not available."""
        with patch.dict(os.environ, {}, clear=True):
            assert copilot_api_available() is False


class TestIdeDetected:
    """Test cases for ide_detected function."""

    def test_vscode_pid_detected(self) -> None:
        """Detects VS Code when VSCODE_PID is set."""
        with patch.dict(os.environ, {"VSCODE_PID": "12345"}):
            assert ide_detected() is True

    def test_vscode_injection_detected(self) -> None:
        """Detects VS Code when VSCODE_INJECTION is set."""
        with patch.dict(os.environ, {"VSCODE_INJECTION": "1"}):
            assert ide_detected() is True

    def test_cursor_pid_detected(self) -> None:
        """Detects Cursor when CURSOR_PID is set."""
        with patch.dict(os.environ, {"CURSOR_PID": "12345"}):
            assert ide_detected() is True

    def test_cursor_mode_detected(self) -> None:
        """Detects Cursor when CURSOR_MODE is set."""
        with patch.dict(os.environ, {"CURSOR_MODE": "true"}):
            assert ide_detected() is True

    def test_term_program_vscode_detected(self) -> None:
        """Detects VS Code when TERM_PROGRAM is 'vscode'."""
        with patch.dict(os.environ, {"TERM_PROGRAM": "vscode"}):
            assert ide_detected() is True

    def test_no_ide_when_not_detected(self) -> None:
        """Returns False when no IDE is detected."""
        with patch.dict(os.environ, {}, clear=True):
            assert ide_detected() is False


class TestIdeHasCopilot:
    """Test cases for ide_has_copilot function."""

    def test_copilot_enabled_detected(self) -> None:
        """Detects CoPilot when COPILOT_ENABLED is 'true'."""
        with patch.dict(os.environ, {"COPILOT_ENABLED": "true"}):
            assert ide_has_copilot() is True

    def test_vscode_copilot_enabled_detected(self) -> None:
        """Detects CoPilot when VSCODE_COPILOT_ENABLED is 'true'."""
        with patch.dict(os.environ, {"VSCODE_COPILOT_ENABLED": "true"}):
            assert ide_has_copilot() is True

    def test_cursor_copilot_enabled_detected(self) -> None:
        """Detects CoPilot when CURSOR_COPILOT_ENABLED is 'true'."""
        with patch.dict(os.environ, {"CURSOR_COPILOT_ENABLED": "true"}):
            assert ide_has_copilot() is True

    def test_no_copilot_when_not_enabled(self) -> None:
        """Returns False when CoPilot is not enabled."""
        with patch.dict(os.environ, {}, clear=True):
            assert ide_has_copilot() is False

    def test_copilot_enabled_false_not_detected(self) -> None:
        """Returns False when COPILOT_ENABLED is 'false'."""
        with patch.dict(os.environ, {"COPILOT_ENABLED": "false"}):
            assert ide_has_copilot() is False

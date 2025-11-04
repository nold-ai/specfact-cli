"""
Mode detection for SpecFact CLI.

This module provides automatic detection of operational mode (CI/CD vs CoPilot)
based on environment and explicit flags.
"""

from __future__ import annotations

import os
from enum import Enum

from beartype import beartype
from icontract import ensure, require


class OperationalMode(str, Enum):
    """Operational modes for SpecFact CLI."""

    CICD = "cicd"
    COPILOT = "copilot"


@beartype
@require(lambda explicit_mode: explicit_mode is None or isinstance(explicit_mode, OperationalMode))
@ensure(lambda result: isinstance(result, OperationalMode))
def detect_mode(explicit_mode: OperationalMode | None = None) -> OperationalMode:
    """
    Auto-detect operational mode or use explicit override.

    Priority:
    1. Explicit mode flag (highest)
    2. CoPilot API availability
    3. IDE integration (VS Code/Cursor with CoPilot)
    4. Default to CI/CD mode

    Args:
        explicit_mode: Explicitly specified mode (overrides auto-detection)

    Returns:
        Detected or explicit operational mode

    Raises:
        ValueError: If explicit_mode is invalid OperationalMode value
    """
    # 1. Check explicit flag (highest priority)
    if explicit_mode is not None:
        return explicit_mode

    # 2. Check environment variable (SPECFACT_MODE)
    env_mode = os.environ.get("SPECFACT_MODE", "").lower()
    if env_mode == "copilot":
        return OperationalMode.COPILOT
    if env_mode == "cicd":
        return OperationalMode.CICD

    # 3. Check CoPilot API availability
    if copilot_api_available():
        return OperationalMode.COPILOT

    # 4. Check IDE integration
    if ide_detected() and ide_has_copilot():
        return OperationalMode.COPILOT

    # 5. Default to CI/CD
    return OperationalMode.CICD


@beartype
@ensure(lambda result: isinstance(result, bool))
def copilot_api_available() -> bool:
    """
    Check if CoPilot API is available.

    Returns:
        True if CoPilot API is available, False otherwise
    """
    # Check environment variables
    if os.environ.get("COPILOT_API_URL"):
        return True

    # Check for CoPilot token or credentials
    return bool(os.environ.get("COPILOT_API_TOKEN") or os.environ.get("GITHUB_COPILOT_TOKEN"))


@beartype
@ensure(lambda result: isinstance(result, bool))
def ide_detected() -> bool:
    """
    Check if running in IDE (VS Code/Cursor).

    Returns:
        True if running in IDE, False otherwise
    """
    # Check VS Code
    if os.environ.get("VSCODE_PID") or os.environ.get("VSCODE_INJECTION"):
        return True

    # Check Cursor
    if os.environ.get("CURSOR_PID") or os.environ.get("CURSOR_MODE"):
        return True

    # Check for common IDE environment variables
    return os.environ.get("TERM_PROGRAM") == "vscode"


@beartype
@ensure(lambda result: isinstance(result, bool))
def ide_has_copilot() -> bool:
    """
    Check if IDE has CoPilot extension enabled.

    Returns:
        True if IDE has CoPilot enabled, False otherwise
    """
    # Check for CoPilot extension environment variables
    if os.environ.get("COPILOT_ENABLED") == "true":
        return True

    # Check for VS Code/Cursor Copilot settings
    if os.environ.get("VSCODE_COPILOT_ENABLED") == "true":
        return True

    # Placeholder: Future implementation may check IDE configuration files
    # For now, we only check environment variables
    return os.environ.get("CURSOR_COPILOT_ENABLED") == "true"

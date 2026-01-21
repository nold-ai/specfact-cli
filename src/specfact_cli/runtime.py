"""
Runtime configuration helpers shared across commands.

Centralizes CLI-wide settings such as operational mode, interaction style,
and preferred structured data formats for inputs/outputs.
"""

from __future__ import annotations

import os
import sys
from enum import Enum

from beartype import beartype
from icontract import ensure
from rich.console import Console

from specfact_cli.modes import OperationalMode
from specfact_cli.utils.structured_io import StructuredFormat
from specfact_cli.utils.terminal import detect_terminal_capabilities, get_console_config


class TerminalMode(str, Enum):
    """Terminal output modes for Rich Console and Progress."""

    GRAPHICAL = "graphical"  # Full Rich features (colors, animations)
    BASIC = "basic"  # Plain text, no animations
    MINIMAL = "minimal"  # Minimal output (test mode, CI/CD)


_operational_mode: OperationalMode = OperationalMode.CICD
_input_format: StructuredFormat = StructuredFormat.YAML
_output_format: StructuredFormat = StructuredFormat.YAML
_non_interactive_override: bool | None = None
_debug_mode: bool = False
_console_cache: dict[TerminalMode, Console] = {}


@beartype
def set_operational_mode(mode: OperationalMode) -> None:
    """Persist active operational mode for downstream consumers."""
    global _operational_mode
    _operational_mode = mode


@beartype
def get_operational_mode() -> OperationalMode:
    """Return the current operational mode."""
    return _operational_mode


@beartype
def configure_io_formats(
    *, input_format: StructuredFormat | None = None, output_format: StructuredFormat | None = None
) -> None:
    """Update global default structured data formats."""
    global _input_format, _output_format
    if input_format is not None:
        _input_format = input_format
    if output_format is not None:
        _output_format = output_format


@beartype
def get_input_format() -> StructuredFormat:
    """Return default structured input format (defaults to YAML)."""
    return _input_format


@beartype
def get_output_format() -> StructuredFormat:
    """Return default structured output format (defaults to YAML)."""
    return _output_format


@beartype
def set_non_interactive_override(value: bool | None) -> None:
    """Force interactive/non-interactive behavior (None resets to auto)."""
    global _non_interactive_override
    _non_interactive_override = value


@beartype
def is_non_interactive() -> bool:
    """
    Determine whether prompts should be suppressed.

    Priority:
        1. Explicit override
        2. CI/CD mode
        3. TTY detection
    """
    if _non_interactive_override is not None:
        return _non_interactive_override

    if _operational_mode == OperationalMode.CICD:
        return True

    try:
        stdin_tty = bool(sys.stdin and sys.stdin.isatty())
        stdout_tty = bool(sys.stdout and sys.stdout.isatty())
        return not (stdin_tty and stdout_tty)
    except Exception:  # pragma: no cover - defensive fallback
        return True


@beartype
def is_interactive() -> bool:
    """Inverse helper for readability."""
    return not is_non_interactive()


@beartype
def set_debug_mode(enabled: bool) -> None:
    """Enable or disable debug output mode."""
    global _debug_mode
    _debug_mode = enabled


@beartype
def is_debug_mode() -> bool:
    """Check if debug mode is enabled."""
    return _debug_mode


@beartype
@ensure(lambda result: isinstance(result, TerminalMode), "Must return TerminalMode")
def get_terminal_mode() -> TerminalMode:
    """
    Get terminal mode based on detected capabilities and operational mode.

    Terminal modes:
    - GRAPHICAL: Full Rich features (colors, animations) - interactive TTY
    - BASIC: Plain text, no animations - non-interactive or CI/CD
    - MINIMAL: Minimal output - test mode

    Returns:
        TerminalMode enum value
    """
    caps = detect_terminal_capabilities()

    # Test mode always returns MINIMAL
    if os.environ.get("TEST_MODE") == "true" or os.environ.get("PYTEST_CURRENT_TEST") is not None:
        return TerminalMode.MINIMAL

    # CI/CD or non-interactive returns BASIC
    if caps.is_ci or not caps.is_interactive:
        return TerminalMode.BASIC

    # Interactive TTY with animations returns GRAPHICAL
    if caps.supports_animations and caps.is_interactive:
        return TerminalMode.GRAPHICAL

    # Fallback to BASIC
    return TerminalMode.BASIC


@beartype
@ensure(lambda result: isinstance(result, Console), "Must return Console")
def get_configured_console() -> Console:
    """
    Get or create configured Console instance based on terminal capabilities.

    Caches Console instance per terminal mode to avoid repeated detection.

    Returns:
        Configured Rich Console instance
    """
    mode = get_terminal_mode()

    if mode not in _console_cache:
        config = get_console_config()
        _console_cache[mode] = Console(**config)

    return _console_cache[mode]


@beartype
def debug_print(*args, **kwargs) -> None:
    """
    Print debug messages only if debug mode is enabled.

    This function behaves like console.print() but only outputs when --debug flag is set.
    Use this for diagnostic information, URL construction details, authentication status, etc.

    Args:
        *args: Arguments to pass to console.print()
        **kwargs: Keyword arguments to pass to console.print()
    """
    if _debug_mode:
        console = get_configured_console()
        console.print(*args, **kwargs)

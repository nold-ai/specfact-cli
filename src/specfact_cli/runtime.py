"""
Runtime configuration helpers shared across commands.

Centralizes CLI-wide settings such as operational mode, interaction style,
and preferred structured data formats for inputs/outputs.
"""

from __future__ import annotations

import sys

from beartype import beartype

from specfact_cli.modes import OperationalMode
from specfact_cli.utils.structured_io import StructuredFormat


_operational_mode: OperationalMode = OperationalMode.CICD
_input_format: StructuredFormat = StructuredFormat.YAML
_output_format: StructuredFormat = StructuredFormat.YAML
_non_interactive_override: bool | None = None


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

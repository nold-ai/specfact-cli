"""
Terminal capability detection and configuration for Rich Console and Progress.

This module provides utilities to detect terminal capabilities (colors, animations,
interactive features) and configure Rich Console and Progress accordingly for optimal
user experience across different terminal environments (full terminals, embedded
terminals, CI/CD pipelines).
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Any

from beartype import beartype
from icontract import ensure, require
from rich.progress import BarColumn, SpinnerColumn, TextColumn, TimeElapsedColumn


_CI_ENV_VARS = ("CI", "GITHUB_ACTIONS", "GITLAB_CI", "CIRCLECI", "TRAVIS", "JENKINS_URL", "BUILDKITE")


def _is_ci_environment() -> bool:
    return any(os.environ.get(var) for var in _CI_ENV_VARS)


def _stdout_is_tty() -> bool:
    try:
        return bool(sys.stdout and sys.stdout.isatty())
    except Exception:  # pragma: no cover - defensive fallback
        return False


def _compute_supports_color(no_color: bool, force_color: bool, is_tty: bool, is_ci: bool) -> bool:
    if no_color:
        return False
    if force_color:
        return True
    term = os.environ.get("TERM", "")
    colorterm = os.environ.get("COLORTERM", "")
    return (is_tty and not is_ci) or bool(term and "color" in term.lower()) or bool(colorterm)


@dataclass(frozen=True)
class TerminalCapabilities:
    """Terminal capability information."""

    supports_color: bool
    supports_animations: bool
    is_interactive: bool
    is_ci: bool
    supports_unicode: bool = True
    stream_encoding: str | None = None


def _get_stream_encoding(stream: Any) -> str | None:
    """Return normalized stream encoding when available."""
    encoding = getattr(stream, "encoding", None)
    return str(encoding) if encoding else None


def _stream_supports_unicode(stream: Any) -> bool:
    """Check whether the stream encoding can emit common SpecFact symbols."""
    encoding = _get_stream_encoding(stream)
    if encoding is None:
        return True
    try:
        "✓⚠".encode(encoding)
    except (LookupError, UnicodeEncodeError):
        return False
    return True


@beartype
@ensure(lambda result: isinstance(result, TerminalCapabilities), "Must return TerminalCapabilities")
def detect_terminal_capabilities() -> TerminalCapabilities:
    """
    Detect terminal capabilities from environment variables and TTY checks.

    Detects:
    - Color support via NO_COLOR, FORCE_COLOR, TERM, COLORTERM env vars
    - Terminal type (interactive TTY vs non-interactive)
    - CI/CD environment (CI, GITHUB_ACTIONS, GITLAB_CI, etc.)
    - Animation support (based on terminal type and capabilities)
    - Test mode (TEST_MODE env var = minimal terminal)

    Returns:
        TerminalCapabilities instance with detected capabilities
    """
    no_color = os.environ.get("NO_COLOR") is not None
    force_color = os.environ.get("FORCE_COLOR") == "1"
    is_ci = _is_ci_environment()
    is_test_mode = os.environ.get("TEST_MODE") == "true" or os.environ.get("PYTEST_CURRENT_TEST") is not None
    is_tty = _stdout_is_tty()
    supports_color = _compute_supports_color(no_color, force_color, is_tty, is_ci)
    stream_encoding = _get_stream_encoding(sys.stdout)
    supports_unicode = _stream_supports_unicode(sys.stdout)

    # Determine animation support
    # Animations require interactive TTY and not CI/CD, and not test mode
    supports_animations = is_tty and not is_ci and not is_test_mode

    # Interactive means TTY and not CI/CD
    is_interactive = is_tty and not is_ci

    return TerminalCapabilities(
        supports_color=supports_color,
        supports_animations=supports_animations,
        is_interactive=is_interactive,
        is_ci=is_ci,
        supports_unicode=supports_unicode,
        stream_encoding=stream_encoding,
    )


@beartype
@ensure(lambda result: result is None, "Function returns None")
def ensure_output_stream_safety(stdout: Any | None = None, stderr: Any | None = None) -> None:
    """Switch unicode-unsafe text streams to replacement mode to avoid hard encode failures."""
    for stream in (sys.stdout if stdout is None else stdout, sys.stderr if stderr is None else stderr):
        if stream is None or _stream_supports_unicode(stream):
            continue
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(errors="replace")


@beartype
@ensure(lambda result: isinstance(result, dict), "Must return dict")
def get_console_config() -> dict[str, Any]:
    """
    Get Rich Console configuration based on terminal capabilities.

    Returns:
        Dictionary of Console kwargs based on detected capabilities
    """
    caps = detect_terminal_capabilities()

    config: dict[str, Any] = {}

    # Set force_terminal based on interactive status
    # For non-interactive terminals, don't force terminal mode
    if not caps.is_interactive:
        config["force_terminal"] = False

    # Set no_color based on color support
    if not caps.supports_color:
        config["no_color"] = True

    # Set width for non-interactive terminals (default to 80)
    if not caps.is_interactive:
        config["width"] = 80

    # Legacy Windows support (check if on Windows)
    if sys.platform == "win32":
        config["legacy_windows"] = True

    if not caps.supports_unicode:
        config["emoji"] = False
        config["safe_box"] = True

    # In test mode, don't explicitly set file=sys.stdout when using Typer's CliRunner
    # CliRunner needs to capture output itself, so we let it use the default file
    # Only set file=sys.stdout if we're not in a CliRunner test context
    # (CliRunner tests will work with default console file handling)
    # Note: This allows both pytest's own capturing and CliRunner's capturing to work

    return config


@beartype
@ensure(
    lambda result: (
        isinstance(result, tuple) and len(result) == 2 and isinstance(result[0], tuple) and isinstance(result[1], dict)
    ),
    "Must return tuple of (columns tuple, kwargs dict)",
)
def get_progress_config() -> tuple[tuple[Any, ...], dict[str, Any]]:
    """
    Get Rich Progress configuration based on terminal capabilities.

    Returns:
        Tuple of (columns tuple, kwargs dict) for Progress initialization
        Columns are passed as positional arguments, other config as kwargs
    """
    caps = detect_terminal_capabilities()

    if caps.supports_animations:
        # Full Rich Progress with animations
        columns = (
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
        )
        return columns, {}
    # Basic Progress with text only (no animations)
    columns = (TextColumn("{task.description}"),)
    return columns, {"disable": False}  # Still use Progress, just without animations


@beartype
@require(lambda current: current >= 0, "Current must be non-negative")
@require(lambda total: total >= 0, "Total must be non-negative")
@require(lambda current, total: current <= total or total == 0, "Current must not exceed total")
@ensure(lambda result: result is None, "Function returns None")
def print_progress(description: str, current: int, total: int) -> None:
    """
    Print plain text progress update for basic terminal mode.

    Emits periodic status updates visible in CI/CD logs and embedded terminals.
    Format: "Description... 45% (123/273)" or "Description..." if total is 0.

    Args:
        description: Progress description text
        current: Current progress count
        total: Total progress count (0 for indeterminate)
    """
    if total > 0:
        percentage = (current / total) * 100
        sys.stdout.write(f"{description}... {percentage:.0f}% ({current}/{total})\n")
    else:
        sys.stdout.write(f"{description}...\n")

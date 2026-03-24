"""
Runtime configuration helpers shared across commands.

Centralizes CLI-wide settings such as operational mode, interaction style,
and preferred structured data formats for inputs/outputs.
"""

from __future__ import annotations

import inspect
import json
import logging
import os
import sys
from enum import StrEnum
from logging.handlers import RotatingFileHandler
from typing import Any, cast

from beartype import beartype
from icontract import ensure, require
from rich.console import Console

from specfact_cli.common.logger_setup import (
    LoggerSetup,
    format_debug_log_message,
    get_runtime_logs_dir,
    get_specfact_home_logs_dir,
)
from specfact_cli.modes import OperationalMode
from specfact_cli.utils.structured_io import StructuredFormat
from specfact_cli.utils.terminal import detect_terminal_capabilities, ensure_output_stream_safety, get_console_config


DEBUG_LOG_DATEFMT = "%Y-%m-%d %H:%M:%S"
DEBUG_LOG_FORMAT = "%(asctime)s | %(message)s"


class TerminalMode(StrEnum):
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
_debug_logger: logging.Logger | None = None
_debug_log_path: str | None = None


@beartype
@require(lambda mode: isinstance(mode, OperationalMode), "mode must be a valid OperationalMode")
def set_operational_mode(mode: OperationalMode) -> None:
    """Persist active operational mode for downstream consumers."""
    global _operational_mode
    _operational_mode = mode


@beartype
@ensure(lambda result: isinstance(result, OperationalMode), "Must return a valid OperationalMode")
def get_operational_mode() -> OperationalMode:
    """Return the current operational mode."""
    return _operational_mode


@beartype
@require(
    lambda input_format, output_format: input_format is not None or output_format is not None,
    "At least one format must be specified",
)
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
@ensure(lambda result: isinstance(result, StructuredFormat), "Must return a valid StructuredFormat")
def get_input_format() -> StructuredFormat:
    """Return default structured input format (defaults to YAML)."""
    return _input_format


@beartype
@ensure(lambda result: isinstance(result, StructuredFormat), "Must return a valid StructuredFormat")
def get_output_format() -> StructuredFormat:
    """Return default structured output format (defaults to YAML)."""
    return _output_format


@beartype
@ensure(
    lambda: _non_interactive_override is None or isinstance(_non_interactive_override, bool),
    "Override must remain bool or None",
)
def set_non_interactive_override(value: bool | None) -> None:
    """Force interactive/non-interactive behavior (None resets to auto)."""
    global _non_interactive_override
    _non_interactive_override = value


@beartype
@ensure(lambda result: isinstance(result, bool), "Must return boolean")
def is_non_interactive() -> bool:
    """
    Determine whether prompts should be suppressed.

    Priority:
        1. Explicit override
        2. Terminal/environment auto-detection (CI and TTY)
    """
    if _non_interactive_override is not None:
        return _non_interactive_override

    try:
        caps = detect_terminal_capabilities()
        if caps.is_ci:
            return True
        return not caps.is_interactive
    except Exception:  # pragma: no cover - defensive fallback
        return True


@beartype
@ensure(lambda result: isinstance(result, bool))
def is_interactive() -> bool:
    """Inverse helper for readability."""
    return not is_non_interactive()


@beartype
@ensure(lambda: isinstance(_debug_mode, bool), "Debug mode must remain bool")
def set_debug_mode(enabled: bool) -> None:
    """Enable or disable debug output mode."""
    global _debug_mode
    _debug_mode = enabled


@beartype
@ensure(lambda result: isinstance(result, bool), "Must return boolean")
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


def _is_test_env() -> bool:
    """True when running under pytest or TEST_MODE (avoids caching Console with closed streams)."""
    return os.environ.get("TEST_MODE") == "true" or os.environ.get("PYTEST_CURRENT_TEST") is not None


@beartype
@ensure(lambda result: isinstance(result, Console), "Must return Console")
def get_configured_console() -> Console:
    """
    Get or create configured Console instance based on terminal capabilities.

    Caches Console instance per terminal mode to avoid repeated detection.
    In test mode, never caches so we never hold a reference to a closed stream
    (e.g. CliRunner's captured stdout after invoke() ends).
    """
    mode = get_terminal_mode()
    ensure_output_stream_safety()

    if _is_test_env():
        config = get_console_config()
        return Console(**config)

    if mode not in _console_cache:
        config = get_console_config()
        _console_cache[mode] = Console(**config)

    return _console_cache[mode]


@beartype
@ensure(lambda result: result >= 0, "Must return non-negative count")
def refresh_loaded_module_consoles() -> int:
    """
    Rebind loaded module-level `console` variables to the current configured Console.

    This prevents stale Rich Console instances from referencing closed CliRunner capture
    streams across sequential command invocations in tests.

    Returns:
        Number of module console attributes refreshed.
    """
    from rich.console import Console as RichConsole

    refreshed = 0
    fresh_console = get_configured_console()
    for module in list(sys.modules.values()):
        if module is None:
            continue
        module_name = getattr(module, "__name__", "")
        if not isinstance(module_name, str) or not module_name.startswith("specfact_cli."):
            continue
        module_dict = getattr(module, "__dict__", None)
        if not isinstance(module_dict, dict):
            continue
        module_ns: dict[str, Any] = cast(dict[str, Any], module_dict)
        current_console = module_ns.get("console")
        if current_console is None:
            continue
        if isinstance(current_console, RichConsole):
            try:
                module.console = fresh_console  # type: ignore[attr-defined]
                refreshed += 1
            except Exception:
                continue
    return refreshed


def _get_debug_caller() -> str:
    """Return module:function for the caller of debug_print/debug_log_operation (first frame outside runtime)."""
    for frame_info in inspect.stack():
        module = inspect.getmodule(frame_info.frame)
        if module is None:
            continue
        name = getattr(module, "__name__", "") or ""
        if "specfact_cli.runtime" in name:
            continue
        func = frame_info.function
        return f"{name}:{func}"
    return "unknown"


def _ensure_debug_log_file() -> None:
    """Initialize debug log file under ~/.specfact/logs when debug is on (lazy, once per run)."""
    global _debug_logger
    global _debug_log_path
    if _debug_logger is not None:
        return
    candidate_paths: list[str] = []
    candidate_paths.append(os.path.join(get_specfact_home_logs_dir(), "specfact-debug.log"))
    candidate_paths.append(os.path.join(get_runtime_logs_dir(), "specfact-debug.log"))

    for log_path in candidate_paths:
        try:
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            handler = RotatingFileHandler(
                log_path,
                maxBytes=5 * 1024 * 1024,
                backupCount=5,
                mode="a",
                encoding="utf-8",
            )
            handler.setLevel(logging.DEBUG)
            handler.setFormatter(logging.Formatter(DEBUG_LOG_FORMAT, datefmt=DEBUG_LOG_DATEFMT))
            _debug_logger = logging.getLogger("specfact.debug")
            _debug_logger.setLevel(logging.DEBUG)
            _debug_logger.propagate = False
            _debug_logger.handlers.clear()
            _debug_logger.addHandler(handler)
            _debug_log_path = os.path.abspath(log_path)
            return
        except (OSError, PermissionError):
            continue

    _debug_logger = None
    _debug_log_path = None


@beartype
@require(lambda: isinstance(_debug_mode, bool), "Debug mode must be configured before initializing log")
def init_debug_log_file() -> None:
    """
    Ensure debug log file is initialized when debug mode is on.

    Call this after set_debug_mode(True) so that the first debug_print or
    debug_log_operation writes to ~/.specfact/logs/specfact-debug.log immediately.
    """
    if _debug_mode:
        _ensure_debug_log_file()


@beartype
@ensure(lambda result: result is None or len(result) > 0, "Log path must be non-empty if set")
def get_debug_log_path() -> str | None:
    """Return active debug log file path if initialized, else None."""
    return _debug_log_path


def _append_debug_log(*args: Any, **kwargs: Any) -> None:
    """Write print-style message to the debug log file. No-op if debug off or file unavailable."""
    if not _debug_mode:
        return
    _ensure_debug_log_file()
    if _debug_logger is None:
        return
    plain = format_debug_log_message(*args, **kwargs)
    if plain:
        caller = _get_debug_caller()
        _debug_logger.debug("%s | %s", caller, plain)


@beartype
@require(lambda args: len(args) >= 0)
def debug_print(*args: Any, **kwargs: Any) -> None:
    """
    Print debug messages only if debug mode is enabled.

    This function behaves like console.print() but only outputs when --debug flag is set.
    Also writes the same content to ~/.specfact/logs/specfact-debug.log when debug is on.

    Args:
        *args: Arguments to pass to console.print()
        **kwargs: Keyword arguments to pass to console.print()
    """
    if _debug_mode:
        get_configured_console().print(*args, **kwargs)
        _append_debug_log(*args, **kwargs)


@beartype
@require(lambda operation: bool(operation), "operation must not be empty")
@require(lambda status: bool(status), "status must not be empty")
def debug_log_operation(
    operation: str,
    target: str,
    status: str,
    error: str | None = None,
    extra: dict[str, object] | None = None,
    caller: str | None = None,
) -> None:
    """
    Log structured operation metadata to the debug log file when debug mode is enabled.

    No-op when debug is off. When debug is on, writes a structured line (operation, target,
    status, error, extra, caller) to ~/.specfact/logs/specfact-debug.log. Redacts target/extra
    via LoggerSetup.redact_secrets. Caller (module/method) is included when provided or inferred.

    Args:
        operation: Operation type (e.g. file_read, api_request).
        target: Target path or URL (will be redacted).
        status: Status or result (e.g. success, 200, failure, prepared, finished, failed).
        error: Optional error message.
        extra: Optional dict of extra fields (will be redacted); for API: payload, response, reason.
        caller: Optional module:function for context; if None, inferred from call stack.
    """
    if not _debug_mode:
        return
    _ensure_debug_log_file()
    if _debug_logger is None:
        return
    payload: dict[str, object] = {
        "operation": operation,
        "target": LoggerSetup.redact_secrets(target),
        "status": status,
        "caller": caller if caller is not None else _get_debug_caller(),
    }
    if error is not None:
        payload["error"] = error
    if extra is not None:
        payload["extra"] = LoggerSetup.redact_secrets(extra)
    _debug_logger.debug("debug_log_operation %s", json.dumps(payload, default=str))

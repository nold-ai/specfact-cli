"""
Progressive disclosure utilities for CLI help system.

This module provides utilities for implementing progressive disclosure in Typer CLI,
allowing advanced options to be hidden by default and revealed via --help-advanced.
"""

from __future__ import annotations

import os
import sys
from typing import Any

from beartype import beartype
from click.core import Command, Context as ClickContext
from icontract import ensure
from rich.console import Console
from typer.core import TyperCommand, TyperGroup


console = Console()

# Global flag to track if advanced help is requested
_show_advanced_help = False

# Store original methods (must be done before we define helper functions)
_original_get_params = Command.get_params
_original_make_context = Command.make_context


@beartype
@ensure(lambda result: isinstance(result, bool), "Must return bool")
def is_advanced_help_requested() -> bool:
    """Check if --help-advanced flag is present in sys.argv."""
    return "--help-advanced" in sys.argv or "-ha" in sys.argv or os.environ.get("SPECFACT_SHOW_ADVANCED") == "true"


@beartype
@ensure(lambda result: isinstance(result, bool), "Must return bool")
def should_show_advanced() -> bool:
    """Check if advanced options should be shown."""
    return _show_advanced_help or is_advanced_help_requested()


@beartype
@ensure(lambda result: result is None, "setter returns None")
def set_advanced_help(enabled: bool) -> None:
    """Set advanced help display mode."""
    global _show_advanced_help
    _show_advanced_help = enabled


@beartype
@ensure(lambda result: result is None, "interceptor returns None")
def intercept_help_advanced() -> None:
    """
    Intercept --help-advanced flag and set environment variable.

    This should be called before Typer processes the command.
    We detect --help-advanced and set an environment variable so get_params knows to show hidden options.
    We also normalize sys.argv so Click/Typer treats it like a standard help request.
    """
    # Reset local flag; keep explicit env override if user set it
    set_advanced_help(False)
    if os.environ.get("SPECFACT_SHOW_ADVANCED") == "true":
        set_advanced_help(True)

    # Look for advanced help flags in argv and normalize to --help
    advanced_flag_present = False
    normalized_args: list[str] = []
    for arg in sys.argv:
        if arg in ("--help-advanced", "-ha"):
            advanced_flag_present = True
            normalized_args.append("--help")
            continue
        normalized_args.append(arg)

    if advanced_flag_present:
        os.environ["SPECFACT_SHOW_ADVANCED"] = "true"
        set_advanced_help(True)
        # Replace argv in-place so Click doesn't error on unknown flag
        sys.argv[:] = normalized_args


@beartype
def _is_help_context(ctx: ClickContext | None) -> bool:
    """Check if this context is for showing help."""
    if ctx is None:
        return False
    # Check if help was requested by looking at params or info_name
    if hasattr(ctx, "params") and ctx.params:
        # Check if any help option is in params
        for param in ctx.params.values() if isinstance(ctx.params, dict) else []:
            param_name = getattr(param, "name", None)
            if param_name and param_name in ("--help", "-h", "--help-advanced", "-ha"):
                return True
    # Check info_name for help indicators
    return bool(hasattr(ctx, "info_name") and ctx.info_name and "help" in str(ctx.info_name).lower())


@beartype
def _is_advanced_help_context(ctx: ClickContext | None) -> bool:
    """Check if this context is for showing advanced help."""
    # Check sys.argv directly first
    if "--help-advanced" in sys.argv or "-ha" in sys.argv:
        return True
    # Also check environment variable (set by intercept_help_advanced)
    # This is needed because Click might process --help-advanced before get_params is called
    if os.environ.get("SPECFACT_SHOW_ADVANCED") == "true":
        return True
    # Also check global flag
    return _show_advanced_help


class ProgressiveDisclosureGroup(TyperGroup):
    """Custom Typer group that shows hidden options when advanced help is requested."""

    @beartype
    @ensure(lambda result: isinstance(result, list), "returns param list")
    def get_params(self, ctx: ClickContext) -> list[Any]:
        """
        Override get_params to include hidden options when advanced help is requested.

        Click filters hidden params in get_params(), not format_options(), so we must
        override this method to return all params (including hidden) when --help-advanced is used.

        IMPORTANT: We need to get ALL params from self.params first (including hidden),
        then filter based on whether advanced help is requested. We can't rely on
        super().get_params() because it already filters hidden params.
        """
        # Check if this is advanced help context
        is_advanced = _is_advanced_help_context(ctx)

        # Get ALL params from self.params (including hidden ones)
        help_option = self.get_help_option(ctx)
        all_params = list(self.params)
        if help_option is not None:
            all_params.append(help_option)

        # If advanced help is requested, return all params (including hidden)
        if is_advanced:
            # Un-hide advanced params for this help rendering
            for param in all_params:
                if getattr(param, "hidden", False):
                    param.hidden = False  # type: ignore[attr-defined]
            return all_params

        # Otherwise, filter out hidden params (default behavior)
        return [param for param in all_params if not getattr(param, "hidden", False)]


def _filter_advanced_sections(help_text: str) -> str:
    """Return help text with Advanced/Configuration sections removed."""
    lines = help_text.split("\n")
    filtered: list[str] = []
    skip = False
    for line in lines:
        if "**Advanced/Configuration**" in line or "Advanced/Configuration:" in line:
            skip = True
            continue
        if skip and (line.strip().startswith("**") or not line.strip()):
            skip = False
        if not skip:
            filtered.append(line)
    return "\n".join(filtered)


class ProgressiveDisclosureCommand(TyperCommand):
    """Custom Typer command that shows hidden options when advanced help is requested."""

    @beartype
    @ensure(lambda result: bool(result), "help text must be non-empty")
    def _get_help_text(self) -> str:
        """Return the current help string (pure query — no mutation)."""
        return self.help or ""

    @beartype
    @ensure(lambda result: result is None, "setter returns None")
    def _set_help_text(self, text: str) -> None:
        """Set the help string (pure command — no prior read)."""
        self.help = text

    @beartype
    @ensure(lambda result: result is None, "formatter returns None")
    def format_help(self, ctx: ClickContext, formatter: Any) -> None:
        """
        Override format_help to conditionally show advanced options in docstring.

        Filters the Advanced/Configuration section from the docstring when regular
        help is shown, but includes it when --help-advanced is used.
        """
        is_advanced = _is_advanced_help_context(ctx)

        if not is_advanced and hasattr(self, "help") and self.help:
            # Use query/command helpers to avoid get-modify-same-method pattern.
            original = self._get_help_text()
            self._set_help_text(_filter_advanced_sections(original))
            try:
                super().format_help(ctx, formatter)
            finally:
                self._set_help_text(original)
        else:
            super().format_help(ctx, formatter)

    @beartype
    @ensure(lambda result: isinstance(result, list), "returns param list")
    def get_params(self, ctx: ClickContext) -> list[Any]:
        """
        Override get_params to include hidden options when advanced help is requested.

        Click filters hidden params in get_params(), not format_options(), so we must
        override this method to return all params (including hidden) when --help-advanced is used.

        IMPORTANT: We need to get ALL params from self.params first (including hidden),
        then filter based on whether advanced help is requested. We can't rely on
        super().get_params() because it already filters hidden params.
        """
        # Check if this is advanced help context
        is_advanced = _is_advanced_help_context(ctx)

        # Get ALL params from self.params (including hidden ones)
        help_option = self.get_help_option(ctx)
        all_params = list(self.params)
        if help_option is not None:
            all_params.append(help_option)

        # If advanced help is requested, return all params (including hidden)
        if is_advanced:
            # Un-hide advanced params for this help rendering
            for param in all_params:
                if getattr(param, "hidden", False):
                    param.hidden = False  # type: ignore[attr-defined]
            return all_params

        # Otherwise, filter out hidden params (default behavior)
        return [param for param in all_params if not getattr(param, "hidden", False)]


@beartype
@ensure(lambda result: bool(result), "message must be non-empty")
def get_help_advanced_message() -> str:
    """Get message explaining how to access advanced help."""
    return "\n[dim]💡 Tip: Use [bold]--help-advanced[/bold] (alias: [bold]-ha[/bold]) to see all options including advanced configuration.[/dim]"


@beartype
@ensure(lambda result: isinstance(result, bool), "Must return bool")
def get_hidden_value() -> bool:
    """
    Get the hidden value for advanced options.

    This function checks the environment variable at call time.
    Since Typer evaluates hidden at definition time, we check
    the environment variable that's set by intercept_help_advanced().

    Returns:
        True if options should be hidden, False if they should be shown.
    """
    # Check environment variable set by intercept_help_advanced()
    return os.environ.get("SPECFACT_SHOW_ADVANCED") != "true"


@beartype
def _patched_get_params(self: Command, ctx: ClickContext) -> list[Any]:
    """
    Patched get_params that includes hidden options when advanced help is requested.

    This is monkey-patched onto Click's Command class to work for all commands,
    including subcommands created by Typer.

    IMPORTANT: We need to get ALL params from self.params first (including hidden),
    then filter based on whether advanced help is requested. We can't rely on
    the original get_params because it already filters hidden params.
    """
    # Check if this is advanced help context
    is_advanced = _is_advanced_help_context(ctx)

    # Get ALL params from self.params (including hidden ones)
    help_option = self.get_help_option(ctx)
    all_params = list(self.params)
    if help_option is not None:
        all_params.append(help_option)

    # If advanced help is requested, return all params (including hidden)
    if is_advanced:
        # Un-hide advanced params for this help rendering
        for param in all_params:
            if getattr(param, "hidden", False):
                param.hidden = False  # type: ignore[attr-defined]
        return all_params

    # Otherwise, use original behavior (filter out hidden params)
    return _original_get_params(self, ctx)


@beartype
def _ensure_help_advanced_in_context_settings(self: Command) -> None:
    """Ensure --help-advanced and --help are in context_settings.help_option_names."""
    # Get or create context settings
    if self.context_settings is None:
        self.context_settings = {}
    elif not isinstance(self.context_settings, dict):
        self.context_settings = dict(self.context_settings)

    # Ensure help_option_names includes standard help options and --help-advanced
    help_option_names = list(self.context_settings.get("help_option_names", ["-h", "--help"]))
    # Ensure standard help options are present
    if "-h" not in help_option_names:
        help_option_names.insert(0, "-h")
    if "--help" not in help_option_names:
        help_option_names.append("--help")
    # Add --help-advanced
    if "--help-advanced" not in help_option_names:
        help_option_names.append("--help-advanced")
    if "-ha" not in help_option_names:
        help_option_names.append("-ha")

    # Update context settings
    self.context_settings["help_option_names"] = help_option_names


# Remove parse_args patch - we handle it in intercept_help_advanced instead


@beartype
def _patched_make_context(
    self: Command,
    info_name: str | None = None,
    args: list[str] | None = None,
    parent: ClickContext | None = None,
    **extra: Any,
) -> ClickContext:
    """
    Patched make_context that ensures --help-advanced is always in help_option_names.

    This is called BEFORE argument parsing, so we can ensure --help-advanced is recognized.
    """
    # Ensure --help-advanced is in help_option_names BEFORE creating context
    # This must happen before Click processes arguments
    _ensure_help_advanced_in_context_settings(self)

    # Ensure args is not None
    if args is None:
        args = []

    return _original_make_context(self, info_name, args, parent, **extra)


# Monkey-patch Click's Command class to use our patched methods
# This must happen after all helper functions are defined
Command.get_params = _patched_get_params  # type: ignore[assignment]
Command.make_context = _patched_make_context  # type: ignore[assignment]

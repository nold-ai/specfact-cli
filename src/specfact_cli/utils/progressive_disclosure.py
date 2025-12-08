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
from click.core import Context as ClickContext
from rich.console import Console
from typer.core import TyperGroup


console = Console()

# Global flag to track if advanced help is requested
_show_advanced_help = False


@beartype
def is_advanced_help_requested() -> bool:
    """Check if --help-advanced flag is present in sys.argv."""
    return (
        "--help-advanced" in sys.argv or "-h-advanced" in sys.argv or os.environ.get("SPECFACT_SHOW_ADVANCED") == "true"
    )


@beartype
def should_show_advanced() -> bool:
    """Check if advanced options should be shown."""
    return _show_advanced_help or is_advanced_help_requested()


@beartype
def set_advanced_help(enabled: bool) -> None:
    """Set advanced help display mode."""
    global _show_advanced_help
    _show_advanced_help = enabled


@beartype
def intercept_help_advanced() -> None:
    """
    Intercept --help-advanced flag and show advanced help.

    This should be called before Typer processes the command.
    Sets environment variable that Typer can check.
    """
    if "--help-advanced" in sys.argv or "-h-advanced" in sys.argv:
        # Remove --help-advanced from argv
        sys.argv = [arg for arg in sys.argv if arg not in ("--help-advanced", "-h-advanced")]
        # Set environment variable so Typer can show hidden options
        os.environ["SPECFACT_SHOW_ADVANCED"] = "true"
        set_advanced_help(True)
        # If --help is not already present, add it
        if "--help" not in sys.argv and "-h" not in sys.argv:
            sys.argv.append("--help")


class ProgressiveDisclosureGroup(TyperGroup):
    """Custom Typer group that shows hidden options when advanced help is requested."""

    def format_options(self, ctx: ClickContext, formatter: Any) -> None:
        """Format options with progressive disclosure."""
        # Call parent to get standard formatting
        super().format_options(ctx, formatter)

        # If advanced help is requested, show hidden options
        if should_show_advanced():
            # Typer will automatically show hidden options when SPECFACT_SHOW_ADVANCED is set
            # This is handled by checking hidden attribute in Typer's help formatter
            pass


@beartype
def get_help_advanced_message() -> str:
    """Get message explaining how to access advanced help."""
    return "\n[dim]💡 Tip: Use [bold]--help-advanced[/bold] to see all options including advanced configuration.[/dim]"


@beartype
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

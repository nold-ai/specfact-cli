"""
Progress display utilities for consistent UI/UX across all commands.

This module provides unified progress display functions that ensure
consistent formatting and user experience across all CLI commands.
Includes timing information for visibility into operation duration.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path
from time import time
from typing import Any

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from specfact_cli.models.project import ProjectBundle
from specfact_cli.utils.bundle_loader import load_project_bundle, save_project_bundle


console = Console()


def _is_test_mode() -> bool:
    """Check if running in test mode."""
    return os.environ.get("TEST_MODE") == "true" or os.environ.get("PYTEST_CURRENT_TEST") is not None


def _safe_progress_display(display_console: Console) -> bool:
    """
    Check if it's safe to create a Progress display.

    Returns True if Progress can be created, False if it should be skipped.
    """
    # Always skip in test mode
    if _is_test_mode():
        return False

    # Try to detect if a Progress is already active by checking console state
    # This is a best-effort check - we'll catch LiveError if it fails
    try:
        # Rich stores active Live displays in Console._live
        if hasattr(display_console, "_live") and display_console._live is not None:
            return False
    except Exception:
        pass

    return True


def create_progress_callback(progress: Progress, task_id: Any, prefix: str = "") -> Callable[[int, int, str], None]:
    """
    Create a standardized progress callback function.

    Args:
        progress: Rich Progress instance
        task_id: Task ID from progress.add_task()
        prefix: Optional prefix for progress messages (e.g., "Loading", "Saving")

    Returns:
        Callback function that updates progress with n/m counter format
    """

    def callback(current: int, total: int, artifact: str) -> None:
        """Update progress with n/m counter format."""
        if prefix:
            description = f"{prefix} artifact {current}/{total}: {artifact}"
        else:
            description = f"Processing artifact {current}/{total}: {artifact}"
        progress.update(task_id, description=description)

    return callback


def load_bundle_with_progress(
    bundle_dir: Path,
    validate_hashes: bool = False,
    console_instance: Console | None = None,
) -> ProjectBundle:
    """
    Load project bundle with unified progress display.

    Uses consistent n/m counter format: "Loading artifact 3/12: FEATURE-001.yaml"
    Includes timing information showing elapsed time.

    Args:
        bundle_dir: Path to bundle directory
        validate_hashes: Whether to validate file checksums
        console_instance: Optional Console instance (defaults to module console)

    Returns:
        Loaded ProjectBundle instance
    """
    display_console = console_instance or console
    start_time = time()

    # Try to use Progress display, but fall back to direct load if it fails
    # (e.g., if another Progress is already active)
    use_progress = _safe_progress_display(display_console)

    if use_progress:
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                TimeElapsedColumn(),
                console=display_console,
            ) as progress:
                task = progress.add_task("Loading project bundle...", total=None)

                progress_callback = create_progress_callback(progress, task, prefix="Loading")

                bundle = load_project_bundle(
                    bundle_dir,
                    validate_hashes=validate_hashes,
                    progress_callback=progress_callback,
                )
                elapsed = time() - start_time
                progress.update(task, description=f"✓ Bundle loaded ({elapsed:.2f}s)")
            return bundle
        except Exception:
            # If Progress creation fails (e.g., LiveError), fall back to direct load
            pass

    # No progress display - just load directly
    return load_project_bundle(
        bundle_dir,
        validate_hashes=validate_hashes,
        progress_callback=None,
    )


def save_bundle_with_progress(
    bundle: ProjectBundle,
    bundle_dir: Path,
    atomic: bool = True,
    console_instance: Console | None = None,
) -> None:
    """
    Save project bundle with unified progress display.

    Uses consistent n/m counter format: "Saving artifact 3/12: FEATURE-001.yaml"
    Includes timing information showing elapsed time.

    Args:
        bundle: ProjectBundle instance to save
        bundle_dir: Path to bundle directory
        atomic: Whether to use atomic writes
        console_instance: Optional Console instance (defaults to module console)
    """
    display_console = console_instance or console
    start_time = time()

    # Try to use Progress display, but fall back to direct save if it fails
    # (e.g., if another Progress is already active)
    use_progress = _safe_progress_display(display_console)

    if use_progress:
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                TimeElapsedColumn(),
                console=display_console,
            ) as progress:
                task = progress.add_task("Saving project bundle...", total=None)

                progress_callback = create_progress_callback(progress, task, prefix="Saving")

                save_project_bundle(bundle, bundle_dir, atomic=atomic, progress_callback=progress_callback)
                elapsed = time() - start_time
                progress.update(task, description=f"✓ Bundle saved ({elapsed:.2f}s)")
            return
        except Exception:
            # If Progress creation fails (e.g., LiveError), fall back to direct save
            pass

    # No progress display - just save directly
    save_project_bundle(bundle, bundle_dir, atomic=atomic, progress_callback=None)

"""
Startup Checks - Template file validation and version checking.

This module provides utilities for checking:
1. Template files in IDE directories vs our templates (hash comparison)
2. CLI version updates available from PyPI
"""

from __future__ import annotations

import contextlib
import hashlib
from datetime import UTC
from pathlib import Path
from typing import Any, NamedTuple

import requests
from beartype import beartype
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from specfact_cli import __version__
from specfact_cli.utils.ide_setup import IDE_CONFIG, detect_ide, find_package_resources_path
from specfact_cli.utils.metadata import (
    get_last_checked_version,
    get_last_version_check_timestamp,
    is_version_check_needed,
    update_metadata,
)


console = Console()


class TemplateCheckResult(NamedTuple):
    """Result of template file comparison."""

    ide: str
    templates_outdated: bool
    missing_templates: list[str]
    outdated_templates: list[str]
    ide_dir: Path | None


class VersionCheckResult(NamedTuple):
    """Result of version check."""

    current_version: str
    latest_version: str | None
    update_available: bool
    update_type: str | None  # "minor" or "major"
    error: str | None


@beartype
def calculate_file_hash(file_path: Path) -> str:
    """
    Calculate SHA256 hash of a file.

    Args:
        file_path: Path to file

    Returns:
        SHA256 hash as hex string
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


@beartype
def check_ide_templates(repo_path: Path | None = None) -> TemplateCheckResult | None:
    """
    Check if IDE template files exist and compare with our templates.

    Args:
        repo_path: Repository path (default: current directory)

    Returns:
        TemplateCheckResult if IDE detected and templates found, None otherwise
    """
    if repo_path is None:
        repo_path = Path.cwd()

    # Detect IDE
    try:
        detected_ide = detect_ide("auto")
    except Exception:
        return None

    if detected_ide not in IDE_CONFIG:
        return None

    config = IDE_CONFIG[detected_ide]
    ide_folder = str(config["folder"])
    ide_dir = repo_path / ide_folder

    if not ide_dir.exists():
        return None

    # Find our template resources
    templates_dir = find_package_resources_path("specfact_cli", "resources/prompts")
    if templates_dir is None:
        # Fallback: try to find in development environment
        from specfact_cli.utils.ide_setup import SPECFACT_COMMANDS

        # Check if we're in a development environment
        repo_root = repo_path
        while repo_root.parent != repo_root:
            dev_templates = repo_root / "resources" / "prompts"
            if dev_templates.exists():
                templates_dir = dev_templates
                break
            repo_root = repo_root.parent

        if templates_dir is None:
            return None

    # Get list of template files we expect
    from specfact_cli.utils.ide_setup import SPECFACT_COMMANDS

    format_type = str(config["format"])
    expected_files: list[str] = []
    for command in SPECFACT_COMMANDS:
        if format_type == "prompt.md":
            expected_files.append(f"{command}.prompt.md")
        elif format_type == "toml":
            expected_files.append(f"{command}.toml")
        else:
            expected_files.append(f"{command}.md")

    # Check each expected template file
    missing_templates: list[str] = []
    outdated_templates: list[str] = []

    for expected_file in expected_files:
        ide_file = ide_dir / expected_file
        # Get source template name (remove format-specific extensions to get base command name)
        # e.g., "specfact.01-import.prompt.md" -> "specfact.01-import.md"
        source_template_name = expected_file.replace(".prompt.md", ".md").replace(".toml", ".md")
        source_file = templates_dir / source_template_name

        if not ide_file.exists():
            missing_templates.append(expected_file)
            continue

        if not source_file.exists():
            # Source template doesn't exist, skip comparison
            continue

        # Compare modification times as a heuristic
        # If source template is newer, IDE template might be outdated
        with contextlib.suppress(Exception):
            source_mtime = source_file.stat().st_mtime
            ide_mtime = ide_file.stat().st_mtime

            # If source is significantly newer (more than 1 second), consider outdated
            # This accounts for the fact that processed templates will have different content
            if source_mtime > ide_mtime + 1.0:
                outdated_templates.append(expected_file)

    templates_outdated = len(outdated_templates) > 0 or len(missing_templates) > 0

    return TemplateCheckResult(
        ide=detected_ide,
        templates_outdated=templates_outdated,
        missing_templates=missing_templates,
        outdated_templates=outdated_templates,
        ide_dir=ide_dir if ide_dir.exists() else None,
    )


@beartype
def check_pypi_version(package_name: str = "specfact-cli", timeout: int = 3) -> VersionCheckResult:
    """
    Check PyPI for available version updates.

    Args:
        package_name: Package name on PyPI
        timeout: Request timeout in seconds

    Returns:
        VersionCheckResult with update information
    """
    current_version = __version__

    try:
        # Query PyPI JSON API
        url = f"https://pypi.org/pypi/{package_name}/json"
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()

        data = response.json()
        latest_version = data.get("info", {}).get("version")

        if latest_version is None:
            return VersionCheckResult(
                current_version=current_version,
                latest_version=None,
                update_available=False,
                update_type=None,
                error="Could not determine latest version from PyPI",
            )

        # Compare versions
        try:
            from packaging import version
        except ImportError:
            # Fallback: simple string comparison if packaging not available
            return VersionCheckResult(
                current_version=current_version,
                latest_version=latest_version,
                update_available=latest_version != current_version,
                update_type="unknown" if latest_version != current_version else None,
                error=None,
            )

        current = version.parse(current_version)
        latest = version.parse(latest_version)

        if latest > current:
            # Determine update type
            if latest.major > current.major:
                update_type = "major"
            elif latest.minor > current.minor:
                update_type = "minor"
            elif latest.micro > current.micro:
                update_type = "patch"
            else:
                # Pre-release or dev version
                update_type = "patch"

            return VersionCheckResult(
                current_version=current_version,
                latest_version=latest_version,
                update_available=True,
                update_type=update_type,
                error=None,
            )

        return VersionCheckResult(
            current_version=current_version,
            latest_version=latest_version,
            update_available=False,
            update_type=None,
            error=None,
        )

    except requests.RequestException as e:
        return VersionCheckResult(
            current_version=current_version,
            latest_version=None,
            update_available=False,
            update_type=None,
            error=f"Failed to check PyPI: {e}",
        )
    except Exception as e:
        return VersionCheckResult(
            current_version=current_version,
            latest_version=None,
            update_available=False,
            update_type=None,
            error=f"Unexpected error: {e}",
        )


@beartype
def print_startup_checks(
    repo_path: Path | None = None,
    check_version: bool = True,
    show_progress: bool = True,
    skip_checks: bool = False,
) -> None:
    """
    Print startup check warnings for templates and version updates.

    Optimized to only run checks when needed:
    - Template checks: Only run if CLI version has changed since last check
    - Version checks: Only run if >= 24 hours since last check

    Args:
        repo_path: Repository path (default: current directory)
        check_version: Whether to check for version updates
        show_progress: Whether to show progress indicators during checks
        skip_checks: If True, skip all checks (for CI/CD environments)
    """
    if repo_path is None:
        repo_path = Path.cwd()

    if skip_checks:
        return

    # Check if template check should run (only if version changed)
    last_checked_version = get_last_checked_version()
    should_check_templates = last_checked_version != __version__

    # Check if version check should run (only if >= 24 hours since last check)
    last_version_check_timestamp = get_last_version_check_timestamp()
    should_check_version = check_version and is_version_check_needed(last_version_check_timestamp)

    # Use progress indicator for checks that might take time
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,  # Hide progress when done
    ) as progress:
        # Check IDE templates (only if version changed)
        template_result = None
        if should_check_templates:
            template_task = (
                progress.add_task("[cyan]Checking IDE templates...[/cyan]", total=None) if show_progress else None
            )
            template_result = check_ide_templates(repo_path)
            if template_task:
                progress.update(template_task, description="[green]✓[/green] Checked IDE templates")

        if template_result and template_result.templates_outdated:
            details = []
            if template_result.missing_templates:
                details.append(f"Missing: {len(template_result.missing_templates)} template(s)")
            if template_result.outdated_templates:
                details.append(f"Outdated: {len(template_result.outdated_templates)} template(s)")

            details_str = "\n".join(details) if details else "Templates differ from current version"

            console.print()
            console.print(
                Panel(
                    f"[bold yellow]⚠ IDE Templates Outdated[/bold yellow]\n\n"
                    f"IDE: [cyan]{template_result.ide}[/cyan]\n"
                    f"Location: [dim]{template_result.ide_dir}[/dim]\n\n"
                    f"{details_str}\n\n"
                    f"Run [bold]specfact init --force[/bold] to update them.",
                    border_style="yellow",
                )
            )

        # Check version updates (only if >= 24 hours since last check)
        version_result = None
        if should_check_version:
            version_task = (
                progress.add_task("[cyan]Checking for updates...[/cyan]", total=None) if show_progress else None
            )
            version_result = check_pypi_version()
            if version_task:
                progress.update(version_task, description="[green]✓[/green] Checked for updates")

            if version_result.update_available and version_result.latest_version and version_result.update_type:
                update_type_color = "red" if version_result.update_type == "major" else "yellow"
                update_type_icon = "🔴" if version_result.update_type == "major" else "🟡"
                update_message = (
                    f"[bold {update_type_color}]{update_type_icon} {version_result.update_type.upper()} Update Available[/bold {update_type_color}]\n\n"
                    f"Current: [cyan]{version_result.current_version}[/cyan]\n"
                    f"Latest: [green]{version_result.latest_version}[/green]\n\n"
                )
                if version_result.update_type == "major":
                    update_message += (
                        "[bold red]⚠ Breaking changes may be present![/bold red]\n"
                        "Review release notes before upgrading.\n\n"
                    )
                update_message += (
                    "Upgrade with: [bold]specfact upgrade[/bold] or [bold]pip install --upgrade specfact-cli[/bold]"
                )

                console.print()
                console.print(Panel(update_message, border_style=update_type_color))

        # Update metadata after checks complete
        from datetime import datetime

        metadata_updates: dict[str, Any] = {}
        if should_check_templates or should_check_version:
            metadata_updates["last_checked_version"] = __version__
        if should_check_version:
            metadata_updates["last_version_check_timestamp"] = datetime.now(UTC).isoformat()

        if metadata_updates:
            update_metadata(**metadata_updates)

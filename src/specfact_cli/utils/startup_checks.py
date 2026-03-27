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
from icontract import ensure, require
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from specfact_cli import __version__
from specfact_cli.registry.module_installer import get_outdated_or_missing_bundled_modules
from specfact_cli.utils.contract_predicates import file_path_exists, optional_repo_path_exists
from specfact_cli.utils.ide_setup import IDE_CONFIG, detect_ide, discover_prompt_template_files
from specfact_cli.utils.metadata import (
    get_last_checked_version,
    get_last_module_freshness_check_timestamp,
    get_last_version_check_timestamp,
    is_version_check_needed,
    update_metadata,
)


console = Console()


def _pypi_check_args_valid(package_name: str, timeout: int) -> bool:
    return package_name.strip() != "" and timeout > 0


class TemplateCheckResult(NamedTuple):
    """Result of template file comparison."""

    ide: str
    templates_outdated: bool
    missing_templates: list[str]
    outdated_templates: list[str]
    ide_dir: Path | None
    sources_available: bool = True


class VersionCheckResult(NamedTuple):
    """Result of version check."""

    current_version: str
    latest_version: str | None
    update_available: bool
    update_type: str | None  # "minor" or "major"
    error: str | None


class ModuleFreshnessCheckResult(NamedTuple):
    """Result of bundled module freshness checks for project/user scopes."""

    project_outdated: bool
    user_outdated: bool
    project_outdated_modules: list[str]
    user_outdated_modules: list[str]
    project_modules_root: Path
    user_modules_root: Path


@beartype
@require(file_path_exists, "file_path must exist")
@ensure(lambda result: len(result) == 64, "Must return 64-char SHA256 hex string")
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


def _template_sources_by_basename(repo_path: Path) -> dict[str, Path]:
    """Map specfact*.md basename -> path for drift checks (installed modules and optional dev repo)."""
    files = discover_prompt_template_files(repo_path, include_package_fallback=True)
    return {p.name: p for p in files}


def _expected_ide_template_filenames(format_type: str) -> list[str]:
    from specfact_cli.utils.ide_setup import SPECFACT_COMMANDS

    expected_files: list[str] = []
    for command in SPECFACT_COMMANDS:
        if format_type == "prompt.md":
            expected_files.append(f"{command}.prompt.md")
        elif format_type == "toml":
            expected_files.append(f"{command}.toml")
        else:
            expected_files.append(f"{command}.md")
    return expected_files


def _find_ide_exported_prompt_file(ide_dir: Path, basename: str) -> Path | None:
    """Resolve an exported prompt filename under flat or source-namespaced layouts."""
    direct = ide_dir / basename
    if direct.is_file():
        return direct
    try:
        for path in ide_dir.rglob(basename):
            if path.is_file():
                return path
    except OSError:
        return None
    return None


def _scan_ide_template_drift(
    ide_dir: Path,
    source_by_basename: dict[str, Path],
    expected_files: list[str],
) -> tuple[list[str], list[str]]:
    missing_templates: list[str] = []
    outdated_templates: list[str] = []
    for expected_file in expected_files:
        source_template_name = expected_file.replace(".prompt.md", ".md").replace(".toml", ".md")
        source_file = source_by_basename.get(source_template_name)
        if source_file is None or not source_file.exists():
            continue
        ide_file = _find_ide_exported_prompt_file(ide_dir, expected_file)
        if ide_file is None:
            missing_templates.append(expected_file)
            continue
        with contextlib.suppress(Exception):
            source_mtime = source_file.stat().st_mtime
            ide_mtime = ide_file.stat().st_mtime
            if source_mtime > ide_mtime + 1.0:
                outdated_templates.append(expected_file)
    return missing_templates, outdated_templates


@beartype
@require(optional_repo_path_exists, "repo_path must exist if provided")
def check_ide_templates(repo_path: Path | None = None) -> TemplateCheckResult | None:
    """
    Check if IDE template files exist and compare with our templates.

    Args:
        repo_path: Repository path (default: current directory)

    Returns:
        ``TemplateCheckResult`` when an IDE export directory exists (``sources_available`` is False
        when no prompt templates are discoverable). ``None`` when IDE detection fails or the IDE
        folder is missing.
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

    source_by_basename = _template_sources_by_basename(repo_path)
    if not source_by_basename:
        return TemplateCheckResult(
            ide=detected_ide,
            templates_outdated=False,
            missing_templates=[],
            outdated_templates=[],
            ide_dir=ide_dir if ide_dir.exists() else None,
            sources_available=False,
        )

    format_type = str(config["format"])
    expected_files = _expected_ide_template_filenames(format_type)
    missing_templates, outdated_templates = _scan_ide_template_drift(ide_dir, source_by_basename, expected_files)

    templates_outdated = len(outdated_templates) > 0 or len(missing_templates) > 0

    return TemplateCheckResult(
        ide=detected_ide,
        templates_outdated=templates_outdated,
        missing_templates=missing_templates,
        outdated_templates=outdated_templates,
        ide_dir=ide_dir if ide_dir.exists() else None,
        sources_available=True,
    )


@beartype
@require(_pypi_check_args_valid, "package_name must not be empty and timeout must be positive")
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
@require(optional_repo_path_exists, "repo_path must exist if provided")
def check_module_freshness(repo_path: Path | None = None) -> ModuleFreshnessCheckResult:
    """Check bundled module freshness for project and user scopes."""
    if repo_path is None:
        repo_path = Path.cwd()

    project_modules_root = repo_path / ".specfact" / "modules"
    user_modules_root = Path.home() / ".specfact" / "modules"

    project_outdated_modules = get_outdated_or_missing_bundled_modules(project_modules_root)
    user_outdated_modules = get_outdated_or_missing_bundled_modules(user_modules_root)

    return ModuleFreshnessCheckResult(
        project_outdated=bool(project_outdated_modules),
        user_outdated=bool(user_outdated_modules),
        project_outdated_modules=project_outdated_modules,
        user_outdated_modules=user_outdated_modules,
        project_modules_root=project_modules_root,
        user_modules_root=user_modules_root,
    )


def _print_template_outdated_panel(template_result: TemplateCheckResult) -> None:
    details: list[str] = []
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
            f"Run [bold]specfact init ide --force[/bold] to update them.",
            border_style="yellow",
        )
    )


def _print_version_update_panel(version_result: VersionCheckResult) -> None:
    if not (version_result.update_available and version_result.latest_version and version_result.update_type):
        return
    update_type_color = "red" if version_result.update_type == "major" else "yellow"
    update_type_icon = "🔴" if version_result.update_type == "major" else "🟡"
    update_message = (
        f"[bold {update_type_color}]{update_type_icon} {version_result.update_type.upper()} Update Available[/bold {update_type_color}]\n\n"
        f"Current: [cyan]{version_result.current_version}[/cyan]\n"
        f"Latest: [green]{version_result.latest_version}[/green]\n\n"
    )
    if version_result.update_type == "major":
        update_message += (
            "[bold red]⚠ Breaking changes may be present![/bold red]\nReview release notes before upgrading.\n\n"
        )
    update_message += "Upgrade with: [bold]specfact upgrade[/bold] or [bold]pip install --upgrade specfact-cli[/bold]"
    console.print()
    console.print(Panel(update_message, border_style=update_type_color))


def _print_module_freshness_panel(module_result: ModuleFreshnessCheckResult) -> None:
    if not (module_result.project_outdated or module_result.user_outdated):
        return
    guidance: list[str] = []
    if module_result.project_outdated:
        guidance.append(
            f"- Project scope ({module_result.project_modules_root}): [bold]specfact module init --scope project[/bold]"
        )
    if module_result.user_outdated:
        guidance.append(f"- User scope ({module_result.user_modules_root}): [bold]specfact module init[/bold]")
    guidance_text = "\n".join(guidance)
    console.print()
    console.print(
        Panel(
            "[bold yellow]⚠ Bundled Modules Need Refresh[/bold yellow]\n\n"
            "Some bundled modules are missing or outdated.\n\n"
            f"{guidance_text}",
            border_style="yellow",
        )
    )


def _startup_progress_task(progress: Progress, show_progress: bool, label: str):
    return progress.add_task(label, total=None) if show_progress else None


def _run_startup_templates_segment(progress: Progress, repo_path: Path, show_progress: bool) -> bool:
    """Return True when installable prompt sources existed so drift could be evaluated."""
    task = _startup_progress_task(progress, show_progress, "[cyan]Checking IDE templates...[/cyan]")
    template_result = check_ide_templates(repo_path)
    if task:
        progress.update(task, description="[green]✓[/green] Checked IDE templates")
    if template_result is None:
        return False
    if not template_result.sources_available:
        return False
    if template_result.templates_outdated:
        _print_template_outdated_panel(template_result)
    return True


def _run_startup_version_segment(progress: Progress, show_progress: bool) -> None:
    task = _startup_progress_task(progress, show_progress, "[cyan]Checking for updates...[/cyan]")
    version_result = check_pypi_version()
    if task:
        progress.update(task, description="[green]✓[/green] Checked for updates")
    _print_version_update_panel(version_result)


def _run_startup_modules_segment(progress: Progress, repo_path: Path, show_progress: bool) -> None:
    task = _startup_progress_task(progress, show_progress, "[cyan]Checking bundled modules...[/cyan]")
    module_result = check_module_freshness(repo_path)
    if task:
        progress.update(task, description="[green]✓[/green] Checked bundled modules")
    if module_result:
        _print_module_freshness_panel(module_result)


def _run_startup_progress_block(
    repo_path: Path,
    show_progress: bool,
    should_check_templates: bool,
    should_check_version: bool,
    should_check_modules: bool,
) -> bool | None:
    """Return whether template drift had sources (None if the template segment did not run)."""
    template_sources_available: bool | None = None
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        if should_check_templates:
            template_sources_available = _run_startup_templates_segment(progress, repo_path, show_progress)
        if should_check_version:
            _run_startup_version_segment(progress, show_progress)
        if should_check_modules:
            _run_startup_modules_segment(progress, repo_path, show_progress)
    return template_sources_available


def _flush_startup_metadata(
    should_check_templates: bool,
    should_check_version: bool,
    should_check_modules: bool,
    template_sources_available: bool | None = None,
) -> None:
    from datetime import datetime

    metadata_updates: dict[str, Any] = {}
    if (should_check_templates and template_sources_available is True) or should_check_version:
        metadata_updates["last_checked_version"] = __version__
    if should_check_version:
        metadata_updates["last_version_check_timestamp"] = datetime.now(UTC).isoformat()
    if should_check_modules:
        metadata_updates["last_module_freshness_check_timestamp"] = datetime.now(UTC).isoformat()
    if metadata_updates:
        update_metadata(**metadata_updates)


@beartype
@require(optional_repo_path_exists, "repo_path must exist if provided")
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
    # Check modules on version change and otherwise at most once per 24 hours.
    last_module_freshness_check_timestamp = get_last_module_freshness_check_timestamp()
    should_check_modules = should_check_templates or is_version_check_needed(last_module_freshness_check_timestamp)

    template_sources_available: bool | None = None
    if should_check_templates or should_check_version or should_check_modules:
        template_sources_available = _run_startup_progress_block(
            repo_path,
            show_progress,
            should_check_templates,
            should_check_version,
            should_check_modules,
        )
    _flush_startup_metadata(
        should_check_templates,
        should_check_version,
        should_check_modules,
        template_sources_available,
    )

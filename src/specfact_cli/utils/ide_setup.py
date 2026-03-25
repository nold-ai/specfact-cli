"""
IDE Setup Utilities - Detect IDE and copy prompt templates to IDE-specific locations.

This module provides utilities for detecting IDE type, processing prompt templates,
and copying them to IDE-specific locations for slash command integration.
"""

from __future__ import annotations

import os
import re
import shutil
import site
import sys
from pathlib import Path
from typing import Any, Literal, cast

import yaml
from beartype import beartype
from icontract import ensure, require
from rich.console import Console

from specfact_cli.utils.contract_predicates import (
    repo_path_exists,
    repo_path_is_dir,
    template_path_exists,
    template_path_is_file,
    vscode_settings_result_ok,
)


console = Console()

# IDE configuration map (from Spec-Kit)
IDE_CONFIG: dict[str, dict[str, str | bool | None]] = {
    "claude": {
        "name": "Claude Code",
        "folder": ".claude/commands/",
        "format": "md",
        "settings_file": None,
    },
    "copilot": {
        "name": "GitHub Copilot",
        "folder": ".github/prompts/",
        "format": "prompt.md",
        "settings_file": ".vscode/settings.json",
    },
    "vscode": {
        "name": "VS Code",
        "folder": ".github/prompts/",
        "format": "prompt.md",
        "settings_file": ".vscode/settings.json",
    },
    "cursor": {
        "name": "Cursor",
        "folder": ".cursor/commands/",
        "format": "md",
        "settings_file": None,
    },
    "gemini": {
        "name": "Gemini CLI",
        "folder": ".gemini/commands/",
        "format": "toml",
        "settings_file": None,
    },
    "qwen": {
        "name": "Qwen Code",
        "folder": ".qwen/commands/",
        "format": "toml",
        "settings_file": None,
    },
    "opencode": {
        "name": "opencode",
        "folder": ".opencode/command/",
        "format": "md",
        "settings_file": None,
    },
    "windsurf": {
        "name": "Windsurf",
        "folder": ".windsurf/workflows/",
        "format": "md",
        "settings_file": None,
    },
    "kilocode": {
        "name": "Kilo Code",
        "folder": ".kilocode/workflows/",
        "format": "md",
        "settings_file": None,
    },
    "auggie": {
        "name": "Auggie CLI",
        "folder": ".augment/commands/",
        "format": "md",
        "settings_file": None,
    },
    "roo": {
        "name": "Roo Code",
        "folder": ".roo/commands/",
        "format": "md",
        "settings_file": None,
    },
    "codebuddy": {
        "name": "CodeBuddy",
        "folder": ".codebuddy/commands/",
        "format": "md",
        "settings_file": None,
    },
    "amp": {
        "name": "Amp",
        "folder": ".agents/commands/",
        "format": "md",
        "settings_file": None,
    },
    "q": {
        "name": "Amazon Q Developer",
        "folder": ".amazonq/prompts/",
        "format": "md",
        "settings_file": None,
    },
}

# Canonical id for bundled `specfact_cli` prompt templates (not a module-package name).
PROMPT_SOURCE_CORE = "core"

# Written by ``init ide`` so ``specfact init`` audit matches selective exports (``--prompts``).
IDE_PROMPT_EXPORT_STATE_FILE = "ide-prompt-export.yaml"

# Commands available in SpecFact
# Workflow-ordered commands (Phase 3)
SPECFACT_COMMANDS = [
    "specfact.01-import",
    "specfact.02-plan",
    "specfact.03-review",
    "specfact.04-sdd",
    "specfact.05-enforce",
    "specfact.06-sync",
    "specfact.07-contracts",
    "specfact.compare",
    "specfact.validate",
]


def _iter_prompt_template_files(templates_dir: Path) -> list[Path]:
    """Return prompt template files from a single directory in stable order."""
    if not templates_dir.exists() or not templates_dir.is_dir():
        return []
    return sorted(path for path in templates_dir.glob("specfact*.md") if path.is_file())


def _module_discovery_roots(repo_path: Path | None) -> list[tuple[Path, str]]:
    """Return module roots to inspect across builtin, repo-local, and configured locations."""
    from specfact_cli.registry.module_discovery import MARKETPLACE_MODULES_ROOT, USER_MODULES_ROOT
    from specfact_cli.registry.module_packages import get_modules_root, get_workspace_modules_root

    discovery_roots: list[tuple[Path, str]] = []

    def _add_discovery_root(path: Path | None, source: str) -> None:
        if path is None:
            return
        resolved = path.resolve()
        if any(existing_root.resolve() == resolved for existing_root, _source in discovery_roots):
            return
        discovery_roots.append((path, source))

    _add_discovery_root(get_modules_root(), "builtin")
    if repo_path is not None:
        _add_discovery_root((repo_path / ".specfact" / "modules").resolve(), "project")
    _add_discovery_root(get_workspace_modules_root(repo_path), "project")
    _add_discovery_root(USER_MODULES_ROOT, "user")
    _add_discovery_root(MARKETPLACE_MODULES_ROOT, "marketplace")

    extra_roots = os.environ.get("SPECFACT_MODULES_ROOTS", "")
    for raw_root in extra_roots.split(os.pathsep):
        candidate = raw_root.strip()
        if not candidate:
            continue
        candidate_path = Path(candidate).expanduser()
        if candidate_path.exists():
            _add_discovery_root(candidate_path, "custom")

    return discovery_roots


def _core_prompt_template_paths(repo_path: Path, include_package_fallback: bool) -> list[Path]:
    repo_prompts = (repo_path / "resources" / "prompts").resolve()
    if repo_prompts.is_dir():
        found = _iter_prompt_template_files(repo_prompts)
        if found:
            return found
    if not include_package_fallback:
        return []
    pkg_dir = find_package_resources_path("specfact_cli", "resources/prompts")
    if pkg_dir is not None and pkg_dir.is_dir():
        return _iter_prompt_template_files(pkg_dir)
    return []


def _module_prompt_sources_catalog(repo_path: Path) -> dict[str, list[Path]]:
    from specfact_cli.registry.module_packages import CORE_MODULE_ORDER, discover_package_metadata

    catalog: dict[str, list[Path]] = {}
    for modules_root, source in _module_discovery_roots(repo_path):
        if not modules_root.exists() or not modules_root.is_dir():
            continue
        for package_dir, metadata in discover_package_metadata(modules_root, source=source):
            if metadata.name in CORE_MODULE_ORDER:
                continue
            prompt_dir = (package_dir / "resources" / "prompts").resolve()
            if not prompt_dir.is_dir():
                continue
            files = _iter_prompt_template_files(prompt_dir)
            if not files:
                continue
            module_id = str(metadata.name)
            if module_id in catalog or module_id == PROMPT_SOURCE_CORE:
                continue
            catalog[module_id] = list(files)
    return catalog


@beartype
@require(lambda source_id: isinstance(source_id, str) and source_id.strip() != "", "source_id must be non-empty")
@ensure(lambda result: isinstance(result, str) and len(result) > 0, "segment must be non-empty")
def source_id_to_path_segment(source_id: str) -> str:
    """Map a prompt source id to a single directory segment under the IDE export folder."""
    cleaned = source_id.strip().replace("/", "__").replace("\\", "__")
    if not cleaned or cleaned in {".", ".."}:
        return "unknown"
    return cleaned


@beartype
@require(repo_path_exists, "Repo path must exist")
@require(repo_path_is_dir, "Repo path must be a directory")
@ensure(
    lambda result: (
        isinstance(result, dict)
        and all(isinstance(k, str) for k in result)
        and all(isinstance(v, list) and all(isinstance(p, Path) for p in v) for v in result.values())
    ),
    "Catalog must map str source ids to lists of Paths",
)
def discover_prompt_sources_catalog(
    repo_path: Path,
    include_package_fallback: bool = True,
) -> dict[str, list[Path]]:
    """
    Build prompt templates grouped by owning source: ``core`` or a module id (``module-package.yaml`` name).

    Core templates come from the repo checkout or the installed ``specfact_cli`` package. Module templates
    are discovered from effective module roots (builtin, project, user, marketplace, custom).
    """
    catalog: dict[str, list[Path]] = {}
    core_files = _core_prompt_template_paths(repo_path, include_package_fallback)
    if core_files:
        catalog[PROMPT_SOURCE_CORE] = list(core_files)
    catalog.update(_module_prompt_sources_catalog(repo_path))
    return catalog


def _matches_requested_categories(
    resolved_package_dir: Path,
    candidate: Path,
    metadata: Any | None,
    requested_categories: set[str] | None,
) -> bool:
    """Return whether the package should be considered for the requested categories."""
    if requested_categories is None:
        return True
    if metadata is not None:
        return (metadata.category or "").lower() in requested_categories
    candidate_hint = f"{resolved_package_dir.name} {candidate}".lower()
    return any(category in candidate_hint for category in requested_categories)


def _discover_resource_dirs_from_root(
    modules_root: Path,
    source: str,
    resource_subpath: str,
    requested_categories: set[str] | None,
    seen: set[Path],
) -> list[Path]:
    """Discover module resource directories beneath a single module root."""
    from specfact_cli.registry.module_packages import discover_package_metadata

    if not modules_root.exists() or not modules_root.is_dir():
        return []

    parsed_metadata = {
        package_dir.resolve(): metadata
        for package_dir, metadata in discover_package_metadata(modules_root, source=source)
    }
    discovered_dirs: list[Path] = []
    for package_dir in sorted(path for path in modules_root.iterdir() if path.is_dir()):
        resolved_package_dir = package_dir.resolve()
        metadata = parsed_metadata.get(resolved_package_dir)
        resource_root = _package_resource_dir(
            resolved_package_dir, metadata, resource_subpath, requested_categories, seen
        )
        if resource_root is None:
            continue

        seen.add(resource_root)
        discovered_dirs.append(resource_root)

    return discovered_dirs


def _package_resource_dir(
    resolved_package_dir: Path,
    metadata: Any | None,
    resource_subpath: str,
    requested_categories: set[str] | None,
    seen: set[Path],
) -> Path | None:
    """Return the package resource root when the package should contribute the requested resource."""
    from specfact_cli.registry.module_packages import CORE_MODULE_ORDER

    if metadata is not None and metadata.name in CORE_MODULE_ORDER:
        return None

    resource_root = (resolved_package_dir / "resources").resolve()
    candidate = (resolved_package_dir / resource_subpath).resolve()
    if not resource_root.exists() or not candidate.exists() or resource_root in seen:
        return None
    if not _matches_requested_categories(resolved_package_dir, candidate, metadata, requested_categories):
        return None
    return resource_root


@beartype
@ensure(
    lambda result: isinstance(result, list) and all(isinstance(path, Path) and path.exists() for path in result),
    "Must return existing resource directories",
)
def _discover_module_resource_dirs(
    resource_subpath: str, repo_path: Path | None = None, categories: set[str] | None = None
) -> list[Path]:
    """Discover installed module resource roots that contain the requested subpath."""
    requested_categories = {category.lower() for category in categories} if categories else None
    seen: set[Path] = set()
    discovered_dirs: list[Path] = []
    for modules_root, source in _module_discovery_roots(repo_path):
        discovered_dirs.extend(
            _discover_resource_dirs_from_root(modules_root, source, resource_subpath, requested_categories, seen)
        )
    return discovered_dirs


@beartype
@ensure(
    lambda result: isinstance(result, list) and all(isinstance(path, Path) for path in result),
    "Must return list of Paths",
)
def discover_prompt_template_files(repo_path: Path, include_package_fallback: bool = True) -> list[Path]:
    """Return prompt templates from installed modules, then repo resources, then optional package fallback."""
    catalog = discover_prompt_sources_catalog(repo_path, include_package_fallback=include_package_fallback)
    merged: list[Path] = []
    seen_names: set[str] = set()
    ordered_keys = [PROMPT_SOURCE_CORE, *sorted(k for k in catalog if k != PROMPT_SOURCE_CORE)]
    for key in ordered_keys:
        if key not in catalog:
            continue
        for prompt_file in catalog[key]:
            if prompt_file.name in seen_names:
                continue
            seen_names.add(prompt_file.name)
            merged.append(prompt_file)
    return merged


def _output_filename_for_template(template_path: Path, format_type: str) -> str:
    """Map source markdown templates to IDE-specific filenames."""
    if format_type == "prompt.md":
        return f"{template_path.stem}.prompt.md"
    if format_type == "toml":
        return f"{template_path.stem}.toml"
    return template_path.name


def _safe_resolved_segment_dir(repo_path: Path, ide: str, segment: str) -> Path | None:
    """Return ``repo_path / ide_folder / segment`` resolved, or ``None`` if it escapes the IDE export root."""
    config = IDE_CONFIG[ide]
    base = (repo_path / str(config["folder"])).resolve()
    segment_dir = (base / segment).resolve()
    try:
        segment_dir.relative_to(base)
    except ValueError:
        return None
    return segment_dir


def _prune_segment_exports_not_in_expected(
    repo_path: Path,
    ide: str,
    segment: str,
    template_paths: list[Path],
) -> None:
    """Remove files under ``ide_folder/segment`` that are not part of this export (same filenames as copy)."""
    if not template_paths:
        return
    config = IDE_CONFIG[ide]
    format_type = str(config["format"])
    segment_dir = _safe_resolved_segment_dir(repo_path, ide, segment)
    if segment_dir is None or not segment_dir.is_dir():
        return
    expected_resolved: set[Path] = {
        (segment_dir / _output_filename_for_template(tp, format_type)).resolve() for tp in template_paths
    }
    for p in list(segment_dir.iterdir()):
        if not p.is_file():
            continue
        if p.resolve() not in expected_resolved:
            try:
                p.unlink()
                console.print(f"[dim]Removed stale prompt export:[/dim] {p}")
            except OSError as exc:
                console.print(f"[yellow]Could not remove stale export {p}:[/yellow] {exc}")


def _remove_unselected_prompt_export_segments(
    repo_path: Path,
    ide: str,
    prompts_by_source: dict[str, list[Path]],
) -> None:
    """Remove on-disk segment directories under the IDE export root that are not in this selective export."""
    config = IDE_CONFIG[ide]
    base = (repo_path / str(config["folder"])).resolve()
    selected_segments = {source_id_to_path_segment(sid) for sid in prompts_by_source}
    if not base.is_dir():
        return
    for child in list(base.iterdir()):
        if not child.is_dir():
            continue
        try:
            child.resolve().relative_to(base)
        except ValueError:
            continue
        if child.name in selected_segments:
            continue
        try:
            shutil.rmtree(child)
            console.print(f"[dim]Removed unselected export segment:[/dim] {child}")
        except OSError as exc:
            console.print(f"[yellow]Could not remove segment {child}:[/yellow] {exc}")


def _copy_template_files_to_ide(
    repo_path: Path,
    ide: str,
    template_files: list[Path],
    force: bool = False,
    *,
    source_segment: str | None = None,
    write_settings: bool = True,
) -> tuple[list[Path], Path | None]:
    """Copy a concrete list of prompt template files to the IDE target location."""
    config = IDE_CONFIG[ide]
    ide_folder = str(config["folder"])
    format_type = str(config["format"])
    settings_file = config.get("settings_file")
    if settings_file is not None and not isinstance(settings_file, str):
        settings_file = None

    ide_dir = repo_path / ide_folder
    if source_segment is not None:
        ide_dir = ide_dir / source_segment
    ide_dir.mkdir(parents=True, exist_ok=True)

    copied_files: list[Path] = []

    for template_path in template_files:
        template_data = read_template(template_path)
        processed_content = process_template(template_data["content"], template_data["description"], format_type)  # type: ignore[arg-type]
        output_path = ide_dir / _output_filename_for_template(template_path, format_type)

        if output_path.exists() and not force:
            console.print(f"[yellow]Skipping:[/yellow] {output_path} (already exists, use --force to overwrite)")
            continue

        output_path.write_text(processed_content, encoding="utf-8")
        copied_files.append(output_path)
        console.print(f"[green]Copied:[/green] {output_path}")

    settings_path = None
    if write_settings and settings_file and isinstance(settings_file, str):
        settings_path = create_vscode_settings(repo_path, settings_file)

    return copied_files, settings_path


@beartype
@require(repo_path_exists, "Repo path must exist")
@require(repo_path_is_dir, "Repo path must be a directory")
@require(lambda ide: ide in IDE_CONFIG, "IDE must be valid")
@require(
    lambda prompt_source_ids: (
        prompt_source_ids is None
        or (isinstance(prompt_source_ids, frozenset) and all(isinstance(x, str) for x in prompt_source_ids))
    ),
    "prompt_source_ids must be None or frozenset[str]",
)
@ensure(lambda result: isinstance(result, list) and all(isinstance(p, Path) for p in result), "Must return Paths")
def expected_ide_prompt_export_paths(
    repo_path: Path,
    ide: str,
    *,
    prompt_source_ids: frozenset[str] | None = None,
) -> list[Path]:
    """Return expected on-disk paths for exported IDE prompts (source-namespaced layout).

    If ``prompt_source_ids`` is set (from ``.specfact/ide-prompt-export.yaml``), only those sources are
    expected—matching a selective ``init ide --prompts`` run. Otherwise the full discovered catalog is used.
    """
    config = IDE_CONFIG[ide]
    format_type = str(config["format"])
    base = repo_path / str(config["folder"])
    catalog = discover_prompt_sources_catalog(repo_path)
    if prompt_source_ids is not None:
        catalog = {k: v for k, v in catalog.items() if k in prompt_source_ids}
    paths: list[Path] = []
    for sid, templates in sorted(catalog.items(), key=lambda item: (item[0] != PROMPT_SOURCE_CORE, item[0])):
        segment = source_id_to_path_segment(sid)
        for template_path in templates:
            paths.append(base / segment / _output_filename_for_template(template_path, format_type))
    return paths


@beartype
@require(repo_path_exists, "Repo path must exist")
@require(repo_path_is_dir, "Repo path must be a directory")
@require(lambda ide: ide in IDE_CONFIG, "IDE must be valid")
@require(
    lambda prompt_source_ids: (
        prompt_source_ids is None
        or (isinstance(prompt_source_ids, frozenset) and all(isinstance(x, str) for x in prompt_source_ids))
    ),
    "prompt_source_ids must be None or frozenset[str]",
)
@ensure(lambda result: isinstance(result, int) and result >= 0, "Count must be non-negative")
def count_outdated_ide_prompt_exports(
    repo_path: Path,
    ide: str,
    *,
    prompt_source_ids: frozenset[str] | None = None,
) -> int:
    """Count exported IDE prompt files that are older than their source templates."""
    config = IDE_CONFIG[ide]
    format_type = str(config["format"])
    base = repo_path / str(config["folder"])
    catalog = discover_prompt_sources_catalog(repo_path)
    if prompt_source_ids is not None:
        catalog = {k: v for k, v in catalog.items() if k in prompt_source_ids}
    outdated = 0
    for sid, paths in catalog.items():
        segment = source_id_to_path_segment(sid)
        for src in paths:
            dest = base / segment / _output_filename_for_template(src, format_type)
            if src.exists() and dest.exists() and dest.stat().st_mtime < src.stat().st_mtime:
                outdated += 1
    return outdated


@beartype
@require(repo_path_exists, "Repo path must exist")
@require(repo_path_is_dir, "Repo path must be a directory")
@require(lambda ide: ide in IDE_CONFIG, "IDE must be valid")
@require(lambda prompts_by_source: isinstance(prompts_by_source, dict), "prompts_by_source must be a dict")
@ensure(
    lambda result: (
        isinstance(result, tuple)
        and len(result) == 2
        and isinstance(result[0], list)
        and (result[1] is None or isinstance(result[1], Path))
    ),
    "Must return copied paths and optional settings path",
)
def copy_prompts_by_source_to_ide(
    repo_path: Path,
    ide: str,
    prompts_by_source: dict[str, list[Path]],
    force: bool = False,
) -> tuple[list[Path], Path | None]:
    """Copy prompts grouped by source id into source-namespaced subfolders under the IDE export directory."""
    all_copied: list[Path] = []
    _remove_unselected_prompt_export_segments(repo_path, ide, prompts_by_source)
    ordered = sorted(
        prompts_by_source.items(),
        key=lambda item: (item[0] != PROMPT_SOURCE_CORE, item[0]),
    )
    for source_id, paths in ordered:
        if not paths:
            continue
        segment = source_id_to_path_segment(source_id)
        _prune_segment_exports_not_in_expected(repo_path, ide, segment, paths)
        copied, _settings = _copy_template_files_to_ide(
            repo_path, ide, paths, force, source_segment=segment, write_settings=False
        )
        all_copied.extend(copied)

    settings_path: Path | None = None
    config = IDE_CONFIG[ide]
    settings_file = config.get("settings_file")
    if settings_file and isinstance(settings_file, str):
        settings_path = create_vscode_settings(repo_path, settings_file, prompts_by_source=prompts_by_source)

    return all_copied, settings_path


@beartype
@require(lambda ide: ide in IDE_CONFIG or ide == "auto", "IDE must be valid or 'auto'")
def detect_ide(ide: str = "auto") -> str:
    """
    Detect IDE type from environment or use provided value.

    Args:
        ide: IDE identifier or "auto" for auto-detection

    Returns:
        IDE identifier (e.g., "cursor", "vscode", "copilot")

    Examples:
        >>> detect_ide("cursor")
        'cursor'
        >>> detect_ide("auto")  # Auto-detect from environment
        'vscode'
    """
    if ide != "auto":
        return ide

    # Auto-detect from environment variables
    # Check Cursor FIRST (before VS Code) since Cursor sets VSCODE_* variables too
    # Cursor-specific variables take priority
    # Cursor sets: CURSOR_AGENT, CURSOR_TRACE_ID, CURSOR_PID, CURSOR_INJECTION, CHROME_DESKTOP=cursor.desktop
    if (
        os.environ.get("CURSOR_AGENT")
        or os.environ.get("CURSOR_TRACE_ID")
        or os.environ.get("CURSOR_PID")
        or os.environ.get("CURSOR_INJECTION")
        or os.environ.get("CHROME_DESKTOP") == "cursor.desktop"
    ):
        return "cursor"
    # VS Code / Copilot
    if os.environ.get("VSCODE_PID") or os.environ.get("VSCODE_INJECTION"):
        return "vscode"
    # Claude Code
    if os.environ.get("CLAUDE_PID"):
        return "claude"
    # Default to VS Code if no detection
    return "vscode"


@beartype
@require(template_path_exists, "Template path must exist")
@require(template_path_is_file, "Template path must be a file")
@ensure(
    lambda result: isinstance(result, dict) and "description" in result and "content" in result,
    "Result must be dict with description and content",
)
def read_template(template_path: Path) -> dict[str, str]:
    """
    Read prompt template and extract YAML frontmatter and content.

    Args:
        template_path: Path to template file (.md)

    Returns:
        Dict with "description" (from frontmatter) and "content" (markdown body)

    Examples:
        >>> template = read_template(Path("resources/prompts/specfact.01-import.md"))
        >>> "description" in template
        True
        >>> "content" in template
        True
    """
    content = template_path.read_text(encoding="utf-8")

    # Extract YAML frontmatter
    frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
    if frontmatter_match:
        frontmatter_str = frontmatter_match.group(1)
        body = frontmatter_match.group(2)
        frontmatter_raw = yaml.safe_load(frontmatter_str) or {}
        frontmatter: dict[str, Any] = frontmatter_raw if isinstance(frontmatter_raw, dict) else {}
        description = str(frontmatter.get("description", ""))
    else:
        # No frontmatter, use entire content as body
        description = ""
        body = content

    return {"description": description, "content": body}


@beartype
@require(lambda content: isinstance(content, str), "Content must be string")
@require(lambda format_type: format_type in ("md", "toml", "prompt.md"), "Format must be md, toml, or prompt.md")
def process_template(content: str, description: str, format_type: Literal["md", "toml", "prompt.md"]) -> str:
    """
    Process template content for specific IDE format.

    Args:
        content: Template markdown content
        description: Template description (from frontmatter)
        format_type: Target format (md, toml, or prompt.md)

    Returns:
        Processed template content for target format

    Examples:
        >>> process_template("# Title\n$ARGUMENTS", "Test", "md")
        '# Title\n$ARGUMENTS'
        >>> result = process_template("# Title\n$ARGUMENTS", "Test", "toml")
        >>> "description" in result and "prompt" in result
        True
    """
    # Replace placeholders based on format
    if format_type == "toml":
        # TOML format: Replace $ARGUMENTS with {{args}}, escape backslashes
        processed = content.replace("$ARGUMENTS", "{{args}}")
        processed = processed.replace("\\", "\\\\")
        # Wrap in TOML structure
        return f'description = "{description}"\n\nprompt = """\n{processed}\n"""'
    if format_type == "prompt.md":
        # VS Code/Copilot format: Keep $ARGUMENTS, add .prompt.md extension
        return content
    # Markdown format: Keep $ARGUMENTS as-is
    return content


@beartype
@require(repo_path_exists, "Repo path must exist")
@require(repo_path_is_dir, "Repo path must be a directory")
@require(lambda ide: ide in IDE_CONFIG, "IDE must be valid")
@ensure(
    lambda result: (
        isinstance(result, tuple)
        and len(result) == 2
        and (result[1] is None or (isinstance(result[1], Path) and result[1].exists()))
    ),
    "Settings file path must exist if returned",
)
def copy_templates_to_ide(
    repo_path: Path, ide: str, templates_dir: Path, force: bool = False
) -> tuple[list[Path], Path | None]:
    """
    Copy prompt templates to IDE-specific locations.

    Args:
        repo_path: Repository root path
        ide: IDE identifier
        templates_dir: Directory containing prompt templates
        force: Overwrite existing files

    Returns:
        Tuple of (copied_file_paths, settings_file_path or None)

    Examples:
        >>> copied, settings = copy_templates_to_ide(Path("."), "cursor", Path("resources/prompts"))
        >>> len(copied) > 0
        True
    """
    return _copy_template_files_to_ide(repo_path, ide, _iter_prompt_template_files(templates_dir), force)


def _vscode_prompt_recommendation_paths_from_sources(prompts_by_source: dict[str, list[Path]]) -> list[str]:
    """Build `.github/prompts/...` recommendation strings matching namespaced IDE export layout."""
    prompt_files: list[str] = []
    for source_id, paths in sorted(
        prompts_by_source.items(),
        key=lambda item: (item[0] != PROMPT_SOURCE_CORE, item[0]),
    ):
        segment = source_id_to_path_segment(source_id)
        for template_path in paths:
            prompt_files.append(f".github/prompts/{segment}/{template_path.stem}.prompt.md")
    return prompt_files


def _vscode_prompt_paths_from_full_catalog(repo_path: Path) -> list[str]:
    """Recommendation paths for the full discovered prompt catalog (namespaced segments)."""
    catalog = discover_prompt_sources_catalog(repo_path)
    out: list[str] = []
    for source_id, paths in sorted(catalog.items(), key=lambda item: (item[0] != PROMPT_SOURCE_CORE, item[0])):
        segment = source_id_to_path_segment(source_id)
        for template_path in paths:
            out.append(f".github/prompts/{segment}/{template_path.stem}.prompt.md")
    return out


def _finalize_vscode_prompt_recommendation_paths(repo_path: Path, prompt_files: list[str]) -> list[str]:
    """Fall back to flat discovery or command list when namespaced paths are empty."""
    if not prompt_files:
        discovered_flat = discover_prompt_template_files(repo_path)
        prompt_files = [f".github/prompts/{template_path.stem}.prompt.md" for template_path in discovered_flat]
    if not prompt_files:
        return [f".github/prompts/{cmd}.prompt.md" for cmd in SPECFACT_COMMANDS]
    return prompt_files


def _is_specfact_github_prompt_path(path: str) -> bool:
    """True for SpecFact-managed GitHub prompt recommendations (strip on selective export); keeps team paths."""
    normalized = path.replace("\\", "/").lstrip("./")
    if not normalized.startswith("github/prompts/"):
        return False
    name = Path(normalized).name
    return name.startswith("specfact") and name.endswith(".prompt.md")


def _strip_specfact_github_prompt_recommendations(paths: list[str]) -> list[str]:
    """Remove prior SpecFact-managed ``.github/prompts/`` entries before merging a selective export; keep other paths."""
    return [p for p in paths if not _is_specfact_github_prompt_path(p)]


@beartype
@require(repo_path_exists, "Repo path must exist")
@require(repo_path_is_dir, "Repo path must be a directory")
@require(lambda ide: isinstance(ide, str) and len(ide) > 0, "ide must be non-empty")
@require(lambda source_ids: isinstance(source_ids, list) and all(isinstance(s, str) for s in source_ids), "bad sources")
@ensure(lambda result: result is None, "Must return None")
def write_ide_prompt_export_state(repo_path: Path, ide: str, source_ids: list[str]) -> None:
    """Persist last ``init ide`` source selection for audit/outdated checks on ``specfact init``."""
    specfact_dir = repo_path / ".specfact"
    specfact_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "ide": ide,
        "prompt_sources": sorted(source_ids),
    }
    out = specfact_dir / IDE_PROMPT_EXPORT_STATE_FILE
    out.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=False), encoding="utf-8")


@beartype
@require(repo_path_exists, "Repo path must exist")
@require(repo_path_is_dir, "Repo path must be a directory")
@require(lambda ide: ide in IDE_CONFIG, "IDE must be valid")
@ensure(
    lambda result: result is None or (isinstance(result, frozenset) and all(isinstance(x, str) for x in result)),
    "Must return frozenset of str or None",
)
def load_ide_prompt_export_source_ids(repo_path: Path, ide: str) -> frozenset[str] | None:
    """Return source ids from last ``init ide`` export for this IDE, or ``None`` if unset or IDE mismatches."""
    path = repo_path / ".specfact" / IDE_PROMPT_EXPORT_STATE_FILE
    if not path.is_file():
        return None
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return None
        raw_dict: dict[str, Any] = cast(dict[str, Any], raw)
        stored_ide = raw_dict.get("ide")
        if stored_ide is None or str(stored_ide).strip() != ide:
            return None
        srcs = raw_dict.get("prompt_sources")
        if not isinstance(srcs, list) or not srcs:
            return None
        out = frozenset(str(s).strip() for s in srcs if str(s).strip())
        return out if out else None
    except (OSError, yaml.YAMLError, TypeError, ValueError):
        return None


@beartype
@require(repo_path_exists, "Repo path must exist")
@require(repo_path_is_dir, "Repo path must be a directory")
@require(
    lambda prompts_by_source: prompts_by_source is None or isinstance(prompts_by_source, dict),
    "prompts_by_source must be None or a dict",
)
@ensure(lambda result: vscode_settings_result_ok(result), "Settings file must exist if returned")
def create_vscode_settings(
    repo_path: Path,
    settings_file: str,
    *,
    prompts_by_source: dict[str, list[Path]] | None = None,
) -> Path | None:
    """
    Create or merge VS Code settings.json with prompt file recommendations.

    Args:
        repo_path: Repository root path
        settings_file: Settings file path (e.g., ".vscode/settings.json")
        prompts_by_source: When set (e.g. from ``copy_prompts_by_source_to_ide``), recommendations list only
            templates from that export; prior **SpecFact-managed** ``.github/prompts/`` entries (paths whose
            filename looks like ``specfact*.prompt.md``) are removed so selective ``--prompts`` runs do not
            leave stale exports; other ``.github/prompts/`` entries and paths outside that folder are preserved.
            When ``None``,
            recommendations follow the full discovered catalog (or legacy flat fallbacks).

    Returns:
        Path to settings file, or None if not VS Code/Copilot

    Examples:
        >>> settings = create_vscode_settings(Path("."), ".vscode/settings.json")
        >>> settings is not None
        True
    """
    import json

    settings_path = repo_path / settings_file
    settings_dir = settings_path.parent
    settings_dir.mkdir(parents=True, exist_ok=True)

    if prompts_by_source is not None:
        prompt_files = _finalize_vscode_prompt_recommendation_paths(
            repo_path, _vscode_prompt_recommendation_paths_from_sources(prompts_by_source)
        )
    else:
        prompt_files = _finalize_vscode_prompt_recommendation_paths(
            repo_path, _vscode_prompt_paths_from_full_catalog(repo_path)
        )

    # Load existing settings or create new
    if settings_path.exists():
        try:
            with open(settings_path, encoding="utf-8") as f:
                existing_settings = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            existing_settings = {}
    else:
        existing_settings = {}

    # Merge chat.promptFilesRecommendations
    if "chat" not in existing_settings:
        existing_settings["chat"] = {}

    chat_block = existing_settings["chat"]
    chat_dict: dict[str, Any] = cast(dict[str, Any], chat_block) if isinstance(chat_block, dict) else {}
    existing_recommendations = chat_dict.get("promptFilesRecommendations", [])
    if prompts_by_source is not None:
        existing_recommendations = _strip_specfact_github_prompt_recommendations(
            list(existing_recommendations) if isinstance(existing_recommendations, list) else [],
        )
    merged_recommendations = list(set(existing_recommendations + prompt_files))
    chat_dict["promptFilesRecommendations"] = merged_recommendations
    existing_settings["chat"] = chat_dict

    # Write merged settings
    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(existing_settings, f, indent=4)
        f.write("\n")

    # Ensure file exists before returning (satisfies contract)
    if not settings_path.exists():
        console.print(f"[yellow]Warning:[/yellow] Settings file not created: {settings_path}")
        return None

    console.print(f"[green]Updated:[/green] {settings_path}")
    return settings_path


def _package_path_in_site_packages(site_packages_dir: Path, package_name: str) -> Path | None:
    if not site_packages_dir.is_dir():
        return None
    pkg_path = site_packages_dir / package_name
    return pkg_path.resolve() if pkg_path.exists() else None


def _find_package_paths_under_archive(archive_dir: Path, package_name: str) -> list[Path]:
    out: list[Path] = []
    try:
        for site_packages_dir in archive_dir.rglob("site-packages"):
            resolved = _package_path_in_site_packages(site_packages_dir, package_name)
            if resolved is not None:
                out.append(resolved)
    except (FileNotFoundError, PermissionError, OSError):
        pass
    return out


def _search_uvx_cache_base(package_name: str, uvx_cache_base: Path) -> list[Path]:
    """
    Search a uvx archive-v0 cache directory for a package's site-packages location.

    Args:
        package_name: Package name to find
        uvx_cache_base: Path to the archive-v0 cache root

    Returns:
        List of found package Paths
    """
    found: list[Path] = []
    if not uvx_cache_base.exists():
        return found
    try:
        for archive_dir in uvx_cache_base.iterdir():
            try:
                if not archive_dir.is_dir():
                    continue
                if "typeshed" in archive_dir.name.lower() or "stubs" in archive_dir.name.lower():
                    continue
                found.extend(_find_package_paths_under_archive(archive_dir, package_name))
            except (FileNotFoundError, PermissionError, OSError):
                continue
    except (FileNotFoundError, PermissionError, OSError):
        pass
    return found


def _locations_from_importlib(package_name: str) -> list[Path]:
    """Find package location using importlib.util.find_spec."""
    try:
        import importlib.util

        spec = importlib.util.find_spec(package_name)
        if spec and spec.origin:
            return [Path(spec.origin).parent.resolve()]
    except Exception:
        pass
    return []


def _locations_from_site_packages(package_name: str) -> list[Path]:
    """Find package in user and system site-packages directories."""
    found: list[Path] = []
    try:
        user_site = site.getusersitepackages()
        if user_site:
            p = Path(user_site) / package_name
            if p.exists():
                found.append(p.resolve())
    except Exception:
        pass
    try:
        for site_path in site.getsitepackages():
            p = Path(site_path) / package_name
            if p.exists():
                found.append(p.resolve())
    except Exception:
        pass
    return found


def _locations_from_sys_path(package_name: str) -> list[Path]:
    """Find package by scanning sys.path entries."""
    found: list[Path] = []
    for path_str in sys.path:
        if not path_str:
            continue
        try:
            path = Path(path_str).resolve()
            if path.exists() and path.is_dir():
                p = path / package_name
                if p.exists():
                    found.append(p.resolve())
        except Exception:
            continue
    return found


def _locations_from_uvx_cache(package_name: str) -> list[Path]:
    """Find package in uvx archive cache (Linux/macOS and Windows)."""
    if sys.platform != "win32":
        cache_base = Path.home() / ".cache" / "uv" / "archive-v0"
    else:
        localappdata = os.environ.get("LOCALAPPDATA")
        if not localappdata:
            return []
        cache_base = Path(localappdata) / "uv" / "cache" / "archive-v0"
    return _search_uvx_cache_base(package_name, cache_base)


@beartype
@ensure(
    lambda result: isinstance(result, list) and all(isinstance(p, Path) for p in result), "Must return list of Paths"
)
def get_package_installation_locations(package_name: str) -> list[Path]:
    """
    Get all possible installation locations for a Python package across different OS and installation types.

    This function searches for package locations in:
    - User site-packages (per-user installations: ~/.local/lib/python3.X/site-packages)
    - System site-packages (global installations: /usr/lib/python3.X/site-packages, C:\\Python3X\\Lib\\site-packages)
    - Virtual environments (venv, conda, etc.)
    - uvx cache locations (~/.cache/uv/archive-v0/...)

    Args:
        package_name: Name of the package to locate (e.g., "specfact_cli")

    Returns:
        List of Path objects representing possible package installation locations

    Examples:
        >>> locations = get_package_installation_locations("specfact_cli")
        >>> len(locations) > 0
        True
    """
    locations: list[Path] = (
        _locations_from_importlib(package_name)
        + _locations_from_site_packages(package_name)
        + _locations_from_sys_path(package_name)
        + _locations_from_uvx_cache(package_name)
    )

    seen: set[str] = set()
    unique_locations: list[Path] = []
    for loc in locations:
        loc_str = str(loc)
        if loc_str not in seen:
            seen.add(loc_str)
            unique_locations.append(loc)
    return unique_locations


@beartype
@require(lambda package_name: isinstance(package_name, str) and len(package_name) > 0, "Package name must be non-empty")
@ensure(
    lambda result: result is None or (isinstance(result, Path) and result.exists()),
    "Result must be None or existing Path",
)
def find_package_resources_path(package_name: str, resource_subpath: str) -> Path | None:
    """
    Find the path to a resource within an installed package.

    Searches across all possible installation locations (user, system, venv, uvx cache)
    to find the package and then locates the resource subpath.

    Args:
        package_name: Name of the package (e.g., "specfact_cli")
        resource_subpath: Subpath within the package (e.g., "resources/prompts")

    Returns:
        Path to the resource directory if found, None otherwise

    Examples:
        >>> path = find_package_resources_path("specfact_cli", "resources/prompts")
        >>> path is None or path.exists()
        True
    """
    # Get all possible package installation locations
    package_locations = get_package_installation_locations(package_name)

    # Try each location
    for package_path in package_locations:
        resource_path = (package_path / resource_subpath).resolve()
        if resource_path.exists():
            return resource_path

    return None

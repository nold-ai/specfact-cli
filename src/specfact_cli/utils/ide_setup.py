"""
IDE Setup Utilities - Detect IDE and copy prompt templates to IDE-specific locations.

This module provides utilities for detecting IDE type, processing prompt templates,
and copying them to IDE-specific locations for slash command integration.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Literal

import yaml
from beartype import beartype
from icontract import ensure, require
from rich.console import Console


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

# Commands available in SpecFact
SPECFACT_COMMANDS = [
    "specfact-import-from-code",
    "specfact-plan-init",
    "specfact-plan-add-feature",
    "specfact-plan-add-story",
    "specfact-plan-update-idea",
    "specfact-plan-update-feature",
    "specfact-plan-select",
    "specfact-plan-promote",
    "specfact-plan-compare",
    "specfact-plan-review",
    "specfact-sync",
    "specfact-enforce",
    "specfact-repro",
]


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
@require(lambda template_path: template_path.exists(), "Template path must exist")
@require(lambda template_path: template_path.is_file(), "Template path must be a file")
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
        >>> template = read_template(Path("resources/prompts/specfact-import-from-code.md"))
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
        frontmatter = yaml.safe_load(frontmatter_str) or {}
        description = frontmatter.get("description", "")
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
@require(lambda repo_path: repo_path.exists(), "Repo path must exist")
@require(lambda repo_path: repo_path.is_dir(), "Repo path must be a directory")
@require(lambda ide: ide in IDE_CONFIG, "IDE must be valid")
@ensure(
    lambda result: isinstance(result, tuple)
    and len(result) == 2
    and (result[1] is None or (isinstance(result[1], Path) and result[1].exists())),
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
    config = IDE_CONFIG[ide]
    ide_folder = str(config["folder"])
    format_type = str(config["format"])
    settings_file = config.get("settings_file")
    if settings_file is not None and not isinstance(settings_file, str):
        settings_file = None

    # Create IDE directory
    ide_dir = repo_path / ide_folder
    ide_dir.mkdir(parents=True, exist_ok=True)

    copied_files = []

    # Copy each template
    for command in SPECFACT_COMMANDS:
        template_path = templates_dir / f"{command}.md"
        if not template_path.exists():
            console.print(f"[yellow]Warning:[/yellow] Template not found: {template_path}")
            continue

        # Read and process template
        template_data = read_template(template_path)
        processed_content = process_template(template_data["content"], template_data["description"], format_type)  # type: ignore[arg-type]

        # Determine output filename
        if format_type == "prompt.md":
            output_filename = f"{command}.prompt.md"
        elif format_type == "toml":
            output_filename = f"{command}.toml"
        else:
            output_filename = f"{command}.md"

        output_path = ide_dir / output_filename

        # Check if file exists
        if output_path.exists() and not force:
            console.print(f"[yellow]Skipping:[/yellow] {output_path} (already exists, use --force to overwrite)")
            continue

        # Write processed template
        output_path.write_text(processed_content, encoding="utf-8")
        copied_files.append(output_path)
        console.print(f"[green]Copied:[/green] {output_path}")

    # Handle VS Code settings if needed
    settings_path = None
    if settings_file and isinstance(settings_file, str):
        settings_path = create_vscode_settings(repo_path, settings_file)

    return (copied_files, settings_path)


@beartype
@require(lambda repo_path: repo_path.exists(), "Repo path must exist")
@require(lambda repo_path: repo_path.is_dir(), "Repo path must be a directory")
@ensure(lambda result: result is None or result.exists(), "Settings file must exist if returned")
def create_vscode_settings(repo_path: Path, settings_file: str) -> Path | None:
    """
    Create or merge VS Code settings.json with prompt file recommendations.

    Args:
        repo_path: Repository root path
        settings_file: Settings file path (e.g., ".vscode/settings.json")

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

    # Generate prompt file recommendations
    prompt_files = [f".github/prompts/{cmd}.prompt.md" for cmd in SPECFACT_COMMANDS]

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

    existing_recommendations = existing_settings["chat"].get("promptFilesRecommendations", [])
    merged_recommendations = list(set(existing_recommendations + prompt_files))
    existing_settings["chat"]["promptFilesRecommendations"] = merged_recommendations

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

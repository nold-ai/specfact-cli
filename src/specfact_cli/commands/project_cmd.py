"""
Project command - Persona workflows and bundle management.

This module provides commands for persona-based editing, lock enforcement,
and merge conflict resolution for project bundles.
"""

from __future__ import annotations

import fnmatch
import os
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import typer
from beartype import beartype
from icontract import ensure, require
from rich.console import Console
from rich.table import Table

from specfact_cli.models.project import (
    BundleManifest,
    PersonaMapping,
    ProjectBundle,
    ProjectMetadata,
    SectionLock,
)
from specfact_cli.runtime import debug_log_operation, debug_print, is_debug_mode
from specfact_cli.utils import print_error, print_info, print_section, print_success, print_warning
from specfact_cli.utils.progress import load_bundle_with_progress, save_bundle_with_progress
from specfact_cli.utils.structure import SpecFactStructure
from specfact_cli.versioning import ChangeAnalyzer, bump_version, validate_semver


app = typer.Typer(help="Manage project bundles with persona workflows")
version_app = typer.Typer(help="Manage project bundle versions")
app.add_typer(version_app, name="version")
console = Console()


# Use shared progress utilities for consistency (aliased to maintain existing function names)
def _load_bundle_with_progress(bundle_dir: Path, validate_hashes: bool = False) -> ProjectBundle:
    """Load project bundle with unified progress display."""
    return load_bundle_with_progress(bundle_dir, validate_hashes=validate_hashes, console_instance=console)


def _save_bundle_with_progress(bundle: ProjectBundle, bundle_dir: Path, atomic: bool = True) -> None:
    """Save project bundle with unified progress display."""
    save_bundle_with_progress(bundle, bundle_dir, atomic=atomic, console_instance=console)


# Default persona mappings
DEFAULT_PERSONAS: dict[str, PersonaMapping] = {
    "product-owner": PersonaMapping(
        owns=["idea", "business", "features.*.stories", "features.*.outcomes"],
        exports_to="specs/*/spec.md",
    ),
    "architect": PersonaMapping(
        owns=["features.*.constraints", "protocols", "contracts"],
        exports_to="specs/*/plan.md",
    ),
    "developer": PersonaMapping(
        owns=["features.*.acceptance", "features.*.implementation"],
        exports_to="specs/*/tasks.md",
    ),
}

# Version bump severity ordering (for recommendations)
BUMP_SEVERITY = {"none": 0, "patch": 1, "minor": 2, "major": 3}


@beartype
@require(lambda repo: isinstance(repo, Path), "Repository path must be Path")
@ensure(lambda result: isinstance(result, tuple) and len(result) == 2, "Must return (bundle_name, bundle_dir)")
def _resolve_bundle(repo: Path, bundle: str | None) -> tuple[str, Path]:
    """
    Resolve bundle name and directory, falling back to active bundle.

    Args:
        repo: Repository path
        bundle: Optional bundle name

    Returns:
        Tuple of (bundle_name, bundle_dir)
    """
    bundle_name = bundle or SpecFactStructure.get_active_bundle_name(repo)
    if bundle_name is None:
        print_error("Bundle not specified and no active bundle found. Use --bundle or set active bundle in config.")
        raise typer.Exit(1)

    bundle_dir = SpecFactStructure.project_dir(base_path=repo, bundle_name=bundle_name)
    if not bundle_dir.exists():
        print_error(f"Project bundle not found: {bundle_dir}")
        raise typer.Exit(1)

    return bundle_name, bundle_dir


@beartype
@require(lambda bundle: isinstance(bundle, ProjectBundle), "Bundle must be ProjectBundle")
@require(lambda persona: isinstance(persona, str), "Persona must be str")
@require(lambda no_interactive: isinstance(no_interactive, bool), "No interactive must be bool")
@ensure(lambda result: isinstance(result, bool), "Must return bool")
def _initialize_persona_if_needed(bundle: ProjectBundle, persona: str, no_interactive: bool) -> bool:
    """
    Initialize persona in bundle manifest if missing and available in defaults.

    Args:
        bundle: Project bundle to update
        persona: Persona name to initialize
        no_interactive: If True, auto-initialize without prompting

    Returns:
        True if persona was initialized, False otherwise
    """
    # Check if persona already exists
    if persona in bundle.manifest.personas:
        return False

    # Check if persona is in default personas
    if persona not in DEFAULT_PERSONAS:
        return False

    # Initialize persona
    if no_interactive:
        # Auto-initialize in non-interactive mode
        bundle.manifest.personas[persona] = DEFAULT_PERSONAS[persona]
        print_success(f"Initialized persona '{persona}' in bundle manifest")
        return True
    # Interactive mode: ask user
    from rich.prompt import Confirm

    print_info(f"Persona '{persona}' not found in bundle manifest.")
    print_info(f"Would you like to initialize '{persona}' with default settings?")
    if Confirm.ask("Initialize persona?", default=True):
        bundle.manifest.personas[persona] = DEFAULT_PERSONAS[persona]
        print_success(f"Initialized persona '{persona}' in bundle manifest")
        return True

    return False


@beartype
@require(lambda bundle: isinstance(bundle, ProjectBundle), "Bundle must be ProjectBundle")
@require(lambda no_interactive: isinstance(no_interactive, bool), "No interactive must be bool")
@ensure(lambda result: isinstance(result, bool), "Must return bool")
def _initialize_all_default_personas(bundle: ProjectBundle, no_interactive: bool) -> bool:
    """
    Initialize all default personas in bundle manifest if missing.

    Args:
        bundle: Project bundle to update
        no_interactive: If True, auto-initialize without prompting

    Returns:
        True if any personas were initialized, False otherwise
    """
    # Find missing default personas
    missing_personas = {k: v for k, v in DEFAULT_PERSONAS.items() if k not in bundle.manifest.personas}

    if not missing_personas:
        return False

    if no_interactive:
        # Auto-initialize all missing personas
        bundle.manifest.personas.update(missing_personas)
        print_success(f"Initialized {len(missing_personas)} default persona(s) in bundle manifest")
        return True
    # Interactive mode: ask user
    from rich.prompt import Confirm

    console.print()  # Empty line
    print_info(f"Found {len(missing_personas)} default persona(s) not in bundle:")
    for p_name in missing_personas:
        print_info(f"  - {p_name}")
    console.print()  # Empty line
    if Confirm.ask("Initialize all default personas?", default=True):
        bundle.manifest.personas.update(missing_personas)
        print_success(f"Initialized {len(missing_personas)} default persona(s) in bundle manifest")
        return True

    return False


@beartype
@require(lambda bundle: isinstance(bundle, ProjectBundle), "Bundle must be ProjectBundle")
@require(lambda bundle_name: isinstance(bundle_name, str), "Bundle name must be str")
@ensure(lambda result: result is None, "Must return None")
def _list_available_personas(bundle: ProjectBundle, bundle_name: str) -> None:
    """
    List all available personas (both in bundle and default personas).

    Args:
        bundle: Project bundle to check
        bundle_name: Name of the bundle (for display)
    """
    console.print(f"\n[bold cyan]Available Personas for bundle '{bundle_name}'[/bold cyan]")
    console.print("=" * 60)

    # Show personas in bundle
    available_personas = list(bundle.manifest.personas.keys())
    if available_personas:
        console.print("\n[bold green]Personas in bundle:[/bold green]")
        for p in available_personas:
            persona_mapping = bundle.manifest.personas[p]
            owns_preview = ", ".join(persona_mapping.owns[:3])
            if len(persona_mapping.owns) > 3:
                owns_preview += "..."
            console.print(f"  [green]✓[/green] {p}: owns {owns_preview}")
    else:
        console.print("\n[yellow]No personas defined in bundle manifest.[/yellow]")

    # Show default personas
    console.print("\n[bold cyan]Default personas available:[/bold cyan]")
    for p_name, p_mapping in DEFAULT_PERSONAS.items():
        status = "[green]✓[/green]" if p_name in bundle.manifest.personas else "[dim]○[/dim]"
        owns_preview = ", ".join(p_mapping.owns[:3])
        if len(p_mapping.owns) > 3:
            owns_preview += "..."
        console.print(f"  {status} {p_name}: owns {owns_preview}")

    console.print("\n[dim]To add personas, use:[/dim]")
    console.print("[dim]  specfact project init-personas --bundle <name>[/dim]")
    console.print("[dim]  specfact project init-personas --bundle <name> --persona <name>[/dim]")
    console.print()


@beartype
@require(lambda section_pattern: isinstance(section_pattern, str), "Section pattern must be str")
@require(lambda path: isinstance(path, str), "Path must be str")
@ensure(lambda result: isinstance(result, bool), "Must return bool")
def match_section_pattern(section_pattern: str, path: str) -> bool:
    """
    Check if a path matches a section pattern.

    Args:
        section_pattern: Pattern (e.g., "idea", "features.*.stories", "contracts")
        path: Path to check (e.g., "idea", "features/FEATURE-001/stories/STORY-001")

    Returns:
        True if path matches pattern, False otherwise

    Examples:
        >>> match_section_pattern("idea", "idea")
        True
        >>> match_section_pattern("features.*.stories", "features/FEATURE-001/stories/STORY-001")
        True
        >>> match_section_pattern("contracts", "contracts/FEATURE-001.openapi.yaml")
        True
    """
    # Normalize patterns: replace * with fnmatch pattern
    pattern = section_pattern.replace(".*", "/*")
    return fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(path, section_pattern)


@beartype
@require(lambda persona: isinstance(persona, str), "Persona must be str")
@require(lambda manifest: isinstance(manifest, BundleManifest), "Manifest must be BundleManifest")
@require(lambda section_path: isinstance(section_path, str), "Section path must be str")
@ensure(lambda result: isinstance(result, bool), "Must return bool")
def check_persona_ownership(persona: str, manifest: BundleManifest, section_path: str) -> bool:
    """
    Check if persona owns a section.

    Args:
        persona: Persona name (e.g., "product-owner", "architect")
        manifest: Bundle manifest with persona mappings
        section_path: Section path to check (e.g., "idea", "features/FEATURE-001/stories")

    Returns:
        True if persona owns section, False otherwise
    """
    if persona not in manifest.personas:
        return False

    persona_mapping = manifest.personas[persona]
    return any(match_section_pattern(pattern, section_path) for pattern in persona_mapping.owns)


@beartype
@require(lambda manifest: isinstance(manifest, BundleManifest), "Manifest must be BundleManifest")
@require(lambda section_path: isinstance(section_path, str), "Section path must be str")
@ensure(lambda result: isinstance(result, bool), "Must return bool")
def check_section_locked(manifest: BundleManifest, section_path: str) -> bool:
    """
    Check if a section is locked.

    Args:
        manifest: Bundle manifest with locks
        section_path: Section path to check

    Returns:
        True if section is locked, False otherwise
    """
    return any(match_section_pattern(lock.section, section_path) for lock in manifest.locks)


@beartype
@require(lambda manifest: isinstance(manifest, BundleManifest), "Manifest must be BundleManifest")
@require(lambda section_paths: isinstance(section_paths, list), "Section paths must be list")
@require(lambda persona: isinstance(persona, str), "Persona must be str")
@ensure(lambda result: isinstance(result, tuple), "Must return tuple")
def check_sections_locked_for_persona(
    manifest: BundleManifest, section_paths: list[str], persona: str
) -> tuple[bool, list[str], str | None]:
    """
    Check if any sections are locked and if persona can edit them.

    Args:
        manifest: Bundle manifest with locks
        section_paths: List of section paths to check
        persona: Persona attempting to edit

    Returns:
        Tuple of (is_locked, locked_sections, lock_owner)
        - is_locked: True if any section is locked
        - locked_sections: List of locked section paths
        - lock_owner: Owner persona of the lock (if locked and not owned by persona)
    """
    locked_sections: list[str] = []
    lock_owner: str | None = None

    for section_path in section_paths:
        for lock in manifest.locks:
            if match_section_pattern(lock.section, section_path):
                locked_sections.append(section_path)
                # If locked by a different persona, record the owner
                if lock.owner != persona:
                    lock_owner = lock.owner
                break

    return (len(locked_sections) > 0, locked_sections, lock_owner)


@app.command("export")
@beartype
@require(lambda repo: isinstance(repo, Path), "Repository path must be Path")
@ensure(lambda result: result is None, "Must return None")
def export_persona(
    # Target/Input
    repo: Path = typer.Option(
        Path("."),
        "--repo",
        help="Path to repository",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    bundle: str | None = typer.Option(
        None,
        "--bundle",
        help="Project bundle name (e.g., legacy-api). If not specified, attempts to auto-detect or prompt.",
    ),
    persona: str | None = typer.Option(
        None,
        "--persona",
        help="Persona name (e.g., product-owner, architect). Use --list-personas to see available personas.",
    ),
    # Output/Results
    output: Path | None = typer.Option(
        None,
        "--output",
        "--out",
        help="Output file path (default: docs/project-plans/<bundle>/<persona>.md or stdout with --stdout)",
    ),
    output_dir: Path | None = typer.Option(
        None,
        "--output-dir",
        help="Output directory for Markdown file (default: docs/project-plans/<bundle>)",
    ),
    # Behavior/Options
    stdout: bool = typer.Option(
        False,
        "--stdout",
        help="Output to stdout instead of file (for piping/CI usage)",
    ),
    template: str | None = typer.Option(
        None,
        "--template",
        help="Custom template name (default: uses persona-specific template)",
    ),
    list_personas: bool = typer.Option(
        False,
        "--list-personas",
        help="List all available personas and exit",
    ),
    no_interactive: bool = typer.Option(
        False,
        "--no-interactive",
        help="Non-interactive mode (for CI/CD automation). Default: False (interactive mode)",
    ),
) -> None:
    """
    Export persona-owned sections from project bundle to Markdown.

    Generates well-structured Markdown artifacts using templates, filtered by
    persona ownership. Perfect for AI IDEs and manual editing workflows.

    **Parameter Groups:**
    - **Target/Input**: --repo, --bundle, --persona
    - **Output/Results**: --output, --output-dir, --stdout
    - **Behavior/Options**: --template, --no-interactive

    **Examples:**
        specfact project export --bundle legacy-api --persona product-owner
        specfact project export --bundle legacy-api --persona architect --output-dir docs/plans
        specfact project export --bundle legacy-api --persona developer --stdout
    """
    if is_debug_mode():
        debug_log_operation(
            "command",
            "project export",
            "started",
            extra={"repo": str(repo), "bundle": bundle, "persona": persona},
        )
        debug_print("[dim]project export: started[/dim]")

    # Get bundle name
    if bundle is None:
        bundle = SpecFactStructure.get_active_bundle_name(repo)
        if bundle is None and not no_interactive:
            # Interactive selection
            from rich.prompt import Prompt

            plans = SpecFactStructure.list_plans(repo)
            if not plans:
                if is_debug_mode():
                    debug_log_operation(
                        "command",
                        "project export",
                        "failed",
                        error="No project bundles found",
                        extra={"reason": "no_bundles"},
                    )
                print_error("No project bundles found")
                raise typer.Exit(1)
            bundle_names = [str(p["name"]) for p in plans if p.get("name")]
            if not bundle_names:
                print_error("No valid bundle names found")
                raise typer.Exit(1)
            bundle = Prompt.ask("Select bundle", choices=bundle_names)
        elif bundle is None:
            print_error("Bundle not specified and no active bundle found")
            raise typer.Exit(1)

    # Ensure bundle is not None
    if bundle is None:
        print_error("Bundle not specified")
        raise typer.Exit(1)

    # Get bundle directory
    bundle_dir = SpecFactStructure.project_dir(base_path=repo, bundle_name=bundle)
    if not bundle_dir.exists():
        if is_debug_mode():
            debug_log_operation(
                "command",
                "project export",
                "failed",
                error=f"Project bundle not found: {bundle_dir}",
                extra={"reason": "bundle_not_found", "bundle": bundle},
            )
        print_error(f"Project bundle not found: {bundle_dir}")
        raise typer.Exit(1)

    bundle_obj = _load_bundle_with_progress(bundle_dir, validate_hashes=False)

    # Handle --list-personas flag or missing --persona
    if list_personas or persona is None:
        _list_available_personas(bundle_obj, bundle)
        raise typer.Exit(0)

    # Check persona exists, try to initialize if missing
    if persona not in bundle_obj.manifest.personas:
        # Try to initialize the requested persona
        persona_initialized = _initialize_persona_if_needed(bundle_obj, persona, no_interactive)

        if persona_initialized:
            # Save bundle with new persona
            _save_bundle_with_progress(bundle_obj, bundle_dir, atomic=True)
        else:
            # Persona not available in defaults or user declined
            print_error(f"Persona '{persona}' not found in bundle manifest")
            console.print()  # Empty line

            # Always show available personas in bundle
            available_personas = list(bundle_obj.manifest.personas.keys())
            if available_personas:
                print_info("Available personas in bundle:")
                for p in available_personas:
                    print_info(f"  - {p}")
            else:
                print_info("No personas defined in bundle manifest.")

            console.print()  # Empty line

            # Always show default personas (even if some are already in bundle)
            print_info("Default personas available:")
            for p_name, p_mapping in DEFAULT_PERSONAS.items():
                status = "[green]✓[/green]" if p_name in bundle_obj.manifest.personas else "[dim]○[/dim]"
                owns_preview = ", ".join(p_mapping.owns[:3])
                if len(p_mapping.owns) > 3:
                    owns_preview += "..."
                print_info(f"  {status} {p_name}: owns {owns_preview}")

            console.print()  # Empty line

            # Offer to initialize all default personas if none are defined
            if not available_personas and not no_interactive:
                all_initialized = _initialize_all_default_personas(bundle_obj, no_interactive)
                if all_initialized:
                    _save_bundle_with_progress(bundle_obj, bundle_dir, atomic=True)
                    # Retry with the newly initialized persona
                    if persona in bundle_obj.manifest.personas:
                        persona_initialized = True

            if not persona_initialized:
                print_info("To add personas, use:")
                print_info("  specfact project init-personas --bundle <name>")
                print_info("  specfact project init-personas --bundle <name> --persona <name>")
                raise typer.Exit(1)

    # Get persona mapping
    persona_mapping = bundle_obj.manifest.personas[persona]

    # Initialize exporter with template support
    from specfact_cli.generators.persona_exporter import PersonaExporter

    # Check for project-specific templates
    project_templates_dir = repo / ".specfact" / "templates" / "persona"
    project_templates_dir = project_templates_dir if project_templates_dir.exists() else None

    exporter = PersonaExporter(project_templates_dir=project_templates_dir)

    # Determine output path
    if stdout:
        # Export to stdout
        markdown_content = exporter.export_to_string(bundle_obj, persona_mapping, persona)
        console.print(markdown_content)
    else:
        # Determine output file path
        if output:
            output_path = Path(output)
        elif output_dir:
            output_path = Path(output_dir) / f"{persona}.md"
        else:
            # Default: docs/project-plans/<bundle>/<persona>.md
            default_dir = repo / "docs" / "project-plans" / bundle
            output_path = default_dir / f"{persona}.md"

        # Export to file with progress
        from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(f"[cyan]Exporting persona '{persona}' to Markdown...", total=None)
            try:
                exporter.export_to_file(bundle_obj, persona_mapping, persona, output_path)
                progress.update(task, description=f"[green]✓[/green] Exported to {output_path}")
            except Exception as e:
                progress.update(task, description="[red]✗[/red] Export failed")
                print_error(f"Export failed: {e}")
                raise typer.Exit(1) from e

        if is_debug_mode():
            debug_log_operation(
                "command",
                "project export",
                "success",
                extra={"bundle": bundle, "persona": persona, "output_path": str(output_path)},
            )
            debug_print("[dim]project export: success[/dim]")
        print_success(f"Exported persona '{persona}' sections to {output_path}")
        print_info(f"Template: {persona}.md.j2")


@app.command("import")
@beartype
@require(lambda repo: isinstance(repo, Path), "Repository path must be Path")
@ensure(lambda result: result is None, "Must return None")
def import_persona(
    # Target/Input
    repo: Path = typer.Option(
        Path("."),
        "--repo",
        help="Path to repository",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    bundle: str | None = typer.Option(
        None,
        "--bundle",
        help="Project bundle name (e.g., legacy-api). If not specified, attempts to auto-detect or prompt.",
    ),
    persona: str | None = typer.Option(
        None,
        "--persona",
        help="Persona name (e.g., product-owner, architect). Use --list-personas to see available personas.",
    ),
    # Input
    input_file: Path = typer.Option(
        ...,
        "--input",
        "--file",
        "-i",
        help="Path to Markdown file to import",
        exists=True,
    ),
    # Behavior/Options
    no_interactive: bool = typer.Option(
        False,
        "--no-interactive",
        help="Non-interactive mode (for CI/CD automation). Default: False (interactive mode)",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Validate import without applying changes",
    ),
) -> None:
    """
    Import persona-edited Markdown file back into project bundle.

    Validates Markdown structure against template schema, checks ownership,
    and transforms Markdown content back to YAML bundle format.

    **Parameter Groups:**
    - **Target/Input**: --repo, --bundle, --persona, --input
    - **Behavior/Options**: --dry-run, --no-interactive

    **Examples:**
        specfact project import --bundle legacy-api --persona product-owner --input product-owner.md
        specfact project import --bundle legacy-api --persona architect --input architect.md --dry-run
    """
    if is_debug_mode():
        debug_log_operation(
            "command",
            "project import",
            "started",
            extra={"repo": str(repo), "bundle": bundle, "persona": persona, "input_file": str(input_file)},
        )
        debug_print("[dim]project import: started[/dim]")

    from specfact_cli.models.persona_template import PersonaTemplate, SectionType, TemplateSection
    from specfact_cli.parsers.persona_importer import PersonaImporter, PersonaImportError

    # Get bundle name
    if bundle is None:
        bundle = SpecFactStructure.get_active_bundle_name(repo)
        if bundle is None and not no_interactive:
            from rich.prompt import Prompt

            plans = SpecFactStructure.list_plans(repo)
            if not plans:
                print_error("No project bundles found")
                raise typer.Exit(1)
            bundle_names = [str(p["name"]) for p in plans if p.get("name")]
            if not bundle_names:
                print_error("No valid bundle names found")
                raise typer.Exit(1)
            bundle = Prompt.ask("Select bundle", choices=bundle_names)
        elif bundle is None:
            print_error("Bundle not specified and no active bundle found")
            raise typer.Exit(1)

    if bundle is None:
        print_error("Bundle not specified")
        raise typer.Exit(1)

    # Get bundle directory
    bundle_dir = SpecFactStructure.project_dir(base_path=repo, bundle_name=bundle)
    if not bundle_dir.exists():
        print_error(f"Project bundle not found: {bundle_dir}")
        raise typer.Exit(1)

    bundle_obj = _load_bundle_with_progress(bundle_dir, validate_hashes=False)

    # Handle --list-personas flag or missing --persona
    if persona is None:
        _list_available_personas(bundle_obj, bundle)
        raise typer.Exit(0)

    # Check persona exists
    if persona not in bundle_obj.manifest.personas:
        print_error(f"Persona '{persona}' not found in bundle manifest")
        _list_available_personas(bundle_obj, bundle)
        raise typer.Exit(1)

    persona_mapping = bundle_obj.manifest.personas[persona]

    # Create template (simplified - in production would load from file)
    # For now, create a basic template based on persona
    template_sections = [
        TemplateSection(
            name="idea_business_context",
            heading="## Idea & Business Context",
            type=SectionType.REQUIRED
            if "idea" in " ".join(persona_mapping.owns) or "business" in " ".join(persona_mapping.owns)
            else SectionType.OPTIONAL,
            description="Problem statement, solution vision, and business context",
            order=1,
            validation=None,
            placeholder=None,
            condition=None,
        ),
        TemplateSection(
            name="features",
            heading="## Features & User Stories",
            type=SectionType.REQUIRED if any("features" in o for o in persona_mapping.owns) else SectionType.OPTIONAL,
            description="Features and user stories",
            order=2,
            validation=None,
            placeholder=None,
            condition=None,
        ),
    ]
    template = PersonaTemplate(
        persona_name=persona,
        version="1.0.0",
        description=f"Template for {persona} persona",
        sections=template_sections,
    )

    # Initialize importer
    # Disable agile validation in test mode to allow simpler test scenarios
    validate_agile = os.environ.get("TEST_MODE") != "true"
    importer = PersonaImporter(template, validate_agile=validate_agile)

    # Import with progress
    from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(f"[cyan]Validating and importing '{input_file.name}'...", total=None)

        try:
            if dry_run:
                # Just validate without importing
                markdown_content = input_file.read_text(encoding="utf-8")
                sections = importer.parse_markdown(markdown_content)
                validation_errors = importer.validate_structure(sections)

                if validation_errors:
                    progress.update(task, description="[red]✗[/red] Validation failed")
                    print_error("Template validation failed:")
                    for error in validation_errors:
                        print_error(f"  - {error}")
                    raise typer.Exit(1)
                progress.update(task, description="[green]✓[/green] Validation passed")
                print_success("Import validation passed (dry-run)")
            else:
                # Check locks before importing
                # Determine which sections will be modified based on persona ownership
                sections_to_modify = list(persona_mapping.owns)

                is_locked, locked_sections, lock_owner = check_sections_locked_for_persona(
                    bundle_obj.manifest, sections_to_modify, persona
                )

                # Only block if locked by a different persona
                if is_locked and lock_owner is not None and lock_owner != persona:
                    progress.update(task, description="[red]✗[/red] Import blocked by locks")
                    print_error("Cannot import: Section(s) are locked")
                    for locked_section in locked_sections:
                        # Find the lock for this section
                        for lock in bundle_obj.manifest.locks:
                            if match_section_pattern(lock.section, locked_section):
                                # Only report if locked by different persona
                                if lock.owner != persona:
                                    print_error(
                                        f"  - Section '{locked_section}' is locked by '{lock.owner}' "
                                        f"(locked at {lock.locked_at})"
                                    )
                                break
                    print_info("Use 'specfact project unlock --section <section>' to unlock, or contact the lock owner")
                    raise typer.Exit(1)

                # Import and update bundle
                updated_bundle = importer.import_from_file(input_file, bundle_obj, persona_mapping, persona)
                progress.update(task, description="[green]✓[/green] Import complete")

                # Save updated bundle
                _save_bundle_with_progress(updated_bundle, bundle_dir, atomic=True)
                print_success(f"Imported persona '{persona}' edits from {input_file}")

        except PersonaImportError as e:
            progress.update(task, description="[red]✗[/red] Import failed")
            print_error(f"Import failed: {e}")
            raise typer.Exit(1) from e
        except Exception as e:
            progress.update(task, description="[red]✗[/red] Import failed")
            print_error(f"Unexpected error during import: {e}")
            raise typer.Exit(1) from e


@beartype
@require(lambda bundle: isinstance(bundle, ProjectBundle), "Bundle must be ProjectBundle")
@require(lambda persona_mapping: isinstance(persona_mapping, PersonaMapping), "Persona mapping must be PersonaMapping")
@ensure(lambda result: isinstance(result, dict), "Must return dict")
def _filter_bundle_by_persona(bundle: ProjectBundle, persona_mapping: PersonaMapping) -> dict[str, Any]:
    """
    Filter bundle to include only persona-owned sections.

    Args:
        bundle: Project bundle to filter
        persona_mapping: Persona mapping with owned sections

    Returns:
        Filtered bundle dictionary
    """
    filtered: dict[str, Any] = {
        "bundle_name": bundle.bundle_name,
        "manifest": bundle.manifest.model_dump(),
    }

    # Filter aspects by persona ownership
    if bundle.idea and any(match_section_pattern(p, "idea") for p in persona_mapping.owns):
        filtered["idea"] = bundle.idea.model_dump()

    if bundle.business and any(match_section_pattern(p, "business") for p in persona_mapping.owns):
        filtered["business"] = bundle.business.model_dump()

    if any(match_section_pattern(p, "product") for p in persona_mapping.owns):
        filtered["product"] = bundle.product.model_dump()

    # Filter features by persona ownership
    filtered_features: dict[str, Any] = {}
    for feature_key, feature in bundle.features.items():
        feature_dict = feature.model_dump()
        filtered_feature: dict[str, Any] = {"key": feature.key, "title": feature.title}

        # Filter stories if persona owns stories
        if any(match_section_pattern(p, "features.*.stories") for p in persona_mapping.owns):
            filtered_feature["stories"] = feature_dict.get("stories", [])

        # Filter outcomes if persona owns outcomes
        if any(match_section_pattern(p, "features.*.outcomes") for p in persona_mapping.owns):
            filtered_feature["outcomes"] = feature_dict.get("outcomes", [])

        # Filter constraints if persona owns constraints
        if any(match_section_pattern(p, "features.*.constraints") for p in persona_mapping.owns):
            filtered_feature["constraints"] = feature_dict.get("constraints", [])

        # Filter acceptance if persona owns acceptance
        if any(match_section_pattern(p, "features.*.acceptance") for p in persona_mapping.owns):
            filtered_feature["acceptance"] = feature_dict.get("acceptance", [])

        if filtered_feature:
            filtered_features[feature_key] = filtered_feature

    if filtered_features:
        filtered["features"] = filtered_features

    return filtered


@beartype
@require(lambda bundle_data: isinstance(bundle_data, dict), "Bundle data must be dict")
@require(lambda output_path: isinstance(output_path, Path), "Output path must be Path")
@require(lambda format: isinstance(format, str), "Format must be str")
@ensure(lambda result: result is None, "Must return None")
def _export_bundle_to_file(bundle_data: dict[str, Any], output_path: Path, format: str) -> None:
    """Export bundle data to file."""
    import json

    import yaml

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        if format.lower() == "json":
            json.dump(bundle_data, f, indent=2, default=str)
        else:
            yaml.dump(bundle_data, f, default_flow_style=False, sort_keys=False)


@beartype
@require(lambda bundle_data: isinstance(bundle_data, dict), "Bundle data must be dict")
@require(lambda format: isinstance(format, str), "Format must be str")
@ensure(lambda result: result is None, "Must return None")
def _export_bundle_to_stdout(bundle_data: dict[str, Any], format: str) -> None:
    """Export bundle data to stdout."""
    import json

    import yaml

    if format.lower() == "json":
        console.print(json.dumps(bundle_data, indent=2, default=str))
    else:
        console.print(yaml.dump(bundle_data, default_flow_style=False, sort_keys=False))


@app.command("lock")
@beartype
@require(lambda repo: isinstance(repo, Path), "Repository path must be Path")
@ensure(lambda result: result is None, "Must return None")
def lock_section(
    # Target/Input
    repo: Path = typer.Option(
        Path("."),
        "--repo",
        help="Path to repository",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    bundle: str | None = typer.Option(
        None,
        "--bundle",
        help="Project bundle name (e.g., legacy-api). If not specified, attempts to auto-detect or prompt.",
    ),
    section: str = typer.Option(..., "--section", help="Section pattern (e.g., 'idea', 'features.*.stories')"),
    persona: str = typer.Option(..., "--persona", help="Persona name (e.g., product-owner, architect)"),
    # Behavior/Options
    no_interactive: bool = typer.Option(
        False,
        "--no-interactive",
        help="Non-interactive mode (for CI/CD automation). Default: False (interactive mode)",
    ),
) -> None:
    """
    Lock a section for a persona.

    Prevents other personas from editing the specified section until unlocked.

    **Parameter Groups:**
    - **Target/Input**: --repo, --bundle, --section, --persona
    - **Behavior/Options**: --no-interactive

    **Examples:**
        specfact project lock --bundle legacy-api --section idea --persona product-owner
        specfact project lock --bundle legacy-api --section "features.*.stories" --persona product-owner
    """
    if is_debug_mode():
        debug_log_operation(
            "command",
            "project lock",
            "started",
            extra={"repo": str(repo), "bundle": bundle, "section": section, "persona": persona},
        )
        debug_print("[dim]project lock: started[/dim]")

    # Get bundle name
    if bundle is None:
        bundle = SpecFactStructure.get_active_bundle_name(repo)
        if bundle is None and not no_interactive:
            # Interactive selection
            from rich.prompt import Prompt

            plans = SpecFactStructure.list_plans(repo)
            if not plans:
                print_error("No project bundles found")
                raise typer.Exit(1)
            bundle_names = [str(p["name"]) for p in plans if p.get("name")]
            if not bundle_names:
                print_error("No valid bundle names found")
                raise typer.Exit(1)
            bundle = Prompt.ask("Select bundle", choices=bundle_names)
        elif bundle is None:
            print_error("Bundle not specified and no active bundle found")
            raise typer.Exit(1)

    # Ensure bundle is not None
    if bundle is None:
        print_error("Bundle not specified")
        raise typer.Exit(1)

    # Get bundle directory
    bundle_dir = SpecFactStructure.project_dir(base_path=repo, bundle_name=bundle)
    if not bundle_dir.exists():
        print_error(f"Project bundle not found: {bundle_dir}")
        raise typer.Exit(1)

    bundle_obj = _load_bundle_with_progress(bundle_dir, validate_hashes=False)

    # Check persona exists, try to initialize if missing
    if persona not in bundle_obj.manifest.personas:
        # Try to initialize the requested persona
        persona_initialized = _initialize_persona_if_needed(bundle_obj, persona, no_interactive)

        if persona_initialized:
            # Save bundle with new persona
            _save_bundle_with_progress(bundle_obj, bundle_dir, atomic=True)
        else:
            # Persona not available in defaults or user declined
            print_error(f"Persona '{persona}' not found in bundle manifest")
            console.print()  # Empty line

            # Always show available personas in bundle
            available_personas = list(bundle_obj.manifest.personas.keys())
            if available_personas:
                print_info("Available personas in bundle:")
                for p in available_personas:
                    print_info(f"  - {p}")
            else:
                print_info("No personas defined in bundle manifest.")

            console.print()  # Empty line

            # Always show default personas (even if some are already in bundle)
            print_info("Default personas available:")
            for p_name, p_mapping in DEFAULT_PERSONAS.items():
                status = "[green]✓[/green]" if p_name in bundle_obj.manifest.personas else "[dim]○[/dim]"
                owns_preview = ", ".join(p_mapping.owns[:3])
                if len(p_mapping.owns) > 3:
                    owns_preview += "..."
                print_info(f"  {status} {p_name}: owns {owns_preview}")

            console.print()  # Empty line

            # Offer to initialize all default personas if none are defined
            if not available_personas and not no_interactive:
                all_initialized = _initialize_all_default_personas(bundle_obj, no_interactive)
                if all_initialized:
                    _save_bundle_with_progress(bundle_obj, bundle_dir, atomic=True)
                    # Retry with the newly initialized persona
                    if persona in bundle_obj.manifest.personas:
                        persona_initialized = True

            if not persona_initialized:
                print_info("To add personas, use:")
                print_info("  specfact project init-personas --bundle <name>")
                print_info("  specfact project init-personas --bundle <name> --persona <name>")
                raise typer.Exit(1)

    # Check persona owns section
    if not check_persona_ownership(persona, bundle_obj.manifest, section):
        print_error(f"Persona '{persona}' does not own section '{section}'")
        raise typer.Exit(1)

    # Check if already locked
    if check_section_locked(bundle_obj.manifest, section):
        print_warning(f"Section '{section}' is already locked")
        raise typer.Exit(1)

    # Create lock
    lock = SectionLock(
        section=section,
        owner=persona,
        locked_at=datetime.now(UTC).isoformat(),
        locked_by=os.environ.get("USER", "unknown") + "@" + os.environ.get("HOSTNAME", "unknown"),
    )

    bundle_obj.manifest.locks.append(lock)

    # Save bundle
    _save_bundle_with_progress(bundle_obj, bundle_dir, atomic=True)
    print_success(f"Locked section '{section}' for persona '{persona}'")


@app.command("unlock")
@beartype
@require(lambda repo: isinstance(repo, Path), "Repository path must be Path")
@ensure(lambda result: result is None, "Must return None")
def unlock_section(
    # Target/Input
    repo: Path = typer.Option(
        Path("."),
        "--repo",
        help="Path to repository",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    bundle: str | None = typer.Option(
        None,
        "--bundle",
        help="Project bundle name (e.g., legacy-api). If not specified, attempts to auto-detect or prompt.",
    ),
    section: str = typer.Option(..., "--section", help="Section pattern (e.g., 'idea', 'features.*.stories')"),
    # Behavior/Options
    no_interactive: bool = typer.Option(
        False,
        "--no-interactive",
        help="Non-interactive mode (for CI/CD automation). Default: False (interactive mode)",
    ),
) -> None:
    """
    Unlock a section.

    Removes the lock on the specified section, allowing edits by any persona that owns it.

    **Parameter Groups:**
    - **Target/Input**: --repo, --bundle, --section
    - **Behavior/Options**: --no-interactive

    **Examples:**
        specfact project unlock --bundle legacy-api --section idea
        specfact project unlock --bundle legacy-api --section "features.*.stories"
    """

    # Get bundle name
    if bundle is None:
        bundle = SpecFactStructure.get_active_bundle_name(repo)
        if bundle is None and not no_interactive:
            # Interactive selection
            from rich.prompt import Prompt

            plans = SpecFactStructure.list_plans(repo)
            if not plans:
                print_error("No project bundles found")
                raise typer.Exit(1)
            bundle_names = [str(p["name"]) for p in plans if p.get("name")]
            if not bundle_names:
                print_error("No valid bundle names found")
                raise typer.Exit(1)
            bundle = Prompt.ask("Select bundle", choices=bundle_names)
        elif bundle is None:
            print_error("Bundle not specified and no active bundle found")
            raise typer.Exit(1)

    # Ensure bundle is not None
    if bundle is None:
        print_error("Bundle not specified")
        raise typer.Exit(1)

    # Get bundle directory
    bundle_dir = SpecFactStructure.project_dir(base_path=repo, bundle_name=bundle)
    if not bundle_dir.exists():
        print_error(f"Project bundle not found: {bundle_dir}")
        raise typer.Exit(1)

    bundle_obj = _load_bundle_with_progress(bundle_dir, validate_hashes=False)

    # Find and remove lock
    removed = False
    for i, lock in enumerate(bundle_obj.manifest.locks):
        if match_section_pattern(lock.section, section):
            bundle_obj.manifest.locks.pop(i)
            removed = True
            break

    if not removed:
        print_warning(f"Section '{section}' is not locked")
        raise typer.Exit(1)

    # Save bundle
    _save_bundle_with_progress(bundle_obj, bundle_dir, atomic=True)
    print_success(f"Unlocked section '{section}'")


@app.command("locks")
@beartype
@require(lambda repo: isinstance(repo, Path), "Repository path must be Path")
@ensure(lambda result: result is None, "Must return None")
def list_locks(
    # Target/Input
    repo: Path = typer.Option(
        Path("."),
        "--repo",
        help="Path to repository",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    bundle: str | None = typer.Option(
        None,
        "--bundle",
        help="Project bundle name (e.g., legacy-api). If not specified, attempts to auto-detect or prompt.",
    ),
    # Behavior/Options
    no_interactive: bool = typer.Option(
        False,
        "--no-interactive",
        help="Non-interactive mode (for CI/CD automation). Default: False (interactive mode)",
    ),
) -> None:
    """
    List all section locks.

    Shows all currently locked sections with their owners and lock timestamps.

    **Parameter Groups:**
    - **Target/Input**: --repo, --bundle
    - **Behavior/Options**: --no-interactive

    **Examples:**
        specfact project locks --bundle legacy-api
    """

    # Get bundle name
    if bundle is None:
        bundle = SpecFactStructure.get_active_bundle_name(repo)
        if bundle is None and not no_interactive:
            # Interactive selection
            from rich.prompt import Prompt

            plans = SpecFactStructure.list_plans(repo)
            if not plans:
                print_error("No project bundles found")
                raise typer.Exit(1)
            bundle_names = [str(p["name"]) for p in plans if p.get("name")]
            if not bundle_names:
                print_error("No valid bundle names found")
                raise typer.Exit(1)
            bundle = Prompt.ask("Select bundle", choices=bundle_names)
        elif bundle is None:
            print_error("Bundle not specified and no active bundle found")
            raise typer.Exit(1)

    # Ensure bundle is not None
    if bundle is None:
        print_error("Bundle not specified")
        raise typer.Exit(1)

    # Get bundle directory
    bundle_dir = SpecFactStructure.project_dir(base_path=repo, bundle_name=bundle)
    if not bundle_dir.exists():
        print_error(f"Project bundle not found: {bundle_dir}")
        raise typer.Exit(1)

    bundle_obj = _load_bundle_with_progress(bundle_dir, validate_hashes=False)

    # Display locks
    if not bundle_obj.manifest.locks:
        print_info("No locks found")
        return

    table = Table(title="Section Locks")
    table.add_column("Section", style="cyan")
    table.add_column("Owner", style="magenta")
    table.add_column("Locked At", style="green")
    table.add_column("Locked By", style="yellow")

    for lock in bundle_obj.manifest.locks:
        table.add_row(lock.section, lock.owner, lock.locked_at, lock.locked_by)

    console.print(table)


@app.command("init-personas")
@beartype
@require(lambda repo: isinstance(repo, Path), "Repository path must be Path")
@ensure(lambda result: result is None, "Must return None")
def init_personas(
    # Target/Input
    repo: Path = typer.Option(
        Path("."),
        "--repo",
        help="Path to repository",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    bundle: str | None = typer.Option(
        None,
        "--bundle",
        help="Project bundle name (e.g., legacy-api). If not specified, attempts to auto-detect or prompt.",
    ),
    personas: list[str] = typer.Option(
        [],
        "--persona",
        help="Specific persona(s) to initialize (e.g., --persona product-owner --persona architect). If not specified, initializes all default personas.",
    ),
    # Behavior/Options
    no_interactive: bool = typer.Option(
        False,
        "--no-interactive",
        help="Non-interactive mode (for CI/CD automation). Default: False (interactive mode)",
    ),
) -> None:
    """
    Initialize personas in project bundle manifest.

    Adds default persona mappings to the bundle manifest if they are missing.
    Useful for migrating existing bundles to use persona workflows.

    **Parameter Groups:**
    - **Target/Input**: --repo, --bundle, --persona
    - **Behavior/Options**: --no-interactive

    **Examples:**
        specfact project init-personas --bundle legacy-api
        specfact project init-personas --bundle legacy-api --persona product-owner --persona architect
        specfact project init-personas --bundle legacy-api --no-interactive
    """

    # Get bundle name
    if bundle is None:
        bundle = SpecFactStructure.get_active_bundle_name(repo)
        if bundle is None and not no_interactive:
            # Interactive selection
            from rich.prompt import Prompt

            plans = SpecFactStructure.list_plans(repo)
            if not plans:
                print_error("No project bundles found")
                raise typer.Exit(1)
            bundle_names = [str(p["name"]) for p in plans if p.get("name")]
            if not bundle_names:
                print_error("No valid bundle names found")
                raise typer.Exit(1)
            bundle = Prompt.ask("Select bundle", choices=bundle_names)
        elif bundle is None:
            print_error("Bundle not specified and no active bundle found")
            raise typer.Exit(1)

    # Ensure bundle is not None
    if bundle is None:
        print_error("Bundle not specified")
        raise typer.Exit(1)

    # Get bundle directory
    bundle_dir = SpecFactStructure.project_dir(base_path=repo, bundle_name=bundle)
    if not bundle_dir.exists():
        print_error(f"Project bundle not found: {bundle_dir}")
        raise typer.Exit(1)

    bundle_obj = _load_bundle_with_progress(bundle_dir, validate_hashes=False)

    # Determine which personas to initialize
    personas_to_init: dict[str, PersonaMapping] = {}

    if personas:
        # Initialize specific personas
        for persona_name in personas:
            if persona_name not in DEFAULT_PERSONAS:
                print_error(f"Persona '{persona_name}' is not a default persona")
                print_info("Available default personas:")
                for p_name in DEFAULT_PERSONAS:
                    print_info(f"  - {p_name}")
                raise typer.Exit(1)

            if persona_name in bundle_obj.manifest.personas:
                print_warning(f"Persona '{persona_name}' already exists in bundle manifest")
            else:
                personas_to_init[persona_name] = DEFAULT_PERSONAS[persona_name]
    else:
        # Initialize all missing default personas
        personas_to_init = {k: v for k, v in DEFAULT_PERSONAS.items() if k not in bundle_obj.manifest.personas}

    if not personas_to_init:
        print_info("All default personas are already initialized in bundle manifest")
        return

    # Show what will be initialized
    console.print()  # Empty line
    print_info(f"Will initialize {len(personas_to_init)} persona(s):")
    for p_name, p_mapping in personas_to_init.items():
        owns_preview = ", ".join(p_mapping.owns[:3])
        if len(p_mapping.owns) > 3:
            owns_preview += "..."
        print_info(f"  - {p_name}: owns {owns_preview}")

    # Confirm in interactive mode
    if not no_interactive:
        from rich.prompt import Confirm

        console.print()  # Empty line
        if not Confirm.ask("Initialize these personas?", default=True):
            print_info("Persona initialization cancelled")
            raise typer.Exit(0)

    # Initialize personas
    bundle_obj.manifest.personas.update(personas_to_init)

    # Save bundle
    _save_bundle_with_progress(bundle_obj, bundle_dir, atomic=True)
    print_success(f"Initialized {len(personas_to_init)} persona(s) in bundle manifest")


@app.command("merge")
@beartype
@require(lambda repo: isinstance(repo, Path), "Repository path must be Path")
@ensure(lambda result: result is None, "Must return None")
def merge_bundles(
    # Target/Input
    repo: Path = typer.Option(
        Path("."),
        "--repo",
        help="Path to repository",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    bundle: str | None = typer.Option(
        None,
        "--bundle",
        help="Project bundle name (e.g., legacy-api). If not specified, attempts to auto-detect or prompt.",
    ),
    base: str = typer.Option(..., "--base", help="Base branch/commit (common ancestor)"),
    ours: str = typer.Option(..., "--ours", help="Our branch/commit (current branch)"),
    theirs: str = typer.Option(..., "--theirs", help="Their branch/commit (incoming branch)"),
    persona_ours: str = typer.Option(..., "--persona-ours", help="Persona who made our changes (e.g., product-owner)"),
    persona_theirs: str = typer.Option(
        ..., "--persona-theirs", help="Persona who made their changes (e.g., architect)"
    ),
    # Output/Results
    output: Path | None = typer.Option(
        None,
        "--output",
        "--out",
        help="Output directory for merged bundle (default: current bundle directory)",
    ),
    # Behavior/Options
    no_interactive: bool = typer.Option(
        False,
        "--no-interactive",
        help="Non-interactive mode (for CI/CD automation). Disables interactive prompts.",
    ),
    strategy: str = typer.Option(
        "auto",
        "--strategy",
        help="Merge strategy: auto (persona-based), ours, theirs, base, manual",
    ),
) -> None:
    """
    Merge project bundles using three-way merge with persona-aware conflict resolution.

    Performs a three-way merge between base, ours, and theirs versions of a project bundle,
    automatically resolving conflicts based on persona ownership rules.

    **Parameter Groups:**
    - **Target/Input**: --repo, --bundle, --base, --ours, --theirs, --persona-ours, --persona-theirs
    - **Output/Results**: --output
    - **Behavior/Options**: --no-interactive, --strategy

    **Examples:**
        specfact project merge --base main --ours po-branch --theirs arch-branch --persona-ours product-owner --persona-theirs architect
        specfact project merge --bundle legacy-api --base main --ours feature-1 --theirs feature-2 --persona-ours developer --persona-theirs developer
    """
    from specfact_cli.merge.resolver import MergeStrategy, PersonaMergeResolver
    from specfact_cli.utils.git import GitOperations

    # Get bundle name
    if bundle is None:
        bundle = SpecFactStructure.get_active_bundle_name(repo)
        if bundle is None and not no_interactive:
            from rich.prompt import Prompt

            plans = SpecFactStructure.list_plans(repo)
            if not plans:
                print_error("No project bundles found")
                raise typer.Exit(1)
            bundle_names = [str(p["name"]) for p in plans if p.get("name")]
            if not bundle_names:
                print_error("No valid bundle names found")
                raise typer.Exit(1)
            bundle = Prompt.ask("Select bundle", choices=bundle_names)
        elif bundle is None:
            print_error("Bundle not specified and no active bundle found")
            raise typer.Exit(1)

    if bundle is None:
        print_error("Bundle not specified")
        raise typer.Exit(1)

    # Initialize Git operations
    git_ops = GitOperations(repo)
    if not git_ops._is_git_repo():
        print_error("Not a Git repository. Merge requires Git.")
        raise typer.Exit(1)

    print_section(f"Merging project bundle '{bundle}'")

    # Load bundles from Git branches/commits
    # For now, we'll load from current directory and assume bundles are checked out
    # In a full implementation, we'd checkout branches and load bundles
    bundle_dir = SpecFactStructure.project_dir(base_path=repo, bundle_name=bundle)

    # Load base, ours, and theirs bundles from Git branches/commits
    print_info("Loading bundles from Git branches/commits...")

    # Save current branch
    current_branch = git_ops.get_current_branch()

    try:
        # Load base bundle
        print_info(f"Loading base bundle from {base}...")
        git_ops.checkout(base)
        base_bundle = _load_bundle_with_progress(bundle_dir, validate_hashes=False)

        # Load ours bundle
        print_info(f"Loading ours bundle from {ours}...")
        git_ops.checkout(ours)
        ours_bundle = _load_bundle_with_progress(bundle_dir, validate_hashes=False)

        # Load theirs bundle
        print_info(f"Loading theirs bundle from {theirs}...")
        git_ops.checkout(theirs)
        theirs_bundle = _load_bundle_with_progress(bundle_dir, validate_hashes=False)
    except Exception as e:
        print_error(f"Failed to load bundles from Git: {e}")
        # Restore original branch
        with suppress(Exception):
            git_ops.checkout(current_branch)
        raise typer.Exit(1) from e
    finally:
        # Restore original branch
        with suppress(Exception):
            git_ops.checkout(current_branch)
            print_info(f"Restored branch: {current_branch}")

    # Perform merge
    resolver = PersonaMergeResolver()
    resolution = resolver.resolve(base_bundle, ours_bundle, theirs_bundle, persona_ours, persona_theirs)

    # Display results
    print_section("Merge Resolution Results")
    print_info(f"Auto-resolved: {resolution.auto_resolved}")
    print_info(f"Manual resolution required: {resolution.unresolved}")

    if resolution.conflicts:
        from rich.table import Table

        conflicts_table = Table(title="Conflicts")
        conflicts_table.add_column("Section", style="cyan")
        conflicts_table.add_column("Field", style="magenta")
        conflicts_table.add_column("Resolution", style="green")
        conflicts_table.add_column("Status", style="yellow")

        for conflict in resolution.conflicts:
            status = "✅ Auto-resolved" if conflict.resolution != MergeStrategy.MANUAL else "❌ Manual required"
            conflicts_table.add_row(
                conflict.section_path,
                conflict.field_name,
                conflict.resolution.value if conflict.resolution else "pending",
                status,
            )

        console.print(conflicts_table)

    # Handle unresolved conflicts
    if resolution.unresolved > 0:
        print_warning(f"{resolution.unresolved} conflict(s) require manual resolution")
        if not no_interactive:
            from rich.prompt import Confirm

            if not Confirm.ask("Continue with manual resolution?", default=True):
                print_info("Merge cancelled")
                raise typer.Exit(0)

            # Interactive resolution for each conflict
            for conflict in resolution.conflicts:
                if conflict.resolution == MergeStrategy.MANUAL:
                    print_section(f"Resolving conflict: {conflict.field_name}")
                    print_info(f"Base: {conflict.base_value}")
                    print_info(f"Ours ({persona_ours}): {conflict.ours_value}")
                    print_info(f"Theirs ({persona_theirs}): {conflict.theirs_value}")

                    from rich.prompt import Prompt

                    choice = Prompt.ask(
                        "Choose resolution",
                        choices=["ours", "theirs", "base", "manual"],
                        default="ours",
                    )

                    if choice == "ours":
                        conflict.resolution = MergeStrategy.OURS
                        conflict.resolved_value = conflict.ours_value
                    elif choice == "theirs":
                        conflict.resolution = MergeStrategy.THEIRS
                        conflict.resolved_value = conflict.theirs_value
                    elif choice == "base":
                        conflict.resolution = MergeStrategy.BASE
                        conflict.resolved_value = conflict.base_value
                    else:
                        # Manual edit - prompt for value
                        manual_value = Prompt.ask("Enter manual value")
                        conflict.resolution = MergeStrategy.MANUAL
                        conflict.resolved_value = manual_value

                    # Apply resolution
                    resolver._apply_resolution(resolution.merged_bundle, conflict.field_name, conflict.resolved_value)

    # Save merged bundle
    output_dir = output if output else bundle_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    _save_bundle_with_progress(resolution.merged_bundle, output_dir, atomic=True)
    print_success(f"Merged bundle saved to {output_dir}")


@app.command("resolve-conflict")
@beartype
@require(lambda repo: isinstance(repo, Path), "Repository path must be Path")
@ensure(lambda result: result is None, "Must return None")
def resolve_conflict(
    # Target/Input
    repo: Path = typer.Option(
        Path("."),
        "--repo",
        help="Path to repository",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    bundle: str | None = typer.Option(
        None,
        "--bundle",
        help="Project bundle name (e.g., legacy-api). If not specified, attempts to auto-detect or prompt.",
    ),
    conflict_path: str = typer.Option(..., "--path", help="Conflict path (e.g., 'features.FEATURE-001.title')"),
    resolution: str = typer.Option(..., "--resolution", help="Resolution: ours, theirs, base, or manual value"),
    persona: str | None = typer.Option(
        None, "--persona", help="Persona resolving the conflict (for ownership validation)"
    ),
    # Behavior/Options
    no_interactive: bool = typer.Option(
        False,
        "--no-interactive",
        help="Non-interactive mode (for CI/CD automation). Disables interactive prompts.",
    ),
) -> None:
    """
    Resolve a specific conflict in a project bundle.

    Helper command for manually resolving individual conflicts after a merge operation.

    **Parameter Groups:**
    - **Target/Input**: --repo, --bundle, --path, --resolution, --persona
    - **Behavior/Options**: --no-interactive

    **Examples:**
        specfact project resolve-conflict --path features.FEATURE-001.title --resolution ours
        specfact project resolve-conflict --bundle legacy-api --path idea.intent --resolution theirs --persona product-owner
    """
    # Get bundle name
    if bundle is None:
        bundle = SpecFactStructure.get_active_bundle_name(repo)
        if bundle is None and not no_interactive:
            from rich.prompt import Prompt

            plans = SpecFactStructure.list_plans(repo)
            if not plans:
                print_error("No project bundles found")
                raise typer.Exit(1)
            bundle_names = [str(p["name"]) for p in plans if p.get("name")]
            if not bundle_names:
                print_error("No valid bundle names found")
                raise typer.Exit(1)
            bundle = Prompt.ask("Select bundle", choices=bundle_names)
        elif bundle is None:
            print_error("Bundle not specified and no active bundle found")
            raise typer.Exit(1)

    if bundle is None:
        print_error("Bundle not specified")
        raise typer.Exit(1)

    bundle_dir = SpecFactStructure.project_dir(base_path=repo, bundle_name=bundle)
    if not bundle_dir.exists():
        print_error(f"Project bundle not found: {bundle_dir}")
        raise typer.Exit(1)

    bundle_obj = _load_bundle_with_progress(bundle_dir, validate_hashes=False)

    # Parse resolution
    from specfact_cli.merge.resolver import PersonaMergeResolver

    resolver = PersonaMergeResolver()

    # Determine value based on resolution strategy
    if resolution.lower() in ("ours", "theirs", "base"):
        print_warning("Resolution strategy 'ours', 'theirs', or 'base' requires merge context")
        print_info("Use 'specfact project merge' for full merge resolution")
        raise typer.Exit(1)

    # Manual value provided
    resolved_value = resolution

    # Apply resolution
    resolver._apply_resolution(bundle_obj, conflict_path, resolved_value)

    # Save bundle
    _save_bundle_with_progress(bundle_obj, bundle_dir, atomic=True)
    print_success(f"Conflict resolved: {conflict_path} = {resolved_value}")


# -----------------------------
# Version management subcommands
# -----------------------------


@version_app.command("check")
@beartype
@require(lambda repo: isinstance(repo, Path), "Repository path must be Path")
@ensure(lambda result: result is None, "Must return None")
def version_check(
    # Target/Input
    repo: Path = typer.Option(
        Path("."),
        "--repo",
        help="Path to repository",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    bundle: str | None = typer.Option(
        None,
        "--bundle",
        help="Project bundle name (e.g., legacy-api). If not specified, uses active bundle from config.",
    ),
) -> None:
    """
    Analyze bundle changes and recommend version bump (major/minor/patch/none).
    """
    bundle_name, bundle_dir = _resolve_bundle(repo, bundle)
    bundle_obj = _load_bundle_with_progress(bundle_dir, validate_hashes=False)

    analyzer = ChangeAnalyzer(repo_path=repo)
    analysis = analyzer.analyze(bundle_dir, bundle=bundle_obj)

    print_section(f"Version analysis for bundle '{bundle_name}'")
    print_info(f"Recommended bump: {analysis.recommended_bump}")
    print_info(f"Change type: {analysis.change_type.value}")

    if analysis.changed_files:
        table = Table(title="Bundle changes")
        table.add_column("Path", style="cyan")
        for path in sorted(set(analysis.changed_files)):
            table.add_row(path)
        console.print(table)
    else:
        print_info("No bundle file changes detected.")

    if analysis.reasons:
        print_section("Reasons")
        for reason in analysis.reasons:
            console.print(f"- {reason}")

    if analysis.content_hash:
        print_info(f"Current bundle hash: {analysis.content_hash[:8]}...")


@version_app.command("bump")
@beartype
@require(lambda repo: isinstance(repo, Path), "Repository path must be Path")
@require(lambda bump_type: bump_type in {"major", "minor", "patch"}, "Bump type must be major|minor|patch")
@ensure(lambda result: result is None, "Must return None")
def version_bump(
    # Target/Input
    repo: Path = typer.Option(
        Path("."),
        "--repo",
        help="Path to repository",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    bundle: str | None = typer.Option(
        None,
        "--bundle",
        help="Project bundle name (e.g., legacy-api). If not specified, uses active bundle from config.",
    ),
    bump_type: str = typer.Option(
        ...,
        "--type",
        help="Version bump type: major | minor | patch",
        case_sensitive=False,
    ),
) -> None:
    """
    Bump project version in bundle manifest (SemVer).
    """
    bump_type = bump_type.lower()
    bundle_name, bundle_dir = _resolve_bundle(repo, bundle)

    analyzer = ChangeAnalyzer(repo_path=repo)
    bundle_obj = _load_bundle_with_progress(bundle_dir, validate_hashes=False)
    analysis = analyzer.analyze(bundle_dir, bundle=bundle_obj)
    current_version = bundle_obj.manifest.versions.project
    new_version = bump_version(current_version, bump_type)

    # Warn if selected bump is lower than recommended
    if BUMP_SEVERITY.get(analysis.recommended_bump, 0) > BUMP_SEVERITY.get(bump_type, 0):
        print_warning(
            f"Recommended bump is '{analysis.recommended_bump}' based on detected changes, "
            f"but '{bump_type}' was requested."
        )

    project_metadata = bundle_obj.manifest.project_metadata or ProjectMetadata(stability="alpha")
    project_metadata.version_history.append(
        ChangeAnalyzer.create_history_entry(current_version, new_version, bump_type)
    )
    bundle_obj.manifest.project_metadata = project_metadata
    bundle_obj.manifest.versions.project = new_version

    # Record current content hash to support future comparisons
    summary = bundle_obj.compute_summary(include_hash=True)
    if summary.content_hash:
        bundle_obj.manifest.bundle["content_hash"] = summary.content_hash

    _save_bundle_with_progress(bundle_obj, bundle_dir, atomic=True)
    print_success(f"Bumped project version to {new_version} for bundle '{bundle_name}'")


@version_app.command("set")
@beartype
@require(lambda repo: isinstance(repo, Path), "Repository path must be Path")
@ensure(lambda result: result is None, "Must return None")
def version_set(
    # Target/Input
    repo: Path = typer.Option(
        Path("."),
        "--repo",
        help="Path to repository",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    bundle: str | None = typer.Option(
        None,
        "--bundle",
        help="Project bundle name (e.g., legacy-api). If not specified, uses active bundle from config.",
    ),
    version: str = typer.Option(..., "--version", help="Exact SemVer to set (e.g., 1.2.3)"),
) -> None:
    """
    Set explicit project version in bundle manifest.
    """
    bundle_name, bundle_dir = _resolve_bundle(repo, bundle)
    bundle_obj = _load_bundle_with_progress(bundle_dir, validate_hashes=False)
    current_version = bundle_obj.manifest.versions.project

    # Validate version before loading full bundle again for save
    validate_semver(version)

    project_metadata = bundle_obj.manifest.project_metadata or ProjectMetadata(stability="alpha")
    project_metadata.version_history.append(ChangeAnalyzer.create_history_entry(current_version, version, "set"))
    bundle_obj.manifest.project_metadata = project_metadata
    bundle_obj.manifest.versions.project = version

    summary = bundle_obj.compute_summary(include_hash=True)
    if summary.content_hash:
        bundle_obj.manifest.bundle["content_hash"] = summary.content_hash

    _save_bundle_with_progress(bundle_obj, bundle_dir, atomic=True)
    print_success(f"Set project version to {version} for bundle '{bundle_name}'")

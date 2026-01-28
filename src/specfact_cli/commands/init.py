"""
Init command - Initialize SpecFact for IDE integration.

This module provides the `specfact init` command to copy prompt templates
to IDE-specific locations for slash command integration.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import typer
from beartype import beartype
from icontract import ensure, require
from rich.console import Console
from rich.panel import Panel

from specfact_cli.runtime import debug_log_operation, debug_print, is_debug_mode
from specfact_cli.telemetry import telemetry
from specfact_cli.utils.env_manager import EnvManager, build_tool_command, detect_env_manager
from specfact_cli.utils.ide_setup import (
    IDE_CONFIG,
    copy_templates_to_ide,
    detect_ide,
    find_package_resources_path,
    get_package_installation_locations,
)


def _copy_backlog_field_mapping_templates(repo_path: Path, force: bool, console: Console) -> None:
    """
    Copy backlog field mapping templates to .specfact/templates/backlog/field_mappings/.

    Args:
        repo_path: Repository path
        force: Whether to overwrite existing files
        console: Rich console for output
    """
    import shutil

    # Find backlog field mapping templates directory
    # Priority order:
    # 1. Development: relative to project root (resources/templates/backlog/field_mappings)
    # 2. Installed package: use importlib.resources to find package location
    templates_dir: Path | None = None

    # Try 1: Development mode - relative to repo root
    dev_templates_dir = (repo_path / "resources" / "templates" / "backlog" / "field_mappings").resolve()
    if dev_templates_dir.exists():
        templates_dir = dev_templates_dir
    else:
        # Try 2: Installed package - use importlib.resources
        try:
            import importlib.resources

            resources_ref = importlib.resources.files("specfact_cli")
            templates_ref = resources_ref / "resources" / "templates" / "backlog" / "field_mappings"
            package_templates_dir = Path(str(templates_ref)).resolve()
            if package_templates_dir.exists():
                templates_dir = package_templates_dir
        except Exception:
            # Fallback: try importlib.util.find_spec()
            try:
                import importlib.util

                spec = importlib.util.find_spec("specfact_cli")
                if spec and spec.origin:
                    package_root = Path(spec.origin).parent.resolve()
                    package_templates_dir = (
                        package_root / "resources" / "templates" / "backlog" / "field_mappings"
                    ).resolve()
                    if package_templates_dir.exists():
                        templates_dir = package_templates_dir
            except Exception:
                pass

    if not templates_dir or not templates_dir.exists():
        # Templates not found - this is not critical, just skip
        debug_print("[dim]Debug:[/dim] Backlog field mapping templates not found, skipping copy")
        return

    # Create target directory
    target_dir = repo_path / ".specfact" / "templates" / "backlog" / "field_mappings"
    target_dir.mkdir(parents=True, exist_ok=True)

    # Copy templates (ado_*.yaml files)
    template_files = list(templates_dir.glob("ado_*.yaml"))
    copied_count = 0

    for template_file in template_files:
        target_file = target_dir / template_file.name
        if target_file.exists() and not force:
            continue  # Skip if file exists and --force not used
        try:
            shutil.copy2(template_file, target_file)
            copied_count += 1
        except Exception as e:
            console.print(f"[yellow]⚠[/yellow] Failed to copy {template_file.name}: {e}")

    if copied_count > 0:
        console.print(
            f"[green]✓[/green] Copied {copied_count} ADO field mapping template(s) to .specfact/templates/backlog/field_mappings/"
        )
    elif template_files:
        console.print("[dim]Backlog field mapping templates already exist (use --force to overwrite)[/dim]")


app = typer.Typer(help="Initialize SpecFact for IDE integration")
console = Console()


def _is_valid_repo_path(path: Path) -> bool:
    """Check if path exists and is a directory."""
    return path.exists() and path.is_dir()


@app.callback(invoke_without_command=True)
@require(lambda ide: ide in IDE_CONFIG or ide == "auto", "IDE must be valid or 'auto'")
@require(lambda repo: _is_valid_repo_path(repo), "Repo path must exist and be directory")
@ensure(lambda result: result is None, "Command should return None")
@beartype
def init(
    # Target/Input
    repo: Path = typer.Option(
        Path("."),
        "--repo",
        help="Repository path (default: current directory)",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    # Behavior/Options
    force: bool = typer.Option(
        False,
        "--force",
        help="Overwrite existing files",
    ),
    install_deps: bool = typer.Option(
        False,
        "--install-deps",
        help="Install required packages for contract enhancement (beartype, icontract, crosshair-tool, pytest) using detected environment manager",
    ),
    # Advanced/Configuration
    ide: str = typer.Option(
        "auto",
        "--ide",
        help="IDE type (auto, cursor, vscode, copilot, claude, gemini, qwen, opencode, windsurf, kilocode, auggie, roo, codebuddy, amp, q)",
        hidden=True,  # Hidden by default, shown with --help-advanced
    ),
) -> None:
    """
    Initialize SpecFact for IDE integration.

    Copies prompt templates to IDE-specific locations so slash commands work.
    This command detects the IDE type (or uses --ide flag) and copies
    SpecFact prompt templates to the appropriate directory.

    Also copies backlog field mapping templates to `.specfact/templates/backlog/field_mappings/`
    for custom ADO field mapping configuration.

    Examples:
        specfact init                    # Auto-detect IDE
        specfact init --ide cursor       # Initialize for Cursor
        specfact init --ide vscode --force  # Overwrite existing files
        specfact init --repo /path/to/repo --ide copilot
        specfact init --install-deps     # Install required packages for contract enhancement
    """
    telemetry_metadata = {
        "ide": ide,
        "force": force,
        "install_deps": install_deps,
    }

    with telemetry.track_command("init", telemetry_metadata) as record:
        # Resolve repo path
        repo_path = repo.resolve()

        # Detect IDE
        detected_ide = detect_ide(ide)
        ide_config = IDE_CONFIG[detected_ide]
        ide_name = ide_config["name"]

        console.print()
        console.print(Panel("[bold cyan]SpecFact IDE Setup[/bold cyan]", border_style="cyan"))
        console.print(f"[cyan]Repository:[/cyan] {repo_path}")
        console.print(f"[cyan]IDE:[/cyan] {ide_name} ({detected_ide})")
        console.print()

        # Check for environment manager
        env_info = detect_env_manager(repo_path)
        if env_info.manager == EnvManager.UNKNOWN:
            console.print()
            console.print(
                Panel(
                    "[bold yellow]⚠ No Compatible Environment Manager Detected[/bold yellow]",
                    border_style="yellow",
                )
            )
            console.print(
                "[yellow]SpecFact CLI works best with projects using standard Python project management tools.[/yellow]"
            )
            console.print()
            console.print("[dim]Supported tools:[/dim]")
            console.print("  - hatch (detected from [tool.hatch] in pyproject.toml)")
            console.print("  - poetry (detected from [tool.poetry] in pyproject.toml or poetry.lock)")
            console.print("  - uv (detected from [tool.uv] in pyproject.toml, uv.lock, or uv.toml)")
            console.print("  - pip (detected from requirements.txt or setup.py)")
            console.print()
            console.print(
                "[dim]Note: SpecFact CLI will still work, but commands like 'specfact repro' may use direct tool invocation.[/dim]"
            )
            console.print(
                "[dim]Consider adding a pyproject.toml with [tool.hatch], [tool.poetry], or [tool.uv] for better integration.[/dim]"
            )
            console.print()

        # Install dependencies if requested
        if install_deps:
            console.print()
            console.print(Panel("[bold cyan]Installing Required Packages[/bold cyan]", border_style="cyan"))
            if env_info.message:
                console.print(f"[dim]{env_info.message}[/dim]")

            required_packages = [
                "beartype>=0.22.4",
                "icontract>=2.7.1",
                "crosshair-tool>=0.0.97",
                "pytest>=8.4.2",
                # Sidecar validation tools
                # Note: specmatic may need separate installation (Java-based tool)
                # Users may need to install specmatic separately: https://specmatic.in/documentation/getting_started.html
            ]
            console.print("[dim]Installing packages for contract enhancement:[/dim]")
            for package in required_packages:
                console.print(f"  - {package}")

            # Build install command using environment manager detection
            install_cmd = ["pip", "install", "-U", *required_packages]
            install_cmd = build_tool_command(env_info, install_cmd)

            console.print(f"[dim]Using command: {' '.join(install_cmd)}[/dim]")

            try:
                result = subprocess.run(
                    install_cmd,
                    capture_output=True,
                    text=True,
                    check=False,
                    cwd=str(repo_path),
                    timeout=300,  # 5 minute timeout
                )

                if result.returncode == 0:
                    console.print()
                    console.print("[green]✓[/green] All required packages installed successfully")
                    record(
                        {
                            "deps_installed": True,
                            "packages_count": len(required_packages),
                            "env_manager": env_info.manager.value,
                        }
                    )
                else:
                    console.print()
                    console.print("[yellow]⚠[/yellow] Some packages failed to install")
                    console.print("[dim]Output:[/dim]")
                    if result.stdout:
                        console.print(result.stdout)
                    if result.stderr:
                        console.print(result.stderr)
                    console.print()
                    console.print("[yellow]You may need to install packages manually:[/yellow]")
                    # Provide environment-specific guidance
                    if env_info.manager == EnvManager.HATCH:
                        console.print(f"  hatch run pip install {' '.join(required_packages)}")
                    elif env_info.manager == EnvManager.POETRY:
                        console.print(f"  poetry add --dev {' '.join(required_packages)}")
                    elif env_info.manager == EnvManager.UV:
                        console.print(f"  uv pip install {' '.join(required_packages)}")
                    else:
                        console.print(f"  pip install {' '.join(required_packages)}")
                    record(
                        {
                            "deps_installed": False,
                            "error": result.stderr[:200] if result.stderr else "Unknown error",
                            "env_manager": env_info.manager.value,
                        }
                    )
            except subprocess.TimeoutExpired:
                console.print()
                console.print("[red]Error:[/red] Installation timed out after 5 minutes")
                console.print("[yellow]You may need to install packages manually:[/yellow]")
                if env_info.manager == EnvManager.HATCH:
                    console.print(f"  hatch run pip install {' '.join(required_packages)}")
                elif env_info.manager == EnvManager.POETRY:
                    console.print(f"  poetry add --dev {' '.join(required_packages)}")
                elif env_info.manager == EnvManager.UV:
                    console.print(f"  uv pip install {' '.join(required_packages)}")
                else:
                    console.print(f"  pip install {' '.join(required_packages)}")
                record({"deps_installed": False, "error": "timeout", "env_manager": env_info.manager.value})
            except FileNotFoundError:
                console.print()
                console.print("[red]Error:[/red] pip not found. Please install packages manually:")
                if env_info.manager == EnvManager.HATCH:
                    console.print(f"  hatch run pip install {' '.join(required_packages)}")
                elif env_info.manager == EnvManager.POETRY:
                    console.print(f"  poetry add --dev {' '.join(required_packages)}")
                elif env_info.manager == EnvManager.UV:
                    console.print(f"  uv pip install {' '.join(required_packages)}")
                else:
                    console.print(f"  pip install {' '.join(required_packages)}")
                record({"deps_installed": False, "error": "pip not found", "env_manager": env_info.manager.value})
            except Exception as e:
                console.print()
                console.print(f"[red]Error:[/red] Failed to install packages: {e}")
                console.print("[yellow]You may need to install packages manually:[/yellow]")
                if env_info.manager == EnvManager.HATCH:
                    console.print(f"  hatch run pip install {' '.join(required_packages)}")
                elif env_info.manager == EnvManager.POETRY:
                    console.print(f"  poetry add --dev {' '.join(required_packages)}")
                elif env_info.manager == EnvManager.UV:
                    console.print(f"  uv pip install {' '.join(required_packages)}")
                else:
                    console.print(f"  pip install {' '.join(required_packages)}")
                record({"deps_installed": False, "error": str(e), "env_manager": env_info.manager.value})
            console.print()

        # Find templates directory
        # Priority order:
        # 1. Development: relative to project root (resources/prompts)
        # 2. Installed package: use importlib.resources to find package location
        # 3. Fallback: try relative to this file (for edge cases)
        templates_dir: Path | None = None
        package_templates_dir: Path | None = None
        tried_locations: list[Path] = []

        # Try 1: Development mode - relative to repo root
        dev_templates_dir = (repo_path / "resources" / "prompts").resolve()
        tried_locations.append(dev_templates_dir)
        debug_print(f"[dim]Debug:[/dim] Trying development path: {dev_templates_dir}")
        if dev_templates_dir.exists():
            templates_dir = dev_templates_dir
            console.print(f"[green]✓[/green] Found templates at: {templates_dir}")
        else:
            debug_print("[dim]Debug:[/dim] Development path not found, trying installed package...")
            # Try 2: Installed package - use importlib.resources
            # Note: importlib is part of Python's standard library (since Python 3.1)
            # importlib.resources.files() is available since Python 3.9
            # Since we require Python >=3.11, this should always be available
            # However, we catch exceptions for robustness (minimal installations, edge cases)
            package_templates_dir = None
            try:
                import importlib.resources

                debug_print("[dim]Debug:[/dim] Using importlib.resources.files() API...")
                # Use files() API (Python 3.9+) - recommended approach
                resources_ref = importlib.resources.files("specfact_cli")
                templates_ref = resources_ref / "resources" / "prompts"
                # Convert Traversable to Path
                # Traversable objects can be converted to Path via str()
                # Use resolve() to handle Windows/Linux/macOS path differences
                package_templates_dir = Path(str(templates_ref)).resolve()
                tried_locations.append(package_templates_dir)
                debug_print(f"[dim]Debug:[/dim] Package templates path: {package_templates_dir}")
                if package_templates_dir.exists():
                    templates_dir = package_templates_dir
                    console.print(f"[green]✓[/green] Found templates at: {templates_dir}")
                else:
                    console.print("[yellow]⚠[/yellow] Package templates path exists but directory not found")
            except (ImportError, ModuleNotFoundError) as e:
                console.print(
                    f"[yellow]⚠[/yellow] importlib.resources not available or module not found: {type(e).__name__}: {e}"
                )
                debug_print("[dim]Debug:[/dim] Falling back to importlib.util.find_spec()...")
            except (TypeError, AttributeError, ValueError) as e:
                console.print(f"[yellow]⚠[/yellow] Error converting Traversable to Path: {e}")
                debug_print("[dim]Debug:[/dim] Falling back to importlib.util.find_spec()...")
            except Exception as e:
                console.print(f"[yellow]⚠[/yellow] Unexpected error with importlib.resources: {type(e).__name__}: {e}")
                debug_print("[dim]Debug:[/dim] Falling back to importlib.util.find_spec()...")

            # Fallback: importlib.util.find_spec() + comprehensive package location search
            if not templates_dir or not templates_dir.exists():
                try:
                    import importlib.util

                    debug_print("[dim]Debug:[/dim] Using importlib.util.find_spec() fallback...")
                    spec = importlib.util.find_spec("specfact_cli")
                    if spec and spec.origin:
                        # spec.origin points to __init__.py
                        # Go up to package root, then to resources/prompts
                        # Use resolve() for cross-platform compatibility
                        package_root = Path(spec.origin).parent.resolve()
                        package_templates_dir = (package_root / "resources" / "prompts").resolve()
                        tried_locations.append(package_templates_dir)
                        debug_print(f"[dim]Debug:[/dim] Package root from spec.origin: {package_root}")
                        debug_print(f"[dim]Debug:[/dim] Templates path from spec: {package_templates_dir}")
                        if package_templates_dir.exists():
                            templates_dir = package_templates_dir
                            console.print(f"[green]✓[/green] Found templates at: {templates_dir}")
                        else:
                            console.print("[yellow]⚠[/yellow] Templates path from spec not found")
                    else:
                        console.print("[yellow]⚠[/yellow] Could not find specfact_cli module spec")
                        if spec is None:
                            debug_print("[dim]Debug:[/dim] spec is None")
                        elif not spec.origin:
                            debug_print("[dim]Debug:[/dim] spec.origin is None or empty")
                except Exception as e:
                    console.print(f"[yellow]⚠[/yellow] Error with importlib.util.find_spec(): {type(e).__name__}: {e}")

            # Fallback: Comprehensive package location search (cross-platform)
            if not templates_dir or not templates_dir.exists():
                try:
                    debug_print("[dim]Debug:[/dim] Searching all package installation locations...")
                    package_locations = get_package_installation_locations("specfact_cli")
                    debug_print(f"[dim]Debug:[/dim] Found {len(package_locations)} possible package location(s)")
                    for i, loc in enumerate(package_locations, 1):
                        debug_print(f"[dim]Debug:[/dim]   {i}. {loc}")
                        # Check for resources/prompts in this package location
                        resource_path = (loc / "resources" / "prompts").resolve()
                        tried_locations.append(resource_path)
                        if resource_path.exists():
                            templates_dir = resource_path
                            console.print(f"[green]✓[/green] Found templates at: {templates_dir}")
                            break
                    if not templates_dir or not templates_dir.exists():
                        # Try using the helper function as a final attempt
                        debug_print("[dim]Debug:[/dim] Trying find_package_resources_path() helper...")
                        resource_path = find_package_resources_path("specfact_cli", "resources/prompts")
                        if resource_path and resource_path.exists():
                            tried_locations.append(resource_path)
                            templates_dir = resource_path
                            console.print(f"[green]✓[/green] Found templates at: {templates_dir}")
                        else:
                            console.print("[yellow]⚠[/yellow] Resources not found in any package location")
                except Exception as e:
                    console.print(f"[yellow]⚠[/yellow] Error searching package locations: {type(e).__name__}: {e}")

            # Try 3: Fallback - relative to this file (for edge cases)
            if not templates_dir or not templates_dir.exists():
                try:
                    debug_print("[dim]Debug:[/dim] Trying fallback: relative to __file__...")
                    # Get the directory containing this file (init.py)
                    # init.py is in: src/specfact_cli/commands/init.py
                    # Go up: commands -> specfact_cli -> src -> project root
                    current_file = Path(__file__).resolve()
                    fallback_dir = (current_file.parent.parent.parent.parent / "resources" / "prompts").resolve()
                    tried_locations.append(fallback_dir)
                    debug_print(f"[dim]Debug:[/dim] Current file: {current_file}")
                    debug_print(f"[dim]Debug:[/dim] Fallback templates path: {fallback_dir}")
                    if fallback_dir.exists():
                        templates_dir = fallback_dir
                        console.print(f"[green]✓[/green] Found templates at: {templates_dir}")
                    else:
                        console.print("[yellow]⚠[/yellow] Fallback path not found")
                except Exception as e:
                    console.print(f"[yellow]⚠[/yellow] Error with __file__ fallback: {type(e).__name__}: {e}")

        if templates_dir and templates_dir.exists() and is_debug_mode():
            debug_log_operation("template_resolution", str(templates_dir), "success")
        if not templates_dir or not templates_dir.exists():
            if is_debug_mode() and tried_locations:
                debug_log_operation(
                    "template_resolution",
                    str(tried_locations[-1]) if tried_locations else "unknown",
                    "failure",
                    error="Templates directory not found after all attempts",
                )
            console.print()
            console.print("[red]Error:[/red] Templates directory not found after all attempts")
            console.print()
            console.print("[yellow]Tried locations:[/yellow]")
            for i, location in enumerate(tried_locations, 1):
                exists = "✓" if location.exists() else "✗"
                console.print(f"  {i}. {exists} {location}")
            console.print()
            console.print("[yellow]Debug information:[/yellow]")
            console.print(f"  - Python version: {sys.version}")
            console.print(f"  - Platform: {sys.platform}")
            console.print(f"  - Current working directory: {Path.cwd()}")
            console.print(f"  - Repository path: {repo_path}")
            console.print(f"  - __file__ location: {Path(__file__).resolve()}")
            try:
                import importlib.util

                spec = importlib.util.find_spec("specfact_cli")
                if spec:
                    console.print(f"  - Module spec found: {spec}")
                    console.print(f"  - Module origin: {spec.origin}")
                    if spec.origin:
                        console.print(f"  - Module location: {Path(spec.origin).parent.resolve()}")
                else:
                    console.print("  - Module spec: Not found")
            except Exception as e:
                console.print(f"  - Error checking module spec: {e}")
            console.print()
            console.print("[yellow]Expected location:[/yellow] resources/prompts/")
            console.print("[yellow]Please ensure SpecFact is properly installed.[/yellow]")
            raise typer.Exit(1)

        console.print(f"[cyan]Templates:[/cyan] {templates_dir}")
        console.print()

        # Copy templates to IDE location
        try:
            copied_files, settings_path = copy_templates_to_ide(repo_path, detected_ide, templates_dir, force)

            if not copied_files:
                console.print(
                    "[yellow]No templates copied (all files already exist, use --force to overwrite)[/yellow]"
                )
                record({"files_copied": 0, "already_exists": True})
                raise typer.Exit(0)

            record(
                {
                    "detected_ide": detected_ide,
                    "files_copied": len(copied_files),
                    "settings_updated": settings_path is not None,
                }
            )

            console.print()
            console.print(Panel("[bold green]✓ Initialization Complete[/bold green]", border_style="green"))
            console.print(f"[green]Copied {len(copied_files)} template(s) to {ide_config['folder']}[/green]")
            if settings_path:
                console.print(f"[green]Updated VS Code settings:[/green] {settings_path}")
            console.print()

            # Copy backlog field mapping templates
            _copy_backlog_field_mapping_templates(repo_path, force, console)

            console.print()
            console.print("[dim]You can now use SpecFact slash commands in your IDE![/dim]")
            console.print("[dim]Example: /specfact.01-import --bundle legacy-api --repo .[/dim]")

        except Exception as e:
            console.print(f"[red]Error:[/red] Failed to initialize IDE integration: {e}")
            raise typer.Exit(1) from e

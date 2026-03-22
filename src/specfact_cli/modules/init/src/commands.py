"""Init commands for bootstrap and IDE setup."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import click
import typer
from beartype import beartype
from icontract import ensure, require
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table

from specfact_cli import __version__
from specfact_cli.contracts.module_interface import ModuleIOContract
from specfact_cli.modules import module_io_shim
from specfact_cli.modules.init.src import first_run_selection
from specfact_cli.registry.help_cache import run_discovery_and_write_cache
from specfact_cli.registry.module_installer import USER_MODULES_ROOT as INIT_USER_MODULES_ROOT
from specfact_cli.registry.module_packages import get_discovered_modules_for_state
from specfact_cli.registry.module_state import write_modules_state
from specfact_cli.runtime import debug_log_operation, debug_print, is_debug_mode, is_non_interactive
from specfact_cli.telemetry import telemetry
from specfact_cli.utils.env_manager import EnvManager, EnvManagerInfo, build_tool_command, detect_env_manager
from specfact_cli.utils.ide_setup import (
    IDE_CONFIG,
    SPECFACT_COMMANDS,
    copy_templates_to_ide,
    detect_ide,
    find_package_resources_path,
)


VALID_PROFILES: frozenset[str] = frozenset(
    {
        "solo-developer",
        "backlog-team",
        "api-first-team",
        "enterprise-full-stack",
    }
)
PROFILE_BUNDLES: dict[str, list[str]] = first_run_selection.PROFILE_PRESETS

install_bundles_for_init = first_run_selection.install_bundles_for_init
is_first_run = first_run_selection.is_first_run


def _resolve_field_mapping_templates_dir(repo_path: Path) -> Path | None:
    """Locate backlog field mapping templates (dev checkout or installed package)."""
    dev_templates_dir = (repo_path / "resources" / "templates" / "backlog" / "field_mappings").resolve()
    if dev_templates_dir.exists():
        return dev_templates_dir
    try:
        import importlib.resources

        resources_ref = importlib.resources.files("specfact_cli")
        templates_ref = resources_ref / "resources" / "templates" / "backlog" / "field_mappings"
        package_templates_dir = Path(str(templates_ref)).resolve()
        if package_templates_dir.exists():
            return package_templates_dir
    except Exception:
        try:
            import importlib.util

            spec = importlib.util.find_spec("specfact_cli")
            if spec and spec.origin:
                package_root = Path(spec.origin).parent.resolve()
                package_templates_dir = (
                    package_root / "resources" / "templates" / "backlog" / "field_mappings"
                ).resolve()
                if package_templates_dir.exists():
                    return package_templates_dir
        except Exception:
            pass
    return None


def _copy_backlog_field_mapping_templates(repo_path: Path, force: bool, console: Console) -> None:
    """
    Copy backlog field mapping templates to .specfact/templates/backlog/field_mappings/.

    Args:
        repo_path: Repository path
        force: Whether to overwrite existing files
        console: Rich console for output
    """
    import shutil

    templates_dir = _resolve_field_mapping_templates_dir(repo_path)

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


app = typer.Typer(help="Bootstrap SpecFact (use `init ide` for IDE setup; module lifecycle is under `specfact module`)")
console = Console()
_MODULE_IO_CONTRACT = ModuleIOContract
import_to_bundle = module_io_shim.import_to_bundle
export_from_bundle = module_io_shim.export_from_bundle
sync_with_bundle = module_io_shim.sync_with_bundle
validate_bundle = module_io_shim.validate_bundle


def _install_contract_enhancement_dependencies(repo_path: Path, env_info: EnvManagerInfo) -> None:
    """Install contract enhancement dependencies in the detected environment."""
    required_packages = [
        "beartype>=0.22.4",
        "icontract>=2.7.1",
        "crosshair-tool>=0.0.97",
        "pytest>=8.4.2",
    ]
    install_cmd = build_tool_command(env_info, ["pip", "install", "-U", *required_packages])
    result = subprocess.run(
        install_cmd,
        capture_output=True,
        text=True,
        check=False,
        cwd=str(repo_path),
        timeout=300,
    )
    if result.returncode == 0:
        console.print("[green]✓[/green] Dependencies installed")
    else:
        console.print("[yellow]⚠[/yellow] Dependency installation reported issues")


def _questionary_style() -> Any:
    """Return a shared questionary color theme for interactive selectors."""
    try:
        import questionary  # type: ignore[reportMissingImports]
    except ImportError:
        return None
    return questionary.Style(
        [
            ("qmark", "fg:#00af87 bold"),
            ("question", "bold"),
            ("answer", "fg:#00af87 bold"),
            ("pointer", "fg:#5f87ff bold"),
            ("highlighted", "fg:#5f87ff bold"),
            ("selected", "fg:#00af87 bold"),
            ("instruction", "fg:#808080 italic"),
            ("separator", "fg:#808080"),
            ("text", ""),
            ("disabled", "fg:#6c6c6c"),
        ]
    )


def _render_modules_table(modules_list: list[dict[str, Any]]) -> None:
    """Render discovered modules with effective enabled/disabled state."""
    table = Table(title="Installed Modules")
    table.add_column("Module", style="cyan")
    table.add_column("Version", style="magenta")
    table.add_column("State", style="green")
    for module in modules_list:
        module_id = str(module.get("id", ""))
        version = str(module.get("version", ""))
        enabled = bool(module.get("enabled", True))
        state = "enabled" if enabled else "disabled"
        table.add_row(module_id, version, state)
    console.print(table)


def _module_checkbox_rows(candidates: list[dict[str, Any]]) -> tuple[dict[str, str], list[str]]:
    display_to_id: dict[str, str] = {}
    choices: list[str] = []
    for module in candidates:
        module_id = str(module.get("id", ""))
        version = str(module.get("version", ""))
        state = "enabled" if bool(module.get("enabled", True)) else "disabled"
        marker = "✗" if state == "disabled" else "✓"
        display = f"{marker} {module_id:<14}  [{state}]  v{version}"
        display_to_id[display] = module_id
        choices.append(display)
    return display_to_id, choices


def _run_module_checkbox_prompt(
    action: str,
    display_to_id: dict[str, str],
    choices: list[str],
    questionary: Any,
) -> list[str]:
    action_title = "Enable" if action == "enable" else "Disable"
    current_state = "disabled" if action == "enable" else "enabled"
    selected: list[str] | None = questionary.checkbox(
        f"{action_title} module(s) from currently {current_state}:",
        choices=choices,
        instruction="(multi-select)",
        style=_questionary_style(),
    ).ask()
    if not selected:
        return []
    return [display_to_id[s] for s in selected if s in display_to_id]


def _select_module_ids_interactive(action: str, modules_list: list[dict[str, Any]]) -> list[str]:
    """Select one or more module IDs interactively via arrow-key checkbox menu."""
    try:
        import questionary  # type: ignore[reportMissingImports]
    except ImportError as e:
        console.print(
            "[red]Interactive module selection requires 'questionary'. Install with: pip install questionary[/red]"
        )
        raise typer.Exit(1) from e

    target_enabled = action == "disable"
    candidates = [m for m in modules_list if bool(m.get("enabled", True)) is target_enabled]
    if not candidates:
        console.print(f"[yellow]No modules available to {action}.[/yellow]")
        return []

    action_title = "Enable" if action == "enable" else "Disable"
    current_state = "disabled" if action == "enable" else "enabled"
    console.print()
    console.print(
        Panel(
            f"[bold cyan]{action_title} Modules[/bold cyan]\n"
            f"Choose one or more currently [bold]{current_state}[/bold] modules.",
            border_style="cyan",
        )
    )
    console.print(
        "[dim]Controls: ↑↓ navigate • Space toggle • Enter confirm • Type to search/filter • Ctrl+C cancel[/dim]"
    )

    display_to_id, choices = _module_checkbox_rows(candidates)
    return _run_module_checkbox_prompt(action, display_to_id, choices, questionary)


def _resolve_templates_dir(repo_path: Path) -> Path | None:
    """Resolve templates directory from repo checkout or installed package."""
    dev_templates_dir = (repo_path / "resources" / "prompts").resolve()
    if dev_templates_dir.exists():
        return dev_templates_dir
    try:
        import importlib.resources

        resources_ref = importlib.resources.files("specfact_cli")
        templates_ref = resources_ref / "resources" / "prompts"
        package_templates_dir = Path(str(templates_ref)).resolve()
        if package_templates_dir.exists():
            return package_templates_dir
    except Exception as exc:
        if is_debug_mode():
            debug_log_operation(
                "template_resolution",
                "importlib.resources(specfact_cli/resources/prompts)",
                "error",
                error=repr(exc),
            )
    return find_package_resources_path("specfact_cli", "resources/prompts")


def _expected_ide_prompt_basenames(format_type: str) -> list[str]:
    if format_type == "prompt.md":
        return [f"{cmd}.prompt.md" for cmd in SPECFACT_COMMANDS]
    if format_type == "toml":
        return [f"{cmd}.toml" for cmd in SPECFACT_COMMANDS]
    return [f"{cmd}.md" for cmd in SPECFACT_COMMANDS]


def _count_outdated_ide_prompts(ide_dir: Path, templates_dir: Path, format_type: str) -> int:
    outdated = 0
    for cmd in SPECFACT_COMMANDS:
        src = templates_dir / f"{cmd}.md"
        if format_type == "prompt.md":
            dest = ide_dir / f"{cmd}.prompt.md"
        elif format_type == "toml":
            dest = ide_dir / f"{cmd}.toml"
        else:
            dest = ide_dir / f"{cmd}.md"
        if src.exists() and dest.exists() and dest.stat().st_mtime < src.stat().st_mtime:
            outdated += 1
    return outdated


def _audit_prompt_installation(repo_path: Path) -> None:
    """Report prompt installation health and next steps without mutating files."""
    detected_ide = detect_ide("auto")
    config = IDE_CONFIG[detected_ide]
    ide_dir = repo_path / str(config["folder"])
    format_type = str(config["format"])
    expected_files = _expected_ide_prompt_basenames(format_type)

    if not ide_dir.exists():
        console.print(
            f"[yellow]Prompt status:[/yellow] no prompts found for detected IDE ({detected_ide}). "
            f"Run [bold]specfact init ide --ide {detected_ide}[/bold]."
        )
        return

    missing = [name for name in expected_files if not (ide_dir / name).exists()]
    templates_dir = _resolve_templates_dir(repo_path)
    outdated = _count_outdated_ide_prompts(ide_dir, templates_dir, format_type) if templates_dir else 0

    if not missing and outdated == 0:
        console.print(f"[green]Prompt status:[/green] {detected_ide} prompts are present and up to date.")
        return

    console.print(
        f"[yellow]Prompt status:[/yellow] missing={len(missing)}, outdated={outdated} for detected IDE ({detected_ide})."
    )
    console.print(f"[dim]Run: specfact init ide --ide {detected_ide}{' --force' if outdated > 0 else ''}[/dim]")


def _select_ide_interactive(default_ide: str) -> str:
    """Select IDE interactively with up/down controls."""
    try:
        import questionary  # type: ignore[reportMissingImports]
    except ImportError as e:
        console.print(
            "[red]Interactive IDE selection requires 'questionary'. Install with: pip install questionary[/red]"
        )
        raise typer.Exit(1) from e

    choices: list[str] = []
    label_to_ide: dict[str, str] = {}
    console.print()
    console.print(
        Panel(
            "[bold cyan]IDE Prompt Setup[/bold cyan]\nSelect your editor/assistant integration target.",
            border_style="cyan",
        )
    )
    console.print("[dim]Controls: ↑↓ navigate • Enter select • Type to filter • Ctrl+C cancel[/dim]")
    for ide_id, cfg in IDE_CONFIG.items():
        default_marker = "★" if ide_id == default_ide else " "
        label = f"{default_marker} {cfg['name']:<24} ({ide_id})"
        label_to_ide[label] = ide_id
        choices.append(label)

    default_label = next((lbl for lbl, iid in label_to_ide.items() if iid == default_ide), choices[0])
    selected = questionary.select(
        "Select IDE for prompt setup",
        choices=choices,
        default=default_label,
        style=_questionary_style(),
    ).ask()
    if not selected:
        raise typer.Exit(1)
    console.print(Rule(style="dim"))
    return label_to_ide[str(selected)]


def _is_valid_repo_path(repo: Path) -> bool:
    """Check if path exists and is a directory."""
    return repo.exists() and repo.is_dir()


@beartype
def _install_profile_bundles(profile: str, install_root: Path, non_interactive: bool) -> None:
    """Resolve profile to bundle list and install via module installer."""
    bundle_ids = first_run_selection.resolve_profile_bundles(profile)
    if bundle_ids:
        install_bundles_for_init(
            bundle_ids,
            install_root,
            non_interactive=non_interactive,
        )


@beartype
def _install_bundle_list(install_arg: str, install_root: Path, non_interactive: bool) -> None:
    """Parse comma-separated or 'all' and install bundles via module installer."""
    bundle_ids = first_run_selection.resolve_install_bundles(install_arg)
    if bundle_ids:
        install_bundles_for_init(
            bundle_ids,
            install_root,
            non_interactive=non_interactive,
        )


def _apply_profile_or_install_bundles(profile: str | None, install: str | None) -> None:
    try:
        non_interactive = is_non_interactive()
        if profile is not None:
            _install_profile_bundles(profile, INIT_USER_MODULES_ROOT, non_interactive=non_interactive)
        else:
            _install_bundle_list(install or "", INIT_USER_MODULES_ROOT, non_interactive=non_interactive)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e


def _run_interactive_first_run_install() -> None:
    try:
        bundle_ids = _interactive_first_run_bundle_selection()
        if bundle_ids:
            first_run_selection.install_bundles_for_init(
                bundle_ids,
                INIT_USER_MODULES_ROOT,
                non_interactive=False,
            )
        else:
            console.print(
                "[dim]Tip: Install bundles later with "
                "`specfact module install <bundle>` or `specfact init --profile <name>`[/dim]"
            )
    except typer.Exit:
        raise
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e


def _manual_bundle_ids_from_questionary(questionary: Any) -> list[str]:
    bundle_choices = [
        f"{first_run_selection.BUNDLE_DISPLAY.get(bid, bid)}  [dim]({bid})[/dim]"
        for bid in first_run_selection.CANONICAL_BUNDLES
    ]
    selected = questionary.checkbox(
        "Select bundles to install:",
        choices=bundle_choices,
        style=_questionary_style(),
    ).ask()
    if not selected:
        return []
    return [bid for bid in first_run_selection.CANONICAL_BUNDLES if any(bid in s for s in selected)]


def _bundle_ids_for_first_run_choice(choice: str, profile_to_key: dict[str, str], questionary: Any) -> list[str]:
    if choice in profile_to_key:
        key = profile_to_key[choice]
        if key == "_manual_":
            return _manual_bundle_ids_from_questionary(questionary)
        return list(first_run_selection.PROFILE_PRESETS.get(key, []))

    for key, label in first_run_selection.PROFILE_DISPLAY_ORDER:
        if choice.startswith(label) or f"({key})" in choice:
            return list(first_run_selection.PROFILE_PRESETS.get(key, []))
    return []


def _interactive_first_run_bundle_selection() -> list[str]:
    """Show first-run welcome and bundle selection; return list of canonical bundle ids to install (or empty)."""
    try:
        import questionary  # type: ignore[reportMissingImports]
    except ImportError as e:
        console.print(
            "[red]Interactive bundle selection requires 'questionary'. Install with: pip install questionary[/red]"
        )
        raise typer.Exit(1) from e

    console.print()
    console.print(
        Panel(
            "[bold cyan]Welcome to SpecFact[/bold cyan]\n"
            "Choose which workflow bundles to install. Core commands (init, module, upgrade) are always available.",
            border_style="cyan",
        )
    )
    console.print("[dim]You can install more later with `specfact module install <bundle>`[/dim]")
    console.print()

    profile_choices = [f"{label}  [dim]({key})[/dim]" for key, label in first_run_selection.PROFILE_DISPLAY_ORDER]
    profile_to_key = {f"{label}  [dim]({key})[/dim]": key for key, label in first_run_selection.PROFILE_DISPLAY_ORDER}
    profile_to_key["Choose bundles manually"] = "_manual_"

    choice = questionary.select(
        "Select a profile or choose bundles manually:",
        choices=[*profile_choices, "Choose bundles manually"],
        style=_questionary_style(),
    ).ask()

    if not choice:
        return []

    return _bundle_ids_for_first_run_choice(choice, profile_to_key, questionary)


@app.command("ide")
@require(_is_valid_repo_path, "Repo path must exist and be directory")
@ensure(lambda result: result is None, "Command should return None")
@beartype
def init_ide(
    repo: Path = typer.Option(
        Path("."),
        "--repo",
        help="Repository path (default: current directory)",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    force: bool = typer.Option(False, "--force", help="Overwrite existing files"),
    install_deps: bool = typer.Option(
        False,
        "--install-deps",
        help="Install required packages for contract enhancement (beartype, icontract, crosshair-tool, pytest)",
    ),
    ide: str | None = typer.Option(
        None,
        "--ide",
        help="IDE type (cursor, vscode, copilot, claude, gemini, qwen, opencode, windsurf, kilocode, auggie, roo, codebuddy, amp, q, auto)",
    ),
) -> None:
    """Initialize IDE prompt templates and settings."""
    repo_path = repo.resolve()
    detected_default = detect_ide("auto")
    if ide is not None:
        selected_ide = detect_ide(ide)
    elif is_non_interactive():
        selected_ide = detected_default
    else:
        selected_ide = _select_ide_interactive(detected_default)

    ide_config = IDE_CONFIG[selected_ide]
    ide_name = str(ide_config["name"])

    console.print()
    console.print(Panel("[bold cyan]SpecFact IDE Setup[/bold cyan]", border_style="cyan"))
    console.print(f"[cyan]Repository:[/cyan] {repo_path}")
    console.print(f"[cyan]IDE:[/cyan] {ide_name} ({selected_ide})")
    console.print()

    env_info = detect_env_manager(repo_path)
    if env_info.manager == EnvManager.UNKNOWN:
        console.print(
            Panel(
                "[bold yellow]⚠ No Compatible Environment Manager Detected[/bold yellow]",
                border_style="yellow",
            )
        )
        console.print("[dim]Supported tools: hatch, poetry, uv, pip[/dim]")
        console.print()

    if install_deps:
        _install_contract_enhancement_dependencies(repo_path, env_info)

    templates_dir = _resolve_templates_dir(repo_path)
    if not templates_dir or not templates_dir.exists():
        console.print("[red]Error:[/red] Templates directory not found.")
        raise typer.Exit(1)

    console.print(f"[cyan]Templates:[/cyan] {templates_dir}")
    copied_files, settings_path = copy_templates_to_ide(repo_path, selected_ide, templates_dir, force)
    _copy_backlog_field_mapping_templates(repo_path, force, console)

    console.print()
    console.print(Panel("[bold green]✓ IDE Initialization Complete[/bold green]", border_style="green"))
    console.print(f"[green]Copied {len(copied_files)} template(s) to {ide_config['folder']}[/green]")
    if settings_path:
        console.print(f"[green]Updated VS Code settings:[/green] {settings_path}")


@app.callback(invoke_without_command=True)
@require(lambda repo: _is_valid_repo_path(repo), "Repo path must exist and be directory")
@ensure(lambda result: result is None, "Command should return None")
@beartype
def init(
    ctx: click.Context,
    repo: Path = typer.Option(
        Path("."),
        "--repo",
        help="Repository path (default: current directory)",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    profile: str | None = typer.Option(
        None,
        "--profile",
        help="First-run profile preset: solo-developer, backlog-team, api-first-team, enterprise-full-stack",
    ),
    install: str | None = typer.Option(
        None,
        "--install",
        help="Comma-separated bundle names or 'all' to install without prompting",
    ),
    install_deps: bool = typer.Option(
        False,
        "--install-deps",
        help=(
            "Install required packages for contract enhancement. Prefer `specfact init ide --install-deps` "
            "for IDE setup flow."
        ),
    ),
) -> None:
    """Bootstrap SpecFact local state."""
    with telemetry.track_command("init", {"install_deps": install_deps}) as _record:
        if ctx.invoked_subcommand is not None:
            return

        repo_path = repo.resolve()

        if profile is not None or install is not None:
            _apply_profile_or_install_bundles(profile, install)
        elif is_first_run(user_root=INIT_USER_MODULES_ROOT) and is_non_interactive():
            console.print(
                "[red]Error:[/red] In CI/CD (non-interactive) mode, first-run init requires "
                "--profile or --install to select workflow bundles."
            )
            console.print(
                "[dim]Example: specfact init --repo . --profile solo-developer "
                "or specfact init --repo . --install all[/dim]"
            )
            raise typer.Exit(1)
        elif is_first_run(user_root=INIT_USER_MODULES_ROOT) and not is_non_interactive():
            _run_interactive_first_run_install()

        modules_list = get_discovered_modules_for_state(enable_ids=[], disable_ids=[])
        if modules_list:
            write_modules_state(modules_list)

        run_discovery_and_write_cache(__version__)

        if install_deps:
            env_info = detect_env_manager(repo_path)
            _install_contract_enhancement_dependencies(repo_path, env_info)

        enabled_count = len([m for m in modules_list if bool(m.get("enabled", True))])
        disabled_count = len(modules_list) - enabled_count
        console.print(
            f"[green]✓[/green] Bootstrap complete. Modules discovered: {len(modules_list)} "
            f"(enabled={enabled_count}, disabled={disabled_count})."
        )
        console.print(
            "[cyan]Module management has moved to `specfact module`[/cyan] "
            "[dim](for example: `specfact module list`, `specfact module init`)[/dim]"
        )
        _audit_prompt_installation(repo_path)
        console.print("[dim]Use `specfact init ide` to install/update IDE prompts and settings.[/dim]")


__all__ = [
    "app",
    "export_from_bundle",
    "import_to_bundle",
    "sync_with_bundle",
    "validate_bundle",
]

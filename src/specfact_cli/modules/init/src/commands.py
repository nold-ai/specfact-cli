"""Init commands for bootstrap and IDE setup."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any, cast

import click
import typer
from beartype import beartype
from icontract import ensure, require
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule

from specfact_cli import __version__
from specfact_cli.contracts.module_interface import ModuleIOContract
from specfact_cli.modules import module_io_shim
from specfact_cli.modules.init.src import first_run_selection
from specfact_cli.registry.help_cache import run_discovery_and_write_cache
from specfact_cli.registry.module_installer import USER_MODULES_ROOT as INIT_USER_MODULES_ROOT
from specfact_cli.registry.module_packages import get_discovered_modules_for_state
from specfact_cli.registry.module_state import write_modules_state
from specfact_cli.runtime import debug_print, is_non_interactive
from specfact_cli.telemetry import telemetry
from specfact_cli.utils.contract_predicates import repo_path_exists, repo_path_is_dir
from specfact_cli.utils.env_manager import (
    EnvManager,
    EnvManagerInfo,
    build_tool_command,
    detect_env_manager,
    env_info_from_tool_choice,
)
from specfact_cli.utils.ide_setup import (
    IDE_CONFIG,
    PROMPT_SOURCE_CORE,
    _copy_template_files_to_ide,
    _discover_module_resource_dirs,
    copy_prompts_by_source_to_ide,
    count_outdated_ide_prompt_exports,
    detect_ide,
    discover_prompt_sources_catalog,
    discover_prompt_template_files,
    expected_ide_prompt_export_paths,
    load_ide_prompt_export_source_ids,
    write_ide_prompt_export_state,
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


@beartype
@require(repo_path_exists, "Repo path must exist")
@require(repo_path_is_dir, "Repo path must be a directory")
@require(lambda ide: ide in IDE_CONFIG, "IDE must be valid")
@ensure(
    lambda result: (
        isinstance(result, tuple)
        and len(result) == 2
        and isinstance(result[0], list)
        and all(isinstance(path, Path) for path in result[0])
        and (result[1] is None or isinstance(result[1], Path))
    ),
    "Must return copied files and optional settings path",
)
def copy_templates_to_ide(
    repo_path: Path,
    ide: str,
    force: bool = False,
    *,
    prompts_by_source: dict[str, list[Path]] | None = None,
) -> tuple[list[Path], Path | None]:
    """Discover prompt templates and copy them; use ``prompts_by_source`` for multi-source flat export."""
    if prompts_by_source is not None:
        return copy_prompts_by_source_to_ide(repo_path, ide, prompts_by_source, force)
    return _copy_template_files_to_ide(repo_path, ide, discover_prompt_template_files(repo_path), force)


def _resolve_field_mapping_templates_dir(repo_path: Path) -> Path | None:
    """Locate backlog field mapping templates (dev checkout or installed package)."""
    for resource_root in _discover_module_resource_dirs(
        "resources/templates/backlog/field_mappings",
        repo_path=repo_path,
        categories={"backlog"},
    ):
        installed_templates_dir = (resource_root / "templates" / "backlog" / "field_mappings").resolve()
        if installed_templates_dir.exists():
            return installed_templates_dir

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
    except (ImportError, OSError, ValueError):
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
        except (ImportError, OSError, ValueError):
            return None
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


def _init_user_visible_step(message: str) -> None:
    """Print init progress unless running under pytest (keeps test output clean)."""
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return
    console.print(message)


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
    questionary_module = cast(Any, questionary)
    return questionary_module.Style(
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
    selected: list[str] | None = (
        cast(Any, questionary)
        .checkbox(
            f"{action_title} module(s) from currently {current_state}:",
            choices=choices,
            instruction="(multi-select)",
            style=_questionary_style(),
        )
        .ask()
    )
    if not selected:
        return []
    return [display_to_id[s] for s in selected if s in display_to_id]


def _resolve_templates_dir(repo_path: Path) -> Path | None:
    """Resolve a representative templates directory from installed modules or a dev repo checkout."""
    prompt_files = discover_prompt_template_files(repo_path, include_package_fallback=True)
    if prompt_files:
        return prompt_files[0].parent

    dev_templates_dir = (repo_path / "resources" / "prompts").resolve()
    if dev_templates_dir.exists():
        return dev_templates_dir

    return None


def _audit_prompt_installation(repo_path: Path) -> None:
    """Report prompt installation health and next steps without mutating files."""
    detected_ide = detect_ide("auto")
    config = IDE_CONFIG[detected_ide]
    ide_dir = repo_path / str(config["folder"])
    prompt_subset = load_ide_prompt_export_source_ids(repo_path, detected_ide)
    expected_paths = expected_ide_prompt_export_paths(repo_path, detected_ide, prompt_source_ids=prompt_subset)

    if not ide_dir.exists():
        console.print(
            f"[yellow]Prompt status:[/yellow] no prompts found for detected IDE ({detected_ide}). "
            f"Run [bold]specfact init ide --ide {detected_ide}[/bold]."
        )
        return

    missing = [p for p in expected_paths if not p.exists()]
    outdated = (
        count_outdated_ide_prompt_exports(repo_path, detected_ide, prompt_source_ids=prompt_subset)
        if expected_paths
        else 0
    )

    if not missing and outdated == 0:
        console.print(f"[green]Prompt status:[/green] {detected_ide} prompts are present and up to date.")
        return

    console.print(
        f"[yellow]Prompt status:[/yellow] missing={len(missing)}, outdated={outdated} for detected IDE ({detected_ide})."
    )
    console.print(f"[dim]Run: specfact init ide --ide {detected_ide}{' --force' if outdated > 0 else ''}[/dim]")


def _raise_missing_prompt_source(token: str, catalog: dict[str, list[Path]]) -> None:
    avail = ", ".join(sorted(catalog.keys()))
    console.print(f"[red]Error:[/red] Prompt source [bold]{token}[/bold] is not available or has no prompt resources.")
    console.print(f"[dim]Available sources: {avail}[/dim]")
    console.print(
        "[dim]Install modules with [bold]specfact module install --scope user|project[/bold] "
        "or seed bundled artifacts with [bold]specfact module init --scope user|project[/bold].[/dim]"
    )
    raise typer.Exit(1)


@beartype
def _parse_prompts_option_to_catalog(catalog: dict[str, list[Path]], prompts: str) -> dict[str, list[Path]]:
    tokens = [t.strip() for t in prompts.split(",") if t.strip()]
    if not tokens:
        console.print("[red]Error:[/red] --prompts must list at least one source or `all`.")
        raise typer.Exit(1)
    if len(tokens) == 1 and tokens[0].lower() == "all":
        return dict(catalog)
    result: dict[str, list[Path]] = {}
    for token in tokens:
        key = PROMPT_SOURCE_CORE if token.lower() == "core" else token
        if key not in catalog:
            _raise_missing_prompt_source(token, catalog)
        result[key] = catalog[key]
    return result


def _select_prompt_sources_interactive(catalog: dict[str, list[Path]]) -> dict[str, list[Path]]:
    keys = sorted(catalog.keys(), key=lambda k: (k != PROMPT_SOURCE_CORE, k))
    if len(keys) <= 1:
        return dict(catalog)
    try:
        import questionary  # type: ignore[reportMissingImports]
    except ImportError as e:
        console.print(
            "[red]Interactive prompt source selection requires 'questionary'. "
            "Install with: pip install questionary[/red]"
        )
        raise typer.Exit(1) from e

    console.print()
    console.print(
        Panel(
            "[bold cyan]Prompt sources[/bold cyan]\n"
            "Choose which prompt bundles to export (core and installed modules with prompt resources).",
            border_style="cyan",
        )
    )
    console.print("[dim]Controls: ↑↓ navigate • Space toggle • Enter confirm • Type to filter • Ctrl+C cancel[/dim]")

    labels = [f"{k}  ({len(catalog[k])} template(s))" for k in keys]
    label_to_key = {labels[i]: keys[i] for i in range(len(keys))}

    q = cast(Any, questionary)
    choices_with_default = [q.Choice(title=lab, checked=True) for lab in labels]
    selected = q.checkbox(
        "Select prompt sources:",
        choices=choices_with_default,
        style=_questionary_style(),
    ).ask()
    if not selected:
        console.print("[red]Error:[/red] Select at least one prompt source.")
        raise typer.Exit(1)
    chosen: dict[str, list[Path]] = {}
    for label in selected:
        sid = label_to_key.get(label)
        if sid is not None:
            chosen[sid] = catalog[sid]
    return chosen


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
    selected = (
        cast(Any, questionary)
        .select(
            "Select IDE for prompt setup",
            choices=choices,
            default=default_label,
            style=_questionary_style(),
        )
        .ask()
    )
    if not selected:
        raise typer.Exit(1)
    console.print(Rule(style="dim"))
    return label_to_ide[str(selected)]


def _is_valid_repo_path(repo: Path) -> bool:
    """Check if path exists and is a directory."""
    return repo.exists() and repo.is_dir()


@beartype
def _marketplace_ids_for_bundles(bundle_ids: list[str]) -> list[str]:
    return [
        first_run_selection.MARKETPLACE_ONLY_BUNDLES[bid]
        for bid in bundle_ids
        if bid in first_run_selection.MARKETPLACE_ONLY_BUNDLES
    ]


def _install_profile_bundles(profile: str, install_root: Path, non_interactive: bool) -> list[str]:
    """Resolve profile to bundle list and install via module installer."""
    bundle_ids = first_run_selection.resolve_profile_bundles(profile)
    if bundle_ids:
        _init_user_visible_step(f"[cyan]→[/cyan] Profile [bold]{profile}[/bold]: preparing workflow bundles…")
        install_bundles_for_init(
            bundle_ids,
            install_root,
            non_interactive=non_interactive,
        )
    return _marketplace_ids_for_bundles(bundle_ids)


@beartype
def _install_bundle_list(install_arg: str, install_root: Path, non_interactive: bool) -> list[str]:
    """Parse comma-separated or 'all' and install bundles via module installer."""
    bundle_ids = first_run_selection.resolve_install_bundles(install_arg)
    if bundle_ids:
        _init_user_visible_step("[cyan]→[/cyan] Installing bundles from [bold]--install[/bold]…")
        install_bundles_for_init(
            bundle_ids,
            install_root,
            non_interactive=non_interactive,
        )
    return _marketplace_ids_for_bundles(bundle_ids)


def _apply_profile_or_install_bundles(profile: str | None, install: str | None) -> list[str]:
    try:
        non_interactive = is_non_interactive()
        if profile is not None:
            return _install_profile_bundles(profile, INIT_USER_MODULES_ROOT, non_interactive=non_interactive)
        return _install_bundle_list(install or "", INIT_USER_MODULES_ROOT, non_interactive=non_interactive)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e


def _refresh_init_module_state(repo_path: Path, enabled_module_ids: list[str]) -> list[dict[str, Any]]:
    modules_list = get_discovered_modules_for_state(
        enable_ids=enabled_module_ids,
        disable_ids=[],
        base_path=repo_path,
        preserve_existing=True,
    )
    if modules_list:
        write_modules_state(modules_list)
    return modules_list


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
    selected = (
        cast(Any, questionary)
        .checkbox(
            "Select bundles to install:",
            choices=bundle_choices,
            style=_questionary_style(),
        )
        .ask()
    )
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

    choice = (
        cast(Any, questionary)
        .select(
            "Select a profile or choose bundles manually:",
            choices=[*profile_choices, "Choose bundles manually"],
            style=_questionary_style(),
        )
        .ask()
    )

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
    env_manager: EnvManager = typer.Option(
        EnvManager.AUTO,
        "--env-manager",
        help="Environment manager override: auto, uv, hatch, poetry, or pip",
    ),
    prompts: str | None = typer.Option(
        None,
        "--prompts",
        help=(
            "Comma-separated prompt sources: 'all', 'core', and/or module ids (e.g. nold-ai/specfact-backlog). "
            "Default: all discovered sources. Omitted in interactive mode opens a multi-select."
        ),
    ),
) -> None:
    """Initialize IDE prompt templates and settings (exports core + installed module prompts; re-sync anytime)."""
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

    env_info = (
        detect_env_manager(repo_path)
        if env_manager is EnvManager.AUTO
        else env_info_from_tool_choice(env_manager, repo_path)
    )
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

    catalog = discover_prompt_sources_catalog(repo_path)
    if not catalog:
        console.print("[red]Error:[/red] No prompt templates found.")
        console.print(
            "[dim]Seed or install modules first, e.g. [bold]specfact module init --scope project[/bold] "
            "or [bold]specfact module install --scope user[/bold].[/dim]"
        )
        raise typer.Exit(1)

    if prompts is not None:
        selected_catalog = _parse_prompts_option_to_catalog(catalog, prompts)
    elif is_non_interactive():
        selected_catalog = dict(catalog)
    else:
        selected_catalog = _select_prompt_sources_interactive(catalog)

    source_summary = ", ".join(sorted(selected_catalog.keys()))
    console.print(f"[cyan]Prompt sources:[/cyan] {source_summary}")
    copied_files, settings_path = copy_templates_to_ide(
        repo_path, selected_ide, force, prompts_by_source=selected_catalog
    )
    write_ide_prompt_export_state(repo_path, selected_ide, sorted(selected_catalog.keys()))
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

        enabled_module_ids: list[str] = []
        if profile is not None or install is not None:
            enabled_module_ids = _apply_profile_or_install_bundles(profile, install)
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

        _init_user_visible_step("[cyan]→[/cyan] Discovering installed modules and writing registry state…")
        modules_list = _refresh_init_module_state(repo_path, enabled_module_ids)

        _init_user_visible_step("[cyan]→[/cyan] Indexing CLI commands for help cache…")
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
        _init_user_visible_step("[cyan]→[/cyan] Checking IDE prompt export status…")
        _audit_prompt_installation(repo_path)
        console.print("[dim]Use `specfact init ide` to install/update IDE prompts and settings.[/dim]")


__all__ = [
    "app",
    "export_from_bundle",
    "import_to_bundle",
    "sync_with_bundle",
    "validate_bundle",
]

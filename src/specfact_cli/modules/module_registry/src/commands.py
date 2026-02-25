"""Marketplace module management CLI commands."""

from __future__ import annotations

import inspect
import shutil
from pathlib import Path

import typer
from beartype import beartype
from rich.console import Console
from rich.table import Table

from specfact_cli.modules import module_io_shim
from specfact_cli.registry.marketplace_client import fetch_registry_index
from specfact_cli.registry.module_discovery import discover_all_modules
from specfact_cli.registry.module_installer import (
    USER_MODULES_ROOT,
    get_bundled_module_metadata,
    install_bundled_module,
    install_module,
    sync_bundled_modules_to_user_root,
    uninstall_module,
)
from specfact_cli.registry.module_lifecycle import (
    apply_module_state_update,
    get_modules_with_state,
    render_modules_table,
    select_module_ids_interactive,
)
from specfact_cli.registry.module_security import ensure_publisher_trusted
from specfact_cli.registry.registry import CommandRegistry
from specfact_cli.runtime import is_non_interactive


app = typer.Typer(help="Manage marketplace modules")
console = Console()


@app.command(name="init")
@beartype
def init_modules(
    scope: str = typer.Option("user", "--scope", help="Bootstrap scope: user or project"),
    repo: Path | None = typer.Option(None, "--repo", help="Repository path for project scope (default: current dir)"),
    trust_non_official: bool = typer.Option(
        False,
        "--trust-non-official",
        help="Trust and persist non-official publishers for this bootstrap operation",
    ),
) -> None:
    """Bootstrap shipped module artifacts into user or project module root."""
    scope_normalized = scope.strip().lower()
    if scope_normalized not in {"user", "project"}:
        console.print("[red]Invalid scope. Use 'user' or 'project'.[/red]")
        raise typer.Exit(1)

    target_root = USER_MODULES_ROOT
    if scope_normalized == "project":
        repo_path = (repo or Path.cwd()).resolve()
        target_root = repo_path / ".specfact" / "modules"

    try:
        seeded = sync_bundled_modules_to_user_root(
            target_root=target_root,
            trust_non_official=trust_non_official,
            non_interactive=is_non_interactive(),
        )
    except OSError as exc:
        console.print(f"[red]Failed to seed modules into {target_root}: {exc}[/red]")
        raise typer.Exit(1) from exc
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc
    console.print(f"[green]Seeded {seeded} module(s) into {target_root}[/green]")


@app.command()
@beartype
def install(
    module_id: str = typer.Argument(..., help="Module id (name or namespace/name format)"),
    version: str | None = typer.Option(None, "--version", help="Install a specific version"),
    scope: str = typer.Option("user", "--scope", help="Install scope: user or project"),
    source: str = typer.Option("auto", "--source", help="Install source: auto, bundled, or marketplace"),
    repo: Path | None = typer.Option(None, "--repo", help="Repository path for project scope (default: current dir)"),
    trust_non_official: bool = typer.Option(
        False,
        "--trust-non-official",
        help="Trust and persist non-official publisher for this module install",
    ),
) -> None:
    """Install a module from bundled artifacts or marketplace registry."""
    scope_normalized = scope.strip().lower()
    if scope_normalized not in {"user", "project"}:
        console.print("[red]Invalid scope. Use 'user' or 'project'.[/red]")
        raise typer.Exit(1)
    source_normalized = source.strip().lower()
    if source_normalized not in {"auto", "bundled", "marketplace"}:
        console.print("[red]Invalid source. Use 'auto', 'bundled', or 'marketplace'.[/red]")
        raise typer.Exit(1)

    repo_path = (repo or Path.cwd()).resolve()
    target_root = USER_MODULES_ROOT if scope_normalized == "user" else repo_path / ".specfact" / "modules"

    normalized = module_id if "/" in module_id else f"specfact/{module_id}"
    if normalized.count("/") != 1:
        console.print("[red]Invalid module id. Use 'name' or 'namespace/name'.[/red]")
        raise typer.Exit(1)

    requested_name = normalized.split("/", 1)[1]
    if (target_root / requested_name / "module-package.yaml").exists():
        console.print(f"[yellow]Module '{requested_name}' is already installed in {target_root}.[/yellow]")
        return

    discovered_by_name = {entry.metadata.name: entry for entry in discover_all_modules()}
    existing = discovered_by_name.get(requested_name)
    skip_sources = {"builtin", "project", "user", "custom"}
    if scope_normalized == "project":
        skip_sources.discard("user")
    if scope_normalized == "user":
        skip_sources.discard("project")
    if existing is not None and existing.source in skip_sources:
        console.print(
            f"[yellow]Module '{requested_name}' is already available from source '{existing.source}'. "
            "No marketplace install needed.[/yellow]"
        )
        return

    try:
        if source_normalized in {"auto", "bundled"} and install_bundled_module(
            requested_name,
            target_root=target_root,
            trust_non_official=trust_non_official,
            non_interactive=is_non_interactive(),
        ):
            console.print(f"[green]Installed bundled module[/green] {requested_name} -> {target_root / requested_name}")
            return
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc
    if source_normalized == "bundled":
        console.print(f"[red]Bundled module '{requested_name}' was not found in packaged bundled sources.[/red]")
        raise typer.Exit(1)

    try:
        installed_path = install_module(
            normalized,
            version=version,
            install_root=target_root,
            trust_non_official=trust_non_official,
            non_interactive=is_non_interactive(),
        )
    except Exception as exc:
        console.print(f"[red]Failed installing {normalized}: {exc}[/red]")
        raise typer.Exit(1) from exc
    console.print(f"[green]Installed[/green] {normalized} -> {installed_path}")


@app.command()
@beartype
def uninstall(
    module_name: str = typer.Argument(..., help="Installed module name (name or namespace/name)"),
    scope: str | None = typer.Option(None, "--scope", help="Uninstall scope: user or project"),
    repo: Path | None = typer.Option(None, "--repo", help="Repository path for project scope (default: current dir)"),
) -> None:
    """Uninstall a marketplace module."""
    normalized = module_name
    if "/" in normalized:
        if normalized.count("/") != 1:
            console.print("[red]Invalid module id. Use 'name' or 'namespace/name'.[/red]")
            raise typer.Exit(1)
        normalized = normalized.split("/", 1)[1]

    scope_normalized = scope.strip().lower() if scope else None
    if scope_normalized is not None and scope_normalized not in {"user", "project"}:
        console.print("[red]Invalid scope. Use 'user' or 'project'.[/red]")
        raise typer.Exit(1)

    repo_path = (repo or Path.cwd()).resolve()
    project_root = repo_path / ".specfact" / "modules"
    user_root = USER_MODULES_ROOT
    project_module_dir = project_root / normalized
    user_module_dir = user_root / normalized
    project_exists = project_module_dir.exists()
    user_exists = user_module_dir.exists()

    if scope_normalized is None:
        if project_exists and user_exists:
            console.print(
                f"[red]Module '{normalized}' exists in both user and project module roots. "
                "Use --scope user or --scope project to uninstall the correct copy.[/red]"
            )
            raise typer.Exit(1)
        if project_exists:
            scope_normalized = "project"
        elif user_exists:
            scope_normalized = "user"

    if scope_normalized == "project":
        if not project_exists:
            console.print(f"[red]Module '{normalized}' is not installed in project scope ({project_root}).[/red]")
            raise typer.Exit(1)
        shutil.rmtree(project_module_dir)
        console.print(f"[green]Uninstalled[/green] {normalized} from {project_root}")
        return

    if scope_normalized == "user":
        if not user_exists:
            console.print(f"[red]Module '{normalized}' is not installed in user scope ({user_root}).[/red]")
            raise typer.Exit(1)
        shutil.rmtree(user_module_dir)
        console.print(f"[green]Uninstalled[/green] {normalized} from {user_root}")
        return

    discovered_by_name = {entry.metadata.name: entry for entry in discover_all_modules()}
    existing = discovered_by_name.get(normalized)
    source = existing.source if existing is not None else "unknown"

    if source == "builtin":
        console.print(
            f"[red]Cannot uninstall built-in module '{normalized}'. Use `specfact module disable {normalized}` instead.[/red]"
        )
        raise typer.Exit(1)
    if source in {"project", "custom"}:
        user_modules_root = str(USER_MODULES_ROOT)
        console.print(
            f"[red]Cannot uninstall {source} module '{normalized}' via marketplace uninstall. "
            f"Remove it from your local module roots (workspace `.specfact/modules`, `{user_modules_root}`, "
            "or custom module roots).[/red]"
        )
        raise typer.Exit(1)
    if source == "unknown":
        console.print(
            f"[red]Module '{normalized}' is not installed from marketplace (or not discovered). "
            "Run `specfact module list --show-origin` to inspect available modules.[/red]"
        )
        raise typer.Exit(1)

    try:
        uninstall_module(normalized)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc
    console.print(f"[green]Uninstalled[/green] {normalized}")


@app.command()
@beartype
def enable(
    module_id: str | None = typer.Argument(None, help="Module id to enable; omit in interactive mode to select"),
    force: bool = typer.Option(False, "--force", help="Override dependency checks and cascade dependencies"),
    trust_non_official: bool = typer.Option(
        False,
        "--trust-non-official",
        help="Trust and persist non-official publishers while enabling modules",
    ),
) -> None:
    """Enable modules in lifecycle state registry."""
    enable_ids: list[str]
    if module_id:
        enable_ids = [module_id]
    else:
        if is_non_interactive():
            console.print("[red]Error:[/red] Non-interactive mode requires explicit module id value.")
            raise typer.Exit(1)
        modules = get_modules_with_state()
        enable_ids = select_module_ids_interactive("enable", modules, console)
        if not enable_ids:
            return

    modules_by_id = {str(module.get("id", "")): module for module in get_modules_with_state()}
    try:
        for selected in enable_ids:
            selected_row = modules_by_id.get(selected)
            if selected_row is None:
                continue
            ensure_publisher_trusted(
                str(selected_row.get("publisher", "")).strip() or None,
                trust_non_official=trust_non_official,
                non_interactive=is_non_interactive(),
            )
        apply_module_state_update(enable_ids=enable_ids, disable_ids=[], force=force)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc
    console.print(f"[green]Enabled[/green] {', '.join(sorted(enable_ids, key=str.lower))}")


@app.command()
@beartype
def disable(
    module_id: str | None = typer.Argument(None, help="Module id to disable; omit in interactive mode to select"),
    force: bool = typer.Option(False, "--force", help="Override dependency checks and cascade dependents"),
) -> None:
    """Disable modules in lifecycle state registry."""
    disable_ids: list[str]
    if module_id:
        disable_ids = [module_id]
    else:
        if is_non_interactive():
            console.print("[red]Error:[/red] Non-interactive mode requires explicit module id value.")
            raise typer.Exit(1)
        modules = get_modules_with_state()
        disable_ids = select_module_ids_interactive("disable", modules, console)
        if not disable_ids:
            return

    try:
        apply_module_state_update(enable_ids=[], disable_ids=disable_ids, force=force)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc
    console.print(f"[green]Disabled[/green] {', '.join(sorted(disable_ids, key=str.lower))}")


@app.command()
@beartype
def search(query: str = typer.Argument(..., help="Search query")) -> None:
    """Search marketplace and installed modules by id/description/tags."""
    query_l = query.lower().strip()
    seen_ids: set[str] = set()
    rows: list[dict[str, str]] = []

    index = fetch_registry_index() or {}
    for entry in index.get("modules", []):
        if not isinstance(entry, dict):
            continue
        module_id = str(entry.get("id", ""))
        description = str(entry.get("description", ""))
        tags = entry.get("tags", [])
        tags_text = " ".join(str(t) for t in tags) if isinstance(tags, list) else ""
        haystack = f"{module_id} {description} {tags_text}".lower()
        if query_l in haystack and module_id not in seen_ids:
            seen_ids.add(module_id)
            rows.append(
                {
                    "id": module_id,
                    "version": str(entry.get("latest_version", "")),
                    "description": description,
                    "scope": "marketplace",
                }
            )

    for discovered in discover_all_modules():
        meta = discovered.metadata
        module_id = str(meta.name)
        description = str(meta.description or "")
        publisher = meta.publisher.name if meta.publisher else ""
        haystack = f"{module_id} {description} {publisher}".lower()
        if query_l not in haystack:
            continue

        if module_id in seen_ids:
            continue

        seen_ids.add(module_id)
        rows.append(
            {
                "id": module_id,
                "version": str(meta.version),
                "description": description,
                "scope": "installed",
            }
        )

    if not rows:
        console.print(f"No modules found for query '{query}'")
        return

    rows.sort(key=lambda row: row["id"].lower())

    table = Table(title="Module Search Results")
    table.add_column("ID", style="cyan")
    table.add_column("Version", style="magenta")
    table.add_column("Scope", style="yellow")
    table.add_column("Description")
    for row in rows:
        table.add_row(row["id"], row["version"], row["scope"], row["description"])
    console.print(table)


def _trust_label(module: dict) -> str:
    """Return user-facing trust label for a module row."""
    source = str(module.get("source", "unknown"))
    if bool(module.get("official", False)):
        return "official"
    if source == "marketplace":
        return "community"
    return "local-dev"


def _origin_label(source: str) -> str:
    """Return user-friendly origin label."""
    return "built-in" if source == "builtin" else source


def _typer_command_info_name(command_info: object) -> str:
    """Return a stable command name from Typer command info."""
    explicit_name = getattr(command_info, "name", None)
    if isinstance(explicit_name, str) and explicit_name:
        return explicit_name
    callback = getattr(command_info, "callback", None)
    callback_name = getattr(callback, "__name__", "")
    return callback_name.replace("_", "-") if callback_name else ""


def _short_help(help_text: object) -> str:
    """Normalize help text into a short single-line description."""
    if isinstance(help_text, str) and help_text.strip():
        return " ".join(help_text.strip().split())
    return "No description available"


def _command_info_help(command_info: object) -> str:
    """Extract command help from Typer info or callback docstring."""
    explicit_help = getattr(command_info, "help", None)
    if isinstance(explicit_help, str) and explicit_help.strip():
        return _short_help(explicit_help)

    callback = getattr(command_info, "callback", None)
    callback_doc = inspect.getdoc(callback) if callback is not None else None
    if callback_doc:
        first_line = callback_doc.splitlines()[0].strip()
        if first_line:
            return _short_help(first_line)

    return "No description available"


def _group_info_help(group_info: object) -> str:
    """Extract group help from Typer group info or nested app info."""
    explicit_help = getattr(group_info, "help", None)
    if isinstance(explicit_help, str) and explicit_help.strip():
        return _short_help(explicit_help)

    nested_app = getattr(group_info, "typer_instance", None)
    app_info = getattr(nested_app, "info", None)
    app_help = getattr(app_info, "help", None) if app_info is not None else None
    if isinstance(app_help, str) and app_help.strip():
        return _short_help(app_help)

    return "No description available"


def _collect_typer_command_entries(app: object, prefix: str) -> dict[str, str]:
    """Collect full command paths and short help recursively from a Typer app."""
    entries: dict[str, str] = {}

    command_infos = list(getattr(app, "registered_commands", []))
    for command_info in command_infos:
        command_name = _typer_command_info_name(command_info)
        if not command_name:
            continue
        command_path = f"{prefix} {command_name}"
        entries[command_path] = _command_info_help(command_info)

    group_infos = list(getattr(app, "registered_groups", []))
    for group_info in group_infos:
        group_name = getattr(group_info, "name", "") or ""
        if not group_name:
            continue
        group_prefix = f"{prefix} {group_name}"
        entries[group_prefix] = _group_info_help(group_info)
        nested_app = getattr(group_info, "typer_instance", None)
        if nested_app is not None:
            entries.update(_collect_typer_command_entries(nested_app, group_prefix))

    return entries


def _derive_module_command_entries(metadata: object) -> list[tuple[str, str]]:
    """Derive command/subcommand paths with short help for module show output."""
    roots: list[str] = []
    meta_commands = list(getattr(metadata, "commands", []) or [])
    if meta_commands:
        roots.extend(str(cmd) for cmd in meta_commands)
    else:
        command_help = getattr(metadata, "command_help", None) or {}
        roots.extend(str(cmd) for cmd in command_help)

    if not roots:
        return []

    manifest_help = getattr(metadata, "command_help", None) or {}
    entries: dict[str, str] = {}
    for root in roots:
        registry_meta = CommandRegistry.get_metadata(root)
        root_help = registry_meta.help if registry_meta and registry_meta.help else manifest_help.get(root)
        entries[root] = _short_help(root_help)
        try:
            root_app = CommandRegistry.get_typer(root)
        except Exception:
            continue
        entries.update(_collect_typer_command_entries(root_app, root))

    return sorted(entries.items(), key=lambda item: item[0].lower())


@app.command(name="list")
@beartype
def list_modules(
    source: str | None = typer.Option(
        None, "--source", help="Filter by origin: builtin, project, user, marketplace, custom"
    ),
    show_origin: bool = typer.Option(False, "--show-origin", help="Show raw origin column in addition to trust"),
    show_bundled_available: bool = typer.Option(
        False,
        "--show-bundled-available",
        help="Show bundled modules available in package artifacts but not installed in active roots",
    ),
) -> None:
    """List installed modules with trust labels and optional origin details."""
    modules = get_modules_with_state()
    if source:
        modules = [m for m in modules if str(m.get("source", "")) == source]
    render_modules_table(console, modules, show_origin=show_origin)

    bundled = get_bundled_module_metadata()
    installed_ids = {str(module.get("id", "")).strip() for module in modules}
    available = [meta for name, meta in bundled.items() if name not in installed_ids]
    if not show_bundled_available:
        if available:
            console.print(
                "[dim]Bundled modules are available but not installed. "
                "Use `specfact module list --show-bundled-available` to inspect them.[/dim]"
            )
        return

    if not available:
        console.print("[dim]All bundled modules are already installed in active module roots.[/dim]")
        return

    available.sort(key=lambda meta: meta.name.lower())
    table = Table(title="Bundled Modules Available (Not Installed)")
    table.add_column("Module", style="cyan")
    table.add_column("Version", style="magenta")
    table.add_column("Description", style="white")
    for metadata in available:
        table.add_row(metadata.name, metadata.version, metadata.description or "")
    console.print(table)
    console.print("[dim]Install bundled modules into user scope: specfact module init[/dim]")
    console.print("[dim]Install bundled modules into project scope: specfact module init --scope project[/dim]")


@app.command()
@beartype
def show(module_name: str = typer.Argument(..., help="Installed module name")) -> None:
    """Show detailed metadata for an installed module."""
    modules = get_modules_with_state()
    module_row = next((m for m in modules if str(m.get("id", "")) == module_name), None)
    if module_row is None:
        console.print(f"[red]Module '{module_name}' is not installed.[/red]")
        raise typer.Exit(1)

    discovered = {entry.metadata.name: entry.metadata for entry in discover_all_modules()}
    metadata = discovered.get(module_name)

    source = str(module_row.get("source", "unknown"))
    trust = _trust_label(module_row)
    state = "enabled" if bool(module_row.get("enabled", True)) else "disabled"
    publisher = str(module_row.get("publisher", "unknown"))
    description = metadata.description if metadata and metadata.description else "n/a"
    license_value = metadata.license if metadata and metadata.license else "n/a"
    tier = metadata.tier if metadata and metadata.tier else "n/a"
    command_entries = _derive_module_command_entries(metadata) if metadata else []
    commands = "\n".join(f"{path} - {help_text}" for path, help_text in command_entries) if command_entries else "n/a"
    core_compatibility = metadata.core_compatibility if metadata and metadata.core_compatibility else "n/a"

    publisher_url = "n/a"
    if metadata and metadata.publisher:
        publisher_url = metadata.publisher.attributes.get("url", "n/a")

    table = Table(title=f"Module Details: {module_name}")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Name", module_name)
    table.add_row("Description", description)
    table.add_row("Version", str(module_row.get("version", "")))
    table.add_row("State", state)
    table.add_row("Trust", trust)
    table.add_row("Publisher", publisher)
    table.add_row("Publisher URL", publisher_url)
    table.add_row("License", license_value)
    table.add_row("Origin", _origin_label(source))
    table.add_row("Tier", tier)
    table.add_row("Core Compatibility", core_compatibility)
    table.add_row("Commands", commands)
    console.print(table)


@app.command()
@beartype
def upgrade(
    module_name: str | None = typer.Argument(
        None, help="Installed module name (optional; omit to upgrade all marketplace modules)"
    ),
    all: bool = typer.Option(False, "--all", help="Upgrade all installed marketplace modules"),
) -> None:
    """Upgrade marketplace module(s) to latest available versions."""
    modules = get_modules_with_state()
    by_id = {str(m.get("id", "")): m for m in modules}

    target_ids: list[str] = []
    if all or module_name is None:
        target_ids = [str(m.get("id", "")) for m in modules if str(m.get("source", "")) == "marketplace"]
        if not target_ids:
            console.print("[yellow]No marketplace-installed modules found to upgrade.[/yellow]")
            return
    else:
        normalized = module_name
        if normalized in by_id:
            source = str(by_id[normalized].get("source", "unknown"))
            if source != "marketplace":
                console.print(
                    f"[red]Cannot upgrade '{normalized}' from source '{source}'. Only marketplace modules are upgradeable.[/red]"
                )
                raise typer.Exit(1)
            target_ids = [normalized]
        else:
            prefixed = normalized if "/" in normalized else f"specfact/{normalized}"
            # If module isn't discovered locally, still attempt marketplace install/upgrade by ID.
            target_ids = [prefixed]

    upgraded: list[str] = []
    failed: list[str] = []
    for target in target_ids:
        try:
            module_id = target if "/" in target else f"specfact/{target}"
            install_module(module_id, reinstall=True)
            upgraded.append(module_id)
        except Exception as exc:
            console.print(f"[red]Failed upgrading {target}: {exc}[/red]")
            failed.append(target)

    if upgraded:
        console.print(f"[green]Upgraded[/green] {', '.join(upgraded)}")
    if failed:
        raise typer.Exit(1)


# Expose standard ModuleIOContract operations for protocol compliance discovery.
import_to_bundle = module_io_shim.import_to_bundle
export_from_bundle = module_io_shim.export_from_bundle
sync_with_bundle = module_io_shim.sync_with_bundle
validate_bundle = module_io_shim.validate_bundle

__all__ = [
    "app",
    "export_from_bundle",
    "import_to_bundle",
    "sync_with_bundle",
    "validate_bundle",
]

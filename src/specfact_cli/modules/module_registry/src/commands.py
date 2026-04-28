"""Marketplace module management CLI commands."""

from __future__ import annotations

import inspect
import os
import shutil
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, cast

import typer
import yaml
from beartype import beartype
from click.exceptions import Exit as ClickExit
from icontract import require
from packaging.version import InvalidVersion, Version
from rich.console import Console
from rich.table import Table

from specfact_cli import __version__
from specfact_cli.models.module_package import ModulePackageMetadata
from specfact_cli.modules import module_io_shim
from specfact_cli.registry.alias_manager import create_alias, list_aliases, remove_alias
from specfact_cli.registry.custom_registries import add_registry, fetch_all_indexes, list_registries, remove_registry
from specfact_cli.registry.help_cache import run_discovery_and_write_cache
from specfact_cli.registry.marketplace_client import fetch_registry_index
from specfact_cli.registry.module_discovery import discover_all_modules, discover_all_modules_for_project
from specfact_cli.registry.module_installer import (
    REGISTRY_ID_FILE,
    USER_MODULES_ROOT,
    InstallModuleOptions,
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
from specfact_cli.registry.module_packages import get_discovered_modules_for_state
from specfact_cli.registry.module_security import ensure_publisher_trusted, is_official_publisher
from specfact_cli.registry.module_state import read_modules_state, write_modules_state
from specfact_cli.registry.registry import CommandRegistry
from specfact_cli.runtime import is_non_interactive


app = typer.Typer(help="Manage marketplace modules")
console = Console()


def _module_upgrade_show_spinner() -> bool:
    """Rich Live/spinner breaks some tests; mirror ``utils.progress`` test-mode detection."""
    return os.environ.get("TEST_MODE") != "true" and os.environ.get("PYTEST_CURRENT_TEST") is None


@contextmanager
def _module_upgrade_status(description: str) -> Iterator[None]:
    """Show a Rich status spinner during long-running upgrade steps (fetch, install)."""
    if _module_upgrade_show_spinner():
        with console.status(description, spinner="dots"):
            yield
    else:
        yield


def _init_scope_nonempty(scope: str) -> bool:
    return bool(scope)


def _strip_nonempty(s: str) -> bool:
    return bool(s.strip())


def _module_name_arg_nonempty(module_name: str) -> bool:
    return _strip_nonempty(module_name)


def _alias_name_nonempty(alias_name: str) -> bool:
    return _strip_nonempty(alias_name)


def _command_name_nonempty(command_name: str) -> bool:
    return _strip_nonempty(command_name)


def _url_nonempty(url: str) -> bool:
    return url.strip() != ""


def _registry_id_nonempty(registry_id: str) -> bool:
    return _strip_nonempty(registry_id)


def _search_query_nonempty(query: str) -> bool:
    return _strip_nonempty(query)


def _module_id_optional_nonempty(module_id: str | None) -> bool:
    return module_id is None or module_id.strip() != ""


def _list_source_filter_ok(source: str | None) -> bool:
    return source is None or source in ("builtin", "project", "user", "marketplace", "custom")


def _upgrade_module_names_valid(module_names: list[str] | None) -> bool:
    if module_names is None:
        return True
    return all(m.strip() != "" for m in module_names)


def _install_module_ids_nonempty(module_ids: list[str]) -> bool:
    return bool(module_ids) and all(m.strip() != "" for m in module_ids)


def _uninstall_module_names_nonempty(module_names: list[str]) -> bool:
    return bool(module_names) and all(m.strip() != "" for m in module_names)


def _publisher_url_from_metadata(metadata: object | None) -> str:
    if not metadata:
        return "n/a"
    pub = getattr(metadata, "publisher", None)
    if pub is None:
        return "n/a"
    attrs = getattr(pub, "attributes", None)
    if isinstance(attrs, dict):
        return str(cast(dict[str, Any], attrs).get("url", "n/a"))
    return "n/a"


def _read_installed_module_version(module_dir: Path) -> str:
    """Read installed module version from its manifest, if available."""
    manifest_path = module_dir / "module-package.yaml"
    if not manifest_path.exists():
        return "unknown"
    try:
        loaded = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return "unknown"
    if not isinstance(loaded, dict):
        return "unknown"
    manifest: dict[str, Any] = cast(dict[str, Any], loaded)
    return str(manifest.get("version", "unknown"))


def _publisher_from_module_id(module_id: str) -> str:
    """Extract normalized publisher namespace from module id."""
    return module_id.split("/", 1)[0].strip().lower() if "/" in module_id else ""


def _parse_install_scope_and_source(scope: str, source: str) -> tuple[str, str]:
    scope_normalized = scope.strip().lower()
    if scope_normalized not in {"user", "project"}:
        console.print("[red]Invalid scope. Use 'user' or 'project'.[/red]")
        raise typer.Exit(1)
    source_normalized = source.strip().lower()
    if source_normalized not in {"auto", "bundled", "marketplace"}:
        console.print("[red]Invalid source. Use 'auto', 'bundled', or 'marketplace'.[/red]")
        raise typer.Exit(1)
    return scope_normalized, source_normalized


def _normalize_install_module_id(module_id: str) -> tuple[str, str]:
    normalized = module_id if "/" in module_id else f"specfact/{module_id}"
    if normalized.count("/") != 1:
        console.print("[red]Invalid module id. Use 'name' or 'namespace/name'.[/red]")
        raise typer.Exit(1)
    requested_name = normalized.split("/", 1)[1]
    return normalized, requested_name


def _resolve_install_target_root(scope_normalized: str, repo: Path | None) -> Path:
    repo_path = (repo or Path.cwd()).resolve()
    return USER_MODULES_ROOT if scope_normalized == "user" else repo_path / ".specfact" / "modules"


def _normalize_project_repo(repo: Path | None) -> Path | None:
    """Resolve a project-scoped repo argument to the nearest workspace root."""
    if repo is None:
        return None
    repo_path = repo.resolve()
    for candidate in [repo_path, *repo_path.parents]:
        if (candidate / ".git").exists():
            return candidate
    return repo_path


def _read_installed_manifest_id(module_dir: Path, fallback_name: str) -> str:
    manifest_path = module_dir / "module-package.yaml"
    try:
        raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return fallback_name
    if isinstance(raw, dict):
        manifest = cast(dict[str, Any], raw)
        if manifest.get("name"):
            return str(manifest["name"])
    return fallback_name


def _enable_if_disabled(module_id: str, base_path: Path | None = None) -> bool:
    state = read_modules_state()
    if state.get(module_id, {}).get("enabled", True) is not False:
        return False
    modules = get_discovered_modules_for_state(
        enable_ids=[module_id],
        disable_ids=[],
        base_path=base_path,
        preserve_existing=True,
    )
    write_modules_state(modules)
    run_discovery_and_write_cache(__version__)
    return any(str(row.get("id", "")) == module_id and bool(row.get("enabled", True)) for row in modules)


def _install_skip_if_already_satisfied(
    scope_normalized: str,
    requested_name: str,
    target_root: Path,
    repo: Path | None,
    reinstall: bool,
    discovered_by_name: dict[str, Any],
) -> bool:
    installed_dir = target_root / requested_name
    if (installed_dir / "module-package.yaml").exists() and not reinstall:
        module_id = _read_installed_manifest_id(installed_dir, requested_name)
        enabled = _enable_if_disabled(module_id, base_path=repo if scope_normalized == "project" else None)
        if enabled:
            console.print(
                f"[yellow]Module '{module_id}' is already installed in {target_root}; "
                "enabled it in module state.[/yellow]"
            )
        else:
            console.print(f"[yellow]Module '{module_id}' is already installed in {target_root}.[/yellow]")
        return True
    skip_sources = {"builtin", "project", "user", "custom"}
    if scope_normalized == "project":
        skip_sources.discard("user")
    if scope_normalized == "user":
        skip_sources.discard("project")
    existing = discovered_by_name.get(requested_name)
    if existing is not None and existing.source in skip_sources:
        enabled = _enable_if_disabled(
            existing.metadata.name,
            base_path=repo if scope_normalized == "project" else None,
        )
        state_hint = " Enabled it in module state." if enabled else ""
        console.print(
            f"[yellow]Module '{existing.metadata.name}' is already available from source '{existing.source}'. "
            f"No marketplace install needed.{state_hint}[/yellow]"
        )
        return True
    return False


def _try_install_bundled_module(
    source_normalized: str,
    requested_name: str,
    normalized: str,
    target_root: Path,
    trust_non_official: bool,
) -> bool:
    try:
        if source_normalized in {"auto", "bundled"} and install_bundled_module(
            requested_name,
            target_root=target_root,
            trust_non_official=trust_non_official,
            non_interactive=is_non_interactive(),
        ):
            console.print(f"[green]Installed bundled module[/green] {requested_name} -> {target_root / requested_name}")
            publisher = _publisher_from_module_id(normalized)
            if is_official_publisher(publisher):
                console.print(f"Verified: official ({publisher})")
            return True
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc
    if source_normalized == "bundled":
        console.print(f"[red]Bundled module '{requested_name}' was not found in packaged bundled sources.[/red]")
        raise typer.Exit(1)
    return False


@app.command(name="init")
@beartype
@require(_init_scope_nonempty, "scope must not be empty")
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


@dataclass(frozen=True)
class _InstallOneParams:
    scope_normalized: str
    source_normalized: str
    target_root: Path
    repo: Path | None
    version: str | None
    reinstall: bool
    trust_non_official: bool
    skip_deps: bool
    force: bool
    discovered_by_name: dict[str, Any]


def _install_one(module_id: str, params: _InstallOneParams) -> bool:
    """Install a single module; return True on success, False if skipped/already installed."""
    normalized, requested_name = _normalize_install_module_id(module_id)
    if _install_skip_if_already_satisfied(
        params.scope_normalized,
        requested_name,
        params.target_root,
        params.repo,
        params.reinstall,
        params.discovered_by_name,
    ):
        return True
    if _try_install_bundled_module(
        params.source_normalized,
        requested_name,
        normalized,
        params.target_root,
        params.trust_non_official,
    ):
        return True
    try:
        installed_path = install_module(
            normalized,
            InstallModuleOptions(
                version=params.version,
                reinstall=params.reinstall,
                install_root=params.target_root,
                trust_non_official=params.trust_non_official,
                non_interactive=is_non_interactive(),
                skip_deps=params.skip_deps,
                force=params.force,
            ),
        )
    except Exception as exc:
        console.print(f"[red]Failed installing {normalized}: {exc}[/red]")
        return False
    console.print(f"[green]Installed[/green] {normalized} -> {installed_path}")
    publisher = _publisher_from_module_id(normalized)
    if is_official_publisher(publisher):
        console.print(f"Verified: official ({publisher})")
    return True


def _install_sig_part1(
    module_ids: Annotated[
        list[str],
        typer.Argument(help="Module id(s) (name or namespace/name); space-separated for multiple"),
    ],
    version: str | None = typer.Option(None, "--version", help="Install a specific version (single module only)"),
    scope: str = typer.Option("user", "--scope", help="Install scope: user or project"),
    source: str = typer.Option("auto", "--source", help="Install source: auto, bundled, or marketplace"),
) -> None:
    """Typer param signature fragment (merged for install); not invoked at runtime."""


def _install_sig_part2(
    repo: Path | None = typer.Option(None, "--repo", help="Repository path for project scope (default: current dir)"),
    trust_non_official: bool = typer.Option(
        False,
        "--trust-non-official",
        help="Trust and persist non-official publisher for this module install",
    ),
    skip_deps: bool = typer.Option(
        False,
        "--skip-deps",
        help="Skip dependency resolution before installing (install module only)",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Force install even if dependency resolution reports conflicts",
    ),
) -> None:
    """Typer param signature fragment (merged for install); not invoked at runtime."""


def _install_sig_part3(
    reinstall: bool = typer.Option(
        False,
        "--reinstall",
        help="Reinstall even if module is already present (e.g. to refresh integrity metadata)",
    ),
) -> None:
    """Typer param signature fragment (merged for install); not invoked at runtime."""


def _specfact_merge_install_param_specs(orig: Callable[..., Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    merged.update(orig(_install_sig_part1))
    merged.update(orig(_install_sig_part2))
    merged.update(orig(_install_sig_part3))
    return merged


@beartype
def _install_impl(module_ids: list[str], **kwargs: Any) -> None:
    """Install one or more modules from bundled artifacts or marketplace registry."""
    version = kwargs.get("version")
    scope = kwargs.get("scope", "user")
    source = kwargs.get("source", "auto")
    repo = kwargs.get("repo")
    trust_non_official = kwargs.get("trust_non_official", False)
    skip_deps = kwargs.get("skip_deps", False)
    force = kwargs.get("force", False)
    reinstall = kwargs.get("reinstall", False)
    if version is not None and sum(1 for mid in module_ids if mid.strip()) > 1:
        console.print(
            "[red]--version applies to a single module; install one module at a time or omit --version.[/red]"
        )
        raise typer.Exit(1)
    scope_normalized, source_normalized = _parse_install_scope_and_source(scope, source)
    normalized_repo = _normalize_project_repo(repo) if scope_normalized == "project" else None
    target_root = _resolve_install_target_root(scope_normalized, normalized_repo)
    discovered = (
        discover_all_modules_for_project(normalized_repo) if normalized_repo is not None else discover_all_modules()
    )
    discovered_by_name = {entry.metadata.name: entry for entry in discovered}
    params = _InstallOneParams(
        scope_normalized=scope_normalized,
        source_normalized=source_normalized,
        target_root=target_root,
        repo=normalized_repo,
        version=version,
        reinstall=reinstall,
        trust_non_official=trust_non_official,
        skip_deps=skip_deps,
        force=force,
        discovered_by_name=discovered_by_name,
    )
    for module_id in module_ids:
        if not _install_one(module_id, params):
            raise typer.Exit(1)


@app.command()
@require(_install_module_ids_nonempty, "at least one non-blank module id is required")
@beartype
def install(
    module_ids: Annotated[
        list[str],
        typer.Argument(help="Module id(s) (name or namespace/name); space-separated for multiple"),
    ],
    **kwargs,
) -> None:
    """Install one or more modules from bundled artifacts or marketplace registry."""
    _install_impl(module_ids, **kwargs)


def _normalize_uninstall_module_name(module_name: str) -> str:
    normalized = module_name
    if "/" in normalized:
        if normalized.count("/") != 1:
            console.print("[red]Invalid module id. Use 'name' or 'namespace/name'.[/red]")
            raise typer.Exit(1)
        normalized = normalized.split("/", 1)[1]
    return normalized


def _resolve_uninstall_scope(
    scope: str | None,
    normalized: str,
    project_module_dir: Path,
    user_module_dir: Path,
) -> str | None:
    scope_normalized = scope.strip().lower() if scope else None
    if scope_normalized is not None and scope_normalized not in {"user", "project"}:
        console.print("[red]Invalid scope. Use 'user' or 'project'.[/red]")
        raise typer.Exit(1)
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
    return scope_normalized


@dataclass
class _ExplicitUninstallPaths:
    scope_normalized: str | None
    normalized: str
    project_root: Path
    user_root: Path
    project_module_dir: Path
    user_module_dir: Path


def _uninstall_from_explicit_scope(ctx: _ExplicitUninstallPaths) -> bool:
    if ctx.scope_normalized == "project":
        if not ctx.project_module_dir.exists():
            console.print(
                f"[red]Module '{ctx.normalized}' is not installed in project scope ({ctx.project_root}).[/red]"
            )
            raise typer.Exit(1)
        try:
            shutil.rmtree(ctx.project_module_dir)
        except OSError as exc:
            console.print(f"[red]Could not remove module directory {ctx.project_module_dir}: {exc}[/red]")
            raise typer.Exit(1) from exc
        console.print(f"[green]Uninstalled[/green] {ctx.normalized} from {ctx.project_root}")
        return True
    if ctx.scope_normalized == "user":
        if not ctx.user_module_dir.exists():
            console.print(f"[red]Module '{ctx.normalized}' is not installed in user scope ({ctx.user_root}).[/red]")
            raise typer.Exit(1)
        try:
            shutil.rmtree(ctx.user_module_dir)
        except OSError as exc:
            console.print(f"[red]Could not remove module directory {ctx.user_module_dir}: {exc}[/red]")
            raise typer.Exit(1) from exc
        console.print(f"[green]Uninstalled[/green] {ctx.normalized} from {ctx.user_root}")
        return True
    return False


def _uninstall_single_module(module_name: str, scope: str | None, repo: Path | None) -> None:
    """Uninstall one module; raises ``typer.Exit`` on failure."""
    normalized = _normalize_uninstall_module_name(module_name)
    repo_path = (repo or Path.cwd()).resolve()
    project_root = repo_path / ".specfact" / "modules"
    user_root = USER_MODULES_ROOT
    project_module_dir = project_root / normalized
    user_module_dir = user_root / normalized
    scope_normalized = _resolve_uninstall_scope(scope, normalized, project_module_dir, user_module_dir)
    if _uninstall_from_explicit_scope(
        _ExplicitUninstallPaths(
            scope_normalized=scope_normalized,
            normalized=normalized,
            project_root=project_root,
            user_root=user_root,
            project_module_dir=project_module_dir,
            user_module_dir=user_module_dir,
        )
    ):
        return
    _uninstall_marketplace_default(normalized)


def _uninstall_marketplace_default(normalized: str) -> None:
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
        uninstall_module(normalized, confirm_user_scope=True)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc
    console.print(f"[green]Uninstalled[/green] {normalized}")


@app.command()
@require(_uninstall_module_names_nonempty, "at least one non-blank module name is required")
@beartype
def uninstall(
    module_names: Annotated[
        list[str],
        typer.Argument(help="Installed module name(s) (name or namespace/name)"),
    ],
    scope: str | None = typer.Option(None, "--scope", help="Uninstall scope: user or project"),
    repo: Path | None = typer.Option(None, "--repo", help="Repository path for project scope (default: current dir)"),
) -> None:
    """Uninstall one or more marketplace modules."""
    failed = False
    for module_name in module_names:
        stripped = module_name.strip()
        try:
            _uninstall_single_module(stripped, scope, repo)
        except ClickExit as exc:
            if exc.exit_code not in (0, None):
                failed = True
    if failed:
        raise typer.Exit(1)


alias_app = typer.Typer(help="Manage command aliases (map name to namespaced module)")


@alias_app.command(name="create")
@beartype
@require(_alias_name_nonempty, "alias_name must not be empty")
@require(_command_name_nonempty, "command_name must not be empty")
def alias_create(
    alias_name: str = typer.Argument(..., help="Alias (command name) to map"),
    command_name: str = typer.Argument(..., help="Command name to invoke (e.g. backlog, module)"),
    force: bool = typer.Option(False, "--force", help="Allow alias to shadow built-in command"),
) -> None:
    """Create an alias mapping a custom name to a registered command."""
    try:
        create_alias(alias_name.strip(), command_name.strip(), force=force)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc
    console.print(f"[green]Alias[/green] {alias_name!r} -> {command_name!r}")


@alias_app.command(name="list")
@beartype
@require(lambda: callable(list_aliases), "list_aliases helper must be callable")
def alias_list() -> None:
    """List all configured aliases."""
    aliases = list_aliases()
    if not aliases:
        console.print("[dim]No aliases configured.[/dim]")
        return
    table = Table(title="Aliases")
    table.add_column("Alias", style="cyan")
    table.add_column("Command", style="green")
    for alias, mod in sorted(aliases.items()):
        table.add_row(alias, mod)
    console.print(table)


@alias_app.command(name="remove")
@beartype
@require(_alias_name_nonempty, "alias_name must not be empty")
def alias_remove(
    alias_name: str = typer.Argument(..., help="Alias to remove"),
) -> None:
    """Remove an alias."""
    remove_alias(alias_name.strip())
    console.print(f"[green]Removed alias[/green] {alias_name!r}")


if app.add_typer is not None:
    app.add_typer(alias_app, name="alias")


@app.command(name="add-registry")
@beartype
@require(_url_nonempty, "url must not be empty")
def add_registry_cmd(
    url: str = typer.Argument(..., help="Registry index URL (e.g. https://company.com/index.json)"),
    id: str | None = typer.Option(None, "--id", help="Registry id (default: derived from URL)"),
    priority: int | None = typer.Option(None, "--priority", help="Priority (default: next available)"),
    trust: str = typer.Option("prompt", "--trust", help="Trust level: always, prompt, or never"),
) -> None:
    """Add a custom registry to the config."""
    if trust not in ("always", "prompt", "never"):
        console.print("[red]trust must be one of: always, prompt, never.[/red]")
        raise typer.Exit(1)
    reg_id = (id or url.strip().rstrip("/").split("/")[-2] or "custom").strip() or "custom"
    try:
        add_registry(reg_id, url.strip(), priority=priority, trust=trust)
    except Exception as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc
    console.print(f"[green]Added registry[/green] {reg_id!r} -> {url}")


@app.command(name="list-registries")
@beartype
@require(lambda: callable(list_registries), "list_registries helper must be callable")
def list_registries_cmd() -> None:
    """List all configured registries (official + custom)."""
    registries = list_registries()
    if not registries:
        console.print("[dim]No registries configured.[/dim]")
        return
    table = Table(title="Registries")
    table.add_column("Id", style="cyan")
    table.add_column("URL", style="green")
    table.add_column("Priority", style="dim")
    table.add_column("Trust", style="yellow")
    for r in registries:
        table.add_row(
            str(r.get("id", "")),
            str(r.get("url", "")),
            str(r.get("priority", "")),
            str(r.get("trust", "")),
        )
    console.print(table)


@app.command(name="remove-registry")
@beartype
@require(_registry_id_nonempty, "registry_id must not be empty")
def remove_registry_cmd(
    registry_id: str = typer.Argument(..., help="Registry id to remove"),
) -> None:
    """Remove a custom registry from the config."""
    remove_registry(registry_id.strip())
    console.print(f"[green]Removed registry[/green] {registry_id!r}")


@app.command()
@beartype
@require(_module_id_optional_nonempty, "module_id must be non-empty if provided")
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
@require(_module_id_optional_nonempty, "module_id must be non-empty if provided")
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
@require(_search_query_nonempty, "query must not be empty")
def search(query: str = typer.Argument(..., help="Search query")) -> None:
    """Search marketplace and installed modules by id/description/tags."""
    query_l = query.lower().strip()
    seen_ids: set[str] = set()
    rows: list[dict[str, str]] = []
    _search_append_registry_matches(query_l, seen_ids, rows)
    _search_append_installed_matches(query_l, seen_ids, rows)
    _print_search_results_table(query, rows)


def _trust_label(module: dict[str, Any]) -> str:
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


def _command_root_paths_from_metadata(metadata: object) -> list[str]:
    meta_commands = list(getattr(metadata, "commands", None) or [])
    if meta_commands:
        return [str(cmd) for cmd in meta_commands]
    command_help = getattr(metadata, "command_help", None) or {}
    return [str(cmd) for cmd in command_help]


def _derive_module_command_entries(metadata: object) -> list[tuple[str, str]]:
    """Derive command/subcommand paths with short help for module show output."""
    roots = _command_root_paths_from_metadata(metadata)
    if not roots:
        return []

    raw_manifest = getattr(metadata, "command_help", None) or {}
    manifest_help: dict[str, str] = dict(raw_manifest) if isinstance(raw_manifest, dict) else {}
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


def _search_append_registry_matches(query_l: str, seen_ids: set[str], rows: list[dict[str, str]]) -> None:
    for reg_id, index in fetch_all_indexes():
        for entry in index.get("modules", []):
            if not isinstance(entry, dict):
                continue
            entry_dict = cast(dict[str, Any], entry)
            module_id = str(entry_dict.get("id", ""))
            description = str(entry_dict.get("description", ""))
            tags = entry_dict.get("tags", [])
            tags_text = " ".join(str(t) for t in tags) if isinstance(tags, list) else ""
            haystack = f"{module_id} {description} {tags_text}".lower()
            if query_l in haystack and module_id not in seen_ids:
                seen_ids.add(module_id)
                rows.append(
                    {
                        "id": module_id,
                        "version": str(entry_dict.get("latest_version", "")),
                        "description": description,
                        "scope": "marketplace",
                        "registry": reg_id,
                    }
                )


def _search_append_installed_matches(query_l: str, seen_ids: set[str], rows: list[dict[str, str]]) -> None:
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


def _print_search_results_table(query: str, rows: list[dict[str, str]]) -> None:
    if not rows:
        console.print(f"No modules found for query '{query}'")
        return
    rows.sort(key=lambda row: row["id"].lower())
    table = Table(title="Module Search Results")
    table.add_column("ID", style="cyan")
    table.add_column("Version", style="magenta")
    table.add_column("Scope", style="yellow")
    table.add_column("Registry", style="dim")
    table.add_column("Description")
    for row in rows:
        reg = row.get("registry", "")
        table.add_row(row["id"], row["version"], row["scope"], reg, row["description"])
    console.print(table)


def _print_marketplace_modules_available(index: dict[str, Any]) -> None:
    registry_modules = index.get("modules") or []
    if not isinstance(registry_modules, list):
        registry_modules = []
    if not registry_modules:
        console.print("[dim]No modules listed in the marketplace registry.[/dim]")
        return
    rows: list[tuple[str, str, str]] = []
    for entry in registry_modules:
        if not isinstance(entry, dict):
            continue
        entry_dict = cast(dict[str, Any], entry)
        mod_id = str(entry_dict.get("id", "")).strip()
        if not mod_id:
            continue
        version = str(entry_dict.get("latest_version", "")).strip() or str(entry_dict.get("version", "")).strip()
        desc = str(entry_dict.get("description", "")).strip() if entry_dict.get("description") else ""
        rows.append((mod_id, version, desc))
    rows.sort(key=lambda r: r[0].lower())
    table = Table(title="Marketplace Modules Available")
    table.add_column("Module", style="cyan")
    table.add_column("Version", style="magenta")
    table.add_column("Description", style="white")
    for mod_id, version, desc in rows:
        table.add_row(mod_id, version, desc)
    console.print(table)
    console.print(
        "[dim]Install: specfact module install <module-id>[/dim]\n"
        "[dim]Or use a profile: specfact init --profile solo-developer|backlog-team|api-first-team|enterprise-full-stack[/dim]"
    )


def _print_bundled_available_table(available: list[ModulePackageMetadata]) -> None:
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


@app.command(name="list")
@beartype
@require(
    _list_source_filter_ok,
    "source must be one of: builtin, project, user, marketplace, custom",
)
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
    show_marketplace: bool = typer.Option(
        False,
        "--marketplace",
        "--available",
        help="Show modules available from the marketplace registry (install with specfact module install <id>)",
    ),
) -> None:
    """List installed modules with trust labels and optional origin details."""
    all_modules = get_modules_with_state()
    modules = all_modules
    if source:
        modules = [m for m in modules if str(m.get("source", "")) == source]
    render_modules_table(console, modules, show_origin=show_origin)

    if show_marketplace:
        index = fetch_registry_index()
        if index is None:
            console.print(
                "[yellow]Marketplace registry unavailable (offline or network error). "
                "Check connectivity or try again later.[/yellow]"
            )
        else:
            _print_marketplace_modules_available(index)
        return

    bundled = get_bundled_module_metadata()
    installed_ids = {str(module.get("id", "")).strip() for module in all_modules}
    available = [meta for name, meta in bundled.items() if name not in installed_ids]
    if not show_bundled_available:
        if available:
            console.print(
                "[dim]Bundled modules are available but not installed. "
                "Use `specfact module list --show-bundled-available` to inspect them.[/dim]"
            )
        console.print("[dim]See modules available from the marketplace: specfact module list --marketplace[/dim]")
        return

    if not available:
        console.print("[dim]All bundled modules are already installed in active module roots.[/dim]")
        return

    _print_bundled_available_table(available)


def _meta_field_str(metadata: object | None, attr: str, default: str = "n/a") -> str:
    if metadata is None:
        return default
    val = getattr(metadata, attr, None)
    return str(val) if val is not None and val != "" else default


def _build_module_details_table(module_name: str, module_row: dict[str, Any], metadata: object | None) -> Table:
    source = str(module_row.get("source", "unknown"))
    trust = _trust_label(module_row)
    state = "enabled" if bool(module_row.get("enabled", True)) else "disabled"
    publisher = str(module_row.get("publisher", "unknown"))
    description = _meta_field_str(metadata, "description")
    license_value = _meta_field_str(metadata, "license")
    tier = _meta_field_str(metadata, "tier")
    command_entries = _derive_module_command_entries(metadata) if metadata is not None else []
    commands = "\n".join(f"{path} - {help_text}" for path, help_text in command_entries) if command_entries else "n/a"
    core_compatibility = _meta_field_str(metadata, "core_compatibility")
    publisher_url = _publisher_url_from_metadata(metadata)
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
    return table


@app.command()
@beartype
@require(_module_name_arg_nonempty, "module_name must not be empty")
def show(module_name: str = typer.Argument(..., help="Installed module name")) -> None:
    """Show detailed metadata for an installed module."""
    modules = get_modules_with_state()
    module_row = next((m for m in modules if str(m.get("id", "")) == module_name), None)
    if module_row is None:
        console.print(f"[red]Module '{module_name}' is not installed.[/red]")
        raise typer.Exit(1)

    discovered = {entry.metadata.name: entry.metadata for entry in discover_all_modules()}
    metadata = discovered.get(module_name)
    console.print(_build_module_details_table(module_name, module_row, metadata))


def _upgrade_row_for_target(target: str, by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if target in by_id:
        return by_id[target]
    if target.count("/") > 1:
        return {}
    short = target.split("/")[-1]
    if short in by_id:
        return by_id[short]
    for key, row in by_id.items():
        if key == short or str(key).endswith(f"/{short}"):
            return row
    return {}


def _full_marketplace_module_id_for_install(target: str) -> str:
    """Return ``namespace/name`` for ``install_module`` from a target key or short id."""
    t = target.strip()
    if t.count("/") > 1:
        raise ValueError(
            f"Invalid module id {target!r}: expected owner/repo or a short module name, not a multi-segment path."
        )
    if "/" in t and t.count("/") == 1:
        left, right = t.split("/", 1)
        if left.strip() and right.strip():
            return t
    short = t.split("/")[-1]
    id_file = USER_MODULES_ROOT / short / REGISTRY_ID_FILE
    if id_file.exists():
        txt = id_file.read_text(encoding="utf-8").strip()
        if txt and "/" in txt:
            return txt
    if short.startswith("specfact-"):
        return f"nold-ai/{short}"
    return f"nold-ai/specfact-{short}"


def _latest_version_map_from_registry_index(idx: dict[str, Any] | None) -> dict[str, str]:
    """Build module id -> latest_version from a single registry index fetch."""
    out: dict[str, str] = {}
    if not idx:
        return out
    mods = idx.get("modules", [])
    if not isinstance(mods, list):
        return out
    for raw in mods:
        if not isinstance(raw, dict):
            continue
        raw_dict = cast(dict[str, Any], raw)
        mid = str(raw_dict.get("id", "")).strip()
        if not mid:
            continue
        lv = raw_dict.get("latest_version")
        if lv is None:
            continue
        s = str(lv).strip()
        if s:
            out[mid] = s
    return out


def _versions_equal_for_upgrade(current: str, latest: str) -> bool:
    try:
        return Version(current) == Version(latest)
    except (InvalidVersion, ValueError):
        return current.strip() == latest.strip()


def _is_major_version_increase(current: str, latest: str) -> bool:
    try:
        return Version(latest).major > Version(current).major
    except (InvalidVersion, ValueError):
        return False


def _upgrade_name_candidates(normalized: str, short: str, by_id: dict[str, dict[str, Any]]) -> list[str]:
    candidates = [normalized]
    if short != normalized:
        candidates.append(short)
    if "/" not in normalized and f"specfact-{normalized}" in by_id:
        candidates.append(f"specfact-{normalized}")
    return list(dict.fromkeys(candidates))


def _resolve_marketplace_id_by_short(short: str, marketplace_by_id: dict[str, dict[str, Any]]) -> str | None:
    for key in marketplace_by_id:
        if key == short or str(key).endswith(f"/{short}"):
            return key
    return None


def _resolve_one_upgrade_name(raw: str, by_id: dict[str, dict[str, Any]]) -> str:
    """Resolve a single CLI name to a module id key used in ``by_id`` / targets."""
    normalized = raw.strip()
    if not normalized:
        return normalized
    if normalized.count("/") > 1:
        console.print(
            f"[red]Invalid module id {normalized!r}: use owner/repo or a short name (e.g. backlog), "
            "not a multi-segment path.[/red]"
        )
        raise typer.Exit(1)
    short = normalized.split("/")[-1]
    for cand in _upgrade_name_candidates(normalized, short, by_id):
        if cand not in by_id:
            continue
        source = str(by_id[cand].get("source", "unknown"))
        if source != "marketplace":
            console.print(
                f"[red]Cannot upgrade '{cand}' from source '{source}'. Only marketplace modules are upgradeable.[/red]"
            )
            raise typer.Exit(1)
        return cand
    marketplace_by_id = {k: v for k, v in by_id.items() if str(v.get("source", "")) == "marketplace"}
    resolved = _resolve_marketplace_id_by_short(short, marketplace_by_id)
    if resolved is not None:
        return resolved
    console.print(f"[red]Module '{normalized}' is not installed and cannot be upgraded.[/red]")
    raise typer.Exit(1)


def _resolve_upgrade_target_ids(
    module_names: list[str] | None,
    all_flag: bool,
    modules: list[dict[str, Any]],
    by_id: dict[str, dict[str, Any]],
) -> list[str]:
    if all_flag or not module_names:
        target_ids = [str(m.get("id", "")) for m in modules if str(m.get("source", "")) == "marketplace"]
        if not target_ids:
            console.print("[yellow]No marketplace-installed modules found to upgrade.[/yellow]")
        return target_ids
    return [_resolve_one_upgrade_name(raw, by_id) for raw in module_names]


def _major_upgrade_decision(
    full_id: str,
    current_v: str,
    latest_v: str,
    *,
    yes: bool,
) -> tuple[bool, tuple[str, str, str] | None]:
    """Return (should_install, skipped_major_tuple when skipping a major bump)."""
    if not _is_major_version_increase(current_v, latest_v):
        return True, None
    if yes:
        return True, None
    if is_non_interactive():
        console.print(
            f"[yellow]Skipping major upgrade for {full_id}: {current_v} -> {latest_v} "
            "(non-interactive; use --yes to approve)[/yellow]"
        )
        return False, (full_id, current_v, latest_v)
    if not typer.confirm(
        f"Major version upgrade for {full_id} ({current_v} -> {latest_v}). Continue?",
        default=False,
    ):
        return False, (full_id, current_v, latest_v)
    return True, None


@dataclass
class _MarketplaceUpgradeAccum:
    upgraded: list[tuple[str, str, str]]
    up_to_date: list[str]
    skipped_major: list[tuple[str, str, str]]


def _run_one_marketplace_upgrade_target(
    target: str,
    by_id: dict[str, dict[str, Any]],
    latest_by_id: dict[str, str],
    *,
    yes: bool,
    accum: _MarketplaceUpgradeAccum,
) -> None:
    full_id = _full_marketplace_module_id_for_install(target)
    row = _upgrade_row_for_target(target, by_id)
    current_v = str(row.get("version", "unknown")).strip()
    latest_v = str(row.get("latest_version") or "").strip()
    if not latest_v:
        latest_v = (latest_by_id.get(full_id, "") or "").strip()

    if latest_v and _versions_equal_for_upgrade(current_v, latest_v):
        accum.up_to_date.append(full_id)
        return

    if not latest_v:
        with _module_upgrade_status(f"[cyan]Upgrading[/cyan] [bold]{full_id}[/bold] …"):
            installed_path = install_module(full_id, InstallModuleOptions(reinstall=True))
        accum.upgraded.append((full_id, current_v, _read_installed_module_version(installed_path)))
        return

    should_install, skip_tuple = _major_upgrade_decision(full_id, current_v, latest_v, yes=yes)
    if skip_tuple is not None:
        accum.skipped_major.append(skip_tuple)
    if should_install:
        with _module_upgrade_status(f"[cyan]Upgrading[/cyan] [bold]{full_id}[/bold] …"):
            installed_path = install_module(full_id, InstallModuleOptions(reinstall=True))
        accum.upgraded.append((full_id, current_v, _read_installed_module_version(installed_path)))


def _run_marketplace_upgrades(
    target_ids: list[str],
    by_id: dict[str, dict[str, Any]],
    latest_by_id: dict[str, str],
    *,
    yes: bool = False,
) -> None:
    upgraded: list[tuple[str, str, str]] = []
    up_to_date: list[str] = []
    skipped_major: list[tuple[str, str, str]] = []
    failed: list[str] = []
    accum = _MarketplaceUpgradeAccum(
        upgraded=upgraded,
        up_to_date=up_to_date,
        skipped_major=skipped_major,
    )

    for target in target_ids:
        try:
            _run_one_marketplace_upgrade_target(target, by_id, latest_by_id, yes=yes, accum=accum)
        except Exception as exc:
            console.print(f"[red]Failed upgrading {target}: {exc}[/red]")
            failed.append(target)

    if upgraded:
        console.print("[green]Upgraded:[/green]")
        for module_id, previous_version, new_version in upgraded:
            console.print(f"  {module_id}: {previous_version} -> {new_version}")

    if up_to_date:
        if upgraded or skipped_major:
            console.print("[green]Already up to date:[/green]")
            for mid in up_to_date:
                console.print(f"  {mid}")
        else:
            console.print("[green]All modules are up to date.[/green]")

    if skipped_major:
        console.print("[yellow]Skipped (major bump):[/yellow]")
        for mid, cv, lv in skipped_major:
            console.print(f"  {mid}: {cv} -> {lv}")

    if failed:
        raise typer.Exit(1)


@app.command()
@beartype
@require(_upgrade_module_names_valid, "each module name must be non-empty")
def upgrade(
    module_names: Annotated[
        list[str] | None,
        typer.Argument(help="Installed module name(s); omit to upgrade all marketplace modules"),
    ] = None,
    all: bool = typer.Option(False, "--all", help="Upgrade all installed marketplace modules"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Approve major version upgrades without prompting"),
) -> None:
    """Upgrade marketplace module(s) to latest available versions."""
    modules = get_modules_with_state()
    by_id = {str(m.get("id", "")): m for m in modules}
    target_ids = _resolve_upgrade_target_ids(module_names, all, modules, by_id)
    if not target_ids:
        return
    with _module_upgrade_status("[dim]Fetching marketplace registry index…[/dim]"):
        index = fetch_registry_index()
    if index is None:
        console.print(
            "[yellow]Marketplace registry unavailable (offline or network error). "
            "Upgrade will use installed metadata only.[/yellow]"
        )
    latest_by_id = _latest_version_map_from_registry_index(index)
    _run_marketplace_upgrades(target_ids, by_id, latest_by_id, yes=yes)


# Expose standard ModuleIOContract operations for protocol compliance discovery.
import_to_bundle = module_io_shim.import_to_bundle
export_from_bundle = module_io_shim.export_from_bundle
sync_with_bundle = module_io_shim.sync_with_bundle
validate_bundle = module_io_shim.validate_bundle


def _ensure_specfact_install_param_patch() -> None:
    """When this module is imported before ``specfact_cli.cli`` (e.g. unit tests), Typer must
    still resolve CLI params from merged install signatures instead of the thin ``install`` wrapper.
    If ``cli`` already patched ``typer.utils.get_params_from_function``, skip.

    Match by name/module because ``@app.command()`` wraps the callback, so ``func is install`` fails.
    """
    import importlib

    import typer.utils as tu

    if getattr(tu.get_params_from_function, "__name__", "") == "_specfact_get_params_from_function":
        return
    prev = tu.get_params_from_function
    _mod = "specfact_cli.modules.module_registry.src.commands"

    def _wrapped(func: Callable[..., Any]) -> Any:
        if getattr(func, "__name__", "") == "install" and getattr(func, "__module__", "") == _mod:
            return _specfact_merge_install_param_specs(prev)
        return prev(func)

    tu.get_params_from_function = _wrapped  # type: ignore[assignment]
    typer_main = cast(Any, importlib.import_module("typer.main"))
    typer_main.get_params_from_function = _wrapped  # type: ignore[assignment]


_ensure_specfact_install_param_patch()

__all__ = [
    "app",
    "export_from_bundle",
    "import_to_bundle",
    "sync_with_bundle",
    "validate_bundle",
]

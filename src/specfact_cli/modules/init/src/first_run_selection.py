"""First-run bundle selection: profiles, --install parsing, and installation (Phase 3)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require

from specfact_cli.registry.module_discovery import USER_MODULES_ROOT
from specfact_cli.registry.module_grouping import VALID_CATEGORIES


PROFILE_PRESETS: dict[str, list[str]] = {
    "solo-developer": ["specfact-codebase", "specfact-code-review"],
    "backlog-team": ["specfact-backlog", "specfact-project", "specfact-codebase"],
    "api-first-team": ["specfact-spec", "specfact-codebase"],
    "enterprise-full-stack": [
        "specfact-project",
        "specfact-backlog",
        "specfact-codebase",
        "specfact-spec",
        "specfact-govern",
    ],
}

_INSTALL_ALL_BUNDLES: tuple[str, ...] = (
    "specfact-project",
    "specfact-backlog",
    "specfact-codebase",
    "specfact-spec",
    "specfact-govern",
)

# Includes marketplace-only bundles referenced by profiles (e.g. specfact-code-review).
CANONICAL_BUNDLES: tuple[str, ...] = (*_INSTALL_ALL_BUNDLES, "specfact-code-review")

# Workflow bundles are installed from the marketplace (slim wheel has no per-command shims under ~/.specfact/modules).
MARKETPLACE_ONLY_BUNDLES: dict[str, str] = {
    "specfact-project": "nold-ai/specfact-project",
    "specfact-backlog": "nold-ai/specfact-backlog",
    "specfact-codebase": "nold-ai/specfact-codebase",
    "specfact-spec": "nold-ai/specfact-spec",
    "specfact-govern": "nold-ai/specfact-govern",
    "specfact-code-review": "nold-ai/specfact-code-review",
}

BUNDLE_ALIAS_TO_CANONICAL: dict[str, str] = {
    "project": "specfact-project",
    "backlog": "specfact-backlog",
    "codebase": "specfact-codebase",
    "code": "specfact-codebase",
    "spec": "specfact-spec",
    "govern": "specfact-govern",
}

# Optional: names of *bundled* module dirs shipped inside this CLI wheel (see module_installer). Workflow
# bundles use MARKETPLACE_ONLY_BUNDLES only — do not list Typer subcommand names here.
BUNDLE_TO_MODULE_NAMES: dict[str, list[str]] = {
    "specfact-project": [],
    "specfact-backlog": [],
    "specfact-codebase": [],
    "specfact-spec": [],
    "specfact-govern": [],
    "specfact-code-review": [],
}

BUNDLE_DEPENDENCIES: dict[str, list[str]] = {
    "specfact-spec": ["specfact-project"],
    "specfact-code-review": ["specfact-codebase"],
}

BUNDLE_DISPLAY: dict[str, str] = {
    "specfact-project": "Project lifecycle (project, plan, import, sync, migrate)",
    "specfact-backlog": "Backlog management (backlog, policy)",
    "specfact-codebase": "Codebase quality (analyze, drift, validate, repro)",
    "specfact-spec": "Spec & API (contract, spec, sdd, generate)",
    "specfact-govern": "Governance (enforce, patch)",
    "specfact-code-review": "Scored code review (code review gate)",
}


def _emit_init_bundle_progress() -> bool:
    """Return True when init should print progress (suppressed during pytest)."""
    return os.environ.get("PYTEST_CURRENT_TEST") is None


def _expand_bundle_install_order(bundle_ids: list[str]) -> list[str]:
    to_install: list[str] = []
    seen: set[str] = set()

    def _add_bundle(bid: str) -> None:
        if bid in seen:
            return
        for dep in BUNDLE_DEPENDENCIES.get(bid, []):
            _add_bundle(dep)
        seen.add(bid)
        to_install.append(bid)

    for bid in bundle_ids:
        if bid not in CANONICAL_BUNDLES:
            continue
        _add_bundle(bid)
    return to_install


@dataclass
class _InitBundleInstallDeps:
    root: Path
    trust_non_official: bool
    non_interactive: bool
    emit: bool
    console: Any
    install_bundled_module: Any
    install_module: Any


def _emit_bundle_row_header(
    bid: str,
    deps: _InitBundleInstallDeps,
    *,
    module_names: list[str],
    bundle_label: str,
    marketplace_id: str | None,
) -> None:
    if not deps.emit:
        return
    if module_names or marketplace_id:
        deps.console.print(f"[cyan]→[/cyan] Bundle [bold]{bid}[/bold] — {bundle_label}")
    else:
        deps.console.print(
            f"[yellow]→[/yellow] Bundle [bold]{bid}[/bold] has no bundled modules in this CLI; "
            f"install with [bold]specfact module install nold-ai/{bid}[/bold] when online."
        )


def _install_one_bundled_module_line(bid: str, module_name: str, deps: _InitBundleInstallDeps) -> None:
    from specfact_cli.common import get_bridge_logger

    if deps.emit:
        deps.console.print(f"[dim]   ·[/dim] Installing module [bold]{module_name}[/bold] …")
    try:
        installed = deps.install_bundled_module(
            module_name,
            deps.root,
            trust_non_official=deps.trust_non_official,
            non_interactive=deps.non_interactive,
        )
    except Exception as e:
        logger = get_bridge_logger(__name__)
        logger.warning(
            "Bundle install failed for %s: %s. Dependency resolver may be unavailable.",
            module_name,
            e,
        )
        if deps.emit:
            deps.console.print(
                f"[red]✗[/red] Failed on module [bold]{module_name}[/bold] from bundle [bold]{bid}[/bold]: {e}"
            )
            deps.console.print(
                "[dim]  Check disk space and permissions under ~/.specfact/modules, "
                "or retry if a transient I/O error.[/dim]"
            )
        raise
    if installed:
        if deps.emit:
            deps.console.print(f"[green]   ✓[/green] {module_name} ready")
    elif deps.emit:
        deps.console.print(
            f"[yellow]   ⚠[/yellow] {module_name} is not bundled in this CLI build; "
            f"try [bold]specfact module install nold-ai/{bid}[/bold] when online."
        )


def _install_marketplace_for_bundle(bid: str, marketplace_id: str, deps: _InitBundleInstallDeps) -> None:
    from specfact_cli.common import get_bridge_logger
    from specfact_cli.registry.module_installer import InstallModuleOptions

    if deps.emit:
        deps.console.print(f"[dim]   ·[/dim] Installing marketplace module [bold]{marketplace_id}[/bold] …")
    try:
        deps.install_module(
            marketplace_id,
            options=InstallModuleOptions(
                install_root=deps.root,
                non_interactive=deps.non_interactive,
                trust_non_official=deps.trust_non_official,
            ),
        )
    except Exception as e:
        logger = get_bridge_logger(__name__)
        logger.warning(
            "Marketplace bundle install failed for %s: %s.",
            marketplace_id,
            e,
        )
        if deps.emit:
            deps.console.print(
                f"[red]✗[/red] Failed on marketplace module [bold]{marketplace_id}[/bold] "
                f"from bundle [bold]{bid}[/bold]: {e}"
            )
            deps.console.print(
                "[dim]  Check network access and permissions under ~/.specfact/modules, "
                "or retry if a transient error.[/dim]"
            )
        raise
    if deps.emit:
        deps.console.print(f"[green]   ✓[/green] {marketplace_id.split('/', 1)[1]} ready")


def _process_one_bundle_install_row(bid: str, deps: _InitBundleInstallDeps) -> None:
    """Install bundled and/or marketplace modules for one canonical bundle id."""
    module_names = BUNDLE_TO_MODULE_NAMES.get(bid, [])
    bundle_label = BUNDLE_DISPLAY.get(bid, bid)
    marketplace_id = MARKETPLACE_ONLY_BUNDLES.get(bid)
    _emit_bundle_row_header(
        bid,
        deps,
        module_names=module_names,
        bundle_label=bundle_label,
        marketplace_id=marketplace_id,
    )
    for module_name in module_names:
        _install_one_bundled_module_line(bid, module_name, deps)
    if not marketplace_id:
        return
    _install_marketplace_for_bundle(bid, marketplace_id, deps)


@require(lambda profile: isinstance(profile, str) and profile.strip() != "", "profile must be non-empty string")
@ensure(lambda result: isinstance(result, list), "result must be list of bundle ids")
@beartype
def resolve_profile_bundles(profile: str) -> list[str]:
    """Resolve a profile name to the list of canonical bundle ids to install."""
    key = profile.strip().lower()
    if key not in PROFILE_PRESETS:
        valid = ", ".join(sorted(PROFILE_PRESETS))
        raise ValueError(f"Unknown profile {profile!r}. Valid profiles: {valid}")
    return list(PROFILE_PRESETS[key])


@require(lambda install_arg: isinstance(install_arg, str), "install_arg must be string")
@ensure(lambda result: isinstance(result, list), "result must be list of bundle ids")
@beartype
def resolve_install_bundles(install_arg: str) -> list[str]:
    """Parse --install value (comma-separated or 'all') into canonical bundle ids."""
    raw = install_arg.strip()
    if not raw:
        return []
    if raw.lower() == "all":
        return list(_INSTALL_ALL_BUNDLES)
    seen: set[str] = set()
    result: list[str] = []
    for part in raw.split(","):
        alias = part.strip().lower()
        if not alias:
            continue
        if alias in BUNDLE_ALIAS_TO_CANONICAL:
            canonical = BUNDLE_ALIAS_TO_CANONICAL[alias]
            if canonical not in seen:
                seen.add(canonical)
                result.append(canonical)
        else:
            valid = ", ".join([*sorted(BUNDLE_ALIAS_TO_CANONICAL), "all"])
            raise ValueError(f"Unknown bundle {part.strip()!r}. Valid bundle names: {valid}")
    return result


@ensure(lambda result: isinstance(result, bool), "result must be bool")
@beartype
def is_first_run(
    *,
    user_root: Path | None = None,
) -> bool:
    """Return True when no category bundle is installed (first run)."""
    from specfact_cli.registry.module_discovery import discover_all_modules

    root = user_root or USER_MODULES_ROOT
    discovered = discover_all_modules(user_root=root)
    for entry in discovered:
        if entry.source not in ("user", "marketplace", "project"):
            continue
        cat = entry.metadata.category
        if cat is not None and cat != "core" and cat in VALID_CATEGORIES:
            return False
    return True


@require(lambda bundle_ids: isinstance(bundle_ids, list), "bundle_ids must be list")
@require(
    lambda install_root: install_root is None or isinstance(install_root, Path), "install_root must be Path or None"
)
@beartype
def install_bundles_for_init(
    bundle_ids: list[str],
    install_root: Path | None = None,
    *,
    non_interactive: bool = False,
    trust_non_official: bool = False,
    show_progress: bool = True,
) -> None:
    """Install the given bundles (and their dependencies) via bundled module installer."""
    from rich.console import Console

    from specfact_cli.registry.module_installer import (
        USER_MODULES_ROOT as DEFAULT_ROOT,
        install_bundled_module,
        install_module,
    )

    root = install_root or DEFAULT_ROOT
    emit = show_progress and _emit_init_bundle_progress()
    console = Console()
    to_install = _expand_bundle_install_order(bundle_ids)
    deps = _InitBundleInstallDeps(
        root=root,
        trust_non_official=trust_non_official,
        non_interactive=non_interactive,
        emit=emit,
        console=console,
        install_bundled_module=install_bundled_module,
        install_module=install_module,
    )

    if emit and to_install:
        bundle_list = ", ".join(to_install)
        console.print(f"[cyan]→[/cyan] Seeding workflow bundles: [bold]{bundle_list}[/bold]")
        console.print("[dim]  (copying bundled modules into your user module directory)[/dim]")

    for bid in to_install:
        _process_one_bundle_install_row(bid, deps)

    if emit and to_install:
        console.print(f"[green]✓[/green] Installed: {', '.join(to_install)}")


@ensure(lambda result: isinstance(result, list) and len(result) > 0, "Must return non-empty list of profile names")
def get_valid_profile_names() -> list[str]:
    """Return sorted list of valid profile names for error messages."""
    return sorted(PROFILE_PRESETS)


@ensure(lambda result: isinstance(result, list) and len(result) > 0, "Must return non-empty list of bundle aliases")
def get_valid_bundle_aliases() -> list[str]:
    """Return sorted list of valid bundle aliases (including 'all')."""
    return [*sorted(BUNDLE_ALIAS_TO_CANONICAL), "all"]


PROFILE_DISPLAY_ORDER: list[tuple[str, str]] = [
    ("solo-developer", "Solo developer"),
    ("backlog-team", "Backlog team"),
    ("api-first-team", "API-first team"),
    ("enterprise-full-stack", "Enterprise full-stack"),
]

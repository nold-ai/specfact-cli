"""Shared module lifecycle operations for init and module commands."""

from __future__ import annotations

from typing import Any

from beartype import beartype
from rich.console import Console
from rich.table import Table

from specfact_cli import __version__
from specfact_cli.registry.help_cache import run_discovery_and_write_cache
from specfact_cli.registry.module_discovery import discover_all_modules
from specfact_cli.registry.module_packages import (
    discover_all_package_metadata,
    expand_disable_with_dependents,
    expand_enable_with_dependencies,
    merge_module_state,
    validate_disable_safe,
    validate_enable_safe,
)
from specfact_cli.registry.module_state import read_modules_state, write_modules_state


def _sort_modules_by_id(modules_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return modules sorted alphabetically by module id (case-insensitive)."""
    return sorted(modules_list, key=lambda module: str(module.get("id", "")).lower())


@beartype
def get_modules_with_state(
    enable_ids: list[str] | None = None,
    disable_ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Return discovered modules with version, enabled state, source, and trust metadata."""
    discovered = discover_all_modules()
    discovered_list: list[tuple[str, str]] = [(entry.metadata.name, entry.metadata.version) for entry in discovered]
    state = read_modules_state()
    enabled_map = merge_module_state(discovered_list, state, enable_ids or [], disable_ids or [])

    modules_list: list[dict[str, Any]] = []
    for entry in discovered:
        publisher_name = entry.metadata.publisher.name if entry.metadata.publisher else "unknown"
        modules_list.append(
            {
                "id": entry.metadata.name,
                "version": entry.metadata.version,
                "enabled": enabled_map.get(entry.metadata.name, True),
                "source": entry.source,
                "official": bool(publisher_name.strip().lower() == "nold-ai"),
                "publisher": publisher_name,
            }
        )
    return modules_list


@beartype
def apply_module_state_update(*, enable_ids: list[str], disable_ids: list[str], force: bool) -> list[dict[str, Any]]:
    """Apply lifecycle updates with dependency safety and return resulting module state."""
    packages = discover_all_package_metadata()
    discovered_list = [(meta.name, meta.version) for _package_dir, meta in packages]
    state = read_modules_state()
    if force and enable_ids:
        enable_ids = expand_enable_with_dependencies(enable_ids, packages)
    enabled_map = merge_module_state(discovered_list, state, enable_ids, [])
    if enable_ids and not force:
        blocked_enable = validate_enable_safe(enable_ids, packages, enabled_map)
        if blocked_enable:
            lines: list[str] = []
            for module_id, missing in blocked_enable.items():
                lines.append(f"Cannot enable '{module_id}': missing required dependencies: {', '.join(missing)}")
            raise ValueError("\n".join(lines))
    if disable_ids:
        if force:
            disable_ids = expand_disable_with_dependents(disable_ids, packages, enabled_map)
        blocked_disable = validate_disable_safe(disable_ids, packages, enabled_map)
        if blocked_disable and not force:
            lines = []
            for module_id, dependents in blocked_disable.items():
                lines.append(f"Cannot disable '{module_id}': required by enabled modules: {', '.join(dependents)}")
            raise ValueError("\n".join(lines))
    final_enabled_map = merge_module_state(discovered_list, state, enable_ids, disable_ids)
    modules_list = [
        {"id": meta.name, "version": meta.version, "enabled": final_enabled_map.get(meta.name, True)}
        for _package_dir, meta in packages
    ]
    write_modules_state(modules_list)
    run_discovery_and_write_cache(__version__)
    return get_modules_with_state()


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


@beartype
def render_modules_table(console: Console, modules_list: list[dict[str, Any]], show_origin: bool = False) -> None:
    """Render module table with id, version, state, trust, publisher, and optional origin."""
    table = Table(title="Installed Modules")
    table.add_column("Module", style="cyan")
    table.add_column("Version", style="magenta")
    table.add_column("State", style="green")
    table.add_column("Trust", style="yellow")
    table.add_column("Publisher", style="bright_blue")
    if show_origin:
        table.add_column("Origin", style="blue")
    for module in _sort_modules_by_id(modules_list):
        module_id = str(module.get("id", ""))
        version = str(module.get("version", ""))
        enabled = bool(module.get("enabled", True))
        state = "enabled" if enabled else "disabled"
        source = str(module.get("source", "unknown"))
        if bool(module.get("official", False)):
            trust_label = "official"
        elif source == "marketplace":
            trust_label = "community"
        else:
            trust_label = "local-dev"

        publisher_label = str(module.get("publisher", "unknown"))
        origin_label = "built-in" if source == "builtin" else source
        if show_origin:
            table.add_row(module_id, version, state, trust_label, publisher_label, origin_label)
        else:
            table.add_row(module_id, version, state, trust_label, publisher_label)
    console.print(table)


@beartype
def select_module_ids_interactive(action: str, modules_list: list[dict[str, Any]], console: Console) -> list[str]:
    """Select module ids interactively for enable/disable operations."""
    try:
        import questionary  # type: ignore[reportMissingImports]
    except ImportError as exc:
        console.print(
            "[red]Interactive module selection requires 'questionary'. Install with: pip install questionary[/red]"
        )
        raise RuntimeError("questionary is required for interactive module selection") from exc
    target_enabled = action == "disable"
    candidates = [m for m in _sort_modules_by_id(modules_list) if bool(m.get("enabled", True)) is target_enabled]
    if not candidates:
        console.print(f"[yellow]No modules available to {action}.[/yellow]")
        return []
    action_title = "Enable" if action == "enable" else "Disable"
    current_state = "disabled" if action == "enable" else "enabled"
    console.print()
    console.print(f"[cyan]{action_title} Modules[/cyan] (currently {current_state})")
    console.print("[dim]Controls: arrows navigate, space toggle, enter confirm[/dim]")
    display_to_id: dict[str, str] = {}
    choices: list[str] = []
    for module in candidates:
        module_id = str(module.get("id", ""))
        version = str(module.get("version", ""))
        source = str(module.get("source", "unknown"))
        source_label = "official" if bool(module.get("official", False)) else source
        state = "enabled" if bool(module.get("enabled", True)) else "disabled"
        marker = "✓" if state == "enabled" else "✗"
        display = f"{marker} {module_id:<18} [{state}] v{version} ({source_label})"
        display_to_id[display] = module_id
        choices.append(display)
    selected: list[str] | None = questionary.checkbox(
        f"{action_title} module(s):",
        choices=choices,
        instruction="(multi-select)",
        style=_questionary_style(),
    ).ask()
    if not selected:
        return []
    return [display_to_id[item] for item in selected if item in display_to_id]

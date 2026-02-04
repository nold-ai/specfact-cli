"""
Module packages: discover packages under modules root and register with CommandRegistry.

Each package has module-package.yaml (name, version, commands), src/, optional resources/ and tests/.
Only enabled modules (from modules.json) are registered.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

from beartype import beartype
from pydantic import BaseModel, Field

from specfact_cli.registry.metadata import CommandMetadata
from specfact_cli.registry.module_state import read_modules_state
from specfact_cli.registry.registry import CommandRegistry


class ModulePackageMetadata(BaseModel):
    """Schema for a module package's module-package.yaml."""

    name: str = Field(..., description="Package identifier (e.g. backlog_refine)")
    version: str = Field(default="0.1.0", description="Package version")
    commands: list[str] = Field(default_factory=list, description="Command names this package provides")
    command_help: dict[str, str] | None = Field(
        default=None, description="Optional command name -> help text for root help"
    )
    pip_dependencies: list[str] = Field(default_factory=list, description="Optional pip dependencies")
    module_dependencies: list[str] = Field(default_factory=list, description="Optional other package ids")
    tier: str = Field(default="community", description="Tier: community or enterprise")
    addon_id: str | None = Field(default=None, description="Optional addon identifier")


# Display order for core modules (formerly built-in); others follow alphabetically.
CORE_MODULE_ORDER: tuple[str, ...] = (
    "init",
    "auth",
    "backlog",
    "import_cmd",
    "migrate",
    "plan",
    "project",
    "generate",
    "enforce",
    "repro",
    "sdd",
    "spec",
    "contract",
    "sync",
    "drift",
    "analyze",
    "validate",
    "upgrade",
)


def get_modules_root() -> Path:
    """Return the modules root path (specfact_cli package dir / modules)."""
    import specfact_cli

    pkg_dir = Path(specfact_cli.__path__[0]).resolve()
    return pkg_dir / "modules"


def _package_sort_key(item: tuple[Path, ModulePackageMetadata]) -> tuple[int, str]:
    """Sort key: core modules by CORE_MODULE_ORDER index, then by name."""
    _dir, meta = item
    try:
        idx = CORE_MODULE_ORDER.index(meta.name)
        return (idx, meta.name)
    except ValueError:
        return (len(CORE_MODULE_ORDER), meta.name)


@beartype
def discover_package_metadata(modules_root: Path) -> list[tuple[Path, ModulePackageMetadata]]:
    """
    Scan modules root for package dirs that have module-package.yaml; parse and return (dir, metadata).
    """
    result: list[tuple[Path, ModulePackageMetadata]] = []
    if not modules_root.exists() or not modules_root.is_dir():
        return result
    try:
        import yaml
    except ImportError:
        return result
    for child in sorted(modules_root.iterdir()):
        if not child.is_dir():
            continue
        meta_file = child / "module-package.yaml"
        if not meta_file.exists():
            meta_file = child / "metadata.yaml"
        if not meta_file.exists():
            continue
        try:
            raw = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(raw, dict) or "name" not in raw or "commands" not in raw:
            continue
        try:
            raw_help = raw.get("command_help")
            command_help = None
            if isinstance(raw_help, dict):
                command_help = {str(k): str(v) for k, v in raw_help.items()}
            meta = ModulePackageMetadata(
                name=str(raw["name"]),
                version=str(raw.get("version", "0.1.0")),
                commands=[str(c) for c in raw.get("commands", [])],
                command_help=command_help,
                pip_dependencies=[str(d) for d in raw.get("pip_dependencies", [])],
                module_dependencies=[str(d) for d in raw.get("module_dependencies", [])],
                tier=str(raw.get("tier", "community")),
                addon_id=str(raw["addon_id"]) if raw.get("addon_id") else None,
            )
            result.append((child, meta))
        except Exception:
            continue
    return result


def _make_package_loader(package_dir: Path, package_name: str, _command_name: str) -> Any:
    """Return a callable that loads the package's app (from src/app.py or src/<name>/__init__.py)."""

    def loader() -> Any:
        src_dir = package_dir / "src"
        if not src_dir.exists():
            raise ValueError(f"Package {package_dir.name} has no src/")
        load_path: Path | None = None
        if (src_dir / "app.py").exists():
            load_path = src_dir / "app.py"
        elif (src_dir / f"{package_name}.py").exists():
            load_path = src_dir / f"{package_name}.py"
        elif (src_dir / package_name / "__init__.py").exists():
            load_path = src_dir / package_name / "__init__.py"
        if load_path is None:
            raise ValueError(
                f"Package {package_dir.name} has no src/app.py, src/{package_name}.py or src/{package_name}/"
            )
        submodule_locations = [str(load_path.parent)] if load_path.name == "__init__.py" else None
        spec = importlib.util.spec_from_file_location(
            f"specfact_cli.modules.{package_dir.name}.app",
            load_path,
            submodule_search_locations=submodule_locations,
        )
        if spec is None or spec.loader is None:
            raise ValueError(f"Cannot load from {package_dir.name}")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        app = getattr(mod, "app", None)
        if app is None:
            raise ValueError(f"Package {package_dir.name} has no 'app' attribute")
        return app

    return loader


def merge_module_state(
    discovered: list[tuple[str, str]],
    state: dict[str, dict[str, Any]],
    enable_ids: list[str],
    disable_ids: list[str],
) -> dict[str, bool]:
    """
    Merge discovered (id, version) with state; apply enable/disable overrides.
    Returns dict module_id -> enabled (bool).
    """
    merged: dict[str, bool] = {}
    for mid, _version in discovered:
        if mid in state:
            merged[mid] = state[mid].get("enabled", True)
        else:
            merged[mid] = True
    for mid in enable_ids:
        merged[mid] = True
    for mid in disable_ids:
        merged[mid] = False
    return merged


def register_module_package_commands(
    enable_ids: list[str] | None = None,
    disable_ids: list[str] | None = None,
) -> None:
    """
    Discover module packages, merge with modules.json state, register only enabled packages' commands.

    Call after register_builtin_commands(). enable_ids/disable_ids from CLI (--enable-module/--disable-module).
    """
    enable_ids = enable_ids or []
    disable_ids = disable_ids or []
    modules_root = get_modules_root()
    packages = discover_package_metadata(modules_root)
    packages = sorted(packages, key=_package_sort_key)
    if not packages:
        return
    discovered_list: list[tuple[str, str]] = [(meta.name, meta.version) for _dir, meta in packages]
    state = read_modules_state()
    enabled_map = merge_module_state(discovered_list, state, enable_ids, disable_ids)
    for package_dir, meta in packages:
        if not enabled_map.get(meta.name, True):
            continue
        for cmd_name in meta.commands:
            help_str = (meta.command_help or {}).get(cmd_name) or f"Module package: {meta.name}"
            loader = _make_package_loader(package_dir, meta.name, cmd_name)
            cmd_meta = CommandMetadata(name=cmd_name, help=help_str, tier=meta.tier, addon_id=meta.addon_id)
            CommandRegistry.register(cmd_name, loader, cmd_meta)


def get_discovered_modules_for_state(
    enable_ids: list[str] | None = None,
    disable_ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Discover packages, merge with state, apply overrides; return list for modules.json.
    Does not register commands; use for writing state after init.
    """
    enable_ids = enable_ids or []
    disable_ids = disable_ids or []
    modules_root = get_modules_root()
    packages = discover_package_metadata(modules_root)
    packages = sorted(packages, key=_package_sort_key)
    discovered_list = [(meta.name, meta.version) for _dir, meta in packages]
    state = read_modules_state()
    enabled_map = merge_module_state(discovered_list, state, enable_ids, disable_ids)
    return [
        {"id": meta.name, "version": meta.version, "enabled": enabled_map.get(meta.name, True)}
        for _dir, meta in packages
    ]

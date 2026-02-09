"""
Module packages: discover packages under modules root and register with CommandRegistry.

Each package has module-package.yaml (name, version, commands), src/, optional resources/ and tests/.
Only enabled modules (from modules.json) are registered.
"""

from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require
from packaging.specifiers import SpecifierSet
from packaging.version import InvalidVersion, Version

from specfact_cli import __version__ as cli_version
from specfact_cli.common import get_bridge_logger
from specfact_cli.models.module_package import ModulePackageMetadata, ServiceBridgeMetadata
from specfact_cli.registry.bridge_registry import BridgeRegistry, SchemaConverter
from specfact_cli.registry.metadata import CommandMetadata
from specfact_cli.registry.module_state import find_dependents, read_modules_state
from specfact_cli.registry.registry import CommandRegistry


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
CURRENT_PROJECT_SCHEMA_VERSION = "1"
PROTOCOL_METHODS: dict[str, str] = {
    "import": "import_to_bundle",
    "export": "export_from_bundle",
    "sync": "sync_with_bundle",
    "validate": "validate_bundle",
}
BRIDGE_REGISTRY = BridgeRegistry()


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
            validated_service_bridges: list[ServiceBridgeMetadata] = []
            for bridge_entry in raw.get("service_bridges", []) or []:
                try:
                    validated_service_bridges.append(ServiceBridgeMetadata.model_validate(bridge_entry))
                except Exception:
                    # Keep startup resilient: malformed bridge declarations are skipped later.
                    continue
            meta = ModulePackageMetadata(
                name=str(raw["name"]),
                version=str(raw.get("version", "0.1.0")),
                commands=[str(c) for c in raw.get("commands", [])],
                command_help=command_help,
                pip_dependencies=[str(d) for d in raw.get("pip_dependencies", [])],
                module_dependencies=[str(d) for d in raw.get("module_dependencies", [])],
                core_compatibility=str(raw["core_compatibility"]) if raw.get("core_compatibility") else None,
                tier=str(raw.get("tier", "community")),
                addon_id=str(raw["addon_id"]) if raw.get("addon_id") else None,
                schema_version=str(raw["schema_version"]) if raw.get("schema_version") is not None else None,
                service_bridges=validated_service_bridges,
            )
            result.append((child, meta))
        except Exception:
            continue
    return result


@beartype
@require(lambda class_path: class_path.strip() != "", "Converter class path must not be empty")
@ensure(lambda result: isinstance(result, type), "Resolved converter must be a class")
def _resolve_converter_class(class_path: str) -> type[SchemaConverter]:
    """Resolve a converter class from dotted path."""
    module_path, class_name = class_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    converter_class = getattr(module, class_name)
    if not isinstance(converter_class, type):
        raise TypeError(f"Converter path '{class_path}' did not resolve to a class.")
    return converter_class


@beartype
def _check_core_compatibility(meta: ModulePackageMetadata, current_cli_version: str) -> bool:
    """Return True when module is compatible with the running CLI core version."""
    if not meta.core_compatibility:
        return True
    try:
        specifier = SpecifierSet(meta.core_compatibility)
        return Version(current_cli_version) in specifier
    except (InvalidVersion, Exception):
        # Keep malformed metadata non-blocking; emit details in debug logs at call site.
        return True


@beartype
def _validate_module_dependencies(
    meta: ModulePackageMetadata,
    enabled_map: dict[str, bool],
) -> tuple[bool, list[str]]:
    """Validate that declared dependencies exist and are enabled."""
    missing: list[str] = []
    for dep_id in meta.module_dependencies:
        if dep_id not in enabled_map:
            missing.append(f"{dep_id} (not found)")
        elif not enabled_map[dep_id]:
            missing.append(f"{dep_id} (disabled)")
    return len(missing) == 0, missing


@beartype
def validate_disable_safe(
    disable_ids: list[str],
    packages: list[tuple[Path, ModulePackageMetadata]],
    enabled_map: dict[str, bool],
) -> dict[str, list[str]]:
    """
    Return blocked disable requests mapped to enabled dependents.

    Empty dict means all disables are safe.
    """
    effective_map = {**enabled_map}
    for mid in disable_ids:
        effective_map[mid] = False

    blocked: dict[str, list[str]] = {}
    for mid in disable_ids:
        dependents = find_dependents(mid, packages, effective_map)
        if dependents:
            blocked[mid] = dependents
    return blocked


@beartype
def validate_enable_safe(
    enable_ids: list[str],
    packages: list[tuple[Path, ModulePackageMetadata]],
    enabled_map: dict[str, bool],
) -> dict[str, list[str]]:
    """
    Return blocked enable requests mapped to unmet dependencies.

    Empty dict means all enables are dependency-safe in the effective map.
    """
    meta_by_name: dict[str, ModulePackageMetadata] = {meta.name: meta for _package_dir, meta in packages}
    blocked: dict[str, list[str]] = {}
    for mid in enable_ids:
        meta = meta_by_name.get(mid)
        if meta is None:
            blocked[mid] = ["module not found"]
            continue
        deps_ok, missing = _validate_module_dependencies(meta, enabled_map)
        if not deps_ok:
            blocked[mid] = missing
    return blocked


@beartype
def expand_disable_with_dependents(
    disable_ids: list[str],
    packages: list[tuple[Path, ModulePackageMetadata]],
    enabled_map: dict[str, bool],
) -> list[str]:
    """
    Expand disable set with transitive enabled dependents.

    Used by --force mode so disabling a dependency provider also disables
    modules that depend on it.
    """
    reverse_deps: dict[str, set[str]] = {}
    for _package_dir, meta in packages:
        name = meta.name
        for dep in meta.module_dependencies:
            reverse_deps.setdefault(dep, set()).add(name)

    expanded: set[str] = set(disable_ids)
    queue = list(disable_ids)
    while queue:
        current = queue.pop(0)
        for dependent in sorted(reverse_deps.get(current, set())):
            if dependent in expanded:
                continue
            if not enabled_map.get(dependent, True):
                continue
            expanded.add(dependent)
            queue.append(dependent)
    return list(expanded)


@beartype
def expand_enable_with_dependencies(
    enable_ids: list[str],
    packages: list[tuple[Path, ModulePackageMetadata]],
) -> list[str]:
    """
    Expand enable set with transitive dependencies.

    Used by --force mode so enabling a module also enables required upstream
    dependency providers.
    """
    dep_map: dict[str, list[str]] = {meta.name: list(meta.module_dependencies) for _package_dir, meta in packages}
    expanded: set[str] = set(enable_ids)
    queue = list(enable_ids)
    while queue:
        current = queue.pop(0)
        for dep in dep_map.get(current, []):
            if dep in expanded:
                continue
            expanded.add(dep)
            queue.append(dep)
    return list(expanded)


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


def _resolve_package_load_path(package_dir: Path, package_name: str) -> Path:
    """Resolve a package entrypoint module path."""
    src_dir = package_dir / "src"
    if not src_dir.exists():
        raise ValueError(f"Package {package_dir.name} has no src/")
    if (src_dir / "app.py").exists():
        return src_dir / "app.py"
    if (src_dir / f"{package_name}.py").exists():
        return src_dir / f"{package_name}.py"
    if (src_dir / package_name / "__init__.py").exists():
        return src_dir / package_name / "__init__.py"
    raise ValueError(f"Package {package_dir.name} has no src/app.py, src/{package_name}.py or src/{package_name}/")


def _load_package_module(package_dir: Path, package_name: str) -> Any:
    """Load and return a module package entrypoint module."""
    load_path = _resolve_package_load_path(package_dir, package_name)
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
    return mod


@beartype
@require(lambda module_class: module_class is not None, "Module class must be provided")
@ensure(lambda result: isinstance(result, list), "Protocol operation list must be returned")
def _check_protocol_compliance(module_class: Any) -> list[str]:
    """Return supported protocol operations based on available attributes."""
    operations: list[str] = []
    for operation, method_name in PROTOCOL_METHODS.items():
        if hasattr(module_class, method_name):
            operations.append(operation)
    return operations


@beartype
@require(lambda package_name: package_name.strip() != "", "Package name must not be empty")
@ensure(lambda result: result is not None, "Protocol inspection target must be resolved")
def _resolve_protocol_target(module_obj: Any, package_name: str) -> Any:
    """Resolve runtime interface used for protocol inspection."""
    runtime_interface = getattr(module_obj, "runtime_interface", None)
    if runtime_interface is not None:
        return runtime_interface
    commands_interface = getattr(module_obj, "commands", None)
    if commands_interface is not None:
        return commands_interface
    # Module app entrypoints often only expose `app`; load module-local commands for protocol detection.
    try:
        commands_module = importlib.import_module(f"specfact_cli.modules.{package_name}.src.commands")
        return commands_module
    except Exception:
        pass
    return module_obj


@beartype
@ensure(lambda result: isinstance(result, bool), "Schema compatibility check must return bool")
def _check_schema_compatibility(module_schema: str | None, current: str) -> bool:
    """Return True when module schema is compatible with current ProjectBundle schema."""
    if module_schema is None:
        return True
    return module_schema.strip() == current.strip()


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
    logger = get_bridge_logger(__name__)
    skipped: list[tuple[str, str]] = []
    protocol_full = 0
    protocol_partial = 0
    protocol_legacy = 0
    bridge_owner_map: dict[str, str] = {
        bridge_id: BRIDGE_REGISTRY.get_owner(bridge_id) or "unknown" for bridge_id in BRIDGE_REGISTRY.list_bridge_ids()
    }
    for package_dir, meta in packages:
        if not enabled_map.get(meta.name, True):
            continue
        compatible = _check_core_compatibility(meta, cli_version)
        if not compatible:
            skipped.append((meta.name, f"requires {meta.core_compatibility}, cli is {cli_version}"))
            continue
        deps_ok, missing = _validate_module_dependencies(meta, enabled_map)
        if not deps_ok:
            skipped.append((meta.name, f"missing dependencies: {', '.join(missing)}"))
            continue
        if not _check_schema_compatibility(meta.schema_version, CURRENT_PROJECT_SCHEMA_VERSION):
            skipped.append(
                (
                    meta.name,
                    f"schema version {meta.schema_version} required, current is {CURRENT_PROJECT_SCHEMA_VERSION}",
                )
            )
            logger.warning(
                "Module %s: Schema version %s required, but current is %s (skipped)",
                meta.name,
                meta.schema_version,
                CURRENT_PROJECT_SCHEMA_VERSION,
            )
            continue
        if meta.schema_version is None:
            logger.debug("Module %s: No schema version declared (assuming current)", meta.name)
        else:
            logger.info("Module %s: Schema version %s (compatible)", meta.name, meta.schema_version)

        for bridge in meta.validate_service_bridges():
            existing_owner = bridge_owner_map.get(bridge.id)
            if existing_owner:
                logger.warning(
                    "Duplicate bridge ID '%s' declared by module '%s'; already declared by '%s' (skipped).",
                    bridge.id,
                    meta.name,
                    existing_owner,
                )
                continue
            try:
                converter_class = _resolve_converter_class(bridge.converter_class)
                converter: SchemaConverter = converter_class()
                BRIDGE_REGISTRY.register_converter(bridge.id, converter, meta.name)
                bridge_owner_map[bridge.id] = meta.name
            except Exception as exc:
                logger.warning(
                    "Module %s: Skipping bridge '%s' (converter: %s): %s",
                    meta.name,
                    bridge.id,
                    bridge.converter_class,
                    exc,
                )

        try:
            module_obj = _load_package_module(package_dir, meta.name)
            protocol_target = _resolve_protocol_target(module_obj, meta.name)
            operations = _check_protocol_compliance(protocol_target)  # type: ignore[arg-type]
            meta.protocol_operations = operations
            if len(operations) == 4:
                logger.info("Module %s: ModuleIOContract fully implemented", meta.name)
                protocol_full += 1
            elif operations:
                logger.info("Module %s: ModuleIOContract partial (%s)", meta.name, ", ".join(operations))
                protocol_partial += 1
            else:
                logger.warning("Module %s: No ModuleIOContract (legacy mode)", meta.name)
                protocol_legacy += 1
        except Exception as exc:
            logger.warning("Module %s: Unable to inspect protocol compliance (%s)", meta.name, exc)
            meta.protocol_operations = []
            protocol_legacy += 1

        for cmd_name in meta.commands:
            help_str = (meta.command_help or {}).get(cmd_name) or f"Module package: {meta.name}"
            loader = _make_package_loader(package_dir, meta.name, cmd_name)
            cmd_meta = CommandMetadata(name=cmd_name, help=help_str, tier=meta.tier, addon_id=meta.addon_id)
            CommandRegistry.register(cmd_name, loader, cmd_meta)
    discovered_count = protocol_full + protocol_partial + protocol_legacy
    if discovered_count:
        logger.info(
            "Protocol-compliant: %s/%s modules (Full=%s, Partial=%s, Legacy=%s)",
            protocol_full + protocol_partial,
            discovered_count,
            protocol_full,
            protocol_partial,
            protocol_legacy,
        )
    for module_id, reason in skipped:
        logger.debug("Skipped module '%s': %s", module_id, reason)


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

"""
Module packages: discover packages under modules root and register with CommandRegistry.

Each package has module-package.yaml (name, version, commands), src/, optional resources/ and tests/.
Only enabled modules (from modules.json) are registered.

CrossHair: skip (dynamic imports and module loading are intentionally side-effectful)
"""

from __future__ import annotations

import ast
import importlib
import importlib.util
import os
import sys
from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require
from packaging.specifiers import SpecifierSet
from packaging.version import InvalidVersion, Version

from specfact_cli import __version__ as cli_version
from specfact_cli.common import get_bridge_logger
from specfact_cli.models.module_package import (
    IntegrityInfo,
    ModulePackageMetadata,
    PublisherInfo,
    SchemaExtension,
    ServiceBridgeMetadata,
    VersionedModuleDependency,
    VersionedPipDependency,
)
from specfact_cli.registry.bridge_registry import BridgeRegistry, SchemaConverter
from specfact_cli.registry.extension_registry import get_extension_registry
from specfact_cli.registry.metadata import CommandMetadata
from specfact_cli.registry.module_grouping import (
    ModuleManifestError,
    normalize_legacy_bundle_group_command,
    validate_module_category_manifest,
)
from specfact_cli.registry.module_installer import verify_module_artifact
from specfact_cli.registry.module_state import find_dependents, read_modules_state
from specfact_cli.registry.registry import CommandRegistry
from specfact_cli.runtime import is_debug_mode
from specfact_cli.utils.prompts import print_warning


# Display order for core modules (3 after migration-03); others follow alphabetically.
CORE_NAMES = ("init", "module", "upgrade")
CORE_MODULE_ORDER: tuple[str, ...] = (
    "init",
    "module-registry",
    "upgrade",
)
CURRENT_PROJECT_SCHEMA_VERSION = "1"
PROTOCOL_METHODS: dict[str, str] = {
    "import": "import_to_bundle",
    "export": "export_from_bundle",
    "sync": "sync_with_bundle",
    "validate": "validate_bundle",
}
PROTOCOL_INTERFACE_BINDINGS: tuple[str, ...] = ("runtime_interface", "commands_interface", "commands")
BRIDGE_REGISTRY = BridgeRegistry()
BUILTIN_MODULES_ROOT = (Path(__file__).resolve().parents[1] / "modules").resolve()


def _normalized_module_name(package_name: str) -> str:
    """Normalize package ids to Python import-friendly module names."""
    return package_name.split("/", 1)[-1].replace("-", "_")


def get_modules_root() -> Path:
    """Return the modules root path (specfact_cli package dir / modules).

    When SPECFACT_REPO_ROOT is set (e.g. in tests/CI), use that repo so the
    correct checkout/worktree is used instead of the installed package.
    """
    explicit_root = os.environ.get("SPECFACT_REPO_ROOT")
    if explicit_root:
        candidate = Path(explicit_root).expanduser().resolve() / "src" / "specfact_cli" / "modules"
        if candidate.exists():
            return candidate
    import specfact_cli

    pkg_dir = Path(specfact_cli.__path__[0]).resolve()
    return pkg_dir / "modules"


def _is_builtin_module_package(package_dir: Path) -> bool:
    """Return True when package directory belongs to built-in module tree."""
    try:
        package_dir.resolve().relative_to(BUILTIN_MODULES_ROOT)
        return True
    except ValueError:
        return False


def get_modules_roots() -> list[Path]:
    """Return all module discovery roots in priority order."""
    roots: list[Path] = []
    seen: set[Path] = set()

    def _add_root(path: Path) -> None:
        resolved = path.resolve()
        if resolved in seen:
            return
        seen.add(resolved)
        roots.append(path)

    # Core packaged modules.
    _add_root(get_modules_root())

    workspace_modules_root = get_workspace_modules_root()
    if workspace_modules_root is not None:
        _add_root(workspace_modules_root)

    # Optional extra roots for custom module locations.
    extra_roots = os.environ.get("SPECFACT_MODULES_ROOTS", "")
    for raw_root in extra_roots.split(os.pathsep):
        candidate = raw_root.strip()
        if not candidate:
            continue
        candidate_path = Path(candidate).expanduser()
        if candidate_path.exists():
            _add_root(candidate_path)

    return roots


def get_workspace_modules_root(base_path: Path | None = None) -> Path | None:
    """Return nearest workspace-local .specfact/modules root from base path upward."""
    start = base_path.resolve() if base_path is not None else Path.cwd().resolve()
    for candidate in [start, *start.parents]:
        git_dir = candidate / ".git"
        if git_dir.exists():
            workspace_modules_root = candidate / ".specfact" / "modules"
            if workspace_modules_root.exists():
                return workspace_modules_root
            return None
    workspace_modules_root = start / ".specfact" / "modules"
    if workspace_modules_root.exists():
        return workspace_modules_root
    return None


@beartype
def discover_all_package_metadata() -> list[tuple[Path, ModulePackageMetadata]]:
    """Discover module package metadata across built-in/marketplace/custom roots."""
    from specfact_cli.registry.module_discovery import discover_all_modules

    discovered = discover_all_modules()
    return [(entry.package_dir, entry.metadata) for entry in discovered]


def _package_sort_key(item: tuple[Path, ModulePackageMetadata]) -> tuple[int, str]:
    """Sort key: core modules by CORE_MODULE_ORDER index, then by name."""
    _dir, meta = item
    try:
        idx = CORE_MODULE_ORDER.index(meta.name)
        return (idx, meta.name)
    except ValueError:
        return (len(CORE_MODULE_ORDER), meta.name)


@beartype
def discover_package_metadata(modules_root: Path, source: str = "builtin") -> list[tuple[Path, ModulePackageMetadata]]:
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
            publisher: PublisherInfo | None = None
            if isinstance(raw.get("publisher"), dict):
                pub = raw["publisher"]
                name_val = pub.get("name")
                email_val = pub.get("email")
                if name_val:
                    publisher = PublisherInfo(
                        name=str(name_val),
                        email=str(email_val).strip() if email_val else "noreply@specfact.local",
                        attributes={
                            str(k): str(v) for k, v in pub.items() if k not in ("name", "email") and isinstance(v, str)
                        },
                    )
            integrity: IntegrityInfo | None = None
            if isinstance(raw.get("integrity"), dict):
                integ = raw["integrity"]
                if integ.get("checksum"):
                    integrity = IntegrityInfo(
                        checksum=str(integ["checksum"]),
                        signature=str(integ["signature"]) if integ.get("signature") else None,
                    )
            module_deps_versioned: list[VersionedModuleDependency] = []
            for entry in raw.get("module_dependencies_versioned") or []:
                if isinstance(entry, dict) and entry.get("name"):
                    module_deps_versioned.append(
                        VersionedModuleDependency(
                            name=str(entry["name"]),
                            version_specifier=str(entry["version_specifier"])
                            if entry.get("version_specifier")
                            else None,
                        )
                    )
            pip_deps_versioned: list[VersionedPipDependency] = []
            for entry in raw.get("pip_dependencies_versioned") or []:
                if isinstance(entry, dict) and entry.get("name"):
                    pip_deps_versioned.append(
                        VersionedPipDependency(
                            name=str(entry["name"]),
                            version_specifier=str(entry["version_specifier"])
                            if entry.get("version_specifier")
                            else None,
                        )
                    )
            validated_service_bridges: list[ServiceBridgeMetadata] = []
            for bridge_entry in raw.get("service_bridges", []) or []:
                try:
                    validated_service_bridges.append(ServiceBridgeMetadata.model_validate(bridge_entry))
                except Exception:
                    continue
            validated_schema_extensions: list[SchemaExtension] = []
            for ext_entry in raw.get("schema_extensions", []) or []:
                try:
                    if isinstance(ext_entry, dict):
                        validated_schema_extensions.append(SchemaExtension.model_validate(ext_entry))
                except Exception:
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
                publisher=publisher,
                integrity=integrity,
                module_dependencies_versioned=module_deps_versioned,
                pip_dependencies_versioned=pip_deps_versioned,
                service_bridges=validated_service_bridges,
                schema_extensions=validated_schema_extensions,
                description=str(raw["description"]) if raw.get("description") else None,
                license=str(raw["license"]) if raw.get("license") else None,
                source=source,
                category=str(raw["category"]) if raw.get("category") else None,
                bundle=str(raw["bundle"]) if raw.get("bundle") else None,
                bundle_group_command=str(raw["bundle_group_command"]) if raw.get("bundle_group_command") else None,
                bundle_sub_command=str(raw["bundle_sub_command"]) if raw.get("bundle_sub_command") else None,
            )
            if meta.category is None:
                logger = get_bridge_logger(__name__)
                logger.warning(
                    "Module '%s' has no category field; mounting as flat top-level command.",
                    meta.name,
                )
            else:
                meta = normalize_legacy_bundle_group_command(meta)
                validate_module_category_manifest(meta)
            result.append((child, meta))
        except ModuleManifestError:
            raise
        except Exception:
            continue
    return result


@beartype
@require(lambda class_path: class_path.strip() != "", "Converter class path must not be empty")
@require(lambda class_path: "." in class_path, "Converter class path must include module and class name")
@ensure(lambda result: isinstance(result, type), "Resolved converter must be a class")
def _resolve_converter_class(class_path: str) -> type[SchemaConverter]:
    """Resolve a converter class from dotted path.

    Raises:
        ImportError/AttributeError/TypeError: when path cannot be resolved to a class.
    """
    module_path, class_name = class_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    converter_class = getattr(module, class_name)
    if not isinstance(converter_class, type):
        raise TypeError(f"Converter path '{class_path}' did not resolve to a class.")
    return converter_class


@beartype
def _check_core_compatibility(meta: Any, current_cli_version: str) -> bool:
    """Return True when module is compatible with the running CLI core version."""
    core_compatibility = getattr(meta, "core_compatibility", None)
    if not core_compatibility:
        return True
    try:
        specifier = SpecifierSet(str(core_compatibility))
        return Version(current_cli_version) in specifier
    except (InvalidVersion, Exception):
        # Keep malformed metadata non-blocking; emit details in debug logs at call site.
        return True


@beartype
def _validate_module_dependencies(
    meta: Any,
    enabled_map: dict[str, bool],
) -> tuple[bool, list[str]]:
    """Validate that declared dependencies exist and are enabled."""
    missing: list[str] = []
    module_dependencies = getattr(meta, "module_dependencies", [])
    if not isinstance(module_dependencies, list):
        return False, ["invalid metadata: module_dependencies must be a list"]
    for dep_id in module_dependencies:
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


def _make_package_loader(package_dir: Path, package_name: str, command_name: str) -> Any:
    """Return a callable that loads the package's app (from src/app.py or src/<name>/__init__.py)."""

    def loader() -> Any:
        src_dir = package_dir / "src"
        if not src_dir.exists():
            raise ValueError(f"Package {package_dir.name} has no src/")
        if str(src_dir) not in sys.path:
            sys.path.insert(0, str(src_dir))
        normalized_name = _normalized_module_name(package_name)
        normalized_command = _normalized_module_name(command_name)
        load_path: Path | None = None
        submodule_locations: list[str] | None = None
        # In test/CI (SPECFACT_REPO_ROOT set), prefer local src/<name>/main.py so worktree
        # code runs (e.g. env-aware templates) instead of the bundle delegate (app.py -> specfact_backlog).
        if os.environ.get("SPECFACT_REPO_ROOT") and (src_dir / normalized_name / "main.py").exists():
            load_path = src_dir / normalized_name / "main.py"
            submodule_locations = [str(load_path.parent)]
        if load_path is None:
            # Prefer command-specific namespaced entrypoints for marketplace bundles
            # (e.g. src/specfact_backlog/backlog/app.py) before generic root fallbacks.
            if (src_dir / normalized_name / normalized_command / "app.py").exists():
                load_path = src_dir / normalized_name / normalized_command / "app.py"
            elif (src_dir / normalized_name / normalized_command / "commands.py").exists():
                load_path = src_dir / normalized_name / normalized_command / "commands.py"
            elif (src_dir / "app.py").exists():
                load_path = src_dir / "app.py"
            elif (src_dir / f"{normalized_name}.py").exists():
                load_path = src_dir / f"{normalized_name}.py"
            elif (src_dir / normalized_name / "__init__.py").exists():
                load_path = src_dir / normalized_name / "__init__.py"
                submodule_locations = [str(load_path.parent)]
        if load_path is None:
            raise ValueError(
                f"Package {package_dir.name} has no src/app.py, src/{package_name}.py or src/{package_name}/"
            )
        if submodule_locations is None and load_path.name == "__init__.py":
            submodule_locations = [str(load_path.parent)]
        module_token = _normalized_module_name(package_dir.name)
        spec = importlib.util.spec_from_file_location(
            f"_specfact_module_{module_token}",
            load_path,
            submodule_search_locations=submodule_locations,
        )
        if spec is None or spec.loader is None:
            raise ValueError(f"Cannot load from {package_dir.name}")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        command_attr = f"{_normalized_module_name(command_name)}_app"
        app = getattr(mod, command_attr, None)
        if app is None:
            app = getattr(mod, "app", None)
        if app is None:
            raise ValueError(f"Package {package_dir.name} has no '{command_attr}' or 'app' attribute")
        return app

    return loader


def _command_info_name(command_info: Any) -> str:
    """Return a stable command name from Typer command info."""
    explicit_name = getattr(command_info, "name", None)
    if isinstance(explicit_name, str) and explicit_name:
        return explicit_name
    callback = getattr(command_info, "callback", None)
    callback_name = getattr(callback, "__name__", "")
    return callback_name.replace("_", "-") if callback_name else ""


@beartype
def _is_expected_duplicate_extension(owner_module: str, command_name: str, subcommand_name: str) -> bool:
    """Return True when duplicate command overlap is an expected core+bundle composition case."""
    if owner_module != "nold-ai/specfact-backlog":
        return False
    allowed_duplicates = {
        ("backlog", "daily"),
        ("backlog", "refine"),
        ("backlog", "init-config"),
        ("backlog", "map-fields"),
        ("backlog ceremony", "standup"),
        ("backlog ceremony", "refinement"),
        ("backlog ceremony", "planning"),
        ("backlog ceremony", "flow"),
        ("backlog ceremony", "pi-summary"),
        ("backlog auth", "azure-devops"),
        ("backlog auth", "github"),
        ("backlog auth", "status"),
        ("backlog auth", "clear"),
    }
    return (command_name, subcommand_name) in allowed_duplicates


@beartype
def _merge_typer_apps(base_app: Any, extension_app: Any, owner_module: str, command_name: str) -> None:
    """Merge extension Typer commands/groups into an existing root Typer app."""
    logger = get_bridge_logger(__name__)
    if not hasattr(base_app, "registered_commands") or not hasattr(extension_app, "registered_commands"):
        logger.warning(
            "Module %s attempted to extend command '%s' with a non-Typer app; skipping extension.",
            owner_module,
            command_name,
        )
        return

    existing_command_names = {
        _command_info_name(command_info) for command_info in getattr(base_app, "registered_commands", [])
    }
    for command_info in getattr(extension_app, "registered_commands", []):
        subcommand_name = _command_info_name(command_info)
        if not subcommand_name:
            continue
        if subcommand_name in existing_command_names:
            log_fn = (
                logger.debug
                if _is_expected_duplicate_extension(owner_module, command_name, subcommand_name)
                else logger.warning
            )
            log_fn(
                "Module %s attempted to extend command '%s' with duplicate subcommand '%s'; skipping duplicate.",
                owner_module,
                command_name,
                subcommand_name,
            )
            continue
        base_app.registered_commands.append(command_info)
        existing_command_names.add(subcommand_name)

    if not hasattr(base_app, "registered_groups") or not hasattr(extension_app, "registered_groups"):
        return

    existing_groups = {getattr(group_info, "name", ""): group_info for group_info in base_app.registered_groups}
    for group_info in extension_app.registered_groups:
        group_name = getattr(group_info, "name", "") or ""
        if not group_name:
            continue
        if group_name in existing_groups:
            existing_group = existing_groups[group_name]
            existing_subapp = getattr(existing_group, "typer_instance", None)
            extension_subapp = getattr(group_info, "typer_instance", None)
            if existing_subapp is not None and extension_subapp is not None:
                _merge_typer_apps(
                    existing_subapp,
                    extension_subapp,
                    owner_module,
                    f"{command_name} {group_name}",
                )
                continue
            logger.warning(
                "Module %s attempted to extend subgroup '%s %s' but merger target was invalid; skipping duplicate.",
                owner_module,
                command_name,
                group_name,
            )
            continue
        base_app.registered_groups.append(group_info)
        existing_groups[group_name] = group_info


def _make_extending_loader(
    base_loader: Any,
    extension_loader: Any,
    owner_module: str,
    command_name: str,
) -> Any:
    """Create a loader that merges an extension Typer app into an existing command app."""

    def loader() -> Any:
        base_app = base_loader()
        extension_app = extension_loader()
        _merge_typer_apps(base_app, extension_app, owner_module, command_name)
        return base_app

    return loader


def _resolve_package_load_path(package_dir: Path, package_name: str) -> Path:
    """Resolve a package entrypoint module path."""
    src_dir = package_dir / "src"
    if not src_dir.exists():
        raise ValueError(f"Package {package_dir.name} has no src/")
    normalized_name = _normalized_module_name(package_name)
    if (src_dir / "app.py").exists():
        return src_dir / "app.py"
    if (src_dir / f"{normalized_name}.py").exists():
        return src_dir / f"{normalized_name}.py"
    if (src_dir / normalized_name / "__init__.py").exists():
        return src_dir / normalized_name / "__init__.py"
    raise ValueError(f"Package {package_dir.name} has no src/app.py, src/{package_name}.py or src/{package_name}/")


def _load_package_module(package_dir: Path, package_name: str) -> Any:
    """Load and return a module package entrypoint module."""
    src_dir = package_dir / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    load_path = _resolve_package_load_path(package_dir, package_name)
    submodule_locations = [str(load_path.parent)] if load_path.name == "__init__.py" else None
    module_token = _normalized_module_name(package_dir.name)
    spec = importlib.util.spec_from_file_location(
        f"_specfact_module_{module_token}",
        load_path,
        submodule_search_locations=submodule_locations,
    )
    if spec is None or spec.loader is None:
        raise ValueError(f"Cannot load from {package_dir.name}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
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
        return importlib.import_module(f"specfact_cli.modules.{package_name}.src.commands")
    except Exception:
        pass
    return module_obj


def _resolve_protocol_source_paths(
    package_dir: Path,
    package_name: str,
    command_names: list[str] | None = None,
) -> list[Path]:
    """Resolve source file paths for protocol compliance inspection without importing module code."""
    normalized_name = _normalized_module_name(package_name)
    candidates = [
        package_dir / "src" / "commands.py",
        package_dir / "src" / normalized_name / "commands.py",
        _resolve_package_load_path(package_dir, package_name),
    ]
    for command_name in command_names or []:
        normalized_command = _normalized_module_name(command_name)
        candidates.extend(
            [
                package_dir / "src" / normalized_name / normalized_command / "commands.py",
                package_dir / "src" / normalized_name / normalized_command / "app.py",
            ]
        )
    unique_paths: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        if not candidate.exists():
            continue
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique_paths.append(candidate)
    return unique_paths


def _resolve_import_from_source_path(
    package_dir: Path, package_name: str, source_path: Path, node: ast.ImportFrom
) -> Path | None:
    """Resolve local file path for `from ... import ...` nodes used by protocol interface bindings."""
    module_name = node.module or ""

    normalized_name = _normalized_module_name(package_name)
    if node.level > 0:
        base_dir = source_path.parent
        for _ in range(node.level - 1):
            base_dir = base_dir.parent
        module_parts = module_name.split(".") if module_name else []
    else:
        src_dir = package_dir / "src"
        base_dir = src_dir
        if module_name.startswith(f"specfact_cli.modules.{normalized_name}.src."):
            module_name = module_name.removeprefix(f"specfact_cli.modules.{normalized_name}.src.")
        elif module_name.startswith(f"{normalized_name}."):
            module_name = module_name.removeprefix(f"{normalized_name}.")
        module_parts = module_name.split(".") if module_name else []

    candidate_base = base_dir.joinpath(*module_parts) if module_parts else base_dir
    module_file = candidate_base.with_suffix(".py")
    if module_file.exists():
        return module_file
    init_file = candidate_base / "__init__.py"
    if init_file.exists():
        return init_file
    return None


@beartype
def _check_protocol_compliance_from_source(
    package_dir: Path,
    package_name: str,
    command_names: list[str] | None = None,
) -> list[str]:
    """Inspect protocol operations from source text to keep module registration lazy."""
    exported_function_names: set[str] = set()
    class_method_names: dict[str, set[str]] = {}
    assigned_names: dict[str, ast.expr] = {}
    scanned_sources: list[str] = []
    pending_paths = _resolve_protocol_source_paths(package_dir, package_name, command_names=command_names)
    scanned_paths = {path.resolve() for path in pending_paths}

    while pending_paths:
        source_path = pending_paths.pop(0)
        source = source_path.read_text(encoding="utf-8")
        scanned_sources.append(source)
        tree = ast.parse(source, filename=str(source_path))

        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                methods: set[str] = set()
                for class_node in node.body:
                    if isinstance(class_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        methods.add(class_node.name)
                class_method_names[node.name] = methods
                continue
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                exported_function_names.add(node.name)
                continue
            if isinstance(node, ast.ImportFrom):
                imported_names = {alias.name for alias in node.names}
                if set(PROTOCOL_INTERFACE_BINDINGS).isdisjoint(imported_names):
                    continue
                imported_source = _resolve_import_from_source_path(package_dir, package_name, source_path, node)
                if imported_source is None:
                    continue
                resolved = imported_source.resolve()
                if resolved in scanned_paths:
                    continue
                scanned_paths.add(resolved)
                pending_paths.append(imported_source)
                continue
            if isinstance(node, ast.Assign):
                targets = node.targets
                value = node.value
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                targets = [node.target]
                value = node.value
            else:
                continue
            if value is None:
                continue
            for target in targets:
                if not isinstance(target, ast.Name):
                    continue
                assigned_names[target.id] = value
                if isinstance(value, (ast.Attribute, ast.Name)):
                    exported_function_names.add(target.id)

    for binding_name in PROTOCOL_INTERFACE_BINDINGS:
        binding_value = assigned_names.get(binding_name)
        if binding_value is None:
            continue
        if isinstance(binding_value, ast.Name):
            exported_function_names.update(class_method_names.get(binding_value.id, set()))
            referenced_value = assigned_names.get(binding_value.id)
            if isinstance(referenced_value, ast.Call) and isinstance(referenced_value.func, ast.Name):
                exported_function_names.update(class_method_names.get(referenced_value.func.id, set()))
        elif isinstance(binding_value, ast.Call) and isinstance(binding_value.func, ast.Name):
            exported_function_names.update(class_method_names.get(binding_value.func.id, set()))

    operations: list[str] = []
    for operation, method_name in PROTOCOL_METHODS.items():
        if method_name in exported_function_names:
            operations.append(operation)
    if operations:
        return operations

    # Migration compatibility shims proxy to split bundle repos and may not expose
    # protocol methods in this local source file. Classify these as fully
    # protocol-capable to avoid false "legacy module" reports in static scans.
    joined_source = "\n".join(scanned_sources)
    if (
        (
            "Compatibility shim for legacy specfact_cli.modules." in joined_source
            or "Compatibility alias for legacy specfact_cli.modules." in joined_source
        )
        and "commands" in joined_source
        and ("from specfact_" in joined_source or 'import_module("specfact_' in joined_source)
    ):
        return sorted(PROTOCOL_METHODS.keys())
    return operations


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


@beartype
def get_installed_bundles(
    packages: list[tuple[Path, Any]],
    enabled_map: dict[str, bool],
) -> list[str]:
    """Return sorted list of bundle names from discovered packages that are enabled and have a bundle set."""

    def _resolved_bundle(meta: Any) -> str | None:
        bundle_name = getattr(meta, "bundle", None)
        if isinstance(bundle_name, str) and bundle_name:
            return bundle_name
        module_name = getattr(meta, "name", None)
        if not isinstance(module_name, str) or "/" not in module_name:
            return None
        tail = module_name.split("/", 1)[1]
        return tail if tail.startswith("specfact-") else None

    return sorted(
        {
            resolved
            for _dir, meta in packages
            if enabled_map.get(str(getattr(meta, "name", "")), True)
            and (resolved := _resolved_bundle(meta)) is not None
        }
    )


# Bundle name -> (group_name, help_str, build_app_fn) for conditional category mounting.
def _build_bundle_to_group() -> dict[str, tuple[str, str, Any]]:
    from specfact_cli.groups.backlog_group import build_app as build_backlog_app
    from specfact_cli.groups.codebase_group import build_app as build_codebase_app
    from specfact_cli.groups.govern_group import build_app as build_govern_app
    from specfact_cli.groups.project_group import build_app as build_project_app
    from specfact_cli.groups.spec_group import build_app as build_spec_app

    return {
        "specfact-backlog": ("backlog", "Backlog and policy commands.", build_backlog_app),
        "specfact-codebase": (
            "code",
            "Codebase quality commands: analyze, drift, validate, repro.",
            build_codebase_app,
        ),
        "specfact-project": ("project", "Project lifecycle commands.", build_project_app),
        "specfact-spec": ("spec", "Spec and contract commands: contract, api, sdd, generate.", build_spec_app),
        "specfact-govern": ("govern", "Governance and quality gates: enforce, patch.", build_govern_app),
    }


@beartype
def _mount_installed_category_groups(
    packages: list[tuple[Path, Any]],
    enabled_map: dict[str, bool],
) -> None:
    """Register category groups only for installed bundles."""
    installed = get_installed_bundles(packages, enabled_map)
    bundle_to_group = _build_bundle_to_group()
    module_entries_by_name = {
        entry.get("name"): entry for entry in getattr(CommandRegistry, "_module_entries", []) if entry.get("name")
    }
    seen_groups: set[str] = set()
    for bundle in installed:
        group_info = bundle_to_group.get(bundle)
        if group_info is None:
            continue
        group_name, help_str, build_fn = group_info
        if group_name in seen_groups:
            continue
        seen_groups.add(group_name)
        module_entry = module_entries_by_name.get(group_name)
        if module_entry is not None:
            # Prefer bundle-native group command apps when available and ensure they are mounted at root.
            native_loader = module_entry.get("loader")
            native_meta = module_entry.get("metadata")
            if native_loader is not None and native_meta is not None:
                CommandRegistry.register(group_name, native_loader, native_meta)
            continue

        def _make_group_loader(fn: Any) -> Any:
            def _group_loader(_fn: Any = fn) -> Any:
                return _fn()

            return _group_loader

        loader = _make_group_loader(build_fn)
        cmd_meta = CommandMetadata(
            name=group_name,
            help=help_str,
            tier="community",
            addon_id=None,
        )
        CommandRegistry.register(group_name, loader, cmd_meta)


def register_module_package_commands(
    enable_ids: list[str] | None = None,
    disable_ids: list[str] | None = None,
    allow_unsigned: bool | None = None,
    category_grouping_enabled: bool = True,
) -> None:
    """
    Discover module packages, merge with modules.json state, register only enabled packages' commands.

    Call after register_builtin_commands(). enable_ids/disable_ids from CLI (--enable-module/--disable-module).
    allow_unsigned: If True, allow modules without integrity metadata. Default from SPECFACT_ALLOW_UNSIGNED env.
    category_grouping_enabled: If True, register category groups (code, backlog, project, spec, govern).
    """
    enable_ids = enable_ids or []
    disable_ids = disable_ids or []
    if allow_unsigned is None:
        allow_unsigned = os.environ.get("SPECFACT_ALLOW_UNSIGNED", "").strip().lower() in ("1", "true", "yes")
    is_test_mode = os.environ.get("TEST_MODE") == "true" or os.environ.get("PYTEST_CURRENT_TEST") is not None
    packages = discover_all_package_metadata()
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
    partial_modules: list[tuple[str, list[str]]] = []
    legacy_modules: list[str] = []
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
        if not verify_module_artifact(package_dir, meta, allow_unsigned=allow_unsigned):
            if _is_builtin_module_package(package_dir):
                logger.warning(
                    "Built-in module '%s' failed integrity verification; loading anyway to keep CLI functional.",
                    meta.name,
                )
            elif is_test_mode and allow_unsigned:
                logger.debug(
                    "TEST_MODE: allowing built-in module '%s' despite failed integrity verification.",
                    meta.name,
                )
            else:
                print_warning(
                    f"Security check: module '{meta.name}' failed integrity verification and was not loaded. "
                    "This may indicate tampering or an outdated local module copy. "
                    "Run `specfact module init` to restore trusted bundled modules."
                )
                skipped.append((meta.name, "integrity/trust check failed"))
                continue
        if not _check_schema_compatibility(meta.schema_version, CURRENT_PROJECT_SCHEMA_VERSION):
            skipped.append(
                (
                    meta.name,
                    f"schema version {meta.schema_version} required, current is {CURRENT_PROJECT_SCHEMA_VERSION}",
                )
            )
            logger.debug(
                "Module %s: Schema version %s required, but current is %s (skipped)",
                meta.name,
                meta.schema_version,
                CURRENT_PROJECT_SCHEMA_VERSION,
            )
            continue
        if meta.schema_version is None:
            logger.debug("Module %s: No schema version declared (assuming current)", meta.name)
        else:
            logger.debug("Module %s: Schema version %s (compatible)", meta.name, meta.schema_version)

        if meta.schema_extensions:
            try:
                get_extension_registry().register(meta.name, meta.schema_extensions)
                targets = sorted({e.target for e in meta.schema_extensions})
                logger.debug(
                    "Module %s registered %d schema extensions for %s",
                    meta.name,
                    len(meta.schema_extensions),
                    targets,
                )
            except ValueError as exc:
                logger.error(
                    "Module %s: Schema extension collision - %s (skipping extensions)",
                    meta.name,
                    exc,
                )

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
            operations = _check_protocol_compliance_from_source(package_dir, meta.name, command_names=meta.commands)
            meta.protocol_operations = operations
            if len(operations) == 4:
                protocol_full += 1
            elif operations:
                partial_modules.append((meta.name, operations))
                if is_debug_mode():
                    logger.info("Module %s: ModuleIOContract partial (%s)", meta.name, ", ".join(operations))
                protocol_partial += 1
            else:
                legacy_modules.append(meta.name)
                if is_debug_mode():
                    logger.warning("Module %s: No ModuleIOContract (legacy mode)", meta.name)
                protocol_legacy += 1
        except Exception as exc:
            legacy_modules.append(meta.name)
            if is_debug_mode():
                logger.warning("Module %s: Unable to inspect protocol compliance (%s)", meta.name, exc)
            meta.protocol_operations = []
            protocol_legacy += 1

        for cmd_name in meta.commands:
            if category_grouping_enabled and meta.category is not None:
                help_str = (meta.command_help or {}).get(cmd_name) or f"Module package: {meta.name}"
                extension_loader = _make_package_loader(package_dir, meta.name, cmd_name)
                cmd_meta = CommandMetadata(name=cmd_name, help=help_str, tier=meta.tier, addon_id=meta.addon_id)
                existing_module_entry = next(
                    (entry for entry in CommandRegistry._module_entries if entry.get("name") == cmd_name),
                    None,
                )
                if existing_module_entry is not None:
                    base_loader = existing_module_entry.get("loader")
                    if base_loader is None:
                        logger.warning(
                            "Module %s attempted to extend command '%s' but module base loader was missing; skipping.",
                            meta.name,
                            cmd_name,
                        )
                    else:
                        existing_module_entry["loader"] = _make_extending_loader(
                            base_loader,
                            extension_loader,
                            meta.name,
                            cmd_name,
                        )
                        existing_module_entry["metadata"] = cmd_meta
                        CommandRegistry._module_typer_cache.pop(cmd_name, None)
                else:
                    CommandRegistry.register_module(cmd_name, extension_loader, cmd_meta)
                if cmd_name in CORE_NAMES:
                    existing_root_entry = next(
                        (entry for entry in CommandRegistry._entries if entry.get("name") == cmd_name),
                        None,
                    )
                    if existing_root_entry is not None:
                        base_loader = existing_root_entry.get("loader")
                        if base_loader is None:
                            logger.warning(
                                "Module %s attempted to extend core command '%s' but base loader was missing; skipping.",
                                meta.name,
                                cmd_name,
                            )
                        else:
                            existing_root_entry["loader"] = _make_extending_loader(
                                base_loader,
                                extension_loader,
                                meta.name,
                                cmd_name,
                            )
                            existing_root_entry["metadata"] = cmd_meta
                            CommandRegistry._typer_cache.pop(cmd_name, None)
                    else:
                        CommandRegistry.register(cmd_name, extension_loader, cmd_meta)
                continue
            existing_entry = next((entry for entry in CommandRegistry._entries if entry.get("name") == cmd_name), None)
            if existing_entry is not None:
                extension_loader = _make_package_loader(package_dir, meta.name, cmd_name)
                base_loader = existing_entry.get("loader")
                if base_loader is None:
                    logger.warning(
                        "Module %s attempted to extend command '%s' but base loader was missing; skipping.",
                        meta.name,
                        cmd_name,
                    )
                    continue
                existing_entry["loader"] = _make_extending_loader(
                    base_loader,
                    extension_loader,
                    meta.name,
                    cmd_name,
                )
                CommandRegistry._typer_cache.pop(cmd_name, None)
                if is_debug_mode():
                    logger.debug("Module %s extended command group '%s'.", meta.name, cmd_name)
                continue
            help_str = (meta.command_help or {}).get(cmd_name) or f"Module package: {meta.name}"
            loader = _make_package_loader(package_dir, meta.name, cmd_name)
            cmd_meta = CommandMetadata(name=cmd_name, help=help_str, tier=meta.tier, addon_id=meta.addon_id)
            CommandRegistry.register(cmd_name, loader, cmd_meta)
    if category_grouping_enabled:
        _mount_installed_category_groups(packages, enabled_map)
    discovered_count = protocol_full + protocol_partial + protocol_legacy
    if discovered_count and (protocol_partial > 0 or protocol_legacy > 0) and is_debug_mode():
        logger.info(
            "Module compatibility check: %s/%s compliant (full=%s, partial=%s, legacy=%s)",
            protocol_full + protocol_partial,
            discovered_count,
            protocol_full,
            protocol_partial,
            protocol_legacy,
        )
        if partial_modules:
            partial_desc = ", ".join(f"{name} ({'/'.join(ops)})" for name, ops in sorted(partial_modules))
            logger.info("Partially compliant modules: %s", partial_desc)
        if legacy_modules:
            logger.info("Legacy modules: %s", ", ".join(sorted(set(legacy_modules))))
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
    packages = discover_all_package_metadata()
    packages = sorted(packages, key=_package_sort_key)
    discovered_list = [(meta.name, meta.version) for _dir, meta in packages]
    state = read_modules_state()
    enabled_map = merge_module_state(discovered_list, state, enable_ids, disable_ids)
    return [
        {"id": meta.name, "version": meta.version, "enabled": enabled_map.get(meta.name, True)}
        for _dir, meta in packages
    ]

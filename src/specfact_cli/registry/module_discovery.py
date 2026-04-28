"""Module discovery across built-in, user, marketplace, and custom roots."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure

from specfact_cli.common import get_bridge_logger
from specfact_cli.models.module_package import ModulePackageMetadata
from specfact_cli.utils.prompts import print_warning


USER_MODULES_ROOT = Path.home() / ".specfact" / "modules"
MARKETPLACE_MODULES_ROOT = Path.home() / ".specfact" / "marketplace-modules"
CUSTOM_MODULES_ROOT = Path.home() / ".specfact" / "custom-modules"
_SHADOW_HINT_KEYS: set[tuple[str, str, str, str]] = set()


@dataclass(frozen=True)
class DiscoveredModule:
    """Discovered module package metadata with source tracking."""

    package_dir: Path
    metadata: ModulePackageMetadata
    source: str


@dataclass(frozen=True)
class _DiscoveryRootOptions:
    builtin_root: Path | None = None
    user_root: Path | None = None
    marketplace_root: Path | None = None
    custom_root: Path | None = None
    include_legacy_roots: bool | None = None
    project_base_path: Path | None = None
    include_shadowed_duplicates: bool = False


@dataclass
class _DiscoveryMergeState:
    seen_by_name: dict[str, DiscoveredModule]
    discovered: list[DiscoveredModule]
    logger: Any


def _resolve_include_legacy_roots(
    include_legacy_roots: bool | None,
    builtin_root: Path | None,
    user_root: Path | None,
    marketplace_root: Path | None,
    custom_root: Path | None,
) -> bool:
    if include_legacy_roots is not None:
        return include_legacy_roots
    return builtin_root is None and user_root is None and marketplace_root is None and custom_root is None


def _append_legacy_module_roots(roots: list[tuple[str, Path]]) -> None:
    from specfact_cli.registry.module_packages import get_modules_roots

    seen_root_paths = {path.resolve() for _source, path in roots}
    for extra_root in get_modules_roots():
        resolved = extra_root.resolve()
        if resolved in seen_root_paths:
            continue
        seen_root_paths.add(resolved)
        roots.append(("custom", extra_root))


def _discovery_root_list(options: _DiscoveryRootOptions) -> list[tuple[str, Path]]:
    from specfact_cli.registry.module_packages import get_modules_root, get_workspace_modules_root

    effective_builtin_root = options.builtin_root or get_modules_root()
    effective_project_root = get_workspace_modules_root(options.project_base_path)
    effective_user_root = options.user_root or USER_MODULES_ROOT
    effective_marketplace_root = options.marketplace_root or MARKETPLACE_MODULES_ROOT
    effective_custom_root = options.custom_root or CUSTOM_MODULES_ROOT

    roots: list[tuple[str, Path]] = [("builtin", effective_builtin_root)]
    project_matches_user_root = False
    if effective_project_root is not None:
        try:
            project_matches_user_root = effective_project_root.resolve() == effective_user_root.resolve()
        except OSError:
            project_matches_user_root = effective_project_root == effective_user_root

    if effective_project_root is not None and not project_matches_user_root:
        roots.append(("project", effective_project_root))
    roots.extend(
        [
            ("user", effective_user_root),
            ("marketplace", effective_marketplace_root),
            ("custom", effective_custom_root),
        ]
    )

    legacy = _resolve_include_legacy_roots(
        options.include_legacy_roots,
        options.builtin_root,
        options.user_root,
        options.marketplace_root,
        options.custom_root,
    )
    if legacy:
        _append_legacy_module_roots(roots)
    return roots


def _maybe_warn_user_shadowed_by_project(
    module_name: str,
    source: str,
    package_dir: Path,
    existing: DiscoveredModule,
) -> None:
    if source != "user" or existing.source != "project":
        return
    warning_key = (
        module_name,
        existing.source,
        source,
        str(existing.package_dir.resolve()),
    )
    if warning_key in _SHADOW_HINT_KEYS:
        return
    _SHADOW_HINT_KEYS.add(warning_key)
    print_warning(
        f"Module '{module_name}' from project scope ({existing.package_dir}) takes precedence over "
        f"user-scoped module ({package_dir}) in this workspace. The user copy is ignored here. "
        f"Inspect origins with `specfact module list --show-origin`; if stale, clean user scope "
        f"with `specfact module uninstall {module_name} --scope user`."
    )


def _merge_discovered_entry(
    source: str,
    package_dir: Path,
    metadata: ModulePackageMetadata,
    state: _DiscoveryMergeState,
    include_shadowed_duplicates: bool,
) -> None:
    module_name = metadata.name
    if module_name in state.seen_by_name:
        existing = state.seen_by_name[module_name]
        _maybe_warn_user_shadowed_by_project(module_name, source, package_dir, existing)
        if include_shadowed_duplicates:
            state.discovered.append(
                DiscoveredModule(
                    package_dir=package_dir,
                    metadata=metadata,
                    source=source,
                )
            )
        if source in {"user", "marketplace", "custom"}:
            state.logger.debug(
                "Module '%s' from %s at '%s' is shadowed by higher-priority source %s at '%s'.",
                module_name,
                source,
                package_dir,
                existing.source,
                existing.package_dir,
            )
        return
    entry = DiscoveredModule(
        package_dir=package_dir,
        metadata=metadata,
        source=source,
    )
    state.seen_by_name[module_name] = entry
    state.discovered.append(entry)


def _discover_modules(options: _DiscoveryRootOptions) -> list[DiscoveredModule]:
    """Discover modules from all configured locations with deterministic priority."""
    from specfact_cli.registry.module_packages import discover_package_metadata

    logger = get_bridge_logger(__name__)
    discovered: list[DiscoveredModule] = []
    merge_state = _DiscoveryMergeState(
        seen_by_name={},
        discovered=discovered,
        logger=logger,
    )
    roots = _discovery_root_list(options)

    for source, root in roots:
        if not root.exists() or not root.is_dir():
            continue
        entries = discover_package_metadata(root, source=source)
        for package_dir, metadata in entries:
            _merge_discovered_entry(
                source,
                package_dir,
                metadata,
                merge_state,
                options.include_shadowed_duplicates,
            )

    return discovered


@beartype
@ensure(lambda result: isinstance(result, list), "Discovery result must be a list")
def discover_all_modules(
    builtin_root: Path | None = None,
    user_root: Path | None = None,
    marketplace_root: Path | None = None,
    custom_root: Path | None = None,
    include_legacy_roots: bool | None = None,
) -> list[DiscoveredModule]:
    """Discover modules from all configured locations with deterministic priority."""
    return _discover_modules(
        _DiscoveryRootOptions(
            builtin_root=builtin_root,
            user_root=user_root,
            marketplace_root=marketplace_root,
            custom_root=custom_root,
            include_legacy_roots=include_legacy_roots,
        )
    )


@beartype
@ensure(lambda result: isinstance(result, list), "Discovery result must be a list")
def discover_all_modules_for_project(base_path: Path | None = None) -> list[DiscoveredModule]:
    """Discover modules using a specific project path for workspace-local roots."""
    return _discover_modules(_DiscoveryRootOptions(project_base_path=base_path))


@beartype
@ensure(lambda result: isinstance(result, list), "Discovery result must be a list")
def discover_all_modules_for_project_with_shadowed(base_path: Path | None = None) -> list[DiscoveredModule]:
    """Discover modules for a project path and retain lower-priority shadowed duplicates."""
    return _discover_modules(
        _DiscoveryRootOptions(
            project_base_path=base_path,
            include_shadowed_duplicates=True,
        )
    )

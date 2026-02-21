"""Module discovery across built-in, marketplace, and custom roots."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from beartype import beartype
from icontract import ensure

from specfact_cli.common import get_bridge_logger
from specfact_cli.models.module_package import ModulePackageMetadata


MARKETPLACE_MODULES_ROOT = Path.home() / ".specfact" / "marketplace-modules"
CUSTOM_MODULES_ROOT = Path.home() / ".specfact" / "custom-modules"


@dataclass(frozen=True)
class DiscoveredModule:
    """Discovered module package metadata with source tracking."""

    package_dir: Path
    metadata: ModulePackageMetadata
    source: str


@beartype
@ensure(lambda result: isinstance(result, list), "Discovery result must be a list")
def discover_all_modules(
    builtin_root: Path | None = None,
    marketplace_root: Path | None = None,
    custom_root: Path | None = None,
    include_legacy_roots: bool | None = None,
) -> list[DiscoveredModule]:
    """Discover modules from all configured locations with deterministic priority."""
    from specfact_cli.registry.module_packages import discover_package_metadata, get_modules_root, get_modules_roots

    logger = get_bridge_logger(__name__)
    discovered: list[DiscoveredModule] = []
    seen_names: set[str] = set()

    effective_builtin_root = builtin_root or get_modules_root()
    effective_marketplace_root = marketplace_root or MARKETPLACE_MODULES_ROOT
    effective_custom_root = custom_root or CUSTOM_MODULES_ROOT

    roots: list[tuple[str, Path]] = [
        ("builtin", effective_builtin_root),
        ("marketplace", effective_marketplace_root),
        ("custom", effective_custom_root),
    ]

    # Keep legacy discovery roots (workspace-level + SPECFACT_MODULES_ROOTS) as custom sources.
    # When explicit roots are provided (usually tests), legacy roots are disabled by default.
    if include_legacy_roots is None:
        include_legacy_roots = builtin_root is None and marketplace_root is None and custom_root is None

    if include_legacy_roots:
        seen_root_paths = {path.resolve() for _source, path in roots}
        for extra_root in get_modules_roots():
            resolved = extra_root.resolve()
            if resolved in seen_root_paths:
                continue
            seen_root_paths.add(resolved)
            roots.append(("custom", extra_root))

    for source, root in roots:
        if not root.exists() or not root.is_dir():
            continue

        entries = discover_package_metadata(root, source=source)
        for package_dir, metadata in entries:
            module_name = metadata.name
            if module_name in seen_names:
                if source in {"marketplace", "custom"}:
                    logger.warning(
                        "Module '%s' from %s at '%s' is shadowed by higher-priority source.",
                        module_name,
                        source,
                        package_dir,
                    )
                continue

            seen_names.add(module_name)
            discovered.append(
                DiscoveredModule(
                    package_dir=package_dir,
                    metadata=metadata,
                    source=source,
                )
            )

    return discovered

"""Module category grouping constants and validation (module-grouping capability)."""

from __future__ import annotations

from beartype import beartype
from icontract import require

from specfact_cli.models.module_package import ModulePackageMetadata


VALID_CATEGORIES = frozenset({"core", "project", "backlog", "codebase", "spec", "govern"})
CATEGORY_TO_GROUP_COMMAND: dict[str, str] = {
    "project": "project",
    "backlog": "backlog",
    "codebase": "code",
    "spec": "spec",
    "govern": "govern",
}
LEGACY_GROUP_COMMAND_ALIASES: dict[tuple[str, str], str] = {
    ("codebase", "codebase"): "code",
}


class ModuleManifestError(Exception):
    """Raised when module-package.yaml category/bundle metadata is invalid."""


@require(lambda manifests: isinstance(manifests, list), "manifests must be a list")
@beartype
def group_modules_by_category(
    manifests: list[ModulePackageMetadata],
) -> dict[str, list[ModulePackageMetadata]]:
    """Group module manifests by bundle_group_command; core and missing category are ungrouped."""
    result: dict[str, list[ModulePackageMetadata]] = {}
    for meta in manifests:
        if meta.category == "core" or meta.bundle_group_command is None:
            continue
        cmd = meta.bundle_group_command
        result.setdefault(cmd, []).append(meta)
    return result


@beartype
def validate_module_category_manifest(meta: ModulePackageMetadata) -> None:
    """Validate category and bundle_group_command; raise ModuleManifestError if invalid."""
    if meta.category is None:
        return
    if meta.category not in VALID_CATEGORIES:
        raise ModuleManifestError(
            f"Module '{meta.name}': category must be one of {sorted(VALID_CATEGORIES)}, got {meta.category!r}"
        )
    if meta.category == "core":
        if meta.bundle is not None or meta.bundle_group_command is not None:
            raise ModuleManifestError(
                f"Module '{meta.name}': core category must not set bundle or bundle_group_command"
            )
        return
    expected = CATEGORY_TO_GROUP_COMMAND.get(meta.category)
    if expected is not None and meta.bundle_group_command != expected:
        raise ModuleManifestError(
            f"Module '{meta.name}': bundle_group_command for category {meta.category!r} must be {expected!r}, "
            f"got {meta.bundle_group_command!r}"
        )


@beartype
def normalize_legacy_bundle_group_command(meta: ModulePackageMetadata) -> ModulePackageMetadata:
    """Normalize known legacy bundle group values to canonical grouped commands."""
    if meta.category is None or meta.bundle_group_command is None:
        return meta
    normalized = LEGACY_GROUP_COMMAND_ALIASES.get((meta.category, meta.bundle_group_command))
    if normalized is not None:
        meta.bundle_group_command = normalized
    return meta

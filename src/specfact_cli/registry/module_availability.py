"""Metadata-only module availability classification for user-facing diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from beartype import beartype
from icontract import ensure, require

from specfact_cli import __version__ as cli_version
from specfact_cli.registry.module_discovery import DiscoveredModule, discover_all_modules_for_project_with_shadowed
from specfact_cli.registry.module_packages import (
    _check_core_compatibility,
    _validate_module_dependencies,
    get_module_load_failure_reason,
    merge_module_state,
)
from specfact_cli.registry.module_state import read_modules_state


class ModuleAvailabilityStatus(StrEnum):
    """User-facing module availability states."""

    ABSENT = "absent"
    AVAILABLE = "available"
    DISABLED = "disabled"
    SKIPPED = "skipped"
    SHADOWED = "shadowed"
    AMBIGUOUS = "ambiguous"


@dataclass(frozen=True)
class ModuleAvailability:
    """Availability classification without importing module command code."""

    status: ModuleAvailabilityStatus
    module_id: str | None = None
    source: str | None = None
    package_dir: Path | None = None
    reason: str = ""
    recovery_command: str = ""
    shadowed_by: Path | None = None


def _module_id_tail(module_id: str) -> str:
    """Return the final path segment of a module id."""
    return module_id.rsplit("/", 1)[-1].strip()


def _module_id_matches(requested: str | None, discovered_id: str) -> bool:
    """Return True when a requested module id refers to a discovered manifest id."""
    if requested is None:
        return False
    requested_clean = requested.strip()
    if "/" in requested_clean:
        return requested_clean == discovered_id
    return requested_clean == discovered_id or _module_id_tail(requested_clean) == _module_id_tail(discovered_id)


def _entry_matches(entry: DiscoveredModule, *, module_id: str | None, command_name: str | None) -> bool:
    meta = entry.metadata
    if _module_id_matches(module_id, meta.name):
        return True
    if command_name is None:
        return False
    return command_name in set(meta.commands) or getattr(meta, "bundle_group_command", None) == command_name


def _availability_matches(
    discovered: list[DiscoveredModule],
    *,
    module_id: str | None,
    command_name: str | None,
) -> list[DiscoveredModule]:
    module_matches = [entry for entry in discovered if _module_id_matches(module_id, entry.metadata.name)]
    if module_matches:
        return module_matches
    if module_id is not None and "/" in module_id.strip():
        return []
    return [entry for entry in discovered if _entry_matches(entry, module_id=module_id, command_name=command_name)]


def _ambiguous_bare_module_id_match(
    module_id: str | None,
    matches: list[DiscoveredModule],
) -> bool:
    if module_id is None:
        return False
    requested = module_id.strip()
    if not requested or "/" in requested:
        return False
    matched_ids = {entry.metadata.name for entry in matches}
    return len(matched_ids) > 1


def _recovery_command(status: ModuleAvailabilityStatus, module_id: str) -> str:
    if status is ModuleAvailabilityStatus.DISABLED:
        return f"specfact module enable {module_id}"
    if status is ModuleAvailabilityStatus.ABSENT:
        return f"specfact module install {module_id}"
    return ""


def _skip_reason(entry: DiscoveredModule, enabled_map: dict[str, bool]) -> str:
    meta = entry.metadata
    load_failure = get_module_load_failure_reason(meta.name, None)
    if load_failure:
        return load_failure
    if not _check_core_compatibility(meta, cli_version):
        return f"requires {meta.core_compatibility}, cli is {cli_version}"
    deps_ok, missing = _validate_module_dependencies(meta, enabled_map)
    if not deps_ok:
        return f"missing dependencies: {', '.join(missing)}"
    return ""


def _absent_availability(module_id: str | None, requested_id: str) -> ModuleAvailability:
    return ModuleAvailability(
        status=ModuleAvailabilityStatus.ABSENT,
        module_id=module_id,
        reason="not installed",
        recovery_command=_recovery_command(ModuleAvailabilityStatus.ABSENT, requested_id) if requested_id else "",
    )


def _ambiguous_availability(module_id: str) -> ModuleAvailability:
    return ModuleAvailability(
        status=ModuleAvailabilityStatus.AMBIGUOUS,
        module_id=module_id,
        reason="multiple installed modules share this short id; use namespace/name",
    )


def _shadowed_duplicate(primary: DiscoveredModule, matches: list[DiscoveredModule]) -> DiscoveredModule | None:
    duplicate = next((entry for entry in matches[1:] if entry.metadata.name == primary.metadata.name), None)
    if duplicate is None:
        return None
    if primary.source == "project" and duplicate.source in {"user", "marketplace"}:
        return duplicate
    return None


def _shadowed_availability(primary: DiscoveredModule, duplicate: DiscoveredModule) -> ModuleAvailability:
    return ModuleAvailability(
        status=ModuleAvailabilityStatus.SHADOWED,
        module_id=duplicate.metadata.name,
        source=duplicate.source,
        package_dir=duplicate.package_dir,
        reason=f"shadowed by {primary.source} scope",
        shadowed_by=primary.package_dir,
    )


def _disabled_availability(primary: DiscoveredModule) -> ModuleAvailability:
    module_name = primary.metadata.name
    return ModuleAvailability(
        status=ModuleAvailabilityStatus.DISABLED,
        module_id=module_name,
        source=primary.source,
        package_dir=primary.package_dir,
        reason="disabled in modules.json",
        recovery_command=_recovery_command(ModuleAvailabilityStatus.DISABLED, module_name),
    )


def _available_or_skipped_availability(
    primary: DiscoveredModule,
    enabled_map: dict[str, bool],
) -> ModuleAvailability:
    reason = _skip_reason(primary, enabled_map)
    if reason:
        return ModuleAvailability(
            status=ModuleAvailabilityStatus.SKIPPED,
            module_id=primary.metadata.name,
            source=primary.source,
            package_dir=primary.package_dir,
            reason=reason,
        )
    return ModuleAvailability(
        status=ModuleAvailabilityStatus.AVAILABLE,
        module_id=primary.metadata.name,
        source=primary.source,
        package_dir=primary.package_dir,
    )


@beartype
@require(
    lambda module_id, command_name, base_path: bool(module_id or command_name), "module_id or command_name required"
)
@ensure(lambda result: isinstance(result, ModuleAvailability), "must return module availability")
def classify_module_availability(
    *,
    module_id: str | None = None,
    command_name: str | None = None,
    base_path: Path | None = None,
) -> ModuleAvailability:
    """Classify module availability using manifests and modules.json only."""
    discovered = discover_all_modules_for_project_with_shadowed(base_path)
    matches = _availability_matches(discovered, module_id=module_id, command_name=command_name)
    requested_id = module_id or command_name or ""
    if not matches:
        return _absent_availability(module_id, requested_id)
    if _ambiguous_bare_module_id_match(module_id, matches):
        return _ambiguous_availability(requested_id.strip())

    discovered_list = [(entry.metadata.name, entry.metadata.version) for entry in discovered]
    enabled_map = merge_module_state(discovered_list, read_modules_state(), [], [])
    primary = matches[0]
    module_name = primary.metadata.name
    duplicate = _shadowed_duplicate(primary, matches)
    if duplicate is not None:
        return _shadowed_availability(primary, duplicate)
    if not enabled_map.get(module_name, True):
        return _disabled_availability(primary)
    return _available_or_skipped_availability(primary, enabled_map)

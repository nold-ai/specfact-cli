"""First-run bundle selection: profiles, --install parsing, and installation (Phase 3)."""

from __future__ import annotations

from pathlib import Path

from beartype import beartype
from icontract import ensure, require

from specfact_cli.registry.module_discovery import USER_MODULES_ROOT
from specfact_cli.registry.module_grouping import VALID_CATEGORIES


PROFILE_PRESETS: dict[str, list[str]] = {
    "solo-developer": ["specfact-codebase"],
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

CANONICAL_BUNDLES: tuple[str, ...] = (
    "specfact-project",
    "specfact-backlog",
    "specfact-codebase",
    "specfact-spec",
    "specfact-govern",
)

BUNDLE_ALIAS_TO_CANONICAL: dict[str, str] = {
    "project": "specfact-project",
    "backlog": "specfact-backlog",
    "codebase": "specfact-codebase",
    "code": "specfact-codebase",
    "spec": "specfact-spec",
    "govern": "specfact-govern",
}

BUNDLE_TO_MODULE_NAMES: dict[str, list[str]] = {
    "specfact-project": ["project", "plan", "import_cmd", "sync", "migrate"],
    "specfact-backlog": ["backlog", "policy_engine"],
    "specfact-codebase": ["analyze", "drift", "validate", "repro"],
    "specfact-spec": ["contract", "spec", "sdd", "generate"],
    "specfact-govern": ["enforce", "patch_mode"],
}

BUNDLE_DEPENDENCIES: dict[str, list[str]] = {
    "specfact-spec": ["specfact-project"],
}


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
        return list(CANONICAL_BUNDLES)
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
        if entry.source not in ("user", "marketplace"):
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
) -> None:
    """Install the given bundles (and their dependencies) via bundled module installer."""
    from specfact_cli.registry.module_installer import (
        USER_MODULES_ROOT as DEFAULT_ROOT,
        install_bundled_module,
    )

    root = install_root or DEFAULT_ROOT
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

    for bid in to_install:
        module_names = BUNDLE_TO_MODULE_NAMES.get(bid, [])
        for module_name in module_names:
            try:
                install_bundled_module(
                    module_name,
                    root,
                    trust_non_official=trust_non_official,
                    non_interactive=non_interactive,
                )
            except Exception as e:
                from specfact_cli.common import get_bridge_logger

                logger = get_bridge_logger(__name__)
                logger.warning(
                    "Bundle install failed for %s: %s. Dependency resolver may be unavailable.",
                    module_name,
                    e,
                )
                raise


def get_valid_profile_names() -> list[str]:
    """Return sorted list of valid profile names for error messages."""
    return sorted(PROFILE_PRESETS)


def get_valid_bundle_aliases() -> list[str]:
    """Return sorted list of valid bundle aliases (including 'all')."""
    return [*sorted(BUNDLE_ALIAS_TO_CANONICAL), "all"]


BUNDLE_DISPLAY: dict[str, str] = {
    "specfact-project": "Project lifecycle (project, plan, import, sync, migrate)",
    "specfact-backlog": "Backlog management (backlog, policy)",
    "specfact-codebase": "Codebase quality (analyze, drift, validate, repro)",
    "specfact-spec": "Spec & API (contract, spec, sdd, generate)",
    "specfact-govern": "Governance (enforce, patch)",
}

PROFILE_DISPLAY_ORDER: list[tuple[str, str]] = [
    ("solo-developer", "Solo developer"),
    ("backlog-team", "Backlog team"),
    ("api-first-team", "API-first team"),
    ("enterprise-full-stack", "Enterprise full-stack"),
]

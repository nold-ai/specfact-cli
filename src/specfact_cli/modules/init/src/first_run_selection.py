"""First-run bundle selection: profiles, --install parsing, and installation (Phase 3)."""

from __future__ import annotations

import os
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
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
    "solo": ["specfact-codebase", "specfact-code-review"],
    "startup": ["specfact-project", "specfact-backlog", "specfact-codebase", "specfact-code-review"],
    "mid_size": ["specfact-project", "specfact-backlog", "specfact-codebase", "specfact-spec", "specfact-code-review"],
    "enterprise": [
        "specfact-project",
        "specfact-backlog",
        "specfact-codebase",
        "specfact-spec",
        "specfact-govern",
        "specfact-code-review",
    ],
}

VALIDATION_TIER_PROFILES: tuple[str, ...] = ("solo", "startup", "mid_size", "enterprise")

LEGACY_PROFILE_TO_VALIDATION_TIER: dict[str, str] = {
    "solo-developer": "solo",
    "backlog-team": "startup",
    "api-first-team": "mid_size",
    "enterprise-full-stack": "enterprise",
}

_PROFILE_DEFAULTS: dict[str, dict[str, Any]] = {
    "solo": {
        "profile": "solo",
        "validation": {
            "severity": "advisory",
            "policy_mode": "advisory",
            "evidence_persistence": "local",
        },
        "clean_code": {
            "mode": "advisory",
        },
        "modules": {
            "enabled": ["nold-ai/specfact-codebase", "nold-ai/specfact-code-review"],
        },
        "requirements_schema": {
            "required_fields": ["id", "title", "acceptance"],
        },
    },
    "startup": {
        "profile": "startup",
        "validation": {
            "severity": "mixed",
            "policy_mode": "mixed",
            "evidence_persistence": "repo",
        },
        "clean_code": {
            "mode": "advisory_then_mixed",
        },
        "modules": {
            "enabled": [
                "nold-ai/specfact-project",
                "nold-ai/specfact-backlog",
                "nold-ai/specfact-codebase",
                "nold-ai/specfact-code-review",
            ],
        },
        "requirements_schema": {
            "required_fields": ["id", "title", "owner", "acceptance"],
        },
    },
    "mid_size": {
        "profile": "mid_size",
        "validation": {
            "severity": "mixed",
            "policy_mode": "mixed",
            "evidence_persistence": "repo",
        },
        "clean_code": {
            "mode": "mixed",
        },
        "modules": {
            "enabled": [
                "nold-ai/specfact-project",
                "nold-ai/specfact-backlog",
                "nold-ai/specfact-codebase",
                "nold-ai/specfact-spec",
                "nold-ai/specfact-code-review",
            ],
        },
        "requirements_schema": {
            "required_fields": ["id", "title", "owner", "acceptance", "trace_links"],
        },
    },
    "enterprise": {
        "profile": "enterprise",
        "validation": {
            "severity": "hard",
            "policy_mode": "hard",
            "evidence_persistence": "required",
        },
        "clean_code": {
            "mode": "hard",
        },
        "modules": {
            "enabled": [
                "nold-ai/specfact-project",
                "nold-ai/specfact-backlog",
                "nold-ai/specfact-codebase",
                "nold-ai/specfact-spec",
                "nold-ai/specfact-govern",
                "nold-ai/specfact-code-review",
            ],
        },
        "requirements_schema": {
            "required_fields": [
                "id",
                "title",
                "owner",
                "acceptance",
                "trace_links",
                "risk_classification",
                "exception_evidence",
            ],
        },
    },
}

_RESERVED_CONFIG_KEYS: frozenset[str] = frozenset({"source_annotations", "profile_warnings"})
_POLICY_STRENGTH: dict[str, int] = {"advisory": 1, "advisory_then_mixed": 2, "mixed": 3, "hard": 4}

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


@dataclass(frozen=True)
class ResolvedProfileConfig:
    """Resolved profile config with source annotations for each winning value."""

    values: dict[str, Any]
    sources: dict[str, Any]
    warnings: list[str]


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


def _normalize_profile_key(profile: str) -> str:
    key = profile.strip().lower()
    return "mid_size" if key in {"mid-size", "mid_size"} else key


@require(lambda profile: isinstance(profile, str) and profile.strip() != "", "profile must be non-empty string")
@ensure(lambda result: result in VALIDATION_TIER_PROFILES, "result must be a validation tier")
@beartype
def resolve_validation_tier(profile: str) -> str:
    """Map a validation tier or legacy workflow preset to a validation config tier."""
    key = profile.strip().lower()
    normalized = _normalize_profile_key(profile)
    if normalized in VALIDATION_TIER_PROFILES:
        return normalized
    if key in LEGACY_PROFILE_TO_VALIDATION_TIER:
        return LEGACY_PROFILE_TO_VALIDATION_TIER[key]
    valid = ", ".join(get_valid_profile_names())
    raise ValueError(f"Unknown profile {profile!r}. Valid profiles: {valid}")


def _source_tree(value: Any, source: str) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _source_tree(child, source) for key, child in value.items()}
    return source


def _merge_config_layer(target: dict[str, Any], sources: dict[str, Any], layer: Mapping[str, Any], source: str) -> None:
    for raw_key, raw_value in layer.items():
        key = str(raw_key)
        if key in _RESERVED_CONFIG_KEYS:
            continue
        value = deepcopy(raw_value)
        if isinstance(value, Mapping) and isinstance(target.get(key), dict):
            existing_source = sources.get(key)
            if not isinstance(existing_source, dict):
                sources[key] = {}
            _merge_config_layer(target[key], sources[key], value, source)
            continue
        target[key] = value
        sources[key] = _source_tree(value, source)


def _extract_policy_value(layer: Mapping[str, Any] | None, key: str) -> str | None:
    if not layer:
        return None
    validation = layer.get("validation")
    if not isinstance(validation, Mapping):
        return None
    validation_values: dict[str, Any] = {str(raw_key): raw_value for raw_key, raw_value in validation.items()}
    value = validation_values.get(key)
    return value if isinstance(value, str) else None


def _local_policy_weakened(org_baseline: Mapping[str, Any] | None, developer_local: Mapping[str, Any] | None) -> bool:
    for key in ("severity", "policy_mode"):
        org_value = _extract_policy_value(org_baseline, key)
        local_value = _extract_policy_value(developer_local, key)
        if org_value is None or local_value is None:
            continue
        if _POLICY_STRENGTH.get(local_value, 0) < _POLICY_STRENGTH.get(org_value, 0):
            return True
    return False


@require(lambda profile: isinstance(profile, str) and profile.strip() != "", "profile must be non-empty string")
@ensure(lambda result: isinstance(result, ResolvedProfileConfig), "result must be a resolved profile config")
@beartype
def resolve_profile_config(
    profile: str,
    *,
    org_baseline: Mapping[str, Any] | None = None,
    repo_overlay: Mapping[str, Any] | None = None,
    developer_local: Mapping[str, Any] | None = None,
) -> ResolvedProfileConfig:
    """Resolve profile defaults, org baseline, repo overlay, and developer-local config layers."""
    tier = resolve_validation_tier(profile)
    values: dict[str, Any] = {}
    sources: dict[str, Any] = {}
    _merge_config_layer(values, sources, _PROFILE_DEFAULTS[tier], f"profile:{tier}")
    for layer, source in (
        (org_baseline, "org_baseline"),
        (repo_overlay, "repo_overlay"),
        (developer_local, "developer_local"),
    ):
        if layer:
            _merge_config_layer(values, sources, layer, source)

    warnings: list[str] = []
    if _local_policy_weakened(org_baseline, developer_local):
        warnings.append("developer_local weakens org validation policy")
    return ResolvedProfileConfig(values=values, sources=sources, warnings=warnings)


def _read_yaml_mapping(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"Config file must contain a mapping: {path}")
    return raw


@require(lambda repo_path: isinstance(repo_path, Path), "repo_path must be Path")
@require(lambda profile: isinstance(profile, str) and profile.strip() != "", "profile must be non-empty string")
@ensure(lambda result: isinstance(result, ResolvedProfileConfig), "result must be a resolved profile config")
@beartype
def write_profile_config(repo_path: Path, profile: str) -> ResolvedProfileConfig:
    """Write `.specfact/config.yaml` for the selected profile with source annotations."""
    specfact_dir = repo_path / ".specfact"
    config_path = specfact_dir / "config.yaml"
    local_path = specfact_dir / "config.local.yaml"
    org_path = Path.home() / ".specfact" / "config.yaml"

    repo_overlay = _read_yaml_mapping(config_path)
    repo_overlay.pop("profile", None)
    resolved = resolve_profile_config(
        profile,
        org_baseline=_read_yaml_mapping(org_path),
        repo_overlay=repo_overlay,
        developer_local=_read_yaml_mapping(local_path),
    )

    payload = deepcopy(resolved.values)
    payload["profile"] = resolve_validation_tier(profile)
    payload["source_annotations"] = resolved.sources
    if resolved.warnings:
        payload["profile_warnings"] = resolved.warnings

    specfact_dir.mkdir(parents=True, exist_ok=True)
    config_path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=False), encoding="utf-8")
    return resolved


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
    key = _normalize_profile_key(profile)
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

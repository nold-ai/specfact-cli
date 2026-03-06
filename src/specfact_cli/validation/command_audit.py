"""Helpers for command-package runtime validation."""

from __future__ import annotations

import importlib
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


AuditMode = Literal["help-only", "fixture-backed", "dry-run"]


@dataclass(frozen=True)
class CommandAuditCase:
    """One command-path audit case."""

    command_path: str
    argv: tuple[str, ...]
    phase: str
    mode: AuditMode
    owner: str


def _resolve_modules_repo_root() -> Path | None:
    configured = os.environ.get("SPECFACT_MODULES_REPO", "").strip()
    if configured:
        candidate = Path(configured).expanduser().resolve()
        if candidate.exists():
            return candidate

    current = Path(__file__).resolve()
    for parent in current.parents:
        sibling = parent.parent / "specfact-cli-modules"
        if sibling.exists():
            return sibling.resolve()
        direct = parent / "specfact-cli-modules"
        if direct.exists():
            return direct.resolve()
    return None


def _ensure_bundle_sources_on_sys_path() -> None:
    modules_repo = _resolve_modules_repo_root()
    if modules_repo is None:
        return
    packages_root = modules_repo / "packages"
    if not packages_root.exists():
        return
    for bundle_src in packages_root.glob("*/src"):
        bundle_src_str = str(bundle_src.resolve())
        if bundle_src_str not in sys.path:
            sys.path.insert(0, bundle_src_str)


def _command_info_name(command_info: object) -> str:
    explicit_name = getattr(command_info, "name", None)
    if isinstance(explicit_name, str) and explicit_name:
        return explicit_name
    callback = getattr(command_info, "callback", None)
    callback_name = getattr(callback, "__name__", "")
    return callback_name.replace("_", "-") if callback_name else ""


def _collect_typer_paths(app: object, prefix: str) -> set[str]:
    paths: set[str] = set()

    for command_info in list(getattr(app, "registered_commands", [])):
        command_name = _command_info_name(command_info)
        if command_name:
            paths.add(f"{prefix} {command_name}")

    for group_info in list(getattr(app, "registered_groups", [])):
        group_name = getattr(group_info, "name", "") or ""
        if not group_name:
            nested_app = getattr(group_info, "typer_instance", None)
            nested_info = getattr(nested_app, "info", None) if nested_app is not None else None
            group_name = getattr(nested_info, "name", "") or ""
        if not group_name:
            continue
        group_prefix = f"{prefix} {group_name}"
        paths.add(group_prefix)
        nested_app = getattr(group_info, "typer_instance", None)
        if nested_app is not None:
            paths.update(_collect_typer_paths(nested_app, group_prefix))

    return paths


def _import_typer(module_path: str, attr_name: str = "app") -> object:
    module = importlib.import_module(module_path)
    return getattr(module, attr_name)


def official_marketplace_module_ids() -> tuple[str, ...]:
    """Return the official marketplace module ids that make up the full CLI surface."""
    return (
        "nold-ai/specfact-project",
        "nold-ai/specfact-spec",
        "nold-ai/specfact-codebase",
        "nold-ai/specfact-backlog",
        "nold-ai/specfact-govern",
    )


def _explicit_cases() -> list[CommandAuditCase]:
    return [
        CommandAuditCase("specfact", ("--help",), "root", "help-only", "specfact-core"),
        CommandAuditCase("project", ("project", "--help"), "project", "help-only", "nold-ai/specfact-project"),
        CommandAuditCase("spec", ("spec", "--help"), "spec", "help-only", "nold-ai/specfact-spec"),
        CommandAuditCase("code", ("code", "--help"), "code", "help-only", "nold-ai/specfact-codebase"),
        CommandAuditCase("backlog", ("backlog", "--help"), "backlog", "help-only", "nold-ai/specfact-backlog"),
        CommandAuditCase("govern", ("govern", "--help"), "govern", "help-only", "nold-ai/specfact-govern"),
        CommandAuditCase(
            "module init", ("module", "init", "--scope", "user"), "core", "fixture-backed", "specfact-core"
        ),
        CommandAuditCase("module search", ("module", "search", "specfact"), "core", "fixture-backed", "specfact-core"),
        CommandAuditCase("module list", ("module", "list", "--show-origin"), "core", "fixture-backed", "specfact-core"),
        CommandAuditCase(
            "module show",
            ("module", "show", "nold-ai/specfact-backlog"),
            "core",
            "fixture-backed",
            "specfact-core",
        ),
    ]


def build_command_audit_cases() -> list[CommandAuditCase]:
    """Build the full command audit matrix for core and official bundle command paths."""
    _ensure_bundle_sources_on_sys_path()
    app_specs = [
        ("specfact_cli.modules.init.src.commands", "init", "core", "specfact-core", "import"),
        ("specfact_cli.modules.module_registry.src.commands", "module", "core", "specfact-core", "import"),
        ("specfact_cli.modules.upgrade.src.commands", "upgrade", "core", "specfact-core", "import"),
        ("specfact_project.project.commands", "project", "project", "nold-ai/specfact-project", "import"),
        ("specfact_spec.spec.commands", "spec", "spec", "nold-ai/specfact-spec", "import"),
        ("specfact_codebase.code.commands", "code", "code", "nold-ai/specfact-codebase", "import"),
        ("specfact_backlog.backlog.commands", "backlog", "backlog", "nold-ai/specfact-backlog", "import"),
        ("specfact_govern.govern.commands", "govern", "govern", "nold-ai/specfact-govern", "import"),
    ]

    cases: dict[str, CommandAuditCase] = {case.command_path: case for case in _explicit_cases()}
    for module_path, prefix, phase, owner, _load_mode in app_specs:
        app = _import_typer(module_path)
        cases.setdefault(
            prefix,
            CommandAuditCase(prefix, (*tuple(prefix.split()), "--help"), phase, "help-only", owner),
        )
        for command_path in sorted(_collect_typer_paths(app, prefix)):
            cases.setdefault(
                command_path,
                CommandAuditCase(
                    command_path,
                    (*tuple(command_path.split()), "--help"),
                    phase,
                    "help-only",
                    owner,
                ),
            )

    phase_order = {"root": 0, "core": 1, "project": 2, "spec": 3, "code": 4, "backlog": 5, "govern": 6}
    return sorted(cases.values(), key=lambda case: (phase_order.get(case.phase, 99), case.command_path))

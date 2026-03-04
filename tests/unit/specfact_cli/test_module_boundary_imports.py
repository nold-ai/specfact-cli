"""Boundary tests for module package separation."""

from __future__ import annotations

import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CORE_SRC_ROOT = PROJECT_ROOT / "src" / "specfact_cli"
LEGACY_NON_APP_IMPORT_PATTERN = re.compile(r"from\s+specfact_cli\.commands\.[a-zA-Z0-9_]+\s+import\s+(?!app\b)")
LEGACY_SYMBOL_REF_PATTERN = re.compile(r"specfact_cli\.commands\.[a-zA-Z0-9_]+")
CROSS_MODULE_COMMAND_IMPORT_PATTERN = re.compile(
    r"from\s+specfact_cli\.modules\.([a-zA-Z0-9_]+)\.src\.commands\s+import\s+([^\n]+)"
)
BUNDLE_PACKAGE_IMPORT_PATTERN = re.compile(
    r"(?:from\s+(backlog_core|bundle_mapper)(?:\.[a-zA-Z0-9_]+)*\s+import|import\s+(backlog_core|bundle_mapper))"
)


def test_no_legacy_non_app_command_imports_outside_compat_shims() -> None:
    """Block new non-app command imports outside legacy compatibility shims."""
    violations: list[str] = []
    allowed_shim_dir = PROJECT_ROOT / "src" / "specfact_cli" / "commands"

    for root in (PROJECT_ROOT / "src", PROJECT_ROOT / "tests"):
        for py_file in root.rglob("*.py"):
            if "__pycache__" in py_file.parts:
                continue
            if py_file.is_relative_to(allowed_shim_dir):
                continue

            text = py_file.read_text(encoding="utf-8")
            if LEGACY_NON_APP_IMPORT_PATTERN.search(text) or LEGACY_SYMBOL_REF_PATTERN.search(text):
                rel = py_file.relative_to(PROJECT_ROOT)
                violations.append(str(rel))

    assert not violations, (
        "Legacy command-module references found (use module-local paths or shared modules instead):\n"
        + "\n".join(f"- {path}" for path in sorted(violations))
    )


def test_no_cross_module_non_app_command_imports_in_module_sources() -> None:
    """Block cross-module non-app imports from module command implementations."""
    violations: list[str] = []
    modules_root = PROJECT_ROOT / "src" / "specfact_cli" / "modules"

    for module_dir in sorted(modules_root.iterdir()):
        if not module_dir.is_dir():
            continue
        module_name = module_dir.name
        for py_file in module_dir.rglob("*.py"):
            if "__pycache__" in py_file.parts:
                continue
            text = py_file.read_text(encoding="utf-8")
            for match in CROSS_MODULE_COMMAND_IMPORT_PATTERN.finditer(text):
                imported_module = match.group(1)
                imported_symbols = [sym.strip() for sym in match.group(2).split(",") if sym.strip()]
                if imported_module == module_name:
                    continue
                if all(sym == "app" for sym in imported_symbols):
                    continue
                if imported_module == "sync" and module_name == "plan" and imported_symbols == ["sync_spec_kit"]:
                    continue
                rel = py_file.relative_to(PROJECT_ROOT)
                violations.append(f"{rel}:{match.group(0)}")

    assert not violations, (
        "Cross-module src.commands imports found (use specfact_cli.utils for shared helpers):\n"
        + "\n".join(f"- {v}" for v in sorted(violations))
    )


def test_core_does_not_import_from_bundle_packages() -> None:
    """Block core from importing bundle packages (backlog_core, bundle_mapper).

    Core (src/specfact_cli/) must remain decoupled from bundle implementation.
    Bundles import from specfact_cli; core must not import from bundles.
    """
    violations: list[str] = []
    if not CORE_SRC_ROOT.exists():
        return

    for py_file in CORE_SRC_ROOT.rglob("*.py"):
        if "__pycache__" in py_file.parts:
            continue
        text = py_file.read_text(encoding="utf-8")
        for match in BUNDLE_PACKAGE_IMPORT_PATTERN.finditer(text):
            rel = py_file.relative_to(PROJECT_ROOT)
            violations.append(f"{rel}: {match.group(0).strip()}")

    assert not violations, (
        "Core must not import from bundle packages (backlog_core, bundle_mapper). "
        "Bundles depend on core; core must not depend on bundles.\n" + "\n".join(f"- {v}" for v in sorted(violations))
    )


# MIGRATE-tier paths per IMPORT_DEPENDENCY_ANALYSIS; core must not add new ones.
# These should eventually be removed; test prevents reintroduction.
MIGRATE_TIER_PREFIXES = (
    "specfact_cli.agents",
    "specfact_cli.analyzers",
    "specfact_cli.backlog",
    "specfact_cli.comparators",
    "specfact_cli.enrichers",
    "specfact_cli.generators",
    "specfact_cli.importers",
    "specfact_cli.merge",
    "specfact_cli.migrations",
    "specfact_cli.parsers",
    "specfact_cli.sync",
    "specfact_cli.templates.registry",
    "specfact_cli.validators.repro_checker",
    "specfact_cli.validators.sidecar",
)
CORE_MODULE_DIRS = ("init", "module_registry", "upgrade")


def test_core_modules_do_not_import_migrate_tier() -> None:
    """Core modules (init, module_registry, upgrade) must not import MIGRATE-tier paths.

    MIGRATE-tier code belongs in specfact-cli-modules. Core modules must only use
    CORE/SHARED imports. Prevents reintroduction of bundle-only coupling.
    """
    violations: list[str] = []
    modules_root = PROJECT_ROOT / "src" / "specfact_cli" / "modules"
    if not modules_root.exists():
        return

    for module_name in CORE_MODULE_DIRS:
        module_dir = modules_root / module_name
        if not module_dir.exists():
            continue
        for py_file in module_dir.rglob("*.py"):
            if "__pycache__" in py_file.parts:
                continue
            text = py_file.read_text(encoding="utf-8")
            for line_no, line in enumerate(text.splitlines(), 1):
                for prefix in MIGRATE_TIER_PREFIXES:
                    if f"from {prefix}" in line or f"import {prefix}" in line:
                        rel = py_file.relative_to(PROJECT_ROOT)
                        violations.append(f"{rel}:{line_no}: {line.strip()[:80]}")

    assert not violations, (
        "Core modules (init, module_registry, upgrade) must not import MIGRATE-tier paths. "
        "MIGRATE-tier code lives in specfact-cli-modules.\n" + "\n".join(f"- {v}" for v in sorted(violations))
    )

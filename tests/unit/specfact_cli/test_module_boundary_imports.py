"""Boundary tests for module package separation."""

from __future__ import annotations

import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
LEGACY_NON_APP_IMPORT_PATTERN = re.compile(r"from\s+specfact_cli\.commands\.[a-zA-Z0-9_]+\s+import\s+(?!app\b)")
LEGACY_SYMBOL_REF_PATTERN = re.compile(r"specfact_cli\.commands\.[a-zA-Z0-9_]+")
CROSS_MODULE_COMMAND_IMPORT_PATTERN = re.compile(
    r"from\s+specfact_cli\.modules\.([a-zA-Z0-9_]+)\.src\.commands\s+import\s+([^\n]+)"
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

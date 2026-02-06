"""Scenario-focused tests for module package separation migration."""

from __future__ import annotations

import importlib
import re
from pathlib import Path

import pytest

from specfact_cli.registry.bootstrap import register_builtin_commands
from specfact_cli.registry.registry import CommandRegistry


PROJECT_ROOT = Path(__file__).resolve().parents[3]
MODULES_ROOT = PROJECT_ROOT / "src" / "specfact_cli" / "modules"

# Legacy shim module name -> module package name.
LEGACY_SHIM_TO_MODULE: dict[str, str] = {
    "analyze": "analyze",
    "auth": "auth",
    "backlog_commands": "backlog",
    "contract_cmd": "contract",
    "drift": "drift",
    "enforce": "enforce",
    "generate": "generate",
    "import_cmd": "import_cmd",
    "init": "init",
    "migrate": "migrate",
    "plan": "plan",
    "project_cmd": "project",
    "repro": "repro",
    "sdd": "sdd",
    "spec": "spec",
    "sync": "sync",
    "update": "upgrade",
    "validate": "validate",
}


def _module_package_names() -> list[str]:
    return sorted(path.name for path in MODULES_ROOT.iterdir() if path.is_dir() and (path / "src").exists())


def test_module_app_entrypoints_import_module_local_commands() -> None:
    """Each module app entrypoint imports app from module-local commands."""
    missing: list[str] = []
    wrong_import: list[str] = []

    for module_name in _module_package_names():
        app_path = MODULES_ROOT / module_name / "src" / "app.py"
        if not app_path.exists():
            missing.append(str(app_path.relative_to(PROJECT_ROOT)))
            continue

        expected_import = f"from specfact_cli.modules.{module_name}.src.commands import app"
        text = app_path.read_text(encoding="utf-8")
        if expected_import not in text:
            wrong_import.append(str(app_path.relative_to(PROJECT_ROOT)))

    assert not missing, "Missing module app entrypoint files:\n" + "\n".join(f"- {path}" for path in missing)
    assert not wrong_import, "Module app entrypoints not wired to local commands:\n" + "\n".join(
        f"- {path}" for path in wrong_import
    )


def test_legacy_command_shims_reexport_module_app() -> None:
    """Legacy command import paths still expose same app object as module-local command implementation."""
    mismatches: list[str] = []

    for legacy_mod, module_name in LEGACY_SHIM_TO_MODULE.items():
        legacy = importlib.import_module(f"specfact_cli.commands.{legacy_mod}")
        target = importlib.import_module(f"specfact_cli.modules.{module_name}.src.commands")
        if getattr(legacy, "app", None) is not getattr(target, "app", None):
            mismatches.append(f"{legacy_mod} -> {module_name}")

    assert not mismatches, "Legacy command shims do not re-export module-local app:\n" + "\n".join(
        f"- {entry}" for entry in mismatches
    )


def test_legacy_command_shims_reexport_public_symbols() -> None:
    """Legacy shim modules expose only app plus symbols still required by legacy import usage."""
    pattern = re.compile(r"from\s+specfact_cli\.commands\.(?P<mod>[a-zA-Z0-9_]+)\s+import\s+(?P<names>.+)")
    required: dict[str, set[str]] = {mod: set() for mod in LEGACY_SHIM_TO_MODULE}

    for root in (PROJECT_ROOT / "src", PROJECT_ROOT / "tests"):
        for py_file in root.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            for match in pattern.finditer(text):
                mod = match.group("mod")
                if mod not in required:
                    continue
                for raw in match.group("names").split(","):
                    name = raw.strip().split(" as ")[0].strip()
                    if name:
                        required[mod].add(name)

    issues: list[str] = []
    for legacy_mod, module_name in LEGACY_SHIM_TO_MODULE.items():
        legacy = importlib.import_module(f"specfact_cli.commands.{legacy_mod}")
        target = importlib.import_module(f"specfact_cli.modules.{module_name}.src.commands")

        required_names = {"app"} | required[legacy_mod]
        exported_names = set(getattr(legacy, "__all__", []))

        # Require app compatibility and any still-referenced legacy symbols.
        for name in sorted(required_names):
            if not hasattr(legacy, name):
                issues.append(f"{legacy_mod}.{name} missing")
                continue
            if not hasattr(target, name):
                issues.append(f"{legacy_mod}.{name} not in module-local commands")
                continue
            if getattr(legacy, name) is not getattr(target, name):
                issues.append(f"{legacy_mod}.{name} object mismatch")

        # Shim policy for this migration stage: do not export extra symbols by default.
        extras = sorted(exported_names - required_names)
        if extras:
            issues.append(f"{legacy_mod} extra exports: {', '.join(extras)}")

    assert not issues, "Legacy shim exports do not match required compatibility surface:\n" + "\n".join(
        f"- {item}" for item in issues
    )


def test_module_discovery_registers_commands_from_manifests(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Command registry includes all commands declared by module-package manifests after bootstrap."""
    monkeypatch.setenv("SPECFACT_REGISTRY_DIR", str(tmp_path))

    expected_commands: set[str] = set()
    for module_name in _module_package_names():
        manifest = MODULES_ROOT / module_name / "module-package.yaml"
        if not manifest.exists():
            continue
        lines = manifest.read_text(encoding="utf-8").splitlines()
        in_commands = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("commands:"):
                in_commands = True
                continue
            if in_commands and stripped.startswith("- "):
                expected_commands.add(stripped[2:].strip())
                continue
            if in_commands and stripped and not stripped.startswith("#") and not stripped.startswith("- "):
                in_commands = False

    CommandRegistry._clear_for_testing()
    register_builtin_commands()
    registered = set(CommandRegistry.list_commands())
    missing = sorted(expected_commands - registered)

    assert not missing, "Missing commands after registry bootstrap:\n" + "\n".join(f"- {cmd}" for cmd in missing)

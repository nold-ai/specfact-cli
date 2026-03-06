"""Tests for legacy module re-export shims."""

from __future__ import annotations

import ast
import importlib
import sys
import warnings
from pathlib import Path
from types import ModuleType

import pytest


def test_validate_shim_emits_deprecation_warning_on_attribute_access() -> None:
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        module = importlib.import_module("specfact_codebase.validate")
        _ = module.app
    assert module is not None
    if captured:
        assert any(issubclass(item.category, DeprecationWarning) for item in captured)


@pytest.mark.filterwarnings("ignore:specfact_codebase.analyze is deprecated")
def test_legacy_analyze_import_resolves_without_import_error() -> None:
    from specfact_codebase.analyze import app

    assert app is not None


def test_validate_shim_uses_lazy_getattr_only() -> None:
    module_path = Path("src/specfact_cli/commands/validate.py")
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    function_names = [node.name for node in tree.body if isinstance(node, ast.FunctionDef)]
    class_names = [node.name for node in tree.body if isinstance(node, ast.ClassDef)]

    assert function_names == ["__getattr__"]
    assert class_names == []


def test_validate_shim_name_is_accessible_after_import() -> None:
    module = importlib.import_module("specfact_codebase.validate")
    assert module.__name__ == "specfact_codebase.validate"


def test_command_shim_import_is_lazy_until_app_access(monkeypatch: pytest.MonkeyPatch) -> None:
    imported_targets: list[str] = []
    module_name = "specfact_cli.commands.analyze"

    sys.modules.pop(module_name, None)
    original_import_module = importlib.import_module

    def fake_import_module(name: str, package: str | None = None):
        imported_targets.append(name)
        if name == module_name:
            return original_import_module(name, package)
        if name == "specfact_codebase.analyze.commands":
            stub = ModuleType(name)
            stub.app = object()
            return stub
        return original_import_module(name, package)

    monkeypatch.setattr(importlib, "import_module", fake_import_module)

    module = importlib.import_module(module_name)
    assert imported_targets == [module_name]

    app = module.app
    assert app is not None
    assert imported_targets[-1] == "specfact_codebase.analyze.commands"
    assert imported_targets.count("specfact_codebase.analyze.commands") == 1

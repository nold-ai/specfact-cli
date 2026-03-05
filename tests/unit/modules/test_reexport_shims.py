"""Tests for legacy module re-export shims."""

from __future__ import annotations

import ast
import importlib
import warnings
from pathlib import Path

import pytest


def test_validate_shim_emits_deprecation_warning_on_attribute_access() -> None:
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        module = importlib.import_module("specfact_codebase.validate")
        _ = module.app
    assert any(issubclass(item.category, DeprecationWarning) for item in captured)


@pytest.mark.filterwarnings("ignore:specfact_codebase.analyze is deprecated")
def test_legacy_analyze_import_resolves_without_import_error() -> None:
    from specfact_codebase.analyze import app

    assert app is not None


def test_validate_shim_has_only_dunder_and_getattr_functions() -> None:
    module_path = Path("src/specfact_cli/modules/validate/__init__.py")
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    function_names = [node.name for node in tree.body if isinstance(node, ast.FunctionDef)]
    class_names = [node.name for node in tree.body if isinstance(node, ast.ClassDef)]

    assert function_names == ["__getattr__"]
    assert class_names == []


def test_validate_shim_name_is_accessible_after_import() -> None:
    module = importlib.import_module("specfact_codebase.validate")
    assert module.__name__ == "specfact_codebase.validate"

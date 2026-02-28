"""Tests for bundle package layout and legacy re-export shim behavior."""

from __future__ import annotations

import importlib
import os
import warnings
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]


def _resolve_packages_root() -> Path:
    configured = os.environ.get("SPECFACT_MODULES_REPO")
    if configured:
        return Path(configured).expanduser().resolve() / "packages"
    for candidate_base in (REPO_ROOT, *REPO_ROOT.parents):
        sibling_repo = candidate_base / "specfact-cli-modules"
        if sibling_repo.exists():
            return sibling_repo / "packages"
        sibling_repo = candidate_base.parent / "specfact-cli-modules"
        if sibling_repo.exists():
            return sibling_repo / "packages"
    return REPO_ROOT / "specfact-cli-modules" / "packages"


PACKAGES_ROOT = _resolve_packages_root()
if not PACKAGES_ROOT.exists():
    pytest.skip("specfact-cli-modules packages checkout not available", allow_module_level=True)


def test_specfact_project_namespace_init_exists() -> None:
    path = PACKAGES_ROOT / "specfact-project" / "src" / "specfact_project" / "__init__.py"
    assert path.exists()


def test_specfact_backlog_namespace_init_exists() -> None:
    path = PACKAGES_ROOT / "specfact-backlog" / "src" / "specfact_backlog" / "__init__.py"
    assert path.exists()


def test_specfact_codebase_namespace_init_exists() -> None:
    path = PACKAGES_ROOT / "specfact-codebase" / "src" / "specfact_codebase" / "__init__.py"
    assert path.exists()


def test_specfact_spec_namespace_init_exists() -> None:
    path = PACKAGES_ROOT / "specfact-spec" / "src" / "specfact_spec" / "__init__.py"
    assert path.exists()


def test_specfact_govern_namespace_init_exists() -> None:
    path = PACKAGES_ROOT / "specfact-govern" / "src" / "specfact_govern" / "__init__.py"
    assert path.exists()


def test_import_from_specfact_codebase_analyze_resolves() -> None:
    module = importlib.import_module("specfact_codebase.analyze")
    assert hasattr(module, "app")


def test_validate_shim_emits_deprecation_warning() -> None:
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        module = importlib.import_module("specfact_cli.modules.validate")
        _ = module.app
    assert any(issubclass(item.category, DeprecationWarning) for item in captured)


def test_validate_shim_resolves_without_import_error() -> None:
    module = importlib.import_module("specfact_cli.modules.validate")
    assert module is not None


def test_import_from_specfact_project_plan_resolves() -> None:
    module = importlib.import_module("specfact_project.plan")
    assert hasattr(module, "app")

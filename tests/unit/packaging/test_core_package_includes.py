"""Tests for core-only package includes in pyproject.toml / setup.py (module-migration-03)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
PYPROJECT = REPO_ROOT / "pyproject.toml"
SETUP_PY = REPO_ROOT / "setup.py"
INIT_PY = REPO_ROOT / "src" / "specfact_cli" / "__init__.py"

CORE_MODULE_NAMES = {"init", "auth", "module_registry", "upgrade"}
DELETED_17_NAMES = {
    "project",
    "plan",
    "import_cmd",
    "sync",
    "migrate",
    "backlog",
    "policy_engine",
    "analyze",
    "drift",
    "validate",
    "repro",
    "contract",
    "spec",
    "sdd",
    "generate",
    "enforce",
    "patch_mode",
}


def test_pyproject_wheel_packages_exist() -> None:
    """pyproject.toml [tool.hatch.build.targets.wheel] must define packages."""
    assert PYPROJECT.exists()
    raw = PYPROJECT.read_text(encoding="utf-8")
    assert "packages" in raw
    assert "specfact_cli" in raw


def test_pyproject_force_include_does_not_reference_deleted_modules() -> None:
    """force-include must not reference the 17 deleted module dirs (exact key match)."""
    raw = PYPROJECT.read_text(encoding="utf-8")
    for name in DELETED_17_NAMES:
        if re.search(r'"modules/' + re.escape(name) + r'"\s*=', raw):
            pytest.fail(f"pyproject force-include must not reference deleted module dir: modules/{name}")


def test_pyproject_and_init_version_sync() -> None:
    """Version in pyproject.toml and src/specfact_cli/__init__.py must match."""
    raw = PYPROJECT.read_text(encoding="utf-8")
    in_pyproject = None
    for line in raw.splitlines():
        if line.strip().startswith("version"):
            in_pyproject = line.split("=", 1)[-1].strip().strip('"').strip("'")
            break
    assert in_pyproject is not None
    init_text = INIT_PY.read_text(encoding="utf-8")
    assert f'__version__ = "{in_pyproject}"' in init_text or f"__version__ = '{in_pyproject}'" in init_text


def test_setup_py_version_matches_pyproject() -> None:
    """setup.py version must match pyproject.toml."""
    raw_pyproject = PYPROJECT.read_text(encoding="utf-8")
    version_in_pyproject = None
    for line in raw_pyproject.splitlines():
        if line.strip().startswith("version"):
            version_in_pyproject = line.split("=", 1)[-1].strip().strip('"').strip("'")
            break
    assert version_in_pyproject is not None
    setup_text = SETUP_PY.read_text(encoding="utf-8")
    assert f'version="{version_in_pyproject}"' in setup_text or f"version='{version_in_pyproject}'" in setup_text

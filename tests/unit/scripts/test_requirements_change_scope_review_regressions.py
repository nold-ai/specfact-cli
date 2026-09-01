"""Subprocess-free regressions for authenticated Requirements change scope."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


REPO_ROOT = Path(__file__).resolve().parents[3]


def _load_bootstrap_authority() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "requirements_bootstrap_authority_scope",
        REPO_ROOT / "scripts" / "requirements_bootstrap_authority.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_cycle_base() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "requirements_cycle_base_scope",
        REPO_ROOT / "scripts" / "requirements_cycle_base.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_bootstrap_red_history_uses_a_positive_test_and_change_artifact_allowlist() -> None:
    """Bootstrap authority treats unknown paths as production, not test evidence."""
    module = _load_bootstrap_authority()
    for path in ("implementation.py", "lib/implementation.py", "modules/new/module.py"):
        assert module._has_governed_production_path([path], "next-security-fix"), path
    assert not module._has_governed_production_path(["tests/unit/test_review.py"], "next-security-fix")
    assert not module._has_governed_production_path(
        ["openspec/changes/next-security-fix/specs/requirements/spec.md"], "next-security-fix"
    )
    assert module._has_governed_production_path(
        ["openspec/changes/next-security-fix/TDD_EVIDENCE.md"], "../next-security-fix"
    )
    assert module._has_governed_production_path(
        [
            "openspec/changes/first-fix/TDD_EVIDENCE.md",
            "openspec/changes/second-fix/TDD_EVIDENCE.md",
        ],
        "first-fix",
    )


def test_red_history_accepts_one_authenticated_change_scope_and_rejects_two() -> None:
    """A red segment may carry one active OpenSpec change without hardcoding its identifier."""
    module = _load_cycle_base()
    next_change = "openspec/changes/next-security-fix/specs/requirements/spec.md"

    assert module._red_history_path_is_allowed(next_change, "next-security-fix")
    assert not module._red_history_path_is_allowed(next_change, "unrelated-fix")
    assert not module._red_history_path_is_allowed(next_change, "../next-security-fix")
    assert not module._red_history_path_is_allowed(
        "openspec/changes/unrelated-fix/TDD_EVIDENCE.md", "next-security-fix"
    )

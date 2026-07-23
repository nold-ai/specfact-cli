"""Contract tests for frozen-delivery support scripts."""

from __future__ import annotations

import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_reproducible_delivery_checker_is_versioned() -> None:
    """The lock/export/fixture verifier must be available to local and CI callers."""
    checker = REPO_ROOT / "scripts" / "check_reproducible_delivery.py"
    assert checker.is_file()


def test_reproducible_delivery_checker_verifies_hashed_export() -> None:
    """The frozen export must be a checked-in, hash-protected install input."""
    checker = REPO_ROOT / "scripts" / "check_reproducible_delivery.py"
    spec = importlib.util.spec_from_file_location("check_reproducible_delivery", checker)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.LOCKED_EXPORT.is_file()
    module.verify_locked_export()


def test_reproducible_delivery_refresh_uses_locked_export_contract() -> None:
    """Refresh is explicit and re-validates the generated delivery inputs."""
    refresh = (REPO_ROOT / "scripts" / "refresh_reproducible_delivery.py").read_text(encoding="utf-8")
    assert '"uv", "lock"' in refresh
    assert '"export",' in refresh
    assert "--locked" in refresh
    assert "--no-emit-project" in refresh
    assert "check_reproducible_delivery.py" in refresh

"""Focused migration cleanup checks for module-migration-07."""

from __future__ import annotations

import re
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_no_legacy_specfact_cli_modules_import_paths() -> None:
    """Tests should not import removed in-core module package paths."""
    root = _repo_root()
    allowed_files = {
        root / "tests" / "unit" / "registry" / "test_cross_bundle_imports.py",
        root / "tests" / "unit" / "test_core_module_isolation.py",
        root / "tests" / "unit" / "models" / "test_module_package_metadata.py",
        root / "tests" / "unit" / "migration" / "test_module_migration_07_cleanup.py",
        root / "tests" / "unit" / "specfact_cli" / "test_module_migration_compatibility.py",
        root / "tests" / "unit" / "modules" / "test_bundle_import.py",
    }
    removed_module_pattern = re.compile(r"specfact_cli\.modules\.(?!init\.|module_registry\.|upgrade\.)")

    offenders: list[Path] = []
    for test_file in sorted((root / "tests").rglob("test_*.py")):
        if test_file in allowed_files:
            continue
        if removed_module_pattern.search(_read_text(test_file)):
            offenders.append(test_file.relative_to(root))

    assert offenders == [], f"Legacy import paths found: {offenders}"


def test_no_flat_topology_command_expectations() -> None:
    """Tests should assert grouped command topology instead of removed flat commands."""
    root = _repo_root()
    patterns = ("specfact plan ", "specfact import ", "specfact sync ", "specfact migrate ", "specfact patch apply")
    allowed_files = {
        root / "tests" / "unit" / "migration" / "test_module_migration_07_cleanup.py",
        root / "tests" / "integration" / "test_core_slimming.py",
    }
    offenders: list[str] = []
    for test_file in sorted((root / "tests").rglob("test_*.py")):
        if test_file in allowed_files:
            continue
        text = _read_text(test_file)
        for pattern in patterns:
            if pattern in text:
                offenders.append(f"{test_file.relative_to(root)}::{pattern.strip()}")

    assert offenders == [], f"Flat command expectations found: {offenders}"


def test_deterministic_signing_fixture_exists_and_is_pem() -> None:
    """A deterministic local PEM fixture should be present for signing tests."""
    root = _repo_root()
    key_path = root / "tests" / "fixtures" / "keys" / "test_private_key.pem"
    key_text = _read_text(key_path)
    assert "BEGIN PRIVATE KEY" in key_text
    assert "END PRIVATE KEY" in key_text

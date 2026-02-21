"""Tests for multi-location module discovery."""

from __future__ import annotations

from pathlib import Path

from specfact_cli.registry.module_discovery import discover_all_modules


def _write_manifest(root: Path, module_name: str) -> None:
    module_dir = root / module_name
    module_dir.mkdir(parents=True, exist_ok=True)
    (module_dir / "module-package.yaml").write_text(
        f"name: {module_name}\nversion: '0.1.0'\ncommands: [{module_name}]\n",
        encoding="utf-8",
    )
    (module_dir / "src").mkdir(parents=True, exist_ok=True)


def test_discover_all_modules_scans_builtin_marketplace_and_custom(tmp_path: Path) -> None:
    """Discovery should scan all available roots."""
    builtin_root = tmp_path / "builtin"
    marketplace_root = tmp_path / "marketplace"
    custom_root = tmp_path / "custom"
    _write_manifest(builtin_root, "init")
    _write_manifest(marketplace_root, "backlog")
    _write_manifest(custom_root, "drift")

    discovered = discover_all_modules(
        builtin_root=builtin_root,
        marketplace_root=marketplace_root,
        custom_root=custom_root,
    )

    names = {entry.metadata.name for entry in discovered}
    assert names == {"init", "backlog", "drift"}
    sources = {entry.metadata.name: entry.source for entry in discovered}
    assert sources["init"] == "builtin"
    assert sources["backlog"] == "marketplace"
    assert sources["drift"] == "custom"


def test_discover_all_modules_builtin_takes_priority(tmp_path: Path) -> None:
    """Built-in module should shadow marketplace/custom duplicates."""
    builtin_root = tmp_path / "builtin"
    marketplace_root = tmp_path / "marketplace"
    _write_manifest(builtin_root, "backlog")
    _write_manifest(marketplace_root, "backlog")

    discovered = discover_all_modules(
        builtin_root=builtin_root,
        marketplace_root=marketplace_root,
    )

    backlog_entries = [entry for entry in discovered if entry.metadata.name == "backlog"]
    assert len(backlog_entries) == 1
    assert backlog_entries[0].source == "builtin"


def test_discover_all_modules_handles_missing_optional_paths(tmp_path: Path) -> None:
    """Missing marketplace/custom roots should not raise."""
    builtin_root = tmp_path / "builtin"
    _write_manifest(builtin_root, "init")

    discovered = discover_all_modules(
        builtin_root=builtin_root,
        marketplace_root=tmp_path / "missing-marketplace",
        custom_root=tmp_path / "missing-custom",
    )

    assert [entry.metadata.name for entry in discovered] == ["init"]
    assert discovered[0].source == "builtin"

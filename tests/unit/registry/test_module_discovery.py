"""Tests for multi-location module discovery."""

from __future__ import annotations

from pathlib import Path

from specfact_cli.registry import module_discovery
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
        user_root=tmp_path / "missing-user",
        marketplace_root=marketplace_root,
        custom_root=custom_root,
        include_legacy_roots=False,
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
        user_root=tmp_path / "missing-user",
        marketplace_root=marketplace_root,
        include_legacy_roots=False,
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
        user_root=tmp_path / "missing-user",
        marketplace_root=tmp_path / "missing-marketplace",
        custom_root=tmp_path / "missing-custom",
        include_legacy_roots=False,
    )

    assert [entry.metadata.name for entry in discovered] == ["init"]
    assert discovered[0].source == "builtin"


def test_discover_all_modules_scans_user_root(tmp_path: Path, monkeypatch) -> None:
    """Discovery should include canonical user module root."""
    builtin_root = tmp_path / "builtin"
    user_root = tmp_path / "user-modules"
    _write_manifest(builtin_root, "init")
    _write_manifest(user_root, "backlog-core")
    monkeypatch.setattr(module_discovery, "USER_MODULES_ROOT", user_root)

    discovered = discover_all_modules(builtin_root=builtin_root)

    names = {entry.metadata.name for entry in discovered}
    assert names == {"init", "backlog-core"}
    sources = {entry.metadata.name: entry.source for entry in discovered}
    assert sources["init"] == "builtin"
    assert sources["backlog-core"] == "user"


def test_discover_all_modules_project_scope_takes_priority_over_user(tmp_path: Path, monkeypatch) -> None:
    """Workspace project modules should shadow user modules with same id."""
    repo_root = tmp_path / "repo"
    project_root = repo_root / ".specfact" / "modules"
    builtin_root = tmp_path / "builtin"
    user_root = tmp_path / "user-modules"
    _write_manifest(builtin_root, "init")
    _write_manifest(project_root, "backlog-core")
    _write_manifest(user_root, "backlog-core")

    monkeypatch.chdir(repo_root)
    discovered = discover_all_modules(
        builtin_root=builtin_root,
        user_root=user_root,
        include_legacy_roots=True,
    )

    sources = {entry.metadata.name: entry.source for entry in discovered}
    assert sources["backlog-core"] == "project"


def test_project_shadow_warning_is_actionable_and_emitted_once(tmp_path: Path, monkeypatch) -> None:
    """Project-over-user shadow guidance should be user-facing but deduplicated per process."""
    repo_root = tmp_path / "repo"
    project_root = repo_root / ".specfact" / "modules"
    builtin_root = tmp_path / "builtin"
    user_root = tmp_path / "user-modules"
    _write_manifest(builtin_root, "init")
    _write_manifest(project_root, "backlog-core")
    _write_manifest(user_root, "backlog-core")

    monkeypatch.chdir(repo_root)
    warnings: list[str] = []
    monkeypatch.setattr(module_discovery, "print_warning", warnings.append)
    module_discovery._SHADOW_HINT_KEYS.clear()

    discover_all_modules(
        builtin_root=builtin_root,
        user_root=user_root,
        include_legacy_roots=True,
    )
    discover_all_modules(
        builtin_root=builtin_root,
        user_root=user_root,
        include_legacy_roots=True,
    )

    assert len(warnings) == 1
    assert "takes precedence over user-scoped module" in warnings[0]
    assert "specfact module list --show-origin" in warnings[0]
    assert "specfact module uninstall backlog-core --scope user" in warnings[0]

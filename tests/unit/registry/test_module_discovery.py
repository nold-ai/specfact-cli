"""Tests for multi-location module discovery."""

from __future__ import annotations

from pathlib import Path

import pytest

from specfact_cli.registry import module_discovery
from specfact_cli.registry.module_discovery import discover_all_modules, discover_all_modules_for_project


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


def test_discover_all_modules_skips_missing_optional_roots(tmp_path: Path) -> None:
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


def test_discover_all_modules_scans_user_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
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


def test_discover_all_modules_project_scope_takes_priority_over_user(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
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


def test_explicit_module_roots_take_priority_over_user_installs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Explicit module roots are developer-selected sources and should shadow stale user installs."""
    builtin_root = tmp_path / "builtin"
    explicit_root = tmp_path / "modules-repo" / "packages"
    user_root = tmp_path / "user-modules"
    _write_manifest(builtin_root, "init")
    _write_manifest(explicit_root, "code-review")
    _write_manifest(user_root, "code-review")
    monkeypatch.setenv("SPECFACT_MODULES_ROOTS", str(explicit_root))

    discovered = discover_all_modules(
        builtin_root=builtin_root,
        user_root=user_root,
        include_legacy_roots=False,
    )

    sources = {entry.metadata.name: entry.source for entry in discovered}
    assert sources["code-review"] == "custom"


def test_project_shadow_warning_is_actionable_and_emitted_once(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
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
    assert "remains installed" in warnings[0]
    assert "availability outside this workspace depends on module state" in warnings[0]
    assert "available outside this workspace" not in warnings[0]
    assert "module uninstall" not in warnings[0]


def test_user_module_is_discovered_outside_shadowing_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A preserved user copy is discoverable where no project copy shadows it."""
    repo_root = tmp_path / "other-repo"
    builtin_root = tmp_path / "builtin"
    user_root = tmp_path / "user-modules"
    repo_root.mkdir()
    _write_manifest(builtin_root, "init")
    _write_manifest(user_root, "backlog-core")
    monkeypatch.chdir(repo_root)

    discovered = discover_all_modules(
        builtin_root=builtin_root,
        user_root=user_root,
        include_legacy_roots=False,
    )

    backlog = next(entry for entry in discovered if entry.metadata.name == "backlog-core")
    assert backlog.source == "user"


def test_discover_all_modules_with_explicit_user_root_preserves_project_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """First-run discovery passes user_root explicitly but still needs project modules."""
    repo_root = tmp_path / "repo"
    project_root = repo_root / ".specfact" / "modules"
    builtin_root = tmp_path / "builtin"
    user_root = tmp_path / "user-modules"
    _write_manifest(builtin_root, "init")
    _write_manifest(project_root, "project-only")

    monkeypatch.chdir(repo_root)
    monkeypatch.setattr(module_discovery, "MARKETPLACE_MODULES_ROOT", tmp_path / "missing-marketplace")
    monkeypatch.setattr(module_discovery, "CUSTOM_MODULES_ROOT", tmp_path / "missing-custom")
    monkeypatch.setattr(
        "specfact_cli.registry.module_packages.get_modules_root",
        lambda: builtin_root,
    )

    discovered = discover_all_modules(user_root=user_root)

    sources = {entry.metadata.name: entry.source for entry in discovered}
    assert sources == {"init": "builtin", "project-only": "project"}


def test_discover_all_modules_for_project_ignores_cwd_legacy_roots_by_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Project-scoped discovery should not leak extra legacy roots from the current cwd."""
    repo_root = tmp_path / "repo"
    project_root = repo_root / ".specfact" / "modules"
    builtin_root = tmp_path / "builtin"
    legacy_root = tmp_path / "legacy-modules"
    _write_manifest(builtin_root, "init")
    _write_manifest(project_root, "project-only")
    _write_manifest(legacy_root, "legacy-only")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(module_discovery, "USER_MODULES_ROOT", tmp_path / "missing-user")
    monkeypatch.setattr(module_discovery, "MARKETPLACE_MODULES_ROOT", tmp_path / "missing-marketplace")
    monkeypatch.setattr(module_discovery, "CUSTOM_MODULES_ROOT", tmp_path / "missing-custom")
    monkeypatch.setattr(
        "specfact_cli.registry.module_packages.get_modules_root",
        lambda: builtin_root,
    )
    monkeypatch.setattr(
        "specfact_cli.registry.module_packages.get_modules_roots",
        lambda: [legacy_root],
    )

    discovered = discover_all_modules_for_project(repo_root)

    names = {entry.metadata.name for entry in discovered}
    assert names == {"init", "project-only"}


def test_canonical_user_root_is_not_reported_as_project_shadow(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Running from home should not treat the canonical user root as a conflicting project root."""
    home_root = tmp_path / "home"
    builtin_root = tmp_path / "builtin"
    user_root = home_root / ".specfact" / "modules"
    _write_manifest(builtin_root, "init")
    _write_manifest(user_root, "backlog-core")

    monkeypatch.chdir(home_root)
    monkeypatch.setattr(module_discovery, "USER_MODULES_ROOT", user_root)
    warnings: list[str] = []
    monkeypatch.setattr(module_discovery, "print_warning", warnings.append)
    module_discovery._SHADOW_HINT_KEYS.clear()

    discovered = discover_all_modules(
        builtin_root=builtin_root,
        user_root=user_root,
        include_legacy_roots=False,
    )

    backlog_entries = [entry for entry in discovered if entry.metadata.name == "backlog-core"]
    assert len(backlog_entries) == 1
    assert backlog_entries[0].source == "user"
    assert warnings == []

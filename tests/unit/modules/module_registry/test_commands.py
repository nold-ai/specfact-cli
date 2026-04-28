"""Tests for module marketplace CLI commands."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from specfact_cli.models.module_package import ModulePackageMetadata
from specfact_cli.modules.module_registry.src.commands import app
from specfact_cli.registry.module_installer import USER_MODULES_ROOT, InstallModuleOptions


runner = CliRunner()


@pytest.fixture(autouse=True)
def _isolate_user_modules_root(monkeypatch, tmp_path: Path) -> None:
    """Isolate user module root so tests do not depend on machine-local installs."""
    user_root = tmp_path / "user-modules"
    user_root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.USER_MODULES_ROOT", user_root)
    monkeypatch.setattr("specfact_cli.registry.module_installer.USER_MODULES_ROOT", user_root, raising=False)


def test_install_command_integration(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.discover_all_modules", list)
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.install_module",
        lambda module_id, options=None, **_kwargs: tmp_path / module_id.split("/")[-1],
    )

    result = runner.invoke(app, ["install", "specfact/backlog"])

    assert result.exit_code == 0
    assert "Installed" in result.stdout
    assert "specfact/backlog" in result.stdout


def test_install_command_accepts_bare_module_name(monkeypatch, tmp_path: Path) -> None:
    captured: dict[str, str | None] = {"module_id": None}

    def _install(module_id: str, options: InstallModuleOptions | None = None, **_kwargs):
        captured["module_id"] = module_id
        return tmp_path / module_id.split("/")[-1]

    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.discover_all_modules", list)
    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.install_module", _install)
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.install_bundled_module",
        lambda module_name, target_root, **_kwargs: False,
    )

    result = runner.invoke(app, ["install", "bundle-mapper"])

    assert result.exit_code == 0
    assert captured["module_id"] == "specfact/bundle-mapper"
    assert "Installed" in result.stdout


def test_install_command_rejects_invalid_module_id(monkeypatch) -> None:
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.install_module", lambda *_args, **_kwargs: None
    )

    result = runner.invoke(app, ["install", "a/b/c"])

    assert result.exit_code == 1
    assert "Invalid module id" in result.stdout


def test_install_command_skips_when_module_already_available_locally(monkeypatch, tmp_path: Path) -> None:
    class _Meta:
        name = "bundle-mapper"

    class _Entry:
        metadata = _Meta()
        source = "custom"

    called = {"install": False}

    def _install(module_id: str, options: InstallModuleOptions | None = None, **_kwargs):
        called["install"] = True
        return tmp_path / module_id.split("/")[-1]

    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.discover_all_modules", lambda: [_Entry()])
    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.install_module", _install)

    result = runner.invoke(app, ["install", "bundle-mapper"])

    assert result.exit_code == 0
    assert called["install"] is False
    assert "already installed" in result.stdout or "already available" in result.stdout


def test_install_command_existing_disabled_module_enables_state(monkeypatch, tmp_path: Path) -> None:
    install_root = tmp_path / "user-modules"
    installed_module = install_root / "specfact-codebase"
    installed_module.mkdir(parents=True)
    (installed_module / "module-package.yaml").write_text(
        "name: nold-ai/specfact-codebase\nversion: '0.1.0'\ncommands: [analyze]\n",
        encoding="utf-8",
    )
    enabled: list[list[str]] = []
    captured_state: list[list[dict[str, object]]] = []

    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.USER_MODULES_ROOT", install_root)
    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.discover_all_modules", list)
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.install_module", lambda *_args, **_kwargs: None
    )
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.read_modules_state",
        lambda: {"nold-ai/specfact-codebase": {"version": "0.1.0", "enabled": False}},
    )
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.get_discovered_modules_for_state",
        lambda *, enable_ids, disable_ids, base_path=None, preserve_existing: (
            enabled.append(list(enable_ids))
            or [
                {"id": "nold-ai/specfact-codebase", "version": "0.1.0", "enabled": True},
                {"id": "unrelated-module", "version": "9.9.9", "enabled": False},
            ]
        ),
    )
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.write_modules_state",
        lambda modules: captured_state.append(modules),
    )
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.run_discovery_and_write_cache", lambda _: None
    )

    result = runner.invoke(app, ["install", "nold-ai/specfact-codebase"])

    assert result.exit_code == 0
    assert enabled == [["nold-ai/specfact-codebase"]]
    assert captured_state == [
        [
            {"id": "nold-ai/specfact-codebase", "version": "0.1.0", "enabled": True},
            {"id": "unrelated-module", "version": "9.9.9", "enabled": False},
        ]
    ]
    assert "enabled" in result.stdout.lower()


def test_install_command_project_scope_reenable_uses_selected_repo(monkeypatch, tmp_path: Path) -> None:
    repo_path = tmp_path / "repo"
    install_root = repo_path / ".specfact" / "modules"
    installed_module = install_root / "specfact-codebase"
    installed_module.mkdir(parents=True)
    (installed_module / "module-package.yaml").write_text(
        "name: nold-ai/specfact-codebase\nversion: '0.1.0'\ncommands: [analyze]\n",
        encoding="utf-8",
    )
    base_paths: list[Path | None] = []
    state_by_id = {"nold-ai/specfact-codebase": {"version": "0.1.0", "enabled": False}}

    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.discover_all_modules_for_project", lambda path: []
    )
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.install_module", lambda *_args, **_kwargs: None
    )

    def _read_state():
        return dict(state_by_id)

    def _discover_state(*, enable_ids, disable_ids, base_path=None, preserve_existing):
        base_paths.append(base_path)
        return [{"id": "nold-ai/specfact-codebase", "version": "0.1.0", "enabled": True}]

    def _write_state(modules):
        for row in modules:
            state_by_id[str(row["id"])] = {"version": str(row["version"]), "enabled": bool(row["enabled"])}

    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.read_modules_state", _read_state)
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.get_discovered_modules_for_state",
        _discover_state,
    )
    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.write_modules_state", _write_state)
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.run_discovery_and_write_cache", lambda _: None
    )

    result = runner.invoke(
        app, ["install", "nold-ai/specfact-codebase", "--scope", "project", "--repo", str(repo_path)]
    )

    assert result.exit_code == 0
    assert base_paths == [repo_path]
    assert state_by_id["nold-ai/specfact-codebase"]["enabled"] is True
    assert "enabled" in result.stdout.lower()


def test_install_command_project_scope_installs_to_project_modules_root(monkeypatch, tmp_path: Path) -> None:
    captured: dict[str, object] = {"install_root": None, "module_id": None}

    def _install(module_id: str, options: InstallModuleOptions | None = None, **_kwargs):
        o = options or InstallModuleOptions()
        captured["module_id"] = module_id
        captured["install_root"] = o.install_root
        return tmp_path / "installed"

    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.discover_all_modules", list)
    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.install_module", _install)
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.install_bundled_module",
        lambda module_name, target_root, **_kwargs: False,
        raising=False,
    )

    repo_path = tmp_path / "repo"
    repo_path.mkdir(parents=True)
    result = runner.invoke(app, ["install", "backlog", "--scope", "project", "--repo", str(repo_path)])

    assert result.exit_code == 0
    assert captured["module_id"] == "specfact/backlog"
    assert captured["install_root"] == repo_path / ".specfact" / "modules"


def test_install_command_prefers_bundled_source_when_available(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.discover_all_modules", list)
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.get_bundled_module_metadata",
        lambda: {
            "bundle-mapper": ModulePackageMetadata(
                name="bundle-mapper",
                version="0.1.0",
                description="Bundled mapper",
            )
        },
        raising=False,
    )

    called = {"bundled": False, "marketplace": False}

    def _install_bundled(module_name: str, target_root: Path, **_kwargs) -> bool:
        called["bundled"] = module_name == "bundle-mapper"
        return True

    def _install_marketplace(*_args, **_kwargs):
        called["marketplace"] = True
        raise AssertionError("Marketplace installer must not be called when bundled module exists")

    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.install_bundled_module",
        _install_bundled,
        raising=False,
    )
    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.install_module", _install_marketplace)

    result = runner.invoke(app, ["install", "bundle-mapper"])

    assert result.exit_code == 0
    assert called["bundled"] is True
    assert called["marketplace"] is False


def test_install_command_project_scope_does_not_skip_when_user_scope_module_exists(monkeypatch, tmp_path: Path) -> None:
    class _Meta:
        name = "bundle-mapper"

    class _Entry:
        metadata = _Meta()
        source = "user"

    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.discover_all_modules", lambda: [_Entry()])

    called = {"marketplace": False}

    def _install_marketplace(module_id: str, options: InstallModuleOptions | None = None, **_kwargs):
        called["marketplace"] = True
        return tmp_path / module_id.split("/")[-1]

    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.install_module", _install_marketplace)
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.install_bundled_module",
        lambda module_name, target_root, **_kwargs: False,
    )

    repo_path = tmp_path / "repo"
    repo_path.mkdir(parents=True)
    result = runner.invoke(app, ["install", "bundle-mapper", "--scope", "project", "--repo", str(repo_path)])

    assert result.exit_code == 0
    assert called["marketplace"] is True


def test_install_command_source_marketplace_skips_bundled_resolution(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.discover_all_modules", list)
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.get_bundled_module_metadata",
        lambda: {"bundle-mapper": ModulePackageMetadata(name="bundle-mapper", version="0.1.0")},
    )

    called = {"bundled": False, "marketplace": False}

    def _bundled(*_args, **_kwargs):
        called["bundled"] = True
        return True

    def _marketplace(module_id: str, options: InstallModuleOptions | None = None, **_kwargs):
        called["marketplace"] = True
        return tmp_path / module_id.split("/")[-1]

    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.install_bundled_module", _bundled)
    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.install_module", _marketplace)

    result = runner.invoke(app, ["install", "bundle-mapper", "--source", "marketplace"])

    assert result.exit_code == 0
    assert called["bundled"] is False
    assert called["marketplace"] is True


def test_install_command_requires_explicit_trust_for_non_official_in_non_interactive(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.discover_all_modules", list)
    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.is_non_interactive", lambda: True)

    def _install(module_id: str, options: InstallModuleOptions | None = None, **_kwargs):
        o = options or InstallModuleOptions()
        if not o.trust_non_official and o.non_interactive:
            raise ValueError("requires --trust-non-official")
        return tmp_path / module_id.split("/")[-1]

    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.install_module", _install)
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.install_bundled_module",
        lambda module_name, target_root, **_kwargs: False,
        raising=False,
    )

    result = runner.invoke(app, ["install", "community-module", "--source", "marketplace"])

    assert result.exit_code == 1
    assert "--trust-non-official" in result.stdout


def test_install_command_passes_trust_flag_to_marketplace_installer(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.discover_all_modules", list)
    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.is_non_interactive", lambda: True)
    captured: dict[str, bool | None] = {"trust_non_official": None, "non_interactive": None}

    def _install(module_id: str, options: InstallModuleOptions | None = None, **_kwargs):
        o = options or InstallModuleOptions()
        captured["trust_non_official"] = o.trust_non_official
        captured["non_interactive"] = o.non_interactive
        return tmp_path / module_id.split("/")[-1]

    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.install_module", _install)
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.install_bundled_module",
        lambda module_name, target_root, **_kwargs: False,
        raising=False,
    )

    result = runner.invoke(app, ["install", "community-module", "--source", "marketplace", "--trust-non-official"])

    assert result.exit_code == 0
    assert captured["trust_non_official"] is True
    assert captured["non_interactive"] is True


def test_module_init_passes_trust_flag_and_non_interactive(monkeypatch, tmp_path: Path) -> None:
    captured: dict[str, object] = {"trust_non_official": None, "non_interactive": None}

    def _sync(*, target_root, trust_non_official=False, non_interactive=False):
        captured["trust_non_official"] = trust_non_official
        captured["non_interactive"] = non_interactive
        return 1

    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.sync_bundled_modules_to_user_root", _sync)
    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.is_non_interactive", lambda: True)

    result = runner.invoke(app, ["init", "--scope", "project", "--repo", str(tmp_path), "--trust-non-official"])

    assert result.exit_code == 0
    assert captured["trust_non_official"] is True
    assert captured["non_interactive"] is True


def test_uninstall_command_with_source_validation(monkeypatch) -> None:
    called = {"ok": False}

    class _Meta:
        name = "backlog"

    class _Entry:
        metadata = _Meta()
        source = "marketplace"

    def fake_uninstall(module_name: str, **_kwargs) -> None:
        called["ok"] = module_name == "backlog"

    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.discover_all_modules", lambda: [_Entry()])
    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.uninstall_module", fake_uninstall)

    result = runner.invoke(app, ["uninstall", "backlog"])

    assert result.exit_code == 0
    assert called["ok"] is True


def test_uninstall_command_requires_scope_when_module_exists_in_user_and_project(monkeypatch, tmp_path: Path) -> None:
    repo_path = tmp_path / "repo"
    project_modules = repo_path / ".specfact" / "modules" / "bundle-mapper"
    user_modules = tmp_path / "user-modules" / "bundle-mapper"
    project_modules.mkdir(parents=True)
    user_modules.mkdir(parents=True)

    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.USER_MODULES_ROOT", tmp_path / "user-modules"
    )
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.discover_all_modules",
        list,
    )

    result = runner.invoke(app, ["uninstall", "bundle-mapper", "--repo", str(repo_path)])

    assert result.exit_code == 1
    assert "exists in both user and project module roots" in result.stdout
    assert "--scope" in result.stdout
    assert "user" in result.stdout
    assert "project" in result.stdout


def test_uninstall_command_custom_module_has_clear_guidance(monkeypatch) -> None:
    class _Meta:
        name = "bundle-mapper"

    class _Entry:
        metadata = _Meta()
        source = "custom"

    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.discover_all_modules", lambda: [_Entry()])

    result = runner.invoke(app, ["uninstall", "bundle-mapper"])

    assert result.exit_code == 1
    assert "Cannot uninstall custom module 'bundle-mapper'" in result.stdout
    assert "local module roots" in result.stdout


def test_uninstall_command_namespace_input_normalizes_name(monkeypatch) -> None:
    class _Meta:
        name = "bundle-mapper"

    class _Entry:
        metadata = _Meta()
        source = "custom"

    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.discover_all_modules", lambda: [_Entry()])

    result = runner.invoke(app, ["uninstall", "specfact/bundle-mapper"])

    assert result.exit_code == 1
    assert "Cannot uninstall custom module 'bundle-mapper'" in result.stdout


def test_uninstall_command_unknown_module_has_clear_guidance(monkeypatch) -> None:
    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.discover_all_modules", list)

    result = runner.invoke(app, ["uninstall", "specfact/missing-module"])

    assert result.exit_code == 1
    assert "is not installed from marketplace" in result.stdout
    assert "module list --show-origin" in result.stdout


def test_search_command_filters_registry(monkeypatch) -> None:
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.fetch_all_indexes",
        lambda: [
            (
                "official",
                {
                    "schema_version": "1.0.0",
                    "modules": [
                        {
                            "id": "specfact/backlog",
                            "description": "Backlog workflows",
                            "latest_version": "0.1.0",
                            "tags": ["backlog", "scrum"],
                        },
                        {
                            "id": "specfact/policy",
                            "description": "Policy engine",
                            "latest_version": "0.1.0",
                            "tags": ["governance"],
                        },
                    ],
                },
            )
        ],
    )

    result = runner.invoke(app, ["search", "backlog"])

    assert result.exit_code == 0
    assert "Module Search Results" in result.stdout
    assert "specfact/backlog" in result.stdout
    assert "marketplace" in result.stdout
    assert "specfact/policy" not in result.stdout


def test_search_command_sorts_results_alphabetically(monkeypatch) -> None:
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.fetch_all_indexes",
        lambda: [
            (
                "official",
                {
                    "schema_version": "1.0.0",
                    "modules": [
                        {
                            "id": "specfact/zeta",
                            "description": "Zeta module",
                            "latest_version": "0.1.0",
                            "tags": ["bundle"],
                        },
                        {
                            "id": "specfact/alpha",
                            "description": "Alpha module",
                            "latest_version": "0.1.0",
                            "tags": ["bundle"],
                        },
                    ],
                },
            )
        ],
    )
    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.discover_all_modules", list)

    result = runner.invoke(app, ["search", "module"])

    assert result.exit_code == 0
    assert "specfact/alpha" in result.stdout
    assert "specfact/zeta" in result.stdout
    pos_alpha = result.stdout.index("specfact/alpha")
    pos_zeta = result.stdout.index("specfact/zeta")
    assert pos_alpha < pos_zeta


def test_search_command_finds_installed_module_when_not_in_registry(monkeypatch) -> None:
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.fetch_all_indexes", lambda: [("official", {"modules": []})]
    )

    class _Meta:
        name = "bundle-mapper"
        version = "0.1.0"
        description = "Maps backlog items to modules"
        publisher = None

    class _Entry:
        metadata = _Meta()
        source = "custom"

    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.discover_all_modules", lambda: [_Entry()])

    result = runner.invoke(app, ["search", "bundle-mapper"])

    assert result.exit_code == 0
    assert "Module Search Results" in result.stdout
    assert "bundle-mapper" in result.stdout
    assert "installed" in result.stdout


def test_search_command_reports_no_results_with_query_context(monkeypatch) -> None:
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.fetch_all_indexes", lambda: [("official", {"modules": []})]
    )
    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.discover_all_modules", list)

    result = runner.invoke(app, ["search", "does-not-exist"])

    assert result.exit_code == 0
    assert "No modules found for query 'does-not-exist'" in result.stdout


def test_list_command_sorts_modules_alphabetically(monkeypatch) -> None:
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.get_modules_with_state",
        lambda: [
            {
                "id": "zeta",
                "version": "0.1.0",
                "enabled": True,
                "source": "builtin",
                "official": True,
                "publisher": "nold-ai",
            },
            {
                "id": "alpha",
                "version": "0.1.0",
                "enabled": True,
                "source": "builtin",
                "official": True,
                "publisher": "nold-ai",
            },
        ],
    )

    result = runner.invoke(app, ["list"])

    assert result.exit_code == 0
    assert result.stdout.index("alpha") < result.stdout.index("zeta")


def test_enable_command_message_sorts_module_ids(monkeypatch) -> None:
    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.is_non_interactive", lambda: False)
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.get_modules_with_state",
        lambda: [
            {"id": "alpha", "version": "0.1.0", "enabled": False, "source": "marketplace"},
            {"id": "zeta", "version": "0.1.0", "enabled": False, "source": "marketplace"},
        ],
    )
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.select_module_ids_interactive",
        lambda *_args, **_kwargs: ["zeta", "alpha"],
    )
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.apply_module_state_update",
        lambda **_kwargs: [],
    )

    result = runner.invoke(app, ["enable"])

    assert result.exit_code == 0
    assert "Enabled" in result.stdout
    assert "alpha, zeta" in result.stdout


def test_list_command_shows_version_state_and_trust(monkeypatch) -> None:
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.get_modules_with_state",
        lambda: [
            {
                "id": "init",
                "version": "0.1.0",
                "enabled": True,
                "source": "builtin",
                "official": True,
                "publisher": "nold-ai",
            },
            {
                "id": "backlog",
                "version": "0.2.0",
                "enabled": False,
                "source": "marketplace",
                "official": False,
                "publisher": "community-dev",
            },
        ],
    )

    result = runner.invoke(app, ["list"])

    assert result.exit_code == 0
    assert "Trust" in result.stdout
    assert "Publisher" in result.stdout
    assert "init" in result.stdout
    assert "0.1.0" in result.stdout
    assert "enabled" in result.stdout
    assert "official" in result.stdout
    assert "backlog" in result.stdout
    assert "disabled" in result.stdout
    assert "community" in result.stdout
    assert "nold-ai" in result.stdout
    assert "community-dev" in result.stdout


def test_list_command_marketplace_option_shows_registry_modules(monkeypatch) -> None:
    """specfact module list --marketplace shows modules from the registry index."""
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.fetch_registry_index",
        lambda **_: {
            "modules": [
                {"id": "nold-ai/specfact-backlog", "latest_version": "0.40.0", "description": "Backlog workflows"},
                {"id": "nold-ai/specfact-codebase", "latest_version": "0.40.0", "description": "Codebase analysis"},
            ]
        },
    )
    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.get_modules_with_state", list)

    result = runner.invoke(app, ["list", "--marketplace"])

    assert result.exit_code == 0
    assert "Marketplace Modules Available" in result.stdout
    assert "nold-ai/specfact-backlog" in result.stdout
    assert "nold-ai/specfact-codebase" in result.stdout
    assert "specfact module install" in result.stdout


def test_list_command_marketplace_option_offline_shows_warning(monkeypatch) -> None:
    """specfact module list --marketplace when registry unavailable shows friendly message."""
    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.fetch_registry_index", lambda **_: None)
    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.get_modules_with_state", list)

    result = runner.invoke(app, ["list", "--marketplace"])

    assert result.exit_code == 0
    assert "unavailable" in result.stdout.lower() or "offline" in result.stdout.lower()


def test_list_command_shows_official_label_when_marked(monkeypatch) -> None:
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.get_modules_with_state",
        lambda: [
            {
                "id": "bundle-mapper",
                "version": "0.1.0",
                "enabled": True,
                "source": "custom",
                "official": True,
                "publisher": "nold-ai",
            }
        ],
    )

    result = runner.invoke(app, ["list"])

    assert result.exit_code == 0
    assert "official" in result.stdout
    assert "custom" not in result.stdout


def test_list_command_show_origin_includes_origin_column(monkeypatch) -> None:
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.get_modules_with_state",
        lambda: [
            {
                "id": "bundle-mapper",
                "version": "0.1.0",
                "enabled": True,
                "source": "custom",
                "official": True,
                "publisher": "nold-ai",
            },
            {
                "id": "community-module",
                "version": "0.1.0",
                "enabled": True,
                "source": "marketplace",
                "official": False,
                "publisher": "community-dev",
            },
        ],
    )

    result = runner.invoke(app, ["list", "--show-origin"])

    assert result.exit_code == 0
    assert "Origin" in result.stdout
    assert "official" in result.stdout
    assert "community" in result.stdout
    assert "nold-ai" in result.stdout
    assert "community-dev" in result.stdout
    assert "custom" in result.stdout
    assert "marketplace" in result.stdout


def test_list_command_source_filter(monkeypatch) -> None:
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.get_modules_with_state",
        lambda: [
            {"id": "init", "version": "0.1.0", "enabled": True, "source": "builtin", "publisher": "nold-ai"},
            {
                "id": "backlog",
                "version": "0.2.0",
                "enabled": False,
                "source": "marketplace",
                "publisher": "community-dev",
            },
        ],
    )

    result = runner.invoke(app, ["list", "--source", "marketplace"])

    assert result.exit_code == 0
    assert "backlog" in result.stdout
    assert "init" not in result.stdout


def test_list_command_bundled_available_uses_unfiltered_installed_set(monkeypatch) -> None:
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.get_modules_with_state",
        lambda: [
            {
                "id": "init",
                "version": "0.1.0",
                "enabled": True,
                "source": "builtin",
                "official": True,
                "publisher": "nold-ai",
            },
            {
                "id": "backlog-core",
                "version": "0.2.0",
                "enabled": True,
                "source": "project",
                "official": True,
                "publisher": "nold-ai",
            },
        ],
    )
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.get_bundled_module_metadata",
        lambda: {
            "init": ModulePackageMetadata(name="init", version="0.1.0", description="Core init module"),
            "backlog-core": ModulePackageMetadata(name="backlog-core", version="0.2.0", description="Backlog"),
        },
        raising=False,
    )

    result = runner.invoke(app, ["list", "--source", "builtin", "--show-bundled-available"])

    assert result.exit_code == 0
    assert "Bundled Modules Available" not in result.stdout
    assert "All bundled modules are already installed" in result.stdout


def test_list_command_show_bundled_available_separate_section_with_hints(monkeypatch) -> None:
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.get_modules_with_state",
        lambda: [
            {
                "id": "init",
                "version": "0.1.0",
                "enabled": True,
                "source": "builtin",
                "official": True,
                "publisher": "nold-ai",
            },
        ],
    )
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.get_bundled_module_metadata",
        lambda: {
            "init": ModulePackageMetadata(name="init", version="0.1.0", description="Core init module"),
            "backlog-core": ModulePackageMetadata(
                name="backlog-core",
                version="0.2.0",
                description="Backlog workflows",
            ),
        },
        raising=False,
    )

    result = runner.invoke(app, ["list", "--show-bundled-available"])

    assert result.exit_code == 0
    assert "Bundled Modules Available" in result.stdout
    assert "backlog-core" in result.stdout
    assert "specfact module init" in result.stdout
    assert "specfact module init --scope project" in result.stdout


def test_list_command_show_bundled_available_empty_when_all_installed(monkeypatch) -> None:
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.get_modules_with_state",
        lambda: [
            {
                "id": "init",
                "version": "0.1.0",
                "enabled": True,
                "source": "builtin",
                "official": True,
                "publisher": "nold-ai",
            },
        ],
    )
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.get_bundled_module_metadata",
        lambda: {
            "init": ModulePackageMetadata(name="init", version="0.1.0", description="Core init module"),
        },
        raising=False,
    )

    result = runner.invoke(app, ["list", "--show-bundled-available"])

    assert result.exit_code == 0
    assert "Bundled Modules Available" not in result.stdout
    assert "All bundled modules are already installed" in result.stdout


def test_list_command_without_flag_shows_hint_when_bundled_available(monkeypatch) -> None:
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.get_modules_with_state",
        lambda: [
            {
                "id": "init",
                "version": "0.1.0",
                "enabled": True,
                "source": "builtin",
                "official": True,
                "publisher": "nold-ai",
            },
        ],
    )
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.get_bundled_module_metadata",
        lambda: {
            "init": ModulePackageMetadata(name="init", version="0.1.0", description="Core init module"),
            "backlog-core": ModulePackageMetadata(name="backlog-core", version="0.2.0", description="Backlog"),
        },
    )

    result = runner.invoke(app, ["list"])

    assert result.exit_code == 0
    assert "--show-bundled-available" in result.stdout


def test_list_command_fetches_module_state_once(monkeypatch) -> None:
    calls = {"count": 0}

    def _get_modules_with_state() -> list[dict[str, object]]:
        calls["count"] += 1
        return [
            {
                "id": "init",
                "version": "0.1.0",
                "enabled": True,
                "source": "builtin",
                "official": True,
                "publisher": "nold-ai",
            }
        ]

    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.get_modules_with_state", _get_modules_with_state
    )
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.get_bundled_module_metadata",
        lambda: {
            "init": ModulePackageMetadata(name="init", version="0.1.0", description="Core init module"),
        },
    )

    result = runner.invoke(app, ["list"])

    assert result.exit_code == 0
    assert calls["count"] == 1


def test_show_command_displays_module_details(monkeypatch) -> None:
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.get_modules_with_state",
        lambda: [
            {
                "id": "bundle-mapper",
                "version": "0.1.0",
                "enabled": True,
                "source": "custom",
                "official": True,
                "publisher": "nold-ai",
            }
        ],
    )

    class _Meta:
        name = "bundle-mapper"
        description = "Maps backlog items to modules using confidence heuristics"
        license = "Apache-2.0"
        tier = "community"
        commands = ["backlog"]
        core_compatibility = ">=0.28.0,<1.0.0"

        class publisher:  # noqa: N801
            attributes = {"url": "https://github.com/nold-ai/specfact-cli-modules"}

    class _Entry:
        metadata = _Meta()

    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.discover_all_modules",
        lambda: [_Entry()],
    )

    result = runner.invoke(app, ["show", "bundle-mapper"])

    assert result.exit_code == 0
    assert "Module Details: bundle-mapper" in result.stdout
    assert "Description" in result.stdout
    assert "Apache-2.0" in result.stdout
    assert "Publisher" in result.stdout
    assert "nold-ai" in result.stdout
    assert "Trust" in result.stdout
    assert "official" in result.stdout


def test_show_command_uses_command_help_keys_when_commands_missing(monkeypatch) -> None:
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.get_modules_with_state",
        lambda: [
            {
                "id": "module-registry",
                "version": "0.35.0",
                "enabled": True,
                "source": "builtin",
                "official": True,
                "publisher": "nold-ai",
            }
        ],
    )

    class _Meta:
        name = "module-registry"
        description = "Manage modules"
        license = "Apache-2.0"
        tier = "community"
        commands = []
        command_help = {"list": "List modules", "show": "Show module details"}
        core_compatibility = ">=0.28.0,<1.0.0"

        class publisher:  # noqa: N801
            attributes = {"url": "https://github.com/nold-ai/specfact-cli-modules"}

    class _Entry:
        metadata = _Meta()

    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.discover_all_modules", lambda: [_Entry()])

    result = runner.invoke(app, ["show", "module-registry"])

    assert result.exit_code == 0
    assert "Commands" in result.stdout
    assert "list" in result.stdout
    assert "show" in result.stdout


def test_show_command_derives_full_command_paths_with_subcommands(monkeypatch) -> None:
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.get_modules_with_state",
        lambda: [
            {
                "id": "module-registry",
                "version": "0.35.0",
                "enabled": True,
                "source": "builtin",
                "official": True,
                "publisher": "nold-ai",
            }
        ],
    )

    class _Meta:
        name = "module-registry"
        description = "Manage modules"
        license = "Apache-2.0"
        tier = "community"
        commands = ["module"]
        command_help = {"module": "Manage modules"}
        core_compatibility = ">=0.28.0,<1.0.0"

        class publisher:  # noqa: N801
            attributes = {"url": "https://github.com/nold-ai/specfact-cli-modules"}

    class _Entry:
        metadata = _Meta()

    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.discover_all_modules", lambda: [_Entry()])

    class _CmdInfo:
        def __init__(self, name: str, help_text: str) -> None:
            self.name = name
            self.help = help_text
            self.callback = None

    class _GroupInfo:
        def __init__(self, name: str, typer_instance: object) -> None:
            self.name = name
            self.typer_instance = typer_instance

    class _FakeTyper:
        def __init__(self, commands: list[tuple[str, str]], groups: list[object]) -> None:
            self.registered_commands = [_CmdInfo(name, help_text) for name, help_text in commands]
            self.registered_groups = groups

    delta_app = _FakeTyper([("status", "Show delta status")], [])
    root_app = _FakeTyper([("list", "List modules"), ("show", "Show module details")], [_GroupInfo("delta", delta_app)])

    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.CommandRegistry.get_typer", lambda _name: root_app
    )

    result = runner.invoke(app, ["show", "module-registry"])

    assert result.exit_code == 0
    assert "module list - List modules" in result.stdout
    assert "module show - Show module details" in result.stdout
    assert "module delta" in result.stdout
    assert "module delta status - Show delta status" in result.stdout


def test_show_command_fails_for_unknown_module(monkeypatch) -> None:
    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.get_modules_with_state", list)

    result = runner.invoke(app, ["show", "missing-module"])

    assert result.exit_code == 1
    assert "is not installed" in result.stdout


def test_upgrade_command(monkeypatch, tmp_path: Path) -> None:
    captured: dict[str, bool | None] = {"reinstall": None}

    def _install(module_id: str, options: InstallModuleOptions | None = None, **_kwargs):
        o = options or InstallModuleOptions()
        captured["reinstall"] = o.reinstall
        return tmp_path / module_id.split("/")[-1]

    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.install_module",
        _install,
    )
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.get_modules_with_state",
        lambda: [{"id": "backlog", "version": "0.2.0", "enabled": True, "source": "marketplace"}],
    )

    result = runner.invoke(app, ["upgrade", "backlog"])

    assert result.exit_code == 0
    assert captured["reinstall"] is True
    assert "Upgraded" in result.stdout


def test_upgrade_without_module_name_upgrades_all_marketplace(monkeypatch, tmp_path: Path) -> None:
    installed: list[str] = []
    reinstall_flags: list[bool] = []

    def _install(module_id: str, options: InstallModuleOptions | None = None, **_kwargs):
        o = options or InstallModuleOptions()
        installed.append(module_id)
        reinstall_flags.append(o.reinstall)
        return tmp_path / module_id.split("/")[-1]

    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.install_module", _install)
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.get_modules_with_state",
        lambda: [
            {"id": "backlog", "version": "0.2.0", "enabled": True, "source": "marketplace"},
            {"id": "init", "version": "0.1.0", "enabled": True, "source": "builtin", "publisher": "nold-ai"},
        ],
    )

    result = runner.invoke(app, ["upgrade"])

    assert result.exit_code == 0
    assert installed == ["nold-ai/specfact-backlog"]
    assert reinstall_flags == [True]
    assert "Upgraded" in result.stdout


def test_upgrade_without_module_name_reports_one_line_per_module_with_versions(monkeypatch, tmp_path: Path) -> None:
    installed: list[str] = []

    def _install(module_id: str, options: InstallModuleOptions | None = None, **_kwargs):
        installed.append(module_id)
        module_dir = tmp_path / module_id.split("/")[-1]
        module_dir.mkdir(parents=True, exist_ok=True)
        new_version = "0.3.0" if module_id.endswith("backlog") else "0.5.0"
        (module_dir / "module-package.yaml").write_text(
            f"name: {module_id.split('/')[-1]}\nversion: '{new_version}'\ncommands: [{module_id.split('/')[-1]}]\n",
            encoding="utf-8",
        )
        return module_dir

    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.install_module", _install)
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.get_modules_with_state",
        lambda: [
            {"id": "nold-ai/specfact-backlog", "version": "0.2.0", "enabled": True, "source": "marketplace"},
            {"id": "nold-ai/specfact-project", "version": "0.4.0", "enabled": True, "source": "marketplace"},
        ],
    )

    result = runner.invoke(app, ["upgrade"])

    assert result.exit_code == 0
    assert installed == ["nold-ai/specfact-backlog", "nold-ai/specfact-project"]
    assert "Upgraded" in result.stdout
    assert "nold-ai/specfact-backlog: 0.2.0 -> 0.3.0" in result.stdout
    assert "nold-ai/specfact-project: 0.4.0 -> 0.5.0" in result.stdout


def test_upgrade_rejects_non_marketplace_source(monkeypatch) -> None:
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.get_modules_with_state",
        lambda: [{"id": "bundle-mapper", "version": "0.1.0", "enabled": True, "source": "custom"}],
    )

    result = runner.invoke(app, ["upgrade", "bundle-mapper"])

    assert result.exit_code == 1
    assert "marketplace modules" in result.stdout and "upgradeable" in result.stdout


def test_upgrade_rejects_multi_segment_module_id(monkeypatch, tmp_path: Path) -> None:
    """Malformed owner/repo/extra must not resolve via last-segment fallback to a different module."""
    installed: list[str] = []

    def _install(module_id: str, options: InstallModuleOptions | None = None, **_kwargs):
        installed.append(module_id)
        return tmp_path / module_id.split("/")[-1]

    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.install_module",
        _install,
    )
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.get_modules_with_state",
        lambda: [
            {"id": "nold-ai/specfact-backlog", "version": "0.2.0", "enabled": True, "source": "marketplace"},
        ],
    )

    result = runner.invoke(app, ["upgrade", "foo/bar/backlog"])

    assert result.exit_code == 1
    assert not installed
    assert "Invalid module id" in result.stdout
    assert "multi-segment" in result.stdout


def test_upgrade_row_for_target_does_not_match_last_segment_for_multi_slash_ids() -> None:
    from specfact_cli.modules.module_registry.src.commands import _upgrade_row_for_target

    by_id = {"nold-ai/specfact-backlog": {"version": "1", "source": "marketplace"}}
    assert _upgrade_row_for_target("foo/bar/backlog", by_id) == {}


def test_full_marketplace_module_id_for_install_rejects_multi_segment_path() -> None:
    from specfact_cli.modules.module_registry.src.commands import _full_marketplace_module_id_for_install

    with pytest.raises(ValueError, match="multi-segment"):
        _full_marketplace_module_id_for_install("foo/bar/backlog")


def test_enable_command_updates_state_with_dependency_checks(monkeypatch) -> None:
    captured = {"enable_ids": None, "disable_ids": None, "force": None}

    def _apply(*, enable_ids, disable_ids, force):
        captured["enable_ids"] = enable_ids
        captured["disable_ids"] = disable_ids
        captured["force"] = force
        return []

    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.apply_module_state_update", _apply)

    result = runner.invoke(app, ["enable", "backlog"])

    assert result.exit_code == 0
    assert captured["enable_ids"] == ["backlog"]
    assert captured["disable_ids"] == []
    assert captured["force"] is False
    assert "Enabled" in result.stdout


def test_disable_command_respects_force_cascade(monkeypatch) -> None:
    captured = {"enable_ids": None, "disable_ids": None, "force": None}

    def _apply(*, enable_ids, disable_ids, force):
        captured["enable_ids"] = enable_ids
        captured["disable_ids"] = disable_ids
        captured["force"] = force
        return []

    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.apply_module_state_update", _apply)

    result = runner.invoke(app, ["disable", "sync", "--force"])

    assert result.exit_code == 0
    assert captured["enable_ids"] == []
    assert captured["disable_ids"] == ["sync"]
    assert captured["force"] is True
    assert "Disabled" in result.stdout


def test_enable_command_interactive_mode_selection(monkeypatch) -> None:
    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.is_non_interactive", lambda: False)
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.get_modules_with_state",
        lambda: [
            {
                "id": "backlog",
                "version": "0.2.0",
                "enabled": False,
                "source": "marketplace",
                "publisher": "community-dev",
            }
        ],
    )
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.select_module_ids_interactive",
        lambda *_args, **_kwargs: ["backlog"],
    )
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.ensure_publisher_trusted",
        lambda *_args, **_kwargs: None,
    )

    captured = {"enable_ids": None}

    def _apply(*, enable_ids, disable_ids, force):
        captured["enable_ids"] = enable_ids
        return []

    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.apply_module_state_update", _apply)

    result = runner.invoke(app, ["enable"])

    assert result.exit_code == 0
    assert captured["enable_ids"] == ["backlog"]


def test_disable_command_non_interactive_requires_module_id(monkeypatch) -> None:
    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.is_non_interactive", lambda: True)

    result = runner.invoke(app, ["disable"])

    assert result.exit_code == 1
    assert "Non-interactive mode requires explicit module id value" in result.stdout


def test_module_init_bootstraps_user_modules(monkeypatch) -> None:
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.sync_bundled_modules_to_user_root",
        lambda **_kwargs: 2,
    )

    result = runner.invoke(app, ["init"])

    assert result.exit_code == 0
    assert "Seeded 2 module(s) into" in result.stdout
    assert str(USER_MODULES_ROOT) in result.stdout or "user-modules" in result.stdout


def test_module_init_project_scope_defaults_to_cwd_repo(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    captured: dict[str, Path | None] = {"target_root": None}

    def _sync(target_root=None, **_kwargs):
        captured["target_root"] = target_root
        return 1

    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.sync_bundled_modules_to_user_root", _sync)

    result = runner.invoke(app, ["init", "--scope", "project"])

    assert result.exit_code == 0
    assert captured["target_root"] == tmp_path / ".specfact" / "modules"
    assert "Seeded 1 module(s) into" in result.stdout
    assert str(tmp_path / ".specfact" / "modules") in result.stdout


def test_module_init_project_scope_supports_explicit_repo(monkeypatch, tmp_path: Path) -> None:
    explicit_repo = tmp_path / "customer-a"
    explicit_repo.mkdir(parents=True)
    captured: dict[str, Path | None] = {"target_root": None}

    def _sync(target_root=None, **_kwargs):
        captured["target_root"] = target_root
        return 1

    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.sync_bundled_modules_to_user_root", _sync)

    result = runner.invoke(app, ["init", "--scope", "project", "--repo", str(explicit_repo)])

    assert result.exit_code == 0
    assert captured["target_root"] == explicit_repo / ".specfact" / "modules"
    compact_output = result.stdout.replace("\n", "")
    assert "Seeded 1 module(s) into" in compact_output
    assert str(explicit_repo / ".specfact" / "modules").replace("\n", "") in compact_output

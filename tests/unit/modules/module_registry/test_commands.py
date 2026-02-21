"""Tests for module marketplace CLI commands."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from specfact_cli.modules.module_registry.src.commands import app


runner = CliRunner()


def test_install_command_integration(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.discover_all_modules", list)
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.install_module",
        lambda module_id, version=None: tmp_path / module_id.split("/")[-1],
    )

    result = runner.invoke(app, ["install", "specfact/backlog"])

    assert result.exit_code == 0
    assert "Installed" in result.stdout
    assert "specfact/backlog" in result.stdout


def test_install_command_accepts_bare_module_name(monkeypatch, tmp_path: Path) -> None:
    captured: dict[str, str | None] = {"module_id": None}

    def _install(module_id: str, version=None):
        captured["module_id"] = module_id
        return tmp_path / module_id.split("/")[-1]

    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.discover_all_modules", list)
    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.install_module", _install)

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

    def _install(module_id: str, version=None):
        called["install"] = True
        return tmp_path / module_id.split("/")[-1]

    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.discover_all_modules", lambda: [_Entry()])
    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.install_module", _install)

    result = runner.invoke(app, ["install", "bundle-mapper"])

    assert result.exit_code == 0
    assert called["install"] is False
    assert "already available" in result.stdout


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
        "specfact_cli.modules.module_registry.src.commands.fetch_registry_index",
        lambda: {
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

    result = runner.invoke(app, ["search", "backlog"])

    assert result.exit_code == 0
    assert "Module Search Results" in result.stdout
    assert "specfact/backlog" in result.stdout
    assert "marketplace" in result.stdout
    assert "specfact/policy" not in result.stdout


def test_search_command_finds_installed_module_when_not_in_registry(monkeypatch) -> None:
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.fetch_registry_index", lambda: {"modules": []}
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
        "specfact_cli.modules.module_registry.src.commands.fetch_registry_index", lambda: {"modules": []}
    )
    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.discover_all_modules", list)

    result = runner.invoke(app, ["search", "does-not-exist"])

    assert result.exit_code == 0
    assert "No modules found for query 'does-not-exist'" in result.stdout


def test_search_command_sorts_results_alphabetically(monkeypatch) -> None:
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.fetch_registry_index",
        lambda: {
            "schema_version": "1.0.0",
            "modules": [
                {"id": "specfact/zeta", "description": "Zeta module", "latest_version": "0.1.0", "tags": ["bundle"]},
                {"id": "specfact/alpha", "description": "Alpha module", "latest_version": "0.1.0", "tags": ["bundle"]},
            ],
        },
    )
    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.discover_all_modules", list)

    result = runner.invoke(app, ["search", "module"])

    assert result.exit_code == 0
    assert result.stdout.index("specfact/alpha") < result.stdout.index("specfact/zeta")


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

    def _install(module_id: str, version=None, reinstall: bool = False):
        captured["reinstall"] = reinstall
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

    def _install(module_id: str, version=None, reinstall: bool = False):
        installed.append(module_id)
        reinstall_flags.append(reinstall)
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
    assert installed == ["specfact/backlog"]
    assert reinstall_flags == [True]
    assert "Upgraded" in result.stdout


def test_upgrade_rejects_non_marketplace_source(monkeypatch) -> None:
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.get_modules_with_state",
        lambda: [{"id": "bundle-mapper", "version": "0.1.0", "enabled": True, "source": "custom"}],
    )

    result = runner.invoke(app, ["upgrade", "bundle-mapper"])

    assert result.exit_code == 1
    assert "marketplace modules" in result.stdout and "upgradeable" in result.stdout


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

"""Tests for first-run bundle selection in specfact init (Phase 3)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from specfact_cli.modules.init.src import first_run_selection as frs
from specfact_cli.modules.init.src.commands import app


runner = CliRunner()


def _telemetry_track_context():
    return patch(
        "specfact_cli.modules.init.src.commands.telemetry",
        MagicMock(
            track_command=MagicMock(return_value=MagicMock(__enter__=lambda s: None, __exit__=lambda s, *a: None))
        ),
    )


# --- Profile resolution ---


def test_profile_solo_developer_resolves_to_codebase_and_code_review() -> None:
    bundles = frs.resolve_profile_bundles("solo-developer")
    assert bundles == ["specfact-codebase", "specfact-code-review"]


def test_profile_enterprise_full_stack_resolves_to_all_five_bundles() -> None:
    bundles = frs.resolve_profile_bundles("enterprise-full-stack")
    assert set(bundles) == {
        "specfact-project",
        "specfact-backlog",
        "specfact-codebase",
        "specfact-spec",
        "specfact-govern",
    }
    assert len(bundles) == 5


def test_profile_nonexistent_raises_with_valid_list() -> None:
    with pytest.raises(ValueError) as exc_info:
        frs.resolve_profile_bundles("nonexistent")
    msg = str(exc_info.value).lower()
    assert "nonexistent" in msg or "unknown" in msg or "invalid" in msg
    assert "solo-developer" in msg or "valid" in msg


# --- --install parsing ---


def test_install_backlog_codebase_resolves_to_two_bundles() -> None:
    bundles = frs.resolve_install_bundles("backlog,codebase")
    assert set(bundles) == {"specfact-backlog", "specfact-codebase"}
    assert len(bundles) == 2


def test_install_all_resolves_to_all_five_bundles() -> None:
    bundles = frs.resolve_install_bundles("all")
    assert set(bundles) == {
        "specfact-project",
        "specfact-backlog",
        "specfact-codebase",
        "specfact-spec",
        "specfact-govern",
    }
    assert len(bundles) == 5


def test_install_unknown_bundle_raises() -> None:
    with pytest.raises(ValueError) as exc_info:
        frs.resolve_install_bundles("widgets")
    msg = str(exc_info.value).lower()
    assert "widgets" in msg or "unknown" in msg
    assert "valid" in msg or "bundle" in msg


# --- is_first_run ---


def test_is_first_run_true_when_no_category_bundle_installed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def _discover(_builtin=None, user_root=None, **_kwargs):
        from specfact_cli.models.module_package import ModulePackageMetadata
        from specfact_cli.registry.module_discovery import DiscoveredModule

        meta_core = ModulePackageMetadata(name="init", version="0.1.0", commands=["init"], category="core")
        return [DiscoveredModule(tmp_path / "init", meta_core, "builtin")]

    monkeypatch.setattr("specfact_cli.registry.module_discovery.discover_all_modules", _discover)
    assert frs.is_first_run(user_root=tmp_path) is True


def test_is_first_run_false_when_category_bundle_installed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def _discover(_builtin=None, user_root=None, **_kwargs):
        from specfact_cli.models.module_package import ModulePackageMetadata
        from specfact_cli.registry.module_discovery import DiscoveredModule

        meta_core = ModulePackageMetadata(name="init", version="0.1.0", commands=["init"], category="core")
        meta_code = ModulePackageMetadata(
            name="analyze", version="0.1.0", commands=["analyze"], category="codebase", bundle="specfact-codebase"
        )
        return [
            DiscoveredModule(tmp_path / "init", meta_core, "builtin"),
            DiscoveredModule(tmp_path / "analyze", meta_code, "user"),
        ]

    monkeypatch.setattr("specfact_cli.registry.module_discovery.discover_all_modules", _discover)
    assert frs.is_first_run(user_root=tmp_path) is False


def test_is_first_run_false_when_project_scoped_category_bundle_installed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def _discover(_builtin=None, user_root=None, **_kwargs):
        from specfact_cli.models.module_package import ModulePackageMetadata
        from specfact_cli.registry.module_discovery import DiscoveredModule

        meta_project = ModulePackageMetadata(
            name="analyze", version="0.1.0", commands=["analyze"], category="codebase", bundle="specfact-codebase"
        )
        return [DiscoveredModule(tmp_path / "analyze", meta_project, "project")]

    monkeypatch.setattr("specfact_cli.registry.module_discovery.discover_all_modules", _discover)
    assert frs.is_first_run(user_root=tmp_path) is False


# --- CLI: specfact init --profile (mock installer) ---


def test_init_profile_solo_developer_calls_installer_with_codebase_and_code_review(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    install_calls: list[list[str]] = []

    def _fake_install_bundles(bundle_ids: list[str], install_root: Path, **kwargs: object) -> None:
        install_calls.append(list(bundle_ids))

    monkeypatch.setattr("specfact_cli.modules.init.src.commands.install_bundles_for_init", _fake_install_bundles)
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.is_first_run", lambda **_: True)
    monkeypatch.setattr(
        "specfact_cli.modules.init.src.commands.get_discovered_modules_for_state",
        lambda **_: [{"id": "init", "enabled": True}],
    )
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.write_modules_state", lambda _: None)
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.run_discovery_and_write_cache", lambda _: None)
    monkeypatch.setattr(
        "specfact_cli.modules.init.src.commands.detect_env_manager", lambda _: MagicMock(manager=MagicMock())
    )
    with _telemetry_track_context():
        result = runner.invoke(
            app,
            ["--repo", str(tmp_path), "--profile", "solo-developer"],
            catch_exceptions=False,
        )
    assert result.exit_code == 0, result.output
    assert len(install_calls) == 1
    assert install_calls[0] == ["specfact-codebase", "specfact-code-review"]


def test_init_profile_enables_profile_modules_and_uses_repo_for_discovery(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    captured: dict[str, object] = {}

    def _fake_get_discovered_modules_for_state(**kwargs: object) -> list[dict[str, object]]:
        captured.update(kwargs)
        return [{"id": "nold-ai/specfact-codebase", "enabled": True}]

    monkeypatch.setattr("specfact_cli.modules.init.src.commands.install_bundles_for_init", lambda *_a, **_k: None)
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.is_first_run", lambda **_: True)
    monkeypatch.setattr(
        "specfact_cli.modules.init.src.commands.get_discovered_modules_for_state",
        _fake_get_discovered_modules_for_state,
    )
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.write_modules_state", lambda _: None)
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.run_discovery_and_write_cache", lambda _: None)
    monkeypatch.setattr(
        "specfact_cli.modules.init.src.commands.detect_env_manager", lambda _: MagicMock(manager=MagicMock())
    )

    with _telemetry_track_context():
        result = runner.invoke(
            app,
            ["--repo", str(tmp_path), "--profile", "solo-developer"],
            catch_exceptions=False,
        )

    assert result.exit_code == 0, result.output
    assert captured["base_path"] == tmp_path.resolve()
    enable_ids = captured["enable_ids"]
    assert isinstance(enable_ids, list)
    assert set(enable_ids) == {"nold-ai/specfact-codebase", "nold-ai/specfact-code-review"}
    assert captured["preserve_existing"] is True


def test_init_profile_enterprise_full_stack_calls_installer_with_all_five(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    install_calls: list[list[str]] = []

    def _fake_install_bundles(bundle_ids: list[str], install_root: Path, **kwargs: object) -> None:
        install_calls.append(list(bundle_ids))

    monkeypatch.setattr("specfact_cli.modules.init.src.commands.install_bundles_for_init", _fake_install_bundles)
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.is_first_run", lambda **_: True)
    monkeypatch.setattr(
        "specfact_cli.modules.init.src.commands.get_discovered_modules_for_state",
        lambda **_: [{"id": "init", "enabled": True}],
    )
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.write_modules_state", lambda _: None)
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.run_discovery_and_write_cache", lambda _: None)
    monkeypatch.setattr(
        "specfact_cli.modules.init.src.commands.detect_env_manager", lambda _: MagicMock(manager=MagicMock())
    )
    with _telemetry_track_context():
        result = runner.invoke(
            app,
            ["--repo", str(tmp_path), "--profile", "enterprise-full-stack"],
            catch_exceptions=False,
        )
    assert result.exit_code == 0, result.output
    assert len(install_calls) == 1
    assert set(install_calls[0]) == {
        "specfact-project",
        "specfact-backlog",
        "specfact-codebase",
        "specfact-spec",
        "specfact-govern",
    }
    assert len(install_calls[0]) == 5


def test_init_profile_nonexistent_exits_nonzero_and_lists_valid_profiles(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.get_discovered_modules_for_state", lambda **_: [])
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.write_modules_state", lambda _: None)
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.run_discovery_and_write_cache", lambda _: None)
    with _telemetry_track_context():
        result = runner.invoke(
            app,
            ["--repo", str(tmp_path), "--profile", "nonexistent"],
            catch_exceptions=False,
        )
    assert result.exit_code != 0
    assert (
        "nonexistent" in result.output.lower()
        or "invalid" in result.output.lower()
        or "unknown" in result.output.lower()
    )
    assert "solo-developer" in result.output or "valid" in result.output.lower()


def test_init_install_backlog_codebase_calls_installer_with_two_bundles(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    install_calls: list[list[str]] = []

    def _fake_install_bundles(bundle_ids: list[str], install_root: Path, **kwargs: object) -> None:
        install_calls.append(list(bundle_ids))

    monkeypatch.setattr("specfact_cli.modules.init.src.commands.install_bundles_for_init", _fake_install_bundles)
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.is_first_run", lambda **_: True)
    monkeypatch.setattr(
        "specfact_cli.modules.init.src.commands.get_discovered_modules_for_state",
        lambda **_: [{"id": "init", "enabled": True}],
    )
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.write_modules_state", lambda _: None)
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.run_discovery_and_write_cache", lambda _: None)
    monkeypatch.setattr(
        "specfact_cli.modules.init.src.commands.detect_env_manager", lambda _: MagicMock(manager=MagicMock())
    )
    with _telemetry_track_context():
        result = runner.invoke(
            app,
            ["--repo", str(tmp_path), "--install", "backlog,codebase"],
            catch_exceptions=False,
        )
    assert result.exit_code == 0, result.output
    assert len(install_calls) == 1
    assert set(install_calls[0]) == {"specfact-backlog", "specfact-codebase"}


def test_init_install_all_calls_installer_with_five_bundles(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    install_calls: list[list[str]] = []

    def _fake_install_bundles(bundle_ids: list[str], install_root: Path, **kwargs: object) -> None:
        install_calls.append(list(bundle_ids))

    monkeypatch.setattr("specfact_cli.modules.init.src.commands.install_bundles_for_init", _fake_install_bundles)
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.is_first_run", lambda **_: True)
    monkeypatch.setattr(
        "specfact_cli.modules.init.src.commands.get_discovered_modules_for_state",
        lambda **_: [{"id": "init", "enabled": True}],
    )
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.write_modules_state", lambda _: None)
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.run_discovery_and_write_cache", lambda _: None)
    monkeypatch.setattr(
        "specfact_cli.modules.init.src.commands.detect_env_manager", lambda _: MagicMock(manager=MagicMock())
    )
    with _telemetry_track_context():
        result = runner.invoke(
            app,
            ["--repo", str(tmp_path), "--install", "all"],
            catch_exceptions=False,
        )
    assert result.exit_code == 0, result.output
    assert len(install_calls) == 1
    assert len(install_calls[0]) == 5
    assert set(install_calls[0]) == {
        "specfact-project",
        "specfact-backlog",
        "specfact-codebase",
        "specfact-spec",
        "specfact-govern",
    }


def test_init_install_widgets_exits_nonzero(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["--repo", str(tmp_path), "--install", "widgets"],
        catch_exceptions=False,
    )
    assert result.exit_code != 0
    assert (
        "widgets" in result.output.lower() or "unknown" in result.output.lower() or "invalid" in result.output.lower()
    )


def test_init_second_run_skips_first_run_flow(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    install_calls: list[list[str]] = []

    def _fake_install_bundles(bundle_ids: list[str], install_root: Path, **kwargs: object) -> None:
        install_calls.append(list(bundle_ids))

    monkeypatch.setattr(
        "specfact_cli.modules.init.src.first_run_selection.install_bundles_for_init", _fake_install_bundles
    )
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.is_first_run", lambda **_: False)
    modules_list = [{"id": "init", "enabled": True}, {"id": "analyze", "enabled": True}]
    monkeypatch.setattr(
        "specfact_cli.modules.init.src.commands.get_discovered_modules_for_state",
        lambda **_: modules_list,
    )
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.write_modules_state", lambda _: None)
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.run_discovery_and_write_cache", lambda _: None)
    monkeypatch.setattr(
        "specfact_cli.modules.init.src.commands.detect_env_manager", lambda _: MagicMock(manager=MagicMock())
    )
    with _telemetry_track_context():
        result = runner.invoke(
            app,
            ["--repo", str(tmp_path)],
            catch_exceptions=False,
        )
    assert result.exit_code == 0, result.output
    assert len(install_calls) == 0


def test_init_first_run_interactive_with_selection_calls_installer(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    install_calls: list[list[str]] = []

    def _fake_install(bundle_ids: list[str], install_root: Path, **kwargs: object) -> None:
        install_calls.append(list(bundle_ids))

    monkeypatch.setattr("specfact_cli.modules.init.src.first_run_selection.install_bundles_for_init", _fake_install)
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.is_first_run", lambda **_: True)
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.is_non_interactive", lambda: False)
    monkeypatch.setattr(
        "specfact_cli.modules.init.src.commands._interactive_first_run_bundle_selection",
        lambda: ["specfact-codebase"],
    )
    monkeypatch.setattr(
        "specfact_cli.modules.init.src.commands.get_discovered_modules_for_state",
        lambda **_: [{"id": "init", "enabled": True}],
    )
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.write_modules_state", lambda _: None)
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.run_discovery_and_write_cache", lambda _: None)
    monkeypatch.setattr(
        "specfact_cli.modules.init.src.commands.detect_env_manager", lambda _: MagicMock(manager=MagicMock())
    )
    with _telemetry_track_context():
        result = runner.invoke(app, ["--repo", str(tmp_path)], catch_exceptions=False)
    assert result.exit_code == 0, result.output
    assert len(install_calls) == 1
    assert install_calls[0] == ["specfact-codebase"]


def test_init_first_run_interactive_no_selection_shows_tip(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    install_calls: list[list[str]] = []

    def _fake_install(bundle_ids: list[str], install_root: Path, **kwargs: object) -> None:
        install_calls.append(list(bundle_ids))

    monkeypatch.setattr("specfact_cli.modules.init.src.first_run_selection.install_bundles_for_init", _fake_install)
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.is_first_run", lambda **_: True)
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.is_non_interactive", lambda: False)
    monkeypatch.setattr(
        "specfact_cli.modules.init.src.commands._interactive_first_run_bundle_selection",
        list,
    )
    monkeypatch.setattr(
        "specfact_cli.modules.init.src.commands.get_discovered_modules_for_state",
        lambda **_: [{"id": "init", "enabled": True}],
    )
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.write_modules_state", lambda _: None)
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.run_discovery_and_write_cache", lambda _: None)
    monkeypatch.setattr(
        "specfact_cli.modules.init.src.commands.detect_env_manager", lambda _: MagicMock(manager=MagicMock())
    )
    with _telemetry_track_context():
        result = runner.invoke(app, ["--repo", str(tmp_path)], catch_exceptions=False)
    assert result.exit_code == 0, result.output
    assert len(install_calls) == 0
    assert "module install" in result.output or "Tip" in result.output


def test_spec_bundle_install_includes_project_dep(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    installed_ids: list[str] = []

    def _record_marketplace(module_id: str, options: object | None = None, **_kwargs: object) -> Path:
        installed_ids.append(module_id)
        return tmp_path / module_id.split("/")[1]

    monkeypatch.setattr(
        "specfact_cli.registry.module_installer.install_module",
        _record_marketplace,
    )
    frs.install_bundles_for_init(["specfact-spec"], install_root=tmp_path, show_progress=False)
    assert "nold-ai/specfact-project" in installed_ids, "spec bundle depends on project marketplace module"
    assert "nold-ai/specfact-spec" in installed_ids

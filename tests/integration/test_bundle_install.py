"""Integration tests for bundle install and legacy compatibility."""

from __future__ import annotations

import importlib
import io
import warnings
from collections.abc import Callable
from pathlib import Path

import pytest
from rich.console import Console
from typer.testing import CliRunner

from scripts.runtime_discovery_smoke import _resolve_modules_repo
from specfact_cli.modules.module_registry.src.commands import _install_impl, app
from specfact_cli.registry import module_lifecycle
from specfact_cli.registry.module_installer import InstallModuleOptions, install_module
from specfact_cli.registry.official_module_cutoff import frozen_archive


runner = CliRunner()


@pytest.fixture
def cutoff_archive() -> Callable[[str], Path]:
    modules_repo = _resolve_modules_repo(None)

    def archive_for(module_id: str) -> Path:
        version, _ = frozen_archive(module_id, None)
        name = module_id.split("/", 1)[1]
        return modules_repo / "registry" / "modules" / f"{name}-{version}.tar.gz"

    return archive_for


def _stub_install_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("specfact_cli.registry.module_installer.resolve_dependencies", lambda *_a, **_k: None)
    monkeypatch.setattr(
        "specfact_cli.registry.module_installer.install_resolved_pip_requirements", lambda *_a, **_k: None
    )
    monkeypatch.setattr("specfact_cli.registry.module_installer.ensure_publisher_trusted", lambda *_a, **_k: None)
    monkeypatch.setattr("specfact_cli.registry.module_installer.assert_module_allowed", lambda *_a, **_k: None)
    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.discover_all_modules", list)


def test_module_install_official_bundle_reports_verification(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, cutoff_archive: Callable[[str], Path]
) -> None:
    _stub_install_runtime(monkeypatch)
    monkeypatch.setattr(
        "specfact_cli.registry.module_installer.download_module", lambda module_id, **_kwargs: cutoff_archive(module_id)
    )

    result = runner.invoke(
        app,
        [
            "install",
            "nold-ai/specfact-codebase",
            "--source",
            "marketplace",
            "--scope",
            "project",
            "--repo",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    assert "Verified: official (nold-ai)" in result.stdout


def test_installing_spec_bundle_auto_installs_project_dependency(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, cutoff_archive: Callable[[str], Path]
) -> None:
    _stub_install_runtime(monkeypatch)
    monkeypatch.setattr(
        "specfact_cli.registry.module_installer.download_module", lambda module_id, **_kwargs: cutoff_archive(module_id)
    )
    result = runner.invoke(
        app,
        ["install", "nold-ai/specfact-spec", "--source", "marketplace", "--scope", "project", "--repo", str(tmp_path)],
    )

    assert result.exit_code == 0
    install_root = tmp_path / ".specfact" / "modules"
    assert (install_root / "specfact-project" / "module-package.yaml").exists()
    assert (install_root / "specfact-spec" / "module-package.yaml").exists()


def test_installing_spec_bundle_skips_dependency_when_already_present(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    cutoff_archive: Callable[[str], Path],
) -> None:
    _stub_install_runtime(monkeypatch)
    calls: list[str] = []

    def _download(module_id: str, version: str | None = None) -> Path:
        _ = version
        calls.append(module_id)
        return cutoff_archive(module_id)

    monkeypatch.setattr("specfact_cli.registry.module_installer.download_module", _download)
    install_root = tmp_path / ".specfact" / "modules"
    install_module("nold-ai/specfact-project", InstallModuleOptions(install_root=install_root, skip_deps=True))
    calls.clear()

    _install_impl(
        ["nold-ai/specfact-spec"],
        source="marketplace",
        scope="project",
        repo=tmp_path,
    )

    out = capsys.readouterr().out
    assert "Installed nold-ai/specfact-spec ->" in out
    assert "Verified: official (nold-ai)" in out
    assert calls == ["nold-ai/specfact-spec"]


def test_bundle_install_refreshes_stale_loaded_module_consoles(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, cutoff_archive: Callable[[str], Path]
) -> None:
    _stub_install_runtime(monkeypatch)
    monkeypatch.setattr(
        "specfact_cli.registry.module_installer.download_module", lambda module_id, **_kwargs: cutoff_archive(module_id)
    )
    closed_stream = io.StringIO()
    closed_stream.close()
    stale_console = Console(file=closed_stream)
    monkeypatch.setattr(module_lifecycle, "console", stale_console, raising=False)

    result = runner.invoke(
        app,
        ["install", "nold-ai/specfact-spec", "--source", "marketplace", "--scope", "project", "--repo", str(tmp_path)],
    )

    assert result.exit_code == 0
    assert result.exception is None
    assert vars(module_lifecycle).get("console") is not stale_console
    assert "Installed nold-ai/specfact-spec ->" in result.stdout


def test_module_list_shows_official_badge_for_installed_bundle(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.get_modules_with_state",
        lambda: [
            {
                "id": "nold-ai/specfact-codebase",
                "version": "0.39.0",
                "enabled": True,
                "source": "marketplace",
                "official": True,
                "publisher": "nold-ai",
            }
        ],
    )
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "[official]" in result.stdout


def test_deprecated_flat_validate_import_still_works_and_warns() -> None:
    pytest.importorskip("specfact_codebase.validate")
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        module = importlib.import_module("specfact_codebase.validate")
        _ = module.app
    assert module is not None
    if captured:
        assert any(issubclass(item.category, DeprecationWarning) for item in captured)

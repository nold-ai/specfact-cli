"""Integration tests for bundle install and legacy compatibility."""

from __future__ import annotations

import importlib
import tarfile
import warnings
from pathlib import Path

import pytest
from typer.testing import CliRunner

from specfact_cli.modules.module_registry.src.commands import app
from specfact_cli.registry.module_installer import REGISTRY_ID_FILE


runner = CliRunner()


def _create_module_tarball(
    tmp_path: Path,
    module_name: str,
    *,
    bundle_dependencies: list[str] | None = None,
    version: str = "0.39.0",
) -> Path:
    package_root = tmp_path / f"{module_name}-pkg"
    module_dir = package_root / module_name
    module_dir.mkdir(parents=True, exist_ok=True)
    deps_yaml = ""
    if bundle_dependencies:
        deps_yaml = "bundle_dependencies:\n" + "".join(f"  - {dep}\n" for dep in bundle_dependencies)
    (module_dir / "module-package.yaml").write_text(
        "\n".join(
            [
                f"name: {module_name}",
                f"version: '{version}'",
                f"commands: [{module_name.replace('-', '_')}]",
                'core_compatibility: ">=0.1.0,<1.0.0"',
                deps_yaml.rstrip("\n"),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (module_dir / "src").mkdir(parents=True, exist_ok=True)
    tarball = tmp_path / f"{module_name}.tar.gz"
    with tarfile.open(tarball, "w:gz") as archive:
        archive.add(module_dir, arcname=module_name)
    return tarball


def _stub_install_runtime(monkeypatch) -> None:
    monkeypatch.setattr("specfact_cli.registry.module_installer.resolve_dependencies", lambda *_a, **_k: None)
    monkeypatch.setattr(
        "specfact_cli.registry.module_installer.install_resolved_pip_requirements", lambda *_a, **_k: None
    )
    monkeypatch.setattr("specfact_cli.registry.module_installer.verify_module_artifact", lambda *_a, **_k: True)
    monkeypatch.setattr("specfact_cli.registry.module_installer.ensure_publisher_trusted", lambda *_a, **_k: None)
    monkeypatch.setattr("specfact_cli.registry.module_installer.assert_module_allowed", lambda *_a, **_k: None)
    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.discover_all_modules", list)


def test_module_install_official_bundle_reports_verification(monkeypatch, tmp_path: Path) -> None:
    _stub_install_runtime(monkeypatch)
    tarball = _create_module_tarball(tmp_path, "specfact-codebase")
    monkeypatch.setattr("specfact_cli.registry.module_installer.download_module", lambda *_a, **_k: tarball)

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


def test_installing_spec_bundle_auto_installs_project_dependency(monkeypatch, tmp_path: Path) -> None:
    _stub_install_runtime(monkeypatch)
    tar_project = _create_module_tarball(tmp_path, "specfact-project")
    tar_spec = _create_module_tarball(
        tmp_path,
        "specfact-spec",
        bundle_dependencies=["nold-ai/specfact-project"],
    )

    def _download(module_id: str, version: str | None = None) -> Path:
        _ = version
        if module_id == "nold-ai/specfact-project":
            return tar_project
        if module_id == "nold-ai/specfact-spec":
            return tar_spec
        raise ValueError(f"unexpected module id: {module_id}")

    monkeypatch.setattr("specfact_cli.registry.module_installer.download_module", _download)
    result = runner.invoke(
        app,
        ["install", "nold-ai/specfact-spec", "--source", "marketplace", "--scope", "project", "--repo", str(tmp_path)],
    )

    assert result.exit_code == 0
    install_root = tmp_path / ".specfact" / "modules"
    assert (install_root / "specfact-project" / "module-package.yaml").exists()
    assert (install_root / "specfact-spec" / "module-package.yaml").exists()


def test_installing_spec_bundle_skips_dependency_when_already_present(monkeypatch, tmp_path: Path) -> None:
    _stub_install_runtime(monkeypatch)
    tar_spec = _create_module_tarball(
        tmp_path,
        "specfact-spec",
        bundle_dependencies=["nold-ai/specfact-project"],
    )
    calls: list[str] = []

    def _download(module_id: str, version: str | None = None) -> Path:
        _ = version
        calls.append(module_id)
        if module_id == "nold-ai/specfact-spec":
            return tar_spec
        raise ValueError(f"unexpected module id: {module_id}")

    monkeypatch.setattr("specfact_cli.registry.module_installer.download_module", _download)
    install_root = tmp_path / ".specfact" / "modules"
    dep_dir = install_root / "specfact-project"
    dep_dir.mkdir(parents=True, exist_ok=True)
    (dep_dir / "module-package.yaml").write_text("name: specfact-project\nversion: '0.39.0'\ncommands: [project]\n")
    (dep_dir / REGISTRY_ID_FILE).write_text("nold-ai/specfact-project", encoding="utf-8")

    result = runner.invoke(
        app,
        ["install", "nold-ai/specfact-spec", "--source", "marketplace", "--scope", "project", "--repo", str(tmp_path)],
    )

    assert result.exit_code == 0
    assert calls == ["nold-ai/specfact-spec"]


def test_module_list_shows_official_badge_for_installed_bundle(monkeypatch) -> None:
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

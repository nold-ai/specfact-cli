"""Tests for bundle dependency auto-install in marketplace installer."""

from __future__ import annotations

import tarfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from specfact_cli.registry.module_installer import install_module


def _create_module_tarball(
    tmp_path: Path,
    module_name: str,
    *,
    bundle_dependencies: list[str] | None = None,
    version: str = "0.1.0",
) -> Path:
    package_root = tmp_path / f"{module_name}-pkg"
    module_dir = package_root / module_name
    module_dir.mkdir(parents=True, exist_ok=True)

    deps_yaml = ""
    if bundle_dependencies:
        deps_yaml = "bundle_dependencies:\n" + "".join(f"  - {dep}\n" for dep in bundle_dependencies)

    (module_dir / "module-package.yaml").write_text(
        "name: {name}\nversion: '{version}'\ncommands: [{cmd}]\ncore_compatibility: \">=0.1.0,<1.0.0\"\n{deps}".format(
            name=module_name,
            version=version,
            cmd=module_name.replace("-", "_"),
            deps=deps_yaml,
        ),
        encoding="utf-8",
    )
    (module_dir / "src").mkdir(parents=True, exist_ok=True)

    tarball = tmp_path / f"{module_name}.tar.gz"
    with tarfile.open(tarball, "w:gz") as archive:
        archive.add(module_dir, arcname=module_name)
    return tarball


def _stub_integrity_and_deps(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("specfact_cli.registry.module_installer.resolve_dependencies", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        "specfact_cli.registry.module_installer.install_resolved_pip_requirements", lambda *_args, **_kwargs: None
    )
    monkeypatch.setattr("specfact_cli.registry.module_installer.verify_module_artifact", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(
        "specfact_cli.registry.module_installer.ensure_publisher_trusted", lambda *_args, **_kwargs: None
    )
    monkeypatch.setattr("specfact_cli.registry.module_installer.assert_module_allowed", lambda *_args, **_kwargs: None)


def test_installing_spec_bundle_installs_project_dependency_first(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _stub_integrity_and_deps(monkeypatch)
    tar_project = _create_module_tarball(tmp_path, "specfact-project")
    tar_spec = _create_module_tarball(
        tmp_path,
        "specfact-spec",
        bundle_dependencies=["nold-ai/specfact-project"],
    )
    calls: list[str] = []

    def _download(module_id: str, version: str | None = None) -> Path:
        _ = version
        calls.append(module_id)
        if module_id == "nold-ai/specfact-project":
            return tar_project
        if module_id == "nold-ai/specfact-spec":
            return tar_spec
        raise ValueError(f"unexpected module id: {module_id}")

    monkeypatch.setattr("specfact_cli.registry.module_installer.download_module", _download)
    install_root = tmp_path / "modules"

    install_module("nold-ai/specfact-spec", install_root=install_root)

    assert calls[:2] == ["nold-ai/specfact-spec", "nold-ai/specfact-project"]
    assert (install_root / "specfact-project" / "module-package.yaml").exists()
    assert (install_root / "specfact-spec" / "module-package.yaml").exists()


def test_installing_govern_bundle_installs_project_dependency_first(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _stub_integrity_and_deps(monkeypatch)
    tar_project = _create_module_tarball(tmp_path, "specfact-project")
    tar_govern = _create_module_tarball(
        tmp_path,
        "specfact-govern",
        bundle_dependencies=["nold-ai/specfact-project"],
    )
    calls: list[str] = []

    def _download(module_id: str, version: str | None = None) -> Path:
        _ = version
        calls.append(module_id)
        if module_id == "nold-ai/specfact-project":
            return tar_project
        if module_id == "nold-ai/specfact-govern":
            return tar_govern
        raise ValueError(f"unexpected module id: {module_id}")

    monkeypatch.setattr("specfact_cli.registry.module_installer.download_module", _download)
    install_root = tmp_path / "modules"

    install_module("nold-ai/specfact-govern", install_root=install_root)

    assert calls[:2] == ["nold-ai/specfact-govern", "nold-ai/specfact-project"]
    assert (install_root / "specfact-project" / "module-package.yaml").exists()
    assert (install_root / "specfact-govern" / "module-package.yaml").exists()


def test_dependency_install_is_skipped_when_already_installed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _stub_integrity_and_deps(monkeypatch)
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
    mock_logger = MagicMock()
    monkeypatch.setattr("specfact_cli.registry.module_installer.get_bridge_logger", lambda _name: mock_logger)
    install_root = tmp_path / "modules"
    dep_dir = install_root / "specfact-project"
    dep_dir.mkdir(parents=True, exist_ok=True)
    (dep_dir / "module-package.yaml").write_text(
        "name: specfact-project\nversion: '0.39.0'\ncommands: [project]\n",
        encoding="utf-8",
    )

    install_module("nold-ai/specfact-spec", install_root=install_root)

    assert calls == ["nold-ai/specfact-spec"]
    info_messages = " ".join(str(call.args[0]) for call in mock_logger.info.call_args_list)
    warning_messages = " ".join(str(call.args[0]) for call in mock_logger.warning.call_args_list)
    assert "already satisfied" in info_messages
    assert "already satisfied" not in warning_messages


def test_requested_bundle_install_aborts_when_dependency_install_fails(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _stub_integrity_and_deps(monkeypatch)
    tar_spec = _create_module_tarball(
        tmp_path,
        "specfact-spec",
        bundle_dependencies=["nold-ai/specfact-project"],
    )

    def _download(module_id: str, version: str | None = None) -> Path:
        _ = version
        if module_id == "nold-ai/specfact-spec":
            return tar_spec
        if module_id == "nold-ai/specfact-project":
            raise ValueError("dependency unavailable")
        raise ValueError(f"unexpected module id: {module_id}")

    monkeypatch.setattr("specfact_cli.registry.module_installer.download_module", _download)
    install_root = tmp_path / "modules"

    with pytest.raises(ValueError, match="Dependency install failed"):
        install_module("nold-ai/specfact-spec", install_root=install_root)

    assert not (install_root / "specfact-spec").exists()


def test_offline_install_uses_cached_tarball_when_registry_is_unavailable(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _stub_integrity_and_deps(monkeypatch)
    tar_project = _create_module_tarball(tmp_path, "specfact-project")
    tar_spec = _create_module_tarball(
        tmp_path,
        "specfact-spec",
        bundle_dependencies=["nold-ai/specfact-project"],
    )
    cache_root = tmp_path / "module-cache"
    cache_root.mkdir(parents=True, exist_ok=True)
    cached_project = cache_root / "nold-ai--specfact-project--latest.tar.gz"
    cached_spec = cache_root / "nold-ai--specfact-spec--latest.tar.gz"
    cached_project.write_bytes(tar_project.read_bytes())
    cached_spec.write_bytes(tar_spec.read_bytes())

    monkeypatch.setattr("specfact_cli.registry.module_installer.MODULE_DOWNLOAD_CACHE_ROOT", cache_root)
    monkeypatch.setattr(
        "specfact_cli.registry.module_installer.download_module",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError("Cannot install from marketplace (offline)")),
    )
    install_root = tmp_path / "modules"

    install_module("nold-ai/specfact-spec", install_root=install_root)

    assert (install_root / "specfact-project" / "module-package.yaml").exists()
    assert (install_root / "specfact-spec" / "module-package.yaml").exists()

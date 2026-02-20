"""Tests for marketplace module installer workflows."""

from __future__ import annotations

import tarfile
from pathlib import Path

import pytest

from specfact_cli.registry.module_installer import install_module, uninstall_module


def _create_module_tarball(tmp_path: Path, module_name: str, core_compatibility: str = ">=0.1.0,<1.0.0") -> Path:
    package_root = tmp_path / f"{module_name}-pkg"
    module_dir = package_root / module_name
    module_dir.mkdir(parents=True, exist_ok=True)
    (module_dir / "module-package.yaml").write_text(
        f"name: {module_name}\n"
        "version: '0.1.0'\n"
        f"commands: [{module_name}]\n"
        f'core_compatibility: "{core_compatibility}"\n',
        encoding="utf-8",
    )
    (module_dir / "src").mkdir(parents=True, exist_ok=True)

    tarball = tmp_path / f"{module_name}.tar.gz"
    with tarfile.open(tarball, "w:gz") as archive:
        archive.add(module_dir, arcname=module_name)
    return tarball


def test_install_module_downloads_extracts_and_registers(monkeypatch, tmp_path: Path) -> None:
    tarball = _create_module_tarball(tmp_path, "backlog")
    monkeypatch.setattr("specfact_cli.registry.module_installer.download_module", lambda *_args, **_kwargs: tarball)

    install_root = tmp_path / "marketplace-modules"
    installed = install_module("specfact/backlog", install_root=install_root)

    assert installed.exists()
    assert (installed / "module-package.yaml").exists()
    assert installed.parent == install_root


def test_install_module_to_default_marketplace_path(monkeypatch, tmp_path: Path) -> None:
    tarball = _create_module_tarball(tmp_path, "drift")
    monkeypatch.setattr("specfact_cli.registry.module_installer.download_module", lambda *_args, **_kwargs: tarball)

    install_root = tmp_path / "marketplace-modules"
    installed = install_module("specfact/drift", install_root=install_root)
    assert installed == install_root / "drift"


def test_install_module_already_installed_returns_existing(monkeypatch, tmp_path: Path) -> None:
    tarball = _create_module_tarball(tmp_path, "sync")
    monkeypatch.setattr("specfact_cli.registry.module_installer.download_module", lambda *_args, **_kwargs: tarball)

    install_root = tmp_path / "marketplace-modules"
    first_install = install_module("specfact/sync", install_root=install_root)
    second_install = install_module("specfact/sync", install_root=install_root)

    assert first_install == second_install


def test_uninstall_module_removes_marketplace_module(tmp_path: Path) -> None:
    install_root = tmp_path / "marketplace-modules"
    module_dir = install_root / "backlog"
    module_dir.mkdir(parents=True, exist_ok=True)
    (module_dir / "module-package.yaml").write_text(
        "name: backlog\nversion: '0.1.0'\ncommands: [backlog]\n", encoding="utf-8"
    )

    uninstall_module("backlog", install_root=install_root, source_map={"backlog": "marketplace"})
    assert not module_dir.exists()


def test_uninstall_builtin_module_raises_error(tmp_path: Path) -> None:
    install_root = tmp_path / "marketplace-modules"
    with pytest.raises(ValueError, match="Cannot uninstall built-in module"):
        uninstall_module("init", install_root=install_root, source_map={"init": "builtin"})


def test_install_module_validates_core_compatibility(monkeypatch, tmp_path: Path) -> None:
    tarball = _create_module_tarball(tmp_path, "policy", core_compatibility=">=9.0.0")
    monkeypatch.setattr("specfact_cli.registry.module_installer.download_module", lambda *_args, **_kwargs: tarball)

    with pytest.raises(ValueError, match="incompatible with current SpecFact CLI version"):
        install_module("specfact/policy", install_root=tmp_path / "marketplace-modules")

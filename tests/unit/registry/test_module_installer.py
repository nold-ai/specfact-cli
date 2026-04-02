"""Tests for marketplace module installer workflows."""

from __future__ import annotations

import io
import tarfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from specfact_cli.models.module_package import IntegrityInfo, ModulePackageMetadata
from specfact_cli.registry import module_installer
from specfact_cli.registry.module_installer import install_module, uninstall_module


@pytest.fixture(autouse=True)
def _no_op_resolve_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    """Avoid invoking pip-based resolver in unit tests (Hatch env may lack pip module)."""
    monkeypatch.setattr(
        "specfact_cli.registry.module_installer.resolve_dependencies",
        lambda *_a, **_k: None,
    )


def _create_module_tarball(
    tmp_path: Path,
    module_name: str,
    core_compatibility: str = ">=0.1.0,<1.0.0",
    module_version: str = "0.1.0",
    bundle_dependencies: list[str] | None = None,
) -> Path:
    package_root = tmp_path / f"{module_name}-pkg"
    module_dir = package_root / module_name
    module_dir.mkdir(parents=True, exist_ok=True)
    dependency_yaml = ""
    if bundle_dependencies:
        rendered_dependencies = ", ".join(f"'{dependency}'" for dependency in bundle_dependencies)
        dependency_yaml = f"bundle_dependencies: [{rendered_dependencies}]\n"
    (module_dir / "module-package.yaml").write_text(
        f"name: {module_name}\n"
        f"version: '{module_version}'\n"
        f"commands: [{module_name}]\n"
        f'core_compatibility: "{core_compatibility}"\n',
        encoding="utf-8",
    )
    if dependency_yaml:
        (module_dir / "module-package.yaml").write_text(
            (module_dir / "module-package.yaml").read_text(encoding="utf-8") + dependency_yaml,
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


def test_install_module_replaces_existing_module_on_reinstall(monkeypatch, tmp_path: Path) -> None:
    first_tarball = _create_module_tarball(tmp_path, "sync", module_version="0.1.0")
    second_tarball = _create_module_tarball(tmp_path, "sync-v2", module_version="0.2.0")

    def _download(_module_id: str, version: str | None = None) -> Path:
        return second_tarball if version == "0.2.0" else first_tarball

    monkeypatch.setattr("specfact_cli.registry.module_installer.download_module", _download)

    install_root = tmp_path / "marketplace-modules"
    install_module("specfact/sync", install_root=install_root, version="0.1.0")
    install_module("specfact/sync", install_root=install_root, version="0.2.0", reinstall=True)

    manifest = (install_root / "sync" / "module-package.yaml").read_text(encoding="utf-8")
    assert "version: '0.2.0'" in manifest


def test_install_module_logs_satisfied_dependencies_without_warning(monkeypatch, tmp_path: Path) -> None:
    tarball = _create_module_tarball(
        tmp_path,
        "backlog",
        bundle_dependencies=["nold-ai/specfact-project"],
    )
    monkeypatch.setattr("specfact_cli.registry.module_installer.download_module", lambda *_args, **_kwargs: tarball)
    monkeypatch.setattr("specfact_cli.registry.module_installer.verify_module_artifact", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(
        "specfact_cli.registry.module_installer.ensure_publisher_trusted", lambda *_args, **_kwargs: None
    )
    monkeypatch.setattr("specfact_cli.registry.module_installer.resolve_dependencies", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("specfact_cli.registry.module_installer.discover_all_modules", list)

    mock_logger = MagicMock()
    monkeypatch.setattr(module_installer, "get_bridge_logger", lambda _name: mock_logger)

    install_root = tmp_path / "marketplace-modules"
    dependency_dir = install_root / "specfact-project"
    dependency_dir.mkdir(parents=True, exist_ok=True)
    (dependency_dir / "module-package.yaml").write_text(
        "name: specfact-project\nversion: '0.40.16'\ncommands: [project]\n",
        encoding="utf-8",
    )

    installed = install_module("nold-ai/specfact-backlog", install_root=install_root, reinstall=True)

    assert installed.exists()
    mock_logger.warning.assert_not_called()
    mock_logger.info.assert_called_once_with(
        "Dependency %s already satisfied (version %s)",
        "nold-ai/specfact-project",
        "0.40.16",
    )


def test_install_module_rejects_archive_path_traversal(monkeypatch, tmp_path: Path) -> None:
    tarball = tmp_path / "unsafe.tar.gz"
    with tarfile.open(tarball, "w:gz") as archive:
        manifest_bytes = b"name: policy\nversion: '0.1.0'\ncommands: [policy]\ncore_compatibility: \">=0.1.0,<1.0.0\"\n"
        manifest_info = tarfile.TarInfo(name="policy/module-package.yaml")
        manifest_info.size = len(manifest_bytes)
        archive.addfile(manifest_info, io.BytesIO(manifest_bytes))

        traversal_bytes = b"owned"
        traversal_info = tarfile.TarInfo(name="../outside.txt")
        traversal_info.size = len(traversal_bytes)
        archive.addfile(traversal_info, io.BytesIO(traversal_bytes))

    monkeypatch.setattr("specfact_cli.registry.module_installer.download_module", lambda *_args, **_kwargs: tarball)

    with pytest.raises(ValueError, match="unsafe archive"):
        install_module("specfact/policy", install_root=tmp_path / "marketplace-modules")


def test_install_module_rejects_invalid_namespace_format(monkeypatch, tmp_path: Path) -> None:
    """install_module raises ValueError for module_id not matching namespace/name (lowercase, alphanumeric + hyphens)."""
    tarball = _create_module_tarball(tmp_path, "backlog")
    monkeypatch.setattr("specfact_cli.registry.module_installer.download_module", lambda *_args, **_kwargs: tarball)
    install_root = tmp_path / "marketplace-modules"
    for invalid_id in ("NoCap/backlog", "specfact/Backlog", "123/name"):
        with pytest.raises(ValueError, match=r"namespace/name|Marketplace module id"):
            install_module(invalid_id, install_root=install_root)


def test_install_module_accepts_valid_namespace_format(monkeypatch, tmp_path: Path) -> None:
    """install_module accepts module_id matching namespace/name (lowercase, alphanumeric + hyphens)."""
    tarball = _create_module_tarball(tmp_path, "backlog")
    monkeypatch.setattr("specfact_cli.registry.module_installer.download_module", lambda *_args, **_kwargs: tarball)
    install_root = tmp_path / "marketplace-modules"
    install_module("specfact/backlog", install_root=install_root)
    assert (install_root / "backlog" / "module-package.yaml").exists()
    tarball2 = _create_module_tarball(tmp_path, "backlog-pro", module_version="0.1.0")
    monkeypatch.setattr("specfact_cli.registry.module_installer.download_module", lambda *_args, **_kwargs: tarball2)
    install_module("acme-corp/backlog-pro", install_root=install_root)
    assert (install_root / "backlog-pro" / "module-package.yaml").exists()


def test_install_module_namespace_collision_raises(monkeypatch, tmp_path: Path) -> None:
    """When same name is already installed from a different module_id, install_module raises namespace collision."""
    tarball = _create_module_tarball(tmp_path, "backlog")
    monkeypatch.setattr("specfact_cli.registry.module_installer.download_module", lambda *_args, **_kwargs: tarball)
    install_root = tmp_path / "marketplace-modules"
    install_module("specfact/backlog", install_root=install_root)
    tarball2 = _create_module_tarball(tmp_path, "backlog", module_version="0.2.0")
    monkeypatch.setattr("specfact_cli.registry.module_installer.download_module", lambda *_args, **_kwargs: tarball2)
    with pytest.raises(ValueError, match=r"namespace collision|conflicts with existing"):
        install_module("acme-corp/backlog", install_root=install_root)


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

    with pytest.raises(ValueError, match="requires SpecFact CLI"):
        install_module("specfact/policy", install_root=tmp_path / "marketplace-modules")


def test_install_module_defaults_to_user_modules_root(monkeypatch, tmp_path: Path) -> None:
    """Installer should default to canonical user modules root when no install_root is provided."""
    tarball = _create_module_tarball(tmp_path, "policy")
    monkeypatch.setattr("specfact_cli.registry.module_installer.download_module", lambda *_args, **_kwargs: tarball)
    user_root = tmp_path / "modules"
    monkeypatch.setattr(module_installer, "USER_MODULES_ROOT", user_root)

    installed = install_module("specfact/policy")

    assert installed == user_root / "policy"


def test_install_module_rejects_denylisted_module(monkeypatch, tmp_path: Path) -> None:
    tarball = _create_module_tarball(tmp_path, "blocked")
    monkeypatch.setattr("specfact_cli.registry.module_installer.download_module", lambda *_args, **_kwargs: tarball)
    monkeypatch.setattr(
        "specfact_cli.registry.module_installer.assert_module_allowed",
        lambda module_name: (_ for _ in ()).throw(ValueError("denylisted module: blocked")),
    )

    with pytest.raises(ValueError, match="denylisted module"):
        install_module("specfact/blocked", install_root=tmp_path / "modules")


def test_sync_bundled_modules_rejects_denylisted_module(monkeypatch, tmp_path: Path) -> None:
    bundled = tmp_path / "bundled" / "blocked"
    bundled.mkdir(parents=True)
    (bundled / "module-package.yaml").write_text(
        "name: blocked\nversion: '0.1.0'\ncommands: [blocked]\n", encoding="utf-8"
    )
    monkeypatch.setattr(
        "specfact_cli.registry.module_installer._get_bundled_module_sources",
        lambda: {"blocked": bundled},
    )
    monkeypatch.setattr(
        "specfact_cli.registry.module_installer.assert_module_allowed",
        lambda module_name: (_ for _ in ()).throw(ValueError("denylisted module: blocked")),
    )

    with pytest.raises(ValueError, match="denylisted module"):
        module_installer.sync_bundled_modules_to_user_root(target_root=tmp_path / "target")


def test_install_bundled_module_enforces_integrity_verification(monkeypatch, tmp_path: Path) -> None:
    bundled = tmp_path / "bundled" / "secure"
    bundled.mkdir(parents=True)
    (bundled / "module-package.yaml").write_text(
        "name: secure\nversion: '0.1.0'\ncommands: [secure]\n", encoding="utf-8"
    )
    monkeypatch.setattr(
        "specfact_cli.registry.module_installer._get_bundled_module_sources",
        lambda: {"secure": bundled},
    )
    metadata = module_installer.ModulePackageMetadata(name="secure", version="0.1.0", commands=["secure"])
    monkeypatch.setattr(
        "specfact_cli.registry.module_installer.get_bundled_module_metadata",
        lambda: {"secure": metadata},
    )
    monkeypatch.setattr(
        "specfact_cli.registry.module_installer.verify_module_artifact",
        lambda *args, **kwargs: False,
    )

    with pytest.raises(ValueError, match="integrity"):
        module_installer.install_bundled_module("secure", target_root=tmp_path / "target")


def test_verify_module_artifact_detects_tamper_in_non_manifest_file(tmp_path: Path) -> None:
    module_dir = tmp_path / "secure"
    (module_dir / "src").mkdir(parents=True)
    manifest = module_dir / "module-package.yaml"
    source = module_dir / "src" / "main.py"
    manifest.write_text("name: secure\nversion: '0.1.0'\ncommands: [secure]\n", encoding="utf-8")
    source.write_text("print('v1')\n", encoding="utf-8")

    payload = module_installer._module_artifact_payload(module_dir)
    checksum = f"sha256:{__import__('hashlib').sha256(payload).hexdigest()}"
    metadata = ModulePackageMetadata(
        name="secure",
        version="0.1.0",
        commands=["secure"],
        integrity=IntegrityInfo(checksum=checksum),
    )

    assert module_installer.verify_module_artifact(module_dir, metadata, allow_unsigned=False) is True

    source.write_text("print('tampered')\n", encoding="utf-8")
    assert module_installer.verify_module_artifact(module_dir, metadata, allow_unsigned=False) is False


def test_verify_module_artifact_checksum_mismatch_hides_raw_details_without_debug(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    module_dir = tmp_path / "secure"
    (module_dir / "src").mkdir(parents=True)
    manifest = module_dir / "module-package.yaml"
    source = module_dir / "src" / "main.py"
    manifest.write_text("name: secure\nversion: '0.1.0'\ncommands: [secure]\n", encoding="utf-8")
    source.write_text("print('v1')\n", encoding="utf-8")

    payload = module_installer._module_artifact_payload(module_dir)
    checksum = f"sha256:{__import__('hashlib').sha256(payload).hexdigest()}"
    metadata = ModulePackageMetadata(
        name="secure",
        version="0.1.0",
        commands=["secure"],
        integrity=IntegrityInfo(checksum=checksum),
    )
    source.write_text("print('tampered')\n", encoding="utf-8")

    mock_logger = MagicMock()
    monkeypatch.setattr(module_installer, "get_bridge_logger", lambda _name: mock_logger)
    monkeypatch.setattr(module_installer, "is_debug_mode", lambda: False, raising=False)

    assert module_installer.verify_module_artifact(module_dir, metadata, allow_unsigned=False) is False
    mock_logger.warning.assert_not_called()
    mock_logger.debug.assert_called()


def test_verify_module_artifact_checksum_mismatch_logs_raw_details_in_debug(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    module_dir = tmp_path / "secure"
    (module_dir / "src").mkdir(parents=True)
    manifest = module_dir / "module-package.yaml"
    source = module_dir / "src" / "main.py"
    manifest.write_text("name: secure\nversion: '0.1.0'\ncommands: [secure]\n", encoding="utf-8")
    source.write_text("print('v1')\n", encoding="utf-8")

    payload = module_installer._module_artifact_payload(module_dir)
    checksum = f"sha256:{__import__('hashlib').sha256(payload).hexdigest()}"
    metadata = ModulePackageMetadata(
        name="secure",
        version="0.1.0",
        commands=["secure"],
        integrity=IntegrityInfo(checksum=checksum),
    )
    source.write_text("print('tampered')\n", encoding="utf-8")

    mock_logger = MagicMock()
    monkeypatch.setattr(module_installer, "get_bridge_logger", lambda _name: mock_logger)
    monkeypatch.setattr(module_installer, "is_debug_mode", lambda: True, raising=False)

    assert module_installer.verify_module_artifact(module_dir, metadata, allow_unsigned=False) is False
    mock_logger.warning.assert_called_once()


def test_verify_module_artifact_checksum_mismatch_logs_raw_details_when_debug_flag_in_argv(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    module_dir = tmp_path / "secure"
    (module_dir / "src").mkdir(parents=True)
    manifest = module_dir / "module-package.yaml"
    source = module_dir / "src" / "main.py"
    manifest.write_text("name: secure\nversion: '0.1.0'\ncommands: [secure]\n", encoding="utf-8")
    source.write_text("print('v1')\n", encoding="utf-8")

    payload = module_installer._module_artifact_payload(module_dir)
    checksum = f"sha256:{__import__('hashlib').sha256(payload).hexdigest()}"
    metadata = ModulePackageMetadata(
        name="secure",
        version="0.1.0",
        commands=["secure"],
        integrity=IntegrityInfo(checksum=checksum),
    )
    source.write_text("print('tampered')\n", encoding="utf-8")

    mock_logger = MagicMock()
    monkeypatch.setattr(module_installer, "get_bridge_logger", lambda _name: mock_logger)
    monkeypatch.setattr(module_installer, "is_debug_mode", lambda: False, raising=False)
    monkeypatch.setattr(module_installer.sys, "argv", ["specfact", "--debug", "module", "list"])

    assert module_installer.verify_module_artifact(module_dir, metadata, allow_unsigned=False) is False
    mock_logger.warning.assert_called_once()


def test_verify_module_artifact_ignores_runtime_cache_files(tmp_path: Path) -> None:
    module_dir = tmp_path / "secure"
    (module_dir / "src").mkdir(parents=True)
    manifest = module_dir / "module-package.yaml"
    source = module_dir / "src" / "main.py"
    manifest.write_text("name: secure\nversion: '0.1.0'\ncommands: [secure]\n", encoding="utf-8")
    source.write_text("print('v1')\n", encoding="utf-8")

    payload = module_installer._module_artifact_payload(module_dir)
    checksum = f"sha256:{__import__('hashlib').sha256(payload).hexdigest()}"
    metadata = ModulePackageMetadata(
        name="secure",
        version="0.1.0",
        commands=["secure"],
        integrity=IntegrityInfo(checksum=checksum),
    )

    pycache_file = module_dir / "__pycache__" / "main.cpython-312.pyc"
    pycache_file.parent.mkdir(parents=True)
    pycache_file.write_bytes(b"\x00\x01\x02")

    assert module_installer.verify_module_artifact(module_dir, metadata, allow_unsigned=False) is True


def test_verify_module_artifact_ignores_installer_written_registry_id_file(
    tmp_path: Path,
) -> None:
    """Post-install dir contains .specfact-registry-id; verification must still pass."""
    module_dir = tmp_path / "secure"
    (module_dir / "src").mkdir(parents=True)
    manifest = module_dir / "module-package.yaml"
    source = module_dir / "src" / "main.py"
    manifest.write_text("name: secure\nversion: '0.1.0'\ncommands: [secure]\n", encoding="utf-8")
    source.write_text("print('v1')\n", encoding="utf-8")

    payload = module_installer._module_artifact_payload(module_dir)
    checksum = f"sha256:{__import__('hashlib').sha256(payload).hexdigest()}"
    metadata = ModulePackageMetadata(
        name="secure",
        version="0.1.0",
        commands=["secure"],
        integrity=IntegrityInfo(checksum=checksum),
    )

    registry_id_file = module_dir / module_installer.REGISTRY_ID_FILE
    registry_id_file.write_text("nold-ai/specfact-backlog", encoding="utf-8")

    assert module_installer.verify_module_artifact(module_dir, metadata, allow_unsigned=False) is True


def test_verify_module_artifact_accepts_install_verified_checksum_fallback(
    tmp_path: Path,
) -> None:
    """When manifest checksum does not match (e.g. different sign tool), accept if .specfact-install-verified-checksum matches."""
    module_dir = tmp_path / "secure"
    (module_dir / "src").mkdir(parents=True)
    manifest = module_dir / "module-package.yaml"
    source = module_dir / "src" / "main.py"
    manifest.write_text("name: secure\nversion: '0.1.0'\ncommands: [secure]\n", encoding="utf-8")
    source.write_text("print('v1')\n", encoding="utf-8")

    payload = module_installer._module_artifact_payload(module_dir)
    correct_checksum = f"sha256:{__import__('hashlib').sha256(payload).hexdigest()}"
    metadata = ModulePackageMetadata(
        name="secure",
        version="0.1.0",
        commands=["secure"],
        integrity=IntegrityInfo(checksum="sha256:0000000000000000000000000000000000000000000000000000000000000000"),
    )

    (module_dir / module_installer.REGISTRY_ID_FILE).write_text("nold-ai/specfact-backlog", encoding="utf-8")
    (module_dir / module_installer.INSTALL_VERIFIED_CHECKSUM_FILE).write_text(correct_checksum, encoding="utf-8")

    assert module_installer.verify_module_artifact(module_dir, metadata, allow_unsigned=False) is True


def test_verify_module_artifact_fallback_does_not_emit_info_in_normal_mode(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    module_dir = tmp_path / "secure"
    (module_dir / "src").mkdir(parents=True)
    manifest = module_dir / "module-package.yaml"
    source = module_dir / "src" / "main.py"
    manifest.write_text("name: secure\nversion: '0.1.0'\ncommands: [secure]\n", encoding="utf-8")
    source.write_text("print('v1')\n", encoding="utf-8")

    pycache_file = module_dir / "__pycache__" / "main.cpython-312.pyc"
    pycache_file.parent.mkdir(parents=True)
    pycache_file.write_bytes(b"\x00\x01\x02")

    stable_payload = module_installer._module_artifact_payload_stable(module_dir)
    checksum = f"sha256:{__import__('hashlib').sha256(stable_payload).hexdigest()}"
    metadata = ModulePackageMetadata(
        name="secure",
        version="0.1.0",
        commands=["secure"],
        integrity=IntegrityInfo(checksum=checksum),
    )

    mock_logger = MagicMock()
    monkeypatch.setattr(module_installer, "get_bridge_logger", lambda _name: mock_logger)
    monkeypatch.setattr(module_installer, "is_debug_mode", lambda: False, raising=False)

    assert module_installer.verify_module_artifact(module_dir, metadata, allow_unsigned=False) is True
    mock_logger.info.assert_not_called()
    mock_logger.debug.assert_not_called()


def test_verify_module_artifact_fallback_emits_debug_in_debug_mode(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    module_dir = tmp_path / "secure"
    (module_dir / "src").mkdir(parents=True)
    manifest = module_dir / "module-package.yaml"
    source = module_dir / "src" / "main.py"
    manifest.write_text("name: secure\nversion: '0.1.0'\ncommands: [secure]\n", encoding="utf-8")
    source.write_text("print('v1')\n", encoding="utf-8")

    pycache_file = module_dir / "__pycache__" / "main.cpython-312.pyc"
    pycache_file.parent.mkdir(parents=True)
    pycache_file.write_bytes(b"\x00\x01\x02")

    stable_payload = module_installer._module_artifact_payload_stable(module_dir)
    checksum = f"sha256:{__import__('hashlib').sha256(stable_payload).hexdigest()}"
    metadata = ModulePackageMetadata(
        name="secure",
        version="0.1.0",
        commands=["secure"],
        integrity=IntegrityInfo(checksum=checksum),
    )

    mock_logger = MagicMock()
    monkeypatch.setattr(module_installer, "get_bridge_logger", lambda _name: mock_logger)
    monkeypatch.setattr(module_installer, "is_debug_mode", lambda: True, raising=False)
    monkeypatch.setattr(
        module_installer,
        "_module_artifact_payload_signed",
        lambda _: (_ for _ in ()).throw(ValueError("force fallback")),
    )

    assert module_installer.verify_module_artifact(module_dir, metadata, allow_unsigned=False) is True
    mock_logger.info.assert_not_called()
    mock_logger.debug.assert_called_once()


def test_verify_module_artifact_falls_back_when_signature_backend_unavailable(
    monkeypatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    module_dir = tmp_path / "secure"
    (module_dir / "src").mkdir(parents=True)
    manifest = module_dir / "module-package.yaml"
    source = module_dir / "src" / "main.py"
    manifest.write_text("name: secure\nversion: '0.1.0'\ncommands: [secure]\n", encoding="utf-8")
    source.write_text("print('stable')\n", encoding="utf-8")

    payload = module_installer._module_artifact_payload(module_dir)
    checksum = f"sha256:{__import__('hashlib').sha256(payload).hexdigest()}"
    metadata = ModulePackageMetadata(
        name="secure",
        version="0.1.0",
        commands=["secure"],
        integrity=IntegrityInfo(checksum=checksum, signature="c2ln"),
    )

    monkeypatch.setattr(
        module_installer,
        "verify_signature",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            ValueError("Signature verification backend unavailable: No module named '_cffi_backend'")
        ),
    )
    caplog.set_level("WARNING")

    assert module_installer.verify_module_artifact(module_dir, metadata, allow_unsigned=False) is True


def test_verify_module_artifact_fails_if_signature_required_and_backend_unavailable(
    monkeypatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    module_dir = tmp_path / "secure"
    (module_dir / "src").mkdir(parents=True)
    manifest = module_dir / "module-package.yaml"
    source = module_dir / "src" / "main.py"
    manifest.write_text("name: secure\nversion: '0.1.0'\ncommands: [secure]\n", encoding="utf-8")
    source.write_text("print('stable')\n", encoding="utf-8")

    payload = module_installer._module_artifact_payload(module_dir)
    checksum = f"sha256:{__import__('hashlib').sha256(payload).hexdigest()}"
    metadata = ModulePackageMetadata(
        name="secure",
        version="0.1.0",
        commands=["secure"],
        integrity=IntegrityInfo(checksum=checksum, signature="c2ln"),
    )

    monkeypatch.setattr(
        module_installer,
        "verify_signature",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            ValueError("Signature verification backend unavailable: No module named '_cffi_backend'")
        ),
    )
    caplog.set_level("WARNING")

    assert (
        module_installer.verify_module_artifact(
            module_dir,
            metadata,
            allow_unsigned=False,
            require_signature=True,
        )
        is False
    )


def test_uninstall_module_falls_back_to_legacy_marketplace_root(tmp_path: Path, monkeypatch) -> None:
    user_root = tmp_path / "modules"
    legacy_marketplace_root = tmp_path / "marketplace-modules"
    monkeypatch.setattr(module_installer, "USER_MODULES_ROOT", user_root)
    monkeypatch.setattr(module_installer, "MARKETPLACE_MODULES_ROOT", legacy_marketplace_root)

    module_dir = legacy_marketplace_root / "backlog"
    module_dir.mkdir(parents=True, exist_ok=True)
    (module_dir / "module-package.yaml").write_text(
        "name: backlog\nversion: '0.1.0'\ncommands: [backlog]\n", encoding="utf-8"
    )

    uninstall_module("backlog", source_map={"backlog": "marketplace"})
    assert not module_dir.exists()


def test_load_public_key_pem_prefers_explicit_then_env_then_bundled(monkeypatch, tmp_path: Path) -> None:
    key_file = tmp_path / "module-signing-public.pem"
    key_file.write_text("PUBLIC-KEY-FROM-FILE", encoding="utf-8")
    monkeypatch.setattr(module_installer, "_bundled_public_key_path", lambda: key_file)

    monkeypatch.setenv("SPECFACT_MODULE_PUBLIC_KEY_PEM", "PUBLIC-KEY-FROM-ENV")
    assert module_installer._load_public_key_pem("PUBLIC-KEY-EXPLICIT") == "PUBLIC-KEY-EXPLICIT"
    assert module_installer._load_public_key_pem(None) == "PUBLIC-KEY-FROM-ENV"

    monkeypatch.delenv("SPECFACT_MODULE_PUBLIC_KEY_PEM", raising=False)
    assert module_installer._load_public_key_pem(None) == "PUBLIC-KEY-FROM-FILE"

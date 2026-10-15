import json
from collections.abc import Callable
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from specfact_cli.models.module_package import ModulePackageMetadata
from specfact_cli.registry import CommandRegistry, module_installer as installer, module_packages as packages
from tests.unit.security.test_executable_identity_oracles import (
    _assert_genuine_signature,
    _canonical_compatibility,
    _register,
)
from tests.unit.security.test_module_command_squatting import _reset_registration
from tests.unit.security.test_package_candidate_eligibility import _signed_copy, selection_key as selection_key
from tests.unit.security.test_project_bundle_authority import _isolate_discovery_roots


def _linked_project_copy(root: Path, key: Ed25519PrivateKey, kind: str) -> tuple[Path, Path]:
    workspace = root / kind / "workspace"
    store = workspace / ".specfact/modules"
    target = _signed_copy(root / kind / "authentic", key, None)
    link, destination = {
        "package": (store / target.name, target),
        "modules": (store, target.parent),
        "specfact": (store.parent, target.parent.parent),
    }[kind]
    link.parent.mkdir(parents=True)
    link.symlink_to(destination, target_is_directory=True)
    return workspace, store / target.name


def _observe_path_link(
    monkeypatch: pytest.MonkeyPatch,
    root: Path,
    key: Ed25519PrivateKey,
    case: tuple[str, bool],
) -> tuple[str, bool, bool, bool]:
    kind, grouped = case
    try:
        with monkeypatch.context() as probe:
            _canonical_compatibility(probe, root / kind / "canonical", key, grouped)
            workspace, path = _linked_project_copy(root, key, kind)
            _assert_genuine_signature(path)
            _register(probe, workspace, grouped)
            root_denied = CommandRegistry.get_module_metadata("code") is None
            source_denied = (path / "src").resolve() not in packages._ACTIVE_MODULE_SRC_DIRS
            _reset_registration()
            installed = _signed_copy(root / kind / "user", key, None)
            _isolate_discovery_roots(probe, workspace, installed.parent)
            packages.register_module_package_commands(allow_unsigned=False, category_grouping_enabled=grouped)
            fallback_kept = (installed / "src").resolve() in packages._ACTIVE_MODULE_SRC_DIRS and (
                path / "src"
            ).resolve() not in packages._ACTIVE_MODULE_SRC_DIRS
            return kind, root_denied, source_denied, fallback_kept
    finally:
        _reset_registration()


@pytest.mark.parametrize("grouped", [True, False], ids=["grouped", "legacy"])
def test_project_path_links_have_no_authority(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    selection_key: Ed25519PrivateKey,
    grouped: bool,
    record_testsuite_property: Callable[[str, object], None],
) -> None:
    observations = [
        _observe_path_link(monkeypatch, tmp_path, selection_key, (kind, grouped))
        for kind in ("package", "modules", "specfact")
    ]
    record_testsuite_property(f"project_path_link_observations-{grouped}", json.dumps(observations))
    assert len(observations) == 3
    assert all(
        root_denied and source_denied and fallback_kept for _, root_denied, source_denied, fallback_kept in observations
    ), observations


def test_legacy_native_suffixes_have_no_authority(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    selection_key: Ed25519PrivateKey,
    record_testsuite_property: Callable[[str, object], None],
) -> None:
    observations: list[tuple[str, bool, bool]] = []
    for suffix in ("dll", "dylib", "bundle", "so", "pyd"):
        try:
            with monkeypatch.context() as probe:
                root = tmp_path / suffix
                _canonical_compatibility(probe, root / "canonical", selection_key, False)
                workspace = root / "workspace"
                path = _signed_copy(workspace / ".specfact/modules", selection_key, None)
                (path / "logs").mkdir()
                (path / "logs" / f"probe.{suffix}").write_bytes(b"harmless omitted native library probe")
                _assert_genuine_signature(path)
                _register(probe, workspace, False)
                observations.append(
                    (
                        suffix,
                        CommandRegistry.get_module_metadata("code") is None,
                        (path / "src").resolve() not in packages._ACTIVE_MODULE_SRC_DIRS,
                    )
                )
        finally:
            _reset_registration()
    record_testsuite_property("legacy_native_suffix_observations", json.dumps(observations))
    assert len(observations) == 5
    assert all(root_denied and source_denied for _, root_denied, source_denied in observations), observations


@pytest.mark.parametrize("grouped", [True, False], ids=["grouped", "legacy"])
def test_workspace_alias_keeps_canonical_signed_authority(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    selection_key: Ed25519PrivateKey,
    grouped: bool,
) -> None:
    workspace = tmp_path / "workspace"
    path = _signed_copy(workspace / ".specfact/modules", selection_key, None)
    alias = tmp_path / "workspace-alias"
    alias.symlink_to(workspace, target_is_directory=True)
    _assert_genuine_signature(path)
    _register(monkeypatch, alias, grouped)
    assert CommandRegistry.get_module_metadata("code") is not None
    assert (path / "src").resolve() in packages._ACTIVE_MODULE_SRC_DIRS


@pytest.mark.parametrize("grouped", [True, False], ids=["grouped", "legacy"])
def test_final_selection_revalidates_new_package_link(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    selection_key: Ed25519PrivateKey,
    grouped: bool,
) -> None:
    workspace = tmp_path / "workspace"
    project = _signed_copy(workspace, selection_key, None)
    installed = _signed_copy(tmp_path / "user", selection_key, None)
    target = tmp_path / "authenticated-relocation" / project.name
    target.parent.mkdir()
    original = packages._verified_project_bundle_root

    def link_after_verification(package_dir: Path, metadata: ModulePackageMetadata) -> bool:
        verified = original(package_dir, metadata)
        if verified and package_dir == project and not project.is_symlink():
            project.rename(target)
            project.symlink_to(target, target_is_directory=True)
        return verified

    _assert_genuine_signature(project)
    _assert_genuine_signature(installed)
    _isolate_discovery_roots(monkeypatch, workspace, installed.parent)
    monkeypatch.setattr(packages, "_verified_project_bundle_root", link_after_verification)
    packages.register_module_package_commands(allow_unsigned=False, category_grouping_enabled=grouped)
    assert project.is_symlink()
    assert CommandRegistry.get_module_metadata("code") is not None
    assert (installed / "src").resolve() in packages._ACTIVE_MODULE_SRC_DIRS
    assert (target / "src").resolve() not in packages._ACTIVE_MODULE_SRC_DIRS


def _link_before_snapshot_resolution(monkeypatch: pytest.MonkeyPatch, project: Path, target: Path, kind: str) -> Path:
    source = {"package": project, "modules": project.parent, "specfact": project.parent.parent}[kind]
    original_resolve = Path.resolve
    original_verify = installer.verify_module_artifact_from_filesystem
    active = False
    project_checks = 0

    def resolve(path: Path, strict: bool = False) -> Path:
        if active and path == project and not source.is_symlink():
            source.rename(target)
            source.symlink_to(target, target_is_directory=True)
        return original_resolve(path, strict=strict)

    def verify(package_dir: Path, metadata: ModulePackageMetadata, public_key: str) -> bool:
        nonlocal active, project_checks
        project_checks += int(package_dir == project)
        active = package_dir == project and project_checks == 2
        result = original_verify(package_dir, metadata, public_key)
        active = False
        return result

    monkeypatch.setattr(Path, "resolve", resolve)
    monkeypatch.setattr(installer, "verify_module_artifact_from_filesystem", verify)
    return source


@pytest.mark.parametrize("grouped", [True, False], ids=["grouped", "legacy"])
@pytest.mark.parametrize("kind", ["package", "modules", "specfact"])
def test_final_admission_reobserves_owned_path_links(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    selection_key: Ed25519PrivateKey,
    grouped: bool,
    kind: str,
) -> None:
    _canonical_compatibility(monkeypatch, tmp_path / "canonical", selection_key, grouped)
    workspace = tmp_path / "workspace"
    project = _signed_copy(workspace, selection_key, None)
    installed = _signed_copy(tmp_path / "user", selection_key, None)
    target = tmp_path / "authenticated-relocation"
    _assert_genuine_signature(project)
    _assert_genuine_signature(installed)
    _isolate_discovery_roots(monkeypatch, workspace, installed.parent)
    source = _link_before_snapshot_resolution(monkeypatch, project, target, kind)
    packages.register_module_package_commands(allow_unsigned=False, category_grouping_enabled=grouped)
    assert source.is_symlink()
    assert CommandRegistry.get_module_metadata("code") is not None
    assert (installed / "src").resolve() in packages._ACTIVE_MODULE_SRC_DIRS
    assert (project / "src").resolve() not in packages._ACTIVE_MODULE_SRC_DIRS

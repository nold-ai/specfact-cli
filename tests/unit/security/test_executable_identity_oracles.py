"""Real signed metadata and suffix-independent executable inventory admission controls."""

from pathlib import Path

import pytest
import yaml
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from specfact_cli.models.module_package import ModulePackageMetadata
from specfact_cli.registry import CommandRegistry, module_installer, module_packages as packages
from specfact_cli.registry.module_grouping import ModuleManifestError
from tests.unit.security.test_module_command_squatting import _reset_registration
from tests.unit.security.test_package_candidate_eligibility import (
    _assert_active,
    _signed_copy,
    selection_key as selection_key,
)
from tests.unit.security.test_project_bundle_authority import _isolate_discovery_roots


EXECUTABLE_PROBES = {
    "mode": b"harmless executable-mode probe",
    "shebang": b"#!/bin/sh\nexit 0\n",
    "elf": b"\x7fELF" + bytes(20),
    "pe": b"MZ" + bytes(20),
    "mach-o": b"\xcf\xfa\xed\xfe" + bytes(20),
    "fat-mach-o": b"\xca\xfe\xba\xbe" + bytes(20),
}


def _assert_genuine_signature(path: Path) -> None:
    raw = yaml.safe_load((path / "module-package.yaml").read_text(encoding="utf-8"))
    metadata = ModulePackageMetadata.model_validate(raw)
    public = module_installer._bundled_public_key_path().read_text(encoding="utf-8")
    assert module_installer.verify_module_artifact(
        path, metadata, public_key_pem=public, allow_unsigned=False, require_signature=True
    ), "The real signature must remain valid before public admission is tested"


def _register(monkeypatch: pytest.MonkeyPatch, workspace: Path, grouped: bool) -> None:
    _isolate_discovery_roots(monkeypatch, workspace, workspace / "missing-user")
    packages.register_module_package_commands(allow_unsigned=False, category_grouping_enabled=grouped)


def _canonical_compatibility(
    monkeypatch: pytest.MonkeyPatch, workspace: Path, key: Ed25519PrivateKey, grouped: bool
) -> None:
    path = _signed_copy(workspace, key, None)
    (path / "logs").mkdir()
    (path / "logs/note").write_text("ordinary excluded diagnostic", encoding="utf-8")
    _assert_genuine_signature(path)
    _register(monkeypatch, workspace, grouped)
    assert CommandRegistry.get_module_metadata("code") is not None
    _assert_active([path], [])
    _reset_registration()


@pytest.mark.parametrize("grouped", [True, False], ids=["grouped", "legacy"])
@pytest.mark.parametrize("probe", EXECUTABLE_PROBES)
def test_excluded_extensionless_executable_is_denied(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, selection_key: Ed25519PrivateKey, grouped: bool, probe: str
) -> None:
    """Inspect harmless mode/header probes only; never execute an unsigned candidate artifact."""
    _canonical_compatibility(monkeypatch, tmp_path / "canonical", selection_key, grouped)
    workspace = tmp_path / "candidate"
    path = _signed_copy(workspace, selection_key, None)
    (path / "logs").mkdir()
    target = path / "logs/helper"
    target.write_bytes(EXECUTABLE_PROBES[probe])
    target.chmod(0o755 if probe == "mode" else 0o644)
    _assert_genuine_signature(path)
    _register(monkeypatch, workspace, grouped)
    assert CommandRegistry.get_module_metadata("code") is None, "Omitted executable obtained category authority"
    _assert_active([], [path])


def _deny_noncanonical_identity(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    key: Ed25519PrivateKey,
    grouped: bool,
    identity: tuple[str, str],
) -> None:
    """Keep genuine crypto valid while existing grouping and root admission enforce canonical identity."""
    field, value = identity
    _canonical_compatibility(monkeypatch, tmp_path / "canonical", key, grouped)
    workspace = tmp_path / "candidate"
    path = _signed_copy(workspace, key, None, **{field: value})
    _assert_genuine_signature(path)
    try:
        _register(monkeypatch, workspace, grouped)
    except ModuleManifestError as error:
        assert field in {"category", "bundle_group_command"} and str(error), (
            "Existing grouping validation must report a concrete category/group refusal"
        )
        _assert_active([], [path])
        return
    assert CommandRegistry.get_module_metadata("code") is None
    _assert_active([], [path])


@pytest.mark.parametrize("grouped", [True, False], ids=["grouped", "legacy"])
@pytest.mark.parametrize(
    "identity",
    [("tier", "community"), ("category", "spec"), ("bundle_group_command", "plan")],
    ids=["tier-community", "category-spec", "bundle_group_command-plan"],
)
def test_valid_signature_noncanonical_identity_is_denied(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    selection_key: Ed25519PrivateKey,
    grouped: bool,
    identity: tuple[str, str],
) -> None:
    """Independently verify existing category/group refusal and noncanonical tier denial."""
    _deny_noncanonical_identity(monkeypatch, tmp_path, selection_key, grouped, identity)


@pytest.mark.parametrize("grouped", [True, False], ids=["grouped", "legacy"])
def test_all_signed_identity_fields_retain_canonical_authority(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, selection_key: Ed25519PrivateKey, grouped: bool
) -> None:
    """Keep existing signed category/group rejection before exercising the genuine tier regression."""
    for identity in [("category", "spec"), ("bundle_group_command", "plan"), ("tier", "community")]:
        _deny_noncanonical_identity(monkeypatch, tmp_path / identity[0], selection_key, grouped, identity)
        _reset_registration()

"""Public registration oracles isolate identity, cycle compatibility and explicit refusal."""

import logging
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from specfact_cli.registry import CommandRegistry, module_installer, module_packages as packages
from tests.unit.security.test_module_command_squatting import _reset_registration
from tests.unit.security.test_package_candidate_eligibility import (
    _assert_active,
    _provider,
    _register_candidates,
    _signed_copy,
    selection_key as selection_key,
    test_conflicting_dependency_cycle_refuses_only_unstable_component as _exercise_conflict,
    test_consistent_dependency_cycle_keeps_commands as _exercise_consistent_cycle,
)
from tests.unit.security.test_project_bundle_authority import _isolate_discovery_roots


def _verified_project(parent: Path, key: Ed25519PrivateKey, publisher: str) -> Path:
    """Authenticate the changed publisher with a valid signature before testing identity admission."""
    path = _signed_copy(parent / ".specfact/modules", key, None, publisher={"name": publisher})
    metadata = packages.discover_package_metadata(path.parent, source="project")[0][1]
    public = module_installer._bundled_public_key_path().read_text(encoding="utf-8")
    assert module_installer.verify_module_artifact(
        path, metadata, public_key_pem=public, allow_unsigned=False, require_signature=True
    ), "The identity probe must have genuine valid integrity under the bundled test anchor"
    return path


@pytest.mark.parametrize("grouped", [True, False])
def test_validly_signed_noncanonical_publisher_is_denied(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, selection_key: Ed25519PrivateKey, grouped: bool
) -> None:
    """Keep a canonical signed root, then deny a noncanonical publisher with equally valid integrity."""
    canonical = _verified_project(tmp_path / "canonical", selection_key, "nold-ai")
    _isolate_discovery_roots(monkeypatch, tmp_path / "canonical", tmp_path / "missing-user")
    packages.register_module_package_commands(allow_unsigned=False, category_grouping_enabled=grouped)
    assert CommandRegistry.get_module_metadata("code") is not None
    _assert_active([canonical], [])
    _reset_registration()
    noncanonical = _verified_project(tmp_path / "noncanonical", selection_key, "hostile")
    _isolate_discovery_roots(monkeypatch, tmp_path / "noncanonical", tmp_path / "missing-user")
    packages.register_module_package_commands(allow_unsigned=False, category_grouping_enabled=grouped)
    assert CommandRegistry.get_module_metadata("code") is None, (
        "Valid crypto cannot replace canonical publisher identity"
    )
    _assert_active([], [noncanonical])


def test_consistent_cycle_survives_ineligible_priority_copy(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, selection_key: Ed25519PrivateKey
) -> None:
    """Retain healthy cyclic commands both alone and behind an ineligible same-name copy."""
    _exercise_consistent_cycle(monkeypatch, tmp_path / "healthy", selection_key)
    _reset_registration()
    rejected = _signed_copy(tmp_path / "rejected", selection_key, "core")
    consumer = _signed_copy(tmp_path / "consumer", selection_key, None, module_dependencies=["nold-ai/specfact-spec"])
    provider = _provider(
        tmp_path / "provider", selection_key, "1.0.0", module_dependencies=["nold-ai/specfact-codebase"]
    )
    _register_candidates(monkeypatch, [rejected, consumer, provider])
    _assert_active([consumer, provider], [rejected])
    assert CommandRegistry.get_module_metadata("code") is not None
    assert CommandRegistry.get_module_metadata("spec") is not None


def test_conflict_refusal_has_explicit_registration_diagnostic(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    selection_key: Ed25519PrivateKey,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Observe actual logging while the public conflict control proves refusal and unrelated survival."""
    logger = logging.getLogger("tests.registration.conflict-refusal")
    monkeypatch.setattr(packages, "get_bridge_logger", lambda _name: logger)
    with caplog.at_level(logging.WARNING):
        _exercise_conflict(monkeypatch, tmp_path, selection_key)
    assert any(
        record.name == logger.name
        and record.levelno == logging.WARNING
        and record.getMessage()
        == "Refusing conflicting module dependency selection: nold-ai/specfact-codebase, nold-ai/specfact-spec"
        for record in caplog.records
    ), "Refusing a contradictory priority set must emit the explicit registration diagnostic"

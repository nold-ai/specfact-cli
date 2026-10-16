"""Public registration selects an eligible signed same-name installation before effects."""

import base64
import hashlib
import os
import sys
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest
import yaml
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from typer.testing import CliRunner

from specfact_cli.registry import CommandRegistry, module_installer, module_packages as packages
from tests.unit.security.test_module_command_squatting import _reset_registration
from tests.unit.security.test_project_bundle_authority import _isolate_discovery_roots


def _signed_copy(parent: Path, key: Ed25519PrivateKey, failure: str | None, **changes: Any) -> Path:
    """Sign a harmless bundle with the test trust anchor after declaring actual compatibility inputs."""
    if parent.name != "modules" or parent.parent.name != ".specfact":
        parent = parent / ".specfact/modules"
    package = parent / "specfact-codebase"
    (package / "src").mkdir(parents=True)
    (package / "src/app.py").write_text(
        "import typer\napp = typer.Typer()\n@app.callback()\ndef root(): pass\n"
        "@app.command()\ndef probe(): typer.echo('eligible-installed-copy')\n",
        encoding="utf-8",
    )
    raw: dict[str, Any] = {
        "name": "nold-ai/specfact-codebase",
        "version": "1.0.0",
        "commands": ["code"],
        "category": "codebase",
        "bundle": "specfact-codebase",
        "bundle_group_command": "code",
        "tier": "official",
        "publisher": {"name": "nold-ai", "email": "fixture@example.invalid"},
    }
    if failure == "core":
        raw["core_compatibility"] = "<0.1"
    elif failure == "schema":
        raw["schema_version"] = "incompatible-fixture-schema"
    elif failure == "dependency":
        raw["module_dependencies"] = ["fixture/missing-provider"]
    raw.update(changes)
    manifest = package / "module-package.yaml"
    manifest.write_text(yaml.safe_dump(raw), encoding="utf-8")
    payload = module_installer._module_artifact_payload_signed(package)
    raw["integrity"] = {
        "checksum": "sha256:" + hashlib.sha256(payload).hexdigest(),
        "signature": base64.b64encode(key.sign(payload)).decode("ascii"),
    }
    manifest.write_text(yaml.safe_dump(raw), encoding="utf-8")
    return package


@pytest.mark.parametrize("grouped", [True, False], ids=["grouped", "legacy"])
@pytest.mark.parametrize("failure", ["core", "schema", "dependency"])
def test_signed_ineligible_project_preserves_eligible_installed_copy(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, grouped: bool, failure: str
) -> None:
    """Use actual discovery and crypto, then observe installed activation and its public command."""
    monkeypatch.setattr(sys, "dont_write_bytecode", True)
    key = Ed25519PrivateKey.generate()
    public_key = key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    key_file = tmp_path / "fixture-public.pem"
    key_file.write_bytes(public_key)
    monkeypatch.setattr(module_installer, "_bundled_public_key_path", lambda: key_file)
    project = _signed_copy(tmp_path / "workspace/.specfact/modules", key, failure)
    installed = _signed_copy(tmp_path / "user", key, None)
    _isolate_discovery_roots(monkeypatch, tmp_path / "workspace", installed.parent)
    for path, source in ((project, "project"), (installed, "user")):
        metadata = packages.discover_package_metadata(path.parent, source=source)[0][1]
        assert module_installer.verify_module_artifact(
            path, metadata, public_key_pem=public_key.decode(), allow_unsigned=False, require_signature=True
        )
    _reset_registration()
    try:
        packages.register_module_package_commands(allow_unsigned=False, category_grouping_enabled=grouped)
        assert (installed / "src").resolve() in packages._ACTIVE_MODULE_SRC_DIRS, (
            "An ineligible signed project copy suppressed its eligible same-name installation"
        )
        assert (project / "src").resolve() not in packages._ACTIVE_MODULE_SRC_DIRS
        app = CommandRegistry.get_module_typer("code")
        assert app is not None
        result = CliRunner().invoke(app, ["probe"])
        assert result.exit_code == 0, result.output
        assert "eligible-installed-copy" in result.output
    finally:
        _reset_registration()


@pytest.fixture
def selection_key(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Generator[Ed25519PrivateKey, None, None]:
    """Use a real test trust anchor while retaining production verification decisions."""
    monkeypatch.setattr(sys, "dont_write_bytecode", True)
    key = Ed25519PrivateKey.generate()
    public = tmp_path / "selection-public.pem"
    public.write_bytes(
        key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    )
    monkeypatch.setattr(module_installer, "_bundled_public_key_path", lambda: public)
    monkeypatch.setattr(packages, "get_modules_root", lambda: tmp_path / "missing-builtin")
    monkeypatch.setattr(packages, "read_modules_state", dict)
    _reset_registration()
    yield key
    _reset_registration()


def _register_candidates(monkeypatch: pytest.MonkeyPatch, paths: list[Path]) -> None:
    """Discover actual configured installations in priority order through the public entry point."""
    workspace = paths[0].parents[3] / "empty-workspace"
    workspace.mkdir(exist_ok=True)
    _isolate_discovery_roots(monkeypatch, workspace, workspace / "missing-user")
    roots = dict.fromkeys(str(path.parent) for path in paths)
    monkeypatch.setenv("SPECFACT_MODULES_ROOTS", os.pathsep.join(roots))
    packages.register_module_package_commands(allow_unsigned=False)


def _assert_active(paths: list[Path], rejected: list[Path]) -> None:
    """Inspect exact activated sources instead of trusting a provisional metadata selection."""
    active = set(packages._ACTIVE_MODULE_SRC_DIRS)
    assert all((path / "src").resolve() in active for path in paths), "Eligible copies were suppressed"
    assert all((path / "src").resolve() not in active for path in rejected), "Rejected copies gained import authority"


def _provider(parent: Path, key: Ed25519PrivateKey, version: str, failure: str | None = None, **changes: Any) -> Path:
    """Author a distinct signed spec provider with actual declared version constraints."""
    return _signed_copy(
        parent,
        key,
        failure,
        name="nold-ai/specfact-spec",
        version=version,
        category="spec",
        bundle="specfact-spec",
        bundle_group_command="spec",
        commands=["spec"],
        **changes,
    )


def test_integrity_rejected_user_copy_keeps_signed_fallback(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, selection_key: Ed25519PrivateKey
) -> None:
    """Ordinary integrity failure must not consume a name before the next signed copy is tested."""
    invalid = _signed_copy(tmp_path / "invalid", selection_key, None)
    valid = _signed_copy(tmp_path / "valid", selection_key, None)
    (invalid / "src/app.py").write_text("TAMPERED = True\n", encoding="utf-8")
    _register_candidates(monkeypatch, [invalid, valid])
    _assert_active([valid], [invalid])


def test_dependency_selection_reconsiders_higher_priority_consumer(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, selection_key: Ed25519PrivateKey
) -> None:
    """A provider fallback can restore the first consumer that needs its actual version."""
    dependency = [{"name": "nold-ai/specfact-spec", "version_specifier": ">=2"}]
    consumer = _signed_copy(tmp_path / "a1", selection_key, None, module_dependencies_versioned=dependency)
    fallback = _signed_copy(tmp_path / "a2", selection_key, None, version="2.0.0")
    old = _provider(tmp_path / "b1", selection_key, "1.0.0", "dependency")
    current = _provider(tmp_path / "b2", selection_key, "2.0.0")
    _register_candidates(monkeypatch, [consumer, fallback, old, current])
    _assert_active([consumer, current], [fallback, old])


def test_rejected_provider_cannot_satisfy_consumer_dependencies(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, selection_key: Ed25519PrivateKey
) -> None:
    """A provider that cannot load contributes neither existence nor versions or mounts."""
    provider = _provider(tmp_path / "provider", selection_key, "1.0.0", "core")
    consumer = _signed_copy(tmp_path / "consumer", selection_key, None, module_dependencies=["nold-ai/specfact-spec"])
    _register_candidates(monkeypatch, [consumer, provider])
    _assert_active([], [consumer, provider])
    assert CommandRegistry.get_metadata("spec") is None, "Rejected provider created a category mount"


def test_consistent_dependency_cycle_keeps_commands(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, selection_key: Ed25519PrivateKey
) -> None:
    """Existing consistent edge-local dependencies remain compatible rather than being erased by ordering."""
    consumer = _signed_copy(tmp_path / "a", selection_key, None, module_dependencies=["nold-ai/specfact-spec"])
    provider = _provider(tmp_path / "b", selection_key, "1.0.0", module_dependencies=["nold-ai/specfact-codebase"])
    _register_candidates(monkeypatch, [consumer, provider])
    _assert_active([consumer, provider], [])


def test_conflicting_dependency_cycle_refuses_only_unstable_component(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, selection_key: Ed25519PrivateKey
) -> None:
    """Actual incompatible priority selections terminate before effects while an unrelated module survives."""
    consumers = [
        _signed_copy(
            tmp_path / folder,
            selection_key,
            None,
            version=version,
            module_dependencies_versioned=[{"name": "nold-ai/specfact-spec", "version_specifier": constraint}],
        )
        for folder, version, constraint in (("a1", "1.0.0", ">=2"), ("a2", "2.0.0", "<2"))
    ]
    providers = [
        _provider(
            tmp_path / folder,
            selection_key,
            version,
            module_dependencies_versioned=[{"name": "nold-ai/specfact-codebase", "version_specifier": constraint}],
        )
        for folder, version, constraint in (("b1", "1.0.0", "<2"), ("b2", "2.0.0", ">=2"))
    ]
    unrelated = _signed_copy(
        tmp_path / "unrelated",
        selection_key,
        None,
        name="fixture/independent",
        category=None,
        bundle=None,
        bundle_group_command=None,
        commands=["independent"],
    )
    _register_candidates(monkeypatch, [*consumers, *providers, unrelated])
    _assert_active([unrelated], consumers + providers)
    assert CommandRegistry.get_metadata("code") is None
    assert CommandRegistry.get_metadata("spec") is None


def test_final_revalidation_rejects_payload_changed_after_initial_check(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, selection_key: Ed25519PrivateKey
) -> None:
    """Observe an actual successful signature check, then deny the changed copy before activation."""
    changed = _signed_copy(tmp_path / "changed", selection_key, None)
    fallback = _signed_copy(tmp_path / "fallback", selection_key, None)
    actual_verify = packages.verify_module_artifact
    mutated = False

    def observe_verified_payload(path: Path, metadata: packages.ModulePackageMetadata, **kwargs: Any) -> bool:
        nonlocal mutated
        valid = actual_verify(path, metadata, **kwargs)
        if path == changed and valid and not mutated:
            mutated = True
            (path / "src/app.py").write_text("UNSIGNED_AFTER_VERIFICATION = True\n", encoding="utf-8")
        return valid

    monkeypatch.setattr(packages, "verify_module_artifact", observe_verified_payload)
    _register_candidates(monkeypatch, [changed, fallback])
    assert mutated, "The observer must follow a genuine successful verifier decision"
    _assert_active([fallback], [changed])


def test_versioned_self_dependency_selects_eligible_fallback(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, selection_key: Ed25519PrivateKey
) -> None:
    """Use each real signed candidate's own version for a declared self-dependency."""
    dependency = [{"name": "nold-ai/specfact-codebase", "version_specifier": ">=2"}]
    invalid = _signed_copy(tmp_path / "v1", selection_key, None, module_dependencies_versioned=dependency)
    valid = _signed_copy(
        tmp_path / "v2", selection_key, None, version="2.0.0", module_dependencies_versioned=dependency
    )
    _register_candidates(monkeypatch, [invalid, valid])
    _assert_active([valid], [invalid])

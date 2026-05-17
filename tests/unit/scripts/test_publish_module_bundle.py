"""Tests for publish-module.py bundle publishing mode."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import tarfile
from pathlib import Path

import pytest


SCRIPT_PATH = Path(__file__).resolve().parents[3] / "scripts" / "publish-module.py"
TEST_KEY_PATH = Path(__file__).resolve().parents[2] / "fixtures" / "keys" / "test_private_key.pem"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("publish_module_script", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load publish-module.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _create_bundle_package(tmp_path: Path, bundle_name: str, version: str = "0.39.0") -> Path:
    bundle_dir = tmp_path / "packages" / bundle_name
    src_dir = bundle_dir / "src" / bundle_name.replace("-", "_")
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "__init__.py").write_text("__all__ = []\n", encoding="utf-8")
    manifest = bundle_dir / "module-package.yaml"
    manifest.write_text(
        "\n".join(
            [
                f"name: nold-ai/{bundle_name}",
                f"version: {version}",
                "commands: [bundle]",
                "tier: official",
                "publisher: nold-ai",
                "bundle_dependencies: []",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return bundle_dir


def _write_test_key(target_path: Path) -> Path:
    target_path.write_text(TEST_KEY_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    return target_path


def _init_registry_layout(tmp_path: Path) -> Path:
    registry_dir = tmp_path / "registry"
    (registry_dir / "modules").mkdir(parents=True, exist_ok=True)
    (registry_dir / "signatures").mkdir(parents=True, exist_ok=True)
    (registry_dir / "index.json").write_text(json.dumps({"modules": []}, indent=2) + "\n", encoding="utf-8")
    return registry_dir


def test_publish_bundle_creates_tarball_in_registry_modules(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_script_module()
    packages_root = tmp_path / "packages"
    _create_bundle_package(tmp_path, "specfact-codebase")
    registry_dir = _init_registry_layout(tmp_path)
    key_file = _write_test_key(tmp_path / "private.pem")

    monkeypatch.setattr(module, "BUNDLE_PACKAGES_ROOT", packages_root)
    monkeypatch.setattr(
        module, "sign_bundle", lambda tarball, key_file, registry_dir: registry_dir / "signatures" / "x.sig"
    )
    monkeypatch.setattr(module, "verify_bundle", lambda *args, **kwargs: True)

    module.publish_bundle("specfact-codebase", key_file, registry_dir)

    tarballs = list((registry_dir / "modules").glob("specfact-codebase-*.tar.gz"))
    assert len(tarballs) == 1


def test_tarball_checksum_matches_generated_index_entry(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_script_module()
    packages_root = tmp_path / "packages"
    _create_bundle_package(tmp_path, "specfact-codebase")
    registry_dir = _init_registry_layout(tmp_path)
    key_file = _write_test_key(tmp_path / "private.pem")

    monkeypatch.setattr(module, "BUNDLE_PACKAGES_ROOT", packages_root)
    monkeypatch.setattr(
        module, "sign_bundle", lambda tarball, key_file, registry_dir: registry_dir / "signatures" / "x.sig"
    )
    monkeypatch.setattr(module, "verify_bundle", lambda *args, **kwargs: True)

    module.publish_bundle("specfact-codebase", key_file, registry_dir)

    index = json.loads((registry_dir / "index.json").read_text(encoding="utf-8"))
    entry = index["modules"][0]
    tarball = registry_dir / "modules" / Path(entry["download_url"]).name
    checksum = hashlib.sha256(tarball.read_bytes()).hexdigest()
    assert checksum == entry["checksum_sha256"]


def test_publish_entry_serializes_bundle_dependency_objects_as_ids() -> None:
    module = _load_script_module()

    entry = module._build_publish_entry(
        {
            "bundle_dependencies": [
                "nold-ai/specfact-project",
                {"id": "nold-ai/specfact-codebase", "version": ">=0.41.0"},
            ]
        },
        "nold-ai/specfact-review",
        "0.47.0",
        Path("specfact-review-0.47.0.tar.gz"),
        "abc123",
    )

    assert entry["bundle_dependencies"] == ["nold-ai/specfact-project", "nold-ai/specfact-codebase"]


def test_publish_entry_rejects_malformed_bundle_dependency_object() -> None:
    module = _load_script_module()

    with pytest.raises(ValueError, match="non-empty 'id'"):
        module._build_publish_entry(
            {
                "bundle_dependencies": [
                    {"version": "1.0"},
                ]
            },
            "nold-ai/specfact-review",
            "0.47.0",
            Path("specfact-review-0.47.0.tar.gz"),
            "abc123",
        )

    with pytest.raises(ValueError, match="non-empty 'id'"):
        module._build_publish_entry(
            {
                "bundle_dependencies": [
                    {"id": ""},
                ]
            },
            "nold-ai/specfact-review",
            "0.47.0",
            Path("specfact-review-0.47.0.tar.gz"),
            "abc123",
        )


def test_publish_entry_rejects_non_string_bundle_dependency_ids() -> None:
    module = _load_script_module()

    with pytest.raises(ValueError, match=r"id'.*str"):
        module._build_publish_entry(
            {
                "bundle_dependencies": [
                    {"id": 123},
                ]
            },
            "nold-ai/specfact-review",
            "0.47.0",
            Path("specfact-review-0.47.0.tar.gz"),
            "abc123",
        )

    with pytest.raises(ValueError, match="entries must be strings"):
        module._build_publish_entry(
            {
                "bundle_dependencies": [123],
            },
            "nold-ai/specfact-review",
            "0.47.0",
            Path("specfact-review-0.47.0.tar.gz"),
            "abc123",
        )

    with pytest.raises(ValueError, match="string entries must be non-empty"):
        module._build_publish_entry(
            {
                "bundle_dependencies": [" "],
            },
            "nold-ai/specfact-review",
            "0.47.0",
            Path("specfact-review-0.47.0.tar.gz"),
            "abc123",
        )


def test_tarball_has_no_path_traversal_entries(tmp_path: Path) -> None:
    module = _load_script_module()
    bundle_dir = _create_bundle_package(tmp_path, "specfact-codebase")
    tarball = module.package_bundle(bundle_dir)

    with tarfile.open(tarball, "r:gz") as archive:
        for member in archive.getmembers():
            assert ".." not in member.name
            assert not Path(member.name).is_absolute()


def test_signature_file_created_in_registry_signatures(tmp_path: Path) -> None:
    module = _load_script_module()
    tarball = tmp_path / "sample.tar.gz"
    tarball.write_bytes(b"content")
    key_file = _write_test_key(tmp_path / "private.pem")
    registry_dir = _init_registry_layout(tmp_path)

    signature_path = module.sign_bundle(tarball, key_file, registry_dir)
    assert signature_path.exists()
    assert signature_path.parent == registry_dir / "signatures"


def test_inline_verification_runs_before_index_write(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_script_module()
    packages_root = tmp_path / "packages"
    _create_bundle_package(tmp_path, "specfact-codebase")
    registry_dir = _init_registry_layout(tmp_path)
    key_file = _write_test_key(tmp_path / "private.pem")

    monkeypatch.setattr(module, "BUNDLE_PACKAGES_ROOT", packages_root)
    monkeypatch.setattr(
        module, "sign_bundle", lambda tarball, key_file, registry_dir: registry_dir / "signatures" / "x.sig"
    )
    monkeypatch.setattr(module, "verify_bundle", lambda *args, **kwargs: True)

    module.publish_bundle("specfact-codebase", key_file, registry_dir)
    assert json.loads((registry_dir / "index.json").read_text(encoding="utf-8"))["modules"]


def test_inline_verification_failure_does_not_modify_index(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_script_module()
    packages_root = tmp_path / "packages"
    _create_bundle_package(tmp_path, "specfact-codebase")
    registry_dir = _init_registry_layout(tmp_path)
    key_file = _write_test_key(tmp_path / "private.pem")

    monkeypatch.setattr(module, "BUNDLE_PACKAGES_ROOT", packages_root)
    monkeypatch.setattr(
        module, "sign_bundle", lambda tarball, key_file, registry_dir: registry_dir / "signatures" / "x.sig"
    )
    monkeypatch.setattr(module, "verify_bundle", lambda *args, **kwargs: False)

    with pytest.raises(ValueError, match="verification"):
        module.publish_bundle("specfact-codebase", key_file, registry_dir)
    assert json.loads((registry_dir / "index.json").read_text(encoding="utf-8"))["modules"] == []


def test_index_write_is_atomic_via_os_replace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_script_module()
    index_path = tmp_path / "index.json"
    index_path.write_text(json.dumps({"modules": []}), encoding="utf-8")
    replaced: list[tuple[str, str]] = []

    def _replace(src: str | os.PathLike[str], dst: str | os.PathLike[str]) -> None:
        replaced.append((str(src), str(dst)))
        Path(dst).write_text(Path(src).read_text(encoding="utf-8"), encoding="utf-8")

    monkeypatch.setattr(module.os, "replace", _replace)
    module.write_index_entry(
        index_path,
        {
            "id": "nold-ai/specfact-codebase",
            "latest_version": "0.39.0",
            "download_url": "modules/specfact-codebase-0.39.0.tar.gz",
            "checksum_sha256": "abc",
        },
    )
    assert replaced


def test_publish_bundle_rejects_same_version_as_existing_latest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_script_module()
    packages_root = tmp_path / "packages"
    _create_bundle_package(tmp_path, "specfact-codebase", version="0.39.0")
    registry_dir = _init_registry_layout(tmp_path)
    key_file = _write_test_key(tmp_path / "private.pem")

    existing = {
        "id": "nold-ai/specfact-codebase",
        "latest_version": "0.39.0",
        "download_url": "modules/specfact-codebase-0.39.0.tar.gz",
        "checksum_sha256": "deadbeef",
    }
    (registry_dir / "index.json").write_text(json.dumps({"modules": [existing]}, indent=2), encoding="utf-8")
    monkeypatch.setattr(module, "BUNDLE_PACKAGES_ROOT", packages_root)

    with pytest.raises(ValueError, match=r"same version|downgrade|latest"):
        module.publish_bundle("specfact-codebase", key_file, registry_dir)


def test_bundle_all_flag_publishes_all_five_bundles_in_sequence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_script_module()
    called: list[str] = []
    key_file = _write_test_key(tmp_path / "private.pem")
    registry_dir = _init_registry_layout(tmp_path)

    monkeypatch.setattr(
        module, "publish_bundle", lambda name, key_file, registry_dir, bump_version=None, **kwargs: called.append(name)
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "publish-module.py",
            "--bundle",
            "all",
            "--key-file",
            str(key_file),
            "--registry-dir",
            str(registry_dir),
        ],
    )

    exit_code = module.main()
    assert exit_code == 0
    assert called == [
        "specfact-project",
        "specfact-backlog",
        "specfact-codebase",
        "specfact-spec",
        "specfact-govern",
    ]

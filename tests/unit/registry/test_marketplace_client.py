"""Tests for marketplace registry client."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from specfact_cli.registry.marketplace_client import (
    REGISTRY_BASE_URL,
    SecurityError,
    download_module,
    fetch_registry_index,
    get_modules_branch,
    get_registry_index_url,
    resolve_download_url,
)


def test_get_modules_branch_detached_head_uses_ci_main_ref(monkeypatch: pytest.MonkeyPatch) -> None:
    """Detached HEAD in CI should still resolve main registry when CI ref is main."""
    get_modules_branch.cache_clear()

    class _Result:
        returncode = 0
        stdout = "HEAD\n"

    try:
        monkeypatch.delenv("SPECFACT_MODULES_BRANCH", raising=False)
        monkeypatch.delenv("GITHUB_HEAD_REF", raising=False)
        monkeypatch.delenv("GITHUB_BASE_REF", raising=False)
        monkeypatch.delenv("GITHUB_REF", raising=False)
        monkeypatch.setenv("GITHUB_REF_NAME", "main")
        monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: _Result())
        assert get_modules_branch() == "main"
    finally:
        get_modules_branch.cache_clear()


def test_get_modules_branch_detached_head_uses_ci_dev_ref(monkeypatch: pytest.MonkeyPatch) -> None:
    """Detached HEAD in CI should resolve dev registry when CI refs are non-main."""
    get_modules_branch.cache_clear()

    class _Result:
        returncode = 0
        stdout = "HEAD\n"

    try:
        monkeypatch.delenv("SPECFACT_MODULES_BRANCH", raising=False)
        monkeypatch.setenv("GITHUB_HEAD_REF", "feature/something")
        monkeypatch.setenv("GITHUB_BASE_REF", "dev")
        monkeypatch.setenv("GITHUB_REF_NAME", "main")
        monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: _Result())
        assert get_modules_branch() == "dev"
    finally:
        get_modules_branch.cache_clear()


def test_get_modules_branch_env_main(monkeypatch: pytest.MonkeyPatch) -> None:
    """SPECFACT_MODULES_BRANCH=main forces main branch."""
    get_modules_branch.cache_clear()
    try:
        monkeypatch.setenv("SPECFACT_MODULES_BRANCH", "main")
        assert get_modules_branch() == "main"
    finally:
        get_modules_branch.cache_clear()


def test_get_modules_branch_env_dev(monkeypatch: pytest.MonkeyPatch) -> None:
    """SPECFACT_MODULES_BRANCH=dev forces dev branch."""
    get_modules_branch.cache_clear()
    try:
        monkeypatch.setenv("SPECFACT_MODULES_BRANCH", "dev")
        assert get_modules_branch() == "dev"
    finally:
        get_modules_branch.cache_clear()


def test_get_registry_index_url_uses_branch(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_registry_index_url returns dev or main URL per branch."""
    get_modules_branch.cache_clear()
    try:
        monkeypatch.setenv("SPECFACT_MODULES_BRANCH", "dev")
        url = get_registry_index_url()
        assert "/dev/registry/index.json" in url
        monkeypatch.setenv("SPECFACT_MODULES_BRANCH", "main")
        get_modules_branch.cache_clear()
        url = get_registry_index_url()
        assert "/main/registry/index.json" in url
    finally:
        get_modules_branch.cache_clear()


def test_resolve_download_url_absolute_unchanged() -> None:
    """Absolute download_url is returned as-is."""
    entry: dict[str, object] = {"download_url": "https://cdn.example/modules/foo-0.1.0.tar.gz"}
    index: dict[str, object] = {}
    assert resolve_download_url(entry, index) == "https://cdn.example/modules/foo-0.1.0.tar.gz"


def test_resolve_download_url_relative_uses_registry_base(monkeypatch: pytest.MonkeyPatch) -> None:
    """Relative download_url is resolved against branch-aware registry base when index has no base."""
    monkeypatch.setenv("SPECFACT_MODULES_BRANCH", "main")
    get_modules_branch.cache_clear()
    try:
        entry: dict[str, object] = {"download_url": "modules/specfact-backlog-0.1.0.tar.gz"}
        index: dict[str, object] = {}
        got = resolve_download_url(entry, index)
        assert got == f"{REGISTRY_BASE_URL}/modules/specfact-backlog-0.1.0.tar.gz"
    finally:
        get_modules_branch.cache_clear()


def test_resolve_download_url_relative_uses_index_base() -> None:
    """Relative download_url uses index registry_base_url when set."""
    entry: dict[str, object] = {"download_url": "modules/bar-0.2.0.tar.gz"}
    index: dict[str, object] = {"registry_base_url": "https://custom.registry/registry"}
    assert resolve_download_url(entry, index) == "https://custom.registry/registry/modules/bar-0.2.0.tar.gz"


class _DummyResponse:
    def __init__(self, status_code: int = 200, text: str = "", content: bytes = b"") -> None:
        self.status_code = status_code
        self.text = text
        self.content = content

    def json(self) -> dict:
        return json.loads(self.text)

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"http {self.status_code}")


def test_fetch_registry_index_parses_valid_json(monkeypatch) -> None:
    payload = {"schema_version": "1.0.0", "modules": []}

    def fake_get(*_args, **_kwargs):
        return _DummyResponse(status_code=200, text=json.dumps(payload))

    monkeypatch.setattr("specfact_cli.registry.marketplace_client.requests.get", fake_get)

    index = fetch_registry_index()
    assert index is not None
    assert index["schema_version"] == "1.0.0"


def test_fetch_registry_index_network_unavailable_returns_none(monkeypatch) -> None:
    def fake_get(*_args, **_kwargs):
        raise OSError("network down")

    monkeypatch.setattr("specfact_cli.registry.marketplace_client.requests.get", fake_get)

    assert fetch_registry_index() is None


def test_fetch_registry_index_invalid_json_raises_value_error(monkeypatch) -> None:
    def fake_get(*_args, **_kwargs):
        return _DummyResponse(status_code=200, text="{invalid")

    monkeypatch.setattr("specfact_cli.registry.marketplace_client.requests.get", fake_get)

    with pytest.raises(ValueError, match="Invalid registry index format"):
        fetch_registry_index()


def test_download_module_downloads_tarball_and_verifies_checksum(monkeypatch, tmp_path: Path) -> None:
    module_bytes = b"module-tarball-bytes"
    checksum = hashlib.sha256(module_bytes).hexdigest()
    index = {
        "schema_version": "1.0.0",
        "modules": [
            {
                "id": "specfact/backlog",
                "namespace": "specfact",
                "name": "backlog",
                "description": "Backlog module",
                "latest_version": "0.1.0",
                "core_compatibility": ">=0.1.0,<1.0.0",
                "download_url": "https://example.test/specfact-backlog-0.1.0.tar.gz",
                "checksum_sha256": checksum,
            }
        ],
    }

    monkeypatch.setattr(
        "specfact_cli.registry.marketplace_client.fetch_registry_index", lambda *_args, **_kwargs: index
    )

    def fake_get(*_args, **_kwargs):
        return _DummyResponse(status_code=200, content=module_bytes)

    monkeypatch.setattr("specfact_cli.registry.marketplace_client.requests.get", fake_get)

    tarball_path = download_module("specfact/backlog", download_dir=tmp_path)
    assert tarball_path.exists()
    assert tarball_path.read_bytes() == module_bytes


def test_download_module_checksum_mismatch_raises_security_error(monkeypatch, tmp_path: Path) -> None:
    index = {
        "schema_version": "1.0.0",
        "modules": [
            {
                "id": "specfact/backlog",
                "namespace": "specfact",
                "name": "backlog",
                "description": "Backlog module",
                "latest_version": "0.1.0",
                "core_compatibility": ">=0.1.0,<1.0.0",
                "download_url": "https://example.test/specfact-backlog-0.1.0.tar.gz",
                "checksum_sha256": "0" * 64,
            }
        ],
    }

    monkeypatch.setattr(
        "specfact_cli.registry.marketplace_client.fetch_registry_index", lambda *_args, **_kwargs: index
    )

    def fake_get(*_args, **_kwargs):
        return _DummyResponse(status_code=200, content=b"tampered")

    monkeypatch.setattr("specfact_cli.registry.marketplace_client.requests.get", fake_get)

    with pytest.raises(SecurityError, match="Checksum mismatch"):
        download_module("specfact/backlog", download_dir=tmp_path)

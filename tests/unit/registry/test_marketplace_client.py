"""Tests for marketplace registry client."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from specfact_cli.registry.marketplace_client import SecurityError, download_module, fetch_registry_index


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

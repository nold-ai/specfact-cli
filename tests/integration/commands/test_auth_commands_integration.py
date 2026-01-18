"""Integration tests for auth commands."""

from __future__ import annotations

import sys
import time
import types
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests
from typer.testing import CliRunner

from specfact_cli.cli import app
from specfact_cli.commands.auth import AZURE_DEVOPS_RESOURCE
from specfact_cli.utils.auth_tokens import load_tokens


runner = CliRunner()


class _FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload
        self.status_code = 200

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self._payload


def _set_home(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))


def test_github_device_flow_integration(tmp_path: Path, monkeypatch) -> None:
    _set_home(tmp_path, monkeypatch)
    calls: list[tuple[str, dict[str, Any] | None]] = []

    def fake_post(url: str, data: dict[str, Any] | None = None, **_kwargs):
        if data is None:
            raise AssertionError("Expected request data payload")
        calls.append((url, data))
        if url.endswith("/login/device/code"):
            return _FakeResponse(
                {
                    "device_code": "device-code-123",
                    "user_code": "ABCD-EFGH",
                    "verification_uri": "https://github.com/login/device",
                    "expires_in": 900,
                    "interval": 1,
                }
            )
        if url.endswith("/login/oauth/access_token"):
            return _FakeResponse(
                {
                    "access_token": "gh-token-123",
                    "token_type": "bearer",
                    "scope": "repo",
                }
            )
        raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr(requests, "post", fake_post)

    result = runner.invoke(
        app,
        [
            "auth",
            "github",
            "--client-id",
            "client-123",
            "--base-url",
            "https://ghe.example/api/v3",
        ],
    )

    assert result.exit_code == 0
    assert len(calls) == 2
    assert calls[0][0] == "https://ghe.example/login/device/code"
    assert calls[1][0] == "https://ghe.example/login/oauth/access_token"

    tokens = load_tokens()
    github_token = tokens["github"]
    assert github_token["access_token"] == "gh-token-123"
    assert github_token["base_url"] == "https://ghe.example"
    assert github_token["api_base_url"] == "https://ghe.example/api/v3"


def test_github_enterprise_requires_client_id(tmp_path: Path, monkeypatch) -> None:
    _set_home(tmp_path, monkeypatch)

    result = runner.invoke(
        app,
        [
            "auth",
            "github",
            "--base-url",
            "https://github.example.com",
        ],
    )

    assert result.exit_code != 0
    assert "requires a client id" in result.stdout.lower()


def test_azure_devops_device_flow_integration(tmp_path: Path, monkeypatch) -> None:
    _set_home(tmp_path, monkeypatch)
    prompt_called = {"value": False}

    class FakeToken:
        def __init__(self, token: str, expires_on: int) -> None:
            self.token = token
            self.expires_on = expires_on

    class FakeDeviceCodeCredential:
        def __init__(self, prompt_callback) -> None:
            self._prompt_callback = prompt_callback

        def get_token(self, resource: str) -> FakeToken:
            prompt_called["value"] = True
            self._prompt_callback("https://microsoft.com/devicelogin", "CODE-123", datetime.now(tz=UTC))
            return FakeToken("ado-token-456", int(time.time()) + 3600)

    azure_mod = types.ModuleType("azure")
    identity_mod = types.ModuleType("azure.identity")
    identity_mod.DeviceCodeCredential = FakeDeviceCodeCredential
    azure_mod.identity = identity_mod
    monkeypatch.setitem(sys.modules, "azure", azure_mod)
    monkeypatch.setitem(sys.modules, "azure.identity", identity_mod)

    result = runner.invoke(app, ["auth", "azure-devops"])

    assert result.exit_code == 0
    assert prompt_called["value"]

    tokens = load_tokens()
    ado_token = tokens["azure-devops"]
    assert ado_token["access_token"] == "ado-token-456"
    assert ado_token["resource"] == AZURE_DEVOPS_RESOURCE
    assert "expires_at" in ado_token

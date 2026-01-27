"""E2E tests for auth command flows."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import requests
from typer.testing import CliRunner

from specfact_cli.cli import app
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


def test_github_auth_status_and_clear_e2e(tmp_path: Path, monkeypatch) -> None:
    _set_home(tmp_path, monkeypatch)

    def fake_post(url: str, data: dict[str, Any] | None = None, **_kwargs):
        if data is None:
            raise AssertionError("Expected request data payload")
        if url.endswith("/login/device/code"):
            return _FakeResponse(
                {
                    "device_code": "device-code-xyz",
                    "user_code": "WXYZ-1234",
                    "verification_uri": "https://github.com/login/device",
                    "expires_in": 900,
                    "interval": 1,
                }
            )
        if url.endswith("/login/oauth/access_token"):
            return _FakeResponse(
                {
                    "access_token": "gh-token-xyz",
                    "token_type": "bearer",
                    "scope": "repo",
                }
            )
        raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr(requests, "post", fake_post)

    auth_result = runner.invoke(app, ["--skip-checks", "auth", "github", "--client-id", "client-xyz"])
    assert auth_result.exit_code == 0

    status_result = runner.invoke(app, ["--skip-checks", "auth", "status"])
    assert status_result.exit_code == 0
    # Use result.output which contains all printed output (combined stdout and stderr)
    assert "github" in status_result.output.lower()

    clear_result = runner.invoke(app, ["auth", "clear"])
    assert clear_result.exit_code == 0
    assert load_tokens() == {}

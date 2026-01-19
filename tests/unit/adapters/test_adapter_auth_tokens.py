"""Tests for adapter token resolution from stored credentials."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from specfact_cli.adapters.ado import AdoAdapter
from specfact_cli.adapters.github import GitHubAdapter
from specfact_cli.utils.auth_tokens import save_tokens


def _set_home(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))


def test_github_adapter_uses_stored_token_and_api_base(tmp_path: Path, monkeypatch) -> None:
    _set_home(tmp_path, monkeypatch)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    save_tokens(
        {
            "github": {
                "access_token": "stored-gh",
                "api_base_url": "https://ghe.example.com/api/v3",
            }
        }
    )

    adapter = GitHubAdapter(api_token=None, use_gh_cli=False)
    assert adapter.api_token == "stored-gh"
    assert adapter.base_url == "https://ghe.example.com/api/v3"


def test_ado_adapter_uses_stored_token(tmp_path: Path, monkeypatch) -> None:
    _set_home(tmp_path, monkeypatch)
    monkeypatch.delenv("AZURE_DEVOPS_TOKEN", raising=False)

    expires_at = (datetime.now(tz=UTC) + timedelta(hours=1)).isoformat()
    save_tokens({"azure-devops": {"access_token": "stored-ado", "expires_at": expires_at, "token_type": "bearer"}})

    adapter = AdoAdapter(api_token=None)
    assert adapter.api_token == "stored-ado"
    assert adapter._auth_headers().get("Authorization") == "Bearer stored-ado"

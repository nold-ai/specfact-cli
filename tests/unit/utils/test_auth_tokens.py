"""Unit tests for auth token utilities."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

from specfact_cli.utils.auth_tokens import (
    clear_all_tokens,
    get_token,
    load_tokens,
    save_tokens,
    token_is_expired,
)


def _set_home(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))


def test_save_and_load_tokens(tmp_path: Path, monkeypatch) -> None:
    _set_home(tmp_path, monkeypatch)
    tokens = {"github": {"access_token": "token-123", "token_type": "bearer"}}

    save_tokens(tokens)

    loaded = load_tokens()
    assert loaded["github"]["access_token"] == "token-123"

    token_path = tmp_path / ".specfact" / "tokens.json"
    assert token_path.exists()

    if os.name == "posix":
        assert oct(token_path.stat().st_mode & 0o777) == "0o600"


def test_token_expiry_handling(tmp_path: Path, monkeypatch) -> None:
    _set_home(tmp_path, monkeypatch)
    expired_at = (datetime.now(tz=UTC) - timedelta(hours=1)).isoformat()
    valid_at = (datetime.now(tz=UTC) + timedelta(hours=1)).isoformat()

    assert token_is_expired({"expires_at": expired_at}) is True
    assert token_is_expired({"expires_at": valid_at}) is False

    save_tokens({"azure-devops": {"access_token": "ado", "expires_at": expired_at}})

    assert get_token("azure-devops") is None
    assert get_token("azure-devops", allow_expired=True) is not None

    clear_all_tokens()
    assert load_tokens() == {}

"""Unit tests for auth CLI commands."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from specfact_cli.cli import app
from specfact_cli.utils.auth_tokens import load_tokens, save_tokens


runner = CliRunner()


def _set_home(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))


def test_auth_status_shows_tokens(tmp_path: Path, monkeypatch) -> None:
    _set_home(tmp_path, monkeypatch)
    save_tokens({"github": {"access_token": "token-123", "token_type": "bearer"}})

    result = runner.invoke(app, ["auth", "status"])

    assert result.exit_code == 0
    assert "github" in result.stdout.lower()


def test_auth_clear_provider(tmp_path: Path, monkeypatch) -> None:
    _set_home(tmp_path, monkeypatch)
    save_tokens(
        {
            "github": {"access_token": "token-123"},
            "azure-devops": {"access_token": "ado-456"},
        }
    )

    result = runner.invoke(app, ["auth", "clear", "--provider", "github"])

    assert result.exit_code == 0
    tokens = load_tokens()
    assert "github" not in tokens
    assert "azure-devops" in tokens


def test_auth_clear_all(tmp_path: Path, monkeypatch) -> None:
    _set_home(tmp_path, monkeypatch)
    save_tokens({"github": {"access_token": "token-123"}})

    result = runner.invoke(app, ["auth", "clear"])

    assert result.exit_code == 0
    assert load_tokens() == {}


def test_auth_azure_devops_pat_option(tmp_path: Path, monkeypatch) -> None:
    """Test storing PAT via --pat option."""
    _set_home(tmp_path, monkeypatch)

    result = runner.invoke(app, ["auth", "azure-devops", "--pat", "test-pat-token"])

    assert result.exit_code == 0
    tokens = load_tokens()
    assert "azure-devops" in tokens
    token_data = tokens["azure-devops"]
    assert token_data["access_token"] == "test-pat-token"
    assert token_data["token_type"] == "basic"
    assert "PAT" in result.stdout or "Personal Access Token" in result.stdout

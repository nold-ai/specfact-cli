"""Authentication token storage and retrieval utilities."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require


TOKEN_DIR_NAME = ".specfact"
TOKEN_FILE_NAME = "tokens.json"


@beartype
@require(lambda provider: isinstance(provider, str) and len(provider.strip()) > 0, "Provider must be non-empty string")
@ensure(lambda result: isinstance(result, str) and len(result) > 0, "Must return non-empty provider string")
def normalize_provider(provider: str) -> str:
    """Normalize provider names to canonical identifiers."""
    normalized = provider.strip().lower().replace("_", "-").replace(" ", "-")
    if normalized in {"ado", "azure", "azure-devops", "azuredevops"}:
        return "azure-devops"
    if normalized in {"gh", "github", "git-hub"}:
        return "github"
    return normalized


@beartype
@ensure(lambda result: isinstance(result, Path), "Must return Path")
def tokens_dir() -> Path:
    """Return the directory that stores authentication tokens."""
    return Path.home() / TOKEN_DIR_NAME


@beartype
@ensure(lambda result: isinstance(result, Path), "Must return Path")
def tokens_path() -> Path:
    """Return the token storage file path, ensuring parent directory exists."""
    directory = tokens_dir()
    directory.mkdir(parents=True, exist_ok=True)
    _apply_dir_permissions(directory)
    return directory / TOKEN_FILE_NAME


@beartype
@ensure(lambda result: isinstance(result, dict), "Must return dict")
def load_tokens() -> dict[str, dict[str, Any]]:
    """Load tokens from disk. Returns empty dict if no file exists."""
    path = tokens_path()
    if not path.exists():
        return {}

    try:
        raw = path.read_text(encoding="utf-8")
        if not raw.strip():
            return {}
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("Token file is not valid JSON") from exc

    if not isinstance(data, dict):
        raise ValueError("Token file must contain a JSON object")

    tokens: dict[str, dict[str, Any]] = {}
    for key, value in data.items():
        if isinstance(value, dict):
            tokens[str(key)] = value
    _apply_file_permissions(path)
    return tokens


@beartype
@require(lambda tokens: isinstance(tokens, dict), "Tokens must be dict")
@ensure(lambda result: result is None, "Must return None")
def save_tokens(tokens: dict[str, dict[str, Any]]) -> None:
    """Save tokens to disk with secure permissions."""
    path = tokens_path()
    payload = json.dumps(tokens, indent=2, sort_keys=True)
    path.write_text(payload, encoding="utf-8")
    _apply_file_permissions(path)


@beartype
@require(lambda provider: isinstance(provider, str) and len(provider.strip()) > 0, "Provider must be non-empty string")
@require(lambda token_data: isinstance(token_data, dict), "Token data must be dict")
@ensure(lambda result: result is None, "Must return None")
def set_token(provider: str, token_data: dict[str, Any]) -> None:
    """Store provider token data."""
    tokens = load_tokens()
    tokens[normalize_provider(provider)] = token_data
    save_tokens(tokens)


@beartype
@require(lambda provider: isinstance(provider, str) and len(provider.strip()) > 0, "Provider must be non-empty string")
@ensure(lambda result: result is None, "Must return None")
def clear_token(provider: str) -> None:
    """Remove a provider token from storage."""
    normalized = normalize_provider(provider)
    tokens = load_tokens()
    if normalized in tokens:
        tokens.pop(normalized, None)
        if tokens:
            save_tokens(tokens)
        else:
            path = tokens_path()
            if path.exists():
                path.unlink()


@beartype
@ensure(lambda result: result is None, "Must return None")
def clear_all_tokens() -> None:
    """Clear all stored tokens."""
    path = tokens_path()
    if path.exists():
        path.unlink()


@beartype
@require(lambda provider: isinstance(provider, str) and len(provider.strip()) > 0, "Provider must be non-empty string")
@ensure(lambda result: result is None or isinstance(result, dict), "Must return dict or None")
def get_token(provider: str, allow_expired: bool = False) -> dict[str, Any] | None:
    """Get stored token for provider if available and not expired unless allowed."""
    try:
        tokens = load_tokens()
    except ValueError:
        return None
    token_data = tokens.get(normalize_provider(provider))
    if not token_data:
        return None
    if not allow_expired and token_is_expired(token_data):
        return None
    return token_data


@beartype
@require(lambda token_data: isinstance(token_data, dict), "Token data must be dict")
@ensure(lambda result: isinstance(result, bool), "Must return bool")
def token_is_expired(token_data: dict[str, Any]) -> bool:
    """Check if token has expired based on expires_at metadata."""
    expires_at = token_data.get("expires_at")
    if not expires_at:
        return False

    if isinstance(expires_at, (int, float)):
        expires_dt = datetime.fromtimestamp(float(expires_at), tz=UTC)
    elif isinstance(expires_at, str):
        try:
            expires_dt = datetime.fromisoformat(expires_at)
            if expires_dt.tzinfo is None:
                expires_dt = expires_dt.replace(tzinfo=UTC)
        except ValueError:
            return False
    else:
        return False

    return datetime.now(tz=UTC) >= expires_dt


def _apply_file_permissions(path: Path) -> None:
    """Best-effort file permissions hardening."""
    if os.name != "posix":
        return
    try:
        os.chmod(path, 0o600)
    except OSError:
        return


def _apply_dir_permissions(path: Path) -> None:
    """Best-effort directory permissions hardening."""
    if os.name != "posix":
        return
    try:
        os.chmod(path, 0o700)
    except OSError:
        return

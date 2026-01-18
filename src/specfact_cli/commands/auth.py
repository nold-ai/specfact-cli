"""Authentication commands for DevOps providers."""

from __future__ import annotations

import os
import time
from datetime import UTC, datetime, timedelta
from typing import Any

import requests
import typer
from beartype import beartype
from icontract import ensure, require

from specfact_cli.runtime import get_configured_console
from specfact_cli.utils.auth_tokens import (
    clear_all_tokens,
    clear_token,
    normalize_provider,
    set_token,
    token_is_expired,
)


app = typer.Typer(help="Authenticate with DevOps providers using device code flows")
console = get_configured_console()


AZURE_DEVOPS_RESOURCE = "499b84ac-1321-427f-aa17-267ca6975798/.default"
DEFAULT_GITHUB_BASE_URL = "https://github.com"
DEFAULT_GITHUB_API_URL = "https://api.github.com"
DEFAULT_GITHUB_SCOPES = "repo"
DEFAULT_GITHUB_CLIENT_ID = "Ov23lizkVHsbEIjZKvRD"


@beartype
@ensure(lambda result: result is None, "Must return None")
def _print_token_status(provider: str, token_data: dict[str, Any]) -> None:
    """Print a formatted token status line."""
    expires_at = token_data.get("expires_at")
    status = "valid"
    if token_is_expired(token_data):
        status = "expired"
    scope_info = ""
    scopes = token_data.get("scopes") or token_data.get("scope")
    if isinstance(scopes, list):
        scope_info = ", scopes=" + ",".join(scopes)
    elif isinstance(scopes, str) and scopes:
        scope_info = f", scopes={scopes}"
    expiry_info = f", expires_at={expires_at}" if expires_at else ""
    console.print(f"[bold]{provider}[/bold]: {status}{scope_info}{expiry_info}")


@beartype
@ensure(lambda result: isinstance(result, str), "Must return base URL")
def _normalize_github_host(base_url: str) -> str:
    """Normalize GitHub base URL to host root (no API path)."""
    trimmed = base_url.rstrip("/")
    if trimmed.endswith("/api/v3"):
        trimmed = trimmed[: -len("/api/v3")]
    if trimmed.endswith("/api"):
        trimmed = trimmed[: -len("/api")]
    return trimmed


@beartype
@ensure(lambda result: isinstance(result, str), "Must return API base URL")
def _infer_github_api_base_url(host_url: str) -> str:
    """Infer GitHub API base URL from host URL."""
    normalized = host_url.rstrip("/")
    if normalized.lower() == DEFAULT_GITHUB_BASE_URL:
        return DEFAULT_GITHUB_API_URL
    return f"{normalized}/api/v3"


@beartype
@require(lambda scopes: isinstance(scopes, str), "Scopes must be string")
@ensure(lambda result: isinstance(result, str), "Must return scope string")
def _normalize_scopes(scopes: str) -> str:
    """Normalize scope string to space-separated list."""
    if not scopes.strip():
        return DEFAULT_GITHUB_SCOPES
    if "," in scopes:
        parts = [part.strip() for part in scopes.split(",") if part.strip()]
        return " ".join(parts)
    return scopes.strip()


@beartype
@require(lambda client_id: isinstance(client_id, str) and len(client_id) > 0, "Client ID required")
@require(lambda base_url: isinstance(base_url, str) and len(base_url) > 0, "Base URL required")
@require(lambda scopes: isinstance(scopes, str), "Scopes must be string")
@ensure(lambda result: isinstance(result, dict), "Must return device code response")
def _request_github_device_code(client_id: str, base_url: str, scopes: str) -> dict[str, Any]:
    """Request GitHub device code payload."""
    endpoint = f"{base_url.rstrip('/')}/login/device/code"
    headers = {"Accept": "application/json"}
    payload = {"client_id": client_id, "scope": scopes}
    response = requests.post(endpoint, data=payload, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


@beartype
@require(lambda client_id: isinstance(client_id, str) and len(client_id) > 0, "Client ID required")
@require(lambda base_url: isinstance(base_url, str) and len(base_url) > 0, "Base URL required")
@require(lambda device_code: isinstance(device_code, str) and len(device_code) > 0, "Device code required")
@require(lambda interval: isinstance(interval, int) and interval > 0, "Interval must be positive int")
@require(lambda expires_in: isinstance(expires_in, int) and expires_in > 0, "Expires_in must be positive int")
@ensure(lambda result: isinstance(result, dict), "Must return token response")
def _poll_github_device_token(
    client_id: str,
    base_url: str,
    device_code: str,
    interval: int,
    expires_in: int,
) -> dict[str, Any]:
    """Poll GitHub device code token endpoint until authorized or timeout."""
    endpoint = f"{base_url.rstrip('/')}/login/oauth/access_token"
    headers = {"Accept": "application/json"}
    payload = {
        "client_id": client_id,
        "device_code": device_code,
        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
    }

    deadline = time.monotonic() + expires_in
    poll_interval = interval

    while time.monotonic() < deadline:
        response = requests.post(endpoint, data=payload, headers=headers, timeout=30)
        response.raise_for_status()
        body = response.json()
        error = body.get("error")
        if not error:
            return body

        if error == "authorization_pending":
            time.sleep(poll_interval)
            continue
        if error == "slow_down":
            poll_interval += 5
            time.sleep(poll_interval)
            continue
        if error in {"expired_token", "access_denied"}:
            msg = body.get("error_description") or error
            raise RuntimeError(msg)

        msg = body.get("error_description") or error
        raise RuntimeError(msg)

    raise RuntimeError("Device code expired before authorization completed")


@app.command("azure-devops")
def auth_azure_devops() -> None:
    """Authenticate to Azure DevOps using device code flow."""
    try:
        from azure.identity import DeviceCodeCredential  # type: ignore[reportMissingImports]
    except ImportError:
        console.print("[bold red]✗[/bold red] azure-identity is not installed.")
        console.print("Install dependencies with: pip install specfact-cli")
        raise typer.Exit(1) from None

    def prompt_callback(verification_uri: str, user_code: str, expires_on: datetime) -> None:
        expires_at = expires_on
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        console.print("To sign in, use a web browser to open:")
        console.print(f"[bold]{verification_uri}[/bold]")
        console.print(f"Enter the code: [bold]{user_code}[/bold]")
        console.print(f"Code expires at: {expires_at.isoformat()}")

    console.print("[bold]Starting Azure DevOps device code authentication...[/bold]")
    credential = DeviceCodeCredential(prompt_callback=prompt_callback)
    token = credential.get_token(AZURE_DEVOPS_RESOURCE)

    expires_at = datetime.fromtimestamp(token.expires_on, tz=UTC).isoformat()
    token_data = {
        "access_token": token.token,
        "token_type": "bearer",
        "expires_at": expires_at,
        "resource": AZURE_DEVOPS_RESOURCE,
        "issued_at": datetime.now(tz=UTC).isoformat(),
    }
    set_token("azure-devops", token_data)

    console.print("[bold green]✓[/bold green] Azure DevOps authentication complete")
    console.print("Stored token for provider: azure-devops")


@app.command("github")
def auth_github(
    client_id: str | None = typer.Option(
        None,
        "--client-id",
        help="GitHub OAuth app client ID (defaults to SpecFact GitHub App)",
    ),
    base_url: str = typer.Option(
        DEFAULT_GITHUB_BASE_URL,
        "--base-url",
        help="GitHub base URL (use your enterprise host for GitHub Enterprise)",
    ),
    scopes: str = typer.Option(
        DEFAULT_GITHUB_SCOPES,
        "--scopes",
        help="OAuth scopes (comma or space separated)",
        hidden=True,
    ),
) -> None:
    """Authenticate to GitHub using RFC 8628 device code flow."""
    provided_client_id = client_id or os.environ.get("SPECFACT_GITHUB_CLIENT_ID")
    effective_client_id = provided_client_id or DEFAULT_GITHUB_CLIENT_ID
    if not effective_client_id:
        console.print("[bold red]✗[/bold red] GitHub client_id is required.")
        console.print("Use --client-id or set SPECFACT_GITHUB_CLIENT_ID.")
        raise typer.Exit(1)

    host_url = _normalize_github_host(base_url)
    if provided_client_id is None and host_url.lower() != DEFAULT_GITHUB_BASE_URL:
        console.print("[bold red]✗[/bold red] GitHub Enterprise requires a client ID.")
        console.print("Provide --client-id or set SPECFACT_GITHUB_CLIENT_ID.")
        raise typer.Exit(1)
    scope_string = _normalize_scopes(scopes)

    console.print("[bold]Starting GitHub device code authentication...[/bold]")
    device_payload = _request_github_device_code(effective_client_id, host_url, scope_string)

    user_code = device_payload.get("user_code")
    verification_uri = device_payload.get("verification_uri")
    verification_uri_complete = device_payload.get("verification_uri_complete")
    device_code = device_payload.get("device_code")
    expires_in = int(device_payload.get("expires_in", 900))
    interval = int(device_payload.get("interval", 5))

    if not device_code:
        console.print("[bold red]✗[/bold red] Invalid device code response from GitHub")
        raise typer.Exit(1)

    if verification_uri_complete:
        console.print(f"Open: [bold]{verification_uri_complete}[/bold]")
    elif verification_uri and user_code:
        console.print(f"Open: [bold]{verification_uri}[/bold] and enter code [bold]{user_code}[/bold]")
    else:
        console.print("[bold red]✗[/bold red] Invalid device code response from GitHub")
        raise typer.Exit(1)

    token_payload = _poll_github_device_token(
        effective_client_id,
        host_url,
        device_code,
        interval,
        expires_in,
    )

    access_token = token_payload.get("access_token")
    if not access_token:
        console.print("[bold red]✗[/bold red] GitHub did not return an access token")
        raise typer.Exit(1)

    expires_at = datetime.now(tz=UTC) + timedelta(seconds=expires_in)
    token_data = {
        "access_token": access_token,
        "token_type": token_payload.get("token_type", "bearer"),
        "scopes": token_payload.get("scope", scope_string),
        "client_id": effective_client_id,
        "issued_at": datetime.now(tz=UTC).isoformat(),
        "expires_at": None,
        "base_url": host_url,
        "api_base_url": _infer_github_api_base_url(host_url),
    }

    # Preserve expires_at only if GitHub returns explicit expiry (usually None)
    if token_payload.get("expires_in"):
        token_data["expires_at"] = expires_at.isoformat()

    set_token("github", token_data)

    console.print("[bold green]✓[/bold green] GitHub authentication complete")
    console.print("Stored token for provider: github")


@app.command("status")
def auth_status() -> None:
    """Show authentication status for supported providers."""
    tokens = load_tokens_safe()
    if not tokens:
        console.print("No stored authentication tokens found.")
        return

    if len(tokens) == 1:
        only_provider = next(iter(tokens.keys()))
        console.print(f"Detected provider: {only_provider} (auto-detected)")

    for provider, token_data in tokens.items():
        _print_token_status(provider, token_data)


@app.command("clear")
def auth_clear(
    provider: str | None = typer.Option(
        None,
        "--provider",
        help="Provider to clear (azure-devops or github). Clear all if omitted.",
    ),
) -> None:
    """Clear stored authentication tokens."""
    if provider:
        clear_token(provider)
        console.print(f"Cleared stored token for {normalize_provider(provider)}")
        return

    tokens = load_tokens_safe()
    if not tokens:
        console.print("No stored tokens to clear")
        return

    if len(tokens) == 1:
        only_provider = next(iter(tokens.keys()))
        clear_token(only_provider)
        console.print(f"Cleared stored token for {only_provider} (auto-detected)")
        return

    clear_all_tokens()
    console.print("Cleared all stored tokens")


def load_tokens_safe() -> dict[str, dict[str, Any]]:
    """Load tokens and handle errors gracefully for CLI output."""
    try:
        return get_token_map()
    except ValueError as exc:
        console.print(f"[bold red]✗[/bold red] {exc}")
        raise typer.Exit(1) from exc


def get_token_map() -> dict[str, dict[str, Any]]:
    """Load token map without CLI side effects."""
    from specfact_cli.utils.auth_tokens import load_tokens

    return load_tokens()

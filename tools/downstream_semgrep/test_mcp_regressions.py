from __future__ import annotations

import asyncio
import inspect
import os
import secrets
import shutil
import tempfile
import time
import unittest
from collections.abc import Callable
from pathlib import Path
from typing import Protocol, cast
from unittest.mock import patch

import httpx
from icontract import ensure
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.server.fastmcp import FastMCP
from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager


HEADERS = {
    "Accept": "application/json, text/event-stream",
    "Content-Type": "application/json",
    "MCP-Protocol-Version": "2025-06-18",
}
INITIALIZE = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "downstream-regression", "version": "1"},
    },
}


class _FixedManagerDefaults(Protocol):
    max_sessions: int
    session_idle_timeout: float | None


class _FixedManagerFactory(Protocol):
    def __call__(
        self,
        app: object,
        *,
        json_response: bool,
        session_idle_timeout: float | None,
        max_sessions: int | None,
        max_request_body_size: int,
    ) -> StreamableHTTPSessionManager: ...


async def _await_reclaimed(manager: StreamableHTTPSessionManager, session: str) -> None:
    async with asyncio.timeout(5):
        while session in manager._server_instances:
            await asyncio.sleep(0.02)


class TestMcpLifecycle(unittest.IsolatedAsyncioTestCase):
    def _manager(
        self,
        *,
        session_idle_timeout: float | None = 1800,
        max_sessions: int | None = 10000,
        max_request_body_size: int = 4194304,
    ) -> StreamableHTTPSessionManager:
        parameters = inspect.signature(StreamableHTTPSessionManager).parameters
        self.assertIn("session_idle_timeout", parameters)
        self.assertIn("max_sessions", parameters)
        factory = cast(_FixedManagerFactory, StreamableHTTPSessionManager)
        return factory(
            Server("downstream-regression"),
            json_response=True,
            session_idle_timeout=session_idle_timeout,
            max_sessions=max_sessions,
            max_request_body_size=max_request_body_size,
        )

    @ensure(lambda result: result is None)
    async def test_fixed_defaults(self) -> None:
        manager = self._manager()
        self.assertEqual(manager.session_idle_timeout, 1800)
        self.assertEqual(cast(_FixedManagerDefaults, manager).max_sessions, 10000)

    @ensure(lambda result: result is None)
    async def test_delete_discards_default_manager_registration(self) -> None:
        manager = StreamableHTTPSessionManager(Server("delete-control"), json_response=True)
        async with (
            manager.run(),
            httpx.AsyncClient(
                transport=httpx.ASGITransport(app=manager.handle_request),
                base_url="http://localhost",
                headers=HEADERS,
            ) as client,
        ):
            first = await client.post("/mcp", json=INITIALIZE)
            self.assertEqual(first.status_code, 200, first.text)
            deleted = await client.delete("/mcp", headers={"mcp-session-id": first.headers["mcp-session-id"]})
            self.assertEqual(deleted.status_code, 200, deleted.text)
            retained = len(manager._server_instances)
        self.assertEqual(retained, 0, "DELETE retained a registered session")

    @ensure(lambda result: result is None)
    async def test_refused_opening_discards_default_manager_registration(self) -> None:
        manager = StreamableHTTPSessionManager(Server("refusal-control"), json_response=True)
        async with (
            manager.run(),
            httpx.AsyncClient(
                transport=httpx.ASGITransport(app=manager.handle_request),
                base_url="http://localhost",
                headers=HEADERS,
            ) as client,
        ):
            refused = await client.post("/mcp", content="invalid json")
            self.assertEqual(refused.status_code, 400, refused.text)
            retained = len(manager._server_instances)
        self.assertEqual(retained, 0, "Refused opening retained a registered session")

    @ensure(lambda result: result is None)
    async def test_delete_reclaims_capacity_and_old_id(self) -> None:
        manager = self._manager(max_sessions=1)
        async with (
            manager.run(),
            httpx.AsyncClient(
                transport=httpx.ASGITransport(app=manager.handle_request),
                base_url="http://localhost",
                headers=HEADERS,
            ) as client,
        ):
            first = await client.post("/mcp", json=INITIALIZE)
            self.assertEqual(first.status_code, 200, first.text)
            session = first.headers["mcp-session-id"]
            full = await client.post("/mcp", json=INITIALIZE)
            self.assertEqual(full.status_code, 503)
            deleted = await client.delete("/mcp", headers={"mcp-session-id": session})
            self.assertEqual(deleted.status_code, 200, deleted.text)
            stale = await client.post("/mcp", headers={"mcp-session-id": session}, json=INITIALIZE)
            self.assertEqual(stale.status_code, 404)
            replacement = await client.post("/mcp", json=INITIALIZE)
            self.assertEqual(replacement.status_code, 200, replacement.text)

    @ensure(lambda result: result is None)
    async def test_idle_expiry_reclaims_capacity(self) -> None:
        manager = self._manager(session_idle_timeout=0.05, max_sessions=1)
        async with (
            manager.run(),
            httpx.AsyncClient(
                transport=httpx.ASGITransport(app=manager.handle_request),
                base_url="http://localhost",
                headers=HEADERS,
            ) as client,
        ):
            first = await client.post("/mcp", json=INITIALIZE)
            self.assertEqual(first.status_code, 200, first.text)
            session = first.headers["mcp-session-id"]
            await _await_reclaimed(manager, session)
            expired = await client.delete("/mcp", headers={"mcp-session-id": session})
            self.assertEqual(expired.status_code, 404, expired.text)
            replacement = await client.post("/mcp", json=INITIALIZE)
            self.assertEqual(replacement.status_code, 200, replacement.text)

    @ensure(lambda result: result is None)
    async def test_refused_opening_does_not_consume_capacity(self) -> None:
        manager = self._manager(max_sessions=1)
        async with (
            manager.run(),
            httpx.AsyncClient(
                transport=httpx.ASGITransport(app=manager.handle_request),
                base_url="http://localhost",
                headers=HEADERS,
            ) as client,
        ):
            for _ in range(3):
                refused = await client.post("/mcp", content="invalid json")
                self.assertEqual(refused.status_code, 400, refused.text)
                self.assertEqual(len(manager._server_instances), 0)
            legitimate = await client.post("/mcp", json=INITIALIZE)
            self.assertEqual(legitimate.status_code, 200, legitimate.text)

    @ensure(lambda result: result is None)
    async def test_concurrent_openings_cannot_exceed_capacity(self) -> None:
        manager = self._manager(max_sessions=2)
        async with (
            manager.run(),
            httpx.AsyncClient(
                transport=httpx.ASGITransport(app=manager.handle_request),
                base_url="http://localhost",
                headers=HEADERS,
            ) as client,
        ):
            responses = await asyncio.gather(*(client.post("/mcp", json=INITIALIZE) for _ in range(5)))
            self.assertEqual(sorted(r.status_code for r in responses), [200, 200, 503, 503, 503])
        self.assertEqual(len(manager._server_instances), 0)

    @ensure(lambda result: result is None)
    async def test_oversized_opening_is_rejected_without_retention(self) -> None:
        manager = self._manager(max_sessions=1, max_request_body_size=512)
        async with (
            manager.run(),
            httpx.AsyncClient(
                transport=httpx.ASGITransport(app=manager.handle_request),
                base_url="http://localhost",
                headers=HEADERS,
            ) as client,
        ):
            response = await client.post("/mcp", content="x" * 513)
            self.assertEqual(response.status_code, 413)
            legitimate = await client.post("/mcp", json=INITIALIZE)
            self.assertEqual(legitimate.status_code, 200, legitimate.text)


class TestSemgrepStdio(unittest.IsolatedAsyncioTestCase):
    @ensure(lambda result: result is None)
    async def test_initialize_list_scan_and_shutdown(self) -> None:
        executable = shutil.which("semgrep")
        self.assertIsNotNone(executable, "The matrix must install the actual downstream CLI")
        with tempfile.TemporaryDirectory(prefix="semgrep-mcp-regression-") as directory:
            environment = {
                "PATH": os.environ.get("PATH", ""),
                "HOME": directory,
                "USERPROFILE": directory,
                "SEMGREP_SETTINGS_FILE": str(Path(directory) / "settings.yml"),
                "SEMGREP_SEND_METRICS": "off",
                "SEMGREP_ENABLE_VERSION_CHECK": "0",
            }
            parameters = StdioServerParameters(
                command=str(executable), args=["mcp", "--transport", "stdio"], env=environment
            )
            async with (
                asyncio.timeout(60),
                stdio_client(parameters) as streams,
                ClientSession(*streams) as session,
            ):
                initialized = await session.initialize()
                self.assertEqual(initialized.serverInfo.name, "Semgrep")
                tools = await session.list_tools()
                self.assertIn("semgrep_scan_with_custom_rule", {tool.name for tool in tools.tools})
                result = await session.call_tool(
                    "semgrep_scan_with_custom_rule",
                    {
                        "code_files": [{"path": "unsafe.py", "content": "eval(user_input)\n"}],
                        "rule": (
                            "rules:\n- id: downstream-positive\n  pattern: eval(...)\n"
                            "  message: positive control\n  severity: ERROR\n  languages: [python]\n"
                        ),
                    },
                )
                self.assertFalse(result.isError, str(result))
                self.assertIn("downstream-positive", str(result))


class TestSemgrepHttpAuthentication(unittest.IsolatedAsyncioTestCase):
    @ensure(lambda result: result is None)
    async def test_missing_and_malformed_credentials_remain_rejected(self) -> None:
        from semgrep.commands.mcp import setup_mcp_server

        discovery = {
            "issuer": "https://issuer.invalid",
            "jwks_uri": "https://issuer.invalid/jwks",
            "introspection_endpoint": "https://issuer.invalid/introspect",
        }
        with patch(
            "semgrep.mcp.utilities.utils.get_oauth_authorization_server_metadata",
            return_value=discovery,
        ):
            server = setup_mcp_server("localhost", 8000)
            app = server.streamable_http_app()
            self.assertEqual(server.session_manager.session_idle_timeout, 1800)
            self.assertEqual(cast(_FixedManagerDefaults, server.session_manager).max_sessions, 10000)
            async with (
                app.router.lifespan_context(app),
                httpx.AsyncClient(
                    transport=httpx.ASGITransport(app=app),
                    base_url="http://localhost:8000",
                    headers=HEADERS,
                ) as client,
            ):
                missing = await client.post("/mcp", json=INITIALIZE)
                malformed = await client.post("/mcp", json=INITIALIZE, headers={"Authorization": "Bearer not-a-jwt"})
                self.assertEqual(missing.status_code, 401, missing.text)
                self.assertEqual(malformed.status_code, 401, malformed.text)
                self.assertIn("resource_metadata", missing.headers["www-authenticate"])


def _authenticated_fixture() -> tuple[FastMCP, Callable[[str], str]]:
    import jwt

    key = secrets.token_bytes(32)
    from mcp.server.auth.provider import AccessToken, TokenVerifier
    from mcp.server.auth.settings import AuthSettings
    from mcp.server.fastmcp import FastMCP

    assert "validate_token_resource" in AuthSettings.model_fields

    class FixtureVerifier(TokenVerifier):
        async def verify_token(self, token: str) -> AccessToken | None:
            try:
                claims = jwt.decode(token, key, algorithms=["HS256"], audience="http://localhost:8000")
            except jwt.InvalidTokenError:
                return None
            return AccessToken(
                token=token,
                client_id=claims["client_id"],
                scopes=[],
                expires_at=claims["exp"],
                resource=claims["aud"],
                subject=claims["sub"],
                claims=claims,
            )

    def credential(principal: str) -> str:
        return jwt.encode(
            {
                "client_id": principal,
                "sub": principal,
                "iss": "https://issuer.invalid",
                "aud": "http://localhost:8000",
                "exp": int(time.time()) + 60,
            },
            key,
            algorithm="HS256",
        )

    server = FastMCP(
        "authenticated-sdk-regression",
        json_response=True,
        auth=AuthSettings.model_validate(
            {
                "issuer_url": "https://issuer.invalid",
                "resource_server_url": "http://localhost:8000",
                "required_scopes": [],
                "validate_token_resource": True,
            }
        ),
        token_verifier=FixtureVerifier(),
    )
    return server, credential


class TestSdkAuthenticatedSessions(unittest.IsolatedAsyncioTestCase):
    @ensure(lambda result: result is None)
    async def test_other_principal_cannot_delete_a_legitimate_session(self) -> None:
        server, credential = _authenticated_fixture()
        app = server.streamable_http_app()
        async with (
            app.router.lifespan_context(app),
            httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://localhost:8000", headers=HEADERS
            ) as client,
        ):
            owner = {"Authorization": "Bearer " + credential("owner")}
            created = await client.post("/mcp", json=INITIALIZE, headers=owner)
            self.assertEqual(created.status_code, 200, created.text)
            session = created.headers["mcp-session-id"]
            hostile = await client.delete(
                "/mcp",
                headers={"Authorization": "Bearer " + credential("other"), "mcp-session-id": session},
            )
            self.assertEqual(hostile.status_code, 404, hostile.text)
            deleted = await client.delete("/mcp", headers={**owner, "mcp-session-id": session})
            self.assertEqual(deleted.status_code, 200, deleted.text)


if __name__ == "__main__":
    unittest.main()

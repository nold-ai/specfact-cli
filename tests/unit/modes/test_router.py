"""
Unit tests for command router.

Tests command routing logic based on operational mode.
"""

from __future__ import annotations

import pytest
from beartype import beartype

from specfact_cli.modes import OperationalMode
from specfact_cli.modes.router import CommandRouter, RoutingResult, get_router


class TestCommandRouter:
    """Tests for CommandRouter class."""

    @beartype
    def test_cicd_mode_direct_execution(self) -> None:
        """CI/CD mode uses direct execution."""
        router = CommandRouter()
        result = router.route("import from-code", OperationalMode.CICD, {})
        assert result.execution_mode == "direct"
        assert result.mode == OperationalMode.CICD
        assert result.command == "import from-code"

    @beartype
    def test_copilot_mode_agent_routing(self) -> None:
        """CoPilot mode uses agent routing."""
        router = CommandRouter()
        result = router.route("import from-code", OperationalMode.COPILOT, {})
        assert result.execution_mode == "agent"
        assert result.mode == OperationalMode.COPILOT
        assert result.command == "import from-code"

    @beartype
    def test_route_with_context(self) -> None:
        """Router accepts context dictionary."""
        router = CommandRouter()
        context = {"repo": ".", "confidence": 0.7}
        result = router.route("import from-code", OperationalMode.CICD, context)
        assert result.execution_mode == "direct"
        assert result.mode == OperationalMode.CICD

    @beartype
    def test_route_with_none_context(self) -> None:
        """Router accepts None context."""
        router = CommandRouter()
        result = router.route("plan init", OperationalMode.COPILOT, None)
        assert result.execution_mode == "agent"
        assert result.mode == OperationalMode.COPILOT

    @beartype
    def test_route_with_auto_detect_cicd(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Auto-detect defaults to CI/CD mode."""
        router = CommandRouter()
        # Mock environment to ensure CI/CD mode
        monkeypatch.delenv("SPECFACT_MODE", raising=False)
        monkeypatch.delenv("COPILOT_API_URL", raising=False)
        monkeypatch.delenv("COPILOT_API_TOKEN", raising=False)
        monkeypatch.delenv("GITHUB_COPILOT_TOKEN", raising=False)
        monkeypatch.delenv("VSCODE_PID", raising=False)
        monkeypatch.delenv("CURSOR_PID", raising=False)
        monkeypatch.delenv("TERM_PROGRAM", raising=False)

        result = router.route_with_auto_detect("import from-code", explicit_mode=None, context=None)
        assert result.execution_mode == "direct"
        assert result.mode == OperationalMode.CICD

    @beartype
    def test_route_with_auto_detect_explicit_copilot(self) -> None:
        """Explicit mode override works with auto-detect."""
        router = CommandRouter()
        result = router.route_with_auto_detect("import from-code", explicit_mode=OperationalMode.COPILOT, context=None)
        assert result.execution_mode == "agent"
        assert result.mode == OperationalMode.COPILOT

    @beartype
    def test_route_with_auto_detect_explicit_cicd(self) -> None:
        """Explicit CI/CD mode works with auto-detect."""
        router = CommandRouter()
        result = router.route_with_auto_detect("plan init", explicit_mode=OperationalMode.CICD, context={})
        assert result.execution_mode == "direct"
        assert result.mode == OperationalMode.CICD

    @beartype
    def test_should_use_agent_cicd(self) -> None:
        """CI/CD mode should not use agent."""
        router = CommandRouter()
        assert router.should_use_agent(OperationalMode.CICD) is False

    @beartype
    def test_should_use_agent_copilot(self) -> None:
        """CoPilot mode should use agent."""
        router = CommandRouter()
        assert router.should_use_agent(OperationalMode.COPILOT) is True

    @beartype
    def test_should_use_direct_cicd(self) -> None:
        """CI/CD mode should use direct execution."""
        router = CommandRouter()
        assert router.should_use_direct(OperationalMode.CICD) is True

    @beartype
    def test_should_use_direct_copilot(self) -> None:
        """CoPilot mode should not use direct execution."""
        router = CommandRouter()
        assert router.should_use_direct(OperationalMode.COPILOT) is False

    @beartype
    def test_routing_result_dataclass(self) -> None:
        """RoutingResult dataclass works correctly."""
        result = RoutingResult(execution_mode="direct", mode=OperationalMode.CICD, command="test")
        assert result.execution_mode == "direct"
        assert result.mode == OperationalMode.CICD
        assert result.command == "test"


class TestGetRouter:
    """Tests for get_router function."""

    @beartype
    def test_get_router_returns_instance(self) -> None:
        """get_router returns CommandRouter instance."""
        router = get_router()
        assert isinstance(router, CommandRouter)

    @beartype
    def test_get_router_singleton(self) -> None:
        """get_router returns same instance."""
        router1 = get_router()
        router2 = get_router()
        assert router1 is router2


class TestRouterIntegration:
    """Integration tests for router with various commands."""

    @beartype
    def test_route_analyze_command(self) -> None:
        """Router handles analyze commands correctly."""
        router = CommandRouter()
        result = router.route("import from-code", OperationalMode.CICD)
        assert result.command == "import from-code"
        assert result.execution_mode == "direct"

    @beartype
    def test_route_plan_command(self) -> None:
        """Router handles plan commands correctly."""
        router = CommandRouter()
        result = router.route("plan init", OperationalMode.COPILOT)
        assert result.command == "plan init"
        assert result.execution_mode == "agent"

    @beartype
    def test_route_sync_command(self) -> None:
        """Router handles sync commands correctly."""
        router = CommandRouter()
        result = router.route("sync spec-kit", OperationalMode.CICD)
        assert result.command == "sync spec-kit"
        assert result.execution_mode == "direct"

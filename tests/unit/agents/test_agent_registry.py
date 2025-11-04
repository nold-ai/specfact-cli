"""
Unit tests for agent registry.
"""

from __future__ import annotations

from beartype import beartype

from specfact_cli.agents.analyze_agent import AnalyzeAgent
from specfact_cli.agents.plan_agent import PlanAgent
from specfact_cli.agents.registry import AgentRegistry, get_agent, get_registry
from specfact_cli.agents.sync_agent import SyncAgent


class TestAgentRegistry:
    """Tests for AgentRegistry class."""

    @beartype
    def test_get_registry_returns_singleton(self) -> None:
        """get_registry returns singleton instance."""
        registry1 = get_registry()
        registry2 = get_registry()
        assert registry1 is registry2

    @beartype
    def test_default_agents_registered(self) -> None:
        """Default agents are registered."""
        registry = get_registry()
        assert registry.get("analyze") is not None
        assert registry.get("plan") is not None
        assert registry.get("sync") is not None

    @beartype
    def test_get_analyze_agent(self) -> None:
        """get returns AnalyzeAgent for 'analyze'."""
        registry = get_registry()
        agent = registry.get("analyze")
        assert isinstance(agent, AnalyzeAgent)

    @beartype
    def test_get_plan_agent(self) -> None:
        """get returns PlanAgent for 'plan'."""
        registry = get_registry()
        agent = registry.get("plan")
        assert isinstance(agent, PlanAgent)

    @beartype
    def test_get_sync_agent(self) -> None:
        """get returns SyncAgent for 'sync'."""
        registry = get_registry()
        agent = registry.get("sync")
        assert isinstance(agent, SyncAgent)

    @beartype
    def test_get_agent_for_command(self) -> None:
        """get_agent_for_command returns agent for command."""
        registry = get_registry()
        agent = registry.get_agent_for_command("import from-code")
        assert isinstance(agent, AnalyzeAgent)

    @beartype
    def test_get_agent_for_plan_command(self) -> None:
        """get_agent_for_command returns PlanAgent for plan commands."""
        registry = get_registry()
        agent = registry.get_agent_for_command("plan init")
        assert isinstance(agent, PlanAgent)

    @beartype
    def test_get_agent_for_sync_command(self) -> None:
        """get_agent_for_command returns SyncAgent for sync commands."""
        registry = get_registry()
        agent = registry.get_agent_for_command("sync spec-kit")
        assert isinstance(agent, SyncAgent)

    @beartype
    def test_get_agent_convenience_function(self) -> None:
        """get_agent convenience function works."""
        agent = get_agent("import from-code")
        assert isinstance(agent, AnalyzeAgent)

    @beartype
    def test_register_custom_agent(self) -> None:
        """register allows custom agent registration."""
        registry = AgentRegistry()
        custom_agent = AnalyzeAgent()
        registry.register("custom", custom_agent)
        assert registry.get("custom") is custom_agent

    @beartype
    def test_list_agents(self) -> None:
        """list_agents returns all registered agent names."""
        registry = get_registry()
        names = registry.list_agents()
        assert "analyze" in names
        assert "plan" in names
        assert "sync" in names
        assert len(names) >= 3

"""
Agent Registry - Registry for agent mode instances.

This module provides a registry for managing agent mode instances and
routing commands to appropriate agents based on command type.
"""

from __future__ import annotations

from beartype import beartype
from icontract import ensure, require

from specfact_cli.agents.analyze_agent import AnalyzeAgent
from specfact_cli.agents.base import AgentMode
from specfact_cli.agents.plan_agent import PlanAgent
from specfact_cli.agents.sync_agent import SyncAgent


class AgentRegistry:
    """
    Registry for agent mode instances.

    Provides centralized management of agent instances and routing
    based on command type.
    """

    def __init__(self) -> None:
        """Initialize agent registry with default agents."""
        self._agents: dict[str, AgentMode] = {}
        self._register_default_agents()

    @beartype
    def _register_default_agents(self) -> None:
        """Register default agent instances."""
        self._agents["analyze"] = AnalyzeAgent()
        self._agents["plan"] = PlanAgent()
        self._agents["sync"] = SyncAgent()

    @beartype
    @require(lambda name: bool(name), "Agent name must be non-empty")
    @require(lambda agent: isinstance(agent, AgentMode), "Agent must be AgentMode instance")
    def register(self, name: str, agent: AgentMode) -> None:
        """
        Register an agent instance.

        Args:
            name: Agent name (e.g., "analyze", "plan", "sync")
            agent: Agent mode instance

        Examples:
            >>> registry = AgentRegistry()
            >>> registry.register("custom", AnalyzeAgent())
        """
        self._agents[name] = agent

    @beartype
    @require(lambda name: bool(name), "Agent name must be non-empty")
    @ensure(lambda result: result is None or isinstance(result, AgentMode), "Result must be AgentMode or None")
    def get(self, name: str) -> AgentMode | None:
        """
        Get an agent instance by name.

        Args:
            name: Agent name (e.g., "analyze", "plan", "sync")

        Returns:
            Agent mode instance or None if not found

        Examples:
            >>> registry = AgentRegistry()
            >>> agent = registry.get("analyze")
            >>> isinstance(agent, AnalyzeAgent)
            True
        """
        return self._agents.get(name)

    @beartype
    @require(lambda command: bool(command), "Command must be non-empty")
    @ensure(lambda result: result is None or isinstance(result, AgentMode), "Result must be AgentMode or None")
    def get_agent_for_command(self, command: str) -> AgentMode | None:
        """
        Get agent instance for a command.

        Args:
            command: CLI command (e.g., "import from-code", "plan init", "sync spec-kit")

        Returns:
            Agent mode instance or None if not found

        Examples:
            >>> registry = AgentRegistry()
            >>> agent = registry.get_agent_for_command("import from-code")
            >>> isinstance(agent, AnalyzeAgent)
            True
        """
        # Extract command type from command string
        command_parts = command.split()
        if not command_parts:
            return None

        command_type = command_parts[0]

        # Map command types to agent names
        agent_map: dict[str, str] = {
            "import": "analyze",  # import from-code uses AnalyzeAgent
            "plan": "plan",
            "sync": "sync",
        }

        agent_name = agent_map.get(command_type)
        if agent_name:
            return self.get(agent_name)

        return None

    @beartype
    def list_agents(self) -> list[str]:
        """
        List all registered agent names.

        Returns:
            List of agent names

        Examples:
            >>> registry = AgentRegistry()
            >>> names = registry.list_agents()
            >>> "analyze" in names
            True
        """
        return list(self._agents.keys())


# Global registry instance
_registry: AgentRegistry | None = None


@beartype
@ensure(lambda result: isinstance(result, AgentRegistry), "Result must be AgentRegistry")
def get_registry() -> AgentRegistry:
    """
    Get the global agent registry instance.

    Returns:
        AgentRegistry instance

    Examples:
        >>> registry = get_registry()
        >>> isinstance(registry, AgentRegistry)
        True
    """
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
    return _registry


@beartype
@require(lambda command: bool(command), "Command must be non-empty")
@ensure(lambda result: result is None or isinstance(result, AgentMode), "Result must be AgentMode or None")
def get_agent(command: str) -> AgentMode | None:
    """
    Get agent instance for a command (convenience function).

    Args:
        command: CLI command (e.g., "import from-code")

    Returns:
        Agent mode instance or None if not found

    Examples:
        >>> agent = get_agent("import from-code")
        >>> isinstance(agent, AnalyzeAgent)
        True
    """
    registry = get_registry()
    return registry.get_agent_for_command(command)

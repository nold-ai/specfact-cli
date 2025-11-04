"""
Command Router - Route commands based on operational mode.

This module provides routing logic to execute commands differently based on
the operational mode (CI/CD vs CoPilot).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from beartype import beartype
from icontract import ensure, require

from specfact_cli.agents.registry import get_agent
from specfact_cli.modes.detector import OperationalMode, detect_mode


@dataclass
class RoutingResult:
    """Result of command routing."""

    execution_mode: str  # "direct" or "agent"
    mode: OperationalMode
    command: str


class CommandRouter:
    """Routes commands based on operational mode."""

    @beartype
    @require(lambda command: bool(command), "Command must be non-empty")
    @require(lambda mode: isinstance(mode, OperationalMode), "Mode must be OperationalMode")
    @ensure(lambda result: result.execution_mode in ("direct", "agent"), "Execution mode must be direct or agent")
    @ensure(lambda result: result.mode in (OperationalMode.CICD, OperationalMode.COPILOT), "Mode must be valid")
    def route(self, command: str, mode: OperationalMode, context: dict[str, Any] | None = None) -> RoutingResult:
        """
        Route a command based on operational mode.

        Args:
            command: Command name (e.g., "import from-code")
            mode: Operational mode (CI/CD or CoPilot)
            context: Optional context dictionary for command execution

        Returns:
            RoutingResult with execution mode and mode information

        Examples:
            >>> router = CommandRouter()
            >>> result = router.route("import from-code", OperationalMode.CICD)
            >>> result.execution_mode
            'direct'
            >>> result = router.route("import from-code", OperationalMode.COPILOT)
            >>> result.execution_mode
            'agent'
        """
        if mode == OperationalMode.CICD:
            return RoutingResult(execution_mode="direct", mode=mode, command=command)
        # CoPilot mode uses agent routing (Phase 4.1)
        # Check if agent is available for this command
        agent = get_agent(command)
        if agent:
            return RoutingResult(execution_mode="agent", mode=mode, command=command)
        # Fallback to direct execution if no agent available
        return RoutingResult(execution_mode="direct", mode=mode, command=command)

    @beartype
    @require(lambda command: bool(command), "Command must be non-empty")
    @ensure(lambda result: result.mode in (OperationalMode.CICD, OperationalMode.COPILOT), "Mode must be valid")
    def route_with_auto_detect(
        self, command: str, explicit_mode: OperationalMode | None = None, context: dict[str, Any] | None = None
    ) -> RoutingResult:
        """
        Route a command with automatic mode detection.

        Args:
            command: Command name (e.g., "import from-code")
            explicit_mode: Optional explicit mode override
            context: Optional context dictionary for command execution

        Returns:
            RoutingResult with execution mode and detected mode information

        Examples:
            >>> router = CommandRouter()
            >>> result = router.route_with_auto_detect("import from-code")
            >>> result.execution_mode in ("direct", "agent")
            True
        """
        mode = detect_mode(explicit_mode=explicit_mode)
        return self.route(command, mode, context)

    @beartype
    @require(lambda mode: isinstance(mode, OperationalMode), "Mode must be OperationalMode")
    def should_use_agent(self, mode: OperationalMode) -> bool:
        """
        Check if command should use agent routing.

        Args:
            mode: Operational mode

        Returns:
            True if agent routing should be used, False for direct execution

        Examples:
            >>> router = CommandRouter()
            >>> router.should_use_agent(OperationalMode.CICD)
            False
            >>> router.should_use_agent(OperationalMode.COPILOT)
            True
        """
        return mode == OperationalMode.COPILOT

    @beartype
    @require(lambda mode: isinstance(mode, OperationalMode), "Mode must be OperationalMode")
    def should_use_direct(self, mode: OperationalMode) -> bool:
        """
        Check if command should use direct execution.

        Args:
            mode: Operational mode

        Returns:
            True if direct execution should be used, False for agent routing

        Examples:
            >>> router = CommandRouter()
            >>> router.should_use_direct(OperationalMode.CICD)
            True
            >>> router.should_use_direct(OperationalMode.COPILOT)
            False
        """
        return mode == OperationalMode.CICD


def get_router() -> CommandRouter:
    """
    Get the global command router instance.

    Returns:
        CommandRouter instance

    Examples:
        >>> router = get_router()
        >>> isinstance(router, CommandRouter)
        True
    """
    return _router


# Global router instance
_router = CommandRouter()

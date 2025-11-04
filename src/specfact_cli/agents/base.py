"""
Base Agent Mode - Abstract interface for agent modes.

This module provides the base class for agent modes that generate enhanced
prompts and route commands with context injection for CoPilot integration.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from beartype import beartype
from icontract import ensure, require


class AgentMode(ABC):
    """
    Base class for agent modes.

    Agent modes provide enhanced prompts optimized for CoPilot and route
    commands with context injection.
    """

    @beartype
    @require(lambda command: bool(command), "Command must be non-empty")
    @ensure(lambda result: isinstance(result, str) and bool(result), "Prompt must be non-empty string")
    @abstractmethod
    def generate_prompt(self, command: str, context: dict[str, Any] | None = None) -> str:
        """
        Generate enhanced prompt for CoPilot.

        Args:
            command: CLI command being executed (e.g., "import from-code")
            context: Context dictionary with current file, selection, workspace, etc.

        Returns:
            Enhanced prompt optimized for CoPilot execution

        Examples:
            >>> agent = AnalyzeAgent()
            >>> prompt = agent.generate_prompt("import from-code", {"current_file": "src/main.py"})
            >>> isinstance(prompt, str)
            True
        """

    @beartype
    @require(lambda command: bool(command), "Command must be non-empty")
    @ensure(lambda result: isinstance(result, dict), "Result must be a dictionary")
    @abstractmethod
    def execute(
        self, command: str, args: dict[str, Any] | None = None, context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Execute command with agent mode routing.

        Args:
            command: CLI command being executed (e.g., "import from-code")
            args: Command arguments (e.g., {"repo": ".", "confidence": 0.7})
            context: Context dictionary with current file, selection, workspace, etc.

        Returns:
            Command result dictionary with enhanced output

        Examples:
            >>> agent = AnalyzeAgent()
            >>> result = agent.execute("import from-code", {"repo": "."}, {"current_file": "src/main.py"})
            >>> isinstance(result, dict)
            True
        """

    @beartype
    @ensure(lambda result: isinstance(result, dict), "Result must be a dictionary")
    def inject_context(self, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Inject context information for CoPilot.

        This method can be overridden by specialized agents to add
        context-specific information.

        Args:
            context: Basic context dictionary (can be None)

        Returns:
            Enhanced context dictionary with additional information

        Examples:
            >>> agent = AnalyzeAgent()
            >>> enhanced = agent.inject_context({"current_file": "src/main.py"})
            >>> isinstance(enhanced, dict)
            True
        """
        if context is None:
            return {}
        return context.copy()

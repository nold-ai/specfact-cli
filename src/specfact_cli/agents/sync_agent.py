"""
Sync Agent - Bidirectional sync with conflict resolution.

This module provides the SyncAgent for sync operations with enhanced
prompts and conflict resolution assistance for CoPilot integration.
"""

from __future__ import annotations

from typing import Any

from beartype import beartype
from icontract import ensure, require

from specfact_cli.agents.base import AgentMode


class SyncAgent(AgentMode):
    """
    Bidirectional sync agent with conflict resolution.

    Provides enhanced prompts for sync operations with conflict
    resolution assistance and change explanation.
    """

    @beartype
    @require(lambda command: bool(command), "Command must be non-empty")
    @ensure(lambda result: isinstance(result, str) and bool(result), "Prompt must be non-empty string")
    def generate_prompt(self, command: str, context: dict[str, Any] | None = None) -> str:
        """
        Generate enhanced prompt for sync operation.

        Args:
            command: CLI command being executed (e.g., "sync spec-kit", "sync repository")
            context: Context dictionary with current file, selection, workspace

        Returns:
            Enhanced prompt optimized for CoPilot

        Examples:
            >>> agent = SyncAgent()
            >>> prompt = agent.generate_prompt("sync spec-kit", {"workspace": "."})
            >>> "conflict" in prompt.lower()
            True
        """
        if context is None:
            context = {}

        current_file = context.get("current_file", "")
        selection = context.get("selection", "")
        workspace = context.get("workspace", "")

        prompt = f"""
Perform bidirectional sync with conflict resolution.

Context:
- Current file: {current_file or "None"}
- Selection: {selection or "None"}
- Workspace: {workspace or "None"}

Sync strategy:
1. Detect changes in Spec-Kit artifacts and .specfact/ artifacts
2. Automatic source detection
3. Conflict resolution assistance
4. Change explanation and preview

Generate interactive conflict resolution prompts.
"""
        return prompt.strip()

    @beartype
    @require(lambda command: bool(command), "Command must be non-empty")
    @ensure(lambda result: isinstance(result, dict), "Result must be a dictionary")
    def execute(
        self, command: str, args: dict[str, Any] | None = None, context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Execute sync command with enhanced prompts.

        Args:
            command: CLI command being executed (e.g., "sync spec-kit")
            args: Command arguments (e.g., {"source": "spec-kit", "target": ".specfact"})
            context: Context dictionary with current file, selection, workspace

        Returns:
            Command result with enhanced output

        Examples:
            >>> agent = SyncAgent()
            >>> result = agent.execute("sync spec-kit", {"source": "spec-kit"}, {"workspace": "."})
            >>> isinstance(result, dict)
            True
        """
        if args is None:
            args = {}
        if context is None:
            context = {}

        # Generate enhanced prompt
        prompt = self.generate_prompt(command, context)

        # For Phase 4.1, return structured result with prompt
        # In Phase 4.2+, this will route to actual command execution with agent mode
        return {
            "type": "sync",
            "command": command,
            "prompt": prompt,
            "args": args,
            "context": context,
            "enhanced": True,
        }

    @beartype
    @ensure(lambda result: isinstance(result, dict), "Result must be a dictionary")
    def inject_context(self, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Inject context information specific to sync operations.

        Args:
            context: Basic context dictionary (can be None)

        Returns:
            Enhanced context with sync-specific information

        Examples:
            >>> agent = SyncAgent()
            >>> enhanced = agent.inject_context({"workspace": "."})
            >>> isinstance(enhanced, dict)
            True
        """
        # Sync-specific context injection will be enhanced in Phase 4.2+
        # For now, just return the enhanced context from base class
        return super().inject_context(context)

"""
Plan Agent - Plan management with business logic understanding.

This module provides the PlanAgent for plan management operations with
enhanced prompts and context injection for CoPilot integration.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require

from specfact_cli.agents.base import AgentMode


class PlanAgent(AgentMode):
    """
    Plan management agent with business logic understanding.

    Provides enhanced prompts for plan management operations with
    context injection from IDE and repository analysis.
    """

    @beartype
    @require(lambda command: bool(command), "Command must be non-empty")
    @ensure(lambda result: isinstance(result, str) and bool(result), "Prompt must be non-empty string")
    def generate_prompt(self, command: str, context: dict[str, Any] | None = None) -> str:
        """
        Generate enhanced prompt for plan management.

        Args:
            command: CLI command being executed (e.g., "plan init", "plan compare")
            context: Context dictionary with current file, selection, workspace

        Returns:
            Enhanced prompt optimized for CoPilot

        Examples:
            >>> agent = PlanAgent()
            >>> prompt = agent.generate_prompt("plan init", {"current_file": "idea.yaml"})
            >>> "interactive" in prompt.lower()
            True
        """
        if context is None:
            context = {}

        current_file = context.get("current_file", "")
        selection = context.get("selection", "")
        workspace = context.get("workspace", "")

        if command in ("plan promote", "plan adopt"):
            auto_plan_path = context.get("auto_plan_path", "")
            auto_plan_content = ""
            if auto_plan_path and Path(auto_plan_path).exists():
                auto_plan_content = Path(auto_plan_path).read_text()[:500]  # Limit length

            prompt = f"""
Analyze the repository and cross-validate identified features/stories.

Repository Context:
- Workspace: {workspace or "None"}
- Current file: {current_file or "None"}
- Selection: {selection or "None"}

Auto-Derived Plan (from AST analysis):
{auto_plan_content[:500] if auto_plan_content else "None"}

Tasks:
1. Validate each identified feature exists in the codebase
2. Identify missing features that AST analysis missed
3. Identify false positives (classes/components that aren't features)
4. Cross-validate stories against actual code
5. Refine confidence scores based on code quality and documentation
6. Suggest theme categorization improvements
7. Extract business context from code comments/docs

Output Format:
- Validated features list with refined confidence scores
- Missing features (AI discovered, not in AST analysis)
- False positives (features to remove from plan)
- Story mapping validation (corrections needed)
- Theme categorization suggestions
- Business context extraction (idea, target users, value hypothesis)
"""
        elif command == "plan init":
            prompt = f"""
Initialize plan bundle with interactive wizard.

Context:
- Current file: {current_file or "None"}
- Selection: {selection or "None"}
- Workspace: {workspace or "None"}

Extract from context:
1. Idea from selection or current file
2. Business plan structure
3. Product plan themes
4. Features from workspace structure

Generate interactive prompts for missing information.
"""
        elif command == "plan compare":
            prompt = f"""
Compare manual vs auto-derived plans.

Context:
- Current file: {current_file or "None"}
- Selection: {selection or "None"}
- Workspace: {workspace or "None"}

Focus on:
1. Deviation explanations
2. Fix suggestions
3. Interactive deviation review

Generate rich console output with explanations.
"""
        else:
            prompt = f"Execute plan command: {command}"

        return prompt.strip()

    @beartype
    @require(lambda command: bool(command), "Command must be non-empty")
    @ensure(lambda result: isinstance(result, dict), "Result must be a dictionary")
    def execute(
        self, command: str, args: dict[str, Any] | None = None, context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Execute plan command with enhanced prompts.

        Args:
            command: CLI command being executed (e.g., "plan init")
            args: Command arguments (e.g., {"idea": "idea.yaml"})
            context: Context dictionary with current file, selection, workspace

        Returns:
            Command result with enhanced output

        Examples:
            >>> agent = PlanAgent()
            >>> result = agent.execute("plan init", {"idea": "idea.yaml"}, {"current_file": "idea.yaml"})
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
            "type": "plan",
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
        Inject context information specific to plan operations.

        Args:
            context: Basic context dictionary (can be None)

        Returns:
            Enhanced context with plan-specific information

        Examples:
            >>> agent = PlanAgent()
            >>> enhanced = agent.inject_context({"current_file": "idea.yaml"})
            >>> isinstance(enhanced, dict)
            True
        """
        enhanced = super().inject_context(context)

        # Add plan artifacts if workspace is available
        if enhanced.get("workspace"):
            workspace_path = Path(enhanced["workspace"])
            if workspace_path.exists() and workspace_path.is_dir():
                # Find plan artifacts
                plan_artifacts = {}
                specfact_dir = workspace_path / ".specfact"
                if specfact_dir.exists():
                    plans_dir = specfact_dir / "plans"
                    if plans_dir.exists():
                        plan_files = list(plans_dir.glob("*.yaml")) + list(plans_dir.glob("*.yml"))
                        plan_artifacts["plan_files"] = [str(f) for f in plan_files[:5]]  # Limit to first 5
                enhanced["plan_artifacts"] = plan_artifacts

        return enhanced

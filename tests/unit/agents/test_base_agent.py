"""
Unit tests for base agent mode.
"""

from __future__ import annotations

import pytest
from beartype import beartype

from specfact_cli.agents.analyze_agent import AnalyzeAgent
from specfact_cli.agents.base import AgentMode


class TestAgentMode:
    """Tests for AgentMode abstract base class."""

    @beartype
    def test_agent_mode_interface(self) -> None:
        """AgentMode interface must be implemented by subclasses."""
        # Should not be able to instantiate abstract class
        with pytest.raises(TypeError):
            AgentMode()  # type: ignore[abstract]

    @beartype
    def test_analyze_agent_implements_interface(self) -> None:
        """AnalyzeAgent implements AgentMode interface."""
        agent = AnalyzeAgent()
        assert isinstance(agent, AgentMode)
        assert hasattr(agent, "generate_prompt")
        assert hasattr(agent, "execute")
        assert hasattr(agent, "inject_context")

    @beartype
    def test_generate_prompt_returns_string(self) -> None:
        """generate_prompt must return a non-empty string."""
        agent = AnalyzeAgent()
        prompt = agent.generate_prompt("import from-code", {"current_file": "src/main.py"})
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    @beartype
    def test_execute_returns_dict(self) -> None:
        """execute must return a dictionary."""
        agent = AnalyzeAgent()
        result = agent.execute("import from-code", {"repo": "."}, {"current_file": "src/main.py"})
        assert isinstance(result, dict)
        assert result.get("type") == "analysis"
        assert result.get("enhanced") is True

    @beartype
    def test_inject_context_returns_dict(self) -> None:
        """inject_context must return a dictionary."""
        agent = AnalyzeAgent()
        enhanced = agent.inject_context({"current_file": "src/main.py"})
        assert isinstance(enhanced, dict)

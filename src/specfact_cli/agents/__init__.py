"""
Agent Modes - Enhanced prompts and routing for CoPilot-enabled mode.

This package provides agent mode framework for generating enhanced prompts
and routing commands with context injection for CoPilot integration.
"""

from __future__ import annotations

from specfact_cli.agents.analyze_agent import AnalyzeAgent
from specfact_cli.agents.base import AgentMode
from specfact_cli.agents.plan_agent import PlanAgent
from specfact_cli.agents.registry import AgentRegistry, get_agent
from specfact_cli.agents.sync_agent import SyncAgent


__all__ = [
    "AgentMode",
    "AgentRegistry",
    "AnalyzeAgent",
    "PlanAgent",
    "SyncAgent",
    "get_agent",
]

"""
Protocol data models.

This module defines Pydantic models for FSM protocols, states,
and transitions following the CLI-First specification.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Transition(BaseModel):
    """State machine transition."""

    from_state: str = Field(..., description="Source state")
    on_event: str = Field(..., description="Triggering event")
    to_state: str = Field(..., description="Target state")
    guard: str | None = Field(None, description="Guard function name")


class Protocol(BaseModel):
    """FSM protocol definition."""

    states: list[str] = Field(..., description="State names")
    start: str = Field(..., description="Initial state")
    transitions: list[Transition] = Field(..., description="State transitions")
    guards: dict[str, str] = Field(default_factory=dict, description="Guard definitions")

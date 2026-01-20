"""
Backlog filtering dataclass.

This module provides a standardized filtering interface for backlog adapters,
enabling consistent filtering across all backlog sources.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from beartype import beartype


@dataclass
@beartype
class BacklogFilters:
    """
    Standardized filtering interface for backlog adapters.

    All fields are optional to support extensibility and partial filtering.
    Adapters should apply filters as appropriate for their provider's capabilities.
    """

    assignee: str | None = None
    """Filter by assignee username."""
    state: str | None = None
    """Filter by state (open, closed, etc.)."""
    labels: list[str] | None = None
    """Filter by labels/tags (list of label names)."""
    search: str | None = None
    """Provider-specific search query."""
    area: str | None = None
    """Filter by area path (provider-specific)."""
    iteration: str | None = None
    """Filter by iteration path (provider-specific)."""
    sprint: str | None = None
    """Filter by sprint identifier."""
    release: str | None = None
    """Filter by release identifier."""

    def to_dict(self) -> dict[str, Any]:
        """
        Convert filters to dictionary, excluding None values.

        Returns:
            Dictionary with non-None filter values
        """
        return {k: v for k, v in self.__dict__.items() if v is not None}

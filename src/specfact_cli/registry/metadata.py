"""
Command metadata model for registry discovery and help cache.

Metadata is stored at registration time; accessing it does not trigger module load.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class CommandMetadata(BaseModel):
    """Metadata for a registered command (name, help, tier, optional addon/subcommands)."""

    name: str = Field(..., description="Command group name (e.g. 'init', 'backlog')")
    help: str = Field(..., description="Help string for the command group")
    tier: str = Field(default="community", description="Tier: 'community' or 'enterprise'")
    addon_id: str | None = Field(default=None, description="Optional addon identifier")
    subcommands: list[str] | None = Field(default=None, description="Optional list of subcommand names")

"""Tool capabilities data model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ToolCapabilities:
    """Detected tool capabilities and configuration."""

    tool: str  # Tool name (e.g., "speckit", "openspec")
    version: str | None = None  # Tool version if detectable
    layout: str = "classic"  # Layout type: "classic", "modern", "openspec", etc.
    specs_dir: str = "specs"  # Specs directory path (relative to repo root)
    has_external_config: bool = False  # Has external configuration files
    has_custom_hooks: bool = False  # Has custom hooks or scripts
    supported_sync_modes: list[str] | None = (
        None  # Supported sync modes (e.g., ["bidirectional", "unidirectional", "read-only", "export-only"])
    )

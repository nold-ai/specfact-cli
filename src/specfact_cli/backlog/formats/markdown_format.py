"""
Markdown format implementation for backlog items.

This module provides Markdown serialization for BacklogItem instances,
supporting optional YAML frontmatter for metadata.
"""

from __future__ import annotations

import re
from typing import Any

from beartype import beartype
from icontract import ensure, require

from specfact_cli.backlog.formats.base import BacklogFormat
from specfact_cli.models.backlog_item import BacklogItem


class MarkdownFormat(BacklogFormat):
    """
    Markdown format serializer/deserializer for backlog items.

    Supports:
    - Plain markdown (body_markdown only)
    - Markdown with YAML frontmatter (for provider_fields metadata)
    """

    @property
    @beartype
    def format_type(self) -> str:
        """Get format type identifier."""
        return "markdown"

    @beartype
    @require(lambda item: isinstance(item, BacklogItem), "Item must be BacklogItem")
    @ensure(lambda result: isinstance(result, str), "Must return string")
    def serialize(self, item: BacklogItem) -> str:
        """
        Serialize BacklogItem to markdown.

        If provider_fields exist, includes YAML frontmatter.

        Args:
            item: BacklogItem to serialize

        Returns:
            Markdown string with optional YAML frontmatter
        """
        lines: list[str] = []

        # Add YAML frontmatter if provider_fields exist
        if item.provider_fields:
            lines.append("---")
            # Convert provider_fields to YAML (simple key-value pairs)
            for key, value in item.provider_fields.items():
                if isinstance(value, (str, int, float, bool)):
                    lines.append(f"{key}: {value}")
                elif isinstance(value, dict):
                    # Simple dict representation
                    lines.append(f"{key}:")
                    for sub_key, sub_value in value.items():
                        lines.append(f"  {sub_key}: {sub_value}")
            lines.append("---")
            lines.append("")

        # Add body markdown
        lines.append(item.body_markdown)

        return "\n".join(lines)

    @beartype
    @require(lambda raw: isinstance(raw, str), "Raw must be string")
    @ensure(lambda result: isinstance(result, BacklogItem), "Must return BacklogItem")
    def deserialize(self, raw: str) -> BacklogItem:
        """
        Deserialize markdown to BacklogItem.

        Parses YAML frontmatter if present, otherwise uses body as-is.

        Args:
            raw: Markdown string with optional YAML frontmatter

        Returns:
            BacklogItem instance

        Note:
            This is a simplified implementation. For production use, consider
            using a proper YAML parser for frontmatter extraction.
        """
        provider_fields: dict[str, Any] = {}
        body_markdown = raw

        # Check for YAML frontmatter
        frontmatter_pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
        match = re.match(frontmatter_pattern, raw, re.DOTALL)

        if match:
            frontmatter_text = match.group(1)
            body_markdown = match.group(2)

            # Parse simple YAML frontmatter (key: value pairs)
            for line in frontmatter_text.split("\n"):
                line = line.strip()
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip()
                    value = value.strip()
                    # Try to parse value as appropriate type
                    if value.lower() == "true":
                        provider_fields[key] = True
                    elif value.lower() == "false":
                        provider_fields[key] = False
                    elif value.isdigit():
                        provider_fields[key] = int(value)
                    else:
                        provider_fields[key] = value

        # Create minimal BacklogItem (requires id, provider, url, title, state)
        # This is a simplified implementation - in practice, you'd need more context
        # For now, we'll create a placeholder item
        return BacklogItem(
            id="placeholder",
            provider="unknown",
            url="",
            title="",
            body_markdown=body_markdown,
            state="open",
            provider_fields=provider_fields if provider_fields else {},
        )

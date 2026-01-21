"""
Format detection for backlog content.

This module provides heuristics to automatically detect the format of raw
backlog content (JSON, YAML, or Markdown).
"""

from __future__ import annotations

from beartype import beartype
from icontract import ensure, require


@beartype
@require(lambda raw: isinstance(raw, str), "Raw must be string")
@ensure(lambda result: result in ("json", "yaml", "markdown"), "Must return valid format type")
def detect_format(raw: str) -> str:
    """
    Detect the format of raw backlog content.

    Uses heuristics:
    - JSON: starts with "{" or "["
    - YAML: starts with "---" or contains ":" in first line
    - Markdown: default for other cases

    Args:
        raw: Raw content string

    Returns:
        Format type ("json", "yaml", or "markdown")
    """
    stripped = raw.strip()

    # Detect JSON (starts with { or [)
    if stripped.startswith(("{", "[")):
        return "json"

    # Detect YAML (starts with --- or has : in first line)
    if stripped.startswith("---"):
        return "yaml"

    first_line = stripped.split("\n")[0] if "\n" in stripped else stripped
    if ":" in first_line and not first_line.startswith("#"):
        # Check if it looks like YAML (key: value pattern)
        parts = first_line.split(":", 1)
        if len(parts) == 2 and parts[0].strip() and parts[1].strip():
            return "yaml"

    # Default to markdown
    return "markdown"

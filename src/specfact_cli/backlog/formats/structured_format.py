"""
Structured format implementation (YAML/JSON) for backlog items.

This module provides YAML and JSON serialization for BacklogItem instances.
"""

from __future__ import annotations

import json

from beartype import beartype
from icontract import ensure, require
from ruamel.yaml import YAML

from specfact_cli.backlog.formats.base import BacklogFormat
from specfact_cli.models.backlog_item import BacklogItem


class StructuredFormat(BacklogFormat):
    """
    Structured format serializer/deserializer (YAML/JSON) for backlog items.

    Supports both YAML and JSON format types.
    """

    def __init__(self, format_type: str = "yaml") -> None:
        """
        Initialize structured format.

        Args:
            format_type: Format type ("yaml" or "json")
        """
        if format_type not in ("yaml", "json"):
            msg = f"Format type must be 'yaml' or 'json', got: {format_type}"
            raise ValueError(msg)
        self._format_type = format_type
        self._yaml = YAML() if format_type == "yaml" else None

    @property
    @beartype
    def format_type(self) -> str:
        """Get format type identifier."""
        return self._format_type

    @beartype
    @require(lambda item: isinstance(item, BacklogItem), "Item must be BacklogItem")
    @ensure(lambda result: isinstance(result, str), "Must return string")
    def serialize(self, item: BacklogItem) -> str:
        """
        Serialize BacklogItem to YAML or JSON.

        Args:
            item: BacklogItem to serialize

        Returns:
            YAML or JSON string representation
        """
        # Convert BacklogItem to dict
        data = item.model_dump()

        if self._format_type == "yaml":
            # Serialize to YAML
            from io import StringIO

            if self._yaml is None:
                msg = "YAML instance not initialized"
                raise ValueError(msg)
            stream = StringIO()
            self._yaml.dump(data, stream)
            return stream.getvalue()
        # Serialize to JSON
        return json.dumps(data, indent=2, default=str)

    @beartype
    @require(lambda raw: isinstance(raw, str), "Raw must be string")
    @ensure(lambda result: isinstance(result, BacklogItem), "Must return BacklogItem")
    def deserialize(self, raw: str) -> BacklogItem:
        """
        Deserialize YAML or JSON to BacklogItem.

        Args:
            raw: YAML or JSON string

        Returns:
            BacklogItem instance
        """
        # Deserialize from YAML or JSON
        if self._format_type == "yaml":
            if self._yaml is None:
                msg = "YAML instance not initialized"
                raise ValueError(msg)
            data = self._yaml.load(raw)
        else:
            data = json.loads(raw)

        # Create BacklogItem from dict
        return BacklogItem(**data)

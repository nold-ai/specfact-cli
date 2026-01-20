"""
Backlog format abstraction base class.

This module defines the BacklogFormat interface for serializing and deserializing
backlog items across different formats (Markdown, YAML, JSON).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from beartype import beartype
from icontract import ensure, require

from specfact_cli.models.backlog_item import BacklogItem


class BacklogFormat(ABC):
    """
    Abstract base class for backlog format serialization.

    This class provides a standard interface for converting BacklogItem instances
    to and from different formats (Markdown, YAML, JSON).
    """

    @property
    @abstractmethod
    @beartype
    @ensure(lambda result: isinstance(result, str) and len(result) > 0, "Must return non-empty format type")
    def format_type(self) -> str:
        """
        Get the format type identifier.

        Returns:
            Format type (e.g., "markdown", "yaml", "json")
        """
        ...

    @abstractmethod
    @beartype
    @require(lambda item: isinstance(item, BacklogItem), "Item must be BacklogItem")
    @ensure(lambda result: isinstance(result, str), "Must return string")
    def serialize(self, item: BacklogItem) -> str:
        """
        Serialize a BacklogItem to the format.

        Args:
            item: BacklogItem to serialize

        Returns:
            Serialized string representation
        """
        ...

    @abstractmethod
    @beartype
    @require(lambda raw: isinstance(raw, str), "Raw must be string")
    @ensure(lambda result: isinstance(result, BacklogItem), "Must return BacklogItem")
    def deserialize(self, raw: str) -> BacklogItem:
        """
        Deserialize a string to a BacklogItem.

        Args:
            raw: Raw string representation

        Returns:
            BacklogItem instance
        """
        ...

    @beartype
    @require(lambda item: isinstance(item, BacklogItem), "Item must be BacklogItem")
    @ensure(lambda result: isinstance(result, bool), "Must return boolean")
    def roundtrip_preserves_content(self, item: BacklogItem) -> bool:
        """
        Verify that serialization followed by deserialization preserves content.

        Args:
            item: Original BacklogItem

        Returns:
            True if round-trip preserves content, False otherwise

        Note:
            This method has a default implementation but can be overridden
            by formats that need custom validation logic.
        """
        serialized = self.serialize(item)
        deserialized = self.deserialize(serialized)
        return (
            item.id == deserialized.id
            and item.provider == deserialized.provider
            and item.title == deserialized.title
            and item.body_markdown == deserialized.body_markdown
            and item.state == deserialized.state
            and item.assignees == deserialized.assignees
            and item.tags == deserialized.tags
        )

"""Jira backlog bridge converter."""

from __future__ import annotations

from pathlib import Path

from beartype import beartype

from specfact_cli.modules.backlog.src.adapters.base import MappingBackedConverter


@beartype
class JiraConverter(MappingBackedConverter):
    """Jira converter."""

    def __init__(self, mapping_file: Path | None = None) -> None:
        super().__init__(
            service_name="jira",
            default_to_bundle={"id": "id", "title": "fields.summary"},
            default_from_bundle={"id": "id", "fields.summary": "title"},
            mapping_file=str(mapping_file) if mapping_file is not None else None,
        )

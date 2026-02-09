"""ADO backlog bridge converter."""

from __future__ import annotations

from pathlib import Path

from beartype import beartype

from specfact_cli.modules.backlog.src.adapters.base import MappingBackedConverter


@beartype
class AdoConverter(MappingBackedConverter):
    """Azure DevOps converter."""

    def __init__(self, mapping_file: Path | None = None) -> None:
        super().__init__(
            service_name="ado",
            default_to_bundle={"id": "System.Id", "title": "System.Title"},
            default_from_bundle={"System.Id": "id", "System.Title": "title"},
            mapping_file=mapping_file,
        )

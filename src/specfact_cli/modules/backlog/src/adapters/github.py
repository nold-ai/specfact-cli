"""GitHub backlog bridge converter."""

from __future__ import annotations

from pathlib import Path

from beartype import beartype

from specfact_cli.modules.backlog.src.adapters.base import MappingBackedConverter


@beartype
class GitHubConverter(MappingBackedConverter):
    """GitHub converter."""

    def __init__(self, mapping_file: Path | None = None) -> None:
        super().__init__(
            service_name="github",
            default_to_bundle={"id": "number", "title": "title"},
            default_from_bundle={"number": "id", "title": "title"},
            mapping_file=str(mapping_file) if mapping_file is not None else None,
        )

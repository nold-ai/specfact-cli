"""Linear backlog bridge converter."""

from __future__ import annotations

from beartype import beartype

from specfact_cli.modules.backlog.src.adapters.base import MappingBackedConverter


@beartype
class LinearConverter(MappingBackedConverter):
    """Linear converter."""

    def __init__(self, mapping_file: str | None = None) -> None:
        super().__init__(
            service_name="linear",
            default_to_bundle={"id": "id", "title": "title"},
            default_from_bundle={"id": "id", "title": "title"},
            mapping_file=mapping_file,
        )

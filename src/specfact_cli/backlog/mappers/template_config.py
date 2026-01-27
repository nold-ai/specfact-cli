"""
Template configuration schema for custom ADO field mappings.

This module defines the schema for YAML-based field mapping configurations
that allow teams to customize ADO field mappings for their specific templates.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from beartype import beartype
from icontract import ensure, require
from pydantic import BaseModel, Field


class FieldMappingConfig(BaseModel):
    """
    Field mapping configuration for ADO templates.

    Maps ADO field names to canonical field names, supporting custom templates
    and framework-specific mappings (Scrum, SAFe, Kanban).
    """

    # Framework identifier (scrum, safe, kanban, agile, default)
    framework: str = Field(default="default", description="Agile framework (scrum, safe, kanban, agile, default)")

    # Field mappings: ADO field name -> canonical field name
    field_mappings: dict[str, str] = Field(
        default_factory=dict,
        description="Mapping from ADO field names to canonical field names",
    )

    # Work item type mappings: ADO work item type -> canonical work item type
    work_item_type_mappings: dict[str, str] = Field(
        default_factory=dict,
        description="Mapping from ADO work item types to canonical work item types",
    )

    @beartype
    @classmethod
    @require(lambda cls, file_path: isinstance(file_path, (str, Path)), "File path must be str or Path")
    @ensure(lambda result: isinstance(result, FieldMappingConfig), "Must return FieldMappingConfig")
    def from_file(cls, file_path: str | Path) -> FieldMappingConfig:
        """
        Load field mapping configuration from YAML file.

        Args:
            file_path: Path to YAML configuration file

        Returns:
            FieldMappingConfig instance

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is invalid
        """
        path = Path(file_path)
        if not path.exists():
            msg = f"Field mapping file not found: {file_path}"
            raise FileNotFoundError(msg)

        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not isinstance(data, dict):
            msg = f"Invalid field mapping file format: {file_path}"
            raise ValueError(msg)

        return cls(**data)

    @beartype
    @require(lambda self, ado_field_name: isinstance(ado_field_name, str), "ADO field name must be str")
    @ensure(lambda result: result is None or isinstance(result, str), "Must return str or None")
    def map_to_canonical(self, ado_field_name: str) -> str | None:
        """
        Map ADO field name to canonical field name.

        Args:
            ado_field_name: ADO field name (e.g., "System.Description")

        Returns:
            Canonical field name or None if not mapped
        """
        return self.field_mappings.get(ado_field_name)

    @beartype
    @require(lambda self, ado_work_item_type: isinstance(ado_work_item_type, str), "ADO work item type must be str")
    @ensure(lambda result: result is None or isinstance(result, str), "Must return str or None")
    def map_work_item_type(self, ado_work_item_type: str) -> str | None:
        """
        Map ADO work item type to canonical work item type.

        Args:
            ado_work_item_type: ADO work item type (e.g., "Product Backlog Item")

        Returns:
            Canonical work item type or None if not mapped
        """
        return self.work_item_type_mappings.get(ado_work_item_type, ado_work_item_type)

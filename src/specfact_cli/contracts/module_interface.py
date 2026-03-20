"""Module IO protocol contract for module bundle interactions."""

from __future__ import annotations

from abc import abstractmethod
from pathlib import Path
from typing import Any, Protocol

from beartype import beartype
from icontract import ensure, require

from specfact_cli.models.project import ProjectBundle
from specfact_cli.models.validation import ValidationReport


class ModuleIOContract(Protocol):
    """Protocol for module implementations that exchange data via ProjectBundle."""

    @abstractmethod
    @beartype
    @require(lambda source: isinstance(source, Path), "source must be a Path")
    def import_to_bundle(self, source: Path, config: dict[str, Any]) -> ProjectBundle:
        """Import an external artifact and convert it into a ProjectBundle."""

    @abstractmethod
    @beartype
    @require(lambda target: isinstance(target, Path), "target must be a Path")
    def export_from_bundle(self, bundle: ProjectBundle, target: Path, config: dict[str, Any]) -> None:
        """Export a ProjectBundle to an external artifact format."""

    @abstractmethod
    @beartype
    @require(lambda external_source: external_source.strip() != "", "external_source must not be empty")
    def sync_with_bundle(self, bundle: ProjectBundle, external_source: str, config: dict[str, Any]) -> ProjectBundle:
        """Synchronize a bundle with an external source and return the updated bundle."""

    @abstractmethod
    @beartype
    @ensure(lambda result: isinstance(result, ValidationReport))
    def validate_bundle(self, bundle: ProjectBundle, rules: dict[str, Any]) -> ValidationReport:
        """Run module-specific validation on a ProjectBundle."""

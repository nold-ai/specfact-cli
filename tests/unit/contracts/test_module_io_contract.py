"""Tests for ModuleIOContract protocol and ValidationReport model."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from specfact_cli.contracts.module_interface import ModuleIOContract
from specfact_cli.models.project import ProjectBundle
from specfact_cli.models.validation import ValidationReport


class FullProtocolModule:
    """Implements all required protocol methods without explicit inheritance."""

    def import_to_bundle(self, source: Path, config: dict[str, Any]) -> ProjectBundle:
        raise NotImplementedError

    def export_from_bundle(self, bundle: ProjectBundle, target: Path, config: dict[str, Any]) -> None:
        raise NotImplementedError

    def sync_with_bundle(self, bundle: ProjectBundle, external_source: str, config: dict[str, Any]) -> ProjectBundle:
        raise NotImplementedError

    def validate_bundle(self, bundle: ProjectBundle, rules: dict[str, Any]) -> ValidationReport:
        return ValidationReport(status="passed")


class PartialProtocolModule:
    """Implements only a subset of protocol methods."""

    def import_to_bundle(self, source: Path, config: dict[str, Any]) -> ProjectBundle:
        raise NotImplementedError

    def validate_bundle(self, bundle: ProjectBundle, rules: dict[str, Any]) -> ValidationReport:
        return ValidationReport(status="warnings")


def test_protocol_defines_four_operations() -> None:
    """Verify protocol exposes the four required operations."""
    required = {
        "import_to_bundle",
        "export_from_bundle",
        "sync_with_bundle",
        "validate_bundle",
    }
    assert required.issubset(set(ModuleIOContract.__dict__.keys()))


def test_module_without_inheritance_satisfies_protocol() -> None:
    """Structural typing: full implementation satisfies protocol without inheritance."""
    module = FullProtocolModule()
    protocol_typed: ModuleIOContract = module
    assert protocol_typed is module


def test_module_with_partial_implementation_type_checked() -> None:
    """Partial implementation does not satisfy full runtime contract shape."""
    module = PartialProtocolModule()
    assert hasattr(module, "import_to_bundle")
    assert hasattr(module, "validate_bundle")
    assert not hasattr(module, "export_from_bundle")
    assert not hasattr(module, "sync_with_bundle")


def test_validation_report_model_structure() -> None:
    """ValidationReport provides status, violations, and summary fields."""
    report = ValidationReport(status="failed")
    assert report.status == "failed"
    assert isinstance(report.violations, list)
    assert isinstance(report.summary, dict)
    assert set(report.summary.keys()) == {"total_checks", "passed", "failed", "warnings"}

    with pytest.raises(ValidationError):
        ValidationReport(status="invalid")

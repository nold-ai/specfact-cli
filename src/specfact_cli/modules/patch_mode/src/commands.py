"""Patch module commands entrypoint (convention: src/commands re-exports app and ModuleIOContract)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require

from specfact_cli.models.plan import Product
from specfact_cli.models.project import BundleManifest, ProjectBundle
from specfact_cli.models.validation import ValidationReport
from specfact_cli.modules.patch_mode.src.patch_mode.commands.apply import app


@beartype
@require(lambda source: source.exists(), "Source path must exist")
@ensure(lambda result: isinstance(result, ProjectBundle), "Must return ProjectBundle")
def import_to_bundle(source: Path, config: dict[str, Any]) -> ProjectBundle:
    """Convert external source into a ProjectBundle (patch-mode stub: no bundle I/O)."""
    bundle_name = config.get("bundle_name", source.stem if source.suffix else source.name)
    return ProjectBundle(
        manifest=BundleManifest(schema_metadata=None, project_metadata=None),
        bundle_name=str(bundle_name),
        product=Product(),
    )


@beartype
@require(lambda target: target is not None, "Target path must be provided")
@ensure(lambda result: result is None, "Export returns None")
def export_from_bundle(bundle: ProjectBundle, target: Path, config: dict[str, Any]) -> None:
    """Export a ProjectBundle to target (patch-mode stub: no-op)."""
    return


@beartype
@require(lambda external_source: isinstance(external_source, str), "External source must be string")
@ensure(lambda result: isinstance(result, ProjectBundle), "Must return ProjectBundle")
def sync_with_bundle(bundle: ProjectBundle, external_source: str, config: dict[str, Any]) -> ProjectBundle:
    """Sync bundle with external source (patch-mode stub: return bundle unchanged)."""
    return bundle


@beartype
@ensure(lambda result: isinstance(result, ValidationReport), "Must return ValidationReport")
def validate_bundle(bundle: ProjectBundle, rules: dict[str, Any]) -> ValidationReport:
    """Validate bundle (patch-mode stub: always passed)."""
    total_checks = max(len(rules), 1)
    return ValidationReport(
        status="passed",
        violations=[],
        summary={"total_checks": total_checks, "passed": total_checks, "failed": 0, "warnings": 0},
    )


__all__ = ["app", "export_from_bundle", "import_to_bundle", "sync_with_bundle", "validate_bundle"]

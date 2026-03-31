"""Shared ModuleIOContract helper functions for module command packages."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from beartype import beartype
from icontract import ensure, require

from specfact_cli.models.plan import Product
from specfact_cli.models.project import BundleManifest, ProjectBundle
from specfact_cli.models.validation import ValidationReport


def _import_source_exists(source: Path) -> bool:
    return source.exists()


def _external_source_nonempty(external_source: str) -> bool:
    return len(external_source.strip()) > 0


@beartype
@require(_import_source_exists, "Source path must exist")
@ensure(lambda result: isinstance(result, ProjectBundle), "Must return ProjectBundle")
def import_to_bundle(source: Path, config: dict[str, Any]) -> ProjectBundle:
    """Convert external source artifacts into a ProjectBundle."""
    if source.is_dir() and (source / "bundle.manifest.yaml").exists():
        return ProjectBundle.load_from_directory(source)
    bundle_name = config.get("bundle_name", source.stem if source.suffix else source.name)
    return ProjectBundle(
        manifest=BundleManifest(schema_metadata=None, project_metadata=None),
        bundle_name=str(bundle_name),
        product=Product(),
    )


@beartype
@require(lambda target: target is not None, "Target path must be provided")
@ensure(lambda result, bundle, target, config: cast(Path, target).exists(), "Target must exist after export")
def export_from_bundle(bundle: ProjectBundle, target: Path, config: dict[str, Any]) -> None:
    """Export a ProjectBundle to a target path."""
    if target.suffix:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(bundle.model_dump_json(indent=2), encoding="utf-8")
        return
    target.mkdir(parents=True, exist_ok=True)
    bundle.save_to_directory(target)


@beartype
@require(_external_source_nonempty, "External source must be non-empty")
@ensure(lambda result: isinstance(result, ProjectBundle), "Must return ProjectBundle")
def sync_with_bundle(bundle: ProjectBundle, external_source: str, config: dict[str, Any]) -> ProjectBundle:
    """Synchronize an existing bundle with an external source."""
    source_path = Path(external_source)
    if source_path.exists() and source_path.is_dir() and (source_path / "bundle.manifest.yaml").exists():
        return ProjectBundle.load_from_directory(source_path)
    return bundle


@beartype
@require(lambda rules: isinstance(rules, dict), "Rules must be a dictionary")
@ensure(lambda result: isinstance(result, ValidationReport), "Must return ValidationReport")
def validate_bundle(bundle: ProjectBundle, rules: dict[str, Any]) -> ValidationReport:
    """Validate bundle for generic module constraints."""
    total_checks = max(len(rules), 1)
    report = ValidationReport(
        status="passed",
        violations=[],
        summary={"total_checks": total_checks, "passed": total_checks, "failed": 0, "warnings": 0},
    )
    if not bundle.bundle_name:
        report.status = "failed"
        report.violations.append(
            {
                "severity": "error",
                "message": "Bundle name is required",
                "location": "ProjectBundle.bundle_name",
            }
        )
        report.summary["failed"] += 1
        report.summary["passed"] = max(report.summary["passed"] - 1, 0)
    return report

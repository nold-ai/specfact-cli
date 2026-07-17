"""Requirements context adapter helpers."""

from specfact_cli.requirements.context import (
    RequirementContextAdapter,
    RequirementContextCoverageSummary,
    RequirementContextDiagnostic,
    RequirementContextDiagnosticSeverity,
    RequirementContextImportResult,
    attach_requirements_to_bundle,
    inspect_requirement_context_coverage,
    load_requirements_from_bundle,
    normalize_requirement_records,
    requires_native_openspec_validation,
    validate_requirement_context,
)
from specfact_cli.requirements.importers import import_openspec_change, import_speckit_feature


__all__ = [
    "RequirementContextAdapter",
    "RequirementContextCoverageSummary",
    "RequirementContextDiagnostic",
    "RequirementContextDiagnosticSeverity",
    "RequirementContextImportResult",
    "attach_requirements_to_bundle",
    "import_openspec_change",
    "import_speckit_feature",
    "inspect_requirement_context_coverage",
    "load_requirements_from_bundle",
    "normalize_requirement_records",
    "requires_native_openspec_validation",
    "validate_requirement_context",
]

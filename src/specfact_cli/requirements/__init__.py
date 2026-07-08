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
    validate_requirement_context,
)


__all__ = [
    "RequirementContextAdapter",
    "RequirementContextCoverageSummary",
    "RequirementContextDiagnostic",
    "RequirementContextDiagnosticSeverity",
    "RequirementContextImportResult",
    "attach_requirements_to_bundle",
    "inspect_requirement_context_coverage",
    "load_requirements_from_bundle",
    "normalize_requirement_records",
    "validate_requirement_context",
]

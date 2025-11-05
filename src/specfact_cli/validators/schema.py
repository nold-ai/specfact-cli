"""
Schema validation module.

This module provides schema validation for plan bundles and protocols.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import yaml
from beartype import beartype
from icontract import ensure, require
from pydantic import ValidationError

from specfact_cli.models.deviation import Deviation, DeviationSeverity, DeviationType, ValidationReport
from specfact_cli.models.plan import PlanBundle
from specfact_cli.models.protocol import Protocol


class SchemaValidator:
    """Schema validator for plan bundles and protocols."""

    def __init__(self, schemas_dir: Path | None = None):
        """
        Initialize schema validator.

        Args:
            schemas_dir: Directory containing JSON schemas (default: resources/schemas)
        """
        if schemas_dir is None:
            # Default to resources/schemas relative to project root
            schemas_dir = Path(__file__).parent.parent.parent.parent / "resources" / "schemas"

        self.schemas_dir = Path(schemas_dir)
        self._schemas: dict[str, dict] = {}

    def _load_schema(self, schema_name: str) -> dict:
        """
        Load JSON schema from file.

        Args:
            schema_name: Name of the schema file (with or without .schema.json extension)

        Returns:
            Loaded schema dict

        Raises:
            FileNotFoundError: If schema file doesn't exist
        """
        if schema_name not in self._schemas:
            # Handle both "plan" and "plan.schema.json" as input
            if schema_name.endswith(".schema.json"):
                schema_path = self.schemas_dir / schema_name
            elif schema_name.endswith(".json"):
                # Just add .schema if only .json is present
                schema_path = self.schemas_dir / schema_name.replace(".json", ".schema.json")
            else:
                # Add full suffix
                schema_path = self.schemas_dir / f"{schema_name}.schema.json"

            if not schema_path.exists():
                raise FileNotFoundError(f"Schema file not found: {schema_path}")

            with open(schema_path, encoding="utf-8") as f:
                self._schemas[schema_name] = json.load(f)

        return self._schemas[schema_name]

    @beartype
    @require(lambda data: isinstance(data, dict), "Data must be dictionary")
    @require(
        lambda schema_name: isinstance(schema_name, str) and len(schema_name) > 0,
        "Schema name must be non-empty string",
    )
    @ensure(lambda result: isinstance(result, ValidationReport), "Must return ValidationReport")
    def validate_json_schema(self, data: dict, schema_name: str) -> ValidationReport:
        """
        Validate data against JSON schema.

        Args:
            data: Data to validate
            schema_name: Name of the schema (e.g., 'plan', 'protocol', 'deviation')

        Returns:
            Validation report
        """
        report = ValidationReport()

        try:
            schema = self._load_schema(schema_name)
            jsonschema.validate(instance=data, schema=schema)

        except jsonschema.ValidationError as e:
            deviation = Deviation(
                type=DeviationType.FSM_MISMATCH,  # Generic type for schema violations
                severity=DeviationSeverity.HIGH,
                description=f"Schema validation failed: {e.message}",
                location=f"${'.'.join(str(p) for p in e.path)}" if e.path else "root",
                fix_hint=f"Expected {e.validator}: {e.validator_value}",
            )
            report.add_deviation(deviation)

        except FileNotFoundError as e:
            deviation = Deviation(
                type=DeviationType.FSM_MISMATCH,
                severity=DeviationSeverity.HIGH,
                description=str(e),
                location="schema",
                fix_hint="Ensure the schema file exists in the schemas directory",
            )
            report.add_deviation(deviation)

        return report


@beartype
@ensure(
    lambda result: isinstance(result, ValidationReport)
    or (isinstance(result, tuple) and len(result) == 3 and isinstance(result[0], bool)),
    "Must return ValidationReport or tuple[bool, str | None, PlanBundle | None]",
)
def validate_plan_bundle(
    plan_or_path: PlanBundle | Path,
) -> ValidationReport | tuple[bool, str | None, PlanBundle | None]:
    """
    Validate a plan bundle model or YAML file.

    Args:
        plan_or_path: PlanBundle model or Path to plan bundle YAML file

    Returns:
        ValidationReport if model provided, tuple of (is_valid, error_message, parsed_bundle) if path provided
    """
    # If it's already a model, just return success report
    if isinstance(plan_or_path, PlanBundle):
        return ValidationReport()

    # Otherwise treat as path
    path = plan_or_path
    try:
        with path.open("r") as f:
            data = yaml.safe_load(f)

        bundle = PlanBundle(**data)
        return True, None, bundle

    except FileNotFoundError:
        return False, f"File not found: {path}", None
    except yaml.YAMLError as e:
        return False, f"YAML parsing error: {e}", None
    except ValidationError as e:
        return False, f"Validation error: {e}", None
    except Exception as e:
        return False, f"Unexpected error: {e}", None


@beartype
@ensure(
    lambda result: isinstance(result, ValidationReport)
    or (isinstance(result, tuple) and len(result) == 3 and isinstance(result[0], bool)),
    "Must return ValidationReport or tuple[bool, str | None, Protocol | None]",
)
def validate_protocol(protocol_or_path: Protocol | Path) -> ValidationReport | tuple[bool, str | None, Protocol | None]:
    """
    Validate a protocol model or YAML file.

    Args:
        protocol_or_path: Protocol model or Path to protocol YAML file

    Returns:
        ValidationReport if model provided, tuple of (is_valid, error_message, parsed_protocol) if path provided
    """
    # If it's already a model, just return success report
    if isinstance(protocol_or_path, Protocol):
        return ValidationReport()

    # Otherwise treat as path
    path = protocol_or_path
    try:
        with path.open("r") as f:
            data = yaml.safe_load(f)

        protocol = Protocol(**data)
        return True, None, protocol

    except FileNotFoundError:
        return False, f"File not found: {path}", None
    except yaml.YAMLError as e:
        return False, f"YAML parsing error: {e}", None
    except ValidationError as e:
        return False, f"Validation error: {e}", None
    except Exception as e:
        return False, f"Unexpected error: {e}", None

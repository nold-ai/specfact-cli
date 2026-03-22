"""
Specification templates for high-quality artifacts.

This module provides templates for feature specifications, implementation plans,
and contract extraction following SpecKit SDD principles.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from beartype import beartype
from icontract import ensure, require


def _feature_spec_keys_nonblank(
    feature_key: str, feature_name: str, user_needs: list[str], business_value: str
) -> bool:
    return feature_key.strip() != "" and feature_name.strip() != ""


def _plan_key_nonblank(plan_key: str, _high_level_steps: list[str], _implementation_details_path: str) -> bool:
    return plan_key.strip() != ""


def _contract_paths_nonblank(contract_key: str, openapi_spec_path: str) -> bool:
    return contract_key.strip() != "" and openapi_spec_path.strip() != ""


@dataclass
class FeatureSpecificationTemplate:
    """Template for feature specifications (brownfield enhancement)."""

    feature_key: str
    feature_name: str
    user_needs: list[str]
    business_value: str
    ambiguities: list[str]  # Marked as [NEEDS CLARIFICATION: question]
    completeness_checklist: dict[str, bool]

    @beartype
    @ensure(lambda result: isinstance(result, dict), "Must return a dictionary")
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "feature_key": self.feature_key,
            "feature_name": self.feature_name,
            "user_needs": self.user_needs,
            "business_value": self.business_value,
            "ambiguities": self.ambiguities,
            "completeness_checklist": self.completeness_checklist,
        }


@dataclass
class ImplementationPlanTemplate:
    """Template for implementation plans (modernization roadmap)."""

    plan_key: str
    high_level_steps: list[str]
    implementation_details_path: str  # Path to implementation-details/ files
    test_first_approach: bool
    phase_gates: list[str]

    @beartype
    @ensure(lambda result: isinstance(result, dict), "Must return a dictionary")
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "plan_key": self.plan_key,
            "high_level_steps": self.high_level_steps,
            "implementation_details_path": self.implementation_details_path,
            "test_first_approach": self.test_first_approach,
            "phase_gates": self.phase_gates,
        }


@dataclass
class ContractExtractionTemplate:
    """Template for contract extraction (from legacy code)."""

    contract_key: str
    openapi_spec_path: str
    uncertainty_markers: list[str]  # Marked as [NEEDS CLARIFICATION: question]
    validation_checklist: dict[str, bool]

    @beartype
    @ensure(lambda result: isinstance(result, dict), "Must return a dictionary")
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "contract_key": self.contract_key,
            "openapi_spec_path": self.openapi_spec_path,
            "uncertainty_markers": self.uncertainty_markers,
            "validation_checklist": self.validation_checklist,
        }


@beartype
@require(_feature_spec_keys_nonblank, "feature_key and feature_name must not be empty")
@ensure(lambda result: result is not None, "Must return FeatureSpecificationTemplate")
def create_feature_specification_template(
    feature_key: str, feature_name: str, user_needs: list[str], business_value: str
) -> FeatureSpecificationTemplate:
    """
    Create a feature specification template.

    Args:
        feature_key: Feature key (e.g., FEATURE-001)
        feature_name: Feature name
        user_needs: List of user needs (WHAT and WHY, not HOW)
        business_value: Business value description
    """
    return FeatureSpecificationTemplate(
        feature_key=feature_key,
        feature_name=feature_name,
        user_needs=user_needs,
        business_value=business_value,
        ambiguities=[],
        completeness_checklist={
            "user_needs_defined": len(user_needs) > 0,
            "business_value_clear": bool(business_value),
            "ambiguities_marked": True,  # Will be updated as ambiguities are found
            "no_implementation_details": True,  # Template enforces this
        },
    )


@beartype
@require(_plan_key_nonblank, "plan_key must not be empty")
@ensure(lambda result: result is not None, "Must return ImplementationPlanTemplate")
def create_implementation_plan_template(
    plan_key: str, high_level_steps: list[str], implementation_details_path: str
) -> ImplementationPlanTemplate:
    """
    Create an implementation plan template.

    Args:
        plan_key: Plan key
        high_level_steps: High-level, readable steps
        implementation_details_path: Path to implementation-details/ directory
    """
    return ImplementationPlanTemplate(
        plan_key=plan_key,
        high_level_steps=high_level_steps,
        implementation_details_path=implementation_details_path,
        test_first_approach=True,
        phase_gates=[],
    )


@beartype
@require(_contract_paths_nonblank, "contract_key and openapi_spec_path must not be empty")
@ensure(lambda result: result is not None, "Must return ContractExtractionTemplate")
def create_contract_extraction_template(contract_key: str, openapi_spec_path: str) -> ContractExtractionTemplate:
    """
    Create a contract extraction template.

    Args:
        contract_key: Contract key
        openapi_spec_path: Path to OpenAPI specification
    """
    return ContractExtractionTemplate(
        contract_key=contract_key,
        openapi_spec_path=openapi_spec_path,
        uncertainty_markers=[],
        validation_checklist={
            "openapi_valid": False,
            "uncertainties_marked": True,
            "contracts_extracted": False,
        },
    )

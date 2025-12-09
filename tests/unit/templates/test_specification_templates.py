"""
Unit tests for specification templates.
"""

from __future__ import annotations

from specfact_cli.templates.specification_templates import (
    ContractExtractionTemplate,
    FeatureSpecificationTemplate,
    ImplementationPlanTemplate,
    create_contract_extraction_template,
    create_feature_specification_template,
    create_implementation_plan_template,
)


class TestFeatureSpecificationTemplate:
    """Test FeatureSpecificationTemplate."""

    def test_template_creation(self) -> None:
        """Test creating a feature specification template."""
        template = FeatureSpecificationTemplate(
            feature_key="FEATURE-001",
            feature_name="Test Feature",
            user_needs=["Need 1", "Need 2"],
            business_value="High value",
            ambiguities=[],
            completeness_checklist={"user_needs_defined": True},
        )
        assert template.feature_key == "FEATURE-001"
        assert template.feature_name == "Test Feature"
        assert len(template.user_needs) == 2

    def test_template_to_dict(self) -> None:
        """Test converting template to dictionary."""
        template = FeatureSpecificationTemplate(
            feature_key="FEATURE-001",
            feature_name="Test Feature",
            user_needs=["Need 1"],
            business_value="Value",
            ambiguities=[],
            completeness_checklist={},
        )
        template_dict = template.to_dict()
        assert template_dict["feature_key"] == "FEATURE-001"
        assert template_dict["feature_name"] == "Test Feature"


class TestImplementationPlanTemplate:
    """Test ImplementationPlanTemplate."""

    def test_template_creation(self) -> None:
        """Test creating an implementation plan template."""
        template = ImplementationPlanTemplate(
            plan_key="PLAN-001",
            high_level_steps=["Step 1", "Step 2"],
            implementation_details_path="details/",
            test_first_approach=True,
            phase_gates=[],
        )
        assert template.plan_key == "PLAN-001"
        assert template.test_first_approach is True

    def test_template_to_dict(self) -> None:
        """Test converting template to dictionary."""
        template = ImplementationPlanTemplate(
            plan_key="PLAN-001",
            high_level_steps=["Step 1"],
            implementation_details_path="details/",
            test_first_approach=True,
            phase_gates=[],
        )
        template_dict = template.to_dict()
        assert template_dict["plan_key"] == "PLAN-001"
        assert template_dict["test_first_approach"] is True


class TestContractExtractionTemplate:
    """Test ContractExtractionTemplate."""

    def test_template_creation(self) -> None:
        """Test creating a contract extraction template."""
        template = ContractExtractionTemplate(
            contract_key="CONTRACT-001",
            openapi_spec_path="openapi.yaml",
            uncertainty_markers=[],
            validation_checklist={},
        )
        assert template.contract_key == "CONTRACT-001"
        assert template.openapi_spec_path == "openapi.yaml"

    def test_template_to_dict(self) -> None:
        """Test converting template to dictionary."""
        template = ContractExtractionTemplate(
            contract_key="CONTRACT-001",
            openapi_spec_path="openapi.yaml",
            uncertainty_markers=[],
            validation_checklist={},
        )
        template_dict = template.to_dict()
        assert template_dict["contract_key"] == "CONTRACT-001"


class TestTemplateFactories:
    """Test template factory functions."""

    def test_create_feature_specification_template(self) -> None:
        """Test create_feature_specification_template factory."""
        template = create_feature_specification_template(
            feature_key="FEATURE-001",
            feature_name="Test Feature",
            user_needs=["Need 1"],
            business_value="Value",
        )
        assert isinstance(template, FeatureSpecificationTemplate)
        assert template.feature_key == "FEATURE-001"

    def test_create_implementation_plan_template(self) -> None:
        """Test create_implementation_plan_template factory."""
        template = create_implementation_plan_template(
            plan_key="PLAN-001",
            high_level_steps=["Step 1"],
            implementation_details_path="details/",
        )
        assert isinstance(template, ImplementationPlanTemplate)
        assert template.plan_key == "PLAN-001"
        assert template.test_first_approach is True

    def test_create_contract_extraction_template(self) -> None:
        """Test create_contract_extraction_template factory."""
        template = create_contract_extraction_template(
            contract_key="CONTRACT-001",
            openapi_spec_path="openapi.yaml",
        )
        assert isinstance(template, ContractExtractionTemplate)
        assert template.contract_key == "CONTRACT-001"

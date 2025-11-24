"""
Unit tests for SDD data models - Contract-First approach.

Pydantic models handle most validation (types, ranges, required fields).
Only edge cases and business logic validation are tested here.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from specfact_cli.models.sdd import (
    SDDCoverageThresholds,
    SDDEnforcementBudget,
    SDDHow,
    SDDManifest,
    SDDWhat,
    SDDWhy,
)


class TestSDDWhy:
    """Tests for SDDWhy model - edge cases only."""

    def test_sdd_why_required_fields(self):
        """Test SDDWhy requires intent field."""
        # Valid
        why = SDDWhy(intent="Test intent", target_users=None, value_hypothesis=None)  # type: ignore[call-arg]
        assert why.intent == "Test intent"
        assert why.constraints == []
        assert why.target_users is None
        assert why.value_hypothesis is None

        # Invalid - missing intent
        with pytest.raises(ValidationError):
            SDDWhy()  # type: ignore[call-overload]

    def test_sdd_why_with_all_fields(self):
        """Test SDDWhy with all optional fields."""
        why = SDDWhy(
            intent="Test intent",
            constraints=["Constraint 1", "Constraint 2"],
            target_users="Developers, DevOps",
            value_hypothesis="Reduce technical debt",
        )
        assert why.intent == "Test intent"
        assert len(why.constraints) == 2
        assert why.target_users == "Developers, DevOps"
        assert why.value_hypothesis == "Reduce technical debt"


class TestSDDWhat:
    """Tests for SDDWhat model - edge cases only."""

    def test_sdd_what_required_fields(self):
        """Test SDDWhat requires capabilities field."""
        # Valid
        what = SDDWhat(capabilities=["Capability 1"])
        assert len(what.capabilities) == 1
        assert what.acceptance_criteria == []
        assert what.out_of_scope == []

        # Invalid - missing capabilities
        with pytest.raises(ValidationError):
            SDDWhat()  # type: ignore[call-overload]

    def test_sdd_what_with_all_fields(self):
        """Test SDDWhat with all fields."""
        what = SDDWhat(
            capabilities=["Capability 1", "Capability 2"],
            acceptance_criteria=["AC1", "AC2"],
            out_of_scope=["Out of scope 1"],
        )
        assert len(what.capabilities) == 2
        assert len(what.acceptance_criteria) == 2
        assert len(what.out_of_scope) == 1


class TestSDDHow:
    """Tests for SDDHow model - edge cases only."""

    def test_sdd_how_optional_fields(self):
        """Test SDDHow with all optional fields."""
        how = SDDHow(architecture=None)  # type: ignore[call-arg]
        assert how.architecture is None
        assert how.invariants == []
        assert how.contracts == []
        assert how.module_boundaries == []

    def test_sdd_how_with_all_fields(self):
        """Test SDDHow with all fields populated."""
        how = SDDHow(
            architecture="Microservices architecture",
            invariants=["Invariant 1", "Invariant 2"],
            contracts=["Contract 1", "Contract 2"],
            module_boundaries=["Module 1", "Module 2"],
        )
        assert how.architecture == "Microservices architecture"
        assert len(how.invariants) == 2
        assert len(how.contracts) == 2
        assert len(how.module_boundaries) == 2


class TestSDDCoverageThresholds:
    """Tests for SDDCoverageThresholds model - edge cases only."""

    def test_sdd_coverage_thresholds_defaults(self):
        """Test SDDCoverageThresholds with default values."""
        thresholds = SDDCoverageThresholds(contracts_per_story=1.0, invariants_per_feature=1.0, architecture_facets=3)  # type: ignore[call-arg]
        assert thresholds.contracts_per_story == 1.0
        assert thresholds.invariants_per_feature == 1.0
        assert thresholds.architecture_facets == 3

    def test_sdd_coverage_thresholds_custom_values(self):
        """Test SDDCoverageThresholds with custom values."""
        thresholds = SDDCoverageThresholds(
            contracts_per_story=2.0,
            invariants_per_feature=3.0,
            architecture_facets=5,
        )
        assert thresholds.contracts_per_story == 2.0
        assert thresholds.invariants_per_feature == 3.0
        assert thresholds.architecture_facets == 5

    def test_sdd_coverage_thresholds_validation(self):
        """Test SDDCoverageThresholds validation - negative values."""
        # Invalid - negative contracts_per_story
        with pytest.raises(ValidationError):
            SDDCoverageThresholds(contracts_per_story=-1.0, invariants_per_feature=1.0, architecture_facets=3)  # type: ignore[call-arg]

        # Invalid - negative invariants_per_feature
        with pytest.raises(ValidationError):
            SDDCoverageThresholds(contracts_per_story=1.0, invariants_per_feature=-1.0, architecture_facets=3)  # type: ignore[call-arg]

        # Invalid - negative architecture_facets
        with pytest.raises(ValidationError):
            SDDCoverageThresholds(contracts_per_story=1.0, invariants_per_feature=1.0, architecture_facets=-1)  # type: ignore[call-arg]


class TestSDDEnforcementBudget:
    """Tests for SDDEnforcementBudget model - edge cases only."""

    def test_sdd_enforcement_budget_defaults(self):
        """Test SDDEnforcementBudget with default values."""
        budget = SDDEnforcementBudget(shadow_budget_seconds=300, warn_budget_seconds=180, block_budget_seconds=90)  # type: ignore[call-arg]
        assert budget.shadow_budget_seconds == 300
        assert budget.warn_budget_seconds == 180
        assert budget.block_budget_seconds == 90

    def test_sdd_enforcement_budget_custom_values(self):
        """Test SDDEnforcementBudget with custom values."""
        budget = SDDEnforcementBudget(
            shadow_budget_seconds=600,
            warn_budget_seconds=300,
            block_budget_seconds=120,
        )
        assert budget.shadow_budget_seconds == 600
        assert budget.warn_budget_seconds == 300
        assert budget.block_budget_seconds == 120

    def test_sdd_enforcement_budget_validation(self):
        """Test SDDEnforcementBudget validation - negative values."""
        # Invalid - negative shadow_budget_seconds
        with pytest.raises(ValidationError):
            SDDEnforcementBudget(shadow_budget_seconds=-1, warn_budget_seconds=180, block_budget_seconds=90)  # type: ignore[call-arg]

        # Invalid - negative warn_budget_seconds
        with pytest.raises(ValidationError):
            SDDEnforcementBudget(shadow_budget_seconds=300, warn_budget_seconds=-1, block_budget_seconds=90)  # type: ignore[call-arg]

        # Invalid - negative block_budget_seconds
        with pytest.raises(ValidationError):
            SDDEnforcementBudget(shadow_budget_seconds=300, warn_budget_seconds=180, block_budget_seconds=-1)  # type: ignore[call-arg]


class TestSDDManifest:
    """Tests for SDDManifest model - business logic only."""

    def test_sdd_manifest_required_fields(self):
        """Test SDDManifest requires plan_bundle_id and plan_bundle_hash."""
        why = SDDWhy(intent="Test intent", target_users=None, value_hypothesis=None)  # type: ignore[call-arg]
        what = SDDWhat(capabilities=["Capability 1"])
        how = SDDHow(architecture=None)  # type: ignore[call-arg]

        # Valid
        manifest = SDDManifest(
            version="1.0.0",
            plan_bundle_id="abc123",
            plan_bundle_hash="def456",
            why=why,
            what=what,
            how=how,
            promotion_status="draft",
        )  # type: ignore[call-arg]
        assert manifest.plan_bundle_id == "abc123"
        assert manifest.plan_bundle_hash == "def456"
        assert manifest.version == "1.0.0"
        assert manifest.promotion_status == "draft"

        # Invalid - missing plan_bundle_id
        with pytest.raises(ValidationError):
            SDDManifest(
                plan_bundle_hash="def456",
                why=why,
                what=what,
                how=how,
            )  # type: ignore[call-overload]

    def test_sdd_manifest_promotion_status_validation(self):
        """Test SDDManifest promotion_status validation via contract."""
        why = SDDWhy(intent="Test intent", target_users=None, value_hypothesis=None)  # type: ignore[call-arg]
        what = SDDWhat(capabilities=["Capability 1"])
        how = SDDHow(architecture=None)  # type: ignore[call-arg]

        # Valid statuses
        for status in ("draft", "review", "approved", "released"):
            manifest = SDDManifest(
                version="1.0.0",
                plan_bundle_id="abc123",
                plan_bundle_hash="def456",
                why=why,
                what=what,
                how=how,
                promotion_status=status,
            )  # type: ignore[call-arg]
            assert manifest.promotion_status == status

    def test_sdd_manifest_validate_structure(self):
        """Test SDDManifest validate_structure method."""
        why = SDDWhy(intent="Test intent", target_users=None, value_hypothesis=None)  # type: ignore[call-arg]
        what = SDDWhat(capabilities=["Capability 1"])
        how = SDDHow(architecture=None)  # type: ignore[call-arg]

        manifest = SDDManifest(
            version="1.0.0",
            plan_bundle_id="abc123",
            plan_bundle_hash="def456",
            why=why,
            what=what,
            how=how,
            promotion_status="draft",
        )  # type: ignore[call-arg]

        # Should return True for valid manifest
        assert manifest.validate_structure() is True

    def test_sdd_manifest_update_timestamp(self):
        """Test SDDManifest update_timestamp method."""
        why = SDDWhy(intent="Test intent", target_users=None, value_hypothesis=None)  # type: ignore[call-arg]
        what = SDDWhat(capabilities=["Capability 1"])
        how = SDDHow(architecture=None)  # type: ignore[call-arg]

        manifest = SDDManifest(
            version="1.0.0",
            plan_bundle_id="abc123",
            plan_bundle_hash="def456",
            why=why,
            what=what,
            how=how,
            promotion_status="draft",
        )  # type: ignore[call-arg]

        original_timestamp = manifest.updated_at
        manifest.update_timestamp()
        assert manifest.updated_at != original_timestamp
        assert manifest.updated_at > original_timestamp

    def test_sdd_manifest_with_provenance(self):
        """Test SDDManifest with provenance metadata."""
        why = SDDWhy(intent="Test intent", target_users=None, value_hypothesis=None)  # type: ignore[call-arg]
        what = SDDWhat(capabilities=["Capability 1"])
        how = SDDHow(architecture=None)  # type: ignore[call-arg]

        manifest = SDDManifest(
            version="1.0.0",
            plan_bundle_id="abc123",
            plan_bundle_hash="def456",
            why=why,
            what=what,
            how=how,
            promotion_status="draft",
            provenance={"source": "test", "author": "test_user"},
        )  # type: ignore[call-arg]

        assert manifest.provenance["source"] == "test"
        assert manifest.provenance["author"] == "test_user"

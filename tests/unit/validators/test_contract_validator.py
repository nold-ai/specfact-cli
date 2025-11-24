"""Unit tests for contract density validator."""

import pytest

from specfact_cli.models.deviation import DeviationSeverity, DeviationType
from specfact_cli.models.plan import Feature, PlanBundle, Story
from specfact_cli.models.sdd import SDDCoverageThresholds, SDDEnforcementBudget, SDDHow, SDDManifest, SDDWhat, SDDWhy
from specfact_cli.validators.contract_validator import (
    ContractDensityMetrics,
    calculate_contract_density,
    validate_contract_density,
)


@pytest.fixture
def sample_plan_bundle() -> PlanBundle:
    """Create a sample plan bundle for testing."""
    from specfact_cli.models.plan import Business, Idea, Metadata, Product, Release

    return PlanBundle(
        version="1.0.0",
        idea=Idea(
            title="Test Idea",
            narrative="Test idea narrative",
            constraints=[],
            target_users=["developers"],
            value_hypothesis="Test value",
            metrics=None,
        ),
        product=Product(
            themes=["Theme 1"],
            releases=[
                Release(
                    name="Release 1.0",
                    objectives=[],
                    scope=[],
                    risks=[],
                )
            ],
        ),
        business=Business(
            segments=[],
            problems=[],
            solutions=[],
            differentiation=[],
            risks=[],
        ),
        features=[
            Feature(
                key="FEATURE-001",
                title="Feature 1",
                outcomes=[],
                acceptance=[],
                constraints=[],
                stories=[
                    Story(
                        key="STORY-001",
                        title="Story 1",
                        acceptance=[],
                        story_points=None,
                        value_points=None,
                        scenarios=None,
                        contracts=None,
                    ),
                    Story(
                        key="STORY-002",
                        title="Story 2",
                        acceptance=[],
                        story_points=None,
                        value_points=None,
                        scenarios=None,
                        contracts=None,
                    ),
                ],
            ),
            Feature(
                key="FEATURE-002",
                title="Feature 2",
                outcomes=[],
                acceptance=[],
                constraints=[],
                stories=[
                    Story(
                        key="STORY-003",
                        title="Story 3",
                        acceptance=[],
                        story_points=None,
                        value_points=None,
                        scenarios=None,
                        contracts=None,
                    ),
                ],
            ),
        ],
        metadata=Metadata(
            stage="draft",
            promoted_at=None,
            promoted_by=None,
            analysis_scope=None,
            entry_point=None,
            external_dependencies=[],
            summary=None,
        ),
        clarifications=None,
    )


@pytest.fixture
def sample_sdd_manifest() -> SDDManifest:
    """Create a sample SDD manifest for testing."""
    return SDDManifest(
        version="1.0.0",
        plan_bundle_id="test-plan-id",
        plan_bundle_hash="test-hash",
        why=SDDWhy(
            intent="Test intent",
            constraints=[],
            target_users="developers",
            value_hypothesis="Test value",
        ),
        what=SDDWhat(
            capabilities=["Capability 1", "Capability 2"],
            acceptance_criteria=[],
            out_of_scope=[],
        ),
        how=SDDHow(
            architecture="Test architecture",
            invariants=["Invariant 1", "Invariant 2"],
            contracts=["Contract 1", "Contract 2", "Contract 3"],
            module_boundaries=["Boundary 1", "Boundary 2"],
        ),
        coverage_thresholds=SDDCoverageThresholds(
            contracts_per_story=1.0,
            invariants_per_feature=1.0,
            architecture_facets=3,
        ),
        enforcement_budget=SDDEnforcementBudget(
            shadow_budget_seconds=300,
            warn_budget_seconds=180,
            block_budget_seconds=90,
        ),
        promotion_status="draft",
    )


class TestContractDensityMetrics:
    """Test ContractDensityMetrics class."""

    def test_metrics_initialization(self) -> None:
        """Test metrics initialization."""
        metrics = ContractDensityMetrics(
            contracts_per_story=1.5,
            invariants_per_feature=2.0,
            architecture_facets=3,
            total_contracts=3,
            total_invariants=2,
            total_stories=2,
            total_features=1,
        )

        assert metrics.contracts_per_story == 1.5
        assert metrics.invariants_per_feature == 2.0
        assert metrics.architecture_facets == 3
        assert metrics.total_contracts == 3
        assert metrics.total_invariants == 2
        assert metrics.total_stories == 2
        assert metrics.total_features == 1

    def test_metrics_to_dict(self) -> None:
        """Test metrics to_dict conversion."""
        metrics = ContractDensityMetrics(
            contracts_per_story=1.5,
            invariants_per_feature=2.0,
            architecture_facets=3,
            total_contracts=3,
            total_invariants=2,
            total_stories=2,
            total_features=1,
        )

        result = metrics.to_dict()
        assert result["contracts_per_story"] == 1.5
        assert result["invariants_per_feature"] == 2.0
        assert result["architecture_facets"] == 3
        assert result["total_contracts"] == 3
        assert result["total_invariants"] == 2
        assert result["total_stories"] == 2
        assert result["total_features"] == 1


class TestCalculateContractDensity:
    """Test calculate_contract_density function."""

    def test_calculate_density_with_contracts(
        self, sample_sdd_manifest: SDDManifest, sample_plan_bundle: PlanBundle
    ) -> None:
        """Test density calculation with contracts and invariants."""
        metrics = calculate_contract_density(sample_sdd_manifest, sample_plan_bundle)

        # 3 contracts / 3 stories = 1.0
        assert metrics.contracts_per_story == 1.0
        # 2 invariants / 2 features = 1.0
        assert metrics.invariants_per_feature == 1.0
        # 1 architecture + 2 module boundaries = 3
        assert metrics.architecture_facets == 3
        assert metrics.total_contracts == 3
        assert metrics.total_invariants == 2
        assert metrics.total_stories == 3
        assert metrics.total_features == 2

    def test_calculate_density_no_contracts(self, sample_plan_bundle: PlanBundle) -> None:
        """Test density calculation with no contracts."""
        sdd = SDDManifest(
            version="1.0.0",
            plan_bundle_id="test-id",
            plan_bundle_hash="test-hash",
            why=SDDWhy(intent="Test", target_users="developers", value_hypothesis="Test"),
            what=SDDWhat(capabilities=["Cap 1"]),
            how=SDDHow(architecture=None, invariants=[], contracts=[], module_boundaries=[]),
            coverage_thresholds=SDDCoverageThresholds(
                contracts_per_story=1.0,
                invariants_per_feature=1.0,
                architecture_facets=3,
            ),
            enforcement_budget=SDDEnforcementBudget(
                shadow_budget_seconds=300,
                warn_budget_seconds=180,
                block_budget_seconds=90,
            ),
            promotion_status="draft",
        )

        metrics = calculate_contract_density(sdd, sample_plan_bundle)

        assert metrics.contracts_per_story == 0.0
        assert metrics.invariants_per_feature == 0.0
        assert metrics.architecture_facets == 0
        assert metrics.total_contracts == 0
        assert metrics.total_invariants == 0

    def test_calculate_density_empty_plan(self, sample_sdd_manifest: SDDManifest) -> None:
        """Test density calculation with empty plan."""
        from specfact_cli.models.plan import Business, Idea, Metadata, Product

        empty_plan = PlanBundle(
            version="1.0.0",
            idea=Idea(
                title="Test", narrative="Test", target_users=["developers"], value_hypothesis="Test", metrics=None
            ),
            product=Product(themes=[], releases=[]),
            business=Business(segments=[], problems=[], solutions=[], differentiation=[], risks=[]),
            features=[],
            metadata=Metadata(
                stage="draft",
                promoted_at=None,
                promoted_by=None,
                analysis_scope=None,
                entry_point=None,
                external_dependencies=[],
                summary=None,
            ),
            clarifications=None,
        )

        metrics = calculate_contract_density(sample_sdd_manifest, empty_plan)

        assert metrics.contracts_per_story == 0.0
        assert metrics.invariants_per_feature == 0.0
        assert metrics.total_stories == 0
        assert metrics.total_features == 0


class TestValidateContractDensity:
    """Test validate_contract_density function."""

    def test_validate_all_thresholds_met(
        self, sample_sdd_manifest: SDDManifest, sample_plan_bundle: PlanBundle
    ) -> None:
        """Test validation when all thresholds are met."""
        metrics = calculate_contract_density(sample_sdd_manifest, sample_plan_bundle)
        deviations = validate_contract_density(sample_sdd_manifest, sample_plan_bundle, metrics)

        assert len(deviations) == 0

    def test_validate_contracts_below_threshold(self, sample_plan_bundle: PlanBundle) -> None:
        """Test validation when contracts per story is below threshold."""
        sdd = SDDManifest(
            version="1.0.0",
            plan_bundle_id="test-id",
            plan_bundle_hash="test-hash",
            why=SDDWhy(intent="Test", target_users="developers", value_hypothesis="Test"),
            what=SDDWhat(capabilities=["Cap 1"]),
            how=SDDHow(
                architecture="Test",
                invariants=["Invariant 1", "Invariant 2"],  # 2 invariants for 2 features = 1.0 (meets threshold)
                contracts=["Contract 1"],  # Only 1 contract for 3 stories = 0.33 < 1.0
                module_boundaries=["Boundary 1", "Boundary 2"],  # 1 arch + 2 boundaries = 3 (meets threshold)
            ),
            coverage_thresholds=SDDCoverageThresholds(
                contracts_per_story=1.0,
                invariants_per_feature=1.0,
                architecture_facets=3,
            ),
            enforcement_budget=SDDEnforcementBudget(
                shadow_budget_seconds=300,
                warn_budget_seconds=180,
                block_budget_seconds=90,
            ),
            promotion_status="draft",
        )

        metrics = calculate_contract_density(sdd, sample_plan_bundle)
        deviations = validate_contract_density(sdd, sample_plan_bundle, metrics)

        assert len(deviations) == 1
        assert deviations[0].type == DeviationType.COVERAGE_THRESHOLD
        assert deviations[0].severity == DeviationSeverity.MEDIUM
        assert "Contracts per story" in deviations[0].description

    def test_validate_invariants_below_threshold(self, sample_plan_bundle: PlanBundle) -> None:
        """Test validation when invariants per feature is below threshold."""
        sdd = SDDManifest(
            version="1.0.0",
            plan_bundle_id="test-id",
            plan_bundle_hash="test-hash",
            why=SDDWhy(intent="Test", target_users="developers", value_hypothesis="Test"),
            what=SDDWhat(capabilities=["Cap 1"]),
            how=SDDHow(
                architecture="Test",
                invariants=[],  # No invariants for 2 features = 0.0 < 1.0
                contracts=["Contract 1", "Contract 2", "Contract 3"],
                module_boundaries=["Boundary 1", "Boundary 2"],
            ),
            coverage_thresholds=SDDCoverageThresholds(
                contracts_per_story=1.0,
                invariants_per_feature=1.0,
                architecture_facets=3,
            ),
            enforcement_budget=SDDEnforcementBudget(
                shadow_budget_seconds=300,
                warn_budget_seconds=180,
                block_budget_seconds=90,
            ),
            promotion_status="draft",
        )

        metrics = calculate_contract_density(sdd, sample_plan_bundle)
        deviations = validate_contract_density(sdd, sample_plan_bundle, metrics)

        assert len(deviations) == 1
        assert deviations[0].type == DeviationType.COVERAGE_THRESHOLD
        assert deviations[0].severity == DeviationSeverity.MEDIUM
        assert "Invariants per feature" in deviations[0].description

    def test_validate_architecture_below_threshold(self, sample_plan_bundle: PlanBundle) -> None:
        """Test validation when architecture facets is below threshold."""
        sdd = SDDManifest(
            version="1.0.0",
            plan_bundle_id="test-id",
            plan_bundle_hash="test-hash",
            why=SDDWhy(intent="Test", target_users="developers", value_hypothesis="Test"),
            what=SDDWhat(capabilities=["Cap 1"]),
            how=SDDHow(
                architecture=None,  # No architecture
                invariants=["Invariant 1", "Invariant 2"],
                contracts=["Contract 1", "Contract 2", "Contract 3"],
                module_boundaries=[],  # No boundaries = 0 facets < 3
            ),
            coverage_thresholds=SDDCoverageThresholds(
                contracts_per_story=1.0,
                invariants_per_feature=1.0,
                architecture_facets=3,
            ),
            enforcement_budget=SDDEnforcementBudget(
                shadow_budget_seconds=300,
                warn_budget_seconds=180,
                block_budget_seconds=90,
            ),
            promotion_status="draft",
        )

        metrics = calculate_contract_density(sdd, sample_plan_bundle)
        deviations = validate_contract_density(sdd, sample_plan_bundle, metrics)

        assert len(deviations) == 1
        assert deviations[0].type == DeviationType.COVERAGE_THRESHOLD
        assert deviations[0].severity == DeviationSeverity.LOW
        assert "Architecture facets" in deviations[0].description

    def test_validate_multiple_violations(self, sample_plan_bundle: PlanBundle) -> None:
        """Test validation with multiple threshold violations."""
        sdd = SDDManifest(
            version="1.0.0",
            plan_bundle_id="test-id",
            plan_bundle_hash="test-hash",
            why=SDDWhy(intent="Test", target_users="developers", value_hypothesis="Test"),
            what=SDDWhat(capabilities=["Cap 1"]),
            how=SDDHow(
                architecture=None,
                invariants=[],  # Below threshold
                contracts=["Contract 1"],  # Below threshold (1/3 = 0.33 < 1.0)
                module_boundaries=[],  # Below threshold (0 < 3)
            ),
            coverage_thresholds=SDDCoverageThresholds(
                contracts_per_story=1.0,
                invariants_per_feature=1.0,
                architecture_facets=3,
            ),
            enforcement_budget=SDDEnforcementBudget(
                shadow_budget_seconds=300,
                warn_budget_seconds=180,
                block_budget_seconds=90,
            ),
            promotion_status="draft",
        )

        metrics = calculate_contract_density(sdd, sample_plan_bundle)
        deviations = validate_contract_density(sdd, sample_plan_bundle, metrics)

        assert len(deviations) == 3
        assert all(d.type == DeviationType.COVERAGE_THRESHOLD for d in deviations)
        assert deviations[0].severity == DeviationSeverity.MEDIUM  # Contracts
        assert deviations[1].severity == DeviationSeverity.MEDIUM  # Invariants
        assert deviations[2].severity == DeviationSeverity.LOW  # Architecture

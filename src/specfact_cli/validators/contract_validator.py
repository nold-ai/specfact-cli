"""Contract density validator for SDD manifests.

Calculates contract density metrics (contracts per story, invariants per feature,
architecture facets) and validates against SDD coverage thresholds.
"""

from __future__ import annotations

from beartype import beartype
from icontract import ensure, require

from specfact_cli.models.deviation import Deviation, DeviationSeverity, DeviationType
from specfact_cli.models.plan import PlanBundle
from specfact_cli.models.sdd import SDDManifest


class ContractDensityMetrics:
    """Contract density metrics for a plan bundle."""

    def __init__(
        self,
        contracts_per_story: float,
        invariants_per_feature: float,
        architecture_facets: int,
        total_contracts: int,
        total_invariants: int,
        total_stories: int,
        total_features: int,
        openapi_coverage_percent: float = 0.0,
        features_with_openapi: int = 0,
        total_openapi_contracts: int = 0,
    ) -> None:
        """Initialize contract density metrics.

        Args:
            contracts_per_story: Average contracts per story
            invariants_per_feature: Average invariants per feature
            architecture_facets: Number of architecture facets
            total_contracts: Total number of contracts
            total_invariants: Total number of invariants
            total_stories: Total number of stories
            total_features: Total number of features
            openapi_coverage_percent: Percentage of features with OpenAPI contracts
            features_with_openapi: Number of features with OpenAPI contracts
            total_openapi_contracts: Total number of OpenAPI contracts
        """
        self.contracts_per_story = contracts_per_story
        self.invariants_per_feature = invariants_per_feature
        self.architecture_facets = architecture_facets
        self.total_contracts = total_contracts
        self.total_invariants = total_invariants
        self.total_stories = total_stories
        self.total_features = total_features
        self.openapi_coverage_percent = openapi_coverage_percent
        self.features_with_openapi = features_with_openapi
        self.total_openapi_contracts = total_openapi_contracts

    def to_dict(self) -> dict[str, float | int]:
        """Convert metrics to dictionary."""
        return {
            "contracts_per_story": self.contracts_per_story,
            "invariants_per_feature": self.invariants_per_feature,
            "architecture_facets": self.architecture_facets,
            "total_contracts": self.total_contracts,
            "total_invariants": self.total_invariants,
            "total_stories": self.total_stories,
            "total_features": self.total_features,
            "openapi_coverage_percent": self.openapi_coverage_percent,
            "features_with_openapi": self.features_with_openapi,
            "total_openapi_contracts": self.total_openapi_contracts,
        }


@beartype
@require(lambda sdd: isinstance(sdd, SDDManifest), "SDD must be SDDManifest instance")
@require(lambda plan: isinstance(plan, PlanBundle), "Plan must be PlanBundle instance")
@ensure(lambda result: isinstance(result, ContractDensityMetrics), "Must return ContractDensityMetrics")
def calculate_contract_density(sdd: SDDManifest, plan: PlanBundle) -> ContractDensityMetrics:
    """
    Calculate contract density metrics for a plan bundle.

    Args:
        sdd: SDD manifest with HOW section containing contracts and invariants
        plan: Plan bundle to calculate metrics for

    Returns:
        ContractDensityMetrics with calculated values
    """
    # Count total stories and features
    total_stories = sum(len(feature.stories) for feature in plan.features)
    total_features = len(plan.features)

    # Count contracts and invariants from SDD HOW section
    total_contracts = len(sdd.how.contracts)
    total_invariants = len(sdd.how.invariants)

    # Count OpenAPI contracts from SDD HOW section
    total_openapi_contracts = len(sdd.how.openapi_contracts)
    features_with_openapi = len(sdd.how.openapi_contracts)
    openapi_coverage_percent = (features_with_openapi / total_features * 100.0) if total_features > 0 else 0.0

    # Calculate averages
    contracts_per_story = total_contracts / total_stories if total_stories > 0 else 0.0
    invariants_per_feature = total_invariants / total_features if total_features > 0 else 0.0

    # Count architecture facets
    architecture_facets = 0
    if sdd.how.architecture:
        architecture_facets += 1
    architecture_facets += len(sdd.how.module_boundaries)

    return ContractDensityMetrics(
        contracts_per_story=contracts_per_story,
        invariants_per_feature=invariants_per_feature,
        architecture_facets=architecture_facets,
        total_contracts=total_contracts,
        total_invariants=total_invariants,
        total_stories=total_stories,
        total_features=total_features,
        openapi_coverage_percent=openapi_coverage_percent,
        features_with_openapi=features_with_openapi,
        total_openapi_contracts=total_openapi_contracts,
    )


@beartype
@require(lambda sdd: isinstance(sdd, SDDManifest), "SDD must be SDDManifest instance")
@require(lambda plan: isinstance(plan, PlanBundle), "Plan must be PlanBundle instance")
@require(lambda metrics: isinstance(metrics, ContractDensityMetrics), "Metrics must be ContractDensityMetrics")
@ensure(lambda result: isinstance(result, list), "Must return list of Deviations")
def validate_contract_density(sdd: SDDManifest, plan: PlanBundle, metrics: ContractDensityMetrics) -> list[Deviation]:
    """
    Validate contract density against SDD coverage thresholds.

    Args:
        sdd: SDD manifest with coverage thresholds
        plan: Plan bundle being validated
        metrics: Contract density metrics to validate

    Returns:
        List of Deviation objects for threshold violations
    """
    deviations: list[Deviation] = []
    thresholds = sdd.coverage_thresholds

    # Validate contracts per story
    if metrics.contracts_per_story < thresholds.contracts_per_story:
        deviation = Deviation(
            type=DeviationType.COVERAGE_THRESHOLD,
            severity=DeviationSeverity.MEDIUM,
            description=f"Contracts per story below threshold: {metrics.contracts_per_story:.2f} < {thresholds.contracts_per_story}",
            location=".specfact/projects/<bundle>/sdd.yaml",
            fix_hint=f"Add {thresholds.contracts_per_story - metrics.contracts_per_story:.1f} more contract(s) or update threshold",
        )
        deviations.append(deviation)

    # Validate invariants per feature
    if metrics.invariants_per_feature < thresholds.invariants_per_feature:
        deviation = Deviation(
            type=DeviationType.COVERAGE_THRESHOLD,
            severity=DeviationSeverity.MEDIUM,
            description=f"Invariants per feature below threshold: {metrics.invariants_per_feature:.2f} < {thresholds.invariants_per_feature}",
            location=".specfact/projects/<bundle>/sdd.yaml",
            fix_hint=f"Add {thresholds.invariants_per_feature - metrics.invariants_per_feature:.1f} more invariant(s) or update threshold",
        )
        deviations.append(deviation)

    # Validate architecture facets
    if metrics.architecture_facets < thresholds.architecture_facets:
        deviation = Deviation(
            type=DeviationType.COVERAGE_THRESHOLD,
            severity=DeviationSeverity.LOW,
            description=f"Architecture facets below threshold: {metrics.architecture_facets} < {thresholds.architecture_facets}",
            location=".specfact/projects/<bundle>/sdd.yaml",
            fix_hint=f"Add {thresholds.architecture_facets - metrics.architecture_facets} more architecture facet(s) or update threshold",
        )
        deviations.append(deviation)

    # Validate OpenAPI contract coverage
    if metrics.openapi_coverage_percent < thresholds.openapi_coverage_percent:
        deviation = Deviation(
            type=DeviationType.COVERAGE_THRESHOLD,
            severity=DeviationSeverity.MEDIUM,
            description=f"OpenAPI contract coverage below threshold: {metrics.openapi_coverage_percent:.1f}% < {thresholds.openapi_coverage_percent}%",
            location=".specfact/projects/<bundle>/sdd.yaml",
            fix_hint=f"Add OpenAPI contracts for {int((thresholds.openapi_coverage_percent / 100.0 * metrics.total_features) - metrics.features_with_openapi)} more feature(s) or update threshold. Use 'specfact contract init --feature <key>' to create contracts.",
        )
        deviations.append(deviation)

    return deviations

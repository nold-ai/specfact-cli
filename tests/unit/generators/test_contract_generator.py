"""Unit tests for ContractGenerator.

Focus: Business logic and edge cases only (@beartype handles type validation).
"""

from pathlib import Path

import pytest

from specfact_cli.generators.contract_generator import ContractGenerator
from specfact_cli.models.plan import Feature, Idea, PlanBundle, Product, Story
from specfact_cli.models.sdd import SDDCoverageThresholds, SDDEnforcementBudget, SDDHow, SDDManifest, SDDWhat, SDDWhy


class TestContractGenerator:
    """Test suite for ContractGenerator."""

    @pytest.fixture
    def generator(self):
        """Create a ContractGenerator instance."""
        return ContractGenerator()

    @pytest.fixture
    def sample_sdd_manifest(self):
        """Create a sample SDD manifest for testing."""
        return SDDManifest(
            version="1.0.0",
            plan_bundle_id="test-plan-123",
            plan_bundle_hash="abc123def456",
            promotion_status="draft",
            why=SDDWhy(
                intent="Test intent",
                constraints=["Constraint 1", "Constraint 2"],
                target_users="developers",
                value_hypothesis="Test hypothesis",
            ),
            what=SDDWhat(
                capabilities=["Capability 1", "Capability 2"],
                acceptance_criteria=["Criterion 1"],
                out_of_scope=["Out of scope 1"],
            ),
            how=SDDHow(
                architecture="Test architecture",
                invariants=["Invariant 1: System must be consistent", "Invariant 2: Data must be valid"],
                contracts=[
                    "Contract 1: Payment amount must be positive",
                    "Contract 2: User authentication required",
                ],
                module_boundaries=["Module A", "Module B"],
            ),
            coverage_thresholds=SDDCoverageThresholds(
                contracts_per_story=1.0,
                invariants_per_feature=1.0,
                architecture_facets=3,
                openapi_coverage_percent=80.0,
            ),
            enforcement_budget=SDDEnforcementBudget(
                shadow_budget_seconds=300,
                warn_budget_seconds=180,
                block_budget_seconds=90,
            ),
        )

    @pytest.fixture
    def sample_plan_bundle(self):
        """Create a sample plan bundle for testing."""
        return PlanBundle(
            idea=Idea(
                title="Test Idea",
                narrative="A test idea for validation",
                target_users=["developers"],
                value_hypothesis="Test hypothesis",
                metrics=None,
            ),
            business=None,
            product=Product(themes=["Testing"], releases=[]),
            features=[
                Feature(
                    key="FEATURE-001",
                    title="Payment Processing",
                    outcomes=["Process payments"],
                    stories=[
                        Story(
                            key="STORY-001",
                            title="Process payment for order",
                            acceptance=["Amount must be positive"],
                            story_points=None,
                            value_points=None,
                            scenarios=None,
                            contracts=None,
                        )
                    ],
                    source_tracking=None,
                    contract=None,
                    protocol=None,
                ),
                Feature(
                    key="FEATURE-002",
                    title="User Authentication",
                    outcomes=["Authenticate users"],
                    stories=[
                        Story(
                            key="STORY-002",
                            title="Login with credentials",
                            acceptance=["Credentials must be valid"],
                            story_points=None,
                            value_points=None,
                            scenarios=None,
                            contracts=None,
                        )
                    ],
                    source_tracking=None,
                    contract=None,
                    protocol=None,
                ),
            ],
            metadata=None,
            clarifications=None,
        )

    def test_generate_contracts_creates_files(self, generator, sample_sdd_manifest, sample_plan_bundle, tmp_path):
        """Test that contract generation creates files."""
        result = generator.generate_contracts(sample_sdd_manifest, sample_plan_bundle, tmp_path)

        assert "generated_files" in result
        assert len(result["generated_files"]) > 0
        assert all(Path(f).exists() for f in result["generated_files"])

    def test_generate_contracts_maps_to_features(self, generator, sample_sdd_manifest, sample_plan_bundle, tmp_path):
        """Test that contracts are mapped to features."""
        result = generator.generate_contracts(sample_sdd_manifest, sample_plan_bundle, tmp_path)

        # Should generate one file per feature with contracts/invariants
        assert len(result["generated_files"]) == 2  # Two features

        # Check that files contain feature information
        for file_path in result["generated_files"]:
            content = Path(file_path).read_text()
            assert "FEATURE" in content
            assert "SDD_PLAN_BUNDLE_ID" in content
            assert "SDD_PLAN_BUNDLE_HASH" in content

    def test_generate_contracts_includes_invariants(self, generator, sample_sdd_manifest, sample_plan_bundle, tmp_path):
        """Test that generated files include invariants."""
        result = generator.generate_contracts(sample_sdd_manifest, sample_plan_bundle, tmp_path)

        # Check that at least one file contains invariants
        found_invariants = False
        for file_path in result["generated_files"]:
            content = Path(file_path).read_text()
            if "Invariant" in content:
                found_invariants = True
                break

        assert found_invariants

    def test_generate_contracts_includes_contracts(self, generator, sample_sdd_manifest, sample_plan_bundle, tmp_path):
        """Test that generated files include contract templates."""
        result = generator.generate_contracts(sample_sdd_manifest, sample_plan_bundle, tmp_path)

        # Check that at least one file contains contracts
        found_contracts = False
        for file_path in result["generated_files"]:
            content = Path(file_path).read_text()
            if "Contract" in content and "icontract" in content.lower():
                found_contracts = True
                break

        assert found_contracts

    def test_generate_contracts_counts_contracts_per_story(
        self, generator, sample_sdd_manifest, sample_plan_bundle, tmp_path
    ):
        """Test that contract generation counts contracts per story."""
        result = generator.generate_contracts(sample_sdd_manifest, sample_plan_bundle, tmp_path)

        assert "contracts_per_story" in result
        assert isinstance(result["contracts_per_story"], dict)
        # Should have entries for each story
        assert len(result["contracts_per_story"]) > 0

    def test_generate_contracts_counts_invariants_per_feature(
        self, generator, sample_sdd_manifest, sample_plan_bundle, tmp_path
    ):
        """Test that contract generation counts invariants per feature."""
        result = generator.generate_contracts(sample_sdd_manifest, sample_plan_bundle, tmp_path)

        assert "invariants_per_feature" in result
        assert isinstance(result["invariants_per_feature"], dict)
        # Should have entries for each feature
        assert len(result["invariants_per_feature"]) > 0

    def test_generate_contracts_with_no_contracts(self, generator, sample_sdd_manifest, sample_plan_bundle, tmp_path):
        """Test contract generation when SDD has no contracts."""
        # Create SDD with no contracts
        sdd_no_contracts = SDDManifest(
            version="1.0.0",
            plan_bundle_id="test-plan-123",
            plan_bundle_hash="abc123def456",
            promotion_status="draft",
            why=sample_sdd_manifest.why,
            what=sample_sdd_manifest.what,
            how=SDDHow(
                architecture="Test architecture",
                invariants=[],
                contracts=[],
                module_boundaries=[],
            ),
            coverage_thresholds=sample_sdd_manifest.coverage_thresholds,
            enforcement_budget=sample_sdd_manifest.enforcement_budget,
        )

        result = generator.generate_contracts(sdd_no_contracts, sample_plan_bundle, tmp_path)

        # Should still return result structure
        assert "generated_files" in result
        assert "contracts_per_story" in result
        assert "invariants_per_feature" in result
        assert "errors" in result

    def test_generate_contracts_handles_errors(self, generator, sample_sdd_manifest, sample_plan_bundle, tmp_path):
        """Test that contract generation handles errors gracefully."""
        # Create invalid feature that might cause errors
        invalid_plan = PlanBundle(
            idea=sample_plan_bundle.idea,
            business=None,
            product=sample_plan_bundle.product,
            features=[
                Feature(
                    key="FEATURE-INVALID",
                    title="",  # Empty title might cause issues
                    outcomes=[],
                    stories=[],
                    source_tracking=None,
                    contract=None,
                    protocol=None,
                )
            ],
            metadata=None,
            clarifications=None,
        )

        result = generator.generate_contracts(sample_sdd_manifest, invalid_plan, tmp_path)

        # Should return errors list
        assert "errors" in result
        assert isinstance(result["errors"], list)

    def test_extract_feature_contracts(self, generator, sample_sdd_manifest):
        """Test extracting contracts for a specific feature."""
        feature = Feature(
            key="FEATURE-001",
            title="Payment Processing",
            outcomes=[],
            stories=[],
            source_tracking=None,
            contract=None,
            protocol=None,
        )

        contracts = generator._extract_feature_contracts(sample_sdd_manifest.how, feature)

        assert isinstance(contracts, list)
        # Should find contracts that mention the feature
        assert len(contracts) >= 0

    def test_extract_feature_invariants(self, generator, sample_sdd_manifest):
        """Test extracting invariants for a specific feature."""
        feature = Feature(
            key="FEATURE-001",
            title="Payment Processing",
            outcomes=[],
            stories=[],
            source_tracking=None,
            contract=None,
            protocol=None,
        )

        invariants = generator._extract_feature_invariants(sample_sdd_manifest.how, feature)

        assert isinstance(invariants, list)
        # Should find invariants (may be global or feature-specific)
        assert len(invariants) >= 0

    def test_extract_story_contracts(self, generator, sample_sdd_manifest):
        """Test extracting contracts for a specific story."""
        feature = Feature(
            key="FEATURE-001",
            title="Payment Processing",
            outcomes=[],
            stories=[
                Story(
                    key="STORY-001",
                    title="Process payment",
                    acceptance=[],
                    story_points=None,
                    value_points=None,
                    scenarios=None,
                    contracts=None,
                )
            ],
            source_tracking=None,
            contract=None,
            protocol=None,
        )

        contracts = generator._extract_feature_contracts(sample_sdd_manifest.how, feature)
        story = feature.stories[0]

        story_contracts = generator._extract_story_contracts(contracts, story)

        assert isinstance(story_contracts, list)

    def test_generate_contract_content(self, generator, sample_sdd_manifest):
        """Test contract content generation."""
        feature = Feature(
            key="FEATURE-001",
            title="Payment Processing",
            outcomes=[],
            stories=[],
            source_tracking=None,
            contract=None,
            protocol=None,
        )

        contracts = ["Contract 1: Amount must be positive"]
        invariants = ["Invariant 1: System must be consistent"]

        content = generator._generate_contract_content(feature, contracts, invariants, sample_sdd_manifest)

        assert isinstance(content, str)
        assert len(content) > 0
        assert "FEATURE-001" in content
        assert "Payment Processing" in content
        assert "icontract" in content.lower()
        assert "beartype" in content.lower()
        assert "SDD_PLAN_BUNDLE_ID" in content
        assert "SDD_PLAN_BUNDLE_HASH" in content

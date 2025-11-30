"""
Unit tests for SpecKitConverter - Contract-First approach.

Most validation is covered by @beartype and @icontract decorators.
Only edge cases and integration scenarios are tested here.
"""

from __future__ import annotations

from pathlib import Path

from specfact_cli.importers.speckit_converter import SpecKitConverter
from specfact_cli.models.plan import PlanBundle
from specfact_cli.models.protocol import Protocol


class TestSpecKitConverter:
    """Test cases for SpecKitConverter - focused on edge cases and business logic."""

    def test_convert_protocol_with_features(self, tmp_path: Path) -> None:
        """Test converting features to protocol - integration test."""
        # Create modern Spec-Kit structure
        specify_dir = tmp_path / ".specify"
        specify_dir.mkdir(parents=True)

        specs_dir = tmp_path / "specs" / "001-test-feature"
        specs_dir.mkdir(parents=True)
        (specs_dir / "spec.md").write_text("# Feature Specification: Test Feature\n")

        converter = SpecKitConverter(tmp_path)
        protocol = converter.convert_protocol()

        # Contract ensures Protocol with states (covered by return type annotation)
        assert isinstance(protocol, Protocol)
        assert len(protocol.states) >= 2  # INIT + at least one feature + COMPLETE
        assert "INIT" in protocol.states
        assert "COMPLETE" in protocol.states

    def test_convert_protocol_empty_repo(self, tmp_path: Path) -> None:
        """Test converting empty repo to minimal protocol (edge case)."""
        # Only .specify directory, no features
        specify_dir = tmp_path / ".specify"
        specify_dir.mkdir(parents=True)

        converter = SpecKitConverter(tmp_path)
        protocol = converter.convert_protocol()

        assert isinstance(protocol, Protocol)
        assert len(protocol.states) == 2  # INIT and COMPLETE
        assert "INIT" in protocol.states
        assert "COMPLETE" in protocol.states

    def test_convert_plan_with_markdown_features(self, tmp_path: Path) -> None:
        """Test converting markdown features to plan - integration test."""
        # Create modern Spec-Kit structure
        specify_dir = tmp_path / ".specify" / "memory"
        specify_dir.mkdir(parents=True)

        specs_dir = tmp_path / "specs" / "001-test-feature"
        specs_dir.mkdir(parents=True)
        spec_content = """# Feature Specification: Test Feature

## User Scenarios & Testing

### User Story 1 - Test Story (Priority: P1)

As a user, I want to test features so that I can validate functionality.

## Requirements

- **FR-001**: System MUST test features correctly

## Success Criteria

- **SC-001**: All tests pass
"""
        (specs_dir / "spec.md").write_text(spec_content)

        converter = SpecKitConverter(tmp_path)
        plan_bundle = converter.convert_plan()

        # Contract ensures PlanBundle (covered by return type annotation)
        assert isinstance(plan_bundle, PlanBundle)
        assert plan_bundle.version == "1.1"
        assert len(plan_bundle.features) == 1
        assert plan_bundle.features[0].title == "Test Feature"

    def test_convert_plan_empty_repo(self, tmp_path: Path) -> None:
        """Test converting empty repo to plan with no features (edge case)."""
        specify_dir = tmp_path / ".specify"
        specify_dir.mkdir(parents=True)

        converter = SpecKitConverter(tmp_path)
        plan_bundle = converter.convert_plan()

        assert isinstance(plan_bundle, PlanBundle)
        assert len(plan_bundle.features) == 0

    def test_generate_semgrep_rules(self, tmp_path: Path) -> None:
        """Test generating Semgrep rules - file I/O test."""
        converter = SpecKitConverter(tmp_path)

        output_path = converter.generate_semgrep_rules()

        # Contract ensures Path returned (covered by return type annotation)
        assert output_path.exists()
        assert output_path.name == "async-anti-patterns.yml"

    def test_generate_github_action(self, tmp_path: Path) -> None:
        """Test generating GitHub Action workflow - file I/O test."""
        converter = SpecKitConverter(tmp_path)

        output_path = converter.generate_github_action(repo_name="test-repo")

        # Contract ensures Path returned (covered by return type annotation)
        assert output_path.exists()
        assert output_path.name == "specfact-gate.yml"

        # Verify workflow content (business logic)
        content = output_path.read_text()
        assert "SpecFact CLI Validation" in content
        assert "specfact repro" in content

    def test_convert_to_speckit_sequential_numbering(self, tmp_path: Path) -> None:
        """Test convert_to_speckit uses sequential numbering when feature keys lack numbers."""
        from specfact_cli.models.plan import Feature, PlanBundle, Product

        # Create features without numbers in keys (tests the "000-" bug fix)
        features = [
            Feature(
                key="FEATURE-USER-AUTH",  # No number in key
                title="User Authentication",
                outcomes=["Users can authenticate"],
                acceptance=["Authentication works"],
                constraints=[],
                stories=[],
                confidence=1.0,
                draft=False,
                source_tracking=None,
                contract=None,
                protocol=None,
            ),
            Feature(
                key="FEATURE-PAYMENT",  # No number in key
                title="Payment Processing",
                outcomes=["Users can process payments"],
                acceptance=["Payments work"],
                constraints=[],
                stories=[],
                confidence=1.0,
                draft=False,
                source_tracking=None,
                contract=None,
                protocol=None,
            ),
            Feature(
                key="FEATURE-003",  # Has number in key
                title="Third Feature",
                outcomes=["Third feature works"],
                acceptance=["Feature works"],
                constraints=[],
                stories=[],
                confidence=1.0,
                draft=False,
                source_tracking=None,
                contract=None,
                protocol=None,
            ),
        ]

        plan_bundle = PlanBundle(
            version="1.0",
            product=Product(themes=["Core"], releases=[]),
            features=features,
            metadata=None,
            idea=None,
            business=None,
            clarifications=None,
        )

        converter = SpecKitConverter(tmp_path)
        features_converted = converter.convert_to_speckit(plan_bundle)

        assert features_converted == 3

        # Verify feature directories use correct sequential numbering (not "000-")
        specs_dir = tmp_path / "specs"
        feature_dirs = sorted(specs_dir.iterdir()) if specs_dir.exists() else []

        assert len(feature_dirs) == 3

        # First feature (no number) should be 001-
        assert feature_dirs[0].name.startswith("001-")
        assert "user-authentication" in feature_dirs[0].name

        # Second feature (no number) should be 002-
        assert feature_dirs[1].name.startswith("002-")
        assert "payment-processing" in feature_dirs[1].name

        # Third feature (has number 003) should be 003-
        assert feature_dirs[2].name.startswith("003-")
        assert "third-feature" in feature_dirs[2].name

        # Verify spec.md frontmatter also uses correct numbering (not "000-")
        spec_content_1 = (feature_dirs[0] / "spec.md").read_text()
        assert "**Feature Branch**: `001-" in spec_content_1
        assert "000-" not in spec_content_1

        spec_content_2 = (feature_dirs[1] / "spec.md").read_text()
        assert "**Feature Branch**: `002-" in spec_content_2
        assert "000-" not in spec_content_2

        spec_content_3 = (feature_dirs[2] / "spec.md").read_text()
        assert "**Feature Branch**: `003-" in spec_content_3
        assert "000-" not in spec_content_3

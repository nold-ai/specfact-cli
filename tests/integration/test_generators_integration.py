"""Integration tests for generators with validators and file I/O."""

import pytest

from specfact_cli.generators.plan_generator import PlanGenerator
from specfact_cli.generators.protocol_generator import ProtocolGenerator
from specfact_cli.generators.report_generator import ReportFormat, ReportGenerator
from specfact_cli.models.deviation import Deviation, DeviationSeverity, DeviationType, ValidationReport
from specfact_cli.models.plan import Feature, Idea, PlanBundle, Product, Release, Story
from specfact_cli.models.protocol import Protocol, Transition
from specfact_cli.utils.yaml_utils import load_yaml
from specfact_cli.validators.fsm import FSMValidator
from specfact_cli.validators.schema import SchemaValidator, validate_plan_bundle


class TestPlanGeneratorIntegration:
    """Integration tests for PlanGenerator with validators and file I/O."""

    @pytest.fixture
    def plan_generator(self):
        """Create PlanGenerator instance."""
        return PlanGenerator()

    @pytest.fixture
    def schema_validator(self):
        """Create SchemaValidator instance."""
        return SchemaValidator()

    @pytest.fixture
    def sample_plan_bundle(self):
        """Create a realistic plan bundle."""
        return PlanBundle(
            version="1.0",
            idea=Idea(
                title="AI-Powered Code Review Tool",
                narrative="Automated code review using LLM analysis",
                target_users=["developers", "tech leads", "DevOps engineers"],
                value_hypothesis="Reduce code review time by 60% while improving quality",
                metrics={"review_time_reduction": 0.6, "bug_detection_rate": 0.85},
            ),
            business=None,
            product=Product(
                themes=["AI/ML Integration", "Developer Productivity", "Quality Automation"],
                releases=[
                    Release(
                        name="v1.0 - MVP",
                        objectives=["Basic LLM integration", "GitHub PR analysis"],
                        scope=["FEATURE-001", "FEATURE-002"],
                        risks=["API rate limits", "Model accuracy"],
                    )
                ],
            ),
            features=[
                Feature(
                    key="FEATURE-001",
                    title="LLM Code Analysis",
                    outcomes=["Automated code quality checks", "Security vulnerability detection"],
                    acceptance=["Integrates with OpenAI API", "Provides actionable feedback"],
                    stories=[
                        Story(
                            key="STORY-001",
                            title="Integrate OpenAI API",
                            acceptance=["API client implemented", "Rate limiting handled", "Error handling complete"],
                            story_points=None,
                            value_points=None,
                        )
                    ],
                )
            ],
        )

    def test_generate_and_validate_roundtrip(self, plan_generator, schema_validator, sample_plan_bundle, tmp_path):
        """Test generating plan, validating, and loading back."""
        # Generate plan to file
        output_path = tmp_path / "plan.bundle.yaml"
        plan_generator.generate(sample_plan_bundle, output_path)

        # Verify file exists
        assert output_path.exists()

        # Validate with schema validator
        is_valid, _error, loaded_bundle = validate_plan_bundle(output_path)
        assert is_valid is True
        assert loaded_bundle is not None

        # Load back and verify content
        loaded_data = load_yaml(output_path)
        assert loaded_data["version"] == "1.0"
        assert loaded_data["idea"]["title"] == "AI-Powered Code Review Tool"
        assert len(loaded_data["features"]) == 1
        assert loaded_data["features"][0]["key"] == "FEATURE-001"

    def test_generate_validates_against_json_schema(
        self, plan_generator, schema_validator, sample_plan_bundle, tmp_path
    ):
        """Test that generated plan passes JSON schema validation."""
        output_path = tmp_path / "plan.bundle.yaml"
        plan_generator.generate(sample_plan_bundle, output_path)

        # Validate against JSON schema
        validation_result = schema_validator.validate_json_schema(load_yaml(output_path), "plan")
        assert validation_result.passed is True

    def test_generate_multiple_releases(self, plan_generator, tmp_path):
        """Test generating plan with multiple releases."""
        plan = PlanBundle(
            version="1.0",
            idea=None,
            business=None,
            product=Product(
                themes=["Core"],
                releases=[
                    Release(name="v0.1", objectives=["MVP"], scope=["FEATURE-1"], risks=[]),
                    Release(name="v0.2", objectives=["Scale"], scope=["FEATURE-2"], risks=[]),
                    Release(name="v1.0", objectives=["Production"], scope=["FEATURE-3"], risks=[]),
                ],
            ),
        )

        output_path = tmp_path / "multi-release-plan.yaml"
        plan_generator.generate(plan, output_path)

        # Load and verify
        loaded = load_yaml(output_path)
        assert len(loaded["product"]["releases"]) == 3
        assert loaded["product"]["releases"][1]["name"] == "v0.2"


class TestProtocolGeneratorIntegration:
    """Integration tests for ProtocolGenerator with FSM validators."""

    @pytest.fixture
    def protocol_generator(self):
        """Create ProtocolGenerator instance."""
        return ProtocolGenerator()

    @pytest.fixture
    def sample_protocol(self):
        """Create a realistic FSM protocol."""
        return Protocol(
            states=["INIT", "PLANNING", "CODING", "REVIEW", "MERGED", "FAILED"],
            start="INIT",
            transitions=[
                Transition(from_state="INIT", on_event="start_planning", to_state="PLANNING", guard=None),
                Transition(from_state="PLANNING", on_event="plan_approved", to_state="CODING", guard="has_plan"),
                Transition(from_state="CODING", on_event="code_complete", to_state="REVIEW", guard="has_tests"),
                Transition(from_state="REVIEW", on_event="approved", to_state="MERGED", guard="all_checks_pass"),
                Transition(from_state="REVIEW", on_event="rejected", to_state="CODING", guard=None),
                Transition(from_state="CODING", on_event="error", to_state="FAILED", guard=None),
            ],
            guards={
                "has_plan": "lambda state: state.get('plan') is not None",
                "has_tests": "lambda state: state.get('test_coverage', 0) >= 0.8",
                "all_checks_pass": "lambda state: all(state.get('checks', {}).values())",
            },
        )

    def test_generate_and_validate_protocol(self, protocol_generator, sample_protocol, tmp_path):
        """Test generating protocol and validating FSM."""
        output_path = tmp_path / "workflow.protocol.yaml"
        protocol_generator.generate(sample_protocol, output_path)

        # Verify file exists
        assert output_path.exists()

        # Load back and validate FSM
        loaded_data = load_yaml(output_path)
        loaded_protocol = Protocol(**loaded_data)

        validator = FSMValidator(protocol=loaded_protocol)
        report = validator.validate()

        assert report.passed is True
        assert report.high_count == 0

    def test_protocol_reachability_analysis(self, protocol_generator, tmp_path):
        """Test protocol generation and reachability validation."""
        protocol = Protocol(
            states=["START", "MIDDLE", "END", "UNREACHABLE"],
            start="START",
            transitions=[
                Transition(from_state="START", on_event="go", to_state="MIDDLE", guard=None),
                Transition(from_state="MIDDLE", on_event="finish", to_state="END", guard=None),
            ],
        )

        output_path = tmp_path / "reachability-test.yaml"
        protocol_generator.generate(protocol, output_path)

        # Validate
        loaded = Protocol(**load_yaml(output_path))
        validator = FSMValidator(protocol=loaded)
        report = validator.validate()

        # Should detect unreachable state (MEDIUM severity)
        assert report.medium_count >= 1
        assert any("unreachable" in d.description.lower() for d in report.deviations)

    def test_protocol_with_guards_integration(self, protocol_generator, sample_protocol, tmp_path):
        """Test that guards are properly serialized and validated."""
        output_path = tmp_path / "guarded-protocol.yaml"
        protocol_generator.generate(sample_protocol, output_path)

        # Load and verify guards
        loaded = load_yaml(output_path)
        assert "guards" in loaded
        assert len(loaded["guards"]) == 3
        assert "has_plan" in loaded["guards"]
        assert "has_tests" in loaded["guards"]


class TestReportGeneratorIntegration:
    """Integration tests for ReportGenerator with multiple formats."""

    @pytest.fixture
    def report_generator(self):
        """Create ReportGenerator instance."""
        return ReportGenerator()

    @pytest.fixture
    def validation_report_with_deviations(self):
        """Create a validation report with multiple deviations."""
        report = ValidationReport()
        report.add_deviation(
            Deviation(
                type=DeviationType.FSM_MISMATCH,
                severity=DeviationSeverity.HIGH,
                description="Invalid state transition from INIT to DONE",
                location="workflow.py:42",
                fix_hint="Add intermediate states or update FSM definition",
            )
        )
        report.add_deviation(
            Deviation(
                type=DeviationType.MISSING_FEATURE,
                severity=DeviationSeverity.MEDIUM,
                description="Feature FEATURE-001 not implemented",
                location="features.py:15",
                fix_hint="Implement missing feature or update plan",
            )
        )
        report.add_deviation(
            Deviation(
                type=DeviationType.RISK_OMISSION,
                severity=DeviationSeverity.LOW,
                description="No risks documented for Release v1.0",
                location="plan.yaml:35",
                fix_hint="Add risk analysis to release plan",
            )
        )
        return report

    def test_generate_all_formats_and_verify_content(
        self, report_generator, validation_report_with_deviations, tmp_path
    ):
        """Test generating reports in all formats and verifying content."""
        # Generate markdown
        md_path = tmp_path / "report.md"
        report_generator.generate_validation_report(validation_report_with_deviations, md_path, ReportFormat.MARKDOWN)
        assert md_path.exists()
        md_content = md_path.read_text()
        assert "# Validation Report" in md_content
        assert "HIGH" in md_content
        assert "MEDIUM" in md_content
        assert "LOW" in md_content

        # Generate JSON
        json_path = tmp_path / "report.json"
        report_generator.generate_validation_report(validation_report_with_deviations, json_path, ReportFormat.JSON)
        assert json_path.exists()
        json_content = json_path.read_text()
        assert '"deviations"' in json_content
        assert '"high_count": 1' in json_content

        # Generate YAML
        yaml_path = tmp_path / "report.yaml"
        report_generator.generate_validation_report(validation_report_with_deviations, yaml_path, ReportFormat.YAML)
        assert yaml_path.exists()
        yaml_content = yaml_path.read_text()
        assert "deviations:" in yaml_content
        assert "high_count: 1" in yaml_content

    def test_report_format_consistency(self, report_generator, validation_report_with_deviations, tmp_path):
        """Test that all format outputs contain same information."""
        # Generate all formats
        formats = {
            ReportFormat.MARKDOWN: tmp_path / "report.md",
            ReportFormat.JSON: tmp_path / "report.json",
            ReportFormat.YAML: tmp_path / "report.yaml",
        }

        for fmt, path in formats.items():
            report_generator.generate_validation_report(validation_report_with_deviations, path, fmt)

        # All should mention the same deviations
        for path in formats.values():
            content = path.read_text().lower()
            assert "fsm_mismatch" in content or "fsm" in content
            assert "missing_feature" in content or "missing" in content
            assert "risk_omission" in content or "risk" in content


class TestCrossComponentIntegration:
    """Integration tests across generators, validators, and models."""

    def test_complete_plan_lifecycle(self, tmp_path):
        """Test complete plan lifecycle: create → generate → validate → modify → regenerate."""
        # Step 1: Create initial plan
        plan = PlanBundle(
            version="1.0",
            idea=Idea(
                title="Test Project",
                narrative="Test narrative",
                metrics=None,
            ),
            business=None,
            product=Product(
                themes=["Core"],
                releases=[Release(name="v1.0", objectives=["Launch"], scope=[], risks=[])],
            ),
        )

        # Step 2: Generate to file
        generator = PlanGenerator()
        plan_path = tmp_path / "plan.yaml"
        generator.generate(plan, plan_path)

        # Step 3: Validate
        is_valid, _error, _loaded = validate_plan_bundle(plan_path)
        assert is_valid is True

        # Step 4: Load and modify
        loaded_data = load_yaml(plan_path)
        loaded_data["product"]["themes"].append("Advanced")

        # Step 5: Save modified version
        from specfact_cli.utils.yaml_utils import dump_yaml

        dump_yaml(loaded_data, plan_path)

        # Step 6: Validate modified version
        is_valid2, _error2, _loaded2 = validate_plan_bundle(plan_path)
        assert is_valid2 is True

    def test_protocol_to_validation_report_workflow(self, tmp_path):
        """Test FSM protocol validation and report generation workflow."""
        # Create protocol with intentional issue
        protocol = Protocol(
            states=["A", "B", "C"],
            start="A",
            transitions=[
                Transition(from_state="A", on_event="go", to_state="B", guard=None),
                # B->C transition missing
            ],
        )

        # Generate protocol file
        proto_gen = ProtocolGenerator()
        proto_path = tmp_path / "protocol.yaml"
        proto_gen.generate(protocol, proto_path)

        # Validate and get report
        validator = FSMValidator(protocol=protocol)
        validation_report = validator.validate()

        # Generate validation report
        report_gen = ReportGenerator()
        report_path = tmp_path / "validation-report.md"
        report_gen.generate_validation_report(validation_report, report_path, ReportFormat.MARKDOWN)

        # Verify report contains FSM issues
        report_content = report_path.read_text()
        assert "Validation Report" in report_content
        assert any(word in report_content.lower() for word in ["unreachable", "state"])

    def test_multi_format_report_generation_pipeline(self, tmp_path):
        """Test generating reports in multiple formats from same validation."""
        # Create validation report
        report = ValidationReport()
        for i in range(5):
            report.add_deviation(
                Deviation(
                    type=DeviationType.MISSING_FEATURE,
                    severity=DeviationSeverity.MEDIUM,
                    description=f"Missing feature {i}",
                    location=f"file{i}.py:10",
                    fix_hint=f"Implement feature {i}",
                )
            )

        # Generate all formats
        generator = ReportGenerator()
        outputs = {
            "markdown": tmp_path / "report.md",
            "json": tmp_path / "report.json",
            "yaml": tmp_path / "report.yaml",
        }

        generator.generate_validation_report(report, outputs["markdown"], ReportFormat.MARKDOWN)
        generator.generate_validation_report(report, outputs["json"], ReportFormat.JSON)
        generator.generate_validation_report(report, outputs["yaml"], ReportFormat.YAML)

        # Verify all files exist and contain deviation count
        for fmt, path in outputs.items():
            assert path.exists(), f"{fmt} report not generated"
            content = path.read_text()
            # All should reference 5 deviations
            assert "5" in content or "five" in content.lower()

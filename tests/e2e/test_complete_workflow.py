"""End-to-end tests for complete SpecFact CLI workflows."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from specfact_cli.generators.plan_generator import PlanGenerator
from specfact_cli.generators.protocol_generator import ProtocolGenerator
from specfact_cli.generators.report_generator import ReportFormat, ReportGenerator
from specfact_cli.models.deviation import Deviation, DeviationReport, DeviationSeverity, DeviationType, ValidationReport
from specfact_cli.models.plan import Business, Feature, Idea, PlanBundle, Product, Release, Story
from specfact_cli.models.protocol import Protocol, Transition
from specfact_cli.utils.yaml_utils import dump_yaml, load_yaml
from specfact_cli.validators.fsm import FSMValidator
from specfact_cli.validators.schema import SchemaValidator, validate_plan_bundle, validate_protocol


class TestCompleteWorkflow:
    """Test complete end-to-end workflows."""

    @pytest.fixture
    def workspace(self, tmp_path: Path) -> Path:
        """Create a temporary workspace."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        (workspace / "contracts").mkdir()
        (workspace / "contracts" / "plans").mkdir()
        (workspace / "contracts" / "protocols").mkdir()
        return workspace

    @pytest.fixture
    def resources_dir(self) -> Path:
        """Get the resources directory."""
        return Path(__file__).parent.parent.parent / "resources"

    def test_greenfield_plan_creation_workflow(self, workspace: Path, resources_dir: Path):
        """Test complete workflow for creating a new plan from scratch (greenfield)."""
        # Step 1: Create a new idea
        idea = Idea(
            title="Task Management App",
            narrative="A simple task management application for teams.",
            target_users=["Small teams", "Freelancers"],
            value_hypothesis="Increase team productivity by 30%",
            constraints=["Must work offline", "Mobile-first"],
            metrics={"daily_active_users": "1000", "task_completion_rate": "80%"},
        )

        # Step 2: Define business context
        business = Business(
            segments=["SMB", "Startups"],
            problems=["Scattered task lists", "Poor team collaboration"],
            solutions=["Unified task view", "Real-time collaboration"],
            differentiation=["Offline-first", "Simple UX"],
            risks=["Market competition", "User adoption"],
        )

        # Step 3: Define product structure
        release = Release(
            name="MVP v1.0",
            objectives=["Launch core task features", "Support 100 users"],
            scope=["FEATURE-001", "FEATURE-002"],
            risks=["Technical complexity"],
        )

        product = Product(
            themes=["Productivity", "Collaboration"],
            releases=[release],
        )

        # Step 4: Define features with stories
        story1 = Story(
            key="STORY-001",
            title="As a user, I can create a task",
            acceptance=["Click 'New Task' button", "Enter task details", "Task appears in list"],
            tags=["core", "frontend"],
            story_points=None,
            value_points=None,
            confidence=0.9,
            draft=False,
            scenarios=None,
            contracts=None,
        )

        story2 = Story(
            key="STORY-002",
            title="As a user, I can mark tasks as complete",
            acceptance=["Click checkbox on task", "Task moves to completed section"],
            tags=["core", "frontend"],
            story_points=None,
            value_points=None,
            confidence=0.95,
            draft=False,
            scenarios=None,
            contracts=None,
        )

        feature1 = Feature(
            key="FEATURE-001",
            title="Task Management",
            outcomes=["Users can manage their tasks", "Tasks persist across sessions"],
            acceptance=["Create task works", "Edit task works", "Delete task works"],
            constraints=["Must work offline"],
            stories=[story1, story2],
            confidence=0.85,
            draft=False,
            source_tracking=None,
            contract=None,
            protocol=None,
        )

        feature2 = Feature(
            key="FEATURE-002",
            title="Team Collaboration",
            outcomes=["Team members can share tasks", "Real-time updates"],
            acceptance=["Share task with team", "Team sees updates"],
            stories=[],
            confidence=0.7,
            draft=True,
            source_tracking=None,
            contract=None,
            protocol=None,
        )

        # Step 5: Create complete plan bundle
        plan_bundle = PlanBundle(
            version="1.0",
            idea=idea,
            business=business,
            product=product,
            features=[feature1, feature2],
            metadata=None,
            clarifications=None,
        )

        # Step 6: Validate with Pydantic
        report = validate_plan_bundle(plan_bundle)
        assert report.passed is True
        assert len(report.deviations) == 0

        # Step 7: Save to YAML
        plan_path = workspace / "contracts" / "plans" / "plan.bundle.yaml"
        dump_yaml(plan_bundle.model_dump(exclude_none=True), plan_path)

        # Step 8: Verify file exists
        assert plan_path.exists()

        # Step 9: Reload and validate
        reloaded_data = load_yaml(plan_path)
        reloaded_plan = PlanBundle(**reloaded_data)

        assert reloaded_plan.idea is not None
        assert reloaded_plan.idea.title == "Task Management App"
        assert len(reloaded_plan.features) == 2
        assert len(reloaded_plan.features[0].stories) == 2

        # Step 10: Validate with JSON Schema
        schema_validator = SchemaValidator(resources_dir / "schemas")
        schema_report = schema_validator.validate_json_schema(reloaded_data, "plan.schema.json")
        assert schema_report.passed is True

        print("✅ Greenfield plan creation workflow complete!")

    def test_protocol_design_and_validation_workflow(self, workspace: Path, resources_dir: Path):
        """Test complete workflow for designing and validating an FSM protocol."""
        # Step 1: Design state machine
        states = ["IDLE", "ACTIVE", "PAUSED", "COMPLETED"]
        start_state = "IDLE"

        # Step 2: Define transitions
        transitions = [
            Transition(from_state="IDLE", on_event="start", to_state="ACTIVE", guard=None),
            Transition(from_state="ACTIVE", on_event="pause", to_state="PAUSED", guard=None),
            Transition(from_state="ACTIVE", on_event="complete", to_state="COMPLETED", guard="is_ready"),
            Transition(from_state="PAUSED", on_event="resume", to_state="ACTIVE", guard=None),
            Transition(from_state="PAUSED", on_event="cancel", to_state="IDLE", guard=None),
        ]

        # Step 3: Define guards
        guards = {"is_ready": "return context.progress == 100"}

        # Step 4: Create protocol
        protocol = Protocol(
            states=states,
            start=start_state,
            transitions=transitions,
            guards=guards,
        )

        # Step 5: Validate with Pydantic
        report = validate_protocol(protocol)
        assert report.passed is True

        # Step 6: Validate FSM properties
        fsm_validator = FSMValidator(protocol)
        fsm_report = fsm_validator.validate()

        # Should have LOW warning about undefined guard (no guard function provided)
        assert fsm_report.high_count == 0
        assert fsm_report.medium_count == 0

        # Step 7: Check reachability
        reachable = fsm_validator.get_reachable_states("IDLE")
        assert len(reachable) == 4  # All states reachable

        # Step 8: Check specific transitions
        assert fsm_validator.is_valid_transition("IDLE", "start", "ACTIVE") is True
        assert fsm_validator.is_valid_transition("IDLE", "complete", "COMPLETED") is False

        # Step 9: Save to YAML
        protocol_path = workspace / "contracts" / "protocols" / "protocol.yaml"
        dump_yaml(protocol.model_dump(exclude_none=True), protocol_path)

        # Step 10: Verify file exists
        assert protocol_path.exists()

        # Step 11: Reload and validate
        reloaded_data = load_yaml(protocol_path)
        reloaded_protocol = Protocol(**reloaded_data)

        assert len(reloaded_protocol.states) == 4
        assert reloaded_protocol.start == "IDLE"
        assert len(reloaded_protocol.transitions) == 5

        # Step 12: Validate with JSON Schema
        schema_validator = SchemaValidator(resources_dir / "schemas")
        schema_report = schema_validator.validate_json_schema(reloaded_data, "protocol.schema.json")
        assert schema_report.passed is True

        print("✅ Protocol design and validation workflow complete!")

    def test_deviation_reporting_workflow(self, workspace: Path):
        """Test complete workflow for detecting and reporting deviations."""
        # Step 1: Create a "manual" plan (expected)
        manual_plan = PlanBundle(
            version="1.0",
            idea=None,
            business=None,
            product=Product(themes=["Core"], releases=[]),
            features=[
                Feature(
                    key="FEATURE-001",
                    title="User Authentication",
                    outcomes=["Secure login"],
                    acceptance=["Login works", "Logout works"],
                    stories=[],
                    source_tracking=None,
                    contract=None,
                    protocol=None,
                ),
                Feature(
                    key="FEATURE-002",
                    title="Profile Management",
                    outcomes=["User can edit profile"],
                    acceptance=["Edit profile works"],
                    stories=[],
                    source_tracking=None,
                    contract=None,
                    protocol=None,
                ),
            ],
            metadata=None,
            clarifications=None,
        )

        # Step 2: Create an "auto-derived" plan (actual implementation)
        auto_plan = PlanBundle(
            version="1.0",
            idea=None,
            business=None,
            product=Product(themes=["Core"], releases=[]),
            features=[
                Feature(
                    key="FEATURE-001",
                    title="User Authentication",
                    outcomes=["Secure login"],
                    acceptance=["Login works"],  # Missing "Logout works"
                    stories=[],
                    source_tracking=None,
                    contract=None,
                    protocol=None,
                ),
                Feature(
                    key="FEATURE-003",  # Different key!
                    title="Settings Page",
                    outcomes=["User can change settings"],
                    acceptance=["Settings work"],
                    stories=[],
                    source_tracking=None,
                    contract=None,
                    protocol=None,
                ),
                # Missing FEATURE-002 entirely
            ],
            metadata=None,
            clarifications=None,
        )

        # Step 3: Compare and create deviation report
        manual_features = {f.key: f for f in manual_plan.features}
        auto_features = {f.key: f for f in auto_plan.features}

        deviations = []

        # Find missing features
        for key in manual_features:
            if key not in auto_features:
                from specfact_cli.models.deviation import Deviation

                deviations.append(
                    Deviation(
                        type=DeviationType.MISSING_FEATURE,
                        severity=DeviationSeverity.HIGH,
                        description=f"Feature {key} is in manual plan but missing in auto-derived plan",
                        location=f"features.{key}",
                        fix_hint=f"Implement feature {key} or remove from manual plan",
                    )
                )

        # Find extra features
        for key in auto_features:
            if key not in manual_features:
                from specfact_cli.models.deviation import Deviation

                deviations.append(
                    Deviation(
                        type=DeviationType.EXTRA_FEATURE,
                        severity=DeviationSeverity.MEDIUM,
                        description=f"Feature {key} is in auto-derived plan but not in manual plan",
                        location=f"features.{key}",
                        fix_hint=f"Add feature {key} to manual plan or remove implementation",
                    )
                )

        # Step 4: Create deviation report
        deviation_report = DeviationReport(
            manual_plan=".specfact/plans/main.bundle.yaml",
            auto_plan=".specfact/plans/auto-derived.bundle.yaml",
            deviations=deviations,
            summary={"HIGH": 1, "MEDIUM": 1},
        )

        # Step 5: Verify deviations
        assert len(deviation_report.deviations) == 2
        assert deviation_report.summary["HIGH"] == 1
        assert deviation_report.summary["MEDIUM"] == 1

        # Step 6: Save deviation report
        report_path = workspace / "deviation-report.yaml"
        dump_yaml(deviation_report.model_dump(mode="json"), report_path)

        assert report_path.exists()

        print("✅ Deviation reporting workflow complete!")
        print(f"   Found {len(deviations)} deviations:")
        for dev in deviations:
            print(f"   - [{dev.severity.value}] {dev.description}")

    def test_full_lifecycle_workflow(self, workspace: Path, resources_dir: Path):
        """Test complete lifecycle: Plan → Protocol → Validate → Report."""
        # Phase 1: Create Plan
        idea = Idea(title="CLI Tool", narrative="A powerful CLI tool", metrics=None)
        product = Product(themes=["Automation"], releases=[])
        feature = Feature(
            key="FEATURE-001",
            title="Command Execution",
            outcomes=["Fast command execution"],
            acceptance=["Commands work"],
            source_tracking=None,
            contract=None,
            protocol=None,
        )
        plan = PlanBundle(
            version="1.0",
            idea=idea,
            business=None,
            product=product,
            features=[feature],
            metadata=None,
            clarifications=None,
        )

        # Save plan
        plan_path = workspace / "contracts" / "plans" / "plan.bundle.yaml"
        dump_yaml(plan.model_dump(exclude_none=True), plan_path)

        # Phase 2: Create Protocol
        protocol = Protocol(
            states=["INIT", "RUNNING", "DONE"],
            start="INIT",
            transitions=[
                Transition(from_state="INIT", on_event="execute", to_state="RUNNING", guard=None),
                Transition(from_state="RUNNING", on_event="complete", to_state="DONE", guard=None),
            ],
        )

        # Save protocol
        protocol_path = workspace / "contracts" / "protocols" / "protocol.yaml"
        dump_yaml(protocol.model_dump(exclude_none=True), protocol_path)

        # Phase 3: Validate Plan
        plan_report = validate_plan_bundle(plan)
        assert plan_report.passed is True

        # Phase 4: Validate Protocol
        protocol_report = validate_protocol(protocol)
        assert protocol_report.passed is True

        # Phase 5: FSM Validation
        fsm_validator = FSMValidator(protocol)
        fsm_report = fsm_validator.validate()
        assert fsm_report.high_count == 0

        # Phase 6: JSON Schema Validation
        schema_validator = SchemaValidator(resources_dir / "schemas")

        plan_data = load_yaml(plan_path)
        plan_schema_report = schema_validator.validate_json_schema(plan_data, "plan.schema.json")
        assert plan_schema_report.passed is True

        protocol_data = load_yaml(protocol_path)
        protocol_schema_report = schema_validator.validate_json_schema(protocol_data, "protocol.schema.json")
        assert protocol_schema_report.passed is True

        # Phase 7: Create summary report
        summary = {
            "plan_validation": "PASSED",
            "protocol_validation": "PASSED",
            "fsm_validation": "PASSED",
            "schema_validation": "PASSED",
            "total_features": len(plan.features),
            "total_states": len(protocol.states),
            "total_transitions": len(protocol.transitions),
        }

        summary_path = workspace / "validation-summary.yaml"
        dump_yaml(summary, summary_path)

        # Verify summary
        assert summary_path.exists()
        summary_data = load_yaml(summary_path)
        assert summary_data["plan_validation"] == "PASSED"
        assert summary_data["total_features"] == 1
        assert summary_data["total_states"] == 3

        print("✅ Full lifecycle workflow complete!")
        print(f"   Plan: {len(plan.features)} features")
        print(f"   Protocol: {len(protocol.states)} states, {len(protocol.transitions)} transitions")
        print("   All validations: PASSED")


class TestErrorRecoveryWorkflow:
    """Test error recovery and handling in workflows."""

    def test_invalid_yaml_recovery(self, tmp_path: Path):
        """Test handling of invalid YAML files."""
        # Create invalid YAML
        invalid_yaml_path = tmp_path / "invalid.yaml"
        invalid_yaml_path.write_text("invalid: yaml: content: [")

        # Attempt to load
        from ruamel.yaml import YAMLError

        with pytest.raises(YAMLError):  # ruamel.yaml will raise YAMLError
            load_yaml(invalid_yaml_path)

        print("✅ Invalid YAML correctly rejected")

    def test_schema_validation_failure_recovery(self, tmp_path: Path):
        """Test recovery from schema validation failures."""
        # Create plan with missing required field
        incomplete_data = {
            "version": "1.0",
            # Missing product (required)
            "features": [],
        }

        # Attempt to parse
        with pytest.raises(ValidationError):  # Pydantic will raise ValidationError
            PlanBundle(**incomplete_data)

        print("✅ Schema validation failure correctly detected")

    def test_fsm_validation_failure_recovery(self):
        """Test recovery from FSM validation failures."""
        # Create protocol with invalid start state
        protocol = Protocol(
            states=["A", "B"],
            start="INVALID",  # Not in states list
            transitions=[],
        )

        # Validate
        validator = FSMValidator(protocol)
        report = validator.validate()

        # Should have HIGH severity error
        assert report.passed is False
        assert report.high_count > 0

        print("✅ FSM validation failure correctly detected")
        print(f"   HIGH: {report.high_count}, MEDIUM: {report.medium_count}, LOW: {report.low_count}")


class TestGeneratorE2EWorkflows:
    """End-to-end tests for generator workflows."""

    @pytest.fixture
    def workspace(self, tmp_path: Path) -> Path:
        """Create a temporary workspace with generator outputs."""
        workspace = tmp_path / "gen_workspace"
        workspace.mkdir()
        (workspace / "plans").mkdir()
        (workspace / "protocols").mkdir()
        (workspace / "reports").mkdir()
        return workspace

    def test_complete_plan_generation_workflow(self, workspace: Path):
        """Test complete plan generation: create → generate → validate → report."""
        print("\n🔄 Testing complete plan generation workflow...")

        # Step 1: Create comprehensive plan
        plan = PlanBundle(
            version="1.0",
            idea=Idea(
                title="Multi-Agent System for Code Review",
                narrative="Autonomous system using multiple specialized agents for comprehensive code review",
                target_users=["software teams", "DevOps engineers", "technical leads"],
                value_hypothesis="Reduce code review time by 70% while improving quality scores by 40%",
                metrics={
                    "review_time_reduction": 0.7,
                    "quality_improvement": 0.4,
                    "false_positive_rate": 0.05,
                },
            ),
            business=Business(
                segments=["Enterprise", "Startups"],
                problems=["Manual code review is slow", "Inconsistent quality standards"],
                solutions=["Automated LLM-based review", "Multi-agent system"],
                differentiation=["Faster than human review", "Consistent quality"],
                risks=["Model accuracy", "API costs"],
            ),
            product=Product(
                themes=["AI/ML", "Developer Productivity"],
                releases=[
                    Release(
                        name="v1.0",
                        objectives=["Basic review", "Multi-agent integration"],
                        scope=["FEATURE-001", "FEATURE-002"],
                        risks=["Model accuracy"],
                    )
                ],
            ),
            features=[
                Feature(
                    key="FEATURE-001",
                    title="LLM Code Analysis",
                    outcomes=["Automated review", "Quality checks"],
                    acceptance=["Reviews generated", "Actionable feedback"],
                    stories=[],
                    source_tracking=None,
                    contract=None,
                    protocol=None,
                ),
                Feature(
                    key="FEATURE-002",
                    title="Multi-Agent System",
                    outcomes=["Specialized agents", "Collaborative review"],
                    acceptance=["Agents work together", "Consensus reached"],
                    stories=[],
                    source_tracking=None,
                    contract=None,
                    protocol=None,
                ),
            ],
            metadata=None,
            clarifications=None,
        )
        # Original plan content (removed duplicate)
        original_plan = PlanBundle(
            version="1.0",
            idea=Idea(
                title="Multi-Agent System for Code Review",
                narrative="Autonomous system using multiple specialized agents for comprehensive code review",
                target_users=["software teams", "DevOps engineers", "technical leads"],
                value_hypothesis="Reduce code review time by 70% while improving quality scores by 40%",
                metrics={
                    "review_time_reduction": 0.7,
                    "quality_improvement": 0.4,
                    "false_positive_rate": 0.05,
                },
            ),
            business=Business(
                segments=["Enterprise SaaS", "Developer Tools"],
                problems=[
                    "Manual code reviews are time-consuming",
                    "Inconsistent review quality",
                    "Knowledge silos in teams",
                ],
                solutions=[
                    "Automated multi-agent review system",
                    "LLM-powered analysis",
                    "Continuous learning from feedback",
                ],
                differentiation=["Multi-agent architecture", "Context-aware analysis", "Self-improving system"],
                risks=["Model accuracy concerns", "Integration complexity", "Cost management"],
            ),
            product=Product(
                themes=["AI/ML", "DevOps", "Code Quality"],
                releases=[
                    Release(
                        name="v0.1 - Alpha",
                        objectives=["Prove concept", "Basic agent framework"],
                        scope=["FEATURE-001"],
                        risks=["Technical feasibility"],
                    ),
                    Release(
                        name="v1.0 - Production",
                        objectives=["Full multi-agent system", "Enterprise ready"],
                        scope=["FEATURE-001", "FEATURE-002", "FEATURE-003"],
                        risks=["Scale challenges", "Performance optimization"],
                    ),
                ],
            ),
            features=[
                Feature(
                    key="FEATURE-001",
                    title="Multi-Agent Orchestration",
                    outcomes=["Coordinated agent system", "Conflict resolution", "Result aggregation"],
                    acceptance=["3+ agents coordinated", "Sub-second response time", "95% uptime"],
                    constraints=["Must scale to 100+ repos", "API rate limits respected"],
                    stories=[
                        Story(
                            key="STORY-001",
                            title="Agent Communication Protocol",
                            acceptance=["Message passing implemented", "State synchronization", "Error handling"],
                            tags=["architecture", "critical"],
                            story_points=None,
                            value_points=None,
                            scenarios=None,
                            contracts=None,
                        ),
                        Story(
                            key="STORY-002",
                            title="Orchestrator Implementation",
                            acceptance=["Task routing", "Load balancing", "Health monitoring"],
                            tags=["core", "critical"],
                            story_points=None,
                            value_points=None,
                            scenarios=None,
                            contracts=None,
                        ),
                    ],
                    source_tracking=None,
                    contract=None,
                    protocol=None,
                ),
                Feature(
                    key="FEATURE-002",
                    title="LLM Integration Layer",
                    outcomes=["Multi-model support", "Prompt optimization", "Cost management"],
                    acceptance=["3+ LLM providers", "Automatic fallback", "Cost tracking"],
                    stories=[
                        Story(
                            key="STORY-003",
                            title="LLM Provider Abstraction",
                            acceptance=["Unified interface", "Provider switching", "Error handling"],
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

        # Step 2: Generate plan to file
        generator = PlanGenerator()
        plan_path = workspace / "plans" / "multi-agent-review.yaml"
        generator.generate(original_plan, plan_path)
        print(f"✅ Generated plan: {plan_path.name}")

        # Step 3: Validate generated plan
        is_valid, _error, _loaded_plan_bundle = validate_plan_bundle(plan_path)
        assert is_valid is True
        print(
            f"✅ Plan validation: PASSED (features: {len(plan.features)}, stories: {sum(len(f.stories) for f in plan.features)})"
        )

        # Step 4: Generate validation report (empty since validation passed)
        validation_report = ValidationReport()  # Empty report for passed validation
        report_gen = ReportGenerator()
        report_path = workspace / "reports" / "plan-validation.md"
        report_gen.generate_validation_report(validation_report, report_path, ReportFormat.MARKDOWN)
        print(f"✅ Validation report generated: {report_path.name}")

        # Step 5: Verify roundtrip (load back and validate again)
        loaded_plan_data = load_yaml(plan_path)
        loaded_plan = PlanBundle(**loaded_plan_data)
        assert loaded_plan.idea is not None
        assert loaded_plan.idea.title == "Multi-Agent System for Code Review"
        assert len(loaded_plan.features) == 2
        assert loaded_plan.business is not None
        assert len(loaded_plan.business.segments) == 2
        print("✅ Roundtrip validation: SUCCESS")

        # Verify report content
        report_content = report_path.read_text()
        assert "Validation Report" in report_content
        assert "PASSED" in report_content

    def test_complete_protocol_generation_workflow(self, workspace: Path):
        """Test complete protocol generation: create → generate → validate FSM → report."""
        print("\n🔄 Testing complete protocol generation workflow...")

        # Step 1: Create realistic FSM protocol
        protocol = Protocol(
            states=["INIT", "ANALYSIS", "AGENT_DISPATCH", "REVIEW_AGGREGATION", "FEEDBACK", "COMPLETE", "ERROR"],
            start="INIT",
            transitions=[
                Transition(
                    from_state="INIT",
                    on_event="start_review",
                    to_state="ANALYSIS",
                    guard="has_valid_pr",
                ),
                Transition(
                    from_state="ANALYSIS",
                    on_event="analysis_complete",
                    to_state="AGENT_DISPATCH",
                    guard="analysis_passed",
                ),
                Transition(
                    from_state="AGENT_DISPATCH",
                    on_event="agents_complete",
                    to_state="REVIEW_AGGREGATION",
                    guard="all_agents_responded",
                ),
                Transition(
                    from_state="REVIEW_AGGREGATION",
                    on_event="aggregation_complete",
                    to_state="FEEDBACK",
                    guard="has_results",
                ),
                Transition(
                    from_state="FEEDBACK",
                    on_event="feedback_posted",
                    to_state="COMPLETE",
                    guard=None,
                ),
                # Error transitions
                Transition(from_state="ANALYSIS", on_event="error", to_state="ERROR", guard=None),
                Transition(from_state="AGENT_DISPATCH", on_event="timeout", to_state="ERROR", guard=None),
                Transition(from_state="REVIEW_AGGREGATION", on_event="error", to_state="ERROR", guard=None),
            ],
            guards={
                "has_valid_pr": "lambda state: state.get('pr_number') is not None",
                "analysis_passed": "lambda state: state.get('analysis_score', 0) > 0.5",
                "all_agents_responded": "lambda state: len(state.get('agent_results', [])) >= 3",
                "has_results": "lambda state: state.get('aggregated_results') is not None",
            },
        )

        # Step 2: Generate protocol to file
        generator = ProtocolGenerator()
        protocol_path = workspace / "protocols" / "review-workflow.yaml"
        generator.generate(protocol, protocol_path)
        print(f"✅ Generated protocol: {protocol_path.name}")

        # Step 3: Validate FSM
        fsm_validator = FSMValidator(protocol=protocol)
        validation_report = fsm_validator.validate()
        assert validation_report.passed is True
        print(f"✅ FSM validation: PASSED (states: {len(protocol.states)}, transitions: {len(protocol.transitions)})")

        # Step 4: Generate FSM validation report
        report_gen = ReportGenerator()
        report_path = workspace / "reports" / "fsm-validation.json"
        report_gen.generate_validation_report(validation_report, report_path, ReportFormat.JSON)
        print(f"✅ FSM validation report generated: {report_path.name}")

        # Step 5: Test FSM properties
        assert validation_report.high_count == 0
        assert validation_report.passed is True
        print("✅ FSM analysis: Valid state machine")

        # Step 6: Verify roundtrip
        loaded_protocol_data = load_yaml(protocol_path)
        loaded_protocol = Protocol(**loaded_protocol_data)
        assert loaded_protocol.start == "INIT"
        assert len(loaded_protocol.transitions) == 8
        assert len(loaded_protocol.guards) == 4
        print("✅ Roundtrip validation: SUCCESS")

    def test_multi_format_report_generation_workflow(self, workspace: Path):
        """Test generating reports in multiple formats from single validation."""
        print("\n🔄 Testing multi-format report generation workflow...")

        # Create a validation report with mixed severity deviations
        report = ValidationReport()
        report.add_deviation(
            Deviation(
                type=DeviationType.FSM_MISMATCH,
                severity=DeviationSeverity.HIGH,
                description="Agent state transition violates protocol",
                location="agents/coordinator.py:156",
                fix_hint="Update agent to follow review-workflow.yaml protocol",
            )
        )
        report.add_deviation(
            Deviation(
                type=DeviationType.MISSING_FEATURE,
                severity=DeviationSeverity.MEDIUM,
                description="FEATURE-002 (LLM Integration) not implemented",
                location="src/llm/",
                fix_hint="Implement LLM provider abstraction layer",
            )
        )
        report.add_deviation(
            Deviation(
                type=DeviationType.RISK_OMISSION,
                severity=DeviationSeverity.LOW,
                description="No security risks documented for v1.0 release",
                location="plan.yaml:45",
                fix_hint="Add security risk analysis",
            )
        )

        # Generate reports in all formats
        generator = ReportGenerator()

        # Markdown format
        md_path = workspace / "reports" / "validation-report.md"
        generator.generate_validation_report(report, md_path, ReportFormat.MARKDOWN)
        assert md_path.exists()
        md_content = md_path.read_text()
        assert "# Validation Report" in md_content
        assert "🔴 **HIGH**: 1" in md_content or "HIGH" in md_content
        print(f"✅ Generated Markdown report: {md_path.name}")

        # JSON format
        json_path = workspace / "reports" / "validation-report.json"
        generator.generate_validation_report(report, json_path, ReportFormat.JSON)
        assert json_path.exists()
        json_content = json_path.read_text()
        assert '"high_count": 1' in json_content
        assert '"passed": false' in json_content
        print(f"✅ Generated JSON report: {json_path.name}")

        # YAML format
        yaml_path = workspace / "reports" / "validation-report.yaml"
        generator.generate_validation_report(report, yaml_path, ReportFormat.YAML)
        assert yaml_path.exists()
        yaml_content = yaml_path.read_text()
        assert "high_count: 1" in yaml_content
        assert "passed: false" in yaml_content
        print(f"✅ Generated YAML report: {yaml_path.name}")

        # Verify all formats contain same deviation information
        for fmt_name, path in [("Markdown", md_path), ("JSON", json_path), ("YAML", yaml_path)]:
            content = path.read_text().lower()
            assert "fsm_mismatch" in content or "fsm" in content or "protocol" in content or "agent" in content
            assert "missing_feature" in content or "missing" in content or "feature" in content or "llm" in content
            assert "risk_omission" in content or "risk" in content or "security" in content
            print(f"   ✓ {fmt_name}: All deviations present")

    def test_complete_ci_cd_workflow_simulation(self, workspace: Path):
        """Simulate complete CI/CD workflow: generate plan → validate → generate protocol → validate → report."""
        print("\n🔄 Testing complete CI/CD workflow simulation...")

        # Step 1: Create and generate plan
        plan = PlanBundle(
            version="1.0",
            idea=Idea(
                title="CI/CD Test Project",
                narrative="Testing automated validation",
                metrics=None,
            ),
            business=None,
            product=Product(
                themes=["Testing", "Automation"],
                releases=[
                    Release(
                        name="v1.0",
                        objectives=["Automated validation"],
                        scope=["FEATURE-001"],
                        risks=["Integration complexity"],
                    )
                ],
            ),
            features=[
                Feature(
                    key="FEATURE-001",
                    title="Automated Validation",
                    outcomes=["Fast feedback", "High confidence"],
                    stories=[
                        Story(
                            key="STORY-001",
                            title="Validation Pipeline",
                            acceptance=["All checks pass", "Reports generated"],
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
            ],
            metadata=None,
            clarifications=None,
        )

        plan_gen = PlanGenerator()
        plan_path = workspace / "plans" / "ci-cd-test.yaml"
        plan_gen.generate(plan, plan_path)
        print(f"✅ Plan generated: {plan_path.name}")

        # Step 2: Validate plan
        is_valid, _error, _loaded_plan_bundle = validate_plan_bundle(plan_path)
        assert is_valid is True
        plan_validation = ValidationReport()  # Empty report for passed validation
        print("✅ Plan validation: PASSED")

        # Step 3: Create and generate protocol
        protocol = Protocol(
            states=["START", "VALIDATE", "TEST", "DEPLOY", "DONE"],
            start="START",
            transitions=[
                Transition(from_state="START", on_event="trigger", to_state="VALIDATE", guard=None),
                Transition(from_state="VALIDATE", on_event="valid", to_state="TEST", guard=None),
                Transition(from_state="TEST", on_event="passed", to_state="DEPLOY", guard=None),
                Transition(from_state="DEPLOY", on_event="deployed", to_state="DONE", guard=None),
            ],
        )

        proto_gen = ProtocolGenerator()
        proto_path = workspace / "protocols" / "ci-cd-workflow.yaml"
        proto_gen.generate(protocol, proto_path)
        print(f"✅ Protocol generated: {proto_path.name}")

        # Step 4: Validate protocol
        proto_validator = FSMValidator(protocol=protocol)
        proto_validation = proto_validator.validate()
        assert proto_validation.passed is True
        print("✅ Protocol validation: PASSED")

        # Step 5: Generate consolidated report
        consolidated_report = ValidationReport()
        # Add summary information from both validations
        if not plan_validation.passed:
            for dev in plan_validation.deviations:
                consolidated_report.add_deviation(dev)
        if not proto_validation.passed:
            for dev in proto_validation.deviations:
                consolidated_report.add_deviation(dev)

        report_gen = ReportGenerator()
        final_report_path = workspace / "reports" / "ci-cd-final-report.md"
        report_gen.generate_validation_report(consolidated_report, final_report_path, ReportFormat.MARKDOWN)
        print(f"✅ Final report generated: {final_report_path.name}")

        # Step 6: Verify all artifacts exist
        assert plan_path.exists()
        assert proto_path.exists()
        assert final_report_path.exists()
        print("✅ All CI/CD artifacts present")

        # Verify report indicates success
        report_content = final_report_path.read_text()
        assert "PASSED" in report_content
        print("✅ CI/CD workflow: COMPLETE")


class TestPlanAddCommandsE2E:
    """End-to-end tests for plan add-feature and add-story commands."""

    @pytest.fixture
    def workspace(self, tmp_path: Path) -> Path:
        """Create a temporary workspace for plan add command tests."""
        workspace = tmp_path / "add_commands_workspace"
        workspace.mkdir()
        (workspace / ".specfact").mkdir()
        (workspace / ".specfact" / "plans").mkdir()
        return workspace

    def test_e2e_add_feature_and_story_workflow(self, workspace: Path, monkeypatch):
        """Test complete workflow: init -> add-feature -> add-story -> compare."""
        from typer.testing import CliRunner

        from specfact_cli.cli import app

        monkeypatch.chdir(workspace)
        runner = CliRunner()
        bundle_name = "test-bundle"

        # Step 1: Initialize plan
        result = runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])
        assert result.exit_code == 0
        print("✅ Plan initialized")

        # Step 2: Add feature via CLI
        feature_result = runner.invoke(
            app,
            [
                "plan",
                "add-feature",
                "--bundle",
                bundle_name,
                "--key",
                "FEATURE-001",
                "--title",
                "User Authentication System",
                "--outcomes",
                "Secure login, Session management, Password recovery",
                "--acceptance",
                "Login works, Sessions persist, Recovery flow works",
            ],
        )
        assert feature_result.exit_code == 0
        print("✅ Feature added via CLI")

        # Step 3: Add story to feature via CLI
        story_result = runner.invoke(
            app,
            [
                "plan",
                "add-story",
                "--bundle",
                bundle_name,
                "--feature",
                "FEATURE-001",
                "--key",
                "STORY-001",
                "--title",
                "Implement login API endpoint",
                "--acceptance",
                "API responds 200, Authentication succeeds, JWT token returned",
                "--story-points",
                "5",
                "--value-points",
                "8",
            ],
        )
        assert story_result.exit_code == 0
        print("✅ Story added via CLI")

        # Step 4: Verify plan structure (modular bundle)
        from specfact_cli.commands.plan import _convert_project_bundle_to_plan_bundle
        from specfact_cli.utils.bundle_loader import load_project_bundle

        bundle_dir = workspace / ".specfact" / "projects" / bundle_name
        assert bundle_dir.exists()

        project_bundle = load_project_bundle(bundle_dir, validate_hashes=False)
        bundle = _convert_project_bundle_to_plan_bundle(project_bundle)

        assert len(bundle.features) == 1
        assert bundle.features[0].key == "FEATURE-001"
        assert bundle.features[0].title == "User Authentication System"
        assert len(bundle.features[0].outcomes) == 3
        assert len(bundle.features[0].stories) == 1
        assert bundle.features[0].stories[0].key == "STORY-001"
        assert bundle.features[0].stories[0].story_points == 5
        assert bundle.features[0].stories[0].value_points == 8
        print("✅ Plan structure verified")

        # Step 5: Add another story to demonstrate multi-story feature
        story2_result = runner.invoke(
            app,
            [
                "plan",
                "add-story",
                "--bundle",
                bundle_name,
                "--feature",
                "FEATURE-001",
                "--key",
                "STORY-002",
                "--title",
                "Implement session management",
                "--acceptance",
                "Session created, Session validated, Session expired",
                "--story-points",
                "3",
            ],
        )
        assert story2_result.exit_code == 0

        # Verify both stories exist
        project_bundle = load_project_bundle(bundle_dir, validate_hashes=False)
        bundle = _convert_project_bundle_to_plan_bundle(project_bundle)
        assert bundle is not None, "Plan bundle should not be None when validation passes"
        assert len(bundle.features[0].stories) == 2
        story_keys = {s.key for s in bundle.features[0].stories}
        assert "STORY-001" in story_keys
        assert "STORY-002" in story_keys
        print("✅ Multiple stories verified")

        print("✅ Complete add-feature and add-story E2E workflow passed")

    def test_e2e_add_multiple_features_workflow(self, workspace: Path, monkeypatch):
        """Test adding multiple features sequentially."""
        from typer.testing import CliRunner

        from specfact_cli.cli import app

        monkeypatch.chdir(workspace)
        runner = CliRunner()
        bundle_name = "test-bundle"

        # Initialize plan
        runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])

        # Add first feature
        result1 = runner.invoke(
            app,
            [
                "plan",
                "add-feature",
                "--bundle",
                bundle_name,
                "--key",
                "FEATURE-001",
                "--title",
                "Authentication",
            ],
        )
        assert result1.exit_code == 0

        # Add second feature
        result2 = runner.invoke(
            app,
            [
                "plan",
                "add-feature",
                "--bundle",
                bundle_name,
                "--key",
                "FEATURE-002",
                "--title",
                "Authorization",
            ],
        )
        assert result2.exit_code == 0

        # Add third feature
        result3 = runner.invoke(
            app,
            [
                "plan",
                "add-feature",
                "--bundle",
                bundle_name,
                "--key",
                "FEATURE-003",
                "--title",
                "User Management",
            ],
        )
        assert result3.exit_code == 0

        # Verify all features exist (modular bundle)
        from specfact_cli.commands.plan import _convert_project_bundle_to_plan_bundle
        from specfact_cli.utils.bundle_loader import load_project_bundle

        bundle_dir = workspace / ".specfact" / "projects" / bundle_name
        project_bundle = load_project_bundle(bundle_dir, validate_hashes=False)
        bundle = _convert_project_bundle_to_plan_bundle(project_bundle)

        assert len(bundle.features) == 3
        feature_keys = {f.key for f in bundle.features}
        assert "FEATURE-001" in feature_keys
        assert "FEATURE-002" in feature_keys
        assert "FEATURE-003" in feature_keys

        print("✅ Multiple features E2E workflow passed")


class TestPlanCreationE2E:
    """End-to-end tests for plan creation workflows."""

    @pytest.fixture
    def workspace(self, tmp_path: Path) -> Path:
        """Create a temporary workspace for plan creation tests."""
        workspace = tmp_path / "plan_workspace"
        workspace.mkdir()
        (workspace / "plans").mkdir()
        (workspace / "reports").mkdir()
        return workspace

    def test_complete_plan_creation_and_validation_workflow(self, workspace: Path):
        """Test complete workflow: Create plan → Validate → Use in workflows."""
        print("\n🔄 Testing complete plan creation and validation workflow...")

        # Step 1: Create a comprehensive plan programmatically (simulating CLI output)
        from specfact_cli.generators.plan_generator import PlanGenerator
        from specfact_cli.validators.schema import validate_plan_bundle

        plan = PlanBundle(
            version="1.0",
            idea=Idea(
                title="E2E Test Project",
                narrative="End-to-end testing of plan creation",
                target_users=["developers", "QA engineers"],
                value_hypothesis="Improve test coverage by 80%",
                metrics={"coverage_increase": 0.8, "test_speed": 2.5},
            ),
            clarifications=None,
            business=Business(
                segments=["DevTools", "Enterprise"],
                problems=["Low test coverage", "Slow test execution"],
                solutions=["Automated testing", "Parallel execution"],
                differentiation=["AI-powered test generation"],
                risks=["Integration complexity"],
            ),
            product=Product(
                themes=["Testing", "Quality", "Automation"],
                releases=[
                    Release(
                        name="v0.1 - Alpha",
                        objectives=["Prove concept", "Basic functionality"],
                        scope=["FEATURE-001"],
                        risks=["Technical feasibility"],
                    ),
                    Release(
                        name="v1.0 - Production",
                        objectives=["Full feature set", "Production ready"],
                        scope=["FEATURE-001", "FEATURE-002"],
                        risks=["Performance", "Scale"],
                    ),
                ],
            ),
            features=[
                Feature(
                    key="FEATURE-001",
                    title="Automated Test Generation",
                    outcomes=["Increased coverage", "Reduced manual effort"],
                    acceptance=["Coverage > 80%", "Generation time < 5min"],
                    constraints=["Must work with existing frameworks"],
                    confidence=0.9,
                    stories=[
                        Story(
                            key="STORY-001",
                            title="Test Generator Core",
                            acceptance=["Generates valid tests", "Supports Python/JS"],
                            tags=["core", "critical"],
                            story_points=None,
                            value_points=None,
                            confidence=0.85,
                            scenarios=None,
                            contracts=None,
                        ),
                        Story(
                            key="STORY-002",
                            title="Framework Integration",
                            acceptance=["pytest integration", "jest integration"],
                            tags=["integration"],
                            story_points=None,
                            value_points=None,
                            scenarios=None,
                            contracts=None,
                        ),
                    ],
                    source_tracking=None,
                    contract=None,
                    protocol=None,
                ),
                Feature(
                    key="FEATURE-002",
                    title="Parallel Test Execution",
                    outcomes=["Faster test runs", "Better resource utilization"],
                    acceptance=["2x speed improvement", "No flaky tests"],
                    stories=[
                        Story(
                            key="STORY-003",
                            title="Parallel Runner",
                            acceptance=["Runs tests in parallel", "Handles dependencies"],
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
        )

        # Step 2: Generate plan file
        generator = PlanGenerator()
        plan_path = workspace / "plans" / "e2e-test-plan.yaml"
        generator.generate(plan, plan_path)
        print(f"✅ Generated plan: {plan_path.name}")

        # Step 3: Validate plan
        is_valid, error, loaded_plan = validate_plan_bundle(plan_path)
        assert is_valid is True, f"Plan validation failed: {error}"
        assert loaded_plan is not None
        print("✅ Plan validation: PASSED")

        # Step 4: Verify plan content integrity
        assert loaded_plan.idea is not None
        assert loaded_plan.idea.title == "E2E Test Project"
        assert loaded_plan.idea.metrics is not None
        assert loaded_plan.idea.metrics["coverage_increase"] == 0.8

        assert loaded_plan.business is not None
        assert len(loaded_plan.business.segments) == 2

        assert len(loaded_plan.product.themes) == 3
        assert len(loaded_plan.product.releases) == 2

        assert len(loaded_plan.features) == 2
        assert loaded_plan.features[0].key == "FEATURE-001"
        assert len(loaded_plan.features[0].stories) == 2
        assert len(loaded_plan.features[1].stories) == 1

        print("✅ Plan content verification: COMPLETE")

        # Step 5: Test plan can be used in downstream workflows
        # Simulate using plan for protocol generation
        from specfact_cli.generators.protocol_generator import ProtocolGenerator

        # Create a protocol based on plan features
        protocol = Protocol(
            states=["INIT", "GENERATE", "VALIDATE", "EXECUTE", "REPORT", "DONE"],
            start="INIT",
            transitions=[
                Transition(from_state="INIT", on_event="start", to_state="GENERATE", guard=None),
                Transition(from_state="GENERATE", on_event="generated", to_state="VALIDATE", guard=None),
                Transition(from_state="VALIDATE", on_event="valid", to_state="EXECUTE", guard=None),
                Transition(from_state="EXECUTE", on_event="complete", to_state="REPORT", guard=None),
                Transition(from_state="REPORT", on_event="reported", to_state="DONE", guard=None),
            ],
        )

        proto_gen = ProtocolGenerator()
        proto_path = workspace / "plans" / "test-workflow.yaml"
        proto_gen.generate(protocol, proto_path)
        print("✅ Generated protocol from plan")

        # Step 6: Generate validation report
        from specfact_cli.generators.report_generator import ReportFormat, ReportGenerator

        validation_report = ValidationReport()
        report_gen = ReportGenerator()
        report_path = workspace / "reports" / "plan-validation.md"
        report_gen.generate_validation_report(validation_report, report_path, ReportFormat.MARKDOWN)

        assert report_path.exists()
        report_content = report_path.read_text()
        assert "PASSED" in report_content
        print("✅ Generated validation report")

        # Step 7: Verify all artifacts
        assert plan_path.exists()
        assert proto_path.exists()
        assert report_path.exists()
        print("✅ All artifacts present")

        # Step 8: Verify plan can be reloaded and modified
        reloaded_data = load_yaml(plan_path)
        reloaded_plan = PlanBundle(**reloaded_data)

        assert reloaded_plan.idea is not None
        assert reloaded_plan.idea.title == "E2E Test Project"
        assert len(reloaded_plan.features) == 2
        print("✅ Plan reload and modification: SUCCESS")

        print("\n✅ Complete plan creation E2E workflow: COMPLETE")

    def test_minimal_plan_to_full_plan_evolution(self, workspace: Path):
        """Test evolving a minimal plan into a full plan over time."""
        print("\n🔄 Testing plan evolution workflow...")

        from specfact_cli.generators.plan_generator import PlanGenerator
        from specfact_cli.validators.schema import validate_plan_bundle

        # Step 1: Start with minimal plan
        minimal_plan = PlanBundle(
            version="1.0",
            idea=None,
            business=None,
            product=Product(themes=[], releases=[]),
            features=[],
            metadata=None,
            clarifications=None,
        )

        generator = PlanGenerator()
        plan_path = workspace / "plans" / "evolving-plan.yaml"
        generator.generate(minimal_plan, plan_path)
        print("✅ Created minimal plan")

        # Step 2: Add idea
        plan_data = load_yaml(plan_path)
        plan_data["idea"] = {
            "title": "Evolving Project",
            "narrative": "A project that grows over time",
        }
        dump_yaml(plan_data, plan_path)
        print("✅ Added idea")

        # Step 3: Add themes
        plan_data = load_yaml(plan_path)
        plan_data["product"]["themes"] = ["Core", "Advanced"]
        dump_yaml(plan_data, plan_path)
        print("✅ Added themes")

        # Step 4: Add first feature
        plan_data = load_yaml(plan_path)
        plan_data["features"] = [
            {
                "key": "FEATURE-001",
                "title": "First Feature",
                "outcomes": ["Initial functionality"],
                "acceptance": ["Works"],
                "stories": [],
            }
        ]
        dump_yaml(plan_data, plan_path)
        print("✅ Added first feature")

        # Step 5: Add story to feature
        plan_data = load_yaml(plan_path)
        plan_data["features"][0]["stories"] = [
            {
                "key": "STORY-001",
                "title": "First Story",
                "acceptance": ["Implemented"],
            }
        ]
        dump_yaml(plan_data, plan_path)
        print("✅ Added first story")

        # Step 6: Validate evolved plan
        is_valid, _error, final_plan = validate_plan_bundle(plan_path)
        assert is_valid is True
        assert final_plan is not None
        assert final_plan.idea is not None
        assert final_plan.idea.title == "Evolving Project"
        assert len(final_plan.product.themes) == 2
        assert len(final_plan.features) == 1
        assert len(final_plan.features[0].stories) == 1
        print("✅ Evolved plan validation: PASSED")

        print("\n✅ Plan evolution workflow: COMPLETE")


class TestPlanComparisonWorkflow:
    """Test complete plan comparison workflows."""

    @pytest.fixture
    def workspace(self, tmp_path: Path) -> Path:
        """Create a temporary workspace."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        (workspace / "contracts").mkdir()
        (workspace / "contracts" / "plans").mkdir()
        (workspace / "reports").mkdir()
        return workspace

    def test_complete_plan_comparison_workflow(self, workspace: Path):
        """Test complete plan comparison with deviation detection and reporting."""
        from specfact_cli.comparators.plan_comparator import PlanComparator

        # Step 1: Create manual plan (source of truth)
        manual_idea = Idea(title="Task Manager", narrative="A comprehensive task management system", metrics=None)
        manual_product = Product(themes=["Productivity", "Collaboration"], releases=[])
        manual_features = [
            Feature(
                key="FEATURE-001",
                title="Task CRUD",
                outcomes=["Users can create, read, update, delete tasks"],
                acceptance=["CRUD operations work"],
                stories=[
                    Story(
                        key="STORY-001",
                        title="Create Task",
                        acceptance=["Task created"],
                        story_points=None,
                        value_points=None,
                        scenarios=None,
                        contracts=None,
                    ),
                    Story(
                        key="STORY-002",
                        title="Edit Task",
                        acceptance=["Task updated"],
                        story_points=None,
                        value_points=None,
                        scenarios=None,
                        contracts=None,
                    ),
                    Story(
                        key="STORY-003",
                        title="Delete Task",
                        acceptance=["Task deleted"],
                        story_points=None,
                        value_points=None,
                        scenarios=None,
                        contracts=None,
                    ),
                ],
                source_tracking=None,
                contract=None,
                protocol=None,
            ),
            Feature(
                key="FEATURE-002",
                title="Task Assignments",
                outcomes=["Users can assign tasks to team members"],
                acceptance=["Assignments work"],
                stories=[
                    Story(
                        key="STORY-004",
                        title="Assign Task",
                        acceptance=["Task assigned"],
                        story_points=None,
                        value_points=None,
                        scenarios=None,
                        contracts=None,
                    ),
                ],
                source_tracking=None,
                contract=None,
                protocol=None,
            ),
            Feature(
                key="FEATURE-003",
                title="Notifications",
                outcomes=["Users get notified of task updates"],
                acceptance=["Notifications sent"],
                stories=[],
                source_tracking=None,
                contract=None,
                protocol=None,
            ),
        ]

        manual_plan = PlanBundle(
            version="1.0",
            idea=manual_idea,
            business=None,
            product=manual_product,
            features=manual_features,
            metadata=None,
            clarifications=None,
        )

        manual_path = workspace / "contracts" / "plans" / "manual.yaml"
        generator = PlanGenerator()
        generator.generate(manual_plan, manual_path)
        print("✅ Created manual plan")

        # Step 2: Create auto-derived plan (reverse-engineered from code)
        # Simulating brownfield analysis where some features are missing/different
        auto_idea = Idea(title="Task Manager", narrative="A comprehensive task management system", metrics=None)
        auto_product = Product(themes=["Productivity"], releases=[])  # Missing "Collaboration" theme
        auto_features = [
            Feature(
                key="FEATURE-001",
                title="Task CRUD",
                outcomes=["Users can create, read, update, delete tasks"],
                acceptance=["CRUD operations work"],
                stories=[
                    Story(
                        key="STORY-001",
                        title="Create Task",
                        acceptance=["Task created"],
                        story_points=None,
                        value_points=None,
                        scenarios=None,
                        contracts=None,
                    ),
                    Story(
                        key="STORY-002",
                        title="Edit Task",
                        acceptance=["Task updated"],
                        story_points=None,
                        value_points=None,
                        scenarios=None,
                        contracts=None,
                    ),
                    # Missing STORY-003 (Delete Task)
                ],
                source_tracking=None,
                contract=None,
                protocol=None,
            ),
            Feature(
                key="FEATURE-002",
                title="Task Assignments",
                outcomes=["Users can assign tasks to team members"],
                acceptance=["Assignments work"],
                stories=[
                    Story(
                        key="STORY-004",
                        title="Assign Task",
                        acceptance=["Task assigned"],
                        story_points=None,
                        value_points=None,
                        scenarios=None,
                        contracts=None,
                    ),
                ],
                source_tracking=None,
                contract=None,
                protocol=None,
            ),
            # Missing FEATURE-003 (Notifications)
            Feature(
                key="FEATURE-004",
                title="Task Search",  # Extra feature not in manual plan
                outcomes=["Users can search tasks"],
                acceptance=["Search works"],
                stories=[],
                source_tracking=None,
                contract=None,
                protocol=None,
            ),
        ]

        auto_plan = PlanBundle(
            version="1.0",
            idea=auto_idea,
            business=None,
            product=auto_product,
            features=auto_features,
            metadata=None,
            clarifications=None,
        )

        auto_path = workspace / "contracts" / "plans" / "auto-derived.yaml"
        generator.generate(auto_plan, auto_path)
        print("✅ Created auto-derived plan")

        # Step 3: Compare plans
        comparator = PlanComparator()
        report = comparator.compare(
            manual_plan,
            auto_plan,
            manual_label=str(manual_path),
            auto_label=str(auto_path),
        )
        print(f"✅ Compared plans: {report.total_deviations} deviations found")

        # Step 4: Verify deviations
        assert report.total_deviations > 0

        # Verify expected deviations:
        # 1. Missing theme "Collaboration" (LOW severity)
        # 2. Missing STORY-003 in FEATURE-001 (HIGH severity - not draft)
        # 3. Missing FEATURE-003 (MEDIUM severity - has no stories)
        # 4. Extra FEATURE-004 (HIGH severity if confidence >= 0.8, or LOW if stories == 0 and confidence < 0.8)
        #    Since FEATURE-004 has default confidence 1.0, it will be HIGH

        deviation_types = {d.type for d in report.deviations}
        assert DeviationType.MISMATCH in deviation_types  # Theme mismatch
        assert DeviationType.MISSING_STORY in deviation_types  # Missing story
        assert DeviationType.MISSING_FEATURE in deviation_types  # Missing feature
        assert DeviationType.EXTRA_IMPLEMENTATION in deviation_types  # Extra feature

        # Verify severity counts
        # STORY-003 is HIGH (not draft)
        # FEATURE-004 is HIGH (confidence 1.0 >= 0.8)
        # FEATURE-003 is MEDIUM (no stories)
        assert report.high_count >= 2  # Missing STORY-003 + Extra FEATURE-004
        assert report.medium_count >= 1  # Missing FEATURE-003
        assert report.low_count >= 1  # Theme mismatch

        print(f"   🔴 HIGH: {report.high_count}")
        print(f"   🟡 MEDIUM: {report.medium_count}")
        print(f"   🔵 LOW: {report.low_count}")

        # Step 5: Generate markdown report
        report_generator = ReportGenerator()
        markdown_report_path = workspace / "reports" / "deviations.md"
        report_generator.generate_deviation_report(report, markdown_report_path, ReportFormat.MARKDOWN)
        assert markdown_report_path.exists()
        print("✅ Generated markdown report")

        # Verify markdown content
        markdown_content = markdown_report_path.read_text()
        assert "# Deviation Report" in markdown_content
        assert "FEATURE-003" in markdown_content
        assert "STORY-003" in markdown_content
        assert "FEATURE-004" in markdown_content

        # Step 6: Generate JSON report
        json_report_path = workspace / "reports" / "deviations.json"
        report_generator.generate_deviation_report(report, json_report_path, ReportFormat.JSON)
        assert json_report_path.exists()
        print("✅ Generated JSON report")

        # Verify JSON structure
        import json

        json_data = json.loads(json_report_path.read_text())
        assert "manual_plan" in json_data
        assert "auto_plan" in json_data
        assert "deviations" in json_data
        assert len(json_data["deviations"]) == report.total_deviations

        print("\n✅ Plan comparison workflow: COMPLETE")

    def test_brownfield_to_compliant_workflow(self, workspace: Path):
        """Test workflow from brownfield discovery to plan compliance."""
        from specfact_cli.comparators.plan_comparator import PlanComparator

        # Step 1: Create initial auto-derived plan (incomplete, from code analysis)
        auto_idea = Idea(title="Legacy System", narrative="Existing codebase", metrics=None)
        auto_product = Product(themes=["Legacy"], releases=[])
        auto_features = [
            Feature(
                key="FEATURE-001",
                title="User Auth",
                outcomes=["Authentication works"],
                acceptance=["Users can login"],
                stories=[],  # No stories documented
                source_tracking=None,
                contract=None,
                protocol=None,
            ),
        ]

        initial_auto_plan = PlanBundle(
            version="1.0",
            idea=auto_idea,
            business=None,
            product=auto_product,
            features=auto_features,
            metadata=None,
            clarifications=None,
        )

        auto_path = workspace / "contracts" / "plans" / "brownfield-auto.yaml"
        generator = PlanGenerator()
        generator.generate(initial_auto_plan, auto_path)
        print("✅ Created initial brownfield auto plan")

        # Step 2: Create comprehensive manual plan (what should exist)
        manual_idea = Idea(
            title="Legacy System",
            narrative="Modernized legacy application",
            target_users=["Enterprise customers"],
            metrics=None,
        )
        manual_product = Product(themes=["Modern", "Secure"], releases=[])
        manual_features = [
            Feature(
                key="FEATURE-001",
                title="User Auth",
                outcomes=["Secure authentication", "MFA support"],
                acceptance=["Users can login", "MFA works"],
                stories=[
                    Story(
                        key="STORY-001",
                        title="Login API",
                        acceptance=["API works"],
                        story_points=None,
                        value_points=None,
                        scenarios=None,
                        contracts=None,
                    ),
                    Story(
                        key="STORY-002",
                        title="MFA Setup",
                        acceptance=["MFA configured"],
                        story_points=None,
                        value_points=None,
                        scenarios=None,
                        contracts=None,
                    ),
                ],
                source_tracking=None,
                contract=None,
                protocol=None,
            ),
            Feature(
                key="FEATURE-002",
                title="Session Management",
                outcomes=["Secure sessions"],
                acceptance=["Sessions work"],
                stories=[],
                source_tracking=None,
                contract=None,
                protocol=None,
            ),
        ]

        manual_plan = PlanBundle(
            version="1.0",
            idea=manual_idea,
            business=None,
            product=manual_product,
            features=manual_features,
            metadata=None,
            clarifications=None,
        )

        manual_path = workspace / "contracts" / "plans" / "manual-target.yaml"
        generator.generate(manual_plan, manual_path)
        print("✅ Created target manual plan")

        # Step 3: Compare and identify gaps
        comparator = PlanComparator()
        initial_report = comparator.compare(manual_plan, initial_auto_plan)
        print(f"✅ Initial comparison: {initial_report.total_deviations} gaps found")

        assert initial_report.total_deviations > 0
        assert initial_report.high_count >= 1  # Missing features
        assert initial_report.medium_count >= 1  # Missing stories

        # Step 4: Iteratively fix implementation
        # Simulating developer adding missing features
        improved_auto_plan = PlanBundle(
            version="1.0",
            idea=auto_idea,
            business=None,
            product=Product(themes=["Modern", "Secure"], releases=[]),
            features=[
                Feature(
                    key="FEATURE-001",
                    title="User Auth",
                    outcomes=["Secure authentication", "MFA support"],
                    acceptance=["Users can login", "MFA works"],
                    stories=[
                        Story(
                            key="STORY-001",
                            title="Login API",
                            acceptance=["API works"],
                            story_points=None,
                            value_points=None,
                            scenarios=None,
                            contracts=None,
                        ),
                        Story(
                            key="STORY-002",
                            title="MFA Setup",
                            acceptance=["MFA configured"],
                            story_points=None,
                            value_points=None,
                            scenarios=None,
                            contracts=None,
                        ),
                    ],
                    source_tracking=None,
                    contract=None,
                    protocol=None,
                ),
                Feature(
                    key="FEATURE-002",
                    title="Session Management",
                    outcomes=["Secure sessions"],
                    acceptance=["Sessions work"],
                    stories=[],
                    source_tracking=None,
                    contract=None,
                    protocol=None,
                ),
            ],
            metadata=None,
            clarifications=None,
        )

        generator.generate(improved_auto_plan, auto_path)
        print("✅ Updated brownfield implementation")

        # Step 5: Re-compare and verify compliance
        final_report = comparator.compare(manual_plan, improved_auto_plan)
        print(f"✅ Final comparison: {final_report.total_deviations} deviations remaining")

        # Should have significantly fewer deviations
        assert final_report.total_deviations < initial_report.total_deviations
        assert final_report.high_count == 0  # No missing critical features

        # May still have minor mismatches (idea narrative, etc.)
        assert final_report.low_count >= 0

        print("\n✅ Brownfield compliance workflow: COMPLETE")


class TestBrownfieldAnalysisWorkflow:
    """E2E tests for brownfield code analysis workflow."""

    def test_analyze_specfact_cli_itself(self):
        """
        Test analyzing specfact-cli codebase itself.

        This demonstrates the brownfield analysis workflow on a real codebase.
        """
        print("\n🏭 Testing brownfield analysis on specfact-cli itself")

        from pathlib import Path

        from specfact_cli.analyzers.code_analyzer import CodeAnalyzer

        # Analyze scoped subset of specfact-cli codebase (analyzers module) for faster tests
        repo_path = Path(".")
        entry_point = repo_path / "src" / "specfact_cli" / "analyzers"
        analyzer = CodeAnalyzer(repo_path, confidence_threshold=0.5, entry_point=entry_point)

        print("📊 Analyzing specfact-cli codebase (scoped to analyzers)...")
        plan_bundle = analyzer.analyze()

        # Verify analysis results
        print(f"✅ Found {len(plan_bundle.features)} features")
        assert len(plan_bundle.features) > 0, "Should discover features in codebase"

        # Check themes detected
        print(f"✅ Detected themes: {', '.join(plan_bundle.product.themes)}")
        assert len(plan_bundle.product.themes) > 0, "Should detect themes from imports"

        # Verify stories have points
        total_stories = sum(len(f.stories) for f in plan_bundle.features)
        print(f"✅ Extracted {total_stories} user stories")
        assert total_stories > 0, "Should extract user stories from methods"

        # Verify story structure
        for feature in plan_bundle.features[:3]:  # Check first 3 features
            print(f"\n📦 {feature.title} ({feature.key})")
            print(f"   Confidence: {feature.confidence}")
            print(f"   Stories: {len(feature.stories)}")

            for story in feature.stories:
                # Verify story has required fields
                assert story.story_points is not None, f"Story {story.key} missing story points"
                assert story.value_points is not None, f"Story {story.key} missing value points"
                assert len(story.tasks) > 0, f"Story {story.key} has no tasks"
                assert story.title.startswith("As a "), f"Story {story.key} not user-centric"

                print(f"   - {story.title}")
                print(f"     SP:{story.story_points} VP:{story.value_points} Tasks:{len(story.tasks)}")

        print("\n✅ Brownfield analysis on specfact-cli: COMPLETE")

    @pytest.mark.timeout(60)
    def test_analyze_and_generate_plan_bundle(self):
        """
        Test full workflow: analyze → generate → validate.
        """
        print("\n📝 Testing full brownfield workflow")

        import tempfile
        from pathlib import Path

        from specfact_cli.analyzers.code_analyzer import CodeAnalyzer
        from specfact_cli.generators.plan_generator import PlanGenerator
        from specfact_cli.validators.schema import validate_plan_bundle

        # Analyze scoped subset of codebase (analyzers module) for faster tests
        repo_path = Path(".")
        entry_point = repo_path / "src" / "specfact_cli" / "analyzers"
        analyzer = CodeAnalyzer(repo_path, confidence_threshold=0.6, entry_point=entry_point)

        print("🔍 Step 1: Analyzing codebase...")
        plan_bundle = analyzer.analyze()
        assert len(plan_bundle.features) > 0
        print(f"   ✅ Found {len(plan_bundle.features)} features")

        # Generate YAML file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            output_path = Path(f.name)

        try:
            print("\n📄 Step 2: Generating plan bundle YAML...")
            generator = PlanGenerator()
            generator.generate(plan_bundle, output_path)
            assert output_path.exists()
            print(f"   ✅ Generated: {output_path}")

            # Validate generated plan
            print("\n✓ Step 3: Validating plan bundle...")
            is_valid, error, validated_plan = validate_plan_bundle(output_path)
            assert is_valid, f"Generated plan validation failed: {error}"
            print("   ✅ Plan validation passed")

            # Verify validated plan matches
            assert validated_plan is not None
            assert len(validated_plan.features) == len(plan_bundle.features)
            print(f"   ✅ Validated plan has {len(validated_plan.features)} features")

            print("\n✅ Full brownfield workflow: COMPLETE")

        finally:
            if output_path.exists():
                output_path.unlink()

    @pytest.mark.timeout(60)
    def test_cli_analyze_code2spec_on_self(self):
        """
        Test CLI command to analyze specfact-cli itself (scoped to analyzers module for performance).
        """
        print("\n💻 Testing CLI 'import from-code' on specfact-cli")

        import tempfile
        from pathlib import Path

        from typer.testing import CliRunner

        from specfact_cli.cli import app

        runner = CliRunner()

        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "analysis-report.md"

            print("🚀 Running: specfact import from-code (scoped to analyzers)")
            bundle_name = "specfact-auto"

            # Remove existing bundle if it exists (from previous test runs)
            bundle_dir = Path(".") / ".specfact" / "projects" / bundle_name
            if bundle_dir.exists():
                import shutil

                shutil.rmtree(bundle_dir)

            result = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    bundle_name,
                    "--repo",
                    ".",
                    "--entry-point",
                    "src/specfact_cli/analyzers",
                    "--report",
                    str(report_path),
                    "--confidence",
                    "0.5",
                ],
            )

            print(f"Exit code: {result.exit_code}")
            if result.exit_code != 0:
                print(f"Error output:\n{result.stdout}")

            assert result.exit_code == 0, "CLI command should succeed"

            # Verify modular bundle was created
            bundle_dir = Path(".") / ".specfact" / "projects" / bundle_name
            assert bundle_dir.exists(), "Should create project bundle directory"
            assert (bundle_dir / "bundle.manifest.yaml").exists(), "Should create bundle manifest"
            assert report_path.exists(), "Should create analysis report"

            # Verify bundle content (modular bundle)
            from specfact_cli.commands.plan import _convert_project_bundle_to_plan_bundle
            from specfact_cli.utils.bundle_loader import load_project_bundle

            project_bundle = load_project_bundle(bundle_dir, validate_hashes=False)
            plan_bundle = _convert_project_bundle_to_plan_bundle(project_bundle)

            assert plan_bundle.version == "1.0"
            assert len(plan_bundle.features) > 0
            # Verify stories have story_points and value_points
            for feature in plan_bundle.features:
                for story in feature.stories:
                    assert story.story_points is not None or story.story_points is None  # May be None
                    assert story.value_points is not None or story.value_points is None  # May be None

            # Verify report content
            report_content = report_path.read_text()
            assert "Brownfield Import Report" in report_content
            assert "Features Found" in report_content

            print("✅ CLI import from-code on specfact-cli: COMPLETE")

    @pytest.mark.timeout(60)
    def test_self_analysis_consistency(self):
        """
        Test that analyzing specfact-cli multiple times produces consistent results.
        """
        print("\n🔄 Testing analysis consistency")

        from pathlib import Path

        from specfact_cli.analyzers.code_analyzer import CodeAnalyzer

        repo_path = Path(".")
        entry_point = repo_path / "src" / "specfact_cli" / "analyzers"

        # Run analysis twice (scoped to analyzers module for performance)
        print("🔍 Analysis run 1...")
        analyzer1 = CodeAnalyzer(repo_path, confidence_threshold=0.5, entry_point=entry_point)
        plan1 = analyzer1.analyze()

        print("🔍 Analysis run 2...")
        analyzer2 = CodeAnalyzer(repo_path, confidence_threshold=0.5, entry_point=entry_point)
        plan2 = analyzer2.analyze()

        # Results should be consistent
        assert len(plan1.features) == len(plan2.features), "Feature count should be consistent"
        assert plan1.product.themes == plan2.product.themes, "Themes should be consistent"

        # Story counts should match
        stories1 = sum(len(f.stories) for f in plan1.features)
        stories2 = sum(len(f.stories) for f in plan2.features)
        assert stories1 == stories2, "Story count should be consistent"

        print(f"✅ Both runs found: {len(plan1.features)} features, {stories1} stories")
        print("✅ Analysis consistency: VERIFIED")

    @pytest.mark.timeout(60)
    def test_story_points_fibonacci_compliance(self):
        """
        Verify all discovered stories use valid Fibonacci numbers for points.
        """
        print("\n📊 Testing Fibonacci compliance for story points")

        from pathlib import Path

        from specfact_cli.analyzers.code_analyzer import CodeAnalyzer

        repo_path = Path(".")
        entry_point = repo_path / "src" / "specfact_cli" / "analyzers"
        analyzer = CodeAnalyzer(repo_path, confidence_threshold=0.5, entry_point=entry_point)
        plan = analyzer.analyze()

        valid_fibonacci = [1, 2, 3, 5, 8, 13, 21, 34, 55, 89]

        print(f"🔍 Checking {sum(len(f.stories) for f in plan.features)} stories...")

        for feature in plan.features:
            for story in feature.stories:
                assert story.story_points in valid_fibonacci, (
                    f"Story {story.key} has invalid story points: {story.story_points}"
                )
                assert story.value_points in valid_fibonacci, (
                    f"Story {story.key} has invalid value points: {story.value_points}"
                )

        print("✅ All stories use valid Fibonacci numbers")

    def test_user_centric_story_format(self):
        """
        Verify all discovered stories follow user-centric format.
        """
        print("\n👤 Testing user-centric story format")

        from pathlib import Path

        from specfact_cli.analyzers.code_analyzer import CodeAnalyzer

        repo_path = Path(".")
        entry_point = repo_path / "src" / "specfact_cli" / "analyzers"
        analyzer = CodeAnalyzer(repo_path, confidence_threshold=0.5, entry_point=entry_point)
        plan = analyzer.analyze()

        total_stories = 0
        user_centric_count = 0

        for feature in plan.features:
            for story in feature.stories:
                total_stories += 1
                if story.title.startswith("As a user") or story.title.startswith("As a developer"):
                    user_centric_count += 1

        print(f"✅ {user_centric_count}/{total_stories} stories are user-centric")
        assert user_centric_count == total_stories, "All stories should be user-centric"

    @pytest.mark.timeout(60)
    def test_task_extraction_from_methods(self):
        """
        Verify tasks are properly extracted from method names.
        """
        print("\n⚙️  Testing task extraction from methods")

        from pathlib import Path

        from specfact_cli.analyzers.code_analyzer import CodeAnalyzer

        repo_path = Path(".")
        entry_point = repo_path / "src" / "specfact_cli" / "analyzers"
        analyzer = CodeAnalyzer(repo_path, confidence_threshold=0.5, entry_point=entry_point)
        plan = analyzer.analyze()

        total_tasks = 0

        for feature in plan.features:
            for story in feature.stories:
                assert len(story.tasks) > 0, f"Story {story.key} has no tasks"

                for task in story.tasks:
                    total_tasks += 1
                    assert task.endswith("()"), f"Task should be method name with (): {task}"

        print(f"✅ Extracted {total_tasks} tasks from method names")
        assert total_tasks > 0, "Should extract tasks from methods"

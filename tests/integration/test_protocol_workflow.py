"""Integration tests for protocol validation workflow."""

from __future__ import annotations

from pathlib import Path

import pytest

from specfact_cli.models.protocol import Protocol, Transition
from specfact_cli.utils.yaml_utils import dump_yaml, load_yaml
from specfact_cli.validators.fsm import FSMValidator
from specfact_cli.validators.schema import SchemaValidator


class TestProtocolWorkflow:
    """Test complete protocol workflow from YAML to FSM validation."""

    @pytest.fixture
    def fixtures_dir(self) -> Path:
        """Get the fixtures directory."""
        return Path(__file__).parent.parent / "fixtures"

    @pytest.fixture
    def sample_protocol_path(self, fixtures_dir: Path) -> Path:
        """Get the sample protocol path."""
        return fixtures_dir / "protocols" / "sample-protocol.yaml"

    @pytest.fixture
    def invalid_protocol_path(self, fixtures_dir: Path) -> Path:
        """Get the invalid protocol path."""
        return fixtures_dir / "protocols" / "invalid-protocol.yaml"

    def test_load_protocol_from_yaml(self, sample_protocol_path: Path):
        """Test loading a protocol from YAML file."""
        # Load YAML
        data = load_yaml(sample_protocol_path)

        # Verify structure
        assert "states" in data
        assert "start" in data
        assert "transitions" in data
        assert "guards" in data

        # Verify states
        assert len(data["states"]) == 5
        assert "INIT" in data["states"]

        # Verify transitions
        assert len(data["transitions"]) == 6

    def test_parse_protocol_to_model(self, sample_protocol_path: Path):
        """Test parsing YAML data into Protocol model."""
        data = load_yaml(sample_protocol_path)

        # Parse transitions
        transitions = [Transition(**t) for t in data["transitions"]]

        # Create protocol
        protocol = Protocol(
            states=data["states"],
            start=data["start"],
            transitions=transitions,
            guards=data.get("guards", {}),
        )

        # Verify model
        assert len(protocol.states) == 5
        assert protocol.start == "INIT"
        assert len(protocol.transitions) == 6
        assert "is_approved" in protocol.guards

    def test_validate_protocol_fsm(self, sample_protocol_path: Path):
        """Test FSM validation of a valid protocol."""
        data = load_yaml(sample_protocol_path)

        # Parse to model
        transitions = [Transition(**t) for t in data["transitions"]]
        protocol = Protocol(
            states=data["states"],
            start=data["start"],
            transitions=transitions,
            guards=data.get("guards", {}),
        )

        # Create FSM validator
        validator = FSMValidator(protocol)

        # Validate
        report = validator.validate()

        # Should pass (guards are defined, states are reachable)
        # Note: There might be a cycle warning, but that's LOW severity
        assert report.high_count == 0  # No high severity issues
        assert report.medium_count == 0  # No medium severity issues

    def test_validate_invalid_protocol(self, invalid_protocol_path: Path):
        """Test FSM validation detects errors in invalid protocol."""
        data = load_yaml(invalid_protocol_path)

        # Parse to model
        transitions = [Transition(**t) for t in data["transitions"]]
        protocol = Protocol(
            states=data["states"],
            start=data["start"],
            transitions=transitions,
        )

        # Create FSM validator
        validator = FSMValidator(protocol)

        # Validate
        report = validator.validate()

        # Should have HIGH severity errors
        assert report.high_count > 0
        assert report.passed is False

        # Check specific issues
        deviation_descriptions = [d.description for d in report.deviations]
        assert any("INVALID_START" in d for d in deviation_descriptions)
        assert any("NONEXISTENT" in d for d in deviation_descriptions)
        assert any("ORPHAN_STATE" in d for d in deviation_descriptions)

    def test_fsm_reachability_analysis(self, sample_protocol_path: Path):
        """Test FSM reachability analysis."""
        data = load_yaml(sample_protocol_path)

        # Parse to model
        transitions = [Transition(**t) for t in data["transitions"]]
        protocol = Protocol(
            states=data["states"],
            start=data["start"],
            transitions=transitions,
        )

        # Create FSM validator
        validator = FSMValidator(protocol)

        # Get reachable states from INIT
        reachable = validator.get_reachable_states("INIT")

        # All states should be reachable
        assert len(reachable) == 5
        assert "INIT" in reachable
        assert "PLANNING" in reachable
        assert "IMPLEMENTATION" in reachable
        assert "REVIEW" in reachable
        assert "DONE" in reachable

    def test_fsm_transition_queries(self, sample_protocol_path: Path):
        """Test FSM transition query methods."""
        data = load_yaml(sample_protocol_path)

        # Parse to model
        transitions = [Transition(**t) for t in data["transitions"]]
        protocol = Protocol(
            states=data["states"],
            start=data["start"],
            transitions=transitions,
        )

        # Create FSM validator
        validator = FSMValidator(protocol)

        # Test get_transitions_from
        review_transitions = validator.get_transitions_from("REVIEW")
        assert len(review_transitions) == 2

        # Test is_valid_transition
        assert validator.is_valid_transition("INIT", "start_planning", "PLANNING") is True
        assert validator.is_valid_transition("INIT", "invalid_event", "PLANNING") is False
        assert validator.is_valid_transition("INIT", "start_planning", "DONE") is False

    def test_protocol_with_guards(self, sample_protocol_path: Path):
        """Test protocol with guard functions."""
        data = load_yaml(sample_protocol_path)

        # Parse to model
        transitions = [Transition(**t) for t in data["transitions"]]
        protocol = Protocol(
            states=data["states"],
            start=data["start"],
            transitions=transitions,
            guards=data.get("guards", {}),
        )

        # Verify guards
        assert "is_approved" in protocol.guards

        # Find transition with guard
        guarded_transitions = [t for t in protocol.transitions if t.guard is not None]
        assert len(guarded_transitions) == 1
        assert guarded_transitions[0].guard == "is_approved"

    def test_roundtrip_protocol(self, sample_protocol_path: Path, tmp_path: Path):
        """Test loading, parsing, and saving a protocol."""
        # Load
        data = load_yaml(sample_protocol_path)

        # Parse to model
        transitions = [Transition(**t) for t in data["transitions"]]
        protocol = Protocol(
            states=data["states"],
            start=data["start"],
            transitions=transitions,
            guards=data.get("guards", {}),
        )

        # Convert to dict
        protocol_dict = protocol.model_dump()

        # Save to new file
        output_path = tmp_path / "output-protocol.yaml"
        dump_yaml(protocol_dict, output_path)

        # Reload
        reloaded_data = load_yaml(output_path)

        # Verify roundtrip
        assert reloaded_data["start"] == "INIT"
        assert len(reloaded_data["states"]) == 5
        assert len(reloaded_data["transitions"]) == 6

    def test_validate_with_json_schema(self, sample_protocol_path: Path):
        """Test validating a protocol with JSON Schema."""
        # Load YAML
        data = load_yaml(sample_protocol_path)

        # Create schema validator
        resources_dir = Path(__file__).parent.parent.parent / "resources"
        validator = SchemaValidator(resources_dir / "schemas")

        # Validate
        report = validator.validate_json_schema(data, "protocol.schema.json")

        # Should pass validation
        assert report.passed is True
        assert len(report.deviations) == 0


class TestProtocolEdgeCases:
    """Test edge cases and error handling."""

    def test_minimal_protocol(self):
        """Test creating a minimal valid protocol."""
        protocol = Protocol(
            states=["A", "B"],
            start="A",
            transitions=[
                Transition(from_state="A", on_event="go", to_state="B", guard=None),
            ],
        )

        # Validate
        validator = FSMValidator(protocol)
        report = validator.validate()

        # Should be valid
        assert report.high_count == 0

    def test_protocol_with_cycle(self):
        """Test protocol with intentional cycle."""
        protocol = Protocol(
            states=["A", "B", "C"],
            start="A",
            transitions=[
                Transition(from_state="A", on_event="e1", to_state="B", guard=None),
                Transition(from_state="B", on_event="e2", to_state="C", guard=None),
                Transition(from_state="C", on_event="e3", to_state="A", guard=None),  # Cycle
            ],
        )

        # Validate
        validator = FSMValidator(protocol)
        report = validator.validate()

        # Should have LOW severity cycle warning
        assert report.low_count >= 1
        assert report.high_count == 0

    def test_protocol_with_unreachable_state(self):
        """Test protocol with unreachable state."""
        protocol = Protocol(
            states=["A", "B", "C"],
            start="A",
            transitions=[
                Transition(from_state="A", on_event="e1", to_state="B", guard=None),
                # C is unreachable
            ],
        )

        # Validate
        validator = FSMValidator(protocol)
        report = validator.validate()

        # Should have MEDIUM severity unreachable state warning
        assert report.medium_count >= 1
        assert "C" in str(report.deviations)

    def test_protocol_with_undefined_guard(self):
        """Test protocol with undefined guard function."""
        protocol = Protocol(
            states=["A", "B"],
            start="A",
            transitions=[
                Transition(from_state="A", on_event="go", to_state="B", guard="undefined_guard"),
            ],
        )

        # Validate without providing guard functions
        validator = FSMValidator(protocol)
        report = validator.validate()

        # Should have LOW severity undefined guard warning
        assert report.low_count >= 1
        assert "undefined_guard" in str(report.deviations)

    def test_protocol_with_defined_guards(self):
        """Test protocol with defined guard functions."""
        protocol = Protocol(
            states=["A", "B"],
            start="A",
            transitions=[
                Transition(from_state="A", on_event="go", to_state="B", guard="is_valid"),
            ],
            guards={"is_valid": "return True"},
        )

        # Validate with guard functions
        def is_valid() -> bool:
            return True

        validator = FSMValidator(protocol, guard_functions={"is_valid": is_valid})
        report = validator.validate()

        # Should pass
        assert report.high_count == 0
        assert report.low_count == 0

    def test_protocol_without_guards_dict(self):
        """Test protocol without guards dictionary."""
        protocol = Protocol(
            states=["A", "B"],
            start="A",
            transitions=[
                Transition(from_state="A", on_event="go", to_state="B", guard=None),
            ],
        )

        # guards should default to empty dict
        assert protocol.guards == {}

        # Should validate successfully
        validator = FSMValidator(protocol)
        report = validator.validate()
        assert report.high_count == 0

"""
Unit tests for FSM validator.

Focus: Business logic and edge cases only (@beartype handles type validation).
"""

from specfact_cli.models.deviation import DeviationType
from specfact_cli.models.protocol import Protocol, Transition
from specfact_cli.validators.fsm import FSMValidator


class TestFSMValidator:
    """Tests for FSMValidator."""

    def test_valid_protocol(self):
        """Test validation of a valid protocol."""
        protocol = Protocol(
            states=["INIT", "RUNNING", "DONE"],
            start="INIT",
            transitions=[
                Transition(from_state="INIT", on_event="start", to_state="RUNNING", guard=None),
                Transition(from_state="RUNNING", on_event="complete", to_state="DONE", guard=None),
            ],
        )

        validator = FSMValidator(protocol=protocol)
        report = validator.validate()

        assert report.passed is True
        assert len(report.deviations) == 0

    def test_invalid_start_state(self):
        """Test protocol with invalid start state."""
        protocol = Protocol(
            states=["INIT", "RUNNING"],
            start="INVALID",
            transitions=[],  # Start state not in states list
        )

        validator = FSMValidator(protocol=protocol)
        report = validator.validate()

        assert report.passed is False
        assert report.high_count > 0
        assert any(d.type == DeviationType.FSM_MISMATCH for d in report.deviations)

    def test_invalid_transition_states(self):
        """Test protocol with transitions referencing unknown states."""
        protocol = Protocol(
            states=["INIT", "RUNNING"],
            start="INIT",
            transitions=[
                Transition(from_state="INIT", on_event="start", to_state="UNKNOWN", guard=None),  # Unknown to_state
            ],
        )

        validator = FSMValidator(protocol=protocol)
        report = validator.validate()

        assert report.passed is False
        assert any("unknown state" in d.description.lower() for d in report.deviations)

    def test_unreachable_states(self):
        """Test detection of unreachable states."""
        protocol = Protocol(
            states=["INIT", "RUNNING", "ISOLATED"],
            start="INIT",
            transitions=[
                Transition(from_state="INIT", on_event="start", to_state="RUNNING", guard=None),
                # ISOLATED state is not reachable
            ],
        )

        validator = FSMValidator(protocol=protocol)
        report = validator.validate()

        # Unreachable states are MEDIUM severity
        assert report.medium_count > 0
        assert any("not reachable" in d.description.lower() for d in report.deviations)

    def test_undefined_guard(self):
        """Test detection of undefined guards."""
        protocol = Protocol(
            states=["INIT", "RUNNING"],
            start="INIT",
            transitions=[
                Transition(from_state="INIT", on_event="start", to_state="RUNNING", guard="undefined_guard"),
            ],
            guards={},  # Guard not defined
        )

        validator = FSMValidator(protocol=protocol)
        report = validator.validate()

        # Undefined guards are LOW severity, so report should still pass
        assert report.passed is True
        assert report.low_count >= 1
        assert any(
            "guard" in d.description.lower() and "not defined" in d.description.lower() for d in report.deviations
        )

    def test_cycle_detection(self):
        """Test detection of cycles (informational)."""
        protocol = Protocol(
            states=["A", "B", "C"],
            start="A",
            transitions=[
                Transition(from_state="A", on_event="next", to_state="B", guard=None),
                Transition(from_state="B", on_event="next", to_state="C", guard=None),
                Transition(from_state="C", on_event="next", to_state="A", guard=None),  # Cycle back to A
            ],
        )

        validator = FSMValidator(protocol=protocol)
        report = validator.validate()

        # Cycles are LOW severity (informational)
        assert report.low_count > 0
        assert any("cycle" in d.description.lower() for d in report.deviations)

    def test_get_reachable_states(self):
        """Test get_reachable_states method."""
        protocol = Protocol(
            states=["INIT", "RUNNING", "DONE"],
            start="INIT",
            transitions=[
                Transition(from_state="INIT", on_event="start", to_state="RUNNING", guard=None),
                Transition(from_state="RUNNING", on_event="complete", to_state="DONE", guard=None),
            ],
        )

        validator = FSMValidator(protocol=protocol)
        reachable = validator.get_reachable_states("INIT")

        assert "INIT" in reachable
        assert "RUNNING" in reachable
        assert "DONE" in reachable

    def test_get_transitions_from(self):
        """Test get_transitions_from method."""
        protocol = Protocol(
            states=["INIT", "RUNNING", "DONE"],
            start="INIT",
            transitions=[
                Transition(from_state="INIT", on_event="start", to_state="RUNNING", guard=None),
                Transition(from_state="INIT", on_event="cancel", to_state="DONE", guard=None),
            ],
        )

        validator = FSMValidator(protocol=protocol)
        transitions = validator.get_transitions_from("INIT")

        assert len(transitions) == 2
        assert any(t["to_state"] == "RUNNING" for t in transitions)
        assert any(t["to_state"] == "DONE" for t in transitions)

    def test_is_valid_transition(self):
        """Test is_valid_transition method."""
        protocol = Protocol(
            states=["INIT", "RUNNING", "DONE"],
            start="INIT",
            transitions=[
                Transition(from_state="INIT", on_event="start", to_state="RUNNING", guard=None),
            ],
        )

        validator = FSMValidator(protocol=protocol)

        assert validator.is_valid_transition("INIT", "start", "RUNNING") is True
        assert validator.is_valid_transition("INIT", "invalid", "RUNNING") is False
        assert validator.is_valid_transition("INIT", "start", "DONE") is False
        assert validator.is_valid_transition("RUNNING", "complete", "DONE") is False

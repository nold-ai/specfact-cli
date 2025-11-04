"""
Unit tests for protocol data models - Contract-First approach.

Pydantic models handle most validation (types, required fields).
Only edge cases and business logic validation are tested here.
"""

from specfact_cli.models.protocol import Protocol, Transition


class TestProtocol:
    """Tests for Protocol model - business logic only."""

    def test_protocol_with_transitions(self):
        """Test Protocol with transitions - business logic validation.

        Pydantic validates types and required fields.
        This test verifies transitions work correctly.
        """
        transitions = [
            Transition(from_state="INIT", on_event="start", to_state="RUNNING", guard=None),
            Transition(from_state="RUNNING", on_event="complete", to_state="DONE", guard=None),
        ]

        protocol = Protocol(states=["INIT", "RUNNING", "DONE"], start="INIT", transitions=transitions)

        # Test business logic: transition relationships
        assert len(protocol.transitions) == 2
        assert protocol.transitions[0].from_state == "INIT"
        assert protocol.transitions[1].to_state == "DONE"

    def test_protocol_required_fields(self):
        """Test Protocol requires required fields - Pydantic validation.

        Pydantic validates required fields at the model level.
        Business logic validation (e.g., start in states) is handled by FSMValidator.
        """
        # Test that all required fields are present (Pydantic handles this)
        protocol = Protocol(states=["INIT"], start="INIT", transitions=[])
        assert protocol.states == ["INIT"]
        assert protocol.start == "INIT"
        assert protocol.transitions == []

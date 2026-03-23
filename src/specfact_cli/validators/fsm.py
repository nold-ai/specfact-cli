"""
FSM (Finite State Machine) validation module.

This module provides validators for state machine protocols and transitions.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import networkx as nx
from beartype import beartype
from icontract import ensure, require

from specfact_cli.models.deviation import Deviation, DeviationSeverity, DeviationType, ValidationReport
from specfact_cli.models.protocol import Protocol
from specfact_cli.utils.structured_io import load_structured_file


class FSMValidator:
    """FSM validator for protocol validation."""

    @beartype
    @require(
        lambda protocol, protocol_path: protocol is not None or protocol_path is not None,
        "Either protocol or protocol_path must be provided",
    )
    @require(
        lambda protocol_path: protocol_path is None or (isinstance(protocol_path, Path) and protocol_path.exists()),
        "Protocol path must exist if provided",
    )
    def __init__(
        self,
        protocol: Protocol | None = None,
        protocol_path: Path | None = None,
        guard_functions: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize FSM validator.

        Args:
            protocol: Protocol model to validate
            protocol_path: Path to protocol YAML file (must exist if provided)
            guard_functions: Optional dict of guard function implementations

        Raises:
            ValueError: If neither protocol nor protocol_path is provided
        """

        if protocol is None:
            # Load protocol from file
            data = load_structured_file(protocol_path)  # type: ignore[arg-type]
            self.protocol = Protocol(**data)
        else:
            self.protocol = protocol

        self.guard_functions: dict[str, Any] = guard_functions if guard_functions is not None else {}
        self.graph: nx.DiGraph[str] = self._build_graph()

    def _build_graph(self) -> nx.DiGraph[str]:
        """
        Build directed graph from protocol transitions.

        Returns:
            NetworkX directed graph
        """
        graph: nx.DiGraph[str] = nx.DiGraph()

        # Add all states as nodes
        for state in self.protocol.states:
            graph.add_node(state)

        # Add transitions as edges
        for transition in self.protocol.transitions:
            graph.add_edge(
                transition.from_state,
                transition.to_state,
                event=transition.on_event,
                guard=transition.guard,
            )

        return graph

    def _fsm_check_start_state(self, report: ValidationReport) -> None:
        if self.protocol.start not in self.protocol.states:
            report.add_deviation(
                Deviation(
                    type=DeviationType.FSM_MISMATCH,
                    severity=DeviationSeverity.HIGH,
                    description=f"Start state '{self.protocol.start}' not in states list",
                    location="protocol.start",
                    fix_hint=f"Add '{self.protocol.start}' to states list",
                )
            )

    def _fsm_check_transition_states(self, report: ValidationReport) -> None:
        for transition in self.protocol.transitions:
            if transition.from_state not in self.protocol.states:
                report.add_deviation(
                    Deviation(
                        type=DeviationType.FSM_MISMATCH,
                        severity=DeviationSeverity.HIGH,
                        description=f"Transition from unknown state: '{transition.from_state}'",
                        location=f"transition[{transition.from_state} → {transition.to_state}]",
                        fix_hint=f"Add '{transition.from_state}' to states list",
                    )
                )
            if transition.to_state not in self.protocol.states:
                report.add_deviation(
                    Deviation(
                        type=DeviationType.FSM_MISMATCH,
                        severity=DeviationSeverity.HIGH,
                        description=f"Transition to unknown state: '{transition.to_state}'",
                        location=f"transition[{transition.from_state} → {transition.to_state}]",
                        fix_hint=f"Add '{transition.to_state}' to states list",
                    )
                )

    def _fsm_check_reachability(self, report: ValidationReport) -> None:
        if not report.passed:
            return
        reachable = cast(set[str], nx.descendants(self.graph, self.protocol.start))  # pyright: ignore[reportUnknownMemberType]
        reachable.add(self.protocol.start)
        for state in set(self.protocol.states) - reachable:
            report.add_deviation(
                Deviation(
                    type=DeviationType.FSM_MISMATCH,
                    severity=DeviationSeverity.MEDIUM,
                    description=f"State '{state}' is not reachable from start state",
                    location=f"state[{state}]",
                    fix_hint=f"Add transition path from '{self.protocol.start}' to '{state}'",
                )
            )

    def _fsm_check_guards(self, report: ValidationReport) -> None:
        for transition in self.protocol.transitions:
            if not transition.guard:
                continue
            if transition.guard in self.protocol.guards or transition.guard in self.guard_functions:
                continue
            report.add_deviation(
                Deviation(
                    type=DeviationType.FSM_MISMATCH,
                    severity=DeviationSeverity.LOW,
                    description=f"Guard '{transition.guard}' not defined in protocol or guard_functions",
                    location=f"transition[{transition.from_state} → {transition.to_state}]",
                    fix_hint=f"Add guard definition for '{transition.guard}' in protocol.guards or pass guard_functions",
                )
            )

    def _fsm_check_cycles(self, report: ValidationReport) -> None:
        try:
            cycles = list(nx.simple_cycles(self.graph))
        except nx.NetworkXNoCycle:
            return
        for cycle in cycles:
            report.add_deviation(
                Deviation(
                    type=DeviationType.FSM_MISMATCH,
                    severity=DeviationSeverity.LOW,
                    description=f"Cycle detected: {' → '.join(cycle)}",
                    location="protocol.transitions",
                    fix_hint="Cycles may be intentional for workflows, verify this is expected",
                )
            )

    @beartype
    @ensure(lambda result: isinstance(result, ValidationReport), "Must return ValidationReport")
    def validate(self) -> ValidationReport:
        """
        Validate the FSM protocol.

        Returns:
            Validation report with any deviations found
        """
        report = ValidationReport()
        self._fsm_check_start_state(report)
        self._fsm_check_transition_states(report)
        self._fsm_check_reachability(report)
        self._fsm_check_guards(report)
        self._fsm_check_cycles(report)
        return report

    @beartype
    @require(lambda from_state: isinstance(from_state, str) and len(from_state) > 0, "State must be non-empty string")
    @ensure(lambda result: isinstance(result, set), "Must return set")
    @ensure(lambda result: all(isinstance(s, str) for s in result), "All items must be strings")
    def get_reachable_states(self, from_state: str) -> set[str]:
        """
        Get all states reachable from given state.

        Args:
            from_state: Starting state

        Returns:
            Set of reachable state names
        """
        if from_state not in self.protocol.states:
            return set()

        reachable = cast(set[str], nx.descendants(self.graph, from_state))  # pyright: ignore[reportUnknownMemberType]
        reachable.add(from_state)
        return reachable

    @beartype
    @require(lambda state: isinstance(state, str) and len(state) > 0, "State must be non-empty string")
    @ensure(lambda result: isinstance(result, list), "Must return list")
    @ensure(lambda result: all(isinstance(t, dict) for t in result), "All items must be dictionaries")
    def get_transitions_from(self, state: str) -> list[dict[str, Any]]:
        """
        Get all transitions from given state.

        Args:
            state: State name

        Returns:
            List of transition dictionaries
        """
        if state not in self.protocol.states:
            return []

        transitions: list[dict[str, Any]] = []
        for successor in self.graph.successors(state):
            edge_data = self.graph.get_edge_data(state, successor) or {}
            transitions.append(
                {
                    "from_state": state,
                    "to_state": successor,
                    "event": edge_data.get("event"),
                    "guard": edge_data.get("guard"),
                }
            )

        return transitions

    @beartype
    @require(
        lambda from_state: isinstance(from_state, str) and len(from_state) > 0, "From state must be non-empty string"
    )
    @require(lambda on_event: isinstance(on_event, str) and len(on_event) > 0, "Event must be non-empty string")
    @require(lambda to_state: isinstance(to_state, str) and len(to_state) > 0, "To state must be non-empty string")
    @ensure(lambda result: isinstance(result, bool), "Must return boolean")
    def is_valid_transition(self, from_state: str, on_event: str, to_state: str) -> bool:
        """
        Check if transition is valid.

        Args:
            from_state: Source state
            on_event: Event that triggers the transition
            to_state: Target state

        Returns:
            True if transition exists with the given event
        """
        # Check if edge exists
        if not self.graph.has_edge(from_state, to_state):
            return False

        # Check if the event matches
        edge_data = self.graph.get_edge_data(from_state, to_state) or {}
        return edge_data.get("event") == on_event

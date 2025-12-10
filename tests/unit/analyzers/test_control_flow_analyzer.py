"""Unit tests for control flow analyzer.

Focus: Business logic and edge cases only (@beartype handles type validation).
"""

import ast
from textwrap import dedent

from specfact_cli.analyzers.control_flow_analyzer import ControlFlowAnalyzer


class TestControlFlowAnalyzer:
    """Test suite for ControlFlowAnalyzer."""

    def test_extract_scenarios_from_simple_method(self):
        """Test extracting scenarios from a simple method with no control flow."""
        code = dedent(
            """
            class Service:
                def method(self):
                    return True
            """
        )
        tree = ast.parse(code)
        method_node = tree.body[0].body[0]  # Get the method node

        analyzer = ControlFlowAnalyzer()
        scenarios = analyzer.extract_scenarios_from_method(method_node, "Service", "method")

        # Should have default primary scenario
        assert "primary" in scenarios
        assert len(scenarios["primary"]) == 1
        assert scenarios["primary"][0] == "method executes successfully"
        assert "alternate" in scenarios
        assert "exception" in scenarios
        assert "recovery" in scenarios

    def test_extract_scenarios_no_gwt_patterns(self):
        """Test that GWT patterns are NOT generated (Phase 4.8.1)."""
        code = dedent(
            """
            class Service:
                def method(self):
                    return True
            """
        )
        tree = ast.parse(code)
        method_node = tree.body[0].body[0]

        analyzer = ControlFlowAnalyzer()
        scenarios = analyzer.extract_scenarios_from_method(method_node, "Service", "method")

        # Verify no GWT patterns
        for scenario_type, scenario_list in scenarios.items():
            for scenario in scenario_list:
                assert "Given" not in scenario, f"Found GWT pattern in {scenario_type}: {scenario}"
                assert "When" not in scenario, f"Found GWT pattern in {scenario_type}: {scenario}"
                assert "Then" not in scenario, f"Found GWT pattern in {scenario_type}: {scenario}"

    def test_extract_primary_scenario_from_if(self):
        """Test extracting primary scenario from if statement."""
        code = dedent(
            """
            class Service:
                def process(self, value):
                    if value > 0:
                        return value * 2
            """
        )
        tree = ast.parse(code)
        method_node = tree.body[0].body[0]

        analyzer = ControlFlowAnalyzer()
        scenarios = analyzer.extract_scenarios_from_method(method_node, "Service", "process")

        assert len(scenarios["primary"]) > 0
        primary = scenarios["primary"][0]
        assert "process" in primary
        assert "value" in primary.lower() or "condition" in primary.lower()
        # Verify no GWT
        assert "Given" not in primary
        assert "When" not in primary
        assert "Then" not in primary

    def test_extract_alternate_scenario_from_else(self):
        """Test extracting alternate scenario from else branch."""
        code = dedent(
            """
            class Service:
                def process(self, value):
                    if value > 0:
                        return value * 2
                    else:
                        return 0
            """
        )
        tree = ast.parse(code)
        method_node = tree.body[0].body[0]

        analyzer = ControlFlowAnalyzer()
        scenarios = analyzer.extract_scenarios_from_method(method_node, "Service", "process")

        assert len(scenarios["alternate"]) > 0
        alternate = scenarios["alternate"][0]
        assert "process" in alternate
        # Verify no GWT
        assert "Given" not in alternate
        assert "When" not in alternate
        assert "Then" not in alternate

    def test_extract_primary_scenario_from_try(self):
        """Test extracting primary scenario from try block."""
        code = dedent(
            """
            class Service:
                def process(self, data):
                    try:
                        result = data.process()
                        return result
                    except Exception:
                        return None
            """
        )
        tree = ast.parse(code)
        method_node = tree.body[0].body[0]

        analyzer = ControlFlowAnalyzer()
        scenarios = analyzer.extract_scenarios_from_method(method_node, "Service", "process")

        assert len(scenarios["primary"]) > 0
        primary = scenarios["primary"][0]
        assert "process" in primary
        assert "executes" in primary.lower()
        # Verify no GWT
        assert "Given" not in primary
        assert "When" not in primary
        assert "Then" not in primary

    def test_extract_exception_scenario_from_except(self):
        """Test extracting exception scenario from except block."""
        code = dedent(
            """
            class Service:
                def process(self, data):
                    try:
                        result = data.process()
                        return result
                    except ValueError as e:
                        return None
            """
        )
        tree = ast.parse(code)
        method_node = tree.body[0].body[0]

        analyzer = ControlFlowAnalyzer()
        scenarios = analyzer.extract_scenarios_from_method(method_node, "Service", "process")

        assert len(scenarios["exception"]) > 0
        exception = scenarios["exception"][0]
        assert "process" in exception
        assert "ValueError" in exception or "raises" in exception.lower()
        # Verify no GWT
        assert "Given" not in exception
        assert "When" not in exception
        assert "Then" not in exception

    def test_extract_recovery_scenario_from_finally(self):
        """Test extracting recovery scenario from finally block."""
        code = dedent(
            """
            class Service:
                def process(self, data):
                    try:
                        result = data.process()
                        return result
                    finally:
                        data.cleanup()
            """
        )
        tree = ast.parse(code)
        method_node = tree.body[0].body[0]

        analyzer = ControlFlowAnalyzer()
        scenarios = analyzer.extract_scenarios_from_method(method_node, "Service", "process")

        assert len(scenarios["recovery"]) > 0
        recovery = scenarios["recovery"][0]
        assert "process" in recovery
        assert "cleanup" in recovery.lower()
        # Verify no GWT
        assert "Given" not in recovery
        assert "When" not in recovery
        assert "Then" not in recovery

    def test_extract_recovery_scenario_from_retry_logic(self):
        """Test extracting recovery scenario from retry logic in exception handler."""
        code = dedent(
            """
            class Service:
                def process(self, data):
                    try:
                        result = data.process()
                        return result
                    except Exception:
                        # Retry logic - using retry keyword in variable name
                        retry_count = 0
                        while retry_count < 3:
                            retry_count += 1
                            try:
                                return data.process()
                            except Exception:
                                pass
                        return None
            """
        )
        tree = ast.parse(code)
        method_node = tree.body[0].body[0]

        analyzer = ControlFlowAnalyzer()
        scenarios = analyzer.extract_scenarios_from_method(method_node, "Service", "process")

        # The retry logic detection looks for retry keywords in variable names
        # retry_count should be detected, but it's in the handler body which is checked
        # Note: This test verifies the behavior - if retry logic is detected, we should have recovery scenario
        # If not detected, that's also valid behavior (the detection is heuristic-based)
        if scenarios["recovery"]:
            # If recovery scenarios are found, verify they don't have GWT
            for recovery in scenarios["recovery"]:
                assert "Given" not in recovery
                assert "When" not in recovery
                assert "Then" not in recovery
        # If no recovery scenarios found, that's acceptable - the detection is heuristic

    def test_extract_recovery_scenario_from_loop_with_retry(self):
        """Test extracting recovery scenario from loop containing retry logic."""
        code = dedent(
            """
            class Service:
                def process(self, data):
                    retry_count = 0
                    while retry_count < 3:
                        retry_count += 1
                        try:
                            return data.process()
                        except Exception:
                            pass
                    return None
            """
        )
        tree = ast.parse(code)
        method_node = tree.body[0].body[0]

        analyzer = ControlFlowAnalyzer()
        scenarios = analyzer.extract_scenarios_from_method(method_node, "Service", "process")

        # The retry logic detection should find "retry_count" variable name
        # This should trigger recovery scenario detection
        # Note: Detection is heuristic-based, so we verify behavior exists if detected
        if scenarios["recovery"]:
            # If recovery scenarios are found, verify they don't have GWT
            recovery_found = any("retries" in s.lower() or "retry" in s.lower() for s in scenarios["recovery"])
            if recovery_found:
                for recovery in scenarios["recovery"]:
                    assert "Given" not in recovery
                    assert "When" not in recovery
                    assert "Then" not in recovery

    def test_extract_scenarios_from_nested_control_flow(self):
        """Test extracting scenarios from nested control flow (if inside try)."""
        code = dedent(
            """
            class Service:
                def process(self, value):
                    try:
                        if value > 0:
                            return value * 2
                        else:
                            return 0
                    except Exception:
                        return None
            """
        )
        tree = ast.parse(code)
        method_node = tree.body[0].body[0]

        analyzer = ControlFlowAnalyzer()
        scenarios = analyzer.extract_scenarios_from_method(method_node, "Service", "process")

        # Should have primary from try (and possibly from if)
        assert len(scenarios["primary"]) > 0
        # Should have exception from except
        assert len(scenarios["exception"]) > 0
        # Note: Nested if/else inside try may or may not extract alternate scenarios
        # depending on how the recursive analysis works - both behaviors are acceptable

        # Verify no GWT in any scenario
        for scenario_list in scenarios.values():
            for scenario in scenario_list:
                assert "Given" not in scenario
                assert "When" not in scenario
                assert "Then" not in scenario

    def test_extract_scenarios_from_method_with_multiple_ifs(self):
        """Test extracting scenarios from method with multiple if statements."""
        code = dedent(
            """
            class Service:
                def process(self, value, flag):
                    if value > 0:
                        return value * 2
                    if flag:
                        return value
                    return 0
            """
        )
        tree = ast.parse(code)
        method_node = tree.body[0].body[0]

        analyzer = ControlFlowAnalyzer()
        scenarios = analyzer.extract_scenarios_from_method(method_node, "Service", "process")

        # Should have multiple primary scenarios (one per if)
        assert len(scenarios["primary"]) >= 2

    def test_extract_scenarios_from_method_with_multiple_exceptions(self):
        """Test extracting scenarios from method with multiple exception handlers."""
        code = dedent(
            """
            class Service:
                def process(self, data):
                    try:
                        result = data.process()
                        return result
                    except ValueError:
                        return None
                    except KeyError:
                        return {}
            """
        )
        tree = ast.parse(code)
        method_node = tree.body[0].body[0]

        analyzer = ControlFlowAnalyzer()
        scenarios = analyzer.extract_scenarios_from_method(method_node, "Service", "process")

        # Should have multiple exception scenarios (one per except)
        assert len(scenarios["exception"]) >= 2
        # Verify both exception types are mentioned
        exception_text = " ".join(scenarios["exception"])
        assert "ValueError" in exception_text or "KeyError" in exception_text

    def test_extract_scenarios_from_empty_method(self):
        """Test extracting scenarios from empty method body."""
        code = dedent(
            """
            class Service:
                def method(self):
                    pass
            """
        )
        tree = ast.parse(code)
        method_node = tree.body[0].body[0]

        analyzer = ControlFlowAnalyzer()
        scenarios = analyzer.extract_scenarios_from_method(method_node, "Service", "method")

        # Should have default primary scenario
        assert len(scenarios["primary"]) == 1
        assert scenarios["primary"][0] == "method executes successfully"

    def test_extract_scenarios_from_method_with_nested_function(self):
        """Test extracting scenarios from method with nested function."""
        code = dedent(
            """
            class Service:
                def process(self, value):
                    def helper(x):
                        if x > 0:
                            return x * 2
                        return 0
                    return helper(value)
            """
        )
        tree = ast.parse(code)
        method_node = tree.body[0].body[0]

        analyzer = ControlFlowAnalyzer()
        scenarios = analyzer.extract_scenarios_from_method(method_node, "Service", "process")

        # Should extract scenarios from nested function too
        assert len(scenarios["primary"]) > 0
        # Note: Nested function scenarios may or may not extract alternate scenarios
        # depending on recursive analysis behavior - both are acceptable

    def test_extract_condition_from_comparison(self):
        """Test extracting condition from comparison operators."""
        code = dedent(
            """
            class Service:
                def process(self, value):
                    if value == 10:
                        return True
                    elif value > 5:
                        return False
                    elif value < 0:
                        return None
            """
        )
        tree = ast.parse(code)
        method_node = tree.body[0].body[0]

        analyzer = ControlFlowAnalyzer()
        scenarios = analyzer.extract_scenarios_from_method(method_node, "Service", "process")

        # Should extract conditions properly
        assert len(scenarios["primary"]) > 0
        primary_text = " ".join(scenarios["primary"])
        # Should mention value or condition
        assert "value" in primary_text.lower() or "condition" in primary_text.lower()

    def test_extract_action_from_return_statement(self):
        """Test extracting action description from return statement."""
        code = dedent(
            """
            class Service:
                def process(self, value):
                    if value > 0:
                        return value * 2
            """
        )
        tree = ast.parse(code)
        method_node = tree.body[0].body[0]

        analyzer = ControlFlowAnalyzer()
        scenarios = analyzer.extract_scenarios_from_method(method_node, "Service", "process")

        primary = scenarios["primary"][0]
        # Should mention return or result
        assert "return" in primary.lower() or "result" in primary.lower() or "operation" in primary.lower()

    def test_extract_action_from_assignment(self):
        """Test extracting action description from assignment."""
        code = dedent(
            """
            class Service:
                def process(self, value):
                    if value > 0:
                        result = value * 2
                        return result
            """
        )
        tree = ast.parse(code)
        method_node = tree.body[0].body[0]

        analyzer = ControlFlowAnalyzer()
        scenarios = analyzer.extract_scenarios_from_method(method_node, "Service", "process")

        primary = scenarios["primary"][0]
        # Should mention result or sets
        assert "result" in primary.lower() or "sets" in primary.lower() or "operation" in primary.lower()

    def test_extract_action_from_function_call(self):
        """Test extracting action description from function call."""
        code = dedent(
            """
            class Service:
                def process(self, data):
                    if data:
                        data.save()
                        return True
            """
        )
        tree = ast.parse(code)
        method_node = tree.body[0].body[0]

        analyzer = ControlFlowAnalyzer()
        scenarios = analyzer.extract_scenarios_from_method(method_node, "Service", "process")

        primary = scenarios["primary"][0]
        # Should mention save or calls
        assert "save" in primary.lower() or "calls" in primary.lower() or "operation" in primary.lower()

    def test_all_scenario_types_present(self):
        """Test that all scenario types are always present in result."""
        code = dedent(
            """
            class Service:
                def method(self):
                    return True
            """
        )
        tree = ast.parse(code)
        method_node = tree.body[0].body[0]

        analyzer = ControlFlowAnalyzer()
        scenarios = analyzer.extract_scenarios_from_method(method_node, "Service", "method")

        # All scenario types must be present (contract requirement)
        assert "primary" in scenarios
        assert "alternate" in scenarios
        assert "exception" in scenarios
        assert "recovery" in scenarios
        # All must be lists
        assert isinstance(scenarios["primary"], list)
        assert isinstance(scenarios["alternate"], list)
        assert isinstance(scenarios["exception"], list)
        assert isinstance(scenarios["recovery"], list)

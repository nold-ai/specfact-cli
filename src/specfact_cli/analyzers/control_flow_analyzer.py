"""Control flow analyzer for extracting scenarios from code AST.

Extracts Primary, Alternate, Exception, and Recovery scenarios from code control flow
patterns (if/else, try/except, loops, retry logic).
"""

from __future__ import annotations

import ast
from collections.abc import Sequence

from beartype import beartype
from icontract import ensure, require


class ControlFlowAnalyzer:
    """
    Analyzes AST to extract control flow patterns and generate scenarios.

    Extracts scenarios from:
    - if/else branches → Alternate scenarios
    - try/except blocks → Exception and Recovery scenarios
    - Happy paths → Primary scenarios
    - Retry logic → Recovery scenarios
    """

    @beartype
    def __init__(self) -> None:
        """Initialize control flow analyzer."""
        self.scenarios: dict[str, list[str]] = {
            "primary": [],
            "alternate": [],
            "exception": [],
            "recovery": [],
        }

    @beartype
    @require(lambda method_node: isinstance(method_node, ast.FunctionDef), "Method must be FunctionDef node")
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    @ensure(
        lambda result: "primary" in result and "alternate" in result and "exception" in result and "recovery" in result,
        "Must have all scenario types",
    )
    def extract_scenarios_from_method(
        self, method_node: ast.FunctionDef, class_name: str, method_name: str
    ) -> dict[str, list[str]]:
        """
        Extract scenarios from a method's control flow.

        Args:
            method_node: AST node for the method
            class_name: Name of the class containing the method
            method_name: Name of the method

        Returns:
            Dictionary with scenario types as keys and lists of Given/When/Then scenarios as values
        """
        scenarios: dict[str, list[str]] = {
            "primary": [],
            "alternate": [],
            "exception": [],
            "recovery": [],
        }

        # Analyze method body for control flow
        self._analyze_node(method_node.body, scenarios, class_name, method_name)

        # If no scenarios found, generate default primary scenario
        if not any(scenarios.values()):
            scenarios["primary"].append(
                f"Given {class_name} instance, When {method_name} is called, Then method executes successfully"
            )

        return scenarios

    @beartype
    def _analyze_node(
        self, nodes: Sequence[ast.AST], scenarios: dict[str, list[str]], class_name: str, method_name: str
    ) -> None:
        """Recursively analyze AST nodes for control flow patterns."""
        for node in nodes:
            if isinstance(node, ast.If):
                # if/else → Alternate scenario
                self._extract_if_scenario(node, scenarios, class_name, method_name)
            elif isinstance(node, ast.Try):
                # try/except → Exception and Recovery scenarios
                self._extract_try_scenario(node, scenarios, class_name, method_name)
            elif isinstance(node, (ast.For, ast.While)):
                # Loops might contain retry logic → Recovery scenario
                self._extract_loop_scenario(node, scenarios, class_name, method_name)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Recursively analyze nested functions
                self._analyze_node(node.body, scenarios, class_name, method_name)

    @beartype
    def _extract_if_scenario(
        self, if_node: ast.If, scenarios: dict[str, list[str]], class_name: str, method_name: str
    ) -> None:
        """Extract scenario from if/else statement."""
        # Extract condition
        condition = self._extract_condition(if_node.test)

        # Primary scenario: if branch (happy path)
        if if_node.body:
            primary_action = self._extract_action_from_body(if_node.body)
            scenarios["primary"].append(
                f"Given {class_name} instance, When {method_name} is called with {condition}, Then {primary_action}"
            )

        # Alternate scenario: else branch
        if if_node.orelse:
            alternate_action = self._extract_action_from_body(if_node.orelse)
            scenarios["alternate"].append(
                f"Given {class_name} instance, When {method_name} is called with {self._negate_condition(condition)}, Then {alternate_action}"
            )

    @beartype
    def _extract_try_scenario(
        self, try_node: ast.Try, scenarios: dict[str, list[str]], class_name: str, method_name: str
    ) -> None:
        """Extract scenarios from try/except block."""
        # Primary scenario: try block (happy path)
        if try_node.body:
            primary_action = self._extract_action_from_body(try_node.body)
            scenarios["primary"].append(
                f"Given {class_name} instance, When {method_name} is called, Then {primary_action}"
            )

        # Exception scenarios: except blocks
        for handler in try_node.handlers:
            exception_type = "Exception"
            if handler.type:
                exception_type = self._extract_exception_type(handler.type)

            exception_action = self._extract_action_from_body(handler.body) if handler.body else "error is handled"
            scenarios["exception"].append(
                f"Given {class_name} instance, When {method_name} is called and {exception_type} occurs, Then {exception_action}"
            )

            # Check for retry/recovery logic in exception handler
            if self._has_retry_logic(handler.body):
                scenarios["recovery"].append(
                    f"Given {class_name} instance, When {method_name} fails with {exception_type}, Then system retries and recovers"
                )

        # Recovery scenario: finally block or retry logic
        if try_node.finalbody:
            recovery_action = self._extract_action_from_body(try_node.finalbody)
            scenarios["recovery"].append(
                f"Given {class_name} instance, When {method_name} completes or fails, Then {recovery_action}"
            )

    @beartype
    def _extract_loop_scenario(
        self, loop_node: ast.For | ast.While, scenarios: dict[str, list[str]], class_name: str, method_name: str
    ) -> None:
        """Extract scenario from loop (might indicate retry logic)."""
        # Check if loop contains retry/retry logic
        if self._has_retry_logic(loop_node.body):
            scenarios["recovery"].append(
                f"Given {class_name} instance, When {method_name} is called, Then system retries on failure until success"
            )

    @beartype
    def _extract_condition(self, test_node: ast.AST) -> str:
        """Extract human-readable condition from AST node."""
        if isinstance(test_node, ast.Compare):
            left = self._extract_expression(test_node.left)
            ops = [op.__class__.__name__ for op in test_node.ops]
            comparators = [self._extract_expression(comp) for comp in test_node.comparators]

            op_map = {
                "Eq": "equals",
                "NotEq": "does not equal",
                "Lt": "is less than",
                "LtE": "is less than or equal to",
                "Gt": "is greater than",
                "GtE": "is greater than or equal to",
                "In": "is in",
                "NotIn": "is not in",
            }

            if ops and comparators:
                op_name = op_map.get(ops[0], "matches")
                return f"{left} {op_name} {comparators[0]}"

        elif isinstance(test_node, ast.Name):
            return f"{test_node.id} is true"

        elif isinstance(test_node, ast.Call):
            return f"{self._extract_expression(test_node.func)} is called"

        return "condition is met"

    @beartype
    def _extract_expression(self, node: ast.AST) -> str:
        """Extract human-readable expression from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return f"{self._extract_expression(node.value)}.{node.attr}"
        if isinstance(node, ast.Constant):
            return repr(node.value)
        if isinstance(node, ast.Call):
            func_name = self._extract_expression(node.func)
            return f"{func_name}()"

        return "value"

    @beartype
    def _negate_condition(self, condition: str) -> str:
        """Negate a condition for else branch."""
        if "equals" in condition:
            return condition.replace("equals", "does not equal")
        if "is true" in condition:
            return condition.replace("is true", "is false")
        if "is less than" in condition:
            return condition.replace("is less than", "is greater than or equal to")
        if "is greater than" in condition:
            return condition.replace("is greater than", "is less than or equal to")

        return f"not ({condition})"

    @beartype
    def _extract_action_from_body(self, body: Sequence[ast.AST]) -> str:
        """Extract action description from method body."""
        actions: list[str] = []

        for node in body[:3]:  # Limit to first 3 statements
            if isinstance(node, ast.Return):
                if node.value:
                    value = self._extract_expression(node.value)
                    actions.append(f"returns {value}")
                else:
                    actions.append("returns None")
            elif isinstance(node, ast.Assign):
                if node.targets:
                    target = self._extract_expression(node.targets[0])
                    if node.value:
                        value = self._extract_expression(node.value)
                        actions.append(f"sets {target} to {value}")
            elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                func_name = self._extract_expression(node.value.func)
                actions.append(f"calls {func_name}")

        return " and ".join(actions) if actions else "operation completes"

    @beartype
    def _extract_exception_type(self, type_node: ast.AST) -> str:
        """Extract exception type name from AST node."""
        if isinstance(type_node, ast.Name):
            return type_node.id
        if isinstance(type_node, ast.Tuple):
            # Multiple exception types
            types = [self._extract_exception_type(el) for el in type_node.elts]
            return " or ".join(types)

        return "Exception"

    @beartype
    def _has_retry_logic(self, body: Sequence[ast.AST] | None) -> bool:
        """Check if body contains retry logic patterns."""
        if not body:
            return False

        retry_keywords = ["retry", "retries", "again", "recover", "fallback"]
        # Walk through body nodes directly
        for node in body:
            for subnode in ast.walk(node):
                if isinstance(subnode, ast.Name) and subnode.id.lower() in retry_keywords:
                    return True
                if isinstance(subnode, ast.Attribute) and subnode.attr.lower() in retry_keywords:
                    return True
                if (
                    isinstance(subnode, ast.Constant)
                    and isinstance(subnode.value, str)
                    and any(keyword in subnode.value.lower() for keyword in retry_keywords)
                ):
                    return True

        return False

"""Test pattern extractor for generating testable acceptance criteria.

Extracts test patterns from existing test files (pytest, unittest) and converts
them to Given/When/Then format acceptance criteria.
"""

from __future__ import annotations

import ast
from pathlib import Path

from beartype import beartype
from icontract import ensure, require


class TestPatternExtractor:
    """
    Extracts test patterns from test files and converts them to acceptance criteria.

    Supports pytest and unittest test frameworks.
    """

    @beartype
    @require(lambda repo_path: repo_path is not None and isinstance(repo_path, Path), "Repo path must be Path")
    def __init__(self, repo_path: Path) -> None:
        """
        Initialize test pattern extractor.

        Args:
            repo_path: Path to repository root
        """
        self.repo_path = Path(repo_path)
        self.test_files: list[Path] = []
        self._discover_test_files()

    def _discover_test_files(self) -> None:
        """Discover all test files in the repository."""
        # Common test file patterns
        test_patterns = [
            "test_*.py",
            "*_test.py",
            "tests/**/test_*.py",
            "tests/**/*_test.py",
        ]

        for pattern in test_patterns:
            if "**" in pattern:
                # Recursive pattern
                base_pattern = pattern.split("**")[0].rstrip("/")
                suffix_pattern = pattern.split("**")[1].lstrip("/")
                if (self.repo_path / base_pattern).exists():
                    self.test_files.extend((self.repo_path / base_pattern).rglob(suffix_pattern))
            else:
                # Simple pattern
                self.test_files.extend(self.repo_path.glob(pattern))

        # Remove duplicates and filter out __pycache__
        self.test_files = [f for f in set(self.test_files) if "__pycache__" not in str(f) and f.is_file()]

    @beartype
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def extract_test_patterns_for_class(self, class_name: str, module_path: Path | None = None) -> list[str]:
        """
        Extract test patterns for a specific class.

        Args:
            class_name: Name of the class to find tests for
            module_path: Optional path to the source module (for better matching)

        Returns:
            List of testable acceptance criteria in Given/When/Then format
        """
        acceptance_criteria: list[str] = []

        for test_file in self.test_files:
            try:
                test_patterns = self._parse_test_file(test_file, class_name, module_path)
                acceptance_criteria.extend(test_patterns)
            except Exception:
                # Skip files that can't be parsed
                continue

        return acceptance_criteria

    @beartype
    def _parse_test_file(self, test_file: Path, class_name: str, module_path: Path | None) -> list[str]:
        """Parse a test file and extract test patterns for the given class."""
        try:
            content = test_file.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(test_file))
        except Exception:
            return []

        acceptance_criteria: list[str] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                # Found a test function
                test_pattern = self._extract_test_pattern(node, class_name)
                if test_pattern:
                    acceptance_criteria.append(test_pattern)

        return acceptance_criteria

    @beartype
    def _extract_test_pattern(self, test_node: ast.FunctionDef, class_name: str) -> str | None:
        """
        Extract test pattern from a test function and convert to Given/When/Then format.

        Args:
            test_node: AST node for the test function
            class_name: Name of the class being tested

        Returns:
            Testable acceptance criterion in Given/When/Then format, or None
        """
        # Extract test name (remove "test_" prefix)
        test_name = test_node.name.replace("test_", "").replace("_", " ")

        # Find assertions in the test
        assertions = self._find_assertions(test_node)

        if not assertions:
            return None

        # Extract Given/When/Then from test structure
        given = self._extract_given(test_node, class_name)
        when = self._extract_when(test_node, test_name)
        then = self._extract_then(assertions)

        if given and when and then:
            return f"Given {given}, When {when}, Then {then}"

        return None

    @beartype
    def _find_assertions(self, node: ast.FunctionDef) -> list[ast.AST]:
        """Find all assertion statements in a test function."""
        assertions: list[ast.AST] = []

        for child in ast.walk(node):
            if isinstance(child, ast.Assert):
                assertions.append(child)
            elif (
                isinstance(child, ast.Call)
                and isinstance(child.func, ast.Attribute)
                and child.func.attr.startswith("assert")
            ):
                # Check for pytest assertions (assert_equal, assert_true, etc.)
                assertions.append(child)

        return assertions

    @beartype
    def _extract_given(self, test_node: ast.FunctionDef, class_name: str) -> str:
        """Extract Given clause from test setup."""
        # Look for setup code (fixtures, mocks, initializations)
        given_parts: list[str] = []

        # Check for pytest fixtures
        for decorator in test_node.decorator_list:
            if (
                isinstance(decorator, ast.Call)
                and isinstance(decorator.func, ast.Name)
                and (decorator.func.id == "pytest.fixture" or decorator.func.id == "fixture")
            ):
                given_parts.append("test fixtures are available")

        # Default: assume class instance is available
        if not given_parts:
            given_parts.append(f"{class_name} instance is available")

        return " and ".join(given_parts) if given_parts else "system is initialized"

    @beartype
    def _extract_when(self, test_node: ast.FunctionDef, test_name: str) -> str:
        """Extract When clause from test action."""
        # Extract action from test name or function body
        action = test_name.replace("_", " ")

        # Try to find method calls in the test
        for node in ast.walk(test_node):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                method_name = node.func.attr
                if not method_name.startswith("assert") and not method_name.startswith("_"):
                    action = f"{method_name} is called"
                    break

        return action if action else "action is performed"

    @beartype
    def _extract_then(self, assertions: list[ast.AST]) -> str:
        """Extract Then clause from assertions."""
        if not assertions:
            return "expected result is achieved"

        # Extract expected outcomes from assertions
        outcomes: list[str] = []

        for assertion in assertions:
            if isinstance(assertion, ast.Assert):
                # Simple assert statement
                outcome = self._extract_assertion_outcome(assertion)
                if outcome:
                    outcomes.append(outcome)
            elif isinstance(assertion, ast.Call):
                # Pytest assertion (assert_equal, assert_true, etc.)
                outcome = self._extract_pytest_assertion_outcome(assertion)
                if outcome:
                    outcomes.append(outcome)

        return " and ".join(outcomes) if outcomes else "expected result is achieved"

    @beartype
    def _extract_assertion_outcome(self, assertion: ast.Assert) -> str | None:
        """Extract outcome from a simple assert statement."""
        if isinstance(assertion.test, ast.Compare):
            # Comparison assertion (==, !=, <, >, etc.)
            left = ast.unparse(assertion.test.left) if hasattr(ast, "unparse") else str(assertion.test.left)
            ops = [op.__class__.__name__ for op in assertion.test.ops]
            comparators = [
                ast.unparse(comp) if hasattr(ast, "unparse") else str(comp) for comp in assertion.test.comparators
            ]

            if ops and comparators:
                op_map = {
                    "Eq": "equals",
                    "NotEq": "does not equal",
                    "Lt": "is less than",
                    "LtE": "is less than or equal to",
                    "Gt": "is greater than",
                    "GtE": "is greater than or equal to",
                }
                op_name = op_map.get(ops[0], "matches")
                return f"{left} {op_name} {comparators[0]}"

        return None

    @beartype
    def _extract_pytest_assertion_outcome(self, call: ast.Call) -> str | None:
        """Extract outcome from a pytest assertion call."""
        if isinstance(call.func, ast.Attribute):
            attr_name = call.func.attr

            if attr_name == "assert_equal" and len(call.args) >= 2:
                return f"{ast.unparse(call.args[0]) if hasattr(ast, 'unparse') else str(call.args[0])} equals {ast.unparse(call.args[1]) if hasattr(ast, 'unparse') else str(call.args[1])}"
            if attr_name == "assert_true" and len(call.args) >= 1:
                return f"{ast.unparse(call.args[0]) if hasattr(ast, 'unparse') else str(call.args[0])} is true"
            if attr_name == "assert_false" and len(call.args) >= 1:
                return f"{ast.unparse(call.args[0]) if hasattr(ast, 'unparse') else str(call.args[0])} is false"
            if attr_name == "assert_in" and len(call.args) >= 2:
                return f"{ast.unparse(call.args[0]) if hasattr(ast, 'unparse') else str(call.args[0])} is in {ast.unparse(call.args[1]) if hasattr(ast, 'unparse') else str(call.args[1])}"

        return None

    @beartype
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def infer_from_code_patterns(self, method_node: ast.FunctionDef, class_name: str) -> list[str]:
        """
        Infer testable acceptance criteria from code patterns when tests are missing.

        Args:
            method_node: AST node for the method
            class_name: Name of the class containing the method

        Returns:
            List of testable acceptance criteria in Given/When/Then format
        """
        acceptance_criteria: list[str] = []

        # Extract method name and purpose
        method_name = method_node.name

        # Pattern 1: Validation logic → "Must verify [validation rule]"
        if any(keyword in method_name.lower() for keyword in ["validate", "check", "verify", "is_valid"]):
            validation_target = (
                method_name.replace("validate", "")
                .replace("check", "")
                .replace("verify", "")
                .replace("is_valid", "")
                .strip()
            )
            if validation_target:
                acceptance_criteria.append(
                    f"Given {class_name} instance, When {method_name} is called, Then {validation_target} is validated"
                )

        # Pattern 2: Error handling → "Must handle [error condition]"
        if any(keyword in method_name.lower() for keyword in ["handle", "catch", "error", "exception"]):
            error_type = method_name.replace("handle", "").replace("catch", "").strip()
            acceptance_criteria.append(
                f"Given error condition occurs, When {method_name} is called, Then {error_type or 'error'} is handled"
            )

        # Pattern 3: Success paths → "Must return [expected result]"
        # Check return type hints
        if method_node.returns:
            return_type = ast.unparse(method_node.returns) if hasattr(ast, "unparse") else str(method_node.returns)
            acceptance_criteria.append(
                f"Given {class_name} instance, When {method_name} is called, Then {return_type} is returned"
            )

        # Pattern 4: Type hints → "Must accept [type] and return [type]"
        if method_node.args.args:
            param_types: list[str] = []
            for arg in method_node.args.args:
                if arg.annotation:
                    param_type = ast.unparse(arg.annotation) if hasattr(ast, "unparse") else str(arg.annotation)
                    param_types.append(f"{arg.arg}: {param_type}")

            if param_types:
                params_str = ", ".join(param_types)
                return_type_str = (
                    ast.unparse(method_node.returns)
                    if method_node.returns and hasattr(ast, "unparse")
                    else str(method_node.returns)
                    if method_node.returns
                    else "result"
                )
                acceptance_criteria.append(
                    f"Given {class_name} instance with {params_str}, When {method_name} is called, Then {return_type_str} is returned"
                )

        # Default: Generic acceptance criterion
        if not acceptance_criteria:
            acceptance_criteria.append(
                f"Given {class_name} instance, When {method_name} is called, Then method executes successfully"
            )

        return acceptance_criteria

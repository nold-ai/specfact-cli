"""
Test pattern to OpenAPI example converter.

Extracts test patterns using Semgrep and converts them to OpenAPI examples
instead of verbose Given/When/Then acceptance criteria.
"""

from __future__ import annotations

import ast
import json
import os
import subprocess
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require


class OpenAPITestConverter:
    """
    Converts test patterns to OpenAPI examples using Semgrep.

    Extracts test fixtures, assertions, and request/response data from tests
    and converts them to OpenAPI examples stored in contract files.
    """

    def __init__(self, repo_path: Path, semgrep_config: Path | None = None) -> None:
        """
        Initialize converter with repository path.

        Args:
            repo_path: Path to repository root
            semgrep_config: Path to Semgrep test pattern config (default: tools/semgrep/test-patterns.yml)
        """
        self.repo_path = repo_path.resolve()
        if semgrep_config is None:
            semgrep_config = self.repo_path / "tools" / "semgrep" / "test-patterns.yml"
        self.semgrep_config = semgrep_config

    @beartype
    @require(lambda self, test_files: isinstance(test_files, list), "Test files must be list")
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def extract_examples_from_tests(self, test_files: list[str]) -> dict[str, Any]:
        """
        Extract OpenAPI examples from test files using Semgrep.

        Args:
            test_files: List of test file paths (format: 'test_file.py::test_func' or 'test_file.py')

        Returns:
            Dictionary mapping operation IDs to example data:
            {
                "operation_id": {
                    "request": {...},
                    "response": {...},
                    "status_code": 200
                }
            }
        """
        examples: dict[str, Any] = {}

        # In test mode, skip semgrep entirely to avoid subprocess hangs and use AST-based extraction
        is_test_mode = os.environ.get("TEST_MODE") == "true"
        if is_test_mode:
            # Skip semgrep in test mode - use AST-based extraction directly (faster and more reliable)
            return self._extract_examples_from_ast(test_files)

        if not self.semgrep_config.exists():
            # Semgrep config not available, fall back to AST-based extraction
            return self._extract_examples_from_ast(test_files)

        # Extract unique test file paths
        test_paths: set[Path] = set()
        for test_ref in test_files:
            file_path = test_ref.split("::")[0] if "::" in test_ref else test_ref
            test_paths.add(self.repo_path / file_path)

        # Run Semgrep on test files in parallel (limit to avoid excessive processing time)
        # Process up to 10 test files per feature to avoid timeout issues
        test_paths_list = [p for p in list(test_paths)[:10] if p.exists()]

        if not test_paths_list:
            # No valid test files, fall back to AST
            return self._extract_examples_from_ast(test_files)

        examples.update(self._merge_semgrep_examples(test_paths_list))

        if not examples:
            examples = self._extract_examples_from_ast(test_files)

        return examples

    @staticmethod
    def _cancel_pending_futures(future_to_path: dict[Future[Any], Path]) -> None:
        for f in future_to_path:
            if not f.done():
                f.cancel()

    def _collect_semgrep_results_from_futures(
        self, future_to_path: dict[Future[Any], Path], examples: dict[str, Any]
    ) -> bool:
        try:
            for future in as_completed(future_to_path):
                test_path = future_to_path[future]
                try:
                    semgrep_results = future.result()
                    file_examples = self._parse_semgrep_results(semgrep_results, test_path)
                    examples.update(file_examples)
                except KeyboardInterrupt:
                    self._cancel_pending_futures(future_to_path)
                    return True
                except Exception:
                    continue
        except KeyboardInterrupt:
            self._cancel_pending_futures(future_to_path)
            return True
        return False

    def _merge_semgrep_examples(self, test_paths_list: list[Path]) -> dict[str, Any]:
        examples: dict[str, Any] = {}
        max_workers = min(len(test_paths_list), 4)
        executor = ThreadPoolExecutor(max_workers=max_workers)
        interrupted = False
        try:
            future_to_path = {executor.submit(self._run_semgrep, test_path): test_path for test_path in test_paths_list}
            interrupted = self._collect_semgrep_results_from_futures(future_to_path, examples)
            if interrupted:
                raise KeyboardInterrupt
        except KeyboardInterrupt:
            interrupted = True
            executor.shutdown(wait=False, cancel_futures=True)
            raise
        finally:
            if not interrupted:
                executor.shutdown(wait=True)
            else:
                executor.shutdown(wait=False)

        return examples

    @beartype
    @require(lambda self, test_path: isinstance(test_path, Path), "Test path must be Path")
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def _run_semgrep(self, test_path: Path) -> list[dict[str, Any]]:
        """Run Semgrep on a test file and return results."""
        try:
            # Reduced timeout to avoid hanging on large test files
            # Further reduced to 5s for faster processing (can be made configurable)
            result = subprocess.run(
                ["semgrep", "--config", str(self.semgrep_config), "--json", str(test_path)],
                capture_output=True,
                text=True,
                timeout=5,  # Reduced from 10 to 5 seconds for faster processing
                check=False,
            )

            if result.returncode != 0:
                return []

            data = json.loads(result.stdout)
            return data.get("results", [])

        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
            return []

    @beartype
    @require(lambda results: isinstance(results, list), "Results must be list")
    @require(lambda test_path: isinstance(test_path, Path), "Test path must be Path")
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def _parse_semgrep_results(self, results: list[dict[str, Any]], test_path: Path) -> dict[str, Any]:
        """Parse Semgrep results and extract example data."""
        examples: dict[str, Any] = {}

        # Parse test file with AST to get actual code
        try:
            tree = ast.parse(test_path.read_text(encoding="utf-8"), filename=str(test_path))
        except Exception:
            return examples

        # Map Semgrep results to AST nodes
        for result in results:
            rule_id = result.get("check_id", "")
            start_line = result.get("start", {}).get("line", 0)

            # Extract examples based on rule type
            if "extract-test-request-data" in rule_id:
                example = self._extract_request_example(tree, start_line)
                if example:
                    operation_id = example.get("operation_id", "unknown")
                    if operation_id not in examples:
                        examples[operation_id] = {}
                    examples[operation_id]["request"] = example.get("request", {})
            elif "extract-test-response-data" in rule_id:
                example = self._extract_response_example(tree, start_line)
                if example:
                    operation_id = example.get("operation_id", "unknown")
                    if operation_id not in examples:
                        examples[operation_id] = {}
                    examples[operation_id]["response"] = example.get("response", {})
                    examples[operation_id]["status_code"] = example.get("status_code", 200)

        return examples

    @beartype
    @require(lambda tree: isinstance(tree, ast.AST), "Tree must be AST node")
    @require(lambda line: isinstance(line, int) and line > 0, "Line must be positive integer")
    @ensure(lambda result: result is None or isinstance(result, dict), "Must return None or dict")
    def _extract_request_example(self, tree: ast.AST, line: int) -> dict[str, Any] | None:
        """Extract request example from AST node near the specified line."""
        # Find the function containing this line
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.lineno <= line <= (node.end_lineno or node.lineno):
                # Look for HTTP request patterns
                for child in ast.walk(node):
                    if (
                        isinstance(child, ast.Call)
                        and isinstance(child.func, ast.Attribute)
                        and child.func.attr in ("post", "get", "put", "delete", "patch")
                    ):
                        method_name = child.func.attr
                        # Extract path and data
                        path = self._extract_string_arg(child, 0)
                        data = self._extract_json_arg(child, "json") or self._extract_json_arg(child, "data")

                        if path:
                            operation_id = f"{method_name}_{path.replace('/', '_').replace('-', '_').strip('_')}"
                            return {
                                "operation_id": operation_id,
                                "request": {
                                    "path": path,
                                    "method": method_name.upper(),
                                    "body": data or {},
                                },
                            }

        return None

    def _extract_json_assertion(self, child: ast.AST) -> dict[str, Any] | None:
        """
        Extract a JSON-response example from an assert statement.

        Args:
            child: AST statement node to inspect

        Returns:
            Example dict if a ``response.json() == {...}`` assertion is found, else None
        """
        if not (isinstance(child, ast.Assert) and isinstance(child.test, ast.Compare)):
            return None
        left = child.test.left
        if (
            isinstance(left, ast.Call)
            and isinstance(left.func, ast.Attribute)
            and left.func.attr == "json"
            and child.test.comparators
        ):
            expected = self._extract_ast_value(child.test.comparators[0])
            if expected:
                return {"operation_id": "unknown", "response": expected, "status_code": 200}
        return None

    def _extract_status_code_assertion(self, child: ast.AST) -> dict[str, Any] | None:
        """
        Extract a status-code example from a compare/call node.

        Args:
            child: AST statement node to inspect

        Returns:
            Example dict if a status_code comparison is found, else None
        """
        if (
            isinstance(child, ast.Call)
            and isinstance(child.func, ast.Attribute)
            and child.func.attr == "status_code"
            and isinstance(child, ast.Compare)
            and child.comparators
        ):
            status_code = self._extract_ast_value(child.comparators[0])
            if isinstance(status_code, int):
                return {"operation_id": "unknown", "response": {}, "status_code": status_code}
        return None

    def _scan_function_for_response(self, func_node: ast.FunctionDef) -> dict[str, Any] | None:
        """
        Scan all child nodes of a function for response assertion patterns.

        Args:
            func_node: Function AST node to scan

        Returns:
            First matching response example dict, or None
        """
        for child in ast.walk(func_node):
            result = self._extract_json_assertion(child)
            if result:
                return result
            result = self._extract_status_code_assertion(child)
            if result:
                return result
        return None

    @beartype
    @require(lambda tree: isinstance(tree, ast.AST), "Tree must be AST node")
    @require(lambda line: isinstance(line, int) and line > 0, "Line must be positive integer")
    @ensure(lambda result: result is None or isinstance(result, dict), "Must return None or dict")
    def _extract_response_example(self, tree: ast.AST, line: int) -> dict[str, Any] | None:
        """Extract response example from AST node near the specified line."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.lineno <= line <= (node.end_lineno or node.lineno):
                result = self._scan_function_for_response(node)
                if result:
                    return result
        return None

    @beartype
    def _extract_string_arg(self, call: ast.Call, index: int) -> str | None:
        """Extract string argument from function call."""
        if index < len(call.args):
            arg = call.args[index]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                return arg.value
            # Try to unparse if available
            try:
                if hasattr(ast, "unparse"):
                    return ast.unparse(arg)
            except Exception:
                pass
        return None

    @beartype
    def _extract_json_arg(self, call: ast.Call, keyword: str) -> dict[str, Any] | None:
        """Extract JSON/data argument from function call."""
        for keyword_arg in call.keywords:
            if keyword_arg.arg == keyword:
                value = keyword_arg.value
                # Try to extract dict literal
                if isinstance(value, ast.Dict):
                    result: dict[str, Any] = {}
                    for k, v in zip(value.keys, value.values, strict=True):
                        if k is not None:
                            key = self._extract_ast_value(k)
                            val = self._extract_ast_value(v)
                            if key is not None:
                                result[str(key)] = val
                    return result
        return None

    @beartype
    def _extract_ast_value(self, node: ast.AST) -> Any:
        """Extract value from AST node."""
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Dict):
            result: dict[str, Any] = {}
            for k, v in zip(node.keys, node.values, strict=True):
                key = self._extract_ast_value(k) if k else None
                val = self._extract_ast_value(v)
                if key is not None:
                    result[str(key)] = val
            return result
        if isinstance(node, ast.List):
            return [self._extract_ast_value(item) for item in node.elts]
        if isinstance(node, ast.Name):
            # Variable reference - can't extract value statically
            return None
        # Try to unparse if available
        try:
            if hasattr(ast, "unparse"):
                return ast.unparse(node)
        except Exception:
            pass
        return None

    @beartype
    @require(lambda test_files: isinstance(test_files, list), "Test files must be list")
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def _extract_examples_from_ast(self, test_files: list[str]) -> dict[str, Any]:
        """Fallback: Extract examples using AST when Semgrep is not available."""
        examples: dict[str, Any] = {}

        for test_ref in test_files:
            if "::" in test_ref:
                file_path_str, func_name = test_ref.split("::", 1)
            else:
                file_path_str = test_ref
                func_name = None

            test_path = self.repo_path / file_path_str
            if not test_path.exists():
                continue

            try:
                tree = ast.parse(test_path.read_text(encoding="utf-8"), filename=str(test_path))

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        if func_name and node.name != func_name:
                            continue
                        if node.name.startswith("test_"):
                            # Extract examples from test function
                            example = self._extract_examples_from_test_function(node)
                            if example:
                                operation_id = example.get("operation_id", "unknown")
                                if operation_id not in examples:
                                    examples[operation_id] = {}
                                examples[operation_id].update(example)

            except Exception:
                continue

        return examples

    def _apply_http_call_to_example(self, child: ast.Call, method_name: str, example: dict[str, Any]) -> None:
        """
        Update the example dict with request data extracted from an HTTP method call.

        Args:
            child: AST Call node for the HTTP method
            method_name: HTTP method name (e.g. ``"post"``, ``"get"``)
            example: Mutable example dict to update in place
        """
        path = self._extract_string_arg(child, 0)
        data = self._extract_json_arg(child, "json") or self._extract_json_arg(child, "data")
        if path:
            operation_id = f"{method_name}_{path.replace('/', '_').replace('-', '_').strip('_')}"
            example["operation_id"] = operation_id
            example.setdefault("request", {})
            example["request"].update({"path": path, "method": method_name.upper(), "body": data or {}})

    def _apply_json_response_to_example(self, node: ast.FunctionDef, child: ast.Call, example: dict[str, Any]) -> None:
        """
        Scan the function for an assert that compares ``response.json()`` and update the example.

        Args:
            node: Parent function AST node to walk for sibling assertions
            child: The ``response.json()`` call node
            example: Mutable example dict to update in place
        """
        for sibling in ast.walk(node):
            if (
                isinstance(sibling, ast.Assert)
                and isinstance(sibling.test, ast.Compare)
                and sibling.test.left == child
                and sibling.test.comparators
            ):
                expected = self._extract_ast_value(sibling.test.comparators[0])
                if expected:
                    example["response"] = expected
                    example["status_code"] = 200

    @beartype
    @require(lambda node: isinstance(node, ast.FunctionDef), "Node must be FunctionDef")
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def _extract_examples_from_test_function(self, node: ast.FunctionDef) -> dict[str, Any]:
        """Extract examples from a test function AST node."""
        example: dict[str, Any] = {}

        for child in ast.walk(node):
            if not (isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute)):
                continue
            method_name = child.func.attr
            if method_name in ("post", "get", "put", "delete", "patch"):
                self._apply_http_call_to_example(child, method_name, example)
            if method_name == "json" and isinstance(child.func.value, ast.Attribute):
                self._apply_json_response_to_example(node, child, example)

        return example

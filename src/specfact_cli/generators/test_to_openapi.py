"""Convert Python test source to OpenAPI examples without executing it."""

from __future__ import annotations

import ast
import tokenize
import warnings
from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require


HTTP_METHODS = frozenset({"post", "get", "put", "delete", "patch"})


class OpenAPITestConverter:
    """Extract literal HTTP requests and their asserted responses from Python tests."""

    def __init__(self, repo_path: Path, semgrep_config: Path | None = None) -> None:
        self.repo_path = repo_path.resolve()
        if semgrep_config is not None or (self.repo_path / "tools/semgrep/test-patterns.yml").is_file():
            warnings.warn(
                "Semgrep test-pattern configuration is retired. SpecFact extracts examples from Python test source.",
                UserWarning,
                stacklevel=2,
            )

    @beartype
    @require(lambda self, test_files: isinstance(test_files, list), "Test files must be list")
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def extract_examples_from_tests(self, test_files: list[str]) -> dict[str, Any]:
        """Read selected files or file::test references and return examples by operation ID."""
        examples: dict[str, Any] = {}
        for test_ref in test_files:
            path, _, selected_test = test_ref.partition("::")
            test_path = self.repo_path / path
            try:
                with tokenize.open(test_path) as stream:
                    tree = ast.parse(stream.read(), filename=str(test_path))
            except (OSError, SyntaxError, UnicodeError):
                continue
            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or not node.name.startswith("test_"):
                    continue
                if selected_test and node.name != selected_test:
                    continue
                for operation, example in self._extract_examples_from_test_function(node).items():
                    examples.setdefault(operation, {}).update(example)
        return examples

    def _extract_examples_from_test_function(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> dict[str, dict[str, Any]]:
        """Associate assertions with the request assigned to their response variable."""
        examples: dict[str, dict[str, Any]] = {}
        responses: dict[str, dict[str, Any]] = {}
        statements = sorted(
            (child for child in ast.walk(node) if isinstance(child, (ast.Assign, ast.AnnAssign, ast.Expr, ast.Assert))),
            key=lambda child: (child.lineno, child.col_offset),
        )
        for statement in statements:
            if isinstance(statement, ast.Assert):
                self._apply_response_assertion(statement, responses)
                continue
            targets = self._assignment_names(statement)
            for target in targets:
                responses.pop(target, None)
            value = statement.value
            if isinstance(value, ast.Await):
                value = value.value
            if not isinstance(value, ast.Call) or not isinstance(value.func, ast.Attribute):
                continue
            method = value.func.attr
            path = self._extract_string_arg(value, 0)
            if method not in HTTP_METHODS or not path:
                continue
            operation = f"{method}_{path.replace('/', '_').replace('-', '_').strip('_')}"
            body = self._extract_json_arg(value, "json") or self._extract_json_arg(value, "data") or {}
            example: dict[str, Any] = {
                "operation_id": operation,
                "request": {"path": path, "method": method.upper(), "body": body},
            }
            examples[operation] = example
            for target in targets:
                responses[target] = example
        return examples

    @staticmethod
    def _assignment_names(statement: ast.Assign | ast.AnnAssign | ast.Expr) -> list[str]:
        if isinstance(statement, ast.Assign):
            return [target.id for target in statement.targets if isinstance(target, ast.Name)]
        if isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
            return [statement.target.id]
        return []

    def _apply_response_assertion(self, statement: ast.Assert, responses: dict[str, dict[str, Any]]) -> None:
        compare = statement.test
        if not isinstance(compare, ast.Compare) or len(compare.ops) != 1 or not isinstance(compare.ops[0], ast.Eq):
            return
        left = compare.left
        attribute = left.func if isinstance(left, ast.Call) else left
        if not isinstance(attribute, ast.Attribute) or not isinstance(attribute.value, ast.Name):
            return
        example = responses.get(attribute.value.id)
        if example is None:
            return
        expected = self._extract_ast_value(compare.comparators[0])
        if isinstance(left, ast.Call) and attribute.attr == "json" and expected is not None:
            example["response"] = expected
            example.setdefault("status_code", 200)
        elif attribute.attr == "status_code" and type(expected) is int:
            example["status_code"] = expected

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

    def _coerce_ast_dict_to_plain(self, value: ast.Dict) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for k, v in zip(value.keys, value.values, strict=True):
            if k is None:
                continue
            key = self._extract_ast_value(k)
            val = self._extract_ast_value(v)
            if key is not None:
                result[str(key)] = val
        return result

    @beartype
    def _extract_json_arg(self, call: ast.Call, keyword: str) -> dict[str, Any] | None:
        """Extract JSON/data argument from function call."""
        for keyword_arg in call.keywords:
            if keyword_arg.arg != keyword:
                continue
            inner = keyword_arg.value
            if isinstance(inner, ast.Dict):
                return self._coerce_ast_dict_to_plain(inner)
        return None

    @beartype
    def _extract_ast_value(self, node: ast.AST) -> Any:
        """Extract value from AST node."""
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Dict):
            return self._coerce_ast_dict_to_plain(node)
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

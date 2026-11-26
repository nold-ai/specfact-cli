"""Convert Python test source to OpenAPI examples without executing it."""

from __future__ import annotations

import ast
import tokenize
import warnings
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Any, TypeGuard

from beartype import beartype
from icontract import ensure, require

from specfact_cli.analyzers.async_checks import import_aliases, qualified_name


_ABSENT_BODY = object()

HTTP_METHODS = frozenset({"post", "get", "put", "delete", "patch"})
HTTP_MODULES = frozenset({"requests", "httpx"})
CLIENT_FIXTURES = frozenset({"client", "api_client", "async_client", "http_client", "test_client", "self.client"})
CLIENT_CONSTRUCTORS = frozenset(
    {
        "TestClient",
        "APIClient",
        "fastapi.testclient.TestClient",
        "starlette.testclient.TestClient",
        "rest_framework.test.APIClient",
        "httpx.Client",
        "httpx.AsyncClient",
        "requests.Session",
        "requests.session",
    }
)


def _test_body_nodes(body: Sequence[ast.stmt]) -> Iterator[ast.AST]:
    pending: list[ast.AST] = list(reversed(body))
    while pending:
        node = pending.pop()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            continue
        yield node
        pending.extend(reversed(list(ast.iter_child_nodes(node))))


def _client_assignment(value: ast.AST, aliases: dict[str, str], clients: set[str]) -> bool:
    if isinstance(value, ast.Call):
        return qualified_name(value.func, aliases) in CLIENT_CONSTRUCTORS
    return qualified_name(value, {}) in clients


_TestStatement = (
    ast.Assign | ast.AnnAssign | ast.Expr | ast.Assert | ast.With | ast.AsyncWith | ast.Import | ast.ImportFrom
)


def _test_statements(nodes: Sequence[ast.AST]) -> list[_TestStatement]:
    return sorted(
        (node for node in nodes if isinstance(node, _TestStatement)),
        key=lambda statement: (statement.lineno, statement.col_offset),
    )


def _operation_examples(requests: dict[tuple[str, str], dict[str, Any]]) -> dict[str, Any]:
    """Keep existing operation IDs unless distinct requests collide."""
    reserved = {item["operation_id"] for item in requests.values()}
    examples: dict[str, Any] = {}
    for request in sorted(requests):
        example = requests[request]
        base = example["operation_id"]
        name, suffix = base, 2
        while name in examples or (name != base and name in reserved):
            name = f"{base}_{suffix}"
            suffix += 1
        examples[name] = {**example, "operation_id": name}
    return examples


def _is_equality_assertion(node: ast.AST) -> TypeGuard[ast.Compare]:
    return isinstance(node, ast.Compare) and len(node.ops) == 1 and isinstance(node.ops[0], ast.Eq)


def _response_attribute(expression: ast.expr) -> tuple[str, str] | None:
    attribute = expression.func if isinstance(expression, ast.Call) else expression
    if isinstance(attribute, ast.Attribute) and isinstance(attribute.value, ast.Name):
        return attribute.value.id, attribute.attr
    return None


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
        requests: dict[tuple[str, str], dict[str, Any]] = {}
        for test_ref in test_files:
            path, _, selected_test = test_ref.partition("::")
            test_path = self.repo_path / path
            try:
                with tokenize.open(test_path) as stream:
                    tree = ast.parse(stream.read(), filename=str(test_path))
            except (OSError, SyntaxError, UnicodeError):
                continue
            aliases = import_aliases(tree.body)
            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or not node.name.startswith("test_"):
                    continue
                if selected_test and node.name != selected_test:
                    continue
                requests.update(self._extract_examples_from_test_function(node, aliases))
        return _operation_examples(requests)

    def _extract_examples_from_test_function(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, module_aliases: dict[str, str]
    ) -> dict[tuple[str, str], dict[str, Any]]:
        """Associate assertions with the request assigned to their response variable."""
        nodes = list(_test_body_nodes(node.body))
        aliases = module_aliases.copy()
        clients = set(CLIENT_FIXTURES | HTTP_MODULES)
        clients.update(name for name, module in aliases.items() if module in HTTP_MODULES)
        statements = _test_statements(nodes)
        examples: dict[tuple[str, str], dict[str, Any]] = {}
        responses: dict[str, dict[str, Any]] = {}
        for statement in statements:
            if isinstance(statement, (ast.Import, ast.ImportFrom)):
                imports = import_aliases([statement])
                aliases.update(imports)
                clients.difference_update(imports)
                clients.update(name for name, module in imports.items() if module in HTTP_MODULES)
                for name in imports:
                    responses.pop(name, None)
                continue
            if isinstance(statement, ast.Assert):
                self._apply_response_assertion(statement, responses)
                continue
            if isinstance(statement, (ast.With, ast.AsyncWith)):
                self._bind_context_clients(statement.items, aliases, clients, responses)
                continue
            targets = self._assignment_names(statement)
            for target in targets:
                responses.pop(target, None)
            value = statement.value
            example = self._request_example(value, clients)
            self._bind_clients(targets, value, aliases, clients)
            if example is not None:
                request = example["request"]
                examples[request["method"], request["path"]] = example
                responses.update(dict.fromkeys(targets, example))
        return examples

    @staticmethod
    def _bind_clients(
        targets: Sequence[str], value: ast.AST | None, aliases: dict[str, str], clients: set[str]
    ) -> None:
        if not targets or value is None:
            return
        if _client_assignment(value, aliases, clients):
            clients.update(targets)
        else:
            clients.difference_update(targets)
        for target in targets:
            aliases.pop(target, None)

    @staticmethod
    def _bind_context_clients(
        items: Sequence[ast.withitem],
        aliases: dict[str, str],
        clients: set[str],
        responses: dict[str, dict[str, Any]],
    ) -> None:
        for item in items:
            if item.optional_vars is None:
                continue
            targets = [
                node.id
                for node in ast.walk(item.optional_vars)
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
            ]
            for target in targets:
                responses.pop(target, None)
            value = item.context_expr if isinstance(item.optional_vars, ast.Name) else ast.Constant(None)
            OpenAPITestConverter._bind_clients(targets, value, aliases, clients)

    def _request_example(self, value: ast.AST | None, clients: set[str]) -> dict[str, Any] | None:
        if isinstance(value, ast.Await):
            value = value.value
        if not isinstance(value, ast.Call) or not isinstance(value.func, ast.Attribute):
            return None
        method = value.func.attr
        path = self._extract_string_arg(value, 0)
        if method not in HTTP_METHODS or not path or qualified_name(value.func.value, {}) not in clients:
            return None
        operation = f"{method}_{path.replace('/', '_').replace('-', '_').strip('_')}"
        body = self._extract_json_arg(value, "json", unavailable=_ABSENT_BODY)
        if body is _ABSENT_BODY:
            body = self._extract_json_arg(value, "data", unavailable={})
        return {
            "operation_id": operation,
            "request": {"path": path, "method": method.upper(), "body": body},
        }

    @staticmethod
    def _assignment_names(statement: ast.Assign | ast.AnnAssign | ast.Expr) -> list[str]:
        if isinstance(statement, ast.Assign):
            return [target.id for target in statement.targets if isinstance(target, ast.Name)]
        if isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
            return [statement.target.id]
        return []

    def _apply_response_assertion(self, statement: ast.Assert, responses: dict[str, dict[str, Any]]) -> None:
        compare = statement.test
        if not _is_equality_assertion(compare):
            return
        left = compare.left
        target = _response_attribute(left)
        if target is None:
            return
        receiver, attribute = target
        example = responses.get(receiver)
        if example is None:
            return
        expected = self._extract_ast_value(compare.comparators[0])
        if isinstance(left, ast.Call):
            if attribute == "json" and expected is not None:
                example["response"] = expected
                example.setdefault("status_code", 200)
        elif attribute == "status_code" and type(expected) is int:
            example["status_code"] = expected

    @beartype
    def _extract_string_arg(self, call: ast.Call, index: int) -> str | None:
        """Return a literal string argument."""
        if index < len(call.args):
            arg = call.args[index]
        elif index == 0:
            arg = next((keyword.value for keyword in call.keywords if keyword.arg == "url"), None)
        else:
            return None
        return arg.value if isinstance(arg, ast.Constant) and isinstance(arg.value, str) else None

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
    def _extract_json_arg(self, call: ast.Call, keyword: str, *, unavailable: Any = None) -> Any:
        """Extract a JSON literal and preserve falsey values."""
        for keyword_arg in call.keywords:
            if keyword_arg.arg != keyword:
                continue
            inner = keyword_arg.value
            if isinstance(inner, (ast.Dict, ast.List)):
                return self._extract_ast_value(inner)
            if isinstance(inner, ast.Constant) and isinstance(inner.value, (str, int, float, bool, type(None))):
                return inner.value
        return unavailable

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
        try:
            return ast.unparse(node)
        except (AttributeError, TypeError, ValueError, RecursionError):
            return None

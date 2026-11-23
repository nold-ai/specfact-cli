"""Analyze async Python source without importing or editing the target project."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import sys
import tokenize
from collections.abc import Iterator, Sequence
from dataclasses import asdict, dataclass
from itertools import pairwise
from pathlib import Path


RULES = {
    "asyncio-create-task-not-awaited": ("error", "Keep a reference to the scheduled task or await it."),
    "blocking-sleep-in-async": ("error", "Replace the blocking wait with an awaited async equivalent."),
    "missing-await-on-coroutine": ("error", "Await this coroutine or pass it to a task scheduler."),
    "bare-except-in-async": ("warning", "Use specific exception types and handle the exception."),
    "missing-timeout-on-wait": ("warning", "Set an explicit timeout on this asyncio wait."),
    "blocking-file-io-in-async": ("warning", "Move blocking file I/O to a worker or use an async file API."),
    "asyncio-gather-without-error-handling": ("warning", "Handle gather failures explicitly."),
    "event-loop-in-async-context": ("error", "Await the coroutine directly in the running event loop."),
    "missing-async-context-manager": ("info", "Consider binding the async context manager value."),
    "sync-lock-in-async": ("error", "Use an async synchronization primitive."),
    "sequential-await-could-be-parallel": ("info", "Only parallelize these awaits when operations are independent."),
    "missing-cancellation-handling": ("info", "Review whether this coroutine needs cancellation cleanup."),
    "task-result-not-checked": ("warning", "Await this task or inspect its result or exception."),
}
LEGACY_PACK_SHA256 = "a73e31b8fc7bfc200403037e8aad73c9cf2cadc89ddc662d97b7b1b2bd7fe64f"
PROJECT_EXCLUDES = frozenset({".git", ".hg", ".svn", ".venv", ".tox", ".nox", "__pycache__", "node_modules"})


@dataclass(frozen=True, order=True, slots=True)
class AsyncFinding:
    """Stable diagnostic for a Python source location."""

    file: str
    line: int
    column: int
    rule_id: str
    severity: str
    message: str


def qualified_name(node: ast.AST, aliases: dict[str, str]) -> str:
    """Resolve a syntactically qualified name through known imports."""
    if isinstance(node, ast.Name):
        return aliases.get(node.id, node.id)
    if isinstance(node, ast.Attribute):
        return f"{qualified_name(node.value, aliases)}.{node.attr}"
    return ""


def import_aliases(nodes: Sequence[ast.AST]) -> dict[str, str]:
    """Map aliases to imported Python names without loading modules."""
    aliases: dict[str, str] = {}
    for node in nodes:
        if isinstance(node, ast.Import):
            aliases.update({name.asname: name.name for name in node.names if name.asname})
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            aliases.update({name.asname or name.name: f"{node.module}.{name.name}" for name in node.names})
    return aliases


def _scoped_nodes(node: ast.AST) -> Iterator[ast.AST]:
    def descend(parent: ast.AST) -> Iterator[ast.AST]:
        for child in ast.iter_child_nodes(parent):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
                continue
            yield child
            yield from descend(child)

    return descend(node)


def _is_true(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and node.value is True


def _has_explicit_timeout(call: ast.Call) -> bool:
    timeout = call.args[1] if len(call.args) > 1 else None
    timeout = next((keyword.value for keyword in call.keywords if keyword.arg == "timeout"), timeout)
    return timeout is not None and not (isinstance(timeout, ast.Constant) and timeout.value is None)


def _runs_in_handler_scope(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> bool:
    while (parent := parents.get(node)) is not None:
        if isinstance(parent, (ast.Try, ast.TryStar)) and parent.handlers and node in parent.body:
            return True
        node = parent
    return False


CALL_RULES = {
    "time.sleep": "blocking-sleep-in-async",
    "time.wait": "blocking-sleep-in-async",
    "open": "blocking-file-io-in-async",
    "builtins.open": "blocking-file-io-in-async",
    "io.open": "blocking-file-io-in-async",
    "asyncio.run": "event-loop-in-async-context",
    "threading.Lock": "sync-lock-in-async",
    "threading.RLock": "sync-lock-in-async",
    "threading.Semaphore": "sync-lock-in-async",
}


def _nested_event_loop(call: ast.Call, aliases: dict[str, str]) -> bool:
    target = call.func
    return (
        isinstance(target, ast.Attribute)
        and target.attr == "run_until_complete"
        and isinstance(target.value, ast.Call)
        and qualified_name(target.value.func, aliases) == "asyncio.get_event_loop"
    )


def _unprotected_gather(call: ast.Call, parents: dict[ast.AST, ast.AST]) -> bool:
    accepts_exceptions = any(
        keyword.arg == "return_exceptions" and _is_true(keyword.value) for keyword in call.keywords
    )
    return not accepts_exceptions and not _runs_in_handler_scope(call, parents)


def _awaited_call_rules(call: ast.Call, name: str, parents: dict[ast.AST, ast.AST]) -> Iterator[str]:
    if name in {"asyncio.wait", "asyncio.wait_for"} and not _has_explicit_timeout(call):
        yield "missing-timeout-on-wait"
    if name == "asyncio.gather" and _unprotected_gather(call, parents):
        yield "asyncio-gather-without-error-handling"


def _async_call_rules(
    call: ast.Call,
    parents: dict[ast.AST, ast.AST],
    aliases: dict[str, str],
    coroutines: set[str],
) -> Iterator[str]:
    name = qualified_name(call.func, aliases)
    if rule := CALL_RULES.get(name):
        yield rule
    parent = parents.get(call)
    if isinstance(parent, ast.Expr):
        if name == "asyncio.create_task":
            yield "asyncio-create-task-not-awaited"
        if name in coroutines:
            yield "missing-await-on-coroutine"
    elif isinstance(parent, ast.Await):
        yield from _awaited_call_rules(call, name, parents)
    if _nested_event_loop(call, aliases):
        yield "event-loop-in-async-context"


def _handler_names(node: ast.AST | None, aliases: dict[str, str]) -> set[str]:
    if node is None:
        return set()
    children = node.elts if isinstance(node, ast.Tuple) else [node]
    return {qualified_name(child, aliases) for child in children}


def _is_await_statement(statement: ast.AST) -> bool:
    return isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Await)


def _adjacent_awaits(node: ast.AST) -> Iterator[ast.stmt]:
    for _, children in ast.iter_fields(node):
        if not isinstance(children, list):
            continue
        statements = (item for item in children if isinstance(item, ast.stmt))
        for first, second in pairwise(statements):
            if _is_await_statement(first) and _is_await_statement(second):
                yield first


def _task_names(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Assign):
        return [target.id for target in node.targets if isinstance(target, ast.Name)]
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return [node.target.id]
    return []


def _task_result_references(node: ast.AST, aliases: dict[str, str]) -> Iterator[str]:
    if isinstance(node, ast.Await) and isinstance(node.value, ast.Name):
        yield node.value.id
    if not isinstance(node, ast.Call):
        return
    if (
        isinstance(node.func, ast.Attribute)
        and node.func.attr in {"result", "exception"}
        and isinstance(node.func.value, ast.Name)
    ):
        yield node.func.value.id
    if qualified_name(node.func, aliases) in {"asyncio.wait_for", "asyncio.gather", "asyncio.shield"}:
        yield from (arg.id for arg in node.args if isinstance(arg, ast.Name))


def _assigns_value(node: ast.AST) -> bool:
    return isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None


def _task_event_position(node: ast.AST) -> tuple[int, int]:
    if isinstance(node, (ast.Assign, ast.AnnAssign)):
        return (node.end_lineno or node.lineno, node.end_col_offset or node.col_offset)
    if isinstance(node, (ast.Call, ast.Await)):
        return (node.lineno, node.col_offset)
    raise TypeError("Task events must be assignments, calls or awaits")


def _task_assignment(value: ast.AST | None, aliases: dict[str, str]) -> ast.Call | None:
    if isinstance(value, ast.Call) and qualified_name(value.func, aliases) == "asyncio.create_task":
        return value
    return None


def _track_task_assignment(
    node: ast.Assign | ast.AnnAssign, aliases: dict[str, str], active: dict[str, ast.Call]
) -> ast.Call | None:
    names = _task_names(node)
    for name in names:
        active.pop(name, None)
    task = _task_assignment(node.value, aliases)
    if names and task is not None:
        active.update(dict.fromkeys(names, task))
        return task
    return None


def _unobserved_tasks(nodes: Sequence[ast.AST], aliases: dict[str, str]) -> Iterator[ast.Call]:
    active: dict[str, ast.Call] = {}
    assignments: list[ast.Call] = []
    observed: set[ast.Call] = set()
    events = (node for node in nodes if _assigns_value(node) or isinstance(node, (ast.Call, ast.Await)))
    for node in sorted(events, key=_task_event_position):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            if (task := _track_task_assignment(node, aliases, active)) is not None:
                assignments.append(task)
        else:
            observed.update(active[name] for name in _task_result_references(node, aliases) if name in active)
    yield from (call for call in assignments if call not in observed)


def _silent_handler(handler: ast.ExceptHandler, aliases: dict[str, str]) -> bool:
    names = _handler_names(handler.type, aliases)
    return handler.type is None or ("Exception" in names and all(isinstance(item, ast.Pass) for item in handler.body))


def _async_statement_rules(
    node: ast.AST, aliases: dict[str, str]
) -> Iterator[tuple[str, ast.stmt | ast.ExceptHandler]]:
    if isinstance(node, ast.ExceptHandler) and _silent_handler(node, aliases):
        yield "bare-except-in-async", node
    if isinstance(node, ast.AsyncWith) and any(item.optional_vars is None for item in node.items):
        yield "missing-async-context-manager", node
    yield from (("sequential-await-could-be-parallel", item) for item in _adjacent_awaits(node))


def _has_cancellation_handler(nodes: Sequence[ast.AST], aliases: dict[str, str]) -> bool:
    handlers = (node for node in nodes if isinstance(node, ast.ExceptHandler))
    return any("asyncio.CancelledError" in _handler_names(node.type, aliases) for node in handlers)


def _scope_findings(
    scope: ast.AsyncFunctionDef,
    aliases: dict[str, str],
    coroutines: set[str],
) -> Iterator[tuple[str, ast.stmt | ast.expr | ast.ExceptHandler]]:
    nodes: list[ast.AST] = [scope]
    for statement in scope.body:
        if not isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            nodes.extend((statement, *_scoped_nodes(statement)))
    imports = {**aliases, **import_aliases(nodes)}
    parents = {child: node for node in nodes for child in ast.iter_child_nodes(node)}
    for node in nodes:
        if isinstance(node, ast.Call):
            yield from ((rule, node) for rule in _async_call_rules(node, parents, imports, coroutines))
        yield from _async_statement_rules(node, imports)
    yield from (("task-result-not-checked", call) for call in _unobserved_tasks(nodes, imports))
    if not _has_cancellation_handler(nodes, imports):
        yield "missing-cancellation-handling", scope


_LexicalScope = ast.Module | ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef


def _enclosing_scope(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> _LexicalScope | None:
    while (parent := parents.get(node)) is not None:
        if isinstance(parent, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            return parent
        node = parent
    return None


def _scope_functions(tree: ast.Module, parents: dict[ast.AST, ast.AST]) -> dict[_LexicalScope, dict[str, bool]]:
    definitions: dict[_LexicalScope, dict[str, bool]] = {}
    functions = (node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)))
    for function in sorted(functions, key=lambda node: node.lineno):
        owner = _enclosing_scope(function, parents)
        if owner is not None:
            definitions.setdefault(owner, {})[function.name] = isinstance(function, ast.AsyncFunctionDef)
    return definitions


def _method_coroutines(
    scope: ast.AsyncFunctionDef, owner: _LexicalScope | None, definitions: dict[_LexicalScope, dict[str, bool]]
) -> set[str]:
    arguments = scope.args.posonlyargs + scope.args.args
    if not isinstance(owner, ast.ClassDef) or not arguments:
        return set()
    if any(qualified_name(node, {}).rsplit(".", 1)[-1] == "staticmethod" for node in scope.decorator_list):
        return set()
    receiver = arguments[0].arg
    return {f"{receiver}.{name}" for name, is_async in definitions.get(owner, {}).items() if is_async}


def _visible_coroutines(
    scope: ast.AsyncFunctionDef, parents: dict[ast.AST, ast.AST], definitions: dict[_LexicalScope, dict[str, bool]]
) -> set[str]:
    owner = _enclosing_scope(scope, parents)
    visible = dict(definitions.get(scope, {}))
    visible.update(
        dict.fromkeys((arg.arg for arg in scope.args.posonlyargs + scope.args.args + scope.args.kwonlyargs), False)
    )
    result = _method_coroutines(scope, owner, definitions)
    while owner is not None:
        if not isinstance(owner, ast.ClassDef):
            for name, is_async in definitions.get(owner, {}).items():
                visible.setdefault(name, is_async)
        owner = _enclosing_scope(owner, parents)
    return result | {name for name, is_async in visible.items() if is_async}


def async_findings(tree: ast.Module, filename: str) -> list[AsyncFinding]:
    """Check each async function and attribute findings to source positions."""
    aliases = import_aliases(tree.body)
    nodes = list(ast.walk(tree))
    parents = {child: node for node in nodes for child in ast.iter_child_nodes(node)}
    definitions = _scope_functions(tree, parents)
    findings: set[AsyncFinding] = set()
    for scope in (node for node in nodes if isinstance(node, ast.AsyncFunctionDef)):
        coroutines = _visible_coroutines(scope, parents, definitions)
        for rule, node in _scope_findings(scope, aliases, coroutines):
            severity, message = RULES[rule]
            findings.add(AsyncFinding(filename, node.lineno, node.col_offset + 1, rule, severity, message))
    return sorted(findings)


def _source_paths(root: Path, paths: Sequence[str]) -> Iterator[Path]:
    for argument in paths:
        path = root / argument
        if path.is_dir() and not path.is_symlink():
            for directory, subdirectories, files in os.walk(path):
                subdirectories[:] = sorted(name for name in subdirectories if name not in PROJECT_EXCLUDES)
                yield from (Path(directory) / name for name in sorted(files) if name.endswith(".py"))
        else:
            yield path


def _scan(root: Path, paths: Sequence[str]) -> tuple[list[AsyncFinding], list[dict[str, str]], int]:
    findings: list[AsyncFinding] = []
    diagnostics: list[dict[str, str]] = []
    scanned = 0
    for path in sorted(set(_source_paths(root, paths))):
        try:
            relative = path.relative_to(root)
            if not path.resolve().is_relative_to(root) or path.is_symlink() or path.suffix != ".py":
                raise OSError("not an in-project Python source file")
            with tokenize.open(path) as stream:
                tree = ast.parse(stream.read(), filename=str(relative))
        except (OSError, ValueError, SyntaxError, UnicodeError) as exc:
            diagnostics.append({"file": os.path.relpath(path, root), "message": str(exc)})
        else:
            scanned += 1
            findings.extend(async_findings(tree, str(relative)))
    return findings, diagnostics, scanned


def _legacy_policy_diagnostic(root: Path, policy: Path) -> str | None:
    try:
        if not policy.resolve().is_relative_to(root):
            raise OSError("async policy outside project")
        digest = hashlib.sha256(policy.read_bytes()).hexdigest()
    except OSError:
        return "Could not read the legacy async policy."
    if digest != LEGACY_PACK_SHA256:
        return "Custom Semgrep async rules require migration. Run the built-in checks explicitly with 'hatch run scan'."
    return None


def main() -> int:
    """Run source-only async checks and emit a machine-readable result."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--legacy-config", type=Path)
    parser.add_argument("--fix", action="store_true", help="Report migration guidance for retired source fixes")
    parser.add_argument("paths", nargs="*", default=["."])
    args = parser.parse_intermixed_args()
    root = args.root.resolve()
    findings, diagnostics, scanned = _scan(root, args.paths or ["."])
    if args.legacy_config is not None:
        message = _legacy_policy_diagnostic(root, root / args.legacy_config)
        if message:
            diagnostics.append({"file": str(args.legacy_config), "message": message})
    if args.fix and any(finding.rule_id == "blocking-sleep-in-async" for finding in findings):
        diagnostics.append({"file": "", "message": "Apply manual fixes using the reported async finding locations."})
    json.dump(
        {
            "engine": "python-ast",
            "rules_run": len(RULES),
            "targets_scanned": scanned,
            "total_findings": len(findings),
            "findings": [asdict(finding) for finding in findings],
            "diagnostics": diagnostics,
        },
        sys.stdout,
    )
    sys.stdout.write("\n")
    return 2 if diagnostics else int(any(finding.severity == "error" for finding in findings))


if __name__ == "__main__":
    raise SystemExit(main())

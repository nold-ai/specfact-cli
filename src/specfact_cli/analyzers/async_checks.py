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
from itertools import groupby, pairwise
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
    bindings: Sequence[_CallableBinding],
) -> Iterator[tuple[str, ast.stmt | ast.expr | ast.ExceptHandler]]:
    nodes: list[ast.AST] = [scope]
    for statement in scope.body:
        if not isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            nodes.extend((statement, *_scoped_nodes(statement)))
    imports = {**aliases, **import_aliases(nodes)}
    parents = {child: node for node in nodes for child in ast.iter_child_nodes(node)}
    for call, bound_coroutines in _calls_with_coroutines(nodes, parents, coroutines, bindings):
        yield from ((rule, call) for rule in _async_call_rules(call, parents, imports, bound_coroutines))
    for node in nodes:
        yield from _async_statement_rules(node, imports)
    yield from (("task-result-not-checked", call) for call in _unobserved_tasks(nodes, imports))
    if not _has_cancellation_handler(nodes, imports):
        yield "missing-cancellation-handling", scope


_LexicalScope = (
    ast.Module
    | ast.FunctionDef
    | ast.AsyncFunctionDef
    | ast.ClassDef
    | ast.Lambda
    | ast.ListComp
    | ast.SetComp
    | ast.DictComp
    | ast.GeneratorExp
)
_Loop = ast.For | ast.AsyncFor | ast.While


@dataclass(frozen=True)
class _CallableBinding:
    position: tuple[int, int]
    name: str
    value: bool | tuple[str, ...] | None
    may_skip: bool
    node: ast.AST


def _enclosing_scope(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> _LexicalScope | None:
    while (parent := parents.get(node)) is not None:
        if isinstance(parent, _LexicalScope):
            return parent
        node = parent
    return None


def _store_position(node: ast.Name, parents: dict[ast.AST, ast.AST]) -> tuple[int, int]:
    target: ast.AST = node
    while isinstance(parent := parents.get(target), (ast.List, ast.Tuple, ast.Starred)):
        target = parent
    if isinstance(parent, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
        # Assignment evaluates its value before replacing the target binding.
        return parent.end_lineno or parent.lineno, parent.end_col_offset or parent.col_offset
    return node.lineno, node.col_offset


def _binding_may_be_skipped(node: ast.AST, parents: dict[ast.AST, ast.AST], boundary: _Loop | None = None) -> bool:
    conditional = (
        ast.If,
        ast.IfExp,
        ast.BoolOp,
        ast.For,
        ast.AsyncFor,
        ast.While,
        ast.Try,
        ast.TryStar,
        ast.Match,
        ast.With,
        ast.AsyncWith,
    )
    while (parent := parents.get(node)) is not None:
        if parent is boundary or isinstance(parent, _LexicalScope):
            break
        if isinstance(parent, conditional):
            return True
        node = parent
    return False


def _enclosing_loops(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> Iterator[_Loop]:
    while (parent := parents.get(node)) is not None and not isinstance(parent, _LexicalScope):
        if isinstance(parent, _Loop) and (
            node in parent.body or (isinstance(parent, ast.While) and node is parent.test)
        ):
            yield parent
        node = parent


def _assignment_rhs(target: ast.expr, parents: dict[ast.AST, ast.AST]) -> ast.expr | None:
    container = parents.get(target)
    if isinstance(container, (ast.Assign, ast.AnnAssign, ast.NamedExpr)):
        return container.value
    if not isinstance(container, (ast.List, ast.Tuple)):
        return None
    values = _assignment_rhs(container, parents)
    if not isinstance(values, (ast.List, ast.Tuple)) or len(container.elts) != len(values.elts):
        return None
    if any(isinstance(item, ast.Starred) for item in (*container.elts, *values.elts)):
        return None
    return values.elts[container.elts.index(target)]


def _callable_aliases(value: ast.expr) -> Iterator[str]:
    if isinstance(value, ast.IfExp):
        if isinstance(value.test, ast.Constant):
            yield from _callable_aliases(value.body if value.test.value else value.orelse)
        else:
            yield from _callable_aliases(value.body)
            yield from _callable_aliases(value.orelse)
        return
    if name := qualified_name(value, {}):
        yield name


def _assigned_callable(node: ast.Name, parents: dict[ast.AST, ast.AST]) -> bool | tuple[str, ...] | None:
    assignment = parents.get(node)
    if isinstance(assignment, ast.AnnAssign) and assignment.value is None:
        # A bare annotation declares a local name and leaves its current value alone.
        return None
    value = _assignment_rhs(node, parents)
    return False if value is None else tuple(_callable_aliases(value)) or False


def _scope_callable_bindings(
    nodes: Sequence[ast.AST], parents: dict[ast.AST, ast.AST]
) -> dict[_LexicalScope, list[_CallableBinding]]:
    definitions: dict[_LexicalScope, list[_CallableBinding]] = {}
    for node in nodes:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            position = (node.lineno, node.col_offset)
            name, value = node.name, isinstance(node, ast.AsyncFunctionDef)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            position = _store_position(node, parents)
            name, value = node.id, _assigned_callable(node, parents)
        else:
            continue
        owner = _enclosing_scope(node, parents)
        if owner is not None:
            binding = _CallableBinding(position, name, value, _binding_may_be_skipped(node, parents), node)
            definitions.setdefault(owner, []).append(binding)
    for bindings in definitions.values():
        bindings.sort(key=lambda binding: binding.position)
    return definitions


def _binds_coroutine(binding: _CallableBinding, coroutines: set[str]) -> bool:
    return binding.value is True or (
        isinstance(binding.value, tuple) and any(name in coroutines for name in binding.value)
    )


def _binding_groups(bindings: Sequence[_CallableBinding]) -> Iterator[tuple[_CallableBinding, ...]]:
    return (tuple(group) for _, group in groupby(bindings, key=lambda binding: binding.position))


def _resolved_bindings(group: Sequence[_CallableBinding], coroutines: set[str]) -> list[tuple[_CallableBinding, bool]]:
    # Unpacking reads every right-hand value before storing any of the targets.
    return [(binding, _binds_coroutine(binding, coroutines)) for binding in group]


def _apply_callable_binding(binding: _CallableBinding, coroutines: set[str], is_coroutine: bool) -> None:
    if is_coroutine:
        coroutines.add(binding.name)
    elif binding.value is not None and not binding.may_skip:
        coroutines.discard(binding.name)


def _synchronous_loop_targets(nodes: Sequence[ast.AST]) -> dict[_Loop, dict[str, bool]]:
    # Only infer a synchronous target when every iterable item is a literal lambda.
    return {
        node: {node.target.id: False}
        for node in nodes
        if isinstance(node, ast.For)
        and isinstance(node.target, ast.Name)
        and isinstance(node.iter, (ast.List, ast.Tuple))
        and all(isinstance(item, ast.Lambda) for item in node.iter.elts)
    }


def _iteration_coroutines(
    coroutines: set[str],
    loops: Sequence[_Loop],
    overrides: dict[_Loop, dict[str, bool]],
    carried: dict[_Loop, set[str]],
) -> set[str]:
    if not loops:
        return coroutines
    visible = coroutines.copy()
    for loop in reversed(loops):
        # A loop target resets its own iteration. Inner loops then contribute their bindings.
        visible.update(carried.get(loop, ()))
        for name, is_coroutine in overrides.get(loop, {}).items():
            if is_coroutine:
                visible.add(name)
            else:
                visible.discard(name)
    return visible


def _update_iteration_bindings(
    binding: _CallableBinding,
    loops: Sequence[_Loop],
    overrides: dict[_Loop, dict[str, bool]],
    parents: dict[ast.AST, ast.AST],
    is_coroutine: bool,
) -> None:
    if binding.value is None:
        return
    for loop in loops:
        if is_coroutine or not _binding_may_be_skipped(binding.node, parents, loop):
            overrides.setdefault(loop, {})[binding.name] = is_coroutine


def _apply_iteration_bindings(
    group: tuple[_CallableBinding, ...],
    coroutines: set[str],
    overrides: dict[_Loop, dict[str, bool]],
    parents: dict[ast.AST, ast.AST],
    carried: dict[_Loop, set[str]],
) -> None:
    loops = tuple(_enclosing_loops(group[0].node, parents))
    visible = _iteration_coroutines(coroutines, loops, overrides, carried)
    for binding, is_coroutine in _resolved_bindings(group, visible):
        _apply_callable_binding(binding, coroutines, is_coroutine)
        _update_iteration_bindings(binding, loops, overrides, parents, is_coroutine)


def _body_exit(statements: Sequence[ast.stmt]) -> ast.stmt | None:
    for statement in statements:
        if isinstance(statement, (ast.Break, ast.Continue, ast.Raise, ast.Return)):
            return statement
        if isinstance(statement, ast.If) and _body_exit(statement.body) and _body_exit(statement.orelse):
            return statement
    return None


def _can_repeat(loop: _Loop) -> bool:
    if isinstance(loop, ast.For) and isinstance(loop.iter, (ast.List, ast.Tuple)):
        items = loop.iter.elts
        return len(items) > 1 or any(isinstance(item, ast.Starred) for item in items)
    return True


def _loop_carry_events(
    groups: Sequence[tuple[_CallableBinding, ...]],
    nodes: Sequence[ast.AST],
    parents: dict[ast.AST, ast.AST],
    exits: dict[_Loop, ast.stmt | None],
) -> list[tuple[_CallableBinding, ...] | _Loop]:
    events: list[tuple[tuple[int, int], tuple[_CallableBinding, ...] | _Loop]] = [
        (group[0].position, group) for group in groups
    ]
    for node in nodes:
        if not isinstance(node, ast.Continue):
            continue
        loop = next(_enclosing_loops(node, parents), None)
        if loop is None or loop not in exits:
            continue
        end = exits[loop]
        if end is None or node.lineno <= (end.end_lineno or end.lineno):
            events.append(((node.lineno, node.col_offset), loop))
    return [event for _, event in sorted(events, key=lambda entry: entry[0])]


def _carry_live_bindings(carried: dict[_Loop, set[str]], loop: _Loop, bindings: dict[str, bool]) -> None:
    carried.setdefault(loop, set()).update(name for name, is_coroutine in bindings.items() if is_coroutine)


def _loop_binding_names(
    groups: Sequence[tuple[_CallableBinding, ...]],
    nodes: Sequence[ast.AST],
    coroutines: set[str],
    targets: dict[_Loop, dict[str, bool]],
    parents: dict[ast.AST, ast.AST],
) -> dict[_Loop, set[str]]:
    carried: dict[_Loop, set[str]] = {}
    exits = {node: _body_exit(node.body) for node in nodes if isinstance(node, _Loop) and _can_repeat(node)}
    events = _loop_carry_events(groups, nodes, parents, exits)
    # Only names that may reach a backedge carry. Chained aliases can take
    # multiple passes, and each continuing pass adds a name to a finite set.
    while True:
        prior_count = sum(map(len, carried.values()))
        visible = coroutines.copy()
        overrides = {loop: bindings.copy() for loop, bindings in targets.items()}
        for event in events:
            if isinstance(event, tuple):
                _apply_iteration_bindings(event, visible, overrides, parents, carried)
            else:
                _carry_live_bindings(carried, event, overrides.get(event, {}))
        for loop, end in exits.items():
            if end is None:
                _carry_live_bindings(carried, loop, overrides.get(loop, {}))
        if sum(map(len, carried.values())) == prior_count:
            return carried


def _calls_with_coroutines(
    nodes: Sequence[ast.AST],
    parents: dict[ast.AST, ast.AST],
    coroutines: set[str],
    bindings: Sequence[_CallableBinding],
) -> Iterator[tuple[ast.Call, set[str]]]:
    groups = tuple(_binding_groups(bindings))
    targets = _synchronous_loop_targets(nodes)
    carried = (
        _loop_binding_names(groups, nodes, coroutines, targets, parents)
        if any(isinstance(node, _Loop) for node in nodes)
        else {}
    )
    events = iter(groups)
    event = next(events, None)
    calls = sorted(
        (node for node in nodes if isinstance(node, ast.Call)), key=lambda node: (node.lineno, node.col_offset)
    )
    for call in calls:
        position = (call.lineno, call.col_offset)
        while event is not None and event[0].position <= position:
            _apply_iteration_bindings(event, coroutines, targets, parents, carried)
            event = next(events, None)
        loops = tuple(_enclosing_loops(call, parents))
        yield call, _iteration_coroutines(coroutines, loops, targets, carried)


def _binding_flags(
    bindings: Sequence[_CallableBinding],
    definition_position: tuple[int, int] | None = None,
    inherited: set[str] | None = None,
) -> dict[str, bool]:
    coroutines = set(inherited or ())
    for group in _binding_groups(bindings):
        resolved = _resolved_bindings(group, coroutines)
        if definition_position is None or group[0].position < definition_position:
            for binding, is_coroutine in resolved:
                _apply_callable_binding(binding, coroutines, is_coroutine)
        else:
            # An enclosing scope can rebind the name after the function runs.
            coroutines.update(binding.name for binding, is_coroutine in resolved if is_coroutine)
    return {binding.name: binding.name in coroutines for binding in bindings}


def _method_coroutines(
    scope: ast.AsyncFunctionDef, owner: _LexicalScope | None, definitions: dict[_LexicalScope, list[_CallableBinding]]
) -> set[str]:
    arguments = scope.args.posonlyargs + scope.args.args
    if not isinstance(owner, ast.ClassDef) or not arguments:
        return set()
    if any(qualified_name(node, {}).rsplit(".", 1)[-1] == "staticmethod" for node in scope.decorator_list):
        return set()
    receiver = arguments[0].arg
    return {f"{receiver}.{name}" for name, is_async in _binding_flags(definitions.get(owner, ())).items() if is_async}


def _enclosing_scopes(scope: _LexicalScope, parents: dict[ast.AST, ast.AST]) -> Iterator[_LexicalScope]:
    owner = _enclosing_scope(scope, parents)
    while owner is not None:
        yield owner
        owner = _enclosing_scope(owner, parents)


def _outer_declarations(scope: _LexicalScope) -> tuple[set[str], set[str]]:
    global_names: set[str] = set()
    nonlocal_names: set[str] = set()
    for node in _scoped_nodes(scope):
        if isinstance(node, ast.Global):
            global_names.update(node.names)
        elif isinstance(node, ast.Nonlocal):
            nonlocal_names.update(node.names)
    return global_names, global_names | nonlocal_names


def _apply_enclosing_bindings(
    scope: _LexicalScope,
    bindings: Sequence[_CallableBinding],
    position: tuple[int, int],
    visible: dict[str, bool],
    module_flags: dict[str, bool],
) -> None:
    global_names, redirected = _outer_declarations(scope)
    local_names = {binding.name for binding in bindings} - redirected
    inherited = {name for name, is_async in visible.items() if is_async} - local_names - global_names
    inherited.update(name for name in global_names if module_flags.get(name))
    flags = _binding_flags(bindings, position, inherited)
    module_flags.update({name: flags[name] for name in global_names & flags.keys()})
    visible.update(flags)
    visible.update({name: module_flags.get(name, False) for name in global_names})


def _enclosing_callable_flags(
    scope: ast.AsyncFunctionDef,
    parents: dict[ast.AST, ast.AST],
    definitions: dict[_LexicalScope, list[_CallableBinding]],
    global_names: set[str],
) -> dict[str, bool]:
    visible: dict[str, bool] = {}
    module_flags: dict[str, bool] = {}
    position = scope.lineno, scope.col_offset
    for owner in reversed(tuple(_enclosing_scopes(scope, parents))):
        bindings = definitions.get(owner, ())
        if isinstance(owner, ast.Module):
            module_flags = _binding_flags(bindings, position)
            visible.update(module_flags)
        elif not isinstance(owner, ast.ClassDef):
            _apply_enclosing_bindings(owner, bindings, position, visible, module_flags)
    visible.update({name: module_flags.get(name, False) for name in global_names})
    return visible


def _visible_coroutines(
    scope: ast.AsyncFunctionDef,
    parents: dict[ast.AST, ast.AST],
    definitions: dict[_LexicalScope, list[_CallableBinding]],
) -> set[str]:
    owner = _enclosing_scope(scope, parents)
    # A locally declared name shadows the outer name throughout the function.
    # Its callable type then changes at each statement that binds it.
    global_names, outer_names = _outer_declarations(scope)
    visible = {binding.name for binding in definitions.get(scope, ())} - outer_names
    visible.update(arg.arg for arg in scope.args.posonlyargs + scope.args.args + scope.args.kwonlyargs)
    result = _method_coroutines(scope, owner, definitions)
    inherited = _enclosing_callable_flags(scope, parents, definitions, global_names)
    return result | {name for name, is_async in inherited.items() if is_async and name not in visible}


def async_findings(tree: ast.Module, filename: str) -> list[AsyncFinding]:
    """Check each async function and attribute findings to source positions."""
    aliases = import_aliases(tree.body)
    nodes = list(ast.walk(tree))
    parents = {child: node for node in nodes for child in ast.iter_child_nodes(node)}
    definitions = _scope_callable_bindings(nodes, parents)
    findings: set[AsyncFinding] = set()
    for scope in (node for node in nodes if isinstance(node, ast.AsyncFunctionDef)):
        coroutines = _visible_coroutines(scope, parents, definitions)
        for rule, node in _scope_findings(scope, aliases, coroutines, definitions.get(scope, ())):
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

#!/usr/bin/env python3
"""Ensure VS Code settings JSON I/O for init/ide flows uses project_artifact_write (regression gate)."""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import NamedTuple

from beartype import beartype
from icontract import ensure, require


ROOT = Path(__file__).resolve().parent.parent
IDE_SETUP = ROOT / "src" / "specfact_cli" / "utils" / "ide_setup.py"

_JSON_IO_NAMES = frozenset({"load", "dump", "loads", "dumps"})


def _write_stderr(message: str) -> None:
    sys.stderr.write(message + "\n")


def _repo_layout_ok() -> bool:
    return ROOT.is_dir()


def _register_json_module_alias(alias: ast.alias, module_locals: set[str]) -> None:
    if alias.name != "json":
        return
    module_locals.add(alias.asname or "json")


def _register_json_from_func_alias(alias: ast.alias, func_aliases: dict[str, str]) -> None:
    if alias.name == "*":
        for name in sorted(_JSON_IO_NAMES):
            func_aliases[name] = f"json.{name}"
        return
    if alias.name not in _JSON_IO_NAMES:
        return
    local = alias.asname or alias.name
    func_aliases[local] = f"json.{alias.name}"


def _defers_annotations(node: ast.Module) -> bool:
    """Return whether PEP 563 leaves this module's annotations unevaluated."""
    return any(
        isinstance(stmt, ast.ImportFrom)
        and stmt.module == "__future__"
        and any(alias.name == "annotations" for alias in stmt.names)
        for stmt in node.body
    )


def _argument_slots(args: ast.arguments) -> tuple[ast.arg, ...]:
    named = (*args.posonlyargs, *args.args, *args.kwonlyargs)
    variadic = tuple(slot for slot in (args.vararg, args.kwarg) if slot is not None)
    return (*named, *variadic)


class _Scope(NamedTuple):
    """One name-binding frame; a class body is invisible to the scopes nested in it."""

    is_class_body: bool
    names: set[str]


class _JsonIOShadowVisitor(ast.NodeVisitor):
    """Track json import aliases and whether call targets were shadowed by assignment."""

    def __init__(self) -> None:
        self.func_aliases: dict[str, str] = {}
        self.module_locals: set[str] = set()
        self.scope_stack: list[_Scope] = [_Scope(is_class_body=False, names=set())]
        self.annotations_evaluated = True
        self.offenders: list[tuple[int, str]] = []

    def _visible_shadowed(self) -> set[str]:
        innermost, *enclosing = reversed(self.scope_stack)
        merged = set(innermost.names)
        for scope in enclosing:
            if not scope.is_class_body:
                merged |= scope.names
        return merged

    def _note_shadow(self, name: str) -> None:
        if name in self.func_aliases or name in self.module_locals:
            self.scope_stack[-1].names.add(name)

    def _note_optional_vars(self, node: ast.AST) -> None:
        if isinstance(node, ast.Name):
            self._note_shadow(node.id)
            return
        for elt in ast.walk(node):
            if isinstance(elt, ast.Name):
                self._note_shadow(elt.id)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            _register_json_module_alias(alias, self.module_locals)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module == "json":
            for alias in node.names:
                _register_json_from_func_alias(alias, self.func_aliases)

    def visit_Assign(self, node: ast.Assign) -> None:
        self.visit(node.value)
        for tgt in node.targets:
            if isinstance(tgt, ast.Name):
                self._note_shadow(tgt.id)
            elif isinstance(tgt, (ast.Tuple, ast.List)):
                for elt in ast.walk(tgt):
                    if isinstance(elt, ast.Name):
                        self._note_shadow(elt.id)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if self.annotations_evaluated:
            self.visit(node.annotation)
        if node.value is not None:
            self.visit(node.value)
        if isinstance(node.target, ast.Name):
            self._note_shadow(node.target.id)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        self.visit(node.value)
        if isinstance(node.target, ast.Name):
            self._note_shadow(node.target.id)

    def _visit_for_like(self, node: ast.For | ast.AsyncFor) -> None:
        self.visit(node.iter)
        if isinstance(node.target, ast.Name):
            self._note_shadow(node.target.id)
        elif isinstance(node.target, (ast.Tuple, ast.List)):
            for elt in ast.walk(node.target):
                if isinstance(elt, ast.Name):
                    self._note_shadow(elt.id)
        for stmt in node.body:
            self.visit(stmt)
        for stmt in node.orelse:
            self.visit(stmt)

    def visit_For(self, node: ast.For) -> None:
        self._visit_for_like(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self._visit_for_like(node)

    def _visit_with_like(self, node: ast.With | ast.AsyncWith) -> None:
        for item in node.items:
            self.visit(item.context_expr)
            if item.optional_vars is not None:
                self._note_optional_vars(item.optional_vars)
        for stmt in node.body:
            self.visit(stmt)

    def visit_With(self, node: ast.With) -> None:
        self._visit_with_like(node)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
        self._visit_with_like(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.type is not None:
            self.visit(node.type)
        name = node.name
        # Python deletes the `as` target when the handler ends, so it only shadows inside the body.
        unbinds = bool(name) and name not in self.scope_stack[-1].names
        if name:
            self._note_shadow(name)
        for stmt in node.body:
            self.visit(stmt)
        if name and unbinds:
            self.scope_stack[-1].names.discard(name)

    def _visit_decorators(self, decorators: list[ast.expr]) -> None:
        for decorator in decorators:
            # A decorator that is not itself a call still invokes the name it references.
            if not isinstance(decorator, ast.Call) and (target := self._json_io_target(decorator)) is not None:
                self.offenders.append((decorator.lineno, target))
            self.visit(decorator)

    def _visit_argument_defaults(self, args: ast.arguments) -> None:
        for default in (*args.defaults, *args.kw_defaults):
            if default is not None:
                self.visit(default)

    def _note_parameters(self, args: ast.arguments) -> None:
        for arg in _argument_slots(args):
            self._note_shadow(arg.arg)

    def visit_FunctionDef(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        # Decorators, defaults, and evaluated annotations run in the enclosing scope, not the body.
        self._visit_decorators(node.decorator_list)
        self._visit_argument_defaults(node.args)
        if self.annotations_evaluated:
            slots = _argument_slots(node.args)
            for annotation in (*(slot.annotation for slot in slots), node.returns):
                if annotation is not None:
                    self.visit(annotation)
        self.scope_stack.append(_Scope(is_class_body=False, names=set()))
        self._note_parameters(node.args)
        for stmt in node.body:
            self.visit(stmt)
        self.scope_stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.visit_FunctionDef(node)  # type: ignore[arg-type]

    def visit_Lambda(self, node: ast.Lambda) -> None:
        self._visit_argument_defaults(node.args)
        self.scope_stack.append(_Scope(is_class_body=False, names=set()))
        self._note_parameters(node.args)
        self.visit(node.body)
        self.scope_stack.pop()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._visit_decorators(node.decorator_list)
        for base in node.bases:
            self.visit(base)
        for keyword in node.keywords:
            self.visit(keyword.value)
        self.scope_stack.append(_Scope(is_class_body=True, names=set()))
        for stmt in node.body:
            self.visit(stmt)
        self.scope_stack.pop()

    def _json_io_target(self, func: ast.expr) -> str | None:
        """Return the canonical json I/O name this expression invokes, if any."""
        shadowed = self._visible_shadowed()
        if isinstance(func, ast.Name) and func.id in self.func_aliases and func.id not in shadowed:
            return self.func_aliases[func.id]
        if (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
            and func.value.id in self.module_locals
            and func.value.id not in shadowed
            and func.attr in _JSON_IO_NAMES
        ):
            return f"json.{func.attr}"
        return None

    def visit_Call(self, node: ast.Call) -> None:
        target = self._json_io_target(node.func)
        if target is not None:
            self.offenders.append((node.lineno, target))
        self.generic_visit(node)

    def visit_Module(self, node: ast.Module) -> None:
        self.annotations_evaluated = not _defers_annotations(node)
        for stmt in node.body:
            self.visit(stmt)


def _collect_json_io_offenders(tree: ast.AST) -> list[tuple[int, str]]:
    visitor = _JsonIOShadowVisitor()
    visitor.visit(tree)
    return visitor.offenders


@beartype
@require(_repo_layout_ok)
@ensure(lambda result: result in (0, 1, 2))
def main() -> int:
    if not IDE_SETUP.is_file():
        _write_stderr(f"Expected ide_setup at {IDE_SETUP}")
        return 2
    try:
        source_text = IDE_SETUP.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        _write_stderr(f"Cannot read ide_setup for static analysis: {exc}")
        return 2
    try:
        tree = ast.parse(source_text, filename=str(IDE_SETUP))
    except SyntaxError as exc:
        _write_stderr(f"ide_setup.py has invalid Python syntax (gate cannot run): {exc}")
        return 1
    offenders = _collect_json_io_offenders(tree)
    if offenders:
        lines = ", ".join(f"line {ln} ({name})" for ln, name in offenders)
        _write_stderr(
            "Unsafe JSON I/O in ide_setup.py — route VS Code settings through "
            f"specfact_cli.utils.project_artifact_write.merge_vscode_settings_prompt_recommendations: {lines}",
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

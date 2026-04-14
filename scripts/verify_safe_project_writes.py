#!/usr/bin/env python3
"""Ensure VS Code settings JSON I/O for init/ide flows uses project_artifact_write (regression gate)."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

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


class _JsonIOShadowVisitor(ast.NodeVisitor):
    """Track json import aliases and whether call targets were shadowed by assignment."""

    def __init__(self) -> None:
        self.func_aliases: dict[str, str] = {}
        self.module_locals: set[str] = set()
        self.shadow_stack: list[set[str]] = [set()]
        self.offenders: list[tuple[int, str]] = []

    def _union_shadowed(self) -> set[str]:
        merged: set[str] = set()
        for frame in self.shadow_stack:
            merged |= frame
        return merged

    def _note_shadow(self, name: str) -> None:
        if name in self.func_aliases or name in self.module_locals:
            self.shadow_stack[-1].add(name)

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
        if node.name:
            self._note_shadow(node.name)
        for stmt in node.body:
            self.visit(stmt)

    def visit_FunctionDef(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        self.shadow_stack.append(set())
        for arg in (*getattr(node.args, "posonlyargs", ()), *node.args.args, *node.args.kwonlyargs):
            self._note_shadow(arg.arg)
        if node.args.vararg:
            self._note_shadow(node.args.vararg.arg)
        if node.args.kwarg:
            self._note_shadow(node.args.kwarg.arg)
        for stmt in node.body:
            self.visit(stmt)
        self.shadow_stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.visit_FunctionDef(node)  # type: ignore[arg-type]

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.shadow_stack.append(set())
        for stmt in node.body:
            self.visit(stmt)
        self.shadow_stack.pop()

    def visit_Call(self, node: ast.Call) -> None:
        shadowed = self._union_shadowed()
        func = node.func
        if isinstance(func, ast.Name) and func.id in self.func_aliases and func.id not in shadowed:
            self.offenders.append((node.lineno, self.func_aliases[func.id]))
        elif (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
            and func.value.id in self.module_locals
            and func.value.id not in shadowed
            and func.attr in _JSON_IO_NAMES
        ):
            self.offenders.append((node.lineno, f"json.{func.attr}"))
        self.generic_visit(node)

    def visit_Module(self, node: ast.Module) -> None:
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

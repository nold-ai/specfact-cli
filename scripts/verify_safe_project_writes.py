#!/usr/bin/env python3
"""Ensure VS Code settings JSON I/O for init/ide flows uses project_artifact_write (regression gate)."""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Any

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


def _json_bindings(tree: ast.AST) -> tuple[dict[str, str], frozenset[str]]:
    """``from json import`` function aliases (local name -> ``json.attr``) and ``import json`` module locals."""
    func_aliases: dict[str, str] = {}
    module_locals: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                _register_json_module_alias(alias, module_locals)
            continue
        if isinstance(node, ast.ImportFrom) and node.module == "json":
            for alias in node.names:
                _register_json_from_func_alias(alias, func_aliases)
    return func_aliases, frozenset(module_locals)


def _add_shadows_from_target(
    target: ast.AST,
    func_aliases: dict[str, str],
    module_locals: frozenset[str],
    shadow_func: set[str],
    shadow_mod: set[str],
) -> None:
    if isinstance(target, ast.Name):
        if target.id in func_aliases:
            shadow_func.add(target.id)
        if target.id in module_locals:
            shadow_mod.add(target.id)
    elif isinstance(target, (ast.Tuple, ast.List)):
        for elt in target.elts:
            _add_shadows_from_target(elt, func_aliases, module_locals, shadow_func, shadow_mod)


def _collect_json_io_offenders(tree: ast.AST) -> list[tuple[int, str]]:
    func_aliases, module_locals = _json_bindings(tree)
    offenders: list[tuple[int, str]] = []

    class _Visitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.shadow_func: set[str] = set()
            self.shadow_mod: set[str] = set()

        def _push_scope(self) -> tuple[set[str], set[str]]:
            return (set(self.shadow_func), set(self.shadow_mod))

        def _pop_scope(self, saved: tuple[set[str], set[str]]) -> None:
            self.shadow_func, self.shadow_mod = saved

        def _shadow_arguments(self, args: ast.arguments) -> None:
            for a in list(args.posonlyargs) + list(args.args) + list(args.kwonlyargs):
                _add_shadows_from_target(
                    ast.Name(id=a.arg, ctx=ast.Store()),
                    func_aliases,
                    module_locals,
                    self.shadow_func,
                    self.shadow_mod,
                )
            if args.vararg:
                _add_shadows_from_target(
                    ast.Name(id=args.vararg.arg, ctx=ast.Store()),
                    func_aliases,
                    module_locals,
                    self.shadow_func,
                    self.shadow_mod,
                )
            if args.kwarg:
                _add_shadows_from_target(
                    ast.Name(id=args.kwarg.arg, ctx=ast.Store()),
                    func_aliases,
                    module_locals,
                    self.shadow_func,
                    self.shadow_mod,
                )

        def _visit_function_body(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
            for d in node.decorator_list:
                self.visit(d)
            saved = self._push_scope()
            self._shadow_arguments(node.args)
            for child in node.body:
                self.visit(child)
            self._pop_scope(saved)

        def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
            self._visit_function_body(node)
            return None

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> Any:
            self._visit_function_body(node)
            return None

        def visit_ClassDef(self, node: ast.ClassDef) -> Any:
            for d in node.decorator_list:
                self.visit(d)
            for b in node.bases:
                self.visit(b)
            for k in node.keywords:
                self.visit(k.value)
            saved = self._push_scope()
            for child in node.body:
                self.visit(child)
            self._pop_scope(saved)
            return None

        def visit_Assign(self, node: ast.Assign) -> Any:
            self.visit(node.value)
            for t in node.targets:
                self.visit(t)
                _add_shadows_from_target(t, func_aliases, module_locals, self.shadow_func, self.shadow_mod)
            return None

        def visit_AnnAssign(self, node: ast.AnnAssign) -> Any:
            self.visit(node.annotation)
            if node.value is not None:
                self.visit(node.value)
            if node.target is not None:
                self.visit(node.target)
                _add_shadows_from_target(node.target, func_aliases, module_locals, self.shadow_func, self.shadow_mod)
            return None

        def visit_AugAssign(self, node: ast.AugAssign) -> Any:
            self.visit(node.value)
            self.visit(node.target)
            _add_shadows_from_target(node.target, func_aliases, module_locals, self.shadow_func, self.shadow_mod)
            return None

        def visit_NamedExpr(self, node: ast.NamedExpr) -> Any:
            self.visit(node.value)
            self.visit(node.target)
            _add_shadows_from_target(node.target, func_aliases, module_locals, self.shadow_func, self.shadow_mod)
            return None

        def visit_For(self, node: ast.For) -> Any:
            self.visit(node.iter)
            self.visit(node.target)
            _add_shadows_from_target(node.target, func_aliases, module_locals, self.shadow_func, self.shadow_mod)
            for stmt in node.body:
                self.visit(stmt)
            for stmt in node.orelse:
                self.visit(stmt)
            return None

        def visit_AsyncFor(self, node: ast.AsyncFor) -> Any:
            return self.visit_For(node)  # type: ignore[arg-type]

        def visit_With(self, node: ast.With) -> Any:
            for item in node.items:
                self.visit(item.context_expr)
                if item.optional_vars is not None:
                    self.visit(item.optional_vars)
                    _add_shadows_from_target(
                        item.optional_vars,
                        func_aliases,
                        module_locals,
                        self.shadow_func,
                        self.shadow_mod,
                    )
            for stmt in node.body:
                self.visit(stmt)
            return None

        def visit_AsyncWith(self, node: ast.AsyncWith) -> Any:
            return self.visit_With(node)  # type: ignore[arg-type]

        def visit_ExceptHandler(self, node: ast.ExceptHandler) -> Any:
            if node.type is not None:
                self.visit(node.type)
            if node.name:
                _add_shadows_from_target(
                    ast.Name(id=node.name, ctx=ast.Store()),
                    func_aliases,
                    module_locals,
                    self.shadow_func,
                    self.shadow_mod,
                )
            for stmt in node.body:
                self.visit(stmt)
            return None

        def _visit_comprehensions_then_elt(
            self,
            generators: list[ast.comprehension],
            visit_elt: Any | None = None,
        ) -> None:
            saved = self._push_scope()
            for gen in generators:
                self.visit(gen.iter)
                self.visit(gen.target)
                _add_shadows_from_target(gen.target, func_aliases, module_locals, self.shadow_func, self.shadow_mod)
                for if_clause in gen.ifs:
                    self.visit(if_clause)
            if visit_elt is not None:
                visit_elt()
            self._pop_scope(saved)

        def visit_ListComp(self, node: ast.ListComp) -> Any:
            self._visit_comprehensions_then_elt(node.generators, lambda: self.visit(node.elt))
            return None

        def visit_SetComp(self, node: ast.SetComp) -> Any:
            self._visit_comprehensions_then_elt(node.generators, lambda: self.visit(node.elt))
            return None

        def visit_GeneratorExp(self, node: ast.GeneratorExp) -> Any:
            self._visit_comprehensions_then_elt(node.generators, lambda: self.visit(node.elt))
            return None

        def visit_DictComp(self, node: ast.DictComp) -> Any:
            def visit_kv() -> None:
                self.visit(node.key)
                self.visit(node.value)

            self._visit_comprehensions_then_elt(node.generators, visit_kv)
            return None

        def visit_Call(self, node: ast.Call) -> Any:
            func = node.func
            if isinstance(func, ast.Name) and func.id in func_aliases and func.id not in self.shadow_func:
                offenders.append((node.lineno, func_aliases[func.id]))
            elif (
                isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id in module_locals
                and func.value.id not in self.shadow_mod
                and func.attr in _JSON_IO_NAMES
            ):
                offenders.append((node.lineno, f"json.{func.attr}"))
            self.visit(func)
            for arg in node.args:
                self.visit(arg)
            for kw in node.keywords:
                self.visit(kw.value)
            return None

    _Visitor().visit(tree)
    return offenders


@beartype
@require(_repo_layout_ok)
@ensure(lambda result: result in (0, 1, 2))
def main() -> int:
    if not IDE_SETUP.is_file():
        _write_stderr(f"Expected ide_setup at {IDE_SETUP}")
        return 2
    try:
        source = IDE_SETUP.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(IDE_SETUP))
    except (OSError, UnicodeDecodeError, SyntaxError) as exc:
        _write_stderr(f"Unable to analyze {IDE_SETUP}: {exc}")
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

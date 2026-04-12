#!/usr/bin/env python3
"""Ensure VS Code settings JSON I/O for init/ide flows uses project_artifact_write (regression gate)."""

from __future__ import annotations

import ast
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
IDE_SETUP = ROOT / "src" / "specfact_cli" / "utils" / "ide_setup.py"


class _JsonIoVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.offenders: list[tuple[int, str]] = []

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        if (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
            and func.value.id == "json"
            and func.attr in {"load", "dump", "loads", "dumps"}
        ):
            self.offenders.append((node.lineno, f"json.{func.attr}"))
        self.generic_visit(node)


def main() -> int:
    if not IDE_SETUP.is_file():
        print(f"Expected ide_setup at {IDE_SETUP}", file=sys.stderr)
        return 2
    tree = ast.parse(IDE_SETUP.read_text(encoding="utf-8"), filename=str(IDE_SETUP))
    visitor = _JsonIoVisitor()
    visitor.visit(tree)
    if visitor.offenders:
        lines = ", ".join(f"line {ln} ({name})" for ln, name in visitor.offenders)
        print(
            "Unsafe JSON I/O in ide_setup.py — route VS Code settings through "
            f"specfact_cli.utils.project_artifact_write.merge_vscode_settings_prompt_recommendations: {lines}",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

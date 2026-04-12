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


def _repo_layout_ok() -> bool:
    return ROOT.is_dir()


def _json_import_aliases(tree: ast.AST) -> dict[str, str]:
    """Map local function names to labels like ``json.loads`` for ``from json import ...``."""
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom) or node.module != "json":
            continue
        for alias in node.names:
            if alias.name in _JSON_IO_NAMES:
                local = alias.asname or alias.name
                aliases[local] = f"json.{alias.name}"
    return aliases


def _collect_json_io_offenders(tree: ast.AST) -> list[tuple[int, str]]:
    import_aliases = _json_import_aliases(tree)
    offenders: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id in import_aliases:
            offenders.append((node.lineno, import_aliases[func.id]))
            continue
        if (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
            and func.value.id == "json"
            and func.attr in _JSON_IO_NAMES
        ):
            offenders.append((node.lineno, f"json.{func.attr}"))
    return offenders


@beartype
@require(_repo_layout_ok)
@ensure(lambda result: result in (0, 1, 2))
def main() -> int:
    if not IDE_SETUP.is_file():
        print(f"Expected ide_setup at {IDE_SETUP}", file=sys.stderr)
        return 2
    tree = ast.parse(IDE_SETUP.read_text(encoding="utf-8"), filename=str(IDE_SETUP))
    offenders = _collect_json_io_offenders(tree)
    if offenders:
        lines = ", ".join(f"line {ln} ({name})" for ln, name in offenders)
        print(
            "Unsafe JSON I/O in ide_setup.py — route VS Code settings through "
            f"specfact_cli.utils.project_artifact_write.merge_vscode_settings_prompt_recommendations: {lines}",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

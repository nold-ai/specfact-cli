"""Tests for scripts/verify_safe_project_writes.py."""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path


def _load_verify_module() -> object:
    root = Path(__file__).resolve().parents[3]
    path = root / "scripts" / "verify_safe_project_writes.py"
    spec = importlib.util.spec_from_file_location("_verify_safe_project_writes", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_collect_json_io_flags_from_json_import_loads() -> None:
    mod = _load_verify_module()
    tree = ast.parse('from json import loads\nloads("{}")')
    offenders = mod._collect_json_io_offenders(tree)
    assert offenders
    assert any(name == "json.loads" for _, name in offenders)


def test_collect_json_io_flags_aliased_json_import() -> None:
    mod = _load_verify_module()
    tree = ast.parse('from json import dump as dumper\nx = None\ndumper(x, open("f","w"))')
    offenders = mod._collect_json_io_offenders(tree)
    assert any(name == "json.dump" for _, name in offenders)


def test_collect_json_io_flags_import_json_as_module_alias() -> None:
    mod = _load_verify_module()
    tree = ast.parse('import json as js\nx = None\njs.dump(x, open("f","w"))')
    offenders = mod._collect_json_io_offenders(tree)
    assert any(name == "json.dump" for _, name in offenders)


def test_collect_json_io_flags_from_json_star_import() -> None:
    mod = _load_verify_module()
    tree = ast.parse('from json import *\nx = None\ndump(x, open("f","w"))')
    offenders = mod._collect_json_io_offenders(tree)
    assert any(name == "json.dump" for _, name in offenders)


def test_collect_json_io_ignores_shadowed_json_dump_alias() -> None:
    mod = _load_verify_module()
    tree = ast.parse('from json import dump as dumper\ndumper = 1\ndef f():\n    dumper(1, open("f","w"))\n')
    offenders = mod._collect_json_io_offenders(tree)
    assert not any(name == "json.dump" for _, name in offenders)

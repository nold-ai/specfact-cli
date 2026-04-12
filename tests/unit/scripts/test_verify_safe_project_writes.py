"""Tests for scripts/verify_safe_project_writes.py."""

from __future__ import annotations

import ast
import importlib.util
import subprocess
import sys
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


def test_verify_safe_project_writes_passes_on_repo() -> None:
    """Gate must succeed while ide_setup routes settings through project_artifact_write."""
    script = Path(__file__).resolve().parents[3] / "scripts" / "verify_safe_project_writes.py"
    completed = subprocess.run(
        [sys.executable, str(script)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr

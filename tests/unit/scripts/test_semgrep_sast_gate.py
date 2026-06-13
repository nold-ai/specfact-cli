"""Tests for the Semgrep SAST baseline gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


def _load_gate_module() -> ModuleType:
    script = Path(__file__).resolve().parents[3] / "scripts" / "semgrep_sast_gate.py"
    spec = importlib.util.spec_from_file_location("semgrep_sast_gate", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GATE: Any = _load_gate_module()


def test_load_results_fails_closed_on_non_object_result(tmp_path: Path) -> None:
    """Malformed Semgrep result entries must not be silently dropped."""
    results = tmp_path / "semgrep.json"
    results.write_text(json.dumps({"results": ["not-an-object"]}), encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        GATE._load_results(results)

    assert "results[0] must be an object" in str(exc_info.value)


def test_load_results_fails_closed_on_missing_required_fields(tmp_path: Path) -> None:
    """Missing Semgrep identity fields must fail the gate."""
    results = tmp_path / "semgrep.json"
    results.write_text(json.dumps({"results": [{"check_id": "rule", "path": "file.py"}]}), encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        GATE._load_results(results)

    assert "missing integer start.line" in str(exc_info.value)

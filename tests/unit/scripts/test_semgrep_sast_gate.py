"""Tests for the Semgrep SAST baseline gate."""

from __future__ import annotations

import ast
import importlib.util
import json
import subprocess
import sys
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


def test_weak_hash_scan_preserves_security_findings_and_git_object_ids(tmp_path: Path) -> None:
    expressions = {
        "git_object": "hashlib.sha1(data, usedforsecurity=False)",
        "sha1_default": "hashlib.sha1(data)",
        "sha1_security": "hashlib.sha1(data, usedforsecurity=True)",
        "sha1_dynamic": "hashlib.sha1(data, usedforsecurity=flag)",
        "md5_default": "hashlib.md5(data)",
        "md5_nonsecurity": "hashlib.md5(data, usedforsecurity=False)",
        "strong_hash": "hashlib.sha256(data)",
    }
    source = "import hashlib\n" + "".join(
        f"def {name}(data, flag=True):\n    return {expression}\n" for name, expression in expressions.items()
    )
    fixture = tmp_path / "hash_usage.py"
    fixture.write_text(source, encoding="utf-8")
    rule = Path(__file__).resolve().parents[3] / "tools/semgrep/sast.yml"
    result = subprocess.run(
        [
            str(Path(sys.executable).with_name("semgrep")),
            "scan",
            "--config",
            str(rule),
            "--json",
            "--metrics=off",
            "--disable-version-check",
            "--no-git-ignore",
            str(fixture),
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    findings = json.loads(result.stdout)["results"]
    functions = [node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef)]
    flagged = {
        function.name
        for finding in findings
        if finding["check_id"].endswith("weak-cryptographic-hash")
        for function in functions
        if function.lineno <= finding["start"]["line"] <= function.end_lineno
    }
    assert flagged == {"sha1_default", "sha1_security", "sha1_dynamic", "md5_default", "md5_nonsecurity"}

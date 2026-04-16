"""Unit tests for ``scripts/security_audit_gate.py``."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _load_gate_mod():
    root = Path(__file__).resolve().parents[3]
    path = root / "scripts" / "security_audit_gate.py"
    assert path.is_file(), path
    spec = importlib.util.spec_from_file_location("_security_audit_gate", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def gate_mod():
    return _load_gate_mod()


def test_cvss_for_vuln_reads_numeric_fields(gate_mod) -> None:
    """Nested CVSS-like keys should contribute to the max score."""
    vuln = {"id": "TEST-1", "severity": {"score": 8.2}}
    assert gate_mod._cvss_for_vuln(vuln) == pytest.approx(8.2)


def test_main_passes_when_no_vulnerabilities(gate_mod, capsys) -> None:
    payload = {"dependencies": [{"name": "requests", "version": "2.0.0", "vulns": []}]}
    proc = MagicMock(stdout=json.dumps(payload), stderr="", returncode=0)
    with patch.object(gate_mod.subprocess, "run", return_value=proc):
        assert gate_mod.main() == 0
    assert "passed" in capsys.readouterr().out.lower()


def test_main_warns_when_cvss_below_threshold(gate_mod, capsys) -> None:
    payload = {
        "dependencies": [
            {
                "name": "pillow",
                "version": "1.0.0",
                "vulns": [{"id": "LOW-1", "cvss": 3.0, "description": "low"}],
            }
        ]
    }
    proc = MagicMock(stdout=json.dumps(payload), stderr="", returncode=1)
    with patch.object(gate_mod.subprocess, "run", return_value=proc):
        assert gate_mod.main() == 0
    out = capsys.readouterr().out
    assert "WARNING" in out


def test_main_fails_when_cvss_at_or_above_threshold(gate_mod, capsys) -> None:
    payload = {
        "dependencies": [
            {
                "name": "pillow",
                "version": "1.0.0",
                "vulns": [{"id": "HIGH-1", "cvss": 7.0, "description": "bad"}],
            }
        ]
    }
    proc = MagicMock(stdout=json.dumps(payload), stderr="", returncode=1)
    with patch.object(gate_mod.subprocess, "run", return_value=proc):
        assert gate_mod.main() == 1
    assert "ACTION REQUIRED" in capsys.readouterr().out


def test_main_fail_closed_on_empty_stdout(gate_mod) -> None:
    proc = MagicMock(stdout="", stderr="pip-audit failed\n", returncode=2)
    with patch.object(gate_mod.subprocess, "run", return_value=proc):
        assert gate_mod.main() == 1


def test_main_fail_closed_when_pip_audit_unavailable(gate_mod) -> None:
    with patch.object(gate_mod.subprocess, "run", side_effect=FileNotFoundError("pip-audit not found")):
        assert gate_mod.main() == 1


def test_main_runs_pip_audit_with_skip_editable(gate_mod) -> None:
    payload = {"dependencies": [{"name": "requests", "version": "2.0.0", "vulns": []}]}
    proc = MagicMock(stdout=json.dumps(payload), stderr="", returncode=0)
    with patch.object(gate_mod.subprocess, "run", return_value=proc) as run_mock:
        assert gate_mod.main() == 0
    cmd = run_mock.call_args[0][0]
    assert "--skip-editable" in cmd

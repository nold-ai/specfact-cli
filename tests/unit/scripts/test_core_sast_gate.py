"""Behavior tests for the independent Python SAST command."""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts/core_sast_gate.py"
SOURCE_PATH = "example.py"


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


def _run_gate(
    root: Path, accepted: tuple[tuple[str, str, int], ...] = ()
) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
    baseline = root / "baseline.json"
    baseline.write_text(json.dumps({"version": 1, "accepted_findings": accepted}), encoding="utf-8")
    report = root / "report.json"
    command = [sys.executable, str(SCRIPT), "--root", str(root), "--baseline", str(baseline), "--output", str(report)]
    result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=10)
    assert report.exists(), result.stderr
    return result, json.loads(report.read_text(encoding="utf-8"))


def _tracked_source(root: Path, source: str) -> Path:
    _git(root, "init", "-q")
    path = root / SOURCE_PATH
    path.write_text(source, encoding="utf-8")
    _git(root, "add", SOURCE_PATH)
    return path


def test_independent_workflow_reports_scan_outcome(tmp_path: Path) -> None:
    """Run every fixture under the one Requirements proof selector."""
    cases = [("result = 1\n", 0, "pass"), ("result = eval(text)\n", 1, "findings"), ("def broken(\n", 2, "incomplete")]
    for index, (source, code, status) in enumerate(cases):
        case_root = tmp_path / str(index)
        case_root.mkdir()
        _check_independent_workflow_reports_scan_outcome(case_root, source, code, status)


def _check_independent_workflow_reports_scan_outcome(tmp_path: Path, source: str, code: int, status: str) -> None:
    _tracked_source(tmp_path, source)
    for path in ("scripts/core_sast_gate.py", "ci/core-sast-baseline.json"):
        target = tmp_path / path
        target.parent.mkdir(parents=True)
        target.write_bytes((ROOT / path).read_bytes())

    workflow = yaml.safe_load((ROOT / ".github/workflows/pr-orchestrator.yml").read_text(encoding="utf-8"))
    steps = workflow["jobs"]["independent-static-analysis"]["steps"]
    run = next((step["run"] for step in steps if step.get("id") == "python-sast"), None)
    assert run is not None, "Independent Static Analysis must run the replacement command"
    env = {**os.environ, "PATH": f"{Path(sys.executable).parent}{os.pathsep}{os.environ['PATH']}"}
    result = subprocess.run(
        ["bash", "-eo", "pipefail", "-c", run], cwd=tmp_path, env=env, capture_output=True, text=True, timeout=10
    )
    assert result.returncode == code, result.stderr
    report = json.loads((tmp_path / "logs/static-analysis/python-sast.json").read_text(encoding="utf-8"))
    assert report["status"] == status
    assert report["eligible_paths"] == [SOURCE_PATH]


def test_gate_blocks_new_findings_under_all_existing_rules(tmp_path: Path) -> None:
    """Run every fixture under the one Requirements proof selector."""
    cases = [
        ("value = eval(text)", "unsafe-eval-usage"),
        ("value = exec(text)", "unsafe-eval-usage"),
        ("value = compile(text, label, mode)", "unsafe-eval-usage"),
        ("value = pickle.load(file)", "unsafe-pickle-deserialization"),
        ("value = pickle.loads(raw)", "unsafe-pickle-deserialization"),
        ("value = os.system(command)", "command-injection-risk"),
        ("value = subprocess.run(command, shell=True)", "command-injection-risk"),
        ("value = subprocess.call(command, shell=True)", "command-injection-risk"),
        ("value = subprocess.Popen(command, shell=True)", "command-injection-risk"),
        ("value = hashlib.md5(data, usedforsecurity=False)", "weak-cryptographic-hash"),
        ("value = hashlib.sha1(data)", "weak-cryptographic-hash"),
        ("API_KEY = 'fixture-only'", "hardcoded-secret"),
        ("value = 'password:fixture-only'", "hardcoded-secret"),
        ("value = random.random()", "insecure-random"),
        ("value = random.randint(1, 5)", "insecure-random"),
    ]
    for index, (source, rule) in enumerate(cases):
        case_root = tmp_path / str(index)
        case_root.mkdir()
        _check_gate_blocks_new_findings_under_all_existing_rules(case_root, source, rule)


def _check_gate_blocks_new_findings_under_all_existing_rules(tmp_path: Path, source: str, rule: str) -> None:
    _tracked_source(tmp_path, source + "\n")
    result, report = _run_gate(tmp_path)
    assert result.returncode == 1, result.stderr
    assert report["status"] == "findings"
    assert report["eligible_paths"] == report["scanned_paths"] == [SOURCE_PATH]
    assert [(row["rule_id"], row["path"], row["line"]) for row in report["findings"]] == [(rule, SOURCE_PATH, 1)]
    assert "fixture-only" not in json.dumps(report)


def test_clean_control_and_reviewed_baseline_remain_accepted(tmp_path: Path) -> None:
    _tracked_source(
        tmp_path,
        "import hashlib\n"
        "import subprocess\n"
        "import pickle as serial\n"
        "digest = hashlib.sha1(data, usedforsecurity=False)\n"
        "process = subprocess.run(command, shell=False)\n"
        "value = serial.loads(data)\n",
    )
    result, report = _run_gate(tmp_path, (("tools.semgrep.sast.unsafe-pickle-deserialization", SOURCE_PATH, 6),))
    assert result.returncode == 0, result.stderr
    assert report["status"] == "pass"
    assert report["engine"] == "python-ast"
    assert report["policy"] == "core-python-sast-v1"
    assert len(report["findings"]) == 1
    assert report["new_findings"] == []


def test_legacy_test_directory_scope_is_explicit_in_evidence(tmp_path: Path) -> None:
    _tracked_source(tmp_path, "result = 1\n")
    excluded = ["module/tests/fixture.py", "tests/fixture.py"]
    for relative_path in excluded:
        path = tmp_path / relative_path
        path.parent.mkdir(parents=True)
        path.write_text("fixture = eval(text)\n", encoding="utf-8")
        _git(tmp_path, "add", relative_path)

    result, report = _run_gate(tmp_path)
    assert result.returncode == 0, result.stderr
    assert report["eligible_paths"] == report["scanned_paths"] == [SOURCE_PATH]
    assert report["excluded_test_paths"] == excluded


def test_invalid_baseline_fails_closed(tmp_path: Path) -> None:
    _tracked_source(tmp_path, "result = 1\n")
    result, report = _run_gate(tmp_path, (("unsafe-eval-usage", SOURCE_PATH, True),))
    assert result.returncode == 2, result.stderr
    assert report["status"] == "incomplete"
    assert report["scanned_paths"] == [SOURCE_PATH]
    assert report["diagnostics"][0]["message"] == "invalid or unavailable SAST baseline"


def test_incomplete_inputs_fail_closed(tmp_path: Path) -> None:
    """Run every fixture under the one Requirements proof selector."""
    cases = [("def broken(", "invalid Python"), (None, "unavailable input")]
    for index, (source, diagnostic) in enumerate(cases):
        case_root = tmp_path / str(index)
        case_root.mkdir()
        _check_incomplete_inputs_fail_closed(case_root, source, diagnostic)


def _check_incomplete_inputs_fail_closed(tmp_path: Path, source: str | None, diagnostic: str) -> None:
    tracked = _tracked_source(tmp_path, "result = 1\n")
    if source is None:
        tracked.unlink()
    else:
        tracked.write_text(source, encoding="utf-8")
    result, report = _run_gate(tmp_path)
    assert result.returncode == 2, result.stderr
    assert report["status"] == "incomplete"
    assert report["eligible_paths"] == [SOURCE_PATH]
    assert report["scanned_paths"] == []
    assert diagnostic in report["diagnostics"][0]["message"]


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
    _tracked_source(tmp_path, source)
    result, report = _run_gate(tmp_path)
    assert result.returncode == 1, result.stderr
    findings = report["findings"]
    functions = [node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef)]
    flagged = {
        function.name
        for finding in findings
        if finding["rule_id"] == "weak-cryptographic-hash"
        for function in functions
        if function.end_lineno is not None and function.lineno <= finding["line"] <= function.end_lineno
    }
    assert flagged == {"sha1_default", "sha1_security", "sha1_dynamic", "md5_default", "md5_nonsecurity"}

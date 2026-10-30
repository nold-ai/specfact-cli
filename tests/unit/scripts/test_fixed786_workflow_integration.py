from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType
from typing import Any, cast

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[3]
MANIFEST = "openspec/changes/security-dependencies-0-55-11-dev/requirements-proof/late-red-evidence.json"
LANES = ("requirements-evidence-producer", "requirements-evidence", "requirements-evidence-final")
AUTH_FLAGS = ("--origin", "--origin-bundle", "--workflow-sha", "--trusted-authority")


@pytest.fixture
def owner() -> Iterator[ModuleType]:
    specification = importlib.util.spec_from_file_location(
        "_fixed786_workflow_owner", ROOT / "scripts/requirements_late_red_proof.py"
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    try:
        specification.loader.exec_module(module)
        yield module
    finally:
        sys.modules.pop(specification.name, None)


@pytest.fixture
def workflow() -> dict[str, Any]:
    return cast(dict[str, Any], yaml.safe_load((ROOT / ".github/workflows/requirements-evidence.yml").read_text()))


@pytest.fixture
def arguments(tmp_path: Path) -> list[str]:
    return [
        "--manifest",
        str(ROOT / MANIFEST),
        "--event",
        str(tmp_path / "event.json"),
        "--red-run",
        str(tmp_path / "run.json"),
        "--red-artifacts",
        str(tmp_path / "artifacts.json"),
        "--red-artifact-root",
        str(tmp_path / "packet"),
        "--repo-root",
        str(ROOT),
        "--cycle-base-ref",
        "9b5ad1e78430cc0b061cb16de42f73de96f4f312",
        "--final-ref",
        "HEAD",
        "--trusted-provenance",
        str(tmp_path / "provenance.py"),
        "--output",
        str(tmp_path / "out.json"),
    ]


def test_fixed_authentication_inputs_are_accepted_by_existing_parser(
    owner: ModuleType, arguments: list[str], tmp_path: Path
) -> None:
    values = [
        str(tmp_path / "origin.json"),
        str(tmp_path / "origin.bundle.jsonl"),
        "9b5ad1e78430cc0b061cb16de42f73de96f4f312",
        str(tmp_path / "authority.py"),
    ]
    for flag, value in zip(AUTH_FLAGS, values, strict=True):
        arguments.extend((flag, value))
    failure = None
    parsed: argparse.Namespace | None = None
    try:
        parsed = owner._arguments(arguments)
    except ValueError as error:
        failure = error
    assert failure is None, "Public parser must accept the fixed authentication input paths"
    assert parsed is not None
    assert str(parsed.origin) == values[0]
    assert str(parsed.origin_bundle) == values[1]
    assert parsed.workflow_sha == values[2]
    assert str(parsed.trusted_authority) == values[3]


def test_public_fixed_missing_authentication_stops_before_normalization(
    owner: ModuleType, arguments: list[str], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    calls: list[object] = []
    monkeypatch.setattr(owner, "_normalize", lambda arguments: calls.append(arguments))
    result = owner._main(arguments)
    assert result == 1, "Fixed public input without authentication must refuse"
    assert calls == [], "Public authentication must precede private normalization"
    assert capsys.readouterr().err == "late-red-proof-invalid\n"


def test_fixed_manifest_is_exact_existing_fixture() -> None:
    path = ROOT / MANIFEST
    assert path.is_file(), "Complete fixed connection must commit its exact transfer manifest"
    expected = ROOT / "tests/unit/scripts/fixtures/fixed786_artifact_source/manifest.json"
    assert json.loads(path.read_bytes()) == json.loads(expected.read_bytes())


def test_fixed_origin_precedes_producer_and_is_isolated(workflow: dict[str, Any]) -> None:
    jobs = workflow["jobs"]
    assert "requirements-fixed786-origin" in jobs, "Fixed native origin must exist before producer"
    origin = jobs["requirements-fixed786-origin"]
    serialized = json.dumps(origin)
    producer = jobs[LANES[0]]
    observed = {
        "independent": not origin.get("needs"),
        "exact_pr": "786" in origin["if"],
        "exact_branch": "codex/security-dependencies-0-55-11-dev" in origin["if"],
        "permissions": origin["permissions"],
        "attest_action": "actions/attest@7a37fbbab9669658a566371acd1cf2f8c7a40d32" in serialized,
        "origin": "origin.json" in serialized,
        "bundle": "origin.bundle.jsonl" in serialized,
        "checkout": [step["uses"] for step in origin["steps"] if step.get("uses", "").startswith("actions/checkout@")],
        "pip": "pip install" in serialized,
        "uv": "uv sync" in serialized,
        "producer_dependency": "requirements-fixed786-origin" in producer.get("needs", []),
        "historical_skip": "skipped" in producer.get("if", ""),
    }
    expected = {
        "independent": True,
        "exact_pr": True,
        "exact_branch": True,
        "permissions": {**origin["permissions"], "id-token": "write", "attestations": "write"},
        "attest_action": True,
        "origin": True,
        "bundle": True,
        "checkout": [],
        "pip": False,
        "uv": False,
        "producer_dependency": True,
        "historical_skip": True,
    }
    assert observed == expected


@pytest.mark.parametrize("lane", LANES)
def test_each_lane_wires_fixed_public_authentication_and_protected_tools(workflow: dict[str, Any], lane: str) -> None:
    job = workflow["jobs"][lane]
    body = json.dumps(job)
    assert MANIFEST in body, f"{lane} must select the fixed manifest"
    for flag in AUTH_FLAGS:
        assert flag in body, f"{lane} must pass {flag} to the existing public CLI"
    assert "5441e26e7c3c8f18973c781e7d43c72076b3283c915d98ca5188bb174bf17c45" in body
    assert "969cabb52fc6db85de46967f62ffe4f0f9b0ca50a80b5a3e46255a89b51f78ad" in body
    assert "verify_tool_files" in body
    assert "--prior-red-proof" in body
    assert "reconciliation_arguments" in body
    assert job.get("permissions", {}).get("id-token") != "write"
    assert job.get("permissions", {}).get("attestations") != "write"


def test_historical_origin_and_lanes_retain_native_controls(workflow: dict[str, Any]) -> None:
    jobs = workflow["jobs"]
    old = jobs["requirements-native-origin"]
    assert old["needs"] == ["requirements-evidence-producer"]
    assert "codex/dependency-hotfix-admission" in old["if"]
    for lane in LANES:
        body = json.dumps(jobs[lane])
        assert "bugfix/692-promotion-final-context" in body
        assert "requirements_proof_provenance.py" in body
        assert "69f075819be5e1ceca1446b026b0417f19e584ca" in body
        assert "--prior-red-proof" in body


def test_strict_audit_calendar_is_explicitly_berlin() -> None:
    workflow = cast(dict[str, Any], yaml.safe_load((ROOT / ".github/workflows/pr-orchestrator.yml").read_text()))
    audit = workflow["jobs"]["security-audit"]
    step = next(step for step in audit["steps"] if step.get("name") == "Run CVE security audit")
    assert step.get("env", {}).get("TZ") == "Europe/Berlin", "Strict audit date must close at Berlin midnight"
    commands = [
        line.strip()
        for line in step["run"].splitlines()
        if line.strip().startswith("python scripts/security_audit_gate.py")
    ]
    assert commands == [
        "python scripts/security_audit_gate.py",
        "python scripts/security_audit_gate.py --requirement requirements/code-review/locked.txt",
        "python scripts/security_audit_gate.py --requirement requirements/runtime-smoke/locked.txt",
    ]

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import runpy
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


@pytest.mark.parametrize("omitted", AUTH_FLAGS)
def test_fixed_public_requires_every_authentication_input_before_formatter(
    owner: ModuleType,
    arguments: list[str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    omitted: str,
) -> None:
    calls: list[object] = []
    monkeypatch.setattr(owner, "_normalize", lambda parsed: calls.append(parsed))
    for flag in AUTH_FLAGS:
        if flag != omitted:
            arguments.extend(
                (
                    flag,
                    "9b5ad1e78430cc0b061cb16de42f73de96f4f312"
                    if flag == "--workflow-sha"
                    else str(tmp_path / "untrusted"),
                )
            )
    assert owner._main(arguments) == 1
    assert calls == []


def test_fixed_public_rejects_unverified_origin_before_formatter(
    owner: ModuleType,
    arguments: list[str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[object] = []
    monkeypatch.setattr(owner, "_normalize", lambda parsed: calls.append(parsed))
    monkeypatch.setenv("GITHUB_WORKFLOW_SHA", "9b5ad1e78430cc0b061cb16de42f73de96f4f312")
    for name in ("origin", "origin-bundle", "trusted-authority"):
        path = tmp_path / name
        path.write_text('{"verified":true}')
        arguments.extend(("--" + name, str(path)))
    arguments.extend(("--workflow-sha", "9b5ad1e78430cc0b061cb16de42f73de96f4f312"))

    def unavailable(*args: object, **kwargs: object) -> None:
        raise FileNotFoundError("synthetic unavailable attestation verifier")

    monkeypatch.setattr(owner.subprocess, "run", unavailable)
    assert owner._main(arguments) == 1
    assert calls == []


def test_historical_public_route_does_not_require_fixed_authentication(
    owner: ModuleType,
    arguments: list[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[object] = []
    arguments[arguments.index("--manifest") + 1] = str(
        ROOT / "openspec/changes/fix-release-promotion-requirements-parity/requirements-proof/late-red-evidence.json"
    )
    monkeypatch.setattr(owner, "_normalize", lambda parsed: calls.append(parsed))
    assert owner._main(arguments) == 0
    assert len(calls) == 1


@pytest.fixture
def synthetic_checkpoint_run() -> dict[str, object]:
    return {
        "id": 91,
        "run_attempt": 1,
        "head_sha": "b" * 40,
        "head_branch": "codex/dev786-complete-ci-signer-20261104",
        "event": "workflow_dispatch",
        "path": ".github/workflows/specfact.yml",
        "workflow_id": 204352514,
        "status": "completed",
        "conclusion": "success",
        "repository": {"id": 73, "full_name": "nold-ai/specfact-cli"},
        "head_repository": {"id": 73, "full_name": "nold-ai/specfact-cli"},
        "actor": {"id": 42, "login": "synthetic-actor"},
        "triggering_actor": {"id": 42, "login": "synthetic-actor"},
    }


def synthetic_history_api(records: dict[str, dict[str, object]]) -> ModuleType:
    def local_api(url: str, token: str) -> tuple[dict[str, object], dict[str, str]]:
        assert token == "explicitly-synthetic-no-network-token"
        assert url in records, f"Unexpected synthetic GET: {url}"
        return records[url], {}

    helper = ModuleType("synthetic_history_helper")
    helper._api_json = local_api
    return helper


def synthetic_signature(final: dict[str, object], tree: str, root: str) -> Any:
    def check(helper: ModuleType, record: dict[str, object], oid: str, parent: str, message: str) -> None:
        assert record == final and oid == tree and parent == root and message == final["message"]

    return check


@pytest.fixture
def synthetic_checkpoint_ledger(
    owner: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    synthetic_checkpoint_run: dict[str, object],
) -> tuple[ModuleType, dict[str, object], dict[str, object], dict[str, object]]:
    root = "d77209f4b13c386e29391f93e1f1c58d7fd8622f"
    source, executor, tree, executor_tree = (digit * 40 for digit in "abcd")
    path = "openspec/changes/security-dependencies-0-55-11-dev/tasks.md"
    original = "synthetic checkpoint"
    actor: dict[str, object] = {"id": 42, "login": "synthetic-actor"}
    repository: dict[str, object] = {"id": 73, "full_name": "nold-ai/specfact-cli"}
    checkpoint: dict[str, object] = {
        "source_commit": source,
        "source_parent": root,
        "source_tree": tree,
        "source_message": original,
        "delta": [{"path": path, "before": ["100644", "1" * 40], "after": ["100644", "2" * 40]}],
    }
    intent: dict[str, object] = {
        "repository_id": 73,
        "repository_full_name": repository["full_name"],
        "actor": actor,
        "triggering_actor": actor,
        "dev": "9b5ad1e78430cc0b061cb16de42f73de96f4f312",
        "main": "3" * 40,
        "checkpoints": [checkpoint],
        "auxiliary_ref": "refs/heads/codex/dev786-complete-ci-signer-20261104",
        "destination": "refs/heads/codex/security-dev-complete-candidate-20261104",
    }
    raw_intent = json.dumps(intent).encode()
    digest = hashlib.sha256(raw_intent).hexdigest()
    program = f"_ALLOWED = frozenset({{{path!r}}})\n".encode()
    blobs = {"scripts/dev_security_ci_signer.py": program, "ci/recovery/dev-security-intent.json": raw_intent}
    trees: dict[str, dict[str, tuple[str, str]]] = {
        executor_tree: {},
        "24112d8c9983333f9059283965230348f718b74c": {path: ("100644", "1" * 40)},
        tree: {path: ("100644", "2" * 40)},
    }
    final: dict[str, object] = {
        "sha": "e" * 40,
        "tree": {"sha": tree},
        "parents": [{"sha": root}],
        "message": f"{original}\n\nSource-Commit: {source}\nIntent: {digest}\nExecutor: {executor}\nRun: 91\nAttempt: 1",
    }
    run = synthetic_checkpoint_run
    history: dict[str, object] = {"total_count": 1, "workflow_runs": [dict(run)]}
    prefix = "/repos/nold-ai/specfact-cli"
    records: dict[str, dict[str, object]] = {
        prefix: repository,
        f"{prefix}/git/commits/{executor}": {"sha": executor, "tree": {"sha": executor_tree}},
        f"{prefix}/git/commits/{source}": {
            "sha": source,
            "tree": {"sha": tree},
            "parents": [{"sha": root}],
            "message": original,
        },
        f"{prefix}/git/commits/{root}": {"sha": root},
        f"{prefix}/actions/runs/91": run,
        f"{prefix}/actions/workflows/204352514/runs?event=workflow_dispatch&per_page=100": history,
    }

    helper = synthetic_history_api(records)
    monkeypatch.setattr(owner, "_fixed_pr786_signed", synthetic_signature(final, tree, root))
    monkeypatch.setenv("GITHUB_TOKEN", "explicitly-synthetic-no-network-token")
    monkeypatch.setattr(
        owner,
        "_FIXED_PR786_SIGNER_FILES",
        (("scripts/dev_security_ci_signer.py", hashlib.sha256(program).hexdigest()),),
    )
    monkeypatch.setattr(owner, "_fixed_pr786_tree", lambda helper, oid: trees[oid])
    monkeypatch.setattr(owner, "_fixed_pr786_blob", lambda helper, inventory, name: blobs[name])
    return helper, final, run, history


@pytest.mark.parametrize(
    "case",
    (
        "single-complete",
        "later-second-dispatch",
        "incomplete-count",
        "malformed-list",
        "wrong-run-id",
        "attempt-two",
        "boolean-attempt",
        "boolean-count",
    ),
)
def test_synthetic_checkpoint_dispatch_history_requires_unique_complete_attempt_one(
    owner: ModuleType,
    synthetic_checkpoint_ledger: tuple[ModuleType, dict[str, object], dict[str, object], dict[str, object]],
    case: str,
) -> None:
    helper, final, run, history = synthetic_checkpoint_ledger
    cases: dict[str, dict[str, object]] = {
        "single-complete": {"total_count": 1, "workflow_runs": [dict(run)]},
        "later-second-dispatch": {"total_count": 2, "workflow_runs": [dict(run), {**run, "id": 92}]},
        "incomplete-count": {"total_count": 2, "workflow_runs": [dict(run)]},
        "malformed-list": {"total_count": 1, "workflow_runs": {}},
        "wrong-run-id": {"total_count": 1, "workflow_runs": [{**run, "id": 92}]},
        "attempt-two": {"total_count": 1, "workflow_runs": [{**run, "run_attempt": 2}]},
        "boolean-attempt": {"total_count": 1, "workflow_runs": [{**run, "run_attempt": True}]},
        "boolean-count": {"total_count": True, "workflow_runs": [dict(run)]},
    }
    history.update(cases[case])
    if case == "single-complete":
        observed_run, association = owner._fixed_pr786_checkpoints(helper, final)
        assert observed_run == run
        assert association == {
            "executor": "b" * 40,
            "intent_digest": "sha256:" + str(final["message"]).split("\nIntent: ")[1].split("\n")[0],
            "source_commit": "a" * 40,
            "checkpoint_count": 1,
        }
    else:
        with pytest.raises(ValueError):
            owner._fixed_pr786_checkpoints(helper, final)


@pytest.fixture(params=("requirements-fixed786-origin", *LANES))
def inline_run_admission(workflow: dict[str, Any], request: pytest.FixtureRequest, tmp_path: Path) -> Path:
    programs = [step.get("run", "") for step in workflow["jobs"][request.param]["steps"]]
    program = next(program for program in programs if "expected_run = {" in program)
    source = program.split("python3 -I -S - <<'PYTHON'\n", 1)[1].split("\nPYTHON", 1)[0]
    nodes = ast.parse(source).body
    assignments = {
        target.id: index
        for index, node in enumerate(nodes)
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    }
    selected = ast.Module(body=nodes[assignments["run_id"] : assignments["artifacts"]], type_ignores=[])
    path = tmp_path / "synthetic_inline_run_admission.py"
    path.write_text(ast.unparse(selected) + "\n")
    return path


@pytest.mark.parametrize("case", ("single-complete", "later-second-dispatch", "incomplete-count", "boolean-attempt"))
def test_each_inline_capture_checks_complete_unique_dispatch(
    inline_run_admission: Path,
    synthetic_checkpoint_ledger: tuple[ModuleType, dict[str, object], dict[str, object], dict[str, object]],
    case: str,
) -> None:
    helper, _, run, history = synthetic_checkpoint_ledger
    cases = {
        "single-complete": {"total_count": 1, "workflow_runs": [dict(run)]},
        "later-second-dispatch": {"total_count": 2, "workflow_runs": [dict(run), {**run, "id": 92}]},
        "incomplete-count": {"total_count": 2, "workflow_runs": [dict(run)]},
        "boolean-attempt": {"total_count": 1, "workflow_runs": [{**run, "run_attempt": True}]},
    }
    history.update(cases[case])
    namespace = {
        "get": lambda path: helper._api_json(path, "explicitly-synthetic-no-network-token")[0],
        "run_text": "91",
        "executor": "b" * 40,
        "intent": {"repository_id": 73, "actor": run["actor"], "triggering_actor": run["triggering_actor"]},
    }
    if case == "single-complete":
        observed = runpy.run_path(str(inline_run_admission), init_globals=namespace)
        assert observed["run"] == run
    else:
        with pytest.raises(ValueError):
            runpy.run_path(str(inline_run_admission), init_globals=namespace)

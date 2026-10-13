"""Exercise actual review shells and the immutable provider with synthetic root artifacts."""

from __future__ import annotations

import copy
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any

import pytest
import yaml

from tests.unit.scripts.test_requirements_planning_stack_context import (
    CHECK_ROUTE,
    REPO_ROOT,
    REPOSITORY,
    StackCase,
    _git,
    _planning_context,
    planning_case as planning_case,
)


def _archive(payload: dict[str, Any]) -> bytes:
    """Create clearly synthetic JSON-only artifact bytes for boundary probes."""
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("requirements-evidence.json", json.dumps(payload))
    return stream.getvalue()


def _synthetic_proof(root: str) -> dict[str, Any]:
    """Use provider-normalized synthetic plans solely for isolated boundary tests."""
    from specfact_requirements.requirements.lifecycle import build_plan

    mapping = "sha256:" + "0" * 64
    plan = build_plan(
        mapping, [{"case_id": "SYNTHETIC", "method": "test", "node_id": "tests/control.py::test_runtime"}]
    )
    return {
        "schema_version": "2",
        "required_maturity": "verified",
        "observed_maturity": "verified",
        "delivery_status": "implementation-verified",
        "implementation_evidence": "passing-after-red-proven",
        "verdict": "passed",
        "gate_decision": "pass",
        "findings": [],
        "mapping_digest": mapping,
        "plan_digest": plan["plan_digest"],
        "plan": plan,
        "execution_plan": plan,
        "execution_proof": {
            "run_stage": "final",
            "source_ref": root,
            "selectors": ["tests/control.py::test_runtime"],
            "junit_digest": "sha256:" + "1" * 64,
            "proof_basis": "red-junit",
        },
    }


def _synthetic_artifact(root: str) -> dict[str, Any]:
    """Bind explicit service identity independently from the proof document."""
    return {
        "id": 3101,
        "name": "requirements-evidence",
        "expired": False,
        "size_in_bytes": 4096,
        "workflow_run": {
            "id": 1101,
            "repository_id": 1085706003,
            "head_repository_id": 1085706003,
            "head_sha": root,
            "head_branch": "dependency-root",
        },
    }


def _review_tools(repo: Path, binary: Path) -> Path:
    """Adapt the review executable to its actual frozen final-context reader."""
    verifier = repo / "verifier/bin"
    verifier.mkdir(parents=True)
    review_python = verifier / "python"
    review_python.write_text(
        f"#!{sys.executable}\n"
        "import json,os,sys\nfrom pathlib import Path\n"
        "fixture=Path(os.environ['SPECFACT_MODULES_REPO'])\n"
        "sys.path.insert(0,os.environ['TRUSTED_REQUIREMENTS_CORE'])\n"
        "for source in (fixture/'packages').glob('*/src'): sys.path.insert(0,str(source))\n"
        "from specfact_code_review.run.commands import _requirements_evidence_context\n"
        "args=sys.argv[1:]\n"
        "try: context=_requirements_evidence_context(Path(args[args.index('--requirements-evidence')+1]))\n"
        "except Exception as error: print(str(error),file=sys.stderr);sys.exit(2)\n"
        "Path(os.environ['REVIEW_RECEIPT']).write_text(json.dumps({'context':context.model_dump(),'args':args}))\n"
    )
    review_python.chmod(0o755)
    node = binary / "node"
    node.write_text("#!/bin/sh\nprintf 'v24.16.0\\n'\n")
    node.chmod(0o755)
    (binary / "gh").write_text(
        f"#!{sys.executable}\n"
        "import base64,json,sys\nfrom pathlib import Path\n"
        "routes=json.loads(Path(sys.argv[0]).with_name('api-routes.json').read_text())\n"
        "value=routes[sys.argv[-1]]\n"
        "if isinstance(value,dict) and 'archive_base64' in value: sys.stdout.buffer.write(base64.b64decode(value['archive_base64']))\n"
        "else: print(json.dumps(value))\n"
    )
    (binary / "gh").chmod(0o755)
    return verifier


def _review_environment(case: StackCase, binary: Path, verifier: Path, runner: Path) -> dict[str, str]:
    repo = case.repo
    env = os.environ.copy()
    env.update(
        {
            "PATH": str(binary) + os.pathsep + env.get("PATH", ""),
            "RUNNER_TEMP": str(runner),
            "GITHUB_EVENT_PATH": str(repo / "event.json"),
            "GITHUB_WORKSPACE": str(repo),
            "GITHUB_OUTPUT": str(runner / "output"),
            "GITHUB_STEP_SUMMARY": str(runner / "summary"),
            "REVIEW_BASE_BRANCH": "dev",
            "PROOF_BASE_COMMIT": case.baseline,
            "PLANNING_BASE_COMMIT": case.root,
            "PROOF_HEAD_BRANCH": "dependency-root",
            "REQUIREMENTS_VALIDATOR_ROOT": str(verifier.parent),
            "TRUSTED_REQUIREMENTS_CORE": str(REPO_ROOT / "src"),
            "PYLINT_WRAPPER": str(binary),
            "FINAL_VERIFIER_ROOT": str(verifier.parent),
            "FINAL_TRUSTED_CORE": str(REPO_ROOT / "src"),
            "FINAL_NODE_BIN": str(binary),
            "FINAL_PYLINT_WRAPPER": str(binary),
            "FINAL_BASEDPYRIGHT_ROOT": str(binary),
            "REVIEW_RECEIPT": str(runner / "review-receipt.json"),
        }
    )
    return env


@pytest.fixture
def review_case(planning_case: StackCase, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Reuse isolated real Git/native identity and the verified fixture provider."""
    context = _planning_context(planning_case, monkeypatch)
    fixture = Path(os.environ["SPECFACT_MODULES_REPO"])
    monkeypatch.setattr(sys, "path", [str(source) for source in (fixture / "packages").glob("*/src")] + sys.path)
    report = _synthetic_proof(planning_case.root)
    artifact = _synthetic_artifact(planning_case.root)
    repo = planning_case.repo
    _git(repo, "update-ref", "refs/remotes/origin/dev", planning_case.baseline)
    runner = repo / "runner"
    policy = runner / "trusted-stack-context"
    (policy / "scripts").mkdir(parents=True)
    for name in ("requirements_stack_context.py", "requirements_planning_context.py", "requirements_review_context.py"):
        source = REPO_ROOT / "scripts" / name
        if source.exists():
            shutil.copyfile(source, policy / "scripts" / name)
    (policy / "context.json").write_text(json.dumps(context))
    final_report = repo / "root-final.json"
    final_report.write_text(json.dumps(report))
    artifacts = repo / "artifacts/requirements-evidence"
    artifacts.mkdir(parents=True)
    planning_bytes = json.dumps(
        {"schema_version": "2", "gate_decision": "pass", "required_maturity": "planned"}
    ).encode()
    (artifacts / "requirements-evidence-consumer.json").write_bytes(planning_bytes)
    (runner / "final-requirements.json").write_bytes(planning_bytes)
    binary = repo / "github-fixture-bin"
    verifier = _review_tools(repo, binary)
    env = _review_environment(planning_case, binary, verifier, runner)
    return {
        "case": planning_case,
        "env": env,
        "report": report,
        "artifact": artifact,
        "planning_bytes": planning_bytes,
        "final_report": final_report,
        "binary": binary,
    }


def _proof_variant(report: dict[str, Any], variant: str) -> None:
    """Keep proof-basis compatibility and deliberately malformed proof fixtures distinct."""
    if variant == "producer":
        report["execution_proof"]["run_stage"] = "authored"
    if variant == "foreign-proof":
        report["execution_proof"]["source_ref"] = "f" * 40
    if variant == "incomplete-proof":
        report["execution_plan"] = {}
    if variant == "legacy":
        report["implementation_evidence"] = "passing-after-legacy-tdd-ledger"
        report["execution_proof"]["proof_basis"] = "legacy-tdd-ledger"
        report["legacy_tdd_evidence"] = {
            "schema_version": "1",
            "kind": "legacy-tdd-ledger",
            "change_id": "synthetic-control",
            "ledger_digest": "sha256:" + "2" * 64,
            "mapping_digest": report["mapping_digest"],
            "plan_digest": report["plan_digest"],
        }


def _artifact_routes(probe: dict[str, Any], variant: str) -> None:
    """Supply deliberately malformed service metadata/proof without editing production logic."""
    import base64

    case = probe["case"]
    report = copy.deepcopy(probe["report"])
    artifact = copy.deepcopy(probe["artifact"])
    _proof_variant(report, variant)
    if variant == "foreign-artifact":
        artifact["workflow_run"]["head_repository_id"] = 999
    if variant == "expired":
        artifact["expired"] = True
    data = _archive(report)
    artifact["digest"] = "sha256:" + hashlib.sha256(data).hexdigest()
    artifact["size_in_bytes"] = len(data)
    if variant == "oversized-metadata":
        artifact["size_in_bytes"] = 16 * 1024 * 1024 + 1
    if variant == "corrupted":
        data += b"corruption"
    routes = copy.deepcopy(case.routes)
    if variant == "stale-root":
        routes[CHECK_ROUTE.format(root=case.root)]["check_runs"][0]["conclusion"] = "failure"
    if variant == "stale-native-head":
        number = case.event["pull_request"]["number"]
        routes[f"/repos/{REPOSITORY}/pulls/{number}"]["head"]["sha"] = "f" * 40
    records = [artifact, copy.deepcopy(artifact)] if variant == "ambiguous" else [artifact]
    routes[f"/repos/{REPOSITORY}/actions/runs/1101/artifacts?per_page=100&page=1"] = {
        "total_count": len(records),
        "artifacts": records,
    }
    routes[f"/repos/{REPOSITORY}/actions/artifacts/3101/zip"] = {"archive_base64": base64.b64encode(data).decode()}
    (probe["binary"] / "api-routes.json").write_text(json.dumps(routes))


def _run_review(
    probe: dict[str, Any], final: bool, variant: str = "", ordinary: bool = False
) -> subprocess.CompletedProcess[str]:
    """Execute repository-authored shell unchanged, with explicit service/tool test doubles."""
    case = probe["case"]
    _artifact_routes(probe, variant)
    env = probe["env"].copy()
    receipt = Path(env["REVIEW_RECEIPT"])
    receipt.unlink(missing_ok=True)
    for destination in (
        case.repo / "runner/final-requirements.json",
        case.repo / "artifacts/requirements-evidence/requirements-evidence-consumer.json",
    ):
        destination.write_bytes(probe["planning_bytes"])
    if ordinary:
        env.pop("PLANNING_BASE_COMMIT")
        destination = case.repo / (
            "runner/final-requirements.json"
            if final
            else "artifacts/requirements-evidence/requirements-evidence-consumer.json"
        )
        ordinary_report = copy.deepcopy(probe["report"])
        _proof_variant(ordinary_report, variant)
        destination.write_bytes(json.dumps(ordinary_report).encode())
    workflow = yaml.safe_load((REPO_ROOT / ".github/workflows/requirements-evidence.yml").read_text())
    job = "requirements-evidence-final" if final else "requirements-evidence"
    name = (
        "Run Code Review with trusted final Requirements context"
        if final
        else "Run Code Review with finalized Requirements context"
    )
    scripts = [s["run"] for s in workflow["jobs"][job]["steps"] if s.get("name") == name]
    assert len(scripts) == 1
    return subprocess.run(
        ["bash", "--noprofile", "--norc", "-e", "-o", "pipefail", "-c", scripts[0]],
        cwd=case.repo,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def _assert_preserved_context(probe: dict[str, Any]) -> None:
    """Verify unchanged genuine bytes, full inherited review and independent planning receipts."""
    receipt = json.loads(Path(probe["env"]["REVIEW_RECEIPT"]).read_text())
    assert receipt["context"]["source_ref"] == probe["case"].root
    assert "src/runtime.py" in receipt["args"]
    assert receipt["args"][receipt["args"].index("--enforcement") + 1] == "full"
    context = Path(receipt["context"]["path"])
    assert context.read_bytes() == _archive_report_bytes(probe["report"])
    assert (
        probe["case"].repo / "artifacts/requirements-evidence/requirements-evidence-consumer.json"
    ).read_bytes() == probe["planning_bytes"]
    assert (probe["case"].repo / "runner/final-requirements.json").read_bytes() == probe["planning_bytes"]


def test_actual_consumers_preserve_final_root_context(review_case: dict[str, Any]) -> None:
    """Both review consumers preserve genuine context bytes and full inherited scope."""
    for final in (False, True):
        ordinary = _run_review(review_case, final, ordinary=True)
        assert ordinary.returncode == 0, ordinary.stderr
        result = _run_review(review_case, final)
        assert result.returncode == 0, result.stderr
        _assert_preserved_context(review_case)
        ordinary_legacy = _run_review(review_case, final, "legacy", ordinary=True)
        assert ordinary_legacy.returncode == 0, ordinary_legacy.stderr
        legacy = _run_review(review_case, final, "legacy")
        assert legacy.returncode == 0, legacy.stderr
        assert _run_review(review_case, final, ordinary=True).returncode == 0
        (review_case["case"].repo / "artifacts/requirements-evidence/requirements-evidence-consumer.json").write_bytes(
            review_case["planning_bytes"]
        )
        (review_case["case"].repo / "runner/final-requirements.json").write_bytes(review_case["planning_bytes"])


def _archive_report_bytes(report: dict[str, Any]) -> bytes:
    return json.dumps(report).encode()


def test_actual_consumers_reject_context_forgery(review_case: dict[str, Any]) -> None:
    """Artifact/proof attacks fail closed without preventing genuine finalized root review."""
    for final in (False, True):
        for variant in (
            "producer",
            "foreign-proof",
            "foreign-artifact",
            "expired",
            "corrupted",
            "ambiguous",
            "stale-root",
            "stale-native-head",
            "incomplete-proof",
            "oversized-metadata",
        ):
            result = _run_review(review_case, final, variant)
            assert result.returncode != 0, variant
            assert not Path(review_case["env"]["REVIEW_RECEIPT"]).exists(), variant
        valid = _run_review(review_case, final)
        assert valid.returncode == 0, valid.stderr

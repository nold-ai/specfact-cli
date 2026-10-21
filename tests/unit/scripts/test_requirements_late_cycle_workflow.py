from __future__ import annotations

import hashlib
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NamedTuple

import yaml


ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = ROOT / ".github/workflows/requirements-evidence.yml"
LANES = {
    "final": "Reconcile final Requirements verdict on fresh runner",
    "fresh": "Reconcile Requirements evidence on fresh runner",
    "producer": "Run Requirements evidence gate",
}


def _boundary(lane: str) -> str:
    workflow = yaml.safe_load(WORKFLOW.read_text())
    shell = next(
        step["run"] for job in workflow["jobs"].values() for step in job["steps"] if step.get("name") == LANES[lane]
    )
    if lane == "producer":
        start = shell.index('set +e\n    "${reconciliation_arguments[@]}"')
        end = shell.index('failure_diagnostic="Requirements proof reconciliation exited with status $exit_code', start)
        return shell[start:end] + '\nexit "$exit_code"'
    if lane == "fresh":
        return shell[shell.index('  test -s "$consumer_junit"') :].rsplit("\nfi", 1)[0]
    return shell[shell.index('test -s "$execution_junit"') :].split('cat "$final_summary"')[0]


@dataclass(frozen=True)
class WorkflowProofCase:
    lane: str
    policy_exit: int
    native_exit: int
    scope: str = "scoped"
    extra_failure: bool = False


class BoundaryArtifacts(NamedTuple):
    report: Path
    junit: Path
    plan: Path
    summary: Path
    policy: Path
    called: Path
    bin_dir: Path
    event: Path
    original: bytes


def _write_policy_double(policy: Path, policy_exit: int) -> None:
    policy.write_text(
        "import argparse, json, os, sys\nfrom pathlib import Path\n"
        "p=argparse.ArgumentParser(); p.add_argument('operation'); "
        "p.add_argument('--output'); p.add_argument('--report'); p.add_argument('--plan'); "
        "p.add_argument('--junit'); p.add_argument('--event'); p.add_argument('--policy-revision'); a=p.parse_args()\n"
        "assert a.operation == 'decide'\n"
        "assert Path(a.report).read_bytes() == Path(os.environ['EXPECTED_REPORT']).read_bytes()\n"
        "assert Path(a.plan).is_file() and Path(a.junit).is_file() and Path(a.event).is_file()\n"
        "Path(os.environ['CALLED']).write_text(json.dumps(vars(a)))\n"
        "Path(a.output).write_text(json.dumps({'outcome':'HumanApprovedLateCycle'}))\n"
        f"sys.exit({policy_exit})\n"
    )


def _native_artifacts(tmp_path: Path, case: WorkflowProofCase) -> BoundaryArtifacts:
    artifact = tmp_path / "artifacts/requirements-evidence"
    artifact.mkdir(parents=True)
    report = artifact / "requirements-evidence.json"
    findings = ["prior-red-proof-missing"] if case.native_exit else []
    if case.extra_failure:
        findings.append("failed-test")
    raw = {
        "schema_version": "2",
        "gate_decision": "fail" if case.native_exit else "pass",
        "verdict": "failed" if case.native_exit else "passed",
        "findings": findings,
    }
    original = json.dumps(raw, sort_keys=True).encode()
    report.write_bytes(original)
    junit = artifact / "requirements-proof.xml"
    junit.write_text('<testsuite tests="1"><testcase classname="test" name="current"/></testsuite>')
    plan = artifact / "requirements-evidence-plan.json"
    plan.write_text("{}")
    summary = tmp_path / "summary.md"
    summary.write_text("Native result.\n")
    policy = tmp_path / "policy.py"
    called = tmp_path / "policy-called.json"
    _write_policy_double(policy, case.policy_exit)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    curl = bin_dir / "curl"
    curl.write_text(
        '#!/usr/bin/env bash\nset -eu\nwhile [[ "$1" != --output ]]; do shift; done\ncp "$POLICY_DOUBLE" "$2"\n'
    )
    curl.chmod(0o755)
    event = tmp_path / "event.json"
    event.write_text("{}")
    return BoundaryArtifacts(report, junit, plan, summary, policy, called, bin_dir, event, original)


def _native_prelude(case: WorkflowProofCase, paths: BoundaryArtifacts) -> str:
    report, junit, plan, summary = paths[:4]
    return "\n".join(
        [
            "set -euo pipefail",
            f'isolated_specfact=(bash -c "exit {case.native_exit}" native)',
            f'reconciliation_arguments=(bash -c "exit {case.native_exit}" native)',
            f'execution_junit="{junit}"',
            f'consumer_junit="{junit}"',
            f'final_plan="{plan}"',
            f'consumer_plan="{plan}"',
            f'final_report="{report}"',
            f'consumer_report="{report}"',
            f'final_summary="{summary}"',
            f'consumer_summary="{summary}"',
            'source_ref="0123456789abcdef0123456789abcdef01234567"',
            'LATE_RED_PROVENANCE="${RUNNER_TEMP}/late-red-trusted-provenance/scripts/requirements_proof_provenance.py"',
            'FINAL_LATE_RED_PROVENANCE="$LATE_RED_PROVENANCE"',
            'LATE_RED_CYCLE_BASE="0123456789abcdef0123456789abcdef01234567"',
            f"LATE_RED_ACTIVE={'true' if case.scope == 'invalid-proof' else 'false'}",
            'PRIOR_RED_HEAD_SHA=""',
            "run_stage=final",
            "selected_change=isolate-semgrep-security-runtime",
            'evidence_base_commit="0123456789abcdef0123456789abcdef01234567"',
            f"EVIDENCE_PULL_REQUEST={0 if case.scope == 'invalid-pr' else 900}",
            f"EVIDENCE_HEAD_BRANCH={'other-branch' if case.scope == 'other-branch' else 'codex/dependency-hotfix-admission'}",
        ]
    )


def _boundary_environment(tmp_path: Path, paths: BoundaryArtifacts) -> dict[str, str]:
    report, _, _, _, policy, called, bin_dir, event, _ = paths
    return {
        **os.environ,
        "PATH": f"{bin_dir}:{os.environ['PATH']}",
        "RUNNER_TEMP": str(tmp_path),
        "GITHUB_WORKSPACE": str(tmp_path),
        "GITHUB_EVENT_PATH": str(event),
        "GITHUB_REPOSITORY": "nold-ai/specfact-cli",
        "LATE_CYCLE_POLICY_REVISION": "0123456789abcdef0123456789abcdef01234567",
        "POLICY_DOUBLE": str(policy),
        "CALLED": str(called),
        "EXPECTED_REPORT": str(report),
    }


def _admission_steps(case: WorkflowProofCase) -> tuple[dict[str, Any], dict[str, Any]]:
    workflow = yaml.safe_load(WORKFLOW.read_text())
    job = next(
        job for job in workflow["jobs"].values() if any(step.get("name") == LANES[case.lane] for step in job["steps"])
    )
    steps = job["steps"]
    native = next(step for step in steps if step.get("name") == LANES[case.lane])
    admission = next(step for step in steps if step.get("id") == "late-cycle-admission")
    enforcement = next(step for step in steps if step.get("name") == "Enforce native or admitted Requirements verdict")
    _assert_admission_isolation(steps, native, admission, enforcement)
    return admission, enforcement


def _assert_admission_isolation(
    steps: list[dict[str, Any]], native: dict[str, Any], admission: dict[str, Any], enforcement: dict[str, Any]
) -> None:
    assert native["continue-on-error"] is True
    assert "GH_TOKEN" not in native.get("env", {})
    assert "curl " not in native["run"]
    assert admission["env"]["GH_TOKEN"] == "${{ github.token }}"
    assert steps.index(native) < steps.index(admission) < steps.index(enforcement)
    assert "native-reconciled == 'true'" in admission["if"]
    assert "outcome == 'failure'" in admission["if"]
    assert "selected-change == 'isolate-semgrep-security-runtime'" in admission["if"]
    assert "codex/dependency-hotfix-admission" in admission["if"]


def _run_admission(
    tmp_path: Path,
    case: WorkflowProofCase,
    admission: dict[str, Any],
    environment: dict[str, str],
    native: tuple[subprocess.CompletedProcess[str], bool],
) -> str:
    result, marker = native
    admission_outcome = "skipped"
    if not (result.returncode and marker and case.scope == "scoped"):
        return admission_outcome
    admission_environment = {**environment, "GH_TOKEN": "transport-double-token"}
    paths = {
        "NATIVE_REPORT": environment["EXPECTED_REPORT"],
        "NATIVE_PLAN": str(tmp_path / "artifacts/requirements-evidence/requirements-evidence-plan.json"),
        "NATIVE_JUNIT": str(tmp_path / "artifacts/requirements-evidence/requirements-proof.xml"),
        "ADMISSION_AUDIT": str(tmp_path / "admission.json"),
    }
    admission_result = subprocess.run(
        ["bash", "-c", admission["run"]],
        cwd=tmp_path,
        env={**admission_environment, **paths},
        capture_output=True,
        text=True,
        check=False,
    )
    return "success" if admission_result.returncode == 0 else "failure"


def _run_boundary(tmp_path: Path, case: WorkflowProofCase) -> None:
    paths = _native_artifacts(tmp_path, case)
    report, _, _, summary, _, called, _, _, original = paths
    prelude = _native_prelude(case, paths)
    environment = _boundary_environment(tmp_path, paths)
    admission, enforcement = _admission_steps(case)
    output = tmp_path / "native-output"
    environment["GITHUB_OUTPUT"] = str(output)
    environment["GITHUB_STEP_SUMMARY"] = str(summary)
    environment.pop("GH_TOKEN", None)
    environment.pop("GITHUB_TOKEN", None)
    result = subprocess.run(
        ["bash", "-c", prelude + "\n" + _boundary(case.lane)],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    marker = output.exists() and "native-reconciled=true" in output.read_text()
    assert marker == (case.scope != "invalid-proof" and (case.lane == "producer" or case.scope == "scoped"))
    admission_outcome = _run_admission(tmp_path, case, admission, environment, (result, marker))
    verdict = subprocess.run(
        ["bash", "-c", enforcement["run"]],
        cwd=tmp_path,
        env={
            **environment,
            "NATIVE_OUTCOME": "failure" if result.returncode else "success",
            "ADMISSION_OUTCOME": admission_outcome,
        },
        capture_output=True,
        text=True,
        check=False,
    )
    expected_success = case.scope == "scoped" and (case.native_exit == 0 or case.policy_exit == 0)
    assert (verdict.returncode == 0) == expected_success, result.stderr
    assert report.read_bytes() == original
    assert called.exists() == (bool(case.native_exit) and case.scope == "scoped")


def test_all_three_lanes_preserve_native_bytes_and_enforce_policy_exit(tmp_path: Path) -> None:
    workflow = yaml.safe_load(WORKFLOW.read_text())
    for name in ("requirements-evidence-producer", "requirements-evidence", "requirements-evidence-final"):
        assert workflow["jobs"][name]["permissions"].get("pull-requests") == "read"
    for lane in LANES:
        for policy_exit in (0, 1, 7):
            for native_exit in (0, 1):
                _run_boundary(
                    tmp_path / f"{lane}-{policy_exit}-{native_exit}", WorkflowProofCase(lane, policy_exit, native_exit)
                )
        _run_boundary(tmp_path / f"{lane}-additional-native-failure", WorkflowProofCase(lane, 1, 1, extra_failure=True))


def test_fresh_and_final_preserve_scope_and_invalid_red_guards(tmp_path: Path) -> None:
    for lane in ("fresh", "final"):
        for scope in ("invalid-pr", "other-branch", "invalid-proof"):
            _run_boundary(tmp_path / f"{lane}-{scope}", WorkflowProofCase(lane, 0, 1, scope=scope))


def _origin_fixture(tmp_path: Path, mismatch: str | None) -> tuple[Path, dict[str, Any], dict[str, str]]:
    native_zip = b"inert native archive, never executed"
    head = "1" * 40
    workflow_sha = "2" * 40
    root = tmp_path / str(mismatch)
    root.mkdir()
    (root / "native.zip").write_bytes(native_zip)
    metadata = {
        "id": 123,
        "name": "requirements-evidence",
        "expired": False,
        "workflow_run": {"id": 457 if mismatch == "run" else 456, "head_sha": head},
        "digest": "sha256:" + ("0" * 64 if mismatch == "digest" else hashlib.sha256(native_zip).hexdigest()),
    }
    (root / "artifact.json").write_text(json.dumps(metadata))
    gh = root / "gh"
    gh.write_text(
        '#!/usr/bin/env bash\nset -eu\ncase "$2" in */zip) cat "$FIXTURE/native.zip";; *) cat "$FIXTURE/artifact.json";; esac\n'
    )
    gh.chmod(0o755)
    environment = {
        **os.environ,
        "PATH": f"{root}:{os.environ['PATH']}",
        "FIXTURE": str(root),
        "GITHUB_REPOSITORY": "nold-ai/specfact-cli",
        "RUNNER_TEMP": str(root),
        "GITHUB_RUN_ID": "456",
        "GITHUB_RUN_ATTEMPT": "3",
        "NATIVE_ARTIFACT_ID": "123",
        "NATIVE_HEAD_COMMIT": head,
        "NATIVE_WORKFLOW_SHA": workflow_sha,
    }
    return root, metadata, environment


def _assert_origin_attestation(origin: dict[str, Any]) -> None:
    assert "always()" in origin["if"]
    assert origin["permissions"]["id-token"] == "write"
    assert all("checkout" not in step.get("uses", "") for step in origin["steps"])
    attest = next(step for step in origin["steps"] if step.get("uses", "").startswith("actions/attest@"))
    assert attest["with"]["subject-path"].endswith("/origin.json")
    assert len(attest["uses"].split("@")[1]) == 40


def _origin_binding() -> dict[str, Any]:
    workflow = yaml.safe_load(WORKFLOW.read_text())
    jobs = list(workflow["jobs"].values())
    origins = [job for job in jobs if job.get("name") == "Native Requirements Origin"]
    assert len(origins) == 1, "A failed producer must still generate independently authenticated origin metadata"
    origin = origins[0]
    _assert_origin_attestation(origin)
    return next(step for step in origin["steps"] if step.get("name") == "Bind native artifact to executed workflow")


def test_origin_attestation_survives_producer_failure(tmp_path: Path) -> None:
    binding = _origin_binding()
    assert binding["env"]["NATIVE_WORKFLOW_SHA"] == "${{ github.workflow_sha }}"
    for mismatch in (None, "digest", "run"):
        root, metadata, environment = _origin_fixture(tmp_path, mismatch)
        result = subprocess.run(
            ["bash", "-c", binding["run"]], env=environment, capture_output=True, text=True, check=False
        )
        assert (result.returncode == 0) == (mismatch is None), result.stderr
        manifest = root / "requirements-native-origin/origin.json"
        assert manifest.exists() == (mismatch is None)
        if mismatch is None:
            actual = json.loads(manifest.read_bytes())
            assert actual == {
                "schema_version": 1,
                "repository": "nold-ai/specfact-cli",
                "run_id": 456,
                "run_attempt": 3,
                "artifact_id": 123,
                "artifact_digest": metadata["digest"],
                "head_commit": "1" * 40,
                "workflow_path": ".github/workflows/requirements-evidence.yml",
                "workflow_sha": "2" * 40,
            }

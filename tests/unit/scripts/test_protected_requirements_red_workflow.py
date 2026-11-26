"""Verify protected RED proof runs and is consumed by each existing gate."""

import re
from pathlib import Path

import yaml


WORKFLOW = Path(__file__).resolve().parents[3] / ".github/workflows/requirements-evidence.yml"
EVIDENCE_JOBS = ("requirements-evidence-producer", "requirements-evidence", "requirements-evidence-final")
PROOF_JOB = "protected-red-proof"


def test_protected_red_job_is_bound_to_the_one_pull_request() -> None:
    jobs = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["jobs"]
    proof = jobs[PROOF_JOB]

    assert proof["permissions"] == {"contents": "read"}
    assert "github.event.pull_request.number == 803" in proof["if"]
    assert "github.event.pull_request.head.repo.full_name == github.repository" in proof["if"]
    assert "github.base_ref == 'main'" in proof["if"]
    assert re.fullmatch(
        r"nold-ai/\.github/\.github/actions/protected-requirements-red-803@[0-9a-f]{40}", proof["steps"][0]["uses"]
    )


def test_protected_artifact_is_consumed_in_each_native_requirements_lane() -> None:
    jobs = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["jobs"]
    producer, execution, final = EVIDENCE_JOBS
    assert PROOF_JOB in jobs[producer]["needs"]
    assert jobs[execution]["needs"] == producer
    assert jobs[final]["needs"] == execution
    sources = (
        "needs.protected-red-proof.outputs.artifact-id",
        "steps.protected-red-artifact.outputs.artifact-id",
        "steps.protected-red-artifact.outputs.artifact-id",
    )
    for name, source in zip(EVIDENCE_JOBS, sources, strict=True):
        download = next(
            step for step in jobs[name]["steps"] if step["name"] == "Download current protected before-fix proof"
        )
        assert download["with"]["artifact-ids"] == "${{ " + source + " }}"
        assert "run-id" not in download["with"]
    assert jobs[final]["name"] == "Requirements evidence"


def test_fresh_runners_authenticate_the_same_scoped_run() -> None:
    jobs = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["jobs"]
    _, execution, final = EVIDENCE_JOBS
    for name in (execution, final):
        locator = next(step for step in jobs[name]["steps"] if step.get("id") == "protected-red-artifact")
        assert locator["if"] == jobs[PROOF_JOB]["if"]
        assert "requirements-protected-red-${GITHUB_RUN_ATTEMPT}" in locator["run"]

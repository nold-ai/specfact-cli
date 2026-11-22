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
    assert "github.event.pull_request.number == 799" in proof["if"]
    assert "github.event.pull_request.head.repo.full_name == 'nold-ai/specfact-cli'" in proof["if"]
    assert "github.base_ref == 'dev'" in proof["if"]
    assert re.fullmatch(
        r"nold-ai/\.github/\.github/actions/protected-requirements-red@[0-9a-f]{40}", proof["steps"][0]["uses"]
    )


def test_protected_artifact_is_consumed_in_each_native_requirements_lane() -> None:
    jobs = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["jobs"]
    for name in EVIDENCE_JOBS:
        job = jobs[name]
        assert PROOF_JOB in job["needs"]
        download = next(step for step in job["steps"] if step["name"] == "Download protected RED proof")
        assert download["with"]["artifact-ids"] == "${{ needs.protected-red-proof.outputs.artifact-id }}"
        assert "run-id" not in download["with"]
    assert jobs["requirements-evidence-final"]["name"] == "Requirements evidence"

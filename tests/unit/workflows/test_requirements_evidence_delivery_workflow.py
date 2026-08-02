"""Contract coverage for the core Requirements-evidence pull-request gate."""

from __future__ import annotations

from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]
APPROVED_MODULE_COMMIT = "97e0f917903b09803f48b7d73f56ec9753cf95c7"


def _step_by_name(workflow: dict[str, object], name: str) -> dict[str, object]:
    steps = workflow["jobs"]["requirements-evidence"]["steps"]  # type: ignore[index]
    return next(step for step in steps if step.get("name") == name)  # type: ignore[union-attr,return-value]


def _step_index(workflow: dict[str, object], name: str) -> int:
    """Return a named step's position in the evidence job."""
    steps = workflow["jobs"]["requirements-evidence"]["steps"]  # type: ignore[index]
    return next(index for index, step in enumerate(steps) if step.get("name") == name)  # type: ignore[union-attr]


def _assert_fixture_contract(workflow: dict[str, object]) -> None:
    read_fixture = _step_by_name(workflow, "Read immutable module fixture")
    verify_fixture = _step_by_name(workflow, "Verify immutable module fixture")
    export_fixture = _step_by_name(workflow, "Export verified module fixture paths")
    assert "ci/module-fixture.lock.json" in read_fixture["run"]  # type: ignore[index]
    assert "nold-ai/specfact-cli-modules" in read_fixture["run"]  # type: ignore[index]
    assert f'approved_commit="{APPROVED_MODULE_COMMIT}"' in read_fixture["run"]  # type: ignore[index]
    assert 'test "$commit" = "$approved_commit"' in read_fixture["run"]  # type: ignore[index]
    assert "rev-parse HEAD" in verify_fixture["run"]  # type: ignore[index]
    assert "SPECFACT_MODULES_REPO=${GITHUB_WORKSPACE}/specfact-cli-modules" in export_fixture["run"]  # type: ignore[index]
    assert "SPECFACT_MODULES_ROOTS=${GITHUB_WORKSPACE}/specfact-cli-modules/packages" in export_fixture["run"]  # type: ignore[index]


def _assert_command_contract(workflow: dict[str, object]) -> None:
    run_evidence = _step_by_name(workflow, "Run Requirements evidence gate")
    assert run_evidence["id"] == "run-evidence"  # type: ignore[index]
    required_fragments = (
        "uv run --locked --no-sync specfact requirements evidence",
        '--base-ref "origin/${EVIDENCE_BASE_BRANCH}"',
        "required_maturity=planned",
        "required_maturity=test-authored",
        '--required-maturity "$required_maturity"',
        'if ! changed_paths="$(git diff --name-only "origin/${EVIDENCE_BASE_BRANCH}...HEAD")"; then',
        "--plan-output artifacts/requirements-evidence/requirements-evidence-plan.json",
        '--review-evidence "$review_evidence"',
        "fallback_required=0",
        "fallback_required=1",
        'if [[ "$fallback_required" -eq 1 ]]; then',
        "exit 1",
    )
    assert all(fragment in run_evidence["run"] for fragment in required_fragments)  # type: ignore[index]
    assert run_evidence["env"]["EVIDENCE_BASE_BRANCH"]  # type: ignore[index]
    assert "workflow_dispatch" in workflow["on"]  # type: ignore[operator]


def _assert_retention_contract(workflow: dict[str, object]) -> None:
    publish = _step_by_name(workflow, "Publish Requirements evidence summary")
    upload = _step_by_name(workflow, "Upload requirements evidence artifact")
    enforce = _step_by_name(workflow, "Enforce requirements evidence verdict")
    assert publish["if"] == "always()"  # type: ignore[index]
    assert "GITHUB_STEP_SUMMARY" in publish["run"]  # type: ignore[index]
    assert upload["if"] == "always()"  # type: ignore[index]
    assert upload["uses"] == "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a"  # type: ignore[index]
    assert upload["with"]["path"].splitlines() == [  # type: ignore[index]
        "artifacts/requirements-evidence/requirements-evidence.json",
        "artifacts/requirements-evidence/requirements-evidence.md",
        "artifacts/requirements-evidence/requirements-evidence-plan.json",
    ]
    assert enforce["if"] == "steps.run-evidence.outcome == 'failure'"  # type: ignore[index]
    assert enforce["run"] == "exit 1"  # type: ignore[index]
    assert _step_index(workflow, "Publish Requirements evidence summary") < _step_index(
        workflow, "Enforce requirements evidence verdict"
    )
    assert _step_index(workflow, "Upload requirements evidence artifact") < _step_index(
        workflow, "Enforce requirements evidence verdict"
    )


def test_requirements_evidence_workflow_uses_the_released_fixture_and_retains_reports() -> None:
    """PR enforcement must verify the fixture and publish output before failing red verdicts."""
    workflow = REPO_ROOT / ".github" / "workflows" / "requirements-evidence.yml"
    parsed = yaml.load(workflow.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)

    assert "pull_request" in parsed["on"]
    _assert_fixture_contract(parsed)
    _assert_command_contract(parsed)
    _assert_retention_contract(parsed)

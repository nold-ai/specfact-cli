"""Contract coverage for the core Requirements-evidence pull-request gate."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]
APPROVED_MODULE_COMMIT = "69f075819be5e1ceca1446b026b0417f19e584ca"


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
        "planning_maturity=test-authored",
        '--required-maturity "$planning_maturity"',
        'review_evidence="openspec/changes/${selected_change}/requirements-proof/review-evidence.json"',
        "grep -v '^openspec/changes/archive/'",
        "find openspec/changes -path 'openspec/changes/archive' -prune -o -path '*/requirements-proof/review-evidence.json' -type f -print",
        "write_failure_reports()",
        'write_failure_reports "Invalid evidence base branch: $EVIDENCE_BASE_BRANCH"',
        'if ! changed_status="$(git diff --name-status --find-renames "origin/${EVIDENCE_BASE_BRANCH}...HEAD")"; then',
        'changed_paths=""',
        'write_failure_reports "Unable to derive changed paths for $EVIDENCE_BASE_BRANCH"',
        "--plan-output artifacts/requirements-evidence/requirements-evidence-plan.json",
        '--review-evidence "$review_evidence"',
        "python scripts/requirements_proof_executor.py",
        "--junit artifacts/requirements-evidence/requirements-proof.xml",
        "uv run --locked --no-sync specfact requirements reconcile",
        "rm -f artifacts/requirements-evidence/requirements-evidence.json artifacts/requirements-evidence/requirements-evidence.md",
        "--run-stage final",
        '--source-ref "$GITHUB_SHA"',
        '--prior-red-proof "$prior_red_proof"',
        "fallback_required=0",
        "fallback_required=1",
        'if [[ "$fallback_required" -eq 1 ]]; then',
        "exit 1",
    )
    assert all(fragment in run_evidence["run"] for fragment in required_fragments)  # type: ignore[index]
    assert run_evidence["env"]["EVIDENCE_BASE_BRANCH"]  # type: ignore[index]
    assert "workflow_dispatch" in workflow["on"]  # type: ignore[operator]


def _assert_governed_trigger_contract(workflow: dict[str, object]) -> None:
    pull_request = workflow["on"]["pull_request"]  # type: ignore[index]
    assert pull_request["paths"] == [  # type: ignore[index]
        "openspec/changes/**",
        "openspec/specs/**",
        ".github/**",
        "ci/**",
        "scripts/**",
        "src/**",
        "tests/**",
    ]


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
        "artifacts/requirements-evidence/requirements-proof.xml",
        "artifacts/requirements-evidence/legacy-tdd-evidence.json",
        "artifacts/requirements-evidence/code-review.json",
    ]
    assert "steps.run-evidence.outcome == 'failure'" in enforce["if"]  # type: ignore[index]
    assert "steps.run-code-review.outcome == 'failure'" in enforce["if"]  # type: ignore[index]
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
    _assert_governed_trigger_contract(parsed)
    _assert_retention_contract(parsed)


def test_requirements_evidence_workflow_writes_reports_before_early_failure(tmp_path: Path) -> None:
    """Early setup failures must retain diagnostics for summary and artifact publication."""
    workflow = REPO_ROOT / ".github" / "workflows" / "requirements-evidence.yml"
    parsed = yaml.load(workflow.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    command = _step_by_name(parsed, "Run Requirements evidence gate")["run"]
    assert isinstance(command, str)

    cases = (
        ("invalid branch", "Invalid evidence base branch: invalid branch"),
        ("missing-base", "Unable to derive changed paths for missing-base"),
    )
    for index, (base_branch, expected_diagnostic) in enumerate(cases):
        work_directory = tmp_path / str(index)
        report_directory = work_directory / "artifacts" / "requirements-evidence"
        report_directory.mkdir(parents=True)

        result = subprocess.run(
            ["bash", "-c", command],
            cwd=work_directory,
            env={**os.environ, "EVIDENCE_BASE_BRANCH": base_branch},
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 1
        assert json.loads((report_directory / "requirements-evidence.json").read_text(encoding="utf-8")) == {
            "schema_version": 1,
            "verdict": "failed",
            "diagnostic": expected_diagnostic,
        }
        assert expected_diagnostic in (report_directory / "requirements-evidence.md").read_text(encoding="utf-8")


def test_requirements_evidence_workflow_splits_rename_endpoints_before_maturity() -> None:
    """A renamed production path must retain both source and destination for maturity selection."""
    workflow = REPO_ROOT / ".github" / "workflows" / "requirements-evidence.yml"
    parsed = yaml.load(workflow.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    command = _step_by_name(parsed, "Run Requirements evidence gate")["run"]
    assert isinstance(command, str)
    assert "while IFS=$'\\t' read -r status source_path destination_path" in command
    assert "changed_paths+=\"${source_path}\"$'\\n'" in command
    assert "R*|C*)" in command
    assert "changed_paths+=\"${destination_path}\"$'\\n'" in command


def test_requirements_evidence_workflow_ignores_archived_review_evidence() -> None:
    """Only active change records may supply CI planning and reconciliation evidence."""
    workflow = REPO_ROOT / ".github" / "workflows" / "requirements-evidence.yml"
    parsed = yaml.load(workflow.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    command = _step_by_name(parsed, "Run Requirements evidence gate")["run"]
    assert isinstance(command, str)

    assert "grep -v '^openspec/changes/archive/'" in command
    assert (
        "find openspec/changes -path 'openspec/changes/archive' -prune -o "
        "-path '*/requirements-proof/review-evidence.json' -type f -print"
    ) in command


def test_requirements_evidence_workflow_uses_digest_bound_legacy_tdd_ledger_for_r07() -> None:
    """Only the approved R07 migration may replace historical red-JUnit proof with its ledger."""
    workflow = REPO_ROOT / ".github" / "workflows" / "requirements-evidence.yml"
    parsed = yaml.load(workflow.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    command = _step_by_name(parsed, "Run Requirements evidence gate")["run"]
    assert isinstance(command, str)

    assert 'selected_change" == "requirements-07-runtime-proof-delivery"' in command
    assert "TDD_EVIDENCE.md" in command
    assert "legacy-tdd-ledger" in command
    assert "hashlib.sha256" in command
    assert 'plan_report.get("plan")' in command
    assert '--legacy-tdd-evidence "$legacy_tdd_evidence"' in command
    assert "proof-basis-ambiguous" not in command


def _assert_code_review_handoff_command(command: object) -> None:
    """Keep the review command contract independently readable and bounded."""
    assert isinstance(command, str)
    expected_fragments = (
        "uv run --locked --no-sync specfact code review run",
        "--requirements-evidence artifacts/requirements-evidence/requirements-evidence.json",
        "--enforcement full",
        "--include-tests",
        "--out artifacts/requirements-evidence/code-review.json",
        "origin/${EVIDENCE_BASE_BRANCH}...HEAD",
        '[[ -f "$review_path" ]]',
        "No changed Python files require Code Review context.",
    )
    assert all(fragment in command for fragment in expected_fragments)


def test_requirements_evidence_workflow_hands_final_proof_to_code_review() -> None:
    """Code Review receives finalized proof context without owning its verdict."""
    workflow = REPO_ROOT / ".github" / "workflows" / "requirements-evidence.yml"
    parsed = yaml.load(workflow.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    review = _step_by_name(parsed, "Run Code Review with finalized Requirements context")
    command = review["run"]

    assert review["if"] == "steps.run-evidence.outcome == 'success'"
    _assert_code_review_handoff_command(command)
    assert _step_index(parsed, "Run Requirements evidence gate") < _step_index(
        parsed, "Run Code Review with finalized Requirements context"
    )
    assert _step_index(parsed, "Run Code Review with finalized Requirements context") < _step_index(
        parsed, "Upload requirements evidence artifact"
    )

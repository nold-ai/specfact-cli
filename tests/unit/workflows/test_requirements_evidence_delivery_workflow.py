"""Contract coverage for the core Requirements-evidence pull-request gate."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]
APPROVED_MODULE_COMMIT = "69f075819be5e1ceca1446b026b0417f19e584ca"
EVIDENCE_COMMAND_FRAGMENTS = (
    '"${isolated_specfact[@]}" requirements evidence',
    '--base-ref "$evidence_base_commit"',
    'evidence_base_commit="$(git merge-base "origin/${EVIDENCE_BASE_BRANCH}" HEAD)"',
    "required_maturity=planned",
    "required_maturity=test-authored",
    "requirements/*|pyproject.toml|setup.py|uv.lock",
    "resources/templates/*|resources/schemas/*|resources/mappings/*|resources/keys/*|modules/bundle-mapper/*",
    ".github/*|ci/*|scripts/*|src/*|tools/*",
    "planning_maturity=test-authored",
    'if [[ "$exit_code" -eq 0 && "$required_maturity" != "planned" ]]; then',
    "run_stage=red",
    'if [[ "$required_maturity" == "verified" ]]; then',
    "run_stage=final",
    '--required-maturity "$planning_maturity"',
    'review_evidence="openspec/changes/${selected_change}/requirements-proof/review-evidence.json"',
    "openspec/changes/archive/*",
    "find openspec/changes -path 'openspec/changes/archive' -prune -o -path '*/requirements-proof/review-evidence.json' -type f -print",
    "write_failure_reports()",
    'write_failure_reports "Invalid evidence base branch: $EVIDENCE_BASE_BRANCH"',
    'changed_status_file="${RUNNER_TEMP}/requirements-evidence-changed-status.z"',
    'if ! git diff --name-status -z --find-renames=100% "${evidence_base_commit}..HEAD" > "$changed_status_file"; then',
    "while IFS= read -r -d '' status; do",
    'done < "$changed_status_file"',
    'write_failure_reports "Unable to derive changed paths for $EVIDENCE_BASE_BRANCH"',
    "--plan-output artifacts/requirements-evidence/requirements-evidence-plan.json",
    '--review-evidence "$review_evidence"',
    '"${isolated_python[@]}" scripts/requirements_proof_executor.py',
    "if [[ ! -s artifacts/requirements-evidence/requirements-proof.xml ]]; then",
    "--junit artifacts/requirements-evidence/requirements-proof.xml",
    '"${isolated_python[@]}" scripts/requirements_proof_provenance.py',
    '--final-ref "$EVIDENCE_FINAL_REF"',
    '--final-ref "$EVIDENCE_FINAL_REF" 2>&1)',
    '"${isolated_specfact[@]}" requirements reconcile',
    "rm -f artifacts/requirements-evidence/requirements-evidence.json artifacts/requirements-evidence/requirements-evidence.md",
    '--run-stage "$run_stage"',
    '--source-ref "$EVIDENCE_FINAL_REF"',
    '--prior-red-proof "$prior_red_proof"',
    "fallback_required=0",
    "fallback_required=1",
    'if [[ "$fallback_required" -eq 1 ]]; then',
    "exit 1",
)


def _workflow_steps(workflow: dict[str, object]) -> list[tuple[str, int, dict[str, object]]]:
    """Return typed workflow steps with their owning job and position."""
    collected: list[tuple[str, int, dict[str, object]]] = []
    jobs = cast(dict[object, object], workflow["jobs"])
    for job_name, raw_job in jobs.items():
        assert isinstance(job_name, str)
        assert isinstance(raw_job, dict)
        job = cast(dict[str, object], raw_job)
        steps = job.get("steps", [])
        assert isinstance(steps, list)
        for index, step in enumerate(steps):
            if not isinstance(step, dict):
                continue
            collected.append((job_name, index, cast(dict[str, object], step)))
    return collected


def _step_location(workflow: dict[str, object], name: str) -> tuple[str, int, dict[str, object]]:
    """Return the unique job, index, and step for a workflow step name."""
    matches = [location for location in _workflow_steps(workflow) if location[2].get("name") == name]
    assert len(matches) == 1, name
    return matches[0]


def _step_by_name(workflow: dict[str, object], name: str) -> dict[str, object]:
    return _step_location(workflow, name)[2]


def _assert_step_order(workflow: dict[str, object], earlier: str, later: str) -> None:
    """Assert two uniquely named steps run in that order within one job."""
    earlier_job, earlier_index, _ = _step_location(workflow, earlier)
    later_job, later_index, _ = _step_location(workflow, later)
    assert earlier_job == later_job
    assert earlier_index < later_index


def _run_evidence_command() -> str:
    """Load the shell command that implements the evidence gate."""
    workflow = REPO_ROOT / ".github" / "workflows" / "requirements-evidence.yml"
    parsed = yaml.load(workflow.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    command = _step_by_name(parsed, "Run Requirements evidence gate")["run"]
    assert isinstance(command, str)
    return command


def _git(repo_root: Path, *arguments: str) -> str:
    result = subprocess.run(["git", *arguments], cwd=repo_root, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def _commit(repo_root: Path, message: str) -> str:
    _git(repo_root, "add", ".")
    _git(repo_root, "commit", "--no-gpg-sign", "-m", message)
    return _git(repo_root, "rev-parse", "HEAD")


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


@dataclass(frozen=True)
class _LateRedHistory:
    repo_root: Path
    cycle_base: str
    red_ref: str
    test_path: Path
    failed_selector: str
    passed_selector: str


@dataclass(frozen=True)
class _LateRedArtifact:
    root: Path
    report: Path
    plan: Path
    junit: Path
    mapping_digest: str
    plan_digest: str


@dataclass(frozen=True)
class _LateRedFixtureOptions:
    invalid_failed_selectors: bool = False
    governed_red_path: bool = False
    stale_selected_test: bool = False
    permute_junit_selectors: bool = False
    duplicate_junit_selector: bool = False
    omit_junit_selector: bool = False
    add_junit_selector: bool = False


def _create_late_red_history(tmp_path: Path, *, governed_red_path: bool) -> _LateRedHistory:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True)
    _git(repo_root, "init")
    _git(repo_root, "config", "user.email", "requirements@example.test")
    _git(repo_root, "config", "user.name", "Requirements proof")
    (repo_root / "README.md").write_text("# proof\n", encoding="utf-8")
    cycle_base = _commit(repo_root, "chore: cycle base")
    test_path = repo_root / "tests" / "test_proof.py"
    test_path.parent.mkdir()
    test_path.write_text(
        "def test_fails() -> None:\n    assert False\n\ndef test_passes() -> None:\n    assert True\n",
        encoding="utf-8",
    )
    if governed_red_path:
        governed_path = repo_root / "src" / "smuggled.py"
        governed_path.parent.mkdir()
        governed_path.write_text("SMUGGLED = True\n", encoding="utf-8")
    return _LateRedHistory(
        repo_root=repo_root,
        cycle_base=cycle_base,
        red_ref=_commit(repo_root, "test: reproduce review finding"),
        test_path=test_path,
        failed_selector="tests/test_proof.py::test_fails",
        passed_selector="tests/test_proof.py::test_passes",
    )


def _write_late_red_artifact(
    tmp_path: Path,
    history: _LateRedHistory,
    options: _LateRedFixtureOptions,
) -> _LateRedArtifact:
    root = tmp_path / "artifact"
    root.mkdir()
    failed_case = (
        b'<testcase><properties><property name="specfact.selector" value="tests/test_proof.py::test_fails"/>'
        b'<property name="specfact.runner" value="pytest"/><property name="specfact.python" value="3.12"/>'
        b'<property name="specfact.pytest" value="9.1"/></properties><failure/></testcase>'
    )
    passed_case = (
        b'<testcase><properties><property name="specfact.selector" value="tests/test_proof.py::test_passes"/>'
        b'<property name="specfact.runner" value="pytest"/><property name="specfact.python" value="3.12"/>'
        b'<property name="specfact.pytest" value="9.1"/></properties></testcase>'
    )
    if options.duplicate_junit_selector:
        cases = failed_case + passed_case + passed_case
    elif options.omit_junit_selector:
        cases = failed_case
    elif options.add_junit_selector:
        cases = failed_case + passed_case + passed_case.replace(b"test_passes", b"test_extra")
    else:
        cases = passed_case + failed_case if options.permute_junit_selectors else failed_case + passed_case
    junit = b"<testsuite>" + cases + b"</testsuite>"
    junit_path = root / "requirements-proof.xml"
    junit_path.write_bytes(junit)
    mapping_digest = f"sha256:{'a' * 64}"
    plan_digest = f"sha256:{'b' * 64}"
    plan_path = root / "requirements-evidence-plan.json"
    _write_json(
        plan_path,
        {
            "gate_decision": "pass",
            "plan": {
                "cases": [
                    {"node_id": history.failed_selector, "runner": "pytest"},
                    {"node_id": history.passed_selector, "runner": "pytest"},
                ],
                "mapping_digest": mapping_digest,
                "plan_digest": plan_digest,
            },
        },
    )
    report_path = root / "requirements-evidence.json"
    _write_json(
        report_path,
        {
            "delivery_status": "incomplete",
            "gate_decision": "fail",
            "observed_maturity": "incomplete",
            "required_maturity": "verified",
            "verdict": "failed",
            "mapping_digest": mapping_digest,
            "plan_digest": plan_digest,
            "execution_proof": {
                "junit_digest": f"sha256:{hashlib.sha256(junit).hexdigest()}",
                "run_stage": "final",
                "selectors": [history.failed_selector, history.passed_selector],
                "source_ref": history.red_ref,
            },
        },
    )
    return _LateRedArtifact(root, report_path, plan_path, junit_path, mapping_digest, plan_digest)


def _write_late_red_manifest(
    history: _LateRedHistory, artifact: _LateRedArtifact, *, invalid_failed_selectors: bool
) -> Path:
    manifest_path = (
        history.repo_root
        / "openspec/changes/fix-release-promotion-security-gates/requirements-proof/late-red-evidence.json"
    )
    failed_selectors = [history.passed_selector] if invalid_failed_selectors else [history.failed_selector]
    _write_json(
        manifest_path,
        {
            "schema_version": "1",
            "kind": "late-review-red-proof",
            "repository": "nold-ai/specfact-cli",
            "issue": 692,
            "pull_request": 703,
            "base_branch": "dev",
            "head_branch": "bugfix/692-security-patch-clean-replay",
            "change_id": "fix-release-promotion-security-gates",
            "cycle_base_commit": history.cycle_base,
            "cycle_base_tree": _git(history.repo_root, "rev-parse", f"{history.cycle_base}^{{tree}}"),
            "red_commit": history.red_ref,
            "red_tree": _git(history.repo_root, "rev-parse", f"{history.red_ref}^{{tree}}"),
            "run_id": 11,
            "artifact_id": 22,
            "artifact_digest": f"sha256:{'c' * 64}",
            "report_digest": f"sha256:{hashlib.sha256(artifact.report.read_bytes()).hexdigest()}",
            "plan_report_digest": f"sha256:{hashlib.sha256(artifact.plan.read_bytes()).hexdigest()}",
            "junit_digest": f"sha256:{hashlib.sha256(artifact.junit.read_bytes()).hexdigest()}",
            "mapping_digest": artifact.mapping_digest,
            "plan_digest": artifact.plan_digest,
            "failed_selectors": failed_selectors,
        },
    )
    return manifest_path


def _finalize_late_red_history(history: _LateRedHistory, *, stale_selected_test: bool) -> str:
    source_path = history.repo_root / "src" / "fix.py"
    source_path.parent.mkdir(exist_ok=True)
    source_path.write_text("FIXED = True\n", encoding="utf-8")
    if stale_selected_test:
        history.test_path.write_text(
            "def test_fails() -> None:\n    assert True\n\ndef test_passes() -> None:\n    assert True\n",
            encoding="utf-8",
        )
    return _commit(history.repo_root, "fix: close review finding")


def _write_late_red_metadata(tmp_path: Path, history: _LateRedHistory, final_ref: str) -> tuple[Path, Path, Path]:
    repository = "nold-ai/specfact-cli"
    branch = "bugfix/692-security-patch-clean-replay"
    event_path = tmp_path / "event.json"
    _write_json(
        event_path,
        {
            "number": 703,
            "repository": {"full_name": repository},
            "pull_request": {
                "base": {"ref": "dev", "repo": {"full_name": repository}},
                "head": {"ref": branch, "sha": final_ref, "repo": {"full_name": repository}},
            },
        },
    )
    run_path = tmp_path / "run.json"
    _write_json(
        run_path,
        {
            "id": 11,
            "head_sha": history.red_ref,
            "head_branch": branch,
            "event": "pull_request",
            "status": "completed",
            "conclusion": "failure",
            "name": "Requirements Evidence",
            "path": ".github/workflows/requirements-evidence.yml",
            "repository": {"full_name": repository},
        },
    )
    artifacts_path = tmp_path / "artifacts.json"
    _write_json(
        artifacts_path,
        {
            "artifacts": [
                {
                    "id": 22,
                    "name": "requirements-evidence",
                    "expired": False,
                    "digest": f"sha256:{'c' * 64}",
                    "workflow_run": {"id": 11, "head_sha": history.red_ref},
                }
            ]
        },
    )
    return event_path, run_path, artifacts_path


def _late_red_fixture(
    tmp_path: Path,
    options: _LateRedFixtureOptions | None = None,
) -> tuple[list[str], Path, Path]:
    """Create one exact test-only RED cycle plus live-metadata-shaped inputs."""
    options = options or _LateRedFixtureOptions()
    history = _create_late_red_history(tmp_path, governed_red_path=options.governed_red_path)

    artifact = _write_late_red_artifact(tmp_path, history, options)

    manifest_path = _write_late_red_manifest(
        history,
        artifact,
        invalid_failed_selectors=options.invalid_failed_selectors,
    )
    final_ref = _finalize_late_red_history(history, stale_selected_test=options.stale_selected_test)

    event_path, run_path, artifacts_path = _write_late_red_metadata(tmp_path, history, final_ref)
    output_path = tmp_path / "normalized" / "red.json"
    arguments = [
        str(REPO_ROOT / "scripts" / "requirements_late_red_proof.py"),
        "--manifest",
        str(manifest_path),
        "--event",
        str(event_path),
        "--red-run",
        str(run_path),
        "--red-artifacts",
        str(artifacts_path),
        "--red-artifact-root",
        str(artifact.root),
        "--repo-root",
        str(history.repo_root),
        "--cycle-base-ref",
        history.cycle_base,
        "--final-ref",
        final_ref,
        "--trusted-provenance",
        str(REPO_ROOT / "scripts" / "requirements_proof_provenance.py"),
        "--output",
        str(output_path),
    ]
    return arguments, output_path, run_path


def _assert_fixture_contract(workflow: dict[str, object]) -> None:
    read_fixture = _step_by_name(workflow, "Read immutable module fixture")
    verify_fixture = _step_by_name(workflow, "Verify immutable module fixture")
    export_fixture = _step_by_name(workflow, "Export verified module fixture paths")
    assert "ci/module-fixture.lock.json" in read_fixture["run"]  # type: ignore[index]
    assert "nold-ai/specfact-cli-modules" in read_fixture["run"]  # type: ignore[index]
    assert f'approved_commit="{APPROVED_MODULE_COMMIT}"' in read_fixture["run"]  # type: ignore[index]
    assert 'test "$commit" = "$approved_commit"' in read_fixture["run"]  # type: ignore[index]
    assert "rev-parse HEAD" in verify_fixture["run"]  # type: ignore[index]
    assert "5d0b8e66c6cd467e6b1ad9d582e24c66b907e205" in read_fixture["run"]  # type: ignore[index]
    assert "HEAD^{tree}" in verify_fixture["run"]  # type: ignore[index]
    assert "SPECFACT_MODULES_REPO=${GITHUB_WORKSPACE}/specfact-cli-modules" in export_fixture["run"]  # type: ignore[index]
    assert "SPECFACT_MODULES_ROOTS=${GITHUB_WORKSPACE}/specfact-cli-modules/packages" in export_fixture["run"]  # type: ignore[index]


def _assert_command_contract(workflow: dict[str, object]) -> None:
    run_evidence = _step_by_name(workflow, "Run Requirements evidence gate")
    assert run_evidence["id"] == "run-evidence"  # type: ignore[index]
    assert all(fragment in run_evidence["run"] for fragment in EVIDENCE_COMMAND_FRAGMENTS)  # type: ignore[index]
    assert 'if [[ "$execution_exit" -ne 0 ]]; then' not in run_evidence["run"]  # type: ignore[index]
    assert run_evidence["env"]["EVIDENCE_BASE_BRANCH"]  # type: ignore[index]
    assert "workflow_dispatch" not in workflow["on"]  # type: ignore[operator]
    assert run_evidence["run"].count("clean_environment=(env -i") == 1  # type: ignore[union-attr]
    assert run_evidence["run"].count('"${clean_environment[@]}" "${isolated_specfact[@]}"') == 2  # type: ignore[union-attr]


def _assert_governed_trigger_contract(workflow: dict[str, object]) -> None:
    """The terminal decision must also run for no-impact pull requests."""
    assert set(workflow["on"]) == {"pull_request"}  # type: ignore[arg-type]
    pull_request = workflow["on"]["pull_request"]  # type: ignore[index]
    assert pull_request["branches"] == ["main", "dev"]  # type: ignore[index]
    assert "paths" not in pull_request  # type: ignore[operator]


def test_required_requirements_context_is_pull_request_only() -> None:
    """Manual callers cannot mint the branch-protected Requirements context."""
    workflow_path = REPO_ROOT / ".github" / "workflows" / "requirements-evidence.yml"
    workflow = yaml.load(workflow_path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    jobs = workflow["jobs"]
    assert isinstance(jobs, dict)

    assert set(workflow["on"]) == {"pull_request"}
    assert jobs["requirements-evidence-final"]["name"] == "Requirements evidence"
    producer = _step_by_name(workflow, "Run Requirements evidence gate")
    review = _step_by_name(workflow, "Run Code Review with finalized Requirements context")
    assert producer["env"]["EVIDENCE_BASE_BRANCH"] == "${{ github.base_ref }}"  # type: ignore[index]
    assert review["env"]["REVIEW_BASE_BRANCH"] == "${{ github.base_ref }}"  # type: ignore[index]


def _assert_retention_contract(workflow: dict[str, object]) -> None:
    publish = _step_by_name(workflow, "Publish Requirements evidence summary")
    upload = _step_by_name(workflow, "Persist Requirements evidence before Code Review")
    upload_review = _step_by_name(workflow, "Upload Code Review evidence artifact")
    producer_enforce = _step_by_name(workflow, "Enforce Requirements evidence producer verdict")
    review_enforce = _step_by_name(workflow, "Enforce requirements evidence verdict")
    assert publish["if"] == "always()"  # type: ignore[index]
    assert "GITHUB_STEP_SUMMARY" in publish["run"]  # type: ignore[index]
    assert upload["if"] == "always()"  # type: ignore[index]
    assert upload["uses"] == "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a"  # type: ignore[index]
    assert upload["with"]["path"].splitlines() == [  # type: ignore[index]
        "artifacts/requirements-evidence/requirements-evidence.json",
        "artifacts/requirements-evidence/requirements-evidence.md",
        "artifacts/requirements-evidence/requirements-evidence-plan.json",
        "artifacts/requirements-evidence/requirements-proof.xml",
        "artifacts/requirements-evidence/approved-legacy-tdd-ledger.md",
        "artifacts/requirements-evidence/legacy-tdd-evidence.json",
    ]
    assert upload_review["with"]["path"] == "artifacts/requirements-evidence/code-review.json"  # type: ignore[index]
    assert producer_enforce["if"] == "steps.run-evidence.outcome == 'failure'"
    assert producer_enforce["run"] == "exit 1"
    assert review_enforce["if"] == "steps.run-code-review.outcome == 'failure'"
    assert review_enforce["run"] == "exit 1"
    _assert_step_order(
        workflow, "Publish Requirements evidence summary", "Enforce Requirements evidence producer verdict"
    )
    _assert_step_order(
        workflow, "Persist Requirements evidence before Code Review", "Enforce Requirements evidence producer verdict"
    )
    _assert_step_order(workflow, "Upload Code Review evidence artifact", "Enforce requirements evidence verdict")


def _assert_prior_red_run_selection(locate: dict[str, object]) -> None:
    """Retained-proof discovery must inspect all completed, eligible runs."""
    command = locate["run"]
    assert isinstance(command, str)
    required_fragments = (
        "gh api --method GET --paginate",
        '"repos/${GITHUB_REPOSITORY}/actions/workflows/requirements-evidence.yml/runs"',
        "-f status=completed",
        "-f per_page=100",
        "--jq '.workflow_runs[] | [.id, .head_sha, .conclusion] | @tsv'",
        'current_head="$(git rev-parse HEAD)"',
        '[[ "$head_sha" != "$current_head" ]]',
        'git merge-base --is-ancestor "origin/${GITHUB_BASE_REF}" "$head_sha"',
        'git merge-base --is-ancestor "$head_sha" "$current_head"',
        'mv "$candidate_dir/requirements-evidence.json" "$candidate_dir/red.json"',
        'mv "$candidate_dir/requirements-proof.xml" "$candidate_dir/red.xml"',
        '"${isolated_python[@]}" scripts/requirements_proof_provenance.py',
        '--prior-red-proof "$candidate_dir/red.json"',
        '--base-ref "origin/${GITHUB_BASE_REF}"',
        '--final-ref "$current_head"',
        "continue",
    )
    assert all(fragment in command for fragment in required_fragments)
    assert "--status failure" not in command
    assert "--limit 100" not in command


def _assert_prior_red_download_contract(workflow: dict[str, object]) -> None:
    """A later PR run must download red evidence from an eligible prior run."""
    locate = _step_by_name(workflow, "Locate retained red proof run")
    download = _step_by_name(workflow, "Download retained red proof")
    checkout = _step_by_name(workflow, "Checkout")
    assert workflow["permissions"]["actions"] == "read"  # type: ignore[index]
    assert checkout["with"]["ref"] == "${{ github.event.pull_request.head.sha || github.sha }}"  # type: ignore[index]
    assert locate["id"] == "prior-red-run"  # type: ignore[index]
    _assert_prior_red_run_selection(locate)
    assert download["uses"] == "actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c"  # type: ignore[index]
    assert download["with"]["github-token"] == "${{ github.token }}"  # type: ignore[index]
    assert download["with"]["run-id"] == "${{ steps.prior-red-run.outputs.run-id }}"  # type: ignore[index]
    _assert_step_order(workflow, "Download retained red proof", "Run Requirements evidence gate")


def _assert_prior_red_artifact_contract(workflow: dict[str, object]) -> None:
    """The evidence gate must bind downloaded red proof to the checked-out source."""
    _assert_prior_red_download_contract(workflow)
    run_evidence = _step_by_name(workflow, "Run Requirements evidence gate")
    assert 'candidate_red_proof="${RUNNER_TEMP}/prior-red-proof/red.json"' in run_evidence["run"]  # type: ignore[index]
    assert run_evidence["env"]["EVIDENCE_FINAL_REF"] == "${{ github.event.pull_request.head.sha || github.sha }}"  # type: ignore[index]
    assert '--source-ref "$EVIDENCE_FINAL_REF"' in run_evidence["run"]  # type: ignore[index]
    assert '--final-ref "$EVIDENCE_FINAL_REF"' in run_evidence["run"]  # type: ignore[index]
    assert "openspec/changes/${selected_change}/requirements-proof/red.json" not in run_evidence["run"]  # type: ignore[index]


def test_requirements_evidence_workflow_uses_the_released_fixture_and_retains_reports() -> None:
    """PR enforcement must verify the fixture and publish output before failing red verdicts."""
    workflow = REPO_ROOT / ".github" / "workflows" / "requirements-evidence.yml"
    parsed = yaml.load(workflow.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)

    assert "pull_request" in parsed["on"]
    _assert_fixture_contract(parsed)
    _assert_command_contract(parsed)
    _assert_governed_trigger_contract(parsed)
    _assert_retention_contract(parsed)
    _assert_prior_red_artifact_contract(parsed)


def test_requirements_evidence_workflow_writes_reports_before_early_failure(tmp_path: Path) -> None:
    """Early setup failures must retain diagnostics for summary and artifact publication."""
    workflow = REPO_ROOT / ".github" / "workflows" / "requirements-evidence.yml"
    parsed = yaml.load(workflow.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    command = _step_by_name(parsed, "Run Requirements evidence gate")["run"]
    assert isinstance(command, str)

    cases = (
        ("invalid branch", "Invalid evidence base branch: invalid branch"),
        ("missing-base", "Unable to resolve immutable evidence base for missing-base"),
    )
    for index, (base_branch, expected_diagnostic) in enumerate(cases):
        work_directory = tmp_path / str(index)
        report_directory = work_directory / "artifacts" / "requirements-evidence"
        report_directory.mkdir(parents=True)

        result = subprocess.run(
            ["bash", "-c", command],
            cwd=work_directory,
            env={**os.environ, "EVIDENCE_BASE_BRANCH": base_branch, "RUNNER_TEMP": str(work_directory)},
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
    assert "--name-status -z --find-renames" in command
    assert "while IFS= read -r -d '' status; do" in command
    assert 'changed_paths+=("$source_path")' in command
    assert "R*|C*)" in command
    assert 'changed_paths+=("$destination_path")' in command


def test_requirements_evidence_workflow_fails_when_executor_omits_junit(tmp_path: Path) -> None:
    """Missing execution proof must fail even when the executor returned zero."""
    command = _run_evidence_command()
    missing_junit_branch = command.split(
        "if [[ ! -s artifacts/requirements-evidence/requirements-proof.xml ]]; then", maxsplit=1
    )[1].split("else", maxsplit=1)[0]

    assert "exit_code=1" in missing_junit_branch
    assert 'exit_code="${execution_exit:-1}"' not in missing_junit_branch
    result = subprocess.run(
        [
            "bash",
            "-c",
            f'write_failure_reports() {{ :; }}\nexecution_exit=0\n{missing_junit_branch}\nexit "$exit_code"',
        ],
        cwd=tmp_path,
        check=False,
    )

    assert result.returncode != 0


def test_requirements_evidence_workflow_disables_site_startup_for_security_validators() -> None:
    """Repository startup hooks cannot run before proof or authority validation."""
    workflow = yaml.load(
        (REPO_ROOT / ".github" / "workflows" / "requirements-evidence.yml").read_text(encoding="utf-8"),
        Loader=yaml.BaseLoader,
    )
    run_evidence = _step_by_name(workflow, "Run Requirements evidence gate")["run"]
    locate_red = _step_by_name(workflow, "Locate retained red proof run")["run"]

    assert isinstance(run_evidence, str)
    assert isinstance(locate_red, str)
    assert 'isolated_python=("${REQUIREMENTS_VALIDATOR_ROOT}/bin/python" -I -S -c' in run_evidence
    assert '"${isolated_python[@]}" scripts/requirements_proof_executor.py' in run_evidence
    assert 'isolated_python=("${REQUIREMENTS_VALIDATOR_ROOT}/bin/python" -I -S -c' in locate_red
    assert '"${isolated_python[@]}" scripts/requirements_proof_provenance.py' in locate_red
    assert '"${isolated_python[@]}" scripts/requirements_bootstrap_authority.py' in run_evidence


def test_requirements_evidence_workflow_rechecks_prefetched_proof_bytes_after_tests() -> None:
    """Candidate tests cannot replace prefetched external proof or authority inputs."""
    workflow = yaml.load(
        (REPO_ROOT / ".github" / "workflows" / "requirements-evidence.yml").read_text(encoding="utf-8"),
        Loader=yaml.BaseLoader,
    )
    run_evidence = _step_by_name(workflow, "Run Requirements evidence gate")["run"]
    prepare_authority = _step_by_name(workflow, "Prepare one-time Requirements bootstrap authority")["run"]

    assert isinstance(run_evidence, str)
    assert isinstance(prepare_authority, str)
    assert "prior_red_report_digest" in run_evidence
    assert "prior_red_junit_digest" in run_evidence
    assert "Retained red proof changed during candidate test execution." in run_evidence
    assert "bootstrap_authority_manifest.sha256" in prepare_authority
    assert "sha256sum --check --strict" in run_evidence
    assert run_evidence.index("sha256sum --check --strict") < run_evidence.index(
        "scripts/requirements_bootstrap_authority.py"
    )


def _assert_fresh_consumer_order(
    workflow: dict[str, object], outputs: dict[str, str], permissions: dict[str, str]
) -> None:
    assert outputs["prior-red-run-id"] == "${{ steps.prior-red-run.outputs.run-id }}"
    assert permissions == {"actions": "read", "contents": "read", "issues": "read"}
    _assert_step_order(
        workflow, "Restore Requirements evidence for Code Review", "Download retained red proof for validation"
    )
    _assert_step_order(
        workflow, "Download retained red proof for validation", "Reconcile Requirements evidence on fresh runner"
    )
    _assert_step_order(
        workflow,
        "Reconcile Requirements evidence on fresh runner",
        "Run Code Review with finalized Requirements context",
    )


def _assert_reconciliation_fragments(reconcile: str) -> None:
    reconcile_fragments = (
        '"$TRUSTED_PROOF_PROVENANCE"',
        '"${isolated_python[@]}"',
        "del sys.argv[1:3]",
        'source_ref="$(git rev-parse HEAD)"',
        'evidence_base_commit="$(git merge-base "origin/${GITHUB_BASE_REF}" "$source_ref")"',
        '"${isolated_specfact[@]}" requirements evidence',
        '"${isolated_specfact[@]}" requirements reconcile',
        "requirements-evidence-consumer.json",
        "required_maturity=planned",
        'git diff --name-status -z --find-renames=100% "$evidence_base_commit..$source_ref"',
        ".github/*|ci/*|scripts/*|src/*|tools/*|requirements/*|pyproject.toml|setup.py|uv.lock",
        'test "$(jq -er \'.required_maturity\' "$producer_report")" = "$required_maturity"',
        'if [[ "${#review_evidence_paths[@]}" -eq 0 ]]; then',
        "find openspec/changes -path 'openspec/changes/archive' -prune -o "
        "-path '*/requirements-proof/review-evidence.json' -type f -print | sort",
        'if [[ "${#active_review_evidence[@]}" -eq 1 ]]; then',
        'review_evidence_paths+=("${active_review_evidence[0]}")',
        'consumer_junit="${RUNNER_TEMP}/requirements-proof-consumer.xml"',
        "importlib.util.spec_from_file_location(",
        "sys.modules[executor_spec.name] = trusted_executor",
        "trusted_executor.selectors_from_plan(",
        'os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"',
        "plugins=[trusted_plugin, trusted_plugin_policy]",
        '"--noconftest"',
        '--junit "$consumer_junit"',
    )
    missing_fragments = [fragment for fragment in reconcile_fragments if fragment not in reconcile]
    assert not missing_fragments, missing_fragments


def _assert_reconciliation_order(reconcile: str) -> None:
    fallback_index = reconcile.index('if [[ "${#review_evidence_paths[@]}" -eq 0 ]]; then')
    review_path_order = (
        reconcile.index('done < "$consumer_change_paths_file"'),
        reconcile.index('elif [[ "${#consumer_changed_change_ids[@]}" -gt 1'),
        fallback_index,
        reconcile.index('if [[ "${#review_evidence_paths[@]}" -gt 1'),
    )
    assert review_path_order == tuple(sorted(review_path_order))
    execution_order = tuple(
        reconcile.index(fragment)
        for fragment in ('cmp --silent "$consumer_plan"', "pytest.main(", "reconciliation_arguments=(")
    )
    assert execution_order == tuple(sorted(execution_order))


def _assert_reconciliation_boundaries(reconcile: str, review: str) -> None:
    assert "del sys.argv[1:3]" in review
    required_fragments = ('"$TRUSTED_PROOF_EXECUTOR"', '"$TRUSTED_PROOF_PLUGIN"')
    assert all(fragment in reconcile for fragment in required_fragments)
    forbidden_fragments = (
        "runpy.run_path(trusted_executor)",
        "--junit artifacts/requirements-evidence/requirements-proof.xml",
        'cmp --silent "$consumer_report"',
    )
    assert not any(fragment in reconcile for fragment in forbidden_fragments)
    review_fragments = (
        'requirements_context="artifacts/requirements-evidence/requirements-evidence-consumer.json"',
        '--requirements-evidence "$requirements_context"',
    )
    missing_review_fragments = [fragment for fragment in review_fragments if fragment not in review]
    assert not missing_review_fragments, missing_review_fragments


def _assert_fresh_reconciliation_command(workflow: dict[str, object]) -> None:
    reconcile_step = _step_by_name(workflow, "Reconcile Requirements evidence on fresh runner")
    reconcile = reconcile_step["run"]
    review = _step_by_name(workflow, "Run Code Review with finalized Requirements context")["run"]
    assert isinstance(reconcile, str)
    assert isinstance(review, str)
    assert ("if" not in reconcile_step, reconcile_step["timeout-minutes"]) == (True, "12")
    _assert_reconciliation_fragments(reconcile)
    _assert_reconciliation_order(reconcile)
    _assert_reconciliation_boundaries(reconcile, review)


def test_fresh_consumer_reconciles_evidence_after_candidate_tests() -> None:
    """The required verdict cannot reuse validators writable by candidate tests."""
    workflow = yaml.load(
        (REPO_ROOT / ".github" / "workflows" / "requirements-evidence.yml").read_text(encoding="utf-8"),
        Loader=yaml.BaseLoader,
    )
    jobs = cast(dict[str, dict[str, object]], workflow["jobs"])
    producer = jobs["requirements-evidence-producer"]
    consumer = jobs["requirements-evidence"]
    outputs = cast(dict[str, str], producer["outputs"])
    permissions = cast(dict[str, str], consumer["permissions"])

    _assert_fresh_consumer_order(workflow, outputs, permissions)
    _assert_fresh_reconciliation_command(workflow)


def test_fresh_consumer_selects_review_evidence_for_changed_active_change() -> None:
    """Multiple active records cannot hide the one active change amended by the PR."""
    workflow = yaml.load(
        (REPO_ROOT / ".github" / "workflows" / "requirements-evidence.yml").read_text(encoding="utf-8"),
        Loader=yaml.BaseLoader,
    )
    reconcile = _step_by_name(workflow, "Reconcile Requirements evidence on fresh runner")["run"]
    assert isinstance(reconcile, str)

    required_fragments = (
        'consumer_change_paths_file="${RUNNER_TEMP}/consumer-change-paths.z"',
        'git diff --name-only -z --diff-filter=ACMR "$evidence_base_commit..$source_ref" -- openspec/changes/',
        "declare -A consumer_changed_change_ids=()",
        "openspec/changes/archive/*) continue ;;",
        'consumer_changed_change_ids["$change_id"]=1',
        'if [[ "${#consumer_changed_change_ids[@]}" -eq 1 ]]; then',
        'review_evidence_paths+=("openspec/changes/${selected_change}/requirements-proof/review-evidence.json")',
    )
    assert all(fragment in reconcile for fragment in required_fragments)
    assert reconcile.index("consumer_changed_change_ids") < reconcile.index("active_review_evidence")


def test_code_review_closure_recheck_uses_isolated_trusted_interpreter() -> None:
    """Both frozen-graph checks reject repository startup hooks before isolated installs."""
    workflow = yaml.load(
        (REPO_ROOT / ".github" / "workflows" / "requirements-evidence.yml").read_text(encoding="utf-8"),
        Loader=yaml.BaseLoader,
    )
    consumer_steps = {
        cast(str, step.get("name")): step
        for job, _, step in _workflow_steps(workflow)
        if job == "requirements-evidence"
    }
    verify = consumer_steps["Verify frozen Requirements graph"]["run"]
    install = _step_by_name(workflow, "Install frozen Code Review tools")["run"]
    assert isinstance(verify, str)
    assert isinstance(install, str)

    isolated_bootstrap = '"${REQUIREMENTS_VERIFIER_ROOT}/bin/python" -I -S -c'
    for command in (verify, install):
        assert isolated_bootstrap in command
        assert '"$verifier_site"' in command
        assert '"$TRUSTED_DELIVERY_VERIFIER"' in command
        assert "python scripts/check_reproducible_delivery.py" not in command


def _assert_late_red_command_contract(commands: str) -> None:
    required_fragments = (
        "SPECFACT_TRUSTED_REQUIREMENTS_AUTHORITY_V1",
        "nold-ai/.github",
        "trusted_requirements_authority.py",
        'test "$(git -C "$trusted_policy_root" rev-parse HEAD)" = "$trusted_policy_commit"',
        "requirements_late_red_proof.py",
        "requirements-proof/late-red-evidence.json",
        "actions/runs/${late_red_run_id}",
        "actions/runs/${late_red_run_id}/artifacts",
        "artifact-ids: ${{ steps.late-red.outputs.artifact-id }}",
        "--cycle-base-ref",
        "--final-ref",
        "--event",
        "--red-run",
        "--red-artifacts",
        "--red-artifact-root",
        "--output",
    )
    assert all(fragment in commands for fragment in required_fragments)
    assert commands.count("trusted_requirements_authority.py") >= 3
    assert commands.count("requirements_late_red_proof.py") >= 3


def _assert_late_red_job_contract(workflow: dict[str, object], job_name: str) -> None:
    steps = [step for job, _, step in _workflow_steps(workflow) if job == job_name]
    names = [step.get("name") for step in steps]
    authority_index = names.index("Validate exact final Requirements authority")
    download_index = names.index("Download exact late RED artifact")
    normalize_index = names.index("Normalize exact late RED proof")
    assert authority_index < download_index < normalize_index
    assert "continue-on-error" not in steps[authority_index]
    normalize_environment = cast(dict[str, object], steps[normalize_index].get("env", {}))
    assert normalize_environment.get("GH_TOKEN") is None
    assert normalize_environment.get("GITHUB_TOKEN") is None


def _assert_late_red_producer_order(workflow: dict[str, object]) -> None:
    producer_steps = [step for job, _, step in _workflow_steps(workflow) if job == "requirements-evidence-producer"]
    producer_names = [step.get("name") for step in producer_steps]
    assert producer_names.index("Validate exact final Requirements authority") < producer_names.index(
        "Set up frozen delivery dependencies"
    )


def _assert_late_red_final_job_contract(workflow: dict[str, object]) -> None:
    jobs = cast(dict[str, dict[str, object]], workflow["jobs"])
    execution = jobs["requirements-evidence"]
    final = jobs["requirements-evidence-final"]
    assert execution["name"] == "Requirements evidence execution"
    assert final["name"] == "Requirements evidence"
    assert final["needs"] == "requirements-evidence"
    final_steps = cast(list[dict[str, object]], final["steps"])
    final_names = [step.get("name") for step in final_steps]
    assert final_names.index("Revalidate exact final Requirements authority") < final_names.index(
        "Normalize exact late RED proof on fresh runner"
    )
    assert final_names.index("Normalize exact late RED proof on fresh runner") < final_names.index(
        "Reconcile final Requirements verdict on fresh runner"
    )
    final_commands = "\n".join(str(step.get("run", "")) for step in final_steps)
    assert "pytest.main(" not in final_commands
    assert all(not str(step.get("uses", "")).startswith("./") for step in final_steps)


def _assert_late_red_workflow_contract(workflow: dict[str, object]) -> None:
    commands = "\n".join(
        cast(str, step.get("run", "")) for _, _, step in _workflow_steps(workflow) if isinstance(step.get("run"), str)
    )
    _assert_late_red_command_contract(commands)
    for job_name in ("requirements-evidence-producer", "requirements-evidence"):
        _assert_late_red_job_contract(workflow, job_name)
    _assert_late_red_producer_order(workflow)
    _assert_late_red_final_job_contract(workflow)


def _assert_normalized_late_red_report(normalized: dict[str, object], output_path: Path) -> None:
    assert normalized["gate_decision"] == "pass"
    assert normalized["observed_maturity"] == "red"
    assert output_path.with_suffix(".xml").is_file()


def _assert_normalized_late_red_execution(normalized: dict[str, object]) -> None:
    execution_proof = cast(dict[str, object], normalized["execution_proof"])
    assert execution_proof["run_stage"] == "red"
    assert execution_proof["source_tree"]
    assert execution_proof["merge_base"]
    assert execution_proof["test_file_digests"]
    assert execution_proof["toolchain_identity"]
    assert len(cast(list[object], execution_proof["selectors"])) == 2


def _assert_permuted_late_red_is_accepted(tmp_path: Path) -> None:
    options = _LateRedFixtureOptions(permute_junit_selectors=True)
    permuted_arguments, permuted_output, _ = _late_red_fixture(tmp_path, options)
    permuted = subprocess.run([sys.executable, *permuted_arguments], check=False, capture_output=True, text=True)
    assert permuted.returncode == 0, permuted.stderr
    assert permuted_output.is_file()


def _assert_late_red_happy_path(tmp_path: Path) -> None:
    arguments, output_path, _run_path = _late_red_fixture(tmp_path)
    accepted = subprocess.run([sys.executable, *arguments], check=False, capture_output=True, text=True)
    assert accepted.returncode == 0, accepted.stderr
    normalized = cast(dict[str, object], json.loads(output_path.read_text(encoding="utf-8")))
    _assert_normalized_late_red_report(normalized, output_path)
    _assert_normalized_late_red_execution(normalized)
    _assert_permuted_late_red_is_accepted(tmp_path / "permuted")


def _assert_late_red_rejections(tmp_path: Path) -> None:
    arguments, _, run_path = _late_red_fixture(tmp_path / "wrong-run")

    run = json.loads(run_path.read_text(encoding="utf-8"))
    run["head_sha"] = "0" * 40
    _write_json(run_path, run)
    rejected = subprocess.run([sys.executable, *arguments], check=False, capture_output=True, text=True)
    assert rejected.returncode == 1
    assert rejected.stderr == "late-red-proof-invalid\n"

    for name, options in (
        ("wrong-failures", _LateRedFixtureOptions(invalid_failed_selectors=True)),
        ("production-red", _LateRedFixtureOptions(governed_red_path=True)),
        ("stale-test", _LateRedFixtureOptions(stale_selected_test=True)),
        ("duplicate-selector", _LateRedFixtureOptions(duplicate_junit_selector=True)),
        ("missing-selector", _LateRedFixtureOptions(omit_junit_selector=True)),
        ("extra-selector", _LateRedFixtureOptions(add_junit_selector=True)),
    ):
        invalid_arguments, _, _ = _late_red_fixture(tmp_path / name, options)
        invalid = subprocess.run([sys.executable, *invalid_arguments], check=False, capture_output=True, text=True)
        assert invalid.returncode == 1
        assert invalid.stderr == "late-red-proof-invalid\n"


def test_late_amendment_requires_exact_authority_bound_red_artifact(tmp_path: Path) -> None:
    """A late RED lane remains final-tree-bound, exact, live, and fail closed."""
    workflow = yaml.load(
        (REPO_ROOT / ".github" / "workflows" / "requirements-evidence.yml").read_text(encoding="utf-8"),
        Loader=yaml.BaseLoader,
    )
    _assert_late_red_workflow_contract(workflow)
    _assert_late_red_happy_path(tmp_path / "accepted")
    _assert_late_red_rejections(tmp_path / "rejected")


def test_fresh_consumer_authenticates_retained_red_run_and_artifact() -> None:
    """Retained red bytes must be bound to the live run and immutable artifact identity."""
    parsed = yaml.load(
        (REPO_ROOT / ".github" / "workflows" / "requirements-evidence.yml").read_text(encoding="utf-8"),
        Loader=yaml.BaseLoader,
    )
    locate = _step_by_name(parsed, "Locate retained red proof run")["run"]
    authenticate = _step_by_name(parsed, "Authenticate retained red proof run")["run"]
    download = _step_by_name(parsed, "Download retained red proof for validation")
    reconcile = _step_by_name(parsed, "Reconcile Requirements evidence on fresh runner")["run"]
    assert isinstance(locate, str)
    assert isinstance(authenticate, str)
    assert isinstance(reconcile, str)
    download_with = cast(dict[str, str], download["with"])

    assert '[[ "$conclusion" == "failure" ]]' in locate
    for fragment in (
        "actions/runs/${PRIOR_RED_RUN_ID}",
        ".repository.full_name == $repository",
        '.name == "Requirements Evidence"',
        '.path == ".github/workflows/requirements-evidence.yml"',
        '.event == "pull_request"',
        '.status == "completed"',
        '.conclusion == "failure"',
        ".head_branch == $head_branch",
        "actions/runs/${PRIOR_RED_RUN_ID}/artifacts",
        ".workflow_run.id == $run_id",
        ".workflow_run.head_sha == $head_sha",
        ".expired == false",
        '.name == "requirements-evidence"',
        "printf 'artifact-id=%s\\n' \"$artifact_id\"",
        "printf 'artifact-digest=%s\\n' \"$artifact_digest\"",
        "printf 'head-sha=%s\\n' \"$red_head_sha\"",
    ):
        assert fragment in authenticate
    assert download_with["artifact-ids"] == "${{ steps.consumer-red.outputs.artifact-id }}"
    assert download_with["run-id"] == "${{ needs.requirements-evidence-producer.outputs.prior-red-run-id }}"
    assert 'proof_source_ref="$(jq -er \'.execution_proof.source_ref\' "$prior_red_proof")"' in reconcile
    assert 'test "$proof_source_ref" = "$PRIOR_RED_HEAD_SHA"' in reconcile


def _assert_trusted_core_materialization(materialize: str) -> None:
    materialize_fragments = (
        'base_commit="$(git merge-base "origin/${GITHUB_BASE_REF}" HEAD)"',
        'git archive "$base_commit" --',
        ".pylintrc",
        "src/specfact_cli",
        "requirements/ci/locked.txt",
        "requirements/code-review/locked.txt",
        "scripts/requirements_proof_provenance.py",
        "TRUSTED_REQUIREMENTS_CORE=$trusted_core_root/src",
        "TRUSTED_PYLINTRC=$trusted_core_root/.pylintrc",
    )
    assert all(fragment in materialize for fragment in materialize_fragments)


def _assert_trusted_consumer_order(consumer_steps: list[dict[str, object]]) -> None:
    consumer_step_names = [cast(str, step.get("name", "")) for step in consumer_steps]
    materialize_index = consumer_step_names.index("Materialize trusted Requirements core")
    verifier_index = consumer_step_names.index("Create trusted Requirements verifier environment")
    proof_index = consumer_step_names.index("Verify frozen Requirements graph")
    install_index = consumer_step_names.index("Install frozen Code Review tools")
    assert materialize_index < verifier_index < proof_index < install_index


def test_fresh_consumer_uses_authenticated_base_core_for_validation() -> None:
    """Candidate core code cannot implement its own reconciliation or review verdict."""
    parsed = yaml.load(
        (REPO_ROOT / ".github" / "workflows" / "requirements-evidence.yml").read_text(encoding="utf-8"),
        Loader=yaml.BaseLoader,
    )
    materialize = _step_by_name(parsed, "Materialize trusted Requirements core")["run"]
    consumer = cast(dict[str, object], cast(dict[str, object], parsed["jobs"])["requirements-evidence"])
    consumer_steps = cast(list[dict[str, object]], consumer["steps"])
    reconcile = _step_by_name(parsed, "Reconcile Requirements evidence on fresh runner")["run"]
    review = _step_by_name(parsed, "Run Code Review with finalized Requirements context")["run"]

    assert isinstance(materialize, str)
    assert isinstance(reconcile, str)
    assert isinstance(review, str)
    assert all(step.get("uses") != "./.github/actions/setup-frozen-python" for step in consumer_steps)
    assert (
        _step_by_name(parsed, "Set up uv for trusted Requirements consumer")["uses"]
        == "astral-sh/setup-uv@d0cc045d04ccac9d8b7881df0226f9e82c39688e"
    )
    _assert_trusted_core_materialization(materialize)
    _assert_trusted_consumer_order(consumer_steps)
    trusted_fragments = ('"$TRUSTED_REQUIREMENTS_CORE"', "sys.path.insert(0, trusted_core)")
    assert all(fragment in reconcile and fragment in review for fragment in trusted_fragments)
    assert '"$TRUSTED_PROOF_PROVENANCE"' in reconcile
    assert all('"${GITHUB_WORKSPACE}/src"' not in command for command in (reconcile, review))


def test_fresh_consumer_binds_each_legacy_lane_to_approved_digests() -> None:
    """Matching attacker-controlled ledger fields cannot mint a legacy final verdict."""
    parsed = yaml.load(
        (REPO_ROOT / ".github" / "workflows" / "requirements-evidence.yml").read_text(encoding="utf-8"),
        Loader=yaml.BaseLoader,
    )
    reconcile = _step_by_name(parsed, "Reconcile Requirements evidence on fresh runner")["run"]
    assert isinstance(reconcile, str)
    required_fragments = (
        "requirements-07-runtime-proof-delivery)",
        'expected_ledger_digest="sha256:d6e35c934757c08fd1f3e3071fc02b92b080c009ba5e428f6ea2888e7cd5e8c3"',
        'expected_mapping_digest="sha256:eccdf006792d8910c54a773e30967886063b4e30c99c180bc36d7372b1bbd9ef"',
        'expected_plan_digest="sha256:27ea6e6bcea0d68d68688b89fc8f89315d213b96918f4f76979484756fd8335e"',
        "fix-retained-red-proof-provenance)",
        'expected_ledger_digest="sha256:f948489e94966f4df144c5d83aa1caa6fe7a96f6ade9a4aef864794d8019b158"',
        'expected_mapping_digest="sha256:6a9413ab306eb0cf0aad62661d66c5ef684b91036766acf7021953877c9b617e"',
        'expected_plan_digest="sha256:00595739da3dd81a01032fbc2661094b8c6e2836dc38e366eae0a666e4574222"',
        ".change_id == $change_id",
        ".ledger_digest == $ledger_digest",
        ".mapping_digest == $mapping_digest",
        ".plan_digest == $plan_digest",
    )
    assert all(fragment in reconcile for fragment in required_fragments)


def test_isolated_requirements_installs_follow_reproducible_graph_proof() -> None:
    """Each isolated CI-lock install must follow a successful closure proof in its job."""
    parsed = yaml.load(
        (REPO_ROOT / ".github" / "workflows" / "requirements-evidence.yml").read_text(encoding="utf-8"),
        Loader=yaml.BaseLoader,
    )
    for install_name in ("Create isolated Requirements validator environment",):
        install_job, install_index, _ = _step_location(parsed, install_name)
        matching_proofs = [
            (job, index, step)
            for job, index, step in _workflow_steps(parsed)
            if job == install_job and step.get("name") == "Verify frozen Requirements graph"
        ]
        assert len(matching_proofs) == 1
        _, proof_index, proof = matching_proofs[0]
        proof_command = proof["run"]
        assert isinstance(proof_command, str)
        assert '"${GITHUB_WORKSPACE}/.venv/bin/python" -I -S -c' in proof_command
        assert '"${GITHUB_WORKSPACE}/.venv/lib/python3.12/site-packages"' in proof_command
        assert '"$TRUSTED_DELIVERY_VERIFIER"' in proof_command
        assert "python scripts/check_reproducible_delivery.py" not in proof_command
        assert proof_index < install_index


def test_requirements_evidence_workflow_ignores_archived_review_evidence() -> None:
    """Archived moves are ignored without allowing deletion-only evidence bypasses."""
    command = _run_evidence_command()

    assert "openspec/changes/archive/*" in command
    assert "is_complete_branch_archive_move()" in command
    assert '[[ "$status" == "R100"' in command
    assert 'git ls-tree -r -z --name-only "$evidence_base_commit"' in command
    assert 'destination_mode" != "$source_mode" || "$source_hash" != "$destination_hash"' in command
    assert '"$destination_count" -eq "$source_count"' in command
    assert '[[ -n "$active_entry" ]] || ! is_complete_branch_archive_move "$change_id"' in command
    assert '[[ -e "$changed_path" ]] || continue' not in command
    assert (
        "find openspec/changes -path 'openspec/changes/archive' -prune -o "
        "-path '*/requirements-proof/review-evidence.json' -type f -print"
    ) in command


def test_requirements_evidence_workflow_rejects_partial_exact_archive_move() -> None:
    """One exact rename cannot hide an otherwise active change directory."""
    command = _run_evidence_command()
    assert '[[ -n "$active_entry" ]] || ! is_complete_branch_archive_move "$change_id"' in command
    assert (
        '[[ "$archive_valid" -eq 1 && "$source_count" -gt 0 && "$destination_count" -eq "$source_count" ]]' in command
    )


def test_requirements_bootstrap_authority_is_pull_request_only() -> None:
    """Manual dispatch must not infer a PR identity for the one-time authority."""
    workflow_path = REPO_ROOT / ".github" / "workflows" / "requirements-evidence.yml"
    workflow = yaml.load(workflow_path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    run_evidence = _step_by_name(workflow, "Run Requirements evidence gate")
    command = run_evidence["run"]
    assert isinstance(command, str)
    assert run_evidence["env"]["EVIDENCE_EVENT_NAME"] == "${{ github.event_name }}"  # type: ignore[index]
    context_guard = 'if [[ "$EVIDENCE_EVENT_NAME" != "pull_request" ]]; then'
    assert context_guard in command
    assert command.index(context_guard) < command.index("bootstrap_comment_id=5431081643")
    assert "One-time Requirements bootstrap requires pull-request context." in command


def test_requirements_evidence_workflow_uses_digest_bound_legacy_tdd_ledger_for_r07() -> None:
    """Only the approved R07 migration may replace historical red-JUnit proof with its ledger."""
    workflow = REPO_ROOT / ".github" / "workflows" / "requirements-evidence.yml"
    parsed = yaml.load(workflow.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    command = _step_by_name(parsed, "Run Requirements evidence gate")["run"]
    assert isinstance(command, str)

    legacy_tdd_mapping_digest = "sha256:eccdf006792d8910c54a773e30967886063b4e30c99c180bc36d7372b1bbd9ef"
    legacy_tdd_ledger = (
        REPO_ROOT / "openspec" / "changes" / "requirements-07-runtime-proof-delivery" / "TDD_EVIDENCE.md"
    )
    approved_prefix = b"".join(legacy_tdd_ledger.read_bytes().splitlines(keepends=True)[:1143])
    legacy_tdd_ledger_digest = f"sha256:{hashlib.sha256(approved_prefix).hexdigest()}"
    required_fragments = (
        'selected_change" == "requirements-07-runtime-proof-delivery"',
        "TDD_EVIDENCE.md",
        "legacy_tdd_line_count=1143",
        f'legacy_tdd_ledger_digest="{legacy_tdd_ledger_digest}"',
        f'legacy_tdd_mapping_digest="{legacy_tdd_mapping_digest}"',
        'legacy_tdd_plan_digest="sha256:27ea6e6bcea0d68d68688b89fc8f89315d213b96918f4f76979484756fd8335e"',
        "read_bytes().splitlines(keepends=True)",
        "legacy_tdd_artifact",
        "legacy-tdd-ledger",
        "hashlib.sha256",
        'plan_report.get("plan")',
        "mapping_digest != approved_mapping_digest",
        "plan_digest != approved_plan_digest",
        "Legacy TDD ledger does not cover the current Requirements evidence plan",
        '--legacy-tdd-evidence "$legacy_tdd_evidence"',
    )
    assert all(fragment in command for fragment in required_fragments)
    assert "git cat-file" not in command
    assert "git show" not in command
    assert "proof-basis-ambiguous" not in command


def _assert_code_review_handoff_command(command: object) -> None:
    """Keep the review command contract independently readable and bounded."""
    assert isinstance(command, str)
    expected_fragments = (
        'PATH="${PYLINT_WRAPPER}:$PATH" "${isolated_specfact[@]}" code review run',
        '--requirements-evidence "$requirements_context"',
        "--enforcement full",
        "--include-tests",
        "--out artifacts/requirements-evidence/code-review.json",
        'review_base_commit="$(git merge-base "origin/${REVIEW_BASE_BRANCH}" HEAD)"',
        'review_paths_file="${RUNNER_TEMP}/requirements-code-review-paths.z"',
        'if ! git diff --name-only -z "${review_base_commit}..HEAD"',
        'done < "$review_paths_file"',
        "while IFS= read -r -d '' review_path; do",
        '[[ -f "$review_path" ]]',
        "No changed Python files require Code Review context.",
        "Unable to derive Code Review paths.",
    )
    assert all(fragment in command for fragment in expected_fragments)
    assert "done < <(git diff" not in command


def _assert_frozen_code_review_python_tools(command: object) -> None:
    """Validate the isolated Python resolver input and its reviewed license note."""
    assert isinstance(command, str)
    command_fragments = (
        'verifier_site="${REQUIREMENTS_VERIFIER_ROOT}/lib/python3.12/site-packages"',
        '"${REQUIREMENTS_VERIFIER_ROOT}/bin/python" -I -S -c',
        '"$TRUSTED_DELIVERY_VERIFIER"',
        "uv pip install",
        "--require-hashes",
        '"$TRUSTED_CODE_REVIEW_LOCK"',
        'trusted_pylint="${review_tools}/bin/pylint"',
        'exec "$TRUSTED_PYLINT" --rcfile "$TRUSTED_PYLINTRC" --output-format json -- "$@"',
        'echo "${REQUIREMENTS_VERIFIER_ROOT}/bin"',
        'echo "PYLINT_WRAPPER=$pylint_wrapper"',
    )
    assert all(fragment in command for fragment in command_fragments)
    assert command.index('"$TRUSTED_DELIVERY_VERIFIER"') < command.index("uv pip install")
    assert "python scripts/check_reproducible_delivery.py" not in command
    _assert_frozen_code_review_license_inputs()


def _assert_frozen_code_review_license_inputs() -> None:
    """Keep the frozen Pylint version and license decision synchronized."""
    lock = (REPO_ROOT / "requirements" / "code-review" / "locked.txt").read_text(encoding="utf-8")
    requirement = (REPO_ROOT / "requirements" / "code-review" / "requirements.in").read_text(encoding="utf-8")
    assert requirement.split("#", maxsplit=1)[0].strip() == "pylint==4.0.7"
    assert "GPL-2.0-or-later" in requirement
    assert "Phase 2" in requirement
    assert "pylint==4.0.7" in lock


def _assert_review_job_boundary(parsed: dict[str, object], review: dict[str, object]) -> None:
    """Require the protected context to be emitted only by the fresh final job."""
    jobs = cast(dict[str, object], parsed["jobs"])
    producer = cast(dict[str, object], jobs["requirements-evidence-producer"])
    execution = cast(dict[str, object], jobs["requirements-evidence"])
    final = cast(dict[str, object], jobs["requirements-evidence-final"])
    assert execution["name"] == "Requirements evidence execution"
    assert execution["needs"] == "requirements-evidence-producer"
    assert execution["if"] == "always()"
    assert final["name"] == "Requirements evidence"
    assert final["needs"] == "requirements-evidence"
    assert final["if"] == "always()"
    assert "if" not in review
    assert producer["outputs"] == {
        "artifact-id": "${{ steps.upload-requirements-evidence.outputs.artifact-id }}",
        "prior-red-run-id": "${{ steps.prior-red-run.outputs.run-id }}",
    }


def _assert_review_artifact_binding(parsed: dict[str, object]) -> None:
    """Require immutable artifact-ID transfer and exact-head verification."""
    upload = _step_by_name(parsed, "Persist Requirements evidence before Code Review")
    restore = _step_by_name(parsed, "Restore Requirements evidence for Code Review")
    verify_head = _step_by_name(parsed, "Verify exact head for Code Review")
    assert upload["id"] == "upload-requirements-evidence"
    assert restore["with"] == {
        "artifact-ids": "${{ needs.requirements-evidence-producer.outputs.artifact-id }}",
        "path": "artifacts/requirements-evidence",
    }
    assert verify_head["env"] == {"EXPECTED_HEAD": "${{ github.event.pull_request.head.sha || github.sha }}"}
    assert 'test "$(git rev-parse HEAD)" = "$EXPECTED_HEAD"' in verify_head["run"]  # type: ignore[operator]


def _assert_review_handoff_order(parsed: dict[str, object]) -> None:
    """Require tools, artifact restoration, review, then artifact publication."""
    _assert_step_order(parsed, "Install frozen Code Review tools", "Restore Requirements evidence for Code Review")
    _assert_step_order(
        parsed, "Restore Requirements evidence for Code Review", "Run Code Review with finalized Requirements context"
    )
    _assert_step_order(
        parsed, "Run Code Review with finalized Requirements context", "Upload Code Review evidence artifact"
    )


def test_requirements_code_review_uses_frozen_external_tools() -> None:
    """Code Review must run its declared Pylint and BasedPyright checks from locks."""
    workflow = REPO_ROOT / ".github" / "workflows" / "requirements-evidence.yml"
    parsed = yaml.load(workflow.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    setup_node = _step_by_name(parsed, "Set up reviewed Code Review Node runtime")
    install_tools = _step_by_name(parsed, "Install frozen Code Review tools")

    assert setup_node["uses"] == "actions/setup-node@48b55a011bda9f5d6aeb4c2d9c7362e8dae4041e"
    assert setup_node["with"]["node-version"] == "24.16.0"  # type: ignore[index]
    assert "if" not in setup_node
    command = install_tools["run"]
    assert 'npm ci --ignore-scripts --prefix "$TRUSTED_BASEDPYRIGHT_ROOT"' in command  # type: ignore[operator]
    assert '"${TRUSTED_BASEDPYRIGHT_ROOT}/node_modules/.bin"' in command  # type: ignore[operator]
    _assert_step_order(
        parsed, "Install frozen Code Review tools", "Run Code Review with finalized Requirements context"
    )
    _assert_frozen_code_review_python_tools(command)


def test_requirements_evidence_workflow_hands_final_proof_to_code_review() -> None:
    """A fresh review runner receives only an immutable proof artifact."""
    workflow = REPO_ROOT / ".github" / "workflows" / "requirements-evidence.yml"
    parsed = yaml.load(workflow.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    review = _step_by_name(parsed, "Run Code Review with finalized Requirements context")
    command = review["run"]

    _assert_review_job_boundary(parsed, review)
    _assert_code_review_handoff_command(command)
    _assert_review_artifact_binding(parsed)
    _assert_review_handoff_order(parsed)


def test_requirements_evidence_workflow_binds_red_proof_before_publication() -> None:
    """Only a successfully reconciled red report may receive producer provenance before upload."""
    command = _run_evidence_command()
    binding = "--bind-red-proof artifacts/requirements-evidence/requirements-evidence.json"

    assert 'if [[ "$run_stage" == "red" && "$exit_code" -eq 0 ]]; then' in command
    assert '"${isolated_python[@]}" scripts/requirements_proof_provenance.py' in command
    assert binding in command
    assert '--base-ref "$evidence_base_commit"' in command
    assert 'write_failure_reports "Red proof binding rejected:' in command
    assert 'selected_change" == "fix-retained-red-proof-provenance"' in command
    assert "printf 'Red proof retained; final reconciliation is required.\\n'" in command
    assert "exit_code=1" in command[command.index(binding) : command.index("fallback_required=0")]
    assert command.index(binding) < command.index("fallback_required=0")


def _review_and_enforcement_steps() -> tuple[
    dict[str, object], dict[str, object], dict[str, object], dict[str, object]
]:
    """Load the proof and review steps that independently govern final PR status."""
    workflow = REPO_ROOT / ".github" / "workflows" / "requirements-evidence.yml"
    parsed = yaml.load(workflow.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    return (
        _step_by_name(parsed, "Run Code Review with finalized Requirements context"),
        _step_by_name(parsed, "Enforce Requirements evidence producer verdict"),
        _step_by_name(parsed, "Enforce Requirements evidence producer success"),
        _step_by_name(parsed, "Enforce requirements evidence verdict"),
    )


@pytest.mark.parametrize(
    "verdict",
    ["requirements-failure", "code-review-failure"],
    ids=["requirements-failure", "code-review-failure"],
)
def test_requirements_evidence_workflow_blocks_each_final_verdict(verdict: str) -> None:
    """Requirements and Code Review failures remain independently terminal."""
    review, producer_enforce, producer_guard, review_enforce = _review_and_enforcement_steps()

    if verdict == "requirements-failure":
        assert producer_enforce["if"] == "steps.run-evidence.outcome == 'failure'"
        assert producer_enforce["run"] == "exit 1"
        assert producer_guard["if"] == "needs.requirements-evidence-producer.result != 'success'"
        assert producer_guard["run"] == "exit 1"
    else:
        assert review["continue-on-error"] == "true"
        assert review_enforce["if"] == "steps.run-code-review.outcome == 'failure'"
        assert review_enforce["run"] == "exit 1"

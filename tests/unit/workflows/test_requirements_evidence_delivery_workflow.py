"""Contract coverage for the core Requirements-evidence pull-request gate."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]
APPROVED_MODULE_COMMIT = "69f075819be5e1ceca1446b026b0417f19e584ca"
EVIDENCE_COMMAND_FRAGMENTS = (
    "uv run --locked --no-sync specfact requirements evidence",
    '--base-ref "origin/${EVIDENCE_BASE_BRANCH}"',
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
    'write_failure_reports "Requirements evidence needs exactly one changed active OpenSpec change',
    "write_failure_reports()",
    'write_failure_reports "Invalid evidence base branch: $EVIDENCE_BASE_BRANCH"',
    'changed_status_file="${RUNNER_TEMP}/requirements-evidence-changed-status.z"',
    'if ! git diff --name-status -z --find-renames "origin/${EVIDENCE_BASE_BRANCH}...HEAD" > "$changed_status_file"; then',
    "while IFS= read -r -d '' status; do",
    'done < "$changed_status_file"',
    'write_failure_reports "Unable to derive changed paths for $EVIDENCE_BASE_BRANCH"',
    "--plan-output artifacts/requirements-evidence/requirements-evidence-plan.json",
    '--review-evidence "$review_evidence"',
    "python scripts/requirements_proof_executor.py",
    "if [[ ! -s artifacts/requirements-evidence/requirements-proof.xml ]]; then",
    "--junit artifacts/requirements-evidence/requirements-proof.xml",
    "python scripts/requirements_proof_provenance.py",
    '--final-ref "$EVIDENCE_FINAL_REF"',
    '--final-ref "$EVIDENCE_FINAL_REF" 2>&1)',
    "uv run --locked --no-sync specfact requirements reconcile",
    "rm -f artifacts/requirements-evidence/requirements-evidence.json artifacts/requirements-evidence/requirements-evidence.md",
    '--run-stage "$run_stage"',
    '--source-ref "$EVIDENCE_FINAL_REF"',
    '--prior-red-proof "$prior_red_proof"',
    "fallback_required=0",
    "fallback_required=1",
    'if [[ "$fallback_required" -eq 1 ]]; then',
    "exit 1",
)


def _step_by_name(workflow: dict[str, object], name: str) -> dict[str, object]:
    steps = workflow["jobs"]["requirements-evidence"]["steps"]  # type: ignore[index]
    return next(step for step in steps if step.get("name") == name)  # type: ignore[union-attr,return-value]


def _step_index(workflow: dict[str, object], name: str) -> int:
    """Return a named step's position in the evidence job."""
    steps = workflow["jobs"]["requirements-evidence"]["steps"]  # type: ignore[index]
    return next(index for index, step in enumerate(steps) if step.get("name") == name)  # type: ignore[union-attr]


def _run_evidence_command() -> str:
    """Load the shell command that implements the evidence gate."""
    workflow = REPO_ROOT / ".github" / "workflows" / "requirements-evidence.yml"
    parsed = yaml.load(workflow.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    command = _step_by_name(parsed, "Run Requirements evidence gate")["run"]
    assert isinstance(command, str)
    return command


def _bash_with_associative_arrays() -> Path:
    candidates = [Path(candidate) for candidate in (shutil.which("bash"), "/opt/homebrew/bin/bash") if candidate]
    for candidate in candidates:
        if not candidate.is_file():
            continue
        version = subprocess.run(
            [candidate, "--version"], capture_output=True, text=True, check=True
        ).stdout.splitlines()[0]
        if "version 3." not in version:
            return candidate
    pytest.skip("Bash 4+ is required for associative-array workflow coverage")
    raise AssertionError("pytest.skip must terminate control flow")


def _changed_pr_selection_script(command: str, base_branch: str) -> str:
    """Extract the workflow's real diff parser and change selector."""
    start = command.index("changed_paths=()")
    end = command.index("clean_environment=(", start)
    selection = command[start:end]
    return f"""
set -e
write_failure_reports() {{ :; }}
EVIDENCE_BASE_BRANCH={base_branch}
RUNNER_TEMP="$PWD/.runner-temp"
mkdir -p "$RUNNER_TEMP"
required_maturity=planned
changed_status_file="$RUNNER_TEMP/requirements-evidence-changed-status.z"
git diff --name-status -z --find-renames "origin/${{EVIDENCE_BASE_BRANCH}}...HEAD" > "$changed_status_file"
{selection}
printf '%s\\n' "$selected_change"
"""


def _initialize_selection_repo(tmp_path: Path) -> None:
    """Create the minimal committed repository used by branch-selection tests."""
    subprocess.run(["git", "init", "--quiet"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True)


def _commit_selection_fixture(tmp_path: Path, message: str) -> None:
    """Commit the current selection fixture without repeating Git plumbing."""
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "--quiet", "-m", message], cwd=tmp_path, check=True)


def _write_selection_review_evidence(tmp_path: Path, change_id: str) -> None:
    """Create one active review-evidence fixture."""
    review_evidence = tmp_path / "openspec" / "changes" / change_id / "requirements-proof" / "review-evidence.json"
    review_evidence.parent.mkdir(parents=True)
    review_evidence.write_text("{}\n", encoding="utf-8")


def _create_exact_archive_selection_fixture(tmp_path: Path) -> None:
    """Create a byte-identical archive beside one active change."""
    old_change = tmp_path / "openspec" / "changes" / "old-change"
    old_change.mkdir(parents=True)
    proposal = old_change / "proposal.md"
    proposal.write_text("# Old proposal\n", encoding="utf-8")
    proposal.chmod(0o755)
    (old_change / "CHANGE_VALIDATION.md").write_text("# Old validation\n", encoding="utf-8")
    _write_selection_review_evidence(tmp_path, "unrelated-change")
    _commit_selection_fixture(tmp_path, "baseline")
    subprocess.run(["git", "update-ref", "refs/remotes/origin/dev", "HEAD"], cwd=tmp_path, check=True)
    archive = tmp_path / "openspec" / "changes" / "archive" / "2026-08-27-old-change"
    archive.parent.mkdir(parents=True)
    subprocess.run(["git", "mv", str(old_change), str(archive)], cwd=tmp_path, check=True)
    _write_selection_review_evidence(tmp_path, "selected-change")
    _commit_selection_fixture(tmp_path, "archive and author")


def _create_fabricated_archive_selection_fixture(tmp_path: Path) -> None:
    """Replace an active change with unrelated same-path archive files."""
    old_change = tmp_path / "openspec" / "changes" / "old-change"
    old_change.mkdir(parents=True)
    (old_change / "proposal.md").write_text("# Old proposal\n", encoding="utf-8")
    (old_change / "CHANGE_VALIDATION.md").write_text("# Old validation\n", encoding="utf-8")
    _write_selection_review_evidence(tmp_path, "unrelated-change")
    _commit_selection_fixture(tmp_path, "baseline")
    subprocess.run(["git", "update-ref", "refs/remotes/origin/dev", "HEAD"], cwd=tmp_path, check=True)
    archive = tmp_path / "openspec" / "changes" / "archive" / "2026-08-27-old-change"
    archive.mkdir(parents=True)
    for source in old_change.iterdir():
        (archive / source.name).write_text("fabricated\n", encoding="utf-8")
        source.unlink()
    old_change.rmdir()
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "pipeline.py").write_text("print('governed')\n", encoding="utf-8")
    _commit_selection_fixture(tmp_path, "fabricated archive")


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
    assert "workflow_dispatch" in workflow["on"]  # type: ignore[operator]
    assert run_evidence["run"].count("clean_environment=(env -i") == 1  # type: ignore[union-attr]
    assert run_evidence["run"].count('"${clean_environment[@]}" uv run --locked --no-sync') == 2  # type: ignore[union-attr]


def _assert_governed_trigger_contract(workflow: dict[str, object]) -> None:
    """The terminal decision must also run for no-impact pull requests."""
    pull_request = workflow["on"]["pull_request"]  # type: ignore[index]
    assert pull_request["branches"] == ["main", "dev"]  # type: ignore[index]
    assert "paths" not in pull_request  # type: ignore[operator]


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
        "artifacts/requirements-evidence/approved-legacy-tdd-ledger.md",
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


def _assert_prior_red_run_selection(locate: dict[str, object]) -> None:
    """Retained-proof discovery must inspect all completed, eligible runs."""
    command = locate["run"]
    assert isinstance(command, str)
    required_fragments = (
        "gh api --method GET --paginate",
        '"repos/${GITHUB_REPOSITORY}/actions/workflows/requirements-evidence.yml/runs"',
        "-f status=completed",
        "-f per_page=100",
        "--jq '.workflow_runs[] | [.id, .head_sha] | @tsv'",
        'current_head="$(git rev-parse HEAD)"',
        '[[ "$head_sha" != "$current_head" ]]',
        'git merge-base --is-ancestor "origin/${GITHUB_BASE_REF}" "$head_sha"',
        'git merge-base --is-ancestor "$head_sha" "$current_head"',
        'mv "$candidate_dir/requirements-evidence.json" "$candidate_dir/red.json"',
        'mv "$candidate_dir/requirements-proof.xml" "$candidate_dir/red.xml"',
        "python scripts/requirements_proof_provenance.py",
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
    assert _step_index(workflow, "Download retained red proof") < _step_index(
        workflow, "Run Requirements evidence gate"
    )


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
        ("missing-base", "Unable to derive changed paths for missing-base"),
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


def test_requirements_evidence_workflow_ignores_archived_review_evidence() -> None:
    """Archived moves are ignored without allowing deletion-only evidence bypasses."""
    command = _run_evidence_command()

    assert "openspec/changes/archive/*" in command
    assert "is_complete_branch_archive_move()" in command
    assert "--find-renames=100%" in command
    assert 'git ls-tree -r -z --name-only "origin/${EVIDENCE_BASE_BRANCH}"' in command
    assert 'destination_entry="$(git ls-tree HEAD -- "$destination_path"' in command
    assert 'git ls-tree HEAD -- "openspec/changes/$change_id"' in command
    assert '! is_complete_branch_archive_move "$change_id"' in command
    assert '[[ -e "$changed_path" ]] || continue' not in command
    assert "find openspec/changes -path 'openspec/changes/archive'" not in command


def test_requirements_evidence_workflow_rejects_partial_exact_archive_move(tmp_path: Path) -> None:
    """One exact rename cannot hide an otherwise active change directory."""
    command = _run_evidence_command()
    bash = _bash_with_associative_arrays()
    active_directory = tmp_path / "openspec" / "changes" / "example"
    active_directory.mkdir(parents=True)
    (active_directory / "proposal.md").write_text("# proposal\n", encoding="utf-8")
    (active_directory / "tasks.md").write_text("# still active\n", encoding="utf-8")
    _initialize_selection_repo(tmp_path)
    _commit_selection_fixture(tmp_path, "baseline")
    subprocess.run(["git", "update-ref", "refs/remotes/origin/dev", "HEAD"], cwd=tmp_path, check=True)
    archive_directory = tmp_path / "openspec" / "changes" / "archive" / "2026-08-27-example"
    archive_directory.mkdir(parents=True)
    subprocess.run(
        ["git", "mv", str(active_directory / "proposal.md"), str(archive_directory)],
        cwd=tmp_path,
        check=True,
    )
    _commit_selection_fixture(tmp_path, "partial archive")

    script = _changed_pr_selection_script(command, "dev")
    partial = subprocess.run([bash, "-c", script], cwd=tmp_path, capture_output=True, text=True, check=True)
    assert partial.stdout.strip() == "example"

    subprocess.run(
        ["git", "mv", str(active_directory / "tasks.md"), str(archive_directory)],
        cwd=tmp_path,
        check=True,
    )
    _commit_selection_fixture(tmp_path, "complete archive")
    complete = subprocess.run([bash, "-c", script], cwd=tmp_path, capture_output=True, text=True, check=True)
    assert complete.stdout.strip() == "", complete.stderr


def test_requirements_evidence_workflow_selects_active_change_beside_complete_archive(
    tmp_path: Path,
) -> None:
    """A byte-identical archive does not hide the active PR change."""
    command = _run_evidence_command()
    bash = _bash_with_associative_arrays()
    _initialize_selection_repo(tmp_path)
    _create_exact_archive_selection_fixture(tmp_path)

    result = subprocess.run(
        [bash, "-c", _changed_pr_selection_script(command, "dev")],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    )

    assert result.stdout.strip() == "selected-change"


def test_requirements_evidence_workflow_rejects_fabricated_archive_fallback(tmp_path: Path) -> None:
    """A same-path fabricated archive cannot redirect approval to unrelated evidence."""
    command = _run_evidence_command()
    bash = _bash_with_associative_arrays()
    _initialize_selection_repo(tmp_path)
    _create_fabricated_archive_selection_fixture(tmp_path)

    result = subprocess.run(
        [bash, "-c", _changed_pr_selection_script(command, "dev")],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "old-change has no regular review-evidence record" in result.stderr


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
        "uv run --locked --no-sync specfact code review run",
        "--requirements-evidence artifacts/requirements-evidence/requirements-evidence.json",
        "--enforcement full",
        "--include-tests",
        "--out artifacts/requirements-evidence/code-review.json",
        "origin/${EVIDENCE_BASE_BRANCH}...HEAD",
        "git diff --name-only -z",
        "while IFS= read -r -d '' review_path; do",
        '[[ -f "$review_path" ]]',
        "No changed Python files require Code Review context.",
    )
    assert all(fragment in command for fragment in expected_fragments)


def _assert_frozen_code_review_python_tools(command: object) -> None:
    """Validate the isolated Python resolver input and its reviewed license note."""
    assert isinstance(command, str)
    assert "uv pip install" in command
    assert "--require-hashes" in command
    assert "requirements/code-review/locked.txt" in command
    lock = (REPO_ROOT / "requirements" / "code-review" / "locked.txt").read_text(encoding="utf-8")
    requirement = (REPO_ROOT / "requirements" / "code-review" / "requirements.in").read_text(encoding="utf-8")
    assert requirement.split("#", maxsplit=1)[0].strip() == "pylint==4.0.7"
    assert "GPL-2.0-or-later" in requirement
    assert "Phase 2" in requirement
    assert "pylint==4.0.7" in lock


def test_requirements_code_review_uses_frozen_external_tools() -> None:
    """Code Review must run its declared Pylint and BasedPyright checks from locks."""
    workflow = REPO_ROOT / ".github" / "workflows" / "requirements-evidence.yml"
    parsed = yaml.load(workflow.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    setup_node = _step_by_name(parsed, "Set up reviewed Code Review Node runtime")
    install_tools = _step_by_name(parsed, "Install frozen Code Review tools")

    assert setup_node["uses"] == "actions/setup-node@48b55a011bda9f5d6aeb4c2d9c7362e8dae4041e"
    assert setup_node["with"]["node-version"] == "24.16.0"  # type: ignore[index]
    assert setup_node["if"] == "steps.run-evidence.outcome == 'success'"
    command = install_tools["run"]
    assert "npm ci --ignore-scripts --prefix tools/basedpyright" in command  # type: ignore[operator]
    assert "tools/basedpyright/node_modules/.bin" in command  # type: ignore[operator]
    assert _step_index(parsed, "Install frozen Code Review tools") < _step_index(
        parsed, "Run Code Review with finalized Requirements context"
    )
    _assert_frozen_code_review_python_tools(command)


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


def test_requirements_evidence_code_review_setup_does_not_persist_an_npm_cache() -> None:
    """Module-owned evidence code must not be followed by a persistent npm cache hook."""
    workflow_path = REPO_ROOT / ".github" / "workflows" / "requirements-evidence.yml"
    workflow = yaml.load(workflow_path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    setup_node = _step_by_name(workflow, "Set up reviewed Code Review Node runtime")
    setup_inputs = setup_node.get("with", {})
    assert isinstance(setup_inputs, dict)
    assert "cache" not in setup_inputs
    assert "cache-dependency-path" not in setup_inputs


def test_requirements_evidence_workflow_binds_red_proof_before_publication() -> None:
    """Only a successfully reconciled red report may receive producer provenance before upload."""
    command = _run_evidence_command()
    binding = "--bind-red-proof artifacts/requirements-evidence/requirements-evidence.json"

    assert 'if [[ "$run_stage" == "red" && "$exit_code" -eq 0 ]]; then' in command
    assert "python scripts/requirements_proof_provenance.py" in command
    assert binding in command
    assert '--base-ref "origin/${EVIDENCE_BASE_BRANCH}"' in command
    assert 'write_failure_reports "Red proof binding rejected:' in command
    assert 'selected_change" == "fix-retained-red-proof-provenance"' in command
    assert "printf 'Red proof retained; final reconciliation is required.\\n'" in command
    assert "exit_code=1" in command[command.index(binding) : command.index("fallback_required=0")]
    assert command.index(binding) < command.index("fallback_required=0")


def _review_and_enforcement_steps() -> tuple[dict[str, object], dict[str, object]]:
    """Load the two workflow steps that independently govern final PR status."""
    workflow = REPO_ROOT / ".github" / "workflows" / "requirements-evidence.yml"
    parsed = yaml.load(workflow.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    return (
        _step_by_name(parsed, "Run Code Review with finalized Requirements context"),
        _step_by_name(parsed, "Enforce requirements evidence verdict"),
    )


@pytest.mark.parametrize(
    ("review_field", "review_value", "terminal_failure"),
    [
        ("if", "steps.run-evidence.outcome == 'success'", "steps.run-evidence.outcome == 'failure'"),
        ("continue-on-error", "true", "steps.run-code-review.outcome == 'failure'"),
    ],
    ids=("requirements-failure", "code-review-failure"),
)
def test_requirements_evidence_workflow_blocks_each_final_verdict(
    review_field: str,
    review_value: str,
    terminal_failure: str,
) -> None:
    """Requirements and Code Review failures remain independently terminal."""
    review, enforce = _review_and_enforcement_steps()

    assert review[review_field] == review_value
    assert terminal_failure in enforce["if"]  # type: ignore[index]

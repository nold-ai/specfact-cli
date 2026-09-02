"""Focused red/green contracts for the #692 security patch."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any, cast

import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]


def _load_script(name: str) -> Any:
    path = REPO_ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _workflow(path: str) -> dict[str, Any]:
    payload = yaml.safe_load((REPO_ROOT / path).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return cast(dict[str, Any], payload)


def _on_block(workflow: dict[str, Any]) -> dict[str, Any]:
    value = workflow.get("on", cast(dict[object, Any], workflow).get(True))
    assert isinstance(value, dict)
    return cast(dict[str, Any], value)


def _named_step(job: dict[str, Any], name: str) -> dict[str, Any]:
    steps = job.get("steps")
    assert isinstance(steps, list)
    for item in steps:
        if isinstance(item, dict):
            step = cast(dict[str, Any], item)
            if step.get("name") == name:
                return step
    raise AssertionError(name)


def _assert_fresh_review_job(jobs: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return producer and review jobs after checking the isolated final context."""
    producer = cast(dict[str, Any], jobs["requirements-evidence-producer"])
    review = cast(dict[str, Any], jobs["requirements-evidence"])
    assert review["name"] == "Requirements evidence"
    assert review["needs"] == "requirements-evidence-producer"
    assert review["if"] == "always()"
    return producer, review


def _assert_exact_review_checkout(review: dict[str, Any]) -> None:
    """Require a clean, credential-free checkout of the immutable PR head."""
    checkout = _named_step(review, "Checkout exact head for Code Review")
    assert checkout["uses"] == "actions/checkout@df4cb1c069e1874edd31b4311f1884172cec0e10"
    assert checkout["with"]["ref"] == "${{ github.event.pull_request.head.sha || github.sha }}"  # type: ignore[index]
    assert checkout["with"]["clean"] is True  # type: ignore[index]
    assert checkout["with"]["persist-credentials"] is False  # type: ignore[index]
    verify_head = _named_step(review, "Verify exact head for Code Review")
    assert verify_head["env"]["EXPECTED_HEAD"] == "${{ github.event.pull_request.head.sha || github.sha }}"  # type: ignore[index]
    assert 'test "$(git rev-parse HEAD)" = "$EXPECTED_HEAD"' in str(verify_head.get("run", ""))


def _assert_review_tool_and_artifact_order(review: dict[str, Any]) -> None:
    """Require frozen tools before the immutable proof artifact enters the runner."""
    install = str(_named_step(review, "Install frozen Code Review tools").get("run", ""))
    assert install.index("python scripts/check_reproducible_delivery.py") < install.index("uv pip install")
    review_steps = cast(list[dict[str, Any]], review["steps"])
    step_names = [step.get("name") for step in review_steps]
    assert step_names.index("Install frozen Code Review tools") < step_names.index(
        "Restore Requirements evidence for Code Review"
    )
    restore = _named_step(review, "Restore Requirements evidence for Code Review")
    assert restore["with"]["artifact-ids"] == "${{ needs.requirements-evidence-producer.outputs.artifact-id }}"  # type: ignore[index]


def _assert_review_diff_is_fail_closed(review: dict[str, Any]) -> None:
    """Require checked tempfile transport for the immutable review diff."""
    review_command = str(_named_step(review, "Run Code Review with finalized Requirements context").get("run", ""))
    assert 'if ! git diff --name-only -z "${review_base_commit}..HEAD"' in review_command
    assert 'done < "$review_paths_file"' in review_command
    assert "done < <(git diff" not in review_command


def test_shared_frozen_setup_disables_persistent_cache() -> None:
    """The shared setup action removes both uv cache restore and save."""
    action = (REPO_ROOT / ".github" / "actions" / "setup-frozen-python" / "action.yml").read_text(encoding="utf-8")
    assert "enable-cache: false" in action
    assert "enable-cache: true" not in action
    assert "uv sync --locked --all-extras" in action


def test_compatibility_fixture_is_schedule_only_and_verified_before_export() -> None:
    """Branch-selected workflow bytes cannot manually choose and execute a fixture."""
    workflow = _workflow(".github/workflows/pr-orchestrator.yml")
    assert "workflow_dispatch" not in _on_block(workflow)
    job = cast(dict[str, Any], cast(dict[str, Any], workflow["jobs"])["dependency-compatibility"])
    assert job.get("if") == "github.event_name == 'schedule'"
    read = _named_step(job, "Read immutable module fixture")
    verify = _named_step(job, "Verify immutable module fixture")
    steps = cast(list[dict[str, Any]], job["steps"])
    names = [str(step.get("name", "")) for step in steps]
    assert names.index("Verify immutable module fixture") < names.index("Export module bundles path")
    assert '"tree"' in str(read.get("run", ""))
    assert "HEAD^{tree}" in str(verify.get("run", ""))


def test_post_fixture_node_setup_has_no_persistent_npm_cache() -> None:
    """Code Review setup cannot restore or save npm state after fixture execution."""
    workflow = _workflow(".github/workflows/requirements-evidence.yml")
    job = cast(dict[str, Any], cast(dict[str, Any], workflow["jobs"])["requirements-evidence"])
    step = _named_step(job, "Set up reviewed Code Review Node runtime")
    inputs = step.get("with", {})
    assert isinstance(inputs, dict)
    assert "cache" not in inputs
    assert "cache-dependency-path" not in inputs


def test_requirements_review_restarts_from_exact_head_after_proof() -> None:
    """Proof execution cannot share a runner or mutable tool state with review."""
    workflow = _workflow(".github/workflows/requirements-evidence.yml")
    jobs = cast(dict[str, Any], workflow["jobs"])
    producer, review = _assert_fresh_review_job(jobs)
    _named_step(producer, "Run Requirements evidence gate")
    _assert_exact_review_checkout(review)
    _assert_review_tool_and_artifact_order(review)
    _assert_review_diff_is_fail_closed(review)


def test_required_requirements_check_cannot_be_manually_dispatched() -> None:
    """Only PR provenance may emit the branch-protected Requirements context."""
    workflow = _workflow(".github/workflows/requirements-evidence.yml")
    assert set(_on_block(workflow)) == {"pull_request"}
    jobs = cast(dict[str, Any], workflow["jobs"])
    assert cast(dict[str, Any], jobs["requirements-evidence"])["name"] == "Requirements evidence"


def test_requirements_proof_step_has_no_github_token_ancestor() -> None:
    """Credentialed bootstrap retrieval is isolated from the step that runs tests."""
    workflow = _workflow(".github/workflows/requirements-evidence.yml")
    job = cast(dict[str, Any], cast(dict[str, Any], workflow["jobs"])["requirements-evidence-producer"])
    bootstrap = _named_step(job, "Prepare one-time Requirements bootstrap authority")
    proof = _named_step(job, "Run Requirements evidence gate")
    assert cast(dict[str, Any], bootstrap["env"])["GH_TOKEN"] == "${{ github.token }}"
    assert "GH_TOKEN" not in cast(dict[str, Any], proof.get("env", {}))
    proof_command = str(proof.get("run", ""))
    assert "gh api" not in proof_command
    assert "gh run download" not in proof_command


def test_requirements_archive_uses_one_immutable_merge_base() -> None:
    """Archive selection and blob identity share the exact same base commit."""
    workflow = _workflow(".github/workflows/requirements-evidence.yml")
    job = cast(dict[str, Any], cast(dict[str, Any], workflow["jobs"])["requirements-evidence-producer"])
    command = str(_named_step(job, "Run Requirements evidence gate").get("run", ""))
    assert 'evidence_base_commit="$(git merge-base "origin/${EVIDENCE_BASE_BRANCH}" HEAD)"' in command
    assert '"${evidence_base_commit}..HEAD"' in command
    assert 'git ls-tree -r -z --name-only "$evidence_base_commit"' in command
    assert 'git ls-tree "$evidence_base_commit"' in command
    assert '"origin/${EVIDENCE_BASE_BRANCH}...HEAD"' not in command


def test_every_code_review_lock_install_has_exact_closure_proof() -> None:
    """Hash identity alone never authorizes an extra package in the review lock."""
    for workflow_path, job_name in (
        (".github/workflows/pr-orchestrator.yml", "license-check"),
        (".github/workflows/requirements-evidence.yml", "requirements-evidence"),
    ):
        workflow = _workflow(workflow_path)
        job = cast(dict[str, Any], cast(dict[str, Any], workflow["jobs"])[job_name])
        install = str(
            _named_step(
                job,
                "Install frozen Code Review tools"
                if job_name == "requirements-evidence"
                else "Install frozen Code Review license scope",
            ).get("run", "")
        )
        assert install.index("python scripts/check_reproducible_delivery.py") < install.index("uv pip install")


def test_frozen_graph_uses_fixed_semgrep_mcp_pair_without_waiver() -> None:
    """All authoritative dependency surfaces select the reviewed fixed line."""
    project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dev = cast(list[str], project["project"]["optional-dependencies"]["dev"])
    scanning = cast(list[str], project["project"]["optional-dependencies"]["scanning"])
    assert "semgrep>=1.175.0" in dev
    assert "semgrep>=1.175.0" in scanning

    locked = (REPO_ROOT / "requirements" / "ci" / "locked.txt").read_text(encoding="utf-8")
    assert "semgrep==1.175.0" in locked
    assert "mcp==1.29.0" in locked
    policy = json.loads((REPO_ROOT / "ci" / "security-tool-minimum-versions.json").read_text(encoding="utf-8"))
    assert policy["minimum_versions"] == {"mcp": "1.28.1", "semgrep": "1.175.0"}
    exceptions = json.loads((REPO_ROOT / "ci" / "vulnerability-audit-exceptions.json").read_text(encoding="utf-8"))
    assert all(record.get("package") != "mcp" for record in exceptions["exceptions"])


def test_code_review_lock_is_bound_before_installation(tmp_path: Path) -> None:
    """A stale Code Review input binding fails the standard-library trust gate."""
    input_path = tmp_path / "requirements.in"
    input_path.write_text("pylint==4.0.7\n", encoding="utf-8")
    lock_path = tmp_path / "locked.txt"
    lock_path.write_text(
        f"# input-sha256: {'0' * 64}\npylint==4.0.7 \\\n    --hash=sha256:{'a' * 64}\n",
        encoding="utf-8",
    )
    checker = _load_script("check_dependency_trust_exceptions")

    errors = checker.validate_frozen_dependency_policy(
        code_review_input_path=input_path,
        code_review_lock_path=lock_path,
    )

    assert "Code Review lock input SHA-256 binding does not match requirements.in" in errors


def test_code_review_only_license_exception_does_not_leak() -> None:
    """Only the named isolated interpreter scope may consume the Pylint exception."""
    checker = _load_script("check_license_compliance")
    package = {"Name": "pylint", "Version": "4.0.7", "License": "GPL-2.0-or-later"}
    allowlist = {
        "pylint": [
            {
                "package": "pylint",
                "version": "4.0.7",
                "license": "GPL-2.0-or-later",
                "reason": "isolated review fixture",
                "scope": "code-review-only",
            }
        ]
    }

    assert checker._evaluate_env_package(package, allowlist) == 1
    assert checker._evaluate_env_package(package, allowlist, allowlist_scope="code-review-only") == 0


def test_repository_license_exceptions_match_their_actual_environments() -> None:
    """The root and isolated review scopes accept only their intended rows."""
    checker = _load_script("check_license_compliance")
    allowlist = checker._load_allowlist()
    assert allowlist["pygments"][0]["scope"] == "dev-only"
    assert allowlist["pylint"][0]["scope"] == "code-review-only"


def test_archive_selection_checks_exact_moves_and_git_failures() -> None:
    """Archive absence is accepted only after successful exact Git enumeration."""
    pre_commit = (REPO_ROOT / "scripts" / "pre-commit-quality-checks.sh").read_text(encoding="utf-8")
    workflow = (REPO_ROOT / ".github" / "workflows" / "requirements-evidence.yml").read_text(encoding="utf-8")
    for source in (pre_commit, workflow):
        assert "--find-renames=100%" in source
        assert "R100" in source
        assert "git ls-tree" in source
    assert "if ! git ls-files --cached" in pre_commit
    assert "if ! git ls-tree HEAD" in pre_commit
    assert "if ! git ls-tree -r -z --name-only" in workflow
    assert 'if ! destination_entry="$(git ls-tree HEAD' in workflow


def test_proof_executor_imports_installed_pytest_before_repository_root(tmp_path: Path) -> None:
    """A candidate root-level pytest.py cannot shadow the installed package."""
    module = _load_script("requirements_proof_executor")
    selected = tmp_path / "tests" / "test_proof.py"
    selected.parent.mkdir()
    selected.write_text("def test_selected() -> None: pass\n", encoding="utf-8")
    (tmp_path / "pytest.py").write_text("raise RuntimeError('shadowed')\n", encoding="utf-8")
    plan = {
        "schema_version": "2",
        "gate_decision": "pass",
        "observed_maturity": "test-authored",
        "plan": {
            "cases": [
                {
                    "method": "test",
                    "node_id": "tests/test_proof.py::test_selected",
                    "selector": {"runner": "pytest", "node_id": "tests/test_proof.py::test_selected"},
                }
            ]
        },
    }
    captured: list[Any] = []

    assert (
        module.execute_plan(
            plan,
            tmp_path,
            tmp_path / "proof.xml",
            command_runner=lambda command: captured.append(command) or 0,
        )
        == 0
    )
    command = captured[0]
    bootstrap = getattr(module, "PROOF_PYTEST_BOOTSTRAP", "")
    assert command.arguments[1:4] == ["-P", "-c", bootstrap]
    assert bootstrap.index("import pytest") < bootstrap.index("sys.path.append(repo_root)")


def test_invalid_utf8_authority_is_stable_metadata_failure(tmp_path: Path) -> None:
    """Malformed external bytes fail closed without exposing parser details."""
    comment = tmp_path / "comment.json"
    comment.write_bytes(b"\xff")
    artifact_root = tmp_path / "artifact"
    artifact_root.mkdir()
    arguments = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "requirements_bootstrap_authority.py"),
        "--comment",
        str(comment),
        "--commit",
        str(tmp_path / "commit.json"),
        "--run",
        str(tmp_path / "run.json"),
        "--artifacts",
        str(tmp_path / "artifacts.json"),
        "--artifact-root",
        str(artifact_root),
        "--repo-root",
        str(tmp_path),
        "--comment-id",
        "1",
        "--base-ref",
        "a" * 40,
        "--final-ref",
        "b" * 40,
        "--repository",
        "nold-ai/specfact-cli",
        "--change-id",
        "fix-release-promotion-security-gates",
        "--issue",
        "692",
        "--pull-request",
        "1",
        "--head-branch",
        "bugfix/692-security-patch-clean-replay",
    ]

    authority_validation = subprocess.run(arguments, capture_output=True, text=True, check=False)

    assert authority_validation.returncode == 1
    assert authority_validation.stderr.strip() == "bootstrap-authority-invalid:authority-metadata"


def test_doc_owner_rg_terminates_options(monkeypatch: Any, tmp_path: Path) -> None:
    """A dash-prefixed Markdown path is data, not an ripgrep option."""
    module = _load_script("check_doc_frontmatter")
    observed: list[list[str]] = []

    def run(arguments: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        observed.append(arguments)
        return subprocess.CompletedProcess(arguments, 1, "", "")

    monkeypatch.setattr(module.subprocess, "run", run)
    assert module._missing_owner_via_rg([tmp_path / "--files"]) == []
    assert observed[0][-2:] == ["--", str(tmp_path / "--files")]


def test_patch_release_uses_next_version_in_all_sources() -> None:
    """The security baseline consumes only the next semver patch."""
    expected = "0.55.4"
    project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert project["project"]["version"] == expected
    for path in ("setup.py", "src/__init__.py", "src/specfact_cli/__init__.py"):
        assert expected in (REPO_ROOT / path).read_text(encoding="utf-8")

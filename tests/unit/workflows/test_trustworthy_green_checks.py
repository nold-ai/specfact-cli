"""Workflow and hook policy tests for trustworthy green checks."""

# pyright: reportUnknownMemberType=false

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]
PR_ORCHESTRATOR = REPO_ROOT / ".github" / "workflows" / "pr-orchestrator.yml"
SIGN_MODULES = REPO_ROOT / ".github" / "workflows" / "sign-modules.yml"
PRE_COMMIT_CONFIG = REPO_ROOT / ".pre-commit-config.yaml"
CODERABBIT_CONFIG = REPO_ROOT / ".coderabbit.yaml"
LEGACY_ACTIONLINT_RUNNER = REPO_ROOT / "scripts" / "run_actionlint.sh"


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict), f"Expected mapping at {path}"
    return cast(dict[str, Any], data)


def _workflow_on_block(workflow: dict[str, Any]) -> dict[str, Any]:
    """Return the Actions trigger block, accounting for YAML 1.1 `on` coercion."""
    on_block = workflow.get("on")
    if on_block is None:
        on_block = cast(dict[object, Any], workflow).get(True)
    assert isinstance(on_block, dict), "Workflow must define event mappings"
    return cast(dict[str, Any], on_block)


def _load_jobs() -> dict[str, dict[str, Any]]:
    workflow = _load_yaml(PR_ORCHESTRATOR)
    jobs = workflow.get("jobs")
    assert isinstance(jobs, dict), "Expected jobs mapping in pr-orchestrator workflow"
    typed_jobs: dict[str, dict[str, Any]] = {}
    for job_name, job_value in jobs.items():
        assert isinstance(job_name, str), "Job names must be strings"
        assert isinstance(job_value, dict), f"Expected mapping for job {job_name}"
        typed_jobs[job_name] = cast(dict[str, Any], job_value)
    return typed_jobs


def _load_hooks() -> list[dict[str, Any]]:
    config = _load_yaml(PRE_COMMIT_CONFIG)
    repos = config.get("repos")
    assert isinstance(repos, list) and repos, "Expected repos list in .pre-commit-config.yaml"
    local_repo = next(
        (r for r in repos if isinstance(r, dict) and r.get("repo") == "local"),
        None,
    )
    assert isinstance(local_repo, dict), "Expected a 'repo: local' entry in .pre-commit-config.yaml"
    hooks = local_repo.get("hooks")
    assert isinstance(hooks, list), "Expected hooks list in .pre-commit-config.yaml"
    typed_hooks: list[dict[str, Any]] = []
    for hook in hooks:
        assert isinstance(hook, dict), "Each hook must be a mapping"
        typed_hooks.append(cast(dict[str, Any], hook))
    return typed_hooks


def _load_job_steps(job_name: str) -> list[dict[str, Any]]:
    jobs = _load_jobs()
    job = jobs.get(job_name)
    assert job is not None, f"Expected {job_name!r} job in pr-orchestrator"
    steps = job.get("steps")
    assert isinstance(steps, list), f"Expected steps list in {job_name!r} job"
    return [cast(dict[str, Any], step) for step in steps if isinstance(step, dict)]


def _find_named_step(job_name: str, step_name: str) -> dict[str, Any]:
    step = next((step for step in _load_job_steps(job_name) if step.get("name") == step_name), None)
    assert step is not None, f"Expected {step_name!r} step in {job_name!r} job"
    return step


def _normalized_condition(value: object) -> str:
    assert isinstance(value, str), "Expected workflow condition to be a string"
    return " ".join(value.replace('"', "'").split())


def _assert_condition_contains(value: object, expected: str, *, context: str) -> None:
    normalized = _normalized_condition(value)
    assert expected in normalized, f"{context}; got {value!r}"


def test_pr_orchestrator_pypi_version_check_gated_on_version_sources() -> None:
    """PyPI-ahead must not run on every code PR; gate matches pre-commit staged version files."""
    pypi_step = _find_named_step("tests", "Verify local version is ahead of PyPI")
    _assert_condition_contains(
        pypi_step.get("if"),
        "version_sources_changed == 'true'",
        context="PyPI-ahead step must be gated on version_sources_changed == 'true'",
    )

    run_clause = pypi_step.get("run") or ""
    assert "skip-when-version-unchanged-vs" in str(run_clause), (
        "PyPI-ahead step must invoke check_local_version_ahead_of_pypi.py with --skip-when-version-unchanged-vs"
    )
    assert "github.event.pull_request.base.sha" in str(run_clause), (
        "PyPI-ahead step must compare against the PR base SHA"
    )

    jobs = _load_jobs()
    changes_job = jobs.get("changes")
    assert isinstance(changes_job, dict), "Expected 'changes' job in pr-orchestrator"
    outputs = changes_job.get("outputs")
    assert isinstance(outputs, dict) and "version_sources_changed" in outputs, (
        "'changes' job must export 'version_sources_changed' output for downstream gating"
    )


def test_pr_orchestrator_version_sync_uses_base_sha_on_clean_ci_checkout() -> None:
    """Version-source synchronization must compare PR/push changes, not only the staged index."""
    version_step = _find_named_step("tests", "Verify version strings are synchronized")
    run_clause = str(version_step.get("run") or "")
    assert "--changed-vs" in run_clause, "Version-source sync step must pass --changed-vs in CI"
    assert "github.event.pull_request.base.sha" in run_clause, (
        "Version-source sync step must compare against the PR base SHA"
    )
    assert "github.event.before" in run_clause, (
        "Version-source sync step must compare against the push 'before' SHA when applicable"
    )


def test_pr_orchestrator_required_checks_trigger_on_every_pr_head_commit() -> None:
    """Required checks must not disappear behind workflow-level path filters."""
    workflow = _load_yaml(PR_ORCHESTRATOR)
    on_block = _workflow_on_block(workflow)
    pull_request = on_block.get("pull_request")
    push = on_block.get("push")
    assert isinstance(pull_request, dict), "pull_request trigger must be a mapping"
    assert isinstance(push, dict), "push trigger must be a mapping"
    assert "paths-ignore" not in pull_request, "Required PR workflows must still emit statuses on docs-only commits"
    assert "paths-ignore" not in push, "Required push workflows must still emit statuses on docs-only commits"


def test_pr_orchestrator_required_jobs_fail_closed() -> None:
    """Required jobs should not hide tool failures behind warn-only shell patterns."""
    required_jobs = {
        "verify-module-signatures",
        "tests",
        "compat-py311",
        "contract-first-ci",
        "cli-validation",
        "type-checking",
        "linting",
        "workflow-lint",
    }
    jobs = _load_jobs()
    for job_name in required_jobs:
        job = jobs.get(job_name)
        assert job is not None, f"Expected required job {job_name!r} in pr-orchestrator"
        assert job.get("continue-on-error") is not True, f"Required job {job_name!r} must fail closed"
        steps = job.get("steps")
        assert isinstance(steps, list), f"Expected steps list for job {job_name!r}"
        for step in steps:
            if not isinstance(step, dict):
                continue
            run = step.get("run")
            if not isinstance(run, str):
                continue
            assert "|| echo" not in run, f"Required job {job_name!r} still swallows failure with `|| echo`"
            assert "continue-on-error" not in run, f"Required job {job_name!r} must not emulate continue-on-error"


def test_pr_orchestrator_release_skip_requires_parity_proof() -> None:
    """Release fast-path skips must be gated by parity proof, not only branch names."""
    raw = PR_ORCHESTRATOR.read_text(encoding="utf-8")
    assert 'echo "skip_tests_dev_to_main=true" >> "$GITHUB_OUTPUT"' not in raw
    assert "git merge-base" in raw or "git rev-parse" in raw, "Expected commit-parity proof in release skip logic"
    jobs = _load_jobs()
    changes = jobs.get("changes")
    assert changes is not None, "Expected changes job in pr-orchestrator"
    outputs = changes.get("outputs")
    assert isinstance(outputs, dict), "Expected outputs mapping for changes job"
    assert "skip_tests_dev_to_main" in outputs, "Release skip decision should remain explicit"
    normalized_conditions = [
        _normalized_condition(step.get("if")) for step in _load_job_steps("tests") if isinstance(step.get("if"), str)
    ]
    assert any(
        "needs.changes.outputs.skip_tests_dev_to_main" in cond and "== 'true'" in cond for cond in normalized_conditions
    ), "Expected a condition checking skip_tests_dev_to_main == 'true'"
    assert any(
        "needs.changes.outputs.skip_tests_dev_to_main" in cond and "!= 'true'" in cond for cond in normalized_conditions
    ), "Expected a condition checking skip_tests_dev_to_main != 'true'"


def test_pr_orchestrator_advisory_jobs_are_named_as_advisory() -> None:
    """Advisory jobs should advertise their non-blocking status in the emitted check name."""
    jobs = _load_jobs()
    quality_gate = jobs.get("quality-gates")
    assert quality_gate is not None, "Expected quality-gates job in pr-orchestrator"
    name = quality_gate.get("name")
    assert isinstance(name, str)
    assert "Advisory" in name


def test_pr_orchestrator_contract_first_job_uses_hatch_contract_test() -> None:
    """Contract-first CI should use the hatch contract-test script (no CLI bundle dependency)."""
    raw = PR_ORCHESTRATOR.read_text(encoding="utf-8")
    assert "hatch run contract-test" in raw
    assert "hatch run specfact repro --verbose --crosshair-required --budget 120" not in raw


def test_module_signature_check_name_is_canonical_across_workflows() -> None:
    """Orchestrator and dedicated signature workflows should emit the same required check name."""
    orchestrator_jobs = _load_jobs()
    sign_modules = _load_yaml(SIGN_MODULES)
    sign_jobs = sign_modules.get("jobs")
    assert isinstance(sign_jobs, dict), "Expected jobs mapping in sign-modules workflow"
    orchestrator_name = orchestrator_jobs["verify-module-signatures"].get("name")
    sign_job = sign_jobs.get("verify")
    assert isinstance(sign_job, dict), "Expected verify job in sign-modules workflow"
    dedicated_name = sign_job.get("name")
    assert orchestrator_name == dedicated_name == "Verify Module Signatures"


CANONICAL_VERSION_SOURCE_REGEX = r"^(pyproject\.toml|setup\.py|src/__init__\.py|src/specfact_cli/__init__\.py)$"


def _assert_pre_commit_verify_and_version_hooks(by_id: dict[str, dict[str, Any]]) -> None:
    verify_hook = by_id["verify-module-signatures"]
    assert verify_hook.get("always_run") is True
    assert verify_hook.get("language") == "script"
    verify_entry = str(verify_hook.get("entry", ""))
    assert "pre-commit-verify-modules" in verify_entry
    assert "pre-commit-verify-modules.sh" in verify_entry or "pre-commit-verify-modules-signature.sh" in verify_entry
    verify_script = REPO_ROOT / "scripts" / "pre-commit-verify-modules.sh"
    assert verify_script.is_file()
    legacy_verify = REPO_ROOT / "scripts" / "pre-commit-verify-modules-signature.sh"
    assert legacy_verify.is_file()
    verify_body = verify_script.read_text(encoding="utf-8")
    assert "module-verify-policy.sh" in verify_body
    assert "exec hatch run verify-modules-signature" in verify_body
    assert "exec hatch run verify-modules-signature-pr" in verify_body
    assert "check-version-sources" in by_id
    assert "check-local-version-ahead-of-pypi" in by_id


def _assert_pypi_version_hook(by_id: dict[str, dict[str, Any]]) -> None:
    pypi_hook = by_id["check-local-version-ahead-of-pypi"]
    files_pattern = pypi_hook.get("files")
    assert files_pattern == CANONICAL_VERSION_SOURCE_REGEX, (
        "PyPI-ahead pre-commit hook 'files:' scope must match the canonical version-source set "
        f"({CANONICAL_VERSION_SOURCE_REGEX!r}); got {files_pattern!r}"
    )
    entry = str(pypi_hook.get("entry", ""))
    assert "hatch run python scripts/check_local_version_ahead_of_pypi.py" in entry


def test_pr_orchestrator_package_validation_waits_for_dependency_gates() -> None:
    jobs = _load_jobs()
    package_validation = jobs.get("package-validation")
    assert package_validation is not None, "Expected package-validation job in pr-orchestrator"
    needs = package_validation.get("needs")
    assert isinstance(needs, list), "Expected package-validation needs list"
    assert "license-check" in needs
    assert "security-audit" in needs


def _assert_pre_commit_cli_quality_block_hooks(by_id: dict[str, dict[str, Any]]) -> None:
    hook_ids = (
        "cli-block1-format",
        "cli-block1-yaml",
        "cli-block1-markdown-fix",
        "cli-block1-markdown-lint",
        "cli-block1-workflows",
        "cli-block1-lint",
        "cli-block2",
    )
    for hid in hook_ids:
        assert hid in by_id
        entry = by_id[hid].get("entry", "")
        assert "pre-commit-quality-checks.sh" in str(entry), f"{hid} must invoke quality-checks script"
    assert by_id["cli-block1-format"].get("always_run") is not True
    assert by_id["cli-block1-format"].get("files")
    assert by_id["cli-block2"].get("always_run") is True
    assert "check-doc-frontmatter" in by_id


def test_pre_commit_config_matches_modular_quality_layout() -> None:
    """Local hooks should mirror specfact-cli-modules: fail_fast, verify, block1 stages, block2."""
    config = _load_yaml(PRE_COMMIT_CONFIG)
    assert config.get("fail_fast") is True
    hooks = _load_hooks()
    by_id: dict[str, dict[str, Any]] = {}
    for h in hooks:
        hid = h.get("id")
        if isinstance(hid, str):
            by_id[hid] = h
    _assert_pre_commit_verify_and_version_hooks(by_id)
    _assert_pypi_version_hook(by_id)
    _assert_pre_commit_cli_quality_block_hooks(by_id)


def test_coderabbit_auto_review_covers_dev_and_main() -> None:
    """Automatic review coverage should be consistent for both protected integration branches."""
    config = _load_yaml(CODERABBIT_CONFIG)
    reviews = config.get("reviews")
    assert isinstance(reviews, dict), "Expected reviews block in .coderabbit.yaml"
    auto_review = reviews.get("auto_review")
    assert isinstance(auto_review, dict), "Expected auto_review block in .coderabbit.yaml"
    base_branches = auto_review.get("base_branches")
    assert isinstance(base_branches, list), "Expected base_branches list in .coderabbit.yaml"
    assert "^dev$" in base_branches
    assert "^main$" in base_branches


def test_legacy_actionlint_runner_does_not_mask_docker_failures() -> None:
    """The legacy actionlint wrapper must fail cleanly when Docker is unusable."""
    raw = LEGACY_ACTIONLINT_RUNNER.read_text(encoding="utf-8")
    lines = raw.splitlines()
    assert any("docker run --rm" in line for line in lines), "Expected docker run invocation"
    assert "docker info >/dev/null 2>&1" in raw, "Expected docker daemon reachability check"
    assert "tools/bin" not in raw, "Should not download binaries into repo tree"
    assert "go install github.com/rhysd/actionlint/cmd/actionlint@" in raw, "Expected global install guidance"
    # Both execution paths (local binary and docker) must propagate exit codes
    assert raw.count("exit $?") >= 2, "Expected exit code propagation for both local and docker paths"

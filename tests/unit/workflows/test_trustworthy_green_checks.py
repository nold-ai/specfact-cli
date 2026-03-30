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
    local_repo = repos[0]
    assert isinstance(local_repo, dict), "Expected first pre-commit repo entry to be a mapping"
    hooks = local_repo.get("hooks")
    assert isinstance(hooks, list), "Expected hooks list in .pre-commit-config.yaml"
    typed_hooks: list[dict[str, Any]] = []
    for hook in hooks:
        assert isinstance(hook, dict), "Each hook must be a mapping"
        typed_hooks.append(cast(dict[str, Any], hook))
    return typed_hooks


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
    tests_job = jobs.get("tests")
    assert tests_job is not None, "Expected tests job in pr-orchestrator"
    steps = tests_job.get("steps")
    assert isinstance(steps, list), "Expected tests job to define steps"
    skip_conditions = [step.get("if") for step in steps if isinstance(step, dict)]
    # Normalize conditions by collapsing whitespace and removing surrounding quotes for robust matching
    normalized_conditions = [
        " ".join(cond.replace('"', "'").split()) if isinstance(cond, str) else cond for cond in skip_conditions
    ]
    # Assert key patterns exist regardless of minor spacing/quoting differences
    assert any(
        "needs.changes.outputs.skip_tests_dev_to_main" in str(cond) and "== 'true'" in str(cond)
        for cond in normalized_conditions
    ), "Expected a condition checking skip_tests_dev_to_main == 'true'"
    assert any(
        "needs.changes.outputs.skip_tests_dev_to_main" in str(cond) and "!= 'true'" in str(cond)
        for cond in normalized_conditions
    ), "Expected a condition checking skip_tests_dev_to_main != 'true'"


def test_pr_orchestrator_advisory_jobs_are_named_as_advisory() -> None:
    """Advisory jobs should advertise their non-blocking status in the emitted check name."""
    jobs = _load_jobs()
    quality_gate = jobs.get("quality-gates")
    assert quality_gate is not None, "Expected quality-gates job in pr-orchestrator"
    name = quality_gate.get("name")
    assert isinstance(name, str)
    assert "Advisory" in name


def test_pr_orchestrator_contract_first_job_uses_grouped_repro_command() -> None:
    """Contract-first CI should call the stable grouped repro command path."""
    raw = PR_ORCHESTRATOR.read_text(encoding="utf-8")
    assert "hatch run specfact code repro --verbose --crosshair-required --budget 120" in raw
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


def test_pre_commit_config_installs_supported_smart_check_wrapper() -> None:
    """The supported local hook path should expose the same gate semantics as CI."""
    hooks = _load_hooks()
    matching = [hook for hook in hooks if hook.get("entry") == "scripts/pre-commit-smart-checks.sh"]
    assert matching, "Expected .pre-commit-config.yaml to expose the smart-check wrapper hook"
    hook = matching[0]
    assert hook.get("pass_filenames") is False
    assert hook.get("language") == "script"


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
    assert "docker run --rm \\" in raw
    assert (
        'docker run --rm \\\n      -v "$REPO_ROOT":/repo \\\n      -w /repo \\\n      "$DOCKER_IMAGE" -no-color\n    return 0'
        not in raw
    )
    assert "docker info >/dev/null 2>&1" in raw
    assert "tools/bin" not in raw
    assert "go install github.com/rhysd/actionlint/cmd/actionlint@latest" in raw
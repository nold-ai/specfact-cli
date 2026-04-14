"""Policy tests for sign-modules-on-approval workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "sign-modules-on-approval.yml"


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict), f"Expected mapping at {path}"
    return cast(dict[str, Any], data)


def _workflow_on_block(workflow: dict[str, Any]) -> dict[str, Any]:
    on_block = workflow.get("on")
    if on_block is None:
        on_block = cast(dict[object, Any], workflow).get(True)
    assert isinstance(on_block, dict), "Workflow must define event mappings"
    return cast(dict[str, Any], on_block)


def _job_steps(workflow: dict[str, Any], job_id: str) -> list[dict[str, Any]]:
    jobs = workflow.get("jobs")
    assert isinstance(jobs, dict), "Workflow must define jobs"
    job = jobs.get(job_id)
    assert isinstance(job, dict), f"Job {job_id!r} must be a mapping"
    steps = job.get("steps")
    assert isinstance(steps, list), f"Job {job_id!r} must define steps"
    return [cast(dict[str, Any], s) for s in steps]


def _step_run_text(step: dict[str, Any]) -> str:
    run = step.get("run")
    return run if isinstance(run, str) else ""


def _step_dict_field(step: dict[str, Any], field: str) -> dict[str, Any]:
    block = step.get(field)
    return cast(dict[str, Any], block) if isinstance(block, dict) else {}


def _find_step_by_name(steps: list[dict[str, Any]], name: str) -> dict[str, Any]:
    for step in steps:
        if step.get("name") == name:
            return step
    raise AssertionError(f"No step named {name!r}")


def _assert_pr_review_and_dispatch_triggers(on_block: dict[str, Any]) -> None:
    review = on_block.get("pull_request_review")
    assert isinstance(review, dict), "Expected pull_request_review trigger mapping"
    assert review.get("types") == ["submitted"]
    dispatch = on_block.get("workflow_dispatch")
    assert isinstance(dispatch, dict), "Expected workflow_dispatch for manual runs"
    dispatch_inputs = dispatch.get("inputs")
    assert isinstance(dispatch_inputs, dict)
    assert "base_branch" in dispatch_inputs
    assert "version_bump" in dispatch_inputs


def _assert_sign_on_approval_job_guards(jobs: dict[str, Any]) -> None:
    sign_job = jobs.get("sign-on-approval")
    assert isinstance(sign_job, dict)
    job_if = sign_job.get("if")
    assert isinstance(job_if, str)
    assert "github.event_name == 'pull_request_review'" in job_if
    assert "github.event.review.state == 'approved'" in job_if
    assert "github.event.pull_request.base.ref == 'dev'" in job_if
    assert "github.event.pull_request.base.ref == 'main'" in job_if
    assert "github.event.pull_request.head.repo.full_name == github.repository" in job_if
    perms = sign_job.get("permissions")
    assert isinstance(perms, dict)
    assert perms.get("contents") == "write"


def _assert_sign_on_dispatch_job_guards(jobs: dict[str, Any]) -> None:
    manual = jobs.get("sign-on-dispatch")
    assert isinstance(manual, dict)
    assert manual.get("if") == "github.event_name == 'workflow_dispatch'"
    manual_perms = manual.get("permissions")
    assert isinstance(manual_perms, dict)
    assert manual_perms.get("contents") == "write"


def _assert_approval_trusted_checkout(steps: list[dict[str, Any]]) -> None:
    trusted = _find_step_by_name(steps, "Checkout trusted signing scripts (base branch revision)")
    tw = _step_dict_field(trusted, "with")
    assert "actions/checkout" in str(trusted.get("uses", ""))
    assert "${{ github.event.pull_request.base.sha }}" in str(tw.get("ref", ""))
    assert tw.get("path") == "_trusted_scripts"


def _assert_approval_pr_head_checkout(steps: list[dict[str, Any]]) -> None:
    head = _find_step_by_name(steps, "Checkout PR head (module tree to sign)")
    hw = _step_dict_field(head, "with")
    assert "actions/checkout" in str(head.get("uses", ""))
    assert "${{ github.head_ref }}" in str(hw.get("ref", ""))
    assert hw.get("path") == "_pr_workspace"
    assert hw.get("fetch-depth") == 0


def _assert_approval_sign_step(steps: list[dict[str, Any]]) -> None:
    sign = _find_step_by_name(steps, "Sign changed module manifests")
    run = _step_run_text(sign)
    assert sign.get("working-directory") == "_pr_workspace"
    assert "--changed-only" in run
    assert "--bump-version patch" in run
    assert "--payload-from-filesystem" in run
    assert "BASE_REF" in run
    assert "github.event.pull_request.base.sha" in run
    assert "sign-modules.py" in run
    assert "_trusted_scripts" in run
    env = _step_dict_field(sign, "env")
    assert any("SPECFACT_MODULE_PRIVATE_SIGN_KEY" in str(v) for v in env.values()), (
        "Sign step must wire SPECFACT_MODULE_PRIVATE_SIGN_KEY secret"
    )
    assert any("SPECFACT_MODULE_PRIVATE_SIGN_KEY_PASSPHRASE" in str(v) for v in env.values()), (
        "Sign step must wire passphrase secret"
    )


def _assert_approval_push_step(steps: list[dict[str, Any]]) -> None:
    push = _find_step_by_name(steps, "Commit and push signed manifests")
    prun = _step_run_text(push)
    assert "origin" in prun
    assert "HEAD_REF" in prun
    assert push.get("working-directory") == "_pr_workspace"


def _assert_approval_checkout_and_sign_steps(workflow: dict[str, Any]) -> None:
    steps = _job_steps(workflow, "sign-on-approval")
    _assert_approval_trusted_checkout(steps)
    _assert_approval_pr_head_checkout(steps)
    _assert_approval_sign_step(steps)
    _assert_approval_push_step(steps)


def _assert_dispatch_sign_steps(workflow: dict[str, Any]) -> None:
    steps = _job_steps(workflow, "sign-on-dispatch")
    sign = _find_step_by_name(steps, "Sign changed module manifests")
    srun = _step_run_text(sign)
    assert "git merge-base" in srun
    assert "MERGE_BASE" in srun
    assert '--base-ref "${MERGE_BASE}"' in srun
    assert "sign-modules.py" in srun
    assert "_trusted_scripts" in srun

    push = _find_step_by_name(steps, "Commit and push signed manifests")
    prun = _step_run_text(push)
    assert "chore(modules): manual approval-workflow sign changed modules" in prun
    assert 'git push origin "HEAD:${GITHUB_REF_NAME}"' in prun
    assert "origin" in prun


def test_sign_modules_on_approval_workflow_exists() -> None:
    assert WORKFLOW.is_file(), "sign-modules-on-approval.yml must exist"


def test_sign_modules_on_approval_trigger_and_guards() -> None:
    workflow = _load_yaml(WORKFLOW)
    on_block = _workflow_on_block(workflow)
    _assert_pr_review_and_dispatch_triggers(on_block)
    jobs = workflow.get("jobs")
    assert isinstance(jobs, dict)
    _assert_sign_on_approval_job_guards(jobs)
    _assert_sign_on_dispatch_job_guards(jobs)


def test_sign_modules_on_approval_runs_signer_with_changed_only_mode() -> None:
    workflow = _load_yaml(WORKFLOW)
    _assert_approval_checkout_and_sign_steps(workflow)
    _assert_dispatch_sign_steps(workflow)

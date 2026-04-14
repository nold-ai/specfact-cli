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


def _assert_trusted_dual_checkout_snippets(raw: str) -> None:
    assert "github.event.pull_request.base.sha" in raw
    assert "path: _trusted_scripts" in raw
    assert "path: _pr_workspace" in raw
    assert "working-directory: _pr_workspace" in raw
    assert "${GITHUB_WORKSPACE}/_trusted_scripts/scripts/sign-modules.py" in raw


def _assert_approval_sign_shell_snippets(raw: str) -> None:
    assert "--changed-only" in raw
    assert "--bump-version patch" in raw
    assert "--payload-from-filesystem" in raw
    assert '--base-ref "${BASE_REF}"' in raw
    assert "origin/${{ github.event.pull_request.base.ref }}" in raw
    assert "chore(modules): ci sign changed modules [skip ci]" in raw
    assert 'git push origin "HEAD:${HEAD_REF}"' in raw


def _assert_dispatch_sign_shell_snippets(raw: str) -> None:
    assert "workflow_dispatch:" in raw
    assert "git merge-base" in raw
    assert '--base-ref "${MERGE_BASE}"' in raw
    assert "chore(modules): manual approval-workflow sign changed modules" in raw
    assert 'git push origin "HEAD:${GITHUB_REF_NAME}"' in raw


def _assert_signing_secrets_referenced(raw: str) -> None:
    assert "SPECFACT_MODULE_PRIVATE_SIGN_KEY" in raw
    assert "SPECFACT_MODULE_PRIVATE_SIGN_KEY_PASSPHRASE" in raw


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
    raw = WORKFLOW.read_text(encoding="utf-8")
    _assert_trusted_dual_checkout_snippets(raw)
    _assert_approval_sign_shell_snippets(raw)
    _assert_dispatch_sign_shell_snippets(raw)
    _assert_signing_secrets_referenced(raw)

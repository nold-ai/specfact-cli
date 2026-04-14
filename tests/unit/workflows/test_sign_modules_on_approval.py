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


def test_sign_modules_on_approval_workflow_exists() -> None:
    assert WORKFLOW.is_file(), "sign-modules-on-approval.yml must exist"


def test_sign_modules_on_approval_trigger_and_guards() -> None:
    workflow = _load_yaml(WORKFLOW)
    on_block = _workflow_on_block(workflow)
    review = on_block.get("pull_request_review")
    assert isinstance(review, dict), "Expected pull_request_review trigger mapping"
    assert review.get("types") == ["submitted"]

    jobs = workflow.get("jobs")
    assert isinstance(jobs, dict)
    sign_job = jobs.get("sign")
    assert isinstance(sign_job, dict)
    job_if = sign_job.get("if")
    assert isinstance(job_if, str)
    assert "github.event.review.state == 'approved'" in job_if
    assert "github.event.pull_request.base.ref == 'dev'" in job_if
    assert "github.event.pull_request.base.ref == 'main'" in job_if
    assert "github.event.pull_request.head.repo.full_name == github.repository" in job_if

    perms = sign_job.get("permissions")
    assert isinstance(perms, dict)
    assert perms.get("contents") == "write"


def test_sign_modules_on_approval_runs_signer_with_changed_only_mode() -> None:
    raw = WORKFLOW.read_text(encoding="utf-8")
    assert "scripts/sign-modules.py" in raw
    assert "--changed-only" in raw
    assert "--bump-version patch" in raw
    assert "--payload-from-filesystem" in raw
    assert '--base-ref "${BASE_REF}"' in raw
    assert "origin/${{ github.event.pull_request.base.ref }}" in raw
    assert "SPECFACT_MODULE_PRIVATE_SIGN_KEY" in raw
    assert "SPECFACT_MODULE_PRIVATE_SIGN_KEY_PASSPHRASE" in raw
    assert "chore(modules): ci sign changed modules [skip ci]" in raw
    assert 'git push origin "HEAD:${HEAD_REF}"' in raw

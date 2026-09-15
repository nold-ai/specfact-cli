"""Required checks must be emitted by native events on every supported PR."""

from pathlib import Path
from typing import Any, cast

import pytest
import yaml


WORKFLOW_ROOT = Path(__file__).resolve().parents[3] / ".github" / "workflows"


@pytest.mark.parametrize(
    ("filename", "job_id", "check_name", "push_filter", "required_push_patterns"),
    [
        (
            "docs-review.yml",
            "docs-review",
            "Docs Review",
            "paths",
            {"docs/**", "**/*.md", ".github/workflows/docs-review.yml"},
        ),
        (
            "specfact.yml",
            "specfact-validation",
            "Contract Validation",
            "paths-ignore",
            {"docs/**", "**.md", "**.mdc"},
        ),
    ],
    ids=["docs-review", "contract-validation"],
)
def test_required_workflow_emits_native_pr_check(
    filename: str,
    job_id: str,
    check_name: str,
    push_filter: str,
    required_push_patterns: set[str],
) -> None:
    """Path-filtered workflows cannot satisfy required PR checks on all changes."""
    workflow = cast(dict[str, Any], yaml.safe_load((WORKFLOW_ROOT / filename).read_text(encoding="utf-8")))
    events = cast(dict[str, Any], workflow.get("on", cast(dict[object, Any], workflow).get(True)))
    pull_request = events["pull_request"]
    assert set(pull_request["branches"]) == {"main", "dev"}
    assert "paths" not in pull_request, f"{filename} suppresses required PR checks using paths"
    assert "paths-ignore" not in pull_request, f"{filename} suppresses required PR checks using paths-ignore"
    assert "branches-ignore" not in pull_request
    assert "types" not in pull_request, "Default opened, reopened and synchronize events must remain enabled"

    job = workflow["jobs"][job_id]
    assert job["name"] == check_name
    assert "if" not in job, "Required job must execute after the native PR trigger"

    push = events["push"]
    assert set(push["branches"]) == {"main", "dev"}
    assert required_push_patterns <= set(push[push_filter])
    assert ({"paths", "paths-ignore"} - {push_filter}).isdisjoint(push)

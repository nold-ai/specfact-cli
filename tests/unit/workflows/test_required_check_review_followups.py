"""Supplemental review regressions; the retained Requirements tests stay frozen."""

import json
import subprocess
from pathlib import Path
from typing import Any, cast

import pytest
import yaml
from pydantic import BaseModel, Field


WORKFLOW_ROOT = Path(__file__).resolve().parents[3] / ".github" / "workflows"
# Complete lists captured from dev a4a04786588d61fbc9105137dbaf0236fce009ee.
PUSH_BASELINES = [
    (
        "docs-review.yml",
        "paths",
        [
            "**/*.md",
            "**/*.mdc",
            ".github/**",
            "docs/**",
            "resources/**",
            "src/specfact_cli/resources/**",
            "docs/.doc-frontmatter-enforced",
            "tests/unit/docs/**",
            "tests/unit/workflows/test_docs_module_fixture.py",
            "tests/unit/workflows/test_docs_module_authentication.py",
            "tests/unit/scripts/test_doc_frontmatter/**",
            "tests/integration/scripts/test_doc_frontmatter/**",
            "tests/helpers/doc_frontmatter.py",
            "tests/helpers/doc_frontmatter_fixtures.py",
            "tests/helpers/doc_frontmatter_types.py",
            "scripts/check-docs-commands.py",
            "scripts/check-command-contract.py",
            "scripts/check-documentation-accountability.py",
            "scripts/generate-command-overview.py",
            "scripts/verify_docs_module_source.py",
            "docs/reference/commands.generated.*",
            "llms.txt",
            "scripts/check-cross-site-links.py",
            "scripts/check_doc_frontmatter.py",
            "scripts/validate_agent_rule_applies_when.py",
            "scripts/check_version_sources.py",
            "docs/agent-rules/INDEX.md",
            "pyproject.toml",
            "uv.lock",
            "requirements/ci/locked.txt",
            "ci/docs-module-fixture.lock.json",
            ".github/actions/setup-frozen-python/**",
            ".github/workflows/docs-review.yml",
        ],
    ),
    ("specfact.yml", "paths-ignore", ["docs/**", "**.md", "**.mdc"]),
]


COMMENT_API_HARNESS = r"""
const input = JSON.parse(require('fs').readFileSync(0, 'utf8'));
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
const warnings = [];
const requests = [];
const github = {rest: {issues: {createComment: async (request) => {
  requests.push(request);
  if (input.status !== 201) throw Object.assign(new Error('API rejected'), {status: input.status});
  return {status: 201};
}}}};
const filesystem = {existsSync: () => true, readFileSync: () => 'validation report'};
const context = {issue: {number: 1}, repo: {owner: 'test-owner', repo: 'test-repo'}};
(async () => {
  let error = null;
  try {
    await new AsyncFunction('require', 'github', 'context', 'core', input.script)(
      () => filesystem, github, context, {warning: (message) => warnings.push(message)});
  } catch (failure) { error = failure.status; }
  process.stdout.write(JSON.stringify({warnings, requests, error}));
})();
"""


class CommentRequest(BaseModel):
    """Observed request fields relevant to the comment regression."""

    body: str = Field(description="Validation report submitted as the PR comment body.")


class CommentObservation(BaseModel):
    """Typed output from the native JavaScript comment harness."""

    warnings: list[str] = Field(description="Warnings emitted by the workflow script.")
    requests: list[CommentRequest] = Field(description="Comment API requests attempted by the workflow script.")
    error: int | None = Field(description="Uncaught HTTP status, or null when the workflow script completes.")


def _load_workflow(filename: str) -> dict[str, Any]:
    return cast(dict[str, Any], yaml.safe_load((WORKFLOW_ROOT / filename).read_text(encoding="utf-8")))


@pytest.mark.parametrize(("filename", "filter_name", "expected_patterns"), PUSH_BASELINES)
def test_complete_push_filters_remain_unchanged(filename: str, filter_name: str, expected_patterns: list[str]) -> None:
    """Reject every added or removed push pattern, including nonrepresentative entries."""
    workflow = _load_workflow(filename)
    events = cast(dict[str, Any], workflow.get("on", cast(dict[object, Any], workflow).get(True)))
    push = events["push"]
    assert push[filter_name] == expected_patterns
    assert ({"paths", "paths-ignore"} - {filter_name}).isdisjoint(push)


def test_fork_comment_is_optional_without_skipping_validation() -> None:
    """A read-only fork token must not turn optional comments into validation failures."""
    workflow = _load_workflow("specfact.yml")
    job = workflow["jobs"]["specfact-validation"]
    steps = {step["name"]: step for step in job["steps"] if "name" in step}
    comment = steps["Post PR comment"]
    assert "github.event.pull_request.head.repo.full_name == github.repository" in comment["if"]
    assert "github.event_name == 'pull_request'" in comment["if"]
    assert "steps.pr-comment.outputs.comment_path != ''" in comment["if"]
    assert "if" not in job
    assert steps["Upload validation report"]["if"] == "always()"
    failure = steps["Fail workflow if validation failed"]
    assert failure["if"] == "steps.repro.outputs.exit_code != '0' && steps.validation.outputs.mode == 'block'"
    assert "exit 1" in failure["run"]


@pytest.mark.parametrize("api_status", [201, 403, 500])
def test_optional_comment_tolerates_only_permission_denial(api_status: int) -> None:
    """Execute the workflow script so read-only tokens cannot fail optional publication."""
    workflow = _load_workflow("specfact.yml")
    steps = workflow["jobs"]["specfact-validation"]["steps"]
    script = next(step["with"]["script"] for step in steps if step.get("name") == "Post PR comment")

    result = subprocess.run(
        ["node", "--unhandled-rejections=strict", "-e", COMMENT_API_HARNESS],
        input=json.dumps({"script": script, "status": api_status}),
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr
    observed = CommentObservation.model_validate_json(result.stdout, strict=True)
    assert len(observed.requests) == 1
    assert observed.requests[0].body == "validation report"
    assert observed.error == (500 if api_status == 500 else None)
    assert len(observed.warnings) == (1 if api_status == 403 else 0)

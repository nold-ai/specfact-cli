"""Supplemental review regressions; the retained Requirements tests stay frozen."""

from pathlib import Path
from typing import Any, cast

import pytest
import yaml


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

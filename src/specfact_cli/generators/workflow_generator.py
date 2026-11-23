"""Workflow generator for GitHub Actions."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require
from jinja2 import Environment, FileSystemLoader

from specfact_cli.utils.icontract_helpers import (
    ensure_github_workflow_output_suffix,
    require_output_path_exists,
    require_python_version_is_3_x,
)


class WorkflowGenerator:
    """
    Generator for GitHub Actions workflows.

    Uses Jinja2 templates to render workflows.
    """

    @beartype
    def __init__(self, templates_dir: Path | None = None) -> None:
        """
        Initialize workflow generator.

        Args:
            templates_dir: Directory containing Jinja2 templates (default: resources/templates)
        """
        if templates_dir is None:
            package_root = Path(__file__).resolve().parents[1]
            bundled = package_root / "resources" / "templates"
            templates_dir = bundled if bundled.is_dir() else package_root.parents[1] / "resources" / "templates"

        self.templates_dir = Path(templates_dir)
        self.env = Environment(  # nosec B701 - generates trusted text/YAML workflow templates, not HTML.
            loader=FileSystemLoader(self.templates_dir),
            # Must be False: trim_blocks removes the newline after {% endraw %}, merging `if:` with `run:`.
            trim_blocks=False,
            # Must be False: lstrip_blocks strips newlines after {% endraw %} in some cases.
            lstrip_blocks=False,
        )

    @beartype
    @require(lambda output_path: output_path is not None, "Output path must not be None")
    @require(lambda budget: budget > 0, "Budget must be positive")
    @require(require_python_version_is_3_x, "Python version must be 3.x")
    @ensure(require_output_path_exists, "Output file must exist after generation")
    @ensure(ensure_github_workflow_output_suffix, "Output must be YAML file")
    def generate_github_action(
        self,
        output_path: Path,
        repo_name: str | None = None,
        budget: int = 90,
        python_version: str = "3.12",
        bundle_name: str = "main",
    ) -> None:
        """
        Generate GitHub Action workflow for SpecFact validation.

        Args:
            output_path: Path to write the workflow file (e.g., .github/workflows/specfact-gate.yml)
            repo_name: Repository name for context
            budget: Time budget in seconds for validation (must be > 0)
            python_version: Python version for workflow (must be 3.x)
            bundle_name: Default project bundle name for optional `project version check` in CI

        Raises:
            FileNotFoundError: If template file doesn't exist
            IOError: If unable to write output file
        """
        # Prepare context
        context: dict[str, Any] = {
            "repo_name": repo_name or "specfact-project",
            "budget": budget,
            "python_version": python_version,
            "bundle_name": bundle_name,
        }

        # Render template
        template = self.env.get_template("github-action.yml.j2")
        rendered = template.render(**context)

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write workflow file
        output_path.write_text(rendered, encoding="utf-8")

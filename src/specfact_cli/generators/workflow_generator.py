"""Workflow generator for GitHub Actions and Semgrep rules."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require
from jinja2 import Environment, FileSystemLoader


class WorkflowGenerator:
    """
    Generator for GitHub Actions workflows and Semgrep rules.

    Uses Jinja2 templates to render workflows and copies Semgrep rules.
    """

    @beartype
    def __init__(self, templates_dir: Path | None = None) -> None:
        """
        Initialize workflow generator.

        Args:
            templates_dir: Directory containing Jinja2 templates (default: resources/templates)
        """
        if templates_dir is None:
            # Default to resources/templates relative to project root
            templates_dir = Path(__file__).parent.parent.parent.parent / "resources" / "templates"

        self.templates_dir = Path(templates_dir)
        self.env = Environment(
            loader=FileSystemLoader(self.templates_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    @beartype
    @require(lambda output_path: output_path is not None, "Output path must not be None")
    @require(lambda budget: budget > 0, "Budget must be positive")
    @require(lambda python_version: python_version.startswith("3."), "Python version must be 3.x")
    @ensure(lambda output_path: output_path.exists(), "Output file must exist after generation")
    @ensure(lambda output_path: output_path.suffix == ".yml", "Output must be YAML file")
    def generate_github_action(
        self,
        output_path: Path,
        repo_name: str | None = None,
        budget: int = 90,
        python_version: str = "3.12",
    ) -> None:
        """
        Generate GitHub Action workflow for SpecFact validation.

        Args:
            output_path: Path to write the workflow file (e.g., .github/workflows/specfact-gate.yml)
            repo_name: Repository name for context
            budget: Time budget in seconds for validation (must be > 0)
            python_version: Python version for workflow (must be 3.x)

        Raises:
            FileNotFoundError: If template file doesn't exist
            IOError: If unable to write output file
        """
        # Prepare context
        context: dict[str, Any] = {
            "repo_name": repo_name or "specfact-project",
            "budget": budget,
            "python_version": python_version,
        }

        # Render template
        template = self.env.get_template("github-action.yml.j2")
        rendered = template.render(**context)

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write workflow file
        output_path.write_text(rendered, encoding="utf-8")

    @beartype
    @require(lambda output_path: output_path is not None, "Output path must not be None")
    @ensure(lambda output_path: output_path.exists(), "Output file must exist after generation")
    @ensure(lambda output_path: output_path.suffix in (".yml", ".yaml"), "Output must be YAML file")
    def generate_semgrep_rules(self, output_path: Path, source_rules: Path | None = None) -> None:
        """
        Generate Semgrep async rules for the repository.

        Args:
            output_path: Path to write Semgrep rules (e.g., .semgrep/async-anti-patterns.yml)
            source_rules: Path to source Semgrep rules (default: tools/semgrep/async.yml)

        Raises:
            FileNotFoundError: If source rules file doesn't exist
            IOError: If unable to write output file
        """
        if source_rules is None:
            # Try package resource first (for installed packages)
            package_resource = Path(__file__).parent.parent / "resources" / "semgrep" / "async.yml"
            # Fall back to tools/semgrep/async.yml for development
            dev_resource = Path(__file__).parent.parent.parent.parent / "tools" / "semgrep" / "async.yml"

            if package_resource.exists():
                source_rules = package_resource
            elif dev_resource.exists():
                source_rules = dev_resource
            else:
                raise FileNotFoundError(f"Source Semgrep rules not found. Checked: {package_resource}, {dev_resource}")
        else:
            source_rules = Path(source_rules)
            if not source_rules.exists():
                raise FileNotFoundError(f"Source Semgrep rules not found: {source_rules}")

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Copy source rules to output path
        shutil.copy2(source_rules, output_path)

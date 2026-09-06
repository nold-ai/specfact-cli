"""Regression tests for main-relative Requirements promotion inputs."""

from pathlib import Path
from typing import Any, cast

import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "requirements-evidence.yml"


def _step_command(name: str) -> str:
    parsed = yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    jobs = cast(dict[str, Any], parsed["jobs"])
    for job in jobs.values():
        for step in job.get("steps", []):
            if step.get("name") == name:
                return cast(str, step["run"])
    raise AssertionError(f"Missing workflow step: {name}")


def test_promotion_trusted_core_archives_only_required_review_lock() -> None:
    """Main-relative consumers must not request an unused dev-only source file."""
    for name in ("Materialize trusted Requirements core", "Materialize trusted final Requirements core"):
        command = _step_command(name)
        assert "requirements/code-review/locked.txt" in command
        assert "requirements/code-review/requirements.in" not in command

"""Check independently blocking scanner steps in the core PR workflow."""

from collections.abc import Mapping
from pathlib import Path

import pytest
import yaml


WORKFLOW = Path(__file__).resolve().parents[3] / ".github/workflows/pr-orchestrator.yml"


def _bandit_step() -> dict[str, object]:
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["independent-static-analysis"]["steps"]
    return next(step for step in steps if step.get("name") == "Run independent Bandit gate")


def _require_blocking_bandit(step: Mapping[str, object]) -> None:
    assert step.get("continue-on-error", False) is False


def test_bandit_runs_after_successful_setup_even_when_sast_fails() -> None:
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["independent-static-analysis"]["steps"]
    setup = next(step for step in steps if step.get("name") == "Set up frozen static-analysis dependencies")
    assert setup["if"] == "!cancelled() && steps.analysis-python.outcome == 'success'"
    bandit = _bandit_step()
    assert bandit["if"] == "!cancelled() && steps.bandit-setup.outcome == 'success'"
    _require_blocking_bandit(bandit)


def test_bandit_cannot_suppress_step_failure() -> None:
    bandit = _bandit_step()
    _require_blocking_bandit(bandit)
    with pytest.raises(AssertionError):
        _require_blocking_bandit({**bandit, "continue-on-error": True})

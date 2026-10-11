"""Proof consumers have only the read capabilities needed to authenticate root checks."""

from pathlib import Path

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize(
    "job_name",
    ("requirements-evidence-producer", "requirements-evidence", "requirements-evidence-final"),
)
def test_each_proof_consumer_has_explicit_read_only_checks_permission(job_name: str) -> None:
    """Authenticated check-run reads require permission without check-writing authority."""
    workflow = yaml.safe_load((REPO_ROOT / ".github/workflows/requirements-evidence.yml").read_text())
    permissions = workflow["jobs"][job_name]["permissions"]
    assert permissions == {"actions": "read", "contents": "read", "issues": "read", "checks": "read"}

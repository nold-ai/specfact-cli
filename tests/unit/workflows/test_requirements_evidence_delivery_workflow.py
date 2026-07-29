"""Contract coverage for the core Requirements-evidence pull-request gate."""

from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def _assert_fixture_contract(raw: str) -> None:
    assert "ci/module-fixture.lock.json" in raw
    assert "nold-ai/specfact-cli-modules" in raw
    assert "Verify immutable module fixture" in raw
    assert "SPECFACT_MODULES_REPO=${GITHUB_WORKSPACE}/specfact-cli-modules" in raw
    assert "SPECFACT_MODULES_ROOTS=${GITHUB_WORKSPACE}/specfact-cli-modules/packages" in raw


def _assert_command_contract(raw: str) -> None:
    assert "uv run --locked --no-sync specfact requirements evidence" in raw
    assert "hatch run specfact requirements evidence" not in raw
    assert "--base-ref" in raw
    assert "artifacts/requirements-evidence/requirements-evidence.json" in raw
    assert "artifacts/requirements-evidence/requirements-evidence.md" in raw


def _assert_retention_contract(raw: str) -> None:
    assert "GITHUB_STEP_SUMMARY" in raw
    assert raw.count("if: always()") >= 2
    assert raw.index("Upload requirements evidence artifact") < raw.index("Enforce requirements evidence verdict")


def test_requirements_evidence_workflow_uses_the_released_fixture_and_retains_reports() -> None:
    """PR enforcement must verify the fixture and publish output before failing red verdicts."""
    workflow = REPO_ROOT / ".github" / "workflows" / "requirements-evidence.yml"
    raw = workflow.read_text(encoding="utf-8")

    assert "pull_request:" in raw
    _assert_fixture_contract(raw)
    _assert_command_contract(raw)
    _assert_retention_contract(raw)

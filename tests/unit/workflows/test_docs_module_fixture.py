"""Documentation adoption must not replace the approved Requirements fixture."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize(
    ("filename", "job"), [("docs-review.yml", "docs-review"), ("pr-orchestrator.yml", "cli-validation")]
)
def test_docs_review_uses_independent_verified_module_fixture(filename: str, job: str) -> None:
    workflow = yaml.safe_load((REPO_ROOT / ".github/workflows" / filename).read_text(encoding="utf-8"))
    steps = workflow["jobs"][job]["steps"]
    scripts = "\n".join(step.get("run", "") for step in steps)
    assert "ci/docs-module-fixture.lock.json" in scripts
    assert "ci/module-fixture.lock.json" not in scripts
    assert "HEAD^{tree}" in scripts
    assert "test_code_review_command_parity.py" in scripts
    assert "test_docs_module_fixture.py" in scripts
    assert "test_llms_overview_freshness.py" in scripts
    assert "${SPECFACT_DOCS_MODULES_REPO:?" in scripts
    checkout = next(step for step in steps if step.get("name") == "Checkout module command sources")
    assert checkout["with"]["ref"] in (
        "${{ steps.modules-fixture.outputs.commit }}",
        "${{ steps.modules-fixture.outputs.ref }}",
    )


def test_requirements_fixture_authority_stays_at_approved_release() -> None:
    fixture = json.loads((REPO_ROOT / "ci/module-fixture.lock.json").read_text(encoding="utf-8"))
    assert fixture == {
        "repository": "nold-ai/specfact-cli-modules",
        "commit": "69f075819be5e1ceca1446b026b0417f19e584ca",
        "tree": "5d0b8e66c6cd467e6b1ad9d582e24c66b907e205",
    }


def _fixture_repository(root: Path) -> dict[str, str]:
    checkout = root / "specfact-cli-modules"
    checkout.mkdir()
    subprocess.run(["git", "init", "-q", str(checkout)], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(checkout),
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.test",
            "commit",
            "-q",
            "--allow-empty",
            "-m",
            "fixture",
        ],
        check=True,
    )
    identity = {"repository": "nold-ai/specfact-cli-modules"}
    for key, revision in (("commit", "HEAD"), ("tree", "HEAD^{tree}")):
        identity[key] = subprocess.check_output(["git", "-C", str(checkout), "rev-parse", revision], text=True).strip()
    return identity


@pytest.mark.parametrize(
    ("filename", "job"), [("docs-review.yml", "docs-review"), ("pr-orchestrator.yml", "cli-validation")]
)
@pytest.mark.parametrize("mismatch", [None, "repository", "commit", "tree", "mutable-commit", "dirty"])
def test_docs_fixture_checks_reject_actual_identity_mismatches(
    tmp_path: Path, mismatch: str | None, filename: str, job: str
) -> None:
    identity = _fixture_repository(tmp_path)
    if mismatch in ("commit", "tree"):
        identity[mismatch] = "a" * 40
    if mismatch == "repository":
        identity["repository"] = "example/unreviewed"
    if mismatch == "mutable-commit":
        identity["commit"] = "dev"
    if mismatch == "dirty":
        (tmp_path / "specfact-cli-modules/unreviewed.py").write_text("raise RuntimeError('unreviewed')\n")
    (tmp_path / "ci").mkdir()
    for name in ("module-fixture.lock.json", "docs-module-fixture.lock.json"):
        (tmp_path / "ci" / name).write_text(json.dumps(identity))
    workflow = yaml.safe_load((REPO_ROOT / ".github/workflows" / filename).read_text())
    steps = {step.get("name"): step for step in workflow["jobs"][job]["steps"]}
    script = steps["Read immutable module fixture"]["run"] + steps["Verify immutable module fixture"]["run"]
    script = script.replace("${{ steps.modules-fixture.outputs.repository }}", "nold-ai/specfact-cli-modules")
    environment = {
        **os.environ,
        "PATH": str(Path(sys.executable).parent) + os.pathsep + os.environ["PATH"],
        "GITHUB_OUTPUT": str(tmp_path / "outputs"),
    }
    result = subprocess.run(["bash", "-c", script], cwd=tmp_path, env=environment, capture_output=True, text=True)
    assert (result.returncode == 0) is (mismatch is None), result.stderr


@pytest.mark.parametrize(
    ("filename", "job", "step_name"),
    [
        ("docs-review.yml", "docs-review", "Validate documentation fixture and Code Review command parity"),
        ("pr-orchestrator.yml", "cli-validation", "Validate CLI commands"),
    ],
    ids=["docs-review", "cli-validation"],
)
def test_docs_gate_fails_before_pytest_without_explicit_context(
    tmp_path: Path, filename: str, job: str, step_name: str
) -> None:
    workflow = yaml.safe_load((REPO_ROOT / ".github/workflows" / filename).read_text())
    step = next(step for step in workflow["jobs"][job]["steps"] if step.get("name") == step_name)
    environment = {key: value for key, value in os.environ.items() if key != "SPECFACT_DOCS_MODULES_REPO"}
    result = subprocess.run(["bash", "-c", step["run"]], cwd=tmp_path, env=environment, capture_output=True, text=True)
    assert result.returncode != 0
    assert "Documentation fixture is required" in result.stderr


def test_other_orchestrator_jobs_keep_execution_fixture_authority() -> None:
    workflow = yaml.safe_load((REPO_ROOT / ".github/workflows/pr-orchestrator.yml").read_text())
    for name, job in workflow["jobs"].items():
        if name != "cli-validation":
            assert "ci/docs-module-fixture.lock.json" not in json.dumps(job)

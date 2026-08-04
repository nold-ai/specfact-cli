"""Contract coverage for staged Requirements maturity selection."""

from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_pre_commit_derives_and_forwards_staged_required_maturity() -> None:
    """Local source changes must receive the same maturity policy as CI diffs."""
    pre_commit = (REPO_ROOT / "scripts" / "pre-commit-quality-checks.sh").read_text(encoding="utf-8")

    assert "staged_required_maturity()" in pre_commit
    assert 'required_maturity="$(staged_planning_maturity)"' in pre_commit
    assert '--required-maturity "${required_maturity}"' in pre_commit


def test_pre_commit_runs_planning_evidence_for_governed_product_only_changes() -> None:
    """A committed mapping must still govern later staged delivery changes."""
    pre_commit = (REPO_ROOT / "scripts" / "pre-commit-quality-checks.sh").read_text(encoding="utf-8")

    assert "has_staged_requirements_evidence_scope()" in pre_commit
    assert ".github/*|ci/*|scripts/*|src/*|tests/*)" in pre_commit
    assert "if ! has_staged_requirements_evidence_scope; then" in pre_commit


def test_pre_commit_normalizes_verified_changes_to_test_authored_planning() -> None:
    """Local pre-commit validates a plan and never claims final execution proof."""
    pre_commit = (REPO_ROOT / "scripts" / "pre-commit-quality-checks.sh").read_text(encoding="utf-8")

    assert "staged_planning_maturity()" in pre_commit
    assert 'verified) printf "test-authored\\n"' in pre_commit
    assert 'required_maturity="$(staged_planning_maturity)"' in pre_commit
    assert "requirements-evidence-plan.json" in pre_commit
    assert "requirements-proof/review-evidence.json" in pre_commit


def test_runtime_proof_mapping_uses_unique_exact_pytest_selectors() -> None:
    """Every executable proof case must be independently runnable from the released plan."""
    sidecar = REPO_ROOT / "openspec/changes/requirements-07-runtime-proof-delivery/requirements-evidence.yaml"
    mapping = yaml.safe_load(sidecar.read_text(encoding="utf-8"))
    cases = [
        case
        for requirement in mapping["requirements"].values()
        for case in requirement["verification_cases"]
        if case["method"] == "test"
    ]
    selectors = [case.get("selector") for case in cases]

    assert all(
        isinstance(selector, dict)
        and selector.get("runner") == "pytest"
        and isinstance(selector.get("node_id"), str)
        and selector["node_id"].startswith("tests/")
        for selector in selectors
    )
    assert len({selector["node_id"] for selector in selectors}) == len(selectors)

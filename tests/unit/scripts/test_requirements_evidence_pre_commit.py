"""Contract coverage for staged Requirements maturity selection."""

import subprocess
import sys
from pathlib import Path
from typing import Any, cast

import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]


def _pre_commit_text() -> str:
    return (REPO_ROOT / "scripts" / "pre-commit-quality-checks.sh").read_text(encoding="utf-8")


def _assert_contains_pre_commit_contract(*fragments: str) -> None:
    pre_commit = _pre_commit_text()
    for fragment in fragments:
        assert fragment in pre_commit


def test_pre_commit_derives_maturity_and_governs_product_only_changes() -> None:
    """Local source changes must use CI maturity and the active Requirements mapping."""
    _assert_contains_pre_commit_contract(
        "staged_required_maturity()",
        'required_maturity="$(staged_planning_maturity)"',
        '--required-maturity "${required_maturity}"',
        "has_staged_requirements_evidence_scope()",
        ".github/*|ci/*|scripts/*|src/*|tests/*|openspec/specs/*)",
        "if ! has_staged_requirements_evidence_scope; then",
    )


def test_pre_commit_normalizes_verified_changes_to_test_authored_planning() -> None:
    """Local pre-commit validates a plan and never claims final execution proof."""
    required_fragments = {
        "staged_planning_maturity()",
        'verified) printf "test-authored\\n"',
        'required_maturity="$(staged_planning_maturity)"',
        "requirements-evidence-plan.json",
        "requirements-proof/review-evidence.json",
        "find openspec/changes -path 'openspec/changes/archive' -prune -o -path '*/requirements-proof/review-evidence.json' -type f -print",
    }
    pre_commit = _pre_commit_text()
    assert all(fragment in pre_commit for fragment in required_fragments)


def test_pre_commit_treats_canonical_specs_as_governed_requirement_sources() -> None:
    """Archived OpenSpec specifications must receive a local evidence decision."""
    _assert_contains_pre_commit_contract("openspec/specs/*")


def test_pre_commit_clears_each_owned_report_before_evidence_invocation() -> None:
    """A successful call cannot satisfy its report checks with a prior run's plan."""
    _assert_contains_pre_commit_contract(
        'rm -f "${json_report}" "${markdown_report}" "${plan_report}"',
        "if hatch run python scripts/requirements_evidence_delivery_gate.py",
    )


def test_pre_commit_uses_both_rename_paths_for_requirements_scope_and_maturity() -> None:
    """Renaming governed code away must still trigger the correct evidence decision."""
    pre_commit = _pre_commit_text()
    _assert_contains_pre_commit_contract(
        "staged_evidence_paths()",
        "git diff --cached --name-status --find-renames --diff-filter=ACMRD",
        "R*|C*)",
    )
    assert pre_commit.count("done < <(staged_evidence_paths)") == 2
    assert 'changed_paths="$(staged_evidence_paths)"' in pre_commit


def test_pre_commit_runs_planning_evidence_for_governed_product_only_changes() -> None:
    """Requirements evidence runs before later gates for a governed staged product change."""
    pre_commit = _pre_commit_text()
    block2 = pre_commit[pre_commit.index("run_block2() {") : pre_commit.index("run_all() {")]
    assert "has_staged_requirements_evidence_scope()" in pre_commit
    assert block2.index("run_requirements_evidence_gate") < block2.index("run_code_review_gate")
    assert block2.index("run_requirements_evidence_gate") < block2.index("run_contract_tests_visible")


def test_runtime_proof_mapping_uses_unique_exact_pytest_selectors() -> None:
    """Every executable proof case must be independently runnable from the released plan."""
    sidecar = REPO_ROOT / "openspec/changes/requirements-07-runtime-proof-delivery/requirements-evidence.yaml"
    mapping = cast(dict[str, Any], yaml.safe_load(sidecar.read_text(encoding="utf-8")))
    requirements = cast(dict[str, dict[str, list[dict[str, Any]]]], mapping["requirements"])
    cases = [
        case
        for requirement in requirements.values()
        for case in requirement["verification_cases"]
        if case["method"] == "test"
    ]
    node_ids: list[str] = []
    for case in cases:
        selector = cast(dict[str, Any], case.get("selector"))
        assert selector.get("runner") == "pytest"
        node_id = selector.get("node_id")
        assert isinstance(node_id, str)
        assert node_id.startswith("tests/")
        node_ids.append(node_id)
    assert len(set(node_ids)) == len(node_ids)


def test_runtime_proof_mapping_selectors_are_collectible() -> None:
    """Every mapped selector must resolve in the current repository test collection."""
    sidecar = REPO_ROOT / "openspec/changes/requirements-07-runtime-proof-delivery/requirements-evidence.yaml"
    mapping = cast(dict[str, Any], yaml.safe_load(sidecar.read_text(encoding="utf-8")))
    requirements = cast(dict[str, dict[str, list[dict[str, Any]]]], mapping["requirements"])
    node_ids = [
        cast(str, cast(dict[str, Any], case["selector"])["node_id"])
        for requirement in requirements.values()
        for case in requirement["verification_cases"]
        if case["method"] == "test"
    ]
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", *node_ids],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr

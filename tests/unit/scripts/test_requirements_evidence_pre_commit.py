"""Contract coverage for staged Requirements maturity selection."""

import subprocess
import sys
from pathlib import Path
from typing import Any, cast

import yaml

from tests.unit.scripts.requirements_change_support import runtime_proof_change_root


REPO_ROOT = Path(__file__).resolve().parents[3]


def _pre_commit_text() -> str:
    return (REPO_ROOT / "scripts" / "pre-commit-quality-checks.sh").read_text(encoding="utf-8")


def _assert_contains_pre_commit_contract(*fragments: str) -> None:
    pre_commit = _pre_commit_text()
    for fragment in fragments:
        assert fragment in pre_commit


def _runtime_proof_requirements() -> dict[str, dict[str, list[dict[str, Any]]]]:
    sidecar = runtime_proof_change_root(REPO_ROOT) / "requirements-evidence.yaml"
    assert sidecar.is_file(), f"Required R07 mapping fixture is missing: {sidecar}"
    mapping = cast(dict[str, Any], yaml.safe_load(sidecar.read_text(encoding="utf-8")))
    return cast(dict[str, dict[str, list[dict[str, Any]]]], mapping["requirements"])


def test_pre_commit_derives_maturity_and_governs_product_only_changes() -> None:
    """Local source changes must use CI maturity and the active Requirements mapping."""
    _assert_contains_pre_commit_contract(
        "staged_required_maturity()",
        'required_maturity="$(staged_planning_maturity)"',
        '--required-maturity "${required_maturity}"',
        "has_staged_requirements_evidence_scope()",
        "has_staged_requirements_evidence_scope || scope_status=$?",
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


def test_pre_commit_selects_review_evidence_from_the_staged_change() -> None:
    """Parallel active changes must not make a uniquely staged change ambiguous."""
    _assert_contains_pre_commit_contract(
        "staged_active_change_ids()",
        'selected_change="${staged_change_ids[0]}"',
        'review_evidence="openspec/changes/${selected_change}/requirements-proof/review-evidence.json"',
        "Staged Requirements evidence spans multiple active changes",
        'if ! printf \'%s\\n\' "${relative_path%%/*}" >>"${change_ids_file}"; then',
        'if ! sort -u "${change_ids_file}"; then',
        "require_index_bound_review_evidence()",
        'git cat-file -e ":${review_evidence}"',
        'git diff --quiet -- "${review_evidence}"',
        "must match the staged Git index",
        'index_mode="$(git ls-files --stage -- "${review_evidence}"',
        '[[ "${index_mode}" != "100644" ]]',
        "resolve().relative_to",
    )
    assert "local -A" not in _pre_commit_text()


def test_pre_commit_rejects_symlinked_review_evidence() -> None:
    _assert_contains_pre_commit_contract(
        '[[ -L "${review_evidence}" ]]',
        "Review evidence must be a regular staged repository file",
    )


def test_pre_commit_treats_canonical_specs_as_governed_requirement_sources() -> None:
    """Archived OpenSpec specifications must receive a local evidence decision."""
    pre_commit = _pre_commit_text()
    scope = pre_commit[
        pre_commit.index("has_staged_requirements_evidence_scope() {") : pre_commit.index(
            "staged_active_change_ids() {"
        )
    ]
    assert "return 0" in scope
    assert "case" not in scope


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
        "git diff --cached --name-status -z --find-renames --diff-filter=ACMRD",
        "while IFS= read -r -d '' status; do",
        "printf '%s\\0' \"${source_path}\"",
        "R*|C*)",
    )
    assert pre_commit.count("done < <(staged_evidence_paths)") == 3
    assert 'changed_paths="$(staged_evidence_paths)"' not in pre_commit


def test_pre_commit_rejects_staged_path_enumeration_failures() -> None:
    _assert_contains_pre_commit_contract(
        "STAGED_PATH_ERROR",
        "printf '%s\\0' \"${STAGED_PATH_ERROR}\"",
        'if [[ "${file}" == "${STAGED_PATH_ERROR}" ]]',
        "Unable to enumerate staged paths",
    )

    pre_commit_library = _pre_commit_text().removesuffix('\nmain "$@"\n')
    result = subprocess.run(
        ["bash", "-c", f"{pre_commit_library}\ngit() {{ return 42; }}\nhas_staged_requirements_evidence_scope"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert "Unable to enumerate staged paths" in result.stderr


def test_pre_commit_preserves_tabbed_staged_evidence_paths(tmp_path: Path) -> None:
    """NUL-delimited Git records preserve paths that cannot be parsed line by line."""
    subprocess.run(["git", "init", "--quiet"], cwd=tmp_path, check=True)
    staged_path = tmp_path / "src" / "tab\tpath.py"
    staged_path.parent.mkdir()
    staged_path.write_text("print('proof')\n", encoding="utf-8")
    subprocess.run(["git", "add", "--", staged_path.relative_to(tmp_path)], cwd=tmp_path, check=True)

    pre_commit_library = _pre_commit_text().removesuffix('\nmain "$@"\n')
    result = subprocess.run(
        ["bash", "-c", f"{pre_commit_library}\nstaged_evidence_paths"],
        cwd=tmp_path,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr.decode()
    assert result.stdout.split(b"\0") == [b"src/tab\tpath.py", b""]


def test_pre_commit_routes_docs_only_staging_to_the_evidence_gate(tmp_path: Path) -> None:
    """A staged no-impact diff must invoke the adapter instead of silently skipping it."""
    subprocess.run(["git", "init", "--quiet"], cwd=tmp_path, check=True)
    docs_path = tmp_path / "docs" / "guide.md"
    docs_path.parent.mkdir()
    docs_path.write_text("# guide\n", encoding="utf-8")
    subprocess.run(["git", "add", "--", docs_path.relative_to(tmp_path)], cwd=tmp_path, check=True)

    pre_commit_library = _pre_commit_text().removesuffix('\nmain "$@"\n')
    result = subprocess.run(
        ["bash", "-c", f"{pre_commit_library}\nhas_staged_requirements_evidence_scope"],
        cwd=tmp_path,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr.decode()


def test_pre_commit_runs_planning_evidence_for_governed_product_only_changes() -> None:
    """Requirements evidence runs before later gates for a governed staged product change."""
    pre_commit = _pre_commit_text()
    block2 = pre_commit[pre_commit.index("run_block2() {") : pre_commit.index("run_all() {")]
    assert "has_staged_requirements_evidence_scope()" in pre_commit
    assert block2.index("run_requirements_evidence_gate") < block2.index("run_code_review_gate")
    assert block2.index("run_requirements_evidence_gate") < block2.index("run_contract_tests_visible")


def test_runtime_proof_mapping_uses_unique_exact_pytest_selectors() -> None:
    """Every executable proof case must be independently runnable from the released plan."""
    requirements = _runtime_proof_requirements()
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
    requirements = _runtime_proof_requirements()
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


def test_governed_trigger_scenario_uses_the_workflow_trigger_contract() -> None:
    """The governed-trigger proof must exercise scheduling and terminal enforcement."""
    requirements = _runtime_proof_requirements()
    case = next(
        case
        for requirement in requirements.values()
        for case in requirement["verification_cases"]
        if case["case_id"] == "R07-CORE-007-S01"
    )

    selector = cast(dict[str, str], case["selector"])
    assert selector["node_id"] == (
        "tests/unit/workflows/test_requirements_evidence_delivery_workflow.py::"
        "test_requirements_evidence_workflow_uses_the_released_fixture_and_retains_reports"
    )


def test_review_handoff_scenarios_use_competing_verdict_enforcement_proofs() -> None:
    """R07 must prove each independently blocking final verdict at the workflow boundary."""
    requirements = _runtime_proof_requirements()
    selectors = {
        case["case_id"]: cast(dict[str, str], case["selector"])["node_id"]
        for requirement in requirements.values()
        for case in requirement["verification_cases"]
        if case["case_id"] in {"R07-CORE-006-S02", "R07-CORE-006-S03"}
    }

    assert selectors == {
        "R07-CORE-006-S02": (
            "tests/unit/workflows/test_requirements_evidence_delivery_workflow.py::"
            "test_requirements_evidence_workflow_blocks_each_final_verdict[requirements-failure]"
        ),
        "R07-CORE-006-S03": (
            "tests/unit/workflows/test_requirements_evidence_delivery_workflow.py::"
            "test_requirements_evidence_workflow_blocks_each_final_verdict[code-review-failure]"
        ),
    }


def test_runtime_proof_mapping_uses_released_acceptance_skip_and_reconciliation_proofs() -> None:
    """R07 scenarios must execute the module behavior claimed by their observable."""
    requirements = _runtime_proof_requirements()
    selectors = {
        case["case_id"]: cast(dict[str, str], case["selector"])["node_id"]
        for requirement in requirements.values()
        for case in requirement["verification_cases"]
        if case["case_id"] in {"R07-CORE-002-S01", "R07-CORE-004-S03", "R07-CORE-005-S03"}
    }

    assert selectors == {
        "R07-CORE-002-S01": (
            "tests/unit/scripts/test_requirements_evidence_delivery_gate.py::"
            "test_released_evidence_rejects_stale_acceptance"
        ),
        "R07-CORE-004-S03": (
            "tests/unit/scripts/test_requirements_evidence_delivery_gate.py::"
            "test_released_evidence_publishes_a_bounded_staged_no_impact_decision"
        ),
        "R07-CORE-005-S03": (
            "tests/unit/scripts/test_requirements_evidence_delivery_gate.py::"
            "test_released_reconciliation_marks_incomplete_junit_unverified"
        ),
    }

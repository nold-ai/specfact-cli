from __future__ import annotations

from pathlib import Path


def _quality_script_text() -> str:
    return (Path(__file__).resolve().parents[3] / "scripts" / "pre-commit-quality-checks.sh").read_text(
        encoding="utf-8"
    )


def _smart_shim_text() -> str:
    return (Path(__file__).resolve().parents[3] / "scripts" / "pre-commit-smart-checks.sh").read_text(encoding="utf-8")


def test_pre_commit_markdown_checks_run_autofix_before_lint() -> None:
    script = _quality_script_text()
    assert "run_markdown_autofix_if_needed" in script
    assert "markdownlint --fix --config .markdownlint.json" in script
    idx_fix = script.find("run_markdown_autofix_if_needed")
    idx_lint = script.find("run_markdown_lint_if_needed")
    assert 0 <= idx_fix < idx_lint, "auto-fix must be defined before lint in the script"


def test_pre_commit_markdown_autofix_restages_files() -> None:
    script = _quality_script_text()
    assert 'git add -- "${md_files[@]}"' in script


def test_pre_commit_markdown_autofix_rejects_partial_staging() -> None:
    script = _quality_script_text()
    assert 'git diff --quiet -- "${file}"' in script
    assert "Cannot auto-fix Markdown with unstaged hunks" in script


def test_pre_commit_runs_code_review_gate_before_contract_tests() -> None:
    script = _quality_script_text()
    assert "run_code_review_gate" in script
    assert "hatch run python scripts/pre_commit_code_review.py" in script
    block2 = script.find("run_block2()")
    assert block2 != -1
    tail = script[block2:]
    idx_gate = tail.find("run_code_review_gate")
    idx_contract = tail.find("run_contract_tests_visible")
    assert 0 <= idx_gate < idx_contract
    assert '"${review_array[@]}"' in script


def test_pre_commit_smart_checks_shim_delegates_to_quality_all() -> None:
    shim = _smart_shim_text()
    assert "pre-commit-quality-checks.sh" in shim
    assert 'all "$@"' in shim
    assert "rev-parse --show-toplevel" in shim
    assert 'exec bash "${_repo_root}/scripts/pre-commit-quality-checks.sh"' in shim

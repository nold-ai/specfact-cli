from __future__ import annotations

from pathlib import Path

import yaml


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
    start = script.find("run_all()")
    assert start != -1
    end = script.find("\nusage_error()", start)
    assert end != -1
    run_all_block = script[start:end]
    idx_fix = run_all_block.find("run_markdown_autofix_if_needed")
    idx_lint = run_all_block.find("run_markdown_lint_if_needed")
    assert 0 <= idx_fix < idx_lint, "auto-fix must run before lint inside run_all()"


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


def test_pre_commit_quality_markdown_globs_include_mdc() -> None:
    script = _quality_script_text()
    assert r"\.(md|mdc)$" in script
    assert "mapfile" not in script
    assert "pyproject.toml|setup.py|src/__init__.py" not in script
    assert "*.md|*.mdc|*.rst" in script
    pre_commit = Path(__file__).resolve().parents[3] / ".pre-commit-config.yaml"
    data = yaml.safe_load(pre_commit.read_text(encoding="utf-8"))
    hooks = []
    for repo in data.get("repos", []):
        hooks.extend(repo.get("hooks") or [])
    by_id = {h["id"]: h for h in hooks if isinstance(h, dict) and "id" in h}
    for hid in ("cli-block1-markdown-fix", "cli-block1-markdown-lint"):
        pat = str(by_id[hid].get("files", ""))
        assert r".(md|mdc)" in pat.replace("\\", "") or "(md|mdc)" in pat


def test_pre_commit_staged_files_includes_deletions_for_block2() -> None:
    """staged_files() must list deleted paths so deletion-only commits are not 'safe' skips."""
    script = _quality_script_text()
    assert "--diff-filter=ACMRD" in script

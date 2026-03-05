from __future__ import annotations

from pathlib import Path


def _script_text() -> str:
    return (Path(__file__).resolve().parents[3] / "scripts" / "pre-commit-smart-checks.sh").read_text(encoding="utf-8")


def test_pre_commit_markdown_checks_run_autofix_before_lint() -> None:
    script = _script_text()
    assert "run_markdown_autofix_if_needed" in script
    assert "markdownlint --fix --config .markdownlint.json" in script
    assert "run_markdown_autofix_if_needed\nrun_markdown_lint_if_needed" in script


def test_pre_commit_markdown_autofix_restages_files() -> None:
    script = _script_text()
    assert "xargs -r git add --" in script


def test_pre_commit_markdown_autofix_rejects_partial_staging() -> None:
    script = _script_text()
    assert 'git diff --quiet -- "$file"' in script
    assert "Cannot auto-fix Markdown with unstaged hunks" in script

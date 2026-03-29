from __future__ import annotations

from pathlib import Path


def _docs_text() -> str:
    return (Path(__file__).resolve().parents[3] / "docs" / "modules" / "code-review.md").read_text(encoding="utf-8")


def test_code_review_docs_cover_pre_commit_gate_and_portable_adoption() -> None:
    docs = _docs_text()
    assert "## Pre-Commit Review Gate" in docs
    assert ".pre-commit-config.yaml" in docs
    assert "specfact code review run" in docs
    assert ".specfact/code-review.json" in docs
    assert "verbose: true" in docs
    assert "Verdict line, report file, and Copilot" in docs
    assert "Code review summary" in docs
    assert "copilot" in docs.lower()
    assert "## Add to Any Project" in docs


def test_code_review_docs_describe_json_first_ledger_usage() -> None:
    docs = _docs_text()
    assert "~/.specfact/ledger.json" in docs
    assert "Supabase" in docs
    assert "optional" in docs.lower()

"""Contract coverage for staged Requirements maturity selection."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_pre_commit_derives_and_forwards_staged_required_maturity() -> None:
    """Local source changes must receive the same maturity policy as CI diffs."""
    pre_commit = (REPO_ROOT / "scripts" / "pre-commit-quality-checks.sh").read_text(encoding="utf-8")

    assert "staged_required_maturity()" in pre_commit
    assert 'required_maturity="$(staged_required_maturity)"' in pre_commit
    assert '--required-maturity "$required_maturity"' in pre_commit

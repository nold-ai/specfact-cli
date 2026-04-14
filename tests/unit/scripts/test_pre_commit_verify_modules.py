"""Branch-aware module verify wrapper used by pre-commit (marketplace-06 policy)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
FLAG_SCRIPT = REPO_ROOT / "scripts" / "git-branch-module-signature-flag.sh"
VERIFY_WRAPPER = REPO_ROOT / "scripts" / "pre-commit-verify-modules.sh"


def test_verify_wrapper_invokes_branch_flag_and_payload_from_filesystem() -> None:
    body = VERIFY_WRAPPER.read_text(encoding="utf-8")
    assert "git-branch-module-signature-flag.sh" in body
    assert "--payload-from-filesystem" in body
    assert "--enforce-version-bump" in body
    assert "verify-modules-signature.py" in body


def _run_flag(*, cwd: Path) -> str:
    result = subprocess.run(
        ["bash", str(FLAG_SCRIPT)],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def _git_init_with_commit(repo: Path) -> None:
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    (repo / "README.md").write_text("x\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True, capture_output=True, text=True)


@pytest.mark.parametrize(
    ("branch", "expected"),
    (
        ("feature/foo", "--allow-unsigned"),
        ("dev", "--allow-unsigned"),
        ("main", "--require-signature"),
    ),
)
def test_git_branch_signature_flag(tmp_path: Path, branch: str, expected: str) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git_init_with_commit(repo)
    subprocess.run(["git", "branch", "-M", branch], cwd=repo, check=True, capture_output=True, text=True)
    assert _run_flag(cwd=repo) == expected

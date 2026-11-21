"""Exercise the real native-stack consumer preflight in isolated Git histories."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import yaml


_REPO_ROOT = Path(__file__).resolve().parents[3]


def _git(repo: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *arguments],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _history(tmp_path: Path) -> tuple[Path, str, str, str, str]:
    repo = tmp_path / "lineage"
    repo.mkdir()
    _git(repo, "init", "--quiet", "--initial-branch=dev")
    _git(repo, "config", "user.name", "Lineage control")
    _git(repo, "config", "user.email", "lineage@example.invalid")
    _git(repo, "config", "commit.gpgsign", "false")
    _git(repo, "commit", "--quiet", "--allow-empty", "-m", "protected baseline")
    protected = _git(repo, "rev-parse", "HEAD")
    _git(repo, "update-ref", "refs/remotes/origin/dev", protected)
    _git(repo, "commit", "--quiet", "--allow-empty", "-m", "verified runtime parent")
    parent = _git(repo, "rev-parse", "HEAD")
    _git(repo, "commit", "--quiet", "--allow-empty", "-m", "eligible planning child")
    candidate = _git(repo, "rev-parse", "HEAD")
    tree = _git(repo, "rev-parse", "HEAD^{tree}")
    unrelated = _git(repo, "commit-tree", tree, "-m", "unrelated proof")
    future = _git(repo, "commit-tree", tree, "-p", candidate, "-m", "future evidence")
    return repo, protected, parent, unrelated, future


def _preflight(repo: Path, proof_base: str, planning_base: str | None) -> subprocess.CompletedProcess[str]:
    workflow = yaml.safe_load((_REPO_ROOT / ".github/workflows/requirements-evidence.yml").read_text())
    steps = workflow["jobs"]["requirements-evidence"]["steps"]
    scripts = [step["run"] for step in steps if step.get("name") == "Reconcile Requirements evidence on fresh runner"]
    assert len(scripts) == 1
    preflight, _reconciliation = scripts[0].split('validator_site="', maxsplit=1)
    env = os.environ.copy()
    env["PROOF_BASE_COMMIT"] = proof_base
    env["REVIEW_BASE_BRANCH"] = "dev"
    env.pop("PLANNING_BASE_COMMIT", None)
    if planning_base is not None:
        env["PLANNING_BASE_COMMIT"] = planning_base
    return subprocess.run(
        ["bash", "--noprofile", "--norc", "-e", "-o", "pipefail", "-c", preflight],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_native_planning_parent_preserves_review_trust(tmp_path: Path) -> None:
    repo, protected, parent, _unrelated, _future = _history(tmp_path)
    ordinary = _preflight(repo, protected, None)
    assert ordinary.returncode == 0, ordinary.stderr
    native = _preflight(repo, protected, parent)
    assert native.returncode == 0, (
        "Authenticated planning parent newer than dev must reach reconciliation; "
        f"actual workflow preflight exited {native.returncode}: {native.stderr}"
    )


def test_independent_lineage_rejects_forged_trust_or_parent(tmp_path: Path) -> None:
    repo, protected, parent, unrelated, future = _history(tmp_path)
    forged_trust = _preflight(repo, unrelated, protected)
    assert forged_trust.returncode != 0, "Planning selection must not conceal unrelated protected trust"
    assert _preflight(repo, parent, protected).returncode != 0, "Trust cannot be newer than the review base"
    assert _preflight(repo, "invalid", protected).returncode != 0, "Malformed trust identity must be rejected"
    assert _preflight(repo, protected, unrelated).returncode != 0, "Unrelated planning ancestry must be rejected"
    assert _preflight(repo, protected, future).returncode != 0, "Evidence newer than the candidate must be rejected"
    valid = _preflight(repo, protected, parent)
    assert valid.returncode == 0, valid.stderr

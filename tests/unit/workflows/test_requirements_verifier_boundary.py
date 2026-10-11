"""A stacked parent cannot supply code used as the trusted delivery verifier."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import cast

import yaml


ROOT = Path(__file__).resolve().parents[3]


def _producer_steps() -> list[dict[str, str]]:
    workflow = cast(
        dict[str, object],
        yaml.load((ROOT / ".github/workflows/requirements-evidence.yml").read_text(), Loader=yaml.BaseLoader),
    )
    jobs = cast(dict[str, object], workflow["jobs"])
    producer = cast(dict[str, object], jobs["requirements-evidence-producer"])
    return cast(list[dict[str, str]], producer["steps"])


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.test",
            "-c",
            "commit.gpgsign=false",
            *args,
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=20,
    )
    return result.stdout.strip()


def test_producer_authenticates_before_trusted_verifier_selection() -> None:
    steps = _producer_steps()
    names = [step.get("name", "") for step in steps]
    authentication = names.index("Authenticate live native stack proof boundary")
    selection = names.index("Materialize trusted delivery verifier")
    execution = names.index("Verify frozen Requirements graph")
    assert authentication < selection < execution


def test_stacked_parent_bytes_cannot_be_archived_as_trusted_verifier(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-b", "dev")
    script = tmp_path / "scripts/check_reproducible_delivery.py"
    script.parent.mkdir()
    script.write_text("reviewed protected verifier\n")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "protected verifier")
    protected = _git(tmp_path, "rev-parse", "HEAD")
    _git(tmp_path, "checkout", "-b", "dependency-root")
    script.write_text("unmerged parent verifier\n")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "candidate parent")
    _git(tmp_path, "update-ref", "refs/remotes/origin/dependency-root", "HEAD")
    _git(tmp_path, "checkout", "-b", "dependency-child")
    step = next(step for step in _producer_steps() if step.get("name") == "Materialize trusted delivery verifier")
    runner = tmp_path / "runner"
    runner.mkdir()
    result = subprocess.run(
        ["bash", "-eo", "pipefail", "-c", step["run"]],
        cwd=tmp_path,
        env={
            "PATH": os.environ["PATH"],
            "RUNNER_TEMP": str(runner),
            "GITHUB_BASE_REF": "dependency-root",
            "GITHUB_ENV": str(tmp_path / "github.env"),
            "PROOF_BASE_COMMIT": protected,
        },
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr
    archived = runner / "trusted-requirements/scripts/check_reproducible_delivery.py"
    assert archived.read_text() == "reviewed protected verifier\n"

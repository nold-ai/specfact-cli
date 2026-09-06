"""Regression tests for main-relative Requirements promotion inputs."""

import os
import subprocess
from pathlib import Path
from typing import Any, cast

import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "requirements-evidence.yml"


def _step_command(name: str) -> str:
    parsed = yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    jobs = cast(dict[str, Any], parsed["jobs"])
    for job in jobs.values():
        for step in job.get("steps", []):
            if step.get("name") == name:
                return cast(str, step["run"])
    raise AssertionError(f"Missing workflow step: {name}")


def _assert_materializes_from_exact_main_base(tmp_path: Path, step_name: str, root_variable: str) -> None:
    github_environment = tmp_path / "github-environment"
    completed = subprocess.run(
        ["bash", "--noprofile", "--norc", "-eo", "pipefail", "-c", _step_command(step_name)],
        cwd=REPO_ROOT,
        env={
            **os.environ,
            "GITHUB_BASE_REF": "main",
            "GITHUB_ENV": str(github_environment),
            "RUNNER_TEMP": str(tmp_path),
        },
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    exported = dict(line.split("=", maxsplit=1) for line in github_environment.read_text().splitlines())
    trusted_root = Path(exported[root_variable])
    assert (trusted_root / "requirements/code-review/requirements.in").is_file()
    assert (trusted_root / "requirements/code-review/locked.txt").is_file()


def test_promotion_trusted_core_materializes_from_exact_main_base(tmp_path: Path) -> None:
    """Both trusted cores must retain the frozen review inputs."""
    failures: list[str] = []
    steps = (
        ("Materialize trusted Requirements core", "TRUSTED_REQUIREMENTS_ROOT"),
        ("Materialize trusted final Requirements core", "FINAL_TRUSTED_ROOT"),
    )
    for step_name, root_variable in steps:
        step_tmp_path = tmp_path / root_variable
        step_tmp_path.mkdir()
        try:
            _assert_materializes_from_exact_main_base(step_tmp_path, step_name, root_variable)
        except AssertionError as error:
            failures.append(f"{step_name}: {error}")
    assert not failures, "\n\n".join(failures)

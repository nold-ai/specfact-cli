"""Exercise release source authentication independently of the reviewed wrapper."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any, cast

import pytest
import yaml

from tests.unit.workflows.test_docs_module_authentication import JOBS, REPO_ROOT, _mutate_source, _signed_sources


NODE_ACTION = "actions/setup-node@48b55a011bda9f5d6aeb4c2d9c7362e8dae4041e"
NODE_VERSION = "24.16.0"


def _steps(filename: str, job: str) -> list[dict[str, Any]]:
    document = yaml.safe_load((REPO_ROOT / ".github/workflows" / filename).read_text())
    return cast(list[dict[str, Any]], document["jobs"][job]["steps"])


@pytest.mark.parametrize(("filename", "job"), JOBS)
@pytest.mark.parametrize("mutation", ["valid", "missing-signature", "payload-mismatch", "extra-unsigned-source"])
def test_authentication_ignores_reviewed_wrapper(tmp_path: Path, filename: str, job: str, mutation: str) -> None:
    """Run actual authentication with signed fixtures and a deliberately hostile wrapper."""
    modules, trusted = _signed_sources(tmp_path)
    _mutate_source(modules, trusted, mutation)
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    wrapper = scripts / "verify_docs_module_source.py"
    wrapper.write_text("raise RuntimeError('PR wrapper executed')\n" if mutation == "valid" else "pass\n")
    assert not (trusted / "scripts/verify_docs_module_source.py").exists()
    names = {"Authenticate module command sources", "Export module command source path"}
    script = "\n".join(step["run"] for step in _steps(filename, job) if step.get("name") in names)
    environment = {
        **os.environ,
        "PATH": str(Path(sys.executable).parent) + os.pathsep + os.environ["PATH"],
        "GITHUB_ENV": str(tmp_path / "exports"),
        "GITHUB_WORKSPACE": str(tmp_path),
    }
    result = subprocess.run(
        ["bash", "-c", script], cwd=tmp_path, env=environment, capture_output=True, text=True, check=False, timeout=30
    )
    assert (result.returncode == 0) is (mutation == "valid"), result.stdout + result.stderr
    assert (tmp_path / "exports").exists() is (mutation == "valid")


@pytest.mark.parametrize("job", ["tests", "compat-py311", "dependency-compatibility"])
def test_native_javascript_jobs_prepare_pinned_node(job: str) -> None:
    """Require explicit runtime setup before commands that can collect the native tests."""
    steps = _steps("pr-orchestrator.yml", job)
    setup = [step for step in steps if step.get("uses") == NODE_ACTION]
    assert len(setup) == 1, f"{job} must explicitly prepare the pinned Node runtime"
    assert setup[0]["with"]["node-version"] == NODE_VERSION
    commands = [
        index
        for index, step in enumerate(steps)
        if "pytest" in step.get("run", "") or "tools/smart_test_coverage.py" in step.get("run", "")
    ]
    assert commands, f"{job} must still execute its tests"
    assert steps.index(setup[0]) < min(commands)
    if job == "tests":
        assert setup[0]["if"] == "needs.changes.outputs.skip_expensive_tests_dev_to_main != 'true'"


def test_local_prerequisites_declare_native_node_runtime() -> None:
    """Developers can reproduce native workflow tests outside hosted runners."""
    prerequisites = (REPO_ROOT / "CONTRIBUTING.md").read_text().split("### Prerequisites", 1)[1]
    prerequisites = prerequisites.split("### ", 1)[0]
    assert f"Node.js {NODE_VERSION}" in prerequisites

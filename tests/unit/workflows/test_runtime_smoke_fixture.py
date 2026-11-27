"""Portable smoke identity cannot retarget native Requirements authority."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize("mismatch", [None, "repository", "commit", "tree"])
def test_portable_action_rejects_unreviewed_identity(tmp_path: Path, mismatch: str | None) -> None:
    action = yaml.safe_load((REPO_ROOT / ".github/actions/setup-runtime-smoke-fixture/action.yml").read_text())
    identity = json.loads((REPO_ROOT / "ci/runtime-smoke-fixture.lock.json").read_text())
    if mismatch is not None:
        identity[mismatch] = "unreviewed"
    (tmp_path / "ci").mkdir()
    (tmp_path / "ci/runtime-smoke-fixture.lock.json").write_text(json.dumps(identity))
    result = subprocess.run(
        ["bash", "-c", action["runs"]["steps"][0]["run"]], cwd=tmp_path, env=os.environ, capture_output=True, text=True
    )
    assert (result.returncode == 0) is (mismatch is None), result.stderr


def test_smoke_fixture_is_separate_from_native_proof_provider() -> None:
    proof = json.loads((REPO_ROOT / "ci/module-fixture.lock.json").read_text())
    portable = json.loads((REPO_ROOT / "ci/runtime-smoke-fixture.lock.json").read_text())
    assert proof["commit"] == "69f075819be5e1ceca1446b026b0417f19e584ca"
    assert portable["commit"] == "046d366c190af7a188d6f48953a96edb65e766db"
    workflow = yaml.safe_load((REPO_ROOT / ".github/workflows/pr-orchestrator.yml").read_text())
    for job in ("tests", "compat-py311", "runtime-smoke-macos", "runtime-smoke-windows"):
        assert any(
            step.get("uses") == "./.github/actions/setup-runtime-smoke-fixture"
            for step in workflow["jobs"][job]["steps"]
        )

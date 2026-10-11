"""Proof context retains the common ancestor when the protected base advances."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = ROOT / "scripts"
FIXTURE = ROOT / "tests/fixtures/native_stack_context.json"
PROBE = """
import json,sys
sys.path.insert(0,sys.argv[1])
import requirements_stack_context as context
routes=json.load(sys.stdin)
context._github_json=lambda path:routes[path]
raise SystemExit(context.main(["--event",sys.argv[2],"--output",sys.argv[3]]))
"""


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


@pytest.mark.parametrize("native", [False, True])
def test_proof_cli_uses_root_merge_base_after_protected_tip_advances(tmp_path: Path, native: bool) -> None:
    _git(tmp_path, "init", "-b", "dev")
    _git(tmp_path, "commit", "--allow-empty", "-m", "common")
    common = _git(tmp_path, "rev-parse", "HEAD")
    _git(tmp_path, "checkout", "-b", "dependency-root")
    _git(tmp_path, "commit", "--allow-empty", "-m", "root")
    root = _git(tmp_path, "rev-parse", "HEAD")
    _git(tmp_path, "checkout", "-b", "dependency-child")
    _git(tmp_path, "commit", "--allow-empty", "-m", "child")
    child = _git(tmp_path, "rev-parse", "HEAD")
    _git(tmp_path, "checkout", "dev")
    _git(tmp_path, "commit", "--allow-empty", "-m", "advanced base")
    tip = _git(tmp_path, "rev-parse", "HEAD")
    payload = json.loads(FIXTURE.read_text().replace("a" * 40, tip).replace("b" * 40, root).replace("c" * 40, child))
    if not native:
        parent_path = "/repos/nold-ai/specfact-cli/pulls?state=open&head=nold-ai%3Adependency-root&per_page=100"
        pull = payload["routes"][parent_path][0]
        pull["stack"] = None
        payload["event"]["pull_request"] = pull
        payload["routes"]["/repos/nold-ai/specfact-cli/pulls/744"] = pull
    event = tmp_path / "event.json"
    event.write_text(json.dumps(payload["event"]))
    output = tmp_path / "context.json"
    result = subprocess.run(
        [sys.executable, "-I", "-S", "-c", PROBE, str(SCRIPT_DIR), str(event), str(output)],
        input=json.dumps(payload["routes"]),
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr
    context = json.loads(output.read_text())
    assert tip != common
    assert context["proof_base_commit"] == common
    assert context["proof_head_commit"] == root
    assert context["proof_pull_request"] == 744

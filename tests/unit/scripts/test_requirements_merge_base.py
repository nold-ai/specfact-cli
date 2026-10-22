"""Proof context retains the common ancestor when the protected base advances."""

from __future__ import annotations

import json
import os
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


def _fixture_git_env() -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
    return env


def _git(repo: Path, *args: str) -> str:
    env = _fixture_git_env()
    if args[0] != "init":
        actual = subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", "--absolute-git-dir"], env=env, text=True, timeout=20
        ).strip()
        if Path(actual).resolve() != repo.resolve() / ".git":
            raise RuntimeError("git-fixture-outside-owned-root")
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
        env=env,
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
        env=_fixture_git_env(),
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


@pytest.mark.parametrize(
    ("variable", "query", "target"),
    [
        ("GIT_DIR", "--absolute-git-dir", ".git"),
        ("GIT_COMMON_DIR", "--git-common-dir", ".git"),
        ("GIT_WORK_TREE", "--show-toplevel", ""),
    ],
)
def test_git_fixture_ignores_foreign_repository_selectors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, variable: str, query: str, target: str
) -> None:
    owned, foreign = tmp_path / "owned", tmp_path / "foreign"
    for repo in (owned, foreign):
        repo.mkdir()
        subprocess.run(
            ["git", "init", "-q", str(repo)],
            env={"PATH": os.environ["PATH"], "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"},
            check=True,
            capture_output=True,
            text=True,
            timeout=20,
        )
    monkeypatch.setenv(variable, str(foreign if variable == "GIT_WORK_TREE" else foreign / ".git"))
    observed = Path(_git(owned, "rev-parse", query))
    if not observed.is_absolute():
        observed = owned / observed
    assert observed.resolve() == (owned / target).resolve()

"""Ordinary forks retain their own protected-base proof without native parent privileges."""

from __future__ import annotations

import copy
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
from requirements_stack_context import resolve_stack_context
payload=json.load(sys.stdin)
print(json.dumps(resolve_stack_context(payload["event"],lambda path:payload["routes"][path])))
"""


def _fork_payload(failure: str | None) -> dict[str, object]:
    fixture = json.loads(FIXTURE.read_text())
    pull = copy.deepcopy(fixture["event"]["pull_request"])
    pull.update(state="open", stack=None)
    pull["base"].update(ref="main", sha="a" * 40)
    pull["head"].update(ref="dev", repo={"id": 9, "full_name": "outside/specfact-cli"})
    if failure == "native-fork":
        pull["stack"] = fixture["event"]["pull_request"]["stack"]
    if failure == "foreign-base":
        pull["base"]["repo"] = {"id": 9, "full_name": "outside/specfact-cli"}
    event = {"repository": fixture["event"]["repository"], "pull_request": copy.deepcopy(pull)}
    if failure == "stale-head-repository":
        pull["head"]["repo"]["full_name"] = "outside/other"
    return {"event": event, "routes": {"/repos/nold-ai/specfact-cli/pulls/727": pull}}


@pytest.mark.parametrize("failure", [None, "native-fork", "foreign-base", "stale-head-repository"])
def test_ordinary_fork_context_preserves_own_proof_boundary(failure: str | None) -> None:
    result = subprocess.run(
        [sys.executable, "-I", "-S", "-c", PROBE, str(SCRIPT_DIR)],
        input=json.dumps(_fork_payload(failure)),
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )
    if failure is not None:
        assert result.returncode != 0
        assert "stack-context-invalid" in result.stderr
    else:
        assert result.returncode == 0, result.stderr
        context = json.loads(result.stdout)
        assert context["stack"] is None
        assert context["proof_pull_request"] == 727
        assert context["proof_base_ref"] == "main"
        assert context["proof_head_branch"] == "dev"
        assert len(context["members"]) == 1

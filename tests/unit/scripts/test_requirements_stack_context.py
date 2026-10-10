"""Reject mutable stack relationships before choosing retained proof."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE = REPO_ROOT / "tests/fixtures/native_stack_context.json"
CHILD_PROBE = """
import json, sys
sys.path.insert(0, sys.argv[1])
from scripts.requirements_stack_context import resolve_stack_context
payload = json.load(sys.stdin)
def get_json(path):
    return payload["routes"][path]
print(json.dumps(resolve_stack_context(payload["event"], get_json), sort_keys=True))
"""


def _probe(payload: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-I", "-S", "-c", CHILD_PROBE, str(REPO_ROOT)],
        input=payload,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )


def test_native_stack_uses_original_root_proof_boundary() -> None:
    """A real native parent edge must retain its root branch and immutable base."""
    result = _probe(FIXTURE.read_text())
    assert result.returncode == 0, result.stderr
    context = json.loads(result.stdout)
    assert context["proof_base_commit"] == "a" * 40
    assert context["proof_head_branch"] == "dependency-root"
    assert context["proof_pull_request"] == 744
    assert context["pull_request"] == 727
    assert context["head_commit"] == "c" * 40
    assert [member["pull_request"] for member in context["members"]] == [744, 727]


@pytest.mark.parametrize("field", ["id", "number", "size", "position"])
def test_changed_parent_stack_identity_is_rejected(field: str) -> None:
    payload = json.loads(FIXTURE.read_text())
    parent_route = "/repos/nold-ai/specfact-cli/pulls?state=open&head=nold-ai%3Adependency-root&per_page=100"
    payload["routes"][parent_route][0]["stack"][field] += 1
    result = _probe(json.dumps(payload))
    assert result.returncode != 0
    assert "stack-context-invalid" in result.stderr


def test_unrelated_commit_chain_is_rejected() -> None:
    payload = json.loads(FIXTURE.read_text())
    compare_route = "/repos/nold-ai/specfact-cli/compare/" + "b" * 40 + "..." + "c" * 40
    payload["routes"][compare_route]["merge_base_commit"]["sha"] = "d" * 40
    result = _probe(json.dumps(payload))
    assert result.returncode != 0
    assert "stack-context-invalid" in result.stderr


def test_ambiguous_parent_is_rejected() -> None:
    payload = json.loads(FIXTURE.read_text())
    parent_route = "/repos/nold-ai/specfact-cli/pulls?state=open&head=nold-ai%3Adependency-root&per_page=100"
    payload["routes"][parent_route].append(payload["routes"][parent_route][0])
    result = _probe(json.dumps(payload))
    assert result.returncode != 0
    assert "stack-context-invalid" in result.stderr


def test_forked_parent_is_rejected() -> None:
    payload = json.loads(FIXTURE.read_text())
    parent_route = "/repos/nold-ai/specfact-cli/pulls?state=open&head=nold-ai%3Adependency-root&per_page=100"
    payload["routes"][parent_route][0]["head"]["repo"] = {"id": 9, "full_name": "outside/specfact-cli"}
    result = _probe(json.dumps(payload))
    assert result.returncode != 0
    assert "stack-context-invalid" in result.stderr


def test_stale_event_head_is_rejected() -> None:
    payload = json.loads(FIXTURE.read_text())
    payload["routes"]["/repos/nold-ai/specfact-cli/pulls/727"]["head"]["sha"] = "d" * 40
    result = _probe(json.dumps(payload))
    assert result.returncode != 0
    assert "stack-context-invalid" in result.stderr

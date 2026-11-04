"""Local replay unit contract, not native proof or protected adoption authority."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any, cast

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
RUN_RECORD = REPO_ROOT / "tests/fixtures/requirements-proof/pr786-native34-run.json"
API_SHA256 = "df109a62bd249f55dd25b6d3d22ba5a5b92d0d8d0815334ee424b0b9ab89a072"
SOURCE_COMMIT = "22b2fa7bd763b18ada1bfd1a9ea482a624f34cca"
EXECUTOR_COMMIT = "7b6b5fc1af7b57c2eb5a3546b7578a81175e4dfa"


@pytest.fixture
def owner() -> Iterator[Any]:
    path = REPO_ROOT / "scripts/requirements_late_red_proof.py"
    spec = importlib.util.spec_from_file_location("_fixed786_transfer_owner", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load the existing late-RED owner")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
        yield module
    finally:
        sys.modules.pop(spec.name, None)


@pytest.fixture
def recorded_run() -> dict[str, Any]:
    payload = RUN_RECORD.read_bytes()
    if hashlib.sha256(payload).hexdigest() != API_SHA256:
        raise RuntimeError("Retained API fixture differs from the reviewed bytes")
    return cast(dict[str, Any], json.loads(payload))


@pytest.mark.parametrize(
    "mutation",
    [
        "actual-record",
        "executor-is-source",
        "core-repository",
        "other-run",
        "other-attempt",
        "other-tree",
        "other-branch",
        "other-workflow",
        "pull-request-event",
        "in-progress",
        "failed-executor",
        "coherent-other-executor",
        "coherent-other-source",
        "historical-scope",
    ],
)
def test_fixed786_run_identity(owner: Any, recorded_run: dict[str, Any], mutation: str) -> None:
    manifest = {
        "kind": "fixed-pr786-native-red-proof",
        "pull_request": 786,
        "change_id": "security-dependencies-0-55-11-dev",
        "repository": "nold-ai/specfact-cli",
        "red_commit": SOURCE_COMMIT,
        "red_tree": "fd6a43314d221ee03f6bf476c737487a71aa3677",
        "executor_repository": "nold-ai/.github",
        "executor_commit": EXECUTOR_COMMIT,
        "executor_tree": "3967631c545b5d6ad9bd1132d635cb5b39b3dd78",
        "executor_head_branch": "codex/dev786-original-native-34",
        "executor_workflow_path": ".github/workflows/native-materialization-preflight.yml",
        "executor_workflow_name": "Native materialization development preflight 34",
        "executor_event": "create",
        "executor_conclusion": "success",
        "run_id": 41082128288,
        "run_attempt": 1,
    }
    scope = owner._ProofScope(
        "security-dependencies-0-55-11-dev", 786, "codex/security-dependencies-0-55-11-dev", "red", "red"
    )
    run = copy.deepcopy(recorded_run)
    run_updates = {
        "executor-is-source": {"head_sha": SOURCE_COMMIT},
        "core-repository": {"repository": run["repository"] | {"full_name": "nold-ai/specfact-cli"}},
        "other-run": {"id": run["id"] + 1},
        "other-attempt": {"run_attempt": run["run_attempt"] + 1},
        "other-tree": {"head_commit": run["head_commit"] | {"tree_id": "0" * 40}},
        "other-branch": {"head_branch": "synthetic-other-executor-branch"},
        "other-workflow": {"path": ".github/workflows/requirements-evidence.yml"},
        "pull-request-event": {"event": "pull_request"},
        "in-progress": {"status": "in_progress"},
        "failed-executor": {"conclusion": "failure"},
        "coherent-other-executor": {
            "head_sha": "0" * 40,
            "head_commit": run["head_commit"] | {"id": "0" * 40},
        },
    }
    manifest_updates = {
        "coherent-other-executor": {"executor_commit": "0" * 40},
        "coherent-other-source": {"red_commit": EXECUTOR_COMMIT, "red_tree": manifest["executor_tree"]},
    }
    run.update(run_updates.get(mutation, {}))
    manifest.update(manifest_updates.get(mutation, {}))
    if mutation == "historical-scope":
        scope = owner._PROOF_SCOPES[0]
    accepted = True
    try:
        owner._validate_run(run, manifest, scope)
    except ValueError:
        accepted = False
    assert accepted is (mutation == "actual-record"), (
        f"Fixed PR786 run identity admission mismatch for {mutation}. "
        "The genuine auxiliary executor and SOURCE_COMMIT source must remain distinct. "
        "This assertion concerns only local run-metadata admission."
    )

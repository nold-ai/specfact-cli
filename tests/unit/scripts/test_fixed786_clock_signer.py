from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[3]
CLOCK = (
    "refs/heads/codex/dev786-berlin-clock-signer-20261115",
    "refs/heads/codex/security-dev-berlin-clock-candidate-20261115",
    "e753ac1a3e4bb3bf739bd7203c728a652db6cb90",
)
LEGACY = (
    "refs/heads/codex/dev786-ci-tail-signer-20261104",
    "refs/heads/codex/security-dev-ci-tail-candidate-20261104",
    "b0184ae8c3de2c107d888dc23b0e7402a31d520e",
)


@pytest.fixture
def owner() -> ModuleType:
    spec = importlib.util.spec_from_file_location("_clock_signer_owner", ROOT / "scripts/requirements_late_red_proof.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("origin", [LEGACY, CLOCK])
def test_intent_accepts_only_matching_executor_origin(owner: ModuleType, monkeypatch: pytest.MonkeyPatch, origin: tuple[str, str, str]) -> None:
    program = b"synthetic finite signer"
    pin = (("scripts/dev_security_ci_signer.py", hashlib.sha256(program).hexdigest()),)
    name = "_FIXED_PR786_CLOCK_SIGNER_FILES" if origin == CLOCK else "_FIXED_PR786_SIGNER_FILES"
    monkeypatch.setattr(owner, name, pin)
    intent = {
        "repository_id": 7, "repository_full_name": "nold-ai/specfact-cli",
        "actor": {}, "triggering_actor": {},
        "dev": "9b5ad1e78430cc0b061cb16de42f73de96f4f312", "main": "1" * 40,
        "checkpoints": [], "auxiliary_ref": origin[0], "destination": origin[1],
    }
    raw = json.dumps(intent).encode()
    helper = ModuleType("synthetic_api")
    helper._api_json = lambda *args: ({"id": 7, "full_name": "nold-ai/specfact-cli"}, None)
    monkeypatch.setenv("GITHUB_TOKEN", "synthetic-no-network")
    monkeypatch.setattr(owner, "_fixed_pr786_blob", lambda helper, tree, path: raw if path.endswith("intent.json") else program)
    result = owner._fixed_pr786_intent(helper, {}, hashlib.sha256(raw).hexdigest())
    assert result == intent
    assert owner._fixed_pr786_origin(result) == origin
    intent["destination"] = CLOCK[1] if origin == LEGACY else LEGACY[1]
    raw = json.dumps(intent).encode()
    with pytest.raises(ValueError):
        owner._fixed_pr786_intent(helper, {}, hashlib.sha256(raw).hexdigest())


@pytest.mark.parametrize("origin", [LEGACY, CLOCK])
def test_output_chain_stops_at_its_own_authenticated_source_root(owner: ModuleType, monkeypatch: pytest.MonkeyPatch, origin: tuple[str, str, str]) -> None:
    parent = origin[2]
    final = {"sha": "f" * 40, "parents": [{"sha": parent}]}
    checkpoints = [{"source_parent": parent, "source_commit": "a" * 40, "source_tree": "b" * 40, "source_message": "normal source"}]
    helper = ModuleType("synthetic_api")
    helper._api_json = lambda *args: ({"sha": parent}, None)
    monkeypatch.setenv("GITHUB_TOKEN", "synthetic-no-network")
    monkeypatch.setattr(owner, "_fixed_pr786_signed", lambda *args: None)
    owner._fixed_pr786_outputs(helper, final, checkpoints, ("c" * 64, "d" * 40, 91))
    helper._api_json = lambda *args: ({"sha": LEGACY[2] if origin == CLOCK else CLOCK[2]}, None)
    with pytest.raises(ValueError):
        owner._fixed_pr786_outputs(helper, final, checkpoints, ("c" * 64, "d" * 40, 91))

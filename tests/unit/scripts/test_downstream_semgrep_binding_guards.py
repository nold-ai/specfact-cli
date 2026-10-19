from __future__ import annotations

import base64
import json
import subprocess
from pathlib import Path
from typing import Protocol, cast
from unittest.mock import call, patch

import pytest

from tests.unit.scripts import test_downstream_semgrep as contract


wheel_recipe = contract.wheel_recipe
POLICY_PATH = "ci/downstream-semgrep-admissions.json"
PROTECTED_COMMIT = "a" * 40
BRANCH_COMMAND = ["gh", "api", "--hostname", "github.com", "repos/nold-ai/specfact-cli/branches/dev"]
POLICY_COMMAND = [
    "gh",
    "api",
    "--hostname",
    "github.com",
    f"repos/nold-ai/specfact-cli/contents/{POLICY_PATH}?ref={PROTECTED_COMMIT}",
]


class PolicyModule(contract.DownstreamModule, Protocol):
    def _fetch_protected_policy(self) -> dict[str, object]: ...


def _response(payload: object) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(["gh"], 0, json.dumps(payload), "")


def _policy_response(policy: object) -> dict[str, object]:
    return {
        "encoding": "base64",
        "path": POLICY_PATH,
        "type": "file",
        "content": base64.b64encode(json.dumps(policy).encode("utf-8")).decode("ascii"),
    }


def test_policy_fetch_pins_canonical_protected_dev_commit() -> None:
    module = cast(PolicyModule, contract._module())
    policy = {"schema_version": 1, "admissions": []}
    responses = [
        _response({"protected": True, "commit": {"sha": PROTECTED_COMMIT}}),
        _response(_policy_response(policy)),
    ]
    with patch.object(module, "_run", side_effect=responses) as run:
        assert module._fetch_protected_policy() == policy
    assert run.call_args_list == [call(BRANCH_COMMAND), call(POLICY_COMMAND)]


@pytest.mark.parametrize(
    ("protected", "commit", "message"),
    [
        (False, PROTECTED_COMMIT, "Canonical dev branch is not protected"),
        ("true", PROTECTED_COMMIT, "Canonical dev branch is not protected"),
        (True, "dev", "Invalid immutable digest"),
        (True, "a" * 39, "Invalid immutable digest"),
    ],
    ids=["unprotected", "truthy-protection", "mutable-ref", "short-sha"],
)
def test_policy_fetch_rejects_untrusted_branch(protected: object, commit: str, message: str) -> None:
    module = cast(PolicyModule, contract._module())
    with (
        patch.object(
            module,
            "_run",
            side_effect=[
                _response({"protected": protected, "commit": {"sha": commit}}),
                _response(_policy_response({"schema_version": 1, "admissions": []})),
            ],
        ) as run,
        pytest.raises(ValueError, match=message),
    ):
        module._fetch_protected_policy()
    run.assert_called_once_with(BRANCH_COMMAND)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("path", "ci/candidate-admissions.json", "Unexpected canonical policy response"),
        ("encoding", "utf-8", "Unexpected canonical policy response"),
        ("type", "dir", "Unexpected canonical policy response"),
        ("content", "not valid base64!", "Invalid protected policy encoding"),
        ("content", base64.b64encode(b"not JSON").decode("ascii"), "Invalid JSON evidence"),
    ],
    ids=["wrong-path", "wrong-encoding", "not-file", "malformed-base64", "malformed-json"],
)
def test_policy_fetch_rejects_invalid_content_response(field: str, value: str, message: str) -> None:
    module = cast(PolicyModule, contract._module())
    response = _policy_response({"schema_version": 1, "admissions": []})
    response[field] = value
    with (
        patch.object(
            module,
            "_run",
            side_effect=[_response({"protected": True, "commit": {"sha": PROTECTED_COMMIT}}), _response(response)],
        ) as run,
        pytest.raises(ValueError, match=message),
    ):
        module._fetch_protected_policy()
    assert run.call_args_list == [call(BRANCH_COMMAND), call(POLICY_COMMAND)]


def test_admission_cannot_use_local_or_mutable_candidate_policy(
    wheel_recipe: contract.WheelRecipe, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = contract._module()
    candidate, bundle, candidate_policy = contract._protected_fixture(module, wheel_recipe, tmp_path)
    local_policy = tmp_path / POLICY_PATH
    local_policy.parent.mkdir()
    contract._write_json(local_policy, candidate_policy)
    contract._write_json(bundle / "downstream-semgrep-admissions.json", candidate_policy)
    monkeypatch.chdir(tmp_path)
    immutable_response = _response(_policy_response({"schema_version": 1, "admissions": []}))
    mutable_response = _response(_policy_response(candidate_policy))
    api_responses = {
        BRANCH_COMMAND[-1]: _response({"protected": True, "commit": {"sha": PROTECTED_COMMIT}}),
        POLICY_COMMAND[-1]: immutable_response,
        f"repos/nold-ai/specfact-cli/contents/{POLICY_PATH}?ref=dev": mutable_response,
        f"repos/nold-ai/specfact-cli/contents/{POLICY_PATH}": mutable_response,
    }

    def api_response(command: list[str]) -> subprocess.CompletedProcess[str]:
        if command[:3] == ["gh", "attestation", "verify"]:
            return _response([{"verified": True}])
        return api_responses[command[-1]]

    with (
        patch.object(module, "_run", side_effect=api_response) as run,
        pytest.raises(ValueError, match="Recipe has no unique protected approval"),
    ):
        module.admit_artifact(candidate.path, bundle)
    assert run.call_args_list == [call(BRANCH_COMMAND), call(POLICY_COMMAND)]


def test_matrix_preserves_bound_hashes_without_granting_admission(wheel_recipe: contract.WheelRecipe) -> None:
    module = contract._module()
    recipe_path, recipe, _upstream = wheel_recipe
    reports = contract._reports(recipe_path, recipe)
    candidates = {platform: contract._sha(platform.encode("utf-8")) for platform in contract.PLATFORMS}
    for report in reports:
        report["candidate_sha256"] = candidates[report["platform"]]
    assert module.aggregate_candidate_reports(recipe_path, reports) == {
        "status": "passed",
        "production_admission": "not_requested",
        "recipe_sha256": contract._sha(recipe_path.read_bytes()),
        "artifacts": candidates,
        "source_commit": "d" * 40,
    }


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("recipe_sha256", "f" * 64, "Cell input binding differs"),
        ("upstream_sha256", "f" * 64, "Cell input binding differs"),
    ],
    ids=["recipe", "upstream"],
)
def test_matrix_rejects_single_cell_hash_damage(
    wheel_recipe: contract.WheelRecipe, field: str, value: str, message: str
) -> None:
    module = contract._module()
    recipe_path, recipe, _upstream = wheel_recipe
    reports = contract._reports(recipe_path, recipe)
    damaged: dict[str, object] = dict(reports[-1])
    damaged[field] = value
    reports[-1] = cast(contract.MatrixReport, damaged)
    with pytest.raises(ValueError, match=message):
        module.aggregate_candidate_reports(recipe_path, reports)


def test_matrix_rejects_malformed_candidate_digest_despite_platform_agreement(
    wheel_recipe: contract.WheelRecipe,
) -> None:
    module = contract._module()
    recipe_path, recipe, _upstream = wheel_recipe
    reports = contract._reports(recipe_path, recipe)
    for report in reports:
        if report["platform"] == contract.PLATFORMS[-1]:
            report["candidate_sha256"] = "g" * 64
    with pytest.raises(ValueError, match="Invalid immutable digest"):
        module.aggregate_candidate_reports(recipe_path, reports)


@pytest.mark.parametrize("python_index", [0, 1, 2], ids=["python311", "python312", "python313"])
def test_matrix_rejects_same_platform_candidate_disagreement(
    wheel_recipe: contract.WheelRecipe, python_index: int
) -> None:
    module = contract._module()
    recipe_path, recipe, _upstream = wheel_recipe
    reports = contract._reports(recipe_path, recipe)
    reports[python_index]["candidate_sha256"] = "f" * 64
    with pytest.raises(ValueError, match="Platform cells used different candidate artifacts"):
        module.aggregate_candidate_reports(recipe_path, reports)

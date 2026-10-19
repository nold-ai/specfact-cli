from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Literal

import pytest

from tests.unit.scripts import test_downstream_semgrep as contract


wheel_recipe = contract.wheel_recipe


@pytest.mark.parametrize("cell_index", [0, 1, 2, 20], ids=["first", "second", "third", "last"])
@pytest.mark.parametrize(
    "identity",
    ["candidate_sha256", "upstream_sha256", "recipe_sha256"],
    ids=["candidate", "upstream", "recipe"],
)
def test_matrix_rejects_identity_mismatch_in_otherwise_passing_cells(
    wheel_recipe: contract.WheelRecipe,
    cell_index: int,
    identity: Literal["candidate_sha256", "upstream_sha256", "recipe_sha256"],
) -> None:
    module = contract._module()
    recipe_path, recipe, _upstream = wheel_recipe
    reports = contract._reports(recipe_path, recipe)
    assert module.aggregate_candidate_reports(recipe_path, reports)["status"] == "passed"
    assert reports[cell_index][identity] != "f" * 64
    reports[cell_index][identity] = "f" * 64
    with pytest.raises(ValueError):
        module.aggregate_candidate_reports(recipe_path, reports)


@pytest.mark.parametrize("authority", ["admitted", "candidate"])
@pytest.mark.parametrize(
    "damage",
    ["nonempty-skip", "unexpected-dependency"],
    ids=["nonempty-skip", "unexpected-dependency"],
)
def test_bound_audit_rejects_skipped_or_extra_dependency(
    wheel_recipe: contract.WheelRecipe, tmp_path: Path, authority: str, damage: str
) -> None:
    module = contract._module()
    admitted, actual, candidate = contract._bound_audit(module, wheel_recipe, tmp_path)
    bound = (
        admitted.audit_input(actual, tmp_path / "audit.txt")
        if authority == "admitted"
        else candidate.candidate_audit_input(actual, tmp_path / "audit.txt")
    )
    result = contract._audit_result()
    valid = subprocess.CompletedProcess(["pip-audit"], 0, json.dumps(result), "")
    assert bound.assert_complete_result(valid)["status"] == "passed"
    if damage == "nonempty-skip":
        result["dependencies"][-1]["skip_reason"] = "Package could not be audited"
    else:
        result["dependencies"].append({"name": "unexpected-package", "version": "1.0.0", "vulns": []})
    with pytest.raises(ValueError):
        bound.assert_complete_result(subprocess.CompletedProcess(["pip-audit"], 0, json.dumps(result), ""))

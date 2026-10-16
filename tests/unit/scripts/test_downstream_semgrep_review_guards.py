from __future__ import annotations

import copy
import json
import subprocess
import zipfile
from pathlib import Path
from typing import cast
from unittest.mock import patch

import pytest

from tests.unit.scripts import test_downstream_semgrep as contract


wheel_recipe = contract.wheel_recipe


def test_admission_pins_exact_attestation_identity(wheel_recipe: contract.WheelRecipe, tmp_path: Path) -> None:
    module = contract._module()
    candidate, bundle, policy = contract._protected_fixture(module, wheel_recipe, tmp_path)
    result = subprocess.CompletedProcess(["gh"], 0, '[{"verified":true}]', "")
    with (
        patch.object(module, "_fetch_protected_policy", return_value=policy),
        patch.object(module.subprocess, "run", return_value=result) as run,
    ):
        admitted = module.admit_artifact(candidate.path, bundle)
    assert admitted.wheel == candidate.path
    run.assert_called_once()
    argv = run.call_args.args[0]
    assert argv[:4] == ["gh", "attestation", "verify", str(candidate.path.resolve())]
    assert argv.count("--deny-self-hosted-runners") == 1
    options = [item for item in argv[4:] if item != "--deny-self-hosted-runners"]
    assert len(options) % 2 == 0
    assert len(set(options[::2])) == len(options[::2])
    assert dict(zip(options[::2], options[1::2], strict=True)) == {
        "--hostname": "github.com",
        "--repo": "nold-ai/specfact-cli",
        "--signer-repo": "nold-ai/specfact-cli",
        "--signer-workflow": "nold-ai/specfact-cli/.github/workflows/downstream-semgrep.yml",
        "--source-ref": "refs/heads/dev",
        "--source-digest": "d" * 40,
        "--signer-digest": "e" * 40,
        "--cert-oidc-issuer": "https://token.actions.githubusercontent.com",
        "--bundle": str((bundle / "provenance.jsonl").resolve()),
        "--format": "json",
    }


@pytest.mark.parametrize("damage", ["missing", "duplicate", "emulated", "failed-audit"])
def test_admission_rejects_approved_but_invalid_matrix(
    wheel_recipe: contract.WheelRecipe, tmp_path: Path, damage: str
) -> None:
    module = contract._module()
    candidate, bundle, policy = contract._protected_fixture(module, wheel_recipe, tmp_path)
    matrix = bundle / "matrix.json"
    reports = cast(list[contract.MatrixReport], json.loads(matrix.read_text(encoding="utf-8")))
    if damage == "failed-audit":
        reports[-1]["candidate_audit_passed"] = False
    else:
        contract._damage_matrix(reports, damage)
    contract._write_json(matrix, reports)
    policy["admissions"][0]["matrix_sha256"] = contract._sha(matrix.read_bytes())
    with (
        patch.object(module, "_fetch_protected_policy", return_value=policy),
        patch.object(module.subprocess, "run") as verifier,
        pytest.raises(ValueError),
    ):
        module.admit_artifact(candidate.path, bundle)
    verifier.assert_not_called()


@pytest.mark.parametrize(
    ("attribute", "value"),
    [
        ("date_time", (2025, 2, 3, 4, 5, 6)),
        ("internal_attr", 1),
        ("create_system", 0),
        ("extra", b"\xfe\xca\x02\x00ok"),
        ("comment", b"altered member header"),
        ("compress_type", zipfile.ZIP_DEFLATED),
        ("create_version", 21),
    ],
)
def test_candidate_rejects_preserved_member_header_changes(
    wheel_recipe: contract.WheelRecipe, tmp_path: Path, attribute: str, value: object
) -> None:
    module = contract._module()
    recipe_path, _recipe, upstream = wheel_recipe
    candidate = module.build_candidate(recipe_path, upstream, tmp_path / "candidate")
    with zipfile.ZipFile(candidate.path) as archive:
        members = [(copy.copy(info), archive.read(info)) for info in archive.infolist()]
        record_name = f"semgrep-{contract.DOWNSTREAM}.dist-info/RECORD"
        record = archive.read(record_name)
    target = f"semgrep-{contract.DOWNSTREAM}.data/purelib/semgrep/main.py"
    with zipfile.ZipFile(candidate.path, "w") as archive:
        for info, content in members:
            if info.filename == target:
                setattr(info, attribute, value)
            archive.writestr(info, content)
    with zipfile.ZipFile(candidate.path) as archive:
        assert archive.read(record_name) == record
        contract._assert_record(archive)
        assert getattr(archive.getinfo(target), attribute) == value
    with pytest.raises(ValueError, match="Candidate archive attributes changed"):
        module.verify_candidate(recipe_path, upstream, candidate.path)

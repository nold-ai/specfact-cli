from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from tests.unit.scripts import test_downstream_semgrep as contract


wheel_recipe = contract.wheel_recipe


@pytest.mark.parametrize("mutation", ["replace", "delete", "symlink", "in-place"])
def test_admission_materializes_verified_bytes_after_transport_mutation(
    wheel_recipe: contract.WheelRecipe, tmp_path: Path, mutation: str
) -> None:
    module = contract._module()
    candidate, bundle, policy = contract._protected_fixture(module, wheel_recipe, tmp_path)
    approved = candidate.path.read_bytes()
    authenticated: list[bytes] = []

    def attest(argv: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        snapshot = Path(argv[3])
        assert type(snapshot) is type(candidate.path)
        assert snapshot != candidate.path.resolve()
        assert snapshot.name == candidate.path.name
        authenticated.append(snapshot.read_bytes())
        return subprocess.CompletedProcess(argv, 0, '[{"verified":true}]', "")

    with (
        patch.object(module, "_fetch_protected_policy", return_value=policy),
        patch.object(module.subprocess, "run", side_effect=attest),
    ):
        admitted = module.admit_artifact(candidate.path, bundle)
    assert authenticated == [approved]
    _mutate_transport(candidate, tmp_path, mutation)
    wheel = _assert_materialized_snapshot(admitted, candidate, approved)
    _assert_failed_installer_cleanup(admitted, wheel, approved)


def _mutate_transport(candidate: contract.CandidateWheel, tmp_path: Path, mutation: str) -> None:
    if mutation == "in-place":
        before = candidate.path.stat()
        candidate.path.write_bytes(b"unapproved in-place overwrite")
        after = candidate.path.stat()
        assert (after.st_dev, after.st_ino) == (before.st_dev, before.st_ino)
    else:
        candidate.path.unlink()
        if mutation == "replace":
            candidate.path.write_bytes(b"unapproved replacement")
        elif mutation == "symlink":
            other = tmp_path / "other"
            other.write_bytes(b"unapproved symlink target")
            candidate.path.symlink_to(other)


def _assert_materialized_snapshot(
    admitted: contract.AdmittedWheel, candidate: contract.CandidateWheel, approved: bytes
) -> Path:
    with admitted.materialize() as wheel:
        assert type(wheel) is type(candidate.path)
        assert wheel.name == candidate.path.name
        assert wheel != candidate.path
        assert wheel.read_bytes() == approved
    assert not wheel.exists()
    assert not wheel.parent.exists()
    return wheel


def _assert_failed_installer_cleanup(admitted: contract.AdmittedWheel, wheel: Path, approved: bytes) -> None:
    with pytest.raises(RuntimeError, match="installer failed"), admitted.materialize() as failed_wheel:
        assert failed_wheel != wheel
        assert failed_wheel.read_bytes() == approved
        raise RuntimeError("installer failed")
    assert not failed_wheel.exists()
    assert not failed_wheel.parent.exists()

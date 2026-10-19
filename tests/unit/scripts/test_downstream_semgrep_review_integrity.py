from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import cast
from unittest.mock import patch

import pytest

from tests.unit.scripts import test_downstream_semgrep as contract
from tools.downstream_semgrep import test_mcp_regressions as lifecycle


wheel_recipe = contract.wheel_recipe


def test_admission_validates_the_approved_matrix_snapshot(wheel_recipe: contract.WheelRecipe, tmp_path: Path) -> None:
    module = contract._module()
    candidate, bundle, policy = contract._protected_fixture(module, wheel_recipe, tmp_path)
    matrix = bundle / "matrix.json"
    unapproved_valid_bytes = matrix.read_bytes()
    reports = cast(list[contract.MatrixReport], json.loads(unapproved_valid_bytes))
    reports[-1]["checks"]["mcp_lifecycle"] = False
    contract._write_json(matrix, reports)
    policy["admissions"][0]["matrix_sha256"] = contract._sha(matrix.read_bytes())
    read_bytes = Path.read_bytes

    def replace_after_read(path: Path) -> bytes:
        snapshot = read_bytes(path)
        if path == matrix:
            path.write_bytes(unapproved_valid_bytes)
        return snapshot

    with (
        patch.object(Path, "read_bytes", replace_after_read),
        patch.object(module, "_fetch_protected_policy", return_value=policy),
        patch.object(module, "_verify_provenance") as verifier,
        pytest.raises(ValueError, match="Required cell check missing or failed"),
    ):
        module.admit_artifact(candidate.path, bundle)
    verifier.assert_not_called()


@pytest.mark.parametrize(
    ("changed_read", "message"),
    [(2, "Approved recipe differs from matrix recipe"), (3, "Approved recipe differs from verified recipe")],
    ids=["aggregate", "candidate-verification"],
)
def test_admission_rejects_recipe_replacement_after_approval(
    wheel_recipe: contract.WheelRecipe, tmp_path: Path, changed_read: int, message: str
) -> None:
    module = contract._module()
    candidate, bundle, policy = contract._protected_fixture(module, wheel_recipe, tmp_path)
    recipe = bundle / "recipe.json"
    replacement = recipe.read_bytes() + b"\n"
    if changed_read == 2:
        matrix = bundle / "matrix.json"
        reports = cast(list[contract.MatrixReport], json.loads(matrix.read_bytes()))
        for report in reports:
            report["recipe_sha256"] = contract._sha(replacement)
        contract._write_json(matrix, reports)
        policy["admissions"][0]["matrix_sha256"] = contract._sha(matrix.read_bytes())
    read_bytes = Path.read_bytes
    recipe_reads = 0

    def replace_recipe_read(path: Path) -> bytes:
        nonlocal recipe_reads
        if path == recipe:
            recipe_reads += 1
            if recipe_reads == changed_read:
                return replacement
        return read_bytes(path)

    with (
        patch.object(Path, "read_bytes", replace_recipe_read),
        patch.object(module, "_fetch_protected_policy", return_value=policy),
        patch.object(module, "_verify_provenance") as verifier,
        pytest.raises(ValueError, match=message),
    ):
        module.admit_artifact(candidate.path, bundle)
    verifier.assert_not_called()


@pytest.mark.parametrize(
    ("timeout_default", "capacity_default"), [(None, 10000), (1800, None)], ids=["idle-timeout", "capacity"]
)
def test_lifecycle_default_probe_detects_insecure_constructor_defaults(
    timeout_default: float | None, capacity_default: int | None
) -> None:
    class ManagerWithInsecureDefaults:
        def __init__(
            self,
            app: object,
            *,
            session_idle_timeout: float | None = timeout_default,
            max_sessions: int | None = capacity_default,
            **_options: object,
        ) -> None:
            self.session_idle_timeout = session_idle_timeout
            self.max_sessions = max_sessions

    probe = lifecycle.TestMcpLifecycle("test_fixed_defaults")
    with (
        patch.object(lifecycle, "StreamableHTTPSessionManager", ManagerWithInsecureDefaults),
        pytest.raises(AssertionError),
    ):
        asyncio.run(probe.test_fixed_defaults())


@pytest.mark.parametrize(
    ("suffix", "mode", "message"),
    [("../outside", 0o100644, "Unsafe archive path"), ("purelib/link", 0o120777, "Linked or special archive member")],
    ids=["allowed-root-traversal", "allowed-root-symlink"],
)
def test_archive_guards_reject_unsafe_members_within_allowed_root(
    wheel_recipe: contract.WheelRecipe, tmp_path: Path, suffix: str, mode: int, message: str
) -> None:
    module = contract._module()
    recipe_path, recipe, upstream = wheel_recipe
    members = [*contract._members(), (f"semgrep-{contract.UPSTREAM}.data/{suffix}", b"target", mode)]
    contract._write_wheel(upstream, members)
    recipe["wheels"][0]["upstream_sha256"] = contract._sha(upstream.read_bytes())
    contract._write_json(recipe_path, recipe)
    output = tmp_path / "rejected-candidate"
    with pytest.raises(ValueError, match=message):
        module.build_candidate(recipe_path, upstream, output)
    assert not output.exists()

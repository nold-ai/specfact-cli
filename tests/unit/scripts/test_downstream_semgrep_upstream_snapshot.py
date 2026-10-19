from __future__ import annotations

import copy
from pathlib import Path
from unittest.mock import patch

import pytest

from tests.unit.scripts import test_downstream_semgrep as contract


wheel_recipe = contract.wheel_recipe


def _replacement(upstream: Path, tmp_path: Path) -> bytes:
    replacement = tmp_path / "replacement.whl"
    members = [
        (name, b"def main():\n    return 99\n" if name.endswith("/main.py") else content, mode)
        for name, content, mode in contract._members()
    ]
    contract._write_wheel(replacement, members)
    raw = replacement.read_bytes()
    assert raw != upstream.read_bytes()
    return raw


def _replace_after_read(monkeypatch: pytest.MonkeyPatch, target: Path, replacement: bytes) -> None:
    original = Path.read_bytes
    replaced = False

    def read(path: Path) -> bytes:
        nonlocal replaced
        raw = original(path)
        if path == target and not replaced:
            target.write_bytes(replacement)
            replaced = True
        return raw

    monkeypatch.setattr(Path, "read_bytes", read)


def _candidate_b(
    module: contract.DownstreamModule, fixture: contract.WheelRecipe, tmp_path: Path, replacement: bytes
) -> contract.CandidateWheel:
    _recipe_path, recipe, upstream = fixture
    alternate = copy.deepcopy(recipe)
    alternate["wheels"][0]["upstream_sha256"] = contract._sha(replacement)
    alternate_path = contract._write_json(tmp_path / "alternate-recipe.json", alternate)
    original = upstream.read_bytes()
    upstream.write_bytes(replacement)
    candidate = module.build_candidate(alternate_path, upstream, tmp_path / "candidate-b")
    upstream.write_bytes(original)
    return candidate


def test_build_uses_authenticated_upstream_snapshot(
    wheel_recipe: contract.WheelRecipe, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = contract._module()
    recipe_path, _recipe, upstream = wheel_recipe
    expected = module.build_candidate(recipe_path, upstream, tmp_path / "canonical-a").path.read_bytes()
    replacement = _replacement(upstream, tmp_path)
    alternate = _candidate_b(module, wheel_recipe, tmp_path, replacement).path.read_bytes()
    _replace_after_read(monkeypatch, upstream, replacement)
    actual = module.build_candidate(recipe_path, upstream, tmp_path / "actual").path.read_bytes()
    assert upstream.read_bytes() == replacement
    assert actual == expected
    assert actual != alternate


@pytest.mark.parametrize("candidate_identity", ["a", "b"])
def test_verify_uses_authenticated_upstream_snapshot(
    wheel_recipe: contract.WheelRecipe, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, candidate_identity: str
) -> None:
    module = contract._module()
    recipe_path, _recipe, upstream = wheel_recipe
    replacement = _replacement(upstream, tmp_path)
    candidate_a = module.build_candidate(recipe_path, upstream, tmp_path / "canonical-a")
    candidate_b = _candidate_b(module, wheel_recipe, tmp_path, replacement)
    _replace_after_read(monkeypatch, upstream, replacement)
    if candidate_identity == "a":
        assert module.verify_candidate(recipe_path, upstream, candidate_a.path).sha256 == candidate_a.sha256
    else:
        with pytest.raises(ValueError, match="Candidate payload changed"):
            module.verify_candidate(recipe_path, upstream, candidate_b.path)
    assert upstream.read_bytes() == replacement


@pytest.mark.parametrize("operation", ["build", "verify"])
def test_unapproved_initial_upstream_rejects(
    wheel_recipe: contract.WheelRecipe, tmp_path: Path, operation: str
) -> None:
    module = contract._module()
    recipe_path, _recipe, upstream = wheel_recipe
    candidate = module.build_candidate(recipe_path, upstream, tmp_path / "canonical-a")
    upstream.write_bytes(_replacement(upstream, tmp_path))
    destination = tmp_path / "refused"
    with pytest.raises(ValueError, match="Upstream wheel digest differs"):
        if operation == "build":
            module.build_candidate(recipe_path, upstream, destination)
        else:
            module.verify_candidate(recipe_path, upstream, candidate.path)
    assert not destination.exists()


def test_admission_rejects_candidate_replacement_after_protected_digest(
    wheel_recipe: contract.WheelRecipe, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = contract._module()
    candidate, bundle, policy = contract._protected_fixture(module, wheel_recipe, tmp_path)
    replacement = _replacement(wheel_recipe[2], tmp_path)
    alternate = _candidate_b(module, wheel_recipe, tmp_path, replacement)
    _replace_after_read(monkeypatch, candidate.path, alternate.path.read_bytes())
    with (
        patch.object(module, "_fetch_protected_policy", return_value=policy),
        patch.object(module, "_verify_provenance") as provenance,
        pytest.raises(ValueError, match="Candidate payload changed"),
    ):
        module.admit_artifact(candidate.path, bundle)
    provenance.assert_not_called()

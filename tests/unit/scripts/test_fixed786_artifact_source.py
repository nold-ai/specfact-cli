from __future__ import annotations

import copy
import importlib.util
import json
import sys
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType
from typing import cast

import pytest


FIXTURES = Path(__file__).with_name("fixtures") / "fixed786_artifact_source"
REPO_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def owner() -> Iterator[ModuleType]:
    path = REPO_ROOT / "scripts/requirements_late_red_proof.py"
    spec = importlib.util.spec_from_file_location("_fixed786_artifact_owner", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Existing late-RED owner cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
        yield module
    finally:
        sys.modules.pop(spec.name, None)


@pytest.fixture
def proof_inputs() -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    records = [
        cast(dict[str, object], json.loads((FIXTURES / filename).read_bytes()))
        for filename in ("manifest.json", "artifact-live-api.json", "source-R2-filtered-api.json")
    ]
    return records[0], records[1], records[2]


def test_actual_artifact_is_accepted_without_rewriting(
    owner: ModuleType,
    proof_inputs: tuple[dict[str, object], dict[str, object], dict[str, object]],
) -> None:
    manifest, packet_record, source_commit = proof_inputs
    original = copy.deepcopy(packet_record)
    original_source = copy.deepcopy(source_commit)
    accepted = True
    try:
        owner._validate_artifact({"artifacts": [packet_record], "source_commit": source_commit}, manifest)
    except ValueError:
        accepted = False
    assert accepted, "Existing artifact owner refuses actual E34 artifact association"
    assert packet_record == original
    assert source_commit == original_source


@pytest.mark.parametrize(
    "mutation",
    [
        ("", "id", 13270362279),
        ("", "id", True),
        ("", "id", 13269307808.0),
        ("", "id", "13269307808"),
        ("", "name", "requirements-evidence"),
        ("", "name", True),
        ("", "digest", "sha256:" + "0" * 64),
        ("", "digest", None),
        ("", "expired", True),
        ("", "expired", 0),
        ("", "expired", None),
        ("", "size_in_bytes", 1881845),
        ("", "size_in_bytes", True),
        ("", "size_in_bytes", 1885415.0),
        ("workflow_run", "id", 41082050407),
        ("workflow_run", "id", True),
        ("workflow_run", "id", 41715861806.0),
        ("workflow_run", "repository_id", 1110267668),
        ("workflow_run", "repository_id", True),
        ("workflow_run", "repository_id", 1110267669.0),
        ("workflow_run", "head_repository_id", 1110267668),
        ("workflow_run", "head_repository_id", False),
        ("workflow_run", "head_sha", "d77209f4b13c386e29391f93e1f1c58d7fd8622f"),
        ("workflow_run", "head_sha", "0" * 40),
        ("workflow_run", "head_sha", True),
        ("workflow_run", "head_branch", "codex/dev786-original-native-source-34"),
    ],
)
def test_artifact_rejects_mismatched_api_fields(
    owner: ModuleType,
    proof_inputs: tuple[dict[str, object], dict[str, object], dict[str, object]],
    mutation: tuple[str, str, object],
) -> None:
    manifest, packet_record, source_commit = proof_inputs
    section, field, value = mutation
    target = cast(dict[str, object], packet_record[section]) if section else packet_record
    target[field] = value
    with pytest.raises(ValueError):
        owner._validate_artifact({"artifacts": [packet_record], "source_commit": source_commit}, manifest)


@pytest.mark.parametrize(
    "mutation",
    [
        ("artifact_id", True),
        ("artifact_id", 13270362279),
        ("artifact_name", "requirements-evidence"),
        ("artifact_repository", "nold-ai/specfact-cli"),
        ("artifact_digest", "sha256:" + "0" * 64),
        ("run_id", True),
        ("run_attempt", True),
        ("run_attempt", 2),
        ("red_commit", "8ad0a9434ceeac4a910df3c374536d7c909badec"),
        ("red_tree", "0" * 40),
        ("executor_commit", "d77209f4b13c386e29391f93e1f1c58d7fd8622f"),
        ("executor_repository", "nold-ai/specfact-cli"),
    ],
)
def test_artifact_rejects_wrong_manifest_binding(
    owner: ModuleType,
    proof_inputs: tuple[dict[str, object], dict[str, object], dict[str, object]],
    mutation: tuple[str, object],
) -> None:
    manifest, packet_record, source_commit = proof_inputs
    field, value = mutation
    manifest[field] = value
    with pytest.raises(ValueError):
        owner._validate_artifact({"artifacts": [packet_record], "source_commit": source_commit}, manifest)


@pytest.mark.parametrize("field", ["artifact_id", "artifact_digest", "run_id", "executor_commit"])
def test_artifact_rejects_self_consistent_substitution(
    owner: ModuleType,
    proof_inputs: tuple[dict[str, object], dict[str, object], dict[str, object]],
    field: str,
) -> None:
    manifest, packet_record, source_commit = proof_inputs
    run = cast(dict[str, object], packet_record["workflow_run"])
    substitutions: dict[str, tuple[dict[str, object], str, object]] = {
        "artifact_id": (packet_record, "id", 13270362279),
        "artifact_digest": (packet_record, "digest", "sha256:" + "0" * 64),
        "run_id": (run, "id", 41082050407),
        "executor_commit": (run, "head_sha", "0" * 40),
    }
    target, key, value = substitutions[field]
    manifest[field] = target[key] = value
    with pytest.raises(ValueError):
        owner._validate_artifact({"artifacts": [packet_record], "source_commit": source_commit}, manifest)


@pytest.mark.parametrize("entries", [None, [], [None], [True]])
def test_artifact_rejects_invalid_collection(
    owner: ModuleType,
    proof_inputs: tuple[dict[str, object], dict[str, object], dict[str, object]],
    entries: object,
) -> None:
    manifest, _, _ = proof_inputs
    with pytest.raises(ValueError):
        owner._validate_artifact({"artifacts": entries}, manifest)


def test_artifact_rejects_duplicate_named_entries(
    owner: ModuleType,
    proof_inputs: tuple[dict[str, object], dict[str, object], dict[str, object]],
) -> None:
    manifest, packet_record, source_commit = proof_inputs
    with pytest.raises(ValueError):
        owner._validate_artifact(
            {"artifacts": [packet_record, copy.deepcopy(packet_record)], "source_commit": source_commit}, manifest
        )


@pytest.mark.parametrize("defect", [None, "expired", "digest", "head_sha", "duplicate"])
def test_historical_artifact_contract_is_preserved(owner: ModuleType, defect: str | None) -> None:
    manifest: dict[str, object] = {
        "kind": "late-red-proof",
        "artifact_id": 123,
        "run_id": 456,
        "artifact_digest": "sha256:" + "a" * 64,
        "red_commit": "b" * 40,
    }
    packet_record: dict[str, object] = {
        "name": "requirements-evidence",
        "id": 123,
        "expired": False,
        "digest": manifest["artifact_digest"],
        "workflow_run": {"id": 456, "head_sha": manifest["red_commit"]},
    }
    entries = [packet_record]
    mutations: dict[str, tuple[dict[str, object], str, object]] = {
        "expired": (packet_record, "expired", True),
        "digest": (packet_record, "digest", "sha256:" + "c" * 64),
        "head_sha": (cast(dict[str, object], packet_record["workflow_run"]), "head_sha", "d" * 40),
    }
    mutation = mutations.get(defect or "")
    if mutation is not None:
        target, key, value = mutation
        target[key] = value
    if defect == "duplicate":
        entries.append(copy.deepcopy(packet_record))
    if defect is None:
        owner._validate_artifact({"artifacts": entries}, manifest)
    else:
        with pytest.raises(ValueError):
            owner._validate_artifact({"artifacts": entries}, manifest)


@pytest.mark.parametrize(
    "mutation",
    [
        ("", "sha", "8ad0a9434ceeac4a910df3c374536d7c909badec"),
        ("", "sha", True),
        ("", "parents", []),
        ("", "parents", [{"sha": "9b5ad1e78430cc0b061cb16de42f73de96f4f312"}]),
        ("", "parents", [{"sha": "22b2fa7bd763b18ada1bfd1a9ea482a624f34cca"}] * 2),
        ("author", "id", 39115308),
        ("author", "id", True),
        ("author", "id", 41898282.0),
        ("author", "login", "djm81"),
        ("author", "type", "User"),
        ("committer", "id", 41898282),
        ("committer", "id", True),
        ("committer", "login", "github-actions[bot]"),
        ("committer", "type", "Bot"),
        ("tree", "sha", "975de5bf33e7621f1606eb344383d690dbdcae8a"),
        ("verification", "verified", False),
        ("verification", "verified", 1),
        ("verification", "reason", "unsigned"),
        ("verification", "signature", ""),
        ("verification", "signature", "unrelated-signature"),
        ("verification", "payload", ""),
        ("verification", "payload", "tree " + "0" * 40),
    ],
)
def test_source_rejects_wrong_signature_subject(
    owner: ModuleType,
    proof_inputs: tuple[dict[str, object], dict[str, object], dict[str, object]],
    mutation: tuple[str, str, object],
) -> None:
    manifest, packet_record, source_commit = proof_inputs
    section, field, value = mutation
    if section in {"tree", "verification"}:
        commit = cast(dict[str, object], source_commit["commit"])
        target = cast(dict[str, object], commit[section])
    else:
        target = cast(dict[str, object], source_commit[section]) if section else source_commit
    target[field] = value
    with pytest.raises(ValueError):
        owner._validate_artifact({"artifacts": [packet_record], "source_commit": source_commit}, manifest)


@pytest.mark.parametrize("source_commit", [None, True, [], {}])
def test_source_record_is_required_for_fixed_artifact(
    owner: ModuleType,
    proof_inputs: tuple[dict[str, object], dict[str, object], dict[str, object]],
    source_commit: object,
) -> None:
    manifest, packet_record, _ = proof_inputs
    with pytest.raises(ValueError):
        owner._validate_artifact({"artifacts": [packet_record], "source_commit": source_commit}, manifest)

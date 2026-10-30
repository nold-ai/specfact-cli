from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "tests/unit/scripts/fixtures"
CYCLE = "9b5ad1e78430cc0b061cb16de42f73de96f4f312"
SOURCE = "22b2fa7bd763b18ada1bfd1a9ea482a624f34cca"
VALIDATOR_SHA256 = "5bad94f58f6741cd070e6e9f98a95c88d412365a437e0499e30545603cd9f846"


@pytest.fixture
def owner() -> Iterator[ModuleType]:
    spec = importlib.util.spec_from_file_location(
        "_fixed786_copy_owner", REPO_ROOT / "scripts/requirements_late_red_proof.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
        yield module
    finally:
        sys.modules.pop(spec.name, None)


@pytest.fixture
def inputs(tmp_path: Path) -> argparse.Namespace:
    assert not tmp_path.resolve().is_relative_to(REPO_ROOT.resolve())
    final = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD^{commit}"],
        cwd=REPO_ROOT,
        capture_output=True,
        check=True,
        text=True,
        timeout=30,
    ).stdout.strip()
    assert final != SOURCE
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", SOURCE, final],
        cwd=REPO_ROOT,
        capture_output=True,
        check=True,
        timeout=30,
    )
    trusted = subprocess.run(
        ["git", "show", f"{CYCLE}:scripts/requirements_proof_provenance.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        check=True,
        timeout=30,
    ).stdout
    assert hashlib.sha256(trusted).hexdigest() == VALIDATOR_SHA256
    provenance = tmp_path / "requirements_proof_provenance.py"
    provenance.write_bytes(trusted)
    packet = tmp_path / "packet"
    packet.mkdir()
    metadata = json.loads((FIXTURES / "fixed786-native-packet/fixture-metadata.json").read_bytes())
    for alias, record in metadata["files"].items():
        payload = (FIXTURES / "fixed786-native-packet" / record["source"]).read_bytes()
        assert len(payload) == record["bytes"]
        assert hashlib.sha256(payload).hexdigest() == record["sha256"]
        (packet / alias).write_bytes(payload)
    manifest = tmp_path / "manifest.json"
    manifest.write_bytes((FIXTURES / "fixed786_artifact_source/manifest.json").read_bytes())
    api = FIXTURES / "fixed786_artifact_source"
    artifacts = tmp_path / "artifacts.json"
    artifacts.write_text(
        json.dumps(
            {
                "artifacts": [json.loads((api / "artifact-live-api.json").read_bytes())],
                "source_commit": json.loads((api / "source-R2-filtered-api.json").read_bytes()),
            }
        ),
        encoding="utf-8",
    )
    event = tmp_path / "derived-unit-event.json"
    event.write_text(
        json.dumps(
            {
                "number": 786,
                "repository": {"full_name": "nold-ai/specfact-cli"},
                "pull_request": {
                    "base": {"ref": "dev", "repo": {"full_name": "nold-ai/specfact-cli"}},
                    "head": {
                        "ref": "codex/security-dependencies-0-55-11-dev",
                        "sha": final,
                        "repo": {"full_name": "nold-ai/specfact-cli"},
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    return argparse.Namespace(
        repo_root=REPO_ROOT,
        manifest=manifest,
        event=event,
        red_run=REPO_ROOT / "tests/fixtures/requirements-proof/pr786-native34-run.json",
        red_artifacts=artifacts,
        red_artifact_root=packet,
        cycle_base_ref=CYCLE,
        final_ref=final,
        trusted_provenance=provenance,
        output=tmp_path / "output/canonical.json",
    )


def test_public_fixed_scope_stays_closed(owner: ModuleType) -> None:
    manifest = REPO_ROOT / (
        "openspec/changes/security-dependencies-0-55-11-dev/requirements-proof/late-red-evidence.json"
    )
    with pytest.raises(ValueError):
        owner._proof_scope(manifest, REPO_ROOT)


def test_private_formatter_preserves_canonical_bytes(
    owner: ModuleType,
    inputs: argparse.Namespace,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    before = {path.name: path.read_bytes() for path in inputs.red_artifact_root.iterdir()}
    metadata_before = {
        path: path.read_bytes()
        for path in (inputs.manifest, inputs.event, inputs.red_run, inputs.red_artifacts, inputs.trusted_provenance)
    }
    manifest = json.loads(inputs.manifest.read_bytes())
    assert owner._validate_raw_artifact(inputs.red_artifact_root, manifest, owner._FIXED_PR786_SCOPE) == (
        before["requirements-proof.xml"],
        manifest["failed_selectors"],
    )
    original = inputs.output.parent.parent / "original.json"
    original.write_bytes(before["requirements-evidence.json"])
    original.with_suffix(".xml").write_bytes(before["requirements-proof.xml"])
    _, validate = owner._load_provenance(inputs.trusted_provenance, REPO_ROOT, CYCLE)
    assert validate(original, REPO_ROOT, base_ref=CYCLE, final_ref=inputs.final_ref) == []
    monkeypatch.setattr(owner, "_proof_scope", lambda *_: owner._FIXED_PR786_SCOPE)
    assert owner._normalize(inputs) is None
    assert inputs.output.read_bytes() == before["requirements-evidence.json"]
    assert inputs.output.with_suffix(".xml").read_bytes() == before["requirements-proof.xml"]
    assert validate(inputs.output, REPO_ROOT, base_ref=CYCLE, final_ref=inputs.final_ref) == []
    assert original.read_bytes() == before["requirements-evidence.json"]
    assert original.with_suffix(".xml").read_bytes() == before["requirements-proof.xml"]
    assert {path.name: path.read_bytes() for path in inputs.red_artifact_root.iterdir()} == before
    assert {path: path.read_bytes() for path in metadata_before} == metadata_before


@pytest.mark.parametrize("member", ["requirements-evidence.json", "requirements-proof.xml"])
def test_private_formatter_refuses_modified_packet_without_output(
    owner: ModuleType,
    inputs: argparse.Namespace,
    monkeypatch: pytest.MonkeyPatch,
    member: str,
) -> None:
    target = inputs.red_artifact_root / member
    altered = target.read_bytes() + b"\n"
    target.write_bytes(altered)
    monkeypatch.setattr(owner, "_proof_scope", lambda *_: owner._FIXED_PR786_SCOPE)
    with pytest.raises(ValueError):
        owner._normalize(inputs)
    assert not inputs.output.exists()
    assert not inputs.output.with_suffix(".xml").exists()
    assert target.read_bytes() == altered


def test_private_formatter_rejects_repository_output(
    owner: ModuleType,
    inputs: argparse.Namespace,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs.output = REPO_ROOT / ".fixed786-must-not-write.json"
    assert not inputs.output.exists() and not inputs.output.with_suffix(".xml").exists()
    monkeypatch.setattr(owner, "_proof_scope", lambda *_: owner._FIXED_PR786_SCOPE)
    with pytest.raises(ValueError):
        owner._normalize(inputs)
    assert not inputs.output.exists() and not inputs.output.with_suffix(".xml").exists()


def test_fixed_scope_accepts_actual_history(owner: ModuleType) -> None:
    manifest = json.loads((FIXTURES / "fixed786_artifact_source/manifest.json").read_bytes())
    failure: ValueError | None = None
    try:
        owner._validate_history(REPO_ROOT, manifest, CYCLE, "HEAD", owner._FIXED_PR786_SCOPE)
    except ValueError as error:
        failure = error
    assert failure is None, "Authenticated fixed PR786 source history must be accepted"


@pytest.mark.parametrize(
    "path",
    [
        "scripts/requirements_late_red_proof.py",
        "pyproject.toml",
        "openspec/CHANGE_ORDER.md.bak",
        "openspec/CHANGE_ORDER.md/child",
        "openspec/../openspec/CHANGE_ORDER.md",
        "/openspec/CHANGE_ORDER.md",
        "openspec/change_order.md",
    ],
)
def test_fixed_history_rejects_unapproved_paths(
    owner: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    path: str,
) -> None:
    monkeypatch.setattr(owner, "_changed_paths", lambda *_: [path])
    with pytest.raises(ValueError):
        owner._validate_linear_red_segment(REPO_ROOT, CYCLE, SOURCE, owner._FIXED_PR786_SCOPE)


@pytest.mark.parametrize("scope_index", [0, 1, 2])
def test_historical_scopes_reject_change_order(
    owner: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    scope_index: int,
) -> None:
    monkeypatch.setattr(owner, "_changed_paths", lambda *_: ["openspec/CHANGE_ORDER.md"])
    with pytest.raises(ValueError):
        owner._validate_linear_red_segment(REPO_ROOT, CYCLE, SOURCE, owner._PROOF_SCOPES[scope_index])

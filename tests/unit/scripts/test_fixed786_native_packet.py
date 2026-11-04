from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
import xml.etree.ElementTree as ET
from collections.abc import Callable, Iterator
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


FIXTURES = Path(__file__).parent / "fixtures/fixed786-native-packet"
METADATA = FIXTURES / "fixture-metadata.json"
REPO_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def owner() -> Iterator[ModuleType]:
    path = REPO_ROOT / "scripts/requirements_late_red_proof.py"
    spec = importlib.util.spec_from_file_location("_fixed786_packet_owner", path)
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
def metadata() -> dict[str, Any]:
    return json.loads(METADATA.read_bytes())


@pytest.fixture
def manifest(metadata: dict[str, Any]) -> dict[str, Any]:
    return copy.deepcopy(metadata["manifest"])


@pytest.fixture
def scope(owner: ModuleType) -> Any:
    return owner._ProofScope(
        "security-dependencies-0-55-11-dev", 786, "codex/security-dependencies-0-55-11-dev", "red", "red"
    )


@pytest.fixture
def packet(tmp_path: Path, metadata: dict[str, Any]) -> Path:
    source = FIXTURES / metadata["fixture_root"]
    for alias, expected in metadata["files"].items():
        payload = (source / expected["source"]).read_bytes()
        if len(payload) != expected["bytes"] or hashlib.sha256(payload).hexdigest() != expected["sha256"]:
            raise RuntimeError(f"Authenticated fixture changed: {expected['source']}")
        (tmp_path / alias).write_bytes(payload)
    return tmp_path


def test_actual_canonical_red_packet_is_accepted_unchanged(
    owner: ModuleType, scope: Any, packet: Path, manifest: dict[str, Any]
) -> None:
    before = {path.name: path.read_bytes() for path in packet.iterdir()}
    accepted = True
    result = None
    try:
        result = owner._validate_raw_artifact(packet, manifest, scope)
    except ValueError:
        accepted = False
    assert accepted, "Existing owner refuses the actual canonical RED packet format"
    assert result == (before["requirements-proof.xml"], manifest["failed_selectors"])
    assert {path.name: path.read_bytes() for path in packet.iterdir()} == before


def test_fixed_manifest_accepts_exact_packet_without_claiming_authority(
    owner: ModuleType, scope: Any, manifest: dict[str, Any]
) -> None:
    accepted = True
    try:
        owner._validate_manifest(manifest, scope)
    except ValueError:
        accepted = False
    assert accepted, "Existing manifest boundary refuses the fixed PR786 packet schema"


@pytest.mark.parametrize(
    "field,value",
    [
        ("issue", 692),
        ("pull_request", 717),
        ("red_commit", "7b6b5fc1af7b57c2eb5a3546b7578a81175e4dfa"),
        ("artifact_id", 12988824885),
        ("artifact_repository", "nold-ai/specfact-cli"),
        ("origin_repository", "nold-ai/.github"),
        ("run_attempt", True),
        ("mapping_digest", "sha256:61afa8becd7fed3cbe92a273c955c2e8ba389583f62f0e519c97cafafa7d4307"),
        ("unexpected_authority", "approved"),
    ],
)
def test_fixed_manifest_rejects_wrong_binding(
    owner: ModuleType, scope: Any, manifest: dict[str, Any], field: str, value: object
) -> None:
    manifest[field] = value
    with pytest.raises(ValueError):
        owner._validate_manifest(manifest, scope)


@pytest.mark.parametrize(
    "filename",
    [
        "requirements-evidence.json",
        "requirements-evidence-plan.json",
        "requirements-proof.xml",
        "plan.json",
    ],
)
def test_payload_mutation_without_matching_digest_is_rejected(
    owner: ModuleType, scope: Any, packet: Path, manifest: dict[str, Any], filename: str
) -> None:
    path = packet / filename
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ValueError):
        owner._validate_raw_artifact(packet, manifest, scope)


def _error_outcome(_document: ET.Element, _first: ET.Element, failure: ET.Element) -> None:
    failure.tag = "error"


def _skip_outcome(_document: ET.Element, first: ET.Element, failure: ET.Element) -> None:
    first.remove(failure)
    ET.SubElement(first, "skipped")


def _all_pass_outcome(document: ET.Element, _first: ET.Element, _failure: ET.Element) -> None:
    for case in document.findall(".//testcase"):
        for node in list(case):
            if node.tag in {"failure", "error", "skipped"}:
                case.remove(node)


def _wrong_selector(_document: ET.Element, first: ET.Element, _failure: ET.Element) -> None:
    selector = first.find("properties/property[@name='specfact.selector']")
    if selector is None:
        raise RuntimeError("Authenticated fixture lacks selector property")
    selector.set("value", "tests/test_unrelated.py::test_unrelated")


def _wrong_assertion(_document: ET.Element, _first: ET.Element, failure: ET.Element) -> None:
    failure.set("message", "AssertionError: unrelated assertion")
    failure.text = "AssertionError: unrelated assertion"


@pytest.mark.parametrize(
    "mutate",
    [
        pytest.param(_error_outcome, id="error"),
        pytest.param(_skip_outcome, id="skip"),
        pytest.param(_all_pass_outcome, id="all-pass"),
        pytest.param(_wrong_selector, id="wrong-selector"),
        pytest.param(_wrong_assertion, id="wrong-assertion"),
    ],
)
def test_native_contract_fault_is_rejected_even_with_local_digest_updates(
    owner: ModuleType,
    scope: Any,
    packet: Path,
    manifest: dict[str, Any],
    mutate: Callable[[ET.Element, ET.Element, ET.Element], None],
) -> None:
    path = packet / "requirements-proof.xml"
    document = ET.fromstring(path.read_bytes())
    cases = document.findall(".//testcase")
    first = cases[0]
    failure = first.find("failure")
    if failure is None:
        raise RuntimeError("Authenticated fixture lacks its expected assertion failure")
    mutate(document, first, failure)
    payload = ET.tostring(document, encoding="utf-8")
    path.write_bytes(payload)
    manifest["junit_digest"] = "sha256:" + hashlib.sha256(payload).hexdigest()
    report_path = packet / "requirements-evidence.json"
    report = json.loads(report_path.read_bytes())
    report["execution_proof"]["junit_digest"] = manifest["junit_digest"]
    report_payload = (json.dumps(report, sort_keys=True) + "\n").encode()
    report_path.write_bytes(report_payload)
    manifest["report_digest"] = "sha256:" + hashlib.sha256(report_payload).hexdigest()
    with pytest.raises(ValueError):
        owner._validate_raw_artifact(packet, manifest, scope)


def test_fixed_public_route_stays_closed_until_full_authentication(owner: ModuleType) -> None:
    repo = REPO_ROOT.resolve()
    manifest_path = repo / (
        "openspec/changes/security-dependencies-0-55-11-dev/requirements-proof/late-red-evidence.json"
    )
    with pytest.raises(ValueError):
        owner._proof_scope(manifest_path, repo)

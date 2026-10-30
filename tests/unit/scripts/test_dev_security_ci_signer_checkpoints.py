"""Synthetic API evidence only; run alongside the unchanged existing signer tests."""

from __future__ import annotations

import base64
import copy
import hashlib
import json
import os
import subprocess
import sys
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pytest

from scripts import dev_security_ci_signer as signer
from tests.unit.scripts import test_dev_security_ci_signer as old


ROOT = "22b2fa7bd763b18ada1bfd1a9ea482a624f34cca"
SECOND_SOURCE, SECOND_TREE, SECOND_OUTPUT = (character * 40 for character in "789")
PREFIX = "tests/unit/scripts/fixtures/fixed786-native-packet/"
MESSAGES = (
    "TEST: preserve the reviewed checkpoint\n\nRegression before implementation.",
    "CODE: complete the reviewed correction\n\nPreserve this complete message.\n",
)


class FiniteGitHub(old.GitHub):
    def __init__(self) -> None:
        super().__init__()
        fixture = Path(__file__).parent / "fixtures/fixed786-native-packet"
        self.packet = {path.name: path.read_bytes() for path in fixture.iterdir()}
        self.outputs: dict[str, dict[str, Any]] = {}
        self.records[f"{old.REPO}/pulls/786"]["head"]["sha"] = ROOT
        self.records[f"{old.REPO}/git/commits/{old.SOURCE}"].update(parents=[{"sha": ROOT}], message=MESSAGES[0])
        self.records[f"{old.REPO}/git/commits/{SECOND_SOURCE}"] = {
            "sha": SECOND_SOURCE,
            "tree": {"sha": SECOND_TREE},
            "parents": [{"sha": old.SOURCE}],
            "message": MESSAGES[1],
        }
        fixture_delta = copy.deepcopy(self.intent["checkpoints"][0]["delta"][1:])
        second_tree = copy.deepcopy(self.records[f"{old.REPO}/git/trees/{old.TREE}?recursive=1"])
        second_tree["sha"] = SECOND_TREE
        second_tree["tree"][0]["sha"] = "3" * 40
        self.records[f"{old.REPO}/git/trees/{SECOND_TREE}?recursive=1"] = second_tree
        self.intent = {
            key: self.intent[key]
            for key in (
                "repository_id",
                "repository_full_name",
                "actor",
                "triggering_actor",
                "dev",
                "main",
                "auxiliary_ref",
                "destination",
            )
        }
        self.intent["checkpoints"] = [
            {
                "source_commit": source,
                "source_parent": parent,
                "source_tree": tree,
                "source_message": message,
                "delta": [
                    {"path": old.PATH, "before": ["100644", old.OLD], "after": ["100644", blob]},
                    *copy.deepcopy(fixture_delta),
                ],
            }
            for source, parent, tree, message, blob in (
                (old.SOURCE, ROOT, old.TREE, MESSAGES[0], old.NEW),
                (SECOND_SOURCE, old.SOURCE, SECOND_TREE, MESSAGES[1], "3" * 40),
            )
        ]

    def _create_commit(self, body: dict[str, Any] | None) -> signer._Response:
        super()._create_commit(body)
        assert self.created is not None
        sha = old.CREATED if not self.outputs else SECOND_OUTPUT
        self.created["sha"] = sha
        self.outputs[sha] = copy.deepcopy(self.created)
        return signer._Response(201, json.dumps(self.created).encode())

    def _create_ref(self, body: dict[str, Any] | None) -> signer._Response:
        assert body == {"ref": old.DEST, "sha": SECOND_OUTPUT}
        self.destination = SECOND_OUTPUT
        return signer._Response(201, json.dumps(self.ref(old.DEST, SECOND_OUTPUT)).encode())

    def _read(self, path: str) -> signer._Response:
        for sha, record in self.outputs.items():
            if path == f"{old.REPO}/git/commits/{sha}":
                return signer._Response(200, json.dumps(record).encode())
            if path == f"{old.REPO}/commits/{sha}":
                return signer._Response(
                    200,
                    json.dumps(
                        {
                            "sha": sha,
                            "author": {"id": 41898282, "login": "github-actions[bot]", "type": "Bot"},
                            "committer": {"id": 19864447, "login": "web-flow", "type": "User"},
                        }
                    ).encode(),
                )
        return super()._read(path)


@dataclass(frozen=True)
class FiniteCase:
    api: FiniteGitHub
    intent_file: Path
    context: signer.RunContext

    def prepare(self) -> signer.DispatchExpectation:
        raw = json.dumps(self.api.intent).encode()
        self.intent_file.write_bytes(raw)
        return signer.DispatchExpectation(old.EXECUTOR, hashlib.sha256(raw).hexdigest())

    def publish(self) -> signer.Outcome:
        return signer.publish_once(self.intent_file, self.prepare(), self.context)


@pytest.fixture
def finite(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> FiniteCase:
    api = FiniteGitHub()
    context = signer.RunContext(
        old.EXECUTOR,
        789,
        1,
        123,
        "nold-ai/specfact-cli",
        456,
        "owner",
        456,
        "owner",
        "workflow_dispatch",
        old.AUX,
        204352514,
        ".github/workflows/specfact.yml",
    )
    monkeypatch.setattr(signer, "_request", api.request)
    return FiniteCase(api, tmp_path / "intent.json", context)


def test_all_checkpoint_trees_messages_and_service_parents_survive(finite: FiniteCase) -> None:
    receipt = finite.publish()
    assert receipt.status == "published", receipt.reason
    digest = hashlib.sha256(finite.intent_file.read_bytes()).hexdigest()
    expected: list[tuple[str, str, dict[str, Any] | None]] = []
    for source, tree, parent, message in (
        (old.SOURCE, old.TREE, ROOT, MESSAGES[0]),
        (SECOND_SOURCE, SECOND_TREE, old.CREATED, MESSAGES[1]),
    ):
        signed_message = (
            f"{message}\n\nSource-Commit: {source}\nIntent: {digest}\nExecutor: {old.EXECUTOR}\nRun: 789\nAttempt: 1"
        )
        expected.append(
            (
                "POST",
                f"{old.REPO}/git/commits",
                {
                    "tree": tree,
                    "parents": [parent],
                    "message": signed_message,
                },
            )
        )
    assert finite.api.writes == [
        *expected,
        (
            "POST",
            f"{old.REPO}/git/refs",
            {
                "ref": old.DEST,
                "sha": SECOND_OUTPUT,
            },
        ),
    ]
    assert receipt.commit_sha == receipt.ref_sha == SECOND_OUTPUT
    first_post = next(i for i, event in enumerate(finite.api.trace) if event[0] == "POST")
    for source in (old.SOURCE, SECOND_SOURCE):
        assert ("GET", f"{old.REPO}/git/commits/{source}", None) in finite.api.trace[:first_post]
    for sha in (old.CREATED, SECOND_OUTPUT):
        assert ("GET", f"{old.REPO}/git/commits/{sha}", None) in finite.api.trace
        assert ("GET", f"{old.REPO}/commits/{sha}", None) in finite.api.trace


_CHECKPOINT_MUTATIONS: list[tuple[str, Callable[[FiniteGitHub], object]]] = [
    ("gap", lambda api: api.records[f"{old.REPO}/git/commits/{SECOND_SOURCE}"].update(parents=[{"sha": ROOT}])),
    ("omission", lambda api: api.intent["checkpoints"].pop(0)),
    ("reorder", lambda api: api.intent["checkpoints"].reverse()),
    ("tree", lambda api: api.records[f"{old.REPO}/git/commits/{SECOND_SOURCE}"]["tree"].update(sha=old.TREE)),
    ("delta", lambda api: api.intent["checkpoints"][1]["delta"].pop()),
    (
        "message",
        lambda api: api.records[f"{old.REPO}/git/commits/{SECOND_SOURCE}"].update(
            message=MESSAGES[1] + "Unreviewed change"
        ),
    ),
    ("merge", lambda api: api.records[f"{old.REPO}/git/commits/{SECOND_SOURCE}"]["parents"].append({"sha": ROOT})),
    ("truncated", lambda api: api.records[f"{old.REPO}/git/trees/{SECOND_TREE}?recursive=1"].update(truncated=True)),
]


@pytest.mark.parametrize("mutate", [pytest.param(mutate, id=label) for label, mutate in _CHECKPOINT_MUTATIONS])
def test_bad_late_checkpoint_refuses_before_first_post(
    finite: FiniteCase, mutate: Callable[[FiniteGitHub], object]
) -> None:
    mutate(finite.api)
    assert finite.publish().status == "refused"
    assert finite.api.writes == []


@pytest.mark.parametrize("label", ["Source-Commit", "Intent", "Executor", "Run", "Attempt"])
def test_source_cannot_supply_reserved_signer_suffix(finite: FiniteCase, label: str) -> None:
    message = MESSAGES[1] + f"\n{label}: forged"
    finite.api.intent["checkpoints"][1]["source_message"] = message
    finite.api.records[f"{old.REPO}/git/commits/{SECOND_SOURCE}"]["message"] = message
    assert finite.publish().status == "refused"
    assert finite.api.writes == []


def test_second_commit_uncertainty_retains_confirmed_prefix(finite: FiniteCase) -> None:
    def lose_response(
        method: str, path: str, body: dict[str, Any] | None, response: signer._Response
    ) -> signer._Response:
        if method == "POST" and path.endswith("/git/commits") and len(finite.api.outputs) == 2:
            raise TimeoutError("Second service response lost")
        return response

    finite.api.edit = lose_response
    receipt = finite.publish()
    assert receipt.status == "uncertain_commit", receipt.reason
    assert len(finite.api.writes) == 2
    assert finite.api.destination is None
    prefix = asdict(receipt).get("signed_checkpoints")
    assert isinstance(prefix, (list, tuple)) and len(prefix) == 1
    assert prefix[0]["source_commit"] == old.SOURCE
    assert prefix[0]["commit_sha"] == old.CREATED
    assert prefix[0]["signature"] == "synthetic-signature"
    assert prefix[0]["payload"] == finite.api.outputs[old.CREATED]["verification"]["payload"]


def run_cli(finite: FiniteCase, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[int, Path]:
    expected = finite.prepare()
    output = tmp_path / "evidence"
    monkeypatch.setattr(signer, "_environment_context", lambda: finite.context)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "signer",
            "--intent",
            str(finite.intent_file),
            "--expected-executor",
            old.EXECUTOR,
            "--expected-intent",
            expected.intent_sha256,
            "--output",
            str(output),
        ],
    )

    def forbidden(*args: object, **kwargs: object) -> None:
        pytest.fail("Signer must not execute candidate source or subprocesses")

    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(os, "system", forbidden)
    monkeypatch.chdir(tmp_path)
    poison = tmp_path / PREFIX
    poison.mkdir(parents=True)
    for name in finite.api.packet:
        (poison / name).write_bytes(b"LOCAL SOURCE MUST NOT BE COPIED OR EXECUTED")
    return signer._main(), output


def test_cli_copies_exact_four_authenticated_api_blobs_inertly(
    finite: FiniteCase,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    status, output = run_cli(finite, tmp_path, monkeypatch)
    assert status == 0, (output / "receipt.json").read_text()
    members = output / "copy-members"
    assert members.is_dir(), "Existing --output must own the separate four-member COPY directory"
    metadata = json.loads(finite.api.packet["fixture-metadata.json"])
    assert {path.name for path in members.iterdir()} == set(metadata["files"])
    for name, entry in metadata["files"].items():
        member = members / name
        assert member.is_file() and not member.is_symlink()
        assert member.read_bytes() == finite.api.packet[entry["source"]]
        assert member.stat().st_size == entry["bytes"]
        assert hashlib.sha256(member.read_bytes()).hexdigest() == entry["sha256"]


_PACKET_MUTATIONS: list[tuple[str, str, Callable[[dict[str, Any], dict[str, Any], dict[str, Any]], object]]] = [
    ("content", "plan.json", lambda blob, entry, delta: blob.update(content=base64.b64encode(b"corrupt").decode())),
    ("size", "plan.json", lambda blob, entry, delta: blob.update(size=blob["size"] + 1)),
    ("sha", "plan.json", lambda blob, entry, delta: blob.update(sha="0" * 40)),
    ("encoding", "plan.json", lambda blob, entry, delta: blob.update(encoding="utf-8")),
    (
        "mode",
        "plan.json",
        lambda blob, entry, delta: (entry.update(mode="120000"), delta["after"].__setitem__(0, "120000")),
    ),
    (
        "metadata",
        "fixture-metadata.json",
        lambda blob, entry, delta: blob.update(content=base64.b64encode(b"corrupt").decode()),
    ),
]


@pytest.mark.parametrize(
    ("name", "mutate"), [pytest.param(name, mutate, id=label) for label, name, mutate in _PACKET_MUTATIONS]
)
def test_corrupt_packet_refuses_before_any_post_or_copy(
    finite: FiniteCase,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    mutate: Callable[[dict[str, Any], dict[str, Any], dict[str, Any]], object],
) -> None:
    tree = finite.api.records[f"{old.REPO}/git/trees/{SECOND_TREE}?recursive=1"]["tree"]
    entry = next(item for item in tree if item["path"] == PREFIX + name)
    blob = finite.api.records[f"{old.REPO}/git/blobs/{entry['sha']}"]
    delta = next(item for item in finite.api.intent["checkpoints"][1]["delta"] if item["path"] == PREFIX + name)
    mutate(blob, entry, delta)
    status, output = run_cli(finite, tmp_path, monkeypatch)
    assert status == 1
    assert json.loads((output / "receipt.json").read_text())["status"] == "refused"
    assert finite.api.writes == []
    members = output / "copy-members"
    assert not members.exists() or list(members.iterdir()) == []


@pytest.mark.parametrize("fault", ["signature", "attribution"])
def test_second_invalid_service_object_never_publishes_ref(finite: FiniteCase, fault: str) -> None:
    def corrupt(method: str, path: str, body: dict[str, Any] | None, response: signer._Response) -> signer._Response:
        if len(finite.api.outputs) != 2:
            return response
        record = json.loads(response.body)
        if fault == "signature" and method == "POST" and path.endswith("/git/commits"):
            record["verification"]["verified"] = False
        if fault == "attribution" and path == f"{old.REPO}/commits/{SECOND_OUTPUT}":
            record["committer"]["id"] = 999
        return signer._Response(response.status, json.dumps(record).encode())

    finite.api.edit = corrupt
    receipt = finite.publish()
    assert receipt.status == "object_only", receipt.reason
    assert receipt.commit_sha == SECOND_OUTPUT
    assert len(finite.api.writes) == 2
    assert finite.api.destination is None
    prefix = asdict(receipt).get("signed_checkpoints")
    assert isinstance(prefix, (list, tuple)) and len(prefix) == 1
    assert prefix[0]["commit_sha"] == old.CREATED


@pytest.mark.parametrize("count", [0, 33])
def test_checkpoint_count_is_nonempty_and_bounded(finite: FiniteCase, count: int) -> None:
    checkpoint = finite.api.intent["checkpoints"][0]
    finite.api.intent["checkpoints"] = [copy.deepcopy(checkpoint) for _ in range(count)]
    assert finite.publish().status == "refused"
    assert finite.api.writes == []

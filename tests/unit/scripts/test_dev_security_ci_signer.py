from __future__ import annotations

import copy
import hashlib
import json
import sys
from collections.abc import Callable
from dataclasses import dataclass, replace
from http.client import BadStatusLine, HTTPException, IncompleteRead
from pathlib import Path
from typing import Any, Protocol

import pytest

from scripts import dev_security_ci_signer as signer


REPO = "/repos/nold-ai/specfact-cli"
PARENT = "4ae6175a4d337296d0347e73b66c9da1f0e43f7f"
DEV = "9b5ad1e78430cc0b061cb16de42f73de96f4f312"
MAIN, SOURCE, TREE, BASE_TREE, EXECUTOR, CREATED = (letter * 40 for letter in "abcdef")
OLD, NEW = "1" * 40, "2" * 40
DEST = "refs/heads/codex/security-dev-refreshed-test-prefix-20261029"
AUX = "refs/heads/codex/security-dev-ci-test-refresh-20261029"
PATH = "openspec/changes/security-dependencies-0-55-11-dev/tasks.md"
AUTHOR = {"name": "github-actions[bot]", "email": "41898282+github-actions[bot]@users.noreply.github.com"}
COMMITTER = {"name": "GitHub", "email": "noreply@github.com"}


class GitHub:
    def __init__(self) -> None:
        self.intent: dict[str, Any] = {
            "repository_id": 123,
            "repository_full_name": "nold-ai/specfact-cli",
            "actor": {"id": 456, "login": "owner"},
            "triggering_actor": {"id": 456, "login": "owner"},
            "dev": DEV,
            "main": MAIN,
            "source_commit": SOURCE,
            "source_tree": TREE,
            "delta": [{"path": PATH, "before": ["100644", OLD], "after": ["100644", NEW]}],
            "auxiliary_ref": AUX,
            "destination": DEST,
            "message_stem": "Dev security reviewed snapshot",
        }
        self.run: dict[str, Any] = {
            "id": 789,
            "run_attempt": 1,
            "head_sha": EXECUTOR,
            "head_branch": AUX.removeprefix("refs/heads/"),
            "event": "workflow_dispatch",
            "path": ".github/workflows/specfact.yml",
            "workflow_id": 204352514,
            "status": "in_progress",
            "repository": {"id": 123, "full_name": "nold-ai/specfact-cli"},
            "actor": {"id": 456, "login": "owner"},
            "triggering_actor": {"id": 456, "login": "owner"},
        }
        self.records: dict[str, dict[str, Any]] = {
            REPO: {"id": 123, "full_name": "nold-ai/specfact-cli"},
            f"{REPO}/pulls/786": {
                "number": 786,
                "state": "open",
                "draft": False,
                "auto_merge": None,
                "head": {
                    "sha": PARENT,
                    "ref": "codex/security-dependencies-0-55-11-dev",
                    "repo": {"id": 123, "full_name": "nold-ai/specfact-cli"},
                },
                "base": {"sha": DEV, "ref": "dev", "repo": {"id": 123, "full_name": "nold-ai/specfact-cli"}},
            },
            f"{REPO}/actions/runs/789": self.run,
            f"{REPO}/actions/workflows/204352514/runs?event=workflow_dispatch&per_page=100": {
                "total_count": 1,
                "workflow_runs": [self.run],
            },
            f"{REPO}/git/commits/{SOURCE}": {"sha": SOURCE, "tree": {"sha": TREE}, "parents": [{"sha": PARENT}]},
            f"{REPO}/git/commits/{DEV}": {"sha": DEV, "tree": {"sha": BASE_TREE}},
            f"{REPO}/git/trees/{BASE_TREE}?recursive=1": self.tree(BASE_TREE, OLD),
            f"{REPO}/git/trees/{TREE}?recursive=1": self.tree(TREE, NEW),
        }
        for ref, sha in (("refs/heads/dev", DEV), ("refs/heads/main", MAIN), (AUX, EXECUTOR)):
            self.records[self.ref_path(ref)] = self.ref(ref, sha)
        self.trace: list[tuple[str, str, dict[str, Any] | None]] = []
        self.created: dict[str, Any] | None = None
        self.destination: str | None = None
        self.edit: Callable[[str, str, dict[str, Any] | None, signer._Response], signer._Response] = (
            lambda method, path, body, response: response
        )
        self.uncertain: str | None = None

    @staticmethod
    def tree(sha: str, blob: str) -> dict[str, Any]:
        return {
            "sha": sha,
            "truncated": False,
            "tree": [
                {"path": PATH, "mode": "100644", "type": "blob", "sha": blob},
            ],
        }

    @staticmethod
    def ref_path(ref: str) -> str:
        return f"{REPO}/git/ref/{ref.removeprefix('refs/')}"

    @staticmethod
    def ref(ref: str, sha: str) -> dict[str, Any]:
        return {"ref": ref, "object": {"type": "commit", "sha": sha}}

    @property
    def writes(self) -> list[tuple[str, str, dict[str, Any] | None]]:
        return [item for item in self.trace if item[0] != "GET"]

    def _create_commit(self, body: dict[str, Any] | None) -> signer._Response:
        assert body is not None
        payload = (
            f"tree {body['tree']}\nparent {body['parents'][0]}\n"
            f"author {AUTHOR['name']} <{AUTHOR['email']}> 1793000000 +0000\n"
            f"committer {COMMITTER['name']} <{COMMITTER['email']}> 1793000001 +0000\n\n{body['message']}"
        )
        self.created = {
            "sha": CREATED,
            "tree": {"sha": body["tree"]},
            "parents": [{"sha": parent} for parent in body["parents"]],
            "message": body["message"],
            "author": AUTHOR.copy(),
            "committer": COMMITTER.copy(),
            "verification": {
                "verified": True,
                "reason": "valid",
                "signature": "synthetic-signature",
                "payload": payload,
            },
        }
        return signer._Response(201, json.dumps(self.created).encode())

    def _create_ref(self, body: dict[str, Any] | None) -> signer._Response:
        assert body == {"ref": DEST, "sha": CREATED}
        self.destination = CREATED
        return signer._Response(201, json.dumps(self.ref(DEST, CREATED)).encode())

    def _read(self, path: str) -> signer._Response:
        if path == self.ref_path(DEST):
            if self.destination is None:
                return signer._Response(404, b'{"message": "Not Found"}')
            return signer._Response(200, json.dumps(self.ref(DEST, self.destination)).encode())
        if path == f"{REPO}/git/commits/{CREATED}":
            assert self.created is not None
            return signer._Response(200, json.dumps(self.created).encode())
        if path == f"{REPO}/commits/{CREATED}":
            return signer._Response(
                200,
                json.dumps(
                    {
                        "sha": CREATED,
                        "author": {"id": 41898282, "login": "github-actions[bot]", "type": "Bot"},
                        "committer": {"id": 19864447, "login": "web-flow", "type": "User"},
                    }
                ).encode(),
            )
        if path in self.records:
            return signer._Response(200, json.dumps(self.records[path]).encode())
        pytest.fail(f"Unexpected transport operation GET {path}")

    def request(self, method: str, path: str, body: dict[str, Any] | None = None) -> signer._Response:
        self.trace.append((method, path, copy.deepcopy(body)))
        posts = {f"{REPO}/git/commits": self._create_commit, f"{REPO}/git/refs": self._create_ref}
        if method == "GET":
            wire = self._read(path)
        elif method == "POST" and path in posts:
            wire = posts[path](body)
        else:
            pytest.fail(f"Unexpected transport operation {method} {path}")
        if method == "POST" and path.endswith(f"/git/{self.uncertain}"):
            raise TimeoutError("Response lost after server accepted the write")
        return self.edit(method, path, body, wire)


class Publish(Protocol):
    def __call__(self, raw: bytes | None = None, **context_changes: object) -> signer.Outcome: ...


@dataclass(frozen=True)
class Case:
    api: GitHub
    publish: Publish


@pytest.fixture
def case(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Case:
    api = GitHub()
    context = signer.RunContext(
        executor_sha=EXECUTOR,
        run_id=789,
        run_attempt=1,
        repository_id=123,
        repository_full_name="nold-ai/specfact-cli",
        actor_id=456,
        actor_login="owner",
        triggering_actor_id=456,
        triggering_actor_login="owner",
        event="workflow_dispatch",
        ref=AUX,
        workflow_id=204352514,
        workflow_path=".github/workflows/specfact.yml",
    )
    monkeypatch.setattr(signer, "_request", api.request)

    def publish(raw: bytes | None = None, **context_changes: object) -> signer.Outcome:
        data = json.dumps(api.intent).encode() if raw is None else raw
        intent_file = tmp_path / "intent.json"
        intent_file.write_bytes(data)
        expected = signer.DispatchExpectation(EXECUTOR, hashlib.sha256(data).hexdigest())
        return signer.publish_once(intent_file, expected, replace(context, **context_changes))

    return Case(api, publish)


def test_exact_two_writes_reuse_tree_and_sole_reviewed_parent(case: Case) -> None:
    api, publish = case.api, case.publish
    receipt = publish()
    digest = hashlib.sha256(json.dumps(api.intent).encode()).hexdigest()
    message = f"Dev security reviewed snapshot\n\nIntent: {digest}\nExecutor: {EXECUTOR}\nRun: 789\nAttempt: 1"
    assert api.writes == [
        ("POST", f"{REPO}/git/commits", {"tree": TREE, "parents": [PARENT], "message": message}),
        ("POST", f"{REPO}/git/refs", {"ref": DEST, "sha": CREATED}),
    ]
    _assert_publication_trace(api)
    _assert_published_receipt(api, receipt, digest)


def _assert_publication_trace(api: GitHub) -> None:
    commit_post = next(i for i, item in enumerate(api.trace) if item[:2] == ("POST", f"{REPO}/git/commits"))
    ref_post = next(i for i, item in enumerate(api.trace) if item[:2] == ("POST", f"{REPO}/git/refs"))
    assert ("GET", f"{REPO}/git/commits/{CREATED}", None) in api.trace[commit_post + 1 : ref_post]
    assert ("GET", f"{REPO}/commits/{CREATED}", None) in api.trace[commit_post + 1 : ref_post]
    _assert_live_guards_in_each_segment(api, commit_post, ref_post)
    for path in (api.ref_path(DEST), f"{REPO}/git/commits/{CREATED}", f"{REPO}/commits/{CREATED}"):
        assert ("GET", path, None) in api.trace[ref_post + 1 :]


def _assert_live_guards_in_each_segment(api: GitHub, commit_post: int, ref_post: int) -> None:
    guards = [
        REPO,
        f"{REPO}/pulls/786",
        f"{REPO}/actions/runs/789",
        f"{REPO}/actions/workflows/204352514/runs?event=workflow_dispatch&per_page=100",
        *(api.ref_path(ref) for ref in ("refs/heads/dev", "refs/heads/main", AUX, DEST)),
    ]
    for segment in (api.trace[:commit_post], api.trace[commit_post + 1 : ref_post], api.trace[ref_post + 1 :]):
        for path in guards:
            assert ("GET", path, None) in segment


def _assert_published_receipt(api: GitHub, receipt: signer.Outcome, digest: str) -> None:
    assert receipt.status == "published"
    assert (receipt.commit_sha, receipt.ref_sha) == (CREATED, CREATED)
    assert (receipt.intent_sha256, receipt.executor_sha, receipt.run_id, receipt.run_attempt) == (
        digest,
        EXECUTOR,
        789,
        1,
    )
    assert receipt.signature == "synthetic-signature"
    assert api.created is not None
    assert receipt.payload == api.created["verification"]["payload"]


@pytest.mark.parametrize(
    "raw",
    [
        b'{"repository_id":123,"repository_id":123}',
        b"{} trailing",
        b"[]",
    ],
)
def test_malformed_intent_refuses_without_writes(case: Case, raw: bytes) -> None:
    api, publish = case.api, case.publish
    assert publish(raw).status == "refused"
    assert api.writes == []


_INTENT_MUTATIONS: list[Callable[[dict[str, Any]], None]] = [
    lambda d: d.update(unknown=True),
    lambda d: d["actor"].update(unknown=True),
    lambda d: d["delta"][0].update(unknown=True),
    lambda d: d.update(repository_id=True),
    lambda d: d.update(dev="bad-sha"),
    lambda d: d.update(destination="refs/heads/main"),
    lambda d: d["delta"].append(copy.deepcopy(d["delta"][0])),
    lambda d: d["delta"][0].update(path="../escape"),
    lambda d: d["delta"][0].update(path="src/specfact_cli/unsafe.py"),
    lambda d: d["delta"][0].update(path=".github/workflows/specfact.yml"),
    lambda d: d["delta"][0].update(after=["120000", NEW]),
    lambda d: d["delta"][0].update(after=["160000", NEW]),
    lambda d: d["delta"][0].update(after=["100755", NEW]),
]


@pytest.mark.parametrize("mutation", _INTENT_MUTATIONS)
def test_strict_frozen_intent(case: Case, mutation: Callable[[dict[str, Any]], None]) -> None:
    api, publish = case.api, case.publish
    mutation(api.intent)
    assert publish().status == "refused"
    assert api.writes == []


@pytest.mark.parametrize("field", ["actor", "delta"])
def test_nested_duplicate_json_keys_refuse(case: Case, field: str) -> None:
    api, publish = case.api, case.publish
    raw = json.dumps(api.intent)
    raw = (
        raw.replace('"id": 456', '"id": 456, "id": 456', 1)
        if field == "actor"
        else raw.replace('"path":', '"path": "unused", "path":', 1)
    )
    assert publish(raw.encode()).status == "refused"
    assert api.writes == []


@pytest.mark.parametrize(
    "part", ["source", "tree_sha", "truncated", "unlisted", "old_blob", "new_blob", "mode", "missing", "type"]
)
def test_source_tree_and_full_delta_must_agree(case: Case, part: str) -> None:
    api, publish = case.api, case.publish
    source = api.records[f"{REPO}/git/commits/{SOURCE}"]
    old = api.records[f"{REPO}/git/trees/{BASE_TREE}?recursive=1"]
    new = api.records[f"{REPO}/git/trees/{TREE}?recursive=1"]
    mutations: dict[str, Callable[[], None]] = {
        "source": lambda: source["tree"].update(sha=MAIN),
        "tree_sha": lambda: new.update(sha=MAIN),
        "truncated": lambda: new.update(truncated=True),
        "unlisted": lambda: new["tree"].append(
            {"path": "tests/extra.py", "mode": "100644", "type": "blob", "sha": NEW}
        ),
        "old_blob": lambda: old["tree"][0].update(sha=NEW),
        "new_blob": lambda: new["tree"][0].update(sha=OLD),
        "mode": lambda: new["tree"][0].update(mode="100755"),
        "missing": lambda: new.update(tree=[]),
        "type": lambda: new["tree"][0].update(type="commit"),
    }
    mutations[part]()
    assert publish().status == "refused"
    assert api.writes == []


@pytest.mark.parametrize(
    "field,value",
    [
        ("id", 790),
        ("run_attempt", 2),
        ("head_sha", MAIN),
        ("event", "push"),
        ("workflow_id", 1),
        ("path", ".github/workflows/other.yml"),
        ("status", "completed"),
        ("actor", {"id": 999, "login": "owner"}),
        ("triggering_actor", {"id": 456, "login": "other"}),
        ("repository", {"id": 999, "full_name": "nold-ai/specfact-cli"}),
    ],
)
def test_live_run_identity_guard(case: Case, field: str, value: Any) -> None:
    api, publish = case.api, case.publish
    api.run[field] = value
    assert publish().status == "refused"
    assert api.writes == []


@pytest.mark.parametrize(
    "guard",
    [
        "repository_id",
        "repository_name",
        "dev",
        "main",
        "aux",
        "ref_type",
        "ref_name",
        "other_dispatch",
        "incomplete_runs",
        "occupied",
    ],
)
def test_live_repository_refs_and_single_dispatch(case: Case, guard: str) -> None:
    api, publish = case.api, case.publish
    runs = api.records[f"{REPO}/actions/workflows/204352514/runs?event=workflow_dispatch&per_page=100"]

    def add_dispatch() -> None:
        runs["workflow_runs"].append({**api.run, "id": 790})
        runs["total_count"] = 2

    mutations: dict[str, Callable[[], None]] = {
        "repository_id": lambda: api.records[REPO].update(id=999),
        "repository_name": lambda: api.records[REPO].update(full_name="other/repo"),
        "dev": lambda: api.records[api.ref_path("refs/heads/dev")]["object"].update(sha=SOURCE),
        "main": lambda: api.records[api.ref_path("refs/heads/main")]["object"].update(sha=SOURCE),
        "aux": lambda: api.records[api.ref_path(AUX)]["object"].update(sha=SOURCE),
        "ref_type": lambda: api.records[api.ref_path(AUX)]["object"].update(type="tag"),
        "ref_name": lambda: api.records[api.ref_path(AUX)].update(ref="refs/heads/other"),
        "other_dispatch": add_dispatch,
        "incomplete_runs": lambda: runs.update(total_count=101),
        "occupied": lambda: setattr(api, "destination", CREATED),
    }
    mutations[guard]()
    assert publish().status == "refused"
    assert api.writes == []


def test_context_and_expected_digest_are_bound(case: Case, tmp_path: Path) -> None:
    api, publish = case.api, case.publish
    assert publish(run_attempt=2).status == "refused"
    path = tmp_path / "mismatch.json"
    path.write_text(json.dumps(api.intent))
    context = signer.RunContext(
        EXECUTOR,
        789,
        1,
        123,
        "nold-ai/specfact-cli",
        456,
        "owner",
        456,
        "owner",
        "workflow_dispatch",
        AUX,
        204352514,
        ".github/workflows/specfact.yml",
    )
    assert signer.publish_once(path, signer.DispatchExpectation(EXECUTOR, "0" * 64), context).status == "refused"
    assert api.writes == []


@pytest.mark.parametrize("status", [403, 500])
def test_only_definite_404_proves_destination_absent(case: Case, status: int) -> None:
    api, publish = case.api, case.publish
    api.edit = lambda method, path, body, response: (
        signer._Response(status, b"{}") if path == api.ref_path(DEST) else response
    )
    assert publish().status == "refused"
    assert api.writes == []


@pytest.mark.parametrize(
    "corruption",
    [
        "unverified",
        "reason",
        "signature",
        "payload",
        "extra_parent",
        "extra_header",
        "signed_roles",
        "timestamp",
        "api_roles",
        "readback",
    ],
)
def test_signature_payload_and_service_roles_gate_ref_creation(case: Case, corruption: str) -> None:
    api, publish = case.api, case.publish

    def edit(method: str, path: str, body: dict[str, Any] | None, response: signer._Response) -> signer._Response:
        if path not in (f"{REPO}/git/commits", f"{REPO}/git/commits/{CREATED}", f"{REPO}/commits/{CREATED}"):
            return response
        record: dict[str, Any] = json.loads(response.body)
        if path == f"{REPO}/commits/{CREATED}":
            if corruption == "api_roles":
                record["author"], record["committer"] = record["committer"], record["author"]
            return signer._Response(response.status, json.dumps(record).encode())
        if "verification" in record:
            _corrupt_verification(record, corruption, method)
        return signer._Response(response.status, json.dumps(record).encode())

    api.edit = edit
    receipt = publish()
    assert receipt.status == "object_only"
    assert receipt.commit_sha == CREATED
    assert [item[1] for item in api.writes] == [f"{REPO}/git/commits"]


def _corrupt_verification(record: dict[str, Any], corruption: str, method: str) -> None:
    verification = record["verification"]
    replacements = {
        "extra_header": ("\n\n", "\nencoding UTF-8\n\n"),
        "signed_roles": ("author github-actions[bot]", "author GitHub"),
        "timestamp": ("1793000000 +0000", "invalid UTC"),
    }
    if corruption in replacements:
        old, new = replacements[corruption]
        verification["payload"] = verification["payload"].replace(old, new, 1)
        return
    mutations: dict[str, Callable[[], None]] = {
        "unverified": lambda: verification.update(verified=False),
        "reason": lambda: verification.update(reason="unknown_key"),
        "signature": lambda: verification.update(signature=""),
        "payload": lambda: verification.update(payload=verification["payload"] + "forged"),
        "extra_parent": lambda: record["parents"].append({"sha": MAIN}),
        "readback": lambda: record.update(sha=MAIN) if method == "GET" else None,
    }
    if corruption in mutations:
        mutations[corruption]()


@pytest.mark.parametrize("endpoint,status", [("commits", "uncertain_commit"), ("refs", "uncertain_ref")])
def test_lost_post_response_never_retries_or_becomes_success(case: Case, endpoint: str, status: str) -> None:
    api, publish = case.api, case.publish
    api.uncertain = endpoint
    receipt = publish()
    assert receipt.status == status
    expected = [f"{REPO}/git/commits"] + ([f"{REPO}/git/refs"] if endpoint == "refs" else [])
    assert [item[1] for item in api.writes] == expected
    assert api.created is not None
    if endpoint == "refs":
        assert receipt.commit_sha == CREATED
        assert api.destination == CREATED


@pytest.mark.parametrize("after,status", [(1, "object_only"), (2, "created_ref_with_drift")])
def test_drift_after_known_creation_is_not_success(case: Case, after: int, status: str) -> None:
    api, publish = case.api, case.publish

    def edit(method: str, path: str, body: dict[str, Any] | None, response: signer._Response) -> signer._Response:
        if method == "GET" and path == api.ref_path("refs/heads/dev") and len(api.writes) >= after:
            return signer._Response(200, json.dumps(api.ref("refs/heads/dev", SOURCE)).encode())
        return response

    api.edit = edit
    receipt = publish()
    assert receipt.status == status
    assert receipt.commit_sha == CREATED
    assert len(api.writes) == after


@pytest.mark.parametrize("change", ["addition", "deletion"])
def test_exact_delta_includes_additions_and_deletions(case: Case, change: str) -> None:
    api, publish = case.api, case.publish
    if change == "addition":
        api.intent["delta"][0]["before"] = None
        api.records[f"{REPO}/git/trees/{BASE_TREE}?recursive=1"]["tree"] = []
    else:
        api.intent["delta"][0]["after"] = None
        api.records[f"{REPO}/git/trees/{TREE}?recursive=1"]["tree"] = []
    assert publish().status == "published"
    assert len(api.writes) == 2


@pytest.mark.parametrize("endpoint,status", [("commits", "uncertain_commit"), ("refs", "uncertain_ref")])
def test_ambiguous_post_http_failure_retains_uncertainty(case: Case, endpoint: str, status: str) -> None:
    api, publish = case.api, case.publish
    api.edit = lambda method, path, body, response: (
        signer._Response(502, b'{"message":"upstream response lost"}')
        if method == "POST" and path == f"{REPO}/git/{endpoint}"
        else response
    )
    receipt = publish()
    assert receipt.status == status
    assert len(api.writes) == (1 if endpoint == "commits" else 2)
    if endpoint == "refs":
        assert receipt.commit_sha == CREATED


def test_dispatch_executor_is_independent_of_agreeing_live_context(case: Case, tmp_path: Path) -> None:
    api = case.api
    data = json.dumps(api.intent).encode()
    path = tmp_path / "executor-mismatch.json"
    path.write_bytes(data)
    context = signer.RunContext(
        EXECUTOR,
        789,
        1,
        123,
        "nold-ai/specfact-cli",
        456,
        "owner",
        456,
        "owner",
        "workflow_dispatch",
        AUX,
        204352514,
        ".github/workflows/specfact.yml",
    )
    expected = signer.DispatchExpectation(MAIN, hashlib.sha256(data).hexdigest())
    assert signer.publish_once(path, expected, context).status == "refused"
    assert api.writes == []


@pytest.mark.parametrize(
    "field,value",
    [
        ("executor_sha", MAIN),
        ("run_id", 790),
        ("run_attempt", 2),
        ("actor_id", 999),
        ("actor_login", "other"),
        ("triggering_actor_id", 999),
        ("triggering_actor_login", "other"),
        ("repository_id", 999),
        ("repository_full_name", "other/repo"),
        ("event", "push"),
        ("ref", "refs/heads/other"),
        ("workflow_id", 1),
        ("workflow_path", ".github/workflows/other.yml"),
    ],
)
def test_context_fields_are_independently_bound(case: Case, field: str, value: Any) -> None:
    assert case.publish(**{field: value}).status == "refused"
    assert case.api.writes == []


@pytest.mark.parametrize("after,status", [(1, "object_only"), (2, "created_ref_with_drift")])
@pytest.mark.parametrize(
    "guard",
    [
        "main",
        "aux",
        "repository",
        "run",
        "attempt",
        "status",
        "actor_id",
        "actor_login",
        "triggering_actor",
        "executor",
        "workflow",
        "event",
        "other_dispatch",
        "destination",
    ],
)
def test_every_live_guard_is_rechecked_after_writes(case: Case, after: int, status: str, guard: str) -> None:
    api = case.api

    def edit(method: str, path: str, body: dict[str, Any] | None, response: signer._Response) -> signer._Response:
        if method != "GET" or len(api.writes) < after:
            return response
        if guard == "destination" and path == api.ref_path(DEST):
            return signer._Response(200, json.dumps(api.ref(DEST, MAIN)).encode())
        record: dict[str, Any] = json.loads(response.body)
        _corrupt_live_guard(api, record, path, guard)
        return signer._Response(response.status, json.dumps(record).encode())

    api.edit = edit
    receipt = case.publish()
    assert receipt.status == status
    assert receipt.commit_sha == CREATED
    assert len(api.writes) == after
    if after == 2:
        assert api.destination == CREATED
        assert receipt.ref_sha == (MAIN if guard == "destination" else CREATED)


def _corrupt_live_guard(api: GitHub, record: dict[str, Any], path: str, guard: str) -> None:
    if guard in ("main", "aux") and path == api.ref_path(AUX if guard == "aux" else "refs/heads/main"):
        record["object"]["sha"] = SOURCE
        return
    if guard == "repository" and path == REPO:
        record["id"] = 999
        return
    if path == f"{REPO}/actions/runs/789":
        changes: dict[str, tuple[str, object]] = {
            "run": ("id", 790),
            "attempt": ("run_attempt", 2),
            "status": ("status", "completed"),
            "actor_id": ("actor", {"id": 999, "login": "owner"}),
            "actor_login": ("actor", {"id": 456, "login": "other"}),
            "triggering_actor": ("triggering_actor", {"id": 999, "login": "other"}),
            "executor": ("head_sha", MAIN),
            "workflow": ("workflow_id", 1),
            "event": ("event", "push"),
        }
        if guard in changes:
            key, value = changes[guard]
            record[key] = value
        return
    if guard == "other_dispatch" and path.endswith("/runs?event=workflow_dispatch&per_page=100"):
        record["workflow_runs"].append({**api.run, "id": 790})
        record["total_count"] = 2


@pytest.mark.parametrize("corruption", ["absent_ref", "signature", "payload", "attribution"])
def test_final_verification_failure_retains_creation_effects(case: Case, corruption: str) -> None:
    api = case.api

    def edit(method: str, path: str, body: dict[str, Any] | None, response: signer._Response) -> signer._Response:
        if method != "GET" or len(api.writes) != 2:
            return response
        record = json.loads(response.body)
        if corruption == "absent_ref" and path == api.ref_path(DEST):
            return signer._Response(404, b'{"message":"Not Found"}')
        if path == f"{REPO}/git/commits/{CREATED}" and corruption in ("signature", "payload"):
            record["verification"][corruption] += "changed"
        if path == f"{REPO}/commits/{CREATED}" and corruption == "attribution":
            record["committer"]["id"] = 999
        return signer._Response(response.status, json.dumps(record).encode())

    api.edit = edit
    receipt = case.publish()
    assert receipt.status == "created_ref_with_drift"
    assert receipt.commit_sha == CREATED
    assert api.destination == CREATED
    assert len(api.writes) == 2
    if corruption != "absent_ref":
        assert receipt.ref_sha == CREATED


@pytest.mark.parametrize("role", ["author", "committer"])
@pytest.mark.parametrize("field,value", [("id", 999), ("login", "other"), ("type", "Organization")])
def test_each_api_service_identity_field_is_exact(case: Case, role: str, field: str, value: Any) -> None:
    api = case.api

    def edit(method: str, path: str, body: dict[str, Any] | None, response: signer._Response) -> signer._Response:
        if path != f"{REPO}/commits/{CREATED}":
            return response
        record = json.loads(response.body)
        record[role][field] = value
        return signer._Response(response.status, json.dumps(record).encode())

    api.edit = edit
    receipt = case.publish()
    assert (receipt.status, receipt.commit_sha) == ("object_only", CREATED)
    assert [item[1] for item in api.writes] == [f"{REPO}/git/commits"]


@pytest.mark.parametrize("role", ["author", "committer"])
@pytest.mark.parametrize("field", ["name", "email"])
@pytest.mark.parametrize("surface", ["metadata", "payload", "both"])
def test_each_git_service_identity_field_is_exact(case: Case, role: str, field: str, surface: str) -> None:
    api = case.api

    def edit(method: str, path: str, body: dict[str, Any] | None, response: signer._Response) -> signer._Response:
        if path not in (f"{REPO}/git/commits", f"{REPO}/git/commits/{CREATED}"):
            return response
        record = json.loads(response.body)
        old = record[role][field]
        if surface in ("metadata", "both"):
            record[role][field] = "unauthorized"
        if surface in ("payload", "both"):
            lines = record["verification"]["payload"].splitlines(keepends=True)
            record["verification"]["payload"] = "".join(
                line.replace(old, "unauthorized", 1) if line.startswith(f"{role} ") else line for line in lines
            )
        return signer._Response(response.status, json.dumps(record).encode())

    api.edit = edit
    receipt = case.publish()
    assert (receipt.status, receipt.commit_sha) == ("object_only", CREATED)
    assert [item[1] for item in api.writes] == [f"{REPO}/git/commits"]


@pytest.mark.parametrize("method_to_change", ["POST", "GET"])
@pytest.mark.parametrize("field", ["signature", "payload"])
def test_post_and_readback_verification_must_agree(case: Case, method_to_change: str, field: str) -> None:
    api = case.api

    def edit(method: str, path: str, body: dict[str, Any] | None, response: signer._Response) -> signer._Response:
        if method != method_to_change or path not in (f"{REPO}/git/commits", f"{REPO}/git/commits/{CREATED}"):
            return response
        record = json.loads(response.body)
        record["verification"][field] += "changed"
        return signer._Response(response.status, json.dumps(record).encode())

    api.edit = edit
    receipt = case.publish()
    assert (receipt.status, receipt.commit_sha) == ("object_only", CREATED)
    assert [item[1] for item in api.writes] == [f"{REPO}/git/commits"]


@pytest.mark.parametrize("field", ["tree", "parent", "message"])
def test_self_consistent_signed_commit_must_match_intent(case: Case, field: str) -> None:
    api = case.api

    def edit(method: str, path: str, body: dict[str, Any] | None, response: signer._Response) -> signer._Response:
        if path not in (f"{REPO}/git/commits", f"{REPO}/git/commits/{CREATED}"):
            return response
        record = json.loads(response.body)
        payload = record["verification"]["payload"]
        if field == "tree":
            record["tree"]["sha"] = MAIN
            payload = payload.replace(f"tree {TREE}\n", f"tree {MAIN}\n", 1)
        elif field == "parent":
            record["parents"] = [{"sha": MAIN}]
            payload = payload.replace(f"parent {PARENT}\n", f"parent {MAIN}\n", 1)
        else:
            record["message"] += "unauthorized"
            payload += "unauthorized"
        record["verification"]["payload"] = payload
        return signer._Response(response.status, json.dumps(record).encode())

    api.edit = edit
    receipt = case.publish()
    assert (receipt.status, receipt.commit_sha) == ("object_only", CREATED)
    assert [item[1] for item in api.writes] == [f"{REPO}/git/commits"]


def test_whole_tree_preserves_unchanged_production_executables_and_directories(case: Case) -> None:
    api = case.api
    for sha in (BASE_TREE, TREE):
        inventory = api.records[f"{REPO}/git/trees/{sha}?recursive=1"]["tree"]
        for path in ("openspec", "openspec/changes", "openspec/changes/security-dependencies-0-55-11-dev"):
            inventory.append({"path": path, "mode": "040000", "type": "tree", "sha": sha})
        inventory.extend(
            [
                {"path": "src", "mode": "040000", "type": "tree", "sha": OLD},
                {"path": "src/specfact_cli", "mode": "040000", "type": "tree", "sha": OLD},
                {"path": "src/specfact_cli/cli.py", "mode": "100644", "type": "blob", "sha": OLD},
                {"path": "scripts", "mode": "040000", "type": "tree", "sha": OLD},
                {"path": "scripts/check_license_compliance.py", "mode": "100755", "type": "blob", "sha": OLD},
            ]
        )
    receipt = case.publish()
    assert receipt.status == "published"
    assert api.created is not None
    assert api.writes[0][2] == {"tree": TREE, "parents": [PARENT], "message": api.created["message"]}
    assert len(api.writes) == 2


@pytest.mark.parametrize("tree", [BASE_TREE, TREE], ids=["base", "source"])
@pytest.mark.parametrize(
    "malformed", ["duplicate", "truncated", "missing_marker", "null_marker", "string_marker", "integer_marker"]
)
def test_each_inventory_requires_unique_paths_and_explicit_completeness(case: Case, tree: str, malformed: str) -> None:
    record = case.api.records[f"{REPO}/git/trees/{tree}?recursive=1"]
    if malformed == "duplicate":
        record["tree"].append(copy.deepcopy(record["tree"][0]))
    elif malformed == "missing_marker":
        del record["truncated"]
    else:
        record["truncated"] = {"truncated": True, "null_marker": None, "string_marker": "false", "integer_marker": 0}[
            malformed
        ]
    assert case.publish().status == "refused"
    assert case.api.writes == []


@pytest.mark.parametrize("path", ["scripts/dev_security_ci_signer.py", ".github/workflows/specfact.yml"])
def test_source_delta_cannot_add_auxiliary_signer_or_workflow(case: Case, path: str) -> None:
    api = case.api
    api.intent["delta"].append({"path": path, "before": None, "after": ["100644", NEW]})
    api.records[f"{REPO}/git/trees/{TREE}?recursive=1"]["tree"].append(
        {"path": path, "mode": "100644", "type": "blob", "sha": NEW}
    )
    assert case.publish().status == "refused"
    assert api.writes == []


_HTTP_ERRORS: list[Callable[[], HTTPException]] = [
    lambda: BadStatusLine("invalid status"),
    lambda: IncompleteRead(b"partial", 10),
]


@pytest.mark.parametrize("fault", _HTTP_ERRORS, ids=["bad-status", "incomplete-read"])
@pytest.mark.parametrize("endpoint,status", [("commits", "uncertain_commit"), ("refs", "uncertain_ref")])
def test_http_protocol_failure_after_post_retains_uncertainty(
    case: Case, endpoint: str, status: str, fault: Callable[[], HTTPException]
) -> None:
    api = case.api

    def edit(method: str, path: str, body: dict[str, Any] | None, response: signer._Response) -> signer._Response:
        if method == "POST" and path == f"{REPO}/git/{endpoint}":
            raise fault()
        return response

    api.edit = edit
    receipt = case.publish()
    assert receipt.status == status
    assert len(api.writes) == (1 if endpoint == "commits" else 2)
    assert api.created is not None
    if endpoint == "refs":
        assert receipt.commit_sha == CREATED
        assert api.destination == CREATED


@pytest.mark.parametrize("fault", _HTTP_ERRORS, ids=["bad-status", "incomplete-read"])
@pytest.mark.parametrize("after,status", [(1, "object_only"), (2, "created_ref_with_drift")])
def test_http_protocol_readback_failure_preserves_known_effects(
    case: Case, after: int, status: str, fault: Callable[[], HTTPException]
) -> None:
    api = case.api

    def edit(method: str, path: str, body: dict[str, Any] | None, response: signer._Response) -> signer._Response:
        if method == "GET" and path == f"{REPO}/git/commits/{CREATED}" and len(api.writes) >= after:
            raise fault()
        return response

    api.edit = edit
    receipt = case.publish()
    assert (receipt.status, receipt.commit_sha) == (status, CREATED)
    assert len(api.writes) == after
    if after == 2:
        assert receipt.ref_sha == api.destination == CREATED


@pytest.mark.parametrize("fault", _HTTP_ERRORS, ids=["bad-status", "incomplete-read"])
@pytest.mark.parametrize(
    "stage",
    [("commits", "uncertain_commit"), ("refs", "uncertain_ref")],
    ids=["commits-uncertain_commit", "refs-uncertain_ref"],
)
def test_http_protocol_cli_writes_the_preserved_partial_receipt(
    case: Case,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    stage: tuple[str, str],
    fault: Callable[[], HTTPException],
) -> None:
    endpoint, status = stage
    api = case.api
    data = json.dumps(api.intent).encode()
    intent = tmp_path / "intent.json"
    intent.write_bytes(data)
    output = tmp_path / "receipt"
    context = signer.RunContext(
        EXECUTOR,
        789,
        1,
        123,
        "nold-ai/specfact-cli",
        456,
        "owner",
        456,
        "owner",
        "workflow_dispatch",
        AUX,
        204352514,
        ".github/workflows/specfact.yml",
    )
    monkeypatch.setattr(signer, "_environment_context", lambda: context)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "signer",
            "--intent",
            str(intent),
            "--expected-executor",
            EXECUTOR,
            "--expected-intent",
            hashlib.sha256(data).hexdigest(),
            "--output",
            str(output),
        ],
    )

    def edit(method: str, path: str, body: dict[str, Any] | None, response: signer._Response) -> signer._Response:
        if method == "POST" and path == f"{REPO}/git/{endpoint}":
            raise fault()
        return response

    api.edit = edit
    assert signer._main() == 1
    receipt = json.loads((output / "receipt.json").read_text())
    assert receipt["status"] == status
    assert receipt["reason"] != "Context or intent unavailable"
    assert len(api.writes) == (1 if endpoint == "commits" else 2)
    if endpoint == "refs":
        assert receipt["commit_sha"] == CREATED
        assert api.destination == CREATED


@pytest.mark.parametrize("parents", [None, [], [{"sha": DEV}], [{"sha": PARENT}, {"sha": DEV}]])
def test_refresh_refuses_wrong_source_parent_before_writes(case: Case, parents: object) -> None:
    source = case.api.records[f"{REPO}/git/commits/{SOURCE}"]
    if parents is None:
        source.pop("parents")
    else:
        source["parents"] = parents
    receipt = case.publish()
    assert receipt.status == "refused"
    assert not case.api.writes


@pytest.mark.parametrize(
    "field,value",
    [("state", "closed"), ("draft", True), ("auto_merge", {}), ("head", {"sha": DEV}), ("base", {"sha": MAIN})],
)
def test_refresh_refuses_pr_drift_before_writes(case: Case, field: str, value: object) -> None:
    case.api.records[f"{REPO}/pulls/786"][field] = value
    assert case.publish().status == "refused"
    assert not case.api.writes


@pytest.mark.parametrize(
    "path",
    [
        "tests/unit/security/test_code_review_dependency_security.py",
        "tests/unit/security/test_release_promotion_security_gates.py",
    ],
)
def test_refresh_accepts_only_added_test_paths(case: Case, path: str) -> None:
    api = case.api
    api.intent["delta"].append({"path": path, "before": None, "after": ["100644", NEW]})
    api.records[f"{REPO}/git/trees/{TREE}?recursive=1"]["tree"].append(
        {"path": path, "mode": "100644", "type": "blob", "sha": NEW}
    )
    assert case.publish().status == "published"
    commit_body = api.writes[0][2]
    assert commit_body is not None
    assert commit_body["parents"] == [PARENT]


@pytest.mark.parametrize("path", ["src/specfact_cli/cli.py", "tests/unit/security/test_unreviewed.py"])
def test_refresh_refuses_unreviewed_scope(case: Case, path: str) -> None:
    case.api.intent["delta"][0]["path"] = path
    assert case.publish().status == "refused"
    assert not case.api.writes


@pytest.mark.parametrize(
    "field,value",
    [
        ("auxiliary_ref", "refs/heads/codex/security-dev-ci-signer"),
        ("destination", "refs/heads/codex/security-dependencies-0-55-11-dev"),
    ],
)
def test_refresh_refuses_old_scope(case: Case, field: str, value: str) -> None:
    case.api.intent[field] = value
    assert case.publish().status == "refused"
    assert not case.api.writes


@pytest.mark.parametrize("guard_number,status,writes", [(2, "object_only", 1), (3, "created_ref_with_drift", 2)])
def test_refresh_retains_partial_outcome_on_late_pr_drift(
    case: Case, guard_number: int, status: str, writes: int
) -> None:
    observed = 0

    def edit(method: str, path: str, body: dict[str, Any] | None, response: signer._Response) -> signer._Response:
        nonlocal observed
        if path == f"{REPO}/pulls/786":
            observed += 1
            if observed == guard_number:
                record = json.loads(response.body)
                record["head"]["sha"] = DEV
                return signer._Response(200, json.dumps(record).encode())
        return response

    case.api.edit = edit
    assert case.publish().status == status
    assert len(case.api.writes) == writes


def test_refresh_rejects_old_dev_parent_even_with_consistent_signature(case: Case) -> None:
    def edit(method: str, path: str, body: dict[str, Any] | None, response: signer._Response) -> signer._Response:
        if path == f"{REPO}/git/commits":
            record = json.loads(response.body)
            record["parents"] = [{"sha": DEV}]
            record["verification"]["payload"] = record["verification"]["payload"].replace(
                f"parent {PARENT}\n", f"parent {DEV}\n", 1
            )
            return signer._Response(201, json.dumps(record).encode())
        return response

    case.api.edit = edit
    assert case.publish().status == "object_only"
    assert len(case.api.writes) == 1


def test_unbound_template_refuses_before_transport(case: Case) -> None:
    raw = json.dumps({**case.api.intent, "source_commit": "UNBOUND", "source_tree": "UNBOUND", "delta": []}).encode()
    assert case.publish(raw).status == "refused"
    assert case.api.trace == []

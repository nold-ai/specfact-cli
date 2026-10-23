from __future__ import annotations

import copy
import hashlib
import json
import urllib.error
import urllib.request
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from email.message import Message
from io import BytesIO
from pathlib import Path
from typing import Any

import pytest
import yaml

from scripts import pr785_signing_recovery as recovery
from tests.unit.scripts.test_pr785_signing_recovery import ROOT, FakeAPI, context_env


DIGEST = "6c3d344ecb69beca59231c3c49ae05dba50790fd253db87f37122028de1dfa2a"
MAIN = "5262efb0881e4fac7697d629b0530250342bc656"
EXECUTOR = "a" * 40
ACCEPTED_EXECUTOR = "88dc8c40c7a1e852c539d0668238b94da5ca32b2"
ACCEPTED_RUN = 39936325185
ACCEPTED_ZIP = "7fc151d4549bc6c47e09764106339b8cb52e227cfcc9848ee65373b34f36bb51"
ACCEPTED = {
    "baseline": ("db02837c1922eaa191e10238606ac83571c4f228", "4c9ba46b2ace65cd8df0fcd5a77c2b14a42f599c"),
    "inert-workflow": ("837a9d68fe62bb13e9b272f0c6f11634894ae0fb", "4b2cf05809c1cf687e4eae17a770cd33c97eff72"),
}


@dataclass(frozen=True)
class Source:
    sha: str
    tree: str
    subject: str


SOURCES = (
    Source(
        "dd1b4121944f247c4d5dff0903902e2721d8c1a6",
        "4925c1deff2a09235570f76f3630f15581f679ca",
        "test(release): prove dependency security regressions",
    ),
    Source(
        "08126f3f8a8e46a79c46c574dfd7b0c44e915831",
        "0822952c8a8004c3b92d9c7560b3a24c436443b3",
        "test(release): bind native proof to change failures",
    ),
    Source(
        "a2ee2c9d96e1cce5ba1f13f733ccc49580262ffb",
        "b852f08abbaa1fe90f8fa927369611d31fdd0d58",
        "test(release): isolate the frozen GitPython closure",
    ),
    Source(
        "8cce44f449e9559d0100064d629c81991784ab41",
        "a3cfdc441190e11a0c4db22cbdc324b44a2b7f8e",
        "test(release): refresh official dependency proof",
    ),
    Source(
        "fe1e1e9c0ce77ee0b3b620a882c77b0be8501860",
        "f19f5e36d8535cc7b21c5eaf745661ffb52f0992",
        "test(security): bind advisory correction",
    ),
    Source(
        "4936750186fcb339913a8710f3034cf1d2be901f",
        "a95395aaf17130d8c7835fe2ee19d3e3c251f818",
        "test(security): reconcile release proof quality",
    ),
    Source(
        "2eef82529a8eb166b9a18898316ae92ce170f02a",
        "f82634e9b0f290cfce89a35199dfe5d6216fd54f",
        "test(security): bind supported parser proof",
    ),
)


def signed_object(sha: str, tree: str, parent: str, message: str) -> dict[str, Any]:
    author = {"name": "github-actions[bot]", "email": "41898282+github-actions[bot]@users.noreply.github.com"}
    committer = {"name": "GitHub", "email": "noreply@github.com"}
    payload = f"tree {tree}\nparent {parent}\nauthor {author['name']} <{author['email']}> 1 +0000\ncommitter {committer['name']} <{committer['email']}> 1 +0000\n\n{message}"
    return {
        "sha": sha,
        "tree": {"sha": tree},
        "parents": [{"sha": parent}],
        "message": message,
        "author": author,
        "committer": committer,
        "verification": {"verified": True, "reason": "valid", "signature": "signature", "payload": payload},
    }


def anchor(label: str) -> str:
    return f"heads/codex/pr785-signing-recovery/{DIGEST}/probe-{label}"


def prefix_message(ordinal: int) -> str:
    source = SOURCES[ordinal - 1]
    return f"{source.subject}\n\nStage: prefix7\nSource: {source.sha}\nOrdinal: {ordinal}\nManifest: {DIGEST}\nExecutor: {EXECUTOR}\nRun: 123\nAttempt: 1"


def corrupt(record: dict[str, Any], fault: str) -> None:
    replacements = {
        "sha": "malformed",
        "tree": {"sha": "f" * 40},
        "parent": [{"sha": "f" * 40}],
        "parents": [],
        "subject": "wrong",
        "message": "wrong",
    }
    if fault in replacements:
        key = {"parent": "parents", "subject": "message"}.get(fault, fault)
        record[key] = replacements[fault]
    elif fault in ("unsigned", "signature", "payload", "reason"):
        key, value = {
            "unsigned": ("verified", False),
            "signature": ("signature", ""),
            "payload": ("payload", "wrong"),
            "reason": ("reason", "unknown_key"),
        }[fault]
        record["verification"][key] = value
    else:
        role, field = fault.split(".")
        record[role][field] = "wrong"


class PrefixAPI(FakeAPI):
    def __init__(self) -> None:
        super().__init__(recovery.Manifest.load(ROOT / "ci/recovery/pr785-signing-inputs.json"))
        self.originals: dict[str, dict[str, Any]] = {
            source.sha: {
                "sha": source.sha,
                "tree": {"sha": source.tree},
                "parents": [{"sha": MAIN if i == 0 else SOURCES[i - 1].sha}],
                "message": source.subject + "\n\nHistorical body",
            }
            for i, source in enumerate(SOURCES)
        }
        self.accepted = {
            sha: signed_object(
                sha,
                tree,
                MAIN,
                f"PR785 signing probe {label}\n\nManifest: {DIGEST}\nExecutor: {ACCEPTED_EXECUTOR}\nRun: {ACCEPTED_RUN}\nAttempt: 1",
            )
            for label, (sha, tree) in ACCEPTED.items()
        }
        self.refs: dict[str, dict[str, Any]] = {
            f"/git/ref/{anchor(label)}": {"ref": f"refs/{anchor(label)}", "object": {"type": "commit", "sha": sha}}
            for label, (sha, _) in ACCEPTED.items()
        }
        self.target = 0
        self.attribution_target = ""
        self.object_fault = ""
        self.fault_surface = "create"
        self.transport_fault = ""
        self.postguard_fault = False
        self.guard_phase = ""
        self.guard_counts: dict[int, int] = {}
        self.drift_after_sources = ""

    def request(self, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        if method == "GET" and path in self.refs:
            self.calls.append((method, path, body or {}))
            return copy.deepcopy(self.refs[path])
        sha = path.rsplit("/", 1)[-1]
        if method == "GET" and path.startswith("/git/commits/") and sha in self.originals | self.accepted:
            self.calls.append((method, path, body or {}))
            if sha == SOURCES[-1].sha and self.drift_after_sources:
                self.fault = self.drift_after_sources
            return copy.deepcopy((self.originals | self.accepted)[sha])
        return super().request(method, path, body)

    def main_ref(self) -> dict[str, Any]:
        self.guard_counts[self.writes] = self.guard_counts.get(self.writes, 0) + 1
        count = self.guard_counts[self.writes]
        drift = self.fault == "main" or (self.postguard_fault and self.writes == self.target)
        drift |= self.guard_phase == "post" and self.writes == self.target
        drift |= (
            self.guard_phase == "pre" and self.writes == self.target - 1 and count >= (1 if self.target == 1 else 2)
        )
        return {"object": {"sha": "f" * 40 if drift else MAIN}}

    def create_commit(self, body: dict[str, Any]) -> dict[str, Any]:
        ordinal = self.writes
        assert 1 <= ordinal <= 7, "Only seven prefix writes are authorized"
        assert set(body) == {"tree", "parents", "message"}
        assert body["tree"] == SOURCES[ordinal - 1].tree
        assert body["parents"] == [MAIN if ordinal == 1 else str(ordinal - 1) * 40]
        assert body["message"] == prefix_message(ordinal)
        assert all(("GET", f"/git/commits/{source.sha}", {}) in self.calls for source in SOURCES)
        if ordinal == self.target and self.transport_fault:
            raise_transport(self.transport_fault)
        sha = str(ordinal) * 40
        result = signed_object(sha, body["tree"], body["parents"][0], body["message"])
        if ordinal == self.target and self.fault_surface == "create":
            self.damage(result)
        self.objects[sha] = copy.deepcopy(result)
        return result

    def damage(self, record: dict[str, Any]) -> None:
        old_identities = {
            "original": SOURCES[self.target - 1].sha,
            "auxiliary": EXECUTOR,
            "accepted": ACCEPTED["baseline"][0],
            "main": MAIN,
            "reuse": "1" * 40,
        }
        if self.object_fault in old_identities:
            record["sha"] = old_identities[self.object_fault]
        elif self.object_fault:
            corrupt(record, self.object_fault)

    def read_commit(self, sha: str) -> dict[str, Any]:
        result = super().read_commit(sha)
        if self.writes == self.target and self.fault_surface == "readback":
            self.damage(result)
        return result

    def commit_attribution(self, sha: str) -> dict[str, Any]:
        result = super().commit_attribution(sha)
        if (
            self.writes == self.target
            and self.fault_surface == "attribution"
            and (not self.attribution_target or sha == self.attribution_target)
        ):
            self.damage(result)
        return result


def raise_transport(fault: str) -> None:
    if fault == "denied":
        raise urllib.error.HTTPError(
            "https://api.github.com", 403, "untrusted-secret", Message(), BytesIO(b"untrusted-secret")
        )
    raise urllib.error.URLError("untrusted-secret")


def invoke(
    output: Path,
    monkeypatch: pytest.MonkeyPatch,
    api: FakeAPI,
    stage: str = "prefix7",
    *,
    environment: dict[str, str] | None = None,
) -> int:
    for key, value in (context_env() if environment is None else environment).items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("EXPECTED_MANIFEST_SHA256", DIGEST)
    monkeypatch.setenv("GH_TOKEN", "never-persist-token")

    def respond(_opener: Any, request: urllib.request.Request, *args: Any, **kwargs: Any) -> BytesIO:
        path = request.full_url.removeprefix("https://api.github.com/repos/nold-ai/specfact-cli")
        data = request.data
        assert data is None or isinstance(data, bytes)
        body = json.loads(data) if data is not None else None
        return BytesIO(json.dumps(api.request(request.get_method(), path, body)).encode())

    monkeypatch.setattr(urllib.request.OpenerDirector, "open", respond)
    try:
        return recovery.main(["--stage", stage, "--expected-executor", EXECUTOR, "--output", str(output)])
    except (OSError, TypeError, ValueError) as error:
        pytest.fail(f"CLI escaped safe evidence boundary with {type(error).__name__}")


def receipt_at(output: Path) -> dict[str, Any]:
    return json.loads((output / "receipt.json").read_text())


def assert_steps(receipt: dict[str, Any], count: int) -> None:
    assert receipt.get("stage") == "prefix7"
    assert "objects" not in receipt
    assert receipt["ci_anchor_verified"] is receipt["root_anchor_verified"] is False
    steps = receipt["steps"]
    assert len(steps) == count
    for ordinal, step in enumerate(steps, 1):
        source = SOURCES[ordinal - 1]
        expected = {
            "ordinal": ordinal,
            "source_sha": source.sha,
            "source_tree": source.tree,
            "source_parent": MAIN if ordinal == 1 else SOURCES[ordinal - 2].sha,
            "subject": source.subject,
            "sha": str(ordinal) * 40,
            "tree": source.tree,
            "parent": MAIN if ordinal == 1 else str(ordinal - 1) * 40,
            "message": prefix_message(ordinal),
            "signed_object_verified": True,
        }
        assert {key: step[key] for key in expected} == expected
        assert step["signature"] and step["payload"]


def expected_context() -> dict[str, Any]:
    return {
        "run_id": 123,
        "run_attempt": 1,
        "executor_sha": EXECUTOR,
        "repository": "nold-ai/specfact-cli",
        "actor": "djm81",
        "event": "workflow_dispatch",
        "ref": "refs/heads/codex/pr785-ci-signing-recovery",
        "workflow_id": 204352514,
        "workflow_path": ".github/workflows/specfact.yml",
    }


def assert_receipt_identity(receipt: dict[str, Any], context: dict[str, Any]) -> None:
    assert receipt["manifest_digest"] == DIGEST
    assert receipt["context"] == context
    for key, value in context.items():
        assert type(receipt["context"][key]) is type(value)
    assert_accepted_witness(receipt)


def assert_refused(
    output: Path,
    api: PrefixAPI,
    counts: tuple[int, int],
    *,
    facts: tuple[bool, bool, bool],
    context: dict[str, Any] | None = None,
) -> None:
    writes, verified = counts
    assert api.writes == writes
    receipt = receipt_at(output)
    assert receipt["status"] == "refused"
    assert_steps(receipt, verified)
    assert_receipt_identity(receipt, expected_context() if context is None else context)
    for key, expected in zip(("context_verified", "accepted_probe_verified", "sources_verified"), facts, strict=True):
        assert receipt[key] is expected


def test_prefix7_cli_signs_exact_seven_mapped_trees(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    api = PrefixAPI()
    assert invoke(tmp_path, monkeypatch, api) == 0
    assert api.writes == 7
    receipt = receipt_at(tmp_path)
    assert receipt["status"] == "prefix7_verified"
    assert receipt["manifest_digest"] == DIGEST
    assert receipt["context_verified"] is receipt["sources_verified"] is receipt["accepted_probe_verified"] is True
    assert_steps(receipt, 7)
    assert len({step["sha"] for step in receipt["steps"]}) == 7
    assert receipt["steps"][-1]["tree"] == "f82634e9b0f290cfce89a35199dfe5d6216fd54f"
    assert receipt["context"]["executor_sha"] == EXECUTOR
    assert_receipt_identity(receipt, expected_context())
    assert_prefix_requests(tmp_path, api, receipt)


def expected_witness() -> dict[str, Any]:
    return {
        "executor": ACCEPTED_EXECUTOR,
        "run": ACCEPTED_RUN,
        "attempt": 1,
        "artifact": 12494410796,
        "zip_sha256": ACCEPTED_ZIP,
        "objects": [
            {"label": label, "sha": sha, "tree": tree, "ref": f"refs/{anchor(label)}"}
            for label, (sha, tree) in ACCEPTED.items()
        ],
    }


def assert_accepted_witness(receipt: dict[str, Any]) -> None:
    witness = receipt["accepted_probe"]
    expected = expected_witness()
    assert witness == expected
    for key, value in expected.items():
        assert type(witness[key]) is type(value)
    for record in witness["objects"]:
        assert all(type(value) is str for value in record.values())


def assert_prefix_requests(tmp_path: Path, api: PrefixAPI, receipt: dict[str, Any]) -> None:
    raw = [json.loads(path.read_text()) for path in sorted((tmp_path / "raw").glob("*.json"))]
    assert len(raw) == len(api.calls)
    assert "never-persist-token" not in json.dumps(raw) + json.dumps(receipt)
    assert all(path == "/git/commits" for method, path, _ in api.calls if method != "GET")
    original_reads = [
        path
        for method, path, _ in api.calls
        if method == "GET" and path in {f"/git/commits/{source.sha}" for source in SOURCES}
    ]
    assert original_reads == [f"/git/commits/{source.sha}" for source in SOURCES]
    assert_preflight_order(api)


def assert_preflight_order(api: PrefixAPI) -> None:
    assert api.calls[0] == ("GET", "/actions/runs/123", {})
    first_source = api.calls.index(("GET", f"/git/commits/{SOURCES[0].sha}", {}))
    for label, (sha, _) in ACCEPTED.items():
        for path in (f"/git/ref/{anchor(label)}", f"/git/commits/{sha}", f"/commits/{sha}"):
            assert ("GET", path, {}) in api.calls[:first_source]


@pytest.mark.parametrize("ordinal", range(1, 8))
@pytest.mark.parametrize("fault", ["sha", "tree", "parent", "parents", "subject"])
def test_source_preflight_refuses_before_writes(
    ordinal: int, fault: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    api = PrefixAPI()
    source = SOURCES[ordinal - 1]
    corrupt(api.originals[source.sha], fault)
    assert invoke(tmp_path, monkeypatch, api) == 1
    assert ("GET", f"/git/commits/{source.sha}", {}) in api.calls
    assert_refused(tmp_path, api, (0, 0), facts=(True, True, False))
    assert_preflight_order(api)


@pytest.mark.parametrize("ordinal", range(1, 8))
@pytest.mark.parametrize(
    "surface,fault",
    [
        (surface, fault)
        for surface in ("create", "readback")
        for fault in (
            "sha",
            "tree",
            "parent",
            "message",
            "unsigned",
            "signature",
            "payload",
            "reason",
            "author.name",
            "author.email",
            "committer.name",
            "committer.email",
        )
    ]
    + [("attribution", f"{role}.{field}") for role in ("author", "committer") for field in ("login", "id", "type")],
)
def test_every_signed_step_fault_stops(
    ordinal: int, surface: str, fault: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    api = PrefixAPI()
    api.target, api.fault_surface, api.object_fault = ordinal, surface, fault
    assert invoke(tmp_path, monkeypatch, api) == 1
    assert_refused(tmp_path, api, (ordinal, ordinal - 1), facts=(True, True, True))
    last_post = max(i for i, (method, _, _) in enumerate(api.calls) if method == "POST")
    assert ("GET", "/git/ref/heads/main", {}) in api.calls[last_post + 1 :]


@pytest.mark.parametrize("label", list(ACCEPTED))
@pytest.mark.parametrize(
    "fault",
    [
        "ref",
        "type",
        "sha",
        "message",
        "signature",
        "payload",
        "author.name",
        "committer.email",
        "author.login",
        "committer.id",
    ],
)
def test_accepted_witness_is_reverified(
    label: str, fault: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    api = PrefixAPI()
    path = f"/git/ref/{anchor(label)}"
    sha, _ = ACCEPTED[label]
    if fault == "ref":
        api.refs[path]["ref"] = "refs/heads/main"
    elif fault in ("type", "sha"):
        api.refs[path]["object"][fault] = "wrong"
    elif fault in ("author.login", "committer.id"):
        api.target, api.fault_surface, api.object_fault = 0, "attribution", fault
        api.attribution_target = sha
    else:
        corrupt(api.accepted[sha], fault)
    assert invoke(tmp_path, monkeypatch, api) == 1
    assert ("GET", path, {}) in api.calls
    assert_refused(tmp_path, api, (0, 0), facts=(True, False, False))
    assert not any(("GET", f"/git/commits/{source.sha}", {}) in api.calls for source in SOURCES)


@pytest.mark.parametrize("ordinal", range(1, 8))
@pytest.mark.parametrize("phase", ["pre", "post"])
def test_ref_drift_around_every_write(
    ordinal: int, phase: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    api = PrefixAPI()
    api.target, api.guard_phase = ordinal, phase
    assert invoke(tmp_path, monkeypatch, api) == 1
    assert_refused(tmp_path, api, (ordinal if phase == "post" else ordinal - 1, ordinal - 1), facts=(True, True, True))
    assert api.guard_counts


@pytest.mark.parametrize("ordinal", range(1, 8))
@pytest.mark.parametrize(
    "failure",
    [("denied", False), ("denied", True), ("uncertain", False), ("uncertain", True)],
    ids=["denied", "denied-postguard", "uncertain", "uncertain-postguard"],
)
def test_transport_failure_still_guards_and_keeps_primary_reason(
    ordinal: int,
    failure: tuple[str, bool],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    api = PrefixAPI()
    fault, postguard_fails = failure
    api.target, api.transport_fault, api.postguard_fault = ordinal, fault, postguard_fails
    assert invoke(tmp_path, monkeypatch, api) == 1
    assert_refused(tmp_path, api, (ordinal, ordinal - 1), facts=(True, True, True))
    last_post = max(i for i, (method, _, _) in enumerate(api.calls) if method == "POST")
    assert ("GET", "/git/ref/heads/main", {}) in api.calls[last_post + 1 :]
    diagnostic = capsys.readouterr().err
    assert ("API refused HTTP 403" if fault == "denied" else "transport") in diagnostic
    assert "untrusted-secret" not in diagnostic


@pytest.mark.parametrize("fault", ["original", "auxiliary", "accepted", "main", "reuse"])
def test_new_identity_cannot_reuse_existing_objects(
    fault: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    api = PrefixAPI()
    api.target, api.object_fault = 2, fault
    assert invoke(tmp_path, monkeypatch, api) == 1
    assert_refused(tmp_path, api, (2, 1), facts=(True, True, True))


def test_probe_rejects_prefix_context_before_requests() -> None:
    try:
        context = recovery.RunContext.from_env(context_env(), "prefix7", EXECUTOR)
    except recovery.ProbeRefusalError as error:
        pytest.fail(f"Supported context refused before operation mismatch could be tested: {error}")
    api = PrefixAPI()
    with pytest.raises(recovery.ProbeRefusalError):
        recovery.Probe(api.manifest, context, api).run()
    assert api.calls == []


@pytest.mark.parametrize(
    "field",
    [
        "id",
        "run_attempt",
        "head_sha",
        "head_branch",
        "event",
        "path",
        "workflow_id",
        "actor",
        "triggering_actor",
        "repository",
        "status",
    ],
)
def test_current_run_identity_remains_required(field: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    api = PrefixAPI()
    api.fault = f"run:{field}"
    assert invoke(tmp_path, monkeypatch, api) == 1
    assert api.calls == [("GET", "/actions/runs/123", {})]
    assert_refused(tmp_path, api, (0, 0), facts=(False, False, False))


def test_workflow_prefix_artifact_is_stage_bound() -> None:
    workflow = yaml.safe_load((ROOT / ".github/workflows/specfact.yml").read_text())
    steps = workflow["jobs"]["probe"]["steps"]
    assert (
        steps[-1]["with"]["name"]
        == "pr785-${{ inputs.stage }}-${{ github.run_id }}-${{ github.run_attempt }}-${{ github.sha }}"
    )


@pytest.mark.parametrize("fault", ["count", "duplicate", "chain", "red-head", "red-tree", "final-head", "final-tree"])
def test_full_manifest_validation_survives_digest_boundary(
    fault: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    record = json.loads((ROOT / "ci/recovery/pr785-signing-inputs.json").read_text())
    source = record["source"]
    if fault == "count":
        source["commits"].pop()
    elif fault == "duplicate":
        source["commits"][8]["sha"] = source["commits"][7]["sha"]
    elif fault == "chain":
        source["commits"][8]["parents"] = [MAIN]
    else:
        key = {
            "red-head": "old_red_head",
            "red-tree": "old_red_tree",
            "final-head": "expected_old_head",
            "final-tree": "reviewed_final_tree",
        }[fault]
        source[key] = "f" * 40
    data = json.dumps(record).encode()
    path = tmp_path / "manifest.json"
    path.write_bytes(data)
    monkeypatch.setattr(recovery, "MANIFEST_SHA256", hashlib.sha256(data).hexdigest())
    with pytest.raises(recovery.ProbeRefusalError):
        recovery.Manifest.load(path)


@pytest.mark.parametrize("fault", ["open", "write", "TypeError", "ValueError"])
def test_final_evidence_failure_is_safe_exit(
    fault: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    api = FakeAPI(recovery.Manifest.load(ROOT / "ci/recovery/pr785-signing-inputs.json"))
    original_open = Path.open
    original_dumps = json.dumps

    class FailingWriter:
        def __init__(self, stream: Any) -> None:
            self.stream = stream

        def write(self, _text: str) -> int:
            self.stream.write("{")
            self.stream.flush()
            raise OSError("untrusted-secret")

    @contextmanager
    def failed_write(path: Path) -> Iterator[FailingWriter]:
        with original_open(path, "x", encoding="utf-8") as stream:
            yield FailingWriter(stream)

    def fail_open(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.name == "receipt.json" and args and args[0] == "x":
            if fault == "write":
                return failed_write(path)
            raise OSError("untrusted-secret")
        return original_open(path, *args, **kwargs)

    def fail_serialization(value: Any, *args: Any, **kwargs: Any) -> str:
        if isinstance(value, dict) and "status" in value and "manifest_digest" in value:
            raise {"TypeError": TypeError, "ValueError": ValueError}[fault]("untrusted-secret")
        return original_dumps(value, *args, **kwargs)

    if fault in ("open", "write"):
        monkeypatch.setattr(Path, "open", fail_open)
    else:
        monkeypatch.setattr(json, "dumps", fail_serialization)
    assert invoke(tmp_path, monkeypatch, api, stage="probe") == 1
    diagnostic = capsys.readouterr().err
    assert "untrusted-secret" not in diagnostic
    assert ("Local I/O failure" if fault in ("open", "write") else "Evidence serialization failed") in diagnostic
    path = tmp_path / "receipt.json"
    assert not path.exists() or path.read_text() in ("", "{")


@pytest.mark.parametrize("ordinal", range(1, 8))
def test_raw_persistence_failure_after_post_still_guards(
    ordinal: int, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    api = PrefixAPI()
    original_write = Path.write_bytes

    def fail_raw(path: Path, data: bytes) -> int:
        record = json.loads(data)
        if record.get("sha") == str(ordinal) * 40:
            raise OSError("untrusted-secret")
        return original_write(path, data)

    monkeypatch.setattr(Path, "write_bytes", fail_raw)
    assert invoke(tmp_path, monkeypatch, api) == 1
    assert_refused(tmp_path, api, (ordinal, ordinal - 1), facts=(True, True, True))
    last_post = max(i for i, (method, _, _) in enumerate(api.calls) if method == "POST")
    assert ("GET", "/git/ref/heads/main", {}) in api.calls[last_post + 1 :]
    assert "Local I/O failure" in capsys.readouterr().err


@pytest.mark.parametrize("field", list(context_env()))
def test_prefix_environment_is_bound_before_network(field: str) -> None:
    env = context_env()
    env[field] = "invalid"
    with pytest.raises(recovery.ProbeRefusalError) as error:
        recovery.RunContext.from_env(env, "prefix7", EXECUTOR)
    assert str(error.value) in ("Execution context mismatch", "Invalid run identity")


@pytest.mark.parametrize("label", list(ACCEPTED))
def test_transport_accepts_only_fixed_witness_refs(label: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    api = PrefixAPI()
    path = f"/git/ref/{anchor(label)}"
    calls: list[str] = []

    def respond(_opener: Any, request: urllib.request.Request, *args: Any, **kwargs: Any) -> BytesIO:
        calls.append(request.full_url)
        return BytesIO(json.dumps(api.refs[path]).encode())

    monkeypatch.setattr(urllib.request.OpenerDirector, "open", respond)
    try:
        result = recovery.GitHubAPI("never-sent", tmp_path).request("GET", path)
    except recovery.ProbeRefusalError as error:
        pytest.fail(f"Fixed accepted witness read refused: {error}")
    assert result == api.refs[path]
    assert calls == [f"https://api.github.com/repos/nold-ai/specfact-cli{path}"]


@pytest.mark.parametrize(
    "path",
    [
        "/git/ref/heads/codex/pr785-signing-recovery/arbitrary/probe-baseline",
        f"/git/ref/{anchor('baseline')}?other=1",
        "/actions/artifacts/12494410796/zip",
    ],
    ids=["arbitrary-anchor", "anchor-query", "artifact-zip"],
)
def test_transport_keeps_unapproved_evidence_routes_closed(
    path: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("Unapproved evidence route reached network")

    monkeypatch.setattr(urllib.request.OpenerDirector, "open", forbidden)
    with pytest.raises(recovery.ProbeRefusalError):
        recovery.GitHubAPI("never-sent", tmp_path).request("GET", path)


@pytest.mark.parametrize(
    "option", ["--range", "--source-head", "--probe-evidence", "--probe-success", "--run-id", "--accepted-probe"]
)
def test_prefix_cli_has_no_new_authority_inputs(option: str, tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as error:
        recovery.main(
            ["--stage", "prefix7", "--expected-executor", EXECUTOR, "--output", str(tmp_path), option, "arbitrary"]
        )
    assert error.value.code == 2
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("drift", ["main", "head"], ids=["main", "pr-head"])
def test_first_guard_is_fresh_after_seventh_source_read(
    drift: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    api = PrefixAPI()
    api.drift_after_sources = drift
    assert invoke(tmp_path, monkeypatch, api) == 1
    source_paths = [f"/git/commits/{source.sha}" for source in SOURCES]
    assert [path for method, path, _ in api.calls if method == "GET" and path in source_paths] == source_paths
    assert not [call for call in api.calls if call[0] == "POST"]
    last_source = api.calls.index(("GET", source_paths[-1], {}))
    guard_path = "/git/ref/heads/main" if drift == "main" else "/pulls/785"
    assert ("GET", guard_path, {}) in api.calls[last_source + 1 :]
    assert_refused(tmp_path, api, (0, 0), facts=(True, True, True))


@pytest.mark.parametrize("field", list(context_env()))
def test_prefix_cli_environment_refusal_has_distinct_journal(
    field: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    api = PrefixAPI()
    env = context_env()
    env[field] = "invalid"
    observed = expected_context()
    context_keys = {
        "GITHUB_RUN_ID": "run_id",
        "GITHUB_RUN_ATTEMPT": "run_attempt",
        "GITHUB_SHA": "executor_sha",
        "GITHUB_REPOSITORY": "repository",
        "GITHUB_ACTOR": "actor",
        "GITHUB_EVENT_NAME": "event",
        "GITHUB_REF": "ref",
    }
    if field in context_keys:
        observed[context_keys[field]] = 0 if field in ("GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT") else "invalid"
    assert invoke(tmp_path, monkeypatch, api, environment=env) == 1
    assert api.calls == []
    assert_refused(tmp_path, api, (0, 0), facts=(False, False, False), context=observed)

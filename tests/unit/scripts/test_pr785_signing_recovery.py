from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import urllib.error
import urllib.request
from collections.abc import Mapping
from dataclasses import replace
from email.message import Message
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
import yaml


if TYPE_CHECKING:
    from scripts.pr785_signing_recovery import Manifest, RunContext


JSONValue = str | int | float | bool | None | list["JSONValue"] | dict[str, "JSONValue"]
ROOT = Path(__file__).resolve().parents[3]
PREPARED_TREES = {
    "root": "4b2cf05809c1cf687e4eae17a770cd33c97eff72",
    "github": "6c8d9363427fb97b00eae0a452dab167ba41b8a4",
    "workflows": "f0a1368e6f068ece5c3b1f1bb9264720778af6bd",
}
PREPARED_BLOB = "c00d710f49c952dee0ef3886acf476c7e49e0a8e"
SERVICE_IDENTITIES: dict[str, dict[str, str | int]] = {
    "author": {
        "name": "github-actions[bot]",
        "email": "41898282+github-actions[bot]@users.noreply.github.com",
        "login": "github-actions[bot]",
        "id": 41898282,
        "type": "Bot",
    },
    "committer": {
        "name": "GitHub",
        "email": "noreply@github.com",
        "login": "web-flow",
        "id": 19864447,
        "type": "User",
    },
}


def test_executor_is_dispatch_only() -> None:
    workflow = yaml.safe_load((ROOT / ".github/workflows/specfact.yml").read_text())
    triggers = workflow.get("on", workflow.get(True))
    assert set(triggers) == {"workflow_dispatch"}
    assert set(workflow["jobs"]) == {"probe"}
    assert workflow.get("permissions") == {}
    assert workflow["jobs"]["probe"]["permissions"] == {"contents": "write", "actions": "read", "pull-requests": "read"}


def test_probe_api_contract() -> None:
    from scripts.pr785_signing_recovery import Manifest, Probe, RunContext

    manifest = Manifest.load(ROOT / "ci/recovery/pr785-signing-inputs.json")
    api = FakeAPI(manifest)
    receipt = Probe(manifest, context(), api).run()
    assert receipt["status"] == "signed_objects_verified"
    assert_unverified_anchors(receipt)
    assert len(receipt["objects"]) == 2
    assert_bounded_object_writes(api, manifest)
    assert RunContext.from_env(context_env(), "probe", "a" * 40) == context()


def context_env() -> dict[str, str]:
    return {
        "GITHUB_ACTIONS": "true",
        "GITHUB_REPOSITORY": "nold-ai/specfact-cli",
        "GITHUB_ACTOR": "djm81",
        "GITHUB_TRIGGERING_ACTOR": "djm81",
        "GITHUB_EVENT_NAME": "workflow_dispatch",
        "GITHUB_REF": "refs/heads/codex/pr785-ci-signing-recovery",
        "GITHUB_SHA": "a" * 40,
        "GITHUB_WORKFLOW_SHA": "a" * 40,
        "GITHUB_WORKFLOW_REF": "nold-ai/specfact-cli/.github/workflows/specfact.yml@refs/heads/codex/pr785-ci-signing-recovery",
        "GITHUB_RUN_ID": "123",
        "GITHUB_RUN_ATTEMPT": "1",
        "GITHUB_SERVER_URL": "https://github.com",
        "GITHUB_API_URL": "https://api.github.com",
    }


def context() -> RunContext:
    from scripts.pr785_signing_recovery import RunContext

    return RunContext.from_env(context_env(), "probe", "a" * 40)


class FakeAPI:
    def __init__(self, manifest: Manifest, fault: str = "", drift_after: int = -1) -> None:
        self.manifest = manifest
        self.fault = fault
        self.drift_after = drift_after
        self.calls: list[tuple[str, str, dict[str, Any]]] = []
        self.objects: dict[str, dict[str, Any]] = {}
        self.writes = 0
        self.prepared = prepared_responses()
        self.drift_after_prepared = False

    def request(self, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        self.calls.append((method, path, body or {}))
        read_routes = {
            "/actions/runs/123": self.workflow_run,
            "/git/ref/heads/main": self.main_ref,
            "/pulls/785": self.pull_request,
        }
        if path in read_routes:
            return read_routes[path]()
        if method == "GET" and path.startswith("/git/trees/"):
            return self.prepared_tree(path.rsplit("/", 1)[1])
        if method == "POST":
            self.writes += 1
            if path == "/git/trees":
                return {"sha": self.manifest.probe_tree}
            assert path == "/git/commits"
            assert body is not None
            return self.create_commit(body)
        if path.startswith("/git/commits/"):
            return self.read_commit(path.rsplit("/", 1)[1])
        if path.startswith("/commits/"):
            return self.commit_attribution(path.rsplit("/", 1)[1])
        raise AssertionError((method, path, body))

    def prepared_tree(self, sha: str) -> dict[str, Any]:
        from scripts.pr785_signing_recovery import ProbeRefusalError

        if self.fault == f"unavailable:{sha}":
            raise ProbeRefusalError("API refused HTTP 404")
        result = copy.deepcopy(self.prepared[sha])
        if self.fault == "tree_response" and sha == PREPARED_TREES["root"]:
            result["sha"] = "f" * 40
        return result

    def workflow_run(self) -> dict[str, Any]:
        run: dict[str, Any] = {
            "id": 123,
            "run_attempt": 1,
            "head_sha": "a" * 40,
            "head_branch": "codex/pr785-ci-signing-recovery",
            "event": "workflow_dispatch",
            "path": ".github/workflows/specfact.yml",
            "workflow_id": 204352514,
            "actor": {"login": "djm81"},
            "triggering_actor": {"login": "djm81"},
            "repository": {"full_name": "nold-ai/specfact-cli"},
            "status": "in_progress",
        }
        if self.fault.startswith("run:"):
            run[self.fault[4:]] = "invalid"
        return run

    def main_ref(self) -> dict[str, Any]:
        sha = "f" * 40 if self.fault == "main" or self.writes == self.drift_after else self.manifest.main
        prepared_reads = [path for method, path, _ in self.calls if method == "GET" and path.startswith("/git/trees/")]
        if self.drift_after_prepared and len(prepared_reads) == 3:
            sha = "f" * 40
        return {"object": {"sha": sha}}

    def pull_request(self) -> dict[str, Any]:
        manifest = self.manifest
        pr: dict[str, Any] = {
            "state": "open",
            "merged": False,
            "auto_merge": None,
            "head": {"sha": manifest.old_head, "ref": manifest.branch, "repo": {"full_name": manifest.repository}},
            "base": {"sha": manifest.main, "ref": "main", "repo": {"full_name": manifest.repository}},
        }
        state_faults: dict[str, dict[str, JSONValue]] = {
            "auto_merge": {"auto_merge": {"enabled_by": {"login": "djm81"}}},
            "closed": {"state": "closed"},
            "merged": {"merged": True},
        }
        pr.update(state_faults.get(self.fault, {}))
        ref_faults = {
            "head": ("head", "sha", "f" * 40),
            "base-sha": ("base", "sha", "f" * 40),
            "base-ref": ("base", "ref", "other-branch"),
            "head-ref": ("head", "ref", "other-branch"),
            "base-repo": ("base", "repo", {"full_name": "other/repository"}),
            "head-repo": ("head", "repo", {"full_name": "other/repository"}),
        }
        if self.fault in ref_faults:
            side, field, value = ref_faults[self.fault]
            pr[side][field] = value
        return pr

    def create_commit(self, body: dict[str, Any]) -> dict[str, Any]:
        manifest = self.manifest
        sha = str(self.writes) * 40
        payload = f"tree {body['tree']}\nparent {manifest.main}\nauthor github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com> 1 +0000\ncommitter GitHub <noreply@github.com> 1 +0000\n\n{body['message']}"
        result: dict[str, Any] = {
            "sha": sha,
            "tree": {"sha": body["tree"]},
            "parents": [{"sha": manifest.main}],
            "message": body["message"],
            "author": {
                "name": "github-actions[bot]",
                "email": "41898282+github-actions[bot]@users.noreply.github.com",
            },
            "committer": {"name": "GitHub", "email": "noreply@github.com"},
            "verification": {"verified": True, "reason": "valid", "signature": "signature", "payload": payload},
        }
        object_faults: dict[str, dict[str, JSONValue]] = {
            "tree": {"tree": {"sha": "f" * 40}},
            "parent": {"parents": [{"sha": "f" * 40}]},
            "message": {"message": "wrong"},
        }
        verification_faults: dict[str, dict[str, JSONValue]] = {
            "unsigned": {"verified": False},
            "reason": {"reason": "unknown_key"},
            "signature": {"signature": ""},
            "payload": {"payload": "wrong"},
        }
        result.update(object_faults.get(self.fault, {}))
        result["verification"].update(verification_faults.get(self.fault, {}))
        self.corrupt_identity(result, "create")
        self.objects[sha] = copy.deepcopy(result)
        return result

    def read_commit(self, sha: str) -> dict[str, Any]:
        result = copy.deepcopy(self.objects[sha])
        if self.fault == "readback":
            result["sha"] = "f" * 40
        self.corrupt_identity(result, "readback")
        return result

    def commit_attribution(self, sha: str) -> dict[str, Any]:
        result: dict[str, Any] = {
            "sha": sha,
            "author": {
                "login": "wrong" if self.fault == "bot" else "github-actions[bot]",
                "id": 41898282,
                "type": "Bot",
            },
            "committer": {"login": "web-flow", "id": 19864447, "type": "User"},
        }
        self.corrupt_identity(result, "attribution")
        return result

    def corrupt_identity(self, result: dict[str, Any], surface: str) -> None:
        parts = self.fault.split(":")
        if len(parts) != 4 or parts[0] != surface:
            return
        _, representation, role, field = parts
        opposite = "committer" if role == "author" else "author"
        replacement = SERVICE_IDENTITIES[opposite][field]
        if representation == "metadata":
            result[role][field] = replacement
            return
        identity = SERVICE_IDENTITIES[role]
        changed = {**identity, field: replacement}
        result["verification"]["payload"] = result["verification"]["payload"].replace(
            f"{role} {identity['name']} <{identity['email']}>",
            f"{role} {changed['name']} <{changed['email']}>",
        )


@pytest.mark.parametrize("field", list(context_env()))
def test_context_refusal_precedes_api(field: str) -> None:
    from scripts.pr785_signing_recovery import ProbeRefusalError, RunContext

    env = context_env()
    env[field] = "invalid"
    with pytest.raises(ProbeRefusalError):
        RunContext.from_env(env, "probe", "a" * 40)


@pytest.mark.parametrize(
    "stage",
    ["prefix7", "advisory9", "final10", "", "probe;echo"],
    ids=["prefix7", "advisory9", "final10", "empty-stage", "shell-stage"],
)
def test_only_probe_is_implemented(stage: str) -> None:
    from scripts.pr785_signing_recovery import ProbeRefusalError, RunContext

    if stage == "prefix7":
        try:
            supported = RunContext.from_env(context_env(), stage, "a" * 40)
        except ProbeRefusalError as error:
            pytest.fail(f"Authorized Prefix7 context refused: {error}")
        assert getattr(supported, "stage", None) == "prefix7"
        return
    with pytest.raises(ProbeRefusalError):
        RunContext.from_env(context_env(), stage, "a" * 40)


@pytest.mark.parametrize(
    "fault",
    [
        "main",
        "head",
        "auto_merge",
        "closed",
        "merged",
        "base-sha",
        "base-ref",
        "head-ref",
        "base-repo",
        "head-repo",
        "run:id",
        "run:event",
        "run:repository",
        "run:head_branch",
        "run:triggering_actor",
        "run:status",
        "run:actor",
        "run:head_sha",
        "run:run_attempt",
        "run:workflow_id",
        "run:path",
    ],
)
def test_preflight_refuses_before_writes(fault: str) -> None:
    from scripts.pr785_signing_recovery import Manifest, Probe, ProbeRefusalError

    manifest = Manifest.load(ROOT / "ci/recovery/pr785-signing-inputs.json")
    api = FakeAPI(manifest, fault)
    with pytest.raises(ProbeRefusalError):
        Probe(manifest, context(), api).run()
    assert api.writes == 0


@pytest.mark.parametrize(
    "fault",
    ["tree", "parent", "message", "unsigned", "reason", "signature", "payload", "bot", "readback", "tree_response"],
)
def test_invalid_object_stops_subsequent_writes(fault: str) -> None:
    from scripts.pr785_signing_recovery import Manifest, Probe, ProbeRefusalError

    manifest = Manifest.load(ROOT / "ci/recovery/pr785-signing-inputs.json")
    api = FakeAPI(manifest, fault)
    with pytest.raises(ProbeRefusalError):
        Probe(manifest, context(), api).run()
    assert api.writes == (0 if fault == "tree_response" else 1)


@pytest.mark.parametrize("surface", ["create", "readback"])
@pytest.mark.parametrize("representation", ["metadata", "payload"])
@pytest.mark.parametrize("role", ["author", "committer"])
@pytest.mark.parametrize("field", ["name", "email"])
def test_git_role_mismatch_stops_subsequent_writes(surface: str, representation: str, role: str, field: str) -> None:
    from scripts.pr785_signing_recovery import Manifest, Probe, ProbeRefusalError

    manifest = Manifest.load(ROOT / "ci/recovery/pr785-signing-inputs.json")
    api = FakeAPI(manifest, f"{surface}:{representation}:{role}:{field}")
    with pytest.raises(ProbeRefusalError):
        Probe(manifest, context(), api).run()
    assert api.writes == 1


@pytest.mark.parametrize("role", ["author", "committer"])
@pytest.mark.parametrize("field", ["login", "id", "type"])
def test_service_role_mismatch_stops_subsequent_writes(role: str, field: str) -> None:
    from scripts.pr785_signing_recovery import Manifest, Probe, ProbeRefusalError

    manifest = Manifest.load(ROOT / "ci/recovery/pr785-signing-inputs.json")
    api = FakeAPI(manifest, f"attribution:metadata:{role}:{field}")
    with pytest.raises(ProbeRefusalError):
        Probe(manifest, context(), api).run()
    assert api.writes == 1


@pytest.mark.parametrize("after", [1, 2])
def test_drift_after_each_write_stops(after: int) -> None:
    from scripts.pr785_signing_recovery import Manifest, Probe, ProbeRefusalError

    manifest = Manifest.load(ROOT / "ci/recovery/pr785-signing-inputs.json")
    api = FakeAPI(manifest, drift_after=after)
    with pytest.raises(ProbeRefusalError):
        Probe(manifest, context(), api).run()
    assert api.writes == after


def test_manifest_tampering_refuses(tmp_path: Path) -> None:
    from scripts.pr785_signing_recovery import Manifest, ProbeRefusalError

    data = json.loads((ROOT / "ci/recovery/pr785-signing-inputs.json").read_text())
    data["source"]["commits"][0]["tree"] = "f" * 40
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(data))
    with pytest.raises(ProbeRefusalError):
        Manifest.load(path)


@pytest.mark.parametrize(
    "method,path",
    [
        ("POST", "/git/refs"),
        ("PATCH", "/git/refs/heads/main"),
        ("DELETE", "/git/refs/heads/main"),
        ("GET", "https://evil.invalid"),
        ("GET", "/../secrets"),
        ("POST", "/git/commits?other=1"),
    ],
    ids=["post-ref", "patch-main-ref", "delete-main-ref", "external-url", "parent-path", "commit-query"],
)
def test_transport_rejects_forbidden_endpoints(
    method: str, path: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from scripts.pr785_signing_recovery import GitHubAPI, ProbeRefusalError

    def forbidden_network(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("Forbidden endpoint reached the network")

    monkeypatch.setattr(urllib.request.OpenerDirector, "open", forbidden_network)
    with pytest.raises(ProbeRefusalError):
        GitHubAPI("never-sent", tmp_path).request(method, path)


def test_workflow_has_only_bounded_steps_and_pinned_actions() -> None:
    workflow = yaml.safe_load((ROOT / ".github/workflows/specfact.yml").read_text())
    inputs = workflow.get("on", workflow.get(True))["workflow_dispatch"]["inputs"]
    assert set(inputs) == {"stage", "expected_executor"}
    assert inputs["stage"]["options"] == ["probe", "prefix7"]
    assert inputs["stage"]["default"] == "probe"
    assert inputs["expected_executor"]["required"] is True
    job = workflow["jobs"]["probe"]
    assert not {"environment", "secrets"}.intersection(job)
    steps = job["steps"]
    assert len(steps) == 4
    assert [step.get("uses") for step in steps if "uses" in step] == [
        "actions/checkout@df4cb1c069e1874edd31b4311f1884172cec0e10",
        "actions/setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405",
        "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a",
    ]
    assert_bound_probe_execution(steps)
    assert_bound_artifact_upload(steps[-1])
    text = (ROOT / ".github/workflows/specfact.yml").read_text()
    assert all(forbidden not in text for forbidden in ("secrets.", "id-token"))
    assert "module" not in text.lower()


def test_expected_executor_must_equal_actual_workflow_sha() -> None:
    from scripts.pr785_signing_recovery import ProbeRefusalError, RunContext

    with pytest.raises(ProbeRefusalError):
        RunContext.from_env(context_env(), "probe", "b" * 40)


def test_complete_source_manifest_and_probe_bytes_are_frozen() -> None:
    from scripts.pr785_signing_recovery import MANIFEST_SHA256, Manifest

    path = ROOT / "ci/recovery/pr785-signing-inputs.json"
    data = json.loads(path.read_text())
    original = json.dumps(data["source"], sort_keys=True, separators=(",", ":")).encode()
    assert hashlib.sha256(original).hexdigest() == "8b11607cf78ad8c065e54dd2f83b4c6103ec8da0e362028162f139e450681389"
    assert len(data["source"]["commits"]) == 10
    manifest = Manifest.load(path)
    assert manifest.probe_path == ".github/workflows/pr785-inert-probe.yml"
    assert manifest.probe_content == (ROOT / "ci/recovery/pr785-inert-probe.txt").read_text()
    assert (manifest.main_tree, manifest.probe_tree) == (
        "4c9ba46b2ace65cd8df0fcd5a77c2b14a42f599c",
        "4b2cf05809c1cf687e4eae17a770cd33c97eff72",
    )
    assert manifest.probe_content == (
        "name: PR785 inert signing probe\non:\n  workflow_dispatch:\npermissions:\n  contents: read\n"
        'jobs:\n  inert:\n    runs-on: ubuntu-24.04\n    steps:\n      - run: "true"\n'
    )
    assert hashlib.sha256(path.read_bytes()).hexdigest() == MANIFEST_SHA256
    workflow = yaml.safe_load((ROOT / ".github/workflows/specfact.yml").read_text())
    step = next(step for step in workflow["jobs"]["probe"]["steps"] if "run" in step)
    assert step["env"]["EXPECTED_MANIFEST_SHA256"] == MANIFEST_SHA256
    assert_inert_workflow(manifest.probe_content)


def test_api_error_body_and_token_are_not_persisted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.pr785_signing_recovery import GitHubAPI, ProbeRefusalError

    credential_marker = "unique-secret-never-in-evidence"

    def reject(*args: Any, **kwargs: Any) -> Any:
        raise urllib.error.HTTPError(
            "https://api.github.com", 403, "Forbidden", Message(), BytesIO(credential_marker.encode())
        )

    monkeypatch.setattr(urllib.request.OpenerDirector, "open", reject)
    with pytest.raises(ProbeRefusalError) as error:
        GitHubAPI(credential_marker, tmp_path).request("GET", "/git/ref/heads/main")
    assert credential_marker not in str(error.value)
    assert all(credential_marker not in path.read_text() for path in tmp_path.rglob("*") if path.is_file())


def test_context_failure_still_writes_refusal_receipt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.pr785_signing_recovery import MANIFEST_SHA256, main

    for key, value in context_env().items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("EXPECTED_MANIFEST_SHA256", MANIFEST_SHA256)
    monkeypatch.setenv("GITHUB_ACTOR", "forbidden")
    monkeypatch.setenv("GH_TOKEN", "unique-secret-never-in-evidence")

    def forbidden_network(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("Invalid context reached the network")

    monkeypatch.setattr(urllib.request.OpenerDirector, "open", forbidden_network)
    assert main(["--stage", "probe", "--expected-executor", "a" * 40, "--output", str(tmp_path)]) == 1
    receipt = json.loads((tmp_path / "receipt.json").read_text())
    assert receipt["status"] == "refused"
    assert receipt["objects"] == []
    assert receipt["context_verified"] is False
    assert_receipt_execution_identity(receipt)
    assert receipt["manifest_digest"] == MANIFEST_SHA256
    assert receipt["root_anchor_verified"] is False
    assert "unique-secret-never-in-evidence" not in json.dumps(receipt)


def run_probe_cli(
    output: Path, monkeypatch: pytest.MonkeyPatch, *, refuse_second_commit: bool = False, refuse_prepared_tree: str = ""
) -> tuple[int, FakeAPI, list[dict[str, Any]]]:
    from scripts.pr785_signing_recovery import MANIFEST_SHA256, Manifest, main

    for key, value in context_env().items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("GH_TOKEN", "unique-secret-never-in-evidence")
    monkeypatch.setenv("EXPECTED_MANIFEST_SHA256", MANIFEST_SHA256)
    api = FakeAPI(Manifest.load(ROOT / "ci/recovery/pr785-signing-inputs.json"))
    responses: list[dict[str, Any]] = []

    def respond(_opener: Any, request: urllib.request.Request, *args: Any, **kwargs: Any) -> BytesIO:
        assert request.full_url.startswith("https://api.github.com/repos/nold-ai/specfact-cli/")
        path = request.full_url.removeprefix("https://api.github.com/repos/nold-ai/specfact-cli")
        if refuse_second_commit and request.get_method() == "POST" and path == "/git/commits" and api.objects:
            raise urllib.error.HTTPError(
                request.full_url, 403, "Forbidden", Message(), BytesIO(b"unique-secret-never-in-evidence")
            )
        if request.get_method() == "GET" and path == f"/git/trees/{refuse_prepared_tree}":
            raise urllib.error.HTTPError(
                request.full_url, 404, "Not Found", Message(), BytesIO(b"unique-secret-never-in-evidence")
            )
        data = request.data
        assert data is None or isinstance(data, bytes)
        body = json.loads(data) if data is not None else None
        result = api.request(request.get_method(), path, body)
        responses.append(copy.deepcopy(result))
        return BytesIO(json.dumps(result).encode())

    monkeypatch.setattr(urllib.request.OpenerDirector, "open", respond)
    exit_code = main(["--stage", "probe", "--expected-executor", "a" * 40, "--output", str(output)])
    return exit_code, api, responses


def test_success_persists_bound_receipt_and_raw_responses(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.pr785_signing_recovery import MANIFEST_SHA256

    exit_code, api, responses = run_probe_cli(tmp_path, monkeypatch)
    assert exit_code == 0
    receipt = json.loads((tmp_path / "receipt.json").read_text())
    assert receipt["status"] == "signed_objects_verified"
    assert receipt["manifest_digest"] == MANIFEST_SHA256
    assert receipt["context_verified"] is True
    assert receipt["context"] == {
        "run_id": 123,
        "run_attempt": 1,
        "executor_sha": "a" * 40,
        "repository": "nold-ai/specfact-cli",
        "actor": "djm81",
        "event": "workflow_dispatch",
        "ref": "refs/heads/codex/pr785-ci-signing-recovery",
        "workflow_id": 204352514,
        "workflow_path": ".github/workflows/specfact.yml",
    }
    assert_unverified_anchors(receipt)
    assert len(receipt["objects"]) == 2
    assert all(item["signed_object_verified"] is True for item in receipt["objects"])
    assert {item["sha"] for item in receipt["objects"]} == set(api.objects)
    raw = assert_persisted_responses(tmp_path, responses)
    assert any(item.get("id") == 123 for item in raw)
    assert any(item.get("verification", {}).get("verified") is True for item in raw)


def test_later_refusal_preserves_bound_receipt_and_successful_raw_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from scripts.pr785_signing_recovery import MANIFEST_SHA256

    exit_code, api, responses = run_probe_cli(tmp_path, monkeypatch, refuse_second_commit=True)
    assert exit_code == 1
    assert api.writes == 1
    receipt = json.loads((tmp_path / "receipt.json").read_text())
    assert receipt["status"] == "refused"
    assert receipt["manifest_digest"] == MANIFEST_SHA256
    assert receipt["context_verified"] is True
    assert_receipt_execution_identity(receipt)
    assert_unverified_anchors(receipt)
    assert len(receipt["objects"]) == 1
    assert receipt["objects"][0]["signed_object_verified"] is True
    assert receipt["objects"][0]["sha"] in api.objects
    raw = assert_persisted_responses(tmp_path, responses)
    assert any(item.get("verification", {}).get("verified") is True for item in raw)


def assert_unverified_anchors(receipt: Mapping[str, object]) -> None:
    assert receipt["ci_anchor_verified"] is False
    assert receipt["root_anchor_verified"] is False


def assert_receipt_execution_identity(receipt: dict[str, Any]) -> None:
    assert {key: receipt["context"][key] for key in ("run_id", "run_attempt", "executor_sha")} == {
        "run_id": 123,
        "run_attempt": 1,
        "executor_sha": "a" * 40,
    }


def assert_bound_artifact_upload(step: dict[str, Any]) -> None:
    assert step["if"] == "always()"
    assert all(part in step["with"]["name"] for part in ("github.run_id", "github.run_attempt", "github.sha"))


def assert_persisted_responses(output: Path, responses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    raw = [json.loads(path.read_text()) for path in sorted((output / "raw").glob("*.json"))]
    assert raw == responses
    assert "unique-secret-never-in-evidence" not in "".join(path.read_text() for path in output.rglob("*.json"))
    return raw


def assert_bound_probe_execution(steps: list[dict[str, Any]]) -> None:
    assert steps[0]["with"]["persist-credentials"] is False
    assert steps[0]["with"]["ref"] == "${{ github.sha }}"
    execution = next(step for step in steps if "run" in step)
    assert "python scripts/pr785_signing_recovery.py" in execution["run"]
    assert "${{" not in execution["run"]
    assert execution["env"]["GH_TOKEN"] == "${{ github.token }}"


def assert_bounded_object_writes(api: FakeAPI, manifest: Manifest) -> None:
    writes = [(path, body) for method, path, body in api.calls if method != "GET"]
    assert [path for path, _ in writes] == ["/git/commits", "/git/commits"]
    assert [body["tree"] for _, body in writes] == [manifest.main_tree, manifest.probe_tree]
    for _, body in writes:
        assert set(body) == {"message", "tree", "parents"}
        assert body["parents"] == [manifest.main]
    assert_prepared_reads_before_writes(api)


def assert_prepared_reads_before_writes(api: FakeAPI) -> None:
    reads = [(method, path) for method, path, _ in api.calls if path.startswith("/git/trees/")]
    expected = [("GET", f"/git/trees/{sha}") for sha in PREPARED_TREES.values()]
    assert reads == expected
    first_write = next(i for i, (method, _, _) in enumerate(api.calls) if method == "POST")
    assert all((method, path, {}) in api.calls[:first_write] for method, path in expected)


def assert_inert_workflow(content: str) -> None:
    inert = yaml.safe_load(content)
    assert set(inert.get("on", inert.get(True))) == {"workflow_dispatch"}
    assert inert["permissions"] == {"contents": "read"}
    assert len(inert["jobs"]) == 1
    assert next(iter(inert["jobs"].values()))["steps"] == [{"run": "true"}]


def test_cli_reports_sanitized_http_refusal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code, api, responses = run_probe_cli(tmp_path, monkeypatch, refuse_second_commit=True)
    captured = capsys.readouterr()
    assert exit_code == 1
    assert api.writes == 1
    assert_persisted_responses(tmp_path, responses)
    receipt = json.loads((tmp_path / "receipt.json").read_text())
    assert receipt["status"] == "refused"
    assert len(receipt["objects"]) == 1
    assert_unverified_anchors(receipt)
    assert captured.out == ""
    assert "unique-secret-never-in-evidence" not in captured.err
    assert "Forbidden" not in captured.err
    assert "Traceback" not in captured.err
    assert "API refused HTTP 403" in captured.err


def test_cli_reports_context_policy_refusal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from scripts.pr785_signing_recovery import MANIFEST_SHA256, main

    for key, value in context_env().items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("EXPECTED_MANIFEST_SHA256", MANIFEST_SHA256)
    monkeypatch.setenv("GITHUB_ACTOR", "forbidden")
    monkeypatch.setenv("GH_TOKEN", "unique-secret-never-in-evidence")

    def forbidden_network(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("Invalid context reached the network")

    monkeypatch.setattr(urllib.request.OpenerDirector, "open", forbidden_network)
    assert main(["--stage", "probe", "--expected-executor", "a" * 40, "--output", str(tmp_path)]) == 1
    captured = capsys.readouterr()
    receipt = json.loads((tmp_path / "receipt.json").read_text())
    assert receipt["status"] == "refused"
    assert receipt["context_verified"] is False
    assert receipt["objects"] == []
    assert_unverified_anchors(receipt)
    assert not (tmp_path / "raw").exists()
    assert "unique-secret-never-in-evidence" not in json.dumps(receipt) + captured.out + captured.err
    assert captured.out == ""
    assert "Traceback" not in captured.err
    assert "Execution context mismatch" in captured.err


def test_cli_reports_generic_local_io_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def refuse_raw_write(path: Path, data: bytes) -> int:
        raise OSError("local-error-body-never-in-evidence unique-secret-never-in-evidence")

    monkeypatch.setattr(Path, "write_bytes", refuse_raw_write)
    exit_code, api, responses = run_probe_cli(tmp_path, monkeypatch)
    captured = capsys.readouterr()
    assert exit_code == 1
    assert api.writes == 0
    assert len(responses) == 1
    assert not list((tmp_path / "raw").iterdir())
    receipt = json.loads((tmp_path / "receipt.json").read_text())
    assert receipt["status"] == "refused"
    assert receipt["objects"] == []
    assert_unverified_anchors(receipt)
    persisted = (tmp_path / "receipt.json").read_text()
    assert "unique-secret-never-in-evidence" not in persisted + captured.out + captured.err
    assert "local-error-body-never-in-evidence" not in persisted + captured.out + captured.err
    assert captured.out == ""
    assert captured.err == "Probe refused: Local I/O failure\n"


def prepared_responses() -> dict[str, dict[str, Any]]:
    children = {
        "root": (".github", "040000", "tree", PREPARED_TREES["github"]),
        "github": ("workflows", "040000", "tree", PREPARED_TREES["workflows"]),
        "workflows": ("pr785-inert-probe.yml", "100644", "blob", PREPARED_BLOB),
    }
    return {
        PREPARED_TREES[level]: {
            "sha": PREPARED_TREES[level],
            "truncated": False,
            "tree": [dict(zip(("path", "mode", "type", "sha"), entry, strict=True))],
        }
        for level, entry in children.items()
    }


def corrupt_prepared_response(record: dict[str, Any], fault: str) -> None:
    response_faults: dict[str, dict[str, Any]] = {
        "wrong-sha": {"sha": "f" * 40},
        "malformed-sha": {"sha": 7},
        "truncated": {"truncated": True},
        "false-integer": {"truncated": 0},
        "false-string": {"truncated": "false"},
        "malformed-list": {"tree": {}},
        "malformed-entry": {"tree": [None]},
        "missing-child": {"tree": []},
    }
    if fault in response_faults:
        record.update(response_faults[fault])
    elif fault == "missing-truncated":
        del record["truncated"]
    else:
        corrupt_prepared_entry(record, fault)


def corrupt_prepared_entry(record: dict[str, Any], fault: str) -> None:
    entry = record["tree"][0]
    fields: dict[str, dict[str, Any]] = {
        "wrong-child": {"sha": "f" * 40},
        "wrong-type": {"type": "commit"},
        "wrong-mode": {"mode": "100755"},
        "nested-path": {"path": ".github/workflows/pr785-inert-probe.yml"},
        "non-string-path": {"path": 1},
        "malformed-child-sha": {"sha": "bad"},
    }
    if fault in fields:
        entry.update(fields[fault])
        return
    if fault == "missing-entry-field":
        del entry["type"]
        return
    if fault == "duplicate-child":
        record["tree"].append(copy.deepcopy(entry))
        return
    if fault == "malformed-unrelated-entry":
        record["tree"].append({"path": "other", "mode": "100644", "type": "tree", "sha": "d" * 40})
        return
    raise AssertionError(f"Unknown prepared fault {fault}")


@pytest.mark.parametrize("level", ["root", "github", "workflows"])
@pytest.mark.parametrize(
    "fault",
    [
        "unavailable",
        "wrong-sha",
        "malformed-sha",
        "truncated",
        "false-integer",
        "false-string",
        "missing-truncated",
        "malformed-list",
        "malformed-entry",
        "missing-child",
        "wrong-child",
        "wrong-type",
        "wrong-mode",
        "nested-path",
        "non-string-path",
        "malformed-child-sha",
        "missing-entry-field",
        "duplicate-child",
        "malformed-unrelated-entry",
    ],
)
def test_prepared_tree_refusal_precedes_either_commit(level: str, fault: str) -> None:
    from scripts.pr785_signing_recovery import Manifest, Probe, ProbeRefusalError

    manifest = Manifest.load(ROOT / "ci/recovery/pr785-signing-inputs.json")
    api = FakeAPI(manifest)
    sha = PREPARED_TREES[level]
    if fault == "unavailable":
        api.fault = f"unavailable:{sha}"
    else:
        corrupt_prepared_response(api.prepared[sha], fault)
    probe = Probe(manifest, context(), api)
    with pytest.raises(ProbeRefusalError):
        probe.run()
    assert api.writes == 0
    assert probe.receipt["status"] == "refused"
    assert probe.receipt["objects"] == []
    assert_unverified_anchors(probe.receipt)


def test_drift_after_prepared_reads_stops() -> None:
    from scripts.pr785_signing_recovery import Manifest, Probe, ProbeRefusalError

    api = FakeAPI(Manifest.load(ROOT / "ci/recovery/pr785-signing-inputs.json"))
    api.drift_after_prepared = True
    with pytest.raises(ProbeRefusalError):
        Probe(api.manifest, context(), api).run()
    assert api.writes == 0


def test_prepared_blob_identity_is_derived_from_manifest_bytes() -> None:
    from scripts.pr785_signing_recovery import Manifest

    manifest = Manifest.load(ROOT / "ci/recovery/pr785-signing-inputs.json")
    content = manifest.probe_content.encode()
    result = subprocess.run(["git", "hash-object", "--stdin"], input=content, check=True, capture_output=True, cwd=ROOT)
    assert result.stdout.decode().strip() == PREPARED_BLOB


def test_prepared_blob_must_match_manifest_content_before_either_commit() -> None:
    from scripts.pr785_signing_recovery import Manifest, Probe, ProbeRefusalError

    original = Manifest.load(ROOT / "ci/recovery/pr785-signing-inputs.json")
    manifest = replace(original, probe_content=original.probe_content + "\n")
    api = FakeAPI(manifest)
    probe = Probe(manifest, context(), api)
    with pytest.raises(ProbeRefusalError):
        probe.run()
    assert api.writes == 0
    assert probe.receipt["status"] == "refused"
    assert probe.receipt["objects"] == []
    assert_unverified_anchors(probe.receipt)


def test_transport_refuses_tree_creation_before_network(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.pr785_signing_recovery import GitHubAPI, ProbeRefusalError

    calls: list[str] = []

    def respond(_opener: Any, request: urllib.request.Request, *args: Any, **kwargs: Any) -> BytesIO:
        calls.append(request.full_url)
        return BytesIO(b"{}")

    monkeypatch.setattr(urllib.request.OpenerDirector, "open", respond)
    with pytest.raises(ProbeRefusalError):
        GitHubAPI("never-sent", tmp_path).request("POST", "/git/trees", {})
    assert calls == []


@pytest.mark.parametrize("level", ["root", "github", "workflows"])
def test_transport_reads_exact_prepared_tree(level: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.pr785_signing_recovery import GitHubAPI, ProbeRefusalError

    sha = PREPARED_TREES[level]
    expected = prepared_responses()[sha]
    calls: list[str] = []

    def respond(_opener: Any, request: urllib.request.Request, *args: Any, **kwargs: Any) -> BytesIO:
        calls.append(request.full_url)
        assert request.get_method() == "GET"
        assert request.data is None
        return BytesIO(json.dumps(expected).encode())

    monkeypatch.setattr(urllib.request.OpenerDirector, "open", respond)
    try:
        result = GitHubAPI("never-sent", tmp_path).request("GET", f"/git/trees/{sha}")
    except ProbeRefusalError as error:
        pytest.fail(f"Pinned prepared tree GET was refused: {error}")
    assert result == expected
    assert calls == [f"https://api.github.com/repos/nold-ai/specfact-cli/git/trees/{sha}"]


@pytest.mark.parametrize(
    "path",
    [f"/git/trees/{'f' * 40}", f"/git/trees/{PREPARED_TREES['root']}?recursive=1"],
    ids=["arbitrary-tree", "recursive-tree"],
)
def test_transport_rejects_unpinned_tree_reads(path: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    test_transport_rejects_forbidden_endpoints("GET", path, tmp_path, monkeypatch)


@pytest.mark.parametrize(
    "option,value",
    [
        ("--prepared-tree", "f" * 40),
        ("--manifest-digest", "f" * 64),
        ("--preparation-success", "true"),
        ("--ref", "refs/heads/main"),
        ("--api-url", "https://evil.invalid"),
        ("--tree", "f" * 40),
        ("--content", "arbitrary"),
        ("--author", "arbitrary"),
    ],
    ids=["prepared-tree", "manifest-digest", "preparation-success", "ref", "api-url", "tree", "content", "author"],
)
def test_cli_rejects_arbitrary_signing_inputs(option: str, value: str, tmp_path: Path) -> None:
    from scripts.pr785_signing_recovery import main

    with pytest.raises(SystemExit) as error:
        main(["--stage", "probe", "--expected-executor", "a" * 40, "--output", str(tmp_path), option, value])
    assert error.value.code == 2
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("level", ["root", "github", "workflows"])
def test_cli_prepared_tree_refusal_retains_no_signed_object(
    level: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code, api, responses = run_probe_cli(tmp_path, monkeypatch, refuse_prepared_tree=PREPARED_TREES[level])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert api.writes == 0
    receipt = json.loads((tmp_path / "receipt.json").read_text())
    assert receipt["status"] == "refused"
    assert receipt["context_verified"] is True
    assert receipt["objects"] == []
    assert_unverified_anchors(receipt)
    assert_receipt_execution_identity(receipt)
    assert_persisted_responses(tmp_path, responses)
    assert captured.out == ""
    assert captured.err == "Probe refused: API refused HTTP 404\n"


def test_success_returns_existing_receipt_with_complete_same_run_pair() -> None:
    from scripts.pr785_signing_recovery import MANIFEST_SHA256, Manifest, Probe

    manifest = Manifest.load(ROOT / "ci/recovery/pr785-signing-inputs.json")
    probe = Probe(manifest, context(), FakeAPI(manifest))
    receipt = probe.run()
    assert receipt is probe.receipt
    assert set(receipt) == {
        "status",
        "manifest_digest",
        "context_verified",
        "context",
        "objects",
        "ci_anchor_verified",
        "root_anchor_verified",
    }
    assert receipt["status"] == "signed_objects_verified"
    objects = receipt["objects"]
    assert len(objects) == len({item["sha"] for item in objects}) == 2
    for item, tree, label in zip(
        objects, (manifest.main_tree, manifest.probe_tree), ("baseline", "inert-workflow"), strict=True
    ):
        assert set(item) == {"sha", "tree", "parent", "message", "signature", "payload", "signed_object_verified"}
        assert item["tree"] == tree
        assert item["parent"] == manifest.main
        assert item["message"] == (
            f"PR785 signing probe {label}\n\nManifest: {MANIFEST_SHA256}\nExecutor: {'a' * 40}\nRun: 123\nAttempt: 1"
        )
        assert item["signed_object_verified"] is True
    assert_unverified_anchors(receipt)

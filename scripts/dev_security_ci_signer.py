from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import sys
import time
from dataclasses import asdict, dataclass, replace
from http.client import HTTPException, HTTPResponse
from pathlib import Path
from typing import Literal, cast
from urllib.error import HTTPError
from urllib.request import HTTPErrorProcessor, Request, build_opener

from beartype import beartype
from icontract import ensure, require


_REPO = "/repos/nold-ai/specfact-cli"
_AUX = "refs/heads/codex/dev786-complete-ci-signer-20261030"
_DEST = "refs/heads/codex/security-dev-complete-candidate-20261030"
_PARENT = "d77209f4b13c386e29391f93e1f1c58d7fd8622f"
_DEV = "9b5ad1e78430cc0b061cb16de42f73de96f4f312"
_WORKFLOW = 204352514
_WORKFLOW_PATH = ".github/workflows/specfact.yml"
_ALLOWED = frozenset(
    {
        ".github/workflows/pr-orchestrator.yml",
        ".github/workflows/requirements-evidence.yml",
        "CHANGELOG.md",
        "ci/dependency-trust-exceptions.json",
        "ci/vulnerability-audit-exceptions.json",
        "openspec/CHANGE_ORDER.md",
        "openspec/changes/security-dependencies-0-55-11-dev/.openspec.yaml",
        "openspec/changes/security-dependencies-0-55-11-dev/CHANGE_VALIDATION.md",
        "openspec/changes/security-dependencies-0-55-11-dev/TDD_EVIDENCE.md",
        "openspec/changes/security-dependencies-0-55-11-dev/design.md",
        "openspec/changes/security-dependencies-0-55-11-dev/proposal.md",
        "openspec/changes/security-dependencies-0-55-11-dev/requirements-evidence.yaml",
        "openspec/changes/security-dependencies-0-55-11-dev/requirements-proof/late-red-evidence.json",
        "openspec/changes/security-dependencies-0-55-11-dev/requirements-proof/local-red-behavior-20261026-receipt.json",
        "openspec/changes/security-dependencies-0-55-11-dev/requirements-proof/local-red-behavior-20261026.xml.gz",
        "openspec/changes/security-dependencies-0-55-11-dev/requirements-proof/review-evidence.json",
        "openspec/changes/security-dependencies-0-55-11-dev/specs/dev-security-dependencies/spec.md",
        "openspec/changes/security-dependencies-0-55-11-dev/tasks.md",
        "pyproject.toml",
        "requirements/ci/locked.txt",
        "requirements/code-review/locked.txt",
        "requirements/code-review/requirements.in",
        "scripts/requirements_late_red_proof.py",
        "setup.py",
        "src/__init__.py",
        "src/specfact_cli/__init__.py",
        "tests/fixtures/requirements-proof/pr786-native34-run.json",
        "tests/proof/test_fixed786_canonical_copy.py",
        "tests/unit/scripts/fixtures/fixed786-native-packet/fixture-metadata.json",
        "tests/unit/scripts/fixtures/fixed786-native-packet/local-red-report.json",
        "tests/unit/scripts/fixtures/fixed786-native-packet/plan.json",
        "tests/unit/scripts/fixtures/fixed786-native-packet/planning-report.json",
        "tests/unit/scripts/fixtures/fixed786-native-packet/requirements-proof.xml",
        "tests/unit/scripts/fixtures/fixed786_artifact_source/artifact-live-api.json",
        "tests/unit/scripts/fixtures/fixed786_artifact_source/manifest.json",
        "tests/unit/scripts/fixtures/fixed786_artifact_source/source-R2-filtered-api.json",
        "tests/unit/scripts/test_dependency_compatibility_workflow.py",
        "tests/unit/scripts/test_dependency_trust_review.py",
        "tests/unit/scripts/test_fixed786_artifact_source.py",
        "tests/unit/scripts/test_fixed786_native_packet.py",
        "tests/unit/scripts/test_fixed786_native_run.py",
        "tests/unit/scripts/test_fixed786_workflow_integration.py",
        "tests/unit/scripts/test_security_audit_gate.py",
        "tests/unit/security/test_code_review_dependency_security.py",
        "tests/unit/security/test_frozen_gitpython_compatibility.py",
        "tests/unit/security/test_release_dependency_selection.py",
        "tests/unit/security/test_release_promotion_security_gates.py",
        "uv.lock",
    }
)
_COPY_PREFIX = "tests/unit/scripts/fixtures/fixed786-native-packet/"
_COPY_METADATA_SHA256 = "e491e7ce89edf6a5c4299dc0d723cb9a3ff90573c062b45269da13f963a65617"
_COPY_MEMBERS = (
    ("requirements-evidence.json", "local-red-report.json", "report_digest"),
    ("requirements-evidence-plan.json", "planning-report.json", "plan_report_digest"),
    ("requirements-proof.xml", "requirements-proof.xml", "junit_digest"),
    ("plan.json", "plan.json", "plan_output_digest"),
)
_GIT_ROLES = {
    "author": {"name": "github-actions[bot]", "email": "41898282+github-actions[bot]@users.noreply.github.com"},
    "committer": {"name": "GitHub", "email": "noreply@github.com"},
}
_API_ROLES = {
    "author": {"id": 41898282, "login": "github-actions[bot]", "type": "Bot"},
    "committer": {"id": 19864447, "login": "web-flow", "type": "User"},
}
_MAX_RESPONSE = 32 * 1024 * 1024
_Entry = tuple[str, str]
_Status = Literal["published", "refused", "object_only", "uncertain_commit", "uncertain_ref", "created_ref_with_drift"]


@dataclass(frozen=True)
class DispatchExpectation:
    executor: str
    intent_sha256: str


@dataclass(frozen=True)
class RunContext:
    executor_sha: str
    run_id: int
    run_attempt: int
    repository_id: int
    repository_full_name: str
    actor_id: int
    actor_login: str
    triggering_actor_id: int
    triggering_actor_login: str
    event: str
    ref: str
    workflow_id: int
    workflow_path: str


@dataclass(frozen=True)
class _SignedCheckpoint:
    source_commit: str
    source_tree: str
    parent: str
    commit_sha: str
    signature: str
    payload: str


@dataclass(frozen=True)
class Outcome:
    status: _Status
    intent_sha256: str
    executor_sha: str
    run_id: int
    run_attempt: int
    reason: str = ""
    commit_sha: str | None = None
    ref_sha: str | None = None
    signature: str | None = None
    payload: str | None = None
    signed_checkpoints: tuple[_SignedCheckpoint, ...] = ()


@dataclass(frozen=True)
class _Delta:
    path: str
    before: _Entry | None
    after: _Entry | None


@dataclass(frozen=True)
class _Checkpoint:
    source_commit: str
    source_parent: str
    source_tree: str
    source_message: str
    delta: tuple[_Delta, ...]


@dataclass(frozen=True)
class _Intent:
    repository_id: int
    repository_full_name: str
    actor: tuple[int, str]
    triggering_actor: tuple[int, str]
    dev: str
    main: str
    checkpoints: tuple[_Checkpoint, ...]
    auxiliary_ref: str
    destination: str


@dataclass(frozen=True)
class _Response:
    status: int
    body: bytes


def _check(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def _object(value: object) -> dict[str, object]:
    _check(isinstance(value, dict), "Expected JSON object")
    return cast(dict[str, object], value)


def _array(value: object) -> list[object]:
    _check(isinstance(value, list), "Expected JSON array")
    return cast(list[object], value)


def _text(value: object) -> str:
    _check(isinstance(value, str) and bool(value), "Expected nonempty text")
    return cast(str, value)


def _integer(value: object) -> int:
    _check(type(value) is int and cast(int, value) > 0, "Expected positive integer")
    return cast(int, value)


def _sha(value: object) -> str:
    result = _text(value)
    _check(re.fullmatch(r"[0-9a-f]{40}", result) is not None, "Invalid Git object ID")
    return result


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result = dict(pairs)
    _check(len(result) == len(pairs), "Duplicate JSON key")
    return result


def _decode(raw: bytes) -> dict[str, object]:
    return _object(cast(object, json.loads(raw, object_pairs_hook=_unique)))


def _keys(record: dict[str, object], names: str) -> None:
    _check(set(record) == set(names.split()), "Unexpected or missing intent fields")


def _identity(value: object) -> tuple[int, str]:
    record = _object(value)
    _keys(record, "id login")
    return _integer(record["id"]), _text(record["login"])


def _entry(value: object) -> _Entry | None:
    if value is None:
        return None
    pair = _array(value)
    _check(len(pair) == 2 and pair[0] == "100644", "Unreviewed changed-leaf mode")
    return "100644", _sha(pair[1])


def _path(value: object) -> str:
    path = _text(value)
    _check(not any(part in ("", ".", "..") for part in path.split("/")), "Unsafe tree path")
    _check("\\" not in path and not any(ord(c) < 32 for c in path), "Unsafe path character")
    return path


def _delta(value: object) -> _Delta:
    record = _object(value)
    _keys(record, "path before after")
    path = _path(record["path"])
    _check(path in _ALLOWED, "Unreviewed changed path")
    delta = _Delta(path, _entry(record["before"]), _entry(record["after"]))
    _check(delta.before != delta.after, "Empty delta entry")
    return delta


def _checkpoint(value: object) -> _Checkpoint:
    record = _object(value)
    _keys(record, "source_commit source_parent source_tree source_message delta")
    deltas = tuple(_delta(item) for item in _array(record["delta"]))
    _check(bool(deltas) and len({d.path for d in deltas}) == len(deltas), "Empty or duplicate delta")
    message = _text(record["source_message"])
    _check(
        not any(
            re.match(r"\s*(?:Source-Commit|Intent|Executor|Run|Attempt)\s*:", line, re.IGNORECASE)
            for line in message.splitlines()
        ),
        "Reserved signer suffix in source message",
    )
    return _Checkpoint(
        _sha(record["source_commit"]),
        _sha(record["source_parent"]),
        _sha(record["source_tree"]),
        message,
        deltas,
    )


def _intent(raw: bytes) -> _Intent:
    record = _decode(raw)
    _keys(
        record,
        "repository_id repository_full_name actor triggering_actor dev main checkpoints auxiliary_ref destination",
    )
    entries = _array(record["checkpoints"])
    _check(1 <= len(entries) <= 32, "Expected 1..32 reviewed checkpoints")
    checkpoints = tuple(_checkpoint(value) for value in entries)
    parent = _PARENT
    seen = {_PARENT}
    for checkpoint in checkpoints:
        _check(checkpoint.source_parent == parent and checkpoint.source_commit not in seen, "Broken source chain")
        seen.add(checkpoint.source_commit)
        parent = checkpoint.source_commit
    intent = _Intent(
        _integer(record["repository_id"]),
        _text(record["repository_full_name"]),
        _identity(record["actor"]),
        _identity(record["triggering_actor"]),
        _sha(record["dev"]),
        _sha(record["main"]),
        checkpoints,
        _text(record["auxiliary_ref"]),
        _text(record["destination"]),
    )
    _check(
        (intent.repository_full_name, intent.dev, intent.auxiliary_ref, intent.destination)
        == ("nold-ai/specfact-cli", _DEV, _AUX, _DEST),
        "Unexpected publication scope",
    )
    return intent


class _NoRedirect(HTTPErrorProcessor):
    @ensure(lambda result, response: result is response, "Keep the original HTTP response without redirect handling")
    def http_response(self, request: Request, response: HTTPResponse) -> HTTPResponse:
        return response

    https_response = http_response


def _request(method: str, path: str, body: dict[str, object] | None = None) -> _Response:
    _check(path.startswith(_REPO) and not any(c in path for c in "\r\n#"), "Invalid API path")
    _check(
        method == "GET" or (method == "POST" and path in (_REPO + "/git/commits", _REPO + "/git/refs")),
        "Forbidden API operation",
    )
    token = _text(os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN"))
    request = Request(
        "https://api.github.com" + path,
        method=method,
        data=None if body is None else json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        },
    )
    try:
        with build_opener(_NoRedirect()).open(request, timeout=30) as response:
            raw = cast(bytes, response.read(_MAX_RESPONSE + 1))
            status = cast(int, response.status)
    except HTTPError as error:
        raw, status = error.read(_MAX_RESPONSE + 1), error.code
    _check(len(raw) <= _MAX_RESPONSE, "API response exceeds bound")
    return _Response(status, raw)


def _get(path: str) -> dict[str, object]:
    response = _request("GET", path)
    _check(response.status == 200, f"GET failed with HTTP {response.status}")
    return _decode(response.body)


def _matches(actual: object, expected: object) -> bool:
    if isinstance(expected, dict):
        return isinstance(actual, dict) and all(
            key in actual and _matches(cast(dict[str, object], actual)[key], value)
            for key, value in cast(dict[str, object], expected).items()
        )
    return type(actual) is type(expected) and actual == expected


def _ref(ref: str) -> str | None:
    response = _request("GET", _REPO + "/git/ref/" + ref.removeprefix("refs/"))
    if response.status == 404:
        return None
    _check(response.status == 200, f"Ref observation failed with HTTP {response.status}")
    record = _decode(response.body)
    _check(record.get("ref") == ref, "Ref name mismatch")
    obj = _object(record["object"])
    _check(obj.get("type") == "commit", "Ref is not a commit")
    return _sha(obj["sha"])


def _run_expected(intent: _Intent, context: RunContext) -> dict[str, object]:
    return {
        "id": context.run_id,
        "run_attempt": 1,
        "head_sha": context.executor_sha,
        "head_branch": _AUX.removeprefix("refs/heads/"),
        "event": "workflow_dispatch",
        "path": _WORKFLOW_PATH,
        "workflow_id": _WORKFLOW,
        "status": "in_progress",
        "repository": {"id": intent.repository_id, "full_name": intent.repository_full_name},
        "actor": {"id": intent.actor[0], "login": intent.actor[1]},
        "triggering_actor": {"id": intent.triggering_actor[0], "login": intent.triggering_actor[1]},
    }


def _context(intent: _Intent, expected: DispatchExpectation, context: RunContext, digest: str) -> None:
    _check(
        digest == expected.intent_sha256 and _sha(expected.executor) == context.executor_sha,
        "Dispatch expectation mismatch",
    )
    _integer(context.run_id)
    required = RunContext(
        expected.executor,
        context.run_id,
        1,
        intent.repository_id,
        intent.repository_full_name,
        *intent.actor,
        *intent.triggering_actor,
        "workflow_dispatch",
        _AUX,
        _WORKFLOW,
        _WORKFLOW_PATH,
    )
    _check(_matches(asdict(context), asdict(required)), "Execution context mismatch")


def _guards(intent: _Intent, context: RunContext, destination: str | None) -> None:
    repository = {"id": intent.repository_id, "full_name": intent.repository_full_name}
    _check(_matches(_get(_REPO), repository), "Repository identity mismatch")
    _check(
        _matches(
            _get(f"{_REPO}/pulls/786"),
            {
                "number": 786,
                "state": "open",
                "draft": False,
                "auto_merge": None,
                "head": {"sha": _PARENT, "ref": "codex/security-dependencies-0-55-11-dev", "repo": repository},
                "base": {"sha": intent.dev, "ref": "dev", "repo": repository},
            },
        ),
        "PR 786 state drift",
    )
    expected = _run_expected(intent, context)
    history = _get(f"{_REPO}/actions/workflows/{_WORKFLOW}/runs?event=workflow_dispatch&per_page=100")
    runs = [_object(run) for run in _array(history["workflow_runs"])]
    _check(type(history.get("total_count")) is int and history["total_count"] == len(runs), "Incomplete run history")
    same_executor = [run for run in runs if run.get("head_sha") == context.executor_sha]
    _check(len(same_executor) == 1 and _matches(same_executor[0], expected), "Executor already dispatched or absent")
    _check(_matches(_get(f"{_REPO}/actions/runs/{context.run_id}"), expected), "Live run mismatch")
    for ref, sha in (("refs/heads/dev", intent.dev), ("refs/heads/main", intent.main), (_AUX, context.executor_sha)):
        _check(_ref(ref) == sha, "Guard ref drift")
    _check(_ref(_DEST) == destination, "Destination changed")


def _inventory(sha: str) -> dict[str, _Entry]:
    record = _get(f"{_REPO}/git/trees/{sha}?recursive=1")
    _check(record.get("sha") == sha and record.get("truncated") is False, "Incomplete tree")
    leaves: dict[str, _Entry] = {}
    seen: set[str] = set()
    for value in _array(record["tree"]):
        item = _object(value)
        path, mode, oid = _path(item["path"]), _text(item["mode"]), _sha(item["sha"])
        _check(path not in seen, "Duplicate inventory path")
        seen.add(path)
        _check(
            (mode, item.get("type")) in (("040000", "tree"), ("100644", "blob"), ("100755", "blob")),
            "Invalid inventory mode/type",
        )
        if mode != "040000":
            leaves[path] = mode, oid
    return leaves


def _source(intent: _Intent) -> dict[str, _Entry]:
    base = _get(f"{_REPO}/git/commits/{intent.dev}")
    _check(base.get("sha") == intent.dev, "Base commit mismatch")
    before = _inventory(_sha(_object(base["tree"])["sha"]))
    after: dict[str, _Entry] = {}
    for checkpoint in intent.checkpoints:
        source = _get(f"{_REPO}/git/commits/{checkpoint.source_commit}")
        _check(
            _matches(
                source,
                {
                    "sha": checkpoint.source_commit,
                    "tree": {"sha": checkpoint.source_tree},
                    "message": checkpoint.source_message,
                },
            ),
            "Source tree/message mismatch",
        )
        parents = _array(source["parents"])
        _check(len(parents) == 1 and _matches(parents[0], {"sha": checkpoint.source_parent}), "Wrong source parent")
        after = _inventory(checkpoint.source_tree)
        actual = {
            _Delta(path, before.get(path), after.get(path))
            for path in before.keys() | after.keys()
            if before.get(path) != after.get(path)
        }
        _check(actual == set(checkpoint.delta), "Complete source delta mismatch")
    return after


def _copy_blob(inventory: dict[str, _Entry], name: str) -> bytes:
    mode, oid = inventory[_COPY_PREFIX + name]
    _check(mode == "100644", "COPY requires regular files")
    record = _get(f"{_REPO}/git/blobs/{oid}")
    _check(record.get("sha") == oid and record.get("encoding") == "base64", "Invalid COPY blob identity/encoding")
    content = _text(record["content"])
    _check(len(content) <= _MAX_RESPONSE, "COPY encoded blob exceeds bound")
    raw = base64.b64decode(content.replace("\r", "").replace("\n", ""), validate=True)
    _check(len(raw) <= _MAX_RESPONSE, "COPY decoded blob exceeds bound")
    _check(type(record.get("size")) is int and record["size"] == len(raw), "COPY blob size mismatch")
    git_oid = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw, usedforsecurity=False).hexdigest()
    _check(git_oid == oid, "COPY Git blob mismatch")
    return raw


def _copy_members(inventory: dict[str, _Entry]) -> dict[str, bytes]:
    metadata = _copy_blob(inventory, "fixture-metadata.json")
    _check(hashlib.sha256(metadata).hexdigest() == _COPY_METADATA_SHA256, "COPY metadata mismatch")
    record = _decode(metadata)
    files, manifest = _object(record["files"]), _object(record["manifest"])
    _check(set(files) == {name for name, _, _ in _COPY_MEMBERS}, "Unexpected COPY members")
    members: dict[str, bytes] = {}
    for name, source, digest_key in _COPY_MEMBERS:
        entry = _object(files[name])
        _check(entry.get("source") == source, "COPY source mapping mismatch")
        raw = _copy_blob(inventory, source)
        digest = hashlib.sha256(raw).hexdigest()
        _check(entry.get("bytes") == len(raw) and entry.get("sha256") == digest, "COPY member mismatch")
        _check(manifest.get(digest_key) == "sha256:" + digest, "COPY manifest mismatch")
        members[name] = raw
    return members


def _signed(record: dict[str, object], tree: str, parent: str, message: str, sha: str) -> tuple[str, str]:
    _check(_matches(record, {"sha": sha, "tree": {"sha": tree}, "message": message}), "Commit mismatch")
    parents = _array(record["parents"])
    _check(len(parents) == 1 and _matches(parents[0], {"sha": parent}), "Wrong commit parent")
    verification = _object(record["verification"])
    _check(verification.get("verified") is True and verification.get("reason") == "valid", "Invalid verification")
    signature, payload = _text(verification["signature"]), _text(verification["payload"])
    headers, separator, signed_message = payload.partition("\n\n")
    lines = headers.split("\n")
    _check(separator == "\n\n" and signed_message == message and len(lines) == 4, "Invalid signed payload")
    _check(lines[:2] == [f"tree {tree}", f"parent {parent}"], "Wrong signed tree/parent")
    for index, (role, identity) in enumerate(_GIT_ROLES.items(), start=2):
        _check(_matches(record.get(role), identity), "Wrong Git service identity")
        prefix = f"{role} {identity['name']} <{identity['email']}> "
        _check(
            re.fullmatch(re.escape(prefix) + r"[0-9]+ [+-][0-9]{4}", lines[index]) is not None,
            "Wrong signed service identity or timestamp",
        )
    return signature, payload


def _verify(tree: str, parent: str, message: str, outcome: Outcome) -> None:
    record = _get(f"{_REPO}/git/commits/{outcome.commit_sha}")
    _check(
        _signed(record, tree, parent, message, _text(outcome.commit_sha)) == (outcome.signature, outcome.payload),
        "Commit readback verification mismatch",
    )
    attribution = _get(f"{_REPO}/commits/{outcome.commit_sha}")
    _check(_matches(attribution, {"sha": outcome.commit_sha, **_API_ROLES}), "Wrong API service attribution")


def _execution_retained(result: Outcome, context: RunContext) -> bool:
    return (result.executor_sha, result.run_id, result.run_attempt) == (
        context.executor_sha,
        context.run_id,
        context.run_attempt,
    )


def _publication_complete(result: Outcome) -> bool:
    return result.status != "published" or (
        result.commit_sha is not None
        and result.commit_sha == result.ref_sha
        and bool(result.signature)
        and bool(result.payload)
    )


@beartype
@require(lambda intent_file: isinstance(intent_file, Path), "Intent must be a filesystem path")
@ensure(_execution_retained, "Receipt retains execution identity")
@ensure(_publication_complete, "Publication requires matching commit/ref and signature evidence")
def publish_once(intent_file: Path, expected: DispatchExpectation, context: RunContext) -> Outcome:
    """Publish once only after the complete frozen-source and CI guards agree."""
    outcome = Outcome("refused", "", context.executor_sha, context.run_id, context.run_attempt)
    try:
        raw = intent_file.read_bytes()
        outcome = replace(outcome, intent_sha256=hashlib.sha256(raw).hexdigest())
        intent = _intent(raw)
        _context(intent, expected, context, outcome.intent_sha256)
        _copy_members(_source(intent))
        _guards(intent, context, None)
        parent = _PARENT
        for checkpoint in intent.checkpoints:
            message = (
                f"{checkpoint.source_message}\n\nSource-Commit: {checkpoint.source_commit}"
                f"\nIntent: {outcome.intent_sha256}\nExecutor: {context.executor_sha}"
                f"\nRun: {context.run_id}\nAttempt: {context.run_attempt}"
            )
            outcome = replace(outcome, status="uncertain_commit", commit_sha=None, signature=None, payload=None)
            response = _request(
                "POST",
                _REPO + "/git/commits",
                {"tree": checkpoint.source_tree, "parents": [parent], "message": message},
            )
            _check(response.status == 201, f"Commit POST returned HTTP {response.status}")
            commit = _decode(response.body)
            outcome = replace(outcome, status="object_only", commit_sha=_sha(commit["sha"]))
            signature, payload = _signed(commit, checkpoint.source_tree, parent, message, _text(outcome.commit_sha))
            outcome = replace(outcome, signature=signature, payload=payload)
            _verify(checkpoint.source_tree, parent, message, outcome)
            confirmed = _SignedCheckpoint(
                checkpoint.source_commit,
                checkpoint.source_tree,
                parent,
                _text(outcome.commit_sha),
                signature,
                payload,
            )
            outcome = replace(outcome, signed_checkpoints=(*outcome.signed_checkpoints, confirmed))
            _guards(intent, context, None)
            parent = confirmed.commit_sha
        outcome = replace(outcome, status="uncertain_ref")
        response = _request("POST", _REPO + "/git/refs", {"ref": _DEST, "sha": outcome.commit_sha})
        _check(response.status == 201, f"Ref POST returned HTTP {response.status}")
        outcome = replace(outcome, status="created_ref_with_drift", ref_sha=outcome.commit_sha)
        _check(
            _matches(_decode(response.body), {"ref": _DEST, "object": {"type": "commit", "sha": outcome.commit_sha}}),
            "Ref creation response mismatch",
        )
        outcome = replace(outcome, ref_sha=_ref(_DEST))
        if outcome.ref_sha is None:
            time.sleep(60)
            outcome = replace(outcome, ref_sha=_ref(_DEST))
        _check(outcome.ref_sha == outcome.commit_sha, "Final ref mismatch")
        final = outcome.signed_checkpoints[-1]
        _verify(final.source_tree, final.parent, final.payload.partition("\n\n")[2], outcome)
        _guards(intent, context, outcome.commit_sha)
        return replace(outcome, status="published")
    except (ValueError, KeyError, OSError, HTTPException) as error:
        return replace(outcome, reason=f"{type(error).__name__}: {error}")


def _environment_context() -> RunContext:
    env = os.environ
    _check(env.get("GITHUB_ACTIONS") == "true", "Execution requires GitHub Actions")
    triggering = (int(env["GITHUB_ACTOR_ID"]), env["EXPECTED_TRIGGERING_ACTOR"])
    _check(
        triggering[1] == env["GITHUB_ACTOR"] == env["GITHUB_TRIGGERING_ACTOR"],
        "First-attempt triggering actor environment mismatch",
    )
    workflow = env["GITHUB_WORKFLOW_REF"]
    _check(workflow == f"nold-ai/specfact-cli/{_WORKFLOW_PATH}@{_AUX}", "Workflow environment mismatch")
    return RunContext(
        env["GITHUB_SHA"],
        int(env["GITHUB_RUN_ID"]),
        int(env["GITHUB_RUN_ATTEMPT"]),
        int(env["GITHUB_REPOSITORY_ID"]),
        env["GITHUB_REPOSITORY"],
        int(env["GITHUB_ACTOR_ID"]),
        env["GITHUB_ACTOR"],
        *triggering,
        env["GITHUB_EVENT_NAME"],
        env["GITHUB_REF"],
        _WORKFLOW,
        _WORKFLOW_PATH,
    )


def _main() -> int:
    parser = argparse.ArgumentParser(description="Create the reviewed dev security checkpoints once.")
    parser.add_argument("--intent", type=Path, required=True)
    parser.add_argument("--expected-executor", required=True)
    parser.add_argument("--expected-intent", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = cast(Path, args.output)
    context_record: dict[str, object] = {}
    receipt: dict[str, object] = {"status": "refused", "reason": "Context or intent unavailable"}
    evidence_ok = True
    try:
        output.mkdir(parents=True, exist_ok=True)
        intent_file = cast(Path, args.intent)
        raw = intent_file.read_bytes()
        (output / "intent.json").write_bytes(raw)
        context = _environment_context()
        context_record = asdict(context)
        expected = DispatchExpectation(cast(str, args.expected_executor), cast(str, args.expected_intent))
        digest = hashlib.sha256(raw).hexdigest()
        receipt = asdict(Outcome("refused", digest, context.executor_sha, context.run_id, context.run_attempt))
        intent = _intent(raw)
        _context(intent, expected, context, digest)
        members = _copy_members(_inventory(intent.checkpoints[-1].source_tree))
        copy_dir = output / "copy-members"
        copy_dir.mkdir()
        for name, data in members.items():
            with (copy_dir / name).open("xb") as member:
                member.write(data)
        receipt = asdict(publish_once(intent_file, expected, context))
    except (ValueError, KeyError, OSError, HTTPException) as error:
        receipt["reason"] = f"{type(error).__name__}: {error}"
    finally:
        try:
            (output / "context.json").write_text(json.dumps(context_record, indent=2) + "\n")
        except OSError as error:
            evidence_ok = False
            receipt["evidence_error"] = f"{type(error).__name__}: {error}"
        try:
            (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
        except OSError as error:
            evidence_ok = False
            receipt["evidence_error"] = f"{type(error).__name__}: {error}"
            sys.stderr.write(json.dumps(receipt) + "\n")
    return 0 if evidence_ok and receipt["status"] == "published" else 1


if __name__ == "__main__":
    raise SystemExit(_main())

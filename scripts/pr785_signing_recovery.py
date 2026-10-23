"""Create and verify bounded PR785 probe or seven-source objects in approved CI."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, NoReturn, Protocol, TypedDict, runtime_checkable

from beartype import beartype
from icontract import ensure, require


MANIFEST_SHA256 = "6c3d344ecb69beca59231c3c49ae05dba50790fd253db87f37122028de1dfa2a"
REPOSITORY = "nold-ai/specfact-cli"
AUXILIARY_BRANCH = "codex/pr785-ci-signing-recovery"
WORKFLOW_PATH = ".github/workflows/specfact.yml"
WORKFLOW_ID = 204352514
ACTOR = "djm81"
BOT = "github-actions[bot]"
BOT_EMAIL = "41898282+github-actions[bot]@users.noreply.github.com"
SHA_PATTERN = r"[0-9a-f]{40}"
MAX_RESPONSE_BYTES = 2_000_000
ROOT = Path(__file__).resolve().parents[1]


class ProbeRefusalError(Exception):
    """The approved probe cannot proceed safely."""


def _check(condition: bool, reason: str) -> None:
    if not condition:
        raise ProbeRefusalError(reason)


def _string(value: object) -> str:
    _check(isinstance(value, str), "Expected string field")
    if isinstance(value, str):
        return value
    raise ProbeRefusalError("Expected string field")


def _field(record: Mapping[str, Any], *keys: str) -> Any:
    value: Any = record
    for key in keys:
        _check(isinstance(value, dict) and key in value, "Missing response field")
        value = value[key]
    return value


def _sha(value: object) -> str:
    text = _string(value)
    _check(re.fullmatch(SHA_PATTERN, text) is not None, "Invalid object identity")
    return text


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        _check(key not in result, "Duplicate JSON field")
        result[key] = value
    return result


def _invalid_json_constant(value: str) -> NoReturn:
    raise ProbeRefusalError("Non-finite JSON number")


def _json_object(data: bytes) -> dict[str, Any]:
    try:
        value: Any = json.loads(data, object_pairs_hook=_unique_json_object, parse_constant=_invalid_json_constant)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise ProbeRefusalError("Invalid JSON response") from error
    _check(isinstance(value, dict), "Expected JSON object")
    return value


@dataclass(frozen=True)
class _SourceCommit:
    ordinal: int
    sha: str
    tree: str
    parent: str
    subject: str


@dataclass(frozen=True)
class _PrefixSources:
    steps: tuple[
        _SourceCommit, _SourceCommit, _SourceCommit, _SourceCommit, _SourceCommit, _SourceCommit, _SourceCommit
    ]


def _source_commits(record: Mapping[str, Any]) -> tuple[_SourceCommit, ...]:
    source = _field(record, "source")
    records = _field(source, "commits")
    _check(isinstance(records, list) and len(records) == 10, "Expected ten source commits")
    parent = _sha(_field(source, "expected_main"))
    seen = {parent}
    commits: list[_SourceCommit] = []
    for ordinal, item in enumerate(records, 1):
        sha = _sha(_field(item, "sha"))
        _check(sha not in seen, "Duplicate source identity")
        parents = _field(item, "parents")
        _check(isinstance(parents, list) and parents == [parent], "Source parent chain mismatch")
        subject = _string(_field(item, "subject"))
        _check(bool(subject) and "\n" not in subject and "\r" not in subject, "Invalid source subject")
        commits.append(_SourceCommit(ordinal, sha, _sha(_field(item, "tree")), parent, subject))
        seen.add(sha)
        parent = sha
    _check(commits[-1].sha == _sha(_field(source, "expected_old_head")), "Final source identity mismatch")
    _check(commits[-1].tree == _sha(_field(source, "reviewed_final_tree")), "Final source tree mismatch")
    _check(commits[6].sha == _sha(_field(source, "old_red_head")), "Prefix source identity mismatch")
    _check(commits[6].tree == _sha(_field(source, "old_red_tree")), "Prefix source tree mismatch")
    return tuple(commits)


@dataclass(frozen=True)
class Manifest:
    repository: str
    main: str
    old_head: str
    branch: str
    main_tree: str
    probe_tree: str
    probe_path: str
    probe_content: str
    sources: tuple[_SourceCommit, ...]

    @property
    @ensure(
        lambda result: (
            isinstance(result, _PrefixSources) and tuple(step.ordinal for step in result.steps) == (1, 2, 3, 4, 5, 6, 7)
        )
    )
    def prefix(self) -> _PrefixSources:
        sources = self.sources
        return _PrefixSources((sources[0], sources[1], sources[2], sources[3], sources[4], sources[5], sources[6]))

    @classmethod
    @beartype
    @require(lambda path: isinstance(path, Path))
    @ensure(lambda result: isinstance(result, Manifest) and result.repository == REPOSITORY)
    def load(cls, path: Path) -> Manifest:
        """Read the exact reviewed manifest bytes before exposing probe inputs."""
        data = path.read_bytes()
        _check(hashlib.sha256(data).hexdigest() == MANIFEST_SHA256, "Manifest digest mismatch")
        record = _json_object(data)
        return cls(
            repository=_string(_field(record, "source", "repository")),
            main=_sha(_field(record, "source", "expected_main")),
            old_head=_sha(_field(record, "source", "expected_old_head")),
            branch=_string(_field(record, "source", "branch")),
            main_tree=_sha(_field(record, "probe", "main_tree")),
            probe_tree=_sha(_field(record, "probe", "probe_tree")),
            probe_path=_string(_field(record, "probe", "probe_path")),
            probe_content=_string(_field(record, "probe", "probe_content")),
            sources=_source_commits(record),
        )


class ReceiptContext(TypedDict):
    run_id: int
    run_attempt: int
    executor_sha: str
    repository: str
    actor: str
    event: str
    ref: str
    workflow_id: int
    workflow_path: str


class VerifiedObject(TypedDict):
    sha: str
    tree: str
    parent: str
    message: str
    signature: str
    payload: str
    signed_object_verified: Literal[True]


class ProbeReceipt(TypedDict):
    status: Literal["refused", "signed_objects_verified"]
    manifest_digest: str
    context_verified: bool
    context: ReceiptContext
    objects: list[VerifiedObject]
    ci_anchor_verified: Literal[False]
    root_anchor_verified: Literal[False]


@dataclass(frozen=True)
class RunContext:
    run_id: int
    run_attempt: int
    executor_sha: str
    stage: Literal["probe", "prefix7"] = "probe"

    @classmethod
    @beartype
    @require(lambda env: isinstance(env, Mapping))
    @ensure(lambda result: isinstance(result, RunContext) and result.run_id > 0 and result.run_attempt > 0)
    def from_env(cls, env: Mapping[str, str], stage: str, expected_executor: str) -> RunContext:
        """Reject every environment mismatch before constructing an API client."""
        _check(stage in {"probe", "prefix7"}, "Only probe is authorized")
        executor = _sha(expected_executor)
        expected = {
            "GITHUB_ACTIONS": "true",
            "GITHUB_REPOSITORY": REPOSITORY,
            "GITHUB_ACTOR": ACTOR,
            "GITHUB_TRIGGERING_ACTOR": ACTOR,
            "GITHUB_EVENT_NAME": "workflow_dispatch",
            "GITHUB_REF": f"refs/heads/{AUXILIARY_BRANCH}",
            "GITHUB_SHA": executor,
            "GITHUB_WORKFLOW_SHA": executor,
            "GITHUB_WORKFLOW_REF": f"{REPOSITORY}/{WORKFLOW_PATH}@refs/heads/{AUXILIARY_BRANCH}",
            "GITHUB_SERVER_URL": "https://github.com",
            "GITHUB_API_URL": "https://api.github.com",
        }
        _check(all(env.get(key) == value for key, value in expected.items()), "Execution context mismatch")
        return cls(
            _positive_integer(env.get("GITHUB_RUN_ID", "")),
            _positive_integer(env.get("GITHUB_RUN_ATTEMPT", "")),
            executor,
            "prefix7" if stage == "prefix7" else "probe",
        )


def _positive_integer(value: str) -> int:
    _check(re.fullmatch(r"[1-9][0-9]{0,19}", value) is not None, "Invalid run identity")
    return int(value)


def _observed_context(env: Mapping[str, str]) -> ReceiptContext:
    def observed_number(key: str) -> int:
        value = env.get(key, "")
        return int(value) if re.fullmatch(r"[1-9][0-9]{0,19}", value) else 0

    return {
        "run_id": observed_number("GITHUB_RUN_ID"),
        "run_attempt": observed_number("GITHUB_RUN_ATTEMPT"),
        "executor_sha": env.get("GITHUB_SHA", ""),
        "repository": env.get("GITHUB_REPOSITORY", ""),
        "actor": env.get("GITHUB_ACTOR", ""),
        "event": env.get("GITHUB_EVENT_NAME", ""),
        "ref": env.get("GITHUB_REF", ""),
        "workflow_id": WORKFLOW_ID,
        "workflow_path": WORKFLOW_PATH,
    }


def _receipt(identity: ReceiptContext) -> ProbeReceipt:
    return {
        "status": "refused",
        "manifest_digest": MANIFEST_SHA256,
        "context_verified": False,
        "context": identity,
        "objects": [],
        "ci_anchor_verified": False,
        "root_anchor_verified": False,
    }


@dataclass(frozen=True)
class _AcceptedProbeObject:
    label: Literal["baseline", "inert-workflow"]
    sha: str
    tree: str

    @property
    @ensure(
        lambda result: (
            isinstance(result, str)
            and result.startswith(f"refs/heads/codex/pr785-signing-recovery/{MANIFEST_SHA256}/probe-")
        )
    )
    def ref(self) -> str:
        return f"refs/heads/codex/pr785-signing-recovery/{MANIFEST_SHA256}/probe-{self.label}"


@dataclass(frozen=True)
class _AcceptedProbe:
    executor: str
    run: int
    attempt: int
    artifact: int
    zip_sha256: str
    objects: tuple[_AcceptedProbeObject, _AcceptedProbeObject]

    @ensure(
        lambda result: (
            isinstance(result, dict)
            and set(result) == {"executor", "run", "attempt", "artifact", "zip_sha256", "objects"}
            and len(result["objects"]) == 2
        )
    )
    def as_json(self) -> dict[str, object]:
        return {
            "executor": self.executor,
            "run": self.run,
            "attempt": self.attempt,
            "artifact": self.artifact,
            "zip_sha256": self.zip_sha256,
            "objects": [
                {"label": item.label, "sha": item.sha, "tree": item.tree, "ref": item.ref} for item in self.objects
            ],
        }


_ACCEPTED_PROBE = _AcceptedProbe(
    executor="88dc8c40c7a1e852c539d0668238b94da5ca32b2",
    run=39936325185,
    attempt=1,
    artifact=12494410796,
    zip_sha256="7fc151d4549bc6c47e09764106339b8cb52e227cfcc9848ee65373b34f36bb51",
    objects=(
        _AcceptedProbeObject(
            "baseline", "db02837c1922eaa191e10238606ac83571c4f228", "4c9ba46b2ace65cd8df0fcd5a77c2b14a42f599c"
        ),
        _AcceptedProbeObject(
            "inert-workflow", "837a9d68fe62bb13e9b272f0c6f11634894ae0fb", "4b2cf05809c1cf687e4eae17a770cd33c97eff72"
        ),
    ),
)


@runtime_checkable
class RequestAPI(Protocol):
    request: Callable[[str, str, dict[str, Any] | None], dict[str, Any]]


@dataclass(frozen=True)
class _PreparedTreeIntent:
    sha: str
    path: str
    mode: str
    kind: str
    child: str


_PREPARED_TREES = (
    _PreparedTreeIntent(
        "4b2cf05809c1cf687e4eae17a770cd33c97eff72",
        ".github",
        "040000",
        "tree",
        "6c8d9363427fb97b00eae0a452dab167ba41b8a4",
    ),
    _PreparedTreeIntent(
        "6c8d9363427fb97b00eae0a452dab167ba41b8a4",
        "workflows",
        "040000",
        "tree",
        "f0a1368e6f068ece5c3b1f1bb9264720778af6bd",
    ),
    _PreparedTreeIntent(
        "f0a1368e6f068ece5c3b1f1bb9264720778af6bd",
        "pr785-inert-probe.yml",
        "100644",
        "blob",
        "c00d710f49c952dee0ef3886acf476c7e49e0a8e",
    ),
)


def _verify_tree_response(intent: _PreparedTreeIntent, record: Mapping[str, Any]) -> None:
    _check(_sha(_field(record, "sha")) == intent.sha, "Prepared tree identity mismatch")
    _check(_field(record, "truncated") is False, "Prepared tree is truncated")
    entries = _field(record, "tree")
    _check(isinstance(entries, list), "Expected prepared tree entries")
    children: dict[str, tuple[str, str, str]] = {}
    for entry in entries:
        path = _string(_field(entry, "path"))
        _check(
            bool(path) and path not in {".", ".."} and "/" not in path and "\0" not in path, "Invalid direct tree path"
        )
        _check(path not in children, "Duplicate prepared tree entry")
        mode = _string(_field(entry, "mode"))
        kind = _string(_field(entry, "type"))
        _check(
            (mode, kind)
            in {("040000", "tree"), ("100644", "blob"), ("100755", "blob"), ("120000", "blob"), ("160000", "commit")},
            "Invalid prepared tree entry mode or type",
        )
        children[path] = (mode, kind, _sha(_field(entry, "sha")))
    _check(children.get(intent.path) == (intent.mode, intent.kind, intent.child), "Prepared tree child mismatch")


def _allowed_route(method: str, path: str) -> bool:
    if method == "POST":
        return path == "/git/commits"
    if method != "GET":
        return False
    if path in {f"/git/trees/{intent.sha}" for intent in _PREPARED_TREES}:
        return True
    if path in {f"/git/ref/{item.ref.removeprefix('refs/')}" for item in _ACCEPTED_PROBE.objects}:
        return True
    patterns = (
        r"/actions/runs/[1-9][0-9]{0,19}",
        r"/git/ref/heads/main",
        r"/pulls/785",
        rf"/git/commits/{SHA_PATTERN}",
        rf"/commits/{SHA_PATTERN}",
    )
    return any(re.fullmatch(pattern, path) is not None for pattern in patterns)


class GitHubAPI:
    @beartype
    def __init__(self, token: str, output: Path) -> None:
        self._token = token
        self._raw = output / "raw"
        _check(not self._raw.exists(), "Raw output already exists")
        self._raw.mkdir(parents=True)
        self._sequence = 0
        self._opener = urllib.request.OpenerDirector()
        self._opener.add_handler(urllib.request.HTTPSHandler())
        self._opener.add_handler(urllib.request.HTTPDefaultErrorHandler())
        self._opener.add_handler(urllib.request.HTTPErrorProcessor())

    @beartype
    @require(lambda method, path: isinstance(method, str) and isinstance(path, str))
    @ensure(lambda result: isinstance(result, dict))
    def request(self, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        """Call an allowlisted fixed-origin route and retain only successful JSON."""
        _check(_allowed_route(method, path), "Forbidden API route")
        _check(bool(self._token), "Missing job credential")
        _check((method == "POST") == (body is not None), "Request body mismatch")
        encoded = json.dumps(body).encode() if body is not None else None
        request = urllib.request.Request(
            f"https://api.github.com/repos/{REPOSITORY}{path}",
            data=encoded,
            method=method,
            headers={
                "Authorization": f"Bearer {self._token}",
                "Accept": "application/vnd.github+json",
                "Content-Type": "application/json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        data = self._read(request)
        _check(self._token.encode() not in data, "Credential reflected in response")
        result = _json_object(data)
        self._sequence += 1
        (self._raw / f"{self._sequence:04d}.json").write_bytes(data)
        return result

    def _read(self, request: urllib.request.Request) -> bytes:
        try:
            with self._opener.open(request, timeout=30) as response:
                data = response.read(MAX_RESPONSE_BYTES + 1)
        except urllib.error.HTTPError as error:
            raise ProbeRefusalError(f"API refused HTTP {error.code}") from None
        except (urllib.error.URLError, OSError, TimeoutError) as error:
            raise ProbeRefusalError("API transport failed") from error
        _check(len(data) <= MAX_RESPONSE_BYTES, "API response exceeded size bound")
        return data


@dataclass(frozen=True)
class _CommitIntent:
    tree: str
    parent: str
    message: str


@dataclass(frozen=True)
class _SignedCommit:
    sha: str
    intent: _CommitIntent
    signature: str
    payload: str

    @ensure(
        lambda result: (
            isinstance(result, dict)
            and set(result) == {"sha", "tree", "parent", "message", "signature", "payload", "signed_object_verified"}
            and result["signed_object_verified"] is True
        )
    )
    def as_probe_object(self) -> VerifiedObject:
        return {
            "sha": self.sha,
            "tree": self.intent.tree,
            "parent": self.intent.parent,
            "message": self.intent.message,
            "signature": self.signature,
            "payload": self.payload,
            "signed_object_verified": True,
        }


@dataclass(frozen=True)
class _PrefixStep:
    source: _SourceCommit
    signed: _SignedCommit

    @ensure(
        lambda result: (
            isinstance(result, dict)
            and set(result)
            == {
                "ordinal",
                "source_sha",
                "source_tree",
                "source_parent",
                "subject",
                "sha",
                "tree",
                "parent",
                "message",
                "signature",
                "payload",
                "signed_object_verified",
            }
            and result["signed_object_verified"] is True
        )
    )
    def as_json(self) -> dict[str, object]:
        return {
            "ordinal": self.source.ordinal,
            "source_sha": self.source.sha,
            "source_tree": self.source.tree,
            "source_parent": self.source.parent,
            "subject": self.source.subject,
            "sha": self.signed.sha,
            "tree": self.signed.intent.tree,
            "parent": self.signed.intent.parent,
            "message": self.signed.intent.message,
            "signature": self.signed.signature,
            "payload": self.signed.payload,
            "signed_object_verified": True,
        }


@dataclass
class Prefix7Receipt:
    context: ReceiptContext
    context_verified: bool = False
    accepted_probe_verified: bool = False
    sources_verified: bool = False
    steps: tuple[_PrefixStep, ...] = ()
    status: Literal["refused", "prefix7_verified"] = "refused"
    stage: Literal["prefix7"] = field(default="prefix7", init=False)
    ci_anchor_verified: Literal[False] = field(default=False, init=False)
    root_anchor_verified: Literal[False] = field(default=False, init=False)

    @ensure(
        lambda result: (
            isinstance(result, dict)
            and result["stage"] == "prefix7"
            and "objects" not in result
            and result["ci_anchor_verified"] is result["root_anchor_verified"] is False
        )
    )
    def as_json(self) -> dict[str, object]:
        return {
            "stage": self.stage,
            "status": self.status,
            "manifest_digest": MANIFEST_SHA256,
            "context": self.context,
            "context_verified": self.context_verified,
            "accepted_probe": _ACCEPTED_PROBE.as_json(),
            "accepted_probe_verified": self.accepted_probe_verified,
            "sources_verified": self.sources_verified,
            "steps": [step.as_json() for step in self.steps],
            "ci_anchor_verified": self.ci_anchor_verified,
            "root_anchor_verified": self.root_anchor_verified,
        }


@dataclass(frozen=True)
class _ServiceIdentity:
    role: Literal["author", "committer"]
    name: str
    email: str
    login: str
    account_id: int
    account_type: Literal["Bot", "User"]


_SERVICE_IDENTITIES = (
    _ServiceIdentity("author", BOT, BOT_EMAIL, BOT, 41898282, "Bot"),
    _ServiceIdentity("committer", "GitHub", "noreply@github.com", "web-flow", 19864447, "User"),
)


def _verify_payload(payload: str, intent: _CommitIntent) -> None:
    headers, separator, message = payload.partition("\n\n")
    _check(separator == "\n\n" and message == intent.message, "Signed message mismatch")
    lines = headers.splitlines()
    _check(len(lines) == 4, "Unexpected signed headers")
    _check(lines[:2] == [f"tree {intent.tree}", f"parent {intent.parent}"], "Signed tree or parent mismatch")
    for line, expected in zip(lines[2:], _SERVICE_IDENTITIES, strict=True):
        identity = re.escape(f"{expected.name} <{expected.email}>")
        _check(
            re.fullmatch(rf"{expected.role} {identity} [0-9]+ [+-][0-9]{{4}}", line) is not None,
            "Signed attribution mismatch",
        )


def _verified_commit(
    record: Mapping[str, Any], intent: _CommitIntent, expected_sha: str | None = None
) -> _SignedCommit:
    sha = _sha(_field(record, "sha"))
    _check(expected_sha is None or sha == expected_sha, "Commit readback identity mismatch")
    _check(_field(record, "tree", "sha") == intent.tree, "Commit tree mismatch")
    parents = _field(record, "parents")
    _check(isinstance(parents, list) and len(parents) == 1, "Commit must have one parent")
    _check(_field(parents[0], "sha") == intent.parent, "Commit parent mismatch")
    _check(_field(record, "message") == intent.message, "Commit message mismatch")
    _verify_signature(record, intent)
    return _SignedCommit(
        sha,
        intent,
        _string(_field(record, "verification", "signature")),
        _string(_field(record, "verification", "payload")),
    )


def _verify_signature(record: Mapping[str, Any], intent: _CommitIntent) -> None:
    _check(_field(record, "verification", "verified") is True, "Commit is not verified")
    _check(_field(record, "verification", "reason") == "valid", "Signature reason is not valid")
    _check(bool(_string(_field(record, "verification", "signature")).strip()), "Missing signature")
    for expected in _SERVICE_IDENTITIES:
        _check(_field(record, expected.role, "name") == expected.name, "Git attribution mismatch")
        _check(_field(record, expected.role, "email") == expected.email, "Git attribution email mismatch")
    _verify_payload(_string(_field(record, "verification", "payload")), intent)


def _verify_attribution(record: Mapping[str, Any], sha: str) -> None:
    _check(_field(record, "sha") == sha, "Attribution identity mismatch")
    for identity in _SERVICE_IDENTITIES:
        expected = {"login": identity.login, "id": identity.account_id, "type": identity.account_type}
        _check(
            all(_field(record, identity.role, key) == value for key, value in expected.items()),
            "Service attribution mismatch",
        )


def _context_identity(context: RunContext) -> ReceiptContext:
    return {
        "run_id": context.run_id,
        "run_attempt": context.run_attempt,
        "executor_sha": context.executor_sha,
        "repository": REPOSITORY,
        "actor": ACTOR,
        "event": "workflow_dispatch",
        "ref": f"refs/heads/{AUXILIARY_BRANCH}",
        "workflow_id": WORKFLOW_ID,
        "workflow_path": WORKFLOW_PATH,
    }


def _verify_run(api: RequestAPI, context: RunContext) -> None:
    run = api.request("GET", f"/actions/runs/{context.run_id}", None)
    expected = {
        "id": context.run_id,
        "run_attempt": context.run_attempt,
        "head_sha": context.executor_sha,
        "head_branch": AUXILIARY_BRANCH,
        "event": "workflow_dispatch",
        "path": WORKFLOW_PATH,
        "workflow_id": WORKFLOW_ID,
        "status": "in_progress",
    }
    _check(
        all(type(_field(run, key)) is type(value) and _field(run, key) == value for key, value in expected.items()),
        "Live workflow run mismatch",
    )
    _check(_field(run, "repository", "full_name") == REPOSITORY, "Live run repository mismatch")
    for role in ("actor", "triggering_actor"):
        _check(_field(run, role, "login") == ACTOR, "Live run actor mismatch")


def _guard_refs(api: RequestAPI, manifest: Manifest) -> None:
    main_ref = api.request("GET", "/git/ref/heads/main", None)
    _check(_field(main_ref, "object", "sha") == manifest.main, "Main has drifted")
    pr = api.request("GET", "/pulls/785", None)
    _check(_field(pr, "state") == "open", "Pull request is not open")
    _check(_field(pr, "merged") is False, "Pull request is merged")
    _check(_field(pr, "auto_merge") is None, "Auto-merge is enabled")
    for side, sha, ref in (
        ("base", manifest.main, "main"),
        ("head", manifest.old_head, manifest.branch),
    ):
        _check(_field(pr, side, "sha") == sha, "Pull request revision drift")
        _check(_field(pr, side, "ref") == ref, "Pull request branch drift")
        _check(_field(pr, side, "repo", "full_name") == REPOSITORY, "Pull request repository drift")


def _create_verified_commit(
    api: RequestAPI, manifest: Manifest, intent: _CommitIntent, excluded: frozenset[str]
) -> _SignedCommit:
    _guard_refs(api, manifest)
    try:
        result = api.request(
            "POST", "/git/commits", {"message": intent.message, "tree": intent.tree, "parents": [intent.parent]}
        )
    except (ProbeRefusalError, OSError) as primary:
        try:
            _guard_refs(api, manifest)
        except (ProbeRefusalError, OSError):
            raise primary from None
        raise
    _guard_refs(api, manifest)
    created = _verified_commit(result, intent)
    _check(created.sha not in excluded, "Signed identity is not new")
    readback = api.request("GET", f"/git/commits/{created.sha}", None)
    verified = _verified_commit(readback, intent, created.sha)
    _check(verified == created, "Commit readback differs")
    _verify_attribution(api.request("GET", f"/commits/{verified.sha}", None), verified.sha)
    return verified


def _probe_intent(tree: str, parent: str, label: str, context: RunContext) -> _CommitIntent:
    message = (
        f"PR785 signing probe {label}\n\nManifest: {MANIFEST_SHA256}\n"
        f"Executor: {context.executor_sha}\nRun: {context.run_id}\nAttempt: {context.run_attempt}"
    )
    return _CommitIntent(tree, parent, message)


def _verify_accepted_probe(api: RequestAPI, manifest: Manifest) -> None:
    witness = _ACCEPTED_PROBE
    context = RunContext(witness.run, witness.attempt, witness.executor)
    for item in witness.objects:
        ref = api.request("GET", f"/git/ref/{item.ref.removeprefix('refs/')}", None)
        _check(_field(ref, "ref") == item.ref, "Accepted probe ref mismatch")
        _check(_field(ref, "object", "type") == "commit", "Accepted probe ref type mismatch")
        _check(_field(ref, "object", "sha") == item.sha, "Accepted probe ref identity mismatch")
        intent = _probe_intent(item.tree, manifest.main, item.label, context)
        _verified_commit(api.request("GET", f"/git/commits/{item.sha}", None), intent, item.sha)
        _verify_attribution(api.request("GET", f"/commits/{item.sha}", None), item.sha)


def _verify_sources(api: RequestAPI, manifest: Manifest) -> _PrefixSources:
    prefix = manifest.prefix
    for source in prefix.steps:
        record = api.request("GET", f"/git/commits/{source.sha}", None)
        _check(_sha(_field(record, "sha")) == source.sha, "Source identity mismatch")
        _check(_field(record, "tree", "sha") == source.tree, "Source tree mismatch")
        parents = _field(record, "parents")
        _check(isinstance(parents, list) and len(parents) == 1, "Source must have one parent")
        _check(_field(parents[0], "sha") == source.parent, "Source parent mismatch")
        message = _string(_field(record, "message"))
        _check(message.partition("\n")[0] == source.subject, "Source subject mismatch")
    return prefix


def _prefix_intent(source: _SourceCommit, parent: str, context: RunContext) -> _CommitIntent:
    message = (
        f"{source.subject}\n\nStage: prefix7\nSource: {source.sha}\nOrdinal: {source.ordinal}\n"
        f"Manifest: {MANIFEST_SHA256}\nExecutor: {context.executor_sha}\n"
        f"Run: {context.run_id}\nAttempt: {context.run_attempt}"
    )
    return _CommitIntent(source.tree, parent, message)


class Prefix7:
    @beartype
    def __init__(self, manifest: Manifest, context: RunContext, api: RequestAPI) -> None:
        self._manifest = manifest
        self._context = context
        self._api = api
        self._started = False
        self.receipt = Prefix7Receipt(_context_identity(context))

    @beartype
    @ensure(
        lambda result: (
            isinstance(result, Prefix7Receipt) and result.status == "prefix7_verified" and len(result.steps) == 7
        )
    )
    def run(self) -> Prefix7Receipt:
        """Verify the fixed witness and sources before building the seven-step chain."""
        _check(not self._started, "Prefix operation already attempted")
        self._started = True
        _check(self._context.stage == "prefix7", "Operation context mismatch")
        _verify_run(self._api, self._context)
        self.receipt.context_verified = True
        _verify_accepted_probe(self._api, self._manifest)
        self.receipt.accepted_probe_verified = True
        sources = _verify_sources(self._api, self._manifest)
        self.receipt.sources_verified = True
        excluded = frozenset(
            [source.sha for source in self._manifest.sources]
            + [item.sha for item in _ACCEPTED_PROBE.objects]
            + [self._manifest.main, self._context.executor_sha, _ACCEPTED_PROBE.executor]
        )
        parent = self._manifest.main
        for source in sources.steps:
            intent = _prefix_intent(source, parent, self._context)
            signed = _create_verified_commit(self._api, self._manifest, intent, excluded)
            self.receipt.steps += (_PrefixStep(source, signed),)
            parent = signed.sha
            excluded = excluded | {signed.sha}
        self.receipt.status = "prefix7_verified"
        return self.receipt


class Probe:
    @beartype
    def __init__(self, manifest: Manifest, context: RunContext, api: RequestAPI) -> None:
        self._manifest = manifest
        self._context = context
        self._api = api
        self.receipt = _receipt(_context_identity(context))

    @beartype
    @require(lambda self: isinstance(self, Probe) and not self.receipt["objects"])
    @ensure(lambda result: result["status"] == "signed_objects_verified" and len(result["objects"]) == 2)
    def run(self) -> ProbeReceipt:
        """Verify the live run, then create and reread the two approved objects."""
        _check(self._context.stage == "probe", "Operation context mismatch")
        _verify_run(self._api, self._context)
        self.receipt["context_verified"] = True
        self._verify_prepared_tree()
        self._create_commit(self._manifest.main_tree, "baseline")
        self._create_commit(self._manifest.probe_tree, "inert-workflow")
        self.receipt["status"] = "signed_objects_verified"
        return self.receipt

    def _verify_prepared_tree(self) -> None:
        manifest = self._manifest
        try:
            result = subprocess.run(
                ["git", "hash-object", "--stdin"],
                input=manifest.probe_content.encode(),
                capture_output=True,
                check=True,
                timeout=10,
                cwd=ROOT,
            )
            blob = _sha(result.stdout.decode("ascii").strip())
        except (OSError, subprocess.SubprocessError, UnicodeError):
            raise ProbeRefusalError("Prepared blob identity calculation failed") from None
        _check(blob == _PREPARED_TREES[-1].child, "Prepared blob content mismatch")
        _check(manifest.probe_tree == _PREPARED_TREES[0].sha, "Prepared root manifest mismatch")
        _check(
            manifest.probe_path == "/".join(intent.path for intent in _PREPARED_TREES),
            "Prepared path manifest mismatch",
        )
        for intent in _PREPARED_TREES:
            response = self._api.request("GET", f"/git/trees/{intent.sha}", None)
            _verify_tree_response(intent, response)

    def _create_commit(self, tree: str, label: str) -> None:
        intent = _probe_intent(tree, self._manifest.main, label, self._context)
        verified = _create_verified_commit(self._api, self._manifest, intent, frozenset())
        self.receipt["objects"].append(verified.as_probe_object())


def _parse_arguments(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", required=True)
    parser.add_argument("--expected-executor", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


@beartype
@require(lambda argv: argv is None or isinstance(argv, (list, tuple)))
@ensure(lambda result: result in (0, 1))
def main(argv: Sequence[str] | None = None) -> int:
    """Persist a truthful bound receipt for either success or refusal."""
    args = _parse_arguments(argv)
    output = Path(args.output)
    try:
        output.mkdir(parents=True, exist_ok=True)
        if any(output.iterdir()):
            return 1
    except OSError:
        sys.stderr.write("Probe refused: Local I/O failure\n")
        return 1
    identity = _observed_context(os.environ)
    receipt: ProbeReceipt | Prefix7Receipt = Prefix7Receipt(identity) if args.stage == "prefix7" else _receipt(identity)
    succeeded = False
    try:
        _check(os.environ.get("EXPECTED_MANIFEST_SHA256") == MANIFEST_SHA256, "Expected manifest mismatch")
        context = RunContext.from_env(os.environ, args.stage, args.expected_executor)
        manifest = Manifest.load(ROOT / "ci/recovery/pr785-signing-inputs.json")
        api = GitHubAPI(os.environ.get("GH_TOKEN", ""), output)
        runner = Prefix7(manifest, context, api) if context.stage == "prefix7" else Probe(manifest, context, api)
        receipt = runner.receipt
        runner.run()
        succeeded = True
    except ProbeRefusalError as error:
        sys.stderr.write(f"Probe refused: {error}\n")
    except OSError:
        sys.stderr.write("Probe refused: Local I/O failure\n")
    try:
        wire = receipt.as_json() if isinstance(receipt, Prefix7Receipt) else receipt
        serialized = json.dumps(wire, indent=2) + "\n"
    except (TypeError, ValueError):
        sys.stderr.write("Probe refused: Evidence serialization failed\n")
        return 1
    try:
        with (output / "receipt.json").open("x", encoding="utf-8") as stream:
            stream.write(serialized)
    except OSError:
        sys.stderr.write("Probe refused: Local I/O failure\n")
        return 1
    return 0 if succeeded else 1


if __name__ == "__main__":
    sys.exit(main())

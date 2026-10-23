"""Create and verify the two bounded PR785 probe objects from an approved CI run."""

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
from dataclasses import dataclass
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
class Manifest:
    repository: str
    main: str
    old_head: str
    branch: str
    main_tree: str
    probe_tree: str
    probe_path: str
    probe_content: str

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

    @classmethod
    @beartype
    @require(lambda env: isinstance(env, Mapping))
    @ensure(lambda result: isinstance(result, RunContext) and result.run_id > 0 and result.run_attempt > 0)
    def from_env(cls, env: Mapping[str, str], stage: str, expected_executor: str) -> RunContext:
        """Reject every environment mismatch before constructing an API client."""
        _check(stage == "probe", "Only probe is authorized")
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
) -> VerifiedObject:
    sha = _sha(_field(record, "sha"))
    _check(expected_sha is None or sha == expected_sha, "Commit readback identity mismatch")
    _check(_field(record, "tree", "sha") == intent.tree, "Commit tree mismatch")
    parents = _field(record, "parents")
    _check(isinstance(parents, list) and len(parents) == 1, "Commit must have one parent")
    _check(_field(parents[0], "sha") == intent.parent, "Commit parent mismatch")
    _check(_field(record, "message") == intent.message, "Commit message mismatch")
    _verify_signature(record, intent)
    return {
        "sha": sha,
        "tree": intent.tree,
        "parent": intent.parent,
        "message": intent.message,
        "signature": _string(_field(record, "verification", "signature")),
        "payload": _string(_field(record, "verification", "payload")),
        "signed_object_verified": True,
    }


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


class Probe:
    @beartype
    def __init__(self, manifest: Manifest, context: RunContext, api: RequestAPI) -> None:
        self._manifest = manifest
        self._context = context
        self._api = api
        self.receipt = _receipt(
            {
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
        )

    @beartype
    @require(lambda self: isinstance(self, Probe) and not self.receipt["objects"])
    @ensure(lambda result: result["status"] == "signed_objects_verified" and len(result["objects"]) == 2)
    def run(self) -> ProbeReceipt:
        """Verify the live run, then create and reread the two approved objects."""
        self._verify_run()
        self.receipt["context_verified"] = True
        self._verify_prepared_tree()
        self._create_commit(self._manifest.main_tree, "baseline")
        self._create_commit(self._manifest.probe_tree, "inert-workflow")
        self.receipt["status"] = "signed_objects_verified"
        return self.receipt

    def _verify_run(self) -> None:
        run = self._api.request("GET", f"/actions/runs/{self._context.run_id}", None)
        expected = {
            "id": self._context.run_id,
            "run_attempt": self._context.run_attempt,
            "head_sha": self._context.executor_sha,
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

    def _guard_refs(self) -> None:
        main_ref = self._api.request("GET", "/git/ref/heads/main", None)
        _check(_field(main_ref, "object", "sha") == self._manifest.main, "Main has drifted")
        pr = self._api.request("GET", "/pulls/785", None)
        _check(_field(pr, "state") == "open", "Pull request is not open")
        _check(_field(pr, "merged") is False, "Pull request is merged")
        _check(_field(pr, "auto_merge") is None, "Auto-merge is enabled")
        for side, sha, ref in (
            ("base", self._manifest.main, "main"),
            ("head", self._manifest.old_head, self._manifest.branch),
        ):
            _check(_field(pr, side, "sha") == sha, "Pull request revision drift")
            _check(_field(pr, side, "ref") == ref, "Pull request branch drift")
            _check(_field(pr, side, "repo", "full_name") == REPOSITORY, "Pull request repository drift")

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
        context = self._context
        message = (
            f"PR785 signing probe {label}\n\nManifest: {MANIFEST_SHA256}\n"
            f"Executor: {context.executor_sha}\nRun: {context.run_id}\nAttempt: {context.run_attempt}"
        )
        intent = _CommitIntent(tree, self._manifest.main, message)
        self._guard_refs()
        result = self._api.request(
            "POST", "/git/commits", {"message": message, "tree": tree, "parents": [intent.parent]}
        )
        self._guard_refs()
        created = _verified_commit(result, intent)
        sha = created["sha"]
        readback = self._api.request("GET", f"/git/commits/{sha}", None)
        verified = _verified_commit(readback, intent, sha)
        _check(verified == created, "Commit readback differs")
        _verify_attribution(self._api.request("GET", f"/commits/{sha}", None), sha)
        self.receipt["objects"].append(verified)


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
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        return 1
    receipt = _receipt(_observed_context(os.environ))
    try:
        _check(os.environ.get("EXPECTED_MANIFEST_SHA256") == MANIFEST_SHA256, "Expected manifest mismatch")
        context = RunContext.from_env(os.environ, args.stage, args.expected_executor)
        manifest = Manifest.load(ROOT / "ci/recovery/pr785-signing-inputs.json")
        probe = Probe(manifest, context, GitHubAPI(os.environ.get("GH_TOKEN", ""), output))
        receipt = probe.receipt
        probe.run()
    except ProbeRefusalError as error:
        sys.stderr.write(f"Probe refused: {error}\n")
        receipt["status"] = "refused"
    except OSError:
        sys.stderr.write("Probe refused: Local I/O failure\n")
        receipt["status"] = "refused"
    with (output / "receipt.json").open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(receipt, indent=2) + "\n")
    return 0 if receipt["status"] == "signed_objects_verified" else 1


if __name__ == "__main__":
    sys.exit(main())

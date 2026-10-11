"""Resolve native-stack proof boundaries using only authenticated GitHub data."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.parse
from collections.abc import Callable
from pathlib import Path
from typing import NamedTuple, NoReturn, cast


REPOSITORY = "nold-ai/specfact-cli"
REPOSITORY_ID = 1085706003
PROTECTED_BASES = frozenset({"dev", "main"})
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
REF_PATTERN = re.compile(r"^[^\x00-\x20\x7f~^:?*\[\\]+$")
INVALID_REF_COMPONENT_PATTERN = re.compile(r"(?:^|/)(?:\.|[^/]*\.lock(?:/|$))")
MAX_STACK_SIZE = 50
MAX_INPUT_BYTES = 5_000_000
ApiReader = Callable[[str], object]


class PullBoundary(NamedTuple):
    """Exact repository-local branch identities for one live pull request."""

    number: int
    head_ref: str
    head_sha: str
    base_ref: str
    base_sha: str


class NativeStack(NamedTuple):
    """GitHub-owned stack identity and protected root boundary."""

    identifier: int
    number: int
    size: int
    position: int
    base_ref: str
    base_sha: str


def _reject() -> NoReturn:
    raise ValueError("stack-context-invalid")


def _object(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        _reject()
    return cast(dict[str, object], value)


def _positive_integer(value: object) -> int:
    if type(value) is not int or cast(int, value) <= 0:
        _reject()
    return cast(int, value)


def _sha(value: object) -> str:
    if not isinstance(value, str) or SHA_PATTERN.fullmatch(value) is None:
        _reject()
    return value


def _ref(value: object) -> str:
    if (
        not isinstance(value, str)
        or REF_PATTERN.fullmatch(value) is None
        or value == "HEAD"
        or value.startswith(("-", "/"))
        or ".." in value
        or "//" in value
        or "@{" in value
        or value.endswith(("/", "."))
        or INVALID_REF_COMPONENT_PATTERN.search(value) is not None
    ):
        _reject()
    return value


def _repository(value: object) -> None:
    repository = _object(value)
    if repository.get("full_name") != REPOSITORY or repository.get("id") != REPOSITORY_ID:
        _reject()


def _pull(value: object) -> PullBoundary:
    pull = _object(value)
    head, base = _object(pull.get("head")), _object(pull.get("base"))
    _repository(head.get("repo"))
    _repository(base.get("repo"))
    if pull.get("state") != "open":
        _reject()
    return PullBoundary(
        _positive_integer(pull.get("number")),
        _ref(head.get("ref")),
        _sha(head.get("sha")),
        _ref(base.get("ref")),
        _sha(base.get("sha")),
    )


def _stack(value: object) -> NativeStack:
    stack = _object(value)
    base = _object(stack.get("base"))
    identity = NativeStack(
        _positive_integer(stack.get("id")),
        _positive_integer(stack.get("number")),
        _positive_integer(stack.get("size")),
        _positive_integer(stack.get("position")),
        _ref(base.get("ref")),
        _sha(base.get("sha")),
    )
    if identity.position > identity.size or identity.size > MAX_STACK_SIZE or identity.base_ref not in PROTECTED_BASES:
        _reject()
    return identity


def _parent_payload(child: PullBoundary, get_json: ApiReader) -> dict[str, object]:
    query = urllib.parse.urlencode({"state": "open", "head": "nold-ai:" + child.base_ref, "per_page": 100})
    candidates = get_json(f"/repos/{REPOSITORY}/pulls?{query}")
    if not isinstance(candidates, list) or len(candidates) != 1:
        _reject()
    return _object(candidates[0])


def _verified_parent(child_payload: dict[str, object], get_json: ApiReader) -> dict[str, object]:
    child = _pull(child_payload)
    child_stack = _stack(child_payload.get("stack"))
    parent_payload = _parent_payload(child, get_json)
    parent = _pull(parent_payload)
    parent_stack = _stack(parent_payload.get("stack"))
    if (
        child.base_ref != parent.head_ref
        or child.base_sha != parent.head_sha
        or child_stack.position != parent_stack.position + 1
        or child_stack[:3] != parent_stack[:3]
        or child_stack[4:] != parent_stack[4:]
    ):
        _reject()
    comparison = _object(get_json(f"/repos/{REPOSITORY}/compare/{parent.head_sha}...{child.head_sha}"))
    if (
        comparison.get("status") not in {"ahead", "identical"}
        or _object(comparison.get("merge_base_commit")).get("sha") != parent.head_sha
    ):
        _reject()
    return parent_payload


def _member_record(payload: dict[str, object]) -> dict[str, object]:
    member = _pull(payload)
    return {
        "pull_request": member.number,
        "head_branch": member.head_ref,
        "head_commit": member.head_sha,
        "base_ref": member.base_ref,
        "base_commit": member.base_sha,
    }


def _root_payload(members: list[dict[str, object]], get_json: ApiReader) -> dict[str, object]:
    while _pull(members[-1]).base_ref not in PROTECTED_BASES:
        if len(members) >= MAX_STACK_SIZE:
            _reject()
        members.append(_verified_parent(members[-1], get_json))
    root = members[-1]
    root_boundary = _pull(root)
    if root.get("stack") is not None:
        root_stack = _stack(root["stack"])
        if (
            root_stack.position != 1
            or root_stack.base_ref != root_boundary.base_ref
            or root_stack.base_sha != root_boundary.base_sha
        ):
            _reject()
    return root


def resolve_stack_context(event: dict[str, object], get_json: ApiReader) -> dict[str, object]:
    """Fail closed unless live native ancestry matches the exact workflow event."""
    _repository(event.get("repository"))
    expected = _pull(event.get("pull_request"))
    live_payload = _object(get_json(f"/repos/{REPOSITORY}/pulls/{expected.number}"))
    current = _pull(live_payload)
    if current != expected:
        _reject()
    members = [live_payload]
    root_payload = _root_payload(members, get_json)
    root = _pull(root_payload)
    return {
        "schema_version": 1,
        "repository": REPOSITORY,
        "repository_id": REPOSITORY_ID,
        **_member_record(live_payload),
        "proof_base_ref": root.base_ref,
        "proof_base_commit": root.base_sha,
        "proof_head_branch": root.head_ref,
        "proof_head_commit": root.head_sha,
        "proof_pull_request": root.number,
        "stack": live_payload.get("stack"),
        "members": [_member_record(member) for member in reversed(members)],
    }


def _github_json(path: str) -> object:
    result = subprocess.run(
        ["gh", "api", "--hostname", "github.com", path], capture_output=True, check=True, timeout=30
    )
    if len(result.stdout) > MAX_INPUT_BYTES:
        _reject()
    return cast(object, json.loads(result.stdout))


def main(argv: list[str] | None = None) -> int:
    """Write a deterministic context without executing any pull-request bytes."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.event.is_symlink() or args.event.stat().st_size > MAX_INPUT_BYTES:
            _reject()
        event = _object(json.loads(args.event.read_text()))
        context = resolve_stack_context(event, _github_json)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(context, indent=2, sort_keys=True) + "\n")
    except (OSError, ValueError, subprocess.SubprocessError):
        sys.stderr.write("stack-context-invalid\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

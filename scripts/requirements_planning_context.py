"""Authenticate closed planning layers above independently verified native roots."""

from __future__ import annotations

import os
import re
import subprocess
from collections.abc import Callable
from typing import NamedTuple, cast


REPOSITORY = "nold-ai/specfact-cli"
REPOSITORY_ID = 1085706003
ACTIONS_APP_ID = 15368
MAX_CHECK_PAGES = 50
RAW_ENTRY = re.compile(r":([0-7]{6}) ([0-7]{6}) [0-9a-f]{40} [0-9a-f]{40} [AMDT]")
SOURCE_PATH = re.compile(r"openspec/changes/([a-z0-9][a-z0-9-]*)/")
PLANNING_PATH = re.compile(
    r"openspec/(?:[A-Za-z0-9][A-Za-z0-9_.-]*\.md|changes/[A-Za-z0-9_.-]+/"
    r"(?:[A-Za-z0-9_.-]+/)*(?:[A-Za-z0-9_.-]+\.md|requirements-evidence\.yaml|\.openspec\.yaml))"
)
RUN_URL = re.compile(r"https://github\.com/nold-ai/specfact-cli/actions/runs/([1-9][0-9]*)/job/([1-9][0-9]*)")
ApiReader = Callable[[str], object]


class GitChange(NamedTuple):
    """Both immutable file modes and a non-renamed path in a Git object diff."""

    old_mode: str
    new_mode: str
    path: str


class RequiredWorkflow(NamedTuple):
    """Protected, repository-specific workflow identity for inherited proof."""

    check_name: str
    name: str
    identifier: int
    path: str


WORKFLOWS = (
    RequiredWorkflow(
        "Requirements evidence", "Requirements Evidence", 323253915, ".github/workflows/requirements-evidence.yml"
    ),
    RequiredWorkflow(
        "Trusted Requirements Authority",
        "Trusted Requirements Authority",
        348163848,
        ".github/workflows/trusted-requirements-authority.yml",
    ),
)


def _object(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ValueError("planning-context-invalid")
    return cast(dict[str, object], value)


def _positive_integer(value: object) -> int:
    if type(value) is not int or cast(int, value) <= 0:
        raise ValueError("planning-context-invalid")
    return cast(int, value)


def _git_changes(base: str, head: str) -> list[GitChange]:
    """Read all source/destination changes as independent NUL-delimited Git paths."""
    result = subprocess.run(
        ["git", "diff", "--raw", "--no-renames", "--no-ext-diff", "--no-textconv", "--abbrev=40", "-z", base, head],
        capture_output=True,
        check=True,
        timeout=20,
    )
    entries = result.stdout.split(b"\x00")
    if entries.pop() != b"" or len(entries) % 2:
        raise ValueError("planning-context-invalid")
    changes: list[GitChange] = []
    for index in range(0, len(entries), 2):
        metadata = RAW_ENTRY.fullmatch(entries[index].decode("ascii"))
        if metadata is None:
            raise ValueError("planning-context-invalid")
        path = os.fsdecode(entries[index + 1])
        changes.append(GitChange(metadata[1], metadata[2], path))
    return changes


def _eligible_planning_paths(context: dict[str, object]) -> bool:
    root = cast(str, context["proof_head_commit"])
    head = cast(str, context["head_commit"])
    if root == head:
        return False
    root_changes = _git_changes(cast(str, context["proof_base_commit"]), root)
    if any(change.path.startswith(".github/actions/") or change.path == WORKFLOWS[0].path for change in root_changes):
        return False
    covered_sources = {
        match[0]
        for change in root_changes
        if (match := SOURCE_PATH.match(change.path)) is not None and match[1] != "archive"
    }
    if not covered_sources:
        return False
    changes = _git_changes(root, head)
    return bool(changes) and all(_planning_change(change, covered_sources) for change in changes)


def _planning_change(change: GitChange, covered_sources: set[str]) -> bool:
    """A name alone cannot authorize an executable, symlink or inherited-source edit."""
    if change.old_mode not in {"000000", "100644"} or change.new_mode not in {"000000", "100644"}:
        return False
    if PLANNING_PATH.fullmatch(change.path) is None or any(part in {".", ".."} for part in change.path.split("/")):
        return False
    return not any(change.path.startswith(prefix) for prefix in covered_sources)


def _check_page(payload: dict[str, object], previous_total: int | None) -> tuple[int, list[dict[str, object]]]:
    """Validate page shape and a stable listing count independently of pagination."""
    count, records = payload.get("total_count"), payload.get("check_runs")
    if type(count) is not int or cast(int, count) < 0 or not isinstance(records, list):
        raise ValueError("planning-context-invalid")
    if previous_total is not None and count != previous_total:
        raise ValueError("planning-context-invalid")
    return cast(int, count), [_object(record) for record in records]


def _complete_checks(checks: list[dict[str, object]], total: int) -> list[dict[str, object]]:
    """Reject overfull listings and duplicates before choosing any successful check."""
    if len(checks) != total or len({_positive_integer(check.get("id")) for check in checks}) != total:
        raise ValueError("planning-context-invalid")
    return checks


def _root_checks(root: str, get_json: ApiReader) -> list[dict[str, object]]:
    """Read a complete check listing and fail closed on races or truncation."""
    checks: list[dict[str, object]] = []
    total = None
    for page in range(1, MAX_CHECK_PAGES + 1):
        payload = _object(
            get_json(f"/repos/{REPOSITORY}/commits/{root}/check-runs?filter=all&per_page=100&page={page}")
        )
        total, records = _check_page(payload, total)
        checks.extend(records)
        if len(checks) >= total:
            return _complete_checks(checks, total)
        if len(records) != 100:
            raise ValueError("planning-context-invalid")
    raise ValueError("planning-context-invalid")


def _latest_check(checks: list[dict[str, object]], workflow: RequiredWorkflow, root: str) -> dict[str, object]:
    matching = [
        check
        for check in checks
        if check.get("name") == workflow.check_name
        and _object(check.get("app")).get("id") == ACTIONS_APP_ID
        and _object(check.get("app")).get("slug") == "github-actions"
    ]
    if not matching:
        raise ValueError("planning-context-invalid")
    check = max(matching, key=lambda record: _positive_integer(record.get("id")))
    if check.get("head_sha") != root or check.get("status") != "completed" or check.get("conclusion") != "success":
        raise ValueError("planning-context-invalid")
    return check


def _repository_matches(value: object) -> bool:
    repository = _object(value)
    return repository.get("id") == REPOSITORY_ID and repository.get("full_name") == REPOSITORY


def _verified_run(
    check: dict[str, object],
    workflow: RequiredWorkflow,
    context: dict[str, object],
    get_json: ApiReader,
) -> dict[str, object]:
    details_url = check.get("details_url")
    match = RUN_URL.fullmatch(details_url) if isinstance(details_url, str) else None
    if match is None or int(match[2]) != _positive_integer(check.get("id")):
        raise ValueError("planning-context-invalid")
    run_id = int(match[1])
    run = _object(get_json(f"/repos/{REPOSITORY}/actions/runs/{run_id}"))
    expected = {
        "id": run_id,
        "name": workflow.name,
        "workflow_id": workflow.identifier,
        "path": workflow.path,
        "head_sha": context["proof_head_commit"],
        "head_branch": context["proof_head_branch"],
        "event": "pull_request",
        "status": "completed",
        "conclusion": "success",
    }
    if any(run.get(key) != value for key, value in expected.items()):
        raise ValueError("planning-context-invalid")
    if not _repository_matches(run.get("repository")) or not _repository_matches(run.get("head_repository")):
        raise ValueError("planning-context-invalid")
    if run.get("check_suite_id") != _positive_integer(_object(check.get("check_suite")).get("id")):
        raise ValueError("planning-context-invalid")
    pulls = run.get("pull_requests")
    if not isinstance(pulls, list) or not any(
        _object(pull).get("number") == context["proof_pull_request"] for pull in pulls
    ):
        raise ValueError("planning-context-invalid")
    return {
        "check_name": workflow.check_name,
        "check_id": _positive_integer(check.get("id")),
        "run_id": run_id,
        "run_attempt": _positive_integer(run.get("run_attempt")),
    }


def _resolve_planning_context(context: dict[str, object], get_json: ApiReader) -> dict[str, object]:
    """Append a planning diff boundary only after closed scope and exact-root proof authenticate."""
    if not _eligible_planning_paths(context):
        return context
    root = cast(str, context["proof_head_commit"])
    commit = _object(get_json(f"/repos/{REPOSITORY}/commits/{root}"))
    verification = _object(_object(commit.get("commit")).get("verification"))
    if commit.get("sha") != root or verification.get("verified") is not True:
        raise ValueError("planning-context-invalid")
    checks = _root_checks(root, get_json)
    proof = [
        _verified_run(_latest_check(checks, workflow, root), workflow, context, get_json) for workflow in WORKFLOWS
    ]
    return {**context, "planning_base_commit": root, "inherited_proof": {"head_commit": root, "checks": proof}}


# Explicit stdlib-only entry point loaded from the protected Git archive.
PLANNING_RESOLVER: Callable[[dict[str, object], ApiReader], dict[str, object]] = _resolve_planning_context

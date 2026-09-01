"""Authenticate a prior green Requirements run as an amendment-cycle base."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import cast

from beartype import beartype
from icontract import ensure


GIT_OBJECT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
ALLOWED_RED_HISTORY_PREFIXES = (
    "test/",
    "tests/",
)
CHANGE_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
ALLOWED_RED_OPEN_SPEC_FILES = {
    ".openspec.yaml",
    "CHANGE_VALIDATION.md",
    "README.md",
    "TDD_EVIDENCE.md",
    "design.md",
    "proposal.md",
    "requirements-evidence.yaml",
    "requirements-proof/review-evidence.json",
    "tasks.md",
}
EVIDENCE_AUTHORITY_FILES = {
    ".github/actions/setup-frozen-python/action.yml",
    ".github/workflows/pr-orchestrator.yml",
    ".github/workflows/requirements-evidence.yml",
    "ci/module-fixture.lock.json",
    "pyproject.toml",
    "scripts/check_doc_frontmatter.py",
    "scripts/check_license_compliance.py",
    "scripts/license_scope_policy.py",
    "uv.lock",
}
EVIDENCE_AUTHORITY_PREFIXES = ("requirements/", "scripts/requirements_", "src/specfact_cli/")
EXTERNAL_AUTHORITY_KIND = "externally-approved-amendment-bootstrap"
EXTERNAL_AUTHORITY_COMMENT_ID = 5468600336
EXTERNAL_AUTHORITY_REPOSITORY = "nold-ai/specfact-cli"
EXTERNAL_AUTHORITY_CHANGE_ID = "fix-release-promotion-security-gates"
EXTERNAL_AUTHORITY_ISSUE = 692
EXTERNAL_AUTHORITY_PULL_REQUEST = 698
EXTERNAL_AUTHORITY_BRANCH = "codex/692-computed-owner-red-proof-v2"
FINAL_PRODUCER_AUTHORITY_HEADER = "SPECFACT_REQUIREMENTS_FINAL_PRODUCER_AUTHORITY_V1"
FINAL_PRODUCER_AUTHORITY_KIND = "requirements-final-producer-authority"
FINAL_PRODUCER_AUTHORITY_FIELDS = {
    "authority_version",
    "capability",
    "repository",
    "issue",
    "pull_request",
    "head_branch",
    "change_id",
    "approved_commit",
    "approved_tree",
    "external_authority_digest",
    "producer_blobs",
    "expires_at",
    "signer_login",
}


@dataclass(frozen=True)
class CycleBasePaths:
    """Immutable metadata and artifact inputs for one candidate run."""

    run: Path
    artifacts: Path
    artifact_root: Path
    repo_root: Path


@dataclass(frozen=True)
class CycleBaseContext:
    """Current pull-request identity and Git boundary."""

    base_ref: str
    final_ref: str
    repository: str
    pull_request: int
    head_branch: str
    change_id: str


@dataclass(frozen=True)
class TrustedCycle:
    """A cycle base produced only after run, artifact, and history validation."""

    cycle_base: str
    run_id: int
    artifact_id: int
    artifact_digest: str


@dataclass(frozen=True)
class _ExternalAuthority:
    """Independently supplied live digest and its exact validated receipt."""

    digest: str
    receipt: Mapping[str, object]


@dataclass(frozen=True)
class _FinalAuthorityBoundary:
    """Git and capability inputs for final producer-byte validation."""

    repo_root: Path
    context: CycleBaseContext
    red_ref: str
    external_authority_digest: str


def _read_object(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("amendment-cycle-authority-invalid")
    return cast(dict[str, object], value)


def _git(repo_root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *arguments], cwd=repo_root, capture_output=True, check=False, text=True)


def _is_ancestor(repo_root: Path, ancestor: str, descendant: str) -> bool:
    return _git(repo_root, "merge-base", "--is-ancestor", ancestor, descendant).returncode == 0


def _history_is_linear(repo_root: Path, start_ref: str, end_ref: str) -> bool:
    merges = _git(repo_root, "rev-list", "--merges", f"{start_ref}..{end_ref}")
    return merges.returncode == 0 and not merges.stdout.strip()


def _has_governed_cycle_change(repo_root: Path, start_ref: str, end_ref: str, change_id: str) -> bool:
    """Return whether the proposed red segment contains a non-allowlisted path."""
    changed = _git(
        repo_root,
        "log",
        "--format=",
        "--name-only",
        "--no-renames",
        "-z",
        "--end-of-options",
        f"{start_ref}..{end_ref}",
    )
    if changed.returncode:
        return True
    return any(not _red_history_path_is_allowed(path, change_id) for path in changed.stdout.split("\0") if path)


def _red_history_path_is_allowed(path: str, change_id: str) -> bool:
    """Allow test roots and declarative artifacts for the linked OpenSpec change."""
    if path.startswith(ALLOWED_RED_HISTORY_PREFIXES):
        return True
    if CHANGE_ID_PATTERN.fullmatch(change_id) is None:
        return False
    change_prefix = f"openspec/changes/{change_id}/"
    if not path.startswith(change_prefix):
        return False
    relative = path.removeprefix(change_prefix)
    return relative in ALLOWED_RED_OPEN_SPEC_FILES or (
        relative.startswith("specs/") and Path(relative).name == "spec.md"
    )


def _has_self_authored_evidence_authority(repo_root: Path, base_ref: str, cycle_base: str) -> bool:
    """Return whether a candidate green head changed its own evidence authority."""
    changed = _git(repo_root, "diff", "--name-only", f"{base_ref}...{cycle_base}")
    if changed.returncode:
        return True
    return any(_is_evidence_authority_path(path) for path in changed.stdout.splitlines())


def _is_evidence_authority_path(path: str) -> bool:
    """Return whether one repository path can influence Requirements evidence."""
    return path in EVIDENCE_AUTHORITY_FILES or path.startswith(EVIDENCE_AUTHORITY_PREFIXES)


def _changed_evidence_authority_paths(repo_root: Path, start_ref: str, end_ref: str) -> set[str] | None:
    """Return the complete evidence-authority path set changed in one range."""
    changed = _git(repo_root, "diff", "--name-only", "--find-renames", start_ref, end_ref)
    if changed.returncode:
        return None
    return {path for path in changed.stdout.splitlines() if _is_evidence_authority_path(path)}


def _blob_identity(repo_root: Path, commit: str, path: str) -> str | None:
    """Return an exact regular Git blob identity at one commit."""
    identity = _git(repo_root, "rev-parse", f"{commit}:{path}")
    blob = identity.stdout.strip()
    if identity.returncode or GIT_OBJECT_PATTERN.fullmatch(blob) is None:
        return None
    object_type = _git(repo_root, "cat-file", "-t", blob)
    return blob if object_type.returncode == 0 and object_type.stdout.strip() == "blob" else None


def _comment_objects(path: Path) -> list[dict[str, object]]:
    """Flatten one GitHub issue-comment page or paginated page list."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    pages = payload if isinstance(payload, list) else []
    values = [item for page in pages for item in (page if isinstance(page, list) else [page])]
    return [cast(dict[str, object], value) for value in values if isinstance(value, dict)]


def _authority_payload(comment: Mapping[str, object]) -> dict[str, object] | None:
    """Parse one canonical unedited repository-member authority comment."""
    body = comment.get("body")
    user = comment.get("user")
    if (
        not isinstance(body, str)
        or not isinstance(user, Mapping)
        or comment.get("author_association") not in {"COLLABORATOR", "MEMBER", "OWNER"}
        or comment.get("created_at") != comment.get("updated_at")
    ):
        return None
    header, separator, encoded = body.partition("\n")
    if header != FINAL_PRODUCER_AUTHORITY_HEADER or not separator:
        return None
    try:
        decoded = json.loads(encoded)
    except json.JSONDecodeError:
        return None
    if not isinstance(decoded, dict) or set(decoded) != FINAL_PRODUCER_AUTHORITY_FIELDS:
        return None
    authority = cast(dict[str, object], decoded)
    typed_user = cast(Mapping[str, object], user)
    canonical = json.dumps(authority, sort_keys=True, separators=(",", ":"))
    if encoded != canonical or authority.get("signer_login") != typed_user.get("login"):
        return None
    return authority


def _authority_time_is_valid(authority: Mapping[str, object], comment: Mapping[str, object]) -> bool:
    """Require a live capability whose lifetime is bounded by its comment time."""
    try:
        created = datetime.fromisoformat(str(comment.get("created_at")).replace("Z", "+00:00"))
        expiry = datetime.fromisoformat(str(authority.get("expires_at")).replace("Z", "+00:00"))
    except ValueError:
        return False
    return created <= datetime.now(UTC) < expiry <= created + timedelta(days=7)


def _producer_blob_map(value: object) -> dict[str, str] | None:
    """Return a canonical non-empty repository-path to Git-blob mapping."""
    if not isinstance(value, dict) or not value:
        return None
    blobs = cast(dict[object, object], value)
    if not all(
        isinstance(path, str)
        and path
        and not Path(path).is_absolute()
        and ".." not in Path(path).parts
        and isinstance(blob, str)
        and GIT_OBJECT_PATTERN.fullmatch(blob) is not None
        for path, blob in blobs.items()
    ):
        return None
    return cast(dict[str, str], blobs)


def _final_authority_matches(
    authority: Mapping[str, object],
    comment: Mapping[str, object],
    boundary: _FinalAuthorityBoundary,
) -> bool:
    """Bind the exact approved producer bytes and reject later producer drift."""
    repo_root = boundary.repo_root
    context = boundary.context
    red_ref = boundary.red_ref
    approved_commit = authority.get("approved_commit")
    producer_blobs = _producer_blob_map(authority.get("producer_blobs"))
    changed_at_approval = (
        _changed_evidence_authority_paths(repo_root, red_ref, approved_commit)
        if isinstance(approved_commit, str)
        else None
    )
    changed_now = _changed_evidence_authority_paths(repo_root, red_ref, context.final_ref)
    identity_matches = all(
        (
            authority.get("authority_version") == 1,
            authority.get("capability") == "requirements-final-producer",
            authority.get("repository") == context.repository == EXTERNAL_AUTHORITY_REPOSITORY,
            authority.get("issue") == EXTERNAL_AUTHORITY_ISSUE,
            authority.get("pull_request") == context.pull_request == EXTERNAL_AUTHORITY_PULL_REQUEST,
            authority.get("head_branch") == context.head_branch == EXTERNAL_AUTHORITY_BRANCH,
            authority.get("change_id") == context.change_id == EXTERNAL_AUTHORITY_CHANGE_ID,
            authority.get("external_authority_digest") == boundary.external_authority_digest,
            comment.get("issue_url")
            == f"https://api.github.com/repos/{context.repository}/issues/{EXTERNAL_AUTHORITY_ISSUE}",
            _authority_time_is_valid(authority, comment),
            isinstance(approved_commit, str),
            GIT_OBJECT_PATTERN.fullmatch(approved_commit) is not None if isinstance(approved_commit, str) else False,
            authority.get("approved_tree") == _tree_identity(repo_root, approved_commit)
            if isinstance(approved_commit, str)
            else False,
            _is_ancestor(repo_root, red_ref, approved_commit) if isinstance(approved_commit, str) else False,
            _is_ancestor(repo_root, approved_commit, context.final_ref) if isinstance(approved_commit, str) else False,
            producer_blobs is not None,
            changed_at_approval == changed_now == (set(producer_blobs) if producer_blobs is not None else None),
        )
    )
    if not identity_matches or producer_blobs is None or not isinstance(approved_commit, str):
        return False
    return all(
        _blob_identity(repo_root, approved_commit, path) == blob
        and _blob_identity(repo_root, context.final_ref, path) == blob
        for path, blob in producer_blobs.items()
    )


@beartype
@ensure(lambda result: result is None or isinstance(result, dict))
def validated_final_producer_authority(
    comments_path: Path,
    repo_root: Path,
    context: CycleBaseContext,
    red_ref: str,
    external_authority_digest: str,
) -> dict[str, object] | None:
    """Select exactly one live authority for the current producer blob set."""
    matches: list[dict[str, object]] = []
    try:
        for comment in _comment_objects(comments_path):
            authority = _authority_payload(comment)
            if authority is None or not _final_authority_matches(
                authority,
                comment,
                _FinalAuthorityBoundary(repo_root, context, red_ref, external_authority_digest),
            ):
                continue
            canonical = json.dumps(authority, sort_keys=True, separators=(",", ":")).encode()
            matches.append(
                {
                    **authority,
                    "kind": FINAL_PRODUCER_AUTHORITY_KIND,
                    "comment_id": comment.get("id"),
                    "created_at": comment.get("created_at"),
                    "authority_digest": f"sha256:{hashlib.sha256(canonical).hexdigest()}",
                }
            )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError, subprocess.SubprocessError):
        return None
    return matches[0] if len(matches) == 1 else None


_validated_final_producer_authority = validated_final_producer_authority


def _matching_artifact(artifacts: dict[str, object], run_id: int, cycle_base: str) -> dict[str, object] | None:
    candidates = artifacts.get("artifacts")
    if not isinstance(candidates, list):
        return None
    matching: list[dict[str, object]] = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        typed_candidate = cast(dict[str, object], candidate)
        workflow_run = typed_candidate.get("workflow_run")
        if not isinstance(workflow_run, dict):
            continue
        typed_workflow_run = cast(dict[str, object], workflow_run)
        if (
            typed_candidate.get("name") == "requirements-evidence"
            and typed_candidate.get("expired") is False
            and typed_workflow_run.get("id") == run_id
            and typed_workflow_run.get("head_sha") == cycle_base
        ):
            matching.append(typed_candidate)
    return matching[0] if len(matching) == 1 else None


def _artifact_is_verified_final(
    artifact_root: Path, cycle_base: str, *, external_authority_digest: str | None = None
) -> bool:
    report = _read_object(artifact_root / "requirements-evidence.json")
    plan_report = _read_object(artifact_root / "requirements-evidence-plan.json")
    execution = report.get("execution_proof")
    plan = plan_report.get("plan")
    if not isinstance(execution, dict) or not isinstance(plan, dict):
        return False
    typed_execution = cast(dict[str, object], execution)
    typed_plan = cast(dict[str, object], plan)
    mapping_digest = report.get("mapping_digest")
    plan_digest = report.get("plan_digest")
    report_matches = _fields_match(
        report, {"verdict": "passed", "gate_decision": "pass", "observed_maturity": "verified"}
    )
    expected_execution: dict[str, object] = {"run_stage": "final", "source_ref": cycle_base}
    if external_authority_digest is not None:
        expected_execution["cycle_authority_digest"] = external_authority_digest
    execution_matches = _fields_match(typed_execution, expected_execution)
    plan_matches = _fields_match(typed_plan, {"mapping_digest": mapping_digest, "plan_digest": plan_digest})
    return (
        report_matches
        and execution_matches
        and _valid_digest(mapping_digest)
        and _valid_digest(plan_digest)
        and plan_matches
    )


def _fields_match(value: dict[str, object], expected: dict[str, object]) -> bool:
    """Return whether a JSON object has every expected field value."""
    return all(value.get(field) == expected_value for field, expected_value in expected.items())


def _valid_digest(value: object) -> bool:
    """Return whether a JSON value is a canonical SHA-256 digest."""
    return isinstance(value, str) and DIGEST_PATTERN.fullmatch(value) is not None


def _tree_identity(repo_root: Path, commit: str) -> str | None:
    """Return a commit tree identity without accepting an unresolved ref."""
    result = _git(repo_root, "rev-parse", f"{commit}^{{tree}}")
    tree = result.stdout.strip()
    return tree if result.returncode == 0 and GIT_OBJECT_PATTERN.fullmatch(tree) is not None else None


def _external_authority_digest(receipt: Mapping[str, object]) -> str:
    """Recompute the digest of the owner-approved authority payload."""
    payload = {
        key: value
        for key, value in receipt.items()
        if key
        not in {
            "kind",
            "comment_id",
            "cycle_base",
            "red_ref",
            "authority_digest",
            "final_producer_authority",
        }
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return f"sha256:{hashlib.sha256(canonical).hexdigest()}"


def _final_producer_receipt_matches(
    receipt: object,
    repo_root: Path,
    context: CycleBaseContext,
    red_ref: str,
    external_authority_digest: str,
) -> bool:
    """Recheck a live-produced final authority receipt against current Git bytes."""
    if not isinstance(receipt, Mapping):
        return False
    typed = cast(Mapping[str, object], receipt)
    authority = {
        key: value
        for key, value in typed.items()
        if key not in {"kind", "comment_id", "created_at", "authority_digest"}
    }
    canonical = json.dumps(authority, sort_keys=True, separators=(",", ":")).encode()
    synthetic_comment = {
        "created_at": typed.get("created_at"),
        "issue_url": f"https://api.github.com/repos/{context.repository}/issues/{EXTERNAL_AUTHORITY_ISSUE}",
    }
    return all(
        (
            typed.get("kind") == FINAL_PRODUCER_AUTHORITY_KIND,
            isinstance(typed.get("comment_id"), int),
            typed.get("authority_digest") == f"sha256:{hashlib.sha256(canonical).hexdigest()}",
            set(authority) == FINAL_PRODUCER_AUTHORITY_FIELDS,
            _final_authority_matches(
                authority,
                synthetic_comment,
                _FinalAuthorityBoundary(repo_root, context, red_ref, external_authority_digest),
            ),
        )
    )


def _external_receipt_locator_matches(
    receipt: Mapping[str, object], context: CycleBaseContext, authority_digest: str
) -> bool:
    """Validate the expiring receipt's exact immutable approval locator."""
    try:
        expiry = datetime.fromisoformat(str(receipt.get("expires_at")).replace("Z", "+00:00"))
    except ValueError:
        return False
    return all(
        (
            expiry > datetime.now(UTC),
            receipt.get("kind") == EXTERNAL_AUTHORITY_KIND,
            receipt.get("comment_id") == EXTERNAL_AUTHORITY_COMMENT_ID,
            receipt.get("authority_version") == 3,
            receipt.get("producer_bypass") == "stale-red-proof-only",
            receipt.get("repository") == context.repository == EXTERNAL_AUTHORITY_REPOSITORY,
            receipt.get("change_id") == context.change_id == EXTERNAL_AUTHORITY_CHANGE_ID,
            receipt.get("issue") == EXTERNAL_AUTHORITY_ISSUE,
            receipt.get("pull_request") == context.pull_request == EXTERNAL_AUTHORITY_PULL_REQUEST,
            receipt.get("head_branch") == context.head_branch == EXTERNAL_AUTHORITY_BRANCH,
            receipt.get("authority_digest") == authority_digest == _external_authority_digest(receipt),
        )
    )


def _external_receipt_history_matches(
    paths: CycleBasePaths,
    context: CycleBaseContext,
    candidate_green: str,
    receipt: Mapping[str, object],
) -> bool:
    """Bind the approved green/red root and trees to the candidate chain."""
    root_green = receipt.get("cycle_base_commit")
    approved_red = receipt.get("red_commit")
    if not isinstance(root_green, str) or not isinstance(approved_red, str):
        return False
    candidate_context = CycleBaseContext(
        context.base_ref,
        candidate_green,
        context.repository,
        context.pull_request,
        context.head_branch,
        context.change_id,
    )
    common_matches = all(
        (
            receipt.get("cycle_base") == root_green,
            receipt.get("red_ref") == approved_red,
            receipt.get("cycle_base_tree") == _tree_identity(paths.repo_root, root_green),
            receipt.get("red_tree") == _tree_identity(paths.repo_root, approved_red),
            _common_history_matches(paths, candidate_context, root_green, approved_red),
        )
    )
    producer_changed = _has_self_authored_evidence_authority(paths.repo_root, approved_red, candidate_green)
    return common_matches and (
        not producer_changed
        or _final_producer_receipt_matches(
            receipt.get("final_producer_authority"),
            paths.repo_root,
            candidate_context,
            approved_red,
            cast(str, receipt.get("authority_digest")),
        )
    )


def _external_execution_matches(
    artifact_root: Path,
    candidate_green: str,
    receipt: Mapping[str, object],
    authority_digest: str,
) -> bool:
    """Bind a candidate verified artifact to the exact external root receipt."""
    report = _read_object(artifact_root / "requirements-evidence.json")
    execution = report.get("execution_proof")
    if not isinstance(execution, dict):
        return False
    typed_execution = cast(dict[str, object], execution)
    return _fields_match(
        typed_execution,
        {
            "run_stage": "final",
            "source_ref": candidate_green,
            "cycle_authority_digest": authority_digest,
            "cycle_base": receipt.get("cycle_base_commit"),
            "prior_green_run_id": receipt.get("prior_green_run_id"),
            "prior_green_artifact_id": receipt.get("prior_green_artifact_id"),
            "prior_green_artifact_digest": receipt.get("prior_green_artifact_digest"),
        },
    )


def _pull_request_numbers(value: object) -> list[object] | None:
    """Return pull-request numbers from a workflow run identity."""
    return (
        [cast(dict[str, object], item).get("number") for item in value if isinstance(item, dict)]
        if isinstance(value, list)
        else None
    )


def _run_identity(run: dict[str, object], context: CycleBaseContext) -> tuple[int, str] | None:
    """Return an authenticated successful run identity for this pull request."""
    run_id = run.get("id")
    cycle_base = run.get("head_sha")
    repository = run.get("repository")
    numbers = _pull_request_numbers(run.get("pull_requests"))
    if not isinstance(repository, dict) or numbers is None:
        return None
    typed_repository = cast(dict[str, object], repository)
    run_matches = _fields_match(
        run,
        {
            "event": "pull_request",
            "status": "completed",
            "conclusion": "success",
            "name": "Requirements Evidence",
            "head_branch": context.head_branch,
        },
    )
    valid_identity = (
        isinstance(run_id, int) and isinstance(cycle_base, str) and GIT_OBJECT_PATTERN.fullmatch(cycle_base) is not None
    )
    exact_pr = typed_repository.get("full_name") == context.repository and numbers == [context.pull_request]
    return cast(tuple[int, str], (run_id, cycle_base)) if run_matches and valid_identity and exact_pr else None


def _common_history_matches(paths: CycleBasePaths, context: CycleBaseContext, cycle_base: str, red_ref: str) -> bool:
    """Validate every cycle boundary except the producer-authorship predicate."""
    return (
        cycle_base != context.final_ref
        and _is_ancestor(paths.repo_root, context.base_ref, cycle_base)
        and GIT_OBJECT_PATTERN.fullmatch(red_ref) is not None
        and _is_ancestor(paths.repo_root, cycle_base, red_ref)
        and _is_ancestor(paths.repo_root, red_ref, context.final_ref)
        and _history_is_linear(paths.repo_root, cycle_base, context.final_ref)
        and not _has_governed_cycle_change(paths.repo_root, cycle_base, red_ref, context.change_id)
    )


@beartype
@ensure(lambda result: isinstance(result, bool))
def red_history_is_test_only(repo_root: Path, cycle_base: str, red_ref: str, change_id: str) -> bool:
    """Return whether one linear red extension changes only tests and its bound OpenSpec artifacts."""
    return (
        GIT_OBJECT_PATTERN.fullmatch(cycle_base) is not None
        and GIT_OBJECT_PATTERN.fullmatch(red_ref) is not None
        and cycle_base != red_ref
        and _is_ancestor(repo_root, cycle_base, red_ref)
        and _history_is_linear(repo_root, cycle_base, red_ref)
        and not _has_governed_cycle_change(repo_root, cycle_base, red_ref, change_id)
    )


def _history_matches(
    paths: CycleBasePaths,
    context: CycleBaseContext,
    cycle_base: str,
    red_ref: str,
    *,
    external_authority: _ExternalAuthority | None = None,
) -> bool:
    """Validate an ordinary cycle, including independent producer authority."""
    if not _common_history_matches(paths, context, cycle_base, red_ref):
        return False
    if not _has_self_authored_evidence_authority(paths.repo_root, context.base_ref, cycle_base):
        return True
    return (
        external_authority is not None
        and _external_receipt_locator_matches(external_authority.receipt, context, external_authority.digest)
        and _external_receipt_history_matches(paths, context, cycle_base, external_authority.receipt)
        and _external_execution_matches(
            paths.artifact_root,
            cycle_base,
            external_authority.receipt,
            external_authority.digest,
        )
    )


def _trusted_artifact(artifacts: dict[str, object], run_id: int, cycle_base: str) -> tuple[int, str] | None:
    """Return the unique non-expired artifact identity when its digest is valid."""
    artifact = _matching_artifact(artifacts, run_id, cycle_base)
    artifact_id, artifact_digest = (
        (artifact.get("id"), artifact.get("digest")) if artifact is not None else (None, None)
    )
    valid = (
        isinstance(artifact_id, int)
        and isinstance(artifact_digest, str)
        and DIGEST_PATTERN.fullmatch(artifact_digest) is not None
    )
    return cast(tuple[int, str], (artifact_id, artifact_digest)) if valid else None


@beartype
@ensure(lambda result: result is None or isinstance(result, TrustedCycle))
def validated_cycle_base(
    paths: CycleBasePaths,
    context: CycleBaseContext,
    *,
    red_ref: str | None = None,
    external_authority_digest: str | None = None,
    external_authority_receipt: Mapping[str, object] | None = None,
) -> TrustedCycle | None:
    """Return a trusted prior green head, or fail closed for any mismatch."""
    try:
        effective_red_ref = red_ref or context.final_ref
        external_authority = (
            _ExternalAuthority(external_authority_digest, external_authority_receipt)
            if external_authority_digest is not None and external_authority_receipt is not None
            else None
        )
        run = _read_object(paths.run)
        artifacts = _read_object(paths.artifacts)
        identity = _run_identity(run, context)
        if identity is None:
            return None
        run_id, cycle_base = identity
        if (
            (external_authority_digest is not None and DIGEST_PATTERN.fullmatch(external_authority_digest) is None)
            or not _history_matches(
                paths,
                context,
                cycle_base,
                effective_red_ref,
                external_authority=external_authority,
            )
            or not _artifact_is_verified_final(paths.artifact_root, cycle_base)
        ):
            return None
        artifact_identity = _trusted_artifact(artifacts, run_id, cycle_base)
        if artifact_identity is None:
            return None
        artifact_id, artifact_digest = artifact_identity
        return TrustedCycle(cycle_base, run_id, artifact_id, artifact_digest)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError, subprocess.SubprocessError):
        return None


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--base-ref", required=True)
    parser.add_argument("--final-ref", required=True)
    parser.add_argument("--red-ref", help="Authenticated red source that ends the test-only amendment prefix.")
    parser.add_argument(
        "--external-authority-digest",
        help="Digest of the live-revalidated external authority receipt.",
    )
    parser.add_argument(
        "--external-authority-receipt",
        type=Path,
        help="Live-produced exact external receipt required for producer self-authorship exceptions.",
    )
    parser.add_argument("--repository", required=True)
    parser.add_argument("--change-id", required=True)
    parser.add_argument("--pull-request", type=int, required=True)
    parser.add_argument("--head-branch", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


@beartype
@ensure(lambda result: isinstance(result, int))
def main(argv: Sequence[str] | None = None) -> int:
    arguments = _build_parser().parse_args(argv)
    try:
        external_authority_receipt = (
            _read_object(arguments.external_authority_receipt)
            if arguments.external_authority_receipt is not None
            else None
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return 1
    trusted = validated_cycle_base(
        CycleBasePaths(arguments.run, arguments.artifacts, arguments.artifact_root, arguments.repo_root.resolve()),
        CycleBaseContext(
            arguments.base_ref,
            arguments.final_ref,
            arguments.repository,
            arguments.pull_request,
            arguments.head_branch,
            arguments.change_id,
        ),
        red_ref=arguments.red_ref,
        external_authority_digest=arguments.external_authority_digest,
        external_authority_receipt=external_authority_receipt,
    )
    if trusted is None:
        return 1
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(
            {
                "kind": "verified-pr-run",
                "repository": arguments.repository,
                "pull_request": arguments.pull_request,
                "head_branch": arguments.head_branch,
                "cycle_base": trusted.cycle_base,
                "prior_green_run_id": trusted.run_id,
                "prior_green_artifact_id": trusted.artifact_id,
                "prior_green_artifact_digest": trusted.artifact_digest,
                **(
                    {"external_authority_digest": arguments.external_authority_digest}
                    if arguments.external_authority_digest is not None
                    else {}
                ),
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    sys.stdout.write(f"{trusted.cycle_base}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

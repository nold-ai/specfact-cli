"""Validate one externally authorized Requirements red-proof bootstrap."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from beartype import beartype
from icontract import ensure


AUTHORITY_HEADER = "SPECFACT_REQUIREMENTS_BOOTSTRAP_AUTHORITY_V1"
GIT_OBJECT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
GOVERNED_PRODUCTION_PREFIXES = (
    ".github/",
    "ci/",
    "scripts/",
    "src/",
    "tools/",
    "resources/templates/",
    "resources/schemas/",
    "resources/mappings/",
    "resources/keys/",
    "requirements/",
    "modules/bundle-mapper/",
)
GOVERNED_PRODUCTION_FILES = {"pyproject.toml", "setup.py", "uv.lock"}


@dataclass(frozen=True)
class AuthorityPaths:
    """Local API metadata, artifact, and repository paths."""

    comment: Path
    commit: Path
    run: Path
    artifacts: Path
    artifact_root: Path
    repo_root: Path


@dataclass(frozen=True)
class AuthorityContext:
    """Immutable pull-request identity expected by the one-time authority."""

    comment_id: int
    base_ref: str
    final_ref: str
    repository: str
    change_id: str
    issue: int
    pull_request: int
    head_branch: str


def _read_object(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("bootstrap-authority-invalid")
    return cast(dict[str, object], payload)


def _object(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("bootstrap-authority-invalid")
    return cast(dict[str, object], value)


def _digest(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _git(repo_root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *arguments], cwd=repo_root, capture_output=True, check=False, text=True)


def _is_ancestor(repo_root: Path, ancestor: str, descendant: str) -> bool:
    return _git(repo_root, "merge-base", "--is-ancestor", ancestor, descendant).returncode == 0


def _has_governed_production_path(paths: Sequence[str]) -> bool:
    return any(path in GOVERNED_PRODUCTION_FILES or path.startswith(GOVERNED_PRODUCTION_PREFIXES) for path in paths)


def _authority_from_comment(comment: dict[str, object], context: AuthorityContext) -> dict[str, object]:
    user = _object(comment.get("user"))
    body = comment.get("body")
    expected_issue_url = f"https://api.github.com/repos/{context.repository}/issues/{context.issue}"
    checks = {
        "association": comment.get("author_association") in {"COLLABORATOR", "MEMBER", "OWNER"},
        "body": isinstance(body, str),
        "id": comment.get("id") == context.comment_id,
        "issue": comment.get("issue_url") == expected_issue_url,
        "login": isinstance(user.get("login"), str),
        "unedited": comment.get("created_at") == comment.get("updated_at"),
    }
    failed_checks = [name for name, valid in checks.items() if not valid]
    if failed_checks:
        raise ValueError(f"authority-comment-{','.join(failed_checks)}")
    assert isinstance(body, str)
    header, separator, encoded_authority = body.partition("\n")
    if header != AUTHORITY_HEADER or not separator:
        raise ValueError("authority-comment-header")
    decoded_authority = json.loads(encoded_authority)
    if not isinstance(decoded_authority, dict):
        raise ValueError("authority-comment-payload")
    authority = cast(dict[str, object], decoded_authority)
    if authority.get("signer_login") != user["login"]:
        raise ValueError("authority-comment-signer")
    return authority


def _valid_context(authority: dict[str, object], context: AuthorityContext) -> bool:
    expires_at = authority.get("expires_at")
    try:
        expiry = datetime.fromisoformat(cast(str, expires_at).replace("Z", "+00:00"))
    except (AttributeError, TypeError, ValueError):
        return False
    return (
        expiry > datetime.now(UTC)
        and authority.get("repository") == context.repository
        and authority.get("change_id") == context.change_id
        and authority.get("issue") == context.issue
        and authority.get("pull_request") == context.pull_request
        and authority.get("head_branch") == context.head_branch
    )


def _valid_commit(authority: dict[str, object], commit: dict[str, object]) -> bool:
    author = _object(commit.get("author"))
    verification = _object(_object(commit.get("commit")).get("verification"))
    red_commit = authority.get("red_commit")
    return (
        isinstance(red_commit, str)
        and GIT_OBJECT_PATTERN.fullmatch(red_commit) is not None
        and commit.get("sha") == red_commit
        and author.get("login") == authority.get("signer_login")
        and verification.get("verified") is True
        and verification.get("reason") == "valid"
    )


def _valid_run(authority: dict[str, object], run: dict[str, object]) -> bool:
    repository = _object(run.get("repository"))
    red_branch = authority.get("red_branch", authority.get("head_branch"))
    return (
        run.get("id") == authority.get("run_id")
        and run.get("head_sha") == authority.get("red_commit")
        and isinstance(red_branch, str)
        and bool(red_branch)
        and run.get("head_branch") == red_branch
        and run.get("event") == "pull_request"
        and run.get("status") == "completed"
        and run.get("conclusion") == "failure"
        and run.get("name") == "Requirements Evidence"
        and repository.get("full_name") == authority.get("repository")
    )


def _valid_artifact(authority: dict[str, object], artifacts: dict[str, object]) -> bool:
    entries = artifacts.get("artifacts")
    if not isinstance(entries, list):
        return False
    object_entries = [cast(dict[str, object], entry) for entry in entries if isinstance(entry, dict)]
    matching = [entry for entry in object_entries if entry.get("id") == authority.get("artifact_id")]
    if len(matching) != 1:
        return False
    artifact = cast(dict[str, object], matching[0])
    workflow_run = _object(artifact.get("workflow_run"))
    return (
        artifact.get("name") == "requirements-evidence"
        and artifact.get("expired") is False
        and artifact.get("digest") == authority.get("artifact_digest")
        and workflow_run.get("id") == authority.get("run_id")
        and workflow_run.get("head_sha") == authority.get("red_commit")
    )


def _valid_red_artifact(authority: dict[str, object], artifact_root: Path) -> bool:
    report_path = artifact_root / "requirements-evidence.json"
    junit_path = artifact_root / "requirements-proof.xml"
    plan_path = artifact_root / "requirements-evidence-plan.json"
    if (
        _digest(report_path) != authority.get("report_digest")
        or _digest(junit_path) != authority.get("junit_digest")
        or _digest(plan_path) != authority.get("plan_report_digest")
    ):
        return False
    report = _read_object(report_path)
    execution_proof = _object(report.get("execution_proof"))
    plan = _object(_read_object(plan_path).get("plan"))
    return (
        report.get("gate_decision") == "pass"
        and report.get("observed_maturity") == "red"
        and report.get("mapping_digest") == authority.get("mapping_digest")
        and report.get("plan_digest") == authority.get("plan_digest")
        and execution_proof.get("run_stage") == "red"
        and execution_proof.get("source_ref") == authority.get("red_commit")
        and execution_proof.get("junit_digest") == authority.get("junit_digest")
        and plan.get("mapping_digest") == authority.get("mapping_digest")
        and plan.get("plan_digest") == authority.get("plan_digest")
    )


def _valid_history(authority: dict[str, object], paths: AuthorityPaths, context: AuthorityContext) -> bool:
    red_commit = authority.get("red_commit")
    base_commit = authority.get("base_commit")
    if (
        not isinstance(red_commit, str)
        or GIT_OBJECT_PATTERN.fullmatch(red_commit) is None
        or not isinstance(base_commit, str)
        or GIT_OBJECT_PATTERN.fullmatch(base_commit) is None
        or GIT_OBJECT_PATTERN.fullmatch(context.final_ref) is None
    ):
        return False
    merge_base = _git(paths.repo_root, "merge-base", context.base_ref, red_commit)
    changed_paths = _git(
        paths.repo_root,
        "log",
        "--format=",
        "--name-only",
        "--no-renames",
        "--end-of-options",
        f"{base_commit}..{red_commit}",
    )
    return (
        merge_base.returncode == 0
        and merge_base.stdout.strip() == base_commit
        and _is_ancestor(paths.repo_root, context.base_ref, red_commit)
        and red_commit != context.final_ref
        and _is_ancestor(paths.repo_root, red_commit, context.final_ref)
        and changed_paths.returncode == 0
        and not _has_governed_production_path(changed_paths.stdout.splitlines())
    )


@beartype
@ensure(lambda result: isinstance(result, bool))
def validate_bootstrap_authority(paths: AuthorityPaths, context: AuthorityContext) -> bool:
    """Return whether all external authority, artifact, and Git-history bindings agree."""
    return not _authority_findings(paths, context)


def _record_check(findings: list[str], name: str, validator: Callable[[], bool]) -> None:
    try:
        if not validator():
            findings.append(name)
    except (OSError, TypeError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        findings.append(f"{name}-metadata")


def _authority_findings(paths: AuthorityPaths, context: AuthorityContext) -> list[str]:
    """Name each failed independent binding without exposing authority contents."""
    try:
        authority = _authority_from_comment(_read_object(paths.comment), context)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return ["authority-metadata"]
    except ValueError as error:
        diagnostic = str(error)
        return [diagnostic] if diagnostic.startswith("authority-comment-") else ["authority-metadata"]
    findings: list[str] = []
    checks = (
        ("artifact-files", lambda: _valid_red_artifact(authority, paths.artifact_root)),
        ("artifact-metadata", lambda: _valid_artifact(authority, _read_object(paths.artifacts))),
        ("commit-signature", lambda: _valid_commit(authority, _read_object(paths.commit))),
        ("execution-context", lambda: _valid_context(authority, context)),
        ("git-history", lambda: _valid_history(authority, paths, context)),
        ("workflow-run", lambda: _valid_run(authority, _read_object(paths.run))),
    )
    for name, validator in checks:
        _record_check(findings, name, validator)
    return findings


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comment", type=Path, required=True)
    parser.add_argument("--commit", dest="commit_path", type=Path, required=True)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--comment-id", type=int, required=True)
    parser.add_argument("--base-ref", required=True)
    parser.add_argument("--final-ref", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--change-id", required=True)
    parser.add_argument("--issue", type=int, required=True)
    parser.add_argument("--pull-request", type=int, required=True)
    parser.add_argument("--head-branch", required=True)
    return parser


@beartype
@ensure(lambda result: result in {0, 1})
def main(argv: Sequence[str] | None = None) -> int:
    """Return nonzero unless the one-time bootstrap is exactly authorized."""
    arguments = _build_parser().parse_args(argv)
    paths = AuthorityPaths(
        comment=arguments.comment,
        commit=arguments.commit_path,
        run=arguments.run,
        artifacts=arguments.artifacts,
        artifact_root=arguments.artifact_root,
        repo_root=arguments.repo_root.resolve(),
    )
    context = AuthorityContext(
        comment_id=arguments.comment_id,
        base_ref=arguments.base_ref,
        final_ref=arguments.final_ref,
        repository=arguments.repository,
        change_id=arguments.change_id,
        issue=arguments.issue,
        pull_request=arguments.pull_request,
        head_branch=arguments.head_branch,
    )
    findings = _authority_findings(paths, context)
    if findings:
        sys.stderr.write(f"bootstrap-authority-invalid:{','.join(findings)}\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

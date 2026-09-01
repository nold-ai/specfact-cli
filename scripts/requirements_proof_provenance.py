"""Validate Git-bound provenance before forwarding a red proof to reconciliation."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Protocol, TypeVar, cast
from xml.parsers import expat

from beartype import beartype
from icontract import ensure


GIT_OBJECT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
MAX_TEST_BLOB_BYTES = 10 * 1024 * 1024
MAX_JUNIT_BYTES = 10 * 1024 * 1024
TOOLCHAIN_PROPERTY_NAMES = {
    "runner": "specfact.runner",
    "python": "specfact.python",
    "pytest": "specfact.pytest",
}
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
PYTEST_CONFIGURATION_PATHS = {
    ".pytest.ini",
    ".pytest.toml",
    "pyproject.toml",
    "pytest.ini",
    "pytest.toml",
    "setup.cfg",
    "tox.ini",
}
NON_TRANSITIVE_PROOF_INPUTS = {
    "scripts/requirements_amendment_bootstrap.py",
    "scripts/requirements_bootstrap_authority.py",
    "scripts/requirements_cycle_base.py",
    "scripts/requirements_proof_provenance.py",
}
EXTERNAL_AMENDMENT_KIND = "externally-approved-amendment-bootstrap"
EXTERNAL_AMENDMENT_COMMENT_ID = 5468600336
EXTERNAL_AMENDMENT_RED_RUN_ID = 33310489582
EXTERNAL_AMENDMENT_GREEN_RUN_ID = 33303840056
EXTERNAL_AMENDMENT_REPOSITORY = "nold-ai/specfact-cli"
EXTERNAL_AMENDMENT_CHANGE_ID = "fix-release-promotion-security-gates"
EXTERNAL_AMENDMENT_PULL_REQUEST = 698
EXTERNAL_AMENDMENT_BRANCH = "codex/692-computed-owner-red-proof-v2"


@dataclass(frozen=True)
class ParsedJunit:
    """Only the bounded JUnit facts needed by retained-proof validation."""

    cases: tuple[dict[str, tuple[str, ...]], ...]
    outcomes: tuple[str, ...]
    has_failure: bool


@dataclass(frozen=True)
class TrustedCycleAuthority:
    """Authenticated amendment boundary serialized by the workflow validator."""

    cycle_base: str
    authority_digest: str
    prior_green_run_id: int
    prior_green_artifact_id: int
    prior_green_artifact_digest: str
    producer_paths: frozenset[str] = frozenset()


@dataclass(frozen=True)
class _LiveCyclePayload:
    """Authenticated GitHub run and artifact-list payloads for one cycle."""

    run: str
    artifacts: str


@dataclass(frozen=True)
class CycleAuthorityContext:
    """Repository and pull-request identity used to authenticate a cycle base."""

    repo_root: Path
    base_ref: str
    final_ref: str
    red_ref: str
    repository: str | None
    pull_request: int | None
    head_branch: str | None
    change_id: str | None


@dataclass(frozen=True)
class ProofOptions:
    """Validated keyword options shared by proof binding and verification."""

    base_ref: str
    final_ref: str | None = None
    junit_path: Path | None = None
    cycle_authority: Path | None = None
    repository: str | None = None
    pull_request: int | None = None
    head_branch: str | None = None
    change_id: str | None = None


@dataclass(frozen=True)
class BindingContext:
    """Source and selector inputs used to add immutable proof bindings."""

    repo_root: Path
    source_ref: str
    selector_paths: Sequence[str]
    provenance_base: str
    change_id: str | None


@dataclass(frozen=True)
class _MutablePathPolicy:
    """Inputs shared while validating exact mutable SUT touchpoints."""

    repo_root: Path
    source_ref: str
    frozen: set[str]
    support_roots: set[str]
    accepted: set[str]
    producer_paths: frozenset[str]


@dataclass(frozen=True)
class _RedHistoryBoundary:
    """Authenticated Git range and approved producer paths for one red proof."""

    base_ref: str
    source_ref: str
    final_ref: str
    change_id: str | None
    producer_paths: frozenset[str] = frozenset()


@dataclass(frozen=True)
class ExternalAmendmentPaths:
    """Live GitHub inputs and validator outputs for the approved exception."""

    comment: Path
    producer_comments: Path
    red_run: Path
    red_artifacts: Path
    red_root: Path
    green_run: Path
    green_artifacts: Path
    green_root: Path
    proof: Path
    receipt: Path


class _TrustedCycle(Protocol):
    cycle_base: str
    run_id: int
    artifact_id: int
    artifact_digest: str


class _CycleModule(Protocol):
    CycleBasePaths: Callable[..., object]
    CycleBaseContext: Callable[..., object]

    validated_cycle_base: Callable[..., _TrustedCycle | None]
    _external_receipt_history_matches: Callable[[object, object, str, Mapping[str, object]], bool]


T = TypeVar("T")


class _JunitCollector:
    """Reject declarations and collect testcase properties without building a tree."""

    def __init__(self) -> None:
        self.cases: list[dict[str, list[str]]] = []
        self.outcomes: list[str] = []
        self.current_case: dict[str, list[str]] | None = None
        self.current_outcome: str | None = None
        self.has_failure = False

    def _start(self, name: str, attributes: dict[str, str]) -> None:
        if name == "testcase":
            if self.current_case is not None:
                raise ValueError("prior-red-proof-invalid")
            self.current_case = {}
            self.current_outcome = "passed"
            return
        if self.current_case is None:
            return
        if name in {"failure", "error"}:
            if self.current_outcome != "passed":
                raise ValueError("prior-red-proof-invalid")
            self.current_outcome = "failed"
            self.has_failure = True
        elif name == "skipped":
            if self.current_outcome != "passed":
                raise ValueError("prior-red-proof-invalid")
            self.current_outcome = "skipped"
        elif name == "property":
            self._record_property(attributes)

    def _record_property(self, attributes: dict[str, str]) -> None:
        property_name = attributes.get("name")
        value = attributes.get("value")
        if property_name is not None and value is not None and self.current_case is not None:
            self.current_case.setdefault(property_name, []).append(value)

    def _end(self, name: str) -> None:
        if name == "testcase" and self.current_case is not None:
            if self.current_outcome is None:
                raise ValueError("prior-red-proof-invalid")
            self.cases.append(self.current_case)
            self.outcomes.append(self.current_outcome)
            self.current_case = None
            self.current_outcome = None

    def _reject_declaration(self, *_arguments: object) -> int:
        raise ValueError("prior-red-proof-invalid")

    def _result(self) -> ParsedJunit:
        if self.current_case is not None or self.current_outcome is not None:
            raise ValueError("prior-red-proof-invalid")
        cases = tuple({name: tuple(values) for name, values in case.items()} for case in self.cases)
        return ParsedJunit(cases=cases, outcomes=tuple(self.outcomes), has_failure=self.has_failure)


def _parse_junit(payload: bytes) -> ParsedJunit:
    """Parse bounded XML while rejecting DTD, entity, and external references."""
    if len(payload) > MAX_JUNIT_BYTES:
        raise ValueError("prior-red-proof-invalid")
    collector = _JunitCollector()
    parser = expat.ParserCreate()
    parser.StartElementHandler = collector._start
    parser.EndElementHandler = collector._end
    parser.StartDoctypeDeclHandler = collector._reject_declaration
    parser.EntityDeclHandler = collector._reject_declaration
    parser.ExternalEntityRefHandler = collector._reject_declaration
    parser.SetParamEntityParsing(expat.XML_PARAM_ENTITY_PARSING_NEVER)
    try:
        parser.Parse(payload, True)
    except (expat.ExpatError, ValueError) as error:
        raise ValueError("prior-red-proof-invalid") from error
    return collector._result()


def _git(repo_root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments],
        cwd=repo_root,
        capture_output=True,
        check=False,
        text=True,
    )


def _read_red_proof(red_proof_path: Path) -> dict[str, object]:
    try:
        report = json.loads(red_proof_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("prior-red-proof-invalid") from error
    if not isinstance(report, dict):
        raise ValueError("prior-red-proof-invalid")
    return cast(dict[str, object], report)


def _authority_hint(authority_path: Path, context: CycleAuthorityContext) -> dict[str, object]:
    """Read one untrusted authority hint after requiring live PR context."""
    try:
        hint = json.loads(authority_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("prior-red-proof-invalid") from error
    if (
        not isinstance(hint, dict)
        or context.repository is None
        or context.pull_request is None
        or context.head_branch is None
    ):
        raise ValueError("prior-red-proof-invalid")
    return cast(dict[str, object], hint)


def _verified_cycle_run_id(hint: dict[str, object]) -> int:
    """Return the ordinary same-PR green run identifier."""
    run_id = hint.get("prior_green_run_id")
    if hint.get("kind") != "verified-pr-run" or not isinstance(run_id, int) or run_id <= 0:
        raise ValueError("prior-red-proof-invalid")
    return run_id


def _external_locator_matches(hint: dict[str, object], context: CycleAuthorityContext) -> bool:
    """Return whether an external receipt uses the approved immutable locator."""
    return all(
        (
            hint.get("kind") == EXTERNAL_AMENDMENT_KIND,
            hint.get("comment_id") == EXTERNAL_AMENDMENT_COMMENT_ID,
            hint.get("authority_version") == 3,
            hint.get("producer_bypass") == "stale-red-proof-only",
            context.repository == EXTERNAL_AMENDMENT_REPOSITORY,
            context.pull_request == EXTERNAL_AMENDMENT_PULL_REQUEST,
            context.head_branch == EXTERNAL_AMENDMENT_BRANCH,
            context.change_id == EXTERNAL_AMENDMENT_CHANGE_ID,
            hint.get("repository") == context.repository,
            hint.get("change_id") == context.change_id,
            hint.get("pull_request") == context.pull_request,
            hint.get("head_branch") == context.head_branch,
        )
    )


def _external_hint_matches(hint: dict[str, object], context: CycleAuthorityContext) -> bool:
    """Allow only a test/spec-only red extension beyond the approved red source."""
    approved_red = hint.get("red_ref")
    if not _external_locator_matches(hint, context) or not isinstance(approved_red, str):
        return False
    changed_paths = _changed_paths_in_history(context.repo_root, approved_red, context.red_ref)
    return (
        changed_paths is not None
        and _is_ancestor(context.repo_root, approved_red, context.red_ref)
        and not _has_governed_production_path(changed_paths, context.change_id)
    )


def _cycle_module() -> _CycleModule:
    """Load the sibling validator used for live cycle authentication."""
    cycle_script = Path(__file__).with_name("requirements_cycle_base.py")
    spec = importlib.util.spec_from_file_location("requirements_cycle_base_live", cycle_script)
    if spec is None or spec.loader is None:
        raise ValueError("prior-red-proof-invalid")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return cast(_CycleModule, module)


def _fetch_cycle_evidence(context: CycleAuthorityContext, run_id: int, root: Path) -> tuple[str, str, Path]:
    """Fetch the live run metadata and named artifact into a temporary directory."""
    assert context.repository is not None
    run_result = subprocess.run(
        ["gh", "api", f"repos/{context.repository}/actions/runs/{run_id}"],
        cwd=context.repo_root,
        capture_output=True,
        check=True,
        text=True,
    )
    artifacts_result = subprocess.run(
        ["gh", "api", f"repos/{context.repository}/actions/runs/{run_id}/artifacts"],
        cwd=context.repo_root,
        capture_output=True,
        check=True,
        text=True,
    )
    artifact_root = root / "artifact"
    subprocess.run(
        [
            "gh",
            "run",
            "download",
            str(run_id),
            "--repo",
            context.repository,
            "--name",
            "requirements-evidence",
            "--dir",
            str(artifact_root),
        ],
        cwd=context.repo_root,
        capture_output=True,
        check=True,
        text=True,
    )
    return run_result.stdout, artifacts_result.stdout, artifact_root


def _fetch_github_json(context: CycleAuthorityContext, endpoint: str, output: Path) -> None:
    """Fetch one live GitHub object without trusting workflow-created JSON."""
    assert context.repository is not None
    result = subprocess.run(
        ["gh", "api", f"repos/{context.repository}/{endpoint}"],
        cwd=context.repo_root,
        capture_output=True,
        check=True,
        text=True,
    )
    output.write_text(result.stdout, encoding="utf-8")


def _fetch_issue_comments(context: CycleAuthorityContext, issue: int, output: Path) -> None:
    """Fetch every live issue-comment page for dynamic final-byte authority."""
    assert context.repository is not None
    result = subprocess.run(
        [
            "gh",
            "api",
            "--paginate",
            "--slurp",
            f"repos/{context.repository}/issues/{issue}/comments?per_page=100",
        ],
        cwd=context.repo_root,
        capture_output=True,
        check=True,
        text=True,
    )
    output.write_text(result.stdout, encoding="utf-8")


def _download_requirements_artifact(context: CycleAuthorityContext, run_id: int, output: Path) -> None:
    """Download one exact named Requirements artifact from the approved repository."""
    assert context.repository is not None
    subprocess.run(
        [
            "gh",
            "run",
            "download",
            str(run_id),
            "--repo",
            context.repository,
            "--name",
            "requirements-evidence",
            "--dir",
            str(output),
        ],
        cwd=context.repo_root,
        capture_output=True,
        check=True,
        text=True,
    )


def _external_amendment_paths(root: Path) -> ExternalAmendmentPaths:
    """Create fixed paths for one live external-authority revalidation."""
    red_root = root / "red"
    green_root = root / "green"
    red_root.mkdir()
    green_root.mkdir()
    return ExternalAmendmentPaths(
        root / "comment.json",
        root / "producer-comments.json",
        root / "red-run.json",
        root / "red-artifacts.json",
        red_root,
        root / "green-run.json",
        root / "green-artifacts.json",
        green_root,
        root / "red.json",
        root / "authority.json",
    )


def _fetch_external_amendment(context: CycleAuthorityContext, root: Path) -> ExternalAmendmentPaths:
    """Fetch both exact runs, artifacts, and the unedited approval comment live."""
    paths = _external_amendment_paths(root)
    _fetch_github_json(context, f"issues/comments/{EXTERNAL_AMENDMENT_COMMENT_ID}", paths.comment)
    _fetch_issue_comments(context, 692, paths.producer_comments)
    for run_id, run_path, artifacts_path, artifact_root in (
        (EXTERNAL_AMENDMENT_RED_RUN_ID, paths.red_run, paths.red_artifacts, paths.red_root),
        (EXTERNAL_AMENDMENT_GREEN_RUN_ID, paths.green_run, paths.green_artifacts, paths.green_root),
    ):
        _fetch_github_json(context, f"actions/runs/{run_id}", run_path)
        _fetch_github_json(context, f"actions/runs/{run_id}/artifacts", artifacts_path)
        _download_requirements_artifact(context, run_id, artifact_root)
    return paths


def _external_validator_command(context: CycleAuthorityContext, paths: ExternalAmendmentPaths) -> list[str]:
    """Build the exact validator invocation for the approved capability."""
    assert context.repository is not None and context.pull_request is not None and context.head_branch is not None
    return [
        sys.executable,
        str(Path(__file__).with_name("requirements_amendment_bootstrap.py")),
        "--comment",
        str(paths.comment),
        "--comment-id",
        str(EXTERNAL_AMENDMENT_COMMENT_ID),
        "--producer-comments",
        str(paths.producer_comments),
        "--red-run",
        str(paths.red_run),
        "--red-artifacts",
        str(paths.red_artifacts),
        "--red-artifact-root",
        str(paths.red_root),
        "--green-run",
        str(paths.green_run),
        "--green-artifacts",
        str(paths.green_artifacts),
        "--green-artifact-root",
        str(paths.green_root),
        "--repo-root",
        str(context.repo_root),
        "--repository",
        context.repository,
        "--change-id",
        EXTERNAL_AMENDMENT_CHANGE_ID,
        "--issue",
        "692",
        "--pull-request",
        str(context.pull_request),
        "--head-branch",
        context.head_branch,
        "--base-ref",
        context.base_ref,
        "--final-ref",
        context.final_ref,
        "--output",
        str(paths.proof),
        "--authority-output",
        str(paths.receipt),
    ]


def _trusted_external_amendment(
    context: CycleAuthorityContext, hint: dict[str, object], root: Path
) -> TrustedCycleAuthority:
    """Revalidate the exact capability live and compare its complete receipt."""
    if not _external_hint_matches(hint, context):
        raise ValueError("prior-red-proof-invalid")
    paths = _fetch_external_amendment(context, root)
    subprocess.run(
        _external_validator_command(context, paths),
        cwd=context.repo_root,
        capture_output=True,
        check=True,
        text=True,
    )
    receipt = _read_red_proof(paths.receipt)
    if receipt != hint:
        raise ValueError("prior-red-proof-invalid")
    cycle = _cycle_module()
    history_paths = cycle.CycleBasePaths(
        run=paths.green_run,
        artifacts=paths.green_artifacts,
        artifact_root=paths.green_root,
        repo_root=context.repo_root,
    )
    history_context = cycle.CycleBaseContext(
        base_ref=context.base_ref,
        final_ref=context.final_ref,
        repository=context.repository,
        pull_request=context.pull_request,
        head_branch=context.head_branch,
        change_id=context.change_id,
    )
    if not cycle._external_receipt_history_matches(history_paths, history_context, context.final_ref, receipt):
        raise ValueError("prior-red-proof-invalid")
    values = (
        receipt.get("cycle_base"),
        receipt.get("authority_digest"),
        receipt.get("prior_green_run_id"),
        receipt.get("prior_green_artifact_id"),
        receipt.get("prior_green_artifact_digest"),
    )
    if not (
        isinstance(values[0], str)
        and isinstance(values[1], str)
        and isinstance(values[2], int)
        and isinstance(values[3], int)
        and isinstance(values[4], str)
    ):
        raise ValueError("prior-red-proof-invalid")
    return TrustedCycleAuthority(
        cast(str, values[0]),
        cast(str, values[1]),
        values[2],
        values[3],
        cast(str, values[4]),
        _producer_paths_from_external_receipt(receipt),
    )


def _producer_paths_from_external_receipt(receipt: Mapping[str, object]) -> frozenset[str]:
    """Return exact producer paths from an already validated external receipt."""
    final_authority = receipt.get("final_producer_authority")
    if not isinstance(final_authority, Mapping):
        return frozenset()
    typed_authority = cast(Mapping[str, object], final_authority)
    producer_blobs = typed_authority.get("producer_blobs")
    return frozenset(cast(Mapping[str, object], producer_blobs)) if isinstance(producer_blobs, Mapping) else frozenset()


def _revalidated_external_authority(
    context: CycleAuthorityContext, root: Path, expected_digest: str
) -> tuple[str, dict[str, object]]:
    """Re-fetch the expiring external capability before ordinary receipt reuse."""
    if DIGEST_PATTERN.fullmatch(expected_digest) is None:
        raise ValueError("prior-red-proof-invalid")
    root.mkdir()
    paths = _fetch_external_amendment(context, root)
    subprocess.run(
        _external_validator_command(context, paths),
        cwd=context.repo_root,
        capture_output=True,
        check=True,
        text=True,
    )
    receipt = _read_red_proof(paths.receipt)
    if not _external_locator_matches(receipt, context) or receipt.get("authority_digest") != expected_digest:
        raise ValueError("prior-red-proof-invalid")
    return expected_digest, receipt


def _validated_live_cycle(
    context: CycleAuthorityContext,
    root: Path,
    payload: _LiveCyclePayload,
    *,
    external_authority_digest: str | None = None,
    external_authority_receipt: dict[str, object] | None = None,
) -> _TrustedCycle:
    """Authenticate live evidence against Git history and pull-request identity."""
    assert context.repository is not None and context.pull_request is not None and context.head_branch is not None
    run_path = root / "run.json"
    artifacts_path = root / "artifacts.json"
    artifact_root = root / "artifact"
    run_path.write_text(payload.run, encoding="utf-8")
    artifacts_path.write_text(payload.artifacts, encoding="utf-8")
    module = _cycle_module()
    trusted = module.validated_cycle_base(
        module.CycleBasePaths(
            run=run_path,
            artifacts=artifacts_path,
            artifact_root=artifact_root,
            repo_root=context.repo_root,
        ),
        module.CycleBaseContext(
            base_ref=context.base_ref,
            final_ref=context.final_ref,
            repository=context.repository,
            pull_request=context.pull_request,
            head_branch=context.head_branch,
            change_id=context.change_id,
        ),
        red_ref=context.red_ref,
        external_authority_digest=external_authority_digest,
        external_authority_receipt=external_authority_receipt,
    )
    if trusted is None:
        raise ValueError("prior-red-proof-invalid")
    return trusted


def _cycle_payload_digest(run_payload: str, artifacts_payload: str, artifact_root: Path) -> str:
    """Digest the authenticated GitHub metadata and verification reports."""
    authenticated_payload = b"\0".join(
        (
            json.dumps(json.loads(run_payload), sort_keys=True, separators=(",", ":")).encode(),
            json.dumps(json.loads(artifacts_payload), sort_keys=True, separators=(",", ":")).encode(),
            (artifact_root / "requirements-evidence.json").read_bytes(),
            (artifact_root / "requirements-evidence-plan.json").read_bytes(),
        )
    )
    return f"sha256:{hashlib.sha256(authenticated_payload).hexdigest()}"


def _read_cycle_authority(authority_path: Path | None, context: CycleAuthorityContext) -> TrustedCycleAuthority | None:
    """Re-fetch and authenticate one same-PR green run before trusting its boundary."""
    if authority_path is None:
        return None
    hint = _authority_hint(authority_path, context)
    try:
        with tempfile.TemporaryDirectory(prefix="specfact-cycle-authority-") as temporary:
            root = Path(temporary)
            if hint.get("kind") == EXTERNAL_AMENDMENT_KIND:
                return _trusted_external_amendment(context, hint, root)
            run_id = _verified_cycle_run_id(hint)
            external_authority_digest = hint.get("external_authority_digest")
            external_authority_receipt: dict[str, object] | None = None
            if external_authority_digest is not None and not isinstance(external_authority_digest, str):
                raise ValueError("prior-red-proof-invalid")
            if external_authority_digest is not None:
                external_authority_digest, external_authority_receipt = _revalidated_external_authority(
                    context,
                    root / "external",
                    external_authority_digest,
                )
            run_payload, artifacts_payload, artifact_root = _fetch_cycle_evidence(context, run_id, root)
            trusted = _validated_live_cycle(
                context,
                root,
                _LiveCyclePayload(run_payload, artifacts_payload),
                external_authority_digest=external_authority_digest,
                external_authority_receipt=external_authority_receipt,
            )
            if trusted is None or any(
                hint.get(field) != value
                for field, value in {
                    "cycle_base": trusted.cycle_base,
                    "prior_green_artifact_id": trusted.artifact_id,
                    "prior_green_artifact_digest": trusted.artifact_digest,
                }.items()
            ):
                raise ValueError("prior-red-proof-invalid")
            return TrustedCycleAuthority(
                cycle_base=trusted.cycle_base,
                authority_digest=_cycle_payload_digest(run_payload, artifacts_payload, artifact_root),
                prior_green_run_id=trusted.run_id,
                prior_green_artifact_id=trusted.artifact_id,
                prior_green_artifact_digest=trusted.artifact_digest,
                producer_paths=(
                    _producer_paths_from_external_receipt(external_authority_receipt)
                    if external_authority_receipt is not None
                    else frozenset()
                ),
            )
    except (OSError, subprocess.SubprocessError, ValueError) as error:
        raise ValueError("prior-red-proof-invalid") from error


def _provenance_base_ref(base_ref: str, authority: TrustedCycleAuthority | None) -> str:
    """Use the pull-request base for cycle one and only validated authority thereafter."""
    return authority.cycle_base if authority is not None else base_ref


def _validated_execution_proof(report: dict[str, object]) -> dict[str, object]:
    """Return the red-stage execution record only when its required fields are valid."""
    execution_proof = report.get("execution_proof")
    if not isinstance(execution_proof, dict):
        raise ValueError("prior-red-proof-invalid")
    return cast(dict[str, object], execution_proof)


def _validated_selectors(execution_proof: dict[str, object]) -> list[object]:
    source_ref = execution_proof.get("source_ref")
    selectors = execution_proof.get("selectors")
    if (
        not isinstance(source_ref, str)
        or GIT_OBJECT_PATTERN.fullmatch(source_ref) is None
        or not isinstance(selectors, list)
        or not selectors
    ):
        raise ValueError("prior-red-proof-invalid")
    return selectors


def _selector_paths(report: dict[str, object]) -> tuple[str, list[str]]:
    """Validate the released red-report shape and extract unique selector file paths."""
    execution_proof = _validated_execution_proof(report)
    if report.get("gate_decision") != "pass" or report.get("observed_maturity") != "red":
        raise ValueError("prior-red-proof-invalid")
    if execution_proof.get("run_stage") != "red":
        raise ValueError("prior-red-proof-invalid")
    selectors = _validated_selectors(execution_proof)
    source_ref = execution_proof["source_ref"]
    assert isinstance(source_ref, str)
    paths: set[str] = set()
    for selector in selectors:
        if not isinstance(selector, str):
            raise ValueError("prior-red-proof-invalid")
        test_path, separator, _ = selector.partition("::")
        path = PurePosixPath(test_path)
        if not separator or path.is_absolute() or ".." in path.parts or not test_path.endswith(".py"):
            raise ValueError("prior-red-proof-invalid")
        paths.add(test_path)
    return source_ref, sorted(paths)


def _applicable_conftest_paths(test_path: str) -> set[str]:
    """Return root and ancestor pytest support files that can affect a selected test."""
    parent = PurePosixPath(test_path).parent
    paths = {"conftest.py"}
    while parent != PurePosixPath("."):
        paths.add((parent / "conftest.py").as_posix())
        parent = parent.parent
    return paths


def _applicable_pytest_configuration_paths(test_path: str) -> set[str]:
    """Return every config location pytest searches from a selected test to root."""
    parent = PurePosixPath(test_path).parent
    paths = set(PYTEST_CONFIGURATION_PATHS)
    while parent != PurePosixPath("."):
        paths.update((parent / name).as_posix() for name in PYTEST_CONFIGURATION_PATHS)
        parent = parent.parent
    return paths


def _python_module_paths(module_parts: Sequence[str]) -> set[str]:
    """Return possible paths for a repository-local module, including an absent target."""
    if not module_parts:
        return set()
    module_path = PurePosixPath(*module_parts)
    paths = {module_path.with_suffix(".py").as_posix(), (module_path / "__init__.py").as_posix()}
    for parent_depth in range(1, len(module_parts)):
        parent_path = PurePosixPath(*module_parts[:parent_depth])
        paths.add((parent_path / "__init__.py").as_posix())
    return paths


def _validate_retained_red_junit(
    red_proof_path: Path, report: dict[str, object], *, junit_path: Path | None = None
) -> ParsedJunit:
    """Bind the released report to a retained failing JUnit artifact."""
    execution_proof = _validated_execution_proof(report)
    expected_digest = execution_proof.get("junit_digest")
    retained_junit_path = junit_path or red_proof_path.with_suffix(".xml")
    try:
        if retained_junit_path.stat().st_size > MAX_JUNIT_BYTES:
            raise ValueError("prior-red-proof-invalid")
        payload = retained_junit_path.read_bytes()
        parsed_junit = _parse_junit(payload)
    except (OSError, ValueError) as error:
        raise ValueError("prior-red-proof-invalid") from error
    actual_digest = f"sha256:{hashlib.sha256(payload).hexdigest()}"
    if expected_digest != actual_digest or not parsed_junit.has_failure:
        raise ValueError("prior-red-proof-invalid")
    junit_selectors = {selector for case in parsed_junit.cases for selector in case.get("specfact.selector", ())}
    if junit_selectors != set(_validated_selectors(execution_proof)):
        raise ValueError("prior-red-proof-invalid")
    return parsed_junit


def _case_property(properties: dict[str, tuple[str, ...]], name: str) -> str:
    """Return one non-empty JUnit case property or reject ambiguous producer evidence."""
    values = properties.get(name, ())
    if len(values) != 1 or not values[0]:
        raise ValueError("prior-red-proof-invalid")
    return values[0]


def _toolchain_identity_from_junit(junit: ParsedJunit, selectors: Sequence[object]) -> dict[str, str]:
    """Return one consistent toolchain identity emitted by every selected pytest case."""
    expected_selectors = {selector for selector in selectors if isinstance(selector, str)}
    identities: dict[str, tuple[str, str, str]] = {}
    for properties in junit.cases:
        selector = _case_property(properties, "specfact.selector")
        if selector not in expected_selectors or selector in identities:
            raise ValueError("prior-red-proof-invalid")
        identities[selector] = (
            _case_property(properties, TOOLCHAIN_PROPERTY_NAMES["runner"]),
            _case_property(properties, TOOLCHAIN_PROPERTY_NAMES["python"]),
            _case_property(properties, TOOLCHAIN_PROPERTY_NAMES["pytest"]),
        )
    if set(identities) != expected_selectors or len(set(identities.values())) != 1:
        raise ValueError("prior-red-proof-invalid")
    identity = next(iter(identities.values()))
    return dict(zip(TOOLCHAIN_PROPERTY_NAMES, identity, strict=True))


def _artifact_is_tracked(repo_root: Path, artifact_path: Path) -> bool:
    """Return whether an artifact is controlled by the pull-request Git tree."""
    try:
        relative_path = artifact_path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return False
    return _git(repo_root, "ls-files", "--error-unmatch", "--", relative_path.as_posix()).returncode == 0


def _is_ancestor(repo_root: Path, ancestor: str, descendant: str) -> bool:
    return _git(repo_root, "merge-base", "--is-ancestor", ancestor, descendant).returncode == 0


def _parse_name_status_records(payload: bytes) -> list[str] | None:
    """Return every path from a NUL-delimited Git name-status stream."""
    records = payload.split(b"\0")
    if records.pop() != b"":
        return None
    paths: list[str] = []
    record_index = 0
    while record_index < len(records):
        status = records[record_index]
        record_index += 1
        if record_index >= len(records):
            return None
        paths.append(records[record_index].decode("utf-8", errors="surrogateescape"))
        record_index += 1
        if status.startswith((b"R", b"C")):
            if record_index >= len(records):
                return None
            paths.append(records[record_index].decode("utf-8", errors="surrogateescape"))
            record_index += 1
    return paths


def _changed_paths_in_history(
    repo_root: Path, start_ref: str, end_ref: str, *, merge_parent: int = 2
) -> list[str] | None:
    """Return paths touched by every commit, including changes later restored."""
    revisions = _git(repo_root, "rev-list", "--reverse", f"{start_ref}..{end_ref}")
    if revisions.returncode:
        return None
    paths: list[str] = []
    for revision in revisions.stdout.splitlines():
        parents = _git(repo_root, "rev-list", "--parents", "-n", "1", revision).stdout.split()
        comparison_ref = f"{revision}^{merge_parent}" if len(parents) > 2 else f"{revision}^"
        result = subprocess.run(
            [
                "git",
                "diff",
                "--name-status",
                "-z",
                "--find-renames",
                "--find-copies-harder",
                comparison_ref,
                revision,
            ],
            cwd=repo_root,
            capture_output=True,
            check=False,
        )
        commit_paths = _parse_name_status_records(result.stdout) if result.returncode == 0 else None
        if commit_paths is None:
            return None
        paths.extend(commit_paths)
    return paths


def _red_source_precedes_final(repo_root: Path, base_ref: str, source_ref: str, final_ref: str) -> bool:
    """Require the current base, red source, and final source to form one strict chain."""
    resolved_base = _git(repo_root, "rev-parse", base_ref)
    return (
        GIT_OBJECT_PATTERN.fullmatch(final_ref) is not None
        and resolved_base.returncode == 0
        and source_ref != resolved_base.stdout.strip()
        and source_ref != final_ref
        and _is_ancestor(repo_root, base_ref, source_ref)
        and _is_ancestor(repo_root, source_ref, final_ref)
    )


def _has_governed_production_path(paths: Sequence[str], change_id: str | None) -> bool:
    """Return whether red history contains anything outside its positive allowlist."""
    return any(not _red_history_path_is_allowed(path, change_id) for path in paths)


def _red_history_path_is_allowed(path: str, change_id: str | None) -> bool:
    """Allow test roots and declarative artifacts for the linked OpenSpec change."""
    if path.startswith(ALLOWED_RED_HISTORY_PREFIXES):
        return True
    if change_id is None or CHANGE_ID_PATTERN.fullmatch(change_id) is None:
        return False
    change_prefix = f"openspec/changes/{change_id}/"
    if not path.startswith(change_prefix):
        return False
    relative = path.removeprefix(change_prefix)
    return relative in ALLOWED_RED_OPEN_SPEC_FILES or (
        relative.startswith("specs/") and PurePosixPath(relative).name == "spec.md"
    )


def _test_path_is_regular_at_ref(repo_root: Path, source_ref: str, test_path: str) -> bool:
    """Reject symlink selectors because pytest follows bytes not bound by their Git blob."""
    result = _git(repo_root, "ls-tree", source_ref, "--", test_path)
    return result.returncode == 0 and result.stdout.startswith(("100644 blob ", "100755 blob "))


def _blob_digest_at_ref(repo_root: Path, source_ref: str, test_path: str) -> str | None:
    """Return the digest of committed test bytes without consulting the worktree."""
    size_result = _git(repo_root, "cat-file", "-s", f"{source_ref}:{test_path}")
    try:
        blob_size = int(size_result.stdout.strip())
    except ValueError:
        return None
    if size_result.returncode != 0 or blob_size > MAX_TEST_BLOB_BYTES:
        return None
    result = subprocess.run(
        ["git", "show", f"{source_ref}:{test_path}"],
        cwd=repo_root,
        capture_output=True,
        check=False,
        timeout=30,
    )
    return f"sha256:{hashlib.sha256(result.stdout).hexdigest()}" if result.returncode == 0 else None


def _valid_report_digests(report: dict[str, object]) -> bool:
    """Return whether the report binds both governed input digests."""
    return all(
        isinstance(report.get(field), str) and DIGEST_PATTERN.fullmatch(cast(str, report[field])) is not None
        for field in ("mapping_digest", "plan_digest")
    )


def _validated_toolchain_identity(value: object) -> None:
    """Reject an incomplete toolchain identity."""
    if not isinstance(value, dict):
        raise ValueError("prior-red-proof-invalid")
    identity = cast(dict[str, object], value)
    if set(identity) != {"runner", "python", "pytest"} or not all(
        isinstance(item, str) and item for item in identity.values()
    ):
        raise ValueError("prior-red-proof-invalid")


def _write_report_atomically(red_proof_path: Path, report: dict[str, object]) -> None:
    """Replace the report only after every producer binding has validated."""
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=red_proof_path.parent, prefix=f".{red_proof_path.name}.", delete=False
        ) as handle:
            temporary_path = Path(handle.name)
            json.dump(report, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temporary_path, red_proof_path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _validate_binding_artifact_paths(red_proof_path: Path, junit_path: Path, repo_root: Path) -> None:
    """Reject mutable source-controlled or link-indirected producer artifacts."""
    paths = (red_proof_path, junit_path)
    if any(path.is_symlink() or _artifact_is_tracked(repo_root, path) for path in paths):
        raise ValueError("prior-red-proof-invalid")


def _red_source_identities(repo_root: Path, base_ref: str, source_ref: str, change_id: str | None) -> tuple[str, str]:
    """Return a committed source tree and merge base for one test-only red source."""
    if not _is_ancestor(repo_root, base_ref, source_ref):
        raise ValueError("prior-red-proof-invalid")
    changed_paths = _changed_paths_in_history(repo_root, base_ref, source_ref)
    if changed_paths is None or _has_governed_production_path(changed_paths, change_id):
        raise ValueError("prior-red-proof-invalid")
    source_tree_result = _git(repo_root, "rev-parse", f"{source_ref}^{{tree}}")
    merge_base_result = _git(repo_root, "merge-base", base_ref, source_ref)
    identities = (source_tree_result.stdout.strip(), merge_base_result.stdout.strip())
    if (
        source_tree_result.returncode
        or merge_base_result.returncode
        or any(GIT_OBJECT_PATTERN.fullmatch(identity) is None for identity in identities)
    ):
        raise ValueError("prior-red-proof-invalid")
    return identities


def _selected_test_digests(repo_root: Path, source_ref: str, selector_paths: Sequence[str]) -> dict[str, str]:
    """Bind every selected regular test to its immutable source-commit blob."""
    digests: dict[str, str] = {}
    for test_path in selector_paths:
        digest = _blob_digest_at_ref(repo_root, source_ref, test_path)
        if digest is None or not _test_path_is_regular_at_ref(repo_root, source_ref, test_path):
            raise ValueError("prior-red-proof-invalid")
        digests[test_path] = digest
    return digests


def _merge_execution_bindings(execution_proof: dict[str, object], bindings: dict[str, object]) -> None:
    """Add absent bindings while rejecting any producer-supplied contradiction."""
    conflicts = {
        field for field, value in bindings.items() if field in execution_proof and execution_proof[field] != value
    }
    if conflicts:
        raise ValueError("prior-red-proof-invalid")
    execution_proof.update(bindings)


def _required_string(options: dict[str, object], name: str) -> str:
    """Return one required non-empty string option."""
    value = options.get(name)
    if not isinstance(value, str) or not value:
        raise TypeError(f"{name} must be a non-empty string")
    return value


def _optional_value(options: dict[str, object], name: str, expected_type: type[T]) -> T | None:  # noqa: UP047
    """Return one optional value of the required runtime type."""
    value = options.get(name)
    if value is not None and not isinstance(value, expected_type):
        raise TypeError(f"{name} has an invalid type")
    return cast(T | None, value)


def _proof_options(options: dict[str, object], *, require_final: bool) -> ProofOptions:
    """Validate the stable keyword API without inflating public parameter counts."""
    allowed = {
        "base_ref",
        "final_ref",
        "junit_path",
        "cycle_authority",
        "repository",
        "pull_request",
        "head_branch",
        "change_id",
    }
    if set(options) - allowed:
        raise TypeError("unsupported proof option")
    final_ref = _optional_value(options, "final_ref", str)
    if require_final and final_ref is None:
        raise TypeError("final_ref must be a non-empty string")
    return ProofOptions(
        base_ref=_required_string(options, "base_ref"),
        final_ref=final_ref,
        junit_path=_optional_value(options, "junit_path", Path),
        cycle_authority=_optional_value(options, "cycle_authority", Path),
        repository=_optional_value(options, "repository", str),
        pull_request=_optional_value(options, "pull_request", int),
        head_branch=_optional_value(options, "head_branch", str),
        change_id=_optional_value(options, "change_id", str),
    )


def _binding_values(
    context: BindingContext,
    root: ParsedJunit,
    execution_proof: dict[str, object],
    authority: TrustedCycleAuthority | None,
) -> dict[str, object]:
    """Build immutable source, toolchain, and optional cycle bindings."""
    source_tree, merge_base = _red_source_identities(
        context.repo_root,
        context.provenance_base,
        context.source_ref,
        context.change_id,
    )
    bindings: dict[str, object] = {
        "source_tree": source_tree,
        "merge_base": merge_base,
        "test_file_digests": _selected_test_digests(context.repo_root, context.source_ref, context.selector_paths),
        "toolchain_identity": _toolchain_identity_from_junit(root, _validated_selectors(execution_proof)),
    }
    if authority is not None:
        bindings.update(
            cycle_base=authority.cycle_base,
            cycle_authority_digest=authority.authority_digest,
            prior_green_run_id=authority.prior_green_run_id,
            prior_green_artifact_id=authority.prior_green_artifact_id,
            prior_green_artifact_digest=authority.prior_green_artifact_digest,
        )
    return bindings


@beartype
@ensure(lambda result: result is None)
def bind_red_proof(
    red_proof_path: Path,
    repo_root: Path,
    **options: object,
) -> None:
    """Add immutable core-owned provenance to one freshly reconciled red report."""
    settings = _proof_options(options, require_final=False)
    retained_junit_path = settings.junit_path or red_proof_path.with_suffix(".xml")
    _validate_binding_artifact_paths(red_proof_path, retained_junit_path, repo_root)
    report = _read_red_proof(red_proof_path)
    root = _validate_retained_red_junit(red_proof_path, report, junit_path=retained_junit_path)
    source_ref, selector_paths = _selector_paths(report)
    if not _valid_report_digests(report):
        raise ValueError("prior-red-proof-invalid")
    authority = _read_cycle_authority(
        settings.cycle_authority,
        CycleAuthorityContext(
            repo_root,
            settings.base_ref,
            settings.final_ref or source_ref,
            source_ref,
            settings.repository,
            settings.pull_request,
            settings.head_branch,
            settings.change_id,
        ),
    )
    provenance_base = _provenance_base_ref(settings.base_ref, authority)
    execution_proof = _validated_execution_proof(report)
    bindings = _binding_values(
        BindingContext(repo_root, source_ref, selector_paths, provenance_base, settings.change_id),
        root,
        execution_proof,
        authority,
    )
    producer_paths = authority.producer_paths if authority is not None else frozenset()
    bindings["mutable_sut_paths"] = sorted(
        _mutable_sut_paths(report, repo_root, source_ref, selector_paths, producer_paths)
    )
    _merge_execution_bindings(execution_proof, bindings)
    _validate_execution_bindings(report, repo_root, provenance_base, junit_root=root, cycle_authority=authority)
    _write_report_atomically(red_proof_path, report)


def _validated_test_file_digests(value: object, selector_paths: Sequence[str]) -> dict[str, object]:
    """Return selector-complete test digests or reject the proof."""
    if not isinstance(value, dict):
        raise ValueError("prior-red-proof-invalid")
    digests = cast(dict[str, object], value)
    if set(digests) != set(selector_paths):
        raise ValueError("prior-red-proof-invalid")
    return digests


def _validate_cycle_bindings(execution_proof: dict[str, object], cycle_authority: TrustedCycleAuthority | None) -> None:
    """Require cycle fields exactly when live cycle authority was authenticated."""
    expected = (
        {
            "cycle_base": cycle_authority.cycle_base,
            "cycle_authority_digest": cycle_authority.authority_digest,
            "prior_green_run_id": cycle_authority.prior_green_run_id,
            "prior_green_artifact_id": cycle_authority.prior_green_artifact_id,
            "prior_green_artifact_digest": cycle_authority.prior_green_artifact_digest,
        }
        if cycle_authority is not None
        else {}
    )
    cycle_fields = {
        "cycle_base",
        "cycle_authority_digest",
        "prior_green_run_id",
        "prior_green_artifact_id",
        "prior_green_artifact_digest",
    }
    unexpected = cycle_authority is None and not cycle_fields.isdisjoint(execution_proof)
    mismatch = cycle_authority is not None and any(
        execution_proof.get(field) != value for field, value in expected.items()
    )
    if unexpected or mismatch:
        raise ValueError("prior-red-proof-invalid")


def _validate_test_bindings(
    repo_root: Path, source_ref: str, selector_paths: Sequence[str], test_file_digests: dict[str, object]
) -> None:
    """Match every recorded selector digest to its committed regular test blob."""
    for test_path in selector_paths:
        recorded_digest = test_file_digests.get(test_path)
        if (
            not isinstance(recorded_digest, str)
            or not _test_path_is_regular_at_ref(repo_root, source_ref, test_path)
            or recorded_digest != _blob_digest_at_ref(repo_root, source_ref, test_path)
        ):
            raise ValueError("prior-red-proof-invalid")


def _validate_execution_bindings(
    report: dict[str, object],
    repo_root: Path,
    base_ref: str,
    *,
    junit_root: ParsedJunit,
    cycle_authority: TrustedCycleAuthority | None = None,
) -> None:
    """Verify every source, test, plan, and toolchain binding required by the red-proof contract."""
    source_ref, selector_paths = _selector_paths(report)
    execution_proof = _validated_execution_proof(report)
    source_tree = execution_proof.get("source_tree")
    merge_base = execution_proof.get("merge_base")
    test_file_digests = _validated_test_file_digests(execution_proof.get("test_file_digests"), selector_paths)
    toolchain_identity = execution_proof.get("toolchain_identity")
    _validated_toolchain_identity(toolchain_identity)
    if toolchain_identity != _toolchain_identity_from_junit(junit_root, _validated_selectors(execution_proof)):
        raise ValueError("prior-red-proof-invalid")
    actual_tree = _git(repo_root, "rev-parse", f"{source_ref}^{{tree}}").stdout.strip()
    actual_merge_base = _git(repo_root, "merge-base", base_ref, source_ref).stdout.strip()
    producer_paths = cycle_authority.producer_paths if cycle_authority is not None else frozenset()
    mutable_paths = sorted(_mutable_sut_paths(report, repo_root, source_ref, selector_paths, producer_paths))
    if (
        not _valid_report_digests(report)
        or source_tree != actual_tree
        or merge_base != actual_merge_base
        or execution_proof.get("mutable_sut_paths") != mutable_paths
    ):
        raise ValueError("prior-red-proof-invalid")
    _validate_cycle_bindings(execution_proof, cycle_authority)
    _validate_test_bindings(repo_root, source_ref, selector_paths, test_file_digests)


@beartype
@ensure(
    lambda result: all(
        finding in {"tdd-order-unproven", "stale-red-proof", "prior-red-proof-invalid"} for finding in result
    )
)
def validate_prior_red_proof(
    red_proof_path: Path,
    repo_root: Path,
    **options: object,
) -> list[str]:
    """Return deterministic findings when a red report cannot prove failing-first order."""
    settings = _proof_options(options, require_final=True)
    assert settings.final_ref is not None
    if _artifact_is_tracked(repo_root, red_proof_path) or _artifact_is_tracked(
        repo_root, red_proof_path.with_suffix(".xml")
    ):
        return ["prior-red-proof-invalid"]
    try:
        report = _read_red_proof(red_proof_path)
        junit_root = _validate_retained_red_junit(red_proof_path, report)
        source_ref, _ = _selector_paths(report)
        authority = _read_cycle_authority(
            settings.cycle_authority,
            CycleAuthorityContext(
                repo_root,
                settings.base_ref,
                settings.final_ref,
                source_ref,
                settings.repository,
                settings.pull_request,
                settings.head_branch,
                settings.change_id,
            ),
        )
        provenance_base = _provenance_base_ref(settings.base_ref, authority)
    except ValueError as error:
        return [str(error)]
    cycle_merges = _git(repo_root, "rev-list", "--merges", f"{provenance_base}..{settings.final_ref}")
    if not _red_source_precedes_final(repo_root, provenance_base, source_ref, settings.final_ref) or (
        authority is not None and (cycle_merges.returncode != 0 or bool(cycle_merges.stdout.strip()))
    ):
        return ["tdd-order-unproven"]
    try:
        _validate_execution_bindings(
            report, repo_root, provenance_base, junit_root=junit_root, cycle_authority=authority
        )
    except ValueError as error:
        return [str(error)]
    return _validate_red_history_freshness(
        report,
        repo_root,
        provenance_base,
        source_ref,
        settings.final_ref,
        settings.change_id,
        authority.producer_paths if authority is not None else frozenset(),
    )


def _parent_package_initializers(path: str) -> set[str]:
    """Return candidate package initializers executed while importing one path."""
    parent_parts = PurePosixPath(path).parent.parts
    return {
        (PurePosixPath(*parent_parts[:depth]) / "__init__.py").as_posix() for depth in range(1, len(parent_parts) + 1)
    }


def _validated_plan_cases(report: dict[str, object]) -> list[Mapping[str, object]]:
    """Return digest-bound plan cases from the retained reconciliation report."""
    plan = report.get("plan")
    if not isinstance(plan, Mapping):
        raise ValueError("prior-red-proof-invalid")
    typed_plan = cast(Mapping[str, object], plan)
    if any(typed_plan.get(field) != report.get(field) for field in ("mapping_digest", "plan_digest")):
        raise ValueError("prior-red-proof-invalid")
    cases = typed_plan.get("cases")
    if not isinstance(cases, list) or not cases or not all(isinstance(case, Mapping) for case in cases):
        raise ValueError("prior-red-proof-invalid")
    return cast(list[Mapping[str, object]], cases)


def _touchpoints_by_requirement(report: dict[str, object]) -> list[list[Mapping[str, object]]]:
    """Collapse expected per-case fan-out while rejecting contradictory touchpoints."""
    grouped: dict[str, list[Mapping[str, object]]] = {}
    for case in _validated_plan_cases(report):
        requirement_id = case.get("requirement_id")
        touchpoints = case.get("touchpoints")
        if (
            not isinstance(requirement_id, str)
            or not requirement_id
            or not isinstance(touchpoints, list)
            or not all(isinstance(touchpoint, Mapping) for touchpoint in touchpoints)
        ):
            raise ValueError("prior-red-proof-invalid")
        typed = cast(list[Mapping[str, object]], touchpoints)
        previous = grouped.setdefault(requirement_id, typed)
        if previous != typed:
            raise ValueError("prior-red-proof-invalid")
    return list(grouped.values())


def _test_support_roots(selector_paths: Sequence[str]) -> set[str]:
    """Return the repository roots containing selected pytest support bytes."""
    roots: set[str] = set()
    for selector_path in selector_paths:
        parts = PurePosixPath(selector_path).parts
        test_index = next((index for index, part in enumerate(parts[:-1]) if part in {"test", "tests"}), None)
        if test_index is not None:
            roots.add(PurePosixPath(*parts[: test_index + 1]).as_posix())
        elif len(parts) > 1:
            roots.add(PurePosixPath(*parts[:-1]).as_posix())
    return roots


def _frozen_proof_paths(selector_paths: Sequence[str]) -> set[str]:
    """Return exact proof-authority paths that mapping content cannot unfreeze."""
    configurations = {path for selector in selector_paths for path in _applicable_pytest_configuration_paths(selector)}
    conftests = {path for selector in selector_paths for path in _applicable_conftest_paths(selector)}
    plugin_paths = _python_module_paths(("scripts", "requirements_proof_pytest_plugin"))
    initializers = {
        initializer for path in {*selector_paths, *plugin_paths} for initializer in _parent_package_initializers(path)
    }
    return {
        *configurations,
        *conftests,
        *plugin_paths,
        *initializers,
        *NON_TRANSITIVE_PROOF_INPUTS,
        "scripts/requirements_proof_executor.py",
        "uv.lock",
    }


def _canonical_mutable_locator(locator: object) -> str:
    """Return one literal repository path or reject aliases and broad patterns."""
    if not isinstance(locator, str) or not locator or any(character in locator for character in "*?[]{}\\"):
        raise ValueError("prior-red-proof-invalid")
    if any(ord(character) < 32 for character in locator):
        raise ValueError("prior-red-proof-invalid")
    path = PurePosixPath(locator)
    if path.is_absolute() or ".." in path.parts or path.as_posix() != locator:
        raise ValueError("prior-red-proof-invalid")
    return locator


def _path_is_under(path: str, roots: set[str]) -> bool:
    """Return whether an exact path belongs to one frozen support tree."""
    return any(path == root or path.startswith(f"{root}/") for root in roots)


def _mutable_marker_enabled(touchpoint: Mapping[str, object]) -> bool:
    """Return whether one touchpoint explicitly permits post-red SUT edits."""
    mutable = touchpoint.get("mutable_after_red")
    if mutable is not None and not isinstance(mutable, bool):
        raise ValueError("prior-red-proof-invalid")
    return mutable is True


def _mutable_identity_is_valid(touchpoint: Mapping[str, object]) -> bool:
    """Return whether one mutable touchpoint has literal non-empty identity fields."""
    identifier = touchpoint.get("id")
    kind = touchpoint.get("kind")
    return isinstance(identifier, str) and bool(identifier) and isinstance(kind, str) and bool(kind)


def _mutable_locator_is_valid(locator: str, kind: object, policy: _MutablePathPolicy) -> bool:
    """Return whether one locator is an exact, unique, regular SUT path."""
    immutable_role = (
        kind in {"test_file", "lockfile"} or locator in policy.frozen or _path_is_under(locator, policy.support_roots)
    )
    return (
        not immutable_role
        and locator not in policy.accepted
        and _test_path_is_regular_at_ref(policy.repo_root, policy.source_ref, locator)
    )


def _approved_mutable_locator(touchpoint: Mapping[str, object], policy: _MutablePathPolicy) -> str | None:
    """Return one valid mutable locator, or None for an immutable touchpoint."""
    if not _mutable_marker_enabled(touchpoint):
        return None
    kind = touchpoint.get("kind")
    locator = _canonical_mutable_locator(touchpoint.get("locator"))
    if not _mutable_identity_is_valid(touchpoint):
        raise ValueError("prior-red-proof-invalid")
    if locator in policy.producer_paths:
        return None
    if not _mutable_locator_is_valid(locator, kind, policy):
        raise ValueError("prior-red-proof-invalid")
    return locator


def _mutable_sut_paths(
    report: dict[str, object],
    repo_root: Path,
    source_ref: str,
    selector_paths: Sequence[str],
    producer_paths: frozenset[str] = frozenset(),
) -> set[str]:
    """Return exact owner-approved post-red SUT paths from the bound plan."""
    frozen = _frozen_proof_paths(selector_paths)
    support_roots = _test_support_roots(selector_paths)
    mutable_paths: set[str] = set()
    policy = _MutablePathPolicy(repo_root, source_ref, frozen, support_roots, mutable_paths, producer_paths)
    for touchpoints in _touchpoints_by_requirement(report):
        for touchpoint in touchpoints:
            locator = _approved_mutable_locator(touchpoint, policy)
            if locator is not None:
                mutable_paths.add(locator)
    return mutable_paths


def _red_history_boundary(values: tuple[object, ...]) -> _RedHistoryBoundary:
    """Normalize the retained backward-compatible boundary call shape."""
    if len(values) not in {4, 5}:
        raise ValueError("prior-red-proof-invalid")
    base_ref, source_ref, final_ref, change_id, *producer_values = values
    producer_paths = producer_values[0] if producer_values else frozenset()
    if (
        not isinstance(base_ref, str)
        or not isinstance(source_ref, str)
        or not isinstance(final_ref, str)
        or (change_id is not None and not isinstance(change_id, str))
        or not isinstance(producer_paths, frozenset)
        or not all(isinstance(path, str) for path in producer_paths)
    ):
        raise ValueError("prior-red-proof-invalid")
    return _RedHistoryBoundary(base_ref, source_ref, final_ref, change_id, producer_paths)


def _validate_red_history_freshness(
    report: dict[str, object],
    repo_root: Path,
    *boundary_values: object,
) -> list[str]:
    """Reject production-before-red and every unapproved path touched after red."""
    boundary = _red_history_boundary(boundary_values)
    _, selector_paths = _selector_paths(report)
    paths_before_red = _changed_paths_in_history(repo_root, boundary.base_ref, boundary.source_ref)
    if paths_before_red is None or _has_governed_production_path(paths_before_red, boundary.change_id):
        return ["tdd-order-unproven"]
    paths_after_red = _changed_paths_in_history(repo_root, boundary.source_ref, boundary.final_ref, merge_parent=1)
    if paths_after_red is None:
        return ["tdd-order-unproven"]
    try:
        mutable_paths = _mutable_sut_paths(
            report,
            repo_root,
            boundary.source_ref,
            selector_paths,
            boundary.producer_paths,
        )
    except ValueError as error:
        return [str(error)]
    if any(path not in mutable_paths and path not in boundary.producer_paths for path in paths_after_red):
        return ["stale-red-proof"]
    return []


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    proof_mode = parser.add_mutually_exclusive_group(required=True)
    proof_mode.add_argument("--prior-red-proof", type=Path, help="Runner-produced red reconciliation report.")
    proof_mode.add_argument("--bind-red-proof", type=Path, help="Fresh red report to bind before artifact upload.")
    parser.add_argument("--junit", type=Path, help="JUnit artifact written beside a fresh bind-mode report.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="Repository containing both Git sources.")
    parser.add_argument(
        "--base-ref", required=True, help="Pull-request base ref used to detect pre-red production changes."
    )
    parser.add_argument("--final-ref", help="Final source commit under reconciliation.")
    parser.add_argument(
        "--cycle-authority", type=Path, help="Validator-owned amendment authority; raw cycle refs are rejected."
    )
    parser.add_argument("--repository", help="GitHub owner/name used to re-authenticate amendment authority.")
    parser.add_argument("--pull-request", type=int, help="Pull request bound to the prior successful run.")
    parser.add_argument("--head-branch", help="Head branch bound to the prior successful run.")
    parser.add_argument("--change-id", help="Authenticated OpenSpec change bound to red-history artifacts.")
    return parser


@beartype
@ensure(lambda result: result in {0, 1})
def main(argv: Sequence[str] | None = None) -> int:
    """Print provenance findings for the workflow's retained diagnostic report."""
    arguments = _build_parser().parse_args(argv)
    if arguments.bind_red_proof is not None:
        if arguments.junit is None:
            sys.stderr.write("prior-red-proof-invalid\n")
            return 1
        try:
            bind_red_proof(
                arguments.bind_red_proof,
                arguments.repo_root.resolve(),
                base_ref=arguments.base_ref,
                final_ref=arguments.final_ref,
                junit_path=arguments.junit,
                cycle_authority=arguments.cycle_authority,
                repository=arguments.repository,
                pull_request=arguments.pull_request,
                head_branch=arguments.head_branch,
                change_id=arguments.change_id,
            )
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            sys.stderr.write(f"{error}\n")
            return 1
        return 0
    if arguments.prior_red_proof is None or arguments.final_ref is None:
        sys.stderr.write("prior-red-proof-invalid\n")
        return 1
    findings = validate_prior_red_proof(
        arguments.prior_red_proof,
        arguments.repo_root.resolve(),
        base_ref=arguments.base_ref,
        final_ref=arguments.final_ref,
        cycle_authority=arguments.cycle_authority,
        repository=arguments.repository,
        pull_request=arguments.pull_request,
        head_branch=arguments.head_branch,
        change_id=arguments.change_id,
    )
    if findings:
        sys.stderr.write(f"{','.join(findings)}\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

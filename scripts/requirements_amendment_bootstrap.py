"""Authenticate an approved partial-red amendment artifact and normalize its failed cases."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from html import escape
from pathlib import Path
from typing import Protocol, cast

from beartype import beartype
from icontract import ensure


AUTHORITY_HEADER = "SPECFACT_REQUIREMENTS_AMENDMENT_BOOTSTRAP_V2"
EXTERNAL_AUTHORITY_KIND = "externally-approved-amendment-bootstrap"
APPROVED_BOOTSTRAP_LOCATOR = {
    "comment_id": 5464938148,
    "repository": "nold-ai/specfact-cli",
    "change_id": "fix-release-promotion-security-gates",
    "issue": 692,
    "pull_request": 698,
    "head_branch": "codex/692-computed-owner-red-proof-v2",
}


class _ParsedJunit(Protocol):
    cases: tuple[dict[str, tuple[str, ...]], ...]
    outcomes: tuple[str, ...]


class _ProvenanceModule(Protocol):
    def _parse_junit(self, payload: bytes) -> _ParsedJunit: ...


class _CycleBaseModule(Protocol):
    CycleBasePaths: Callable[[Path, Path, Path, Path], object]
    CycleBaseContext: Callable[[str, str, str, int, str], object]
    _common_history_matches: Callable[[object, object, str, str], bool]
    _artifact_is_verified_final: Callable[[Path, str], bool]


@dataclass(frozen=True)
class _ArtifactFiles:
    red_report: Path
    red_junit: Path
    red_plan: Path
    green_report: Path
    green_junit: Path
    green_plan: Path


@dataclass(frozen=True)
class _EvidenceInputs:
    """Typed raw GitHub metadata and artifact paths for one approved cycle."""

    files: _ArtifactFiles
    red_run: dict[str, object]
    green_run: dict[str, object]
    red_artifacts: dict[str, object]
    green_artifacts: dict[str, object]


def _read(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("amendment-bootstrap-invalid")
    return cast(dict[str, object], value)


def _digest(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _authority(comment_path: Path, *, comment_id: int, repository: str, issue: int) -> dict[str, object]:
    comment = _read(comment_path)
    user = comment.get("user")
    body = comment.get("body")
    identity_matches = all(
        (
            comment.get("id") == comment_id,
            comment.get("issue_url") == f"https://api.github.com/repos/{repository}/issues/{issue}",
            comment.get("author_association") in {"COLLABORATOR", "MEMBER", "OWNER"},
            comment.get("created_at") == comment.get("updated_at"),
            isinstance(user, dict),
            isinstance(body, str),
        )
    )
    if not identity_matches or not isinstance(user, dict) or not isinstance(body, str):
        raise ValueError("amendment-bootstrap-invalid")
    typed_user = cast(dict[str, object], user)
    header, separator, payload = body.partition("\n")
    decoded = json.loads(payload) if header == AUTHORITY_HEADER and separator else None
    if not isinstance(decoded, dict):
        raise ValueError("amendment-bootstrap-invalid")
    typed_decoded = cast(dict[str, object], decoded)
    if typed_decoded.get("signer_login") != typed_user.get("login"):
        raise ValueError("amendment-bootstrap-invalid")
    return typed_decoded


def _artifact(artifacts: dict[str, object], *, artifact_id: object, digest: object, run_id: object) -> bool:
    entries = artifacts.get("artifacts")
    if not isinstance(entries, list):
        return False
    typed_entries = (cast(dict[str, object], entry) for entry in entries if isinstance(entry, dict))
    matches = [entry for entry in typed_entries if entry.get("id") == artifact_id]
    if len(matches) != 1:
        return False
    artifact = cast(dict[str, object], matches[0])
    workflow_run = artifact.get("workflow_run")
    if not isinstance(workflow_run, dict):
        return False
    typed_workflow_run = cast(dict[str, object], workflow_run)
    return all(
        (
            artifact.get("name") == "requirements-evidence",
            artifact.get("expired") is False,
            artifact.get("digest") == digest,
            typed_workflow_run.get("id") == run_id,
        )
    )


def _run(run: dict[str, object], authority: dict[str, object], *, green: bool) -> bool:
    expected_id = authority.get("prior_green_run_id" if green else "run_id")
    expected_sha = authority.get("cycle_base_commit" if green else "red_commit")
    repository = run.get("repository")
    pull_requests = run.get("pull_requests")
    if not isinstance(repository, dict) or not isinstance(pull_requests, list):
        return False
    typed_repository = cast(dict[str, object], repository)
    pull_request_numbers = [
        cast(dict[str, object], item).get("number") for item in pull_requests if isinstance(item, dict)
    ]
    return all(
        (
            run.get("id") == expected_id,
            run.get("head_sha") == expected_sha,
            run.get("head_branch") == authority.get("head_branch"),
            run.get("status") == "completed",
            run.get("conclusion") == ("success" if green else "failure"),
            run.get("name") == "Requirements Evidence",
            typed_repository.get("full_name") == authority.get("repository"),
            authority.get("pull_request") in pull_request_numbers,
        )
    )


def _git(repo_root: Path, *arguments: str) -> str:
    return subprocess.run(["git", *arguments], cwd=repo_root, check=True, capture_output=True, text=True).stdout.strip()


def _load_provenance() -> _ProvenanceModule:
    path = Path(__file__).with_name("requirements_proof_provenance.py")
    spec = importlib.util.spec_from_file_location("requirements_proof_provenance_bootstrap", path)
    if spec is None or spec.loader is None:
        raise ValueError("amendment-bootstrap-invalid")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return cast(_ProvenanceModule, module)


def _load_cycle_base() -> _CycleBaseModule:
    """Load the shared cycle boundary without importing mutable package state."""
    path = Path(__file__).with_name("requirements_cycle_base.py")
    spec = importlib.util.spec_from_file_location("requirements_cycle_base_bootstrap", path)
    if spec is None or spec.loader is None:
        raise ValueError("amendment-bootstrap-invalid")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return cast(_CycleBaseModule, module)


def _plan_selectors(plan_report: dict[str, object]) -> tuple[list[str], str, str]:
    """Return the exact executable plan selectors and governed digests."""
    plan = plan_report.get("plan")
    if not isinstance(plan, dict):
        raise ValueError("amendment-bootstrap-invalid")
    typed_plan = cast(dict[str, object], plan)
    cases = typed_plan.get("cases")
    mapping_digest = plan_report.get("mapping_digest")
    plan_digest = typed_plan.get("plan_digest")
    if (
        plan_report.get("gate_decision") != "pass"
        or plan_report.get("observed_maturity") != "test-authored"
        or not isinstance(cases, list)
        or not isinstance(mapping_digest, str)
        or typed_plan.get("mapping_digest") != mapping_digest
        or not isinstance(plan_digest, str)
    ):
        raise ValueError("amendment-bootstrap-invalid")
    return _test_case_selectors(cases), mapping_digest, plan_digest


def _test_case_selectors(cases: list[object]) -> list[str]:
    """Return the unique sorted selectors from validated test plan cases."""
    selectors: list[object] = []
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("amendment-bootstrap-invalid")
        typed_case = cast(dict[str, object], case)
        if typed_case.get("method") == "test":
            selectors.append(typed_case.get("node_id"))
    if (
        not selectors
        or not all(isinstance(selector, str) for selector in selectors)
        or len(set(selectors)) != len(selectors)
    ):
        raise ValueError("amendment-bootstrap-invalid")
    return sorted(cast(list[str], selectors))


def _raw_failed_selectors(plan_report: dict[str, object], raw_junit: Path) -> tuple[list[str], list[str]]:
    """Derive the red subset only from exact per-case raw JUnit outcomes."""
    expected, _, _ = _plan_selectors(plan_report)
    parsed = _load_provenance()._parse_junit(raw_junit.read_bytes())
    observed: dict[str, str] = {}
    for properties, outcome in zip(parsed.cases, parsed.outcomes, strict=True):
        selectors = properties.get("specfact.selector", ())
        if len(selectors) != 1 or selectors[0] in observed:
            raise ValueError("amendment-bootstrap-invalid")
        observed[selectors[0]] = outcome
    if set(observed) != set(expected):
        raise ValueError("amendment-bootstrap-invalid")
    failed = sorted(selector for selector, outcome in observed.items() if outcome == "failed")
    return failed, expected


def _normalized_junit(raw_junit: Path, failed: Sequence[str]) -> bytes:
    parsed = _load_provenance()._parse_junit(raw_junit.read_bytes())
    cases: list[str] = []
    for properties, outcome in zip(parsed.cases, parsed.outcomes, strict=True):
        selectors = properties.get("specfact.selector", ())
        if len(selectors) != 1 or selectors[0] not in failed:
            continue
        if outcome != "failed":
            raise ValueError("amendment-bootstrap-invalid")
        encoded = "".join(
            f'<property name="{escape(name, quote=True)}" value="{escape(value, quote=True)}"/>'
            for name, values in sorted(properties.items())
            for value in values
        )
        cases.append(f"<testcase><properties>{encoded}</properties><failure/></testcase>")
    if len(cases) != len(failed):
        raise ValueError("amendment-bootstrap-invalid")
    return (f'<testsuite tests="{len(cases)}" failures="{len(cases)}">' + "".join(cases) + "</testsuite>").encode()


def _artifact_files(arguments: argparse.Namespace) -> _ArtifactFiles:
    """Return the fixed report, JUnit, and plan paths in both artifacts."""
    return _ArtifactFiles(
        arguments.red_artifact_root / "requirements-evidence.json",
        arguments.red_artifact_root / "requirements-proof.xml",
        arguments.red_artifact_root / "requirements-evidence-plan.json",
        arguments.green_artifact_root / "requirements-evidence.json",
        arguments.green_artifact_root / "requirements-proof.xml",
        arguments.green_artifact_root / "requirements-evidence-plan.json",
    )


def _context_matches(arguments: argparse.Namespace, authority: dict[str, object]) -> bool:
    """Validate the approved repository, change, branch, and expiry context."""
    expiry = datetime.fromisoformat(str(authority.get("expires_at")).replace("Z", "+00:00"))
    return all(
        (
            expiry > datetime.now(UTC),
            authority.get("repository") == arguments.repository,
            authority.get("change_id") == arguments.change_id,
            authority.get("issue") == arguments.issue,
            authority.get("pull_request") == arguments.pull_request,
            authority.get("head_branch") == arguments.head_branch,
        )
    )


def _approved_locator_matches(arguments: argparse.Namespace) -> bool:
    """Restrict the exception to the one product-owner approved GitHub locator."""
    return all(getattr(arguments, field) == value for field, value in APPROVED_BOOTSTRAP_LOCATOR.items())


def _cycle_boundary_matches(arguments: argparse.Namespace, authority: dict[str, object], files: _ArtifactFiles) -> bool:
    """Retain every ordinary history and verified-green check except producer authorship."""
    module = _load_cycle_base()
    paths = module.CycleBasePaths(
        arguments.green_run, arguments.green_artifacts, files.green_report.parent, arguments.repo_root
    )
    context = module.CycleBaseContext(
        arguments.base_ref,
        arguments.final_ref,
        arguments.repository,
        arguments.pull_request,
        arguments.head_branch,
    )
    cycle_base = authority.get("cycle_base_commit")
    red_ref = authority.get("red_commit")
    return (
        isinstance(cycle_base, str)
        and isinstance(red_ref, str)
        and module._common_history_matches(paths, context, cycle_base, red_ref)
        and module._artifact_is_verified_final(files.green_report.parent, cycle_base)
    )


def _metadata_matches(
    arguments: argparse.Namespace,
    authority: dict[str, object],
    evidence: _EvidenceInputs,
) -> bool:
    """Bind approval metadata to immutable GitHub artifacts and commit trees."""
    return all(
        (
            _approved_locator_matches(arguments),
            _context_matches(arguments, authority),
            _run(evidence.red_run, authority, green=False),
            _run(evidence.green_run, authority, green=True),
            _artifact(
                evidence.red_artifacts,
                artifact_id=authority.get("artifact_id"),
                digest=authority.get("artifact_digest"),
                run_id=authority.get("run_id"),
            ),
            _artifact(
                evidence.green_artifacts,
                artifact_id=authority.get("prior_green_artifact_id"),
                digest=authority.get("prior_green_artifact_digest"),
                run_id=authority.get("prior_green_run_id"),
            ),
            _digest(evidence.files.red_report) == authority.get("report_digest"),
            _digest(evidence.files.red_junit) == authority.get("junit_digest"),
            _digest(evidence.files.red_plan) == authority.get("plan_report_digest"),
            _digest(evidence.files.green_report) == authority.get("prior_green_report_digest"),
            _digest(evidence.files.green_junit) == authority.get("prior_green_junit_digest"),
            _digest(evidence.files.green_plan) == authority.get("prior_green_plan_report_digest"),
            _git(arguments.repo_root, "rev-parse", f"{authority['red_commit']}^{{tree}}") == authority.get("red_tree"),
            _git(arguments.repo_root, "rev-parse", f"{authority['cycle_base_commit']}^{{tree}}")
            == authority.get("cycle_base_tree"),
            _git(arguments.repo_root, "merge-base", "--is-ancestor", str(authority["red_commit"]), arguments.final_ref)
            == "",
            _cycle_boundary_matches(arguments, authority, evidence.files),
        )
    )


def _authority_receipt(arguments: argparse.Namespace, authority: dict[str, object]) -> dict[str, object]:
    """Serialize the exact live-approved capability for downstream revalidation."""
    canonical = json.dumps(authority, sort_keys=True, separators=(",", ":")).encode()
    return {
        **authority,
        "kind": EXTERNAL_AUTHORITY_KIND,
        "comment_id": arguments.comment_id,
        "cycle_base": authority["cycle_base_commit"],
        "red_ref": authority["red_commit"],
        "authority_digest": f"sha256:{hashlib.sha256(canonical).hexdigest()}",
    }


def _validate_failed_selectors(
    plan_report: dict[str, object], authority: dict[str, object], failed: Sequence[str], selectors: Sequence[str]
) -> None:
    """Validate exact failed/passing counts and the approved plan bindings."""
    _, mapping_digest, plan_digest = _plan_selectors(plan_report)
    selector_digest = (
        f"sha256:{hashlib.sha256(json.dumps(failed, sort_keys=True, separators=(',', ':')).encode()).hexdigest()}"
    )
    matches = all(
        (
            len(failed) == authority.get("expected_failed_cases"),
            len(selectors) - len(failed) == authority.get("expected_passing_cases"),
            selector_digest == authority.get("cycle_selector_digest"),
            mapping_digest == authority.get("mapping_digest"),
            plan_digest == authority.get("plan_digest"),
        )
    )
    if not matches:
        raise ValueError("amendment-bootstrap-invalid")


def _red_report(
    plan_report: dict[str, object],
    authority: dict[str, object],
    failed: Sequence[str],
    junit: bytes,
) -> dict[str, object]:
    """Build a red report from an immutable plan and exact raw failures."""
    _, mapping_digest, plan_digest = _plan_selectors(plan_report)
    report = dict(plan_report)
    report.update(
        delivery_status="failing-first-proven",
        implementation_evidence="failing-first-proven",
        observed_maturity="red",
        required_maturity="red",
        mapping_digest=mapping_digest,
        plan_digest=plan_digest,
        gate_decision="pass",
        verdict="passed",
        findings=[],
        execution_proof={
            "run_stage": "red",
            "source_ref": authority["red_commit"],
            "selectors": list(failed),
            "junit_digest": f"sha256:{hashlib.sha256(junit).hexdigest()}",
            "approved_raw_report_digest": authority["report_digest"],
            "approved_raw_junit_digest": authority["junit_digest"],
        },
    )
    return report


@beartype
@ensure(lambda result: result is None)
def normalize(arguments: argparse.Namespace) -> None:
    """Authenticate approved raw evidence and write its minimal failed subset."""
    authority = _authority(
        arguments.comment, comment_id=arguments.comment_id, repository=arguments.repository, issue=arguments.issue
    )
    evidence = _EvidenceInputs(
        _artifact_files(arguments),
        _read(arguments.red_run),
        _read(arguments.green_run),
        _read(arguments.red_artifacts),
        _read(arguments.green_artifacts),
    )
    if not _metadata_matches(arguments, authority, evidence):
        raise ValueError("amendment-bootstrap-invalid")
    plan_report = _read(evidence.files.red_plan)
    failed, selectors = _raw_failed_selectors(plan_report, evidence.files.red_junit)
    _validate_failed_selectors(plan_report, authority, failed, selectors)
    junit = _normalized_junit(evidence.files.red_junit, failed)
    report = _red_report(plan_report, authority, failed, junit)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    arguments.output.with_suffix(".xml").write_bytes(junit)
    if arguments.authority_output is not None:
        arguments.authority_output.parent.mkdir(parents=True, exist_ok=True)
        arguments.authority_output.write_text(
            json.dumps(_authority_receipt(arguments, authority), sort_keys=True) + "\n", encoding="utf-8"
        )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "comment",
        "red-run",
        "red-artifacts",
        "red-artifact-root",
        "green-run",
        "green-artifacts",
        "green-artifact-root",
        "repo-root",
        "output",
    ):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--comment-id", type=int, required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--change-id", required=True)
    parser.add_argument("--issue", type=int, required=True)
    parser.add_argument("--pull-request", type=int, required=True)
    parser.add_argument("--head-branch", required=True)
    parser.add_argument("--final-ref", required=True)
    parser.add_argument("--base-ref", required=True)
    parser.add_argument("--authority-output", type=Path)
    return parser


@beartype
@ensure(lambda result: isinstance(result, int))
def main(argv: Sequence[str] | None = None) -> int:
    try:
        normalize(_parser().parse_args(argv))
    except (KeyError, OSError, subprocess.SubprocessError, TypeError, ValueError):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

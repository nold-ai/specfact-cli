#!/usr/bin/env python3
"""Authenticate Requirements evidence reused by an exact dev-to-main promotion."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import zipfile
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import NamedTuple, NoReturn, cast
from xml.parsers import expat


REPOSITORY = "nold-ai/specfact-cli"
REPOSITORY_ID = 1085706003
BASE_REF = "main"
HEAD_REF = "dev"
GITHUB_ACTIONS_APP_ID = 15368
REQUIREMENTS_WORKFLOW_ID = 323253915
AUTHORITY_WORKFLOW_ID = 348163848
REQUIREMENTS_WORKFLOW_PATH = ".github/workflows/requirements-evidence.yml"
AUTHORITY_WORKFLOW_PATH = ".github/workflows/trusted-requirements-authority.yml"
MAX_INPUT_BYTES = 100 * 1024 * 1024
MAX_ARCHIVE_MEMBER_BYTES = 25 * 1024 * 1024
MAX_ARCHIVE_CONTENT_BYTES = 50 * 1024 * 1024
OBJECT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
GitRunner = Callable[[Path, list[str]], str]


PromotionReuseError = ValueError


class PromotionInputs(NamedTuple):
    """Authenticated inputs required to validate one protected promotion."""

    event: dict[str, object]
    repo_root: Path
    source_pulls: object
    check_runs: object
    requirements_run: dict[str, object]
    authority_run: dict[str, object]
    artifacts: object
    producer_archive: Path
    execution_archive: Path


class _RunExpectation(NamedTuple):
    source_branch: str
    source_sha: str
    name: str
    path: str
    workflow_id: int
    required_workflow: bool


class _SourceRun(NamedTuple):
    run_id: int
    branch: str
    sha: str


class _ArtifactFiles(NamedTuple):
    producer: Path
    execution: Path


def _reject() -> NoReturn:
    raise PromotionReuseError("promotion-reuse-invalid")


def _object(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        _reject()
    return cast(dict[str, object], value)


def _integer(value: object) -> int:
    if type(value) is not int or cast(int, value) <= 0:
        _reject()
    return cast(int, value)


def _string(value: object, pattern: re.Pattern[str] | None = None) -> str:
    if not isinstance(value, str) or not value or (pattern is not None and pattern.fullmatch(value) is None):
        _reject()
    return value


def _strings(value: object) -> list[str]:
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
        _reject()
    result = cast(list[str], value)
    if len(result) != len(set(result)):
        _reject()
    return result


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            _reject()
        result[key] = value
    return result


def _regular_payload(path: Path, *, maximum: int = MAX_INPUT_BYTES) -> bytes:
    details = path.lstat()
    if not stat.S_ISREG(details.st_mode) or details.st_size > maximum:
        _reject()
    payload = path.read_bytes()
    if len(payload) != details.st_size:
        _reject()
    return payload


def _json_value(payload: bytes) -> object:
    try:
        return json.loads(payload, object_pairs_hook=_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise PromotionReuseError("promotion-reuse-invalid") from error


def _read_json(path: Path) -> object:
    return _json_value(_regular_payload(path))


def _digest(payload: bytes) -> str:
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def _repository(value: object) -> None:
    repository = _object(value)
    if repository.get("id") != REPOSITORY_ID or repository.get("full_name") != REPOSITORY:
        _reject()


def _run_git(repo_root: Path, arguments: list[str]) -> str:
    """Run one bounded Git query and return its stripped stdout."""
    completed = subprocess.run(
        ["git", *arguments],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return completed.stdout.strip()


def _git(git_runner: GitRunner, repo_root: Path, arguments: list[str]) -> str:
    try:
        return git_runner(repo_root, arguments).strip()
    except (OSError, subprocess.SubprocessError) as error:
        raise PromotionReuseError("promotion-reuse-invalid") from error


def _git_object(git_runner: GitRunner, repo_root: Path, commit: str) -> None:
    if _git(git_runner, repo_root, ["cat-file", "-t", commit]) != "commit":
        _reject()


def _validate_event(event: dict[str, object]) -> tuple[int, str, str]:
    _repository(event.get("repository"))
    pull_request = _object(event.get("pull_request"))
    base = _object(pull_request.get("base"))
    head = _object(pull_request.get("head"))
    _repository(base.get("repo"))
    _repository(head.get("repo"))
    if base.get("ref") != BASE_REF or head.get("ref") != HEAD_REF:
        _reject()
    return (
        _integer(pull_request.get("number")),
        _string(base.get("sha"), OBJECT_PATTERN),
        _string(head.get("sha"), OBJECT_PATTERN),
    )


def _validate_git(repo_root: Path, base_sha: str, head_sha: str, git_runner: GitRunner) -> tuple[str, str, str]:
    if _git(git_runner, repo_root, ["rev-parse", "HEAD"]) != head_sha:
        _reject()
    head_tree = _string(_git(git_runner, repo_root, ["rev-parse", "HEAD^{tree}"]), OBJECT_PATTERN)
    if _git(git_runner, repo_root, ["rev-parse", "refs/remotes/origin/main^{commit}"]) != base_sha:
        _reject()
    if _git(git_runner, repo_root, ["rev-parse", "refs/remotes/origin/dev^{commit}"]) != head_sha:
        _reject()
    _git_object(git_runner, repo_root, base_sha)
    _git_object(git_runner, repo_root, head_sha)
    _git(git_runner, repo_root, ["merge-base", "--is-ancestor", base_sha, head_sha])
    parents = _git(git_runner, repo_root, ["rev-list", "--parents", "-n", "1", head_sha]).split()
    if len(parents) != 3 or parents[0] != head_sha:
        _reject()
    previous_dev_sha = _string(parents[1], OBJECT_PATTERN)
    source_sha = _string(parents[2], OBJECT_PATTERN)
    if len({head_sha, previous_dev_sha, source_sha}) != 3:
        _reject()
    _git_object(git_runner, repo_root, previous_dev_sha)
    _git_object(git_runner, repo_root, source_sha)
    if _git(git_runner, repo_root, ["rev-parse", f"{source_sha}^{{tree}}"]) != head_tree:
        _reject()
    return head_tree, previous_dev_sha, source_sha


def _flatten_source_pulls(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        _reject()
    entries = cast(list[object], value)
    if entries and all(isinstance(entry, list) for entry in entries):
        entries = [item for page in cast(list[list[object]], entries) for item in page]
    if not all(isinstance(entry, dict) for entry in entries):
        _reject()
    return cast(list[dict[str, object]], entries)


def _validate_source_pull(
    source_pulls: object, previous_dev_sha: str, source_sha: str, head_sha: str
) -> dict[str, object]:
    candidates = [pull for pull in _flatten_source_pulls(source_pulls) if pull.get("merge_commit_sha") == head_sha]
    if len(candidates) != 1:
        _reject()
    source_pull = candidates[0]
    base = _object(source_pull.get("base"))
    head = _object(source_pull.get("head"))
    _repository(base.get("repo"))
    _repository(head.get("repo"))
    if (
        source_pull.get("state") != "closed"
        or not isinstance(source_pull.get("merged_at"), str)
        or not source_pull["merged_at"]
        or base.get("ref") != HEAD_REF
        or base.get("sha") != previous_dev_sha
        or head.get("sha") != source_sha
    ):
        _reject()
    _string(head.get("ref"))
    _integer(source_pull.get("number"))
    return source_pull


def _complete_collection(payload: object, field: str) -> list[dict[str, object]]:
    pages = cast(list[object], payload) if isinstance(payload, list) else [payload]
    parsed_pages = [_collection_page(page, field) for page in pages]
    totals = {total for total, _entries in parsed_pages}
    if len(totals) != 1:
        _reject()
    expected_total = totals.pop()
    entries = [entry for _total, page_entries in parsed_pages for entry in page_entries]
    if len(entries) != expected_total:
        _reject()
    return entries


def _collection_page(page_value: object, field: str) -> tuple[int, list[dict[str, object]]]:
    page = _object(page_value)
    total = page.get("total_count")
    page_entries = page.get(field)
    if type(total) is not int or cast(int, total) < 0:
        _reject()
    if not isinstance(page_entries, list) or not all(isinstance(entry, dict) for entry in page_entries):
        _reject()
    return cast(int, total), cast(list[dict[str, object]], page_entries)


def _required_check(checks: list[dict[str, object]], name: str) -> dict[str, object]:
    matching = [check for check in checks if check.get("name") == name]
    if len(matching) != 1:
        _reject()
    return matching[0]


def _validate_check(check: dict[str, object], *, run_id: int, source_sha: str) -> None:
    check_id = _integer(check.get("id"))
    app = _object(check.get("app"))
    owner = _object(app.get("owner"))
    expected_url = f"https://github.com/{REPOSITORY}/actions/runs/{run_id}/job/{check_id}"
    if (
        check.get("status") != "completed"
        or check.get("conclusion") != "success"
        or check.get("head_sha") != source_sha
        or check.get("details_url") != expected_url
        or app.get("id") != GITHUB_ACTIONS_APP_ID
        or app.get("slug") != "github-actions"
        or owner.get("login") != "github"
    ):
        _reject()


def _validate_run(
    run: dict[str, object],
    *,
    check: dict[str, object],
    expected: _RunExpectation,
) -> int:
    run_id = _integer(run.get("id"))
    _repository(run.get("repository"))
    workflow_kind = "required_workflows" if expected.required_workflow else "workflows"
    expected_url = f"https://api.github.com/repos/{REPOSITORY}/actions/{workflow_kind}/{expected.workflow_id}"
    fields = {
        "event": "pull_request",
        "name": expected.name,
        "path": expected.path,
        "workflow_id": expected.workflow_id,
        "workflow_url": expected_url,
        "status": "completed",
        "conclusion": "success",
        "head_sha": expected.source_sha,
        "head_branch": expected.source_branch,
    }
    if any(run.get(field) != value for field, value in fields.items()):
        _reject()
    _validate_check(check, run_id=run_id, source_sha=expected.source_sha)
    return run_id


def _validate_checks_and_runs(
    check_runs: object,
    requirements_run: dict[str, object],
    authority_run: dict[str, object],
    source_branch: str,
    source_sha: str,
) -> tuple[int, int]:
    checks = _complete_collection(check_runs, "check_runs")
    requirements_check = _required_check(checks, "Requirements evidence")
    authority_check = _required_check(checks, "Trusted Requirements Authority")
    requirements_run_id = _validate_run(
        requirements_run,
        check=requirements_check,
        expected=_RunExpectation(
            source_branch,
            source_sha,
            "Requirements Evidence",
            REQUIREMENTS_WORKFLOW_PATH,
            REQUIREMENTS_WORKFLOW_ID,
            False,
        ),
    )
    authority_run_id = _validate_run(
        authority_run,
        check=authority_check,
        expected=_RunExpectation(
            source_branch,
            source_sha,
            "Trusted Requirements Authority",
            AUTHORITY_WORKFLOW_PATH,
            AUTHORITY_WORKFLOW_ID,
            True,
        ),
    )
    if requirements_run_id == authority_run_id:
        _reject()
    return requirements_run_id, authority_run_id


def _artifact(
    artifacts: list[dict[str, object]],
    *,
    name: str,
    source_run: _SourceRun,
    archive: Path,
) -> dict[str, object]:
    matching = [artifact for artifact in artifacts if artifact.get("name") == name]
    if len(matching) != 1:
        _reject()
    artifact = matching[0]
    _integer(artifact.get("id"))
    digest = _string(artifact.get("digest"), DIGEST_PATTERN)
    workflow_run = _object(artifact.get("workflow_run"))
    expected_run = {
        "id": source_run.run_id,
        "head_sha": source_run.sha,
        "head_branch": source_run.branch,
        "head_repository_id": REPOSITORY_ID,
        "repository_id": REPOSITORY_ID,
    }
    invalid_run = any(workflow_run.get(field) != value for field, value in expected_run.items())
    if artifact.get("expired") is not False or invalid_run or _digest(_regular_payload(archive)) != digest:
        _reject()
    return artifact


def _validate_artifacts(
    payload: object,
    *,
    source_run: _SourceRun,
    files: _ArtifactFiles,
) -> tuple[dict[str, object], dict[str, object]]:
    artifacts = _complete_collection(payload, "artifacts")
    artifact_ids = [_integer(artifact.get("id")) for artifact in artifacts]
    if len(artifact_ids) != len(set(artifact_ids)):
        _reject()
    producer = _artifact(
        artifacts,
        name="requirements-evidence",
        source_run=source_run,
        archive=files.producer,
    )
    execution = _artifact(
        artifacts,
        name="requirements-evidence-execution",
        source_run=source_run,
        archive=files.execution,
    )
    return producer, execution


def _archive_files(path: Path) -> dict[str, bytes]:
    _regular_payload(path)
    try:
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            _validate_archive_index(infos)
            return {info.filename: _archive_member(archive, info) for info in infos}
    except (OSError, RuntimeError, zipfile.BadZipFile) as error:
        raise PromotionReuseError("promotion-reuse-invalid") from error


def _validate_archive_index(infos: list[zipfile.ZipInfo]) -> None:
    if len(infos) != len({info.filename for info in infos}):
        _reject()
    if sum(info.file_size for info in infos) > MAX_ARCHIVE_CONTENT_BYTES:
        _reject()


def _archive_member(archive: zipfile.ZipFile, info: zipfile.ZipInfo) -> bytes:
    mode = info.external_attr >> 16
    file_type = stat.S_IFMT(mode)
    if info.flag_bits & 0x1 or info.is_dir() or file_type not in {0, stat.S_IFREG}:
        _reject()
    if info.file_size > MAX_ARCHIVE_MEMBER_BYTES:
        _reject()
    payload = archive.read(info)
    if len(payload) != info.file_size:
        _reject()
    return payload


class _JunitCollector:
    def __init__(self) -> None:
        self.cases: list[tuple[str, str, bool]] = []
        self.properties: dict[str, list[str]] | None = None
        self.failed = False

    def _start(self, name: str, attributes: dict[str, str]) -> None:
        if name == "testcase":
            if self.properties is not None:
                _reject()
            self.properties = {}
            self.failed = False
            return
        if self.properties is None:
            return
        if name in {"failure", "error", "skipped"}:
            self.failed = True
        elif name == "property":
            key, value = attributes.get("name"), attributes.get("value")
            if key is not None and value is not None:
                self.properties.setdefault(key, []).append(value)

    def _end(self, name: str) -> None:
        if name != "testcase" or self.properties is None:
            return
        selectors = self.properties.get("specfact.selector", [])
        runners = self.properties.get("specfact.runner", [])
        if len(selectors) != 1 or len(runners) != 1 or not selectors[0] or not runners[0]:
            _reject()
        self.cases.append((selectors[0], runners[0], self.failed))
        self.properties = None

    def _reject(self, *_arguments: object) -> int:
        _reject()


def _junit_selectors(payload: bytes) -> list[str]:
    collector = _JunitCollector()
    parser = expat.ParserCreate()
    parser.StartElementHandler = collector._start
    parser.EndElementHandler = collector._end
    parser.StartDoctypeDeclHandler = collector._reject
    parser.EntityDeclHandler = collector._reject
    parser.ExternalEntityRefHandler = collector._reject
    parser.SetParamEntityParsing(expat.XML_PARAM_ENTITY_PARSING_NEVER)
    try:
        parser.Parse(payload, True)
    except expat.ExpatError as error:
        raise PromotionReuseError("promotion-reuse-invalid") from error
    if collector.properties is not None or not collector.cases:
        _reject()
    selectors = [selector for selector, runner, failed in collector.cases if runner == "pytest" and not failed]
    if len(selectors) != len(collector.cases) or len(selectors) != len(set(selectors)):
        _reject()
    return selectors


def _planned_selectors(plan: dict[str, object]) -> list[str]:
    cases = plan.get("cases")
    if not isinstance(cases, list) or not cases:
        _reject()
    selectors: list[str] = []
    for case_value in cast(list[object], cases):
        case = _object(case_value)
        selector = _object(case.get("selector"))
        node_id = _string(case.get("node_id"))
        if case.get("method") != "test" or selector.get("runner") != "pytest" or selector.get("node_id") != node_id:
            _reject()
        selectors.append(node_id)
    if len(selectors) != len(set(selectors)):
        _reject()
    return selectors


def _expected_fields(payload: dict[str, object], expected: Mapping[str, object]) -> None:
    if any(payload.get(key) != value for key, value in expected.items()):
        _reject()


def _evidence_payloads(producer_archive: Path, execution_archive: Path) -> tuple[bytes, bytes, bytes]:
    producer_files = _archive_files(producer_archive)
    execution_files = _archive_files(execution_archive)
    required_producer = {
        "requirements-evidence.json",
        "requirements-evidence-plan.json",
        "requirements-evidence.md",
        "requirements-proof.xml",
    }
    if not required_producer.issubset(producer_files) or "requirements-evidence-plan.json" not in execution_files:
        _reject()
    producer_plan = producer_files["requirements-evidence-plan.json"]
    if execution_files["requirements-evidence-plan.json"] != producer_plan:
        _reject()
    return producer_files["requirements-evidence.json"], producer_plan, producer_files["requirements-proof.xml"]


def _report_evidence(report: dict[str, object], source_sha: str, junit_digest: str) -> tuple[str, str, list[str]]:
    expected_report = {
        "schema_version": "2",
        "verdict": "passed",
        "gate_decision": "pass",
        "required_maturity": "verified",
        "observed_maturity": "verified",
        "delivery_status": "implementation-verified",
        "implementation_evidence": "passing-after-red-proven",
    }
    _expected_fields(report, expected_report)
    execution_proof = _object(report.get("execution_proof"))
    expected_execution = {
        "source_ref": source_sha,
        "run_stage": "final",
        "proof_basis": "red-junit",
        "junit_digest": junit_digest,
    }
    _expected_fields(execution_proof, expected_execution)
    mapping_digest = _string(report.get("mapping_digest"), DIGEST_PATTERN)
    plan_digest = _string(report.get("plan_digest"), DIGEST_PATTERN)
    return mapping_digest, plan_digest, _strings(execution_proof.get("selectors"))


def _validate_plan_sources(plan_report: dict[str, object]) -> None:
    sources = plan_report.get("sources")
    if not isinstance(sources, list) or not sources:
        _reject()
    source_names: list[str] = []
    for source_value in cast(list[object], sources):
        source = _object(source_value)
        source_names.append(_string(source.get("source")))
        _string(source.get("mapping_digest"), DIGEST_PATTERN)
    if len(source_names) != len(set(source_names)):
        _reject()


def _plan_evidence(plan_report: dict[str, object], mapping_digest: str, plan_digest: str) -> list[str]:
    expected_plan_report = {
        "schema_version": "2",
        "verdict": "passed",
        "gate_decision": "pass",
        "required_maturity": "test-authored",
        "observed_maturity": "test-authored",
        "mapping_digest": mapping_digest,
    }
    _expected_fields(plan_report, expected_plan_report)
    _string(plan_report.get("plan_identity_digest"), DIGEST_PATTERN)
    plan = _object(plan_report.get("plan"))
    _expected_fields(plan, {"mapping_digest": mapping_digest, "plan_digest": plan_digest})
    _validate_plan_sources(plan_report)
    return _planned_selectors(plan)


def _validate_selectors(reported: list[str], planned: list[str], junit_payload: bytes) -> None:
    junit_selectors = _junit_selectors(junit_payload)
    if set(reported) != set(planned) or set(junit_selectors) != set(planned):
        _reject()


def _validate_evidence(
    producer_archive: Path, execution_archive: Path, source_sha: str
) -> tuple[bytes, str, str, str, list[str]]:
    report_payload, producer_plan_payload, junit_payload = _evidence_payloads(producer_archive, execution_archive)
    report = _object(_json_value(report_payload))
    plan_report = _object(_json_value(producer_plan_payload))
    junit_digest = _digest(junit_payload)
    mapping_digest, plan_digest, selectors = _report_evidence(report, source_sha, junit_digest)
    planned_selectors = _plan_evidence(plan_report, mapping_digest, plan_digest)
    _validate_selectors(selectors, planned_selectors, junit_payload)
    return report_payload, mapping_digest, plan_digest, junit_digest, selectors


def _build_validation(inputs: PromotionInputs, *, git_runner: GitRunner = _run_git) -> tuple[dict[str, object], bytes]:
    """Return the canonical attestation and exact authenticated report bytes."""
    try:
        pull_request, base_sha, head_sha = _validate_event(inputs.event)
        head_tree, previous_dev_sha, source_sha = _validate_git(inputs.repo_root, base_sha, head_sha, git_runner)
        source_pull = _validate_source_pull(inputs.source_pulls, previous_dev_sha, source_sha, head_sha)
        source_head = _object(source_pull.get("head"))
        source_branch = _string(source_head.get("ref"))
        requirements_run_id, authority_run_id = _validate_checks_and_runs(
            inputs.check_runs,
            inputs.requirements_run,
            inputs.authority_run,
            source_branch,
            source_sha,
        )
        producer, execution = _validate_artifacts(
            inputs.artifacts,
            source_run=_SourceRun(requirements_run_id, source_branch, source_sha),
            files=_ArtifactFiles(inputs.producer_archive, inputs.execution_archive),
        )
        verified_evidence, mapping_digest, plan_digest, junit_digest, selectors = _validate_evidence(
            inputs.producer_archive, inputs.execution_archive, source_sha
        )
        attestation: dict[str, object] = {
            "schema_version": "1",
            "claim": "promotion-reused",
            "repository": {"id": REPOSITORY_ID, "full_name": REPOSITORY},
            "promotion": {
                "base_ref": BASE_REF,
                "base_sha": base_sha,
                "head_ref": HEAD_REF,
                "head_sha": head_sha,
                "head_tree": head_tree,
                "pull_request": pull_request,
            },
            "source_pull_request": {
                "number": _integer(source_pull.get("number")),
                "base_sha": previous_dev_sha,
                "head_ref": source_branch,
                "head_sha": source_sha,
                "merge_commit_sha": head_sha,
            },
            "checks": {
                "requirements_run_id": requirements_run_id,
                "authority_run_id": authority_run_id,
            },
            "artifacts": {
                "producer_id": _integer(producer.get("id")),
                "producer_digest": _string(producer.get("digest"), DIGEST_PATTERN),
                "execution_id": _integer(execution.get("id")),
                "execution_digest": _string(execution.get("digest"), DIGEST_PATTERN),
            },
            "evidence": {
                "mapping_digest": mapping_digest,
                "plan_digest": plan_digest,
                "junit_digest": junit_digest,
                "selectors": selectors,
            },
        }
        return attestation, verified_evidence
    except Exception as error:
        if isinstance(error, PromotionReuseError):
            raise
        raise PromotionReuseError("promotion-reuse-invalid") from error


def build_attestation(inputs: PromotionInputs, *, git_runner: GitRunner = _run_git) -> dict[str, object]:
    """Return one canonical attestation or fail closed on any incomplete binding."""
    return _build_validation(inputs, git_runner=git_runner)[0]


def _argument_error(message: str) -> NoReturn:
    del message
    raise PromotionReuseError("promotion-reuse-invalid")


def _arguments(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.error = _argument_error
    for name in (
        "event",
        "repo-root",
        "source-pulls",
        "check-runs",
        "requirements-run",
        "authority-run",
        "artifacts",
        "producer-archive",
        "execution-archive",
        "output",
    ):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--expected-attestation", type=Path)
    parser.add_argument("--verified-evidence-output", type=Path)
    return parser.parse_args(argv)


def _canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode() + b"\n"


def _write_output(path: Path, payload: bytes) -> None:
    parent = path.parent.resolve(strict=True)
    with tempfile.NamedTemporaryFile(prefix=f".{path.name}.", dir=parent, delete=False) as candidate:
        candidate_path = Path(candidate.name)
        candidate.write(payload)
        candidate.flush()
        os.fsync(candidate.fileno())
    try:
        os.replace(candidate_path, path)
    except Exception:
        candidate_path.unlink(missing_ok=True)
        raise


def main(argv: Sequence[str] | None = None) -> int:
    """Validate promotion reuse, write canonical JSON, and return a shell status."""
    try:
        arguments = _arguments(argv)
        inputs = PromotionInputs(
            event=_object(_read_json(arguments.event)),
            repo_root=arguments.repo_root.resolve(strict=True),
            source_pulls=_read_json(arguments.source_pulls),
            check_runs=_read_json(arguments.check_runs),
            requirements_run=_object(_read_json(arguments.requirements_run)),
            authority_run=_object(_read_json(arguments.authority_run)),
            artifacts=_read_json(arguments.artifacts),
            producer_archive=arguments.producer_archive,
            execution_archive=arguments.execution_archive,
        )
        attestation, verified_evidence = _build_validation(inputs)
        payload = _canonical_json(attestation)
        if arguments.expected_attestation is not None and _regular_payload(arguments.expected_attestation) != payload:
            _reject()
        if arguments.verified_evidence_output is not None:
            if arguments.verified_evidence_output.resolve() == arguments.output.resolve():
                _reject()
            _write_output(arguments.verified_evidence_output, verified_evidence)
        _write_output(arguments.output, payload)
    except Exception:
        sys.stderr.write("promotion-reuse-invalid\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

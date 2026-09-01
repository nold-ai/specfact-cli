"""Authenticate one GitHub partial-red run and retain only its exact failed selectors."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import cast

import requirements_amendment_bootstrap as bootstrap
import requirements_cycle_base as cycle


DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
GIT_OBJECT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
REPOSITORY = "nold-ai/specfact-cli"
WORKFLOW_NAME = "Requirements Evidence"
WORKFLOW_PATH = ".github/workflows/requirements-evidence.yml"


def _read_object(path: Path) -> dict[str, object]:
    """Read one regular JSON object from outside the repository tree."""
    if path.is_symlink() or not path.is_file():
        raise ValueError("red-run-normalization-invalid")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("red-run-normalization-invalid")
    return cast(dict[str, object], value)


def _digest(path: Path) -> str:
    """Return the canonical SHA-256 digest for one immutable input."""
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _repository_matches(run: dict[str, object]) -> bool:
    """Return whether GitHub reports the exact trusted repository."""
    repository = run.get("repository")
    if not isinstance(repository, dict):
        return False
    return cast(dict[str, object], repository).get("full_name") == REPOSITORY


def _run_matches(run: dict[str, object], arguments: argparse.Namespace) -> bool:
    """Bind the raw evidence to one completed workflow-dispatch red run."""
    return all(
        (
            run.get("id") == arguments.run_id,
            run.get("head_sha") == arguments.source_ref,
            run.get("head_branch") == arguments.head_branch,
            run.get("event") == "workflow_dispatch",
            run.get("status") == "completed",
            run.get("conclusion") == "failure",
            run.get("name") == WORKFLOW_NAME,
            run.get("path") == WORKFLOW_PATH,
            run.get("pull_requests") == [],
            _repository_matches(run),
        )
    )


def _artifact_matches(artifacts: dict[str, object], arguments: argparse.Namespace) -> bool:
    """Bind the unique named artifact to its immutable GitHub digest and run."""
    entries = artifacts.get("artifacts")
    if not isinstance(entries, list):
        return False
    matches: list[dict[str, object]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        candidate = cast(dict[str, object], entry)
        if candidate.get("id") == arguments.artifact_id:
            matches.append(candidate)
    if len(matches) != 1:
        return False
    artifact = matches[0]
    workflow_run = artifact.get("workflow_run")
    workflow_run_id = cast(dict[str, object], workflow_run).get("id") if isinstance(workflow_run, dict) else None
    return all(
        (
            artifact.get("name") == "requirements-evidence",
            artifact.get("expired") is False,
            artifact.get("digest") == arguments.artifact_digest,
            workflow_run_id == arguments.run_id,
        )
    )


def _artifact_files(root: Path) -> tuple[Path, Path, Path]:
    """Return the exact regular report, plan, and JUnit inputs."""
    files = (
        root / "requirements-evidence.json",
        root / "requirements-evidence-plan.json",
        root / "requirements-proof.xml",
    )
    if any(path.is_symlink() or not path.is_file() for path in files):
        raise ValueError("red-run-normalization-invalid")
    return files


def _raw_report_matches(
    report: dict[str, object],
    plan: dict[str, object],
    junit: Path,
    source_ref: str,
) -> bool:
    """Require the raw report to bind the exact test-authored plan and JUnit."""
    execution = report.get("execution_proof")
    execution_values = cast(dict[str, object], execution) if isinstance(execution, dict) else {}
    _, mapping_digest, plan_digest = bootstrap._plan_selectors(plan)
    return all(
        (
            report.get("gate_decision") == "fail",
            report.get("observed_maturity") == "incomplete",
            report.get("mapping_digest") == mapping_digest,
            report.get("plan_digest") == plan_digest,
            bool(execution_values),
            execution_values.get("run_stage") == "red",
            execution_values.get("source_ref") == source_ref,
            execution_values.get("junit_digest") == _digest(junit),
        )
    )


def _output_is_external(output: Path, repo_root: Path, inputs: tuple[Path, ...]) -> bool:
    """Reject repository-controlled, linked, or input-overlapping output paths."""
    xml_output = output.with_suffix(".xml")
    if output.is_symlink() or xml_output.is_symlink():
        return False
    outputs = {output.resolve(), xml_output.resolve()}
    if len(outputs) != 2 or any(candidate in outputs for candidate in (path.resolve() for path in inputs)):
        return False
    return all(not candidate.is_relative_to(repo_root.resolve()) for candidate in outputs)


def _write_atomic(path: Path, payload: bytes) -> None:
    """Atomically replace one normalized artifact in its external directory."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(payload)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _context_matches(arguments: argparse.Namespace) -> bool:
    """Bind normalization to one exact repository and linear test-only red history."""
    return all(
        (
            GIT_OBJECT_PATTERN.fullmatch(arguments.source_ref) is not None,
            DIGEST_PATTERN.fullmatch(arguments.artifact_digest) is not None,
            arguments.repository == REPOSITORY,
            cycle.red_history_is_test_only(
                arguments.repo_root,
                arguments.base_ref,
                arguments.source_ref,
                arguments.change_id,
            ),
        )
    )


def _evidence_matches(
    arguments: argparse.Namespace,
    run: dict[str, object],
    artifacts: dict[str, object],
    inputs: tuple[Path, ...],
) -> bool:
    """Authenticate exact GitHub metadata and external input/output paths."""
    return all(
        (
            _run_matches(run, arguments),
            _artifact_matches(artifacts, arguments),
            _output_is_external(arguments.output, arguments.repo_root, inputs),
        )
    )


def _normalize(arguments: argparse.Namespace) -> None:
    """Authenticate raw red evidence and emit its fail-only canonical proof."""
    if not _context_matches(arguments):
        raise ValueError("red-run-normalization-invalid")
    run = _read_object(arguments.run)
    artifacts = _read_object(arguments.artifacts)
    raw_report_path, plan_path, raw_junit_path = _artifact_files(arguments.artifact_root)
    inputs = (arguments.run, arguments.artifacts, raw_report_path, plan_path, raw_junit_path)
    if not _evidence_matches(arguments, run, artifacts, inputs):
        raise ValueError("red-run-normalization-invalid")
    raw_report = _read_object(raw_report_path)
    plan = _read_object(plan_path)
    if not _raw_report_matches(raw_report, plan, raw_junit_path, arguments.source_ref):
        raise ValueError("red-run-normalization-invalid")
    outcomes, selectors = bootstrap._raw_selector_outcomes(plan, raw_junit_path)
    if set(outcomes.values()) != {"failed", "passed"}:
        raise ValueError("red-run-normalization-invalid")
    failed = sorted(selector for selector in selectors if outcomes[selector] == "failed")
    junit = bootstrap._normalized_junit(raw_junit_path, failed)
    authority = {
        "red_commit": arguments.source_ref,
        "report_digest": _digest(raw_report_path),
        "junit_digest": _digest(raw_junit_path),
    }
    report = bootstrap._red_report(plan, authority, failed, junit)
    execution = report.get("execution_proof")
    if not isinstance(execution, dict):
        raise ValueError("red-run-normalization-invalid")
    cast(dict[str, object], execution).update(
        approved_raw_plan_digest=_digest(plan_path),
        approved_raw_run_id=arguments.run_id,
        approved_raw_artifact_id=arguments.artifact_id,
        approved_raw_artifact_digest=arguments.artifact_digest,
    )
    _write_atomic(arguments.output, (json.dumps(report, indent=2, sort_keys=True) + "\n").encode())
    _write_atomic(arguments.output.with_suffix(".xml"), junit)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--run-id", type=int, required=True)
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--artifact-id", type=int, required=True)
    parser.add_argument("--artifact-digest", required=True)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--base-ref", required=True)
    parser.add_argument("--source-ref", required=True)
    parser.add_argument("--head-branch", required=True)
    parser.add_argument("--change-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


if __name__ == "__main__":
    try:
        _normalize(_parser().parse_args())
    except (OSError, subprocess.SubprocessError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        sys.stderr.write("red-run-normalization-invalid\n")
        raise SystemExit(1) from None

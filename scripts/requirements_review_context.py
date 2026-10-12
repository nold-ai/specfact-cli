"""Read authentic finalized root proof without relabeling child planning evidence."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import stat
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import cast
from zipfile import ZipFile


REPOSITORY = "nold-ai/specfact-cli"
REPOSITORY_ID = 1085706003
MAX_ARCHIVE_BYTES = 16 * 1024 * 1024
MAX_REPORT_BYTES = 4 * 1024 * 1024
MAX_ARTIFACT_PAGES = 50
ApiReader = Callable[[str], object]
ArchiveReader = Callable[[str], bytes]


def _object(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ValueError("review-context-invalid")
    return cast(dict[str, object], value)


def _integer(value: object) -> int:
    if type(value) is not int or cast(int, value) <= 0:
        raise ValueError("review-context-invalid")
    return cast(int, value)


def _reauthenticate(context: dict[str, object], event: dict[str, object], get_json: ApiReader) -> dict[str, object]:
    """Repeat live native resolution and protected selection before artifact retrieval."""
    helper = Path(__file__).with_name("requirements_stack_context.py")
    spec = importlib.util.spec_from_file_location("_trusted_review_stack_context", helper)
    if spec is None or spec.loader is None:
        raise ValueError("review-context-invalid")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    resolve = cast(Callable[[dict[str, object], ApiReader], dict[str, object]], module.resolve_stack_context)
    merge_base = cast(Callable[[str, str], str], module._proof_merge_base)
    planning = cast(Callable[[dict[str, object], ApiReader], dict[str, object]], module._planning_context)
    fresh = resolve(event, get_json)
    fresh["protected_base_commit"] = fresh["proof_base_commit"]
    fresh["proof_base_commit"] = merge_base(
        cast(str, fresh["proof_base_commit"]), cast(str, fresh["proof_head_commit"])
    )
    fresh = planning(fresh, get_json)
    if fresh != context or fresh.get("planning_base_commit") != fresh.get("proof_head_commit"):
        raise ValueError("review-context-invalid")
    return fresh


def _root_run(context: dict[str, object]) -> int:
    proof = _object(context.get("inherited_proof"))
    records = proof.get("checks")
    if not isinstance(records, list) or proof.get("head_commit") != context.get("proof_head_commit"):
        raise ValueError("review-context-invalid")
    matching = [_object(record) for record in records if _object(record).get("check_name") == "Requirements evidence"]
    if len(matching) != 1:
        raise ValueError("review-context-invalid")
    return _integer(matching[0].get("run_id"))


def _artifact_page(payload: object) -> tuple[int, list[dict[str, object]]]:
    record = _object(payload)
    total = _integer(record.get("total_count"))
    entries = record.get("artifacts")
    if not isinstance(entries, list) or not entries:
        raise ValueError("review-context-invalid")
    return total, [_object(entry) for entry in entries]


def _unique_artifact(records: list[dict[str, object]], total: int) -> dict[str, object]:
    identifiers = {_integer(record.get("id")) for record in records}
    matching = [record for record in records if record.get("name") == "requirements-evidence"]
    if len(identifiers) != total or len(records) != total or len(matching) != 1:
        raise ValueError("review-context-invalid")
    return matching[0]


def _artifact(run_id: int, get_json: ApiReader) -> dict[str, object]:
    """Require a complete stable inventory with one exact named artifact."""
    records: list[dict[str, object]] = []
    total: int | None = None
    for page in range(1, MAX_ARTIFACT_PAGES + 1):
        count, entries = _artifact_page(
            get_json(f"/repos/{REPOSITORY}/actions/runs/{run_id}/artifacts?per_page=100&page={page}")
        )
        if total is not None and count != total:
            raise ValueError("review-context-invalid")
        total = count
        records.extend(entries)
        if len(records) >= total:
            return _unique_artifact(records, total)
    raise ValueError("review-context-invalid")


def _verify_archive(artifact: dict[str, object], context: dict[str, object], run_id: int, archive: bytes) -> None:
    expected = {
        "id": run_id,
        "repository_id": REPOSITORY_ID,
        "head_repository_id": REPOSITORY_ID,
        "head_sha": context["proof_head_commit"],
        "head_branch": context["proof_head_branch"],
    }
    metadata = _object(artifact.get("workflow_run"))
    if any(metadata.get(key) != value for key, value in expected.items()) or artifact.get("expired") is not False:
        raise ValueError("review-context-invalid")
    if _integer(artifact.get("size_in_bytes")) != len(archive) or len(archive) > MAX_ARCHIVE_BYTES:
        raise ValueError("review-context-invalid")
    if artifact.get("digest") != "sha256:" + hashlib.sha256(archive).hexdigest():
        raise ValueError("review-context-invalid")


def _json_member(archive: bytes) -> bytes:
    with ZipFile(io.BytesIO(archive)) as zipped:
        entries = zipped.infolist()
        reports = [entry for entry in entries if entry.filename == "requirements-evidence.json"]
        if len(entries) > 8 or len(reports) != 1:
            raise ValueError("review-context-invalid")
        member = reports[0]
        if member.is_dir() or stat.S_IFMT(member.external_attr >> 16) not in {0, stat.S_IFREG}:
            raise ValueError("review-context-invalid")
        if member.file_size <= 0 or member.file_size > MAX_REPORT_BYTES:
            raise ValueError("review-context-invalid")
        return zipped.read(member)


def _report(artifact: dict[str, object], context: dict[str, object], run_id: int, archive: bytes) -> bytes:
    """Read bounded regular JSON bytes after service provenance and ZIP integrity."""
    _verify_archive(artifact, context, run_id, archive)
    data = _json_member(archive)
    report = _object(json.loads(data))
    proof = _object(report.get("execution_proof"))
    expected_report = {
        "schema_version": "2",
        "required_maturity": "verified",
        "observed_maturity": "verified",
        "gate_decision": "pass",
        "findings": [],
    }
    if any(report.get(key) != value for key, value in expected_report.items()):
        raise ValueError("review-context-invalid")
    if proof.get("run_stage") != "final" or proof.get("source_ref") != context["proof_head_commit"]:
        raise ValueError("review-context-invalid")
    # The immutable review provider independently validates plans, selectors and complete proof structure.
    return data


def _api(path: str) -> object:
    result = subprocess.run(
        ["gh", "api", "--hostname", "github.com", path], capture_output=True, check=True, timeout=30
    )
    return json.loads(result.stdout)


def _archive(path: str) -> bytes:
    result = subprocess.run(
        ["gh", "api", "--hostname", "github.com", path], capture_output=True, check=True, timeout=30
    )
    if len(result.stdout) > MAX_ARCHIVE_BYTES:
        raise ValueError("review-context-invalid")
    return result.stdout


def _main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--context", type=Path, required=True)
    parser.add_argument("--event", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    context = _reauthenticate(
        _object(json.loads(arguments.context.read_bytes())), _object(json.loads(arguments.event.read_bytes())), _api
    )
    run_id = _root_run(context)
    artifact = _artifact(run_id, _api)
    if _integer(artifact.get("size_in_bytes")) > MAX_ARCHIVE_BYTES:
        raise ValueError("review-context-invalid")
    archive = _archive(f"/repos/{REPOSITORY}/actions/artifacts/{_integer(artifact.get('id'))}/zip")
    data = _report(artifact, context, run_id, archive)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_bytes(data)


if __name__ == "__main__":
    _main()

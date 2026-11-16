"""Retained bytes require live original-provider upload provenance."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[3]
ARCHIVE = ROOT / "tests/fixtures/requirements-proof/pr786-original-native36.zip"
Evidence = tuple[ModuleType, dict[str, Any], bytes, bytes, dict[str, Any], Path]


@pytest.fixture
def evidence(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Evidence:
    spec = importlib.util.spec_from_file_location(
        "_retained_origin_owner", ROOT / "scripts/requirements_late_red_proof.py"
    )
    assert spec is not None and spec.loader is not None
    owner = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = owner
    spec.loader.exec_module(owner)
    manifest = json.loads(
        (
            ROOT / "openspec/changes/security-dependencies-0-55-11-dev/requirements-proof/late-red-evidence.json"
        ).read_text()
    )
    job = {
        "id": 126195535776,
        "run_id": 41715861806,
        "run_attempt": 1,
        "head_sha": "8ad0a9434ceeac4a910df3c374536d7c909badec",
        "name": "materialize",
        "status": "completed",
        "conclusion": "success",
        "started_at": "2026-11-03T20:47:57Z",
        "completed_at": "2026-11-03T20:50:17Z",
        "steps": [
            {"number": 7, "name": "Observe one original native materialization", "conclusion": "success"},
            {"number": 9, "name": "Retain original execution packet", "conclusion": "success"},
        ],
    }
    log = (
        "##[group]Run actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a\n"
        "  name: original-execution-packet-41715861806-1\n"
        "SHA256 digest of uploaded artifact is 0567a53963df112f2ac3f2e2024c1b93c6f9fafc00052ce137c4d5495c07f433\n"
        "Artifact original-execution-packet-41715861806-1 successfully finalized. Artifact ID 13269307808\n"
        "Artifact original-execution-packet-41715861806-1 has been successfully uploaded! "
        "Final size is 1885415 bytes. Artifact ID is 13269307808\n"
        "Artifact download URL: https://github.com/nold-ai/.github/actions/runs/41715861806/artifacts/13269307808\n"
    ).encode()
    monkeypatch.setattr(owner, "_FIXED_PR786_UPLOAD_LOG_SHA256", hashlib.sha256(log).hexdigest(), raising=False)
    monkeypatch.setattr(owner, "_FIXED_PR786_UPLOAD_LOG_BYTES", len(log), raising=False)
    source = ROOT / "tests/unit/scripts/fixtures/fixed786-native-packet"
    for original, normalized in (
        ("local-red-report.json", "requirements-evidence.json"),
        ("planning-report.json", "requirements-evidence-plan.json"),
        ("requirements-proof.xml", "requirements-proof.xml"),
        ("plan.json", "plan.json"),
    ):
        (tmp_path / normalized).write_bytes((source / original).read_bytes())
    return owner, job, log, ARCHIVE.read_bytes(), manifest, tmp_path


def test_live_original_upload_authenticates_retained_archive_members(evidence: Evidence) -> None:
    owner, job, log, archive, manifest, packet = evidence
    receipt = owner._fixed_pr786_upload_receipt(job, log, archive, manifest, packet)
    assert receipt["source"] == "live-provider-upload-log"
    assert receipt["artifact_metadata_role"] == "historical"
    assert receipt["artifacts_present"] == 0
    assert receipt["upload"]["id"] == 13269307808
    assert receipt["archive"]["digest"] == manifest["artifact_digest"]
    assert len(receipt["members"]) == 4


@pytest.mark.parametrize(
    "mutation",
    [
        "job",
        "run",
        "attempt",
        "head",
        "status",
        "native-skipped",
        "upload-failed",
        "expired-execution",
        "log",
        "receipt",
        "archive",
        "member",
    ],
)
def test_retained_bytes_refuse_changed_or_missing_live_origin(evidence: Evidence, mutation: str) -> None:
    owner, recorded, log, archive, manifest, packet = evidence
    job = copy.deepcopy(recorded)
    if mutation in {"job", "run", "attempt", "head", "status"}:
        key = {"job": "id", "run": "run_id", "attempt": "run_attempt", "head": "head_sha", "status": "status"}[mutation]
        job[key] = "wrong"
    elif mutation == "native-skipped":
        job["steps"][0]["conclusion"] = "skipped"
    elif mutation == "upload-failed":
        job["steps"][1]["conclusion"] = "failure"
    elif mutation == "expired-execution":
        job["completed_at"] = "2026-11-05T00:00:00Z"
    elif mutation == "log":
        log += b"changed"
    elif mutation == "receipt":
        log = log.replace(b"Artifact ID 13269307808", b"Artifact ID 1")
        owner._FIXED_PR786_UPLOAD_LOG_SHA256 = hashlib.sha256(log).hexdigest()
        owner._FIXED_PR786_UPLOAD_LOG_BYTES = len(log)
    elif mutation == "archive":
        archive = archive[:-1]
    elif mutation == "member":
        (packet / "requirements-evidence.json").write_bytes(b"substituted")
    with pytest.raises(ValueError):
        owner._fixed_pr786_upload_receipt(job, log, archive, manifest, packet)

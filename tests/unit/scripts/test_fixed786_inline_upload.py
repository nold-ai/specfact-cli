"""Exercise the protected workflow's checked-in upload-verification block."""

from __future__ import annotations

import ast
import hashlib
import io
import runpy
import stat
import zipfile
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import pytest
import yaml

from tests.unit.scripts.test_fixed786_retained_origin import ROOT, Evidence, evidence as evidence


def _upload_fragment() -> str:
    workflow = yaml.safe_load((ROOT / ".github/workflows/requirements-evidence.yml").read_text())
    steps = workflow["jobs"]["requirements-fixed786-origin"]["steps"]
    shell = next(step["run"] for step in steps if "original_upload_receipt =" in step.get("run", ""))
    source = shell.split("<<'PYTHON'\n", 1)[1].rsplit("\nPYTHON", 1)[0]
    nodes = ast.parse(source).body
    assignments = {
        target.id: index
        for index, node in enumerate(nodes)
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    }
    functions = {node.name: index for index, node in enumerate(nodes) if isinstance(node, ast.FunctionDef)}
    fragment = [
        nodes[assignments["_FIXED_PR786_ORIGINAL_ZIP"]],
        *nodes[functions["_fixed_pr786_upload_steps"] : functions["_fixed_pr786_original_log"]],
    ]
    fragment.append(nodes[assignments["original_upload_receipt"]])
    return ast.unparse(ast.Module(body=fragment, type_ignores=[]))


def _run_inline_upload(evidence: Evidence) -> dict[str, Any]:
    _, job, log, archive, manifest, packet = evidence
    fragment = packet / "inline_upload.py"
    fragment.write_text(_upload_fragment() + "\n", encoding="utf-8")
    globals_for_fragment = {
        # Use the synthetic provider log's digest while preserving the production receipt checks.
        "_FIXED_PR786_UPLOAD_LOG_BYTES": len(log),
        "_FIXED_PR786_UPLOAD_LOG_SHA256": hashlib.sha256(log).hexdigest(),
        "_fixed_pr786_original_log": lambda: log,
        "UTC": UTC,
        "cast": cast,
        "datetime": datetime,
        "hashlib": hashlib,
        "io": io,
        "manifest": manifest,
        "original_archive": archive,
        "original_job": job,
        "packet": packet,
        "Path": Path,
        "stat": stat,
        "zipfile": zipfile,
    }
    return cast(
        dict[str, Any], runpy.run_path(str(fragment), init_globals=globals_for_fragment)["original_upload_receipt"]
    )


def test_inline_upload_authenticates_retained_members(evidence: Evidence) -> None:
    receipt = _run_inline_upload(evidence)
    assert receipt["upload"]["id"] == 13269307808
    assert receipt["archive"]["digest"] == evidence[4]["artifact_digest"]
    assert len(receipt["members"]) == 4


def _replace_job_attempt(evidence: Evidence) -> Evidence:
    owner, job, log, archive, manifest, packet = evidence
    return owner, {**job, "run_attempt": 2}, log, archive, manifest, packet


def _replace_receipt_id(evidence: Evidence) -> Evidence:
    owner, job, log, archive, manifest, packet = evidence
    return owner, job, log.replace(b"Artifact ID 13269307808", b"Artifact ID 1"), archive, manifest, packet


def _truncate_archive(evidence: Evidence) -> Evidence:
    owner, job, log, archive, manifest, packet = evidence
    return owner, job, log, archive[:-1], manifest, packet


def _replace_retained_member(evidence: Evidence) -> Evidence:
    (evidence[5] / "requirements-evidence.json").write_bytes(b"substituted")
    return evidence


@pytest.mark.parametrize(
    ("alter", "error"),
    [
        (_replace_job_attempt, "fixed786 original upload job"),
        (_replace_receipt_id, "fixed786 original provider receipt"),
        (_truncate_archive, "fixed786 retained original archive"),
        (_replace_retained_member, "fixed786 original member mismatch"),
    ],
)
def test_inline_upload_rejects_changed_evidence(
    evidence: Evidence, alter: Callable[[Evidence], Evidence], error: str
) -> None:
    with pytest.raises(ValueError, match=error):
        _run_inline_upload(alter(evidence))

"""Normalize an exact authority-bound late review RED artifact."""

from __future__ import annotations

import argparse
import ast
import base64
import hashlib
import http.client
import importlib.util
import io
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import urllib.parse
import zipfile
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from types import ModuleType
from typing import Any, NamedTuple, NoReturn, cast
from xml.parsers import expat


REPOSITORY = "nold-ai/specfact-cli"
ISSUE = 692
BASE_BRANCH = "dev"
WORKFLOW_PATH = ".github/workflows/requirements-evidence.yml"
PROVENANCE_PATH = "scripts/requirements_proof_provenance.py"
PROOF_CYCLE_PROVENANCE_BLOB = "28491925ea5242d58e7cdaeff8ada8291382a15a"
MAX_INPUT_BYTES = 10 * 1024 * 1024
OBJECT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
MANIFEST_FIELDS = {
    "schema_version",
    "kind",
    "repository",
    "issue",
    "pull_request",
    "base_branch",
    "head_branch",
    "change_id",
    "cycle_base_commit",
    "cycle_base_tree",
    "red_commit",
    "red_tree",
    "run_id",
    "artifact_id",
    "artifact_digest",
    "report_digest",
    "plan_report_digest",
    "junit_digest",
    "mapping_digest",
    "plan_digest",
    "failed_selectors",
}


class _ProofScope(NamedTuple):
    change_id: str
    pull_request: int
    head_branch: str
    required_maturity: str
    run_stage: str


_FIXED_PR786_SCOPE = _ProofScope(
    "security-dependencies-0-55-11-dev", 786, "codex/security-dependencies-0-55-11-dev", "red", "red"
)
_FIXED_PR786_MANIFEST: tuple[tuple[str, str | int], ...] = (
    ("schema_version", "1"),
    ("kind", "fixed-pr786-native-red-proof"),
    ("repository", "nold-ai/specfact-cli"),
    ("issue", 780),
    ("pull_request", 786),
    ("base_branch", "dev"),
    ("head_branch", "codex/security-dependencies-0-55-11-dev"),
    ("change_id", "security-dependencies-0-55-11-dev"),
    ("cycle_base_commit", "9b5ad1e78430cc0b061cb16de42f73de96f4f312"),
    ("cycle_base_tree", "24112d8c9983333f9059283965230348f718b74c"),
    ("red_commit", "d77209f4b13c386e29391f93e1f1c58d7fd8622f"),
    ("red_tree", "cfba03cf57f6de2fc6dd37709c9d8e38d03f2187"),
    ("run_id", 41715861806),
    ("run_attempt", 1),
    ("artifact_id", 13269307808),
    ("artifact_digest", "sha256:0567a53963df112f2ac3f2e2024c1b93c6f9fafc00052ce137c4d5495c07f433"),
    ("report_digest", "sha256:b53ca5669e50819646bb4f088ed2bac44308043395e7ecfe315cfef1f82f15ef"),
    ("plan_report_digest", "sha256:c3de795387a8b289ebf1d8a0b976c25102f5563b7b94a60423cfaccd0c291607"),
    ("junit_digest", "sha256:92992ccec3f3e546ce0d79ab8403806be31cd2a267ed61147eee90a27338e401"),
    ("mapping_digest", "sha256:caeca573ba8a7c69fad2c530d67e502f6a3a51c82c8d8e6f1659c4bcfe7b34d0"),
    ("plan_digest", "sha256:befd8204588ac5de083e48e62c480b23cbdecbf3b4a2006fdf0e2901a213ae0f"),
    ("executor_repository", "nold-ai/.github"),
    ("executor_commit", "8ad0a9434ceeac4a910df3c374536d7c909badec"),
    ("executor_tree", "975de5bf33e7621f1606eb344383d690dbdcae8a"),
    ("executor_head_branch", "codex/dev786-original-native-36"),
    ("executor_workflow_path", ".github/workflows/native-materialization-preflight.yml"),
    ("executor_workflow_name", "Native materialization development preflight 36"),
    ("executor_event", "create"),
    ("executor_conclusion", "success"),
    ("artifact_repository", "nold-ai/.github"),
    ("artifact_name", "original-execution-packet-41715861806-1"),
    ("artifact_member_prefix", "original15-a2103119d418a02310d994a6-export"),
    ("origin_repository", "nold-ai/specfact-cli"),
    ("origin_workflow_path", ".github/workflows/requirements-evidence.yml"),
    ("source_mapping_digest", "sha256:61afa8becd7fed3cbe92a273c955c2e8ba389583f62f0e519c97cafafa7d4307"),
    ("source_plan_digest", "sha256:37841eeb1f226f62250712050c42c52f032689fa19d091b4c83dc74d9eb8487c"),
    ("plan_output_digest", "sha256:83e229add4081858e5ec708ab4ff35c7d9d5db03e65de2eb8a0a8a064fa8d31b"),
)
_FIXED_PR786_SELECTORS = (
    "tests/unit/scripts/test_dependency_compatibility_workflow.py::test_resolver_selection_excludes_only_frozen_release_cases",
    "tests/unit/scripts/test_dependency_trust_review.py::test_pycparser_has_current_exact_version_review_record",
    "tests/unit/scripts/test_security_audit_gate.py::test_committed_otel_exception_is_exact_and_time_bounded[exact-cve]",
    "tests/unit/scripts/test_security_audit_gate.py::test_committed_otel_exception_is_exact_and_time_bounded[exact-ghsa]",
    "tests/unit/scripts/test_security_audit_gate.py::test_committed_otel_exception_is_exact_and_time_bounded[expiry-day]",
    "tests/unit/security/test_code_review_dependency_security.py::test_code_review_pins_fixed_pylint_with_bound_artifact_hashes",
    "tests/unit/security/test_frozen_gitpython_compatibility.py::test_submodule_creation_validates_checkout_before_clone[absolute-metadata]",
    "tests/unit/security/test_frozen_gitpython_compatibility.py::test_submodule_creation_validates_checkout_before_clone[git-metadata]",
    "tests/unit/security/test_frozen_gitpython_compatibility.py::test_submodule_creation_validates_checkout_before_clone[git-short-name]",
    "tests/unit/security/test_release_dependency_selection.py::test_public_declarations_require_reviewed_security_floor[gitpython-floor]",
    "tests/unit/security/test_release_dependency_selection.py::test_public_declarations_require_reviewed_security_floor[pycparser-floor]",
    "tests/unit/security/test_release_dependency_selection.py::test_reviewed_tooling_versions_match_frozen_export[filelock-4.2.1]",
    "tests/unit/security/test_release_dependency_selection.py::test_reviewed_tooling_versions_match_frozen_export[gitpython-3.2.1]",
    "tests/unit/security/test_release_dependency_selection.py::test_reviewed_tooling_versions_match_frozen_export[msgpack-1.2.3]",
    "tests/unit/security/test_release_dependency_selection.py::test_reviewed_tooling_versions_match_frozen_export[packaging-26.3]",
    "tests/unit/security/test_release_dependency_selection.py::test_reviewed_tooling_versions_match_frozen_export[pycparser-3.12]",
    "tests/unit/security/test_release_dependency_selection.py::test_reviewed_tooling_versions_match_frozen_export[python-discovery-1.6.1]",
    "tests/unit/security/test_release_dependency_selection.py::test_reviewed_tooling_versions_match_frozen_export[semgrep-1.182.1]",
    "tests/unit/security/test_release_dependency_selection.py::test_reviewed_tooling_versions_match_frozen_export[setuptools-84.1.0]",
    "tests/unit/security/test_release_dependency_selection.py::test_reviewed_tooling_versions_match_frozen_export[virtualenv-21.14.13]",
    "tests/unit/security/test_release_promotion_security_gates.py::test_frozen_graph_uses_official_semgrep_with_bounded_mcp_exception",
)


_PROOF_SCOPES = (
    _ProofScope("fix-release-promotion-security-gates", 704, "bugfix/692-release-review-followup", "verified", "final"),
    _ProofScope(
        "fix-release-promotion-requirements-parity",
        717,
        "bugfix/692-promotion-final-context",
        "verified",
        "final",
    ),
    _ProofScope(
        "fix-release-promotion-requirements-parity",
        716,
        "bugfix/692-promotion-core-manifest",
        "verified",
        "final",
    ),
    _FIXED_PR786_SCOPE,
)


def _proof_scope(manifest_path: Path, repo_root: Path) -> _ProofScope:
    for scope in _PROOF_SCOPES:
        expected = repo_root / f"openspec/changes/{scope.change_id}/requirements-proof/late-red-evidence.json"
        if manifest_path == expected:
            return scope
    raise ValueError


def _argument_error(message: str) -> NoReturn:
    raise ValueError(message)


def _object(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError
    return cast(dict[str, object], value)


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError
        result[key] = value
    return result


def _regular_payload(path: Path) -> bytes:
    details = path.lstat()
    if not stat.S_ISREG(details.st_mode) or details.st_size > MAX_INPUT_BYTES:
        raise ValueError
    payload = path.read_bytes()
    if len(payload) != details.st_size:
        raise ValueError
    return payload


def _read_json(path: Path) -> dict[str, object]:
    try:
        parsed = json.loads(_regular_payload(path), object_pairs_hook=_pairs)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError from error
    return _object(parsed)


def _digest(payload: bytes) -> str:
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def _integer(value: object) -> int:
    if type(value) is not int or cast(int, value) <= 0:
        raise ValueError
    return cast(int, value)


def _string(value: object, pattern: re.Pattern[str] | None = None) -> str:
    if not isinstance(value, str) or not value or (pattern is not None and pattern.fullmatch(value) is None):
        raise ValueError
    return value


def _strings(value: object) -> list[str]:
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
        raise ValueError
    result = cast(list[str], value)
    if len(set(result)) != len(result):
        raise ValueError
    return result


def _validate_fixed_pr786_manifest(manifest: dict[str, object]) -> None:
    expected = dict(_FIXED_PR786_MANIFEST)
    if set(manifest) != {*expected, "failed_selectors"}:
        raise ValueError
    if any(type(manifest[key]) is not type(value) or manifest[key] != value for key, value in expected.items()):
        raise ValueError
    if type(manifest["failed_selectors"]) is not list:
        raise ValueError
    selectors = _strings(manifest["failed_selectors"])
    if tuple(selectors) != _FIXED_PR786_SELECTORS:
        raise ValueError


def _validate_manifest(manifest: dict[str, object], scope: _ProofScope) -> None:
    if scope == _FIXED_PR786_SCOPE:
        _validate_fixed_pr786_manifest(manifest)
        return
    if set(manifest) != MANIFEST_FIELDS:
        raise ValueError
    expected = {
        "schema_version": "1",
        "kind": "late-review-red-proof",
        "repository": REPOSITORY,
        "issue": ISSUE,
        "pull_request": scope.pull_request,
        "base_branch": BASE_BRANCH,
        "head_branch": scope.head_branch,
        "change_id": scope.change_id,
    }
    if any(manifest.get(key) != value for key, value in expected.items()):
        raise ValueError
    for field in ("issue", "pull_request", "run_id", "artifact_id"):
        _integer(manifest[field])
    for field in ("cycle_base_commit", "cycle_base_tree", "red_commit", "red_tree"):
        _string(manifest[field], OBJECT_PATTERN)
    for field in (
        "artifact_digest",
        "report_digest",
        "plan_report_digest",
        "junit_digest",
        "mapping_digest",
        "plan_digest",
    ):
        _string(manifest[field], DIGEST_PATTERN)
    _strings(manifest["failed_selectors"])


def _validate_event(event: dict[str, object], manifest: dict[str, object], final_ref: str, scope: _ProofScope) -> None:
    pull_request = _object(event.get("pull_request"))
    repository = _object(event.get("repository"))
    base = _object(pull_request.get("base"))
    head = _object(pull_request.get("head"))
    if (
        _integer(event.get("number")) != manifest["pull_request"]
        or repository.get("full_name") != REPOSITORY
        or base.get("ref") != BASE_BRANCH
        or _object(base.get("repo")).get("full_name") != REPOSITORY
        or head.get("ref") != scope.head_branch
        or head.get("sha") != final_ref
        or _object(head.get("repo")).get("full_name") != REPOSITORY
    ):
        raise ValueError


def _validate_run(run: dict[str, object], manifest: dict[str, object], scope: _ProofScope) -> None:
    fixed_scope = _ProofScope(
        "security-dependencies-0-55-11-dev", 786, "codex/security-dependencies-0-55-11-dev", "red", "red"
    )
    if scope == fixed_scope:
        expected_manifest = {
            "kind": "fixed-pr786-native-red-proof",
            "pull_request": 786,
            "change_id": "security-dependencies-0-55-11-dev",
            "repository": "nold-ai/specfact-cli",
            "red_commit": "d77209f4b13c386e29391f93e1f1c58d7fd8622f",
            "red_tree": "cfba03cf57f6de2fc6dd37709c9d8e38d03f2187",
            "executor_repository": "nold-ai/.github",
            "executor_commit": "8ad0a9434ceeac4a910df3c374536d7c909badec",
            "executor_tree": "975de5bf33e7621f1606eb344383d690dbdcae8a",
            "executor_head_branch": "codex/dev786-original-native-36",
            "executor_workflow_path": ".github/workflows/native-materialization-preflight.yml",
            "executor_workflow_name": "Native materialization development preflight 36",
            "executor_event": "create",
            "executor_conclusion": "success",
            "run_id": 41715861806,
            "run_attempt": 1,
        }
        expected_run = {
            "id": 41715861806,
            "run_attempt": 1,
            "workflow_id": 396761484,
            "head_sha": "8ad0a9434ceeac4a910df3c374536d7c909badec",
            "head_branch": "codex/dev786-original-native-36",
            "event": "create",
            "status": "completed",
            "conclusion": "success",
            "name": "Native materialization development preflight 36",
            "path": ".github/workflows/native-materialization-preflight.yml",
        }
        repository = _object(run.get("repository"))
        head_repository = _object(run.get("head_repository"))
        expected_repository = {"id": 1110267669, "full_name": "nold-ai/.github", "private": False, "fork": False}
        expected_owner = {"id": 225190663, "login": "nold-ai", "type": "Organization"}
        expected_actor = {"id": 39115308, "login": "djm81", "type": "User"}
        expected_commit = {
            "id": "8ad0a9434ceeac4a910df3c374536d7c909badec",
            "tree_id": "975de5bf33e7621f1606eb344383d690dbdcae8a",
        }
        for actual, expected in (
            (manifest, expected_manifest),
            (run, expected_run),
            (repository, expected_repository),
            (head_repository, expected_repository),
            (_object(repository.get("owner")), expected_owner),
            (_object(head_repository.get("owner")), expected_owner),
            (_object(run.get("actor")), expected_actor),
            (_object(run.get("triggering_actor")), expected_actor),
            (_object(run.get("head_commit")), expected_commit),
        ):
            if any(
                type(actual.get(key)) is not type(value) or actual.get(key) != value for key, value in expected.items()
            ):
                raise ValueError
        return
    if _integer(run.get("id")) != manifest["run_id"]:
        raise ValueError
    expected_fields = {
        "head_sha": manifest["red_commit"],
        "head_branch": scope.head_branch,
        "event": "pull_request",
        "status": "completed",
        "conclusion": "failure",
        "name": "Requirements Evidence",
        "path": WORKFLOW_PATH,
    }
    if any(run.get(key) != value for key, value in expected_fields.items()):
        raise ValueError
    if _object(run.get("repository")).get("full_name") != REPOSITORY:
        raise ValueError


def _validate_fixed_pr786_source(source: dict[str, object]) -> None:
    commit = _object(source.get("commit"))
    verification = _object(commit.get("verification"))
    parents = source.get("parents")
    if not isinstance(parents, list) or len(parents) != 1:
        raise ValueError
    expected_sections: tuple[tuple[dict[str, object], dict[str, object]], ...] = (
        (source, {"sha": "d77209f4b13c386e29391f93e1f1c58d7fd8622f"}),
        (_object(commit.get("tree")), {"sha": "cfba03cf57f6de2fc6dd37709c9d8e38d03f2187"}),
        (_object(cast(list[object], parents)[0]), {"sha": "22b2fa7bd763b18ada1bfd1a9ea482a624f34cca"}),
        (_object(source.get("author")), {"id": 41898282, "login": "github-actions[bot]", "type": "Bot"}),
        (_object(source.get("committer")), {"id": 19864447, "login": "web-flow", "type": "User"}),
        (verification, {"verified": True, "reason": "valid"}),
    )
    for actual, expected in expected_sections:
        if any(type(actual.get(key)) is not type(value) or actual.get(key) != value for key, value in expected.items()):
            raise ValueError
    signed_digests = (
        ("signature", "sha256:93fd3eda71f08a5916ce7c21de05d9f956ab35f3f4e3fbc82b245b0983300c5f"),
        ("payload", "sha256:5deb53f08b63c5f9810efd34d28445f521e1fa828384961d0a916d370286c1ce"),
    )
    for field, expected_digest in signed_digests:
        if _digest(_string(verification.get(field)).encode("utf-8")) != expected_digest:
            raise ValueError


def _validate_fixed_pr786_artifact(metadata: dict[str, object], manifest: dict[str, object]) -> None:
    _validate_fixed_pr786_manifest(manifest)
    entries = metadata.get("artifacts")
    if not isinstance(entries, list):
        raise ValueError
    named = [entry for entry in cast(list[object], entries) if _object(entry).get("name") == manifest["artifact_name"]]
    if len(named) != 1:
        raise ValueError
    artifact = _object(named[0])
    expected_sections: tuple[tuple[dict[str, object], dict[str, object]], ...] = (
        (
            artifact,
            {
                "id": manifest["artifact_id"],
                "name": manifest["artifact_name"],
                "size_in_bytes": 1885415,
                "expired": False,
                "digest": manifest["artifact_digest"],
            },
        ),
        (
            _object(artifact.get("workflow_run")),
            {
                "id": manifest["run_id"],
                "repository_id": 1110267669,
                "head_repository_id": 1110267669,
                "head_branch": manifest["executor_head_branch"],
                "head_sha": manifest["executor_commit"],
            },
        ),
    )
    for actual, expected in expected_sections:
        if any(type(actual.get(key)) is not type(value) or actual.get(key) != value for key, value in expected.items()):
            raise ValueError
    _validate_fixed_pr786_source(_object(metadata.get("source_commit")))


def _validate_artifact(metadata: dict[str, object], manifest: dict[str, object]) -> None:
    if manifest.get("kind") == "fixed-pr786-native-red-proof":
        _validate_fixed_pr786_artifact(metadata, manifest)
        return
    entries = metadata.get("artifacts")
    if not isinstance(entries, list):
        raise ValueError
    named = [entry for entry in cast(list[object], entries) if _object(entry).get("name") == "requirements-evidence"]
    if len(named) != 1:
        raise ValueError
    artifact = _object(named[0])
    workflow_run = _object(artifact.get("workflow_run"))
    if (
        _integer(artifact.get("id")) != manifest["artifact_id"]
        or artifact.get("expired") is not False
        or artifact.get("digest") != manifest["artifact_digest"]
        or _integer(workflow_run.get("id")) != manifest["run_id"]
        or workflow_run.get("head_sha") != manifest["red_commit"]
    ):
        raise ValueError


class _JunitCollector:
    def __init__(self) -> None:
        self.cases: list[tuple[str, bool]] = []
        self.properties: dict[str, list[str]] | None = None
        self.failed = False

    def _start_case(self) -> None:
        if self.properties is not None:
            raise ValueError
        self.properties, self.failed = {}, False

    def _record_property(self, attributes: dict[str, str]) -> None:
        key, value = attributes.get("name"), attributes.get("value")
        if key is not None and value is not None and self.properties is not None:
            self.properties.setdefault(key, []).append(value)

    def _start(self, name: str, attributes: dict[str, str]) -> None:
        if name == "testcase":
            self._start_case()
            return
        if self.properties is None:
            return
        if name in {"failure", "error"}:
            self.failed = True
        elif name == "property":
            self._record_property(attributes)

    def _end(self, name: str) -> None:
        if name != "testcase" or self.properties is None:
            return
        selectors = self.properties.get("specfact.selector", [])
        if len(selectors) != 1 or not selectors[0]:
            raise ValueError
        self.cases.append((selectors[0], self.failed))
        self.properties = None

    def _reject(self, *_arguments: object) -> int:
        raise ValueError


def _junit_selectors(payload: bytes) -> tuple[list[str], list[str]]:
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
    except (expat.ExpatError, ValueError) as error:
        raise ValueError from error
    if collector.properties is not None or not collector.cases:
        raise ValueError
    selectors = [selector for selector, _failed in collector.cases]
    if len(set(selectors)) != len(selectors):
        raise ValueError
    return selectors, [selector for selector, failed in collector.cases if failed]


def _normalize_junit_selector(selector: str, expected_selectors: set[str]) -> str:
    """Map one exact pytest parameter case to an unambiguous governed selector."""
    if selector in expected_selectors:
        return selector
    matches = [
        expected
        for expected in expected_selectors
        if selector.startswith(f"{expected}[") and selector.endswith("]") and len(selector) > len(expected) + 2
    ]
    if len(matches) != 1:
        raise ValueError
    return matches[0]


def _normalize_junit_selectors(selectors: Sequence[str], expected_selectors: set[str]) -> list[str]:
    """Map unique pytest parameter cases to their governed selectors."""
    if len(selectors) != len(set(selectors)):
        raise ValueError
    return [_normalize_junit_selector(selector, expected_selectors) for selector in selectors]


def _artifact_payloads(root: Path, manifest: dict[str, object]) -> tuple[bytes, bytes, bytes]:
    report_payload = _regular_payload(root / "requirements-evidence.json")
    plan_payload = _regular_payload(root / "requirements-evidence-plan.json")
    junit_payload = _regular_payload(root / "requirements-proof.xml")
    actual = {
        "report_digest": _digest(report_payload),
        "plan_report_digest": _digest(plan_payload),
        "junit_digest": _digest(junit_payload),
    }
    if any(manifest[field] != digest for field, digest in actual.items()):
        raise ValueError
    return report_payload, plan_payload, junit_payload


def _planned_selectors(plan: dict[str, object]) -> list[str]:
    cases = plan.get("cases")
    if not isinstance(cases, list):
        raise ValueError
    return [
        _string(case_object.get("node_id"))
        for case in cast(list[object], cases)
        if (case_object := _object(case)).get("runner") == "pytest"
    ]


def _validate_final_report(
    report: dict[str, object], execution: dict[str, object], manifest: dict[str, object], scope: _ProofScope
) -> None:
    expected_report = {
        "delivery_status": "incomplete",
        "gate_decision": "fail",
        "observed_maturity": "incomplete",
        "required_maturity": scope.required_maturity,
        "verdict": "failed",
        "mapping_digest": manifest["mapping_digest"],
        "plan_digest": manifest["plan_digest"],
    }
    expected_execution = {
        "junit_digest": manifest["junit_digest"],
        "run_stage": scope.run_stage,
        "source_ref": manifest["red_commit"],
    }
    if any(report.get(field) != value for field, value in expected_report.items()):
        raise ValueError
    if any(execution.get(field) != value for field, value in expected_execution.items()):
        raise ValueError


def _validate_plan_report(plan_report: dict[str, object], plan: dict[str, object], manifest: dict[str, object]) -> None:
    expected_plan = {
        "mapping_digest": manifest["mapping_digest"],
        "plan_digest": manifest["plan_digest"],
    }
    if plan_report.get("gate_decision") != "pass":
        raise ValueError
    if any(plan.get(field) != value for field, value in expected_plan.items()):
        raise ValueError


def _validate_fixed_pr786_plan(
    plan_report: dict[str, object], aggregate: dict[str, object], manifest: dict[str, object]
) -> list[str]:
    plan = _object(aggregate.get("plan"))
    _validate_plan_report(aggregate, plan, manifest)
    sources = plan_report.get("sources")
    if not isinstance(sources, list) or len(sources) != 1:
        raise ValueError
    source = _object(cast(list[object], sources)[0])
    source_plan = _object(source.get("plan"))
    expected = {
        "mapping_digest": manifest["source_mapping_digest"],
        "plan_digest": manifest["source_plan_digest"],
    }
    if plan_report.get("gate_decision") != "pass" or source.get("gate_decision") != "pass":
        raise ValueError
    if source.get("source") != f"openspec/changes/{_FIXED_PR786_SCOPE.change_id}":
        raise ValueError
    if any(source_plan.get(key) != value for key, value in expected.items()):
        raise ValueError
    planned = _planned_selectors(plan)
    if sorted(_planned_selectors(source_plan)) != sorted(planned):
        raise ValueError
    return planned


def _validate_fixed_pr786_packet(root: Path, manifest: dict[str, object]) -> tuple[bytes, list[str]]:
    _validate_fixed_pr786_manifest(manifest)
    report_payload, planning_payload, junit_payload = _artifact_payloads(root, manifest)
    aggregate_payload = _regular_payload(root / "plan.json")
    if _digest(aggregate_payload) != manifest["plan_output_digest"]:
        raise ValueError
    report = _object(json.loads(report_payload, object_pairs_hook=_pairs))
    planning = _object(json.loads(planning_payload, object_pairs_hook=_pairs))
    aggregate = _object(json.loads(aggregate_payload, object_pairs_hook=_pairs))
    execution = _object(report.get("execution_proof"))
    expected_report = {
        "delivery_status": "failing-first-proven",
        "gate_decision": "pass",
        "observed_maturity": "red",
        "required_maturity": "red",
        "verdict": "passed",
        "mapping_digest": manifest["mapping_digest"],
        "plan_digest": manifest["plan_digest"],
    }
    expected_execution = {
        "junit_digest": manifest["junit_digest"],
        "run_stage": "red",
        "source_ref": manifest["red_commit"],
        "source_tree": manifest["red_tree"],
        "merge_base": manifest["cycle_base_commit"],
    }
    for actual, expected in ((report, expected_report), (execution, expected_execution)):
        if any(actual.get(key) != value for key, value in expected.items()):
            raise ValueError
    planned = _validate_fixed_pr786_plan(planning, aggregate, manifest)
    reported = _strings(execution.get("selectors"))
    junit, failed = _junit_selectors(junit_payload)
    expected_selectors = list(_FIXED_PR786_SELECTORS)
    if reported != expected_selectors or junit != planned or failed != junit:
        raise ValueError
    if sorted(planned) != expected_selectors:
        raise ValueError
    return junit_payload, reported


def _validate_raw_artifact(root: Path, manifest: dict[str, object], scope: _ProofScope) -> tuple[bytes, list[str]]:
    if scope == _FIXED_PR786_SCOPE:
        return _validate_fixed_pr786_packet(root, manifest)
    report_payload, plan_payload, junit_payload = _artifact_payloads(root, manifest)
    report = _object(json.loads(report_payload, object_pairs_hook=_pairs))
    plan_report = _object(json.loads(plan_payload, object_pairs_hook=_pairs))
    execution = _object(report.get("execution_proof"))
    plan = _object(plan_report.get("plan"))
    _validate_final_report(report, execution, manifest, scope)
    _validate_plan_report(plan_report, plan, manifest)
    planned = _planned_selectors(plan)
    reported = _strings(execution.get("selectors"))
    junit, failed = _junit_selectors(junit_payload)
    expected_failures = _strings(manifest["failed_selectors"])
    selector_lists = (planned, reported)
    if any(not selectors or len(selectors) != len(set(selectors)) for selectors in selector_lists):
        raise ValueError
    expected_selectors = set(reported)
    normalized_junit = _normalize_junit_selectors(junit, expected_selectors)
    normalized_failures = _normalize_junit_selectors(failed, expected_selectors)
    if set(planned) != expected_selectors or set(normalized_junit) != expected_selectors:
        raise ValueError
    if (
        len(expected_failures) != len(set(expected_failures))
        or set(normalized_failures) != set(expected_failures)
        or not set(normalized_failures).issubset(expected_selectors)
    ):
        raise ValueError
    return junit_payload, reported


def _git(repo_root: Path, *arguments: str, binary: bool = False) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(
        ["git", *arguments], cwd=repo_root, capture_output=True, check=False, text=not binary, timeout=30
    )


def _resolve_commit(repo_root: Path, reference: str) -> str:
    result = _git(repo_root, "rev-parse", "--verify", f"{reference}^{{commit}}")
    value = result.stdout.strip() if result.returncode == 0 else ""
    return _string(value, OBJECT_PATTERN)


def _validated_history_commits(
    repo_root: Path, manifest: dict[str, object], cycle_ref: str, final_ref: str
) -> tuple[str, str, str]:
    cycle = _resolve_commit(repo_root, cycle_ref)
    red = _resolve_commit(repo_root, _string(manifest["red_commit"], OBJECT_PATTERN))
    final = _resolve_commit(repo_root, final_ref)
    if cycle != manifest["cycle_base_commit"] or red != manifest["red_commit"] or red in {cycle, final}:
        raise ValueError
    return cycle, red, final


def _validate_recorded_trees(repo_root: Path, manifest: dict[str, object], cycle: str, red: str) -> None:
    for commit, field in ((cycle, "cycle_base_tree"), (red, "red_tree")):
        if _resolve_commit(repo_root, commit) != commit:
            raise ValueError
        tree = _git(repo_root, "rev-parse", "--verify", f"{commit}^{{tree}}")
        if tree.returncode or tree.stdout.strip() != manifest[field]:
            raise ValueError


def _changed_paths(repo_root: Path, parent: str, commit: str) -> list[str]:
    changed = _git(repo_root, "diff", "--name-only", "-z", "--no-renames", parent, commit, binary=True)
    if changed.returncode or not changed.stdout.endswith(b"\0"):
        raise ValueError
    return [raw_path.decode("utf-8") for raw_path in changed.stdout[:-1].split(b"\0")]


def _validate_red_path(path: str, allowed_change: str) -> None:
    pure = PurePosixPath(path)
    if pure.is_absolute() or ".." in pure.parts or not path.startswith(("tests/", allowed_change)):
        raise ValueError


def _validate_linear_red_segment(repo_root: Path, cycle: str, red: str, scope: _ProofScope) -> None:
    revisions = _git(repo_root, "rev-list", "--reverse", "--parents", f"{cycle}..{red}")
    if revisions.returncode or not revisions.stdout.splitlines():
        raise ValueError
    parent = cycle
    allowed_change = f"openspec/changes/{scope.change_id}/"
    for line in revisions.stdout.splitlines():
        values = line.split()
        if len(values) != 2 or values[1] != parent:
            raise ValueError
        commit = values[0]
        for path in _changed_paths(repo_root, parent, commit):
            if scope == _FIXED_PR786_SCOPE and path == "openspec/CHANGE_ORDER.md":
                continue
            _validate_red_path(path, allowed_change)
        parent = commit
    if parent != red:
        raise ValueError


def _validate_history(
    repo_root: Path, manifest: dict[str, object], cycle_ref: str, final_ref: str, scope: _ProofScope
) -> None:
    cycle, red, final = _validated_history_commits(repo_root, manifest, cycle_ref, final_ref)
    _validate_recorded_trees(repo_root, manifest, cycle, red)
    _validate_linear_red_segment(repo_root, cycle, red, scope)
    if _git(repo_root, "merge-base", "--is-ancestor", red, final).returncode:
        raise ValueError


def _load_provenance(
    path: Path, repo_root: Path, cycle_commit: str
) -> tuple[Callable[..., None], Callable[..., list[str]]]:
    if path.name != "requirements_proof_provenance.py":
        raise ValueError
    payload = _regular_payload(path)
    cycle = _string(cycle_commit, OBJECT_PATTERN)
    trusted = _git(repo_root, "show", f"{cycle}:{PROVENANCE_PATH}", binary=True)
    if trusted.returncode:
        validator_root = Path(__file__).resolve(strict=True).parents[1]
        expected_path = validator_root / PROVENANCE_PATH
        if path.resolve(strict=True) != expected_path:
            raise ValueError
        trusted = _git(validator_root, "cat-file", "blob", PROOF_CYCLE_PROVENANCE_BLOB, binary=True)
    if trusted.returncode or trusted.stdout != payload:
        raise ValueError
    module_name = "_specfact_trusted_requirements_proof_provenance"
    specification = importlib.util.spec_from_file_location(module_name, path)
    if specification is None or specification.loader is None:
        raise ValueError
    module = importlib.util.module_from_spec(specification)
    prior = sys.modules.get(module_name)
    sys.modules[module_name] = module
    try:
        specification.loader.exec_module(module)
    finally:
        if prior is None:
            sys.modules.pop(module_name, None)
        else:
            sys.modules[module_name] = prior
    bind = getattr(cast(ModuleType, module), "bind_red_proof", None)
    validate = getattr(cast(ModuleType, module), "validate_prior_red_proof", None)
    if not callable(bind) or not callable(validate):
        raise ValueError
    if _regular_payload(path) != payload:
        raise ValueError
    return cast(Callable[..., None], bind), cast(Callable[..., list[str]], validate)


def _external_outputs(output: Path, repo_root: Path) -> tuple[Path, Path]:
    output.parent.mkdir(parents=True, exist_ok=True)
    parent = output.parent.resolve(strict=True)
    repository = repo_root.resolve(strict=True)
    try:
        parent.relative_to(repository)
    except ValueError:
        pass
    else:
        raise ValueError
    report = parent / output.name
    junit = report.with_suffix(".xml")
    for path in (report, junit):
        if path.exists() and (path.is_symlink() or not path.is_file()):
            raise ValueError
    return report, junit


def _normalize(arguments: argparse.Namespace) -> None:
    repo_root = arguments.repo_root.resolve(strict=True)
    manifest_path = arguments.manifest.resolve(strict=True)
    scope = _proof_scope(manifest_path, repo_root)
    manifest = _read_json(manifest_path)
    _validate_manifest(manifest, scope)
    final = _resolve_commit(repo_root, arguments.final_ref)
    _validate_event(_read_json(arguments.event), manifest, final, scope)
    _validate_run(_read_json(arguments.red_run), manifest, scope)
    _validate_artifact(_read_json(arguments.red_artifacts), manifest)
    cycle_commit = _string(manifest["cycle_base_commit"], OBJECT_PATTERN)
    _validate_history(repo_root, manifest, arguments.cycle_base_ref, final, scope)
    junit_payload, selectors = _validate_raw_artifact(arguments.red_artifact_root, manifest, scope)
    bind, validate = _load_provenance(arguments.trusted_provenance, repo_root, cycle_commit)
    output, output_xml = _external_outputs(arguments.output, repo_root)
    with tempfile.TemporaryDirectory(prefix=".late-red-", dir=output.parent) as directory:
        candidate = Path(directory) / output.name
        candidate_xml = candidate.with_suffix(".xml")
        candidate_xml.write_bytes(junit_payload)
        if scope == _FIXED_PR786_SCOPE:
            report_payload = _regular_payload(arguments.red_artifact_root / "requirements-evidence.json")
            if _digest(report_payload) != manifest["report_digest"]:
                raise ValueError
            candidate.write_bytes(report_payload)
        else:
            normalized = {
                "gate_decision": "pass",
                "observed_maturity": "red",
                "mapping_digest": manifest["mapping_digest"],
                "plan_digest": manifest["plan_digest"],
                "execution_proof": {
                    "junit_digest": manifest["junit_digest"],
                    "run_stage": "red",
                    "selectors": selectors,
                    "source_ref": manifest["red_commit"],
                },
            }
            candidate.write_text(json.dumps(normalized, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
            bind(candidate, repo_root, base_ref=manifest["cycle_base_commit"], junit_path=candidate_xml)
        if validate(candidate, repo_root, base_ref=manifest["cycle_base_commit"], final_ref=final):
            raise ValueError
        os.replace(candidate_xml, output_xml)
        os.replace(candidate, output)


_FIXED_PR786_SIGNER_FILES = (
    ("scripts/dev_security_ci_signer.py", "dfc44d082253e71d0344e0ead08bb846d37ae2010e70dc06506746610ea6e4c8"),
    (".github/workflows/specfact.yml", "8896864306ea9a1bb385e68348b0a74f029227292e461abb080f937833f8fea6"),
    ("ci/recovery/dev-security-signer-runtime.txt", "bc64c498cf74b3a959a1522c04614e199061dea2e35ab0110d58b9411db38712"),
)
_FIXED_PR786_AUTHORITY_SHA256 = "5441e26e7c3c8f18973c781e7d43c72076b3283c915d98ca5188bb174bf17c45"
_FIXED_PR786_MANIFEST_SHA256 = "f08743305cbd774e1d097c9911383a113943071adc8c256528866adb4c1f098a"


def _fixed_pr786_authority_helper(path: Path) -> ModuleType:
    raw = _regular_payload(path)
    if hashlib.sha256(raw).hexdigest() != _FIXED_PR786_AUTHORITY_SHA256:
        raise ValueError
    with tempfile.TemporaryDirectory(prefix="fixed786-authority-") as directory:
        frozen = Path(directory) / "trusted_requirements_authority.py"
        with frozen.open("xb") as stream:
            stream.write(raw)
        frozen.chmod(0o400)
        if _regular_payload(frozen) != raw:
            raise ValueError
        module_name = "_fixed_pr786_f7"
        specification = importlib.util.spec_from_file_location(module_name, frozen)
        if specification is None or specification.loader is None:
            raise ValueError
        helper = importlib.util.module_from_spec(specification)
        prior = sys.modules.get(module_name)
        sys.modules[module_name] = helper
        try:
            specification.loader.exec_module(helper)
        finally:
            if prior is None:
                sys.modules.pop(module_name, None)
            else:
                sys.modules[module_name] = prior
        if _regular_payload(frozen) != raw:
            raise ValueError
    return helper


def _fixed_pr786_pr_heads(current: dict[str, object], event: dict[str, object], manifest: dict[str, object]) -> None:
    for side in ("head", "base"):
        observed, expected = _object(current.get(side)), _object(_object(event["pull_request"])[side])
        if (
            any(observed.get(key) != expected.get(key) for key in ("sha", "ref"))
            or _object(observed.get("repo")).get("full_name") != REPOSITORY
        ):
            raise ValueError
    if _object(current["base"]).get("sha") != manifest["cycle_base_commit"]:
        raise ValueError


def _fixed_pr786_current_commit(
    helper: ModuleType, event: dict[str, object], manifest: dict[str, object], final: str, repo_root: Path
) -> dict[str, object]:
    token = os.environ["GITHUB_TOKEN"]
    current = _object(helper._api_json("/repos/nold-ai/specfact-cli/pulls/786", token)[0])
    if (
        current.get("number") != 786
        or current.get("state") != "open"
        or current.get("draft") is not False
        or current.get("auto_merge") is not None
    ):
        raise ValueError
    _fixed_pr786_pr_heads(current, event, manifest)
    commit = _object(helper._api_json(f"/repos/{REPOSITORY}/git/commits/{final}", token)[0])
    if _object(commit.get("tree")).get("sha") != _git(repo_root, "rev-parse", f"{final}^{{tree}}").stdout.strip():
        raise ValueError
    return commit


def _fixed_pr786_authority(arguments: argparse.Namespace) -> tuple[ModuleType, dict[str, object], dict[str, object]]:
    helper = _fixed_pr786_authority_helper(arguments.trusted_authority)
    token = _string(os.environ.get("GITHUB_TOKEN"))
    if os.environ.get("GITHUB_API_URL") != "https://api.github.com":
        raise ValueError
    event = _read_json(arguments.event)
    helper._event_boundary(event)
    final = _resolve_commit(arguments.repo_root, arguments.final_ref)
    manifest = _read_json(arguments.manifest)
    _validate_fixed_pr786_manifest(manifest)
    _validate_event(event, manifest, final, _FIXED_PR786_SCOPE)
    commit = _fixed_pr786_current_commit(helper, event, manifest, final, arguments.repo_root)
    comments = helper._comments(token, REPOSITORY, 786)
    _, provisional = helper._matching_authority(event, comments, commit, datetime.now(UTC))
    signer = urllib.parse.quote(_string(provisional["signer_login"]), safe="")
    permission = helper._api_json(f"/repos/{REPOSITORY}/collaborators/{signer}/permission", token)[0]
    now = datetime.now(UTC)
    receipt = helper.validate_authority(event, comments, commit, permission, now)
    selected, _ = helper._matching_authority(event, comments, commit, now)
    comment = {key: selected[key] for key in ("id", "body", "user", "author_association", "created_at", "updated_at")}
    comment["body_digest"] = _digest(_string(comment["body"]).encode())
    return helper, commit, {"receipt": receipt, "comment": comment}


def _fixed_pr786_tree_path(path: str, seen: set[str]) -> None:
    if (
        path in seen
        or "\\" in path
        or any(ord(c) < 32 for c in path)
        or any(p in ("", ".", "..") for p in path.split("/"))
    ):
        raise ValueError


def _fixed_pr786_tree(helper: ModuleType, sha: str) -> dict[str, tuple[str, str]]:
    record = _object(
        helper._api_json(f"/repos/{REPOSITORY}/git/trees/{sha}?recursive=1", os.environ["GITHUB_TOKEN"])[0]
    )
    entries = record.get("tree")
    if record.get("sha") != sha or record.get("truncated") is not False or not isinstance(entries, list):
        raise ValueError
    result: dict[str, tuple[str, str]] = {}
    seen: set[str] = set()
    for value in entries:
        entry = _object(value)
        path = _string(entry.get("path"))
        mode, kind = entry.get("mode"), entry.get("type")
        _fixed_pr786_tree_path(path, seen)
        seen.add(path)
        oid = _string(entry.get("sha"), OBJECT_PATTERN)
        if (mode, kind) not in (("040000", "tree"), ("100644", "blob"), ("100755", "blob")):
            raise ValueError
        if kind == "blob":
            result[path] = (_string(mode), oid)
    return result


def _fixed_pr786_blob(helper: ModuleType, inventory: dict[str, tuple[str, str]], path: str) -> bytes:
    mode, oid = inventory[path]
    if mode != "100644":
        raise ValueError
    record = _object(helper._api_json(f"/repos/{REPOSITORY}/git/blobs/{oid}", os.environ["GITHUB_TOKEN"])[0])
    if record.get("sha") != oid or record.get("encoding") != "base64":
        raise ValueError
    encoded = _string(record.get("content"))
    if len(encoded) > MAX_INPUT_BYTES:
        raise ValueError
    raw = base64.b64decode(encoded.replace("\r", "").replace("\n", ""), validate=True)
    if type(record.get("size")) is not int or record["size"] != len(raw) or len(raw) > MAX_INPUT_BYTES:
        raise ValueError
    if hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw, usedforsecurity=False).hexdigest() != oid:
        raise ValueError
    return raw


def _fixed_pr786_signed_headers(record: dict[str, object], tree: str, parent: str, message: str) -> list[str]:
    verification = _object(record.get("verification"))
    if verification.get("verified") is not True or verification.get("reason") != "valid":
        raise ValueError
    signature = _string(verification.get("signature"))
    if not signature.startswith("-----BEGIN PGP SIGNATURE-----") or not signature.rstrip().endswith(
        "-----END PGP SIGNATURE-----"
    ):
        raise ValueError
    headers, separator, signed_message = _string(verification.get("payload")).partition("\n\n")
    lines = headers.split("\n")
    if (
        separator != "\n\n"
        or signed_message != message
        or len(lines) != 4
        or lines[:2] != [f"tree {tree}", f"parent {parent}"]
    ):
        raise ValueError
    return lines


def _fixed_pr786_signed_identities(record: dict[str, object], lines: list[str]) -> None:
    roles = (
        ("author", "github-actions[bot]", "41898282+github-actions[bot]@users.noreply.github.com"),
        ("committer", "GitHub", "noreply@github.com"),
    )
    for index, (role, name, email) in enumerate(roles, 2):
        identity = _object(record.get(role))
        if (
            identity.get("name") != name
            or identity.get("email") != email
            or re.fullmatch(re.escape(f"{role} {name} <{email}> ") + r"[0-9]+ [+-][0-9]{4}", lines[index]) is None
        ):
            raise ValueError


def _fixed_pr786_signed_readback(helper: ModuleType, record: dict[str, object], sha: str) -> None:
    token = os.environ["GITHUB_TOKEN"]
    readback = _object(helper._api_json(f"/repos/{REPOSITORY}/git/commits/{sha}", token)[0])
    if any(
        readback.get(key) != record.get(key)
        for key in ("sha", "tree", "parents", "message", "verification", "author", "committer")
    ):
        raise ValueError
    api = _object(helper._api_json(f"/repos/{REPOSITORY}/commits/{sha}", token)[0])
    if api.get("sha") != sha:
        raise ValueError
    for role, expected in (
        ("author", {"id": 41898282, "login": "github-actions[bot]", "type": "Bot"}),
        ("committer", {"id": 19864447, "login": "web-flow", "type": "User"}),
    ):
        actual = _object(api.get(role))
        if any(type(actual.get(key)) is not type(value) or actual.get(key) != value for key, value in expected.items()):
            raise ValueError


def _fixed_pr786_signed(helper: ModuleType, record: dict[str, object], tree: str, parent: str, message: str) -> None:
    sha = _string(record.get("sha"), OBJECT_PATTERN)
    if _object(record.get("tree")).get("sha") != tree or record.get("message") != message:
        raise ValueError
    parents = record.get("parents")
    if not isinstance(parents, list) or len(parents) != 1 or _object(parents[0]).get("sha") != parent:
        raise ValueError
    lines = _fixed_pr786_signed_headers(record, tree, parent, message)
    _fixed_pr786_signed_identities(record, lines)
    _fixed_pr786_signed_readback(helper, record, sha)


def _fixed_pr786_allowed_expression(pinned_program: bytes) -> ast.expr:
    assignments = [
        node
        for node in ast.parse(pinned_program).body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "_ALLOWED" for target in node.targets)
    ]
    if len(assignments) != 1:
        raise ValueError
    return assignments[0].value


def _fixed_pr786_allowed_paths(pinned_program: bytes) -> set[str]:
    expression = _fixed_pr786_allowed_expression(pinned_program)
    if (
        not isinstance(expression, ast.Call)
        or not isinstance(expression.func, ast.Name)
        or expression.func.id != "frozenset"
        or len(expression.args) != 1
    ):
        raise ValueError
    allowed = ast.literal_eval(expression.args[0])
    if not isinstance(allowed, set) or not all(isinstance(path, str) for path in allowed):
        raise ValueError
    return cast(set[str], allowed)


def _fixed_pr786_executor_tree(helper: ModuleType, executor: str) -> tuple[dict[str, tuple[str, str]], set[str]]:
    token = os.environ["GITHUB_TOKEN"]
    executor_commit = _object(helper._api_json(f"/repos/{REPOSITORY}/git/commits/{executor}", token)[0])
    if executor_commit.get("sha") != executor:
        raise ValueError
    executor_tree = _fixed_pr786_tree(helper, _string(_object(executor_commit.get("tree")).get("sha"), OBJECT_PATTERN))
    pinned_program = b""
    for path, expected in _FIXED_PR786_SIGNER_FILES:
        raw = _fixed_pr786_blob(helper, executor_tree, path)
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError
        if path == "scripts/dev_security_ci_signer.py":
            pinned_program = raw
    return executor_tree, _fixed_pr786_allowed_paths(pinned_program)


def _fixed_pr786_intent(
    helper: ModuleType, executor_tree: dict[str, tuple[str, str]], intent_digest: str
) -> dict[str, object]:
    raw_intent = _fixed_pr786_blob(helper, executor_tree, "ci/recovery/dev-security-intent.json")
    if hashlib.sha256(raw_intent).hexdigest() != intent_digest:
        raise ValueError
    intent = _object(json.loads(raw_intent, object_pairs_hook=_pairs))
    if set(intent) != {
        "repository_id",
        "repository_full_name",
        "actor",
        "triggering_actor",
        "dev",
        "main",
        "checkpoints",
        "auxiliary_ref",
        "destination",
    }:
        raise ValueError
    if (intent["repository_full_name"], intent["dev"], intent["auxiliary_ref"], intent["destination"]) != (
        REPOSITORY,
        "9b5ad1e78430cc0b061cb16de42f73de96f4f312",
        "refs/heads/codex/dev786-complete-ci-signer-20261104",
        "refs/heads/codex/security-dev-complete-candidate-20261104",
    ):
        raise ValueError
    _string(intent["main"], OBJECT_PATTERN)
    repository_id = _integer(intent["repository_id"])
    token = os.environ["GITHUB_TOKEN"]
    repository = _object(helper._api_json(f"/repos/{REPOSITORY}", token)[0])
    if repository.get("id") != repository_id or repository.get("full_name") != REPOSITORY:
        raise ValueError
    return intent


def _fixed_pr786_source_record(
    helper: ModuleType, source_sha: str, source_parent: str, tree: str, original_message: str
) -> None:
    token = os.environ["GITHUB_TOKEN"]
    actual_source = _object(helper._api_json(f"/repos/{REPOSITORY}/git/commits/{source_sha}", token)[0])
    parents = actual_source.get("parents")
    if (
        actual_source.get("sha") != source_sha
        or actual_source.get("message") != original_message
        or _object(actual_source.get("tree")).get("sha") != tree
        or not isinstance(parents, list)
        or len(parents) != 1
        or _object(parents[0]).get("sha") != source_parent
    ):
        raise ValueError


def _fixed_pr786_source_commit(
    helper: ModuleType, checkpoint: dict[str, object], source_parent: str, seen: set[str]
) -> str:
    if set(checkpoint) != {"source_commit", "source_parent", "source_tree", "source_message", "delta"}:
        raise ValueError
    source_sha = _string(checkpoint["source_commit"], OBJECT_PATTERN)
    tree = _string(checkpoint["source_tree"], OBJECT_PATTERN)
    original_message = _string(checkpoint["source_message"])
    if (
        checkpoint["source_parent"] != source_parent
        or source_sha in seen
        or any(
            re.match(r"\s*(?:Source-Commit|Intent|Executor|Run|Attempt)\s*:", line, re.IGNORECASE)
            for line in original_message.splitlines()
        )
    ):
        raise ValueError
    seen.add(source_sha)
    _fixed_pr786_source_record(helper, source_sha, source_parent, tree, original_message)
    return source_sha


def _fixed_pr786_delta_entry(entry: object) -> None:
    if entry is not None and (
        not isinstance(entry, list)
        or len(entry) != 2
        or entry[0] != "100644"
        or OBJECT_PATTERN.fullmatch(_string(entry[1])) is None
    ):
        raise ValueError


def _fixed_pr786_expected_delta(checkpoint: dict[str, object], allowed: set[str]) -> dict[str, tuple[object, object]]:
    delta = checkpoint["delta"]
    if not isinstance(delta, list) or not delta:
        raise ValueError
    expected_delta: dict[str, tuple[object, object]] = {}
    for value in delta:
        item = _object(value)
        if set(item) != {"path", "before", "after"} or item["path"] not in allowed or item["path"] in expected_delta:
            raise ValueError
        _fixed_pr786_delta_entry(item["before"])
        _fixed_pr786_delta_entry(item["after"])
        expected_delta[_string(item["path"])] = (item["before"], item["after"])
    return expected_delta


def _fixed_pr786_source_delta(
    checkpoint: dict[str, object],
    allowed: set[str],
    before: dict[str, tuple[str, str]],
    after: dict[str, tuple[str, str]],
) -> None:
    expected_delta = _fixed_pr786_expected_delta(checkpoint, allowed)
    actual_delta = {
        path: (list(before[path]) if path in before else None, list(after[path]) if path in after else None)
        for path in before.keys() | after.keys()
        if before.get(path) != after.get(path)
    }
    if actual_delta != expected_delta:
        raise ValueError


def _fixed_pr786_sources(
    helper: ModuleType, intent: dict[str, object], allowed: set[str], source: str, final: dict[str, object]
) -> list[dict[str, object]]:
    values = intent["checkpoints"]
    if not isinstance(values, list) or not 1 <= len(values) <= 32:
        raise ValueError
    before = _fixed_pr786_tree(helper, "24112d8c9983333f9059283965230348f718b74c")
    source_parent = "d77209f4b13c386e29391f93e1f1c58d7fd8622f"
    seen = {source_parent}
    checkpoints = [_object(value) for value in values]
    for checkpoint in checkpoints:
        source_parent = _fixed_pr786_source_commit(helper, checkpoint, source_parent, seen)
        after = _fixed_pr786_tree(helper, _string(checkpoint["source_tree"], OBJECT_PATTERN))
        _fixed_pr786_source_delta(checkpoint, allowed, before, after)
    if source != source_parent or _object(final.get("tree")).get("sha") != checkpoints[-1]["source_tree"]:
        raise ValueError
    return checkpoints


def _fixed_pr786_outputs(
    helper: ModuleType,
    final: dict[str, object],
    checkpoints: list[dict[str, object]],
    signing: tuple[str, str, int],
) -> None:
    intent_digest, executor, run_id = signing
    token = os.environ["GITHUB_TOKEN"]
    output = final
    for checkpoint in reversed(checkpoints):
        parents = output.get("parents")
        if not isinstance(parents, list) or len(parents) != 1:
            raise ValueError
        parent = _string(_object(parents[0]).get("sha"), OBJECT_PATTERN)
        expected_message = f"{checkpoint['source_message']}\n\nSource-Commit: {checkpoint['source_commit']}\nIntent: {intent_digest}\nExecutor: {executor}\nRun: {run_id}\nAttempt: 1"
        _fixed_pr786_signed(
            helper, output, _string(checkpoint["source_tree"], OBJECT_PATTERN), parent, expected_message
        )
        output = _object(helper._api_json(f"/repos/{REPOSITORY}/git/commits/{parent}", token)[0])
    if output.get("sha") != "d77209f4b13c386e29391f93e1f1c58d7fd8622f":
        raise ValueError


def _fixed_pr786_run_actors(run: dict[str, object], intent: dict[str, object]) -> None:
    for key in ("actor", "triggering_actor"):
        expected = _object(intent[key])
        if set(expected) != {"id", "login"} or any(
            _object(run.get(key)).get(field) != expected[field] for field in expected
        ):
            raise ValueError
        _integer(expected["id"])
        _string(expected["login"])


def _fixed_pr786_run_repositories(run: dict[str, object], repository_id: int) -> None:
    for key in ("repository", "head_repository"):
        repository = _object(run.get(key))
        if repository.get("id") != repository_id or repository.get("full_name") != REPOSITORY:
            raise ValueError


def _fixed_pr786_history_runs(helper: ModuleType) -> list[dict[str, object]]:
    token = os.environ["GITHUB_TOKEN"]
    history = _object(
        helper._api_json(
            f"/repos/{REPOSITORY}/actions/workflows/204352514/runs?event=workflow_dispatch&per_page=100", token
        )[0]
    )
    runs = history.get("workflow_runs")
    if (
        not isinstance(runs, list)
        or type(history.get("total_count")) is not int
        or history["total_count"] != len(runs)
        or len(runs) > 100
    ):
        raise ValueError
    return [_object(value) for value in runs]


def _fixed_pr786_run_history(helper: ModuleType, executor: str, expected_run: dict[str, object]) -> None:
    same_executor = [run for run in _fixed_pr786_history_runs(helper) if run.get("head_sha") == executor]
    if len(same_executor) != 1 or any(
        type(same_executor[0].get(key)) is not type(value) or same_executor[0].get(key) != value
        for key, value in expected_run.items()
    ):
        raise ValueError


def _fixed_pr786_signer_run(
    helper: ModuleType, executor: str, run_id: int, intent: dict[str, object]
) -> dict[str, object]:
    token = os.environ["GITHUB_TOKEN"]
    run = _object(helper._api_json(f"/repos/{REPOSITORY}/actions/runs/{run_id}", token)[0])
    expected_run = {
        "id": run_id,
        "run_attempt": 1,
        "head_sha": executor,
        "head_branch": _string(intent["auxiliary_ref"]).removeprefix("refs/heads/"),
        "event": "workflow_dispatch",
        "path": ".github/workflows/specfact.yml",
        "workflow_id": 204352514,
        "status": "completed",
        "conclusion": "success",
    }
    if any(type(run.get(key)) is not type(value) or run.get(key) != value for key, value in expected_run.items()):
        raise ValueError
    _fixed_pr786_run_repositories(run, _integer(intent["repository_id"]))
    _fixed_pr786_run_actors(run, intent)
    _fixed_pr786_run_history(helper, executor, expected_run)
    return run


def _fixed_pr786_checkpoints(
    helper: ModuleType, final: dict[str, object]
) -> tuple[dict[str, object], dict[str, object]]:
    message = _string(final.get("message"))
    suffix = re.search(
        r"\n\nSource-Commit: ([0-9a-f]{40})\nIntent: ([0-9a-f]{64})\nExecutor: ([0-9a-f]{40})\nRun: ([1-9][0-9]*)\nAttempt: 1\Z",
        message,
    )
    if suffix is None:
        raise ValueError
    source, intent_digest, executor, run_id_text = suffix.groups()
    run_id = int(run_id_text)
    executor_tree, allowed = _fixed_pr786_executor_tree(helper, executor)
    intent = _fixed_pr786_intent(helper, executor_tree, intent_digest)
    checkpoints = _fixed_pr786_sources(helper, intent, allowed, source, final)
    _fixed_pr786_outputs(helper, final, checkpoints, (intent_digest, executor, run_id))
    run = _fixed_pr786_signer_run(helper, executor, run_id, intent)
    return run, {
        "executor": executor,
        "intent_digest": "sha256:" + intent_digest,
        "source_commit": source,
        "checkpoint_count": len(checkpoints),
    }


def _fixed_pr786_copy_artifact(helper: ModuleType, run: dict[str, object]) -> tuple[dict[str, object], str]:
    token = os.environ["GITHUB_TOKEN"]
    run_id = _integer(run.get("id"))
    record = _object(helper._api_json(f"/repos/{REPOSITORY}/actions/runs/{run_id}/artifacts?per_page=100", token)[0])
    entries = record.get("artifacts")
    if (
        not isinstance(entries, list)
        or type(record.get("total_count")) is not int
        or record["total_count"] != len(entries)
        or len(entries) > 100
    ):
        raise ValueError
    name = f"fixed786-native36-copy-{run_id}-1-{run['head_sha']}"
    matches = [_object(entry) for entry in entries if _object(entry).get("name") == name]
    if len(matches) != 1:
        raise ValueError
    return matches[0], name


def _fixed_pr786_copy_association(artifact: dict[str, object], run: dict[str, object]) -> dict[str, object]:
    run_id = _integer(run.get("id"))
    association = _object(artifact.get("workflow_run"))
    expected = {
        "id": run_id,
        "repository_id": _object(run["repository"])["id"],
        "head_repository_id": _object(run["repository"])["id"],
        "head_sha": run["head_sha"],
        "head_branch": run["head_branch"],
    }
    if any(
        type(association.get(key)) is not type(value) or association.get(key) != value
        for key, value in expected.items()
    ):
        raise ValueError
    return association


def _fixed_pr786_copy_location(artifact_id: int) -> urllib.parse.SplitResult:
    token = os.environ["GITHUB_TOKEN"]
    # The API redirect carries a short-lived signed storage URL. Never forward the repository token.
    connection = http.client.HTTPSConnection("api.github.com", timeout=20)
    try:
        connection.request(
            "GET",
            f"/repos/{REPOSITORY}/actions/artifacts/{artifact_id}/zip",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "User-Agent": "specfact-fixed786",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        response = connection.getresponse()
        if response.status != 302:
            raise ValueError
        location = urllib.parse.urlsplit(_string(response.getheader("Location")))
    finally:
        connection.close()
    return location


def _fixed_pr786_copy_storage(location: urllib.parse.SplitResult) -> str:
    if (
        location.scheme != "https"
        or location.username
        or location.password
        or location.port not in (None, 443)
        or location.fragment
        or not location.hostname
        or not (
            location.hostname.endswith(".blob.core.windows.net")
            or location.hostname.endswith(".actions.githubusercontent.com")
        )
    ):
        raise ValueError
    return location.hostname


def _fixed_pr786_copy_archive(location: urllib.parse.SplitResult, size: int, digest: str) -> bytes:
    connection = http.client.HTTPSConnection(_fixed_pr786_copy_storage(location), timeout=20)
    try:
        connection.request(
            "GET",
            urllib.parse.urlunsplit(("", "", location.path, location.query, "")),
            headers={"User-Agent": "specfact-fixed786"},
        )
        response = connection.getresponse()
        if response.status != 200:
            raise ValueError
        archive = response.read(MAX_INPUT_BYTES + 1)
    finally:
        connection.close()
    if len(archive) != size or _digest(archive) != digest:
        raise ValueError
    return archive


def _fixed_pr786_copy_member(
    zipped: zipfile.ZipFile, info: zipfile.ZipInfo, expected: tuple[int, object], size: int, packet: Path
) -> None:
    length, expected_digest = expected
    mode = info.external_attr >> 16
    if (
        info.is_dir()
        or info.flag_bits & 1
        or info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
        or info.file_size != length
        or info.compress_size > size
        or stat.S_IFMT(mode) not in (0, stat.S_IFREG)
    ):
        raise ValueError
    with zipped.open(info) as stream:
        raw = stream.read(length + 1)
    if len(raw) != length or _digest(raw) != expected_digest or _regular_payload(packet / info.filename) != raw:
        raise ValueError


def _fixed_pr786_copy_members(
    archive: bytes, size: int, manifest: dict[str, object], packet: Path
) -> dict[str, object]:
    expected_members = {
        "requirements-evidence.json": (64255, manifest["report_digest"]),
        "requirements-evidence-plan.json": (31641, manifest["plan_report_digest"]),
        "requirements-proof.xml": (62923, manifest["junit_digest"]),
        "plan.json": (30303, manifest["plan_output_digest"]),
    }
    members: dict[str, object] = {}
    with zipfile.ZipFile(io.BytesIO(archive)) as zipped:
        infos = zipped.infolist()
        if len(infos) != 4 or {info.filename for info in infos} != set(expected_members):
            raise ValueError
        for info in infos:
            length, expected_digest = expected_members[info.filename]
            _fixed_pr786_copy_member(zipped, info, (length, expected_digest), size, packet)
            members[info.filename] = {"bytes": length, "digest": expected_digest}
    if packet.is_symlink() or {path.name for path in packet.iterdir()} != set(expected_members):
        raise ValueError
    return members


def _fixed_pr786_copy(
    helper: ModuleType, run: dict[str, object], manifest: dict[str, object], packet: Path
) -> dict[str, object]:
    artifact, name = _fixed_pr786_copy_artifact(helper, run)
    artifact_id = _integer(artifact.get("id"))
    size = _integer(artifact.get("size_in_bytes"))
    if artifact_id == manifest["artifact_id"] or artifact.get("expired") is not False or size > MAX_INPUT_BYTES:
        raise ValueError
    digest = _string(artifact.get("digest"), DIGEST_PATTERN)
    association = _fixed_pr786_copy_association(artifact, run)
    location = _fixed_pr786_copy_location(artifact_id)
    archive = _fixed_pr786_copy_archive(location, size, digest)
    members = _fixed_pr786_copy_members(archive, size, manifest, packet)
    return {
        "id": artifact_id,
        "name": name,
        "digest": digest,
        "size_in_bytes": size,
        "workflow_run": association,
        "members": members,
    }


def _fixed_pr786_verified_origin(arguments: argparse.Namespace) -> tuple[bytes, str]:
    if any(
        getattr(arguments, name, None) is None
        for name in ("origin", "origin_bundle", "workflow_sha", "trusted_authority")
    ):
        raise ValueError
    workflow_sha = _string(arguments.workflow_sha, OBJECT_PATTERN)
    if os.environ.get("GITHUB_WORKFLOW_SHA") != workflow_sha:
        raise ValueError
    origin_raw, bundle_raw = _regular_payload(arguments.origin), _regular_payload(arguments.origin_bundle)
    with tempfile.TemporaryDirectory(prefix="fixed786-origin-") as directory:
        origin_path, bundle_path = Path(directory) / "origin.json", Path(directory) / "origin.bundle.jsonl"
        origin_path.write_bytes(origin_raw)
        bundle_path.write_bytes(bundle_raw)
        subprocess.run(
            [
                "gh",
                "attestation",
                "verify",
                str(origin_path),
                "--bundle",
                str(bundle_path),
                "--repo",
                REPOSITORY,
                "--signer-workflow",
                REPOSITORY + "/" + WORKFLOW_PATH,
                "--signer-digest",
                workflow_sha,
                "--source-digest",
                workflow_sha,
                "--deny-self-hosted-runners",
            ],
            timeout=90,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    return origin_raw, workflow_sha


def _fixed_pr786_original_metadata(
    helper: ModuleType, arguments: argparse.Namespace, manifest: dict[str, object]
) -> dict[str, object]:
    token = os.environ["GITHUB_TOKEN"]
    original_run = _object(helper._api_json("/repos/nold-ai/.github/actions/runs/41715861806", token)[0])
    original_artifact = _object(helper._api_json("/repos/nold-ai/.github/actions/artifacts/13269307808", token)[0])
    source = _object(
        helper._api_json(f"/repos/{REPOSITORY}/commits/d77209f4b13c386e29391f93e1f1c58d7fd8622f", token)[0]
    )
    metadata = {"artifacts": [original_artifact], "source_commit": source}
    _validate_run(original_run, manifest, _FIXED_PR786_SCOPE)
    _validate_fixed_pr786_artifact(metadata, manifest)
    supplied_metadata = _read_json(arguments.red_artifacts)
    _validate_run(_read_json(arguments.red_run), manifest, _FIXED_PR786_SCOPE)
    _validate_fixed_pr786_artifact(supplied_metadata, manifest)
    if _read_json(arguments.red_run) != original_run or supplied_metadata != metadata:
        raise ValueError
    return {"original_run": original_run, "original_artifact": original_artifact, "source_commit": source}


def _fixed_pr786_origin_authority(origin: dict[str, object], authority: dict[str, object]) -> dict[str, object]:
    origin_authority = _object(origin.get("authority"))
    receipt, original_receipt = _object(authority["receipt"]), _object(origin_authority.get("receipt"))
    if {key: value for key, value in receipt.items() if key != "validated_at"} != {
        key: value for key, value in original_receipt.items() if key != "validated_at"
    } or authority["comment"] != origin_authority.get("comment"):
        raise ValueError
    validated = datetime.fromisoformat(_string(original_receipt.get("validated_at")).replace("Z", "+00:00"))
    now = datetime.now(UTC)
    if (
        validated.tzinfo is None
        or validated > now
        or validated >= datetime.fromisoformat(_string(receipt["expires_at"]).replace("Z", "+00:00"))
    ):
        raise ValueError
    return origin_authority


def _fixed_pr786_final_authority(
    arguments: argparse.Namespace, final: dict[str, object], authority: dict[str, object]
) -> None:
    receipt = _object(authority["receipt"])
    _, latest, fresh = _fixed_pr786_authority(arguments)
    if (
        latest != final
        or fresh["comment"] != authority["comment"]
        or _object(fresh["receipt"])["authority_digest"] != receipt["authority_digest"]
    ):
        raise ValueError


def _authenticate_fixed_pr786(arguments: argparse.Namespace) -> None:
    origin_raw, workflow_sha = _fixed_pr786_verified_origin(arguments)
    manifest_raw = _regular_payload(arguments.manifest)
    if hashlib.sha256(manifest_raw).hexdigest() != _FIXED_PR786_MANIFEST_SHA256:
        raise ValueError
    manifest = _object(json.loads(manifest_raw, object_pairs_hook=_pairs))
    _validate_fixed_pr786_manifest(manifest)
    helper, final, authority = _fixed_pr786_authority(arguments)
    run, signer = _fixed_pr786_checkpoints(helper, final)
    copy = _fixed_pr786_copy(helper, run, manifest, arguments.red_artifact_root)
    metadata = _fixed_pr786_original_metadata(helper, arguments, manifest)
    origin = _object(json.loads(origin_raw, object_pairs_hook=_pairs))
    origin_authority = _fixed_pr786_origin_authority(origin, authority)
    expected = {
        "schema_version": 1,
        "kind": "fixed-pr786-retained-member-origin",
        "repository": REPOSITORY,
        "head_commit": final["sha"],
        "head_tree": _object(final["tree"])["sha"],
        "workflow_sha": workflow_sha,
        "run_id": int(os.environ["GITHUB_RUN_ID"]),
        "run_attempt": int(os.environ["GITHUB_RUN_ATTEMPT"]),
        "manifest_digest": _digest(manifest_raw),
        "signer": signer,
        "copy": copy,
        **metadata,
        "authority": origin_authority,
    }
    if origin != expected:
        raise ValueError
    _fixed_pr786_final_authority(arguments, final, authority)


def _arguments(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.error = _argument_error
    for name in ("manifest", "event", "red-run", "red-artifacts", "red-artifact-root", "repo-root"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--cycle-base-ref", required=True)
    parser.add_argument("--final-ref", required=True)
    parser.add_argument("--trusted-provenance", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    for name in ("origin", "origin-bundle", "trusted-authority"):
        parser.add_argument(f"--{name}", type=Path)
    parser.add_argument("--workflow-sha")
    return parser.parse_args(argv)


def _main(argv: Sequence[str] | None = None) -> int:
    try:
        arguments = _arguments(argv)
        fixed_path = (
            arguments.repo_root.resolve()
            / "openspec/changes/security-dependencies-0-55-11-dev/requirements-proof/late-red-evidence.json"
        )
        if arguments.manifest.resolve() == fixed_path:
            _authenticate_fixed_pr786(arguments)
        _normalize(arguments)
    except Exception:
        sys.stderr.write("late-red-proof-invalid\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

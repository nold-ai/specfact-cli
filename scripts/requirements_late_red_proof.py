"""Normalize an exact authority-bound late review RED artifact."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
from collections.abc import Callable, Sequence
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
    ("red_commit", "22b2fa7bd763b18ada1bfd1a9ea482a624f34cca"),
    ("red_tree", "fd6a43314d221ee03f6bf476c737487a71aa3677"),
    ("run_id", 41082128288),
    ("run_attempt", 1),
    ("artifact_id", 12988969594),
    ("artifact_digest", "sha256:ae9f1bd8efb862d2b03f9c584cded897e1ac0d945a3b60265347670d21bcab79"),
    ("report_digest", "sha256:8e4f937211396d0859286e0aa7d4db4bfbe7feed720125c7ee9fff28cddf05fb"),
    ("plan_report_digest", "sha256:c3de795387a8b289ebf1d8a0b976c25102f5563b7b94a60423cfaccd0c291607"),
    ("junit_digest", "sha256:f20bfadc80b82843b79af71e9e466b30f84301031a5ade0ae45cf51df599cb5f"),
    ("mapping_digest", "sha256:caeca573ba8a7c69fad2c530d67e502f6a3a51c82c8d8e6f1659c4bcfe7b34d0"),
    ("plan_digest", "sha256:befd8204588ac5de083e48e62c480b23cbdecbf3b4a2006fdf0e2901a213ae0f"),
    ("executor_repository", "nold-ai/.github"),
    ("executor_commit", "7b6b5fc1af7b57c2eb5a3546b7578a81175e4dfa"),
    ("executor_tree", "3967631c545b5d6ad9bd1132d635cb5b39b3dd78"),
    ("executor_head_branch", "codex/dev786-original-native-34"),
    ("executor_workflow_path", ".github/workflows/native-materialization-preflight.yml"),
    ("executor_workflow_name", "Native materialization development preflight 34"),
    ("executor_event", "create"),
    ("executor_conclusion", "success"),
    ("artifact_repository", "nold-ai/.github"),
    ("artifact_name", "original-execution-packet-41082128288-1"),
    ("artifact_member_prefix", "original15-4e811f75e0e79cf04ba66a15-export"),
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
            "red_commit": "22b2fa7bd763b18ada1bfd1a9ea482a624f34cca",
            "red_tree": "fd6a43314d221ee03f6bf476c737487a71aa3677",
            "executor_repository": "nold-ai/.github",
            "executor_commit": "7b6b5fc1af7b57c2eb5a3546b7578a81175e4dfa",
            "executor_tree": "3967631c545b5d6ad9bd1132d635cb5b39b3dd78",
            "executor_head_branch": "codex/dev786-original-native-34",
            "executor_workflow_path": ".github/workflows/native-materialization-preflight.yml",
            "executor_workflow_name": "Native materialization development preflight 34",
            "executor_event": "create",
            "executor_conclusion": "success",
            "run_id": 41082128288,
            "run_attempt": 1,
        }
        expected_run = {
            "id": 41082128288,
            "run_attempt": 1,
            "workflow_id": 396761484,
            "head_sha": "7b6b5fc1af7b57c2eb5a3546b7578a81175e4dfa",
            "head_branch": "codex/dev786-original-native-34",
            "event": "create",
            "status": "completed",
            "conclusion": "success",
            "name": "Native materialization development preflight 34",
            "path": ".github/workflows/native-materialization-preflight.yml",
        }
        repository = _object(run.get("repository"))
        head_repository = _object(run.get("head_repository"))
        expected_repository = {"id": 1110267669, "full_name": "nold-ai/.github", "private": False, "fork": False}
        expected_owner = {"id": 225190663, "login": "nold-ai", "type": "Organization"}
        expected_actor = {"id": 39115308, "login": "djm81", "type": "User"}
        expected_commit = {
            "id": "7b6b5fc1af7b57c2eb5a3546b7578a81175e4dfa",
            "tree_id": "3967631c545b5d6ad9bd1132d635cb5b39b3dd78",
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


def _validate_artifact(metadata: dict[str, object], manifest: dict[str, object]) -> None:
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
    with tempfile.TemporaryDirectory(prefix=".late-red-", dir=output.parent) as directory:
        candidate = Path(directory) / output.name
        candidate_xml = candidate.with_suffix(".xml")
        candidate.write_text(json.dumps(normalized, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
        candidate_xml.write_bytes(junit_payload)
        bind(candidate, repo_root, base_ref=manifest["cycle_base_commit"], junit_path=candidate_xml)
        if validate(candidate, repo_root, base_ref=manifest["cycle_base_commit"], final_ref=final):
            raise ValueError
        os.replace(candidate_xml, output_xml)
        os.replace(candidate, output)


def _arguments(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.error = _argument_error
    for name in ("manifest", "event", "red-run", "red-artifacts", "red-artifact-root", "repo-root"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--cycle-base-ref", required=True)
    parser.add_argument("--final-ref", required=True)
    parser.add_argument("--trusted-provenance", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def _main(argv: Sequence[str] | None = None) -> int:
    try:
        _normalize(_arguments(argv))
    except Exception:
        sys.stderr.write("late-red-proof-invalid\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

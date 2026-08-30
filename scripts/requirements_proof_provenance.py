"""Validate Git-bound provenance before forwarding a red proof to reconciliation."""

from __future__ import annotations

import argparse
import ast
import configparser
import hashlib
import importlib.util
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import tomllib
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from enum import Enum, auto
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
PYTEST_CONFIGURATION_PATHS = {
    ".pytest.ini",
    ".pytest.toml",
    "pyproject.toml",
    "pytest.ini",
    "pytest.toml",
    "setup.cfg",
    "tox.ini",
}
PYTHON_MODULE_PATTERN = re.compile(r"^[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*$")
EXTERNAL_AMENDMENT_KIND = "externally-approved-amendment-bootstrap"
EXTERNAL_AMENDMENT_COMMENT_ID = 5464938148
EXTERNAL_AMENDMENT_RED_RUN_ID = 33274773197
EXTERNAL_AMENDMENT_GREEN_RUN_ID = 33270463697
EXTERNAL_AMENDMENT_REPOSITORY = "nold-ai/specfact-cli"
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


@dataclass(frozen=True)
class BindingContext:
    """Source and selector inputs used to add immutable proof bindings."""

    repo_root: Path
    source_ref: str
    selector_paths: Sequence[str]
    provenance_base: str


@dataclass
class ImportNamespaceAliases:
    """Aliases that can expose one dynamic module loader."""

    loader_name: str
    owners: set[str]
    mappings: set[str]
    mapping_methods: set[str]


@dataclass
class DynamicImportAliases:
    """Fixed-point state for direct and namespace-backed import loaders."""

    direct_loaders: set[str]
    importlib: ImportNamespaceAliases
    builtins: ImportNamespaceAliases

    def _sizes(self) -> tuple[int, ...]:
        """Return the monotonic state size used to detect convergence."""
        return (
            len(self.direct_loaders),
            len(self.importlib.owners),
            len(self.importlib.mappings),
            len(self.importlib.mapping_methods),
            len(self.builtins.owners),
            len(self.builtins.mappings),
            len(self.builtins.mapping_methods),
        )


@dataclass(frozen=True)
class ExternalAmendmentPaths:
    """Live GitHub inputs and validator outputs for the approved exception."""

    comment: Path
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
    CycleBasePaths: Callable[[Path, Path, Path, Path], object]
    CycleBaseContext: Callable[[str, str, str, int, str], object]

    validated_cycle_base: Callable[..., _TrustedCycle | None]


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
            context.repository == EXTERNAL_AMENDMENT_REPOSITORY,
            context.pull_request == EXTERNAL_AMENDMENT_PULL_REQUEST,
            context.head_branch == EXTERNAL_AMENDMENT_BRANCH,
            hint.get("repository") == context.repository,
            hint.get("pull_request") == context.pull_request,
            hint.get("head_branch") == context.head_branch,
        )
    )


def _external_hint_matches(hint: dict[str, object], context: CycleAuthorityContext) -> bool:
    """Restrict external capability routing to its approved red source."""
    return _external_locator_matches(hint, context) and hint.get("red_ref") == context.red_ref


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
        "fix-release-promotion-security-gates",
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
    return TrustedCycleAuthority(cast(str, values[0]), cast(str, values[1]), values[2], values[3], cast(str, values[4]))


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
        module.CycleBasePaths(run_path, artifacts_path, artifact_root, context.repo_root),
        module.CycleBaseContext(
            context.base_ref,
            context.final_ref,
            context.repository,
            context.pull_request,
            context.head_branch,
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


def _option_tokens(value: object) -> list[str]:
    """Normalize pytest string or TOML-array options without executing config code."""
    if isinstance(value, str):
        return shlex.split(value)
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return [token for item in cast(list[str], value) for token in shlex.split(item)]
    raise ValueError("prior-red-proof-invalid")


def _object_mapping(value: object) -> dict[str, object]:
    """Return a typed object mapping or an empty mapping for absent sections."""
    return cast(dict[str, object], value) if isinstance(value, dict) else {}


def _pytest_addopts(config_path: str, payload: str) -> list[str]:
    """Read addopts from each repository config syntax supported by pytest."""
    if config_path.endswith(".toml"):
        parsed = _object_mapping(tomllib.loads(payload))
        section = (
            _object_mapping(_object_mapping(_object_mapping(parsed.get("tool")).get("pytest")).get("ini_options"))
            if PurePosixPath(config_path).name == "pyproject.toml"
            else _object_mapping(parsed.get("pytest"))
        )
        value = section.get("addopts")
    else:
        parser = configparser.ConfigParser(interpolation=None)
        parser.read_string(payload)
        section_name = "tool:pytest" if PurePosixPath(config_path).name == "setup.cfg" else "pytest"
        value = parser.get(section_name, "addopts", fallback=None)
    return [] if value is None else _option_tokens(value)


def _plugin_option(options: Sequence[str], index: int) -> tuple[tuple[str, ...] | None, int]:
    """Parse one option and return an enabled plugin plus the next index."""
    option = options[index]
    if not option.startswith("-p"):
        return None, index + 1
    if option == "-p":
        plugin_index = index + 1
        if plugin_index >= len(options):
            raise ValueError("prior-red-proof-invalid")
        plugin = options[plugin_index]
        next_index = plugin_index + 1
    else:
        plugin = option[2:].removeprefix("=")
        next_index = index + 1
    if plugin.startswith("no:"):
        return None, next_index
    if PYTHON_MODULE_PATTERN.fullmatch(plugin) is None:
        raise ValueError("prior-red-proof-invalid")
    return tuple(plugin.split(".")), next_index


def _plugin_modules(options: Sequence[str]) -> set[tuple[str, ...]]:
    """Return exact enabled modules from pytest ``-p`` options."""
    modules: set[tuple[str, ...]] = set()
    index = 0
    while index < len(options):
        plugin, index = _plugin_option(options, index)
        if plugin is not None:
            modules.add(plugin)
    return modules


def _configured_pytest_plugin_paths(repo_root: Path, source_ref: str, config_paths: Sequence[str]) -> set[str]:
    """Return repository module paths loaded by literal pytest ``-p`` options."""
    modules: set[tuple[str, ...]] = set()
    for config_path in config_paths:
        result = _git(repo_root, "show", f"{source_ref}:{config_path}")
        if result.returncode == 0:
            modules.update(_plugin_modules(_pytest_addopts(config_path, result.stdout)))
    return {path for module_parts in modules for path in _python_module_paths(module_parts)}


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


def _definition_expression_children(node: ast.AST, scope_aliases: ScopeAliases | None = None) -> list[ast.AST] | None:
    """Return enclosing-scope expressions for one nested definition boundary."""
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
        return None
    if getattr(node, "name", None) == "pytest_plugins":
        raise ValueError("prior-red-proof-invalid")
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "__getattr__":
        raise ValueError("prior-red-proof-invalid")
    if isinstance(node, ast.ClassDef) and _class_body_can_bind_module_plugin(node, scope_aliases):
        raise ValueError("prior-red-proof-invalid")
    nested_body = {node.body} if isinstance(node, ast.Lambda) else set(node.body)
    return [child for child in ast.iter_child_nodes(node) if child not in nested_body]


def _import_binds_pytest_plugins(node: ast.AST) -> bool:
    """Return whether an import can create the active module global."""
    if isinstance(node, ast.Import):
        bound_names = {alias.asname or alias.name.split(".", maxsplit=1)[0] for alias in node.names}
        return "pytest_plugins" in bound_names
    if isinstance(node, ast.ImportFrom):
        bound_names = {alias.asname or alias.name for alias in node.names}
        return "pytest_plugins" in bound_names or "*" in bound_names
    return False


def _same_scope_nodes(statements: Sequence[ast.AST]) -> list[ast.AST]:
    """Return import-time nodes without descending into nested definition bodies."""
    discovered: list[ast.AST] = []
    pending: list[tuple[ast.AST, ast.AST | None]] = [(node, None) for node in reversed(statements)]
    while pending:
        current, parent = pending.pop()
        discovered.append(current)
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            nested_body = {current.body} if isinstance(current, ast.Lambda) else set(current.body)
            children = [child for child in ast.iter_child_nodes(current) if child not in nested_body]
        else:
            children = _class_import_time_children(current, parent or current)
        pending.extend((child, current) for child in reversed(children))
    return discovered


def _bound_names(target: ast.AST) -> set[str]:
    """Return names introduced by one assignment or iteration target."""
    if isinstance(target, ast.Name):
        return {target.id}
    return {child.id for child in ast.walk(target) if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store)}


def _pattern_bound_names(root: ast.pattern) -> set[str]:
    """Return names introduced by one match pattern."""
    names: set[str] = set()
    for pattern in ast.walk(root):
        if isinstance(pattern, (ast.MatchAs, ast.MatchStar)) and pattern.name is not None:
            names.add(pattern.name)
        elif isinstance(pattern, ast.MatchMapping) and pattern.rest is not None:
            names.add(pattern.rest)
    return names


def _pattern_value_capture_names(root: ast.pattern) -> set[str]:
    """Return captures that receive subject values rather than copied rest mappings."""
    names = _pattern_bound_names(root)
    for pattern in ast.walk(root):
        if isinstance(pattern, ast.MatchMapping) and pattern.rest is not None:
            names.discard(pattern.rest)
    return names


ScopeBinding = tuple[set[str], ast.AST | None]
ScopeAliases = tuple[set[str], set[str], set[str], set[str]]


class AliasAuthority(Enum):
    """Conservative authority state for one alias assignment."""

    AUTHORITY = auto()
    PROVEN_SAFE = auto()
    UNKNOWN = auto()


_UNRESOLVED_MAPPING_KEY = object()
_IMPORT_FACTORY_PREFIX = "__specfact_import_factory__:"
_BUILTINS_MAPPING_PREFIX = "__specfact_builtins_mapping__:"
_MODULE_MAPPING_PREFIX = "__specfact_module_mapping__:"
_NAMESPACE_MUTATORS = {"update", "setdefault", "__setitem__", "__ior__"}


def _starred_sequence_bindings(target: ast.Tuple | ast.List, value: ast.Tuple | ast.List) -> list[ScopeBinding] | None:
    """Correlate Python extended-unpacking targets with their source values."""
    starred_indexes = [index for index, item in enumerate(target.elts) if isinstance(item, ast.Starred)]
    if len(starred_indexes) != 1 or len(value.elts) < len(target.elts) - 1:
        return None
    starred_index = starred_indexes[0]
    suffix_count = len(target.elts) - starred_index - 1
    bindings = [
        binding
        for item, source in zip(target.elts[:starred_index], value.elts[:starred_index], strict=True)
        for binding in _target_bindings(item, source)
    ]
    starred_end = len(value.elts) - suffix_count
    starred_value = ast.List(elts=value.elts[starred_index:starred_end], ctx=ast.Load())
    bindings.extend(_target_bindings(target.elts[starred_index], starred_value))
    if suffix_count:
        bindings.extend(
            binding
            for item, source in zip(target.elts[-suffix_count:], value.elts[-suffix_count:], strict=True)
            for binding in _target_bindings(item, source)
        )
    return bindings


def _target_bindings(target: ast.AST, value: ast.AST | None) -> list[ScopeBinding]:
    """Pair destructuring targets with statically corresponding source values."""
    if isinstance(target, ast.Name):
        return [({target.id}, value)]
    if isinstance(target, ast.Starred):
        return _target_bindings(target.value, value)
    if isinstance(target, (ast.Tuple, ast.List)) and isinstance(value, (ast.Tuple, ast.List)):
        starred_bindings = _starred_sequence_bindings(target, value)
        if starred_bindings is not None:
            return starred_bindings
    if (
        isinstance(target, (ast.Tuple, ast.List))
        and isinstance(value, (ast.Tuple, ast.List))
        and len(target.elts) == len(value.elts)
    ):
        return [
            binding
            for item, source in zip(target.elts, value.elts, strict=True)
            for binding in _target_bindings(item, source)
        ]
    return [(_bound_names(target), value)]


def _assignment_bindings(node: ast.AST) -> list[ScopeBinding]:
    """Return position-preserving aliases introduced by one assignment."""
    if isinstance(node, ast.Assign):
        return [binding for target in node.targets for binding in _target_bindings(target, node.value)]
    if isinstance(node, (ast.AnnAssign, ast.NamedExpr)):
        return _target_bindings(node.target, node.value)
    return []


def _qualified_name(node: ast.AST | None) -> str | None:
    """Return one static dotted name without evaluating its expression."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _qualified_name(node.value)
        return f"{parent}.{node.attr}" if parent is not None else None
    return None


def _literal_callable_reference(node: ast.AST | None) -> ast.AST | None:
    """Unwrap literal ``__call__`` selection without evaluating an expression."""
    current = node
    while True:
        if isinstance(current, ast.Attribute) and current.attr == "__call__":
            current = current.value
            continue
        if (
            isinstance(current, ast.Call)
            and isinstance(current.func, ast.Name)
            and current.func.id == "getattr"
            and len(current.args) >= 2
            and isinstance(current.args[1], ast.Constant)
            and current.args[1].value == "__call__"
        ):
            current = current.args[0]
            continue
        return current


def _authority_marker(prefix: str, name: str) -> str:
    """Return one internal dynamic-authority marker."""
    return f"{prefix}{name}"


def _is_import_factory(name: str, dynamic_executors: set[str]) -> bool:
    """Return whether a name retains built-in import-factory authority."""
    return _authority_marker(_IMPORT_FACTORY_PREFIX, name) in dynamic_executors


def _is_builtins_mapping(node: ast.AST | None, dynamic_executors: set[str]) -> bool:
    """Return whether an expression exposes an imported builtins module mapping."""
    if isinstance(node, ast.Name):
        return node.id == "__builtins__" or _authority_marker(_BUILTINS_MAPPING_PREFIX, node.id) in dynamic_executors
    if isinstance(node, ast.Attribute) and node.attr == "__dict__":
        return _is_dynamic_executor_owner_reference(node.value, dynamic_executors)
    copied_source = _copied_mapping_source(node)
    if copied_source is not None:
        return _is_builtins_mapping(copied_source, dynamic_executors)
    if isinstance(node, ast.Dict):
        return _dict_unpacks_builtins(node, dynamic_executors)
    return _vars_exposes_builtins(node, dynamic_executors)


def _copied_mapping_source(node: ast.AST | None) -> ast.AST | None:
    """Return the source copied by a literal mapping-copy expression."""
    if isinstance(node, ast.Call) and not node.keywords:
        if isinstance(node.func, ast.Attribute) and node.func.attr == "copy" and not node.args:
            return node.func.value
        if isinstance(node.func, ast.Name) and node.func.id == "dict" and len(node.args) == 1:
            return node.args[0]
    return None


def _dict_unpacks_builtins(node: ast.Dict, dynamic_executors: set[str]) -> bool:
    """Return whether a literal mapping unpacks a builtins mapping."""
    pairs = zip(node.keys, node.values, strict=True)
    return any(key is None and _is_builtins_mapping(value, dynamic_executors) for key, value in pairs)


def _vars_exposes_builtins(node: ast.AST | None, dynamic_executors: set[str]) -> bool:
    """Return whether ``vars`` exposes a tracked builtins-module mapping."""
    return bool(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "vars"
        and node.args
        and _is_dynamic_executor_owner_reference(node.args[0], dynamic_executors)
    )


def _is_builtins_mapping_executor(node: ast.AST | None, dynamic_executors: set[str]) -> bool:
    """Return whether an imported builtins mapping is indexed for an executor."""
    subscript_executor = (
        isinstance(node, ast.Subscript)
        and _is_builtins_mapping(node.value, dynamic_executors)
        and (not isinstance(node.slice, ast.Constant) or node.slice.value in {"exec", "eval"})
    )
    accessor_owner, accessor_name = _mapping_accessor(node.func if isinstance(node, ast.Call) else None)
    method_executor = bool(
        isinstance(node, ast.Call)
        and accessor_name in {"get", "__getitem__", "setdefault", "pop"}
        and _is_builtins_mapping(accessor_owner, dynamic_executors)
        and node.args
        and (not isinstance(node.args[0], ast.Constant) or node.args[0].value in {"exec", "eval"})
    )
    return subscript_executor or method_executor


def _mapping_accessor(node: ast.AST | None) -> tuple[ast.AST | None, str | None]:
    """Return the owner and selected name for a direct or computed mapping accessor."""
    if isinstance(node, ast.Attribute):
        return node.value, node.attr
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "getattr"
        and len(node.args) >= 2
    ):
        attribute = node.args[1]
        return node.args[0], str(attribute.value) if isinstance(attribute, ast.Constant) else None
    return None, None


def _is_executor_attribute(node: ast.AST | None) -> bool:
    """Return whether an attribute access may invoke dynamic execution."""
    return isinstance(node, ast.Attribute) and node.attr in {"exec", "eval"}


def _is_imported_builtins_owner(node: ast.AST | None, dynamic_executors: set[str]) -> bool:
    """Return whether an expression imports the builtins module directly."""
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and _is_import_factory(node.func.id, dynamic_executors)
        and bool(node.args)
        and (not isinstance(node.args[0], ast.Constant) or node.args[0].value == "builtins")
    )


def _is_getattr_executor(node: ast.AST | None) -> bool:
    """Fail closed when ``getattr`` may select a dynamic executor."""
    if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "getattr"):
        return False
    if len(node.args) < 2:
        return False
    attribute = node.args[1]
    return not isinstance(attribute, ast.Constant) or attribute.value in {"exec", "eval"}


def _is_dynamic_executor_reference(node: ast.AST | None, dynamic_executors: set[str]) -> bool:
    """Return whether an expression statically names a built-in executor."""
    if isinstance(node, ast.Attribute) and node.attr == "__call__":
        return _is_dynamic_executor_reference(node.value, dynamic_executors)
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "getattr"
        and len(node.args) >= 2
        and isinstance(node.args[1], ast.Constant)
        and node.args[1].value == "__call__"
    ):
        return _is_dynamic_executor_reference(node.args[0], dynamic_executors)
    return (
        _qualified_name(node) in dynamic_executors
        or _is_builtins_mapping_executor(node, dynamic_executors)
        or _is_executor_attribute(node)
        or _is_getattr_executor(node)
    )


def _is_dynamic_executor_owner_reference(node: ast.AST | None, dynamic_executors: set[str]) -> bool:
    """Return whether an expression names a module that owns a tracked executor."""
    if _is_imported_builtins_owner(node, dynamic_executors):
        return True
    source_name = _qualified_name(node)
    return source_name is not None and any(
        f"{source_name}.{executor}" in dynamic_executors for executor in ("exec", "eval")
    )


def _is_zero_argument_call_to(node: ast.AST | None, names: set[str]) -> bool:
    """Return whether an expression calls one named factory without arguments."""
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in names
        and not node.args
        and not node.keywords
    )


def _namespace_mutator_references(
    node: ast.AST | None, factories: set[str], namespaces: set[str], namespace_mutators: set[str]
) -> set[str]:
    """Return namespace-mutator methods carried by one expression."""
    node = _literal_callable_reference(node)
    if isinstance(node, ast.Name):
        prefix = f"{node.id}."
        return {entry.removeprefix(prefix) for entry in namespace_mutators if entry.startswith(prefix)}
    source_name = _qualified_name(node)
    if source_name in namespace_mutators:
        return {source_name.rsplit(".", maxsplit=1)[-1]}
    if isinstance(node, ast.Attribute) and _is_namespace_reference(node.value, factories, namespaces):
        return {node.attr} if node.attr in _NAMESPACE_MUTATORS else set()
    return _getattr_namespace_mutator_references(node, factories, namespaces)


def _getattr_namespace_mutator_references(node: ast.AST | None, factories: set[str], namespaces: set[str]) -> set[str]:
    """Return namespace methods selected by one ``getattr`` expression."""
    if not (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "getattr"
        and len(node.args) >= 2
        and _is_namespace_reference(node.args[0], factories, namespaces)
    ):
        return set()
    attribute = node.args[1]
    if isinstance(attribute, ast.Constant) and attribute.value in _NAMESPACE_MUTATORS:
        return {str(attribute.value)}
    return {"*"}


def _propagate_scope_aliases(binding: ScopeBinding, aliases: ScopeAliases) -> None:
    """Extend alias groups from one import-time binding."""
    target_names, value = binding
    factories, namespaces, dynamic_executors, namespace_mutators = aliases
    source_name = _qualified_name(value)
    _propagate_namespace_aliases(target_names, value, source_name, factories, namespaces)
    _propagate_dynamic_aliases(target_names, value, source_name, dynamic_executors)
    _propagate_executor_owner_aliases(target_names, value, source_name, dynamic_executors)
    for method in _namespace_mutator_references(value, factories, namespaces, namespace_mutators):
        namespace_mutators.update(f"{target}.{method}" for target in target_names)
    if _is_zero_argument_call_to(value, factories):
        namespaces.update(target_names)


def _propagate_namespace_aliases(
    targets: set[str], value: ast.AST | None, source_name: str | None, factories: set[str], namespaces: set[str]
) -> None:
    """Propagate namespace factories and objects through one assignment."""
    if source_name in factories:
        factories.update(targets)
    if value is not None and _is_module_mapping_reference(value, factories):
        factories.update(_authority_marker(_MODULE_MAPPING_PREFIX, target) for target in targets)
    if (
        source_name in namespaces
        or (value is not None and _is_namespace_reference(value, factories, namespaces))
        or _contains_namespace_authority(value, factories, namespaces)
    ):
        namespaces.update(targets)


def _propagate_dynamic_aliases(
    targets: set[str], value: ast.AST | None, source_name: str | None, dynamic_executors: set[str]
) -> None:
    """Propagate dynamic executors, module mappings, and import factories."""
    if _is_dynamic_executor_reference(value, dynamic_executors):
        dynamic_executors.update(targets)
    if _is_builtins_mapping(value, dynamic_executors):
        dynamic_executors.update(_authority_marker(_BUILTINS_MAPPING_PREFIX, target) for target in targets)
    if source_name is not None and _is_import_factory(source_name, dynamic_executors):
        dynamic_executors.update(_authority_marker(_IMPORT_FACTORY_PREFIX, target) for target in targets)


def _propagate_executor_owner_aliases(
    target_names: set[str], value: ast.AST | None, source_name: str | None, dynamic_executors: set[str]
) -> None:
    """Propagate exec/eval members from one imported builtins owner."""
    if not _is_dynamic_executor_owner_reference(value, dynamic_executors):
        return
    if _is_imported_builtins_owner(value, dynamic_executors):
        owners = {"exec", "eval"}
    else:
        owners = {
            executor
            for executor in ("exec", "eval")
            if source_name is not None and f"{source_name}.{executor}" in dynamic_executors
        }
    dynamic_executors.update(f"{target}.{executor}" for target in target_names for executor in owners)


def _dynamic_executor_import_names(node: ast.AST) -> set[str]:
    """Return dynamic-executor names introduced by one builtins import."""
    if isinstance(node, ast.Import):
        owners = [alias.asname or alias.name for alias in node.names if alias.name == "builtins"]
        return {f"{owner}.{executor}" for owner in owners for executor in ("exec", "eval")}
    if isinstance(node, ast.ImportFrom) and node.module == "builtins":
        return {alias.asname or alias.name for alias in node.names if alias.name in {"exec", "eval"}}
    return set()


def _imported_dynamic_executors(statements: Sequence[ast.AST]) -> set[str]:
    """Return qualified or direct aliases imported from the builtins module."""
    executors = {"exec", "eval", _authority_marker(_IMPORT_FACTORY_PREFIX, "__import__")}
    for node in _same_scope_nodes(statements):
        executors.update(_dynamic_executor_import_names(node))
    return executors


def _qualified_namespace_mutators(node: ast.Import) -> set[str]:
    """Return qualified namespace-mutator imports."""
    module_methods = {"operator": "setitem", "builtins": "setattr"}
    return {
        f"{alias.asname or alias.name}.{module_methods[alias.name]}"
        for alias in node.names
        if alias.name in module_methods
    }


def _direct_namespace_mutators(node: ast.ImportFrom) -> set[str]:
    """Return directly imported namespace-mutator aliases."""
    module_methods = {"operator": "setitem", "builtins": "setattr"}
    imported_method = module_methods.get(node.module or "")
    if imported_method is None:
        return set()
    return {f"{alias.asname or alias.name}.{imported_method}" for alias in node.names if alias.name == imported_method}


def _namespace_mutator_import_names(node: ast.AST) -> set[str]:
    """Return namespace-mutator authority introduced by one import."""
    if isinstance(node, ast.Import):
        return _qualified_namespace_mutators(node)
    if isinstance(node, ast.ImportFrom):
        return _direct_namespace_mutators(node)
    return set()


def _imported_namespace_mutators(statements: Sequence[ast.AST]) -> set[str]:
    """Return aliases of the stdlib namespace setter used by reviewed proofs."""
    mutators = {"setattr.setattr"}
    for node in _same_scope_nodes(statements):
        mutators.update(_namespace_mutator_import_names(node))
    return mutators


def _imported_module_mappings(statements: Sequence[ast.AST]) -> set[str]:
    """Return authority markers for imported aliases of ``sys.modules``."""
    mappings: set[str] = set()
    for node in _same_scope_nodes(statements):
        if isinstance(node, ast.Import):
            mappings.update(
                _authority_marker(_MODULE_MAPPING_PREFIX, f"{alias.asname or alias.name}.modules")
                for alias in node.names
                if alias.name == "sys"
            )
        elif isinstance(node, ast.ImportFrom) and node.module == "sys":
            mappings.update(
                _authority_marker(_MODULE_MAPPING_PREFIX, alias.asname or alias.name)
                for alias in node.names
                if alias.name == "modules"
            )
    return mappings


def _scope_aliases(statements: Sequence[ast.AST], namespace_builtins: set[str]) -> ScopeAliases:
    """Resolve namespace factories, namespace objects, and dynamic-execution aliases."""
    factories = set(namespace_builtins)
    factories.update(_imported_module_mappings(statements))
    namespaces: set[str] = set()
    dynamic_executors = _imported_dynamic_executors(statements)
    namespace_mutators = _imported_namespace_mutators(statements)
    assignments = [binding for node in _same_scope_nodes(statements) for binding in _assignment_bindings(node)]
    changed = True
    while changed:
        before = (len(factories), len(namespaces), len(dynamic_executors), len(namespace_mutators))
        for binding in assignments:
            _propagate_scope_aliases(binding, (factories, namespaces, dynamic_executors, namespace_mutators))
        changed = before != (len(factories), len(namespaces), len(dynamic_executors), len(namespace_mutators))
    return factories, namespaces, dynamic_executors, namespace_mutators


def _is_namespace_mapping_view(node: ast.AST, factories: set[str], namespaces: set[str]) -> bool:
    """Return whether an expression exposes a tracked namespace mapping."""
    if isinstance(node, ast.Attribute) and node.attr == "__dict__":
        return _is_namespace_reference(node.value, factories, namespaces)
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "vars"
        and len(node.args) == 1
        and not node.keywords
        and _is_namespace_reference(node.args[0], factories, namespaces)
    )


def _is_namespace_reference(node: ast.AST, factories: set[str], namespaces: set[str]) -> bool:
    """Return whether an expression resolves to the active module namespace."""
    if isinstance(node, ast.Name):
        return node.id in namespaces
    if _is_current_module_lookup(node, factories) or _is_namespace_mapping_view(node, factories, namespaces):
        return True
    if isinstance(node, ast.Subscript):
        return _is_namespace_reference(node.value, factories, namespaces)
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in factories
        and not node.args
        and not node.keywords
    )


def _is_module_mapping_reference(node: ast.AST, factories: set[str]) -> bool:
    """Return whether an expression retains ``sys.modules`` mapping authority."""
    name = _qualified_name(node)
    return name == "sys.modules" or (name is not None and _authority_marker(_MODULE_MAPPING_PREFIX, name) in factories)


def _is_current_module_lookup(node: ast.AST, factories: set[str]) -> bool:
    """Return whether a sys.modules lookup can select the executing module."""
    if isinstance(node, ast.Subscript) and _is_module_mapping_reference(node.value, factories):
        key = node.slice
    elif (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"get", "__getitem__", "setdefault"}
        and _is_module_mapping_reference(node.func.value, factories)
        and node.args
    ):
        key = node.args[0]
    else:
        return False
    return (isinstance(key, ast.Name) and key.id == "__name__") or not isinstance(key, ast.Constant)


def _contains_namespace_authority(node: ast.AST | None, factories: set[str], namespaces: set[str]) -> bool:
    """Return whether an expression contains a tracked namespace value."""
    return node is not None and any(
        child is not node and _is_namespace_reference(child, factories, namespaces)
        for child in _same_scope_nodes([node])
    )


def _is_namespace_plugin_subscript(node: ast.AST, factories: set[str], namespaces: set[str]) -> bool:
    """Return whether a module-namespace write targets ``pytest_plugins``."""
    return (
        isinstance(node, ast.Subscript)
        and isinstance(node.ctx, (ast.Store, ast.Del))
        and (not isinstance(node.slice, ast.Constant) or node.slice.value == "pytest_plugins")
        and _is_namespace_reference(node.value, factories, namespaces)
    )


def _is_namespace_plugin_attribute(node: ast.AST, factories: set[str], namespaces: set[str]) -> bool:
    """Return whether an unresolved attribute write can target the plugin global."""
    del factories, namespaces
    return (
        isinstance(node, ast.Attribute) and isinstance(node.ctx, (ast.Store, ast.Del)) and node.attr == "pytest_plugins"
    )


def _setattr_can_bind_plugin(node: ast.Call, factories: set[str], namespaces: set[str]) -> bool:
    """Return whether setattr can create the current module plugin attribute."""
    if any(isinstance(argument, ast.Starred) for argument in node.args):
        return True
    bound_to_namespace = isinstance(node.func, ast.Attribute) and _is_namespace_reference(
        node.func.value, factories, namespaces
    )
    namespace_index, attribute_index = (None, 0) if bound_to_namespace else (0, 1)
    if len(node.args) <= attribute_index:
        return False
    if namespace_index is not None and not _is_namespace_reference(node.args[namespace_index], factories, namespaces):
        return False
    attribute = node.args[attribute_index]
    return not isinstance(attribute, ast.Constant) or attribute.value == "pytest_plugins"


def _mapping_can_bind_plugin(node: ast.AST) -> bool:
    """Return whether an update mapping can contain the plugin global."""
    if not isinstance(node, ast.Dict):
        return True
    return any(not isinstance(key, ast.Constant) or key.value == "pytest_plugins" for key in node.keys)


def _key_mutator_can_bind_plugin(node: ast.Call) -> bool:
    """Return whether a key-based namespace mutation can bind the plugin global."""
    if any(isinstance(argument, ast.Starred) for argument in node.args):
        return True
    external_setter = len(node.args) >= 3
    key_index = 1 if external_setter else 0
    key = node.args[key_index] if len(node.args) > key_index else None
    return key is not None and (not isinstance(key, ast.Constant) or key.value == "pytest_plugins")


def _update_mutator_can_bind_plugin(node: ast.Call) -> bool:
    """Return whether an update-style namespace mutation can bind the plugin global."""
    has_plugin_keyword = any(keyword.arg in {None, "pytest_plugins"} for keyword in node.keywords)
    return has_plugin_keyword or any(_mapping_can_bind_plugin(argument) for argument in node.args)


def _namespace_mutator_names(
    node: ast.Call, factories: set[str], namespaces: set[str], namespace_mutators: set[str]
) -> set[str]:
    """Return invoked namespace methods, using ``*`` for an unresolved method name."""
    if isinstance(node.func, ast.Name):
        return _namespace_mutator_references(node.func, factories, namespaces, namespace_mutators)
    carried_mutators = _namespace_mutator_references(node.func, factories, namespaces, namespace_mutators)
    if carried_mutators:
        return carried_mutators
    computed_mutators = _computed_setter_references(node.func)
    if computed_mutators and node.args and _is_namespace_reference(node.args[0], factories, namespaces):
        return computed_mutators
    external = _external_namespace_mutator(node, factories, namespaces)
    if external:
        return external
    return _computed_namespace_method(node.func, factories, namespaces)


def _external_namespace_mutator(node: ast.Call, factories: set[str], namespaces: set[str]) -> set[str]:
    """Return a direct external setter or namespace-bound method."""
    operation = node.func
    if not isinstance(operation, ast.Attribute):
        return set()
    has_namespace_argument = any(isinstance(argument, ast.Starred) for argument in node.args) or bool(
        node.args and _is_namespace_reference(node.args[0], factories, namespaces)
    )
    if operation.attr in {"setattr", "__setattr__", "setitem", "__setitem__"} and has_namespace_argument:
        return {operation.attr}
    return {operation.attr} if _is_namespace_reference(operation.value, factories, namespaces) else set()


def _computed_namespace_method(getter: ast.AST, factories: set[str], namespaces: set[str]) -> set[str]:
    """Return a namespace method selected through a literal or computed ``getattr``."""
    if not (
        isinstance(getter, ast.Call)
        and isinstance(getter.func, ast.Name)
        and getter.func.id == "getattr"
        and len(getter.args) >= 2
        and _is_namespace_reference(getter.args[0], factories, namespaces)
    ):
        return set()
    attribute = getter.args[1]
    return {str(attribute.value)} if isinstance(attribute, ast.Constant) else {"*"}


def _computed_setter_references(node: ast.AST | None) -> set[str]:
    """Return setter names selected through ``getattr`` or mapping lookup."""
    node = _literal_callable_reference(node)
    selected: ast.AST | None = None
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "getattr"
        and len(node.args) >= 2
    ):
        selected = node.args[1]
    elif isinstance(node, ast.Subscript):
        selected = node.slice
    if not isinstance(selected, ast.Constant):
        return set()
    name = str(selected.value)
    return {name} if name in {"setattr", "__setattr__", "setitem", "__setitem__"} else set()


def _is_namespace_plugin_mutator(
    node: ast.AST, factories: set[str], namespaces: set[str], namespace_mutators: set[str]
) -> bool:
    """Return whether an import-time call can create the plugin global."""
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "exec":
        return True
    if not isinstance(node, ast.Call):
        return False
    mutator_names = _namespace_mutator_names(node, factories, namespaces, namespace_mutators)
    if not mutator_names:
        return False
    if mutator_names & {"setattr", "__setattr__"} and _setattr_can_bind_plugin(node, factories, namespaces):
        return True
    if "*" in mutator_names:
        return True
    if mutator_names & {"setitem", "__setitem__", "setdefault"} and _key_mutator_can_bind_plugin(node):
        return True
    return bool(mutator_names & {"update", "__ior__"}) and _update_mutator_can_bind_plugin(node)


def _is_namespace_plugin_augmented_union(node: ast.AST, factories: set[str], namespaces: set[str]) -> bool:
    """Return whether ``|=`` can add the plugin global through a namespace alias."""
    return (
        isinstance(node, ast.AugAssign)
        and isinstance(node.op, ast.BitOr)
        and _is_namespace_reference(node.target, factories, namespaces)
        and _mapping_can_bind_plugin(node.value)
    )


def _is_namespace_plugin_binding_operation(
    node: ast.AST, factories: set[str], namespaces: set[str], namespace_mutators: set[str]
) -> bool:
    """Return whether an operation can bind the plugin through a module namespace."""
    return (
        _is_namespace_plugin_subscript(node, factories, namespaces)
        or _is_namespace_plugin_attribute(node, factories, namespaces)
        or _is_namespace_plugin_mutator(node, factories, namespaces, namespace_mutators)
        or _is_namespace_plugin_augmented_union(node, factories, namespaces)
    )


def _is_global_namespace_plugin_operation(
    node: ast.AST,
    factories: set[str],
    namespaces: set[str],
    dynamic_executors: set[str],
    namespace_mutators: set[str],
) -> bool:
    """Return whether a class-body operation can mutate the containing module."""
    global_declaration = isinstance(node, ast.Global) and "pytest_plugins" in node.names
    dynamic_execution = isinstance(node, ast.Call) and _is_dynamic_executor_reference(node.func, dynamic_executors)
    return (
        global_declaration
        or dynamic_execution
        or _is_namespace_plugin_binding_operation(node, factories, namespaces, namespace_mutators)
    )


def _copy_scope_aliases(aliases: ScopeAliases) -> ScopeAliases:
    """Return mutable copies for one nested import-time binding scope."""
    return tuple(set(group) for group in aliases)  # type: ignore[return-value]


def _iterated_values(node: ast.AST) -> tuple[list[ast.AST], bool]:
    """Return statically iterable values and whether their source is indirect."""
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return list(node.elts), False
    return [node], True


def _propagate_nested_aliases(target_names: set[str], value: ast.AST, aliases: ScopeAliases) -> None:
    """Conservatively bind a target from a context-manager or opaque iterable."""
    factories, namespaces, dynamic_executors, namespace_mutators = aliases
    value_nodes = _same_scope_nodes([value])
    if any(_is_namespace_reference(child, factories, namespaces) for child in value_nodes):
        namespaces.update(target_names)
    if any(isinstance(child, ast.Name) and child.id in factories for child in value_nodes):
        factories.update(target_names)
    if any(_is_dynamic_executor_reference(child, dynamic_executors) for child in value_nodes):
        dynamic_executors.update(target_names)
    for child in value_nodes:
        for method in _namespace_mutator_references(child, factories, namespaces, namespace_mutators):
            namespace_mutators.update(f"{target}.{method}" for target in target_names)


def _bind_compound_target(target: ast.AST, value: ast.AST, aliases: ScopeAliases, *, indirect: bool) -> None:
    """Propagate position-preserving aliases into one nested binding scope."""
    for binding in _target_bindings(target, value):
        _propagate_scope_aliases(binding, aliases)
    if indirect:
        _propagate_nested_aliases(_bound_names(target), value, aliases)


def _sequence_pattern_bindings(pattern: ast.MatchSequence, value: ast.Tuple | ast.List) -> list[ScopeBinding]:
    """Return position-preserving sequence captures when statically resolvable."""
    return [
        binding
        for child, source in zip(pattern.patterns, value.elts, strict=True)
        for binding in _match_pattern_bindings(child, source)
    ]


def _resolved_mapping_bindings(
    pattern: ast.MatchMapping, value: ast.Dict, pattern_keys: list[object], value_keys: list[object]
) -> list[ScopeBinding]:
    """Return captures correlated through fully resolved literal mapping keys."""
    bindings: list[ScopeBinding] = []
    for key, child in zip(pattern_keys, pattern.patterns, strict=True):
        matching_values = [
            source for source_key, source in zip(value_keys, value.values, strict=True) if source_key == key
        ]
        if matching_values:
            bindings.extend(_match_pattern_bindings(child, matching_values[-1]))
    return bindings


def _mapping_pattern_bindings(pattern: ast.pattern, value: ast.AST) -> list[ScopeBinding] | None:
    """Return conservative mapping captures when both AST nodes are mappings."""
    if not isinstance(pattern, ast.MatchMapping):
        return None
    mapping_value = value if isinstance(value, ast.Dict) else _dict_call_mapping(value)
    if mapping_value is None:
        capture_names = _pattern_value_capture_names(pattern)
        if not capture_names:
            return []
        unresolved_namespace = ast.Call(func=ast.Name(id="globals", ctx=ast.Load()), args=[], keywords=[])
        return [(capture_names, unresolved_namespace)]
    pattern_keys = [_literal_mapping_key(key) for key in pattern.keys]
    value_keys = [_literal_mapping_key(key) for key in mapping_value.keys]
    resolved = all(key is not _UNRESOLVED_MAPPING_KEY for key in [*pattern_keys, *value_keys])
    if resolved:
        return _resolved_mapping_bindings(pattern, mapping_value, pattern_keys, value_keys)
    capture_names = _pattern_value_capture_names(pattern)
    if not capture_names:
        return []
    return [(capture_names, candidate) for candidate in _mapping_value_candidates(mapping_value)]


def _dict_call_mapping(node: ast.AST) -> ast.Dict | None:
    """Return the statically correlated mapping for a simple ``dict`` call."""
    if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "dict"):
        return None
    if len(node.args) > 1 or any(keyword.arg is None for keyword in node.keywords):
        return None
    positional_entries = _dict_positional_entries(node.args)
    if positional_entries is None:
        return None
    keys, values = positional_entries
    keys.extend(ast.Constant(keyword.arg) for keyword in node.keywords)
    values.extend(keyword.value for keyword in node.keywords)
    return ast.Dict(keys=keys, values=values)


def _dict_positional_entries(args: list[ast.expr]) -> tuple[list[ast.expr | None], list[ast.expr]] | None:
    """Return keys and values from zero or one static ``dict`` argument."""
    if not args:
        return [], []
    positional = args[0]
    if isinstance(positional, ast.Dict):
        return list(positional.keys), list(positional.values)
    if not isinstance(positional, (ast.List, ast.Tuple)):
        return None
    pairs = [_dict_pair_entries(pair) for pair in positional.elts]
    if any(pair is None for pair in pairs):
        return None
    typed_pairs = [pair for pair in pairs if pair is not None]
    return [pair[0] for pair in typed_pairs], [pair[1] for pair in typed_pairs]


def _dict_pair_entries(node: ast.expr) -> tuple[ast.expr, ast.expr] | None:
    """Return one static key/value pair accepted by ``dict``."""
    return (node.elts[0], node.elts[1]) if isinstance(node, (ast.List, ast.Tuple)) and len(node.elts) == 2 else None


def _match_pattern_bindings(pattern: ast.pattern, value: ast.AST) -> list[ScopeBinding]:
    """Pair match captures with statically corresponding subject values."""
    if isinstance(pattern, (ast.MatchAs, ast.MatchStar)) and pattern.name is not None:
        return [({pattern.name}, value)]
    if (
        isinstance(pattern, ast.MatchSequence)
        and isinstance(value, (ast.Tuple, ast.List))
        and len(pattern.patterns) == len(value.elts)
    ):
        return _sequence_pattern_bindings(pattern, value)
    mapping_bindings = _mapping_pattern_bindings(pattern, value)
    return mapping_bindings if mapping_bindings is not None else [(_pattern_bound_names(pattern), value)]


def _literal_mapping_key(node: ast.AST | None) -> object:
    """Return a comparable literal mapping key, or an unresolved sentinel."""
    if node is None:
        return _UNRESOLVED_MAPPING_KEY
    try:
        value = ast.literal_eval(node)
        hash(value)
    except (ValueError, TypeError):
        return _UNRESOLVED_MAPPING_KEY
    return value


def _mapping_value_candidates(node: ast.Dict) -> list[ast.AST]:
    """Return values that an unresolved literal mapping pattern may capture."""
    candidates: list[ast.AST] = []
    pending = list(node.values)
    while pending:
        value = pending.pop()
        candidates.append(value)
        if isinstance(value, ast.Dict):
            pending.extend(value.values)
    return candidates


BindingRegion = tuple[ScopeAliases, list[ast.AST]]


def _loop_binding_region(node: ast.For | ast.AsyncFor, aliases: ScopeAliases) -> BindingRegion:
    """Return one loop body with its iteration aliases."""
    local = _copy_scope_aliases(aliases)
    values, indirect = _iterated_values(node.iter)
    for value in values:
        _bind_compound_target(node.target, value, local, indirect=indirect)
    return local, [*node.body, *node.orelse]


def _with_binding_region(node: ast.With | ast.AsyncWith, aliases: ScopeAliases) -> BindingRegion:
    """Return one context body with its optional binding aliases."""
    local = _copy_scope_aliases(aliases)
    for item in node.items:
        if item.optional_vars is not None:
            _bind_compound_target(item.optional_vars, item.context_expr, local, indirect=True)
    return local, list(node.body)


def _comprehension_binding_region(
    node: ast.ListComp | ast.SetComp | ast.DictComp, aliases: ScopeAliases
) -> BindingRegion:
    """Return one eager comprehension body with scoped iteration aliases."""
    local = _copy_scope_aliases(aliases)
    for generator in node.generators:
        values, indirect = _iterated_values(generator.iter)
        for value in values:
            _bind_compound_target(generator.target, value, local, indirect=indirect)
    result_nodes = [node.key, node.value] if isinstance(node, ast.DictComp) else [node.elt]
    conditions = [condition for generator in node.generators for condition in generator.ifs]
    return local, [*result_nodes, *conditions]


def _match_binding_regions(node: ast.Match, aliases: ScopeAliases) -> list[BindingRegion]:
    """Return match-case bodies with position-preserving capture aliases."""
    regions: list[BindingRegion] = []
    for case in node.cases:
        local = _copy_scope_aliases(aliases)
        for binding in _match_pattern_bindings(case.pattern, node.subject):
            _propagate_scope_aliases(binding, local)
        case_nodes = [*([case.guard] if case.guard is not None else []), *case.body]
        regions.append((local, case_nodes))
    return regions


def _compound_binding_regions(node: ast.AST, aliases: ScopeAliases) -> list[BindingRegion]:
    """Return nested regions with aliases created by compound bindings."""
    if isinstance(node, (ast.For, ast.AsyncFor)):
        return [_loop_binding_region(node, aliases)]
    if isinstance(node, (ast.With, ast.AsyncWith)):
        return [_with_binding_region(node, aliases)]
    if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp)):
        return [_comprehension_binding_region(node, aliases)]
    if isinstance(node, ast.Match):
        return _match_binding_regions(node, aliases)
    return []


def _aliases_with_prior_compound_bindings(
    statements: Sequence[ast.AST], node: ast.AST, aliases: ScopeAliases
) -> ScopeAliases:
    """Merge aliases from earlier compound targets that persist in this scope."""
    merged = _copy_scope_aliases(aliases)
    factories, namespaces, dynamic_executors, namespace_mutators = merged
    for statement in statements:
        if _node_position(statement) >= _node_position(node):
            continue
        for local_aliases, _ in _compound_binding_regions(statement, merged):
            local_factories, local_namespaces, local_executors, local_mutators = local_aliases
            factories.update(local_factories)
            namespaces.update(local_namespaces)
            dynamic_executors.update(local_executors)
            namespace_mutators.update(local_mutators)
    return merged


def _direct_indirect_plugin_binding(node: ast.AST, aliases: ScopeAliases) -> bool:
    """Return whether one operation directly creates the module plugin binding."""
    factories, namespaces, dynamic_executors, namespace_mutators = aliases
    pattern_binding = (isinstance(node, (ast.MatchAs, ast.MatchStar)) and node.name == "pytest_plugins") or (
        isinstance(node, ast.MatchMapping) and node.rest == "pytest_plugins"
    )
    name_binding = (
        isinstance(node, ast.Name) and node.id == "pytest_plugins" and isinstance(node.ctx, (ast.Store, ast.Del))
    )
    dynamic_execution = isinstance(node, ast.Call) and _is_dynamic_executor_reference(node.func, dynamic_executors)
    return (
        pattern_binding
        or name_binding
        or dynamic_execution
        or _is_namespace_plugin_binding_operation(node, factories, namespaces, namespace_mutators)
    )


def _compound_binding_can_bind_plugin(
    node: ast.AST, aliases: ScopeAliases, *, class_scope: bool, _visited: set[int] | None = None
) -> bool:
    """Inspect operations inside one loop, context, comprehension, or match binding scope."""
    if not isinstance(
        node,
        (ast.For, ast.AsyncFor, ast.With, ast.AsyncWith, ast.ListComp, ast.SetComp, ast.DictComp, ast.Match),
    ):
        return False
    visited: set[int] = _visited if _visited is not None else set()
    for local_aliases, statements in _compound_binding_regions(node, aliases):
        local_factories, local_namespaces, local_executors, local_mutators = local_aliases
        for current in _same_scope_nodes(statements):
            if id(current) in visited:
                continue
            visited.add(id(current))
            direct_binding = (
                _is_global_namespace_plugin_operation(
                    current, local_factories, local_namespaces, local_executors, local_mutators
                )
                if class_scope
                else _direct_indirect_plugin_binding(current, local_aliases)
            )
            if direct_binding or _compound_binding_can_bind_plugin(
                current, local_aliases, class_scope=class_scope, _visited=visited
            ):
                return True
            if isinstance(current, ast.ClassDef) and _class_body_can_bind_module_plugin(current, local_aliases):
                return True
    return False


def _class_import_time_children(current: ast.AST, parent: ast.AST) -> list[ast.AST]:
    """Return class-body children that execute while the class is defined."""
    if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
        nested_body = {current.body} if isinstance(current, ast.Lambda) else set(current.body)
        return [child for child in ast.iter_child_nodes(current) if child not in nested_body]
    deferred_generator = (
        isinstance(current, ast.GeneratorExp)
        and isinstance(parent, (ast.Assign, ast.AnnAssign, ast.NamedExpr))
        and parent.value is current
    )
    if deferred_generator:
        assert isinstance(current, ast.GeneratorExp)
        return [current.generators[0].iter] if current.generators else []
    return list(ast.iter_child_nodes(current))


def _class_body_can_bind_module_plugin(node: ast.ClassDef, inherited_aliases: ScopeAliases | None = None) -> bool:
    """Inspect import-time class code without treating class locals as module globals."""
    factories, namespaces, dynamic_executors, namespace_mutators = _scope_aliases(node.body, {"globals"})
    if inherited_aliases is not None:
        inherited_factories, inherited_namespaces, inherited_executors, inherited_mutators = inherited_aliases
        factories.update(inherited_factories)
        namespaces.update(inherited_namespaces)
        dynamic_executors.update(inherited_executors)
        namespace_mutators.update(inherited_mutators)
    pending: list[tuple[ast.AST, ast.AST]] = [(child, node) for child in reversed(node.body)]
    while pending:
        current, parent = pending.pop()
        aliases = _aliases_with_prior_compound_bindings(
            node.body, current, (factories, namespaces, dynamic_executors, namespace_mutators)
        )
        current_factories, current_namespaces, current_executors, current_mutators = aliases
        direct_operation = _is_global_namespace_plugin_operation(
            current, current_factories, current_namespaces, current_executors, current_mutators
        )
        if (
            direct_operation and not _operation_uses_definitely_shadowed_alias(current, node.body, aliases)
        ) or _compound_binding_can_bind_plugin(current, aliases, class_scope=True):
            return True
        children = _class_import_time_children(current, parent)
        pending.extend((child, current) for child in reversed(children))
    return False


def _is_indirect_plugin_binding(
    node: ast.AST,
    factories: set[str],
    namespaces: set[str],
    dynamic_executors: set[str],
    namespace_mutators: set[str],
) -> bool:
    """Return whether an unresolved enclosing-scope operation binds the plugin global."""
    aliases = (factories, namespaces, dynamic_executors, namespace_mutators)
    return _direct_indirect_plugin_binding(node, aliases) or _compound_binding_can_bind_plugin(
        node, aliases, class_scope=False
    )


def _function_body_aliases(
    node: ast.FunctionDef | ast.AsyncFunctionDef, inherited_aliases: ScopeAliases
) -> ScopeAliases:
    """Return local aliases augmented by the enclosing module authority."""
    aliases = _scope_aliases(node.body, {"globals"})
    for target, inherited in zip(aliases, inherited_aliases, strict=True):
        target.update(inherited)
    return aliases


def _function_declares_global_plugin(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Return whether a local callable declares the module plugin name global."""
    return any(
        isinstance(current, ast.Global) and "pytest_plugins" in current.names
        for current in _same_scope_nodes(node.body)
    )


def _function_operation_can_bind_plugin(current: ast.AST, aliases: ScopeAliases, declares_global: bool) -> bool:
    """Return whether one function-body operation can bind the module plugin."""
    factories, namespaces, dynamic_executors, namespace_mutators = aliases
    global_assignment = (
        declares_global
        and isinstance(current, ast.Name)
        and current.id == "pytest_plugins"
        and isinstance(current.ctx, (ast.Store, ast.Del))
    )
    dynamic_execution = isinstance(current, ast.Call) and _is_dynamic_executor_reference(
        current.func, dynamic_executors
    )
    return (
        global_assignment
        or dynamic_execution
        or _is_namespace_plugin_binding_operation(current, factories, namespaces, namespace_mutators)
    )


def _function_body_can_bind_module_plugin(
    node: ast.FunctionDef | ast.AsyncFunctionDef, inherited_aliases: ScopeAliases
) -> bool:
    """Return whether calling one local function can create the module plugin binding."""
    aliases = _function_body_aliases(node, inherited_aliases)
    declares_global = _function_declares_global_plugin(node)
    return any(
        _function_operation_can_bind_plugin(current, aliases, declares_global)
        and not _operation_uses_definitely_shadowed_alias(current, node.body, aliases)
        for current in _same_scope_nodes(node.body)
    )


def _definition_can_bind_when_called(node: ast.AST, aliases: ScopeAliases) -> bool:
    """Return whether directly invoking one local definition can bind the plugin."""
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return _function_body_can_bind_module_plugin(node, aliases)
    if isinstance(node, ast.ClassDef):
        methods = (item for item in node.body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)))
        return any(_function_body_can_bind_module_plugin(method, aliases) for method in methods)
    return False


def _direct_local_binder_is_invoked(statements: Sequence[ast.AST], aliases: ScopeAliases) -> bool:
    """Return whether import-time code directly invokes a binding-capable local definition."""
    definitions = {
        node.name: node
        for node in statements
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }
    invoked = {
        node.func.id
        for node in _same_scope_nodes(statements)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    return any(
        name in invoked and _definition_can_bind_when_called(node, aliases) for name, node in definitions.items()
    )


def _node_position(node: ast.AST) -> tuple[int, int]:
    """Return a stable source-order position for one parsed node."""
    return getattr(node, "lineno", -1), getattr(node, "col_offset", -1)


def _latest_direct_binding(statements: Sequence[ast.AST], name: str, before: ast.AST) -> ast.AST | None:
    """Return the latest definite direct assignment to ``name`` before a node."""
    latest: ast.AST | None = None
    latest_position = (-1, -1)
    before_position = _node_position(before)
    for statement in statements:
        position = _node_position(statement)
        if position >= before_position:
            continue
        for target_names, value in _assignment_bindings(statement):
            if name in target_names and value is not None and position > latest_position:
                latest = value
                latest_position = position
    return latest


def _literal_value_is_proven_safe(value: ast.AST, aliases: ScopeAliases) -> bool:
    """Return whether an inert literal expression cannot carry runtime authority."""
    if isinstance(value, ast.Constant):
        return True
    if isinstance(value, (ast.Tuple, ast.List, ast.Set)):
        return all(_alias_authority_value(item, aliases) is AliasAuthority.PROVEN_SAFE for item in value.elts)
    if isinstance(value, ast.Dict):
        return all(
            key is not None
            and _alias_authority_value(key, aliases) is AliasAuthority.PROVEN_SAFE
            and _alias_authority_value(item, aliases) is AliasAuthority.PROVEN_SAFE
            for key, item in zip(value.keys, value.values, strict=True)
        )
    return False


def _lambda_is_proven_inert(value: ast.AST, aliases: ScopeAliases) -> bool:
    """Accept only a side-effect-free literal-returning lambda."""
    return isinstance(value, ast.Lambda) and _literal_value_is_proven_safe(value.body, aliases)


def _alias_authority_value(value: ast.AST, aliases: ScopeAliases) -> AliasAuthority:
    """Classify an assignment without conflating unknown values with safe shadows."""
    factories, namespaces, dynamic_executors, namespace_mutators = aliases
    source_name = _qualified_name(value)
    carries_authority = (
        source_name in factories
        or source_name in namespaces
        or _is_zero_argument_call_to(value, factories)
        or _is_dynamic_executor_reference(value, dynamic_executors)
        or _is_dynamic_executor_owner_reference(value, dynamic_executors)
        or bool(_namespace_mutator_references(value, factories, namespaces, namespace_mutators))
    )
    if carries_authority:
        return AliasAuthority.AUTHORITY
    return AliasAuthority.PROVEN_SAFE if _value_is_proven_safe(value, aliases) else AliasAuthority.UNKNOWN


def _value_is_proven_safe(value: ast.AST, aliases: ScopeAliases) -> bool:
    """Return whether an assignment is demonstrably inert at import time."""
    inert_container_method = (
        isinstance(value, ast.Attribute) and isinstance(value.value, ast.Dict) and value.attr in _NAMESPACE_MUTATORS
    )
    inert_object = (
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Name)
        and value.func.id == "object"
        and not value.args
        and not value.keywords
    )
    return (
        _literal_value_is_proven_safe(value, aliases)
        or _lambda_is_proven_inert(value, aliases)
        or inert_container_method
        or inert_object
    )


def _node_binds_name(node: ast.AST, name: str) -> bool:
    """Return whether one same-scope node may bind or remove ``name``."""
    if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
        return node.id == name
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return node.name == name
    if isinstance(node, ast.Import):
        return any((alias.asname or alias.name.split(".", maxsplit=1)[0]) == name for alias in node.names)
    if isinstance(node, ast.ImportFrom):
        return any((alias.asname or alias.name) in {name, "*"} for alias in node.names)
    if isinstance(node, (ast.MatchAs, ast.MatchStar)):
        return node.name == name
    return isinstance(node, ast.MatchMapping) and node.rest == name


def _simple_namespace_import_is_unshadowed(statements: Sequence[ast.AST], qualified_name: str, before: ast.AST) -> bool:
    """Prove that a SimpleNamespace constructor still names the stdlib type."""
    before_position = _node_position(before)
    imports, shadow_name = _simple_namespace_imports(statements, qualified_name, before_position)
    if not imports or shadow_name is None:
        return False
    latest_import_position = max(_node_position(node) for node in imports)
    return not any(
        latest_import_position < _node_position(node) < before_position and _node_binds_name(node, shadow_name)
        for node in _same_scope_nodes(statements)
    )


def _simple_namespace_imports(
    statements: Sequence[ast.AST], qualified_name: str, before_position: tuple[int, int]
) -> tuple[Sequence[ast.AST], str | None]:
    """Return matching stdlib imports and the name whose shadowing invalidates them."""
    if qualified_name == "SimpleNamespace":
        return _direct_simple_namespace_imports(statements, before_position), qualified_name
    if qualified_name.endswith(".SimpleNamespace"):
        owner = qualified_name.removesuffix(".SimpleNamespace")
        return _qualified_simple_namespace_imports(statements, owner, before_position), owner
    return [], None


def _direct_simple_namespace_imports(
    statements: Sequence[ast.AST], before_position: tuple[int, int]
) -> list[ast.ImportFrom]:
    """Return direct imports of the stdlib SimpleNamespace constructor."""
    return [
        node
        for node in statements
        if isinstance(node, ast.ImportFrom)
        and node.module == "types"
        and any(
            alias.name == "SimpleNamespace" and (alias.asname or alias.name) == "SimpleNamespace"
            for alias in node.names
        )
        and _node_position(node) < before_position
    ]


def _qualified_simple_namespace_imports(
    statements: Sequence[ast.AST], owner: str, before_position: tuple[int, int]
) -> list[ast.Import]:
    """Return imports that expose the stdlib types module through one owner."""
    return [
        node
        for node in statements
        if isinstance(node, ast.Import)
        and any(alias.name == "types" and (alias.asname or alias.name) == owner for alias in node.names)
        and _node_position(node) < before_position
    ]


def _operation_uses_proven_safe_executor_owner(
    node: ast.AST, statements: Sequence[ast.AST], aliases: ScopeAliases
) -> bool:
    """Allow direct calls through an authenticated inert SimpleNamespace member."""
    operation = _literal_callable_reference(node.func) if isinstance(node, ast.Call) else None
    if not isinstance(operation, ast.Attribute):
        return False
    owner = operation.value
    if not isinstance(owner, ast.Call):
        return False
    constructor = _qualified_name(owner.func)
    if constructor is None or not _simple_namespace_import_is_unshadowed(statements, constructor, node):
        return False
    if owner.args or any(keyword.arg is None for keyword in owner.keywords):
        return False
    members = {keyword.arg: keyword.value for keyword in owner.keywords if keyword.arg is not None}
    selected = members.get(operation.attr)
    return selected is not None and _lambda_is_proven_inert(selected, aliases)


def _name_is_unbound_before(statements: Sequence[ast.AST], name: str, before: ast.AST) -> bool:
    """Prove that a selected safe builtin has not been rebound or imported."""
    before_position = _node_position(before)
    return not any(
        _node_position(node) < before_position and _node_binds_name(node, name)
        for node in _same_scope_nodes(statements)
    )


def _assigned_simple_namespace_is_proven_safe(
    value: ast.AST, operation: ast.AST, statements: Sequence[ast.AST], aliases: ScopeAliases
) -> bool:
    """Prove that an assigned stdlib namespace exposes an inert selected executor."""
    selected_operation = _literal_callable_reference(operation.func) if isinstance(operation, ast.Call) else None
    if not (isinstance(value, ast.Call) and isinstance(selected_operation, ast.Attribute)):
        return False
    constructor = _qualified_name(value.func)
    if constructor is None or not _simple_namespace_import_is_unshadowed(statements, constructor, value):
        return False
    if value.args or any(keyword.arg is None for keyword in value.keywords):
        return False
    selected = next((keyword.value for keyword in value.keywords if keyword.arg == selected_operation.attr), None)
    return selected is not None and _lambda_is_proven_inert(selected, aliases)


def _assignment_value_is_proven_safe(
    value: ast.AST, operation: ast.AST, statements: Sequence[ast.AST], aliases: ScopeAliases
) -> bool:
    """Return whether the latest definite replacement has no tracked authority."""
    if _alias_authority_value(value, aliases) is AliasAuthority.PROVEN_SAFE:
        return True
    if isinstance(value, ast.Name) and value.id == "print" and _name_is_unbound_before(statements, value.id, value):
        return True
    if _assigned_simple_namespace_is_proven_safe(value, operation, statements, aliases):
        return True
    if _assigned_inert_local_instance_is_proven_safe(value, statements):
        return True
    return (
        isinstance(value, ast.Call)
        and (constructor := _qualified_name(value.func)) is not None
        and _simple_namespace_import_is_unshadowed(statements, constructor, value)
        and not value.args
        and not value.keywords
    )


def _assigned_inert_local_instance_is_proven_safe(value: ast.AST, statements: Sequence[ast.AST]) -> bool:
    """Prove that an empty local class instance cannot redirect attribute writes."""
    constructor = _empty_constructor_name(value)
    if constructor is None:
        return False
    definitions = [statement for statement in statements if _is_prior_inert_class(statement, constructor, value)]
    if len(definitions) != 1:
        return False
    definition = definitions[0]
    return not _name_is_rebound_between(statements, constructor, definition, value)


def _empty_constructor_name(value: ast.AST) -> str | None:
    """Return the simple constructor name for an argument-free call."""
    return (
        value.func.id
        if isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and not value.args and not value.keywords
        else None
    )


def _is_inert_class_member(member: ast.AST) -> bool:
    """Return whether a class member is a pass statement or docstring."""
    return isinstance(member, ast.Pass) or (
        isinstance(member, ast.Expr) and isinstance(member.value, ast.Constant) and isinstance(member.value.value, str)
    )


def _is_prior_inert_class(statement: ast.AST, constructor: str, value: ast.AST) -> bool:
    """Return whether one prior class is an undecorated empty local owner."""
    return (
        isinstance(statement, ast.ClassDef)
        and statement.name == constructor
        and _node_position(statement) < _node_position(value)
        and not statement.bases
        and not statement.keywords
        and not statement.decorator_list
        and all(_is_inert_class_member(member) for member in statement.body)
    )


def _name_is_rebound_between(statements: Sequence[ast.AST], name: str, after: ast.AST, before: ast.AST) -> bool:
    """Return whether a same-scope binding replaces a proven owner before use."""
    return any(
        _node_position(after) < _node_position(node) < _node_position(before) and _node_binds_name(node, name)
        for node in _same_scope_nodes(statements)
    )


def _without_alias_name(aliases: ScopeAliases, name: str) -> ScopeAliases:
    """Return an alias snapshot without authority inherited through one name."""
    factories, namespaces, dynamic_executors, namespace_mutators = _copy_scope_aliases(aliases)
    factories.discard(name)
    module_mapping_marker = _authority_marker(_MODULE_MAPPING_PREFIX, name)
    factories.difference_update({entry for entry in factories if entry.startswith(module_mapping_marker)})
    namespaces.discard(name)
    dynamic_executors.discard(name)
    dynamic_executors.discard(f"{name}.exec")
    dynamic_executors.discard(f"{name}.eval")
    dynamic_executors.discard(_authority_marker(_IMPORT_FACTORY_PREFIX, name))
    dynamic_executors.discard(_authority_marker(_BUILTINS_MAPPING_PREFIX, name))
    namespace_mutators.difference_update({entry for entry in namespace_mutators if entry.startswith(f"{name}.")})
    return factories, namespaces, dynamic_executors, namespace_mutators


def _compound_statement_binds_authority(node: ast.AST, name: str, aliases: ScopeAliases) -> bool:
    """Return whether a compound statement can persist tracked authority in a name."""
    clean_aliases = _without_alias_name(aliases, name)
    return any(
        name in local_factories
        or name in local_namespaces
        or name in local_executors
        or any(entry.startswith(f"{name}.") for entry in local_mutators)
        for local_factories, local_namespaces, local_executors, local_mutators in (
            local_aliases for local_aliases, _ in _compound_binding_regions(node, clean_aliases)
        )
    )


def _nested_assignment_binds_authority(node: ast.AST, name: str, aliases: ScopeAliases) -> bool:
    """Fail closed when one nested assignment is not a proven-safe shadow."""
    return any(
        name in target_names
        and (value is None or _alias_authority_value(value, aliases) is not AliasAuthority.PROVEN_SAFE)
        for target_names, value in _assignment_bindings(node)
    )


def _node_restores_alias_authority(
    node: ast.AST, name: str, aliases: ScopeAliases, direct_statement_ids: set[int]
) -> bool:
    """Return whether one intervening node can restore an alias."""
    is_direct_statement = id(node) in direct_statement_ids
    if not is_direct_statement and _nested_assignment_binds_authority(node, name, aliases):
        return True
    if is_direct_statement and _compound_statement_binds_authority(node, name, aliases):
        return True
    imported_executors = _dynamic_executor_import_names(node)
    return name in imported_executors or f"{name}.exec" in imported_executors


def _has_uncertain_authority_binding(
    statements: Sequence[ast.AST], name: str, after: ast.AST, before: ast.AST, aliases: ScopeAliases
) -> bool:
    """Return whether a non-definite path can restore authority before use."""
    after_position = _node_position(after)
    before_position = _node_position(before)
    direct_statement_ids = {id(statement) for statement in statements}
    for node in _same_scope_nodes(statements):
        position = _node_position(node)
        if after_position < position < before_position and _node_restores_alias_authority(
            node, name, aliases, direct_statement_ids
        ):
            return True
    return False


def _namespace_operation_alias_name(node: ast.AST, aliases: ScopeAliases) -> str | None:
    """Return the simple alias name used by one namespace operation."""
    factories, namespaces, _, namespace_mutators = aliases
    augmented_alias = _augmented_namespace_alias_name(node, factories, namespaces)
    if augmented_alias is not None:
        return augmented_alias
    target_alias = _namespace_target_alias_name(node, factories, namespaces)
    if target_alias is not None:
        return target_alias
    if isinstance(node, ast.Call) and _namespace_mutator_names(node, factories, namespaces, namespace_mutators):
        return _namespace_mutator_owner_name(node)
    return None


def _namespace_target_alias_name(node: ast.AST, factories: set[str], namespaces: set[str]) -> str | None:
    """Return the name targeted by a direct namespace subscript or attribute."""
    if isinstance(node, ast.Subscript) and _is_namespace_plugin_subscript(node, factories, namespaces):
        return node.value.id if isinstance(node.value, ast.Name) else None
    if isinstance(node, ast.Attribute) and _is_namespace_plugin_attribute(node, factories, namespaces):
        return node.value.id if isinstance(node.value, ast.Name) else None
    return None


def _namespace_mutator_owner_name(node: ast.Call) -> str | None:
    """Return the simple owner passed to one namespace mutator call."""
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        owner: ast.AST = node.func.value
    elif isinstance(node.func, ast.Call) and node.func.args:
        owner = node.func.args[0]
    else:
        return None
    return owner.id if isinstance(owner, ast.Name) else None


def _augmented_namespace_alias_name(node: ast.AST, factories: set[str], namespaces: set[str]) -> str | None:
    """Return the alias targeted by a plugin-relevant namespace union."""
    return (
        node.target.id
        if isinstance(node, ast.AugAssign)
        and _is_namespace_plugin_augmented_union(node, factories, namespaces)
        and isinstance(node.target, ast.Name)
        else None
    )


def _dynamic_operation_alias_name(node: ast.AST, dynamic_executors: set[str]) -> str | None:
    """Return the simple alias name used by one dynamic-execution call."""
    if not isinstance(node, ast.Call) or not _is_dynamic_executor_reference(node.func, dynamic_executors):
        return None
    operation = _literal_callable_reference(node.func)
    if isinstance(operation, ast.Name):
        return operation.id
    if isinstance(operation, ast.Attribute) and isinstance(operation.value, ast.Name):
        return operation.value.id
    if isinstance(operation, ast.Call) and operation.args and isinstance(operation.args[0], ast.Name):
        return operation.args[0].id
    return None


def _operation_alias_names(node: ast.AST, aliases: ScopeAliases) -> set[str]:
    """Return simple alias names whose authority makes an operation unsafe."""
    namespace_name = _namespace_operation_alias_name(node, aliases)
    dynamic_name = _dynamic_operation_alias_name(node, aliases[2])
    return {name for name in (namespace_name, dynamic_name) if name is not None}


def _operation_uses_definitely_shadowed_alias(
    node: ast.AST, statements: Sequence[ast.AST], aliases: ScopeAliases
) -> bool:
    """Return whether every alias-dependent authority was definitely replaced."""
    if _operation_uses_proven_safe_executor_owner(node, statements, aliases):
        return True
    names = _operation_alias_names(node, aliases)
    if not names:
        return False
    bindings = [_latest_direct_binding(statements, name, node) for name in names]
    return all(
        value is not None
        and _assignment_value_is_proven_safe(value, node, statements, aliases)
        and not _has_uncertain_authority_binding(statements, name, value, node, aliases)
        for name, value in zip(names, bindings, strict=True)
    )


def _plugin_assignment(node: ast.AST) -> tuple[ast.Name | None, ast.AST | None]:
    """Return one direct plugin target and its value, when present."""
    if isinstance(node, ast.Assign):
        target = next(
            (
                candidate
                for candidate in node.targets
                if isinstance(candidate, ast.Name) and candidate.id == "pytest_plugins"
            ),
            None,
        )
        return target, node.value if target is not None else None
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == "pytest_plugins":
        return node.target, node.value
    return None, None


def _enclosing_scope_children(node: ast.AST, plugin_target: ast.Name | None) -> list[ast.AST]:
    """Return children evaluated in the same scope, excluding local comprehension targets."""
    outer_iterable = node.generators[0].iter if isinstance(node, ast.GeneratorExp) and node.generators else None
    empty_sequence = isinstance(outer_iterable, (ast.List, ast.Tuple, ast.Set)) and not outer_iterable.elts
    empty_mapping = isinstance(outer_iterable, ast.Dict) and not outer_iterable.keys
    if isinstance(node, ast.GeneratorExp) and outer_iterable is not None and (empty_sequence or empty_mapping):
        return [outer_iterable]
    if isinstance(node, ast.comprehension):
        return [node.iter, *node.ifs]
    return [child for child in ast.iter_child_nodes(node) if child is not plugin_target]


def _literal_plugin_names(value_node: ast.AST) -> list[list[str]]:
    """Parse one literal plugin declaration or reject ambiguous runtime data."""
    try:
        value = ast.literal_eval(value_node)
    except (ValueError, TypeError) as error:
        raise ValueError("prior-red-proof-invalid") from error
    declared_plugins = [value] if isinstance(value, str) else value
    if not isinstance(declared_plugins, (list, tuple)):
        raise ValueError("prior-red-proof-invalid")
    string_plugins = [plugin for plugin in declared_plugins if isinstance(plugin, str)]
    if len(string_plugins) != len(declared_plugins):
        raise ValueError("prior-red-proof-invalid")
    return [plugin.split(".") for plugin in string_plugins]


def _pytest_plugin_names(tree: ast.AST) -> list[list[str]]:
    """Return literal module-scope plugins or reject an unresolved declaration."""
    plugin_names: list[list[str]] = []
    root_statements = tree.body if isinstance(tree, ast.Module) else []
    factories, namespaces, dynamic_executors, namespace_mutators = _scope_aliases(
        root_statements, {"globals", "locals", "vars"}
    )
    root_aliases = (factories, namespaces, dynamic_executors, namespace_mutators)
    if _direct_local_binder_is_invoked(root_statements, root_aliases):
        raise ValueError("prior-red-proof-invalid")
    class_factories, _, _, _ = _scope_aliases(root_statements, {"globals"})
    scope_nodes: list[ast.AST] = list(reversed(tree.body)) if isinstance(tree, ast.Module) else []
    while scope_nodes:
        node = scope_nodes.pop()
        if _node_binds_name(node, "__getattr__"):
            raise ValueError("prior-red-proof-invalid")
        node_aliases = _aliases_with_prior_compound_bindings(
            root_statements, node, (factories, namespaces, dynamic_executors, namespace_mutators)
        )
        node_factories, node_namespaces, node_executors, node_mutators = node_aliases
        class_aliases = (class_factories, node_namespaces, node_executors, node_mutators)
        definition_children = _definition_expression_children(node, class_aliases)
        if definition_children is not None:
            scope_nodes.extend(reversed(definition_children))
            continue
        indirect_binding = _is_indirect_plugin_binding(
            node, node_factories, node_namespaces, node_executors, node_mutators
        )
        if _import_binds_pytest_plugins(node) or (
            indirect_binding and not _operation_uses_definitely_shadowed_alias(node, root_statements, node_aliases)
        ):
            raise ValueError("prior-red-proof-invalid")
        plugin_target, value_node = _plugin_assignment(node)
        scope_nodes.extend(reversed(_enclosing_scope_children(node, plugin_target)))
        if value_node is not None:
            plugin_names.extend(_literal_plugin_names(value_node))
    return plugin_names


def _literal_binding(statement: ast.AST) -> tuple[list[str], str | None]:
    """Return simple assignment targets and their literal string value."""
    if isinstance(statement, ast.Assign):
        targets, value = statement.targets, statement.value
    elif isinstance(statement, ast.AnnAssign):
        targets, value = [statement.target], statement.value
    else:
        return [], None
    names = [target.id for target in targets if isinstance(target, ast.Name)]
    literal = value.value if isinstance(value, ast.Constant) and isinstance(value.value, str) else None
    return names, literal


def _record_literal_binding(bindings: dict[str, str], ambiguous: set[str], name: str, literal: str | None) -> None:
    """Record one literal name, permanently rejecting conflicting assignments."""
    if literal is None or (name in bindings and bindings[name] != literal):
        ambiguous.add(name)
        bindings.pop(name, None)
    elif name not in ambiguous:
        bindings[name] = literal


def _literal_module_bindings(tree: ast.AST) -> dict[str, str]:
    """Return unambiguous module-scope string bindings used by dynamic imports."""
    bindings: dict[str, str] = {}
    ambiguous: set[str] = set()
    statements = tree.body if isinstance(tree, ast.Module) else []
    for statement in statements:
        names, literal = _literal_binding(statement)
        for name in names:
            _record_literal_binding(bindings, ambiguous, name, literal)
    return bindings


def _initial_dynamic_import_aliases(tree: ast.AST) -> DynamicImportAliases:
    """Collect import statements that introduce dynamic-loader authority."""
    return DynamicImportAliases(
        direct_loaders={"__import__", *_direct_loader_aliases(tree)},
        importlib=ImportNamespaceAliases("import_module", _module_owner_aliases(tree, "importlib"), set(), set()),
        builtins=ImportNamespaceAliases("__import__", _module_owner_aliases(tree, "builtins"), set(), set()),
    )


def _module_owner_aliases(tree: ast.AST, module_name: str) -> set[str]:
    """Return aliases introduced by direct imports of one loader module."""
    return {
        alias.asname or alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
        if alias.name == module_name
    }


def _direct_loader_aliases(tree: ast.AST) -> set[str]:
    """Return aliases introduced by from-imports of supported loaders."""
    supported = {("builtins", "__import__"), ("importlib", "import_module")}
    return {
        alias.asname or alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module in {"builtins", "importlib"}
        for alias in node.names
        if (node.module, alias.name) in supported
    }


def _simple_dynamic_import_bindings(statements: Sequence[ast.AST]) -> Iterator[tuple[str, ast.AST]]:
    """Yield simple one-name assignments eligible for alias propagation."""
    for statement in statements:
        for target_names, value in _assignment_bindings(statement):
            if value is not None and len(target_names) == 1:
                yield next(iter(target_names)), value


def _record_dynamic_import_alias(target: str, value: ast.AST, aliases: DynamicImportAliases) -> None:
    """Propagate one assignment across the two loader namespaces."""
    qualified_value = _qualified_name(value)
    if qualified_value in aliases.direct_loaders:
        aliases.direct_loaders.add(target)
        return
    namespaces = (aliases.importlib, aliases.builtins)
    for namespace in namespaces:
        if qualified_value in namespace.owners:
            namespace.owners.add(target)
            return
    for namespace in namespaces:
        if qualified_value in namespace.mappings or _is_importlib_mapping_reference(
            value, namespace.owners, namespace.mappings
        ):
            namespace.mappings.add(target)
            return
    for namespace in namespaces:
        if qualified_value in namespace.mapping_methods or _is_importlib_mapping_method_reference(
            value, namespace.owners, namespace.mappings, namespace.mapping_methods
        ):
            namespace.mapping_methods.add(target)
            return
    if any(_is_importlib_loader_reference(value, namespace) for namespace in namespaces):
        aliases.direct_loaders.add(target)


def _propagate_dynamic_import_aliases(statements: Sequence[ast.AST], aliases: DynamicImportAliases) -> None:
    """Reach a fixed point over simple module-scope alias assignments."""
    while True:
        before = aliases._sizes()
        for target, value in _simple_dynamic_import_bindings(statements):
            _record_dynamic_import_alias(target, value, aliases)
        if aliases._sizes() == before:
            return


def _dynamic_import_aliases(tree: ast.AST) -> DynamicImportAliases:
    """Return loader and module-specific namespace authority aliases."""
    aliases = _initial_dynamic_import_aliases(tree)
    _propagate_dynamic_import_aliases(tree.body if isinstance(tree, ast.Module) else [], aliases)
    return aliases


def _is_importlib_loader_reference(
    node: ast.AST,
    aliases: ImportNamespaceAliases,
) -> bool:
    """Return whether an expression selects one loader from an imported module."""
    reference = _literal_callable_reference(node)
    if reference is None:
        return False
    return _selected_loader_name(reference, aliases) == aliases.loader_name


def _selected_loader_name(reference: ast.AST, aliases: ImportNamespaceAliases) -> str | None:
    """Return the statically selected attribute from one loader namespace."""
    if isinstance(reference, ast.Attribute):
        return reference.attr if _qualified_name(reference.value) in aliases.owners else None
    if isinstance(reference, ast.Subscript) and _is_importlib_mapping_reference(
        reference.value, aliases.owners, aliases.mappings
    ):
        key = reference.slice
        if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
            raise ValueError("prior-red-proof-invalid")
        return key.value
    mapping_lookup = _importlib_mapping_lookup(
        reference,
        aliases.owners,
        aliases.mappings,
        aliases.mapping_methods,
    )
    if mapping_lookup is not None:
        return mapping_lookup
    if not _is_importlib_getattr(reference, aliases.owners):
        return None
    assert isinstance(reference, ast.Call)
    attribute = reference.args[1]
    if not isinstance(attribute, ast.Constant) or not isinstance(attribute.value, str):
        raise ValueError("prior-red-proof-invalid")
    return attribute.value


def _is_importlib_getattr(reference: ast.AST, owners: set[str]) -> bool:
    """Return whether a call selects an attribute from an imported module."""
    return (
        isinstance(reference, ast.Call)
        and isinstance(reference.func, ast.Name)
        and reference.func.id == "getattr"
        and len(reference.args) >= 2
        and _qualified_name(reference.args[0]) in owners
    )


def _is_importlib_mapping_reference(node: ast.AST, importlib_owners: set[str], importlib_mappings: set[str]) -> bool:
    """Return whether an expression exposes an imported importlib namespace."""
    if isinstance(node, ast.Name) and node.id in importlib_mappings:
        return True
    if isinstance(node, ast.Attribute) and node.attr == "__dict__":
        return _qualified_name(node.value) in importlib_owners
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "vars"
        and len(node.args) == 1
        and not node.keywords
        and _qualified_name(node.args[0]) in importlib_owners
    )


def _is_importlib_mapping_method_reference(
    node: ast.AST,
    importlib_owners: set[str],
    importlib_mappings: set[str],
    importlib_mapping_methods: set[str],
) -> bool:
    """Return whether an expression selects a tracked mapping lookup method."""
    reference = _literal_callable_reference(node)
    if isinstance(reference, ast.Name):
        return reference.id in importlib_mapping_methods
    if isinstance(reference, ast.Attribute):
        return reference.attr in {"get", "__getitem__"} and _is_importlib_mapping_reference(
            reference.value, importlib_owners, importlib_mappings
        )
    if not (
        isinstance(reference, ast.Call)
        and isinstance(reference.func, ast.Name)
        and reference.func.id == "getattr"
        and len(reference.args) >= 2
        and _is_importlib_mapping_reference(reference.args[0], importlib_owners, importlib_mappings)
    ):
        return False
    selector = reference.args[1]
    if not isinstance(selector, ast.Constant) or not isinstance(selector.value, str):
        raise ValueError("prior-red-proof-invalid")
    return selector.value in {"get", "__getitem__"}


def _importlib_mapping_lookup(
    node: ast.AST,
    importlib_owners: set[str],
    importlib_mappings: set[str],
    importlib_mapping_methods: set[str],
) -> str | None:
    """Return a literal key selected from an importlib namespace mapping."""
    if not isinstance(node, ast.Call):
        return None
    if not _is_importlib_mapping_method_reference(
        node.func,
        importlib_owners,
        importlib_mappings,
        importlib_mapping_methods,
    ):
        return None
    if not node.args:
        raise ValueError("prior-red-proof-invalid")
    key = node.args[0]
    if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
        raise ValueError("prior-red-proof-invalid")
    return key.value


def _dynamic_import_name(
    node: ast.Call,
    aliases: DynamicImportAliases,
    literal_bindings: dict[str, str],
) -> str | None:
    """Return a statically resolved dynamic import name or reject ambiguity."""
    direct_reference = _literal_callable_reference(node.func)
    direct_call = isinstance(direct_reference, ast.Name) and direct_reference.id in aliases.direct_loaders
    owner_call = _is_importlib_loader_reference(node.func, aliases.importlib) or _is_importlib_loader_reference(
        node.func, aliases.builtins
    )
    if not (direct_call or owner_call):
        return None
    if not node.args:
        raise ValueError("prior-red-proof-invalid")
    target = node.args[0]
    if isinstance(target, ast.Constant) and isinstance(target.value, str):
        module_name = target.value
    elif isinstance(target, ast.Name) and target.id in literal_bindings:
        module_name = literal_bindings[target.id]
    else:
        raise ValueError("prior-red-proof-invalid")
    if PYTHON_MODULE_PATTERN.fullmatch(module_name) is None:
        raise ValueError("prior-red-proof-invalid")
    return module_name


def _import_module_names(tree: ast.AST, current_path: str) -> list[list[str]]:
    """Return imported module names, including relative import candidates."""
    current_package = list(PurePosixPath(current_path).parent.parts)
    module_names = _pytest_plugin_names(tree)
    aliases = _dynamic_import_aliases(tree)
    literal_bindings = _literal_module_bindings(tree)
    for node in ast.walk(tree):
        module_names.extend(_static_import_names(node, current_package))
        if isinstance(node, ast.Call) and (dynamic_name := _dynamic_import_name(node, aliases, literal_bindings)):
            module_names.append(dynamic_name.split("."))
    return module_names


def _static_import_names(node: ast.AST, current_package: list[str]) -> list[list[str]]:
    """Return the module candidates introduced by one static import node."""
    if isinstance(node, ast.Import):
        return [alias.name.split(".") for alias in node.names]
    if not isinstance(node, ast.ImportFrom):
        return []
    parent_parts = current_package[: max(len(current_package) - node.level + 1, 0)] if node.level else []
    base_parts = parent_parts + (node.module.split(".") if node.module else [])
    return [base_parts, *(base_parts + alias.name.split(".") for alias in node.names if alias.name != "*")]


def _python_tree_at_ref(repo_root: Path, source_ref: str, path: str) -> ast.AST | None:
    """Parse committed Python source without consulting mutable worktree bytes."""
    result = _git(repo_root, "show", f"{source_ref}:{path}")
    try:
        return ast.parse(result.stdout) if result.returncode == 0 else None
    except SyntaxError:
        return None


def _imported_python_paths(repo_root: Path, source_ref: str, source_paths: Sequence[str]) -> set[str]:
    """Return transitive repository-local Python imports used by pytest inputs."""
    pending = list(source_paths)
    imported_paths: set[str] = set()
    while pending:
        current_path = pending.pop()
        tree = _python_tree_at_ref(repo_root, source_ref, current_path)
        if tree is None:
            continue
        discovered_paths = {
            imported_path
            for module_parts in _import_module_names(tree, current_path)
            for imported_path in _python_module_paths(module_parts)
        }
        for imported_path in discovered_paths - imported_paths:
            imported_paths.add(imported_path)
            if _test_path_exists_at_ref(repo_root, source_ref, imported_path):
                pending.append(imported_path)
    return imported_paths


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


def _has_governed_production_path(paths: Sequence[str]) -> bool:
    return any(path in GOVERNED_PRODUCTION_FILES or path.startswith(GOVERNED_PRODUCTION_PREFIXES) for path in paths)


def _test_path_exists_at_ref(repo_root: Path, source_ref: str, test_path: str) -> bool:
    return _git(repo_root, "cat-file", "-e", f"{source_ref}:{test_path}").returncode == 0


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


def _red_source_identities(repo_root: Path, base_ref: str, source_ref: str) -> tuple[str, str]:
    """Return a committed source tree and merge base for one test-only red source."""
    if not _is_ancestor(repo_root, base_ref, source_ref):
        raise ValueError("prior-red-proof-invalid")
    changed_paths = _changed_paths_in_history(repo_root, base_ref, source_ref)
    if changed_paths is None or _has_governed_production_path(changed_paths):
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
    allowed = {"base_ref", "final_ref", "junit_path", "cycle_authority", "repository", "pull_request", "head_branch"}
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
    )


def _binding_values(
    context: BindingContext,
    root: ParsedJunit,
    execution_proof: dict[str, object],
    authority: TrustedCycleAuthority | None,
) -> dict[str, object]:
    """Build immutable source, toolchain, and optional cycle bindings."""
    source_tree, merge_base = _red_source_identities(context.repo_root, context.provenance_base, context.source_ref)
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
            source_ref,
            source_ref,
            settings.repository,
            settings.pull_request,
            settings.head_branch,
        ),
    )
    provenance_base = _provenance_base_ref(settings.base_ref, authority)
    execution_proof = _validated_execution_proof(report)
    bindings = _binding_values(
        BindingContext(repo_root, source_ref, selector_paths, provenance_base), root, execution_proof, authority
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
        if not isinstance(recorded_digest, str) or recorded_digest != _blob_digest_at_ref(
            repo_root, source_ref, test_path
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
    if not _valid_report_digests(report) or source_tree != actual_tree or merge_base != actual_merge_base:
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
    return _validate_red_history_freshness(report, repo_root, provenance_base, source_ref, settings.final_ref)


def _parent_package_initializers(path: str) -> set[str]:
    """Return candidate package initializers executed while importing one path."""
    parent_parts = PurePosixPath(path).parent.parts
    return {
        (PurePosixPath(*parent_parts[:depth]) / "__init__.py").as_posix() for depth in range(1, len(parent_parts) + 1)
    }


def _pytest_proof_inputs(repo_root: Path, source_ref: str, selector_paths: Sequence[str]) -> set[str]:
    """Return every committed selector, config, plugin, conftest, and import input."""
    pytest_configurations = {
        config_path for test_path in selector_paths for config_path in _applicable_pytest_configuration_paths(test_path)
    }
    configured_plugins = _configured_pytest_plugin_paths(repo_root, source_ref, sorted(pytest_configurations))
    fixed_plugin_paths = _python_module_paths(("scripts", "requirements_proof_pytest_plugin"))
    pytest_inputs = {
        *pytest_configurations,
        *configured_plugins,
        *fixed_plugin_paths,
        "scripts/requirements_proof_executor.py",
        "uv.lock",
    }
    for test_path in selector_paths:
        if not _test_path_exists_at_ref(repo_root, source_ref, test_path) or not _test_path_is_regular_at_ref(
            repo_root, source_ref, test_path
        ):
            raise ValueError("prior-red-proof-invalid")
        python_seeds = {test_path, *_applicable_conftest_paths(test_path)}
        pytest_inputs.update(python_seeds)
        pytest_inputs.update(
            initializer for seed_path in python_seeds for initializer in _parent_package_initializers(seed_path)
        )
    return {*pytest_inputs, *_imported_python_paths(repo_root, source_ref, sorted(pytest_inputs))}


def _validate_red_history_freshness(
    report: dict[str, object], repo_root: Path, base_ref: str, source_ref: str, final_ref: str
) -> list[str]:
    """Reject production-before-red and changed proof inputs after the red source."""
    _, selector_paths = _selector_paths(report)
    paths_before_red = _changed_paths_in_history(repo_root, base_ref, source_ref)
    if paths_before_red is None or _has_governed_production_path(paths_before_red):
        return ["tdd-order-unproven"]
    paths_after_red = _changed_paths_in_history(repo_root, source_ref, final_ref, merge_parent=1)
    if paths_after_red is None:
        return ["tdd-order-unproven"]
    try:
        proof_inputs = _pytest_proof_inputs(repo_root, source_ref, selector_paths)
    except ValueError as error:
        return [str(error)]
    if not proof_inputs.isdisjoint(paths_after_red):
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
                junit_path=arguments.junit,
                cycle_authority=arguments.cycle_authority,
                repository=arguments.repository,
                pull_request=arguments.pull_request,
                head_branch=arguments.head_branch,
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
    )
    if findings:
        sys.stderr.write(f"{','.join(findings)}\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Security-boundary tests for protected release-promotion proof reuse."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import inspect
import json
import os
import subprocess
import sys
import types
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATOR_PATH = REPO_ROOT / "scripts" / "requirements_promotion_reuse.py"
REPOSITORY = "nold-ai/specfact-cli"
REPOSITORY_ID = 1085706003
BASE_SHA = "1" * 40
PREVIOUS_DEV_SHA = "2" * 40
SOURCE_SHA = "3" * 40
HEAD_SHA = "4" * 40
HEAD_TREE = "5" * 40
MAPPING_DIGEST = f"sha256:{'6' * 64}"
PLAN_DIGEST = f"sha256:{'7' * 64}"
REQUIREMENTS_WORKFLOW_ID = 323253915
AUTHORITY_WORKFLOW_ID = 348163848
GitArguments = tuple[str, ...]


@dataclass
class _PromotionFixture:
    event: dict[str, object]
    source_pulls: list[object]
    check_runs: dict[str, object]
    requirements_run: dict[str, object]
    authority_run: dict[str, object]
    artifacts: dict[str, object]
    producer_archive: Path
    execution_archive: Path
    git_outputs: dict[GitArguments, str]
    git_failures: set[GitArguments] = field(default_factory=set)
    git_calls: list[GitArguments] = field(default_factory=list)

    def run_git(self, _repo_root: Path, arguments: list[str]) -> str:
        command = tuple(arguments)
        self.git_calls.append(command)
        if command in self.git_failures or command not in self.git_outputs:
            raise subprocess.CalledProcessError(1, ["git", *arguments])
        return self.git_outputs[command]


@dataclass(frozen=True)
class _CliInputs:
    event: Path
    source_pulls: Path
    check_runs: Path
    requirements_run: Path
    authority_run: Path
    artifacts: Path


def _load_validator() -> types.ModuleType:
    if not VALIDATOR_PATH.is_file():
        pytest.fail("protected-promotion validator is not implemented")
    name = "requirements_promotion_reuse"
    spec = importlib.util.spec_from_file_location(name, VALIDATOR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(name, None)
    return module


def _json_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode() + b"\n"


def _write_json(path: Path, value: object) -> None:
    path.write_bytes(_json_bytes(value))


def _archive_files(path: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(path) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


def _write_archive(path: Path, files: dict[str, bytes]) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.external_attr = 0o100644 << 16
            archive.writestr(info, content)


def _artifact_digest(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _set_nested(payload: dict[str, object], path: tuple[str, ...], value: object) -> None:
    target = payload
    for key in path[:-1]:
        target = cast(dict[str, object], target[key])
    target[path[-1]] = value


def _object_list(payload: dict[str, object], key: str) -> list[dict[str, object]]:
    return cast(list[dict[str, object]], payload[key])


def _rewrite_json_member(path: Path, name: str, field_path: tuple[str, ...], value: object) -> None:
    files = _archive_files(path)
    payload = json.loads(files[name])
    assert isinstance(payload, dict)
    _set_nested(payload, field_path, value)
    files[name] = _json_bytes(payload)
    _write_archive(path, files)


def _refresh_artifact_digest(fixture: _PromotionFixture, artifact_index: int, archive: Path) -> None:
    _object_list(fixture.artifacts, "artifacts")[artifact_index]["digest"] = _artifact_digest(archive)


def _proof_archives(tmp_path: Path) -> tuple[Path, Path]:
    selector = "tests/test_fix.py::test_fix"
    plan = {
        "schema_version": "2",
        "verdict": "passed",
        "gate_decision": "pass",
        "required_maturity": "test-authored",
        "observed_maturity": "test-authored",
        "mapping_digest": MAPPING_DIGEST,
        "plan_identity_digest": f"sha256:{'8' * 64}",
        "sources": [{"source": "openspec/changes/fix", "mapping_digest": MAPPING_DIGEST}],
        "plan": {
            "mapping_digest": MAPPING_DIGEST,
            "plan_digest": PLAN_DIGEST,
            "cases": [
                {
                    "method": "test",
                    "node_id": selector,
                    "selector": {"runner": "pytest", "node_id": selector},
                }
            ],
        },
    }
    junit = (
        b'<testsuite tests="1" failures="0"><testcase><properties>'
        b'<property name="specfact.selector" value="tests/test_fix.py::test_fix"/>'
        b'<property name="specfact.runner" value="pytest"/>'
        b"</properties></testcase></testsuite>\n"
    )
    report = {
        "schema_version": "2",
        "verdict": "passed",
        "gate_decision": "pass",
        "required_maturity": "verified",
        "observed_maturity": "verified",
        "delivery_status": "implementation-verified",
        "implementation_evidence": "passing-after-red-proven",
        "mapping_digest": MAPPING_DIGEST,
        "plan_digest": PLAN_DIGEST,
        "execution_proof": {
            "source_ref": SOURCE_SHA,
            "run_stage": "final",
            "proof_basis": "red-junit",
            "selectors": [selector],
            "junit_digest": f"sha256:{hashlib.sha256(junit).hexdigest()}",
        },
    }
    producer_archive = tmp_path / "producer.zip"
    execution_archive = tmp_path / "execution.zip"
    _write_archive(
        producer_archive,
        {
            "requirements-evidence.json": _json_bytes(report),
            "requirements-evidence-plan.json": _json_bytes(plan),
            "requirements-evidence.md": b"# passed\n",
            "requirements-proof.xml": junit,
        },
    )
    _write_archive(execution_archive, {"requirements-evidence-plan.json": _json_bytes(plan)})
    return producer_archive, execution_archive


def _repository_identity() -> dict[str, object]:
    return {"id": REPOSITORY_ID, "full_name": REPOSITORY}


def _promotion_event() -> dict[str, object]:
    return {
        "repository": {"id": REPOSITORY_ID, "full_name": REPOSITORY},
        "pull_request": {
            "number": 691,
            "base": {
                "ref": "main",
                "sha": BASE_SHA,
                "repo": _repository_identity(),
            },
            "head": {
                "ref": "dev",
                "sha": HEAD_SHA,
                "repo": _repository_identity(),
            },
        },
    }


def _source_pull() -> dict[str, object]:
    return {
        "number": 714,
        "state": "closed",
        "merged_at": "2026-09-05T00:00:00Z",
        "merge_commit_sha": HEAD_SHA,
        "base": {
            "ref": "dev",
            "sha": PREVIOUS_DEV_SHA,
            "repo": _repository_identity(),
        },
        "head": {
            "ref": "bugfix/692-release-promotion-requirements-parity",
            "sha": SOURCE_SHA,
            "repo": _repository_identity(),
        },
    }


def _release_association() -> dict[str, object]:
    return {
        "number": 691,
        "state": "open",
        "merged_at": None,
        "merge_commit_sha": None,
        "base": {
            "ref": "main",
            "sha": BASE_SHA,
            "repo": _repository_identity(),
        },
        "head": {
            "ref": "dev",
            "sha": HEAD_SHA,
            "repo": _repository_identity(),
        },
    }


def _check_run(run_id: int, check_id: int, name: str, conclusion: str = "success") -> dict[str, object]:
    return {
        "id": check_id,
        "name": name,
        "status": "completed",
        "conclusion": conclusion,
        "head_sha": SOURCE_SHA,
        "details_url": f"https://github.com/{REPOSITORY}/actions/runs/{run_id}/job/{check_id}",
        "app": {"id": 15368, "slug": "github-actions", "owner": {"login": "github"}},
    }


def _check_runs() -> dict[str, object]:
    return {
        "total_count": 4,
        "check_runs": [
            _check_run(201, 101, "Requirements evidence"),
            _check_run(202, 102, "Trusted Requirements Authority"),
            _check_run(203, 103, "Tests (Python 3.12)"),
            _check_run(204, 104, "Unrelated failed check", "failure"),
        ],
    }


def _workflow_runs(source_branch: object) -> tuple[dict[str, object], dict[str, object]]:
    common_run: dict[str, object] = {
        "event": "pull_request",
        "status": "completed",
        "conclusion": "success",
        "head_sha": SOURCE_SHA,
        "head_branch": source_branch,
        "pull_requests": [],
        "repository": _repository_identity(),
    }
    requirements_run = {
        **common_run,
        "id": 201,
        "name": "Requirements Evidence",
        "path": ".github/workflows/requirements-evidence.yml",
        "workflow_id": REQUIREMENTS_WORKFLOW_ID,
        "workflow_url": f"https://api.github.com/repos/{REPOSITORY}/actions/workflows/{REQUIREMENTS_WORKFLOW_ID}",
    }
    authority_run = {
        **common_run,
        "id": 202,
        "name": "Trusted Requirements Authority",
        "path": ".github/workflows/trusted-requirements-authority.yml",
        "workflow_id": AUTHORITY_WORKFLOW_ID,
        "workflow_url": f"https://api.github.com/repos/{REPOSITORY}/actions/required_workflows/{AUTHORITY_WORKFLOW_ID}",
    }
    return requirements_run, authority_run


def _artifact_record(artifact_id: int, name: str, archive: Path, source_branch: object) -> dict[str, object]:
    return {
        "id": artifact_id,
        "name": name,
        "expired": False,
        "digest": _artifact_digest(archive),
        "workflow_run": {
            "id": 201,
            "head_sha": SOURCE_SHA,
            "head_branch": source_branch,
            "head_repository_id": REPOSITORY_ID,
            "repository_id": REPOSITORY_ID,
        },
    }


def _artifacts(producer_archive: Path, execution_archive: Path, source_branch: object) -> dict[str, object]:
    return {
        "total_count": 2,
        "artifacts": [
            _artifact_record(301, "requirements-evidence", producer_archive, source_branch),
            _artifact_record(302, "requirements-evidence-execution", execution_archive, source_branch),
        ],
    }


def _git_outputs() -> dict[GitArguments, str]:
    return {
        ("rev-parse", "HEAD"): HEAD_SHA,
        ("rev-parse", "HEAD^{tree}"): HEAD_TREE,
        ("rev-parse", "refs/remotes/origin/main^{commit}"): BASE_SHA,
        ("rev-parse", "refs/remotes/origin/dev^{commit}"): HEAD_SHA,
        ("cat-file", "-t", BASE_SHA): "commit",
        ("cat-file", "-t", HEAD_SHA): "commit",
        ("merge-base", "--is-ancestor", BASE_SHA, HEAD_SHA): "",
        ("rev-list", "--parents", "-n", "1", HEAD_SHA): f"{HEAD_SHA} {PREVIOUS_DEV_SHA} {SOURCE_SHA}",
        ("cat-file", "-t", PREVIOUS_DEV_SHA): "commit",
        ("cat-file", "-t", SOURCE_SHA): "commit",
        ("rev-parse", f"{SOURCE_SHA}^{{tree}}"): HEAD_TREE,
    }


def _promotion_fixture(tmp_path: Path) -> _PromotionFixture:
    producer_archive, execution_archive = _proof_archives(tmp_path)
    source_pull = _source_pull()
    source_branch = cast(dict[str, object], source_pull["head"])["ref"]
    requirements_run, authority_run = _workflow_runs(source_branch)
    return _PromotionFixture(
        event=_promotion_event(),
        source_pulls=[_release_association(), source_pull],
        check_runs=_check_runs(),
        requirements_run=requirements_run,
        authority_run=authority_run,
        artifacts=_artifacts(producer_archive, execution_archive, source_branch),
        producer_archive=producer_archive,
        execution_archive=execution_archive,
        git_outputs=_git_outputs(),
    )


def _validate(fixture: _PromotionFixture) -> dict[str, object]:
    validator = _load_validator()
    return validator.build_attestation(
        event=fixture.event,
        repo_root=REPO_ROOT,
        source_pulls=fixture.source_pulls,
        check_runs=fixture.check_runs,
        requirements_run=fixture.requirements_run,
        authority_run=fixture.authority_run,
        artifacts=fixture.artifacts,
        producer_archive=fixture.producer_archive,
        execution_archive=fixture.execution_archive,
        git_runner=fixture.run_git,
    )


def _write_cli_inputs(tmp_path: Path, fixture: _PromotionFixture) -> _CliInputs:
    inputs = _CliInputs(
        event=tmp_path / "event.json",
        source_pulls=tmp_path / "source-pulls.json",
        check_runs=tmp_path / "check-runs.json",
        requirements_run=tmp_path / "requirements-run.json",
        authority_run=tmp_path / "authority-run.json",
        artifacts=tmp_path / "artifacts.json",
    )
    for path, value in (
        (inputs.event, fixture.event),
        (inputs.source_pulls, fixture.source_pulls),
        (inputs.check_runs, fixture.check_runs),
        (inputs.requirements_run, fixture.requirements_run),
        (inputs.authority_run, fixture.authority_run),
        (inputs.artifacts, fixture.artifacts),
    ):
        _write_json(path, value)
    return inputs


def _cli_arguments(
    fixture: _PromotionFixture,
    inputs: _CliInputs,
    output: Path,
    expected_attestation: Path | None = None,
) -> list[str]:
    arguments = [
        "--event",
        str(inputs.event),
        "--repo-root",
        str(REPO_ROOT),
        "--source-pulls",
        str(inputs.source_pulls),
        "--check-runs",
        str(inputs.check_runs),
        "--requirements-run",
        str(inputs.requirements_run),
        "--authority-run",
        str(inputs.authority_run),
        "--artifacts",
        str(inputs.artifacts),
        "--producer-archive",
        str(fixture.producer_archive),
        "--execution-archive",
        str(fixture.execution_archive),
        "--output",
        str(output),
    ]
    if expected_attestation is not None:
        arguments.extend(("--expected-attestation", str(expected_attestation)))
    return arguments


def _assert_cli_contract(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    tmp_path.mkdir(parents=True)
    validator = _load_validator()
    fixture = _promotion_fixture(tmp_path)
    inputs = _write_cli_inputs(tmp_path, fixture)
    attestation: dict[str, object] = {"claim": "promotion-reused", "source_head": SOURCE_SHA}
    captured: dict[str, object] = {}

    def accepted_build(**keywords: object) -> dict[str, object]:
        captured.update(keywords)
        return attestation

    monkeypatch.setattr(validator, "build_attestation", accepted_build)
    first_output = tmp_path / "first.json"
    second_output = tmp_path / "second.json"
    assert validator.main(_cli_arguments(fixture, inputs, first_output)) == 0
    assert validator.main(_cli_arguments(fixture, inputs, second_output)) == 0
    assert first_output.read_bytes() == second_output.read_bytes() == _json_bytes(attestation)
    assert "git_runner" not in captured
    assert captured["repo_root"] == REPO_ROOT

    expected = tmp_path / "expected.json"
    expected.write_bytes(b"{}\n")
    rejected_output = tmp_path / "rejected.json"
    assert validator.main(_cli_arguments(fixture, inputs, rejected_output, expected)) == 1
    assert not rejected_output.exists()

    def rejected_build(**_keywords: object) -> dict[str, object]:
        raise validator.PromotionReuseError

    monkeypatch.setattr(validator, "build_attestation", rejected_build)
    invalid_output = tmp_path / "invalid.json"
    assert validator.main(_cli_arguments(fixture, inputs, invalid_output)) == 1
    assert not invalid_output.exists()


def _assert_default_git_runner(tmp_path: Path) -> None:
    validator = _load_validator()
    repo_root = tmp_path / "git-repository"
    repo_root.mkdir()
    git_environment = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("GIT_CONFIG_")
        and key not in {"GIT_COMMON_DIR", "GIT_DIR", "GIT_INDEX_FILE", "GIT_TEMPLATE_DIR", "GIT_WORK_TREE"}
    }
    git_environment.update(
        {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "XDG_CONFIG_HOME": str(tmp_path / "xdg"),
        }
    )
    git_command = ["git", "-c", f"core.hooksPath={os.devnull}"]
    subprocess.run([*git_command, "init", "--quiet", "--template="], cwd=repo_root, check=True, env=git_environment)
    subprocess.run(
        [*git_command, "config", "user.email", "proof@example.test"],
        cwd=repo_root,
        check=True,
        env=git_environment,
    )
    subprocess.run([*git_command, "config", "user.name", "Proof"], cwd=repo_root, check=True, env=git_environment)
    (repo_root / "proof.txt").write_text("proof\n", encoding="utf-8")
    subprocess.run([*git_command, "add", "proof.txt"], cwd=repo_root, check=True, env=git_environment)
    subprocess.run(
        [*git_command, "commit", "--quiet", "--no-gpg-sign", "-m", "proof"],
        cwd=repo_root,
        check=True,
        env=git_environment,
    )
    expected = subprocess.run(
        [*git_command, "rev-parse", "HEAD"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        env=git_environment,
        text=True,
    ).stdout.strip()
    assert validator._run_git(repo_root, ["rev-parse", "HEAD"]) == expected


def _assert_rejected(validator: types.ModuleType, fixture: _PromotionFixture) -> None:
    with pytest.raises(validator.PromotionReuseError):
        _validate(fixture)


def test_exact_protected_promotion_produces_canonical_attestation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _promotion_fixture(tmp_path)

    attestation = _validate(fixture)

    assert "git_facts" not in inspect.signature(_load_validator().build_attestation).parameters
    assert attestation["claim"] == "promotion-reused"
    assert attestation["promotion"] == {
        "base_ref": "main",
        "base_sha": BASE_SHA,
        "head_ref": "dev",
        "head_sha": HEAD_SHA,
        "head_tree": HEAD_TREE,
        "pull_request": 691,
    }
    source = attestation["source_pull_request"]
    assert isinstance(source, dict)
    assert source["number"] == 714
    assert source["head_sha"] == SOURCE_SHA
    assert ("merge-base", "--is-ancestor", BASE_SHA, HEAD_SHA) in fixture.git_calls
    assert ("rev-parse", f"{SOURCE_SHA}^{{tree}}") in fixture.git_calls

    failed_git = _promotion_fixture(tmp_path)
    failed_git.git_failures.add(("rev-parse", "HEAD"))
    _assert_rejected(_load_validator(), failed_git)
    _assert_cli_contract(tmp_path / "cli", monkeypatch)
    _assert_default_git_runner(tmp_path)


def test_lookalike_promotion_is_rejected(tmp_path: Path) -> None:
    validator = _load_validator()
    for field_path, value in (
        (("pull_request", "head", "repo", "id"), 999),
        (("pull_request", "head", "repo", "full_name"), "fork/specfact-cli"),
        (("pull_request", "base", "ref"), "release"),
        (("pull_request", "head", "ref"), "dev-lookalike"),
    ):
        fixture = _promotion_fixture(tmp_path)
        _set_nested(fixture.event, field_path, value)
        _assert_rejected(validator, fixture)


def _assert_field_mutations_rejected(
    validator: types.ModuleType,
    tmp_path: Path,
    target_name: str,
    mutations: tuple[tuple[tuple[str, ...], object], ...],
) -> None:
    for field_path, value in mutations:
        fixture = _promotion_fixture(tmp_path)
        target = cast(dict[str, object], getattr(fixture, target_name))
        _set_nested(target, field_path, value)
        _assert_rejected(validator, fixture)


def _assert_source_pull_mutations_rejected(validator: types.ModuleType, tmp_path: Path) -> None:
    mutations: tuple[tuple[tuple[str, ...], object], ...] = (
        (("state",), "open"),
        (("merged_at",), None),
        (("merge_commit_sha",), "9" * 40),
        (("base", "ref"), "main"),
        (("base", "sha"), "9" * 40),
        (("base", "repo", "id"), 999),
        (("base", "repo", "full_name"), "fork/specfact-cli"),
        (("head", "ref"), "other-source"),
        (("head", "sha"), "9" * 40),
        (("head", "repo", "id"), 999),
        (("head", "repo", "full_name"), "fork/specfact-cli"),
    )
    for field_path, value in mutations:
        fixture = _promotion_fixture(tmp_path)
        source_pull = cast(dict[str, object], fixture.source_pulls[1])
        _set_nested(source_pull, field_path, value)
        _assert_rejected(validator, fixture)
    duplicate = _promotion_fixture(tmp_path)
    other_pull = copy.deepcopy(cast(dict[str, object], duplicate.source_pulls[1]))
    other_pull["number"] = 715
    duplicate.source_pulls.append(other_pull)
    _assert_rejected(validator, duplicate)


def _assert_check_and_run_mutations_rejected(validator: types.ModuleType, tmp_path: Path) -> None:
    for check_index in (0, 1):
        for field_path, value in (
            (("status",), "in_progress"),
            (("conclusion",), "failure"),
            (("head_sha",), "9" * 40),
            (("app", "id"), 999),
            (("app", "slug"), "spoof"),
            (("app", "owner", "login"), "spoof"),
            (("details_url",), f"https://github.com/{REPOSITORY}/actions/runs/999/job/1"),
        ):
            fixture = _promotion_fixture(tmp_path)
            _set_nested(_object_list(fixture.check_runs, "check_runs")[check_index], field_path, value)
            _assert_rejected(validator, fixture)
    for check_index in (0, 1):
        duplicate = _promotion_fixture(tmp_path)
        checks = _object_list(duplicate.check_runs, "check_runs")
        checks.append(copy.deepcopy(checks[check_index]))
        duplicate.check_runs["total_count"] = len(checks)
        _assert_rejected(validator, duplicate)
    incomplete_checks = _promotion_fixture(tmp_path)
    incomplete_checks.check_runs["total_count"] = 5
    _assert_rejected(validator, incomplete_checks)
    for target_name in ("requirements_run", "authority_run"):
        _assert_field_mutations_rejected(
            validator,
            tmp_path,
            target_name,
            (
                (("event",), "push"),
                (("id",), 999),
                (("name",), "Spoofed workflow"),
                (("status",), "in_progress"),
                (("conclusion",), "failure"),
                (("head_sha",), "9" * 40),
                (("head_branch",), "other"),
                (("repository", "id"), 999),
                (("repository", "full_name"), "fork/specfact-cli"),
            ),
        )
    _assert_field_mutations_rejected(
        validator,
        tmp_path,
        "requirements_run",
        (
            (("path",), ".github/workflows/spoof.yml"),
            (("workflow_id",), 999),
            (("workflow_url",), f"https://api.github.com/repos/{REPOSITORY}/actions/workflows/999"),
        ),
    )
    _assert_field_mutations_rejected(
        validator,
        tmp_path,
        "authority_run",
        (
            (("path",), ".github/workflows/spoof.yml"),
            (("workflow_id",), 999),
            (
                ("workflow_url",),
                f"https://api.github.com/repos/{REPOSITORY}/actions/workflows/{AUTHORITY_WORKFLOW_ID}",
            ),
        ),
    )


def _assert_artifact_metadata_mutations_rejected(validator: types.ModuleType, tmp_path: Path) -> None:
    for artifact_index in (0, 1):
        for field_path, value in (
            (("id",), 0),
            (("name",), "spoofed-evidence"),
            (("expired",), True),
            (("digest",), f"sha256:{'0' * 64}"),
            (("workflow_run", "id"), 999),
            (("workflow_run", "head_sha"), "9" * 40),
            (("workflow_run", "head_branch"), "other-source"),
            (("workflow_run", "head_repository_id"), 999),
            (("workflow_run", "repository_id"), 999),
        ):
            fixture = _promotion_fixture(tmp_path)
            _set_nested(_object_list(fixture.artifacts, "artifacts")[artifact_index], field_path, value)
            _assert_rejected(validator, fixture)
    for artifact_index in (0, 1):
        missing = _promotion_fixture(tmp_path)
        _object_list(missing.artifacts, "artifacts").pop(artifact_index)
        _assert_rejected(validator, missing)
        duplicate = _promotion_fixture(tmp_path)
        artifacts = _object_list(duplicate.artifacts, "artifacts")
        artifacts.append(copy.deepcopy(artifacts[artifact_index]))
        duplicate.artifacts["total_count"] = len(artifacts)
        _assert_rejected(validator, duplicate)
    incomplete_artifacts = _promotion_fixture(tmp_path)
    incomplete_artifacts.artifacts["total_count"] = 3
    _assert_rejected(validator, incomplete_artifacts)


def _assert_archive_semantic_mutations_rejected(validator: types.ModuleType, tmp_path: Path) -> None:
    report_mutations: tuple[tuple[tuple[str, ...], object], ...] = (
        (("verdict",), "failed"),
        (("gate_decision",), "fail"),
        (("required_maturity",), "planned"),
        (("observed_maturity",), "red"),
        (("delivery_status",), "proposal-only"),
        (("implementation_evidence",), "not-yet-available"),
        (("mapping_digest",), f"sha256:{'9' * 64}"),
        (("plan_digest",), f"sha256:{'9' * 64}"),
        (("execution_proof", "source_ref"), "9" * 40),
        (("execution_proof", "proof_basis"), "untrusted"),
        (("execution_proof", "selectors"), ["tests/test_other.py::test_other"]),
        (("execution_proof", "junit_digest"), f"sha256:{'9' * 64}"),
    )
    for field_path, value in report_mutations:
        fixture = _promotion_fixture(tmp_path)
        _rewrite_json_member(fixture.producer_archive, "requirements-evidence.json", field_path, value)
        _refresh_artifact_digest(fixture, 0, fixture.producer_archive)
        _assert_rejected(validator, fixture)
    for member in ("requirements-evidence.json", "requirements-evidence-plan.json", "requirements-proof.xml"):
        fixture = _promotion_fixture(tmp_path)
        files = _archive_files(fixture.producer_archive)
        files.pop(member)
        _write_archive(fixture.producer_archive, files)
        _refresh_artifact_digest(fixture, 0, fixture.producer_archive)
        _assert_rejected(validator, fixture)
    tampered_junit = _promotion_fixture(tmp_path)
    files = _archive_files(tampered_junit.producer_archive)
    files["requirements-proof.xml"] += b"tampered"
    _write_archive(tampered_junit.producer_archive, files)
    _refresh_artifact_digest(tampered_junit, 0, tampered_junit.producer_archive)
    _assert_rejected(validator, tampered_junit)
    producer_plan = _promotion_fixture(tmp_path)
    _rewrite_json_member(
        producer_plan.producer_archive,
        "requirements-evidence-plan.json",
        ("plan", "plan_digest"),
        f"sha256:{'9' * 64}",
    )
    _refresh_artifact_digest(producer_plan, 0, producer_plan.producer_archive)
    _assert_rejected(validator, producer_plan)
    mismatched_case = _promotion_fixture(tmp_path)
    _rewrite_json_member(
        mismatched_case.producer_archive,
        "requirements-evidence-plan.json",
        ("plan", "cases"),
        [
            {
                "method": "test",
                "node_id": "tests/test_other.py::test_other",
                "selector": {"runner": "pytest", "node_id": "tests/test_other.py::test_other"},
            }
        ],
    )
    _refresh_artifact_digest(mismatched_case, 0, mismatched_case.producer_archive)
    _assert_rejected(validator, mismatched_case)
    execution_plan = _promotion_fixture(tmp_path)
    _rewrite_json_member(
        execution_plan.execution_archive,
        "requirements-evidence-plan.json",
        ("mapping_digest",),
        f"sha256:{'9' * 64}",
    )
    _refresh_artifact_digest(execution_plan, 1, execution_plan.execution_archive)
    _assert_rejected(validator, execution_plan)


def test_incomplete_or_stale_promotion_provenance_is_rejected(tmp_path: Path) -> None:
    validator = _load_validator()
    for git_command, value in (
        (("rev-parse", "HEAD"), "9" * 40),
        (("rev-parse", "HEAD^{tree}"), "9" * 40),
        (("rev-parse", "refs/remotes/origin/main^{commit}"), "9" * 40),
        (("rev-parse", "refs/remotes/origin/dev^{commit}"), "9" * 40),
        (("rev-list", "--parents", "-n", "1", HEAD_SHA), f"{HEAD_SHA} {PREVIOUS_DEV_SHA} {'9' * 40}"),
        (("rev-parse", f"{SOURCE_SHA}^{{tree}}"), "9" * 40),
    ):
        fixture = _promotion_fixture(tmp_path)
        fixture.git_outputs[git_command] = value
        _assert_rejected(validator, fixture)
    diverged = _promotion_fixture(tmp_path)
    diverged.git_failures.add(("merge-base", "--is-ancestor", BASE_SHA, HEAD_SHA))
    _assert_rejected(validator, diverged)
    for commit in (BASE_SHA, HEAD_SHA, PREVIOUS_DEV_SHA, SOURCE_SHA):
        missing_commit = _promotion_fixture(tmp_path)
        missing_commit.git_failures.add(("cat-file", "-t", commit))
        _assert_rejected(validator, missing_commit)
    _assert_source_pull_mutations_rejected(validator, tmp_path)
    _assert_check_and_run_mutations_rejected(validator, tmp_path)
    _assert_artifact_metadata_mutations_rejected(validator, tmp_path)
    _assert_archive_semantic_mutations_rejected(validator, tmp_path)

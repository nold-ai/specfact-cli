"""Authenticate the docs fixture, then assert its real native pytest evidence policy."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import time
from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Protocol

import pytest
import yaml
from pydantic import BaseModel, Field


REPO_ROOT = Path(__file__).resolve().parents[3]
PUBLIC_ORIGIN = "https://github.com/nold-ai/specfact-cli-modules.git"
CASES = ("skip", "xfail", "xpass", "xpass-empty", "missing-source-coverage", "low-source-coverage")
ACQUISITION_RECEIPT = pytest.StashKey[dict[str, Any]]()
ISOLATED_LAUNCH = """
import json, runpy, sys
source, paths, *arguments = sys.argv[1:]
sys.path[:0] = json.loads(paths)
sys.argv = [source, *arguments]
runpy.run_path(source, run_name="__main__")
"""


class FixtureLock(BaseModel):
    """Immutable source selected by the unchanged documentation lock."""

    repository: str = Field(pattern=r"^nold-ai/specfact-cli-modules$", description="Fixed public source repository.")
    commit: str = Field(pattern=r"^[0-9a-f]{40}$", description="Immutable source commit.")
    tree: str = Field(pattern=r"^[0-9a-f]{40}$", description="Expected complete source tree.")


class Finding(BaseModel):
    """Actual module finding fields used by the behavioral assertion."""

    rule: str = Field(description="Actual selected module finding rule.")
    severity: str = Field(description="Actual selected module finding severity.")
    message: str = Field(description="Actual selected module diagnostic.")


class CaseEvidence(BaseModel):
    """Native execution preconditions and unchanged adapter result."""

    case: str = Field(description="Selected native scenario.")
    native_exit: int = Field(description="Actual native pytest subprocess exit.")
    observation: dict[str, Any] = Field(description="Actual selected Observer evidence and native coverage.")
    outcomes: list[dict[str, Any]] = Field(description="Independent native phase records establishing preconditions.")
    findings: list[Finding] = Field(description="Findings returned by the actual selected portable adapter.")


def _environment() -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if key in {"PATH", "HOME", "LANG", "TMPDIR"}}
    env.update(
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_CONFIG_NOSYSTEM="1",
        GIT_TERMINAL_PROMPT="0",
        GIT_ASKPASS="",
        PYTHONDONTWRITEBYTECODE="1",
        PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
        PYTEST_ADDOPTS="",
    )
    return env


def _git(checkout: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-c", "credential.helper=", "-c", "core.hooksPath=/dev/null", "-C", str(checkout), *arguments],
        env=_environment(),
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    if result.returncode:
        raise RuntimeError(f"docs_fixture_acquisition:{arguments[0]}:{result.stderr.strip()}")
    return result.stdout.strip()


def _identity(checkout: Path, lock: FixtureLock) -> None:
    expected = (PUBLIC_ORIGIN, lock.commit, lock.tree, "")
    actual = (
        _git(checkout, "remote", "get-url", "origin"),
        _git(checkout, "rev-parse", "HEAD"),
        _git(checkout, "rev-parse", "HEAD^{tree}"),
        _git(checkout, "status", "--porcelain", "--untracked-files=all"),
    )
    if actual != expected:
        raise RuntimeError("docs_fixture_identity: public origin, exact HEAD/tree and clean checkout are required")


def _trusted_verification(checkout: Path) -> int:
    path = REPO_ROOT / "scripts/verify_docs_module_source.py"
    spec = importlib.util.spec_from_file_location("docs17_core_authenticator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("docs_fixture_authentication: trusted core verifier unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.verify_source(checkout, trusted_root=REPO_ROOT)


def _acquisition_receipt(
    checkout: Path, lock: FixtureLock, count: int, transport: str, started: float
) -> dict[str, Any]:
    manifest = checkout / "packages/specfact-code-review/module-package.yaml"
    identities = {
        name: hashlib.sha256((REPO_ROOT / name).read_bytes()).hexdigest()
        for name in (
            "scripts/verify_docs_module_source.py",
            "scripts/verify-modules-signature.py",
            "resources/keys/module-signing-public.pem",
        )
    }
    return {
        "expected": lock.model_dump(),
        "actual_commit": _git(checkout, "rev-parse", "HEAD"),
        "actual_tree": _git(checkout, "rev-parse", "HEAD^{tree}"),
        "verified_bundles": count,
        "manifest_version": yaml.safe_load(manifest.read_text())["version"],
        "manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
        "trusted_inputs_sha256": identities,
        "transport": transport,
        "seconds": time.monotonic() - started,
    }


@pytest.fixture(scope="session")
def authenticated_docs_source(
    tmp_path_factory: pytest.TempPathFactory, request: pytest.FixtureRequest
) -> Iterator[Path]:
    lock = FixtureLock.model_validate_json((REPO_ROOT / "ci/docs-module-fixture.lock.json").read_text(), strict=True)
    started = time.monotonic()
    private = tmp_path_factory.mktemp("docs17-authenticated-source")
    checkout = Path(os.environ.get("SPECFACT_DOCS_MODULES_REPO", private / "checkout")).resolve()
    transport = "verified-existing-public-checkout"
    try:
        _identity(checkout, lock)
    except (RuntimeError, OSError):
        checkout = private / "checkout"
        checkout.mkdir()
        _git(checkout, "init", "--quiet")
        _git(checkout, "remote", "add", "origin", PUBLIC_ORIGIN)
        _git(checkout, "fetch", "--depth=1", "--no-tags", "origin", lock.commit)
        _git(checkout, "checkout", "--detach", "--quiet", "FETCH_HEAD")
        transport = "private-public-https-exact-commit-fetch"
    _identity(checkout, lock)
    count = _trusted_verification(checkout)
    receipt = _acquisition_receipt(checkout, lock, count, transport, started)
    (private / "acquisition-receipt.json").write_text(json.dumps(receipt, indent=2))
    request.config.stash[ACQUISITION_RECEIPT] = receipt
    yield checkout
    _identity(checkout, lock)
    _trusted_verification(checkout)


def _isolated_command(checkout: Path, action: str, *arguments: str) -> list[str]:
    paths = [str(path) for path in sorted((checkout / "packages").glob("*/src"))]
    paths.extend((str(REPO_ROOT / "src"), str(Path(pytest.__file__).resolve().parents[1])))
    return [
        sys.executable,
        "-B",
        "-I",
        "-S",
        "-c",
        ISOLATED_LAUNCH,
        __file__,
        json.dumps(paths),
        action,
        str(checkout),
        *arguments,
    ]


def _project(root: Path, case: str) -> tuple[Path, str]:
    project = root / "project"
    (project / "src").mkdir(parents=True)
    (project / "tests").mkdir()
    (project / "pytest.ini").write_text("[pytest]\npythonpath = src\n")
    app = project / "src/app.py"
    app.write_text("VALUE = 1\n")
    (project / "src/other.py").write_text("VALUE = 1\n")
    tests = "import pytest\nimport app\ndef test_good(): assert app.VALUE == 1\n"
    coverage_target = "app"
    match case:
        case "skip":
            tests += "def test_affected(): pytest.skip('expected')\n"
        case "xfail":
            tests += "@pytest.mark.xfail(reason='expected')\ndef test_affected(): assert False\n"
        case "xpass" | "xpass-empty":
            reason = "" if case == "xpass-empty" else "expected"
            tests += f"@pytest.mark.xfail(reason={reason!r},strict=False)\ndef test_affected(): assert True\n"
        case "missing-source-coverage":
            tests = "import other\ndef test_good(): assert other.VALUE == 1\n"
            coverage_target = "other"
        case "low-source-coverage":
            app.write_text("VALUE = 1\n" + "\n".join(f"def unused_{i}():\n    return {i}" for i in range(12)) + "\n")
        case _:
            raise RuntimeError(f"docs_fixture_scenario_unknown:{case}")
    (project / "tests/test_app.py").write_text(tests)
    return project, coverage_target


class NativePreconditions:
    """Collect independent actual report markers without replacing the selected Observer."""

    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []

    def pytest_runtest_logreport(self, report: Any) -> None:
        self.records.append(
            {
                "phase": report.when,
                "outcome": report.outcome,
                "has_xfail": hasattr(report, "wasxfail"),
                "wasxfail": getattr(report, "wasxfail", None),
            }
        )


def _native(checkout: Path, output: Path, coverage_target: str) -> None:
    target_pytest = importlib.import_module("specfact_code_review.run.target_pytest")

    if not target_pytest.__file__ or not Path(target_pytest.__file__).resolve().is_relative_to(checkout):
        raise RuntimeError("docs_fixture_import_origin: observer did not come from authenticated source")
    pytest.MonkeyPatch().setattr(target_pytest, "SNAPSHOT_ROOT", Path.cwd(), raising=False)
    for name in ("pytest_xdist_node_collection_finished", "pytest_testnodedown"):
        pytest.hookimpl(optionalhook=True)(getattr(target_pytest.Observer, name))
    observer, independent = target_pytest.Observer(), NativePreconditions()
    coverage_output = output.with_suffix(".coverage.json")
    code = pytest.main(
        [
            "-q",
            "-p",
            "pytest_cov",
            f"--cov={coverage_target}",
            f"--cov-report=json:{coverage_output}",
            "--cov-fail-under=0",
            "--rootdir=.",
            "-o",
            f"cache_dir={output.with_suffix('.cache')}",
            "tests",
        ],
        plugins=[observer, independent],
    )
    observation = {
        "exit_code": int(code),
        "collected": sorted(observer.collected),
        "deselected": sorted(observer.deselected),
        "records": observer.records,
        "collection_errors": observer.collection_errors,
        "internal_errors": observer.internal_errors,
        "coverage": json.loads(coverage_output.read_text()),
        "coverage_threshold": getattr(observer, "coverage_threshold", None),
        "test_roots": getattr(observer, "test_roots", []),
        "pytest_root": getattr(observer, "pytest_root", "."),
    }
    output.write_text(json.dumps({"observation": observation, "outcomes": independent.records}))
    raise SystemExit(int(code))


def _consume_observation(worker: Any, project: Path, output: Path, observation: dict[str, Any]) -> list[Any]:
    """Replay only capsule transport while retaining the selected module's policy."""
    payload = json.dumps(observation)

    def replay(*_args: Any, **_kwargs: Any) -> SimpleNamespace:
        output.write_text(payload)
        return SimpleNamespace(returncode=observation["exit_code"])

    with pytest.MonkeyPatch.context() as patch:
        patch.chdir(project)
        patch.setattr(
            worker,
            "Path",
            lambda value: output if value == "/opt/specfact/tmp/pytest-observation.json" else Path(value),
        )
        patch.setattr(worker, "target_command", lambda *_args: ["native-observation-already-executed"])
        patch.setattr(worker, "subprocess", SimpleNamespace(run=replay, SubprocessError=subprocess.SubprocessError))
        return worker.run_portable_pytest(
            [project / "src/app.py", project / "tests/test_app.py"],
            ("portable-pytest-v2", '{"selectors":["tests/test_app.py"]}'),
        )


def _adapter(checkout: Path, case: str, root: Path, output: Path) -> None:
    portable_worker = importlib.import_module("specfact_code_review.run.portable_worker")

    if not portable_worker.__file__ or not Path(portable_worker.__file__).resolve().is_relative_to(checkout):
        raise RuntimeError("docs_fixture_import_origin: adapter did not come from authenticated source")
    project, coverage_target = _project(root, case)
    native_output = root / "native-observation.json"
    env = _environment()
    env["COVERAGE_FILE"] = str(root / ".coverage")
    result = subprocess.run(
        _isolated_command(checkout, "native", str(native_output), coverage_target),
        cwd=project,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    (root / "native-output.txt").write_text(result.stdout + result.stderr)
    if result.returncode != 0:
        raise RuntimeError(f"docs_fixture_native_execution:{result.returncode}:{result.stdout}:{result.stderr}")
    native = json.loads(native_output.read_text())
    observation = native["observation"]
    findings = _consume_observation(portable_worker, project, native_output, observation)
    evidence = CaseEvidence(
        case=case,
        native_exit=result.returncode,
        observation=observation,
        outcomes=native["outcomes"],
        findings=[Finding(rule=row.rule, severity=row.severity, message=row.message) for row in findings],
    )
    output.write_text(evidence.model_dump_json(indent=2))


def _coverage_precondition(case: str, rows: dict[str, Any]) -> bool:
    if not rows:
        return False
    source = next((row for path, row in rows.items() if path.endswith("src/app.py")), None)
    if case == "missing-source-coverage":
        return source is None
    if source is None:
        return False
    percent = source["summary"]["percent_covered"]
    return 0 < percent < 80 if case == "low-source-coverage" else percent == 100


def _outcome_precondition(case: str, outcomes: list[dict[str, Any]]) -> bool:
    calls = [row for row in outcomes if row["phase"] == "call"]
    states = {(row["outcome"], row["has_xfail"]) for row in calls}
    if ("passed", False) not in states:
        return False
    expected = {
        "skip": ("skipped", False),
        "xfail": ("skipped", True),
        "xpass": ("passed", True),
        "xpass-empty": ("passed", True),
    }
    if case not in expected:
        return states == {("passed", False)}
    outcome, marker = expected[case]
    affected = [row for row in calls if (row["outcome"], row["has_xfail"]) == (outcome, marker)]
    if case == "xpass-empty":
        return any(row["wasxfail"] == "" for row in affected)
    return bool(affected)


def _preconditions(evidence: CaseEvidence) -> None:
    observation = evidence.observation
    if evidence.native_exit != 0 or observation["exit_code"] != 0 or not observation["collected"]:
        raise RuntimeError("docs_fixture_native_precondition: actual successful collection/execution is required")
    if observation["collection_errors"] or observation["internal_errors"]:
        raise RuntimeError("docs_fixture_native_precondition: native collection/internal error")
    if not _coverage_precondition(evidence.case, observation["coverage"]["files"]):
        raise RuntimeError(f"docs_fixture_native_precondition:{evidence.case}: unexpected actual coverage")
    if not _outcome_precondition(evidence.case, evidence.outcomes):
        raise RuntimeError(f"docs_fixture_native_precondition:{evidence.case}: unexpected actual test outcomes")


class ScenarioRequest(Protocol):
    """Typed function-scoped pytest request used by the scenario fixture."""

    param: str
    node: pytest.Item
    config: pytest.Config


@pytest.fixture
def scenario_result(request: ScenarioRequest, authenticated_docs_source: Path, tmp_path: Path) -> CaseEvidence:
    node = request.node
    node.user_properties.append(("docs_fixture_acquisition", json.dumps(request.config.stash[ACQUISITION_RECEIPT])))
    output = tmp_path / "adapter-evidence.json"
    result = subprocess.run(
        _isolated_command(authenticated_docs_source, "adapter", request.param, str(tmp_path), str(output)),
        cwd=REPO_ROOT,
        env=_environment(),
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f"docs_fixture_adapter_precondition:{result.stdout}:{result.stderr}")
    evidence = CaseEvidence.model_validate_json(output.read_text(), strict=True)
    _preconditions(evidence)
    node.user_properties.append(("docs_fixture_native_evidence", evidence.model_dump_json()))
    return evidence


@pytest.mark.parametrize("scenario_result", CASES, indirect=True)
def test_documentation_fixture_enforces_portable_pytest_policy(scenario_result: CaseEvidence) -> None:
    """Only the required actual error finding satisfies documentation fixture selection."""
    case = scenario_result.case
    expected = "TEST_COVERAGE_LOW" if case == "low-source-coverage" else "TEST_OUTCOME_NOT_PASS"
    if case == "missing-source-coverage":
        valid = any(
            row.rule == "tool_error"
            and row.severity == "error"
            and "coverage" in row.message.lower()
            and "missing" in row.message.lower()
            for row in scenario_result.findings
        )
    else:
        valid = any(row.rule == expected and row.severity == "error" for row in scenario_result.findings)
    assert valid, f"documentation fixture permits falsely passing portable pytest evidence: {case}"


if __name__ == "__main__":
    mode, source, *inputs = sys.argv[1:]
    if mode == "native":
        _native(Path(source), Path(inputs[0]), inputs[1])
    elif mode == "adapter":
        _adapter(Path(source), inputs[0], Path(inputs[1]), Path(inputs[2]))
    else:
        raise RuntimeError(f"docs_fixture_unknown_execution_mode:{mode}")

"""Contract tests for the core-owned Requirements proof executor."""

from __future__ import annotations

import importlib.util
import json
import platform
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Protocol, cast

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
EXECUTOR_SCRIPT = REPO_ROOT / "scripts" / "requirements_proof_executor.py"
pytest_runtime = cast(Any, pytest)


class MonkeyPatch(Protocol):
    """Typed subset of pytest's fixture used by these executor contracts."""

    def setenv(self, name: str, value: str) -> None:
        raise NotImplementedError

    def setattr(self, target: object, name: str, value: object) -> None:
        raise NotImplementedError


class ProofCommand(Protocol):
    """Typed command fields observed by the proof-executor unit tests."""

    arguments: list[str]
    cwd: Path
    env: dict[str, str]
    shell: bool
    timeout: int


class ExecutorModule(Protocol):
    """Minimal typed surface of the proof-execution boundary."""

    def selectors_from_plan(self, plan: dict[str, object], repo_root: Path) -> list[str]:
        raise NotImplementedError

    def execute_plan(
        self,
        plan: dict[str, object],
        repo_root: Path,
        junit_path: Path,
        **kwargs: object,
    ) -> int:
        raise NotImplementedError

    def main(self, argv: list[str] | None) -> int:
        raise NotImplementedError


def _load_executor_module() -> ExecutorModule:
    spec = importlib.util.spec_from_file_location("requirements_proof_executor", EXECUTOR_SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError("Requirements proof executor must be importable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return cast(ExecutorModule, module)


def _plan(*selectors: str) -> dict[str, object]:
    return {
        "schema_version": "2",
        "gate_decision": "pass",
        "observed_maturity": "test-authored",
        "plan": {
            "cases": [
                {
                    "method": "test",
                    "selector": {"runner": "pytest", "node_id": selector},
                    "node_id": selector,
                }
                for selector in selectors
            ]
        },
    }


def _write_selected_test(tmp_path: Path) -> None:
    test_file = tmp_path / "tests" / "test_proof.py"
    test_file.parent.mkdir()
    test_file.write_text("def test_selected() -> None: pass\n", encoding="utf-8")


def _assert_argument_contract(command: ProofCommand, junit_path: Path) -> None:
    assert command.shell is False
    assert command.arguments[:3] == [sys.executable, "-P", "-c"]
    bootstrap = command.arguments[3]
    assert bootstrap.index("import pytest") < bootstrap.index("sys.path.append(repo_root)")
    assert command.arguments[4:] == [
        str(junit_path.parents[1]),
        "--junitxml",
        str(junit_path),
        "-p",
        "scripts.requirements_proof_pytest_plugin",
        "--",
        "tests/test_proof.py::test_selected",
    ]


def _assert_environment_contract(command: ProofCommand) -> None:
    environment = command.env
    assert environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "1"
    assert environment["SPECFACT_MODULES_REPO"] == "/verified/modules"
    assert environment["SPECFACT_MODULES_ROOTS"] == "/verified/modules/packages"
    assert not {"PYTEST_ADDOPTS", "PYTEST_PLUGINS", "PYTHONPATH"} & environment.keys()


def test_executor_accepts_existing_exact_selectors_and_uses_argument_array(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """Only existing exact pytest node IDs may reach the no-shell invocation."""
    module = _load_executor_module()
    _write_selected_test(tmp_path)
    plan = _plan("tests/test_proof.py::test_selected")
    junit_path = tmp_path / "artifacts" / "proof.xml"
    captured: ProofCommand | None = None

    for name, value in (
        ("PYTEST_ADDOPTS", "--collect-only"),
        ("PYTEST_PLUGINS", "untrusted_plugin"),
        ("PYTHONPATH", "/untrusted/python"),
        ("SPECFACT_MODULES_REPO", "/verified/modules"),
        ("SPECFACT_MODULES_ROOTS", "/verified/modules/packages"),
    ):
        monkeypatch.setenv(name, value)

    def capture_command(command: ProofCommand) -> int:
        nonlocal captured
        captured = command
        return 0

    observed = module.execute_plan(
        plan,
        tmp_path,
        junit_path,
        command_runner=capture_command,
    )

    assert observed == 0
    assert module.selectors_from_plan(plan, tmp_path) == ["tests/test_proof.py::test_selected"]
    assert captured is not None
    assert captured.cwd == tmp_path
    _assert_argument_contract(captured, junit_path)
    _assert_environment_contract(captured)


def test_executor_rejects_unsafe_selectors_before_spawning(tmp_path: Path) -> None:
    """Path escapes, option injection, globs, and shell syntax are never executable."""
    module = _load_executor_module()
    _write_selected_test(tmp_path)

    for selector in (
        "/tmp/test_proof.py::test_selected",
        "../tests/test_proof.py::test_selected",
        "tests/test_proof.py::test_*",
        "-p.py::test_selected",
        "tests/test_proof.py::test_selected;touch pwned",
        "tests/test_proof.py::test_selected\tinjected",
    ):
        with pytest_runtime.raises(ValueError, match="invalid pytest selector"):
            module.execute_plan(_plan(selector), tmp_path, tmp_path / "proof.xml", command_runner=lambda _command: 0)


def test_executor_rejects_junit_destination_that_overlaps_selected_test(tmp_path: Path) -> None:
    """The executor must not unlink a selected repository input."""
    module = _load_executor_module()
    _write_selected_test(tmp_path)
    selected_test = tmp_path / "tests" / "test_proof.py"

    with pytest_runtime.raises(ValueError, match="overlaps a selected repository input"):
        module.execute_plan(
            _plan("tests/test_proof.py::test_selected"), tmp_path, selected_test, command_runner=lambda _command: 0
        )
    assert selected_test.exists()


def test_executor_rejects_existing_repository_file_as_junit_destination(tmp_path: Path) -> None:
    """The executor must not unlink a repository file unrelated to the selected test."""
    module = _load_executor_module()
    _write_selected_test(tmp_path)
    repository_input = tmp_path / "pyproject.toml"
    repository_input.write_text("[project]\nname = 'proof-target'\n", encoding="utf-8")

    with pytest_runtime.raises(ValueError, match="overlaps an existing repository input"):
        module.execute_plan(
            _plan("tests/test_proof.py::test_selected"), tmp_path, repository_input, command_runner=lambda _command: 0
        )
    assert repository_input.read_text(encoding="utf-8") == "[project]\nname = 'proof-target'\n"


def test_executor_rejects_duplicate_or_unsupported_plan_entries(tmp_path: Path) -> None:
    """A plan must contain unique supported pytest selector records."""
    module = _load_executor_module()
    test_file = tmp_path / "tests" / "test_proof.py"
    test_file.parent.mkdir()
    test_file.write_text("def test_selected() -> None: pass\n", encoding="utf-8")

    with pytest_runtime.raises(ValueError, match="duplicate pytest selector"):
        module.selectors_from_plan(
            _plan("tests/test_proof.py::test_selected", "tests/test_proof.py::test_selected"), tmp_path
        )
    with pytest_runtime.raises(ValueError, match="unsupported runner"):
        module.selectors_from_plan(
            {
                "schema_version": "2",
                "gate_decision": "pass",
                "observed_maturity": "test-authored",
                "plan": {"cases": [{"method": "test", "selector": {"runner": "unittest", "node_id": "tests/x.py::x"}}]},
            },
            tmp_path,
        )


def test_executor_rejects_unsupported_or_nonexecutable_plan_state_before_spawning(tmp_path: Path) -> None:
    """Only released, passing test-authored plan reports may reach pytest."""
    module = _load_executor_module()
    _write_selected_test(tmp_path)
    for field, value in (("schema_version", "3"), ("gate_decision", "fail"), ("observed_maturity", "planned")):
        plan = _plan("tests/test_proof.py::test_selected")
        plan[field] = value
        with pytest_runtime.raises(ValueError, match="invalid proof plan state"):
            module.execute_plan(plan, tmp_path, tmp_path / "proof.xml", command_runner=lambda _command: 0)


def test_executor_accepts_module_valid_pytest_node_ids(tmp_path: Path) -> None:
    """Parameterized and class-method node IDs remain exact safe argument values."""
    module = _load_executor_module()
    test_file = tmp_path / "tests" / "test_proof.py"
    test_file.parent.mkdir()
    test_file.write_text(
        "import pytest\n\n"
        "@pytest.mark.parametrize('label', ['first', 'second'], ids=['param-value', 'spec commands-commands0'])\n"
        "def test_parameterized(label: str) -> None: pass\n\n"
        "class TestProof:\n"
        "    def test_selected(self) -> None: pass\n\n"
        "class TestParameterizedProof:\n"
        "    @pytest.mark.parametrize('label', ['first'], ids=['param-value'])\n"
        "    def test_selected(self, label: str) -> None: pass\n",
        encoding="utf-8",
    )

    for selector in (
        "tests/test_proof.py::test_parameterized[param-value]",
        "tests/test_proof.py::test_parameterized[spec commands-commands0]",
        "tests/test_proof.py::TestProof::test_selected",
        "tests/test_proof.py::TestParameterizedProof::test_selected[param-value]",
    ):
        assert module.selectors_from_plan(_plan(selector), tmp_path) == [selector]


def test_executor_cli_reads_plan_and_forwards_no_shell_junit_path(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    """The command-line adapter parses a plan and sends validated arguments without a shell."""
    module = _load_executor_module()
    test_file = tmp_path / "tests" / "test_proof.py"
    test_file.parent.mkdir()
    test_file.write_text("def test_selected() -> None: pass\n", encoding="utf-8")
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(_plan("tests/test_proof.py::test_selected")), encoding="utf-8")
    junit_path = tmp_path / "artifacts" / "proof.xml"
    captured: ProofCommand | None = None

    def run_command(command: ProofCommand) -> int:
        nonlocal captured
        captured = command
        return 0

    monkeypatch.setattr(module, "_run_command", run_command)

    assert module.main(["--plan", str(plan_path), "--repo-root", str(tmp_path), "--junit", str(junit_path)]) == 0
    assert captured is not None
    assert captured.cwd == tmp_path
    _assert_argument_contract(captured, junit_path)


def test_executor_cli_rejects_malformed_plan_before_spawning(tmp_path: Path) -> None:
    """Malformed external plan data cannot reach the proof subprocess."""
    module = _load_executor_module()
    plan_path = tmp_path / "plan.json"
    plan_path.write_text("{not-json", encoding="utf-8")

    with pytest_runtime.raises(SystemExit, match="cannot read proof plan"):
        module.main(["--plan", str(plan_path), "--repo-root", str(tmp_path), "--junit", str(tmp_path / "proof.xml")])


def test_executor_records_canonical_selector_property_in_junit(tmp_path: Path) -> None:
    """Reconciliation receives the collected node ID, never a reconstructed JUnit label."""
    module = _load_executor_module()
    selector = "tests/fixtures/requirements_proof_target.py::test_records_canonical_selector"
    junit_path = tmp_path / "requirements-proof.xml"

    assert module.execute_plan(_plan(selector), REPO_ROOT, junit_path) == 0

    root = ET.parse(junit_path).getroot()
    assert root.find(".//property[@name='specfact.selector'][@value='" + selector + "']") is not None


def test_executor_records_proof_toolchain_identity_in_junit(tmp_path: Path) -> None:
    """Retained provenance must identify the interpreter and pytest process that ran the selector."""
    module = _load_executor_module()
    selector = "tests/fixtures/requirements_proof_target.py::test_records_canonical_selector"
    junit_path = tmp_path / "requirements-proof.xml"

    assert module.execute_plan(_plan(selector), REPO_ROOT, junit_path) == 0

    root = ET.parse(junit_path).getroot()
    expected_properties = {
        "specfact.runner": "pytest",
        "specfact.python": platform.python_version(),
        "specfact.pytest": pytest.__version__,
    }
    for name, value in expected_properties.items():
        assert root.find(f".//property[@name='{name}'][@value='{value}']") is not None


def test_executor_records_canonical_selector_for_skipped_and_setup_error_cases(tmp_path: Path) -> None:
    """Reconciliation can identify collected selectors without a call-phase report."""
    module = _load_executor_module()
    selectors = (
        "tests/fixtures/requirements_proof_terminal_states.py::test_skipped_by_proof",
        "tests/fixtures/requirements_proof_terminal_states.py::TestSetupError::test_unreachable",
    )

    for index, selector in enumerate(selectors):
        junit_path = tmp_path / f"requirements-proof-{index}.xml"
        module.execute_plan(_plan(selector), REPO_ROOT, junit_path)
        root = ET.parse(junit_path).getroot()
        assert root.find(".//property[@name='specfact.selector'][@value='" + selector + "']") is not None

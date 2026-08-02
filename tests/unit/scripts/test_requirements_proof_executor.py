"""Contract tests for the core-owned Requirements proof executor."""

from __future__ import annotations

import importlib.util
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Protocol, cast

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
EXECUTOR_SCRIPT = REPO_ROOT / "scripts" / "requirements_proof_executor.py"


class ExecutorModule(Protocol):
    """Minimal typed surface of the proof-execution boundary."""

    def selectors_from_plan(self, plan: dict[str, object], repo_root: Path) -> list[str]:
        raise NotImplementedError

    def execute_plan(
        self,
        plan: dict[str, object],
        repo_root: Path,
        junit_path: Path,
        *,
        command_runner: object | None = None,
    ) -> int:
        raise NotImplementedError

    def _run_command(self, arguments: list[str], *, cwd: Path, env: dict[str, str], shell: bool, timeout: int) -> int:
        raise NotImplementedError

    def main(self, argv: list[str] | None = None) -> int:
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
        "plan": {
            "cases": [
                {
                    "method": "test",
                    "selector": {"runner": "pytest", "node_id": selector},
                    "node_id": selector,
                }
                for selector in selectors
            ]
        }
    }


def test_executor_accepts_existing_exact_selectors_and_uses_argument_array(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Only existing exact pytest node IDs may reach the no-shell invocation."""
    module = _load_executor_module()
    test_file = tmp_path / "tests" / "test_proof.py"
    test_file.parent.mkdir()
    test_file.write_text("def test_selected() -> None: pass\n", encoding="utf-8")
    plan = _plan("tests/test_proof.py::test_selected")
    junit_path = tmp_path / "artifacts" / "proof.xml"
    captured: dict[str, object] = {}
    monkeypatch.setenv("PYTEST_ADDOPTS", "--collect-only")
    monkeypatch.setenv("PYTEST_PLUGINS", "untrusted_plugin")
    monkeypatch.setenv("PYTHONPATH", "/untrusted/python")
    monkeypatch.setenv("SPECFACT_MODULES_REPO", "/untrusted/modules")

    observed = module.execute_plan(
        plan,
        tmp_path,
        junit_path,
        command_runner=lambda arguments, **kwargs: captured.update({"arguments": arguments, **kwargs}) or 0,
    )

    assert observed == 0
    assert module.selectors_from_plan(plan, tmp_path) == ["tests/test_proof.py::test_selected"]
    assert captured["shell"] is False
    assert captured["cwd"] == tmp_path
    assert captured["arguments"] == [
        sys.executable,
        "-m",
        "pytest",
        "--junitxml",
        str(junit_path),
        "-p",
        "scripts.requirements_proof_pytest_plugin",
        "--",
        "tests/test_proof.py::test_selected",
    ]
    environment = captured["env"]
    assert isinstance(environment, dict)
    assert environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "1"
    assert "PYTEST_ADDOPTS" not in environment
    assert "PYTEST_PLUGINS" not in environment
    assert "PYTHONPATH" not in environment
    assert "SPECFACT_MODULES_REPO" not in environment


@pytest.mark.parametrize(
    "selector",
    [
        "/tmp/test_proof.py::test_selected",
        "../tests/test_proof.py::test_selected",
        "tests/test_proof.py::test_*",
        "-p.py::test_selected",
        "tests/test_proof.py::test_selected;touch pwned",
    ],
)
def test_executor_rejects_unsafe_selectors_before_spawning(tmp_path: Path, selector: str) -> None:
    """Path escapes, option injection, globs, and shell syntax are never executable."""
    module = _load_executor_module()

    with pytest.raises(ValueError, match="invalid pytest selector"):
        module.execute_plan(
            _plan(selector), tmp_path, tmp_path / "proof.xml", command_runner=lambda *_args, **_kwargs: 0
        )


def test_executor_rejects_duplicate_or_unsupported_plan_entries(tmp_path: Path) -> None:
    """A plan must contain unique supported pytest selector records."""
    module = _load_executor_module()
    test_file = tmp_path / "tests" / "test_proof.py"
    test_file.parent.mkdir()
    test_file.write_text("def test_selected() -> None: pass\n", encoding="utf-8")

    with pytest.raises(ValueError, match="duplicate pytest selector"):
        module.selectors_from_plan(
            _plan("tests/test_proof.py::test_selected", "tests/test_proof.py::test_selected"), tmp_path
        )
    with pytest.raises(ValueError, match="unsupported runner"):
        module.selectors_from_plan(
            {"plan": {"cases": [{"method": "test", "selector": {"runner": "unittest", "node_id": "tests/x.py::x"}}]}},
            tmp_path,
        )


@pytest.mark.parametrize(
    "selector",
    [
        "tests/test_proof.py::test_parameterized[param-value]",
        "tests/test_proof.py::test_parameterized[spec commands-commands0]",
        "tests/test_proof.py::TestProof::test_selected",
        "tests/test_proof.py::TestParameterizedProof::test_selected[param-value]",
    ],
)
def test_executor_accepts_module_valid_pytest_node_ids(tmp_path: Path, selector: str) -> None:
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

    assert module.selectors_from_plan(_plan(selector), tmp_path) == [selector]


def test_executor_cli_reads_plan_and_forwards_no_shell_junit_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The command-line adapter parses a plan and sends validated arguments without a shell."""
    module = _load_executor_module()
    test_file = tmp_path / "tests" / "test_proof.py"
    test_file.parent.mkdir()
    test_file.write_text("def test_selected() -> None: pass\n", encoding="utf-8")
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(_plan("tests/test_proof.py::test_selected")), encoding="utf-8")
    junit_path = tmp_path / "artifacts" / "proof.xml"
    captured: dict[str, object] = {}

    def run_command(arguments: list[str], **kwargs: object) -> int:
        captured.update({"arguments": arguments, **kwargs})
        return 0

    monkeypatch.setattr(module, "_run_command", run_command)

    assert module.main(["--plan", str(plan_path), "--repo-root", str(tmp_path), "--junit", str(junit_path)]) == 0
    assert captured["shell"] is False
    assert captured["cwd"] == tmp_path
    assert captured["arguments"] == [
        sys.executable,
        "-m",
        "pytest",
        "--junitxml",
        str(junit_path),
        "-p",
        "scripts.requirements_proof_pytest_plugin",
        "--",
        "tests/test_proof.py::test_selected",
    ]


def test_executor_cli_rejects_malformed_plan_before_spawning(tmp_path: Path) -> None:
    """Malformed external plan data cannot reach the proof subprocess."""
    module = _load_executor_module()
    plan_path = tmp_path / "plan.json"
    plan_path.write_text("{not-json", encoding="utf-8")

    with pytest.raises(SystemExit, match="cannot read proof plan"):
        module.main(["--plan", str(plan_path), "--repo-root", str(tmp_path), "--junit", str(tmp_path / "proof.xml")])


def test_executor_records_canonical_selector_property_in_junit(tmp_path: Path) -> None:
    """Reconciliation receives the collected node ID, never a reconstructed JUnit label."""
    module = _load_executor_module()
    selector = "tests/fixtures/requirements_proof_target.py::test_records_canonical_selector"
    junit_path = tmp_path / "requirements-proof.xml"

    assert module.execute_plan(_plan(selector), REPO_ROOT, junit_path) == 0

    root = ET.parse(junit_path).getroot()
    assert root.find(".//property[@name='specfact.selector'][@value='" + selector + "']") is not None

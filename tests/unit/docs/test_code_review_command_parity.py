"""The reviewed module source and core docs expose the same Code Review commands."""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import click
import pytest
from typer.core import TyperArgument


REPO_ROOT = Path(__file__).resolve().parents[3]
CODE_REVIEW = "nold-ai/specfact-code-review"
COMPLETION_OPTIONS = {"--install-completion", "--show-completion"}


def _command_surface(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Normalize only completion switches contributed by standalone Typer mounts."""
    return {
        row["command"]: {
            "arguments": row["arguments"],
            "options": sorted(set(row["options"]) - COMPLETION_OPTIONS),
            "subcommands": row["subcommands"],
        }
        for row in records
        if row["owner_package"] == CODE_REVIEW
    }


def test_code_review_generated_contract_matches_reviewed_module_source() -> None:
    configured = os.environ.get("SPECFACT_DOCS_MODULES_REPO", "").strip()
    if not configured:
        pytest.skip("The immutable documentation module fixture is not configured")
    module_path = Path(configured) / "docs/reference/commands.generated.json"
    module_records = json.loads(module_path.read_text(encoding="utf-8"))
    core_records = json.loads((REPO_ROOT / "docs/reference/commands.generated.json").read_text(encoding="utf-8"))
    expected, actual = _command_surface(module_records), _command_surface(core_records)
    assert expected, "Reviewed module fixture has no Code Review contract"
    assert actual == expected, "Core Code Review command paths, arguments, options or subcommands differ"


def test_generated_contract_documents_portable_runtime_registration() -> None:
    records = json.loads((REPO_ROOT / "docs/reference/commands.generated.json").read_text(encoding="utf-8"))
    surface = _command_surface(records)
    assert "runtime" in surface["specfact code review"]["subcommands"]
    assert surface["specfact code review runtime"]["subcommands"] == ["inspect", "prepare"]
    assert {"--project-config", "--project-runtime"} <= set(surface["specfact code review run"]["options"])
    assert {"--json", "--project-config"} <= set(surface["specfact code review runtime inspect"]["options"])
    assert {"--json", "--project-config", "--offline"} <= set(
        surface["specfact code review runtime prepare"]["options"]
    )


def _load_command_script(filename: str = "generate-command-overview.py") -> ModuleType:
    spec = importlib.util.spec_from_file_location("command_overview", REPO_ROOT / "scripts" / filename)
    assert spec and spec.loader
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    return generator


@pytest.mark.parametrize("argument_type", [click.Argument, TyperArgument])
@pytest.mark.parametrize(("required", "nargs", "metavar"), [(False, -1, None), (True, 1, "INPUT")])
def test_generator_preserves_positional_argument_contract(
    argument_type: type[click.Argument] | type[TyperArgument], required: bool, nargs: int, metavar: str | None
) -> None:
    generator = _load_command_script()
    argument = argument_type(param_decls=["files"], required=required, nargs=nargs, metavar=metavar)
    command = SimpleNamespace(params=[argument, click.Option(["--json"], is_flag=True)])
    assert generator._command_arguments(command) == [{"name": metavar or "FILES", "required": required, "nargs": nargs}]


@pytest.mark.parametrize("filename", ["generate-command-overview.py", "check-command-contract.py"])
def test_explicit_docs_source_takes_precedence_over_execution_source(
    filename: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    generator = _load_command_script(filename)
    monkeypatch.setenv("SPECFACT_COMMAND_CONTRACT_USE_REAL_HOME", "1")
    documentation = tmp_path / "documentation"
    execution = tmp_path / "execution"
    for root in (documentation, execution):
        (root / "packages/example/src").mkdir(parents=True)
    monkeypatch.setenv("SPECFACT_DOCS_MODULES_REPO", str(documentation))
    monkeypatch.setenv("SPECFACT_MODULES_REPO", str(execution))
    monkeypatch.setattr(sys, "path", sys.path.copy())
    generator._ensure_imports()
    assert str(documentation / "packages/example/src") in sys.path
    assert str(execution / "packages/example/src") not in sys.path
    assert os.environ["SPECFACT_MODULES_REPO"] == str(documentation)


@pytest.mark.parametrize("kind", ["empty", "missing", "file"])
@pytest.mark.parametrize("filename", ["generate-command-overview.py", "check-command-contract.py"])
def test_invalid_explicit_docs_source_cannot_fall_back(
    kind: str, filename: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    generator = _load_command_script(filename)
    monkeypatch.setenv("SPECFACT_COMMAND_CONTRACT_USE_REAL_HOME", "1")
    execution = tmp_path / "execution"
    (execution / "packages/example/src").mkdir(parents=True)
    documentation = tmp_path / "documentation"
    if kind == "file":
        documentation.write_text("not a repository")
    monkeypatch.setenv("SPECFACT_DOCS_MODULES_REPO", "" if kind == "empty" else str(documentation))
    monkeypatch.setenv("SPECFACT_MODULES_REPO", str(execution))
    monkeypatch.setattr(sys, "path", sys.path.copy())
    with pytest.raises(ValueError, match="SPECFACT_DOCS_MODULES_REPO"):
        generator._ensure_imports()
    assert str(execution / "packages/example/src") not in sys.path


@pytest.mark.parametrize("filename", ["generate-command-overview.py", "check-command-contract.py"])
def test_generic_generator_callers_keep_execution_source_discovery(
    filename: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    generator = _load_command_script(filename)
    monkeypatch.setenv("SPECFACT_COMMAND_CONTRACT_USE_REAL_HOME", "1")
    (tmp_path / "packages/example/src").mkdir(parents=True)
    monkeypatch.delenv("SPECFACT_DOCS_MODULES_REPO", raising=False)
    monkeypatch.setenv("SPECFACT_MODULES_REPO", str(tmp_path))
    monkeypatch.setattr(sys, "path", sys.path.copy())
    generator._ensure_imports()
    assert str(tmp_path / "packages/example/src") in sys.path


@pytest.mark.parametrize("mutation", ["path", "options", "arguments", "subcommands"])
def test_parity_gate_rejects_changed_contract(mutation: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Exercise the real parity gate with controlled artifacts and no external checkout."""
    records: list[dict[str, Any]] = json.loads(
        (REPO_ROOT / "docs/reference/commands.generated.json").read_text(encoding="utf-8")
    )
    module_path = tmp_path / "docs/reference/commands.generated.json"
    module_path.parent.mkdir(parents=True)
    module_path.write_text(json.dumps(records), encoding="utf-8")
    monkeypatch.setenv("SPECFACT_DOCS_MODULES_REPO", str(tmp_path))
    test_code_review_generated_contract_matches_reviewed_module_source()

    run = next(row for row in records if row["command"] == "specfact code review run")
    if mutation == "path":
        records = [row for row in records if row["command"] != "specfact code review runtime inspect"]
    if mutation == "options":
        run["options"].remove("--project-runtime")
    if mutation == "arguments":
        run["arguments"] = []
    if mutation == "subcommands":
        next(row for row in records if row["command"] == "specfact code review")["subcommands"].remove("runtime")
    module_path.write_text(json.dumps(records), encoding="utf-8")
    with pytest.raises(AssertionError, match="command paths, arguments, options or subcommands differ"):
        test_code_review_generated_contract_matches_reviewed_module_source()

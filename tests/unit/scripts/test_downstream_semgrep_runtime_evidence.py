from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Protocol, cast
from unittest.mock import patch

import pytest

from tests.unit.scripts import test_downstream_semgrep as contract


wheel_recipe = contract.wheel_recipe


class Cell(Protocol):
    def _run(
        self, label: str, command: list[str], expected: tuple[int, ...] = (0,), timeout: int = 120
    ) -> subprocess.CompletedProcess[str]: ...


class Runner(Protocol):
    _Cell: Callable[[Path, dict[str, object]], Cell]


def _runner() -> Runner:
    path = Path(__file__).resolve().parents[3] / "scripts/verify_downstream_semgrep.py"
    assert path.is_file(), f"Downstream matrix runner is absent: {path}"
    spec = importlib.util.spec_from_file_location("_downstream_semgrep_runtime_contract", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    assert callable(getattr(module, "_Cell", None)), "Downstream matrix command recorder is absent"
    return cast(Runner, module)


@pytest.mark.parametrize("damage", ["mismatch", "missing", "null", "list", "string"])
def test_required_matrix_rejects_unbound_runtime_policy(wheel_recipe: contract.WheelRecipe, damage: str) -> None:
    module = contract._module()
    assert callable(getattr(module, "required_matrix", None)), "Downstream matrix boundary is absent"
    recipe_path, recipe, _upstream = wheel_recipe
    payload: dict[str, object] = dict(recipe)
    if damage == "mismatch":
        payload["build_runtime_digest"] = "a" * 64
    elif damage == "missing":
        del payload["build_runtime_policy"]
    else:
        malformed: object = {"null": None, "list": [], "string": "CPython"}[damage]
        payload["build_runtime_policy"] = malformed
        payload["build_runtime_digest"] = contract._sha(
            json.dumps(malformed, sort_keys=True, separators=(",", ":")).encode("utf-8")
        )
    contract._write_json(recipe_path, payload)
    with pytest.raises(ValueError):
        module.required_matrix(recipe_path)


@pytest.mark.parametrize("line_ending", ["\n", "\r\n", "\r"], ids=["lf", "crlf", "cr"])
def test_cell_preserves_utf8_command_evidence_under_windows_locale(tmp_path: Path, line_ending: str) -> None:
    runner = _runner()
    cell = runner._Cell(tmp_path, {})
    stdout = f"Grüße €{line_ending}".encode()
    stderr = f"Prüfung €{line_ending}".encode()
    command = [
        sys.executable,
        "-c",
        f"import sys; sys.stdout.buffer.write({stdout!r}); sys.stderr.buffer.write({stderr!r})",
    ]
    with patch.object(subprocess, "_text_encoding", return_value="cp1252"):
        result = cell._run("utf8", command)
    assert result.stdout == "Grüße €\n"
    assert result.stderr == "Prüfung €\n"
    assert (tmp_path / "01-utf8.stdout").read_text(encoding="utf-8") == result.stdout
    assert (tmp_path / "01-utf8.stderr").read_text(encoding="utf-8") == result.stderr


@pytest.mark.parametrize("stream", ["stdout", "stderr"])
def test_cell_rejects_invalid_utf8_command_evidence(tmp_path: Path, stream: str) -> None:
    runner = _runner()
    cell = runner._Cell(tmp_path, {})
    command = [sys.executable, "-c", f"import sys; sys.{stream}.buffer.write(bytes([255]))"]
    with patch.object(subprocess, "_text_encoding", return_value="cp1252"), pytest.raises(UnicodeError):
        cell._run("invalid", command)
    assert not (tmp_path / "01-invalid.stdout").exists()
    assert not (tmp_path / "01-invalid.stderr").exists()


@pytest.mark.parametrize("line_ending", ["\n", "\r\n", "\r"], ids=["lf", "crlf", "cr"])
def test_cell_preserves_utf8_timeout_evidence(tmp_path: Path, line_ending: str) -> None:
    cell = _runner()._Cell(tmp_path, {})
    command = [sys.executable, "-c", "pass"]
    stdout, stderr = f"Grüße €{line_ending}".encode(), f"Prüfung €{line_ending}".encode()
    expired = subprocess.TimeoutExpired(command, 1, output=stdout, stderr=stderr)
    with patch.object(subprocess, "run", side_effect=expired):
        result = cell._run("timeout", command, expected=(124,))
    assert result.returncode == 124
    assert result.stdout == "Grüße €\n"
    assert result.stderr == "Prüfung €\n\nExternal process timeout\n"
    assert (tmp_path / "01-timeout.stdout").read_text(encoding="utf-8") == result.stdout
    assert (tmp_path / "01-timeout.stderr").read_text(encoding="utf-8") == result.stderr


@pytest.mark.parametrize("stream", ["stdout", "stderr"])
def test_cell_rejects_invalid_utf8_timeout_evidence(tmp_path: Path, stream: str) -> None:
    cell = _runner()._Cell(tmp_path, {})
    command = [sys.executable, "-c", "pass"]
    stdout = b"\xff" if stream == "stdout" else b"valid output"
    stderr = b"\xff" if stream == "stderr" else b"valid diagnostics"
    expired = subprocess.TimeoutExpired(command, 1, output=stdout, stderr=stderr)
    with patch.object(subprocess, "run", side_effect=expired), pytest.raises(UnicodeError):
        cell._run("timeout", command, expected=(124,))
    assert not (tmp_path / "01-timeout.stdout").exists()
    assert not (tmp_path / "01-timeout.stderr").exists()

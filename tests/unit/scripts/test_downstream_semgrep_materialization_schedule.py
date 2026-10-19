from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import downstream_semgrep as boundary, verify_downstream_semgrep as driver


def _stub_external_phases(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> boundary.CandidateWheel:
    wheel = tmp_path / "candidate.whl"
    wheel.write_bytes(b"native integration fixture")
    candidate = boundary.CandidateWheel(wheel, "a" * 64, "test", "b" * 64, "c" * 64, boundary._CANDIDATE_AUTHORITY)
    environment = driver._Environment(Path(sys.executable), {}, tmp_path / "inventory.txt")
    monkeypatch.setattr(driver, "_cell_runtime", lambda *_args: None)
    monkeypatch.setattr(driver, "_cell_build", lambda *_args: (candidate, tmp_path / "upstream.whl"))
    monkeypatch.setattr(driver, "_cell_install", lambda *_args: (environment, environment))
    monkeypatch.setattr(driver, "_scanners", lambda *_args: None)
    monkeypatch.setattr(driver, "_mcp_regressions", lambda *_args: None)
    monkeypatch.setattr(boundary, "_validate_native_report", lambda *_args: None)
    return candidate


@pytest.mark.parametrize("probe_fails", [False, True], ids=["successful-probe", "failed-probe"])
def test_native_cell_requires_materialization_execution(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, probe_fails: bool
) -> None:
    candidate = _stub_external_phases(monkeypatch, tmp_path)
    invocations: list[list[str]] = []

    def capture(
        _cell: driver._Cell, _label: str, command: list[str], **_kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        invocations.append(command)
        if probe_fails:
            raise ValueError("materialization fixture failed")
        return subprocess.CompletedProcess(command, 0, "{}", "")

    monkeypatch.setattr(driver._Cell, "_run", capture)
    output = tmp_path / "cell"
    exit_code = driver._execute_cell(tmp_path / "recipe.json", "test", "3.12", output)
    probes = [argv for argv in invocations if any(Path(arg).name == "test_artifact_materialization.py" for arg in argv)]
    assert len(probes) == 1
    assert probes[0] == [
        sys.executable,
        str(driver.ROOT / "tools/downstream_semgrep/test_artifact_materialization.py"),
        str(candidate.path),
    ]
    assert exit_code == int(probe_fails)
    report = json.loads((output / "report.json").read_text(encoding="utf-8"))
    assert report["status"] == ("failed" if probe_fails else "passed")
    assert report["candidate_only"] is True
    assert report["production_admission"] == "not_requested"


def test_native_source_inventory_binds_the_materialization_probe() -> None:
    assert "tools/downstream_semgrep/test_artifact_materialization.py" in driver._SOURCE_FILES

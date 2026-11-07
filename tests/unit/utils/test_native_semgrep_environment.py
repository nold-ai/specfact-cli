import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, cast
from unittest.mock import patch

import pytest

from specfact_cli.analyzers.code_analyzer import CodeAnalyzer
from specfact_cli.generators.test_to_openapi import OpenAPITestConverter
from specfact_cli.utils.env_manager import EnvManager, EnvManagerInfo, check_tool_in_env
from specfact_cli.validators.repro_checker import CheckStatus, ReproChecker, _repro_checks_append_semgrep


@pytest.fixture
def native_utf8_child(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    finding = {"check_id": "utf8-marker", "extra": {"message": "雪 ← café"}}
    original_run = subprocess.run
    monkeypatch.setattr(subprocess, "_text_encoding", lambda: "cp1252")

    def emit(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        native = "osemgrep" in command
        stdout = json.dumps({"results": [finding]}, ensure_ascii=False).encode() if native else b"tool \x80"
        stderr = "native ← stderr".encode() if native else b"tool \x80"
        program = f"import os;os.write(1,{stdout!r});os.write(2,{stderr!r})"
        result = cast(
            subprocess.CompletedProcess[str], original_run([sys.executable, "-I", "-S", "-c", program], **kwargs)
        )
        assert result.stderr == ("native ← stderr" if native else "tool €")
        return result

    monkeypatch.setattr(subprocess, "run", emit)
    return finding


@pytest.mark.parametrize("owner", ["availability", "analyzer", "converter"])
def test_native_capture_preserves_utf8_json_and_diagnostics(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, native_utf8_child: dict[str, Any], owner: str
) -> None:
    monkeypatch.delenv("TEST_MODE", raising=False)
    monkeypatch.setattr("shutil.which", lambda _tool: "/native/osemgrep")
    config = tmp_path / "rules.yml"
    config.write_text("rules: []\n", encoding="utf-8")
    analyzer = object.__new__(CodeAnalyzer)
    analyzer.repo_path = tmp_path
    analyzer.semgrep_enabled = True
    analyzer.semgrep_config = config
    analyzer.semgrep_quality_config = None
    match owner:
        case "availability":
            assert analyzer._check_semgrep_available()
        case "analyzer":
            assert analyzer._run_semgrep_patterns(config) == [native_utf8_child]
        case _:
            converter = OpenAPITestConverter(tmp_path, semgrep_config=config)
            assert converter._run_semgrep(config) == [native_utf8_child]


@pytest.mark.parametrize("tool", ["osemgrep", "ruff"])
def test_managed_probe_decodes_native_utf8_and_retains_other_tool_locale(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, native_utf8_child: dict[str, Any], tool: str
) -> None:
    _ = native_utf8_child
    monkeypatch.setattr("shutil.which", lambda _tool: None)
    environment = EnvManagerInfo(manager=EnvManager.UV, available=True, command_prefix=["uv", "run"])
    assert check_tool_in_env(tmp_path, tool, environment) == (True, None)


@pytest.mark.parametrize("tool", ["semgrep", "ruff"])
def test_repro_execution_decodes_native_utf8_and_retains_other_tool_locale(
    tmp_path: Path, native_utf8_child: dict[str, Any], tool: str
) -> None:
    checker = ReproChecker(repo_path=tmp_path)
    executable = "osemgrep" if tool == "semgrep" else tool
    result = checker.run_check("Encoding probe", tool, [executable, "--version"], timeout=5, skip_if_missing=False)
    assert result.status is CheckStatus.PASSED, result.error
    if tool == "semgrep":
        assert json.loads(result.output)["results"] == [native_utf8_child]
    else:
        assert result.output == "tool €"


def test_managed_native_scanner_probe_avoids_python_fallback(tmp_path: Path) -> None:
    environment = EnvManagerInfo(manager=EnvManager.UV, available=True, command_prefix=["uv", "run"])

    def probe(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        _ = kwargs
        native = command[2:5] == ["osemgrep", "scan", "--experimental"]
        return subprocess.CompletedProcess(command, 0 if native else 2, stdout="1.182.1\n", stderr="")

    with patch("shutil.which", return_value=None), patch("subprocess.run", side_effect=probe):
        available, error = check_tool_in_env(tmp_path, "osemgrep", environment)
    assert available, error


def test_missing_native_scanner_does_not_recommend_a_python_package(tmp_path: Path) -> None:
    environment = EnvManagerInfo(manager=EnvManager.UNKNOWN, available=False, command_prefix=[])
    with patch("shutil.which", return_value=None):
        available, error = check_tool_in_env(tmp_path, "osemgrep", environment)
    assert not available
    assert error is not None
    assert "pip install" not in error


def test_repro_report_keeps_native_guidance_when_scanner_is_missing(tmp_path: Path) -> None:
    config = tmp_path / "tools/semgrep/async.yml"
    config.parent.mkdir(parents=True)
    config.write_text("rules: []\n", encoding="utf-8")
    environment = EnvManagerInfo(manager=EnvManager.UNKNOWN, available=False, command_prefix=[])
    with (
        patch("specfact_cli.utils.env_manager.detect_env_manager", return_value=environment),
        patch("shutil.which", return_value=None),
    ):
        report = ReproChecker(repo_path=tmp_path).run_all_checks()
    result = next(check for check in report.checks if check.tool == "semgrep")
    assert result.status is CheckStatus.SKIPPED
    assert "osemgrep" in result.error
    assert "pip install" not in result.error


@pytest.mark.parametrize("owner", ["analyzer", "converter", "probe", "repro"])
@pytest.mark.parametrize("override", [None, "", "/caller/libraries"])
def test_linux_native_children_preserve_private_loader_selection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, owner: str, override: str | None
) -> None:
    monkeypatch.setattr(os, "environ", {"PATH": os.defpath})
    monkeypatch.setattr("sys.platform", "linux")
    monkeypatch.delenv("TEST_MODE", raising=False)
    if override is None:
        monkeypatch.delenv("LD_LIBRARY_PATH", raising=False)
    else:
        monkeypatch.setenv("LD_LIBRARY_PATH", override)
    environments: list[dict[str, str]] = []

    def complete(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        environment = kwargs.get("env")
        assert isinstance(environment, dict)
        environments.append(environment)
        return subprocess.CompletedProcess(command, 0, stdout='{"results": []}', stderr="")

    config = tmp_path / "rules.yml"
    config.write_text("rules: []\n", encoding="utf-8")
    with patch("shutil.which", return_value="/selected/osemgrep"), patch("subprocess.run", side_effect=complete):
        match owner:
            case "analyzer":
                analyzer = object.__new__(CodeAnalyzer)
                analyzer.repo_path = tmp_path
                assert analyzer._check_semgrep_available()
            case "converter":
                OpenAPITestConverter(tmp_path, semgrep_config=config)._run_semgrep(config)
            case "probe":
                environment = EnvManagerInfo(manager=EnvManager.UV, available=True, command_prefix=["uv", "run"])
                with patch("shutil.which", return_value=None):
                    assert check_tool_in_env(tmp_path, "osemgrep", environment)[0]
            case _:
                checks: list[tuple[str, str, list[str], int | None, bool, dict[str, str] | None]] = []
                environment = EnvManagerInfo(manager=EnvManager.UNKNOWN, available=True, command_prefix=[])
                _repro_checks_append_semgrep(checks, ReproChecker(repo_path=tmp_path), environment, tmp_path, config)
                assert checks and checks[0][5] is not None
                environments.append(checks[0][5])
    assert len(environments) == 1
    actual = environments[0].get("LD_LIBRARY_PATH")
    assert actual == ("$ORIGIN/libs" if override is None else override)

import os
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from specfact_cli.analyzers.code_analyzer import CodeAnalyzer
from specfact_cli.generators.test_to_openapi import OpenAPITestConverter
from specfact_cli.utils.env_manager import EnvManager, EnvManagerInfo, check_tool_in_env
from specfact_cli.validators.repro_checker import CheckStatus, ReproChecker, _repro_checks_append_semgrep


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

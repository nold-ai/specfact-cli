import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, cast

import certifi
import pytest
import yaml

from specfact_cli.analyzers.code_analyzer import CodeAnalyzer
from specfact_cli.generators.test_to_openapi import OpenAPITestConverter
from specfact_cli.utils.env_manager import EnvManager, EnvManagerInfo
from specfact_cli.validators.repro_checker import ReproChecker, _repro_checks_append_semgrep


@pytest.fixture
def native_analyzer(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> CodeAnalyzer:
    executable = shutil.which("osemgrep")
    if executable is None:
        pytest.skip("upstream native Semgrep executable is required")
    monkeypatch.setenv("PATH", str(Path(executable).parent) + os.pathsep + os.defpath)
    monkeypatch.delenv("TEST_MODE", raising=False)
    monkeypatch.delenv("SSL_CERT_FILE", raising=False)
    analyzer = object.__new__(CodeAnalyzer)
    analyzer.repo_path = tmp_path
    analyzer.semgrep_enabled = True
    rules = Path(__file__).resolve().parents[3] / "tools" / "semgrep" / "sast.yml"
    analyzer.semgrep_config = tmp_path / "sast.yml"
    analyzer.semgrep_config.write_bytes(rules.read_bytes())
    quality = tmp_path / "quality.yml"
    quality.write_text(
        "rules:\n  - id: native-quality-marker\n    languages: [python]\n"
        "    pattern: print(...)\n    message: marker\n    severity: INFO\n",
        encoding="utf-8",
    )
    analyzer.semgrep_quality_config = quality
    return analyzer


def test_native_executable_is_available_without_python_cli(native_analyzer: CodeAnalyzer) -> None:
    assert shutil.which("pysemgrep") is None
    assert native_analyzer._check_semgrep_available()


@pytest.mark.parametrize("override", ["malformed", "empty"])
def test_native_scanner_preserves_explicit_ca_override(
    native_analyzer: CodeAnalyzer, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, override: str
) -> None:
    certificate = tmp_path / "invalid-ca.pem"
    certificate.write_text("not a certificate", encoding="utf-8")
    value = str(certificate) if override == "malformed" else ""
    monkeypatch.setenv("SSL_CERT_FILE", value)
    original_run = subprocess.run
    statuses: list[int] = []

    def observe(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        assert kwargs["env"]["SSL_CERT_FILE"] == value
        result = cast(subprocess.CompletedProcess[str], original_run(command, **kwargs))
        statuses.append(result.returncode)
        return result

    monkeypatch.setattr(subprocess, "run", observe)
    available = native_analyzer._check_semgrep_available()
    assert len(statuses) == 1
    assert available is (statuses[0] == 0)
    assert os.environ["SSL_CERT_FILE"] == value


@pytest.fixture
def native_source(native_analyzer: CodeAnalyzer) -> Path:
    source = native_analyzer.repo_path / "example.py"
    source.write_text(
        "import subprocess\n\ndef check(cmd):\n    enabled = True\n    disabled = False\n"
        "    subprocess.run(cmd, shell=True)\n    subprocess.run(cmd, shell=enabled)\n"
        "    subprocess.run(cmd, shell=False)\n    subprocess.run(cmd, shell=disabled)\n"
        "    print('marker')\n",
        encoding="utf-8",
    )
    return source


def test_native_scan_preserves_propagation_and_all_configs(native_analyzer: CodeAnalyzer, native_source: Path) -> None:
    findings = native_analyzer._run_semgrep_patterns(native_source)
    command_lines = {
        finding["start"]["line"] for finding in findings if finding["check_id"].endswith("command-injection-risk")
    }
    assert command_lines == {6, 7}
    assert any(finding["check_id"].endswith("native-quality-marker") for finding in findings)


def test_openapi_converter_uses_native_scanner(native_analyzer: CodeAnalyzer, native_source: Path) -> None:
    converter = OpenAPITestConverter(native_analyzer.repo_path, semgrep_config=native_analyzer.semgrep_config)
    findings = converter._run_semgrep(native_source)
    assert {finding["start"]["line"] for finding in findings} == {6, 7}


def test_repro_checker_runs_native_scanner(native_analyzer: CodeAnalyzer, native_source: Path) -> None:
    _ = native_source
    checks: list[tuple[str, str, list[str], int | None, bool, dict[str, str] | None]] = []
    checker = ReproChecker(repo_path=native_analyzer.repo_path)
    environment = EnvManagerInfo(manager=EnvManager.UNKNOWN, available=True, command_prefix=[])
    assert native_analyzer.semgrep_config is not None
    _repro_checks_append_semgrep(
        checks, checker, environment, native_analyzer.repo_path, native_analyzer.semgrep_config
    )
    command, timeout, env = checks[0][2], checks[0][3], checks[0][5]
    assert command
    result = subprocess.run(
        [*command, "--json"], cwd=native_analyzer.repo_path, env=env, capture_output=True, text=True, timeout=timeout
    )
    assert result.returncode == 0, result.stderr
    assert {finding["start"]["line"] for finding in json.loads(result.stdout)["results"]} == {6, 7}


def _ci_scan_inputs(native_analyzer: CodeAnalyzer, ca_input: str) -> tuple[str, Path, dict[str, str]]:
    root = Path(__file__).resolve().parents[3]
    workflow = yaml.safe_load((root / ".github/workflows/pr-orchestrator.yml").read_text(encoding="utf-8"))
    steps = workflow["jobs"]["independent-static-analysis"]["steps"]
    script = next(step["run"] for step in steps if step.get("name") == "Run independent Semgrep and Bandit gates")
    command = next(
        line.strip() for line in script.splitlines() if "osemgrep scan " in line or line.startswith("semgrep ")
    )
    config = native_analyzer.repo_path / "tools/semgrep/sast.yml"
    config.parent.mkdir(parents=True)
    assert native_analyzer.semgrep_config is not None
    config.write_bytes(native_analyzer.semgrep_config.read_bytes())
    output = native_analyzer.repo_path / "logs/static-analysis/semgrep.json"
    output.parent.mkdir(parents=True)
    environment = {"PATH": str(Path(sys.executable).parent) + os.pathsep + os.environ["PATH"]}
    if ca_input in {"valid", "invalid"}:
        certificate = native_analyzer.repo_path / "caller CA.pem"
        certificate.write_bytes(Path(certifi.where()).read_bytes() if ca_input == "valid" else b"not a certificate")
        environment["SSL_CERT_FILE"] = str(certificate)
    elif ca_input == "empty":
        environment["SSL_CERT_FILE"] = ""
    return command, output, environment


@pytest.mark.skipif(os.name != "posix", reason="The static-analysis producer runs in a POSIX CI job")
@pytest.mark.parametrize(("ca_input", "expected_status"), [("absent", 0), ("valid", 0), ("invalid", 2), ("empty", 2)])
def test_ci_producer_writes_native_json(
    native_analyzer: CodeAnalyzer, native_source: Path, ca_input: str, expected_status: int
) -> None:
    _ = native_source
    command, output, environment = _ci_scan_inputs(native_analyzer, ca_input)
    result = subprocess.run(
        ["bash", "-e", "-c", command + '\nprintf "%s" "${SSL_CERT_FILE-UNSET}"'],
        cwd=native_analyzer.repo_path,
        env=environment,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == expected_status, result.stderr
    if expected_status == 0:
        assert {finding["start"]["line"] for finding in json.loads(output.read_text(encoding="utf-8"))["results"]} == {
            6,
            7,
        }
        assert result.stdout == environment.get("SSL_CERT_FILE", "UNSET")

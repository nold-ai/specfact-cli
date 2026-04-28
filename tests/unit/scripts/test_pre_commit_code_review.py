"""Tests for scripts/pre_commit_code_review.py."""

# pyright: reportUnknownMemberType=false

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest


def _load_script_module() -> Any:
    """Load scripts/pre_commit_code_review.py as a Python module."""
    script_path = Path(__file__).resolve().parents[3] / "scripts" / "pre_commit_code_review.py"
    spec = importlib.util.spec_from_file_location("pre_commit_code_review", script_path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Unable to load script module at {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_filter_review_files_keeps_only_python_sources() -> None:
    """Only relevant staged Python files should be reviewed."""
    module = _load_script_module()

    assert module.filter_review_files(["src/app.py", "README.md", "tests/test_app.py", "notes.txt"]) == [
        "src/app.py",
        "tests/test_app.py",
    ]


def test_build_review_command_writes_json_report() -> None:
    """Pre-commit gate should write ReviewReport JSON for IDE/Copilot and enforce errors only."""
    module = _load_script_module()

    command = module.build_review_command(["src/app.py", "tests/test_app.py"])

    assert command[:5] == [sys.executable, "-m", "specfact_cli.cli", "code", "review"]
    assert "--json" in command
    assert "--out" in command
    assert module.REVIEW_JSON_OUT in command
    assert command[-2:] == ["src/app.py", "tests/test_app.py"]


def test_main_skips_when_no_relevant_files(capsys: pytest.CaptureFixture[str]) -> None:
    """Hook should not fail commits when no staged Python files are present."""
    module = _load_script_module()

    exit_code = module.main(["README.md", "docs/guide.md"])

    assert exit_code == 0
    assert "No staged Python files" in capsys.readouterr().out


def test_main_allows_fail_verdict_when_only_warnings(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Score-based FAIL with zero error-severity findings must not block pre-commit."""
    module = _load_script_module()
    repo_root = tmp_path
    payload = {
        "overall_verdict": "FAIL",
        "findings": [
            {"severity": "warning", "rule": "w1"},
            {"severity": "warning", "rule": "w2"},
        ],
    }

    def _fake_root() -> Path:
        return repo_root

    def _fake_ensure() -> tuple[bool, str | None]:
        return True, None

    def _fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        assert "--json" in cmd
        assert module.REVIEW_JSON_OUT in cmd
        _write_sample_review_report(repo_root, payload)
        return subprocess.CompletedProcess(cmd, 1, stdout=".specfact/code-review.json\n", stderr="")

    monkeypatch.setattr(module, "_repo_root", _fake_root)
    monkeypatch.setattr(module, "ensure_runtime_available", _fake_ensure)
    monkeypatch.setattr(module.subprocess, "run", _fake_run)

    exit_code = module.main(["src/app.py"])

    assert exit_code == 0
    err = capsys.readouterr().err
    assert "errors=0" in err
    assert "overall_verdict='FAIL'" in err


def test_main_propagates_review_gate_exit_code(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Blocking review verdicts must block the commit by returning non-zero."""
    module = _load_script_module()
    repo_root = tmp_path
    payload = {
        "overall_verdict": "FAIL",
        "findings": [
            {"severity": "error", "rule": "e1"},
            {"severity": "warning", "rule": "w1"},
        ],
    }

    def _fake_root() -> Path:
        return repo_root

    def _fake_ensure() -> tuple[bool, str | None]:
        return True, None

    def _fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        assert "--json" in cmd
        assert module.REVIEW_JSON_OUT in cmd
        assert kwargs.get("cwd") == str(repo_root)
        assert kwargs.get("timeout") == 300
        _write_sample_review_report(repo_root, payload)
        return subprocess.CompletedProcess(cmd, 1, stdout=".specfact/code-review.json\n", stderr="")

    monkeypatch.setattr(module, "_repo_root", _fake_root)
    monkeypatch.setattr(module, "ensure_runtime_available", _fake_ensure)
    monkeypatch.setattr(module.subprocess, "run", _fake_run)

    exit_code = module.main(["src/app.py"])

    assert exit_code == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    err = captured.err
    assert "Code review summary: 2 finding(s)" in err
    assert "errors=1" in err
    assert "warnings=1" in err
    assert "overall_verdict='FAIL'" in err
    assert "Code review report file:" in err
    assert "absolute path:" in err
    assert "Copy-paste for Copilot or Cursor:" in err
    assert "blocks only on severity=error" in err
    assert "@workspace Open `.specfact/code-review.json`" in err


def _write_sample_review_report(repo_root: Path, payload: dict[str, object]) -> None:
    spec_dir = repo_root / ".specfact"
    spec_dir.mkdir(parents=True, exist_ok=True)
    (spec_dir / "code-review.json").write_text(json.dumps(payload), encoding="utf-8")


def test_count_findings_by_severity_buckets_unknown() -> None:
    """Severities map to error/warning/advisory; others go to other."""
    module = _load_script_module()
    counts = module._count_findings_by_severity(
        [
            module.ReviewFinding(severity="error"),
            module.ReviewFinding(severity="WARN"),
            module.ReviewFinding(severity="advisory"),
            module.ReviewFinding(severity="info"),
            module.ReviewFinding(severity="custom"),
            module.ReviewFinding.model_validate({}),
        ]
    )
    assert counts == {"error": 1, "warning": 1, "advisory": 1, "info": 1, "other": 2}


def test_main_missing_report_still_returns_exit_code_and_warns(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """If JSON is missing, the hook fails and surfaces subprocess output for debugging."""
    module = _load_script_module()

    def _fake_root() -> Path:
        return tmp_path

    def _fake_ensure() -> tuple[bool, str | None]:
        return True, None

    def _fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        report_dir = tmp_path / ".specfact"
        assert report_dir.is_dir()
        return subprocess.CompletedProcess(cmd, 0, stdout="review stdout", stderr="review stderr")

    monkeypatch.setattr(module, "_repo_root", _fake_root)
    monkeypatch.setattr(module, "ensure_runtime_available", _fake_ensure)
    monkeypatch.setattr(module.subprocess, "run", _fake_run)

    exit_code = module.main(["src/app.py"])

    assert exit_code == 1
    err = capsys.readouterr().err
    assert "no report file" in err or "expected review report" in err
    assert ".specfact/code-review.json" in err
    assert "review stdout" in err
    assert "review stderr" in err


def test_main_timeout_fails_hook(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """Subprocess timeout must fail the hook with a clear message."""
    module = _load_script_module()
    repo_root = Path(__file__).resolve().parents[3]

    def _fake_root() -> Path:
        return repo_root

    def _fake_ensure() -> tuple[bool, str | None]:
        return True, None

    def _fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        assert kwargs.get("cwd") == str(repo_root)
        assert kwargs.get("timeout") == 300
        raise subprocess.TimeoutExpired(cmd, 300)

    monkeypatch.setattr(module, "_repo_root", _fake_root)
    monkeypatch.setattr(module, "ensure_runtime_available", _fake_ensure)
    monkeypatch.setattr(module.subprocess, "run", _fake_run)

    exit_code = module.main(["src/app.py"])

    assert exit_code == 1
    err = capsys.readouterr().err
    assert "timed out after 300s" in err
    assert "src/app.py" in err


def test_print_summary_rejects_non_object_json(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Top-level JSON must be an object so findings can be summarized safely."""
    module = _load_script_module()
    repo_root = tmp_path

    def _fake_root() -> Path:
        return repo_root

    def _fake_ensure() -> tuple[bool, str | None]:
        return True, None

    def _fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        spec_dir = repo_root / ".specfact"
        spec_dir.mkdir(parents=True, exist_ok=True)
        (spec_dir / "code-review.json").write_text(json.dumps(["not", "an", "object"]), encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(module, "_repo_root", _fake_root)
    monkeypatch.setattr(module, "ensure_runtime_available", _fake_ensure)
    monkeypatch.setattr(module.subprocess, "run", _fake_run)

    exit_code = module.main(["src/app.py"])

    assert exit_code == 1
    err = capsys.readouterr().err
    assert "expected a JSON object" in err


def test_main_prints_actionable_setup_guidance_when_runtime_missing(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Missing review runtime should fail with actionable setup guidance."""
    module = _load_script_module()

    def _fake_ensure() -> tuple[bool, str | None]:
        return False, 'Install dev dependencies with `pip install -e ".[dev]"` or run `hatch env create`.'

    monkeypatch.setattr(module, "ensure_runtime_available", _fake_ensure)

    exit_code = module.main(["src/app.py"])

    assert exit_code == 1
    assert "Install dev dependencies" in capsys.readouterr().out


def test_discover_specfact_modules_repo_finds_ancestor_sibling(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Walking up from the repo root must find a sibling ``specfact-cli-modules`` tree."""
    module = _load_script_module()
    modules_root = tmp_path / "specfact-cli-modules"
    (modules_root / "packages" / "specfact-codebase").mkdir(parents=True)
    fake_repo = tmp_path / "worktrees" / "feature" / "my-checkout"
    (fake_repo / "scripts").mkdir(parents=True)

    monkeypatch.setattr(module, "_repo_root", lambda: fake_repo)

    found = module.discover_specfact_modules_repo()

    assert found == modules_root.resolve()


def test_discover_specfact_modules_repo_returns_none_when_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Without a valid modules checkout, discovery returns None."""
    module = _load_script_module()
    fake_repo = tmp_path / "solo-repo"
    (fake_repo / "scripts").mkdir(parents=True)
    monkeypatch.setattr(module, "_repo_root", lambda: fake_repo)

    assert module.discover_specfact_modules_repo() is None


def test_build_review_subprocess_env_injects_discovered_repo_without_mutating_os_environ(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Review subprocess env may add ``SPECFACT_MODULES_REPO`` without changing ``os.environ``."""
    module = _load_script_module()
    modules_root = tmp_path / "specfact-cli-modules"
    (modules_root / "packages" / "specfact-codebase").mkdir(parents=True)
    fake_repo = tmp_path / "a" / "b" / "repo"
    (fake_repo / "scripts").mkdir(parents=True)
    monkeypatch.setattr(module, "_repo_root", lambda: fake_repo)
    monkeypatch.delenv("SPECFACT_MODULES_REPO", raising=False)

    before = "SPECFACT_MODULES_REPO" in os.environ
    env = module.build_review_subprocess_env()
    after = "SPECFACT_MODULES_REPO" in os.environ

    assert before is False
    assert after is False
    assert env["SPECFACT_MODULES_REPO"] == str(modules_root.resolve())
    assert env["XDG_CONFIG_HOME"] == str((fake_repo / ".specfact" / "config").resolve())
    assert env["XDG_CACHE_HOME"] == str((fake_repo / ".specfact" / "cache").resolve())
    assert env["SEMGREP_VERSION_CACHE_PATH"] == str((fake_repo / ".specfact" / "cache" / "semgrep").resolve())
    assert env["SEMGREP_LOG_FILE"] == str((fake_repo / ".specfact" / "logs" / "semgrep.log").resolve())
    assert Path(env["XDG_CONFIG_HOME"]).is_dir()
    assert Path(env["XDG_CACHE_HOME"]).is_dir()
    assert Path(env["SEMGREP_VERSION_CACHE_PATH"]).is_dir()


def test_build_review_subprocess_env_preserves_explicit_value(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """An explicit ``SPECFACT_MODULES_REPO`` must not be overwritten in the returned env."""
    module = _load_script_module()
    explicit = str(tmp_path / "custom-modules")
    monkeypatch.setenv("SPECFACT_MODULES_REPO", explicit)
    env = module.build_review_subprocess_env()
    assert env["SPECFACT_MODULES_REPO"] == explicit


def test_build_review_subprocess_env_overrides_explicit_xdg_paths(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Nested review tooling must ignore ambient XDG paths and use repo-local dirs."""
    module = _load_script_module()
    explicit_config = str(tmp_path / "xdg-config")
    explicit_cache = str(tmp_path / "xdg-cache")
    fake_repo = tmp_path / "repo"
    (fake_repo / "scripts").mkdir(parents=True)
    monkeypatch.setattr(module, "_repo_root", lambda: fake_repo)
    monkeypatch.setenv("XDG_CONFIG_HOME", explicit_config)
    monkeypatch.setenv("XDG_CACHE_HOME", explicit_cache)

    env = module.build_review_subprocess_env()

    assert env["XDG_CONFIG_HOME"] == str((fake_repo / ".specfact" / "config").resolve())
    assert env["XDG_CACHE_HOME"] == str((fake_repo / ".specfact" / "cache").resolve())

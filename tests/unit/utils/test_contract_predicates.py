"""Tests for typed icontract path/string predicates."""

from __future__ import annotations

from pathlib import Path

from specfact_cli.utils import contract_predicates as cp


def test_repo_path_exists(tmp_path: Path) -> None:
    assert cp.repo_path_exists(tmp_path) is True


def test_optional_repo_path_exists() -> None:
    assert cp.optional_repo_path_exists(None) is True


def test_report_path_is_parseable_repro(tmp_path: Path) -> None:
    p = tmp_path / "r.yaml"
    p.write_text("checks: []", encoding="utf-8")
    assert cp.report_path_is_parseable_repro(p) is True


def test_class_name_nonblank() -> None:
    assert cp.class_name_nonblank("X") is True
    assert cp.class_name_nonblank("  ") is False


def test_vscode_settings_result_ok(tmp_path: Path) -> None:
    p = tmp_path / "s.json"
    p.write_text("{}", encoding="utf-8")
    assert cp.vscode_settings_result_ok(p) is True
    assert cp.vscode_settings_result_ok(None) is True


def test_settings_relative_nonblank() -> None:
    assert cp.settings_relative_nonblank(".vscode/settings.json") is True
    assert cp.settings_relative_nonblank("  ") is False
    assert cp.settings_relative_nonblank("/abs/settings.json") is False
    assert cp.settings_relative_nonblank(".vscode/../settings.json") is False


def test_prompt_files_all_strings() -> None:
    assert cp.prompt_files_all_strings([]) is True
    assert cp.prompt_files_all_strings(["a", "b"]) is True
    assert cp.prompt_files_all_strings(["a", 1]) is False
    assert cp.prompt_files_all_strings(["a", None]) is False

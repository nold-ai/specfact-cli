"""Tests for typed icontract predicate helpers."""

from __future__ import annotations

from pathlib import Path

from specfact_cli.models.protocol import Protocol
from specfact_cli.utils import icontract_helpers as ih


def test_require_path_exists_true(tmp_path: Path) -> None:
    p = tmp_path / "a.txt"
    p.write_text("x", encoding="utf-8")
    assert ih.require_path_exists(p) is True


def test_require_path_exists_false(tmp_path: Path) -> None:
    assert ih.require_path_exists(tmp_path / "missing.txt") is False


def test_require_protocol_has_states() -> None:
    p = Protocol(
        states=["a"],
        start="a",
        transitions=[],
    )
    assert ih.require_protocol_has_states(p) is True


def test_require_protocol_has_states_empty() -> None:
    p = Protocol(states=[], start="a", transitions=[])
    assert ih.require_protocol_has_states(p) is False


def test_require_python_version_is_3_x() -> None:
    assert ih.require_python_version_is_3_x("3.12") is True
    assert ih.require_python_version_is_3_x("2.7") is False


def test_ensure_yaml_suffix_helpers(tmp_path: Path) -> None:
    y = tmp_path / "f.yml"
    y.write_text("x", encoding="utf-8")
    assert ih.ensure_github_workflow_output_suffix(y) is True
    assert ih.ensure_yaml_output_suffix(y) is True
    assert ih.ensure_yaml_output_suffix(tmp_path / "g.yaml") is True

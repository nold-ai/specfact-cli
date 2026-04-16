"""Tests for scripts/_detect_modules_to_publish.py."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


def _repo_root() -> Path:
    here = Path(__file__).resolve().parent
    for candidate in (here, *here.parents):
        script = candidate / "scripts" / "_detect_modules_to_publish.py"
        if script.is_file() and (candidate / "pyproject.toml").is_file():
            return candidate
    raise AssertionError("repository root not found")


def _load_script():
    root = _repo_root()
    path = root / "scripts" / "_detect_modules_to_publish.py"
    spec = importlib.util.spec_from_file_location("_detect_modules_to_publish", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def detect_mod():
    return _load_script()


def test_is_strictly_newer_semver_greater(detect_mod) -> None:
    assert detect_mod._is_strictly_newer("2.0.0", "1.9.9") is True


def test_is_strictly_newer_rejects_unparsable_candidate(detect_mod) -> None:
    assert detect_mod._is_strictly_newer("not-a-version", "1.0.0") is False


def test_is_strictly_newer_rejects_unparsable_registered(detect_mod) -> None:
    assert detect_mod._is_strictly_newer("2.0.0", "not-a-version") is False


def test_load_registry_versions_requires_modules_array(tmp_path: Path, detect_mod) -> None:
    reg = tmp_path / "index.json"
    reg.write_text('{"not_modules": []}', encoding="utf-8")
    with pytest.raises(ValueError, match="modules"):
        detect_mod._load_registry_versions(reg)


def test_load_registry_versions_rejects_non_list_modules(tmp_path: Path, detect_mod) -> None:
    reg = tmp_path / "index.json"
    reg.write_text('{"modules": {}}', encoding="utf-8")
    with pytest.raises(ValueError, match="modules"):
        detect_mod._load_registry_versions(reg)

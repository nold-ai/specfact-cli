from __future__ import annotations

import ast
import re
import tomllib
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize(
    ("name", "version"),
    [
        ("certifi", "2026.10.19"),
        ("gitpython", "3.2.1"),
        ("pyjwt", "2.15.1"),
        ("hatchling", "1.32.4"),
        ("urllib3", "2.8.0"),
        ("virtualenv", "21.14.12"),
        ("python-discovery", "1.6.1"),
        ("packaging", "26.3"),
        ("pycparser", "3.12"),
    ],
)
def test_reviewed_tooling_versions_match_frozen_export(name: str, version: str) -> None:
    lock = tomllib.loads((REPO_ROOT / "uv.lock").read_text(encoding="utf-8"))
    packages = [package for package in lock["package"] if package["name"] == name]
    assert len(packages) == 1
    assert packages[0]["version"] == version
    assert packages[0]["source"] == {"registry": "https://pypi.org/simple"}
    export = (REPO_ROOT / "requirements/ci/locked.txt").read_text(encoding="utf-8")
    assert re.search(rf"^{re.escape(name)}=={re.escape(version)}\s", export, re.MULTILINE)


@pytest.mark.parametrize(
    ("name", "version"),
    [("jekyll-feed", "0.18.0"), ("jekyll-redirect-from", "0.17.0"), ("jekyll-relative-links", "0.9.1")],
)
def test_reviewed_documentation_plugins_are_locked(name: str, version: str) -> None:
    locked = (REPO_ROOT / "docs/Gemfile.lock").read_text(encoding="utf-8")
    assert re.search(rf"^    {re.escape(name)} \({re.escape(version)}\)$", locked, re.MULTILINE)


def test_documentation_json_has_reviewed_floor_and_major_bound() -> None:
    gemfile = (REPO_ROOT / "docs/Gemfile").read_text(encoding="utf-8")
    assert 'gem "json", ">= 2.21.2", "< 3"' in gemfile


@pytest.mark.parametrize(
    "requirement",
    [
        pytest.param("gitpython>=3.2.1", id="gitpython-floor"),
        pytest.param("pycparser>=3.12,!=3.0.*", id="pycparser-floor"),
    ],
)
def test_public_declarations_require_reviewed_security_floor(requirement: str) -> None:
    project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert requirement in project["project"]["dependencies"]
    setup = ast.parse((REPO_ROOT / "setup.py").read_text(encoding="utf-8"))
    declarations = [
        ast.literal_eval(keyword.value)
        for node in ast.walk(setup)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "setup"
        for keyword in node.keywords
        if keyword.arg == "install_requires"
    ]
    assert len(declarations) == 1
    assert requirement in declarations[0]

"""The child smoke environment must not invoke parent package entry points."""

import os
import sys
from pathlib import Path

import pytest


def test_isolated_smoke_does_not_use_parent_cli_tools(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Parent entry points cannot resolve/install packages for the child interpreter."""
    import scripts.runtime_discovery_smoke as smoke

    parent_bin = str(Path(sys.prefix) / ("Scripts" if sys.platform == "win32" else "bin"))
    monkeypatch.setenv("PATH", parent_bin + os.pathsep + os.defpath)
    home = tmp_path / "home-direct"
    env = smoke._build_launcher_env("direct", home, tmp_path / "index.json", tmp_path / "modules")
    assert parent_bin not in env["PATH"].split(os.pathsep)
    assert "VIRTUAL_ENV" not in env

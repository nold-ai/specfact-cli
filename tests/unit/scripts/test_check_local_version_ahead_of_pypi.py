"""Tests for scripts/check_local_version_ahead_of_pypi.py."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _load_module():
    root = Path(__file__).resolve().parents[3]
    path = root / "scripts" / "check_local_version_ahead_of_pypi.py"
    spec = importlib.util.spec_from_file_location("_check_pypi_ahead", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_mod = _load_module()


@pytest.mark.parametrize(
    ("local", "pypi", "expect_ok"),
    (
        ("0.46.1", "0.46.0", True),
        ("0.46.0", "0.46.0", False),
        ("0.45.9", "0.46.0", False),
        ("1.0.0", None, True),
    ),
)
def test_compare_local_to_pypi_version(local: str, pypi: str | None, expect_ok: bool) -> None:
    ok, _msg = _mod.compare_local_to_pypi_version(local, pypi)
    assert ok is expect_ok


def test_fetch_latest_pypi_version_404_returns_none() -> None:
    import urllib.error

    with patch("urllib.request.urlopen") as mock_open:
        mock_open.side_effect = urllib.error.HTTPError(
            "https://pypi.org/pypi/nonexistent-pkg-xyz/json",
            404,
            "Not Found",
            hdrs=MagicMock(),
            fp=None,
        )
        assert _mod.fetch_latest_pypi_version("nonexistent-pkg-xyz") is None


def test_fetch_latest_pypi_version_parses_info_version() -> None:
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"info": {"version": "0.46.0"}}'
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value = mock_response
    mock_cm.__exit__.return_value = None

    with patch("urllib.request.urlopen", return_value=mock_cm):
        assert _mod.fetch_latest_pypi_version("specfact-cli") == "0.46.0"


def test_main_network_error_exit_code_2() -> None:
    with (
        patch.object(_mod, "fetch_latest_pypi_version", side_effect=RuntimeError("boom")),
        patch.object(_mod, "read_local_version", return_value="9.9.9"),
    ):
        assert _mod.main() == 2


def test_main_skip_env_returns_0() -> None:
    with patch.dict(os.environ, {"SPECFACT_SKIP_PYPI_VERSION_CHECK": "1"}):
        assert _mod.main() == 0


def test_script_exits_zero_when_skip_env() -> None:
    script = Path(__file__).resolve().parents[3] / "scripts" / "check_local_version_ahead_of_pypi.py"
    env = os.environ.copy()
    env["SPECFACT_SKIP_PYPI_VERSION_CHECK"] = "1"
    completed = subprocess.run(
        [sys.executable, str(script)],
        check=False,
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr

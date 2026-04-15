"""Tests for scripts/check_local_version_ahead_of_pypi.py."""

from __future__ import annotations

import importlib.util
import os
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


@pytest.fixture
def mod():
    return _load_module()


@pytest.mark.parametrize(
    ("local", "pypi", "expect_ok"),
    (
        ("0.46.1", "0.46.0", True),
        ("0.46.0", "0.46.0", False),
        ("0.45.9", "0.46.0", False),
        ("1.0.0", None, True),
    ),
)
def test_compare_local_to_pypi_version(mod, local: str, pypi: str | None, expect_ok: bool) -> None:
    ok, _msg = mod.compare_local_to_pypi_version(local, pypi)
    assert ok is expect_ok


def test_fetch_latest_pypi_version_404_returns_none(mod) -> None:
    import urllib.error

    with patch("urllib.request.urlopen") as mock_open:
        mock_open.side_effect = urllib.error.HTTPError(
            "https://pypi.org/pypi/nonexistent-pkg-xyz/json",
            404,
            "Not Found",
            hdrs=MagicMock(),
            fp=None,
        )
        assert mod.fetch_latest_pypi_version("nonexistent-pkg-xyz") is None


def test_fetch_latest_pypi_version_parses_info_version(mod) -> None:
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"info": {"version": "0.46.0"}}'
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value = mock_response
    mock_cm.__exit__.return_value = None

    with patch("urllib.request.urlopen", return_value=mock_cm):
        assert mod.fetch_latest_pypi_version("specfact-cli") == "0.46.0"


def test_main_network_error_exit_code_2(mod) -> None:
    with (
        patch.object(mod, "fetch_latest_pypi_version", side_effect=mod.PypiFetchError("boom")),
        patch.object(mod, "read_local_version", return_value="9.9.9"),
    ):
        assert mod.main() == 2


def test_main_pypi_fetch_lenient_network_returns_0(mod) -> None:
    with (
        patch.object(mod, "fetch_latest_pypi_version", side_effect=mod.PypiFetchError("boom")),
        patch.object(mod, "read_local_version", return_value="9.9.9"),
        patch.dict(os.environ, {"SPECFACT_PYPI_VERSION_CHECK_LENIENT_NETWORK": "1"}),
    ):
        assert mod.main() == 0


def test_main_skip_env_returns_0(mod) -> None:
    with patch.dict(os.environ, {"SPECFACT_SKIP_PYPI_VERSION_CHECK": "1"}):
        assert mod.main() == 0


def test_main_invalid_version_exit_code_2(mod) -> None:
    with (
        patch.object(mod, "fetch_latest_pypi_version", return_value="0.46.0"),
        patch.object(mod, "read_local_version", return_value="not-a-version"),
    ):
        assert mod.main() == 2


def test_read_project_version_from_pyproject_bytes(mod) -> None:
    toml = b'[project]\nname = "x"\nversion = "1.2.3"\n'
    assert mod.read_project_version_from_pyproject_bytes(toml) == "1.2.3"


def test_main_skip_when_version_unchanged_vs_skips_pypi_query(mod) -> None:
    with (
        patch.object(mod, "read_local_version", return_value="9.9.9"),
        patch.object(mod, "pyproject_version_at_git_revision", return_value="9.9.9"),
        patch.object(mod, "fetch_latest_pypi_version") as fetch_mock,
    ):
        assert mod.main(["--skip-when-version-unchanged-vs", "deadbeef"]) == 0
    fetch_mock.assert_not_called()


def test_main_skip_when_base_unknown_still_queries_pypi(mod) -> None:
    with (
        patch.object(mod, "read_local_version", return_value="99.0.0"),
        patch.object(mod, "pyproject_version_at_git_revision", return_value=None),
        patch.object(mod, "fetch_latest_pypi_version", return_value="0.1.0"),
    ):
        assert mod.main(["--skip-when-version-unchanged-vs", "deadbeef"]) == 0

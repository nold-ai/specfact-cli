"""Unit tests for optional dependency helpers."""

import subprocess
from unittest.mock import patch

from specfact_cli.utils.optional_deps import (
    check_cli_tool_available,
    check_enhanced_analysis_dependencies,
    check_python_package_available,
)


def test_check_python_package_available_returns_false_for_control_character_name() -> None:
    """Control-character package names should fail closed instead of raising."""

    assert check_python_package_available("\x00") is False


def test_check_enhanced_analysis_deps_pycg_resolves_false_when_unavailable() -> None:
    """When `pycg` is not on PATH, the check must surface (False, hint) — not just expose the key."""
    with patch("specfact_cli.utils.optional_deps._resolve_cli_tool_executable", return_value=None):
        result = check_enhanced_analysis_dependencies()
    assert "pycg" in result, "'pycg' key must be present after migration"
    available, hint = result["pycg"]
    assert available is False, "shutil.which patched to None must produce a 'not available' result for pycg"
    assert isinstance(hint, str) and "pycg" in hint, "missing-tool hint must mention pycg"


def test_check_enhanced_analysis_deps_excludes_removed_tools() -> None:
    """`pyan3` (GPL), `syft` (wrong PyPI), and `bearer` (wrong PyPI) must be absent post-migration."""
    with patch("specfact_cli.utils.optional_deps._resolve_cli_tool_executable", return_value=None):
        result = check_enhanced_analysis_dependencies()
    assert "pyan3" not in result, "'pyan3' must be removed — it is GPL-2.0 and unmaintained"
    assert "syft" not in result, "'syft' (PyPI) is the wrong package (OpenMined ML, not Anchore SBOM)"
    assert "bearer" not in result, "'bearer' (PyPI) is the wrong package (SaaS auth client, not security scanner)"


def test_check_enhanced_analysis_deps_bandit_resolves_false_when_unavailable() -> None:
    """When `bandit` is not on PATH, the check must surface (False, hint) — not just expose the key."""
    with patch("specfact_cli.utils.optional_deps._resolve_cli_tool_executable", return_value=None):
        result = check_enhanced_analysis_dependencies()
    assert "bandit" in result, "'bandit' key must be present after migration"
    available, hint = result["bandit"]
    assert available is False, "shutil.which patched to None must produce a 'not available' result for bandit"
    assert isinstance(hint, str) and "bandit" in hint, "missing-tool hint must mention bandit"


def test_check_cli_tool_available_uses_pycg_help_probe() -> None:
    """PyCG must be probed with ``-h`` because ``--version`` expects a value."""

    def _fake_run(cmd: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        assert cmd == ["/tmp/pycg", "-h"]
        return subprocess.CompletedProcess(cmd, 0, stdout="usage: pycg", stderr="")

    with (
        patch("specfact_cli.utils.optional_deps._resolve_cli_tool_executable", return_value="/tmp/pycg"),
        patch("specfact_cli.utils.optional_deps.subprocess.run", side_effect=_fake_run),
    ):
        available, hint = check_cli_tool_available("pycg")

    assert available is True
    assert hint is None

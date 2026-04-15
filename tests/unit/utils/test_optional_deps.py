"""Unit tests for optional dependency helpers."""

from unittest.mock import patch

from specfact_cli.utils.optional_deps import check_enhanced_analysis_dependencies, check_python_package_available


def test_check_python_package_available_returns_false_for_control_character_name() -> None:
    """Control-character package names should fail closed instead of raising."""

    assert check_python_package_available("\x00") is False


def test_check_optional_analysis_deps_includes_pycg_key() -> None:
    """After migration, check_optional_analysis_deps must return a 'pycg' key."""
    with patch("shutil.which", return_value=None):
        result = check_enhanced_analysis_dependencies()
    assert "pycg" in result, "'pycg' key must be present after migration"


def test_check_optional_analysis_deps_excludes_pyan3() -> None:
    """After migration, 'pyan3' must NOT appear in check_optional_analysis_deps."""
    with patch("shutil.which", return_value=None):
        result = check_enhanced_analysis_dependencies()
    assert "pyan3" not in result, "'pyan3' must be removed — it is GPL-2.0 and unmaintained"


def test_check_optional_analysis_deps_excludes_syft() -> None:
    """After migration, 'syft' must NOT appear in check_optional_analysis_deps."""
    with patch("shutil.which", return_value=None):
        result = check_enhanced_analysis_dependencies()
    assert "syft" not in result, "'syft' (PyPI) is the wrong package (OpenMined ML, not Anchore SBOM)"


def test_check_optional_analysis_deps_excludes_bearer() -> None:
    """After migration, 'bearer' must NOT appear in check_optional_analysis_deps."""
    with patch("shutil.which", return_value=None):
        result = check_enhanced_analysis_dependencies()
    assert "bearer" not in result, "'bearer' (PyPI) is the wrong package (SaaS auth client, not security scanner)"


def test_check_optional_analysis_deps_includes_bandit_key() -> None:
    """After migration, 'bandit' must appear as a checked CLI tool."""
    with patch("shutil.which", return_value=None):
        result = check_enhanced_analysis_dependencies()
    assert "bandit" in result, "'bandit' key must be present after migration"

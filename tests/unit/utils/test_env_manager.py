"""Unit tests for environment manager detection utilities.

Focus: Business logic and edge cases only (@beartype handles type validation).
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from specfact_cli.utils.env_manager import (
    EnvManager,
    EnvManagerInfo,
    build_tool_command,
    check_tool_in_env,
    detect_env_manager,
    detect_source_directories,
)


class TestDetectEnvManager:
    """Test environment manager detection."""

    def test_detect_hatch_from_pyproject(self, tmp_path: Path):
        """Test detection of hatch from pyproject.toml."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[tool.hatch]
version = "1.0.0"
"""
        )

        with patch("shutil.which", return_value="/usr/bin/hatch"):
            info = detect_env_manager(tmp_path)

        assert info.manager == EnvManager.HATCH
        assert info.available is True
        assert info.command_prefix == ["hatch", "run"]
        assert info.message is not None and "hatch" in info.message.lower()

    def test_detect_hatch_not_available(self, tmp_path: Path):
        """Test detection of hatch when not available in PATH."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[tool.hatch]
version = "1.0.0"
"""
        )

        with patch("shutil.which", return_value=None):
            info = detect_env_manager(tmp_path)

        assert info.manager == EnvManager.HATCH
        assert info.available is False
        assert info.command_prefix == []
        assert info.message is not None and "not found" in info.message.lower()

    def test_detect_poetry_from_pyproject(self, tmp_path: Path):
        """Test detection of poetry from pyproject.toml."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[tool.poetry]
name = "test-project"
version = "1.0.0"
"""
        )

        with patch("shutil.which", return_value="/usr/bin/poetry"):
            info = detect_env_manager(tmp_path)

        assert info.manager == EnvManager.POETRY
        assert info.available is True
        assert info.command_prefix == ["poetry", "run"]

    def test_detect_poetry_from_lock(self, tmp_path: Path):
        """Test detection of poetry from poetry.lock."""
        lock_file = tmp_path / "poetry.lock"
        lock_file.write_text('[[package]]\nname = "test"\nversion = "1.0.0"')

        with patch("shutil.which", return_value="/usr/bin/poetry"):
            info = detect_env_manager(tmp_path)

        assert info.manager == EnvManager.POETRY
        assert info.available is True
        assert info.command_prefix == ["poetry", "run"]
        assert info.message is not None and "poetry.lock" in info.message.lower()

    def test_detect_uv_from_pyproject(self, tmp_path: Path):
        """Test detection of uv from pyproject.toml."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[tool.uv]
version = "1.0.0"
"""
        )

        with patch("shutil.which", return_value="/usr/bin/uv"):
            info = detect_env_manager(tmp_path)

        assert info.manager == EnvManager.UV
        assert info.available is True
        assert info.command_prefix == ["uv", "run"]

    def test_detect_uv_from_lock(self, tmp_path: Path):
        """Test detection of uv from uv.lock."""
        lock_file = tmp_path / "uv.lock"
        lock_file.write_text("version = 1")

        with patch("shutil.which", return_value="/usr/bin/uv"):
            info = detect_env_manager(tmp_path)

        assert info.manager == EnvManager.UV
        assert info.available is True
        assert info.command_prefix == ["uv", "run"]

    def test_detect_uv_from_toml(self, tmp_path: Path):
        """Test detection of uv from uv.toml."""
        uv_toml = tmp_path / "uv.toml"
        uv_toml.write_text("version = 1")

        with patch("shutil.which", return_value="/usr/bin/uv"):
            info = detect_env_manager(tmp_path)

        assert info.manager == EnvManager.UV
        assert info.available is True
        assert info.command_prefix == ["uv", "run"]

    def test_detect_pip_from_requirements(self, tmp_path: Path):
        """Test detection of pip from requirements.txt."""
        requirements = tmp_path / "requirements.txt"
        requirements.write_text("requests==1.0.0\n")

        info = detect_env_manager(tmp_path)

        assert info.manager == EnvManager.PIP
        assert info.available is True
        assert info.command_prefix == []
        assert info.message is not None and "requirements.txt" in info.message.lower()

    def test_detect_pip_from_setup_py(self, tmp_path: Path):
        """Test detection of pip from setup.py."""
        setup_py = tmp_path / "setup.py"
        setup_py.write_text("from setuptools import setup\nsetup(name='test')")

        info = detect_env_manager(tmp_path)

        assert info.manager == EnvManager.PIP
        assert info.available is True
        assert info.command_prefix == []

    def test_detect_unknown_fallback(self, tmp_path: Path):
        """Test fallback to unknown when no manager detected."""
        info = detect_env_manager(tmp_path)

        assert info.manager == EnvManager.UNKNOWN
        assert info.available is True
        assert info.command_prefix == []
        assert info.message is not None and "No environment manager detected" in info.message

    def test_detect_priority_hatch_over_poetry(self, tmp_path: Path):
        """Test that hatch takes priority over poetry when both present."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[tool.hatch]
version = "1.0.0"
[tool.poetry]
name = "test"
"""
        )

        with patch("shutil.which", return_value="/usr/bin/hatch"):
            info = detect_env_manager(tmp_path)

        assert info.manager == EnvManager.HATCH


class TestBuildToolCommand:
    """Test building tool commands with environment prefixes."""

    def test_build_command_with_hatch(self):
        """Test building command with hatch prefix."""
        env_info = EnvManagerInfo(
            manager=EnvManager.HATCH,
            available=True,
            command_prefix=["hatch", "run"],
            message="Test",
        )
        tool_command = ["python", "-m", "crosshair", "check", "src/"]

        result = build_tool_command(env_info, tool_command)

        assert result == ["hatch", "run", "python", "-m", "crosshair", "check", "src/"]

    def test_build_command_with_poetry(self):
        """Test building command with poetry prefix."""
        env_info = EnvManagerInfo(
            manager=EnvManager.POETRY,
            available=True,
            command_prefix=["poetry", "run"],
            message="Test",
        )
        tool_command = ["ruff", "check", "src/"]

        result = build_tool_command(env_info, tool_command)

        assert result == ["poetry", "run", "ruff", "check", "src/"]

    def test_build_command_with_uv(self):
        """Test building command with uv prefix."""
        env_info = EnvManagerInfo(
            manager=EnvManager.UV,
            available=True,
            command_prefix=["uv", "run"],
            message="Test",
        )
        tool_command = ["basedpyright", "src/"]

        result = build_tool_command(env_info, tool_command)

        assert result == ["uv", "run", "basedpyright", "src/"]

    def test_build_command_with_pip(self):
        """Test building command with pip (no prefix)."""
        env_info = EnvManagerInfo(
            manager=EnvManager.PIP,
            available=True,
            command_prefix=[],
            message="Test",
        )
        tool_command = ["ruff", "check", "src/"]

        result = build_tool_command(env_info, tool_command)

        assert result == ["ruff", "check", "src/"]

    def test_build_command_unavailable_manager(self):
        """Test building command when manager not available."""
        env_info = EnvManagerInfo(
            manager=EnvManager.HATCH,
            available=False,
            command_prefix=[],
            message="Test",
        )
        tool_command = ["ruff", "check", "src/"]

        result = build_tool_command(env_info, tool_command)

        assert result == ["ruff", "check", "src/"]


class TestCheckToolInEnv:
    """Test checking tool availability in environment."""

    def test_check_tool_available_globally(self, tmp_path: Path):
        """Test checking tool available globally."""
        with patch("shutil.which", return_value="/usr/bin/ruff"):
            available, message = check_tool_in_env(tmp_path, "ruff")

        assert available is True
        assert message is None

    def test_check_tool_not_available(self, tmp_path: Path):
        """Test checking tool not available."""
        with patch("shutil.which", return_value=None):
            available, message = check_tool_in_env(tmp_path, "nonexistent")

        assert available is False
        assert message is not None
        assert "not found" in message.lower()
        assert "install" in message.lower()

    def test_check_tool_with_env_info(self, tmp_path: Path):
        """Test checking tool with pre-detected environment info."""
        env_info = EnvManagerInfo(
            manager=EnvManager.HATCH,
            available=True,
            command_prefix=["hatch", "run"],
            message="Test",
        )

        with patch("shutil.which", return_value="/usr/bin/ruff"):
            available, message = check_tool_in_env(tmp_path, "ruff", env_info)

        assert available is True
        assert message is None


class TestDetectSourceDirectories:
    """Test source directory detection."""

    def test_detect_src_directory(self, tmp_path: Path):
        """Test detection of src/ directory."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "__init__.py").write_text("")

        result = detect_source_directories(tmp_path)

        assert "src/" in result

    def test_detect_lib_directory(self, tmp_path: Path):
        """Test detection of lib/ directory."""
        lib_dir = tmp_path / "lib"
        lib_dir.mkdir()

        result = detect_source_directories(tmp_path)

        assert "lib/" in result

    def test_detect_package_from_pyproject(self, tmp_path: Path):
        """Test detection of package name from pyproject.toml."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[project]
name = "my-package"
"""
        )
        # Package name "my-package" converts to directory "my_package" or "my-package"
        # Try both common conventions
        for package_dir_name in ["my_package", "my-package"]:
            package_dir = tmp_path / package_dir_name
            if package_dir.exists():
                package_dir.rmdir()
            package_dir.mkdir()
            (package_dir / "__init__.py").write_text("")

            result = detect_source_directories(tmp_path)

            # Should detect at least one of the package directories
            assert len(result) > 0
            assert any(package_dir_name in r for r in result)
            break

    def test_detect_package_from_poetry(self, tmp_path: Path):
        """Test detection of package name from poetry config."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[tool.poetry]
name = "poetry-package"
"""
        )
        # Package name "poetry-package" converts to directory "poetry_package" or "poetry-package"
        # Try both common conventions
        for package_dir_name in ["poetry_package", "poetry-package"]:
            package_dir = tmp_path / package_dir_name
            if package_dir.exists():
                package_dir.rmdir()
            package_dir.mkdir()
            (package_dir / "__init__.py").write_text("")

            result = detect_source_directories(tmp_path)

            # Should detect at least one of the package directories
            assert len(result) > 0
            assert any(package_dir_name in r for r in result)
            break

    def test_detect_no_standard_directories(self, tmp_path: Path):
        """Test detection when no standard directories exist."""
        result = detect_source_directories(tmp_path)

        assert result == []

    def test_detect_multiple_directories(self, tmp_path: Path):
        """Test detection of multiple source directories."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        lib_dir = tmp_path / "lib"
        lib_dir.mkdir()

        result = detect_source_directories(tmp_path)

        assert "src/" in result
        assert "lib/" in result

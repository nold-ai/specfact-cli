"""
Unit tests for update command.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from specfact_cli.modules.upgrade.src.commands import (
    InstallationMethod,
    _upgrade_install_or_check_only,
    detect_installation_method,
    install_update,
)


class TestInstallationMethodDetection:
    """Tests for installation method detection."""

    @patch("specfact_cli.modules.upgrade.src.commands.subprocess.run")
    @patch("specfact_cli.modules.upgrade.src.commands.sys.executable", "/workspace/specfact-cli/.venv/bin/python")
    @patch(
        "specfact_cli.modules.upgrade.src.commands.sys.argv",
        ["/workspace/specfact-cli/.venv/bin/python", "-m", "specfact_cli"],
    )
    @patch.dict(
        "specfact_cli.modules.upgrade.src.commands.os.environ",
        {"UV_PROJECT_ENVIRONMENT": "/workspace/specfact-cli/.venv"},
        clear=False,
    )
    def test_detect_uv_virtualenv_installation(self, mock_subprocess: MagicMock) -> None:
        """Test detecting uv-managed venv installation."""
        method = detect_installation_method()
        assert method.method == "uv"
        assert (
            method.command == "uv pip install --python /workspace/specfact-cli/.venv/bin/python --upgrade specfact-cli"
        )
        assert method.location == "/workspace/specfact-cli/.venv/bin/python"

    @patch("specfact_cli.modules.upgrade.src.commands.subprocess.run")
    @patch("specfact_cli.modules.upgrade.src.commands.sys.executable", "/usr/bin/python3")
    @patch("specfact_cli.modules.upgrade.src.commands.sys.argv", ["/usr/bin/python3", "-m", "specfact_cli"])
    def test_detect_pip_installation(self, mock_subprocess: MagicMock) -> None:
        """Test detecting pip installation."""

        # pipx check fails (not pipx), then pip show succeeds
        def side_effect(*args, **kwargs):
            result = MagicMock()
            cmd = args[0] if args else []
            cmd_str = " ".join(cmd) if isinstance(cmd, list) else str(cmd)
            if "pipx" in cmd_str:
                # pipx list fails (not installed via pipx)
                result.returncode = 1
            elif "pip" in cmd_str and "show" in cmd_str:
                # pip show succeeds
                result.returncode = 0
                result.stdout = "Name: specfact-cli\nLocation: /usr/local/lib/python3.11/site-packages"
            else:
                result.returncode = 1
            return result

        mock_subprocess.side_effect = side_effect

        method = detect_installation_method()
        assert method.method == "pip", f"Expected pip, got {method.method}"
        assert "pip" in method.command.lower()

    @patch("specfact_cli.modules.upgrade.src.commands.subprocess.run")
    @patch("specfact_cli.modules.upgrade.src.commands.sys.argv", ["uvx", "--from", "specfact-cli", "specfact"])
    def test_detect_uvx_installation(self, mock_subprocess: MagicMock) -> None:
        """Test detecting uvx installation."""
        method = detect_installation_method()
        assert method.method == "uvx"

    @patch("specfact_cli.modules.upgrade.src.commands.subprocess.run")
    @patch("specfact_cli.modules.upgrade.src.commands.sys.executable", "/tmp/not-uvx-cache/bin/python")
    @patch("specfact_cli.modules.upgrade.src.commands.sys.argv", ["/tmp/not-uvx-cache/bin/specfact"])
    def test_detect_uvx_avoids_substring_false_positive(self, mock_subprocess: MagicMock) -> None:
        """uvx detection must match path segments, not arbitrary substrings."""
        mock_subprocess.return_value.returncode = 1
        mock_subprocess.return_value.stdout = ""

        method = detect_installation_method()
        assert method.method == "pip"

    @patch("specfact_cli.modules.upgrade.src.commands.subprocess.run")
    @patch("specfact_cli.modules.upgrade.src.commands.sys.executable", "/usr/bin/python3")
    @patch("specfact_cli.modules.upgrade.src.commands.sys.argv", ["/usr/bin/python3", "-m", "specfact_cli"])
    def test_detect_pipx_installation(self, mock_subprocess: MagicMock) -> None:
        """Test detecting pipx installation."""

        # pipx list returns with specfact-cli
        def side_effect(*args, **kwargs):
            result = MagicMock()
            # Check if pipx is in the command
            cmd = args[0] if args else []
            cmd_str = " ".join(cmd) if isinstance(cmd, list) else str(cmd)
            if "pipx" in cmd_str and "list" in cmd_str:
                # pipx list call - returns success with specfact-cli
                result.returncode = 0
                result.stdout = "package specfact-cli 1.0.0"
            else:
                # Other calls (pip show, etc.) - fail
                result.returncode = 1
            return result

        mock_subprocess.side_effect = side_effect

        method = detect_installation_method()
        # Should detect pipx first (before checking pip)
        assert method.method == "pipx", f"Expected pipx, got {method.method}"

    @patch("specfact_cli.modules.upgrade.src.commands.subprocess.run")
    @patch("specfact_cli.modules.upgrade.src.commands.sys.executable", "/usr/bin/python3")
    @patch("specfact_cli.modules.upgrade.src.commands.sys.argv", ["/usr/bin/python3", "-m", "specfact_cli"])
    def test_detect_pipx_before_generic_uv_tool_installation(self, mock_subprocess: MagicMock) -> None:
        """Prefer the active pipx install when a stale uv tool install also exists."""

        def side_effect(*args, **kwargs):
            result = MagicMock()
            cmd = args[0] if args else []
            cmd_str = " ".join(cmd) if isinstance(cmd, list) else str(cmd)
            if "pipx list" in cmd_str:
                result.returncode = 0
                result.stdout = "package specfact-cli 1.0.0"
            elif "uv tool list" in cmd_str:
                result.returncode = 0
                result.stdout = "specfact-cli v0.46.10"
            else:
                result.returncode = 1
                result.stdout = ""
            return result

        mock_subprocess.side_effect = side_effect

        method = detect_installation_method()
        assert method.method == "pipx", f"Expected pipx, got {method.method}"
        assert method.command == "pipx upgrade specfact-cli"

    @patch("specfact_cli.modules.upgrade.src.commands.subprocess.run")
    @patch("specfact_cli.modules.upgrade.src.commands.sys.executable", "/usr/bin/python3")
    @patch("specfact_cli.modules.upgrade.src.commands.sys.argv", ["/usr/bin/python3", "-m", "specfact_cli"])
    def test_detect_uv_tool_installation(self, mock_subprocess: MagicMock) -> None:
        """Test detecting uv tool installation via `uv tool list`."""

        def side_effect(*args, **kwargs):
            result = MagicMock()
            cmd = args[0] if args else []
            cmd_str = " ".join(cmd) if isinstance(cmd, list) else str(cmd)
            if "pipx list" in cmd_str:
                result.returncode = 1
                result.stdout = ""
            elif "uv tool list" in cmd_str:
                result.returncode = 0
                result.stdout = "specfact-cli v0.46.10"
            else:
                result.returncode = 1
                result.stdout = ""
            return result

        mock_subprocess.side_effect = side_effect

        method = detect_installation_method()
        assert method.method == "uv"
        assert method.command == "uv tool upgrade specfact-cli"

    @patch("specfact_cli.modules.upgrade.src.commands.subprocess.run")
    @patch("specfact_cli.modules.upgrade.src.commands.sys.executable", "/usr/bin/python3")
    @patch("specfact_cli.modules.upgrade.src.commands.sys.argv", ["/usr/bin/python3", "-m", "specfact_cli"])
    def test_fallback_to_pip(self, mock_subprocess: MagicMock) -> None:
        """Test fallback to pip when detection fails."""
        # All detection attempts fail
        mock_subprocess.return_value.returncode = 1

        method = detect_installation_method()
        assert method.method == "pip"
        assert method.command == "/usr/bin/python3 -m pip install --upgrade specfact-cli"


class TestUpdateInstallation:
    """Tests for update installation."""

    @patch("specfact_cli.modules.upgrade.src.commands.subprocess.run")
    @patch("specfact_cli.modules.upgrade.src.commands.Confirm.ask", return_value=True)
    @patch("specfact_cli.modules.upgrade.src.commands.update_metadata")
    def test_install_update_pip_success(
        self, mock_update_metadata: MagicMock, mock_confirm: MagicMock, mock_subprocess: MagicMock
    ) -> None:
        """Test successful pip update installation."""
        method = InstallationMethod(method="pip", command="pip install --upgrade specfact-cli", location=None)
        mock_subprocess.return_value.returncode = 0

        result = install_update(method, yes=False)
        assert result is True
        mock_subprocess.assert_called_once()
        mock_update_metadata.assert_called_once()

    @patch("specfact_cli.modules.upgrade.src.commands.subprocess.run")
    @patch("specfact_cli.modules.upgrade.src.commands.Confirm.ask", return_value=False)
    def test_install_update_user_cancels(self, mock_confirm: MagicMock, mock_subprocess: MagicMock) -> None:
        """Test update installation when user cancels."""
        method = InstallationMethod(method="pip", command="pip install --upgrade specfact-cli", location=None)

        result = install_update(method, yes=False)
        assert result is False
        mock_subprocess.assert_not_called()

    @patch("specfact_cli.modules.upgrade.src.commands.subprocess.run")
    @patch("specfact_cli.modules.upgrade.src.commands.update_metadata")
    def test_install_update_with_yes_flag(self, mock_update_metadata: MagicMock, mock_subprocess: MagicMock) -> None:
        """Test update installation with --yes flag (no confirmation)."""
        method = InstallationMethod(method="pip", command="pip install --upgrade specfact-cli", location=None)
        mock_subprocess.return_value.returncode = 0

        result = install_update(method, yes=True)
        assert result is True
        mock_subprocess.assert_called_once()

    @patch("specfact_cli.modules.upgrade.src.commands.subprocess.run")
    def test_install_update_failure(self, mock_subprocess: MagicMock) -> None:
        """Test update installation failure."""
        method = InstallationMethod(method="pip", command="pip install --upgrade specfact-cli", location=None)
        mock_subprocess.return_value.returncode = 1

        result = install_update(method, yes=True)
        assert result is False

    @patch("specfact_cli.modules.upgrade.src.commands.subprocess.run")
    def test_install_update_uvx_informs_user(self, mock_subprocess: MagicMock) -> None:
        """Test update installation for uvx (just informs user)."""
        method = InstallationMethod(method="uvx", command="uvx --from specfact-cli specfact", location=None)

        result = install_update(method, yes=True)
        assert result is True
        # Should not call subprocess for uvx
        mock_subprocess.assert_not_called()

    @patch("specfact_cli.modules.upgrade.src.commands.subprocess.run")
    @patch("specfact_cli.modules.upgrade.src.commands.update_metadata")
    def test_install_update_uv_tool_success(self, mock_update_metadata: MagicMock, mock_subprocess: MagicMock) -> None:
        """Test successful uv tool update installation."""
        method = InstallationMethod(method="uv", command="uv tool upgrade specfact-cli", location=None)
        mock_subprocess.return_value.returncode = 0

        result = install_update(method, yes=True)
        assert result is True
        mock_subprocess.assert_called_once_with(["uv", "tool", "upgrade", "specfact-cli"], check=False, timeout=300)


@patch("specfact_cli.modules.upgrade.src.commands.subprocess.run")
@patch("specfact_cli.modules.upgrade.src.commands.update_metadata")
def test_install_update_pip_with_spaced_executable_uses_shlex(
    mock_update_metadata: MagicMock, mock_subprocess: MagicMock
) -> None:
    """Pip command parsing must handle executable paths with spaces."""
    method = InstallationMethod(
        method="pip",
        command='"/tmp/Program Files/Python/python" -m pip install --upgrade specfact-cli',
        location=None,
    )
    mock_subprocess.return_value.returncode = 0

    result = install_update(method, yes=True)
    assert result is True
    mock_subprocess.assert_called_once_with(
        ["/tmp/Program Files/Python/python", "-m", "pip", "install", "--upgrade", "specfact-cli"],
        check=False,
        timeout=300,
    )


@patch("specfact_cli.modules.upgrade.src.commands.subprocess.run")
@patch("specfact_cli.modules.upgrade.src.commands.update_metadata")
def test_install_update_uv_pip_targets_detected_interpreter(
    mock_update_metadata: MagicMock, mock_subprocess: MagicMock
) -> None:
    """uv pip upgrades must target the detected interpreter location."""
    method = InstallationMethod(
        method="uv",
        command="uv pip install --upgrade specfact-cli",
        location="/workspace/specfact-cli/.venv/bin/python",
    )
    mock_subprocess.return_value.returncode = 0

    result = install_update(method, yes=True)
    assert result is True
    mock_subprocess.assert_called_once_with(
        ["uv", "pip", "install", "--python", "/workspace/specfact-cli/.venv/bin/python", "--upgrade", "specfact-cli"],
        check=False,
        timeout=300,
    )


@patch("specfact_cli.modules.upgrade.src.commands.subprocess.run")
@patch("specfact_cli.modules.upgrade.src.commands.update_metadata")
def test_install_update_returns_true_when_state_write_fails(
    mock_update_metadata: MagicMock, mock_run: MagicMock
) -> None:
    """Successful subprocess upgrade remains successful if metadata persistence fails."""
    method = InstallationMethod(method="pip", command="pip install --upgrade specfact-cli", location=None)
    mock_run.return_value.returncode = 0
    mock_update_metadata.side_effect = OSError("metadata unavailable")

    result = install_update(method, yes=True)
    assert result is True


@patch("specfact_cli.modules.upgrade.src.commands.console.print")
@patch("specfact_cli.modules.upgrade.src.commands.detect_installation_method")
def test_check_only_uvx_does_not_print_upgrade_command(mock_detect: MagicMock, mock_print: MagicMock) -> None:
    """check-only should not print upgrade command for uvx installs."""
    mock_detect.return_value = InstallationMethod(
        method="uvx", command="uvx --from specfact-cli specfact", location=None
    )

    _upgrade_install_or_check_only(version_result=MagicMock(), check_only=True, yes=False)

    printed = "\n".join(str(c.args[0]) for c in mock_print.call_args_list if c.args)
    assert "To upgrade, run" not in printed
    assert "uvx automatically uses the latest version" in printed

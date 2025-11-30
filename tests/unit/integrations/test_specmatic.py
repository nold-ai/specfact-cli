"""Unit tests for Specmatic integration."""

from unittest.mock import MagicMock, patch

import pytest

from specfact_cli.integrations.specmatic import (
    SpecValidationResult,
    check_backward_compatibility,
    check_specmatic_available,
    create_mock_server,
    generate_specmatic_tests,
    validate_spec_with_specmatic,
)


class TestCheckSpecmaticAvailable:
    """Test suite for check_specmatic_available function."""

    def setup_method(self):
        """Clear cache before each test."""
        import specfact_cli.integrations.specmatic as specmatic_module

        specmatic_module._specmatic_command_cache = None

    @patch("specfact_cli.integrations.specmatic.subprocess.run")
    def test_specmatic_available(self, mock_run):
        """Test when Specmatic is available directly."""
        mock_run.return_value = MagicMock(returncode=0)
        is_available, error_msg = check_specmatic_available()
        assert is_available is True
        assert error_msg is None
        # Should try specmatic first
        mock_run.assert_any_call(
            ["specmatic", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )

    @patch("specfact_cli.integrations.specmatic.subprocess.run")
    def test_specmatic_available_via_npx(self, mock_run):
        """Test when Specmatic is available via npx."""
        # First call (specmatic) fails, second (npx) succeeds
        mock_run.side_effect = [
            FileNotFoundError(),  # specmatic not found
            MagicMock(returncode=0),  # npx specmatic works
        ]
        is_available, error_msg = check_specmatic_available()
        assert is_available is True
        assert error_msg is None
        # Should try both
        assert mock_run.call_count == 2

    @patch("specfact_cli.integrations.specmatic.subprocess.run")
    def test_specmatic_not_available_returncode(self, mock_run):
        """Test when Specmatic returns non-zero exit code."""
        # Both specmatic and npx fail
        mock_run.side_effect = [
            MagicMock(returncode=1),  # specmatic fails
            MagicMock(returncode=1),  # npx specmatic also fails
        ]
        is_available, error_msg = check_specmatic_available()
        assert is_available is False
        assert error_msg is not None and "Specmatic CLI not found" in error_msg

    @patch("specfact_cli.integrations.specmatic.subprocess.run")
    def test_specmatic_file_not_found(self, mock_run):
        """Test when Specmatic command is not found."""
        # Both specmatic and npx fail
        mock_run.side_effect = [
            FileNotFoundError(),  # specmatic not found
            FileNotFoundError(),  # npx also not found
        ]
        is_available, error_msg = check_specmatic_available()
        assert is_available is False
        assert error_msg is not None and "Specmatic CLI not found" in error_msg

    @patch("specfact_cli.integrations.specmatic.subprocess.run")
    def test_specmatic_timeout(self, mock_run):
        """Test when Specmatic check times out."""
        import subprocess

        # Both specmatic and npx timeout
        mock_run.side_effect = [
            subprocess.TimeoutExpired("specmatic", 5),
            subprocess.TimeoutExpired("npx", 10),
        ]
        is_available, error_msg = check_specmatic_available()
        assert is_available is False
        assert error_msg is not None and "Specmatic CLI not found" in error_msg

    @patch("specfact_cli.integrations.specmatic.subprocess.run")
    def test_specmatic_other_error(self, mock_run):
        """Test when Specmatic check raises other exception."""
        # Both specmatic and npx raise exceptions
        mock_run.side_effect = [
            Exception("Unexpected error"),
            Exception("Unexpected error"),
        ]
        is_available, error_msg = check_specmatic_available()
        assert is_available is False
        assert error_msg is not None and "Specmatic CLI not found" in error_msg


class TestSpecValidationResult:
    """Test suite for SpecValidationResult dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = SpecValidationResult(
            is_valid=True,
            schema_valid=True,
            examples_valid=True,
            backward_compatible=True,
            errors=["error1"],
            warnings=["warning1"],
            breaking_changes=["change1"],
        )
        data = result.to_dict()
        assert data["is_valid"] is True
        assert data["schema_valid"] is True
        assert data["examples_valid"] is True
        assert data["backward_compatible"] is True
        assert data["errors"] == ["error1"]
        assert data["warnings"] == ["warning1"]
        assert data["breaking_changes"] == ["change1"]

    def test_to_json(self):
        """Test conversion to JSON string."""
        result = SpecValidationResult(
            is_valid=True,
            schema_valid=True,
            examples_valid=True,
        )
        json_str = result.to_json()
        assert '"is_valid": true' in json_str
        assert '"schema_valid": true' in json_str


class TestValidateSpecWithSpecmatic:
    """Test suite for validate_spec_with_specmatic function."""

    @pytest.mark.asyncio
    @patch("specfact_cli.integrations.specmatic._get_specmatic_command")
    @patch("specfact_cli.integrations.specmatic.asyncio.to_thread")
    async def test_validate_success(self, mock_to_thread, mock_get_cmd, tmp_path):
        """Test successful validation."""
        # Mock specmatic command
        mock_get_cmd.return_value = ["specmatic"]
        # Mock successful subprocess runs
        mock_schema_result = MagicMock(returncode=0, stderr="")
        mock_examples_result = MagicMock(returncode=0, stderr="")
        mock_to_thread.side_effect = [mock_schema_result, mock_examples_result]

        spec_path = tmp_path / "openapi.yaml"
        spec_path.write_text("openapi: 3.0.0\n")

        result = await validate_spec_with_specmatic(spec_path)

        assert result.is_valid is True
        assert result.schema_valid is True
        assert result.examples_valid is True
        assert mock_to_thread.call_count == 2  # Schema validation + examples

    @pytest.mark.asyncio
    @patch("specfact_cli.integrations.specmatic._get_specmatic_command")
    async def test_validate_specmatic_not_available(self, mock_get_cmd, tmp_path):
        """Test when Specmatic is not available."""
        mock_get_cmd.return_value = None

        spec_path = tmp_path / "openapi.yaml"
        spec_path.write_text("openapi: 3.0.0\n")

        result = await validate_spec_with_specmatic(spec_path)

        assert result.is_valid is False
        assert result.schema_valid is False
        assert result.examples_valid is False
        assert "Specmatic" in result.errors[0] and "not available" in result.errors[0]

    @pytest.mark.asyncio
    @patch("specfact_cli.integrations.specmatic._get_specmatic_command")
    @patch("specfact_cli.integrations.specmatic.asyncio.to_thread")
    async def test_validate_with_previous_version(self, mock_to_thread, mock_get_cmd, tmp_path):
        """Test validation with previous version for backward compatibility."""
        mock_get_cmd.return_value = ["specmatic"]
        # Mock successful subprocess runs
        mock_schema_result = MagicMock(returncode=0, stderr="")
        mock_examples_result = MagicMock(returncode=0, stderr="")
        mock_compat_result = MagicMock(returncode=0, stdout="", stderr="")
        mock_to_thread.side_effect = [mock_schema_result, mock_examples_result, mock_compat_result]

        spec_path = tmp_path / "openapi.yaml"
        spec_path.write_text("openapi: 3.0.0\n")
        previous_path = tmp_path / "openapi.v1.yaml"
        previous_path.write_text("openapi: 3.0.0\n")

        result = await validate_spec_with_specmatic(spec_path, previous_path)

        assert result.is_valid is True
        assert result.backward_compatible is True
        assert mock_to_thread.call_count == 3  # Schema validation + examples + backward compat check


class TestCheckBackwardCompatibility:
    """Test suite for check_backward_compatibility function."""

    @pytest.mark.asyncio
    @patch("specfact_cli.integrations.specmatic._get_specmatic_command")
    @patch("specfact_cli.integrations.specmatic.asyncio.to_thread")
    async def test_backward_compatible(self, mock_to_thread, mock_get_cmd, tmp_path):
        """Test when specs are backward compatible."""
        mock_get_cmd.return_value = ["specmatic"]
        # Mock successful backward compatibility check
        mock_compat_result = MagicMock(returncode=0, stdout="", stderr="")
        mock_to_thread.return_value = mock_compat_result

        old_spec = tmp_path / "old.yaml"
        old_spec.write_text("openapi: 3.0.0\n")
        new_spec = tmp_path / "new.yaml"
        new_spec.write_text("openapi: 3.0.0\n")

        is_compatible, breaking_changes = await check_backward_compatibility(old_spec, new_spec)

        assert is_compatible is True
        assert breaking_changes == []

    @pytest.mark.asyncio
    @patch("specfact_cli.integrations.specmatic._get_specmatic_command")
    @patch("specfact_cli.integrations.specmatic.asyncio.to_thread")
    async def test_backward_incompatible(self, mock_to_thread, mock_get_cmd, tmp_path):
        """Test when specs are not backward compatible."""
        mock_get_cmd.return_value = ["specmatic"]
        # Mock failed backward compatibility check with breaking changes in output
        mock_compat_result = MagicMock(
            returncode=1,
            stdout="Breaking change: Removed endpoint /api/v1/users",
            stderr="incompatible changes detected",
        )
        mock_to_thread.return_value = mock_compat_result

        old_spec = tmp_path / "old.yaml"
        old_spec.write_text("openapi: 3.0.0\n")
        new_spec = tmp_path / "new.yaml"
        new_spec.write_text("openapi: 3.0.0\n")

        is_compatible, breaking_changes = await check_backward_compatibility(old_spec, new_spec)

        assert is_compatible is False
        assert len(breaking_changes) > 0
        assert any("Removed endpoint" in change or "incompatible" in change.lower() for change in breaking_changes)


class TestGenerateSpecmaticTests:
    """Test suite for generate_specmatic_tests function."""

    @pytest.mark.asyncio
    @patch("specfact_cli.integrations.specmatic._get_specmatic_command")
    @patch("specfact_cli.integrations.specmatic.asyncio.to_thread")
    async def test_generate_tests_success(self, mock_to_thread, mock_get_cmd, tmp_path):
        """Test successful test generation."""
        mock_get_cmd.return_value = ["specmatic"]
        mock_result = MagicMock(returncode=0, stderr="")
        mock_to_thread.return_value = mock_result

        spec_path = tmp_path / "openapi.yaml"
        spec_path.write_text("openapi: 3.0.0\n")
        output_dir = tmp_path / "tests"

        output = await generate_specmatic_tests(spec_path, output_dir)

        assert output == output_dir
        mock_to_thread.assert_called_once()


class TestCreateMockServer:
    """Test suite for create_mock_server function."""

    @pytest.mark.asyncio
    @patch("specfact_cli.integrations.specmatic._get_specmatic_command")
    @patch("specfact_cli.integrations.specmatic.asyncio.to_thread")
    @patch("specfact_cli.integrations.specmatic.asyncio.sleep")
    async def test_create_mock_server(self, mock_sleep, mock_to_thread, mock_get_cmd, tmp_path):
        """Test mock server creation."""
        mock_get_cmd.return_value = ["specmatic"]
        # Mock a running process
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # Process is running
        mock_process.stderr = MagicMock()
        mock_process.stderr.read.return_value = ""
        mock_to_thread.return_value = mock_process
        mock_sleep.return_value = None

        spec_path = tmp_path / "openapi.yaml"
        spec_path.write_text("openapi: 3.0.0\n")

        mock_server = await create_mock_server(spec_path, port=9000, strict_mode=True)

        assert mock_server.port == 9000
        assert mock_server.spec_path == spec_path
        assert mock_server.process is not None
        mock_to_thread.assert_called_once()

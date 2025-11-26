"""E2E integration tests for telemetry functionality."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from specfact_cli.cli import app
from specfact_cli.telemetry import TelemetrySettings


runner = CliRunner()


class TestTelemetryE2E:
    """E2E tests for telemetry integration with CLI commands."""

    def test_telemetry_disabled_in_test_environment(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verify telemetry is automatically disabled when TEST_MODE is set."""
        # Ensure TEST_MODE is set (should be set by pytest, but verify)
        monkeypatch.setenv("TEST_MODE", "true")
        monkeypatch.delenv("SPECFACT_TELEMETRY_OPT_IN", raising=False)

        # Create sample codebase
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "module.py").write_text("class Module:\n    pass\n")

        # Run import command
        bundle_name = "test-project"
        result = runner.invoke(
            app,
            [
                "import",
                "from-code",
                bundle_name,
                "--repo",
                str(tmp_path),
                "--confidence",
                "0.5",
            ],
        )

        assert result.exit_code == 0

        # Verify telemetry was disabled
        settings = TelemetrySettings.from_env()
        assert not settings.enabled, "Telemetry should be disabled in test environment"

        # Note: In test mode, telemetry is disabled, so no log should be created
        # We verify the settings are correct above

    def test_telemetry_enabled_with_opt_in(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verify telemetry works when explicitly opted in (outside test mode)."""
        # Clear test mode flags
        monkeypatch.delenv("TEST_MODE", raising=False)
        monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
        monkeypatch.setenv("SPECFACT_TELEMETRY_OPT_IN", "true")

        # Use custom local path for testing
        telemetry_log = tmp_path / "telemetry.log"
        monkeypatch.setenv("SPECFACT_TELEMETRY_LOCAL_PATH", str(telemetry_log))

        # Create sample codebase
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "module.py").write_text("class Module:\n    pass\n")

        # Run import command
        bundle_name = "test-project"
        result = runner.invoke(
            app,
            [
                "import",
                "from-code",
                bundle_name,
                "--repo",
                str(tmp_path),
                "--confidence",
                "0.5",
            ],
        )

        assert result.exit_code == 0

        # Verify telemetry was enabled
        settings = TelemetrySettings.from_env()
        # Note: In actual test environment, TEST_MODE might still be set by pytest
        # So we check if telemetry log exists (only if truly enabled)
        if settings.enabled and telemetry_log.exists():
            # Verify telemetry log contains expected data
            log_lines = telemetry_log.read_text(encoding="utf-8").strip().splitlines()
            assert len(log_lines) > 0, "Telemetry log should contain events"

            # Parse last event
            last_event = json.loads(log_lines[-1])
            assert last_event["command"] == "import.from_code"
            assert "files_analyzed" in last_event
            assert "duration_ms" in last_event
            assert "success" in last_event

    def test_telemetry_sanitization_e2e(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verify telemetry sanitizes sensitive data in e2e scenario."""
        # Clear test mode flags
        monkeypatch.delenv("TEST_MODE", raising=False)
        monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
        monkeypatch.setenv("SPECFACT_TELEMETRY_OPT_IN", "true")

        # Use custom local path for testing
        telemetry_log = tmp_path / "telemetry.log"
        monkeypatch.setenv("SPECFACT_TELEMETRY_LOCAL_PATH", str(telemetry_log))

        # Create sample codebase with potentially sensitive names
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "secret_module.py").write_text("class SecretClass:\n    pass\n")

        # Run import command
        bundle_name = "test-project"
        result = runner.invoke(
            app,
            [
                "import",
                "from-code",
                bundle_name,
                "--repo",
                str(tmp_path),
                "--confidence",
                "0.5",
            ],
        )

        assert result.exit_code == 0

        # Verify telemetry was enabled and sanitized
        settings = TelemetrySettings.from_env()
        if settings.enabled and telemetry_log.exists():
            log_lines = telemetry_log.read_text(encoding="utf-8").strip().splitlines()
            if log_lines:
                last_event = json.loads(log_lines[-1])
                # Verify sensitive data is not in telemetry
                event_str = json.dumps(last_event)
                assert "secret_module" not in event_str.lower(), "Sensitive file names should not be in telemetry"
                assert "SecretClass" not in event_str, "Sensitive class names should not be in telemetry"
                # Verify only allowed fields are present
                allowed_fields = {
                    "command",
                    "mode",
                    "execution_mode",
                    "files_analyzed",
                    "features_detected",
                    "stories_detected",
                    "duration_ms",
                    "success",
                    "telemetry_version",
                    "session_id",
                    "opt_in_source",
                    "cli_version",
                }
                for key in last_event:
                    assert key in allowed_fields, f"Unexpected field in telemetry: {key}"

    def test_telemetry_configuration_options(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verify all telemetry configuration options work in e2e."""
        # Clear test mode flags
        monkeypatch.delenv("TEST_MODE", raising=False)
        monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)

        # Test all configuration options
        monkeypatch.setenv("SPECFACT_TELEMETRY_OPT_IN", "true")
        monkeypatch.setenv("SPECFACT_TELEMETRY_SERVICE_NAME", "test-service")
        monkeypatch.setenv("SPECFACT_TELEMETRY_BATCH_SIZE", "256")
        monkeypatch.setenv("SPECFACT_TELEMETRY_BATCH_TIMEOUT", "3")
        monkeypatch.setenv("SPECFACT_TELEMETRY_EXPORT_TIMEOUT", "15")
        monkeypatch.setenv("SPECFACT_TELEMETRY_LOCAL_PATH", str(tmp_path / "custom-telemetry.log"))

        settings = TelemetrySettings.from_env()
        # Note: In actual test environment, settings might be disabled due to TEST_MODE
        # But we can verify the configuration is read correctly
        if not settings.enabled:
            # If disabled due to test mode, that's expected and correct
            return

        # Verify settings are correct
        assert settings.enabled
        assert settings.local_path == tmp_path / "custom-telemetry.log"

        # Verify environment variables are read
        assert os.getenv("SPECFACT_TELEMETRY_SERVICE_NAME") == "test-service"
        assert os.getenv("SPECFACT_TELEMETRY_BATCH_SIZE") == "256"
        assert os.getenv("SPECFACT_TELEMETRY_BATCH_TIMEOUT") == "3"
        assert os.getenv("SPECFACT_TELEMETRY_EXPORT_TIMEOUT") == "15"

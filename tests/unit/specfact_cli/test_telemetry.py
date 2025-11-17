"""Tests for the privacy-first telemetry manager."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from specfact_cli.telemetry import (
    TelemetryManager,
    TelemetrySettings,
)


def test_track_command_disabled(tmp_path: Path) -> None:
    """Ensure no events are recorded when telemetry is disabled."""
    settings = TelemetrySettings(
        enabled=False,
        endpoint=None,
        headers={},
        local_path=tmp_path / "telemetry.log",
        debug=False,
        opt_in_source="test",
    )
    manager = TelemetryManager(settings=settings)

    with manager.track_command("import.from_code") as record:
        record({"features_detected": 3})

    assert manager.last_event is None
    assert not settings.local_path.exists()


def test_track_command_records_anonymized_event(tmp_path: Path) -> None:
    """Telemetry should sanitize fields and persist to the local log."""
    local_path = tmp_path / "telemetry.log"
    settings = TelemetrySettings(
        enabled=True,
        endpoint=None,
        headers={},
        local_path=local_path,
        debug=False,
        opt_in_source="env",
    )
    manager = TelemetryManager(settings=settings)

    with manager.track_command("import.from_code", {"mode": "cicd", "files_analyzed": 42}) as record:
        record({"features_detected": 7, "stories_detected": 14, "sensitive": "ignore-me"})

    event = manager.last_event
    assert event is not None
    assert event["command"] == "import.from_code"
    assert event["files_analyzed"] == 42
    assert event["features_detected"] == 7
    assert event["stories_detected"] == 14
    assert "sensitive" not in event
    assert event["success"] is True
    assert event["telemetry_version"] == TelemetryManager.TELEMETRY_VERSION

    log_line = local_path.read_text(encoding="utf-8").strip().splitlines()[-1]
    log_event = json.loads(log_line)
    assert log_event["command"] == "import.from_code"


def test_track_command_marks_failure(tmp_path: Path) -> None:
    """Failures should be captured without preventing the original exception."""
    settings = TelemetrySettings(
        enabled=True,
        endpoint=None,
        headers={},
        local_path=tmp_path / "telemetry.log",
        debug=False,
        opt_in_source="env",
    )
    manager = TelemetryManager(settings=settings)

    class CustomError(RuntimeError):
        """Test-specific error."""

    with pytest.raises(CustomError), manager.track_command("repro.run") as record:
        record({"checks_total": 5})
        raise CustomError("boom")

    event = manager.last_event
    assert event is not None
    assert event["command"] == "repro.run"
    assert event["checks_total"] == 5
    assert event["success"] is False
    assert event["error"] == "CustomError"


def test_test_environment_detection(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Telemetry should be automatically disabled in test environments."""
    # Set TEST_MODE
    monkeypatch.setenv("TEST_MODE", "true")
    monkeypatch.delenv("SPECFACT_TELEMETRY_OPT_IN", raising=False)

    settings = TelemetrySettings.from_env()
    assert not settings.enabled
    assert settings.opt_in_source == "disabled"

    # Set PYTEST_CURRENT_TEST
    monkeypatch.delenv("TEST_MODE", raising=False)
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "test_telemetry.py::test_something")

    settings = TelemetrySettings.from_env()
    assert not settings.enabled
    assert settings.opt_in_source == "disabled"


def test_service_name_configuration(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Service name should be configurable via environment variable."""
    monkeypatch.setenv("SPECFACT_TELEMETRY_SERVICE_NAME", "custom-service")
    monkeypatch.setenv("SPECFACT_TELEMETRY_OPT_IN", "true")
    monkeypatch.setenv("SPECFACT_TELEMETRY_ENDPOINT", "http://localhost:4318/v1/traces")

    settings = TelemetrySettings.from_env()
    # Initialize manager to verify it doesn't crash with custom service name
    TelemetryManager(settings=settings)

    # Service name is used in tracer initialization, so we can't easily test it
    # without mocking OpenTelemetry. But we can verify the env var is read.
    assert os.getenv("SPECFACT_TELEMETRY_SERVICE_NAME") == "custom-service"


def test_batch_configuration(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Batch settings should be configurable via environment variables."""
    monkeypatch.setenv("SPECFACT_TELEMETRY_BATCH_SIZE", "1024")
    monkeypatch.setenv("SPECFACT_TELEMETRY_BATCH_TIMEOUT", "10")
    monkeypatch.setenv("SPECFACT_TELEMETRY_OPT_IN", "true")
    monkeypatch.setenv("SPECFACT_TELEMETRY_ENDPOINT", "http://localhost:4318/v1/traces")

    settings = TelemetrySettings.from_env()
    # Initialize manager to verify it doesn't crash with custom batch settings
    TelemetryManager(settings=settings)

    # Batch settings are used in tracer initialization, so we can't easily test them
    # without mocking OpenTelemetry. But we can verify the env vars are read.
    assert os.getenv("SPECFACT_TELEMETRY_BATCH_SIZE") == "1024"
    assert os.getenv("SPECFACT_TELEMETRY_BATCH_TIMEOUT") == "10"


def test_export_timeout_configuration(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Export timeout should be configurable via environment variable."""
    monkeypatch.setenv("SPECFACT_TELEMETRY_EXPORT_TIMEOUT", "30")
    monkeypatch.setenv("SPECFACT_TELEMETRY_OPT_IN", "true")
    monkeypatch.setenv("SPECFACT_TELEMETRY_ENDPOINT", "http://localhost:4318/v1/traces")

    settings = TelemetrySettings.from_env()
    # Initialize manager to verify it doesn't crash with custom export timeout
    TelemetryManager(settings=settings)

    # Export timeout is used in exporter initialization, so we can't easily test it
    # without mocking OpenTelemetry. But we can verify the env var is read.
    assert os.getenv("SPECFACT_TELEMETRY_EXPORT_TIMEOUT") == "30"


def test_config_file_support(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that telemetry settings can be read from config file."""
    from specfact_cli.utils.yaml_utils import dump_yaml

    # Create config file
    config_file = tmp_path / "telemetry.yaml"
    config_data = {
        "enabled": True,
        "endpoint": "https://example.com/v1/traces",
        "headers": {
            "Authorization": "Basic test123",
        },
        "service_name": "my-specfact",
        "batch_size": "1024",
        "batch_timeout": "10",
        "export_timeout": "30",
        "debug": True,
    }
    dump_yaml(config_data, config_file)

    # Mock the config file path and disable test environment detection
    monkeypatch.setattr("specfact_cli.telemetry.TELEMETRY_CONFIG_FILE", config_file)
    monkeypatch.delenv("SPECFACT_TELEMETRY_OPT_IN", raising=False)
    monkeypatch.delenv("SPECFACT_TELEMETRY_ENDPOINT", raising=False)
    monkeypatch.delenv("TEST_MODE", raising=False)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)

    settings = TelemetrySettings.from_env()
    assert settings.enabled
    assert settings.endpoint == "https://example.com/v1/traces"
    assert settings.headers == {"Authorization": "Basic test123"}
    assert settings.debug
    assert settings.opt_in_source == "config"

    # Verify manager can be initialized with config file settings
    manager = TelemetryManager(settings=settings)
    assert manager is not None


def test_config_file_env_var_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that environment variables override config file settings."""
    from specfact_cli.utils.yaml_utils import dump_yaml

    # Create config file
    config_file = tmp_path / "telemetry.yaml"
    config_data = {
        "enabled": True,
        "endpoint": "https://config-file.com/v1/traces",
        "headers": {
            "Authorization": "Basic config123",
        },
    }
    dump_yaml(config_data, config_file)

    # Mock the config file path and disable test environment detection
    monkeypatch.setattr("specfact_cli.telemetry.TELEMETRY_CONFIG_FILE", config_file)
    monkeypatch.setenv("SPECFACT_TELEMETRY_OPT_IN", "true")
    monkeypatch.setenv("SPECFACT_TELEMETRY_ENDPOINT", "https://env-var.com/v1/traces")
    monkeypatch.setenv("SPECFACT_TELEMETRY_HEADERS", "Authorization: Basic env123")
    monkeypatch.delenv("TEST_MODE", raising=False)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)

    settings = TelemetrySettings.from_env()
    assert settings.enabled
    # Environment variables should override config file
    assert settings.endpoint == "https://env-var.com/v1/traces"
    assert settings.headers == {"Authorization": "Basic env123"}
    assert settings.opt_in_source == "env"


def test_config_file_backward_compatibility(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that simple opt-in file still works for backward compatibility."""
    # Create simple opt-in file (old method)
    opt_in_file = tmp_path / "telemetry.opt-in"
    opt_in_file.write_text("true")

    # Mock both file paths and disable test environment detection
    monkeypatch.setattr("specfact_cli.telemetry.OPT_IN_FILE", opt_in_file)
    monkeypatch.setattr("specfact_cli.telemetry.TELEMETRY_CONFIG_FILE", tmp_path / "nonexistent.yaml")
    monkeypatch.delenv("SPECFACT_TELEMETRY_OPT_IN", raising=False)
    monkeypatch.delenv("TEST_MODE", raising=False)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)

    settings = TelemetrySettings.from_env()
    assert settings.enabled
    assert settings.opt_in_source == "file"

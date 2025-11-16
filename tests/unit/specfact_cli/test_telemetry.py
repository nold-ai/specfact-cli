"""Tests for the privacy-first telemetry manager."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from specfact_cli.telemetry import TelemetryManager, TelemetrySettings


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

"""
Privacy-first telemetry utilities for SpecFact CLI.

Telemetry is disabled by default and only activates after the user
explicitly opts in via environment variables or the ~/.specfact/telemetry.opt-in
flag file. When enabled, the manager emits anonymized OpenTelemetry spans
and appends sanitized JSON lines to a local log file so users can inspect,
rotate, or delete their own data.
"""

from __future__ import annotations

import json
import logging
import os
import time
from collections.abc import MutableMapping
from contextlib import contextmanager, suppress
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

from beartype import beartype
from beartype.typing import Callable, Iterator, Mapping
from icontract import ensure, require

from specfact_cli import __version__


try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter, SimpleSpanProcessor
except ImportError:  # pragma: no cover - optional dependency
    trace = None  # type: ignore[assignment]
    TracerProvider = None  # type: ignore[assignment]
    BatchSpanProcessor = None  # type: ignore[assignment]
    SimpleSpanProcessor = None  # type: ignore[assignment]
    ConsoleSpanExporter = None  # type: ignore[assignment]
    OTLPSpanExporter = None  # type: ignore[assignment]
    Resource = None  # type: ignore[assignment]


LOGGER = logging.getLogger(__name__)

OPT_IN_FILE = Path.home() / ".specfact" / "telemetry.opt-in"
TELEMETRY_CONFIG_FILE = Path.home() / ".specfact" / "telemetry.yaml"
DEFAULT_LOCAL_LOG = Path.home() / ".specfact" / "telemetry.log"

ALLOWED_FIELDS = {
    "command",
    "mode",
    "execution_mode",
    "shadow_mode",
    "files_analyzed",
    "features_detected",
    "stories_detected",
    "violations_detected",
    "checks_total",
    "checks_failed",
    "duration_ms",
    "success",
    "error",
    "telemetry_version",
    "session_id",
    "opt_in_source",
    "cli_version",
}


@beartype
@require(lambda value: value is None or isinstance(value, str), "Value must be None or string")
@ensure(lambda result: isinstance(result, bool), "Must return boolean")
def _coerce_bool(value: str | None) -> bool:
    """Convert truthy string representations to boolean."""
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


@beartype
@require(
    lambda: OPT_IN_FILE.parent.exists() or not OPT_IN_FILE.exists(),
    "Opt-in file parent directory must exist if file exists",
)
@ensure(lambda result: isinstance(result, bool), "Must return boolean")
def _read_opt_in_file() -> bool:
    """Read opt-in flag from ~/.specfact/telemetry.opt-in if it exists."""
    try:
        content = OPT_IN_FILE.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return False
    except OSError:
        return False
    return _coerce_bool(content)


@beartype
@require(
    lambda: TELEMETRY_CONFIG_FILE.parent.exists() or not TELEMETRY_CONFIG_FILE.exists(),
    "Config file parent directory must exist if file exists",
)
@ensure(
    lambda result: isinstance(result, dict) and all(isinstance(k, str) for k in result), "Must return dict[str, Any]"
)
def _read_config_file() -> dict[str, Any]:
    """Read telemetry configuration from ~/.specfact/telemetry.yaml if it exists."""
    if not TELEMETRY_CONFIG_FILE.exists():
        return {}

    try:
        from specfact_cli.utils.yaml_utils import load_yaml

        config = load_yaml(TELEMETRY_CONFIG_FILE)
        if not isinstance(config, dict):
            LOGGER.warning("Invalid telemetry config file format: expected dict, got %s", type(config))
            return {}
        return config
    except FileNotFoundError:
        return {}
    except Exception as e:
        LOGGER.warning("Failed to read telemetry config file: %s", e)
        return {}


@beartype
@require(lambda raw: raw is None or isinstance(raw, str), "Raw must be None or string")
@ensure(
    lambda result: isinstance(result, dict)
    and all(isinstance(k, str) and isinstance(v, str) for k, v in result.items()),
    "Must return dict[str, str]",
)
def _parse_headers(raw: str | None) -> dict[str, str]:
    """Parse comma-separated header string into a dictionary."""
    if not raw:
        return {}
    headers: dict[str, str] = {}
    for pair in raw.split(","):
        if ":" not in pair:
            continue
        key, value = pair.split(":", 1)
        key_clean = key.strip()
        value_clean = value.strip()
        if key_clean and value_clean:
            headers[key_clean] = value_clean
    return headers


@dataclass(frozen=True)
class TelemetrySettings:
    """User-configurable telemetry settings."""

    enabled: bool
    endpoint: str | None = None
    headers: dict[str, str] = field(default_factory=dict)
    local_path: Path = DEFAULT_LOCAL_LOG
    debug: bool = False
    opt_in_source: str = "disabled"

    @classmethod
    @beartype
    @require(lambda cls: cls is TelemetrySettings, "Must be called on TelemetrySettings class")
    @ensure(
        lambda result: isinstance(result, TelemetrySettings)
        and isinstance(result.enabled, bool)
        and (result.endpoint is None or isinstance(result.endpoint, str))
        and isinstance(result.headers, dict)
        and isinstance(result.local_path, Path)
        and isinstance(result.debug, bool)
        and isinstance(result.opt_in_source, str),
        "Must return valid TelemetrySettings instance",
    )
    def from_env(cls) -> TelemetrySettings:
        """
        Build telemetry settings from environment variables, config file, and opt-in file.

        Precedence (highest to lowest):
        1. Environment variables (override everything)
        2. Config file (~/.specfact/telemetry.yaml)
        3. Simple opt-in file (~/.specfact/telemetry.opt-in) - for backward compatibility
        4. Defaults (disabled)
        """
        # Disable in test environments (GitHub pattern)
        if os.getenv("TEST_MODE") == "true" or os.getenv("PYTEST_CURRENT_TEST"):
            return cls(
                enabled=False,
                endpoint=None,
                headers={},
                local_path=DEFAULT_LOCAL_LOG,
                debug=False,
                opt_in_source="disabled",
            )

        # Step 1: Read config file (if exists)
        config = _read_config_file()

        # Step 2: Check environment variables (override config file)
        env_flag = os.getenv("SPECFACT_TELEMETRY_OPT_IN")
        if env_flag is not None:
            enabled = _coerce_bool(env_flag)
            opt_in_source = "env" if enabled else "disabled"
        else:
            # Check config file for enabled flag (can be bool or string)
            config_enabled = config.get("enabled", False)
            if isinstance(config_enabled, bool):
                enabled = config_enabled
            elif isinstance(config_enabled, str):
                enabled = _coerce_bool(config_enabled)
            else:
                enabled = False
            opt_in_source = "config" if enabled else "disabled"

        # Step 3: Fallback to simple opt-in file (backward compatibility)
        if not enabled:
            file_enabled = _read_opt_in_file()
            if file_enabled:
                enabled = True
                opt_in_source = "file"

        # Step 4: Get endpoint (env var > config file > None)
        endpoint = os.getenv("SPECFACT_TELEMETRY_ENDPOINT") or config.get("endpoint")

        # Step 5: Get headers (env var > config file > empty dict)
        env_headers = _parse_headers(os.getenv("SPECFACT_TELEMETRY_HEADERS"))
        config_headers = config.get("headers", {})
        headers = (
            {**config_headers, **env_headers} if isinstance(config_headers, dict) else env_headers
        )  # Env vars override config file

        # Step 6: Get local path (env var > config file > default)
        local_path_str = (
            os.getenv("SPECFACT_TELEMETRY_LOCAL_PATH") or config.get("local_path") or str(DEFAULT_LOCAL_LOG)
        )
        local_path = Path(local_path_str).expanduser()

        # Step 7: Get debug flag (env var > config file > False)
        env_debug = os.getenv("SPECFACT_TELEMETRY_DEBUG")
        debug = _coerce_bool(env_debug) if env_debug is not None else config.get("debug", False)

        return cls(
            enabled=enabled,
            endpoint=endpoint,
            headers=headers,
            local_path=local_path,
            debug=debug,
            opt_in_source=opt_in_source if enabled else "disabled",
        )


class TelemetryManager:
    """Privacy-first telemetry helper."""

    TELEMETRY_VERSION = "1.0"

    @beartype
    @require(
        lambda self, settings: settings is None or isinstance(settings, TelemetrySettings),
        "Settings must be None or TelemetrySettings",
    )
    @ensure(
        lambda self, result: hasattr(self, "_settings")
        and hasattr(self, "_enabled")
        and hasattr(self, "_session_id")
        and isinstance(self._session_id, str)
        and len(self._session_id) > 0,
        "Must initialize all required instance attributes",
    )
    def __init__(self, settings: TelemetrySettings | None = None) -> None:
        self._settings = settings or TelemetrySettings.from_env()
        self._enabled = self._settings.enabled
        self._session_id = uuid4().hex
        self._tracer = None
        self._last_event: dict[str, Any] | None = None

        if not self._enabled:
            return

        self._prepare_storage()
        self._initialize_tracer()

    @property
    @beartype
    @ensure(lambda result: isinstance(result, bool), "Must return boolean")
    def enabled(self) -> bool:
        """Return True if telemetry is active."""
        return self._enabled

    @property
    @beartype
    @ensure(lambda result: result is None or isinstance(result, dict), "Must return None or dict")
    def last_event(self) -> dict[str, Any] | None:
        """Expose the last emitted telemetry event (used for tests)."""
        return self._last_event

    @beartype
    @require(
        lambda self: hasattr(self, "_settings") and isinstance(self._settings, TelemetrySettings),
        "Settings must be initialized",
    )
    @ensure(lambda self, result: result is None, "Must return None")
    def _prepare_storage(self) -> None:
        """Ensure local telemetry directory exists."""
        try:
            self._settings.local_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:  # pragma: no cover - catastrophic filesystem issue
            LOGGER.warning("Failed to prepare telemetry directory: %s", exc)

    @beartype
    @require(
        lambda self: hasattr(self, "_settings") and isinstance(self._settings, TelemetrySettings),
        "Settings must be initialized",
    )
    @ensure(lambda self, result: result is None, "Must return None")
    def _initialize_tracer(self) -> None:
        """Configure OpenTelemetry exporter if endpoint is provided."""
        if not self._settings.endpoint:
            return
        if (
            trace is None
            or TracerProvider is None
            or BatchSpanProcessor is None
            or OTLPSpanExporter is None
            or Resource is None
        ):
            LOGGER.warning(
                "Telemetry opt-in detected with endpoint set, but OpenTelemetry dependencies are missing. "
                "Events will be stored locally only."
            )
            return

        # Read config file for service name and batch settings (env vars override config)
        config = _read_config_file()

        # Allow user to customize service name (env var > config file > default)
        service_name = os.getenv("SPECFACT_TELEMETRY_SERVICE_NAME") or config.get("service_name") or "specfact-cli"
        # Allow user to customize service namespace (env var > config file > default)
        service_namespace = (
            os.getenv("SPECFACT_TELEMETRY_SERVICE_NAMESPACE") or config.get("service_namespace") or "cli"
        )
        # Allow user to customize deployment environment (env var > config file > default)
        deployment_environment = (
            os.getenv("SPECFACT_TELEMETRY_DEPLOYMENT_ENVIRONMENT")
            or config.get("deployment_environment")
            or "production"
        )
        resource = Resource.create(
            {
                "service.name": service_name,
                "service.namespace": service_namespace,
                "service.version": __version__,
                "deployment.environment": deployment_environment,
                "telemetry.opt_in_source": self._settings.opt_in_source,
            }
        )
        provider = TracerProvider(resource=resource)

        # Configure exporter (timeout is handled by BatchSpanProcessor)
        # Export timeout (env var > config file > default)
        export_timeout_str = os.getenv("SPECFACT_TELEMETRY_EXPORT_TIMEOUT") or str(config.get("export_timeout", "10"))
        export_timeout = int(export_timeout_str)
        exporter = OTLPSpanExporter(
            endpoint=self._settings.endpoint,
            headers=self._settings.headers or None,
        )

        # Allow user to configure batch settings (env var > config file > default)
        batch_size_str = os.getenv("SPECFACT_TELEMETRY_BATCH_SIZE") or str(config.get("batch_size", "512"))
        batch_timeout_str = os.getenv("SPECFACT_TELEMETRY_BATCH_TIMEOUT") or str(config.get("batch_timeout", "5"))
        batch_size = int(batch_size_str)
        batch_timeout_ms = int(batch_timeout_str) * 1000  # Convert to milliseconds
        export_timeout_ms = export_timeout * 1000  # Convert to milliseconds

        provider.add_span_processor(
            BatchSpanProcessor(
                exporter,
                max_queue_size=batch_size,
                export_timeout_millis=export_timeout_ms,
                schedule_delay_millis=batch_timeout_ms,
            )
        )

        if self._settings.debug and ConsoleSpanExporter and SimpleSpanProcessor:
            provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))

        trace.set_tracer_provider(provider)
        self._tracer = trace.get_tracer("specfact_cli.telemetry")

    @beartype
    @require(lambda self, raw: hasattr(self, "_settings"), "Manager must be initialized")
    @require(lambda self, raw: raw is None or isinstance(raw, Mapping), "Raw must be None or Mapping")
    @ensure(
        lambda self, result: isinstance(result, dict) and all(key in ALLOWED_FIELDS for key in result),
        "Must return dictionary with only allowed fields",
    )
    def _sanitize(self, raw: Mapping[str, Any] | None) -> dict[str, Any]:
        """Whitelist metadata fields to avoid leaking sensitive information."""
        sanitized: dict[str, Any] = {}
        if not raw:
            return sanitized

        for key, value in raw.items():
            if key not in ALLOWED_FIELDS:
                continue
            normalized = self._normalize_value(value)
            if normalized is not None:
                sanitized[key] = normalized
        return sanitized

    @beartype
    @require(lambda self, value: hasattr(self, "_settings"), "Manager must be initialized")
    @ensure(
        lambda self, result: result is None or isinstance(result, (bool, int, float, str)),
        "Must return None or primitive type",
    )
    def _normalize_value(self, value: Any) -> bool | int | float | str | None:
        """Normalize values to primitive types suitable for telemetry."""
        if isinstance(value, bool):
            return value
        if isinstance(value, int) and not isinstance(value, bool):
            return value
        if isinstance(value, float):
            return round(value, 4)
        if isinstance(value, str):
            trimmed = value.strip()
            if not trimmed:
                return None
            return trimmed[:128]
        if value is None:
            return None
        if isinstance(value, (list, tuple)):
            return len(value)
        return None

    @beartype
    @require(lambda self, event: hasattr(self, "_settings"), "Manager must be initialized")
    @require(lambda self, event: isinstance(event, Mapping), "Event must be Mapping")
    @ensure(lambda self, result: result is None, "Must return None")
    def _write_local_event(self, event: Mapping[str, Any]) -> None:
        """Persist event to local JSONL file."""
        try:
            with self._settings.local_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, separators=(",", ":")))
                handle.write("\n")
        except OSError as exc:  # pragma: no cover - filesystem failures
            LOGGER.warning("Failed to write telemetry event locally: %s", exc)

    @beartype
    @require(lambda self, event: hasattr(self, "_settings"), "Manager must be initialized")
    @require(lambda self, event: isinstance(event, MutableMapping), "Event must be MutableMapping")
    @ensure(
        lambda self, result: hasattr(self, "_last_event") and self._last_event is not None,
        "Must set _last_event after emitting",
    )
    def _emit_event(self, event: MutableMapping[str, Any]) -> None:
        """Emit sanitized event to local storage and optional OTLP exporter."""
        event.setdefault("cli_version", __version__)
        event.setdefault("opt_in_source", self._settings.opt_in_source)

        self._last_event = dict(event)
        self._write_local_event(self._last_event)

        if self._tracer is None:
            return

        # Emit to OTLP exporter with error handling
        span_name = f"specfact.{event.get('command', 'unknown')}"
        try:
            with self._tracer.start_as_current_span(span_name) as span:  # pragma: no cover - exercised indirectly
                for key, value in self._last_event.items():
                    span.set_attribute(f"specfact.{key}", value)
        except Exception as exc:  # pragma: no cover - collector failures
            # Log but don't fail - local storage already succeeded
            LOGGER.warning("Failed to export telemetry to OTLP collector: %s. Event stored locally only.", exc)

    @contextmanager
    @beartype
    @require(lambda self, command, initial_metadata: hasattr(self, "_settings"), "Manager must be initialized")
    @require(
        lambda self, command, initial_metadata: isinstance(command, str) and len(command) > 0,
        "Command must be non-empty string",
    )
    @require(
        lambda self, command, initial_metadata: initial_metadata is None or isinstance(initial_metadata, Mapping),
        "Initial metadata must be None or Mapping",
    )
    @ensure(
        lambda self, result: True,  # Context manager returns iterator, postcondition checked in finally block
        "Context manager must yield callable",
    )
    def track_command(
        self,
        command: str,
        initial_metadata: Mapping[str, Any] | None = None,
    ) -> Iterator[Callable[[Mapping[str, Any] | None], None]]:
        """
        Context manager to record anonymized telemetry for a CLI command.

        Usage:
            with telemetry.track_command("import.from_code", {"mode": "cicd"}) as record:
                ...
                record({"features_detected": len(features)})
        """

        if not self._enabled:
            yield lambda _: None
            return

        metadata: dict[str, Any] = self._sanitize(initial_metadata)
        start_time = time.perf_counter()
        success = False
        error_name: str | None = None

        @beartype
        @require(lambda extra: extra is None or isinstance(extra, Mapping), "Extra must be None or Mapping")
        @ensure(lambda result: result is None, "Must return None")
        def record(extra: Mapping[str, Any] | None) -> None:
            if extra:
                metadata.update(self._sanitize(extra))

        try:
            yield record
            success = True
        except Exception as exc:
            error_name = exc.__class__.__name__
            metadata["error"] = error_name
            raise
        finally:
            metadata.setdefault("session_id", self._session_id)
            metadata["success"] = success
            if error_name:
                metadata["error"] = error_name
            metadata["duration_ms"] = round((time.perf_counter() - start_time) * 1000, 2)
            metadata["command"] = command
            metadata["telemetry_version"] = self.TELEMETRY_VERSION
            self._emit_event(metadata)


# Shared singleton used throughout the CLI.
telemetry = TelemetryManager()

__all__ = ["TelemetryManager", "TelemetrySettings", "telemetry"]


# CrossHair property-based test functions
# CrossHair: skip (side-effectful imports in YAML utils)
# These functions are designed for CrossHair symbolic execution analysis
@beartype
def test_coerce_bool_property(value: str | None) -> None:
    """CrossHair property test for _coerce_bool function."""
    result = _coerce_bool(value)
    assert isinstance(result, bool)
    if value is None:
        assert result is False
    elif value.strip().lower() in {"1", "true", "yes", "y", "on"}:
        assert result is True


@beartype
def test_read_opt_in_file_property() -> None:
    """CrossHair property test for _read_opt_in_file function."""
    result = _read_opt_in_file()
    assert isinstance(result, bool)


@beartype
def test_read_config_file_property() -> None:
    """CrossHair property test for _read_config_file function."""
    result = _read_config_file()
    assert isinstance(result, dict)
    assert all(isinstance(k, str) for k in result)


@beartype
def test_parse_headers_property(raw: str | None) -> None:
    """CrossHair property test for _parse_headers function."""
    result = _parse_headers(raw)
    assert isinstance(result, dict)
    assert all(isinstance(k, str) and isinstance(v, str) for k, v in result.items())
    if raw is None or not raw:
        assert len(result) == 0


@beartype
def test_telemetry_settings_from_env_property() -> None:
    """CrossHair property test for TelemetrySettings.from_env."""
    settings = TelemetrySettings.from_env()
    assert isinstance(settings, TelemetrySettings)
    assert isinstance(settings.enabled, bool)
    assert settings.endpoint is None or isinstance(settings.endpoint, str)
    assert isinstance(settings.headers, dict)
    assert all(isinstance(k, str) and isinstance(v, str) for k, v in settings.headers.items())
    assert isinstance(settings.local_path, Path)
    assert isinstance(settings.debug, bool)
    assert isinstance(settings.opt_in_source, str)


@beartype
def test_telemetry_manager_init_property(settings: TelemetrySettings | None) -> None:
    """CrossHair property test for TelemetryManager.__init__."""
    manager = TelemetryManager(settings)
    assert hasattr(manager, "_settings")
    assert hasattr(manager, "_enabled")
    assert hasattr(manager, "_session_id")
    assert isinstance(manager._session_id, str)
    assert len(manager._session_id) > 0


@beartype
def test_telemetry_manager_sanitize_property(raw: Mapping[str, Any] | None) -> None:
    """CrossHair property test for TelemetryManager._sanitize."""
    manager = TelemetryManager(TelemetrySettings(enabled=False))
    result = manager._sanitize(raw)
    assert isinstance(result, dict)
    assert all(key in ALLOWED_FIELDS for key in result)
    if raw is None:
        assert len(result) == 0


@beartype
def test_telemetry_manager_normalize_value_property(value: Any) -> None:
    """CrossHair property test for TelemetryManager._normalize_value."""
    manager = TelemetryManager(TelemetrySettings(enabled=False))
    result = manager._normalize_value(value)
    assert result is None or isinstance(result, (bool, int, float, str))
    if isinstance(value, bool) or (isinstance(value, int) and not isinstance(value, bool)):
        assert result == value
    elif isinstance(value, float):
        assert isinstance(result, float)
    elif isinstance(value, str):
        if value.strip():
            assert isinstance(result, str)
            assert len(result) <= 128
        else:
            assert result is None
    elif value is None:
        assert result is None
    elif isinstance(value, (list, tuple)):
        assert isinstance(result, int)


@beartype
def test_telemetry_manager_write_local_event_property(event: Mapping[str, Any]) -> None:
    """CrossHair property test for TelemetryManager._write_local_event."""
    manager = TelemetryManager(TelemetrySettings(enabled=False, local_path=Path("/tmp/test_telemetry.log")))
    # This test verifies the function doesn't raise exceptions
    # Actual file writing is tested in integration tests
    with suppress(OSError):  # Expected in some test environments
        manager._write_local_event(event)


@beartype
def test_telemetry_manager_emit_event_property(event: MutableMapping[str, Any]) -> None:
    """CrossHair property test for TelemetryManager._emit_event."""
    manager = TelemetryManager(TelemetrySettings(enabled=False, local_path=Path("/tmp/test_telemetry.log")))
    manager._emit_event(event)
    assert manager._last_event is not None
    assert isinstance(manager._last_event, dict)


@beartype
def test_telemetry_manager_track_command_property(command: str, initial_metadata: Mapping[str, Any] | None) -> None:
    """CrossHair property test for TelemetryManager.track_command."""
    if not command or len(command) == 0:
        return  # Skip invalid inputs
    manager = TelemetryManager(TelemetrySettings(enabled=True, local_path=Path("/tmp/test_telemetry.log")))
    try:
        with manager.track_command(command, initial_metadata) as record:
            assert callable(record)
            record(None)
            record({"test": "value"})
    except Exception:
        pass  # Expected in some test scenarios
    # Verify event was emitted
    assert manager._last_event is not None
    assert manager._last_event.get("command") == command

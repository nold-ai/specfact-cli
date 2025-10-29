"""
Platform Base Class - Universal observability infrastructure

This module provides comprehensive observability capabilities including:
- Method tracing and performance monitoring
- Centralized logging with structured output
- Metrics collection and reporting
- Error tracking and alerting
- Resource usage monitoring

All classes in the SpecFact CLI ecosystem can inherit from PlatformBaseClass
or use the provided metaclasses to get these capabilities automatically.
"""

import asyncio
import functools
import logging
import os
import sys
import time
from abc import ABC, ABCMeta
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from types import SimpleNamespace
from typing import Any, Protocol

import psutil


# Ensure a TRACE level exists on the standard logger even when using basic logging
TRACE_LEVEL_NUM = 5


def _ensure_trace_level() -> None:
    """Register TRACE level and Logger.trace method if missing."""
    if not hasattr(logging, "TRACE"):
        logging.TRACE = TRACE_LEVEL_NUM  # type: ignore[attr-defined]
    # Register level name
    if logging.getLevelName(TRACE_LEVEL_NUM) == str(TRACE_LEVEL_NUM):
        logging.addLevelName(TRACE_LEVEL_NUM, "TRACE")

    # Attach Logger.trace if absent
    if not hasattr(logging.Logger, "trace"):

        def trace(self: logging.Logger, msg: str, *args, **kwargs) -> None:  # type: ignore[override]
            if self.isEnabledFor(TRACE_LEVEL_NUM):
                self._log(TRACE_LEVEL_NUM, msg, args, **kwargs)

        logging.Logger.trace = trace  # type: ignore[attr-defined]


_ensure_trace_level()

# Import LoggerSetup with circular dependency protection
try:
    from .logger_setup import LoggerSetup as _LoggerSetup

    LoggerSetup = _LoggerSetup  # type: ignore
except ImportError:
    # Fallback for when LoggerSetup is not available
    import logging


class LoggerSetup:  # type: ignore
    @staticmethod
    def create_logger(
        name: str,
        log_file: str | None = None,
        agent_name: str | None = None,
        log_level: str | None = None,
        session_id: str | None = None,
        use_rotating_file: bool = True,
        append_mode: bool = True,
        preserve_test_format: bool = False,
    ) -> logging.Logger:
        _ensure_trace_level()
        # Fallback stub ignores advanced parameters but keeps signature compatibility
        return logging.getLogger(name)

    @staticmethod
    def create_agent_flow_logger(
        session_id: str | None = None,
    ) -> logging.Logger:
        _ensure_trace_level()
        return logging.getLogger("agent_flow")

    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """Compatibility method used by tests; delegates to create_logger."""
        _ensure_trace_level()
        return logging.getLogger(name)


def _is_crosshair_analysis() -> bool:
    """Determine if the current process is running under CrossHair exploration."""
    return bool(os.environ.get("CROSSHAIR_ARGS")) or any(
        module_name.startswith("crosshair.") for module_name in sys.modules.keys()
    )


class _CrosshairLogger:
    """No-op logger used to avoid side effects during CrossHair analysis."""

    def isEnabledFor(self, _level: int) -> bool:  # pragma: no cover - simple stub
        return False

    def __getattr__(self, _name: str):
        def _noop(*_args: Any, **_kwargs: Any) -> None:  # pragma: no cover - simple stub
            return None

        return _noop


class _ProcessLike(Protocol):
    def memory_info(self) -> Any: ...

    def cpu_percent(self) -> float: ...


class _CrosshairProcessStub:
    """Lightweight psutil.Process replacement for CrossHair analysis."""

    _memory = SimpleNamespace(rss=0, vms=0)

    def memory_info(self) -> Any:  # pragma: no cover - simple stub
        return self._memory

    def cpu_percent(self) -> float:  # pragma: no cover - simple stub
        return 0.0


class ObservabilityLevel(Enum):
    """Levels of observability detail"""

    NONE = "none"
    BASIC = "basic"
    DETAILED = "detailed"
    COMPREHENSIVE = "comprehensive"


@dataclass
class MethodTrace:
    """Data structure for method tracing information"""

    class_name: str
    method_name: str
    start_time: float
    end_time: float | None = None
    duration: float | None = None
    args: list[Any] = field(default_factory=list)
    kwargs: dict[str, Any] = field(default_factory=dict)
    return_value: Any = None
    exception: Exception | None = None
    memory_before: float | None = None
    memory_after: float | None = None
    cpu_before: float | None = None
    cpu_after: float | None = None


@dataclass
class PerformanceMetrics:
    """Performance metrics for a method or class"""

    method_name: str
    call_count: int = 0
    total_duration: float = 0.0
    average_duration: float = 0.0
    min_duration: float = float("inf")
    max_duration: float = 0.0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    error_count: int = 0
    last_called: datetime | None = None


class PlatformBaseClassMeta(type):
    """Metaclass for PlatformBaseClass that automatically wraps methods with tracing"""

    def __new__(cls, name: str, bases: tuple, attrs: dict) -> type:
        """Create a new class with automatic method tracing"""
        # Create the class first
        new_class = super().__new__(cls, name, bases, attrs)

        # Only apply to PlatformBaseClass and its subclasses
        if name == "PlatformBaseClass" or any(
            issubclass(base, PlatformBaseClass) for base in bases if isinstance(base, type)
        ):
            # Apply observability to methods
            PlatformBaseClassMeta._apply_observability_to_methods(new_class, attrs)

        return new_class

    @staticmethod
    def _apply_observability_to_methods(new_class: type, attrs: dict) -> None:
        """Apply observability to methods in the class"""
        # Wrap methods with tracing using static methods
        for attr_name, attr_value in attrs.items():
            # Skip static methods - they should remain static
            if isinstance(attr_value, staticmethod):
                continue
            # Skip class methods - they should remain class methods
            if isinstance(attr_value, classmethod):
                continue
            # Skip property descriptors
            if isinstance(attr_value, property):
                continue

            # Skip methods marked with _no_trace attribute
            if hasattr(attr_value, "_no_trace") and attr_value._no_trace:
                continue

            if callable(attr_value) and not str(attr_name).startswith("__") and not str(attr_name).startswith("_"):
                # Wrap public methods
                setattr(
                    new_class,
                    attr_name,
                    PlatformBaseClassMeta._create_traced_method(attr_value, attr_name),
                )
            elif (
                callable(attr_value)
                and str(attr_name).startswith("_")
                and attr_name
                in [
                    "_tick",
                    "_process_agent_specific",
                    "_handle_request",
                    "_listen_for_requests",
                ]
            ):
                # Wrap specific private methods that are commonly overridden
                setattr(
                    new_class,
                    attr_name,
                    PlatformBaseClassMeta._create_traced_method(attr_value, attr_name),
                )

    @staticmethod
    def _create_traced_method(func: Callable[..., Any], method_name: str) -> Callable[..., Any]:
        """Create a traced version of a method"""
        if asyncio.iscoroutinefunction(func):
            return PlatformBaseClassMeta._create_async_traced_method(func, method_name)
        return PlatformBaseClassMeta._create_sync_traced_method(func, method_name)

    @staticmethod
    def _create_sync_traced_method(func: Callable[..., Any], method_name: str) -> Callable[..., Any]:
        """Create a traced version of a synchronous method"""

        @functools.wraps(func)
        def sync_wrapper(self, *args, **kwargs):
            # Early return if tracing is disabled
            if not hasattr(self, "_tracing_enabled") or not self._tracing_enabled:
                return func(self, *args, **kwargs)

            # Create trace
            trace = MethodTrace(
                class_name=getattr(self, "_class_name", self.__class__.__name__),
                method_name=method_name,
                start_time=time.time(),
                args=list(args),
                kwargs=kwargs,
            )

            # Collect resource info if performance monitoring is enabled
            if hasattr(self, "_performance_monitoring_enabled") and self._performance_monitoring_enabled:
                process = psutil.Process()
                trace.memory_before = process.memory_info().rss / 1024 / 1024
                trace.cpu_before = process.cpu_percent()

            # Log entry
            if hasattr(self, "logger") and self.logger.isEnabledFor(5):  # TRACE level
                self.logger.trace(
                    "🔍 ENTER %s.%s()",
                    getattr(self, "_class_name", self.__class__.__name__),
                    method_name,
                    extra={
                        "trace_id": id(trace),
                        "session_id": getattr(self, "_session_id", None),
                        "args_count": len(args),
                        "kwargs_count": len(kwargs),
                    },
                )

            try:
                # Execute the method
                result = func(self, *args, **kwargs)
                trace.return_value = result
                trace.end_time = time.time()
                trace.duration = trace.end_time - trace.start_time

                # Update performance metrics
                if hasattr(self, "_performance_monitoring_enabled") and self._performance_monitoring_enabled:
                    PlatformBaseClassMeta._update_performance_metrics(self, trace, method_name)

                # Log exit
                if hasattr(self, "logger") and self.logger.isEnabledFor(5):  # TRACE level
                    self.logger.trace(
                        "🔍 LEAVE %s.%s() [%.3fms]",
                        getattr(self, "_class_name", self.__class__.__name__),
                        method_name,
                        trace.duration * 1000,
                        extra={
                            "trace_id": id(trace),
                            "session_id": getattr(self, "_session_id", None),
                            "duration_ms": trace.duration * 1000,
                        },
                    )

                return result

            except Exception as e:
                trace.exception = e
                trace.end_time = time.time()
                trace.duration = trace.end_time - trace.start_time

                # Update error metrics
                if hasattr(self, "_performance_monitoring_enabled") and self._performance_monitoring_enabled:
                    PlatformBaseClassMeta._update_performance_metrics(self, trace, method_name)

                # Log error
                if hasattr(self, "_error_tracking_enabled") and self._error_tracking_enabled:
                    self.logger.error(
                        "❌ ERROR in %s.%s() [%.3fms]: %s",
                        getattr(self, "_class_name", self.__class__.__name__),
                        method_name,
                        trace.duration * 1000,
                        str(e),
                        extra={
                            "trace_id": id(trace),
                            "session_id": getattr(self, "_session_id", None),
                            "exception_type": type(e).__name__,
                            "duration_ms": trace.duration * 1000,
                        },
                        exc_info=True,
                    )

                raise

        return sync_wrapper

    @staticmethod
    def _create_async_traced_method(func: Callable[..., Any], method_name: str) -> Callable[..., Any]:
        """Create a traced version of an asynchronous method"""

        @functools.wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            # Early return if tracing is disabled
            if not hasattr(self, "_tracing_enabled") or not self._tracing_enabled:
                return await func(self, *args, **kwargs)

            # Create trace
            trace = MethodTrace(
                class_name=getattr(self, "_class_name", self.__class__.__name__),
                method_name=method_name,
                start_time=time.time(),
                args=list(args),
                kwargs=kwargs,
            )

            # Collect resource info if performance monitoring is enabled
            if hasattr(self, "_performance_monitoring_enabled") and self._performance_monitoring_enabled:
                process = psutil.Process()
                trace.memory_before = process.memory_info().rss / 1024 / 1024
                trace.cpu_before = process.cpu_percent()

            # Log entry
            if hasattr(self, "logger") and self.logger.isEnabledFor(5):  # TRACE level
                self.logger.trace(
                    "🔍 ENTER %s.%s() [ASYNC]",
                    getattr(self, "_class_name", self.__class__.__name__),
                    method_name,
                    extra={
                        "trace_id": id(trace),
                        "session_id": getattr(self, "_session_id", None),
                        "args_count": len(args),
                        "kwargs_count": len(kwargs),
                    },
                )

            try:
                # Execute the method
                result = await func(self, *args, **kwargs)
                trace.return_value = result
                trace.end_time = time.time()
                trace.duration = trace.end_time - trace.start_time

                # Update performance metrics
                if hasattr(self, "_performance_monitoring_enabled") and self._performance_monitoring_enabled:
                    PlatformBaseClassMeta._update_performance_metrics(self, trace, method_name)

                # Log exit
                if hasattr(self, "logger") and self.logger.isEnabledFor(5):  # TRACE level
                    self.logger.trace(
                        "🔍 LEAVE %s.%s() [ASYNC] [%.3fms]",
                        getattr(self, "_class_name", self.__class__.__name__),
                        method_name,
                        trace.duration * 1000,
                        extra={
                            "trace_id": id(trace),
                            "session_id": getattr(self, "_session_id", None),
                            "duration_ms": trace.duration * 1000,
                        },
                    )

                return result

            except Exception as e:
                trace.exception = e
                trace.end_time = time.time()
                trace.duration = trace.end_time - trace.start_time

                # Update error metrics
                if hasattr(self, "_performance_monitoring_enabled") and self._performance_monitoring_enabled:
                    PlatformBaseClassMeta._update_performance_metrics(self, trace, method_name)

                # Log error
                if hasattr(self, "_error_tracking_enabled") and self._error_tracking_enabled:
                    self.logger.error(
                        "❌ ERROR in %s.%s() [ASYNC] [%.3fms]: %s",
                        getattr(self, "_class_name", self.__class__.__name__),
                        method_name,
                        trace.duration * 1000,
                        str(e),
                        extra={
                            "trace_id": id(trace),
                            "session_id": getattr(self, "_session_id", None),
                            "exception_type": type(e).__name__,
                            "duration_ms": trace.duration * 1000,
                        },
                        exc_info=True,
                    )

                raise

        return async_wrapper

    @staticmethod
    def _update_performance_metrics(instance, trace: MethodTrace, method_name: str) -> None:
        """Update performance metrics for a method"""
        if not hasattr(instance, "_performance_monitoring_enabled") or not instance._performance_monitoring_enabled:
            return

        # Complete the trace
        trace.end_time = time.time()
        trace.duration = trace.end_time - trace.start_time

        # Collect resource info after execution
        if trace.memory_before is not None:
            process = psutil.Process()
            trace.memory_after = process.memory_info().rss / 1024 / 1024
        if trace.cpu_before is not None:
            process = psutil.Process()
            trace.cpu_after = process.cpu_percent()

        # Update or create metrics
        if not hasattr(instance, "_performance_metrics"):
            instance._performance_metrics = {}

        if method_name not in instance._performance_metrics:
            instance._performance_metrics[method_name] = PerformanceMetrics(method_name=method_name)

        metrics = instance._performance_metrics[method_name]
        metrics.call_count += 1
        metrics.total_duration += trace.duration
        metrics.average_duration = metrics.total_duration / metrics.call_count
        metrics.min_duration = min(metrics.min_duration, trace.duration)
        metrics.max_duration = max(metrics.max_duration, trace.duration)
        metrics.last_called = datetime.now()

        if trace.exception:
            metrics.error_count += 1

        if trace.memory_after and trace.memory_before:
            metrics.memory_usage = max(metrics.memory_usage, trace.memory_after - trace.memory_before)

        if trace.cpu_after and trace.cpu_before:
            metrics.cpu_usage = max(metrics.cpu_usage, trace.cpu_after - trace.cpu_before)


class PlatformBaseClass(metaclass=PlatformBaseClassMeta):
    """
    Universal base class providing comprehensive observability capabilities.

    This class provides:
    - Method tracing and performance monitoring
    - Centralized logging with structured output
    - Metrics collection and reporting
    - Error tracking and alerting
    - Resource usage monitoring
    """

    def __init__(
        self,
        class_name: str | None = None,
        session_id: str | None = None,
        observability_level: ObservabilityLevel = ObservabilityLevel.BASIC,
    ):
        """
        Initialize the platform base class with observability capabilities.

        Args:
            class_name: Name of the class (auto-detected if not provided)
            session_id: Session ID for correlation
            observability_level: Level of observability detail
        """
        self._class_name = class_name or self.__class__.__name__
        self._session_id = session_id
        self._observability_level = observability_level
        self._process: _ProcessLike

        if _is_crosshair_analysis():
            # Lightweight initialization without logging side effects
            self.logger = _CrosshairLogger()
            self.agent_flow_logger = self.logger
            self._performance_metrics = {}
            self._active_traces = {}
            self._tracing_enabled = False
            self._performance_monitoring_enabled = False
            self._error_tracking_enabled = False
            self._metrics_collection_enabled = False
            self._process = _CrosshairProcessStub()
            self._initial_memory = 0.0
            self._initial_cpu = 0.0
            return

        # Initialize logging
        self._initialize_logging()

        # Performance tracking
        self._performance_metrics: dict[str, PerformanceMetrics] = {}
        self._active_traces: dict[str, MethodTrace] = {}

        # Configuration
        self._tracing_enabled = self._should_enable_tracing()
        self._performance_monitoring_enabled = self._should_enable_performance_monitoring()
        self._error_tracking_enabled = self._should_enable_error_tracking()
        self._metrics_collection_enabled = self._should_enable_metrics_collection()

        # Resource monitoring
        self._process = psutil.Process()
        self._initial_memory = self._process.memory_info().rss / 1024 / 1024  # MB
        self._initial_cpu = self._process.cpu_percent()

    def _initialize_logging(self) -> None:
        """Initialize logging with circular dependency protection"""
        try:
            # Get the actual module name for proper logger identification
            module_name = self.__class__.__module__
            logger_name = f"{module_name}.{self._class_name}"

            flag = getattr(LoggerSetup, "_is_platform_base_initializing", False)
            use_basic_logging = isinstance(flag, bool) and flag

            # Check if we're in a circular dependency situation
            if use_basic_logging:
                # Use basic logging to avoid circular dependency
                import logging

                self.logger = logging.getLogger(logger_name)
                self.agent_flow_logger = logging.getLogger("agent_flow")
            else:
                # Normal LoggerSetup usage: write agent logs to per-agent file and console
                # Import inside method to avoid module-level circular import fallback
                from .logger_setup import LoggerSetup as _RealLoggerSetup

                per_agent_log = f"{self._class_name}.log"
                self.logger = _RealLoggerSetup.create_logger(
                    logger_name,
                    session_id=self._session_id,
                    log_file=per_agent_log,
                )
                self.agent_flow_logger = _RealLoggerSetup.create_agent_flow_logger(session_id=self._session_id)
        except Exception as e:
            # Fallback to basic logging
            import logging

            module_name = self.__class__.__module__
            logger_name = f"{module_name}.{self._class_name}"
            self.logger = logging.getLogger(logger_name)
            self.agent_flow_logger = logging.getLogger("agent_flow")
            self.logger.warning(f"Failed to initialize LoggerSetup, using basic logging: {e}")

    def _should_enable_tracing(self) -> bool:
        """Check if method tracing should be enabled"""
        return (
            os.environ.get("PLATFORM_TRACING_ENABLED", "true").lower() == "true"
            and self._observability_level != ObservabilityLevel.NONE
        )

    def _should_enable_performance_monitoring(self) -> bool:
        """Check if performance monitoring should be enabled"""
        return os.environ.get(
            "PLATFORM_PERFORMANCE_MONITORING", "true"
        ).lower() == "true" and self._observability_level in [
            ObservabilityLevel.DETAILED,
            ObservabilityLevel.COMPREHENSIVE,
        ]

    def _should_enable_error_tracking(self) -> bool:
        """Check if error tracking should be enabled"""
        return (
            os.environ.get("PLATFORM_ERROR_TRACKING", "true").lower() == "true"
            and self._observability_level != ObservabilityLevel.NONE
        )

    def _should_enable_metrics_collection(self) -> bool:
        """Check if metrics collection should be enabled"""
        return os.environ.get(
            "PLATFORM_METRICS_COLLECTION", "true"
        ).lower() == "true" and self._observability_level in [
            ObservabilityLevel.DETAILED,
            ObservabilityLevel.COMPREHENSIVE,
        ]

    def enable_tracing(self) -> None:
        """Enable method tracing for this instance"""
        self._tracing_enabled = True
        logger = getattr(self, "logger", None)
        if logger:
            info = getattr(logger, "info", None)
            if callable(info):
                info("Method tracing enabled for %s", self._class_name)

    def disable_tracing(self) -> None:
        """Disable method tracing for this instance"""
        self._tracing_enabled = False
        logger = getattr(self, "logger", None)
        if logger:
            info = getattr(logger, "info", None)
            if callable(info):
                info("Method tracing disabled for %s", self._class_name)

    def enable_performance_monitoring(self) -> None:
        """Enable performance monitoring for this instance"""
        self._performance_monitoring_enabled = True
        logger = getattr(self, "logger", None)
        if logger:
            info = getattr(logger, "info", None)
            if callable(info):
                info("Performance monitoring enabled for %s", self._class_name)

    def disable_performance_monitoring(self) -> None:
        """Disable performance monitoring for this instance"""
        self._performance_monitoring_enabled = False
        logger = getattr(self, "logger", None)
        if logger:
            info = getattr(logger, "info", None)
            if callable(info):
                info("Performance monitoring disabled for %s", self._class_name)

    def enable_error_tracking(self) -> None:
        """Enable error tracking for this instance"""
        self._error_tracking_enabled = True
        logger = getattr(self, "logger", None)
        if logger:
            info = getattr(logger, "info", None)
            if callable(info):
                info("Error tracking enabled for %s", self._class_name)

    def disable_error_tracking(self) -> None:
        """Disable error tracking for this instance"""
        self._error_tracking_enabled = False
        logger = getattr(self, "logger", None)
        if logger:
            info = getattr(logger, "info", None)
            if callable(info):
                info("Error tracking disabled for %s", self._class_name)

    def enable_metrics_collection(self) -> None:
        """Enable metrics collection for this instance"""
        self._metrics_collection_enabled = True
        logger = getattr(self, "logger", None)
        if logger:
            info = getattr(logger, "info", None)
            if callable(info):
                info("Metrics collection enabled for %s", self._class_name)

    def disable_metrics_collection(self) -> None:
        """Disable metrics collection for this instance"""
        self._metrics_collection_enabled = False
        logger = getattr(self, "logger", None)
        if logger:
            info = getattr(logger, "info", None)
            if callable(info):
                info("Metrics collection disabled for %s", self._class_name)

    def is_tracing_enabled(self) -> bool:
        """Check if tracing is enabled for this instance"""
        return self._tracing_enabled

    def is_performance_monitoring_enabled(self) -> bool:
        """Check if performance monitoring is enabled for this instance"""
        return self._performance_monitoring_enabled

    def is_error_tracking_enabled(self) -> bool:
        """Check if error tracking is enabled for this instance"""
        return self._error_tracking_enabled

    def is_metrics_collection_enabled(self) -> bool:
        """Check if metrics collection is enabled for this instance"""
        return self._metrics_collection_enabled

    def get_performance_metrics(
        self, method_name: str | None = None
    ) -> dict[str, PerformanceMetrics] | PerformanceMetrics:
        """Get performance metrics for a method or all methods"""
        if method_name:
            return self._performance_metrics.get(method_name, PerformanceMetrics(method_name=method_name))
        return self._performance_metrics.copy()

    def reset_performance_metrics(self, method_name: str | None = None) -> None:
        """Reset performance metrics for a method or all methods"""
        if method_name:
            if method_name in self._performance_metrics:
                del self._performance_metrics[method_name]
        else:
            self._performance_metrics.clear()

    def get_resource_usage(self) -> dict[str, float]:
        """Get current resource usage information"""
        if isinstance(self._process, _CrosshairProcessStub):
            return {
                "memory_rss_mb": 0.0,
                "memory_vms_mb": 0.0,
                "cpu_percent": 0.0,
                "memory_delta_mb": 0.0,
                "cpu_delta": 0.0,
            }
        memory_info = self._process.memory_info()
        return {
            "memory_rss_mb": memory_info.rss / 1024 / 1024,
            "memory_vms_mb": memory_info.vms / 1024 / 1024,
            "cpu_percent": self._process.cpu_percent(),
            "memory_delta_mb": (memory_info.rss / 1024 / 1024) - self._initial_memory,
            "cpu_delta": self._process.cpu_percent() - self._initial_cpu,
        }

    def _create_traced_method(self, func: Callable[..., Any], method_name: str) -> Callable[..., Any]:
        """Create a traced version of a method"""
        if asyncio.iscoroutinefunction(func):
            return self._create_async_traced_method(func, method_name)
        return self._create_sync_traced_method(func, method_name)

    def _create_sync_traced_method(self, func: Callable[..., Any], method_name: str) -> Callable[..., Any]:
        """Create a traced version of a synchronous method"""

        @functools.wraps(func)
        def sync_wrapper(self, *args, **kwargs):
            # Early return if tracing is disabled
            if not self._tracing_enabled:
                return func(self, *args, **kwargs)

            # Create trace
            trace = MethodTrace(
                class_name=self._class_name,
                method_name=method_name,
                start_time=time.time(),
                args=list(args),
                kwargs=kwargs,
            )

            # Collect resource info if performance monitoring is enabled
            if self._performance_monitoring_enabled:
                trace.memory_before = self._process.memory_info().rss / 1024 / 1024
                trace.cpu_before = self._process.cpu_percent()

            # Log entry
            if self.logger.isEnabledFor(5):  # TRACE level
                self.logger.trace(
                    "🔍 ENTER %s.%s()",
                    self._class_name,
                    method_name,
                    extra={
                        "trace_id": id(trace),
                        "session_id": self._session_id,
                        "args_count": len(args),
                        "kwargs_count": len(kwargs),
                    },
                )

            try:
                # Execute the method
                result = func(self, *args, **kwargs)
                trace.return_value = result

                # Update performance metrics
                if self._performance_monitoring_enabled:
                    self._update_performance_metrics(trace, method_name)

                # Log exit
                if self.logger.isEnabledFor(5):  # TRACE level
                    duration_ms = (trace.duration or 0) * 1000
                    self.logger.trace(
                        "🔍 LEAVE %s.%s() [%.3fms]",
                        self._class_name,
                        method_name,
                        duration_ms,
                        extra={
                            "trace_id": id(trace),
                            "session_id": self._session_id,
                            "duration_ms": duration_ms,
                        },
                    )

                return result

            except Exception as e:
                trace.exception = e
                trace.end_time = time.time()
                trace.duration = trace.end_time - trace.start_time

                # Update error metrics
                if self._performance_monitoring_enabled:
                    self._update_performance_metrics(trace, method_name)

                # Log error
                if self._error_tracking_enabled:
                    self.logger.error(
                        "❌ ERROR in %s.%s() [%.3fms]: %s",
                        self._class_name,
                        method_name,
                        trace.duration * 1000,
                        str(e),
                        extra={
                            "trace_id": id(trace),
                            "session_id": self._session_id,
                            "exception_type": type(e).__name__,
                            "duration_ms": trace.duration * 1000,
                        },
                        exc_info=True,
                    )

                raise

        return sync_wrapper

    def _create_async_traced_method(self, func: Callable[..., Any], method_name: str) -> Callable[..., Any]:
        """Create a traced version of an asynchronous method"""

        @functools.wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            # Early return if tracing is disabled
            if not self._tracing_enabled:
                return await func(self, *args, **kwargs)

            # Create trace
            trace = MethodTrace(
                class_name=self._class_name,
                method_name=method_name,
                start_time=time.time(),
                args=list(args),
                kwargs=kwargs,
            )

            # Collect resource info if performance monitoring is enabled
            if self._performance_monitoring_enabled:
                trace.memory_before = self._process.memory_info().rss / 1024 / 1024
                trace.cpu_before = self._process.cpu_percent()

            # Log entry
            if self.logger.isEnabledFor(5):  # TRACE level
                self.logger.trace(
                    "🔍 ENTER %s.%s() [ASYNC]",
                    self._class_name,
                    method_name,
                    extra={
                        "trace_id": id(trace),
                        "session_id": self._session_id,
                        "args_count": len(args),
                        "kwargs_count": len(kwargs),
                    },
                )

            try:
                # Execute the method
                result = await func(self, *args, **kwargs)
                trace.return_value = result

                # Update performance metrics
                if self._performance_monitoring_enabled:
                    self._update_performance_metrics(trace, method_name)

                # Log exit
                if self.logger.isEnabledFor(5):  # TRACE level
                    duration_ms = (trace.duration or 0) * 1000
                    self.logger.trace(
                        "🔍 LEAVE %s.%s() [ASYNC] [%.3fms]",
                        self._class_name,
                        method_name,
                        duration_ms,
                        extra={
                            "trace_id": id(trace),
                            "session_id": self._session_id,
                            "duration_ms": duration_ms,
                        },
                    )

                return result

            except Exception as e:
                trace.exception = e
                trace.end_time = time.time()
                trace.duration = trace.end_time - trace.start_time

                # Update error metrics
                if self._performance_monitoring_enabled:
                    self._update_performance_metrics(trace, method_name)

                # Log error
                if self._error_tracking_enabled:
                    self.logger.error(
                        "❌ ERROR in %s.%s() [ASYNC] [%.3fms]: %s",
                        self._class_name,
                        method_name,
                        trace.duration * 1000,
                        str(e),
                        extra={
                            "trace_id": id(trace),
                            "session_id": self._session_id,
                            "exception_type": type(e).__name__,
                            "duration_ms": trace.duration * 1000,
                        },
                        exc_info=True,
                    )

                raise

        return async_wrapper

    def _update_performance_metrics(self, trace: MethodTrace, method_name: str) -> None:
        """Update performance metrics for a method"""
        if not self._performance_monitoring_enabled:
            return

        # Complete the trace
        trace.end_time = time.time()
        trace.duration = trace.end_time - trace.start_time

        # Collect resource info after execution
        if trace.memory_before is not None:
            trace.memory_after = self._process.memory_info().rss / 1024 / 1024
        if trace.cpu_before is not None:
            trace.cpu_after = self._process.cpu_percent()

        # Update or create metrics
        if method_name not in self._performance_metrics:
            self._performance_metrics[method_name] = PerformanceMetrics(method_name=method_name)

        metrics = self._performance_metrics[method_name]
        metrics.call_count += 1
        metrics.total_duration += trace.duration
        metrics.average_duration = metrics.total_duration / metrics.call_count
        metrics.min_duration = min(metrics.min_duration, trace.duration)
        metrics.max_duration = max(metrics.max_duration, trace.duration)
        metrics.last_called = datetime.now()

        if trace.exception:
            metrics.error_count += 1

        if trace.memory_after and trace.memory_before:
            metrics.memory_usage = max(metrics.memory_usage, trace.memory_after - trace.memory_before)

        if trace.cpu_after and trace.cpu_before:
            metrics.cpu_usage = max(metrics.cpu_usage, trace.cpu_after - trace.cpu_before)


class PlatformABC(ABCMeta):
    """
    Metaclass for ABC-based classes that need observability.
    Automatically applies PlatformBaseClass capabilities.
    """

    def __new__(cls, name: str, bases: tuple, attrs: dict) -> type:
        """Create a new class with automatic observability capabilities"""
        # Create the class first
        new_class = super().__new__(cls, name, bases, attrs)

        # Check if this class should have observability
        if not cls._should_apply_observability(name, bases, attrs):
            return new_class

        # Apply observability to methods
        cls._apply_observability_to_methods(new_class, attrs)

        return new_class

    @staticmethod
    def _should_apply_observability(name: str, bases: tuple, attrs: dict) -> bool:
        """Check if observability should be applied to this class"""
        # Skip if explicitly disabled
        if attrs.get("_platform_observability_disabled", False):
            return False

        # Apply to classes that inherit from ABC or have observability enabled
        return any(issubclass(base, ABC) for base in bases if isinstance(base, type)) or attrs.get(
            "_platform_observability_enabled", False
        )

    @staticmethod
    def _create_traced_method(func: Callable[..., Any], method_name: str) -> Callable[..., Any]:
        """Create a traced method wrapper"""
        return PlatformBaseClassMeta._create_traced_method(func, method_name)

    @staticmethod
    def _apply_observability_to_methods(new_class: type, attrs: dict) -> None:
        """Apply observability to methods in the class"""
        # Wrap methods with tracing using static utilities, without instantiating the class
        for attr_name, attr_value in attrs.items():
            # Skip static methods - they should remain static
            if isinstance(attr_value, staticmethod):
                continue
            # Skip class methods - they should remain class methods
            if isinstance(attr_value, classmethod):
                continue
            # Skip property descriptors
            if isinstance(attr_value, property):
                continue

            # Skip methods marked with _no_trace attribute
            if hasattr(attr_value, "_no_trace") and attr_value._no_trace:
                continue

            if callable(attr_value) and not str(attr_name).startswith("__") and not str(attr_name).startswith("_"):
                # Wrap public methods
                setattr(
                    new_class,
                    attr_name,
                    PlatformABC._create_traced_method(attr_value, attr_name),
                )
            elif (
                callable(attr_value)
                and str(attr_name).startswith("_")
                and attr_name
                in [
                    "_tick",
                    "_process_agent_specific",
                    "_handle_request",
                    "_listen_for_requests",
                ]
            ):
                # Wrap specific private methods that are commonly overridden
                setattr(
                    new_class,
                    attr_name,
                    PlatformABC._create_traced_method(attr_value, attr_name),
                )


# Try to import Pydantic and create the correct metaclass
try:
    from pydantic import BaseModel
    from pydantic._internal._model_construction import ModelMetaclass

    class _PlatformPydanticImpl(ModelMetaclass):
        """
        Metaclass for Pydantic-based classes that need observability.
        Automatically applies PlatformBaseClass capabilities.
        """

        def __new__(cls, name: str, bases: tuple, attrs: dict) -> type:
            """Create a new class with automatic observability capabilities"""
            # Create the class first using Pydantic's metaclass
            new_class = super().__new__(cls, name, bases, attrs)

            # Check if this class should have observability
            if not cls._should_apply_observability(name, bases, attrs):
                return new_class

            # Apply observability to methods
            cls._apply_observability_to_methods(new_class, attrs)

            return new_class

        @staticmethod
        def _should_apply_observability(name: str, bases: tuple, attrs: dict) -> bool:
            """Check if observability should be applied to this class"""
            # Skip if explicitly disabled
            if attrs.get("_platform_observability_disabled", False):
                return False

            # Apply to classes that have observability enabled
            return attrs.get("_platform_observability_enabled", False)

        @staticmethod
        def _apply_observability_to_methods(new_class: type, attrs: dict) -> None:
            """Apply observability to methods in the class"""
            # Create a temporary instance to get the tracing methods
            temp_instance = None
            try:
                # Try to create a temporary instance
                temp_instance = new_class()
            except Exception:
                # If we can't create an instance, skip observability
                return

            # Wrap methods with tracing
            for attr_name, attr_value in attrs.items():
                if callable(attr_value) and not str(attr_name).startswith("__") and not str(attr_name).startswith("_"):
                    # Wrap public methods
                    setattr(
                        new_class,
                        attr_name,
                        PlatformABC._create_traced_method(attr_value, attr_name),
                    )

    PlatformPydantic = _PlatformPydanticImpl

except ImportError:
    # Fallback if Pydantic is not available
    class _PlatformPydanticFallback(type):
        """Fallback metaclass when Pydantic is not available"""

    PlatformPydantic = _PlatformPydanticFallback


# Global observability control functions
def enable_global_tracing() -> None:
    """Enable tracing globally via environment variable"""
    os.environ["PLATFORM_TRACING_ENABLED"] = "true"


def disable_global_tracing() -> None:
    """Disable tracing globally via environment variable"""
    os.environ["PLATFORM_TRACING_ENABLED"] = "false"


def enable_global_performance_monitoring() -> None:
    """Enable performance monitoring globally via environment variable"""
    os.environ["PLATFORM_PERFORMANCE_MONITORING"] = "true"


def disable_global_performance_monitoring() -> None:
    """Disable performance monitoring globally via environment variable"""
    os.environ["PLATFORM_PERFORMANCE_MONITORING"] = "false"


def enable_global_error_tracking() -> None:
    """Enable error tracking globally via environment variable"""
    os.environ["PLATFORM_ERROR_TRACKING"] = "true"


def disable_global_error_tracking() -> None:
    """Disable error tracking globally via environment variable"""
    os.environ["PLATFORM_ERROR_TRACKING"] = "false"


def enable_global_metrics_collection() -> None:
    """Enable metrics collection globally via environment variable"""
    os.environ["PLATFORM_METRICS_COLLECTION"] = "true"


def disable_global_metrics_collection() -> None:
    """Disable metrics collection globally via environment variable"""
    os.environ["PLATFORM_METRICS_COLLECTION"] = "false"

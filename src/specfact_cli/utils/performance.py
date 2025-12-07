"""
Performance monitoring and benchmarking utilities.

This module provides utilities for tracking command execution time,
identifying slow operations, and reporting performance metrics.
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

from beartype import beartype
from rich.console import Console


console = Console()


@dataclass
class PerformanceMetric:
    """Performance metric for a single operation."""

    operation: str
    duration: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "operation": self.operation,
            "duration": self.duration,
            "metadata": self.metadata,
        }


@dataclass
class PerformanceReport:
    """Performance report for a command execution."""

    command: str
    total_duration: float
    metrics: list[PerformanceMetric] = field(default_factory=list)
    slow_operations: list[PerformanceMetric] = field(default_factory=list)
    threshold: float = 5.0  # Operations taking > 5 seconds are considered slow

    def add_metric(self, metric: PerformanceMetric) -> None:
        """Add a performance metric."""
        self.metrics.append(metric)
        if metric.duration > self.threshold:
            self.slow_operations.append(metric)

    def get_summary(self) -> dict[str, Any]:
        """Get summary of performance report."""
        return {
            "command": self.command,
            "total_duration": self.total_duration,
            "total_operations": len(self.metrics),
            "slow_operations_count": len(self.slow_operations),
            "slow_operations": [
                {
                    "operation": m.operation,
                    "duration": m.duration,
                    "metadata": m.metadata,
                }
                for m in self.slow_operations
            ],
        }

    def print_summary(self) -> None:
        """Print performance summary to console."""
        console.print(f"\n[bold cyan]Performance Report: {self.command}[/bold cyan]")
        console.print(f"[dim]Total duration: {self.total_duration:.2f}s[/dim]")
        console.print(f"[dim]Total operations: {len(self.metrics)}[/dim]")

        if self.slow_operations:
            console.print(f"\n[bold yellow]Slow operations (> {self.threshold}s):[/bold yellow]")
            for metric in sorted(self.slow_operations, key=lambda m: m.duration, reverse=True):
                console.print(
                    f"  • {metric.operation}: {metric.duration:.2f}s"
                    + (f" ({metric.metadata})" if metric.metadata else "")
                )


class PerformanceMonitor:
    """Performance monitor for tracking command execution."""

    def __init__(self, command: str, threshold: float = 5.0) -> None:
        """
        Initialize performance monitor.

        Args:
            command: Command name being monitored
            threshold: Threshold in seconds for slow operations
        """
        self.command = command
        self.threshold = threshold
        self.start_time: float | None = None
        self.metrics: list[PerformanceMetric] = []
        self._enabled = True

    @beartype
    def start(self) -> None:
        """Start performance monitoring."""
        if not self._enabled:
            return
        self.start_time = time.time()

    @beartype
    def stop(self) -> None:
        """Stop performance monitoring."""
        if not self.start_time:
            return
        self.start_time = None

    @beartype
    @contextmanager
    def track(self, operation: str, metadata: dict[str, Any] | None = None):
        """
        Track an operation's performance.

        Args:
            operation: Operation name
            metadata: Optional metadata about the operation

        Yields:
            None
        """
        if not self._enabled:
            yield
            return

        start = time.time()
        try:
            yield
        finally:
            duration = time.time() - start
            metric = PerformanceMetric(
                operation=operation,
                duration=duration,
                metadata=metadata or {},
            )
            self.metrics.append(metric)

    @beartype
    def get_report(self) -> PerformanceReport:
        """
        Get performance report.

        Returns:
            PerformanceReport with all metrics
        """
        total_duration = 0.0
        if self.start_time:
            total_duration = time.time() - self.start_time

        report = PerformanceReport(
            command=self.command,
            total_duration=total_duration,
            threshold=self.threshold,
        )

        for metric in self.metrics:
            report.add_metric(metric)

        return report

    @beartype
    def disable(self) -> None:
        """Disable performance monitoring."""
        self._enabled = False

    @beartype
    def enable(self) -> None:
        """Enable performance monitoring."""
        self._enabled = True


# Global performance monitor instance
_performance_monitor: PerformanceMonitor | None = None


@beartype
def get_performance_monitor() -> PerformanceMonitor | None:
    """Get global performance monitor instance."""
    return _performance_monitor


@beartype
def set_performance_monitor(monitor: PerformanceMonitor | None) -> None:
    """Set global performance monitor instance."""
    global _performance_monitor
    _performance_monitor = monitor


@beartype
@contextmanager
def track_performance(command: str, threshold: float = 5.0):
    """
    Context manager for tracking command performance.

    Args:
        command: Command name
        threshold: Threshold in seconds for slow operations

    Yields:
        PerformanceMonitor instance
    """
    monitor = PerformanceMonitor(command, threshold)
    monitor.start()
    set_performance_monitor(monitor)

    try:
        yield monitor
    finally:
        monitor.stop()
        set_performance_monitor(None)

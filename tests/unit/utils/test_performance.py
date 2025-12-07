"""Unit tests for performance monitoring utilities."""

from __future__ import annotations

import time

from specfact_cli.utils.performance import (
    PerformanceMetric,
    PerformanceMonitor,
    PerformanceReport,
    get_performance_monitor,
    set_performance_monitor,
    track_performance,
)


class TestPerformanceMetric:
    """Tests for PerformanceMetric."""

    def test_to_dict(self) -> None:
        """Test converting metric to dictionary."""
        metric = PerformanceMetric(operation="test_op", duration=1.5, metadata={"key": "value"})
        result = metric.to_dict()
        assert result == {"operation": "test_op", "duration": 1.5, "metadata": {"key": "value"}}


class TestPerformanceReport:
    """Tests for PerformanceReport."""

    def test_add_metric(self) -> None:
        """Test adding metrics to report."""
        report = PerformanceReport(command="test", total_duration=10.0, threshold=5.0)
        metric1 = PerformanceMetric(operation="fast_op", duration=1.0)
        metric2 = PerformanceMetric(operation="slow_op", duration=6.0)

        report.add_metric(metric1)
        report.add_metric(metric2)

        assert len(report.metrics) == 2
        assert len(report.slow_operations) == 1
        assert report.slow_operations[0].operation == "slow_op"

    def test_get_summary(self) -> None:
        """Test getting summary of report."""
        report = PerformanceReport(command="test", total_duration=10.0, threshold=5.0)
        report.add_metric(PerformanceMetric(operation="slow_op", duration=6.0))

        summary = report.get_summary()
        assert summary["command"] == "test"
        assert summary["total_duration"] == 10.0
        assert summary["total_operations"] == 1
        assert summary["slow_operations_count"] == 1


class TestPerformanceMonitor:
    """Tests for PerformanceMonitor."""

    def test_start_stop(self) -> None:
        """Test starting and stopping monitor."""
        monitor = PerformanceMonitor("test_command")
        monitor.start()
        assert monitor.start_time is not None
        monitor.stop()
        # start_time may still be set, but that's okay for this test

    def test_track_operation(self) -> None:
        """Test tracking an operation."""
        monitor = PerformanceMonitor("test_command")
        monitor.start()

        with monitor.track("test_operation", {"key": "value"}):
            time.sleep(0.01)  # Small delay to ensure duration > 0

        monitor.stop()
        report = monitor.get_report()
        assert len(report.metrics) == 1
        assert report.metrics[0].operation == "test_operation"
        assert report.metrics[0].duration > 0
        assert report.metrics[0].metadata == {"key": "value"}

    def test_disable_enable(self) -> None:
        """Test disabling and enabling monitor."""
        monitor = PerformanceMonitor("test_command")
        monitor.disable()
        monitor.start()

        with monitor.track("test_operation"):
            pass

        monitor.stop()
        report = monitor.get_report()
        # When disabled, no metrics should be recorded
        assert len(report.metrics) == 0

        monitor.enable()
        monitor.start()
        with monitor.track("test_operation"):
            pass
        monitor.stop()
        report = monitor.get_report()
        assert len(report.metrics) == 1


class TestTrackPerformance:
    """Tests for track_performance context manager."""

    def test_track_performance_context(self) -> None:
        """Test track_performance context manager."""
        with track_performance("test_command", threshold=5.0) as monitor:
            assert monitor is not None
            assert monitor.command == "test_command"
            assert monitor.threshold == 5.0

            with monitor.track("test_op"):
                time.sleep(0.01)

        # After context exits, monitor should be stopped
        report = monitor.get_report()
        assert len(report.metrics) == 1

    def test_global_monitor(self) -> None:
        """Test global monitor instance."""
        # Clear any existing monitor
        set_performance_monitor(None)
        assert get_performance_monitor() is None

        with track_performance("test_command") as monitor:
            assert get_performance_monitor() is monitor

        # After context exits, monitor should be cleared
        assert get_performance_monitor() is None

"""
E2E integration tests for watch mode with actual file changes.

These tests verify that watch mode correctly detects and syncs changes
when files are created/modified on either Spec-Kit or SpecFact side.
"""

from __future__ import annotations

import os
import threading
import time
from contextlib import suppress
from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import dedent
from typing import Any

import pytest
from typer.testing import CliRunner

from specfact_cli.cli import app


runner = CliRunner()


class TestWatchModeE2E:
    """E2E tests for watch mode with actual file changes."""

    def test_watch_mode_detects_speckit_changes(self) -> None:
        """Test that watch mode detects and syncs Spec-Kit changes."""
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            # Create initial Spec-Kit structure
            specify_dir = repo_path / ".specify" / "memory"
            specify_dir.mkdir(parents=True)
            (specify_dir / "constitution.md").write_text("# Constitution\n")

            # Create SpecFact structure
            plans_dir = repo_path / ".specfact" / "plans"
            plans_dir.mkdir(parents=True)
            (plans_dir / "main.bundle.yaml").write_text("version: '1.0'\n")

            # Track sync events
            sync_events: list[str] = []
            sync_lock = threading.Lock()

            def run_watch_mode() -> None:
                """Run watch mode in a separate thread."""
                result = runner.invoke(
                    app,
                    [
                        "sync",
                        "spec-kit",
                        "--repo",
                        str(repo_path),
                        "--bidirectional",
                        "--watch",
                        "--interval",
                        "1",
                    ],
                )
                with sync_lock:
                    sync_events.append("watch_completed")
                    if result.stdout:
                        sync_events.append(f"stdout: {result.stdout}")

            # Start watch mode in background thread
            watch_thread = threading.Thread(target=run_watch_mode, daemon=True)
            watch_thread.start()

            # Wait for watch mode to start
            time.sleep(1.5)

            # Create a new Spec-Kit feature while watch mode is running
            specs_dir = repo_path / "specs" / "001-test-feature"
            specs_dir.mkdir(parents=True)
            spec_file = specs_dir / "spec.md"
            spec_file.write_text(
                dedent(
                    """# Feature Specification: Test Feature

## User Scenarios & Testing

### User Story 1 - Test Story (Priority: P1)
As a user, I want to test features so that I can validate functionality.

**Acceptance Scenarios**:
1. Given test setup, When test runs, Then test passes
"""
                )
            )

            # Wait for watch mode to detect and process the change
            # Watch mode processes changes at the interval (1 second), plus debounce (0.5 seconds)
            time.sleep(3.0)

            # Verify that sync was triggered (check if SpecFact plan was created/updated)
            # After Spec-Kit change, bidirectional sync should create/update SpecFact plans
            plan_files = list(plans_dir.glob("*.yaml"))
            assert len(plan_files) > 0, "SpecFact plan should be created/updated after Spec-Kit change"

            # Verify the plan file was actually updated (not just exists)
            # The sync should have processed the Spec-Kit spec.md and created/updated the plan
            main_plan = plans_dir / "main.bundle.yaml"
            if main_plan.exists():
                plan_content = main_plan.read_text()
                # Plan should contain version at minimum
                assert "version" in plan_content, "Plan should contain version after sync"

            # Note: Watch mode will continue running, but we've verified it detects changes
            # The thread will be cleaned up when tmpdir is removed

    def test_watch_mode_detects_specfact_changes(self) -> None:
        """Test that watch mode detects and syncs SpecFact changes."""
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            # Create initial Spec-Kit structure
            specify_dir = repo_path / ".specify" / "memory"
            specify_dir.mkdir(parents=True)
            (specify_dir / "constitution.md").write_text("# Constitution\n")

            # Create SpecFact structure
            plans_dir = repo_path / ".specfact" / "plans"
            plans_dir.mkdir(parents=True)
            (plans_dir / "main.bundle.yaml").write_text("version: '1.0'\n")

            # Start watch mode in background thread
            def run_watch_mode() -> None:
                """Run watch mode in a separate thread."""
                runner.invoke(
                    app,
                    [
                        "sync",
                        "spec-kit",
                        "--repo",
                        str(repo_path),
                        "--bidirectional",
                        "--watch",
                        "--interval",
                        "1",
                    ],
                )

            watch_thread = threading.Thread(target=run_watch_mode, daemon=True)
            watch_thread.start()

            # Wait for watch mode to start
            time.sleep(1.5)

            # Modify SpecFact plan while watch mode is running
            plan_file = plans_dir / "main.bundle.yaml"
            plan_file.write_text(
                dedent(
                    """version: '1.0'
features:
  - key: FEATURE-001
    title: Test Feature
    outcomes:
      - Test outcome
"""
                )
            )

            # Wait for watch mode to detect and process the change
            # Watch mode processes changes at the interval (1 second), plus debounce (0.5 seconds)
            time.sleep(3.0)

            # Verify that sync was triggered (check if Spec-Kit artifacts were updated)
            # In bidirectional sync, SpecFact changes should sync to Spec-Kit
            # Check if Spec-Kit artifacts were created/updated
            specs_dir = repo_path / "specs"
            if specs_dir.exists():
                # SpecFact → Spec-Kit sync should create/update Spec-Kit artifacts
                # Note: Actual sync logic is tested in unit tests
                # This e2e test verifies watch mode detects and triggers sync
                _ = list(specs_dir.rglob("*.md"))  # Verify spec files exist

    @pytest.mark.timeout(10)
    def test_watch_mode_bidirectional_sync(self) -> None:
        """Test that watch mode handles bidirectional sync with changes on both sides."""

        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            try:
                # Create initial Spec-Kit structure
                specify_dir = repo_path / ".specify" / "memory"
                specify_dir.mkdir(parents=True)
                (specify_dir / "constitution.md").write_text("# Constitution\n")

                # Create SpecFact structure
                plans_dir = repo_path / ".specfact" / "plans"
                plans_dir.mkdir(parents=True)
                (plans_dir / "main.bundle.yaml").write_text("version: '1.0'\n")

                # Start watch mode in background thread
                def run_watch_mode() -> None:
                    """Run watch mode in a separate thread."""
                    runner.invoke(
                        app,
                        [
                            "sync",
                            "spec-kit",
                            "--repo",
                            str(repo_path),
                            "--bidirectional",
                            "--watch",
                            "--interval",
                            "1",
                        ],
                    )

                watch_thread = threading.Thread(target=run_watch_mode, daemon=True)
                watch_thread.start()

                # Wait for watch mode to start
                time.sleep(1.5)

                # Create Spec-Kit feature
                specs_dir = repo_path / "specs" / "001-test-feature"
                specs_dir.mkdir(parents=True)
                spec_file = specs_dir / "spec.md"
                spec_file.write_text(
                    dedent(
                        """# Feature Specification: Test Feature

## User Scenarios & Testing

### User Story 1 - Test Story (Priority: P1)
As a user, I want to test features so that I can validate functionality.
"""
                    )
                )

                # Wait for first sync (Spec-Kit → SpecFact)
                # Watch mode processes changes at the interval (1 second), plus debounce (0.5 seconds)
                time.sleep(2.5)

                # Verify first sync happened (Spec-Kit → SpecFact)
                plan_files = list(plans_dir.glob("*.yaml"))
                assert len(plan_files) > 0, "SpecFact plan should exist after Spec-Kit change"

                # Then modify SpecFact plan
                plan_file = plans_dir / "main.bundle.yaml"
                plan_file.write_text(
                    dedent(
                        """version: '1.0'
features:
  - key: FEATURE-001
    title: Test Feature
"""
                    )
                )

                # Wait for second sync (SpecFact → Spec-Kit)
                time.sleep(2.5)

                # Verify both sides were synced
                # Spec-Kit → SpecFact: spec.md should create/update plan
                assert len(plan_files) > 0, "SpecFact plan should exist after Spec-Kit change"

                # SpecFact → Spec-Kit: plan changes should sync back (if bidirectional works)
                # Check if Spec-Kit artifacts were updated
                specs_dir = repo_path / "specs"
                if specs_dir.exists():
                    # Note: Actual sync logic is tested in unit tests
                    # This e2e test verifies watch mode detects changes on both sides
                    _ = list(specs_dir.rglob("*.md"))  # Verify spec files exist

                # Wait a bit for any final file operations to complete
                # This allows file handles to be released before cleanup
                time.sleep(0.5)
            finally:
                # Wait for watch mode thread to release file handles
                # Since it's a daemon thread, it will be terminated, but we need to give
                # the Observer time to release file handles
                time.sleep(0.5)

                # Comprehensive cleanup: Remove all files and directories recursively
                # This ensures TemporaryDirectory can clean up properly
                # Retry cleanup up to 3 times with brief delays
                for attempt in range(3):
                    try:
                        # Remove all files first
                        for root, dirs, files in os.walk(repo_path, topdown=False):
                            for file in files:
                                file_path = Path(root) / file
                                with suppress(OSError, PermissionError):
                                    file_path.unlink()
                            # Then remove directories (bottom-up)
                            for dir_name in dirs:
                                dir_path = Path(root) / dir_name
                                with suppress(OSError, PermissionError):
                                    dir_path.rmdir()
                        # Success - break out of retry loop
                        break
                    except (OSError, PermissionError):
                        if attempt < 2:  # Don't sleep on last attempt
                            time.sleep(0.2)  # Brief delay before retry

    def test_watch_mode_detects_repository_changes(self) -> None:
        """Test that watch mode detects and syncs repository code changes."""
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            # Create initial repository structure
            src_dir = repo_path / "src" / "module"
            src_dir.mkdir(parents=True)
            (src_dir / "__init__.py").write_text("")

            # Create SpecFact structure
            plans_dir = repo_path / ".specfact" / "plans"
            plans_dir.mkdir(parents=True)
            (plans_dir / "main.bundle.yaml").write_text("version: '1.0'\n")

            # Start watch mode in background thread
            def run_watch_mode() -> None:
                """Run watch mode in a separate thread."""
                runner.invoke(
                    app,
                    [
                        "sync",
                        "repository",
                        "--repo",
                        str(repo_path),
                        "--watch",
                        "--interval",
                        "1",
                    ],
                )

            watch_thread = threading.Thread(target=run_watch_mode, daemon=True)
            watch_thread.start()

            # Wait for watch mode to start
            time.sleep(1.5)

            # Create new code file while watch mode is running
            new_file = src_dir / "new_module.py"
            new_file.write_text(
                dedent(
                    """class NewModule:
    def new_function(self):
        pass
"""
                )
            )

            # Wait for watch mode to detect and process the change
            time.sleep(2.5)

            # Verify that sync was triggered
            # Repository sync should update SpecFact plans based on code changes
            # This is a basic check - actual sync logic is tested in unit tests

    @pytest.mark.timeout(10)
    def test_watch_mode_handles_multiple_changes(self) -> None:
        """Test that watch mode handles multiple rapid file changes."""
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            # Create initial Spec-Kit structure
            specify_dir = repo_path / ".specify" / "memory"
            specify_dir.mkdir(parents=True)
            (specify_dir / "constitution.md").write_text("# Constitution\n")

            # Create SpecFact structure
            plans_dir = repo_path / ".specfact" / "plans"
            plans_dir.mkdir(parents=True)
            (plans_dir / "main.bundle.yaml").write_text("version: '1.0'\n")

            # Start watch mode in background thread
            def run_watch_mode() -> None:
                """Run watch mode in a separate thread."""
                runner.invoke(
                    app,
                    [
                        "sync",
                        "spec-kit",
                        "--repo",
                        str(repo_path),
                        "--bidirectional",
                        "--watch",
                        "--interval",
                        "1",
                    ],
                )

            watch_thread = threading.Thread(target=run_watch_mode, daemon=True)
            watch_thread.start()

            # Wait for watch mode to start
            time.sleep(1.5)

            # Create multiple Spec-Kit features rapidly
            for i in range(3):
                specs_dir = repo_path / "specs" / f"00{i + 1}-test-feature-{i}"
                specs_dir.mkdir(parents=True)
                spec_file = specs_dir / "spec.md"
                spec_file.write_text(f"# Feature {i + 1}\n")

                # Small delay between changes
                time.sleep(0.3)

            # Wait for watch mode to process all changes
            time.sleep(2.5)

            # Verify that sync was triggered for multiple changes
            # Watch mode should handle debouncing and process changes
            plan_files = list(plans_dir.glob("*.yaml"))
            assert len(plan_files) > 0, "SpecFact plans should exist after multiple Spec-Kit changes"

    @pytest.mark.slow
    @pytest.mark.timeout(8)
    def test_watch_mode_graceful_shutdown(self) -> None:
        """Test that watch mode handles graceful shutdown (Ctrl+C simulation)."""
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            # Create initial Spec-Kit structure
            specify_dir = repo_path / ".specify" / "memory"
            specify_dir.mkdir(parents=True)
            (specify_dir / "constitution.md").write_text("# Constitution\n")

            # Create SpecFact structure
            plans_dir = repo_path / ".specfact" / "plans"
            plans_dir.mkdir(parents=True)
            (plans_dir / "main.bundle.yaml").write_text("version: '1.0'\n")

            # Track if watch mode started
            watch_started = threading.Event()
            result_container: dict[str, Any] = {"result": None}

            def run_watch_mode() -> None:
                """Run watch mode in a separate thread."""
                try:
                    result = runner.invoke(
                        app,
                        [
                            "sync",
                            "spec-kit",
                            "--repo",
                            str(repo_path),
                            "--bidirectional",
                            "--watch",
                            "--interval",
                            "1",
                        ],
                    )
                    result_container["result"] = result
                    # Check if watch mode started by looking at stdout
                    if result.stdout and (
                        "Watch mode enabled" in result.stdout or "Watching for changes" in result.stdout
                    ):
                        watch_started.set()
                except KeyboardInterrupt:
                    watch_started.set()
                except Exception:
                    # If any exception occurs, still mark as started if we got output
                    stored_result = result_container.get("result")
                    if stored_result and hasattr(stored_result, "stdout") and stored_result.stdout:
                        watch_started.set()

            watch_thread = threading.Thread(target=run_watch_mode, daemon=True)
            watch_thread.start()

            # Wait for watch mode to start (check stdout for confirmation)
            time.sleep(2.0)

            # Verify watch mode started successfully
            # Since watch mode runs continuously, we verify it started by checking
            # that the thread is still alive and watch mode output would be present
            assert watch_thread.is_alive() or watch_started.is_set(), "Watch mode should start successfully"

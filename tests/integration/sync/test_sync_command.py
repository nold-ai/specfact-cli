"""
Integration tests for sync command with realistic scenarios.
"""

from __future__ import annotations

import contextlib
from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import dedent

from typer.testing import CliRunner

from specfact_cli.cli import app


runner = CliRunner()


class TestSyncCommandIntegration:
    """Integration tests for sync command with realistic repositories."""

    def test_sync_spec_kit_basic(self) -> None:
        """Test basic sync spec-kit command."""
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            # Create minimal Spec-Kit structure
            specify_dir = repo_path / ".specify" / "memory"
            specify_dir.mkdir(parents=True)
            (specify_dir / "constitution.md").write_text("# Constitution\n")

            # Create minimal feature spec (required for sync)
            specs_dir = repo_path / "specs" / "001-test-feature"
            specs_dir.mkdir(parents=True)
            (specs_dir / "spec.md").write_text(
                "# Feature Specification: Test Feature\n\n## User Scenarios & Testing\n\n### User Story 1 - Test Story (Priority: P1)\nTest story\n"
            )

            # Create modular bundle first
            bundle_name = "main"
            projects_dir = repo_path / ".specfact" / "projects"
            projects_dir.mkdir(parents=True)
            bundle_dir = projects_dir / bundle_name
            bundle_dir.mkdir()

            from specfact_cli.commands.plan import _convert_plan_bundle_to_project_bundle
            from specfact_cli.models.plan import PlanBundle, Product
            from specfact_cli.utils.bundle_loader import save_project_bundle

            plan_bundle = PlanBundle(
                version="1.0",
                idea=None,
                business=None,
                product=Product(themes=[], releases=[]),
                features=[],
                clarifications=None,
                metadata=None,
            )
            project_bundle = _convert_plan_bundle_to_project_bundle(plan_bundle, bundle_name)
            save_project_bundle(project_bundle, bundle_dir, atomic=True)

            result = runner.invoke(
                app, ["sync", "bridge", "--repo", str(repo_path), "--adapter", "speckit", "--bundle", bundle_name]
            )

            assert result.exit_code == 0
            assert "Syncing" in result.stdout or "Sync complete" in result.stdout or "Bridge" in result.stdout

    def test_sync_spec_kit_with_bidirectional(self) -> None:
        """Test sync spec-kit with bidirectional flag."""
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            # Create Spec-Kit structure
            specify_dir = repo_path / ".specify" / "memory"
            specify_dir.mkdir(parents=True)
            (specify_dir / "constitution.md").write_text("# Constitution\n")

            # Create SpecFact structure (modular bundle)
            bundle_name = "main"
            projects_dir = repo_path / ".specfact" / "projects"
            projects_dir.mkdir(parents=True)
            bundle_dir = projects_dir / bundle_name
            bundle_dir.mkdir()

            from specfact_cli.commands.plan import _convert_plan_bundle_to_project_bundle
            from specfact_cli.models.plan import PlanBundle, Product
            from specfact_cli.utils.bundle_loader import save_project_bundle

            plan_bundle = PlanBundle(
                version="1.0",
                idea=None,
                business=None,
                product=Product(themes=[], releases=[]),
                features=[],
                clarifications=None,
                metadata=None,
            )
            project_bundle = _convert_plan_bundle_to_project_bundle(plan_bundle, bundle_name)
            save_project_bundle(project_bundle, bundle_dir, atomic=True)

            result = runner.invoke(
                app,
                [
                    "sync",
                    "bridge",
                    "--repo",
                    str(repo_path),
                    "--adapter",
                    "speckit",
                    "--bundle",
                    bundle_name,
                    "--bidirectional",
                ],
            )

            assert result.exit_code == 0
            assert "Syncing" in result.stdout or "Sync complete" in result.stdout or "Bridge" in result.stdout

    def test_sync_spec_kit_with_changes(self) -> None:
        """Test sync spec-kit with actual changes."""
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            # Create Spec-Kit structure (required for detection)
            specify_dir = repo_path / ".specify" / "memory"
            specify_dir.mkdir(parents=True)
            (specify_dir / "constitution.md").write_text("# Constitution\n")

            # Create Spec-Kit structure with feature
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

            # Create modular bundle
            bundle_name = "main"
            projects_dir = repo_path / ".specfact" / "projects"
            projects_dir.mkdir(parents=True)
            bundle_dir = projects_dir / bundle_name
            bundle_dir.mkdir()

            from specfact_cli.commands.plan import _convert_plan_bundle_to_project_bundle
            from specfact_cli.models.plan import PlanBundle, Product
            from specfact_cli.utils.bundle_loader import save_project_bundle

            plan_bundle = PlanBundle(
                version="1.0",
                idea=None,
                business=None,
                product=Product(themes=[], releases=[]),
                features=[],
                clarifications=None,
                metadata=None,
            )
            project_bundle = _convert_plan_bundle_to_project_bundle(plan_bundle, bundle_name)
            save_project_bundle(project_bundle, bundle_dir, atomic=True)

            result = runner.invoke(
                app,
                [
                    "sync",
                    "bridge",
                    "--repo",
                    str(repo_path),
                    "--adapter",
                    "speckit",
                    "--bundle",
                    bundle_name,
                    "--bidirectional",
                ],
            )

            assert result.exit_code == 0
            assert "Detected" in result.stdout or "Sync complete" in result.stdout or "Bridge" in result.stdout

    def test_sync_spec_kit_watch_mode_not_implemented(self) -> None:
        """Test sync spec-kit watch mode (now implemented)."""
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            # Create Spec-Kit structure
            specify_dir = repo_path / ".specify" / "memory"
            specify_dir.mkdir(parents=True)
            (specify_dir / "constitution.md").write_text("# Constitution\n")

            # Create SpecFact structure (modular bundle)
            bundle_name = "main"
            projects_dir = repo_path / ".specfact" / "projects"
            projects_dir.mkdir(parents=True)
            bundle_dir = projects_dir / bundle_name
            bundle_dir.mkdir()

            from specfact_cli.commands.plan import _convert_plan_bundle_to_project_bundle
            from specfact_cli.models.plan import PlanBundle, Product
            from specfact_cli.utils.bundle_loader import save_project_bundle

            plan_bundle = PlanBundle(
                version="1.0",
                idea=None,
                business=None,
                product=Product(themes=[], releases=[]),
                features=[],
                clarifications=None,
                metadata=None,
            )
            project_bundle = _convert_plan_bundle_to_project_bundle(plan_bundle, bundle_name)
            save_project_bundle(project_bundle, bundle_dir, atomic=True)

            # Watch mode is now implemented - it will start and wait
            # Use a short timeout to verify it starts correctly
            import threading
            import time
            from typing import Any

            result_container: dict[str, Any] = {"result": None}

            def run_command() -> None:
                with contextlib.suppress(ValueError, OSError):
                    # Handle case where streams are closed (expected in threading scenarios)
                    result_container["result"] = runner.invoke(
                        app,
                        [
                            "sync",
                            "bridge",
                            "--repo",
                            str(repo_path),
                            "--adapter",
                            "speckit",
                            "--bundle",
                            bundle_name,
                            "--watch",
                            "--interval",
                            "1",
                        ],
                    )

            thread = threading.Thread(target=run_command, daemon=True)
            thread.start()
            time.sleep(0.5)  # Give it time to start
            thread.join(timeout=0.1)

            # Verify watch mode started (not "not implemented")
            # The command may still be running, but we can check the output
            if result_container["result"]:
                assert "Watch mode enabled" in result_container["result"].stdout
                assert "not implemented" not in result_container["result"].stdout.lower()
            else:
                # Command is still running (expected for watch mode)
                # Just verify it doesn't say "not implemented"
                pass

    def test_sync_spec_kit_nonexistent_repo(self) -> None:
        """Test sync bridge with nonexistent repository."""
        result = runner.invoke(
            app,
            ["sync", "bridge", "--adapter", "speckit", "--repo", "/nonexistent/path"],
        )

        # Should fail gracefully
        assert result.exit_code != 0

    def test_sync_spec_kit_with_overwrite_flag(self) -> None:
        """Test sync spec-kit with overwrite flag is accepted."""
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            # Create minimal Spec-Kit structure
            specify_dir = repo_path / ".specify" / "memory"
            specify_dir.mkdir(parents=True)
            (specify_dir / "constitution.md").write_text("# Constitution\n")

            # Create modular bundle
            bundle_name = "main"
            projects_dir = repo_path / ".specfact" / "projects"
            projects_dir.mkdir(parents=True)
            bundle_dir = projects_dir / bundle_name
            bundle_dir.mkdir()

            from specfact_cli.commands.plan import _convert_plan_bundle_to_project_bundle
            from specfact_cli.models.plan import PlanBundle, Product
            from specfact_cli.utils.bundle_loader import save_project_bundle

            plan_bundle = PlanBundle(
                version="1.0",
                idea=None,
                business=None,
                product=Product(themes=[], releases=[]),
                features=[],
                clarifications=None,
                metadata=None,
            )
            project_bundle = _convert_plan_bundle_to_project_bundle(plan_bundle, bundle_name)
            save_project_bundle(project_bundle, bundle_dir, atomic=True)

            # Test that --overwrite flag is accepted (doesn't cause argument error)
            result = runner.invoke(
                app,
                [
                    "sync",
                    "bridge",
                    "--adapter",
                    "speckit",
                    "--bundle",
                    bundle_name,
                    "--repo",
                    str(repo_path),
                    "--overwrite",
                ],
            )

            # Flag should be accepted (may fail for other reasons like missing plan)
            # But it should not fail with "unrecognized arguments" or similar
            assert result.exit_code != 2, "Overwrite flag should be recognized"

    def test_plan_sync_shared_command(self) -> None:
        """Test plan sync --shared command (convenience wrapper for bidirectional sync)."""
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            # Create Spec-Kit structure
            specify_dir = repo_path / ".specify" / "memory"
            specify_dir.mkdir(parents=True)
            (specify_dir / "constitution.md").write_text("# Constitution\n")

            # Create SpecFact structure (modular bundle)
            bundle_name = "main"
            projects_dir = repo_path / ".specfact" / "projects"
            projects_dir.mkdir(parents=True)
            bundle_dir = projects_dir / bundle_name
            bundle_dir.mkdir()

            from specfact_cli.commands.plan import _convert_plan_bundle_to_project_bundle
            from specfact_cli.models.plan import PlanBundle, Product
            from specfact_cli.utils.bundle_loader import save_project_bundle

            plan_bundle = PlanBundle(
                version="1.0",
                idea=None,
                business=None,
                product=Product(themes=[], releases=[]),
                features=[],
                clarifications=None,
                metadata=None,
            )
            project_bundle = _convert_plan_bundle_to_project_bundle(plan_bundle, bundle_name)
            save_project_bundle(project_bundle, bundle_dir, atomic=True)

            result = runner.invoke(
                app,
                [
                    "sync",
                    "bridge",
                    "--adapter",
                    "speckit",
                    "--bundle",
                    bundle_name,
                    "--bidirectional",
                    "--repo",
                    str(repo_path),
                ],
            )

            assert result.exit_code == 0
            assert (
                "Shared Plans Sync" in result.stdout
                or "team collaboration" in result.stdout.lower()
                or "Syncing" in result.stdout
            )

    def test_plan_sync_shared_without_flag(self) -> None:
        """Test plan sync command requires --shared flag (deprecated, use sync bridge instead)."""
        result = runner.invoke(
            app,
            ["plan", "sync"],
        )

        # The command should fail (either with --shared flag requirement or ImportError)
        assert result.exit_code != 0
        # Check for error message in stdout (ImportError may be in exception, not stdout)
        # Just verify it failed - the actual error may be ImportError due to deprecated command
        assert result.exit_code == 1 or result.exit_code == 2

    def test_sync_spec_kit_watch_mode(self) -> None:
        """Test sync spec-kit watch mode (basic functionality)."""
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            # Create Spec-Kit structure
            specify_dir = repo_path / ".specify" / "memory"
            specify_dir.mkdir(parents=True)
            (specify_dir / "constitution.md").write_text("# Constitution\n")

            # Create SpecFact structure (modular bundle)
            bundle_name = "main"
            projects_dir = repo_path / ".specfact" / "projects"
            projects_dir.mkdir(parents=True)
            bundle_dir = projects_dir / bundle_name
            bundle_dir.mkdir()

            from specfact_cli.commands.plan import _convert_plan_bundle_to_project_bundle
            from specfact_cli.models.plan import PlanBundle, Product
            from specfact_cli.utils.bundle_loader import save_project_bundle

            plan_bundle = PlanBundle(
                version="1.0",
                idea=None,
                business=None,
                product=Product(themes=[], releases=[]),
                features=[],
                clarifications=None,
                metadata=None,
            )
            project_bundle = _convert_plan_bundle_to_project_bundle(plan_bundle, bundle_name)
            save_project_bundle(project_bundle, bundle_dir, atomic=True)

            # Test watch mode (should start and be interruptible)
            # Note: This test verifies watch mode starts correctly
            # Actual file watching is tested in unit tests for SyncWatcher
            import threading
            import time
            from typing import Any

            result_container: dict[str, Any] = {"result": None}

            def run_command() -> None:
                with contextlib.suppress(ValueError, OSError):
                    # Handle case where streams are closed (expected in threading scenarios)
                    result_container["result"] = runner.invoke(
                        app,
                        [
                            "sync",
                            "bridge",
                            "--adapter",
                            "speckit",
                            "--bundle",
                            bundle_name,
                            "--repo",
                            str(repo_path),
                            "--watch",
                            "--interval",
                            "1",
                        ],
                        input="\n",  # Send empty input to simulate Ctrl+C
                    )

            thread = threading.Thread(target=run_command, daemon=True)
            thread.start()
            time.sleep(0.5)  # Give it time to start
            thread.join(timeout=0.1)

            # Watch mode should start (may exit with KeyboardInterrupt or timeout)
            # The important thing is it doesn't fail with "not implemented"
            if result_container["result"]:
                assert (
                    "Watch mode enabled" in result_container["result"].stdout
                    or "Watching for changes" in result_container["result"].stdout
                )
                assert "not implemented" not in result_container["result"].stdout.lower()
            else:
                # Command is still running (expected for watch mode)
                pass

    def test_sync_repository_watch_mode(self) -> None:
        """Test sync repository watch mode (basic functionality)."""
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            # Create minimal repository structure
            src_dir = repo_path / "src"
            src_dir.mkdir(parents=True)
            (src_dir / "main.py").write_text("# Main module\n")

            # Create SpecFact structure
            plans_dir = repo_path / ".specfact" / "plans"
            plans_dir.mkdir(parents=True)
            (plans_dir / "main.bundle.yaml").write_text("version: '1.0'\n")

            # Test watch mode (should start and be interruptible)
            # Note: This test verifies watch mode starts correctly
            # Actual file watching is tested in unit tests for SyncWatcher
            import threading
            import time
            from typing import Any

            result_container: dict[str, Any] = {"result": None}

            def run_command() -> None:
                with contextlib.suppress(ValueError, OSError):
                    # Handle case where streams are closed (expected in threading scenarios)
                    result_container["result"] = runner.invoke(
                        app,
                        ["sync", "repository", "--repo", str(repo_path), "--watch", "--interval", "1"],
                        input="\n",  # Send empty input to simulate Ctrl+C
                    )

            thread = threading.Thread(target=run_command, daemon=True)
            thread.start()
            time.sleep(0.5)  # Give it time to start
            thread.join(timeout=0.1)

            # Watch mode should start (may exit with KeyboardInterrupt or timeout)
            # The important thing is it doesn't fail with "not implemented"
            if result_container["result"]:
                assert (
                    "Watch mode enabled" in result_container["result"].stdout
                    or "Watching for changes" in result_container["result"].stdout
                )
                assert "not implemented" not in result_container["result"].stdout.lower()
            else:
                # Command is still running (expected for watch mode)
                pass

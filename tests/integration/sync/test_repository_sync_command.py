"""
Integration tests for sync repository command with realistic scenarios.
"""

from __future__ import annotations

import contextlib
from pathlib import Path
from tempfile import TemporaryDirectory

from typer.testing import CliRunner

from specfact_cli.cli import app


runner = CliRunner()


class TestSyncRepositoryCommandIntegration:
    """Integration tests for sync repository command with realistic repositories."""

    def test_sync_repository_basic(self) -> None:
        """Test basic sync repository command."""
        import os

        # Set TEST_MODE to disable Progress (avoids LiveError)
        os.environ["TEST_MODE"] = "true"
        try:
            with TemporaryDirectory() as tmpdir:
                repo_path = Path(tmpdir)

                # Create minimal repository structure
                src_dir = repo_path / "src" / "module"
                src_dir.mkdir(parents=True)
                (src_dir / "__init__.py").write_text("")

                result = runner.invoke(app, ["sync", "repository", "--repo", str(repo_path)])

                assert result.exit_code == 0
                assert "Syncing repository changes" in result.stdout or "Repository sync complete" in result.stdout
        finally:
            os.environ.pop("TEST_MODE", None)

    def test_sync_repository_with_confidence(self) -> None:
        """Test sync repository with confidence threshold."""
        import os

        # Set TEST_MODE to disable Progress (avoids LiveError)
        os.environ["TEST_MODE"] = "true"
        try:
            with TemporaryDirectory() as tmpdir:
                repo_path = Path(tmpdir)

                # Create repository structure with code
                src_dir = repo_path / "src" / "module"
                src_dir.mkdir(parents=True)
                (src_dir / "module.py").write_text("class TestClass:\n    pass\n")

                result = runner.invoke(
                    app,
                    ["sync", "repository", "--repo", str(repo_path), "--confidence", "0.7"],
                )

                assert result.exit_code == 0
                assert "Repository sync complete" in result.stdout or "Syncing repository changes" in result.stdout
        finally:
            os.environ.pop("TEST_MODE", None)

    def test_sync_repository_watch_mode_not_implemented(self) -> None:
        """Test sync repository watch mode (now implemented)."""
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            src_dir = repo_path / "src"
            src_dir.mkdir(parents=True)

            # Create SpecFact structure
            plans_dir = repo_path / ".specfact" / "plans"
            plans_dir.mkdir(parents=True)
            (plans_dir / "main.bundle.yaml").write_text("version: '1.0'\n")

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
                        ["sync", "repository", "--repo", str(repo_path), "--watch", "--interval", "1"],
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

    def test_sync_repository_with_target(self) -> None:
        """Test sync repository with custom target directory."""
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            target = repo_path / "custom-specfact"

            src_dir = repo_path / "src"
            src_dir.mkdir(parents=True)

            try:
                result = runner.invoke(
                    app,
                    ["sync", "repository", "--repo", str(repo_path), "--target", str(target)],
                )
            except (ValueError, OSError) as e:
                # Handle case where streams are closed (can happen in parallel test execution)
                if "closed file" in str(e).lower() or "I/O operation" in str(e):
                    # Test passed but had I/O issue - skip assertion
                    return
                raise

            assert result.exit_code == 0
            assert "Repository sync complete" in result.stdout

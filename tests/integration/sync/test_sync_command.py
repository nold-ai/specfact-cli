"""
Integration tests for sync command with realistic scenarios.
"""

from __future__ import annotations

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

            result = runner.invoke(app, ["sync", "spec-kit", "--repo", str(repo_path)])

            assert result.exit_code == 0
            assert "Syncing Spec-Kit artifacts" in result.stdout

    def test_sync_spec_kit_with_bidirectional(self) -> None:
        """Test sync spec-kit with bidirectional flag."""
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            # Create Spec-Kit structure
            specify_dir = repo_path / ".specify" / "memory"
            specify_dir.mkdir(parents=True)
            (specify_dir / "constitution.md").write_text("# Constitution\n")

            # Create SpecFact structure
            plans_dir = repo_path / ".specfact" / "plans"
            plans_dir.mkdir(parents=True)
            (plans_dir / "main.bundle.yaml").write_text("version: '1.0'\n")

            result = runner.invoke(
                app,
                ["sync", "spec-kit", "--repo", str(repo_path), "--bidirectional"],
            )

            assert result.exit_code == 0
            assert "Syncing Spec-Kit artifacts" in result.stdout
            assert "Sync complete" in result.stdout

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

            result = runner.invoke(
                app,
                ["sync", "spec-kit", "--repo", str(repo_path), "--bidirectional"],
            )

            assert result.exit_code == 0
            assert "Detected" in result.stdout or "Sync complete" in result.stdout

    def test_sync_spec_kit_watch_mode_not_implemented(self) -> None:
        """Test sync spec-kit watch mode (not implemented yet)."""
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            specify_dir = repo_path / ".specify" / "memory"
            specify_dir.mkdir(parents=True)
            (specify_dir / "constitution.md").write_text("# Constitution\n")

            result = runner.invoke(
                app,
                ["sync", "spec-kit", "--repo", str(repo_path), "--watch"],
            )

            assert result.exit_code == 0
            assert "Watch mode enabled" in result.stdout or "not implemented" in result.stdout.lower()

    def test_sync_spec_kit_nonexistent_repo(self) -> None:
        """Test sync spec-kit with nonexistent repository."""
        result = runner.invoke(
            app,
            ["sync", "spec-kit", "--repo", "/nonexistent/path"],
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

            # Test that --overwrite flag is accepted (doesn't cause argument error)
            result = runner.invoke(
                app,
                [
                    "sync",
                    "spec-kit",
                    "--repo",
                    str(repo_path),
                    "--overwrite",
                ],
            )

            # Flag should be accepted (may fail for other reasons like missing plan)
            # But it should not fail with "unrecognized arguments" or similar
            assert result.exit_code != 2, "Overwrite flag should be recognized"

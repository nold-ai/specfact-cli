"""
Integration tests for sync repository command with realistic scenarios.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from typer.testing import CliRunner

from specfact_cli.cli import app

runner = CliRunner()


class TestSyncRepositoryCommandIntegration:
    """Integration tests for sync repository command with realistic repositories."""

    def test_sync_repository_basic(self) -> None:
        """Test basic sync repository command."""
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            # Create minimal repository structure
            src_dir = repo_path / "src" / "module"
            src_dir.mkdir(parents=True)
            (src_dir / "__init__.py").write_text("")

            result = runner.invoke(app, ["sync", "repository", "--repo", str(repo_path)])

            assert result.exit_code == 0
            assert "Syncing repository changes" in result.stdout

    def test_sync_repository_with_confidence(self) -> None:
        """Test sync repository with confidence threshold."""
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
            assert "Repository sync complete" in result.stdout

    def test_sync_repository_watch_mode_not_implemented(self) -> None:
        """Test sync repository watch mode (not implemented yet)."""
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            src_dir = repo_path / "src"
            src_dir.mkdir(parents=True)

            result = runner.invoke(
                app,
                ["sync", "repository", "--repo", str(repo_path), "--watch"],
            )

            assert result.exit_code == 0
            assert "Watch mode enabled" in result.stdout or "not implemented" in result.stdout.lower()

    def test_sync_repository_with_target(self) -> None:
        """Test sync repository with custom target directory."""
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            target = repo_path / "custom-specfact"

            src_dir = repo_path / "src"
            src_dir.mkdir(parents=True)

            result = runner.invoke(
                app,
                ["sync", "repository", "--repo", str(repo_path), "--target", str(target)],
            )

            assert result.exit_code == 0
            assert "Repository sync complete" in result.stdout

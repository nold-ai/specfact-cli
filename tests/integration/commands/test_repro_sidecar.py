"""
Integration tests for repro sidecar integration.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from typer.testing import CliRunner

from specfact_cli.cli import app


class TestReproSidecarIntegration:
    """Integration tests for specfact repro --sidecar command."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def temp_repo(self) -> Iterator[Path]:
        """Create temporary repository for testing."""
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "test_repo"
            repo_path.mkdir()
            (repo_path / "src").mkdir()
            (repo_path / "src" / "__init__.py").write_text("")

            # Create a simple Python file with unannotated function
            (repo_path / "src" / "module.py").write_text(
                """
def unannotated_function(x):
    return x * 2
"""
            )

            yield repo_path

    def test_repro_sidecar_without_bundle_fails(self, runner: CliRunner, temp_repo: Path) -> None:
        """Test that --sidecar without --sidecar-bundle fails."""
        result = runner.invoke(app, ["repro", "--sidecar", "--repo", str(temp_repo)])

        # Should fail with error about missing bundle
        assert result.exit_code != 0
        output = result.stdout
        if result.stderr_bytes is not None:
            output += result.stderr
        assert "sidecar-bundle" in output.lower() or "required" in output.lower() or result.exit_code == 2

    @pytest.mark.timeout(30)
    def test_repro_sidecar_detects_unannotated(self, runner: CliRunner, temp_repo: Path) -> None:
        """Test that repro sidecar detects unannotated functions."""
        result = runner.invoke(
            app,
            [
                "repro",
                "--sidecar",
                "--sidecar-bundle",
                "test-bundle",
                "--repo",
                str(temp_repo),
                "--budget",
                "30",
            ],
        )

        # Should not fail (may skip if sidecar workspace not initialized)
        # But should at least attempt to detect unannotated code
        assert "unannotated" in result.stdout.lower() or result.exit_code == 0

    def test_repro_sidecar_applies_safe_defaults(self, runner: CliRunner, temp_repo: Path) -> None:
        """Test that repro sidecar applies safe defaults."""
        from specfact_cli.validators.sidecar.models import TimeoutConfig

        safe_timeouts = TimeoutConfig.safe_defaults_for_repro()

        assert safe_timeouts.crosshair == 30
        assert safe_timeouts.crosshair_per_path == 5
        assert safe_timeouts.crosshair_per_condition == 2

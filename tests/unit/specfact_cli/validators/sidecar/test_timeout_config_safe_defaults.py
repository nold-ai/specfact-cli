"""
Unit tests for TimeoutConfig safe defaults.
"""

from __future__ import annotations

from specfact_cli.validators.sidecar.models import TimeoutConfig


class TestTimeoutConfigSafeDefaults:
    """Test safe defaults for repro mode."""

    def test_safe_defaults_for_repro(self) -> None:
        """Test that safe defaults are applied correctly."""
        config = TimeoutConfig.safe_defaults_for_repro()

        assert config.crosshair == 30
        assert config.specmatic == 30
        assert config.semgrep == 30
        assert config.basedpyright == 30
        assert config.crosshair_per_path == 5
        assert config.crosshair_per_condition == 2

    def test_safe_defaults_different_from_default(self) -> None:
        """Test that safe defaults differ from regular defaults."""
        safe_config = TimeoutConfig.safe_defaults_for_repro()
        default_config = TimeoutConfig()

        assert safe_config.crosshair < default_config.crosshair
        assert safe_config.crosshair_per_path is not None
        assert safe_config.crosshair_per_condition is not None
        assert default_config.crosshair_per_path is None
        assert default_config.crosshair_per_condition is None

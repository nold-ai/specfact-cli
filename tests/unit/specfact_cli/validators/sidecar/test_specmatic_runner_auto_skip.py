"""
Unit tests for Specmatic auto-skip detection.
"""

from __future__ import annotations

from specfact_cli.validators.sidecar.models import AppConfig, SpecmaticConfig
from specfact_cli.validators.sidecar.specmatic_runner import has_service_configuration


class TestHasServiceConfiguration:
    """Test service configuration detection."""

    def test_has_test_base_url(self) -> None:
        """Test detection with test_base_url."""
        specmatic_config = SpecmaticConfig(test_base_url="http://localhost:8000")
        app_config = AppConfig()

        result = has_service_configuration(specmatic_config, app_config)

        assert result is True

    def test_has_host_and_port(self) -> None:
        """Test detection with host and port."""
        specmatic_config = SpecmaticConfig(host="127.0.0.1", port=8080)
        app_config = AppConfig()

        result = has_service_configuration(specmatic_config, app_config)

        assert result is True

    def test_has_app_cmd_and_port(self) -> None:
        """Test detection with app command and port."""
        specmatic_config = SpecmaticConfig()
        app_config = AppConfig(cmd="python app.py", port=8000)

        result = has_service_configuration(specmatic_config, app_config)

        assert result is True

    def test_no_service_configuration(self) -> None:
        """Test detection with no service configuration."""
        specmatic_config = SpecmaticConfig()
        app_config = AppConfig()

        result = has_service_configuration(specmatic_config, app_config)

        assert result is False

    def test_partial_configuration_host_only(self) -> None:
        """Test detection with only host (no port)."""
        specmatic_config = SpecmaticConfig(host="127.0.0.1")
        app_config = AppConfig()

        result = has_service_configuration(specmatic_config, app_config)

        assert result is False

    def test_partial_configuration_port_only(self) -> None:
        """Test detection with only port (no host)."""
        specmatic_config = SpecmaticConfig(port=8080)
        app_config = AppConfig()

        result = has_service_configuration(specmatic_config, app_config)

        assert result is False

    def test_partial_configuration_app_cmd_only(self) -> None:
        """Test detection with only app cmd (no port)."""
        specmatic_config = SpecmaticConfig()
        app_config = AppConfig(cmd="python app.py")

        result = has_service_configuration(specmatic_config, app_config)

        assert result is False

    def test_multiple_configurations(self) -> None:
        """Test detection with multiple configuration options."""
        specmatic_config = SpecmaticConfig(test_base_url="http://localhost:8000", host="127.0.0.1", port=8080)
        app_config = AppConfig(cmd="python app.py", port=8000)

        result = has_service_configuration(specmatic_config, app_config)

        assert result is True

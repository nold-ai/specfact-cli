#!/usr/bin/env python3
"""Validate telemetry configuration and test telemetry collection."""

import logging
import os
import sys
from pathlib import Path

from beartype import beartype
from icontract import ensure


logger = logging.getLogger(__name__)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from specfact_cli.telemetry import TelemetryManager, TelemetrySettings, _read_config_file  # noqa: E402


@beartype
@ensure(lambda result: result == 0, "validation returns success exit code")
def main() -> int:
    logger.info("=== Telemetry Validation ===")

    # Check config file
    config_file = Path.home() / ".specfact" / "telemetry.yaml"
    logger.info("1. Config file exists: %s", config_file.exists())
    if config_file.exists():
        config = _read_config_file()
        logger.debug("   Config content: %s", config)
        logger.info("   Enabled in config: %s", config.get("enabled", False))
        logger.info("   Endpoint: %s", config.get("endpoint", "None"))
    else:
        logger.warning("   Config file not found!")

    # Check environment
    logger.info("2. Environment check:")
    logger.info("   TEST_MODE: %s", os.getenv("TEST_MODE", "Not set"))
    logger.info("   PYTEST_CURRENT_TEST: %s", os.getenv("PYTEST_CURRENT_TEST", "Not set"))
    logger.info("   SPECFACT_TELEMETRY_OPT_IN: %s", os.getenv("SPECFACT_TELEMETRY_OPT_IN", "Not set"))

    # Check settings
    logger.info("3. Telemetry settings:")
    settings = TelemetrySettings.from_env()
    logger.info("   Enabled: %s", settings.enabled)
    logger.info("   Endpoint: %s", settings.endpoint)
    logger.info("   Source: %s", settings.opt_in_source)
    logger.info("   Local path: %s", settings.local_path)

    # Check manager
    logger.info("4. Telemetry manager:")
    manager = TelemetryManager()
    logger.info("   Manager enabled: %s", manager.enabled)
    logger.info("   Last event: %s", manager.last_event)

    # Test event generation
    logger.info("5. Testing event generation:")
    if manager.enabled:
        logger.info("   Telemetry is enabled, generating test event...")
        with manager.track_command("test.validation", {"test": True}) as record:
            record({"test_complete": True})

        if manager.last_event:
            logger.info("   Event generated successfully!")
            logger.debug("   Event: %s", manager.last_event)

            # Check if log file exists
            if settings.local_path.exists():
                logger.info("   Log file exists: %s", settings.local_path)
                logger.info("   Log size: %d bytes", settings.local_path.stat().st_size)
            else:
                logger.warning("   Log file not created: %s", settings.local_path)
        else:
            logger.warning("   No event generated")
    else:
        logger.warning("   Telemetry is disabled - cannot generate events")
        logger.warning("   Check your config file or environment variables")

    logger.info("=== Validation Complete ===")
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    raise SystemExit(main())

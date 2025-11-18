#!/usr/bin/env python3
"""Validate telemetry configuration and test telemetry collection."""

import sys
from pathlib import Path


# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from specfact_cli.telemetry import TelemetryManager, TelemetrySettings, _read_config_file


def main():
    print("=== Telemetry Validation ===\n")

    # Check config file
    config_file = Path.home() / ".specfact" / "telemetry.yaml"
    print(f"1. Config file exists: {config_file.exists()}")
    if config_file.exists():
        config = _read_config_file()
        print(f"   Config content: {config}")
        print(f"   Enabled in config: {config.get('enabled', False)}")
        print(f"   Endpoint: {config.get('endpoint', 'None')}")
    else:
        print("   ⚠️  Config file not found!")

    # Check environment
    import os

    print("\n2. Environment check:")
    print(f"   TEST_MODE: {os.getenv('TEST_MODE', 'Not set')}")
    print(f"   PYTEST_CURRENT_TEST: {os.getenv('PYTEST_CURRENT_TEST', 'Not set')}")
    print(f"   SPECFACT_TELEMETRY_OPT_IN: {os.getenv('SPECFACT_TELEMETRY_OPT_IN', 'Not set')}")

    # Check settings
    print("\n3. Telemetry settings:")
    settings = TelemetrySettings.from_env()
    print(f"   Enabled: {settings.enabled}")
    print(f"   Endpoint: {settings.endpoint}")
    print(f"   Source: {settings.opt_in_source}")
    print(f"   Local path: {settings.local_path}")

    # Check manager
    print("\n4. Telemetry manager:")
    manager = TelemetryManager()
    print(f"   Manager enabled: {manager.enabled}")
    print(f"   Last event: {manager.last_event}")

    # Test event generation
    print("\n5. Testing event generation:")
    if manager.enabled:
        print("   ✓ Telemetry is enabled, generating test event...")
        with manager.track_command("test.validation", {"test": True}) as record:
            record({"test_complete": True})

        if manager.last_event:
            print("   ✓ Event generated successfully!")
            print(f"   Event: {manager.last_event}")

            # Check if log file exists
            if settings.local_path.exists():
                print(f"   ✓ Log file exists: {settings.local_path}")
                print(f"   Log size: {settings.local_path.stat().st_size} bytes")
            else:
                print(f"   ⚠️  Log file not created: {settings.local_path}")
        else:
            print("   ⚠️  No event generated")
    else:
        print("   ⚠️  Telemetry is disabled - cannot generate events")
        print("   Check your config file or environment variables")

    print("\n=== Validation Complete ===")


if __name__ == "__main__":
    main()

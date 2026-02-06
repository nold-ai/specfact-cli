"""Pytest configuration for tools tests."""

import os
import sys
import tempfile
from pathlib import Path


# Add project root to path for tools imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Set TEST_MODE globally for all tests to avoid interactive prompts
os.environ["TEST_MODE"] = "true"

# Isolate registry state for test runs to avoid coupling with ~/.specfact/registry.
# This prevents local module enable/disable settings from affecting command discovery in tests.
os.environ.setdefault("SPECFACT_REGISTRY_DIR", tempfile.mkdtemp(prefix="specfact-test-registry-"))

"""Pytest configuration for tools tests."""

import os
import sys
import tempfile
from pathlib import Path


# Add project root to path for tools imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def _resolve_modules_repo_root() -> Path:
    configured = os.environ.get("SPECFACT_MODULES_REPO")
    if configured:
        return Path(configured).expanduser().resolve()
    for candidate_base in (project_root, *project_root.parents):
        sibling_repo = candidate_base / "specfact-cli-modules"
        if sibling_repo.exists():
            return sibling_repo
        sibling_repo = candidate_base.parent / "specfact-cli-modules"
        if sibling_repo.exists():
            return sibling_repo
    return project_root / "specfact-cli-modules"


# Add bundle package src roots for module-migration-02 test runs.
bundle_packages_root = _resolve_modules_repo_root() / "packages"
if bundle_packages_root.exists():
    for bundle_src in bundle_packages_root.glob("*/src"):
        bundle_src_str = str(bundle_src)
        if bundle_src_str not in sys.path:
            sys.path.insert(0, bundle_src_str)

# Set TEST_MODE globally for all tests to avoid interactive prompts
os.environ["TEST_MODE"] = "true"
# Allow loading bundled modules without signature in tests
os.environ.setdefault("SPECFACT_ALLOW_UNSIGNED", "1")

# Isolate registry state for test runs to avoid coupling with ~/.specfact/registry.
# This prevents local module enable/disable settings from affecting command discovery in tests.
os.environ.setdefault("SPECFACT_REGISTRY_DIR", tempfile.mkdtemp(prefix="specfact-test-registry-"))
